#!/usr/bin/env python3
"""
数据库迁移脚本 - 支持 GLM 1024 维向量
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

class DatabaseMigrator:
    """数据库迁移器"""
    
    def __init__(self):
        """初始化迁移器"""
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.service_key:
            raise ValueError("缺少 Supabase 环境变量")
        
        from supabase import create_client, Client
        self.supabase: Client = create_client(self.url, self.service_key)
        
        logger.info("✅ 数据库迁移器初始化成功")
    
    async def migrate_to_glm_dimensions(self):
        """迁移到 GLM 1024 维向量"""
        try:
            logger.info("🔧 开始数据库迁移 - 支持 GLM 1024 维向量...")
            
            # 1. 删除现有的 embeddings 表
            logger.info("🗑️ 删除现有 embeddings 表...")
            try:
                drop_result = self.supabase.rpc('exec_sql', {
                    'sql': 'DROP TABLE IF EXISTS embeddings CASCADE;'
                }).execute()
                logger.info("✅ 现有表删除成功")
            except Exception as e:
                logger.warning(f"⚠️ 删除表失败（可能不存在）: {e}")
            
            # 2. 创建新的 embeddings 表（1024 维）
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
            
            try:
                create_result = self.supabase.rpc('exec_sql', {
                    'sql': create_table_sql
                }).execute()
                logger.info("✅ 新表创建成功")
            except Exception as e:
                logger.error(f"❌ 创建表失败: {e}")
                return False
            
            # 3. 创建向量索引
            logger.info("🔨 创建向量索引...")
            
            create_index_sql = """
            CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            """
            
            try:
                index_result = self.supabase.rpc('exec_sql', {
                    'sql': create_index_sql
                }).execute()
                logger.info("✅ 向量索引创建成功")
            except Exception as e:
                logger.warning(f"⚠️ 创建索引失败: {e}")
            
            # 4. 更新 search_embeddings 函数
            logger.info("🔨 更新 search_embeddings 函数...")
            
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
            
            try:
                function_result = self.supabase.rpc('exec_sql', {
                    'sql': create_function_sql
                }).execute()
                logger.info("✅ search_embeddings 函数更新成功")
            except Exception as e:
                logger.error(f"❌ 更新函数失败: {e}")
                return False
            
            logger.info("✅ 数据库迁移完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库迁移失败: {e}")
            return False
    
    async def verify_migration(self):
        """验证迁移结果"""
        try:
            logger.info("🔍 验证迁移结果...")
            
            # 检查表结构
            logger.info("📋 检查表结构...")
            try:
                result = self.supabase.table('embeddings').select('*').limit(1).execute()
                logger.info("✅ embeddings 表存在")
            except Exception as e:
                logger.error(f"❌ embeddings 表不存在: {e}")
                return False
            
            # 检查函数
            logger.info("📋 检查 search_embeddings 函数...")
            try:
                # 使用测试向量调用函数
                test_vector = [0.1] * 1024
                result = self.supabase.rpc('search_embeddings', {
                    'query_embedding': test_vector,
                    'match_count': 1
                }).execute()
                logger.info("✅ search_embeddings 函数正常")
            except Exception as e:
                logger.error(f"❌ search_embeddings 函数异常: {e}")
                return False
            
            logger.info("✅ 迁移验证成功！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移验证失败: {e}")
            return False

async def main():
    """主函数"""
    logger.info("🚀 数据库迁移 - 支持 GLM 1024 维向量...")
    logger.info("=" * 60)
    
    try:
        # 初始化迁移器
        migrator = DatabaseMigrator()
        
        # 执行迁移
        logger.info("\n🔧 执行数据库迁移...")
        migrate_ok = await migrator.migrate_to_glm_dimensions()
        
        if not migrate_ok:
            logger.error("❌ 数据库迁移失败")
            return
        
        # 验证迁移
        logger.info("\n🔍 验证迁移结果...")
        verify_ok = await migrator.verify_migration()
        
        # 输出总结
        logger.info("\n" + "=" * 60)
        logger.info("📊 数据库迁移结果:")
        logger.info("=" * 60)
        
        logger.info(f"数据库迁移: {'✅ 成功' if migrate_ok else '❌ 失败'}")
        logger.info(f"迁移验证: {'✅ 成功' if verify_ok else '❌ 失败'}")
        
        # 总体评估
        all_ok = migrate_ok and verify_ok
        
        if all_ok:
            logger.info("\n🎉 数据库迁移全部完成！")
            logger.info("💡 现在支持 GLM 1024 维向量")
            logger.info("💡 可以正常使用 GLM 嵌入服务")
            logger.info("💡 向量搜索功能已就绪")
        else:
            logger.info("\n⚠️ 迁移未完全成功")
            logger.info("💡 请检查数据库权限和网络连接")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
