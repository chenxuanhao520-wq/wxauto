#!/usr/bin/env python3
"""
检查现有数据库结构
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


async def check_existing_tables():
    """检查现有的表"""
    try:
        from supabase import create_client, Client
        
        logger.info("🔍 检查现有数据库表...")
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        supabase: Client = create_client(url, key)
        
        # 尝试查询一些可能的表名
        possible_tables = [
            'messages',
            'sessions', 
            'knowledge_chunks',
            'knowledge_vectors',
            'embeddings',
            'vectors',
            'documents',
            'chunks',
            'conversations',
            'chat_history',
            'user_messages',
            'ai_responses'
        ]
        
        existing_tables = []
        
        for table in possible_tables:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                existing_tables.append(table)
                logger.info(f"✅ 找到表: {table} ({len(result.data)} 条记录)")
            except Exception as e:
                logger.debug(f"❌ 表 {table} 不存在: {e}")
        
        if existing_tables:
            logger.info(f"📊 找到 {len(existing_tables)} 个现有表: {existing_tables}")
            
            # 检查表结构
            for table in existing_tables:
                try:
                    result = supabase.table(table).select('*').limit(1).execute()
                    if result.data:
                        columns = list(result.data[0].keys())
                        logger.info(f"📋 表 {table} 的列: {columns}")
                except Exception as e:
                    logger.warning(f"⚠️ 无法获取表 {table} 的结构: {e}")
        else:
            logger.warning("⚠️ 没有找到任何表")
        
        return existing_tables
        
    except Exception as e:
        logger.error(f"❌ 检查表失败: {e}")
        return []


async def check_pgvector_status():
    """检查 pgvector 状态"""
    try:
        from supabase import create_client, Client
        
        logger.info("🔍 检查 pgvector 状态...")
        
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not service_key:
            logger.warning("⚠️ 没有 SERVICE_ROLE_KEY，无法检查 pgvector")
            return False
        
        supabase: Client = create_client(url, service_key)
        
        # 尝试查询 pgvector 相关信息
        try:
            # 检查扩展
            result = supabase.rpc('check_extensions').execute()
            logger.info(f"✅ 扩展检查结果: {result.data}")
        except Exception as e:
            logger.warning(f"⚠️ 扩展检查失败: {e}")
        
        # 尝试创建测试向量表
        try:
            test_sql = """
            CREATE TABLE IF NOT EXISTS test_vectors (
                id TEXT PRIMARY KEY,
                embedding VECTOR(3)
            );
            """
            result = supabase.rpc('exec', {'sql': test_sql}).execute()
            logger.info("✅ pgvector 测试表创建成功")
            
            # 清理测试表
            cleanup_sql = "DROP TABLE IF EXISTS test_vectors;"
            supabase.rpc('exec', {'sql': cleanup_sql}).execute()
            logger.info("✅ 测试表清理完成")
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ pgvector 测试失败: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ pgvector 检查失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 检查现有数据库结构...")
    logger.info("=" * 50)
    
    # 检查环境变量
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        logger.error("❌ 缺少 Supabase 环境变量")
        return
    
    logger.info("✅ 环境变量检查通过")
    
    # 检查现有表
    existing_tables = await check_existing_tables()
    
    # 检查 pgvector
    pgvector_ok = await check_pgvector_status()
    
    # 输出总结
    logger.info("\n" + "=" * 50)
    logger.info("📊 检查结果总结:")
    logger.info("=" * 50)
    
    if existing_tables:
        logger.info(f"✅ 找到 {len(existing_tables)} 个现有表")
        logger.info(f"📋 表列表: {existing_tables}")
    else:
        logger.warning("⚠️ 没有找到现有表")
    
    if pgvector_ok:
        logger.info("✅ pgvector 扩展可用")
    else:
        logger.warning("⚠️ pgvector 扩展可能未启用")
    
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
