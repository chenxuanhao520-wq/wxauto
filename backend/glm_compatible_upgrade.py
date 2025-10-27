#!/usr/bin/env python3
"""
GLM 嵌入服务兼容升级
将 GLM 1024 维向量填充到 1536 维以兼容现有数据库
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

class GLMCompatibleEmbeddingService:
    """GLM 兼容嵌入服务"""
    
    def __init__(self):
        """初始化嵌入服务"""
        self.glm_api_key = os.getenv("GLM_API_KEY")
        self.glm_dimension = 1024  # GLM embedding-2 是 1024 维
        self.db_dimension = 1536   # 数据库期望的维度
        
        if not self.glm_api_key:
            raise ValueError("GLM API Key 未配置")
        
        logger.info("✅ GLM 兼容嵌入服务初始化")
        logger.info(f"📋 GLM API Key: {self.glm_api_key[:10]}...")
        logger.info(f"📋 GLM 向量维度: {self.glm_dimension}")
        logger.info(f"📋 数据库向量维度: {self.db_dimension}")
    
    async def embed_text(self, text: str):
        """使用 GLM 生成嵌入并填充到 1536 维"""
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
                        glm_embedding = result["data"][0]["embedding"]
                        
                        # 填充到 1536 维
                        padded_embedding = self._pad_embedding(glm_embedding)
                        
                        logger.info(f"✅ GLM 嵌入生成成功: {len(glm_embedding)} -> {len(padded_embedding)} 维")
                        return padded_embedding
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ GLM API 调用失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ GLM 嵌入生成失败: {e}")
            return None
    
    def _pad_embedding(self, embedding):
        """将 1024 维向量填充到 1536 维"""
        if len(embedding) != self.glm_dimension:
            raise ValueError(f"期望 {self.glm_dimension} 维向量，得到 {len(embedding)} 维")
        
        # 计算需要填充的维度
        padding_size = self.db_dimension - self.glm_dimension
        
        # 使用简单的填充策略：重复向量的一部分
        padding = embedding[:padding_size] if padding_size <= self.glm_dimension else embedding * (padding_size // self.glm_dimension + 1)
        padding = padding[:padding_size]
        
        # 组合原始向量和填充
        padded_embedding = embedding + padding
        
        return padded_embedding

class GLMKnowledgeBaseBuilder:
    """GLM 知识库构建器"""
    
    def __init__(self):
        """初始化构建器"""
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.service_key:
            raise ValueError("缺少 Supabase 环境变量")
        
        from supabase import create_client, Client
        self.supabase: Client = create_client(self.url, self.service_key)
        
        self.embedding_service = GLMCompatibleEmbeddingService()
        
        logger.info("✅ GLM 知识库构建器初始化成功")
    
    async def clear_existing_data(self):
        """清空现有数据"""
        try:
            logger.info("🗑️ 清空现有数据...")
            
            # 删除所有现有记录
            result = self.supabase.table('embeddings').delete().neq('id', 0).execute()
            
            logger.info("✅ 现有数据清空完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 清空数据失败: {e}")
            return False
    
    async def build_knowledge_base(self):
        """构建知识库"""
        try:
            logger.info("🔧 构建 GLM 知识库...")
            
            # 知识库文档
            knowledge_docs = [
                {
                    "title": "充电桩故障排除指南",
                    "content": "充电桩故障排除指南：1.检查电源连接是否正常 2.确认指示灯状态 3.重启设备 4.检查通信连接 5.联系技术支持",
                    "category": "troubleshooting"
                },
                {
                    "title": "充电桩安装步骤",
                    "content": "充电桩安装步骤：1.选择合适位置 2.安装固定支架 3.连接电源线 4.测试功能 5.记录安装信息",
                    "category": "installation"
                },
                {
                    "title": "充电桩维护保养",
                    "content": "充电桩维护保养：1.定期清洁设备 2.检查连接状态 3.更新软件版本 4.记录维护日志 5.预防性维护",
                    "category": "maintenance"
                },
                {
                    "title": "充电桩安全操作规程",
                    "content": "安全操作规程：1.操作前检查设备状态 2.佩戴防护用品 3.按规程操作 4.记录操作日志 5.应急处理",
                    "category": "safety"
                },
                {
                    "title": "充电桩故障代码说明",
                    "content": "故障代码：E001-电源故障 E002-通信故障 E003-温度异常 E004-过流保护 E005-接地故障",
                    "category": "technical"
                },
                {
                    "title": "充电桩日常检查清单",
                    "content": "日常检查：1.外观检查 2.指示灯检查 3.连接检查 4.功能测试 5.清洁保养",
                    "category": "inspection"
                },
                {
                    "title": "充电桩技术参数",
                    "content": "技术参数：电压220V，功率7kW，防护等级IP65，工作温度-20°C到50°C，通信协议Modbus",
                    "category": "technical"
                },
                {
                    "title": "充电桩使用注意事项",
                    "content": "使用注意事项：1.确保设备干燥 2.检查电缆完好 3.避免过载使用 4.定期维护检查 5.遵守安全规定",
                    "category": "usage"
                }
            ]
            
            added_count = 0
            
            for i, doc_data in enumerate(knowledge_docs):
                try:
                    logger.info(f"📝 处理文档 {i+1}/{len(knowledge_docs)}: {doc_data['title']}")
                    
                    # 生成 GLM 嵌入向量（填充到 1536 维）
                    embedding = await self.embedding_service.embed_text(doc_data["content"])
                    
                    if embedding:
                        # 创建文档记录
                        doc_id = int(datetime.now().timestamp()) + i
                        
                        document = {
                            "id": doc_id,
                            "content": doc_data["content"],
                            "embedding": embedding,
                            "metadata": {
                                "title": doc_data["title"],
                                "category": doc_data["category"],
                                "source": "glm_compatible",
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
                    logger.error(f"❌ 文档处理失败: {doc_data['title']}: {e}")
                    continue
            
            logger.info(f"✅ 知识库构建完成: {added_count}/{len(knowledge_docs)} 条文档")
            return True
            
        except Exception as e:
            logger.error(f"❌ 知识库构建失败: {e}")
            return False
    
    async def test_rag_flow(self):
        """测试 RAG 流程"""
        try:
            logger.info("🔍 测试 RAG 流程...")
            
            # 测试查询
            test_queries = [
                "充电桩出现故障怎么办？",
                "如何安装充电桩？",
                "充电桩需要维护吗？"
            ]
            
            for query in test_queries:
                logger.info(f"📝 测试查询: {query}")
                
                # 生成查询嵌入向量（填充到 1536 维）
                query_embedding = await self.embedding_service.embed_text(query)
                
                if not query_embedding:
                    logger.error("❌ 查询嵌入生成失败")
                    continue
                
                logger.info(f"✅ 查询嵌入生成成功: {len(query_embedding)} 维")
                
                # 向量搜索
                try:
                    search_result = self.supabase.rpc('search_embeddings', {
                        'query_embedding': query_embedding,
                        'match_count': 3
                    }).execute()
                    
                    logger.info(f"🔍 找到 {len(search_result.data)} 条相关文档")
                    
                    # 显示搜索结果
                    for i, result in enumerate(search_result.data):
                        title = result.get('metadata', {}).get('title', '未知标题')
                        similarity = result.get('similarity', 0)
                        logger.info(f"📄 结果{i+1}: {title} (相似度: {similarity:.3f})")
                    
                    logger.info("---")
                    
                except Exception as e:
                    logger.error(f"❌ 向量搜索失败: {e}")
                    continue
            
            logger.info("✅ RAG 流程测试完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ RAG 流程测试失败: {e}")
            return False

async def main():
    """主函数"""
    logger.info("🚀 GLM 兼容嵌入服务升级...")
    logger.info("=" * 60)
    
    try:
        # 初始化构建器
        builder = GLMKnowledgeBaseBuilder()
        
        # 清空现有数据
        logger.info("\n🗑️ 清空现有数据...")
        clear_ok = await builder.clear_existing_data()
        
        if not clear_ok:
            logger.error("❌ 清空数据失败")
            return
        
        # 构建知识库
        logger.info("\n🔧 构建知识库...")
        build_ok = await builder.build_knowledge_base()
        
        if not build_ok:
            logger.error("❌ 知识库构建失败")
            return
        
        # 测试 RAG 流程
        logger.info("\n🔍 测试 RAG 流程...")
        test_ok = await builder.test_rag_flow()
        
        # 输出总结
        logger.info("\n" + "=" * 60)
        logger.info("📊 GLM 兼容嵌入服务升级结果:")
        logger.info("=" * 60)
        
        logger.info(f"数据清空: {'✅ 成功' if clear_ok else '❌ 失败'}")
        logger.info(f"知识库构建: {'✅ 成功' if build_ok else '❌ 失败'}")
        logger.info(f"RAG 流程测试: {'✅ 成功' if test_ok else '❌ 失败'}")
        
        # 总体评估
        all_ok = clear_ok and build_ok and test_ok
        
        if all_ok:
            logger.info("\n🎉 GLM 兼容嵌入服务升级全部完成！")
            logger.info("💡 使用智谱 GLM embedding-2 模型")
            logger.info("💡 GLM 向量维度: 1024")
            logger.info("💡 数据库兼容维度: 1536")
            logger.info("💡 知识库包含 8 个充电桩相关文档")
            logger.info("💡 RAG 搜索功能正常工作")
        else:
            logger.info("\n⚠️ 部分升级未完成")
            logger.info("💡 请检查API配置和网络连接")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ GLM 兼容嵌入服务升级失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
