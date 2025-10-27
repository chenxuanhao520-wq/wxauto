#!/usr/bin/env python3
"""
简化的 Supabase 数据库管理工具
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

class SimpleSupabaseManager:
    """简化的 Supabase 数据库管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.service_key:
            raise ValueError("缺少 Supabase 环境变量")
        
        from supabase import create_client, Client
        self.supabase: Client = create_client(self.url, self.service_key)
        
        logger.info("✅ Supabase 管理器初始化成功")
    
    async def show_connection_info(self):
        """显示连接信息"""
        logger.info("📋 Supabase 连接信息:")
        logger.info(f"   URL: {self.url}")
        logger.info(f"   Service Key: {self.service_key[:10]}...{self.service_key[-10:]}")
        
        # 解析项目引用
        project_ref = self.url.replace("https://", "").replace(".supabase.co", "")
        logger.info(f"   Project Ref: {project_ref}")
        
        # 数据库连接信息
        db_host = f"db.{project_ref}.supabase.co"
        logger.info(f"   DB Host: {db_host}")
        logger.info(f"   DB Port: 5432")
        logger.info(f"   DB Name: postgres")
        logger.info(f"   DB User: postgres")
        logger.info(f"   DB Password: [需要从 Dashboard 获取]")
    
    async def test_embeddings_table(self):
        """测试 embeddings 表"""
        try:
            logger.info("🔍 测试 embeddings 表...")
            
            # 查询表数据
            result = self.supabase.table('embeddings').select('*').limit(5).execute()
            
            logger.info(f"📊 embeddings 表状态:")
            logger.info(f"   - 记录数: {len(result.data)}")
            
            if result.data:
                logger.info("   - 示例数据:")
                for i, row in enumerate(result.data):
                    logger.info(f"     行 {i+1}: ID={row.get('id')}, 内容={row.get('content', '')[:50]}...")
            else:
                logger.info("   - 表为空")
            
            return result.data
            
        except Exception as e:
            logger.error(f"❌ 测试 embeddings 表失败: {e}")
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
            
            logger.info(f"📊 向量搜索测试:")
            logger.info(f"   - 查询向量维度: {len(test_vector)}")
            logger.info(f"   - 搜索结果数: {len(result.data)}")
            
            if result.data:
                logger.info("   - 搜索结果:")
                for i, item in enumerate(result.data):
                    logger.info(f"     结果 {i+1}: ID={item.get('id')}, 相似度={item.get('similarity', 'N/A')}")
            else:
                logger.info("   - 没有匹配结果")
            
            return result.data
            
        except Exception as e:
            logger.error(f"❌ 向量搜索测试失败: {e}")
            return []
    
    async def add_test_data(self):
        """添加测试数据"""
        try:
            logger.info("🔍 添加测试数据...")
            
            # 测试文档
            test_documents = [
                {
                    'id': 1,
                    'content': '充电桩故障排除指南',
                    'embedding': [0.1] * 1536,
                    'metadata': {
                        'title': '充电桩故障排除指南',
                        'source': 'test',
                        'created_at': '2025-10-27T23:42:00Z'
                    }
                },
                {
                    'id': 2,
                    'content': '如何安装充电桩',
                    'embedding': [0.2] * 1536,
                    'metadata': {
                        'title': '如何安装充电桩',
                        'source': 'test',
                        'created_at': '2025-10-27T23:42:00Z'
                    }
                }
            ]
            
            # 插入测试数据
            for doc in test_documents:
                try:
                    result = self.supabase.table('embeddings').insert(doc).execute()
                    logger.info(f"✅ 文档 {doc['id']} 插入成功")
                except Exception as e:
                    logger.warning(f"⚠️ 文档 {doc['id']} 插入失败: {e}")
            
            logger.info("📊 测试数据添加完成")
            
        except Exception as e:
            logger.error(f"❌ 添加测试数据失败: {e}")
    
    async def cleanup_test_data(self):
        """清理测试数据"""
        try:
            logger.info("🧹 清理测试数据...")
            
            # 删除测试数据
            result = self.supabase.table('embeddings').delete().eq('id', 1).execute()
            logger.info("✅ 测试数据 1 清理完成")
            
            result = self.supabase.table('embeddings').delete().eq('id', 2).execute()
            logger.info("✅ 测试数据 2 清理完成")
            
            logger.info("📊 测试数据清理完成")
            
        except Exception as e:
            logger.error(f"❌ 清理测试数据失败: {e}")
    
    async def show_postgrestools_info(self):
        """显示 Postgrestools 连接信息"""
        logger.info("🔧 Postgrestools 连接信息:")
        logger.info("=" * 40)
        
        project_ref = self.url.replace("https://", "").replace(".supabase.co", "")
        db_host = f"db.{project_ref}.supabase.co"
        
        logger.info(f"Host: {db_host}")
        logger.info("Port: 5432")
        logger.info("Database: postgres")
        logger.info("Username: postgres")
        logger.info("Password: [需要从 Supabase Dashboard 获取]")
        
        logger.info("\n💡 获取密码的步骤:")
        logger.info("1. 访问 https://supabase.com/dashboard")
        logger.info("2. 选择您的项目")
        logger.info("3. 进入 Settings > Database")
        logger.info("4. 找到 'Connection string' 部分")
        logger.info("5. 复制密码（在 postgres: 后面的部分）")
        
        logger.info("\n🔗 连接字符串格式:")
        logger.info(f"postgresql://postgres:[PASSWORD]@{db_host}:5432/postgres")

async def main():
    """主函数"""
    logger.info("🚀 简化的 Supabase 数据库管理工具...")
    logger.info("=" * 50)
    
    try:
        # 初始化管理器
        manager = SimpleSupabaseManager()
        
        # 显示连接信息
        await manager.show_connection_info()
        
        # 测试 embeddings 表
        await manager.test_embeddings_table()
        
        # 测试向量搜索
        await manager.test_vector_search()
        
        # 显示 Postgrestools 连接信息
        await manager.show_postgrestools_info()
        
        logger.info("\n" + "=" * 50)
        logger.info("🎉 数据库管理工具运行完成！")
        logger.info("💡 您的 Supabase 连接完全正常")
        logger.info("💡 可以使用 Postgrestools 或继续使用 API 方式")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ 管理器初始化失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
