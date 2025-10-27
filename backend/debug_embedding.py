#!/usr/bin/env python3
"""
调试 ZhipuAI API 调用
"""

import os
import sys
import asyncio
import logging
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def debug_zhipu_api():
    """调试 ZhipuAI API"""
    try:
        logger.info("🔍 调试 ZhipuAI API...")
        
        zhipu_key = os.getenv("ZHIPUAI_API_KEY")
        if not zhipu_key:
            logger.error("❌ 缺少 ZHIPUAI_API_KEY")
            return False
        
        logger.info(f"📋 API Key: {zhipu_key[:10]}...{zhipu_key[-10:]}")
        
        # 测试不同的 API 端点
        api_endpoints = [
            {
                "name": "text2vec-large-chinese",
                "url": "https://open.bigmodel.cn/api/paas/v4/embeddings",
                "data": {
                    "model": "text2vec-large-chinese",
                    "input": ["这是一个测试文本"]
                }
            },
            {
                "name": "text2vec-base-chinese", 
                "url": "https://open.bigmodel.cn/api/paas/v4/embeddings",
                "data": {
                    "model": "text2vec-base-chinese",
                    "input": ["这是一个测试文本"]
                }
            },
            {
                "name": "text2vec",
                "url": "https://open.bigmodel.cn/api/paas/v4/embeddings", 
                "data": {
                    "model": "text2vec",
                    "input": ["这是一个测试文本"]
                }
            }
        ]
        
        headers = {
            "Authorization": f"Bearer {zhipu_key}",
            "Content-Type": "application/json"
        }
        
        for endpoint in api_endpoints:
            logger.info(f"🧪 测试模型: {endpoint['name']}")
            
            try:
                response = requests.post(
                    endpoint['url'], 
                    headers=headers, 
                    json=endpoint['data'],
                    timeout=10
                )
                
                logger.info(f"📡 响应状态: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result['data'][0]['embedding']
                    logger.info(f"✅ {endpoint['name']} 成功: 维度 {len(embedding)}")
                    return True
                else:
                    logger.warning(f"⚠️ {endpoint['name']} 失败: {response.status_code}")
                    logger.warning(f"   响应内容: {response.text}")
                    
            except Exception as e:
                logger.error(f"❌ {endpoint['name']} 异常: {e}")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ API 调试失败: {e}")
        return False


async def test_simple_embedding():
    """测试简单的嵌入功能"""
    try:
        logger.info("🔍 测试简单嵌入功能...")
        
        # 使用 OpenAI 风格的 API（如果可用）
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your_openai_api_key":
            logger.info("🧪 测试 OpenAI 嵌入...")
            
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "text-embedding-3-small",
                "input": "这是一个测试文本"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result['data'][0]['embedding']
                logger.info(f"✅ OpenAI 嵌入成功: 维度 {len(embedding)}")
                return True
            else:
                logger.warning(f"⚠️ OpenAI 嵌入失败: {response.status_code}")
        
        # 使用 Qwen 嵌入（如果可用）
        qwen_key = os.getenv("QWEN_API_KEY")
        if qwen_key and qwen_key != "your_qwen_api_key":
            logger.info("🧪 测试 Qwen 嵌入...")
            
            headers = {
                "Authorization": f"Bearer {qwen_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "text-embedding-v2",
                "input": {
                    "texts": ["这是一个测试文本"]
                }
            }
            
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result['output']['embeddings'][0]['embedding']
                logger.info(f"✅ Qwen 嵌入成功: 维度 {len(embedding)}")
                return True
            else:
                logger.warning(f"⚠️ Qwen 嵌入失败: {response.status_code}")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ 简单嵌入测试失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 调试嵌入服务...")
    logger.info("=" * 50)
    
    # 调试 ZhipuAI API
    zhipu_ok = await debug_zhipu_api()
    
    # 测试其他嵌入服务
    other_ok = await test_simple_embedding()
    
    # 输出总结
    logger.info("\n" + "=" * 50)
    logger.info("📊 嵌入服务调试结果:")
    logger.info("=" * 50)
    
    if zhipu_ok:
        logger.info("✅ ZhipuAI 嵌入服务正常")
    else:
        logger.warning("⚠️ ZhipuAI 嵌入服务有问题")
    
    if other_ok:
        logger.info("✅ 其他嵌入服务正常")
    else:
        logger.warning("⚠️ 其他嵌入服务有问题")
    
    logger.info("=" * 50)
    
    if zhipu_ok or other_ok:
        logger.info("🎉 至少有一个嵌入服务可用！")
    else:
        logger.warning("⚠️ 所有嵌入服务都有问题")


if __name__ == "__main__":
    asyncio.run(main())
