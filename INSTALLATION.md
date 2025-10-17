# 📦 完整安装指南

根据您的需求选择安装方案。

---

## 🎯 方案选择

| 方案 | 适用场景 | 安装时间 | 依赖数量 |
|------|---------|---------|---------|
| **基础版** | 测试、演示 | 5分钟 | 3个 |
| **标准版** | 生产环境 | 15分钟 | 5个 |
| **企业版** | 大规模部署 | 30分钟 | 10+ |

---

## 🚀 方案A：基础版（推荐新手）

**功能**：微信监听 + 简单AI + BM25检索

### 安装步骤

```bash
# 1. 安装核心依赖
pip install pyyaml requests openai pytest

# 2. 初始化数据库
python -c "from storage.db import Database; db=Database('data/data.db'); db.init_database(); db.close()"

# 3. 添加示例知识库
python kb_manager.py --action add

# 4. 配置API Key（选一个）
export DEEPSEEK_API_KEY=sk-xxxxx  # 推荐，最便宜

# 5. 运行
python main.py
```

**成本**：~¥100/月  
**时间**：5分钟

---

## 🌟 方案B：标准版（推荐生产）

**功能**：基础版 + 对话追踪 + 多维表格

### 安装步骤

```bash
# 1. 安装所有基础依赖
pip install -r requirements.txt

# 2. 运行快速启动
python quickstart.py  # 自动初始化

# 3. 配置主备大模型
export OPENAI_API_KEY=sk-xxxxx      # 主
export DEEPSEEK_API_KEY=sk-xxxxx    # 备

# 4. 升级数据库（对话追踪）
sqlite3 data/data.db < sql/upgrade_v3.1.sql

# 5. 配置飞书表格（可选）
export FEISHU_APP_ID=cli_xxxxx
export FEISHU_APP_SECRET=xxxxx
export FEISHU_BITABLE_TOKEN=bascnxxxxx
export FEISHU_TABLE_ID=tblxxxxx

# 6. 测试
python sync_to_bitable.py test --platform feishu

# 7. 运行
python main.py
```

**成本**：~¥500/月  
**时间**：15分钟

---

## 🏢 方案C：企业版（大规模）

**功能**：标准版 + 向量检索 + 多格式文档

### 安装步骤

```bash
# 1. 安装基础依赖
pip install -r requirements.txt

# 2. 安装知识库依赖
pip install chromadb FlagEmbedding paddleocr pymupdf python-docx

# 注意：PaddleOCR 首次运行会下载模型（约200MB）

# 3. 运行快速启动
python quickstart.py

# 4. 上传文档到知识库
python upload_documents.py upload-dir --dir /path/to/your/documents/

# 5. 其他步骤同方案B
```

**成本**：~¥500-700/月  
**时间**：30分钟（模型下载时间）

---

## 📋 详细依赖说明

### 核心依赖（必需）

```bash
pyyaml>=6.0          # 配置文件
requests>=2.31.0     # HTTP请求
openai>=1.0.0        # 大模型API
pytest>=7.4.0        # 测试框架
```

### 微信依赖（Windows）

```bash
wxauto>=3.9.0        # 微信自动化（仅Windows）
```

### 可选依赖

#### 企业级知识库
```bash
chromadb>=0.4.0              # 向量数据库
FlagEmbedding>=1.2.0         # BGE-M3嵌入模型
pymupdf>=1.23.0              # PDF解析
python-docx>=0.8.11          # DOC解析
paddleocr>=2.7.0             # OCR（中文）
paddlepaddle>=2.5.0          # OCR依赖
```

#### 其他大模型
```bash
anthropic>=0.18.0            # Claude支持
```

#### 企业微信（防封号）
```bash
wechatpy>=1.8.0              # 企业微信SDK
```

---

## 🐛 常见安装问题

### Q1: PaddleOCR 安装失败

**Windows**：
```bash
# 先安装CPU版本
pip install paddlepaddle

# 再安装OCR
pip install paddleocr
```

**Mac/Linux**：
```bash
pip install paddlepaddle
pip install paddleocr
```

### Q2: chromadb 安装失败

```bash
# 尝试升级pip
pip install --upgrade pip

# 再安装
pip install chromadb
```

### Q3: FlagEmbedding 下载慢

首次运行会自动下载BGE-M3模型（约2GB），可能较慢。

**解决**：
1. 使用国内镜像加速
2. 或手动下载模型文件

### Q4: wxauto 无法使用

**原因**：wxauto 只支持 Windows + PC 微信

**解决**：
- Windows：正常安装
- Mac/Linux：使用测试模式 `USE_FAKE_ADAPTER=true`

---

## ✅ 安装验证

### 1. 运行测试

```bash
# 基础测试
pytest tests/ -v

# 应该看到：44+ passed
```

### 2. 健康检查

```bash
python ops_tools.py health

# 应该看到：
# ✅ 数据库正常
# ✅ AI 网关可用
# ✅ 知识库已加载
```

### 3. 功能演示

```bash
python demo.py

# 应该看到所有演示通过
```

---

## 📞 安装支持

如遇问题：

1. 查看 `logs/app.log`
2. 运行 `python ops_tools.py health`
3. 参考对应功能的文档

---

**安装完成后，查看 `FINAL_GUIDE.md` 了解如何使用所有功能！** 🚀

