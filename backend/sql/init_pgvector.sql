-- =====================================================
-- Supabase pgvector 初始化脚本
-- 替代 Pinecone，实现统一向量存储
-- =====================================================

-- 1. 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 创建向量嵌入表
CREATE TABLE IF NOT EXISTS embeddings (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI/DeepSeek 维度
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 创建索引
-- HNSW索引（高性能，推荐）
CREATE INDEX IF NOT EXISTS embeddings_embedding_hnsw_idx 
ON embeddings 
USING hnsw (embedding vector_cosine_ops);

-- B-tree索引（用于过滤）
CREATE INDEX IF NOT EXISTS embeddings_metadata_idx 
ON embeddings 
USING GIN (metadata);

CREATE INDEX IF NOT EXISTS embeddings_created_at_idx 
ON embeddings (created_at DESC);

-- 4. 创建向量搜索函数
CREATE OR REPLACE FUNCTION search_embeddings(
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
$$;

-- 5. 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_embeddings_updated_at 
BEFORE UPDATE ON embeddings 
FOR EACH ROW 
EXECUTE FUNCTION update_updated_at_column();

-- 6. 创建统计视图
CREATE OR REPLACE VIEW embeddings_stats AS
SELECT 
    COUNT(*) as total_vectors,
    AVG(length(content)) as avg_content_length,
    COUNT(DISTINCT metadata->>'source') as unique_sources,
    MIN(created_at) as first_created,
    MAX(created_at) as last_created
FROM embeddings;

-- 7. 授权（如果需要）
-- GRANT SELECT, INSERT, UPDATE, DELETE ON embeddings TO authenticated;
-- GRANT SELECT ON embeddings_stats TO authenticated;

-- 8. 注释
COMMENT ON TABLE embeddings IS 'Supabase pgvector向量嵌入表，替代Pinecone';
COMMENT ON COLUMN embeddings.embedding IS '1536维向量（OpenAI/DeepSeek/ZhipuAI）';
COMMENT ON FUNCTION search_embeddings IS '向量相似度搜索，支持元数据过滤';

-- 完成
SELECT 'Supabase pgvector 初始化完成！' AS status;
