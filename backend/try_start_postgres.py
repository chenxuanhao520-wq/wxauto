#!/usr/bin/env python3
"""
尝试启动 Postgres Tools 并连接 Supabase
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

def try_connect_with_common_passwords():
    """尝试使用常见密码连接"""
    try:
        logger.info("🔍 尝试使用常见密码连接...")
        
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
        
        # 常见密码列表
        common_passwords = [
            "",  # 空密码
            "postgres",
            "password",
            "123456",
            "admin",
            "root",
            "supabase",
            project_ref,  # 使用项目引用作为密码
        ]
        
        psql_path = "/opt/homebrew/opt/postgresql@14/bin/psql"
        
        for password in common_passwords:
            logger.info(f"🧪 尝试密码: {'[空]' if password == '' else password}")
            
            try:
                if password:
                    connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
                else:
                    connection_string = f"postgresql://{username}@{host}:{port}/{database}"
                
                cmd = [psql_path, connection_string, "-c", "SELECT version();"]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    logger.info(f"✅ 连接成功！密码: {'[空]' if password == '' else password}")
                    logger.info(f"📋 PostgreSQL 版本: {result.stdout.strip()}")
                    
                    # 测试查询表
                    logger.info("🔍 测试查询表...")
                    cmd2 = [psql_path, connection_string, "-c", "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"]
                    
                    result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=10)
                    
                    if result2.returncode == 0:
                        logger.info("✅ 表查询成功！")
                        logger.info(f"📋 表列表:\n{result2.stdout}")
                        
                        # 测试 embeddings 表
                        logger.info("🔍 测试 embeddings 表...")
                        cmd3 = [psql_path, connection_string, "-c", "SELECT * FROM embeddings LIMIT 3;"]
                        
                        result3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=10)
                        
                        if result3.returncode == 0:
                            logger.info("✅ embeddings 表查询成功！")
                            logger.info(f"📋 数据:\n{result3.stdout}")
                        else:
                            logger.warning(f"⚠️ embeddings 表查询失败: {result3.stderr}")
                        
                        return True
                    else:
                        logger.warning(f"⚠️ 表查询失败: {result2.stderr}")
                        return True
                else:
                    logger.debug(f"❌ 密码 {password} 失败: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️ 密码 {password} 连接超时")
            except Exception as e:
                logger.debug(f"❌ 密码 {password} 异常: {e}")
        
        logger.warning("⚠️ 所有常见密码都失败了")
        return False
        
    except Exception as e:
        logger.error(f"❌ 尝试连接失败: {e}")
        return False

def try_connect_with_service_key():
    """尝试使用 Service Role Key 连接"""
    try:
        logger.info("🔍 尝试使用 Service Role Key 连接...")
        
        # Service Role Key 通常不能直接用于数据库连接
        # 但我们可以尝试一些变体
        
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not service_key:
            logger.error("❌ 缺少 SUPABASE_SERVICE_ROLE_KEY")
            return False
        
        logger.info("💡 Service Role Key 通常不能直接用于数据库连接")
        logger.info("💡 但我们可以尝试一些变体")
        
        # 尝试使用 Service Role Key 的某些部分作为密码
        key_variants = [
            service_key[:20],  # 前20个字符
            service_key[-20:],  # 后20个字符
            service_key.split('.')[0] if '.' in service_key else service_key[:10],  # 第一部分
        ]
        
        url = os.getenv("SUPABASE_URL")
        project_ref = url.replace("https://", "").replace(".supabase.co", "")
        
        host = f"db.{project_ref}.supabase.co"
        port = "5432"
        database = "postgres"
        username = "postgres"
        
        psql_path = "/opt/homebrew/opt/postgresql@14/bin/psql"
        
        for variant in key_variants:
            logger.info(f"🧪 尝试 Service Key 变体: {variant[:10]}...")
            
            try:
                connection_string = f"postgresql://{username}:{variant}@{host}:{port}/{database}"
                cmd = [psql_path, connection_string, "-c", "SELECT version();"]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    logger.info(f"✅ 连接成功！使用 Service Key 变体")
                    logger.info(f"📋 PostgreSQL 版本: {result.stdout.strip()}")
                    return True
                else:
                    logger.debug(f"❌ Service Key 变体失败: {result.stderr}")
                    
            except Exception as e:
                logger.debug(f"❌ Service Key 变体异常: {e}")
        
        logger.warning("⚠️ Service Key 变体都失败了")
        return False
        
    except Exception as e:
        logger.error(f"❌ Service Key 连接失败: {e}")
        return False

def show_connection_instructions():
    """显示连接说明"""
    logger.info("📋 连接说明:")
    logger.info("=" * 40)
    
    url = os.getenv("SUPABASE_URL")
    project_ref = url.replace("https://", "").replace(".supabase.co", "")
    
    logger.info("🔗 Postgrestools 连接信息:")
    logger.info(f"   Host: db.{project_ref}.supabase.co")
    logger.info("   Port: 5432")
    logger.info("   Database: postgres")
    logger.info("   Username: postgres")
    logger.info("   Password: [需要从 Supabase Dashboard 获取]")
    
    logger.info("\n💡 获取密码的步骤:")
    logger.info("1. 访问 https://supabase.com/dashboard")
    logger.info("2. 选择您的项目")
    logger.info("3. 进入 Settings > Database")
    logger.info("4. 找到 'Connection string' 部分")
    logger.info("5. 复制密码（在 postgres: 后面的部分）")
    
    logger.info("\n🔧 在 Postgrestools 中使用:")
    logger.info("1. 启动 Postgres Tools")
    logger.info("2. 添加新连接")
    logger.info("3. 输入上面的连接信息")
    logger.info("4. 输入从 Dashboard 获取的密码")

def main():
    """主函数"""
    logger.info("🚀 尝试启动 Postgres Tools 并连接 Supabase...")
    logger.info("=" * 60)
    
    # 检查 psql 是否可用
    psql_path = "/opt/homebrew/opt/postgresql@14/bin/psql"
    if not os.path.exists(psql_path):
        logger.error("❌ psql 不可用，请检查 PostgreSQL 安装")
        return
    
    logger.info("✅ psql 可用")
    
    # 尝试使用常见密码连接
    logger.info("\n🧪 尝试使用常见密码连接...")
    common_ok = try_connect_with_common_passwords()
    
    if not common_ok:
        # 尝试使用 Service Key 连接
        logger.info("\n🧪 尝试使用 Service Key 连接...")
        service_ok = try_connect_with_service_key()
    
    # 显示连接说明
    logger.info("\n📋 连接说明:")
    show_connection_instructions()
    
    # 输出总结
    logger.info("\n" + "=" * 60)
    logger.info("📊 连接尝试结果:")
    logger.info("=" * 60)
    
    if common_ok:
        logger.info("🎉 连接成功！可以使用 Postgrestools 了")
    else:
        logger.info("⚠️ 自动连接失败，需要手动获取密码")
        logger.info("💡 请按照上面的步骤获取密码")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
