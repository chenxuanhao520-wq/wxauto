"""
Supabase向量数据库服务 - 基于 pgvector
替代 Pinecone，统一存储，零成本

服务层封装，提供高级文档搜索接口
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class VectorSearchService:
    """向量搜索服务 - 集成 Supabase pgvector 和嵌入服务"""
    
    def __init__(self, supabase_client):
        """
        初始化向量搜索服务
        
        Args:
            supabase_client: Supabase客户端实例
        """
        # 导入统一的向量客户端
        from .supabase_vector_client import SupabaseVectorClient
        
        # 获取配置
        table_name = os.getenv("VECTOR_TABLE_NAME", "knowledge_vectors")
        dimension = int(os.getenv("VECTOR_DIMENSION", "1536"))
        distance_metric = os.getenv("VECTOR_DISTANCE_METRIC", "cosine")
        
        # 处理不同类型的客户端
        if hasattr(supabase_client, 'client'):
            supabase_url = supabase_client.url
            supabase_key = supabase_client.supabase_key
        else:
            supabase_url = supabase_client.url
            supabase_key = supabase_client.supabase_key
        
        # 初始化向量客户端
        self.vector_client = SupabaseVectorClient(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            table_name=table_name,
            embedding_dimension=dimension,
            distance_metric=distance_metric
        )
        
        self.embedding_service = None
        
        # 初始化嵌入服务
        self._initialize_embedding_service()
        
        logger.info(f"✅ 向量搜索服务初始化完成（Supabase pgvector, 表: {table_name}）")
    
    def _initialize_embedding_service(self):
        """初始化嵌入服务"""
        try:
            from modules.embeddings.unified_embedding_service import get_embedding_service
            self.embedding_service = get_embedding_service()
            logger.info("✅ 嵌入服务初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 嵌入服务初始化失败: {e}")
            logger.info("💡 向量搜索功能将不可用")
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档列表，每个文档包含：
                - id: 文档ID
                - content: 文档内容
                - title: 文档标题（可选）
                - source: 文档来源（可选）
        """
        try:
            if not self.embedding_service:
                logger.error("❌ 嵌入服务未初始化")
                return False
            
            vectors = []
            for doc in documents:
                # 生成嵌入向量
                embedding = await self.embedding_service.embed_text(doc.get("content", ""))
                
                if embedding:
                    vector = {
                        "id": doc.get("id"),
                        "content": doc.get("content", ""),
                        "embedding": embedding,
                        "metadata": {
                            "title": doc.get("title", ""),
                            "source": doc.get("source", ""),
                            "created_at": datetime.now().isoformat()
                        }
                    }
                    vectors.append(vector)
            
            # 插入到 Supabase
            success = await self.vector_client.upsert_vectors(vectors)
            
            if success:
                logger.info(f"✅ 文档添加成功: {len(documents)}条")
            else:
                logger.error(f"❌ 文档添加失败")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 添加文档失败: {e}")
            return False
    
    async def search_similar_documents(
        self, 
        query: str, 
        top_k: int = 10,
        similarity_threshold: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值
            metadata_filter: 元数据过滤条件
        """
        try:
            if not self.embedding_service:
                logger.error("❌ 嵌入服务未初始化")
                return []
            
            # 生成查询向量
            query_embedding = await self.embedding_service.embed_text(query)
            
            if not query_embedding:
                logger.error("❌ 查询向量生成失败")
                return []
            
            # 在 Supabase 中搜索
            matches = await self.vector_client.search_vectors(
                query_embedding=query_embedding,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                metadata_filter=metadata_filter
            )
            
            # 转换结果格式
            results = []
            for match in matches:
                result = {
                    "id": match["id"],
                    "score": match["similarity"],
                    "content": match["content"],
                    "metadata": match["metadata"]
                }
                results.append(result)
            
            logger.debug(f"✅ 文档搜索成功: {len(results)}条结果")
            return results
            
        except Exception as e:
            logger.error(f"❌ 文档搜索失败: {e}")
            return []
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档"""
        try:
            success = await self.vector_client.delete_vectors(document_ids)
            
            if success:
                logger.info(f"✅ 文档删除成功: {len(document_ids)}条")
            else:
                logger.error(f"❌ 文档删除失败")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 删除文档失败: {e}")
            return False
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        try:
            stats = await self.vector_client.get_stats()
            
            return {
                "service_type": "vector_search",
                "backend": "supabase_pgvector",
                "stats": stats,
                "embedding_service_available": self.embedding_service is not None
            }
            
        except Exception as e:
            logger.error(f"❌ 获取服务统计失败: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return await self.vector_client.health_check()
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return False


# 全局向量搜索服务实例
_vector_search_service: Optional[VectorSearchService] = None


def get_vector_search_service() -> VectorSearchService:
    """获取全局向量搜索服务实例"""
    global _vector_search_service
    if _vector_search_service is None:
        raise RuntimeError("向量搜索服务未初始化")
    return _vector_search_service


def init_vector_search_service(supabase_client):
    """初始化全局向量搜索服务"""
    global _vector_search_service
    _vector_search_service = VectorSearchService(supabase_client)
    logger.info("✅ 全局向量搜索服务初始化完成（Supabase pgvector）")
