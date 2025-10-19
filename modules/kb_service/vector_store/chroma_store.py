"""
Chroma 向量数据库
轻量级、易部署、适合中小规模
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ChromaStore:
    """
    Chroma 向量数据库
    
    优势：
    - 轻量级，无需独立部署
    - 持久化到本地文件
    - API简单易用
    - 适合<10万文档
    """
    
    def __init__(self, persist_directory: str = "data/chroma_db"):
        """
        初始化 Chroma
        
        Args:
            persist_directory: 持久化目录
        """
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise ImportError("chromadb未安装，请运行: pip install chromadb")
        
        # 初始化客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        logger.info(f"Chroma 向量数据库初始化: {persist_directory}")
    
    def create_collection(
        self,
        collection_name: str = "knowledge_base",
        embedding_function = None
    ):
        """
        创建或获取集合
        
        Args:
            collection_name: 集合名称
            embedding_function: 嵌入函数（可选）
        """
        try:
            # 获取已存在的集合
            collection = self.client.get_collection(name=collection_name)
            logger.info(f"使用已存在的集合: {collection_name}")
        except:
            # 创建新集合
            collection = self.client.create_collection(
                name=collection_name,
                embedding_function=embedding_function,
                metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
            )
            logger.info(f"创建新集合: {collection_name}")
        
        return collection
    
    def add_documents(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        """
        添加文档
        
        Args:
            collection_name: 集合名称
            texts: 文本列表
            metadatas: 元数据列表
            ids: ID列表
            embeddings: 嵌入向量（可选，如果提供则直接使用）
        """
        collection = self.create_collection(collection_name)
        
        if embeddings:
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
        else:
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
        
        logger.info(f"添加文档成功: {len(texts)}条")
    
    def search(
        self,
        collection_name: str,
        query_text: str = None,
        query_embedding: List[float] = None,
        n_results: int = 10,
        where: Dict = None
    ) -> Dict[str, Any]:
        """
        检索文档
        
        Args:
            collection_name: 集合名称
            query_text: 查询文本
            query_embedding: 查询向量
            n_results: 返回数量
            where: 过滤条件
        
        Returns:
            检索结果
        """
        collection = self.create_collection(collection_name)
        
        if query_embedding:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
        elif query_text:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
        else:
            raise ValueError("必须提供 query_text 或 query_embedding")
        
        return results
    
    def delete_collection(self, collection_name: str) -> None:
        """删除集合"""
        self.client.delete_collection(name=collection_name)
        logger.info(f"集合已删除: {collection_name}")
    
    def get_count(self, collection_name: str) -> int:
        """获取文档数量"""
        collection = self.create_collection(collection_name)
        return collection.count()

