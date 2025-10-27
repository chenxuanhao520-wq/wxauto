#!/usr/bin/env python3
"""
使用 Supabase Service Role Key 连接数据库
"""

import os
import sys
import subprocess
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

def get_database_password_from_service_key():
    """从 Service Role Key 获取数据库密码"""
    try:
        logger.info("🔍 尝试从 Service Role Key 获取数据库密码...")
        
        # 从环境变量获取信息
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not service_key:
            logger.error("❌ 缺少 Supabase 环境变量")
            return None
        
        # 解析项目引用
        project_ref = url.replace("https://", "").replace(".supabase.co", "")
        
        logger.info(f"📡 项目引用: {project_ref}")
        logger.info(f"🔑 Service Role Key: {service_key[:10]}...{service_key[-10:]}")
        
        # 尝试使用 Service Role Key 连接
        # 注意：Service Role Key 通常不能直接用于数据库连接
        # 但我们可以尝试使用它来获取连接信息
        
        logger.info("💡 Service Role Key 通常用于 API 调用，不是数据库密码")
        logger.info("💡 数据库密码需要从 Supabase Dashboard 获取")
        
        return None
        
    except Exception as e:
        logger.error(f"❌ 获取密码失败: {e}")
        return None

def test_connection_with_service_key():
    """使用 Service Role Key 测试连接"""
    try:
        logger.info("🔍 使用 Service Role Key 测试连接...")
        
        from supabase import create_client, Client
        
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not service_key:
            logger.error("❌ 缺少 Supabase 环境变量")
            return False
        
        # 使用 Service Role Key 创建客户端
        supabase: Client = create_client(url, service_key)
        
        # 测试连接
        try:
            result = supabase.table('embeddings').select('*').limit(1).execute()
            logger.info("✅ Service Role Key 连接成功！")
            logger.info(f"📊 embeddings 表: {len(result.data)} 条记录")
            
            # 测试向量搜索函数
            try:
                search_result = supabase.rpc('search_embeddings', {
                    'query_embedding': [0.1] * 1536,
                    'match_count': 3
                }).execute()
                logger.info("✅ 向量搜索函数正常！")
                logger.info(f"📋 搜索结果: {len(search_result.data)} 条")
            except Exception as e:
                logger.warning(f"⚠️ 向量搜索函数测试失败: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Service Role Key 连接失败: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Service Role Key 测试失败: {e}")
        return False

def get_connection_info_for_postgrestools():
    """获取 Postgrestools 连接信息"""
    try:
        logger.info("📋 获取 Postgrestools 连接信息...")
        
        url = os.getenv("SUPABASE_URL")
        if not url:
            logger.error("❌ 缺少 SUPABASE_URL 环境变量")
            return None
        
        # 解析项目引用
        project_ref = url.replace("https://", "").replace(".supabase.co", "")
        
        # 构建连接信息
        host = f"db.{project_ref}.supabase.co"
        port = "5432"
        database = "postgres"
        username = "postgres"
        
        logger.info("🔗 Postgrestools 连接信息:")
        logger.info(f"   Host: {host}")
        logger.info(f"   Port: {port}")
        logger.info(f"   Database: {database}")
        logger.info(f"   Username: {username}")
        logger.info(f"   Password: [需要从 Supabase Dashboard 获取]")
        
        logger.info("\n💡 获取密码的步骤:")
        logger.info("   1. 访问 https://supabase.com/dashboard")
        logger.info("   2. 选择您的项目")
        logger.info("   3. 进入 Settings > Database")
        logger.info("   4. 找到 'Connection string' 部分")
        logger.info("   5. 复制密码（在 postgres: 后面的部分）")
        
        logger.info("\n🔧 在 Postgrestools 中使用:")
        logger.info("   1. 启动 Postgres Tools")
        logger.info("   2. 添加新连接")
        logger.info("   3. 输入上面的连接信息")
        logger.info("   4. 输入从 Dashboard 获取的密码")
        
        return {
            "host": host,
            "port": port,
            "database": database,
            "username": username
        }
        
    except Exception as e:
        logger.error(f"❌ 获取连接信息失败: {e}")
        return None

def test_direct_connection():
    """测试直接连接"""
    try:
        logger.info("🔍 测试直接数据库连接...")
        
        connection_info = get_connection_info_for_postgrestools()
        if not connection_info:
            return False
        
        # 构建连接字符串
        connection_string = f"postgresql://{connection_info['username']}@{connection_info['host']}:{connection_info['port']}/{connection_info['database']}"
        
        logger.info(f"🔗 连接字符串: {connection_string}")
        
        # 执行连接测试
        psql_path = "/opt/homebrew/opt/postgresql@14/bin/psql"
        cmd = [psql_path, connection_string, "-c", "SELECT version();"]
        
        logger.info("🚀 尝试连接数据库...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("✅ 数据库连接成功！")
                logger.info(f"📋 PostgreSQL 版本: {result.stdout.strip()}")
                return True
            else:
                logger.warning(f"⚠️ 需要密码: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ 连接超时，可能需要输入密码")
            return False
        except Exception as e:
            logger.error(f"❌ 连接异常: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 测试连接失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 使用 Supabase Service Role Key 连接数据库...")
    logger.info("=" * 60)
    
    # 检查环境变量
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not service_key:
        logger.error("❌ 缺少 Supabase 环境变量")
        return
    
    logger.info("✅ 环境变量检查通过")
    
    # 测试 Service Role Key 连接
    logger.info("\n🧪 测试 Service Role Key 连接...")
    service_ok = test_connection_with_service_key()
    
    # 获取连接信息
    logger.info("\n📋 获取 Postgrestools 连接信息...")
    connection_info = get_connection_info_for_postgrestools()
    
    # 测试直接连接
    logger.info("\n🧪 测试直接数据库连接...")
    direct_ok = test_direct_connection()
    
    # 输出总结
    logger.info("\n" + "=" * 60)
    logger.info("📊 连接测试结果:")
    logger.info("=" * 60)
    
    if service_ok:
        logger.info("✅ Service Role Key 连接正常")
    else:
        logger.error("❌ Service Role Key 连接有问题")
    
    if direct_ok:
        logger.info("✅ 直接数据库连接正常")
    else:
        logger.warning("⚠️ 直接数据库连接需要密码")
    
    logger.info("=" * 60)
    
    if service_ok:
        logger.info("🎉 Supabase 连接正常！")
        logger.info("💡 您可以使用 Service Role Key 进行 API 调用")
        logger.info("💡 或者获取数据库密码后使用 Postgrestools")
    else:
        logger.error("❌ Supabase 连接有问题，请检查配置")

if __name__ == "__main__":
    main()
