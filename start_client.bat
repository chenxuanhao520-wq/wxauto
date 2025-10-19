@echo off
chcp 65001 >nul
echo ==========================================
echo   微信客服中台 - 客户端启动脚本
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
pip install -q -r requirements_client.txt

REM 检查配置
echo [2/3] 检查配置...
if not exist "client\config\client_config.yaml" (
    echo ❌ 配置文件不存在: client\config\client_config.yaml
    echo 请先配置客户端
    pause
    exit /b 1
)

REM 创建日志目录
if not exist "logs\" mkdir logs

REM 启动客户端
echo [3/3] 启动客户端...
echo.
echo ==========================================
echo   客户端运行中
echo   按 Ctrl+C 停止
echo ==========================================
echo.

python client\main_client.py

pause

