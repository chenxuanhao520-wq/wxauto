# wxauto-smart-service 系统完整指南

## 🎉 系统概述

wxauto-smart-service 是一个基于 Supabase pgvector 的智能客服系统，支持微信自动化、RAG 知识库、多模型 AI 网关等功能。

## ✨ 核心特性

### 🔧 技术架构
- **向量数据库**: Supabase pgvector (替代 Pinecone)
- **AI 模型**: 支持 Qwen、DeepSeek、OpenAI 等多种模型
- **知识库**: 支持文档上传、向量搜索、智能检索
- **对话跟踪**: 完整的对话记录和分析
- **性能监控**: 实时性能监控和健康检查

### 🚀 主要功能
1. **智能客服**: 基于 RAG 的智能问答
2. **知识管理**: 文档上传、分类、搜索
3. **对话跟踪**: 对话记录、分析、满意度评估
4. **性能监控**: 系统性能实时监控
5. **健康检查**: 自动系统健康检查

## 📋 系统要求

### 环境要求
- Python 3.9+
- Node.js 16+
- PostgreSQL 14+ (通过 Supabase)

### 依赖服务
- Supabase 账户
- AI 模型 API 密钥 (Qwen/DeepSeek/OpenAI)

## 🛠️ 安装配置

### 1. 克隆项目
```bash
git clone https://github.com/chenxuanhao520-wq/wxauto.git
cd wxauto/wxauto-smart-service
```

### 2. 安装依赖
```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

### 3. 环境配置
```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑环境变量
vim backend/.env
```

### 4. 配置 Supabase
```bash
# 在 Supabase Dashboard 中:
# 1. 创建新项目
# 2. 获取项目 URL 和 API Key
# 3. 运行数据库初始化脚本
python3 backend/init_database.py
```

## 🔧 配置说明

### 环境变量配置
```bash
# Supabase 配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI 模型配置
QWEN_API_KEY=your-qwen-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
OPENAI_API_KEY=your-openai-api-key

# 其他配置
DEBUG=true
LOG_LEVEL=INFO
PORT=8888
```

### 数据库配置
```sql
-- 创建 embeddings 表
CREATE TABLE embeddings (
    id BIGINT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB
);

-- 创建搜索函数
CREATE OR REPLACE FUNCTION search_embeddings(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id BIGINT,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
)
LANGUAGE SQL
AS $$
    SELECT 
        id,
        content,
        1 - (embedding <=> query_embedding) AS similarity,
        metadata
    FROM embeddings
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
```

## 🚀 使用方法

### 1. 启动系统
```bash
# 启动后端
cd backend
python3 main.py

# 启动前端
cd frontend
npm run dev
```

### 2. 添加知识库
```bash
# 使用知识管理工具
python3 backend/system_enhancer.py
```

### 3. 测试系统
```bash
# 运行完整系统测试
python3 backend/test_complete_system.py

# 运行系统优化
python3 backend/system_optimizer.py
```

## 📊 系统监控

### 性能监控
- **搜索时间**: 平均 < 2 秒
- **响应时间**: 平均 < 5 秒
- **系统资源**: CPU < 80%, 内存 < 80%

### 健康检查
```bash
# 运行健康检查
python3 backend/system_enhancer.py
```

## 🔍 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查环境变量
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY

# 测试连接
python3 backend/test_db_connection.py
```

#### 2. 向量搜索失败
```bash
# 检查 pgvector 扩展
python3 backend/test_vector_db.py

# 重新初始化数据库
python3 backend/init_database.py
```

#### 3. AI 模型调用失败
```bash
# 检查 API 密钥
python3 backend/test_embedding_service.py

# 测试 AI 网关
python3 backend/test_complete_system.py
```

### 日志查看
```bash
# 查看系统日志
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log
```

## 📈 性能优化

### 向量搜索优化
1. **添加索引**: 为 embedding 列添加 HNSW 索引
2. **连接池**: 使用数据库连接池
3. **缓存机制**: 实现查询结果缓存
4. **批量处理**: 批量处理多个查询

### 系统优化
1. **资源监控**: 实时监控系统资源
2. **负载均衡**: 分布式部署
3. **数据分片**: 大数据量分片存储

## 🔐 安全配置

### API 安全
- 使用 HTTPS 连接
- API 密钥加密存储
- 请求频率限制
- 输入验证和过滤

### 数据安全
- 数据库访问控制
- 敏感数据加密
- 定期备份
- 访问日志记录

## 📚 API 文档

### 向量搜索 API
```python
# 搜索相似文档
result = supabase.rpc('search_embeddings', {
    'query_embedding': query_vector,
    'match_count': 5
}).execute()
```

### 知识管理 API
```python
# 添加文档
document = {
    "id": doc_id,
    "content": content,
    "embedding": embedding_vector,
    "metadata": metadata
}
result = supabase.table('embeddings').insert(document).execute()
```

## 🤝 贡献指南

### 开发环境
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

### 代码规范
- 使用 Python 3.9+ 语法
- 遵循 PEP 8 规范
- 添加适当的注释
- 编写单元测试

## 📞 技术支持

### 联系方式
- GitHub Issues: [项目 Issues](https://github.com/chenxuanhao520-wq/wxauto/issues)
- 邮箱: support@example.com

### 社区
- 技术讨论: GitHub Discussions
- 问题反馈: GitHub Issues
- 功能建议: GitHub Discussions

## 📄 许可证

本项目采用 MIT 许可证，详情请查看 [LICENSE](LICENSE) 文件。

## 🎯 路线图

### 近期计划
- [ ] 支持更多文档格式
- [ ] 添加多语言支持
- [ ] 优化搜索算法
- [ ] 增加用户管理

### 长期计划
- [ ] 微服务架构
- [ ] 容器化部署
- [ ] 机器学习优化
- [ ] 企业级功能

---

**最后更新**: 2025-10-28  
**版本**: v2.0.0  
**状态**: 生产就绪 ✅
