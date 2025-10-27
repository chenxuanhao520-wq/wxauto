#!/usr/bin/env python3
"""
准确的向量数据库测试
根据实际表结构进行调整
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


async def test_correct_vector_operations():
    """使用正确的向量维度测试"""
    try:
        from supabase import create_client, Client
        
        logger.info("🔍 使用正确的向量维度测试...")
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        supabase: Client = create_client(url, key)
        
        # 使用正确的 1536 维向量
        test_vector_data = {
            'id': 1,  # 使用数字 ID
            'content': '这是一个测试文档',
            'embedding': [0.1] * 1536,  # 1536维向量
            'metadata': {
                'title': '测试文档',
                'source': 'test',
                'created_at': '2025-10-27T23:28:00Z'
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
                    logger.info(f"           内容: {item.get('content', 'N/A')[:50]}...")
            
            # 清理测试数据
            delete_result = supabase.table('embeddings').delete().eq('id', 1).execute()
            logger.info("✅ 测试数据清理完成")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 向量操作测试失败: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 向量操作测试失败: {e}")
        return False


async def test_embedding_service_integration():
    """测试嵌入服务集成"""
    try:
        logger.info("🔍 测试嵌入服务集成...")
        
        # 检查是否有嵌入服务模块
        try:
            from modules.embeddings.unified_embedding_service import get_embedding_service
            
            embedding_service = get_embedding_service()
            logger.info("✅ 嵌入服务模块加载成功")
            
            # 测试文本嵌入
            test_text = "这是一个测试文本，用于生成嵌入向量"
            embedding = await embedding_service.embed_text(test_text)
            
            if embedding and len(embedding) == 1536:
                logger.info(f"✅ 嵌入向量生成成功: 维度 {len(embedding)}")
                
                # 测试插入到数据库
                from supabase import create_client, Client
                
                url = os.getenv("SUPABASE_URL")
                key = os.getenv("SUPABASE_ANON_KEY")
                supabase: Client = create_client(url, key)
                
                test_data = {
                    'id': 2,
                    'content': test_text,
                    'embedding': embedding,
                    'metadata': {
                        'title': '嵌入服务测试',
                        'source': 'embedding_service',
                        'created_at': '2025-10-27T23:28:00Z'
                    }
                }
                
                insert_result = supabase.table('embeddings').insert(test_data).execute()
                logger.info("✅ 嵌入向量插入数据库成功")
                
                # 测试搜索
                search_result = supabase.rpc('search_embeddings', {
                    'query_embedding': embedding,
                    'match_count': 3
                }).execute()
                
                logger.info(f"✅ 嵌入向量搜索成功: {len(search_result.data)} 条结果")
                
                # 清理测试数据
                delete_result = supabase.table('embeddings').delete().eq('id', 2).execute()
                logger.info("✅ 嵌入服务测试数据清理完成")
                
                return True
            else:
                logger.error(f"❌ 嵌入向量维度错误: {len(embedding) if embedding else 0}")
                return False
                
        except ImportError as e:
            logger.warning(f"⚠️ 嵌入服务模块未找到: {e}")
            logger.info("💡 可能需要安装相关依赖")
            return False
        
    except Exception as e:
        logger.error(f"❌ 嵌入服务集成测试失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 开始准确的向量数据库测试...")
    logger.info("=" * 50)
    
    # 检查环境变量
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        logger.error("❌ 缺少 Supabase 环境变量")
        return
    
    logger.info("✅ 环境变量检查通过")
    
    # 测试正确的向量操作
    vector_ok = await test_correct_vector_operations()
    
    # 测试嵌入服务集成
    embedding_ok = await test_embedding_service_integration()
    
    # 输出总结
    logger.info("\n" + "=" * 50)
    logger.info("📊 向量数据库测试结果:")
    logger.info("=" * 50)
    
    if vector_ok:
        logger.info("✅ 向量操作正常")
    else:
        logger.error("❌ 向量操作有问题")
    
    if embedding_ok:
        logger.info("✅ 嵌入服务集成正常")
    else:
        logger.warning("⚠️ 嵌入服务集成有问题")
    
    logger.info("=" * 50)
    
    if vector_ok:
        logger.info("🎉 向量数据库连接正常！")
        logger.info("💡 建议使用 Supabase Postgrestools 扩展进一步检查数据库结构")
    else:
        logger.warning("⚠️ 向量数据库存在问题，需要修复")


if __name__ == "__main__":
    asyncio.run(main())
