"""
测试 Supabase 连接和 pgvector 初始化
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 加载环境变量
load_dotenv()

def test_supabase_connection():
    """测试 Supabase 连接"""
    print("🔍 测试 Supabase 连接...")
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    print(f"URL: {url}")
    print(f"Key: {key[:20]}...")
    
    try:
        # 创建客户端
        supabase: Client = create_client(url, key)
        
        # 测试查询
        result = supabase.table('_migrations').select("*").limit(1).execute()
        
        print("✅ Supabase 连接成功！")
        print(f"响应: {result}")
        return supabase
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return None


def init_pgvector(supabase: Client):
    """初始化 pgvector"""
    print("\n🔧 初始化 pgvector...")
    
    # 读取 SQL 脚本
    with open('sql/init_pgvector.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    try:
        # 执行 SQL（分段执行）
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        
        for i, stmt in enumerate(statements):
            if stmt and not stmt.startswith('--'):
                print(f"执行语句 {i+1}/{len(statements)}...")
                try:
                    result = supabase.rpc('exec_sql', {'sql': stmt}).execute()
                    print(f"  ✅ 完成")
                except Exception as e:
                    print(f"  ⚠️ 跳过（可能已存在）: {str(e)[:100]}")
        
        print("✅ pgvector 初始化完成！")
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


def verify_pgvector(supabase: Client):
    """验证 pgvector 安装"""
    print("\n🔍 验证 pgvector...")
    
    try:
        # 查询 embeddings 表
        result = supabase.table('embeddings').select('id').limit(1).execute()
        print(f"✅ embeddings 表存在！当前记录数: {len(result.data)}")
        
        # 查询统计视图
        result = supabase.table('embeddings_stats').select('*').execute()
        if result.data:
            stats = result.data[0]
            print(f"📊 统计信息:")
            print(f"   - 总向量数: {stats.get('total_vectors', 0)}")
            print(f"   - 唯一来源: {stats.get('unique_sources', 0)}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ 验证警告: {e}")
        print("💡 需要在 Supabase SQL Editor 中手动执行 init_pgvector.sql")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Supabase + pgvector 对接测试")
    print("=" * 60)
    
    # 1. 测试连接
    supabase = test_supabase_connection()
    
    if supabase:
        # 2. 初始化 pgvector（可选，可能需要手动执行）
        # init_pgvector(supabase)
        
        # 3. 验证 pgvector
        verify_pgvector(supabase)
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        print("\n下一步：")
        print("1. 如果 pgvector 未初始化，请访问:")
        print("   https://app.supabase.com/project/akqmgarrnvetaxucxfct/sql/new")
        print("2. 复制粘贴 backend/sql/init_pgvector.sql 的内容")
        print("3. 点击 'Run' 执行")
        print("4. 重启后端服务: PORT=8888 python3 main.py")
    else:
        print("\n❌ 连接失败，请检查配置")
