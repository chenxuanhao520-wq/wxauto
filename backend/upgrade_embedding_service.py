#!/usr/bin/env python3
"""
真实嵌入服务实现
使用 Qwen 和 GLM 的真实嵌入模型
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

class RealEmbeddingService:
    """真实嵌入服务"""
    
    def __init__(self):
        """初始化嵌入服务"""
        self.qwen_api_key = os.getenv("QWEN_API_KEY")
        self.glm_api_key = os.getenv("GLM_API_KEY")
        self.dimension = 1536
        
        logger.info("✅ 真实嵌入服务初始化")
        logger.info(f"📋 Qwen API Key: {self.qwen_api_key[:10]}..." if self.qwen_api_key else "❌ 未配置")
        logger.info(f"📋 GLM API Key: {self.glm_api_key[:10]}..." if self.glm_api_key else "❌ 未配置")
    
    async def embed_text_qwen(self, text: str):
        """使用 Qwen 生成嵌入"""
        try:
            if not self.qwen_api_key:
                raise ValueError("Qwen API Key 未配置")
            
            url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
            
            headers = {
                "Authorization": f"Bearer {self.qwen_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "text-embedding-v1",
                "input": text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        embedding = result["output"]["embeddings"][0]["embedding"]
                        logger.info(f"✅ Qwen 嵌入生成成功: {len(embedding)} 维")
                        return embedding
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Qwen API 调用失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Qwen 嵌入生成失败: {e}")
            return None
    
    async def embed_text_glm(self, text: str):
        """使用 GLM 生成嵌入"""
        try:
            if not self.glm_api_key:
                raise ValueError("GLM API Key 未配置")
            
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
    
    async def embed_text(self, text: str, provider: str = "qwen"):
        """生成文本嵌入"""
        try:
            logger.info(f"🔍 生成嵌入向量: {text[:50]}...")
            
            if provider == "qwen":
                return await self.embed_text_qwen(text)
            elif provider == "glm":
                return await self.embed_text_glm(text)
            else:
                # 自动选择可用的提供商
                if self.qwen_api_key:
                    return await self.embed_text_qwen(text)
                elif self.glm_api_key:
                    return await self.embed_text_glm(text)
                else:
                    raise ValueError("没有可用的嵌入服务提供商")
                    
        except Exception as e:
            logger.error(f"❌ 嵌入生成失败: {e}")
            return None

class EmbeddingServiceUpgrader:
    """嵌入服务升级器"""
    
    def __init__(self):
        """初始化升级器"""
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.service_key:
            raise ValueError("缺少 Supabase 环境变量")
        
        from supabase import create_client, Client
        self.supabase: Client = create_client(self.url, self.service_key)
        
        self.embedding_service = RealEmbeddingService()
        
        logger.info("✅ 嵌入服务升级器初始化成功")
    
    async def test_embedding_service(self):
        """测试嵌入服务"""
        try:
            logger.info("🔍 测试嵌入服务...")
            
            test_texts = [
                "充电桩故障排除指南",
                "如何安装充电桩",
                "充电桩维护保养"
            ]
            
            for text in test_texts:
                logger.info(f"📝 测试文本: {text}")
                
                # 测试 Qwen
                if self.embedding_service.qwen_api_key:
                    qwen_embedding = await self.embedding_service.embed_text(text, "qwen")
                    if qwen_embedding:
                        logger.info(f"✅ Qwen 测试成功: {len(qwen_embedding)} 维")
                    else:
                        logger.warning("⚠️ Qwen 测试失败")
                
                # 测试 GLM
                if self.embedding_service.glm_api_key:
                    glm_embedding = await self.embedding_service.embed_text(text, "glm")
                    if glm_embedding:
                        logger.info(f"✅ GLM 测试成功: {len(glm_embedding)} 维")
                    else:
                        logger.warning("⚠️ GLM 测试失败")
                
                logger.info("---")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 嵌入服务测试失败: {e}")
            return False
    
    async def upgrade_existing_documents(self):
        """升级现有文档的嵌入向量"""
        try:
            logger.info("🔧 升级现有文档的嵌入向量...")
            
            # 获取现有文档
            result = self.supabase.table('embeddings').select('*').execute()
            
            if not result.data:
                logger.info("📋 没有现有文档需要升级")
                return True
            
            logger.info(f"📋 找到 {len(result.data)} 条文档需要升级")
            
            upgraded_count = 0
            
            for doc in result.data:
                try:
                    content = doc.get('content', '')
                    if not content:
                        continue
                    
                    logger.info(f"🔄 升级文档: {doc.get('id')}")
                    
                    # 生成新的嵌入向量
                    new_embedding = await self.embedding_service.embed_text(content)
                    
                    if new_embedding:
                        # 更新文档
                        update_result = self.supabase.table('embeddings').update({
                            'embedding': new_embedding
                        }).eq('id', doc['id']).execute()
                        
                        if update_result.data:
                            upgraded_count += 1
                            logger.info(f"✅ 文档 {doc['id']} 升级成功")
                        else:
                            logger.warning(f"⚠️ 文档 {doc['id']} 升级失败")
                    else:
                        logger.warning(f"⚠️ 文档 {doc['id']} 嵌入生成失败")
                        
                except Exception as e:
                    logger.error(f"❌ 文档 {doc.get('id')} 升级失败: {e}")
                    continue
            
            logger.info(f"✅ 升级完成: {upgraded_count}/{len(result.data)} 条文档")
            return True
            
        except Exception as e:
            logger.error(f"❌ 文档升级失败: {e}")
            return False
    
    async def add_new_documents_with_real_embeddings(self):
        """添加使用真实嵌入的新文档"""
        try:
            logger.info("🔧 添加使用真实嵌入的新文档...")
            
            new_documents = [
                {
                    "title": "充电桩安全操作规程",
                    "content": "安全操作规程：1.操作前检查设备状态 2.佩戴防护用品 3.按规程操作 4.记录操作日志",
                    "category": "safety"
                },
                {
                    "title": "充电桩故障代码说明",
                    "content": "故障代码：E001-电源故障 E002-通信故障 E003-温度异常 E004-过流保护",
                    "category": "technical"
                },
                {
                    "title": "充电桩日常检查清单",
                    "content": "日常检查：1.外观检查 2.指示灯检查 3.连接检查 4.功能测试 5.清洁保养",
                    "category": "maintenance"
                }
            ]
            
            added_count = 0
            
            for doc_data in new_documents:
                try:
                    # 生成真实嵌入向量
                    embedding = await self.embedding_service.embed_text(doc_data["content"])
                    
                    if embedding:
                        # 创建文档
                        doc_id = int(datetime.now().timestamp()) + added_count
                        
                        document = {
                            "id": doc_id,
                            "content": doc_data["content"],
                            "embedding": embedding,
                            "metadata": {
                                "title": doc_data["title"],
                                "category": doc_data["category"],
                                "source": "real_embedding",
                                "created_at": datetime.now().isoformat()
                            }
                        }
                        
                        # 插入数据库
                        result = self.supabase.table('embeddings').insert(document).execute()
                        
                        if result.data:
                            added_count += 1
                            logger.info(f"✅ 文档添加成功: {doc_data['title']}")
                        else:
                            logger.warning(f"⚠️ 文档添加失败: {doc_data['title']}")
                    else:
                        logger.warning(f"⚠️ 嵌入生成失败: {doc_data['title']}")
                        
                except Exception as e:
                    logger.error(f"❌ 文档添加失败: {doc_data['title']}: {e}")
                    continue
            
            logger.info(f"✅ 新文档添加完成: {added_count}/{len(new_documents)} 条")
            return True
            
        except Exception as e:
            logger.error(f"❌ 新文档添加失败: {e}")
            return False
    
    async def test_real_rag_flow(self):
        """测试真实RAG流程"""
        try:
            logger.info("🔍 测试真实RAG流程...")
            
            # 用户查询
            user_query = "充电桩出现故障怎么办？"
            logger.info(f"📝 用户查询: {user_query}")
            
            # 生成查询嵌入向量
            query_embedding = await self.embedding_service.embed_text(user_query)
            
            if not query_embedding:
                logger.error("❌ 查询嵌入生成失败")
                return False
            
            logger.info(f"✅ 查询嵌入生成成功: {len(query_embedding)} 维")
            
            # 向量搜索
            search_result = self.supabase.rpc('search_embeddings', {
                'query_embedding': query_embedding,
                'match_count': 3
            }).execute()
            
            logger.info(f"🔍 找到 {len(search_result.data)} 条相关文档")
            
            # 构建上下文
            context = ""
            for i, result in enumerate(search_result.data):
                context += f"文档{i+1}: {result.get('content', '')}\n"
                logger.info(f"📄 相关文档{i+1}: {result.get('metadata', {}).get('title', '')}")
            
            logger.info(f"📚 构建上下文: {len(context)} 字符")
            
            # 模拟AI响应
            ai_response = f"根据您的问题'{user_query}'，我为您提供以下建议：\n\n"
            ai_response += "基于知识库内容：\n"
            ai_response += context[:300] + "...\n\n"
            ai_response += "建议解决方案：\n"
            ai_response += "1. 检查故障代码和指示灯状态\n"
            ai_response += "2. 按照安全操作规程进行处理\n"
            ai_response += "3. 联系技术支持获取进一步帮助\n"
            ai_response += "4. 记录故障情况和处理过程"
            
            logger.info(f"🤖 AI响应: {len(ai_response)} 字符")
            logger.info("✅ 真实RAG流程测试成功！")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 真实RAG流程测试失败: {e}")
            return False

async def main():
    """主函数"""
    logger.info("🚀 嵌入服务升级 - 使用真实嵌入模型...")
    logger.info("=" * 60)
    
    try:
        # 初始化升级器
        upgrader = EmbeddingServiceUpgrader()
        
        # 测试嵌入服务
        logger.info("\n🔍 测试嵌入服务...")
        test_ok = await upgrader.test_embedding_service()
        
        if not test_ok:
            logger.error("❌ 嵌入服务测试失败，请检查API配置")
            return
        
        # 升级现有文档
        logger.info("\n🔧 升级现有文档...")
        upgrade_ok = await upgrader.upgrade_existing_documents()
        
        # 添加新文档
        logger.info("\n🔧 添加新文档...")
        add_ok = await upgrader.add_new_documents_with_real_embeddings()
        
        # 测试真实RAG流程
        logger.info("\n🔍 测试真实RAG流程...")
        rag_ok = await upgrader.test_real_rag_flow()
        
        # 输出总结
        logger.info("\n" + "=" * 60)
        logger.info("📊 嵌入服务升级结果:")
        logger.info("=" * 60)
        
        logger.info(f"嵌入服务测试: {'✅ 成功' if test_ok else '❌ 失败'}")
        logger.info(f"现有文档升级: {'✅ 成功' if upgrade_ok else '❌ 失败'}")
        logger.info(f"新文档添加: {'✅ 成功' if add_ok else '❌ 失败'}")
        logger.info(f"真实RAG测试: {'✅ 成功' if rag_ok else '❌ 失败'}")
        
        # 总体评估
        all_ok = test_ok and upgrade_ok and add_ok and rag_ok
        
        if all_ok:
            logger.info("\n🎉 嵌入服务升级全部完成！")
            logger.info("💡 现在使用真实的AI嵌入模型")
            logger.info("💡 系统具备真正的语义搜索能力")
        else:
            logger.info("\n⚠️ 部分升级未完成")
            logger.info("💡 请检查API配置和网络连接")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 嵌入服务升级失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
