# GitHub 绑定指南

将项目上传到GitHub的完整步骤。

---

## 🚀 快速开始

### 方式1：使用命令行（推荐）

#### 步骤1：创建GitHub仓库

1. 访问：https://github.com/new
2. 仓库名称：`wechat-ai-customer-service`（或其他名称）
3. 描述：`智能微信客服中台 - 支持多模态、自适应学习的AI客服系统`
4. 选择：**Private**（私有仓库，保护代码）
5. **不要**勾选 "Initialize this repository with a README"
6. 点击 "Create repository"

#### 步骤2：配置Git（如果是首次使用）

```bash
# 设置用户名和邮箱
git config --global user.name "您的GitHub用户名"
git config --global user.email "您的GitHub邮箱"
```

#### 步骤3：提交现有代码

```bash
# 切换到项目目录
cd "/Users/chenxuanhao/Desktop/wx au to"

# 添加所有新文件
git add .

# 提交
git commit -m "feat: 完整的智能客服系统

功能：
- 7个大模型支持（OpenAI/DeepSeek/Claude等）
- 多模态处理（语音+图片识别）
- 自适应学习（用户画像+个性化回复）
- 对话效果追踪
- 飞书/钉钉多维表格集成
- 防封号机制
- Windows一键部署

技术栈：
- Python 3.10+
- SQLite
- RAG (BM25 + 向量检索)
- PaddleOCR + FunASR
- Chroma + BGE-M3"
```

#### 步骤4：绑定GitHub仓库

```bash
# 添加远程仓库（替换为您的GitHub仓库地址）
git remote add origin https://github.com/您的用户名/wechat-ai-customer-service.git

# 推送到GitHub
git push -u origin main

# 如果分支是master，使用：
# git push -u origin master
```

---

### 方式2：使用GitHub Desktop（图形界面）

1. 下载安装：https://desktop.github.com/
2. 登录GitHub账号
3. 点击 "Add" → "Add Existing Repository"
4. 选择项目目录：`/Users/chenxuanhao/Desktop/wx au to`
5. 点击 "Publish repository"
6. 选择 "Private"，点击确认

---

## 📝 推荐的仓库设置

### README.md（GitHub首页）

您的现有README.md已经很完善了，它会自动显示在GitHub仓库首页。

### .gitignore（已有）

项目已包含`.gitignore`，以下内容不会上传：
- `data/` - 数据库文件
- `logs/` - 日志文件
- `.env` - 环境变量（API密钥）
- `venv/` - 虚拟环境

### LICENSE（建议添加）

```bash
# 创建LICENSE文件（MIT许可证）
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 [您的名字]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

git add LICENSE
git commit -m "docs: add MIT license"
git push
```

---

## 🔐 保护敏感信息

### 确保这些文件不会上传

检查`.gitignore`是否包含：

```
# 环境变量和密钥
.env
*.env

# 数据库
data/
*.db
*.sqlite

# 日志
logs/
*.log

# Python
venv/
__pycache__/
*.pyc

# 备份文件
*.bak
MsgBackup.db
```

### 如果不小心上传了敏感信息

```bash
# 从Git历史中删除敏感文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（注意：会重写历史）
git push origin --force --all
```

---

## 📊 GitHub仓库优化

### 添加标签（Topics）

在GitHub仓库页面，点击 "Add topics"，添加：
- `ai`
- `chatbot`
- `wechat`
- `customer-service`
- `rag`
- `llm`
- `python`
- `adaptive-learning`

### 添加徽章（Badges）

在README.md开头添加：

```markdown
# 微信客服中台

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)
```

### 设置GitHub Actions（可选）

创建`.github/workflows/test.yml`用于自动化测试：

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.10
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest tests/ -v
```

---

## 🌟 推荐的分支策略

### 简单项目（当前）

```
main (生产环境)
```

### 如果团队协作

```
main (生产环境，保护分支)
  ↑
develop (开发分支)
  ↑
feature/* (功能分支)
```

设置分支保护：
1. GitHub仓库 → Settings → Branches
2. Add rule → Branch name pattern: `main`
3. 勾选 "Require pull request reviews before merging"

---

## 📦 日常使用

### 提交新代码

```bash
# 1. 查看修改
git status

# 2. 添加文件
git add .

# 3. 提交
git commit -m "feat: 添加新功能"

# 4. 推送
git push
```

### 提交信息规范

使用约定式提交（Conventional Commits）：

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试相关
chore: 构建/工具相关

示例：
feat: 添加企业微信适配器
fix: 修复频率控制bug
docs: 更新安装文档
```

### 查看历史

```bash
# 查看提交历史
git log --oneline --graph

# 查看特定文件的历史
git log --follow main.py
```

---

## 🔄 同步代码

### 从GitHub拉取更新

```bash
git pull origin main
```

### 克隆到其他电脑

```bash
git clone https://github.com/您的用户名/wechat-ai-customer-service.git
cd wechat-ai-customer-service
pip install -r requirements.txt
python quickstart.py
```

---

## 🐛 常见问题

### Q1: git push被拒绝

```bash
# 错误：Updates were rejected because the remote contains work
# 解决：先拉取再推送
git pull origin main --rebase
git push origin main
```

### Q2: 文件太大无法推送

```bash
# GitHub限制单个文件100MB
# 使用Git LFS处理大文件
git lfs install
git lfs track "*.db"
git lfs track "*.model"
```

### Q3: 不小心提交了敏感信息

```bash
# 从最后一次提交中删除
git rm --cached .env
git commit --amend
git push --force
```

### Q4: 想要更改提交信息

```bash
# 修改最后一次提交
git commit --amend -m "新的提交信息"
git push --force
```

---

## 📖 GitHub功能利用

### Issues（问题追踪）

用于：
- Bug报告
- 功能需求
- 开发计划

### Projects（项目管理）

创建看板：
```
TODO → In Progress → Done
```

### Wiki（文档）

存放：
- 详细开发文档
- API文档
- 使用案例

### Releases（版本发布）

发布稳定版本：
1. 打标签：`git tag -a v1.0.0 -m "Release v1.0.0"`
2. 推送标签：`git push origin v1.0.0`
3. GitHub上创建Release，附带说明

---

## 🎯 推荐的仓库结构（已完成）

您的项目结构已经很好：

```
wechat-ai-customer-service/
├── README.md                    # ⭐ 项目介绍
├── START_HERE.md               # 快速开始
├── FINAL_GUIDE.md              # 完整指南
├── FINAL_COMPLETE.md           # 完成总结
├── LICENSE                     # 许可证
├── requirements.txt            # 依赖
├── .gitignore                  # Git忽略
│
├── main.py                     # 主程序
├── config.yaml                 # 配置文件
│
├── adapters/                   # 适配器
├── ai_gateway/                 # AI网关
├── adaptive_learning/          # 自适应学习 ⭐
├── kb_service/                 # 知识库
├── multimodal/                 # 多模态
├── storage/                    # 存储
├── rag/                        # RAG
├── integrations/               # 集成
│
├── tests/                      # 测试
├── docs/                       # 文档
├── sql/                        # SQL脚本
│
├── *.bat                       # Windows脚本
└── *.py                        # 工具脚本
```

---

## 🎉 完成后

### 验证

1. 访问：`https://github.com/您的用户名/wechat-ai-customer-service`
2. 确认代码已上传
3. README.md正确显示
4. Topics已添加

### 分享

复制仓库链接分享：
```
https://github.com/您的用户名/wechat-ai-customer-service
```

---

## 📞 需要帮助？

如果遇到问题：
1. 查看GitHub文档：https://docs.github.com/
2. 或运行：`git help <command>`

---

**准备好了吗？让我们开始吧！** 🚀

