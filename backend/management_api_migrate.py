#!/usr/bin/env python3
"""
通过 Supabase Management API 修改数据库结构
支持 GLM 1024 维向量
"""

import os
import sys
import asyncio
import logging
import aiohttp
import json
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

class SupabaseManagementMigrator:
    """Supabase Management API 迁移器"""
    
    def __init__(self):
        """初始化迁移器"""
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.service_key:
            raise ValueError("缺少 Supabase 环境变量")
        
        logger.info("✅ Supabase Management API 迁移器初始化成功")
    
    async def execute_sql_via_rest(self, sql_query):
        """通过 REST API 执行 SQL"""
        try:
            # 尝试通过 SQL Editor API
            headers = {
                "Authorization": f"Bearer {self.service_key}",
                "Content-Type": "application/json",
                "apikey": self.service_key
            }
            
            # 尝试不同的 API 端点
            endpoints = [
                f"{self.url}/rest/v1/rpc/exec_sql",
                f"{self.url}/rest/v1/rpc/execute_sql",
                f"{self.url}/rest/v1/rpc/run_sql",
                f"{self.url}/sql/v1/query"
            ]
            
            for endpoint in endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            endpoint,
                            headers=headers,
                            json={"sql": sql_query}
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                logger.info(f"✅ SQL 执行成功: {endpoint}")
                                return True
                            else:
                                logger.debug(f"⚠️ 端点 {endpoint} 失败: {response.status}")
                except Exception as e:
                    logger.debug(f"⚠️ 端点 {endpoint} 异常: {e}")
                    continue
            
            logger.error("❌ 所有 SQL 执行端点都失败")
            return False
            
        except Exception as e:
            logger.error(f"❌ SQL 执行失败: {e}")
            return False
    
    async def migrate_via_direct_api(self):
        """通过直接 API 调用迁移"""
        try:
            logger.info("🔧 通过直接 API 调用迁移数据库...")
            
            # 1. 删除现有表
            logger.info("🗑️ 删除现有 embeddings 表...")
            
            # 尝试直接删除表
            try:
                from supabase import create_client, Client
                supabase: Client = create_client(self.url, self.service_key)
                
                # 先清空表
                result = supabase.table('embeddings').delete().neq('id', 0).execute()
                logger.info("✅ 现有数据清空成功")
                
                # 尝试删除表结构（通过 REST API）
                delete_sql = "DROP TABLE IF EXISTS embeddings CASCADE;"
                await self.execute_sql_via_rest(delete_sql)
                
            except Exception as e:
                logger.warning(f"⚠️ 删除表失败: {e}")
            
            # 2. 创建新表
            logger.info("🔨 创建新的 embeddings 表（1024 维）...")
            
            create_table_sql = """
            CREATE TABLE embeddings (
                id BIGINT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(1024) NOT NULL,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            
            # 尝试通过 REST API 创建表
            table_created = await self.execute_sql_via_rest(create_table_sql)
            
            if not table_created:
                logger.warning("⚠️ 通过 API 创建表失败，尝试其他方法")
                # 这里可以添加其他创建表的方法
                return False
            
            # 3. 创建搜索函数
            logger.info("🔨 创建 search_embeddings 函数...")
            
            create_function_sql = """
            CREATE OR REPLACE FUNCTION search_embeddings(
                query_embedding vector(1024),
                match_count int DEFAULT 5,
                similarity_threshold float DEFAULT 0.7
            )
            RETURNS TABLE (
                id BIGINT,
                content TEXT,
                metadata JSONB,
                similarity FLOAT
            )
            LANGUAGE SQL STABLE
            AS $$
                SELECT 
                    embeddings.id,
                    embeddings.content,
                    embeddings.metadata,
                    1 - (embeddings.embedding <=> query_embedding) AS similarity
                FROM embeddings
                WHERE 1 - (embeddings.embedding <=> query_embedding) > similarity_threshold
                ORDER BY embeddings.embedding <=> query_embedding
                LIMIT match_count;
            $$;
            """
            
            function_created = await self.execute_sql_via_rest(create_function_sql)
            
            if function_created:
                logger.info("✅ 数据库结构迁移完成！")
                return True
            else:
                logger.error("❌ 函数创建失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 数据库迁移失败: {e}")
            return False
    
    async def create_glm_knowledge_base(self):
        """创建 GLM 知识库"""
        try:
            logger.info("🔧 创建 GLM 知识库...")
            
            # 导入 GLM 嵌入服务
            from glm_embedding_service import GLMEmbeddingService
            
            embedding_service = GLMEmbeddingService()
            
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
                }
            ]
            
            from supabase import create_client, Client
            supabase: Client = create_client(self.url, self.service_key)
            
            added_count = 0
            
            for i, doc_data in enumerate(knowledge_docs):
                try:
                    logger.info(f"📝 处理文档 {i+1}/{len(knowledge_docs)}: {doc_data['title']}")
                    
                    # 生成 GLM 嵌入向量
                    embedding = await embedding_service.embed_text(doc_data["content"])
                    
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
                                "source": "glm_knowledge_base",
                                "created_at": datetime.now().isoformat()
                            }
                        }
                        
                        # 插入数据库
                        result = supabase.table('embeddings').insert(document).execute()
                        
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

async def main():
    """主函数"""
    logger.info("🚀 通过 Supabase Management API 迁移数据库...")
    logger.info("=" * 60)
    
    try:
        # 初始化迁移器
        migrator = SupabaseManagementMigrator()
        
        # 执行迁移
        logger.info("\n🔧 执行数据库迁移...")
        migrate_ok = await migrator.migrate_via_direct_api()
        
        if migrate_ok:
            # 创建知识库
            logger.info("\n🔧 创建 GLM 知识库...")
            kb_ok = await migrator.create_glm_knowledge_base()
            
            # 输出总结
            logger.info("\n" + "=" * 60)
            logger.info("📊 数据库迁移结果:")
            logger.info("=" * 60)
            
            logger.info(f"数据库迁移: {'✅ 成功' if migrate_ok else '❌ 失败'}")
            logger.info(f"知识库构建: {'✅ 成功' if kb_ok else '❌ 失败'}")
            
            if migrate_ok and kb_ok:
                logger.info("\n🎉 GLM 嵌入服务升级全部完成！")
                logger.info("💡 使用智谱 GLM embedding-2 模型")
                logger.info("💡 向量维度: 1024")
                logger.info("💡 知识库构建完成")
            else:
                logger.info("\n⚠️ 部分升级未完成")
        else:
            logger.error("❌ 数据库迁移失败")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
