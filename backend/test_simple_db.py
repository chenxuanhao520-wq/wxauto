#!/usr/bin/env python3
"""
简化的数据库连接测试脚本
直接测试 Supabase 连接
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


async def test_supabase_direct():
    """直接测试 Supabase 连接"""
    try:
        from supabase import create_client, Client
        
        logger.info("🔍 测试 Supabase 直接连接...")
        
        # 获取环境变量
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.error("❌ 缺少 Supabase 环境变量")
            return False
        
        logger.info(f"📡 连接 URL: {url}")
        
        # 创建客户端
        supabase: Client = create_client(url, key)
        
        # 测试基础查询
        try:
            result = supabase.table('messages').select('id').limit(1).execute()
            logger.info(f"✅ Supabase 连接成功: {len(result.data)} 条记录")
            return True
        except Exception as e:
            logger.warning(f"⚠️ messages 表查询失败: {e}")
            
            # 尝试查询其他表
            try:
                result = supabase.table('sessions').select('id').limit(1).execute()
                logger.info(f"✅ Supabase 连接成功 (sessions表): {len(result.data)} 条记录")
                return True
            except Exception as e2:
                logger.warning(f"⚠️ sessions 表查询失败: {e2}")
                
                # 尝试查询向量表
                try:
                    result = supabase.table('knowledge_vectors').select('id').limit(1).execute()
                    logger.info(f"✅ Supabase 连接成功 (knowledge_vectors表): {len(result.data)} 条记录")
                    return True
                except Exception as e3:
                    logger.error(f"❌ 所有表查询失败: {e3}")
                    return False
        
    except Exception as e:
        logger.error(f"❌ Supabase 连接失败: {e}")
        return False


async def test_vector_extension():
    """测试 pgvector 扩展"""
    try:
        from supabase import create_client, Client
        
        logger.info("🔍 测试 pgvector 扩展...")
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # 使用 service role key
        
        if not url or not key:
            logger.error("❌ 缺少 Supabase 环境变量")
            return False
        
        supabase: Client = create_client(url, key)
        
        # 检查 pgvector 扩展
        try:
            result = supabase.rpc('check_vector_extension').execute()
            logger.info("✅ pgvector 扩展已启用")
            return True
        except Exception as e:
            logger.warning(f"⚠️ pgvector 扩展检查失败: {e}")
            
            # 尝试创建向量表
            try:
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS knowledge_vectors (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    embedding VECTOR(1536),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
                
                result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
                logger.info("✅ 向量表创建成功")
                return True
            except Exception as e2:
                logger.error(f"❌ 向量表创建失败: {e2}")
                return False
        
    except Exception as e:
        logger.error(f"❌ pgvector 测试失败: {e}")
        return False


async def test_ai_services():
    """测试 AI 服务配置"""
    logger.info("🔍 检查 AI 服务配置...")
    
    # 检查 Qwen API Key
    qwen_key = os.getenv("QWEN_API_KEY")
    if qwen_key and qwen_key != "your_qwen_api_key":
        logger.info("✅ Qwen API Key 已配置")
    else:
        logger.warning("⚠️ Qwen API Key 未配置")
    
    # 检查 ZhipuAI API Key
    zhipu_key = os.getenv("ZHIPUAI_API_KEY")
    if zhipu_key and zhipu_key != "your_zhipuai_api_key":
        logger.info("✅ ZhipuAI API Key 已配置")
    else:
        logger.warning("⚠️ ZhipuAI API Key 未配置")
    
    return True


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
        ("Supabase 直接连接", test_supabase_direct),
        ("pgvector 扩展", test_vector_extension),
        ("AI 服务配置", test_ai_services),
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
