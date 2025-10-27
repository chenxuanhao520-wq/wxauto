# 🔧 GLM 嵌入服务升级指南

## 📋 问题说明

当前数据库的 `embeddings` 表中的 `embedding` 字段被设置为 `vector(1536)` 维度，但智谱 GLM 的 `embedding-2` 模型生成的是 1024 维向量，导致维度不匹配。

## 🎯 解决方案

需要通过 Supabase Dashboard 手动修改数据库结构，将向量维度从 1536 改为 1024。

## 📝 操作步骤

### 1. 登录 Supabase Dashboard
- 访问：https://supabase.com/dashboard
- 选择您的项目

### 2. 进入 SQL Editor
- 点击左侧菜单的 "SQL Editor"
- 点击 "New query"

### 3. 执行以下 SQL 语句

```sql
-- 1. 删除现有的 embeddings 表
DROP TABLE IF EXISTS embeddings CASCADE;

-- 2. 创建新的 embeddings 表（1024 维）
CREATE TABLE embeddings (
    id BIGINT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1024) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 创建向量索引
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 4. 创建 search_embeddings 函数
CREATE OR REPLACE FUNCTION search_embeddings(
    query_embedding vector(1024),
    match_count int DEFAULT 5,
    similarity_threshold float DEFAULT 0.7
)
RETURNS TABLE (
    id BIGINT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT 
        embeddings.id,
        embeddings.content,
        embeddings.metadata,
        1 - (embeddings.embedding <=> query_embedding) AS similarity
    FROM embeddings
    WHERE 1 - (embeddings.embedding <=> query_embedding) > similarity_threshold
    ORDER BY embeddings.embedding <=> query_embedding
    LIMIT match_count;
$$;
```

### 4. 执行 SQL
- 点击 "Run" 按钮执行 SQL
- 确认所有语句都成功执行

## ✅ 验证步骤

执行完 SQL 后，运行以下命令验证：

```bash
cd "/Users/chenxuanhao/Desktop/wx au to/wxauto-smart-service/backend"
python3 build_glm_knowledge_base.py
```

## 🎉 预期结果

如果操作成功，您应该看到：
- ✅ GLM 嵌入生成成功: 1024 维
- ✅ 文档添加成功
- ✅ RAG 流程测试成功
- 📊 知识库构建完成: 8/8 条文档

## 🔍 技术细节

### GLM embedding-2 模型特性
- **向量维度**: 1024
- **API 端点**: https://open.bigmodel.cn/api/paas/v4/embeddings
- **模型名称**: embedding-2
- **相似度计算**: 余弦相似度

### 数据库结构
```sql
CREATE TABLE embeddings (
    id BIGINT PRIMARY KEY,                    -- 文档ID
    content TEXT NOT NULL,                    -- 文档内容
    embedding vector(1024) NOT NULL,         -- GLM 1024维向量
    metadata JSONB DEFAULT '{}'::jsonb,      -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🚀 完成后的功能

升级完成后，系统将具备：
- ✅ 真实的 AI 嵌入服务（GLM embedding-2）
- ✅ 1024 维向量搜索
- ✅ 语义相似度计算
- ✅ RAG 知识检索
- ✅ 充电桩专业知识库

## 💡 注意事项

1. **备份数据**: 执行 DROP TABLE 前，确保重要数据已备份
2. **API 限制**: GLM API 有调用频率限制，请合理使用
3. **成本控制**: 每次调用 GLM API 都会产生费用
4. **网络连接**: 确保网络连接稳定，避免 API 调用失败

## 🆘 如果遇到问题

1. **SQL 执行失败**: 检查 Supabase 项目权限
2. **API 调用失败**: 检查 GLM API Key 是否正确
3. **向量维度错误**: 确认 SQL 中的 `vector(1024)` 设置正确
4. **索引创建失败**: 检查 pgvector 扩展是否已安装

---

**完成这些步骤后，您的系统将使用真实的 GLM AI 嵌入模型，具备真正的语义搜索能力！** 🎉
