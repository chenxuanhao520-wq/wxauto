#!/usr/bin/env python3
"""
使用 Supabase API 获取数据库连接信息
"""

import os
import sys
import requests
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

def get_database_info_from_api():
    """从 Supabase API 获取数据库信息"""
    try:
        logger.info("🔍 尝试从 Supabase API 获取数据库信息...")
        
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not service_key:
            logger.error("❌ 缺少 Supabase 环境变量")
            return None
        
        # 解析项目引用
        project_ref = url.replace("https://", "").replace(".supabase.co", "")
        
        # 尝试获取项目信息
        headers = {
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json"
        }
        
        # 尝试访问项目 API
        project_url = f"https://api.supabase.com/v1/projects/{project_ref}"
        
        try:
            response = requests.get(project_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                project_info = response.json()
                logger.info("✅ 成功获取项目信息")
                logger.info(f"📋 项目信息: {project_info}")
                
                # 尝试获取数据库连接信息
                if 'database' in project_info:
                    db_info = project_info['database']
                    logger.info(f"📋 数据库信息: {db_info}")
                
                return project_info
            else:
                logger.warning(f"⚠️ 获取项目信息失败: {response.status_code}")
                logger.warning(f"   响应: {response.text}")
                
        except Exception as e:
            logger.warning(f"⚠️ API 调用失败: {e}")
        
        # 尝试其他方法获取连接信息
        logger.info("💡 尝试其他方法获取连接信息...")
        
        # 使用 Supabase 客户端
        from supabase import create_client, Client
        
        supabase: Client = create_client(url, service_key)
        
        # 尝试查询系统表
        try:
            # 查询数据库版本
            result = supabase.rpc('version').execute()
            logger.info(f"✅ 数据库版本查询成功: {result.data}")
        except Exception as e:
            logger.warning(f"⚠️ 版本查询失败: {e}")
        
        # 尝试查询表信息
        try:
            result = supabase.table('embeddings').select('*').limit(1).execute()
            logger.info(f"✅ embeddings 表查询成功: {len(result.data)} 条记录")
        except Exception as e:
            logger.warning(f"⚠️ embeddings 表查询失败: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"❌ 获取数据库信息失败: {e}")
        return None

def try_alternative_connection_methods():
    """尝试替代连接方法"""
    try:
        logger.info("🔍 尝试替代连接方法...")
        
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not service_key:
            logger.error("❌ 缺少 Supabase 环境变量")
            return False
        
        # 解析项目引用
        project_ref = url.replace("https://", "").replace(".supabase.co", "")
        
        logger.info(f"📋 项目引用: {project_ref}")
        
        # 尝试使用不同的连接方式
        connection_methods = [
            {
                "name": "直接连接",
                "host": f"db.{project_ref}.supabase.co",
                "port": "5432",
                "database": "postgres",
                "username": "postgres"
            },
            {
                "name": "Pooler 连接",
                "host": f"db.{project_ref}.supabase.co",
                "port": "6543",
                "database": "postgres",
                "username": "postgres"
            },
            {
                "name": "Session 连接",
                "host": f"db.{project_ref}.supabase.co",
                "port": "5432",
                "database": "postgres",
                "username": "postgres"
            }
        ]
        
        for method in connection_methods:
            logger.info(f"🧪 尝试 {method['name']} 连接...")
            logger.info(f"   Host: {method['host']}")
            logger.info(f"   Port: {method['port']}")
            logger.info(f"   Database: {method['database']}")
            logger.info(f"   Username: {method['username']}")
        
        logger.info("💡 所有方法都需要密码才能连接")
        logger.info("💡 建议从 Supabase Dashboard 获取密码")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ 替代连接方法失败: {e}")
        return False

def show_final_instructions():
    """显示最终说明"""
    logger.info("📋 最终连接说明:")
    logger.info("=" * 50)
    
    url = os.getenv("SUPABASE_URL")
    project_ref = url.replace("https://", "").replace(".supabase.co", "")
    
    logger.info("🔗 Postgrestools 连接信息:")
    logger.info(f"   Host: db.{project_ref}.supabase.co")
    logger.info("   Port: 5432")
    logger.info("   Database: postgres")
    logger.info("   Username: postgres")
    logger.info("   Password: [需要从 Supabase Dashboard 获取]")
    
    logger.info("\n💡 获取密码的详细步骤:")
    logger.info("1. 访问 https://supabase.com/dashboard")
    logger.info("2. 登录您的账户")
    logger.info("3. 选择您的项目")
    logger.info("4. 点击左侧菜单的 'Settings'")
    logger.info("5. 选择 'Database'")
    logger.info("6. 找到 'Connection string' 部分")
    logger.info("7. 复制连接字符串")
    logger.info("8. 从连接字符串中提取密码")
    
    logger.info("\n🔧 在 Postgrestools 中使用:")
    logger.info("1. 在 Cursor 中按 Cmd+Shift+P")
    logger.info("2. 输入 'Postgres Tools: Start'")
    logger.info("3. 选择 'Postgres Tools: Start'")
    logger.info("4. 添加新连接")
    logger.info("5. 输入上面的连接信息")
    logger.info("6. 输入从 Dashboard 获取的密码")
    
    logger.info("\n🎯 连接字符串示例:")
    logger.info(f"   postgresql://postgres:[PASSWORD]@db.{project_ref}.supabase.co:5432/postgres")
    
    logger.info("\n✅ 替代方案:")
    logger.info("1. 使用 Supabase Dashboard 的 SQL Editor")
    logger.info("2. 使用我们创建的 API 管理脚本")
    logger.info("3. 使用 Supabase CLI")

def main():
    """主函数"""
    logger.info("🚀 尝试启动 Postgres Tools 并获取连接信息...")
    logger.info("=" * 60)
    
    # 尝试从 API 获取数据库信息
    logger.info("\n🧪 尝试从 API 获取数据库信息...")
    api_info = get_database_info_from_api()
    
    # 尝试替代连接方法
    logger.info("\n🧪 尝试替代连接方法...")
    alternative_ok = try_alternative_connection_methods()
    
    # 显示最终说明
    logger.info("\n📋 最终说明:")
    show_final_instructions()
    
    # 输出总结
    logger.info("\n" + "=" * 60)
    logger.info("📊 启动尝试结果:")
    logger.info("=" * 60)
    
    if api_info:
        logger.info("✅ 成功获取项目信息")
    else:
        logger.info("⚠️ 无法自动获取数据库密码")
    
    logger.info("💡 需要手动从 Supabase Dashboard 获取密码")
    logger.info("💡 或者使用 Supabase Dashboard 的 SQL Editor")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
