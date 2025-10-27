@echo off
chcp 65001 >nul
echo ========================================
echo   微信客服中台 - 云原生架构启动脚本
echo ========================================
echo.

:: 检查虚拟环境
if not exist "venv\" (
    echo [错误] 虚拟环境不存在！
    echo 请先运行 setup.bat 进行初始化
    pause
    exit /b 1
)

:: 激活虚拟环境
echo [1/5] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 检查Supabase配置
echo [2/5] 检查Supabase配置...
if "%SUPABASE_URL%"=="" (
    echo [错误] Supabase配置不完整！
    echo 请设置以下环境变量：
    echo   set SUPABASE_URL=https://your-project.supabase.co
    echo   set SUPABASE_ANON_KEY=your_supabase_anon_key
    echo   set SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
    echo.
    echo 或运行: python client/cloud_client.py --setup
    pause
    exit /b 1
) else (
    echo [信息] Supabase配置已就绪
)

:: 检查Pinecone配置
echo [3/5] 检查Pinecone配置...
if "%PINECONE_API_KEY%"=="" (
    echo [错误] Pinecone配置不完整！
    echo 请设置以下环境变量：
    echo   set PINECONE_API_KEY=your_pinecone_api_key
    echo   set PINECONE_ENVIRONMENT=us-west1-gcp-free
    echo   set PINECONE_INDEX_NAME=wxauto-messages
    echo.
    echo 获取API Key: https://app.pinecone.io/
    pause
    exit /b 1
) else (
    echo [信息] Pinecone配置已就绪
)

:: 检查AI模型配置
echo [4/5] 检查AI模型配置...
if "%OPENAI_API_KEY%"=="" if "%DEEPSEEK_API_KEY%"=="" if "%QWEN_API_KEY%"=="" (
    echo [警告] 未检测到大模型API Key
    echo 系统将使用测试模式（模板回复）
    echo.
    echo 建议设置至少一个API Key：
    echo   set DEEPSEEK_API_KEY=sk-your-key
    echo   set OPENAI_API_KEY=sk-your-key
    echo.
    pause
)

:: 启动云原生客户端
echo [5/5] 启动云原生客户端...
echo.
echo ========================================
echo   系统正在运行...
echo   按 Ctrl+C 停止
echo ========================================
echo.

python client/cloud_client.py

:: 程序结束
echo.
echo ========================================
echo   系统已停止
echo ========================================
pause

