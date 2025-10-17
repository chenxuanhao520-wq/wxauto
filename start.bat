@echo off
chcp 65001 >nul
echo ========================================
echo   微信客服中台 - 启动脚本
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
echo [1/4] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 检查配置
echo [2/4] 检查配置...
if not exist "data\data.db" (
    echo [警告] 数据库不存在，正在创建...
    python -c "from storage.db import Database; db=Database('data/data.db'); db.init_database(); db.close()"
)

:: 检查环境变量
echo [3/4] 检查环境变量...
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

:: 启动主程序
echo [4/4] 启动主程序...
echo.
echo ========================================
echo   系统正在运行...
echo   按 Ctrl+C 停止
echo ========================================
echo.

python main.py

:: 程序结束
echo.
echo ========================================
echo   系统已停止
echo ========================================
pause

