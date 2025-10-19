@echo off
chcp 65001 >nul
echo ==========================================
echo   微信客服中台 - 服务器启动脚本
echo ==========================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装
    pause
    exit /b 1
)

REM 检查依赖
echo [1/3] 检查依赖...
if not exist "venv\" (
    echo 创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements_server.txt

REM 创建日志目录
echo [2/3] 创建日志目录...
if not exist "logs\" mkdir logs

REM 启动服务器
echo [3/3] 启动服务器...
echo.
echo ==========================================
echo   服务器运行中
echo   地址: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo   按 Ctrl+C 停止
echo ==========================================
echo.

cd server
python main_server.py

pause

