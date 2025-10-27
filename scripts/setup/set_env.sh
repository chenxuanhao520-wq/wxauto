#!/bin/bash
# ==================== 环境变量设置脚本 ====================
# 使用方法: source set_env.sh

# ✅ 主力模型：Qwen-Turbo (速度快31.8%，质量4.5/5)
export QWEN_API_KEY=sk-1d7d593d85b1469683eb8e7988a0f646
export QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
export QWEN_MODEL=qwen-turbo

# ✅ 备用模型：GLM-4-Flash (完全免费，token精简45%)
export GLM_API_KEY=2853e43adea74724865746c7ddfcd7ad.qp589y9s3P2KRlI4
export GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
export GLM_MODEL=glm-4-flash

# AI Gateway 配置
export ENABLE_SMART_ROUTING=true
export PRIMARY_PROVIDER=qwen
export PRIMARY_MODEL=qwen-turbo
export FALLBACK_PROVIDER=glm
export FALLBACK_MODEL=glm-4-flash

# JWT 认证
export JWT_SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
export JWT_ALGORITHM=HS256
export JWT_EXPIRE_MINUTES=1440

# 客户端认证
export VALID_AGENT_CREDENTIALS=agent_001:test-api-key-001

# 数据库
export DATABASE_PATH=data/data.db

# 服务器
export SERVER_HOST=0.0.0.0
export SERVER_PORT=8000

# 智邦国际 ERP 配置
export ERP_BASE_URL="http://ls1.jmt.ink:46088"
export ERP_USERNAME="admin"
export ERP_PASSWORD="Abcd@1234"

echo "✅ 环境变量已设置"
echo "QWEN_API_KEY: ${QWEN_API_KEY:0:20}..."
echo "GLM_API_KEY: ${GLM_API_KEY:0:20}..."
echo ""
echo "现在可以运行:"
echo "  python3 test_all_fixes.py      # 运行测试"
echo "  python3 server/main_server.py  # 启动服务器"
echo "  python3 client/main_client.py  # 启动客户端"

