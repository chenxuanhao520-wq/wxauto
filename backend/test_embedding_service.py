#!/usr/bin/env python3
"""
初始化嵌入服务
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_embedding_service():
    """初始化嵌入服务"""
    try:
        logger.info("🔍 初始化嵌入服务...")
        
        # 检查环境变量
        zhipu_key = os.getenv("ZHIPUAI_API_KEY")
        if not zhipu_key:
            logger.error("❌ 缺少 ZHIPUAI_API_KEY")
            return False
        
        logger.info("✅ ZhipuAI API Key 已配置")
        
        # 简单的嵌入服务测试
        try:
            import requests
            
            # 测试 ZhipuAI 嵌入 API
            url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
            headers = {
                "Authorization": f"Bearer {zhipu_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "text2vec-large-chinese",
                "input": ["这是一个测试文本"]
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                embedding = result['data'][0]['embedding']
                logger.info(f"✅ ZhipuAI 嵌入服务正常: 维度 {len(embedding)}")
                return True
            else:
                logger.error(f"❌ ZhipuAI API 调用失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 嵌入服务测试失败: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 嵌入服务初始化失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 初始化嵌入服务...")
    logger.info("=" * 50)
    
    success = await init_embedding_service()
    
    if success:
        logger.info("🎉 嵌入服务初始化成功！")
        logger.info("💡 现在可以开始使用向量数据库了")
    else:
        logger.error("❌ 嵌入服务初始化失败")


if __name__ == "__main__":
    asyncio.run(main())
