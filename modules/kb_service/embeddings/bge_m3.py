"""
BGE-M3 嵌入模型
中文效果最佳的开源嵌入模型
"""
import logging
from typing import List
import numpy as np

logger = logging.getLogger(__name__)


class BGEM3Embeddings:
    """
    BGE-M3 嵌入模型
    
    特点：
    - 中文效果最佳（C-MTEB榜单第一）
    - 支持100+语言
    - 向量维度：1024
    - 本地部署，免费使用
    """
    
    def __init__(self, model_name: str = "BAAI/bge-m3", use_fp16: bool = True):
        """
        初始化BGE-M3模型
        
        Args:
            model_name: 模型名称
            use_fp16: 是否使用FP16（节省显存）
        """
        self.model_name = model_name
        self.use_fp16 = use_fp16
        self._model = None
        
        logger.info(f"初始化 BGE-M3 模型: {model_name}")
    
    def _load_model(self):
        """懒加载模型"""
        if self._model is not None:
            return
        
        try:
            from FlagEmbedding import BGEM3FlagModel
        except ImportError:
            raise ImportError("FlagEmbedding未安装，请运行: pip install FlagEmbedding")
        
        logger.info("加载 BGE-M3 模型（首次加载会下载，请稍候）...")
        
        self._model = BGEM3FlagModel(
            self.model_name,
            use_fp16=self.use_fp16
        )
        
        logger.info("BGE-M3 模型加载完成")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文档嵌入
        
        Args:
            texts: 文本列表
        
        Returns:
            嵌入向量列表
        """
        self._load_model()
        
        if not texts:
            return []
        
        # BGE-M3 批量编码
        embeddings = self._model.encode(
            texts,
            batch_size=12,
            max_length=512,  # 最大长度
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False
        )
        
        # 转换为列表
        if isinstance(embeddings, dict):
            embeddings = embeddings['dense_vecs']
        
        return embeddings.tolist() if hasattr(embeddings, 'tolist') else list(embeddings)
    
    def embed_query(self, text: str) -> List[float]:
        """
        生成查询嵌入
        
        Args:
            text: 查询文本
        
        Returns:
            嵌入向量
        """
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else []
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return 1024  # BGE-M3 固定维度

