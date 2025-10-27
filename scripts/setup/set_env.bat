@echo off
REM ==================== 环境变量设置脚本 (Windows) ====================
REM 使用方法: set_env.bat

REM ✅ 主力模型：Qwen-Turbo (速度快31.8%%，质量4.5/5)
set QWEN_API_KEY=sk-1d7d593d85b1469683eb8e7988a0f646
set QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
set QWEN_MODEL=qwen-turbo

REM ✅ 备用模型：GLM-4-Flash (完全免费，token精简45%%)
set GLM_API_KEY=2853e43adea74724865746c7ddfcd7ad.qp589y9s3P2KRlI4
set GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
set GLM_MODEL=glm-4-flash

REM AI Gateway 配置
set ENABLE_SMART_ROUTING=true
set PRIMARY_PROVIDER=qwen
set PRIMARY_MODEL=qwen-turbo
set FALLBACK_PROVIDER=glm
set FALLBACK_MODEL=glm-4-flash

REM JWT 认证
set JWT_SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
set JWT_ALGORITHM=HS256
set JWT_EXPIRE_MINUTES=1440

REM 客户端认证
set VALID_AGENT_CREDENTIALS=agent_001:test-api-key-001

REM 数据库
set DATABASE_PATH=data/data.db

REM 服务器
set SERVER_HOST=0.0.0.0
set SERVER_PORT=8000

echo ✅ 环境变量已设置
echo QWEN_API_KEY: %QWEN_API_KEY:~0,20%...
echo GLM_API_KEY: %GLM_API_KEY:~0,20%...
echo.
echo 现在可以运行:
echo   python test_all_fixes.py      # 运行测试
echo   python server/main_server.py  # 启动服务器
echo   python client/main_client.py  # 启动客户端

