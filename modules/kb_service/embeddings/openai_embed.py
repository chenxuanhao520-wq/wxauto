"""
OpenAI 嵌入模型
"""
import os
import logging
from typing import List

logger = logging.getLogger(__name__)


class OpenAIEmbeddings:
    """
    OpenAI 嵌入模型
    
    优势：
    - 无需本地部署
    - 质量稳定
    - API调用简单
    
    劣势：
    - 需要付费
    - 数据上云
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "text-embedding-3-small"
    ):
        """
        初始化OpenAI嵌入模型
        
        Args:
            api_key: API密钥
            model: 模型名称（text-embedding-3-small / text-embedding-3-large）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("需要设置 OPENAI_API_KEY")
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai未安装，请运行: pip install openai")
        
        logger.info(f"OpenAI嵌入模型初始化: {model}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文档嵌入
        
        Args:
            texts: 文本列表
        
        Returns:
            嵌入向量列表
        """
        if not texts:
            return []
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            embeddings = [item.embedding for item in response.data]
            
            logger.info(f"生成嵌入成功: {len(texts)}条文本")
            return embeddings
            
        except Exception as e:
            logger.error(f"OpenAI嵌入生成失败: {e}")
            raise
    
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
        dimensions = {
            'text-embedding-3-small': 1536,
            'text-embedding-3-large': 3072,
            'text-embedding-ada-002': 1536
        }
        return dimensions.get(self.model, 1536)

