# ⚠️ API 密钥安全说明

## 🚨 紧急处理

如果您的 API 密钥已泄露到 Git 仓库，请立即执行以下步骤：

### 1. 立即更换密钥

- **Qwen (通义千问)**: https://dashscope.console.aliyun.com
- **GLM (智谱AI)**: https://open.bigmodel.cn

### 2. 清除 Git 历史中的密钥

```bash
# 方法 1: 使用 git filter-branch (适用于小仓库)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch cursor_glm_fix.py test_glm_config.py test_all_fixes.py env_example.txt" \
  --prune-empty --tag-name-filter cat -- --all

# 方法 2: 使用 BFG Repo-Cleaner (推荐，更快)
# 下载 BFG: https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --delete-files "cursor_glm_fix.py"
java -jar bfg.jar --delete-files "test_glm_config.py"
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送（谨慎！）
git push origin --force --all
```

---

## ✅ 正确使用 API 密钥

### 方法 1: 环境变量 (推荐)

```bash
# Linux/macOS
export QWEN_API_KEY=your-actual-key-here
export GLM_API_KEY=your-actual-key-here

# Windows PowerShell
$env:QWEN_API_KEY="your-actual-key-here"
$env:GLM_API_KEY="your-actual-key-here"

# Windows CMD
set QWEN_API_KEY=your-actual-key-here
set GLM_API_KEY=your-actual-key-here
```

### 方法 2: .env 文件 (已在 .gitignore 中)

1. 复制示例文件：
```bash
cp env_example.txt .env
```

2. 编辑 `.env` 文件，填写真实密钥：
```bash
QWEN_API_KEY=sk-your-real-key-here
GLM_API_KEY=your-real-glm-key-here
```

3. 确认 `.env` 在 .gitignore 中（已配置）：
```bash
# 检查 .gitignore
grep "\.env" .gitignore
```

---

## 🛡️ 安全检查清单

- [ ] 所有 API 密钥都从环境变量读取
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 测试文件中没有硬编码密钥
- [ ] Git 历史中没有密钥泄露
- [ ] 生产环境使用密钥管理服务（如 AWS Secrets Manager）

---

## 📁 安全的文件结构

```
✅ 安全（可以提交）:
- env_example.txt (示例，使用占位符)
- config.yaml (不包含密钥)
- README.md

❌ 危险（不要提交）:
- .env (包含真实密钥)
- config_production.yaml (包含真实密钥)
- *_secret.yaml
- 任何包含 API Key 的文件
```

---

## 🔒 生产环境最佳实践

### 1. 使用密钥管理服务

```python
# AWS Secrets Manager
import boto3
secrets = boto3.client('secretsmanager')
api_key = secrets.get_secret_value(SecretId='qwen-api-key')['SecretString']

# Azure Key Vault
from azure.keyvault.secrets import SecretClient
secret = client.get_secret("qwen-api-key").value

# Google Cloud Secret Manager
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = f"projects/{project_id}/secrets/qwen-api-key/versions/latest"
response = client.access_secret_version(request={"name": name})
api_key = response.payload.data.decode("UTF-8")
```

### 2. 使用加密存储

```python
# 使用 cryptography 加密密钥文件
from cryptography.fernet import Fernet

# 生成密钥（仅一次，保存到安全位置）
key = Fernet.generate_key()

# 加密
cipher = Fernet(key)
encrypted_api_key = cipher.encrypt(b"your-api-key")

# 解密
api_key = cipher.decrypt(encrypted_api_key).decode()
```

### 3. 限制 API Key 权限

- 启用 IP 白名单
- 设置使用配额
- 定期轮换密钥
- 监控异常使用

---

## 🚫 绝对不要做

1. ❌ 在代码中硬编码 API Key
2. ❌ 提交 `.env` 文件到 Git
3. ❌ 在日志中打印完整密钥
4. ❌ 通过 URL 参数传递密钥
5. ❌ 与他人共享密钥截图/聊天记录
6. ❌ 在公开的 Issue/PR 中粘贴密钥

---

## 📞 如果密钥已泄露

1. **立即更换密钥** (最高优先级)
2. **清除 Git 历史** (使用上述方法)
3. **检查账单** (确认是否有异常使用)
4. **启用告警** (设置使用量/费用告警)
5. **审查日志** (检查谁使用了泄露的密钥)

---

## 🔗 相关资源

- [GitHub 密钥扫描](https://docs.github.com/en/code-security/secret-scanning)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-secrets](https://github.com/awslabs/git-secrets)
- [truffleHog](https://github.com/trufflesecurity/trufflehog)

---

**记住：API 密钥泄露可能导致：**
- 💰 高额账单（他人恶意使用）
- 🔓 数据泄露
- ⛔ 账户被封禁
- ⚖️ 法律责任

**永远不要低估密钥安全的重要性！**

