#!/usr/bin/env python3
"""
GLM 嵌入服务模块
"""

import os
import asyncio
import logging
import aiohttp
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GLMEmbeddingService:
    """GLM 嵌入服务"""
    
    def __init__(self):
        """初始化嵌入服务"""
        self.glm_api_key = os.getenv("GLM_API_KEY")
        self.dimension = 1024  # GLM embedding-2 是 1024 维
        
        if not self.glm_api_key:
            raise ValueError("GLM API Key 未配置")
        
        logger.info("✅ GLM 嵌入服务初始化")
        logger.info(f"📋 GLM API Key: {self.glm_api_key[:10]}...")
        logger.info(f"📋 向量维度: {self.dimension}")
    
    async def embed_text(self, text: str):
        """使用 GLM 生成嵌入"""
        try:
            url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
            
            headers = {
                "Authorization": f"Bearer {self.glm_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "embedding-2",
                "input": text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        embedding = result["data"][0]["embedding"]
                        logger.info(f"✅ GLM 嵌入生成成功: {len(embedding)} 维")
                        return embedding
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ GLM API 调用失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ GLM 嵌入生成失败: {e}")
            return None

# 测试函数
async def test_glm_service():
    """测试 GLM 服务"""
    try:
        service = GLMEmbeddingService()
        embedding = await service.embed_text("测试文本")
        if embedding:
            logger.info(f"✅ GLM 服务测试成功: {len(embedding)} 维")
            return True
        else:
            logger.error("❌ GLM 服务测试失败")
            return False
    except Exception as e:
        logger.error(f"❌ GLM 服务测试异常: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_glm_service())
