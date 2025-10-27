#!/usr/bin/env python3
"""
Supabase 数据库管理工具
使用 Service Role Key 进行数据库操作
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

class SupabaseManager:
    """Supabase 数据库管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.service_key:
            raise ValueError("缺少 Supabase 环境变量")
        
        from supabase import create_client, Client
        self.supabase: Client = create_client(self.url, self.service_key)
        
        logger.info("✅ Supabase 管理器初始化成功")
    
    async def list_tables(self):
        """列出所有表"""
        try:
            logger.info("🔍 列出所有表...")
            
            # 查询所有表
            result = self.supabase.rpc('get_tables').execute()
            
            if result.data:
                logger.info("📋 数据库表列表:")
                for table in result.data:
                    logger.info(f"   - {table}")
            else:
                logger.info("📋 没有找到表")
            
            return result.data
            
        except Exception as e:
            logger.warning(f"⚠️ 无法获取表列表: {e}")
            
            # 尝试直接查询 information_schema
            try:
                result = self.supabase.rpc('exec_sql', {
                    'sql': "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
                }).execute()
                
                if result.data:
                    logger.info("📋 数据库表列表:")
                    for table in result.data:
                        logger.info(f"   - {table}")
                    return result.data
                    
            except Exception as e2:
                logger.error(f"❌ 查询表列表失败: {e2}")
                return []
    
    async def describe_table(self, table_name):
        """描述表结构"""
        try:
            logger.info(f"🔍 描述表结构: {table_name}")
            
            # 查询表结构
            result = self.supabase.rpc('exec_sql', {
                'sql': f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                ORDER BY ordinal_position;
                """
            }).execute()
            
            if result.data:
                logger.info(f"📋 表 {table_name} 结构:")
                for column in result.data:
                    logger.info(f"   - {column['column_name']}: {column['data_type']} {'NULL' if column['is_nullable'] == 'YES' else 'NOT NULL'}")
            else:
                logger.info(f"📋 表 {table_name} 没有列")
            
            return result.data
            
        except Exception as e:
            logger.error(f"❌ 描述表结构失败: {e}")
            return []
    
    async def query_table(self, table_name, limit=10):
        """查询表数据"""
        try:
            logger.info(f"🔍 查询表数据: {table_name}")
            
            result = self.supabase.table(table_name).select('*').limit(limit).execute()
            
            if result.data:
                logger.info(f"📋 表 {table_name} 数据 (前 {len(result.data)} 条):")
                for i, row in enumerate(result.data):
                    logger.info(f"   行 {i+1}: {row}")
            else:
                logger.info(f"📋 表 {table_name} 没有数据")
            
            return result.data
            
        except Exception as e:
            logger.error(f"❌ 查询表数据失败: {e}")
            return []
    
    async def test_vector_search(self):
        """测试向量搜索"""
        try:
            logger.info("🔍 测试向量搜索...")
            
            # 创建测试向量
            test_vector = [0.1] * 1536
            
            result = self.supabase.rpc('search_embeddings', {
                'query_embedding': test_vector,
                'match_count': 5
            }).execute()
            
            if result.data:
                logger.info(f"✅ 向量搜索成功: {len(result.data)} 条结果")
                for i, item in enumerate(result.data):
                    logger.info(f"   结果 {i+1}: {item}")
            else:
                logger.info("✅ 向量搜索成功: 没有匹配结果")
            
            return result.data
            
        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []
    
    async def execute_sql(self, sql):
        """执行 SQL 查询"""
        try:
            logger.info(f"🔍 执行 SQL: {sql}")
            
            result = self.supabase.rpc('exec_sql', {'sql': sql}).execute()
            
            if result.data:
                logger.info(f"✅ SQL 执行成功: {len(result.data)} 条结果")
                for i, row in enumerate(result.data):
                    logger.info(f"   行 {i+1}: {row}")
            else:
                logger.info("✅ SQL 执行成功: 没有结果")
            
            return result.data
            
        except Exception as e:
            logger.error(f"❌ SQL 执行失败: {e}")
            return []

async def main():
    """主函数"""
    logger.info("🚀 Supabase 数据库管理工具...")
    logger.info("=" * 50)
    
    try:
        # 初始化管理器
        manager = SupabaseManager()
        
        # 列出所有表
        await manager.list_tables()
        
        # 描述 embeddings 表
        await manager.describe_table('embeddings')
        
        # 查询 embeddings 表数据
        await manager.query_table('embeddings')
        
        # 测试向量搜索
        await manager.test_vector_search()
        
        # 执行自定义 SQL
        await manager.execute_sql("SELECT version();")
        
        logger.info("\n" + "=" * 50)
        logger.info("🎉 数据库管理工具运行完成！")
        logger.info("💡 您可以使用这个工具管理 Supabase 数据库")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ 管理器初始化失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
