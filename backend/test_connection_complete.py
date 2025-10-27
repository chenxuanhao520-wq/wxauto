#!/usr/bin/env python3
"""
测试 Supabase 数据库连接
使用 psql 命令行工具
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

def get_connection_info():
    """获取连接信息"""
    try:
        logger.info("🔍 获取 Supabase 数据库连接信息...")
        
        # 从环境变量获取信息
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
        
        logger.info(f"📡 连接信息:")
        logger.info(f"   Host: {host}")
        logger.info(f"   Port: {port}")
        logger.info(f"   Database: {database}")
        logger.info(f"   Username: {username}")
        
        return {
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "project_ref": project_ref
        }
        
    except Exception as e:
        logger.error(f"❌ 获取连接信息失败: {e}")
        return None

def test_connection_without_password():
    """测试连接（不输入密码）"""
    try:
        logger.info("🔍 测试 Supabase 数据库连接...")
        
        connection_info = get_connection_info()
        if not connection_info:
            return False
        
        # 构建连接字符串
        connection_string = f"postgresql://{connection_info['username']}@{connection_info['host']}:{connection_info['port']}/{connection_info['database']}"
        
        logger.info(f"🔗 连接字符串: {connection_string}")
        
        # 执行连接测试
        psql_path = "/opt/homebrew/opt/postgresql@14/bin/psql"
        cmd = [psql_path, connection_string, "-c", "SELECT version();"]
        
        logger.info("🚀 尝试连接数据库...")
        logger.info("💡 如果提示输入密码，请从 Supabase Dashboard 获取")
        
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

def show_connection_instructions():
    """显示连接说明"""
    try:
        logger.info("📋 Supabase 数据库连接说明")
        logger.info("=" * 50)
        
        connection_info = get_connection_info()
        if not connection_info:
            return
        
        logger.info("🔗 连接信息:")
        logger.info(f"   Host: {connection_info['host']}")
        logger.info(f"   Port: {connection_info['port']}")
        logger.info(f"   Database: {connection_info['database']}")
        logger.info(f"   Username: {connection_info['username']}")
        logger.info(f"   Password: [需要从 Supabase Dashboard 获取]")
        
        logger.info("\n💡 获取密码的步骤:")
        logger.info("   1. 访问 https://supabase.com/dashboard")
        logger.info("   2. 选择您的项目")
        logger.info("   3. 进入 Settings > Database")
        logger.info("   4. 找到 'Connection string' 部分")
        logger.info("   5. 复制密码")
        
        logger.info("\n🔧 在 Postgrestools 中使用:")
        logger.info("   1. 启动 Postgres Tools")
        logger.info("   2. 添加新连接")
        logger.info("   3. 输入上面的连接信息")
        logger.info("   4. 输入从 Dashboard 获取的密码")
        
        logger.info("\n📝 连接字符串格式:")
        logger.info(f"   postgresql://{connection_info['username']}:[PASSWORD]@{connection_info['host']}:{connection_info['port']}/{connection_info['database']}")
        
        logger.info("\n🧪 测试连接命令:")
        logger.info(f"   psql 'postgresql://{connection_info['username']}:[PASSWORD]@{connection_info['host']}:{connection_info['port']}/{connection_info['database']}'")
        
    except Exception as e:
        logger.error(f"❌ 显示说明失败: {e}")

def test_supabase_api_connection():
    """测试 Supabase API 连接"""
    try:
        logger.info("🔍 测试 Supabase API 连接...")
        
        from supabase import create_client, Client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.error("❌ 缺少 Supabase 环境变量")
            return False
        
        supabase: Client = create_client(url, key)
        
        # 测试连接
        try:
            result = supabase.table('embeddings').select('*').limit(1).execute()
            logger.info("✅ Supabase API 连接成功！")
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
            logger.error(f"❌ Supabase API 连接失败: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ API 连接测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 测试 Supabase 数据库连接...")
    logger.info("=" * 50)
    
    # 检查 psql 是否可用
    psql_path = "/opt/homebrew/opt/postgresql@14/bin/psql"
    if not os.path.exists(psql_path):
        logger.error("❌ psql 不可用，请检查 PostgreSQL 安装")
        return
    
    logger.info("✅ psql 可用")
    
    # 测试 Supabase API 连接
    logger.info("\n🧪 测试 Supabase API 连接...")
    api_ok = test_supabase_api_connection()
    
    # 测试直接数据库连接
    logger.info("\n🧪 测试直接数据库连接...")
    db_ok = test_connection_without_password()
    
    # 显示连接说明
    logger.info("\n📋 连接说明:")
    show_connection_instructions()
    
    # 输出总结
    logger.info("\n" + "=" * 50)
    logger.info("📊 测试结果总结:")
    logger.info("=" * 50)
    
    if api_ok:
        logger.info("✅ Supabase API 连接正常")
    else:
        logger.error("❌ Supabase API 连接有问题")
    
    if db_ok:
        logger.info("✅ 直接数据库连接正常")
    else:
        logger.warning("⚠️ 直接数据库连接需要密码")
    
    logger.info("=" * 50)
    
    if api_ok:
        logger.info("🎉 Supabase 连接正常！")
        logger.info("💡 您可以使用 Supabase API 或获取密码后使用 Postgrestools")
    else:
        logger.error("❌ Supabase 连接有问题，请检查配置")

if __name__ == "__main__":
    main()
