"""
简化版 Supabase 连接测试
"""
import os
from supabase import create_client

# Supabase 配置
SUPABASE_URL = "https://akqmgarrnvetaxucxfct.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFrcW1nYXJybnZldGF4dWN4ZmN0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTU2ODk4NCwiZXhwIjoyMDc3MTQ0OTg0fQ.Dzu42Z4j57uFIM92THNENuAwYgBqQNSKZAQbwbsBiOg"

print("🔍 测试 Supabase 基础连接...")

try:
    # 创建客户端
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase 客户端创建成功！")
    
    # 测试简单查询
    print("\n🔍 测试数据库查询...")
    try:
        # 尝试查询 embeddings 表
        result = supabase.table('embeddings').select('*').limit(1).execute()
        print(f"✅ embeddings 表已存在！记录数: {len(result.data)}")
        
    except Exception as e:
        print(f"⚠️ embeddings 表不存在: {str(e)[:100]}")
        print("\n📝 需要在 Supabase 中执行初始化 SQL")
        print("\n请按以下步骤操作:")
        print("1. 访问: https://app.supabase.com/project/akqmgarrnvetaxucxfct/sql/new")
        print("2. 复制 backend/sql/init_pgvector.sql 的内容")
        print("3. 粘贴到 SQL Editor 并点击 'Run'")
        print("4. 重新运行此测试脚本")
    
    print("\n✅ Supabase 连接正常！")
    
except Exception as e:
    print(f"❌ 连接失败: {e}")

print("\n" + "="*60)
print("SQL 初始化脚本路径:")
print("backend/sql/init_pgvector.sql")
print("="*60)
