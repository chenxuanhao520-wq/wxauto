#!/usr/bin/env python3
"""
数据库连接测试脚本
测试 Supabase 数据库和向量数据库连接
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_supabase_connection():
    """测试 Supabase 基础连接"""
    try:
        from modules.storage.supabase_client import get_supabase_client
        
        logger.info("🔍 测试 Supabase 基础连接...")
        
        supabase = get_supabase_client()
        if not supabase:
            logger.error("❌ Supabase 客户端初始化失败")
            return False
        
        # 测试基础查询
        result = supabase.table('messages').select('id').limit(1).execute()
        logger.info(f"✅ Supabase 基础连接成功: {len(result.data)} 条记录")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase 连接失败: {e}")
        return False


async def test_vector_database():
    """测试向量数据库连接"""
    try:
        from modules.vector.supabase_vector import get_vector_search_service
        
        logger.info("🔍 测试向量数据库连接...")
        
        # 获取向量搜索服务
        vector_service = get_vector_search_service()
        
        # 健康检查
        health_status = await vector_service.health_check()
        
        if health_status:
            logger.info("✅ 向量数据库连接成功")
            
            # 获取统计信息
            stats = await vector_service.get_service_stats()
            logger.info(f"📊 向量数据库统计: {stats}")
            
            return True
        else:
            logger.error("❌ 向量数据库健康检查失败")
            return False
            
    except RuntimeError as e:
        logger.error(f"❌ 向量搜索服务未初始化: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 向量数据库连接失败: {e}")
        return False


async def test_embedding_service():
    """测试嵌入服务"""
    try:
        from modules.embeddings.unified_embedding_service import get_embedding_service
        
        logger.info("🔍 测试嵌入服务...")
        
        embedding_service = get_embedding_service()
        
        # 测试文本嵌入
        test_text = "这是一个测试文本"
        embedding = await embedding_service.embed_text(test_text)
        
        if embedding and len(embedding) > 0:
            logger.info(f"✅ 嵌入服务正常: 向量维度 {len(embedding)}")
            return True
        else:
            logger.error("❌ 嵌入服务返回空向量")
            return False
            
    except Exception as e:
        logger.error(f"❌ 嵌入服务测试失败: {e}")
        return False


async def test_database_schema():
    """测试数据库表结构"""
    try:
        from modules.storage.supabase_client import get_supabase_client
        
        logger.info("🔍 检查数据库表结构...")
        
        supabase = get_supabase_client()
        
        # 检查必要的表
        required_tables = [
            'messages',
            'sessions', 
            'knowledge_chunks',
            'knowledge_vectors'
        ]
        
        for table in required_tables:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                logger.info(f"✅ 表 '{table}' 存在: {len(result.data)} 条记录")
            except Exception as e:
                logger.warning(f"⚠️ 表 '{table}' 可能不存在: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库表结构检查失败: {e}")
        return False


async def test_vector_table_creation():
    """测试向量表创建"""
    try:
        from modules.vector.supabase_vector_client import SupabaseVectorClient
        from modules.storage.supabase_client import get_supabase_client
        
        logger.info("🔍 测试向量表创建...")
        
        supabase = get_supabase_client()
        
        # 创建向量客户端
        vector_client = SupabaseVectorClient(
            supabase_url=supabase.url,
            supabase_key=supabase.supabase_key,
            table_name="knowledge_vectors",
            embedding_dimension=1536,
            distance_metric="cosine"
        )
        
        # 初始化表
        await vector_client._init_table()
        logger.info("✅ 向量表初始化完成")
        
        # 测试插入
        test_vector = {
            "id": "test_001",
            "content": "这是一个测试文档",
            "embedding": [0.1] * 1536,  # 测试向量
            "metadata": {
                "title": "测试文档",
                "source": "test",
                "created_at": datetime.now().isoformat()
            }
        }
        
        success = await vector_client.upsert_vectors([test_vector])
        
        if success:
            logger.info("✅ 向量插入测试成功")
            
            # 测试搜索
            results = await vector_client.search_vectors(
                query_embedding=[0.1] * 1536,
                top_k=5,
                similarity_threshold=0.5
            )
            
            logger.info(f"✅ 向量搜索测试成功: {len(results)} 条结果")
            
            # 清理测试数据
            await vector_client.delete_vectors(["test_001"])
            logger.info("✅ 测试数据清理完成")
            
            return True
        else:
            logger.error("❌ 向量插入测试失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 向量表测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始数据库连接测试...")
    logger.info("=" * 50)
    
    # 检查环境变量
    logger.info("🔍 检查环境变量...")
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY', 
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ 缺少环境变量: {missing_vars}")
        return
    
    logger.info("✅ 环境变量检查通过")
    logger.info("=" * 50)
    
    # 运行测试
    tests = [
        ("Supabase 基础连接", test_supabase_connection),
        ("数据库表结构", test_database_schema),
        ("向量表创建", test_vector_table_creation),
        ("向量数据库连接", test_vector_database),
        ("嵌入服务", test_embedding_service),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 运行测试: {test_name}")
        try:
            result = await test_func()
            results[test_name] = result
            if result:
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
            results[test_name] = False
    
    # 输出测试结果
    logger.info("\n" + "=" * 50)
    logger.info("📊 测试结果汇总:")
    logger.info("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 50)
    logger.info(f"📈 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！数据库连接正常")
    else:
        logger.warning(f"⚠️ {total - passed} 个测试失败，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())
