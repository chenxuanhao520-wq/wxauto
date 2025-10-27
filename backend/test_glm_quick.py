#!/usr/bin/env python3
"""
GLM 嵌入服务快速测试
在修改数据库结构后，快速验证 GLM 嵌入服务是否正常工作
"""

import os
import sys
import asyncio
import logging
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GLMQuickTester:
    """GLM 快速测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.glm_api_key = os.getenv("GLM_API_KEY")
        
        if not all([self.url, self.service_key, self.glm_api_key]):
            raise ValueError("缺少必要的环境变量")
        
        from supabase import create_client, Client
        self.supabase: Client = create_client(self.url, self.service_key)
        
        logger.info("✅ GLM 快速测试器初始化成功")
    
    async def test_glm_api(self):
        """测试 GLM API"""
        try:
            logger.info("🔍 测试 GLM API...")
            
            url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
            headers = {
                "Authorization": f"Bearer {self.glm_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "embedding-2",
                "input": "测试文本"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        embedding = result["data"][0]["embedding"]
                        logger.info(f"✅ GLM API 测试成功: {len(embedding)} 维")
                        return embedding
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ GLM API 测试失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ GLM API 测试失败: {e}")
            return None
    
    async def test_database_structure(self):
        """测试数据库结构"""
        try:
            logger.info("🔍 测试数据库结构...")
            
            # 测试插入 1024 维向量
            test_embedding = [0.1] * 1024
            test_doc = {
                "id": int(datetime.now().timestamp()),
                "content": "测试文档",
                "embedding": test_embedding,
                "metadata": {"title": "测试", "source": "test"}
            }
            
            result = self.supabase.table('embeddings').insert(test_doc).execute()
            
            if result.data:
                logger.info("✅ 数据库结构测试成功 - 可以插入 1024 维向量")
                
                # 清理测试数据
                self.supabase.table('embeddings').delete().eq('id', test_doc['id']).execute()
                logger.info("🧹 测试数据已清理")
                return True
            else:
                logger.error("❌ 数据库结构测试失败 - 无法插入 1024 维向量")
                return False
                
        except Exception as e:
            logger.error(f"❌ 数据库结构测试失败: {e}")
            return False
    
    async def test_vector_search(self):
        """测试向量搜索"""
        try:
            logger.info("🔍 测试向量搜索...")
            
            # 使用测试向量搜索
            test_vector = [0.1] * 1024
            
            result = self.supabase.rpc('search_embeddings', {
                'query_embedding': test_vector,
                'match_count': 1
            }).execute()
            
            if result.data is not None:
                logger.info("✅ 向量搜索测试成功")
                return True
            else:
                logger.error("❌ 向量搜索测试失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 向量搜索测试失败: {e}")
            return False
    
    async def quick_build_test(self):
        """快速构建测试"""
        try:
            logger.info("🔧 快速构建测试...")
            
            # 生成真实嵌入向量
            test_embedding = await self.test_glm_api()
            if not test_embedding:
                return False
            
            # 插入测试文档
            test_doc = {
                "id": int(datetime.now().timestamp()),
                "content": "充电桩故障排除：检查电源、重启设备、联系技术支持",
                "embedding": test_embedding,
                "metadata": {
                    "title": "充电桩故障排除",
                    "category": "troubleshooting",
                    "source": "glm_test"
                }
            }
            
            result = self.supabase.table('embeddings').insert(test_doc).execute()
            
            if result.data:
                logger.info("✅ 测试文档插入成功")
                
                # 测试搜索
                search_result = self.supabase.rpc('search_embeddings', {
                    'query_embedding': test_embedding,
                    'match_count': 1
                }).execute()
                
                if search_result.data:
                    logger.info("✅ 向量搜索成功")
                    logger.info(f"📄 搜索结果: {search_result.data[0].get('metadata', {}).get('title', '未知')}")
                    
                    # 清理测试数据
                    self.supabase.table('embeddings').delete().eq('id', test_doc['id']).execute()
                    logger.info("🧹 测试数据已清理")
                    
                    return True
                else:
                    logger.error("❌ 向量搜索失败")
                    return False
            else:
                logger.error("❌ 测试文档插入失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 快速构建测试失败: {e}")
            return False

async def main():
    """主函数"""
    logger.info("🚀 GLM 嵌入服务快速测试...")
    logger.info("=" * 50)
    
    try:
        # 初始化测试器
        tester = GLMQuickTester()
        
        # 测试 GLM API
        logger.info("\n🔍 测试 GLM API...")
        api_ok = await tester.test_glm_api() is not None
        
        # 测试数据库结构
        logger.info("\n🔍 测试数据库结构...")
        db_ok = await tester.test_database_structure()
        
        # 测试向量搜索
        logger.info("\n🔍 测试向量搜索...")
        search_ok = await tester.test_vector_search()
        
        # 快速构建测试
        logger.info("\n🔧 快速构建测试...")
        build_ok = await tester.quick_build_test()
        
        # 输出总结
        logger.info("\n" + "=" * 50)
        logger.info("📊 GLM 嵌入服务测试结果:")
        logger.info("=" * 50)
        
        logger.info(f"GLM API 测试: {'✅ 成功' if api_ok else '❌ 失败'}")
        logger.info(f"数据库结构测试: {'✅ 成功' if db_ok else '❌ 失败'}")
        logger.info(f"向量搜索测试: {'✅ 成功' if search_ok else '❌ 失败'}")
        logger.info(f"快速构建测试: {'✅ 成功' if build_ok else '❌ 失败'}")
        
        # 总体评估
        all_ok = api_ok and db_ok and search_ok and build_ok
        
        if all_ok:
            logger.info("\n🎉 GLM 嵌入服务测试全部通过！")
            logger.info("💡 可以运行完整的知识库构建")
            logger.info("💡 运行命令: python3 build_glm_knowledge_base.py")
        else:
            logger.info("\n⚠️ 部分测试未通过")
            if not api_ok:
                logger.info("💡 请检查 GLM API Key")
            if not db_ok:
                logger.info("💡 请按照 GLM_UPGRADE_GUIDE.md 修改数据库结构")
            if not search_ok:
                logger.info("💡 请检查 search_embeddings 函数")
        
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ GLM 嵌入服务测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
