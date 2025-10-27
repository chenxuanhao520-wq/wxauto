"""
Supabase pgvector 向量数据库客户端
使用Supabase内置的pgvector扩展进行向量存储和搜索

特性：
- 高性能向量搜索
- 与Supabase数据库集成
- 支持多种距离度量
- 自动索引管理
- 批量操作支持
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from supabase import create_client, Client
import numpy as np
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SupabaseVectorClient:
    """
    Supabase pgvector 向量数据库客户端
    
    特性：
    1. 使用Supabase内置pgvector扩展
    2. 与现有数据库集成
    3. 支持向量相似度搜索
    4. 成本更低，维护更简单
    5. 支持多种距离度量（cosine, l2, inner_product）
    6. 自动索引管理
    """
    
    def __init__(
        self, 
        supabase_url: str, 
        supabase_key: str,
        table_name: str = "knowledge_vectors",
        embedding_dimension: int = 1536,
        distance_metric: str = "cosine"
    ):
        """
        初始化Supabase向量客户端
        
        Args:
            supabase_url: Supabase项目URL
            supabase_key: Supabase服务密钥
            table_name: 向量表名
            embedding_dimension: 向量维度
            distance_metric: 距离度量（cosine, l2, inner_product）
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.table_name = table_name
        self.embedding_dimension = embedding_dimension
        self.distance_metric = distance_metric
        self._init_table()
    
    def _init_table(self):
        """初始化向量表"""
        try:
            # 创建向量表（如果不存在）
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id SERIAL PRIMARY KEY,
                vector_id TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                metadata JSONB,
                embedding VECTOR({self.embedding_dimension}),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            
            -- 创建向量索引
            CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx 
            ON {self.table_name} USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            
            -- 创建元数据索引
            CREATE INDEX IF NOT EXISTS {self.table_name}_metadata_idx 
            ON {self.table_name} USING gin (metadata);
            
            -- 创建向量ID索引
            CREATE INDEX IF NOT EXISTS {self.table_name}_vector_id_idx 
            ON {self.table_name} (vector_id);
            """
            
            # 执行SQL
            result = self.supabase.rpc('exec_sql', {'sql': create_table_sql})
            logger.info(f"✅ 向量表 {self.table_name} 初始化成功")
            
        except Exception as e:
            logger.warning(f"⚠️ 向量表初始化失败: {e}")
    
    def _get_distance_operator(self) -> str:
        """获取距离操作符"""
        distance_ops = {
            "cosine": "<=>",
            "l2": "<->", 
            "inner_product": "<#>"
        }
        return distance_ops.get(self.distance_metric, "<=>")
    
    def _calculate_similarity(self, distance: float) -> float:
        """计算相似度分数"""
        if self.distance_metric == "cosine":
            return 1 - distance
        elif self.distance_metric == "l2":
            return 1 / (1 + distance)
        elif self.distance_metric == "inner_product":
            return distance
        else:
            return 1 - distance
    
    async def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        """
        插入或更新向量
        
        Args:
            vectors: 向量列表，每个向量包含：
                - id: 向量ID
                - content: 文本内容
                - embedding: 向量嵌入
                - metadata: 元数据
        """
        try:
            if not vectors:
                logger.warning("⚠️ 向量列表为空")
                return True
            
            # 验证向量格式
            for vector in vectors:
                if not vector.get("id"):
                    raise ValueError("向量ID不能为空")
                if not vector.get("embedding"):
                    raise ValueError("向量嵌入不能为空")
                if len(vector.get("embedding", [])) != self.embedding_dimension:
                    raise ValueError(f"向量维度必须为 {self.embedding_dimension}")
            
            # 批量插入/更新
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                
                for vector in batch:
                    # 准备数据
                    data = {
                        "vector_id": vector.get("id"),
                        "content": vector.get("content", ""),
                        "metadata": vector.get("metadata", {}),
                        "embedding": vector.get("embedding"),
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    # 使用upsert操作
                    result = self.supabase.table(self.table_name).upsert(
                        data, 
                        on_conflict="vector_id"
                    ).execute()
                
                logger.info(f"✅ 已处理 {min(i + batch_size, len(vectors))}/{len(vectors)} 个向量")
                
            logger.info(f"✅ 成功插入/更新 {len(vectors)} 个向量")
            return True
            
        except Exception as e:
            logger.error(f"❌ 向量插入失败: {e}")
            return False
    
    async def search_vectors(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        metadata_filter: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        向量相似度搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值
            metadata_filter: 元数据过滤条件
        """
        try:
            if not query_embedding:
                logger.warning("⚠️ 查询向量为空")
                return []
            
            if len(query_embedding) != self.embedding_dimension:
                logger.error(f"❌ 查询向量维度错误: {len(query_embedding)} != {self.embedding_dimension}")
                return []
            
            # 构建SQL查询
            distance_op = self._get_distance_operator()
            
            sql = f"""
            SELECT 
                vector_id,
                content,
                metadata,
                embedding {distance_op} %s as distance,
                created_at,
                updated_at
            FROM {self.table_name}
            WHERE embedding {distance_op} %s < %s
            """
            
            params = [query_embedding, query_embedding, 1 - similarity_threshold]
            
            # 添加元数据过滤
            if metadata_filter:
                for key, value in metadata_filter.items():
                    sql += f" AND metadata->>'{key}' = %s"
                    params.append(str(value))
            
            sql += f" ORDER BY distance ASC LIMIT %s"
            params.append(top_k)
            
            # 执行查询
            result = self.supabase.rpc('exec_sql', {
                'sql': sql,
                'params': params
            })
            
            # 处理结果
            results = []
            if result.data:
                for row in result.data:
                    similarity = self._calculate_similarity(row["distance"])
                    results.append({
                        "id": row["vector_id"],
                        "content": row["content"],
                        "metadata": row["metadata"],
                        "similarity": similarity,
                        "distance": row["distance"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"]
                    })
            
            logger.info(f"🔍 找到 {len(results)} 个相似向量")
            return results
            
        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []
    
    async def delete_vectors(self, vector_ids: List[str]) -> bool:
        """删除向量"""
        try:
            if not vector_ids:
                logger.warning("⚠️ 向量ID列表为空")
                return True
            
            result = self.supabase.table(self.table_name).delete().in_(
                "vector_id", vector_ids
            ).execute()
            
            logger.info(f"✅ 成功删除 {len(vector_ids)} 个向量")
            return True
            
        except Exception as e:
            logger.error(f"❌ 向量删除失败: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取向量统计信息"""
        try:
            # 获取总数
            count_result = self.supabase.table(self.table_name).select("id", count="exact").execute()
            total_count = count_result.count if count_result.count else 0
            
            # 获取最近更新时间
            latest_result = self.supabase.table(self.table_name).select("updated_at").order("updated_at", desc=True).limit(1).execute()
            latest_update = latest_result.data[0]["updated_at"] if latest_result.data else None
            
            # 获取创建时间
            created_result = self.supabase.table(self.table_name).select("created_at").order("created_at", desc=True).limit(1).execute()
            latest_created = created_result.data[0]["created_at"] if created_result.data else None
            
            return {
                "total_vectors": total_count,
                "table_name": self.table_name,
                "embedding_dimension": self.embedding_dimension,
                "distance_metric": self.distance_metric,
                "latest_update": latest_update,
                "latest_created": latest_created
            }
            
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {
                "total_vectors": 0,
                "table_name": self.table_name,
                "embedding_dimension": self.embedding_dimension,
                "distance_metric": self.distance_metric,
                "latest_update": None,
                "latest_created": None
            }
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            result = self.supabase.table(self.table_name).select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return False
    
    async def batch_search(
        self, 
        query_embeddings: List[List[float]], 
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[List[Dict[str, Any]]]:
        """
        批量向量搜索
        
        Args:
            query_embeddings: 查询向量列表
            top_k: 每个查询返回结果数量
            similarity_threshold: 相似度阈值
        """
        try:
            results = []
            for query_embedding in query_embeddings:
                result = await self.search_vectors(
                    query_embedding, 
                    top_k, 
                    similarity_threshold
                )
                results.append(result)
            
            logger.info(f"🔍 批量搜索完成: {len(query_embeddings)} 个查询")
            return results
            
        except Exception as e:
            logger.error(f"❌ 批量搜索失败: {e}")
            return []
    
    async def update_vector_metadata(self, vector_id: str, metadata: Dict[str, Any]) -> bool:
        """更新向量元数据"""
        try:
            result = self.supabase.table(self.table_name).update({
                "metadata": metadata,
                "updated_at": datetime.now().isoformat()
            }).eq("vector_id", vector_id).execute()
            
            logger.info(f"✅ 成功更新向量 {vector_id} 的元数据")
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新向量元数据失败: {e}")
            return False
    
    async def get_vector_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取向量"""
        try:
            result = self.supabase.table(self.table_name).select("*").eq("vector_id", vector_id).execute()
            
            if result.data:
                row = result.data[0]
                return {
                    "id": row["vector_id"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "embedding": row["embedding"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取向量失败: {e}")
            return None


# 兼容性包装器
class VectorClientWrapper:
    """向量客户端包装器，保持与Pinecone相同的接口"""
    
    def __init__(self, supabase_url: str, supabase_key: str, **kwargs):
        self.client = SupabaseVectorClient(supabase_url, supabase_key, **kwargs)
    
    async def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        return await self.client.upsert_vectors(vectors)
    
    async def search_vectors(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        return await self.client.search_vectors(query_embedding, top_k)
    
    async def delete_vectors(self, vector_ids: List[str]) -> bool:
        return await self.client.delete_vectors(vector_ids)
    
    async def get_stats(self) -> Dict[str, Any]:
        return await self.client.get_stats()
    
    async def health_check(self) -> bool:
        return await self.client.health_check()
