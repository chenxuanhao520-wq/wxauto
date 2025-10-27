#!/usr/bin/env python3
"""
Supabase 数据库初始化脚本
创建必要的表和 pgvector 扩展
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


async def init_database():
    """初始化数据库表结构"""
    try:
        from supabase import create_client, Client
        
        logger.info("🔍 开始初始化 Supabase 数据库...")
        
        # 获取环境变量
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not service_key:
            logger.error("❌ 缺少 Supabase 环境变量")
            return False
        
        # 创建客户端（使用 service role key 以获得更多权限）
        supabase: Client = create_client(url, service_key)
        
        logger.info("✅ Supabase 客户端创建成功")
        
        # 1. 启用 pgvector 扩展
        logger.info("🔧 启用 pgvector 扩展...")
        try:
            # 注意：这需要在 Supabase Dashboard 的 SQL Editor 中手动执行
            logger.info("💡 请在 Supabase Dashboard 的 SQL Editor 中执行以下 SQL:")
            logger.info("   CREATE EXTENSION IF NOT EXISTS vector;")
            logger.info("   然后按 Enter 继续...")
            input()
        except Exception as e:
            logger.warning(f"⚠️ pgvector 扩展设置: {e}")
        
        # 2. 创建基础表
        tables_to_create = [
            {
                "name": "messages",
                "sql": """
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    sender_name TEXT,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    group_id TEXT,
                    group_name TEXT,
                    is_ai_response BOOLEAN DEFAULT FALSE,
                    confidence_score FLOAT,
                    metadata JSONB
                );
                """
            },
            {
                "name": "sessions",
                "sql": """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL,
                    group_name TEXT,
                    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    end_time TIMESTAMP WITH TIME ZONE,
                    status TEXT DEFAULT 'active',
                    total_messages INTEGER DEFAULT 0,
                    ai_messages INTEGER DEFAULT 0,
                    summary TEXT,
                    metadata JSONB
                );
                """
            },
            {
                "name": "knowledge_chunks",
                "sql": """
                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    title TEXT,
                    source TEXT,
                    chunk_index INTEGER,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
            },
            {
                "name": "knowledge_vectors",
                "sql": """
                CREATE TABLE IF NOT EXISTS knowledge_vectors (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding VECTOR(1536),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
            }
        ]
        
        # 创建表
        for table_info in tables_to_create:
            logger.info(f"🔧 创建表: {table_info['name']}")
            try:
                # 注意：Supabase 客户端不能直接执行 DDL，需要在 Dashboard 中执行
                logger.info(f"💡 请在 Supabase Dashboard 的 SQL Editor 中执行以下 SQL:")
                logger.info(f"   {table_info['sql'].strip()}")
                logger.info("   执行完成后按 Enter 继续...")
                input()
                logger.info(f"✅ 表 {table_info['name']} 创建完成")
            except Exception as e:
                logger.error(f"❌ 创建表 {table_info['name']} 失败: {e}")
        
        # 3. 创建索引
        indexes_to_create = [
            {
                "name": "messages_session_idx",
                "sql": "CREATE INDEX IF NOT EXISTS messages_session_idx ON messages(session_id);"
            },
            {
                "name": "messages_timestamp_idx", 
                "sql": "CREATE INDEX IF NOT EXISTS messages_timestamp_idx ON messages(timestamp);"
            },
            {
                "name": "sessions_group_idx",
                "sql": "CREATE INDEX IF NOT EXISTS sessions_group_idx ON sessions(group_id);"
            },
            {
                "name": "knowledge_vectors_embedding_idx",
                "sql": "CREATE INDEX IF NOT EXISTS knowledge_vectors_embedding_idx ON knowledge_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
            }
        ]
        
        for index_info in indexes_to_create:
            logger.info(f"🔧 创建索引: {index_info['name']}")
            logger.info(f"💡 请在 Supabase Dashboard 的 SQL Editor 中执行以下 SQL:")
            logger.info(f"   {index_info['sql']}")
            logger.info("   执行完成后按 Enter 继续...")
            input()
            logger.info(f"✅ 索引 {index_info['name']} 创建完成")
        
        # 4. 创建 RPC 函数
        rpc_functions = [
            {
                "name": "search_embeddings",
                "sql": """
                CREATE OR REPLACE FUNCTION search_embeddings(
                    query_embedding VECTOR(1536),
                    match_count INTEGER DEFAULT 10,
                    filter JSONB DEFAULT '{}'::jsonb
                )
                RETURNS TABLE(
                    id TEXT,
                    content TEXT,
                    similarity FLOAT,
                    metadata JSONB
                )
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        kv.id,
                        kv.content,
                        1 - (kv.embedding <=> query_embedding) AS similarity,
                        kv.metadata
                    FROM knowledge_vectors kv
                    WHERE 
                        CASE 
                            WHEN filter = '{}'::jsonb THEN TRUE
                            ELSE kv.metadata @> filter
                        END
                    ORDER BY kv.embedding <=> query_embedding
                    LIMIT match_count;
                END;
                $$;
                """
            }
        ]
        
        for rpc_info in rpc_functions:
            logger.info(f"🔧 创建 RPC 函数: {rpc_info['name']}")
            logger.info(f"💡 请在 Supabase Dashboard 的 SQL Editor 中执行以下 SQL:")
            logger.info(f"   {rpc_info['sql'].strip()}")
            logger.info("   执行完成后按 Enter 继续...")
            input()
            logger.info(f"✅ RPC 函数 {rpc_info['name']} 创建完成")
        
        logger.info("🎉 数据库初始化完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False


async def test_after_init():
    """初始化后测试"""
    try:
        from supabase import create_client, Client
        
        logger.info("🔍 测试初始化后的数据库...")
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        supabase: Client = create_client(url, key)
        
        # 测试各个表
        tables_to_test = ['messages', 'sessions', 'knowledge_chunks', 'knowledge_vectors']
        
        for table in tables_to_test:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                logger.info(f"✅ 表 {table} 测试成功: {len(result.data)} 条记录")
            except Exception as e:
                logger.error(f"❌ 表 {table} 测试失败: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 初始化后测试失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 开始 Supabase 数据库初始化...")
    logger.info("=" * 60)
    
    # 检查环境变量
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ 缺少环境变量: {missing_vars}")
        return
    
    logger.info("✅ 环境变量检查通过")
    
    # 初始化数据库
    success = await init_database()
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("🎉 数据库初始化完成！")
        logger.info("=" * 60)
        
        # 测试初始化结果
        logger.info("\n🔍 测试初始化结果...")
        await test_after_init()
        
    else:
        logger.error("❌ 数据库初始化失败")


if __name__ == "__main__":
    asyncio.run(main())
