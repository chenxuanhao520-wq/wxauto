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

def test_supabase_connection():
    """测试 Supabase 数据库连接"""
    try:
        logger.info("🔍 测试 Supabase 数据库连接...")
        
        # 从环境变量获取信息
        url = os.getenv("SUPABASE_URL")
        if not url:
            logger.error("❌ 缺少 SUPABASE_URL 环境变量")
            return False
        
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
        
        # 构建 psql 命令
        psql_path = "/opt/homebrew/opt/postgresql@14/bin/psql"
        
        # 测试连接（不输入密码，让用户手动输入）
        logger.info("💡 请手动输入数据库密码")
        logger.info("💡 密码可以从 Supabase Dashboard > Settings > Database 获取")
        
        # 构建连接字符串
        connection_string = f"postgresql://{username}@{host}:{port}/{database}"
        
        logger.info(f"🔗 连接字符串: {connection_string}")
        
        # 执行连接测试
        cmd = [psql_path, connection_string, "-c", "SELECT version();"]
        
        logger.info("🚀 尝试连接数据库...")
        logger.info("💡 如果提示输入密码，请从 Supabase Dashboard 获取")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("✅ 数据库连接成功！")
                logger.info(f"📋 PostgreSQL 版本: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"❌ 数据库连接失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ 连接超时，可能需要输入密码")
            return False
        except Exception as e:
            logger.error(f"❌ 连接异常: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 测试连接失败: {e}")
        return False

def test_with_password():
    """使用密码测试连接"""
    try:
        logger.info("🔍 使用密码测试连接...")
        
        # 从环境变量获取信息
        url = os.getenv("SUPABASE_URL")
        if not url:
            logger.error("❌ 缺少 SUPABASE_URL 环境变量")
            return False
        
        project_ref = url.replace("https://", "").replace(".supabase.co", "")
        
        # 构建连接信息
        host = f"db.{project_ref}.supabase.co"
        port = "5432"
        database = "postgres"
        username = "postgres"
        
        # 提示用户输入密码
        password = input("请输入 Supabase 数据库密码: ")
        
        if not password:
            logger.error("❌ 密码不能为空")
            return False
        
        # 构建连接字符串
        connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        # 执行连接测试
        psql_path = "/opt/homebrew/opt/postgresql@14/bin/psql"
        cmd = [psql_path, connection_string, "-c", "SELECT version();"]
        
        logger.info("🚀 尝试连接数据库...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("✅ 数据库连接成功！")
                logger.info(f"📋 PostgreSQL 版本: {result.stdout.strip()}")
                
                # 测试查询表
                logger.info("🔍 测试查询表...")
                cmd2 = [psql_path, connection_string, "-c", "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"]
                
                result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
                
                if result2.returncode == 0:
                    logger.info("✅ 表查询成功！")
                    logger.info(f"📋 表列表:\n{result2.stdout}")
                else:
                    logger.warning(f"⚠️ 表查询失败: {result2.stderr}")
                
                return True
            else:
                logger.error(f"❌ 数据库连接失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ 连接超时")
            return False
        except Exception as e:
            logger.error(f"❌ 连接异常: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 测试连接失败: {e}")
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
    
    # 选择测试方式
    print("\n选择测试方式:")
    print("1. 手动输入密码测试")
    print("2. 显示连接信息")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        success = test_with_password()
    elif choice == "2":
        success = test_supabase_connection()
    else:
        logger.error("❌ 无效选择")
        return
    
    logger.info("\n" + "=" * 50)
    if success:
        logger.info("🎉 数据库连接测试成功！")
        logger.info("💡 现在您可以在 Postgrestools 中使用这些信息")
    else:
        logger.info("❌ 数据库连接测试失败")
        logger.info("💡 请检查密码和网络连接")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
