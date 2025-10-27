"""
直接执行 pgvector 初始化
"""
from supabase import create_client

# Supabase 配置
SUPABASE_URL = "https://akqmgarrnvetaxucxfct.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFrcW1nYXJybnZldGF4dWN4ZmN0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTU2ODk4NCwiZXhwIjoyMDc3MTQ0OTg0fQ.Dzu42Z4j57uFIM92THNENuAwYgBqQNSKZAQbwbsBiOg"

print("🚀 开始初始化 Supabase pgvector...")

# 创建客户端
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL 语句列表
sql_statements = [
    # 1. 启用 pgvector 扩展
    "CREATE EXTENSION IF NOT EXISTS vector",
    
    # 2. 创建向量嵌入表
    """CREATE TABLE IF NOT EXISTS embeddings (
        id BIGSERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        embedding vector(1536),
        metadata JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    
    # 3. 创建 HNSW 索引
    """CREATE INDEX IF NOT EXISTS embeddings_embedding_hnsw_idx 
       ON embeddings USING hnsw (embedding vector_cosine_ops)""",
    
    """CREATE INDEX IF NOT EXISTS embeddings_metadata_idx 
       ON embeddings USING GIN (metadata)""",
    
    """CREATE INDEX IF NOT EXISTS embeddings_created_at_idx 
       ON embeddings (created_at DESC)""",
    
    # 4. 创建搜索函数
    """CREATE OR REPLACE FUNCTION search_embeddings(
        query_embedding vector(1536),
        match_count int DEFAULT 10,
        filter jsonb DEFAULT '{}'::jsonb
    )
    RETURNS TABLE (
        id bigint,
        content text,
        similarity float,
        metadata jsonb
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            e.id,
            e.content,
            1 - (e.embedding <=> query_embedding) AS similarity,
            e.metadata
        FROM embeddings e
        WHERE (
            filter = '{}'::jsonb 
            OR e.metadata @> filter
        )
        ORDER BY e.embedding <=> query_embedding
        LIMIT match_count;
    END;
    $$""",
    
    # 5. 创建触发器函数
    """CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql'""",
    
    """DROP TRIGGER IF EXISTS update_embeddings_updated_at ON embeddings""",
    
    """CREATE TRIGGER update_embeddings_updated_at 
       BEFORE UPDATE ON embeddings 
       FOR EACH ROW 
       EXECUTE FUNCTION update_updated_at_column()""",
    
    # 6. 创建统计视图
    """CREATE OR REPLACE VIEW embeddings_stats AS
    SELECT 
        COUNT(*) as total_vectors,
        AVG(length(content)) as avg_content_length,
        COUNT(DISTINCT metadata->>'source') as unique_sources,
        MIN(created_at) as first_created,
        MAX(created_at) as last_created
    FROM embeddings"""
]

# 执行每条 SQL
success_count = 0
for i, sql in enumerate(sql_statements, 1):
    print(f"\n[{i}/{len(sql_statements)}] 执行 SQL...")
    print(f"SQL: {sql[:80]}...")
    
    try:
        # 使用 Supabase 的 PostgreSQL REST API
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        print(f"✅ 成功")
        success_count += 1
    except Exception as e:
        error_msg = str(e)
        if 'already exists' in error_msg or 'PGRST' in error_msg:
            # 尝试直接执行（某些 SQL 不需要 RPC）
            print(f"⚠️ RPC 方式失败，尝试直接执行...")
            print(f"   提示：{error_msg[:100]}")
        else:
            print(f"❌ 失败: {error_msg[:200]}")

print(f"\n{'='*60}")
print(f"执行完成！成功: {success_count}/{len(sql_statements)}")
print(f"{'='*60}")

# 验证结果
print("\n🔍 验证 embeddings 表...")
try:
    result = supabase.table('embeddings').select('*').limit(1).execute()
    print(f"✅ embeddings 表已就绪！当前记录: {len(result.data)}")
except Exception as e:
    print(f"⚠️ 需要手动执行 SQL: {e}")
    print("\n📝 请访问 Supabase SQL Editor:")
    print("https://app.supabase.com/project/akqmgarrnvetaxucxfct/sql/new")
    print("\n复制 backend/sql/init_pgvector.sql 的内容并执行")
