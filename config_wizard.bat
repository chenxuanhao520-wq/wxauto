@echo off
chcp 65001 >nul
echo ========================================
echo   配置向导
echo ========================================
echo.
echo 此向导将帮助您配置系统
echo.
pause

:: 创建.env文件
echo [1/4] 创建配置文件...
if exist ".env" (
    echo .env 文件已存在
    set /p OVERWRITE="是否覆盖？[y/N]: "
    if /i not "%OVERWRITE%"=="y" goto skip_env
)

(
echo # 微信客服中台配置
echo # 生成时间：%date% %time%
echo.
echo # ============================================
echo # 运行模式
echo # ============================================
echo.
echo # 测试模式（无需真实微信）
echo USE_FAKE_ADAPTER=true
echo.
echo # 真实模式（需要PC微信）
echo # USE_FAKE_ADAPTER=false
echo.
) > .env

echo .env 文件已创建 ✓
:skip_env

echo.

:: 配置大模型
echo [2/4] 配置大模型 API Key...
echo.
echo 请选择要使用的大模型：
echo   1. DeepSeek（推荐，最便宜 ¥0.1/百万tokens）
echo   2. OpenAI（质量最好）
echo   3. 通义千问（国内稳定）
echo   4. 其他（稍后手动配置）
echo.
set /p MODEL_CHOICE="请选择 [1-4]: "

if "%MODEL_CHOICE%"=="1" (
    echo.
    set /p DEEPSEEK_KEY="请输入DeepSeek API Key: "
    echo DEEPSEEK_API_KEY=!DEEPSEEK_KEY! >> .env
    echo DeepSeek 配置完成 ✓
)

if "%MODEL_CHOICE%"=="2" (
    echo.
    set /p OPENAI_KEY="请输入OpenAI API Key: "
    echo OPENAI_API_KEY=!OPENAI_KEY! >> .env
    echo OpenAI 配置完成 ✓
)

if "%MODEL_CHOICE%"=="3" (
    echo.
    set /p QWEN_KEY="请输入通义千问 API Key: "
    echo QWEN_API_KEY=!QWEN_KEY! >> .env
    echo 通义千问 配置完成 ✓
)

echo.

:: 配置白名单群
echo [3/4] 配置白名单群聊...
echo.
echo 当前配置的白名单群（config.yaml）：
type config.yaml | findstr "whitelisted_groups" -A 2
echo.
echo 如需修改，请编辑 config.yaml 文件
pause

echo.

:: 配置多维表格（可选）
echo [4/4] 配置多维表格（可选）...
echo.
set /p SETUP_FEISHU="是否配置飞书多维表格？[y/N]: "

if /i "%SETUP_FEISHU%"=="y" (
    echo.
    set /p FEISHU_APP_ID="飞书 App ID: "
    set /p FEISHU_APP_SECRET="飞书 App Secret: "
    set /p FEISHU_BITABLE_TOKEN="飞书 Bitable Token: "
    set /p FEISHU_TABLE_ID="飞书 Table ID: "
    
    echo. >> .env
    echo # 飞书多维表格配置 >> .env
    echo FEISHU_APP_ID=!FEISHU_APP_ID! >> .env
    echo FEISHU_APP_SECRET=!FEISHU_APP_SECRET! >> .env
    echo FEISHU_BITABLE_TOKEN=!FEISHU_BITABLE_TOKEN! >> .env
    echo FEISHU_TABLE_ID=!FEISHU_TABLE_ID! >> .env
    
    echo 飞书配置完成 ✓
)

echo.
echo ========================================
echo   配置完成！
echo ========================================
echo.
echo 配置已保存到 .env 文件
echo.
echo 下一步：
echo   1. 双击 start.bat 启动系统
echo   2. 或运行 test.bat 进行测试
echo.
pause

