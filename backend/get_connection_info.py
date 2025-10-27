#!/usr/bin/env python3
"""
获取 Supabase 数据库连接信息
"""

import os
import sys
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
    """获取 Supabase 连接信息"""
    try:
        logger.info("🔍 获取 Supabase 数据库连接信息...")
        
        # 从环境变量获取信息
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.error("❌ 缺少 Supabase 环境变量")
            return None
        
        # 解析 URL
        # Supabase URL 格式: https://project-ref.supabase.co
        # 数据库连接格式: postgresql://postgres:[password]@db.project-ref.supabase.co:5432/postgres
        
        project_ref = url.replace("https://", "").replace(".supabase.co", "")
        
        logger.info("📋 Supabase 连接信息:")
        logger.info(f"   Project URL: {url}")
        logger.info(f"   Project Ref: {project_ref}")
        logger.info(f"   API Key: {key[:10]}...{key[-10:]}")
        
        # 构建数据库连接字符串
        # 注意：您需要从 Supabase Dashboard 获取数据库密码
        db_host = f"db.{project_ref}.supabase.co"
        db_port = "5432"
        db_name = "postgres"
        db_user = "postgres"
        
        logger.info("\n🔗 数据库连接信息:")
        logger.info(f"   Host: {db_host}")
        logger.info(f"   Port: {db_port}")
        logger.info(f"   Database: {db_name}")
        logger.info(f"   Username: {db_user}")
        logger.info(f"   Password: [需要从 Supabase Dashboard 获取]")
        
        logger.info("\n💡 连接字符串格式:")
        logger.info(f"   postgresql://{db_user}:[PASSWORD]@{db_host}:{db_port}/{db_name}")
        
        logger.info("\n📝 获取密码的步骤:")
        logger.info("   1. 访问 https://supabase.com/dashboard")
        logger.info("   2. 选择您的项目")
        logger.info("   3. 进入 Settings > Database")
        logger.info("   4. 找到 'Connection string' 部分")
        logger.info("   5. 复制密码")
        
        return {
            "host": db_host,
            "port": db_port,
            "database": db_name,
            "username": db_user,
            "url": url,
            "project_ref": project_ref
        }
        
    except Exception as e:
        logger.error(f"❌ 获取连接信息失败: {e}")
        return None

def main():
    """主函数"""
    logger.info("🚀 获取 Supabase 数据库连接信息...")
    logger.info("=" * 50)
    
    connection_info = get_connection_info()
    
    if connection_info:
        logger.info("\n✅ 连接信息获取成功！")
        logger.info("💡 现在您可以在 Postgrestools 中使用这些信息连接数据库")
    else:
        logger.error("❌ 连接信息获取失败")

if __name__ == "__main__":
    main()
