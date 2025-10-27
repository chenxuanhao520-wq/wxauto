"""
Pinecone向量数据库客户端 - 官方接入方案
专为企业级向量检索设计
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class PineconeClient:
    """Pinecone向量数据库客户端 - 官方接入方案"""
    
    def __init__(self):
        """初始化Pinecone客户端"""
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp-free")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "wxauto-knowledge")
        
        if not self.api_key:
            logger.warning("⚠️ Pinecone配置不完整，使用默认配置（开发模式）")
            self.api_key = "your_pinecone_api_key"
        
        self.client = None
        self.index = None
        
        try:
            self._initialize_client()
            self._verify_connection()
        except Exception as e:
            logger.error(f"❌ Pinecone初始化失败: {e}")
            raise
    
    def _initialize_client(self):
        """初始化Pinecone客户端"""
        try:
            from pinecone import Pinecone, ServerlessSpec
            
            # 创建Pinecone客户端
            pc = Pinecone(api_key=self.api_key)
            
            # 检查索引是否存在
            existing_indexes = pc.list_indexes()
            # 兼容不同版本的SDK
            if hasattr(existing_indexes, 'names'):
                index_names = existing_indexes.names()
            else:
                # 新版SDK返回迭代器
                index_names = [idx.name for idx in existing_indexes]
            
            if self.index_name not in index_names:
                logger.info(f"📊 创建Pinecone索引: {self.index_name}")
                
                # 创建服务器less索引
                pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI嵌入维度
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                
                logger.info(f"✅ Pinecone索引创建成功: {self.index_name}")
            else:
                logger.info(f"✅ Pinecone索引已存在: {self.index_name}")
            
            # 获取索引实例
            self.index = pc.Index(self.index_name)
            self.client = pc
            
            logger.info(f"✅ Pinecone客户端初始化成功")
            
        except ImportError:
            raise ImportError("Pinecone库未安装: pip install pinecone-client")
        except Exception as e:
            logger.error(f"❌ Pinecone客户端初始化失败: {e}")
            raise
    
    def _verify_connection(self):
        """验证Pinecone连接"""
        try:
            # 获取索引统计信息
            stats = self.index.describe_index_stats()
            logger.info(f"✅ Pinecone连接验证成功")
            logger.info(f"   索引: {self.index_name}")
            logger.info(f"   向量数量: {stats.total_vector_count}")
            logger.info(f"   维度: {stats.dimension}")
        except Exception as e:
            logger.warning(f"⚠️ Pinecone连接验证失败: {e}")
            logger.info("💡 请检查:")
            logger.info("   1. PINECONE_API_KEY是否正确")
            logger.info("   2. 网络连接是否正常")
            logger.info("   3. Pinecone账户是否有权限")
            logger.info("   4. 索引名称是否正确")
    
    async def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        """插入或更新向量"""
        try:
            # 转换向量格式
            pinecone_vectors = []
            for vector in vectors:
                pinecone_vector = {
                    "id": vector.get("id"),
                    "values": vector.get("values"),
                    "metadata": vector.get("metadata", {})
                }
                pinecone_vectors.append(pinecone_vector)
            
            # 批量插入
            self.index.upsert(vectors=pinecone_vectors)
            
            logger.debug(f"✅ Pinecone向量插入成功: {len(vectors)}条")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pinecone向量插入失败: {e}")
            return False
    
    async def query_vectors(
        self, 
        query_vector: List[float], 
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """查询相似向量"""
        try:
            # 构建查询参数
            query_params = {
                "vector": query_vector,
                "top_k": top_k,
                "include_metadata": include_metadata
            }
            
            if filter_dict:
                query_params["filter"] = filter_dict
            
            # 执行查询
            result = self.index.query(**query_params)
            
            # 转换结果格式
            matches = []
            for match in result.matches:
                match_data = {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata if include_metadata else {}
                }
                matches.append(match_data)
            
            logger.debug(f"✅ Pinecone向量查询成功: {len(matches)}条结果")
            return matches
            
        except Exception as e:
            logger.error(f"❌ Pinecone向量查询失败: {e}")
            return []
    
    async def delete_vectors(self, vector_ids: List[str]) -> bool:
        """删除向量"""
        try:
            self.index.delete(ids=vector_ids)
            logger.debug(f"✅ Pinecone向量删除成功: {len(vector_ids)}条")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pinecone向量删除失败: {e}")
            return False
    
    async def get_vector_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取向量"""
        try:
            result = self.index.fetch(ids=[vector_id])
            
            if vector_id in result.vectors:
                vector_data = result.vectors[vector_id]
                return {
                    "id": vector_data.id,
                    "values": vector_data.values,
                    "metadata": vector_data.metadata
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ Pinecone获取向量失败: {e}")
            return None
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        try:
            stats = self.index.describe_index_stats()
            
            return {
                "index_name": self.index_name,
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
            
        except Exception as e:
            logger.error(f"❌ Pinecone获取统计失败: {e}")
            return {"error": str(e)}
    
    async def create_namespace(self, namespace: str) -> bool:
        """创建命名空间"""
        try:
            # Pinecone会自动创建命名空间，无需显式创建
            logger.info(f"✅ Pinecone命名空间准备就绪: {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pinecone命名空间创建失败: {e}")
            return False
    
    async def delete_namespace(self, namespace: str) -> bool:
        """删除命名空间"""
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"✅ Pinecone命名空间删除成功: {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pinecone命名空间删除失败: {e}")
            return False


class VectorSearchService:
    """向量搜索服务 - 集成Pinecone和嵌入服务"""
    
    def __init__(self):
        """初始化向量搜索服务"""
        self.pinecone_client = PineconeClient()
        self.embedding_service = None
        
        # 初始化嵌入服务
        self._initialize_embedding_service()
        
        logger.info("✅ 向量搜索服务初始化完成")
    
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
        """添加文档到向量数据库"""
        try:
            if not self.embedding_service:
                logger.error("❌ 嵌入服务未初始化")
                return False
            
            vectors = []
            for doc in documents:
                # 生成嵌入向量
                embedding = await self.embedding_service.get_embedding(doc.get("content", ""))
                
                if embedding:
                    vector = {
                        "id": doc.get("id"),
                        "values": embedding,
                        "metadata": {
                            "content": doc.get("content", ""),
                            "title": doc.get("title", ""),
                            "source": doc.get("source", ""),
                            "created_at": datetime.now().isoformat()
                        }
                    }
                    vectors.append(vector)
            
            # 插入到Pinecone
            success = await self.pinecone_client.upsert_vectors(vectors)
            
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
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        try:
            if not self.embedding_service:
                logger.error("❌ 嵌入服务未初始化")
                return []
            
            # 生成查询向量
            query_embedding = await self.embedding_service.get_embedding(query)
            
            if not query_embedding:
                logger.error("❌ 查询向量生成失败")
                return []
            
            # 在Pinecone中搜索
            matches = await self.pinecone_client.query_vectors(
                query_vector=query_embedding,
                top_k=top_k,
                filter_dict=filter_dict,
                include_metadata=True
            )
            
            # 转换结果格式
            results = []
            for match in matches:
                result = {
                    "id": match["id"],
                    "score": match["score"],
                    "content": match["metadata"].get("content", ""),
                    "title": match["metadata"].get("title", ""),
                    "source": match["metadata"].get("source", "")
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
            success = await self.pinecone_client.delete_vectors(document_ids)
            
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
            pinecone_stats = await self.pinecone_client.get_index_stats()
            
            return {
                "service_type": "vector_search",
                "pinecone_stats": pinecone_stats,
                "embedding_service_available": self.embedding_service is not None
            }
            
        except Exception as e:
            logger.error(f"❌ 获取服务统计失败: {e}")
            return {"error": str(e)}


# 全局向量搜索服务实例
_vector_search_service: Optional[VectorSearchService] = None


def get_vector_search_service() -> VectorSearchService:
    """获取全局向量搜索服务实例"""
    global _vector_search_service
    if _vector_search_service is None:
        _vector_search_service = VectorSearchService()
    return _vector_search_service


def init_vector_search_service():
    """初始化全局向量搜索服务"""
    global _vector_search_service
    _vector_search_service = VectorSearchService()
    logger.info("✅ 全局向量搜索服务初始化完成")