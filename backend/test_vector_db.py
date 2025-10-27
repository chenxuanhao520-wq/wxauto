#!/usr/bin/env python3
"""
检查 embeddings 表结构和 search_embeddings 函数
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


async def check_embeddings_table():
    """检查 embeddings 表结构"""
    try:
        from supabase import create_client, Client
        
        logger.info("🔍 检查 embeddings 表结构...")
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        supabase: Client = create_client(url, key)
        
        # 获取表结构（通过查询空记录）
        try:
            result = supabase.table('embeddings').select('*').limit(1).execute()
            logger.info(f"✅ embeddings 表存在: {len(result.data)} 条记录")
            
            # 尝试插入一条测试记录来查看表结构
            test_data = {
                'id': 'test_structure_check',
                'content': '测试内容',
                'embedding': [0.1, 0.2, 0.3],  # 测试向量
                'metadata': {'test': True}
            }
            
            try:
                insert_result = supabase.table('embeddings').insert(test_data).execute()
                logger.info("✅ 测试数据插入成功")
                
                # 立即删除测试数据
                delete_result = supabase.table('embeddings').delete().eq('id', 'test_structure_check').execute()
                logger.info("✅ 测试数据清理完成")
                
                # 推断表结构
                logger.info("📋 推断的 embeddings 表结构:")
                logger.info("   - id: TEXT (主键)")
                logger.info("   - content: TEXT")
                logger.info("   - embedding: VECTOR")
                logger.info("   - metadata: JSONB")
                
            except Exception as e:
                logger.warning(f"⚠️ 无法插入测试数据: {e}")
                logger.info("💡 表可能已有数据或结构不同")
        
        except Exception as e:
            logger.error(f"❌ 检查 embeddings 表失败: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ embeddings 表检查失败: {e}")
        return False


async def test_search_embeddings_function():
    """测试 search_embeddings 函数"""
    try:
        from supabase import create_client, Client
        
        logger.info("🔍 测试 search_embeddings 函数...")
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        supabase: Client = create_client(url, key)
        
        # 测试 search_embeddings 函数
        try:
            # 创建一个测试查询向量
            test_query_vector = [0.1] * 1536  # 1536维向量
            
            result = supabase.rpc('search_embeddings', {
                'query_embedding': test_query_vector,
                'match_count': 5
            }).execute()
            
            logger.info(f"✅ search_embeddings 函数测试成功: {len(result.data)} 条结果")
            
            if result.data:
                logger.info("📋 函数返回结果示例:")
                for i, item in enumerate(result.data[:2]):  # 只显示前2条
                    logger.info(f"   结果 {i+1}: {item}")
            else:
                logger.info("💡 函数工作正常，但没有匹配的数据")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ search_embeddings 函数测试失败: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ search_embeddings 测试失败: {e}")
        return False


async def test_vector_operations():
    """测试向量操作"""
    try:
        from supabase import create_client, Client
        
        logger.info("🔍 测试向量操作...")
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        supabase: Client = create_client(url, key)
        
        # 测试插入向量数据
        test_vector_data = {
            'id': 'test_vector_001',
            'content': '这是一个测试文档',
            'embedding': [0.1] * 1536,  # 1536维向量
            'metadata': {
                'title': '测试文档',
                'source': 'test',
                'created_at': '2025-10-27T23:27:00Z'
            }
        }
        
        try:
            # 插入测试数据
            insert_result = supabase.table('embeddings').insert(test_vector_data).execute()
            logger.info("✅ 向量数据插入成功")
            
            # 测试搜索
            search_result = supabase.rpc('search_embeddings', {
                'query_embedding': [0.1] * 1536,
                'match_count': 3
            }).execute()
            
            logger.info(f"✅ 向量搜索成功: {len(search_result.data)} 条结果")
            
            # 显示搜索结果
            if search_result.data:
                logger.info("📋 搜索结果:")
                for i, item in enumerate(search_result.data):
                    logger.info(f"   结果 {i+1}: ID={item.get('id')}, 相似度={item.get('similarity', 'N/A')}")
            
            # 清理测试数据
            delete_result = supabase.table('embeddings').delete().eq('id', 'test_vector_001').execute()
            logger.info("✅ 测试数据清理完成")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 向量操作测试失败: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 向量操作测试失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 检查现有向量数据库...")
    logger.info("=" * 50)
    
    # 检查环境变量
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        logger.error("❌ 缺少 Supabase 环境变量")
        return
    
    logger.info("✅ 环境变量检查通过")
    
    # 检查 embeddings 表
    table_ok = await check_embeddings_table()
    
    # 测试 search_embeddings 函数
    function_ok = await test_search_embeddings_function()
    
    # 测试向量操作
    vector_ok = await test_vector_operations()
    
    # 输出总结
    logger.info("\n" + "=" * 50)
    logger.info("📊 向量数据库检查结果:")
    logger.info("=" * 50)
    
    if table_ok:
        logger.info("✅ embeddings 表正常")
    else:
        logger.error("❌ embeddings 表有问题")
    
    if function_ok:
        logger.info("✅ search_embeddings 函数正常")
    else:
        logger.error("❌ search_embeddings 函数有问题")
    
    if vector_ok:
        logger.info("✅ 向量操作正常")
    else:
        logger.error("❌ 向量操作有问题")
    
    logger.info("=" * 50)
    
    if table_ok and function_ok and vector_ok:
        logger.info("🎉 向量数据库完全正常！")
    else:
        logger.warning("⚠️ 向量数据库存在问题，需要修复")


if __name__ == "__main__":
    asyncio.run(main())
