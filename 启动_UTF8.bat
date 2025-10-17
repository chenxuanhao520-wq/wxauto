@echo off
chcp 65001 >nul
echo ========================================
echo   微信客服中台 - UTF-8 启动脚本
echo ========================================
echo.

REM 设置 UTF-8 环境变量
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONPATH=%CD%

echo [信息] 已设置 UTF-8 环境变量
echo [信息] Python 路径: C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe
echo.

echo 选择运行模式:
echo 1. 快速启动 (quickstart.py)
echo 2. 演示程序 (demo.py)  
echo 3. 主程序 (main.py)
echo 4. 测试程序 (pytest)
echo.

set /p choice="请输入选择 (1-4): "

if "%choice%"=="1" (
    echo [启动] 运行快速启动脚本...
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe" quickstart.py
) else if "%choice%"=="2" (
    echo [启动] 运行演示程序...
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe" demo.py
) else if "%choice%"=="3" (
    echo [启动] 运行主程序...
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe" main.py
) else if "%choice%"=="4" (
    echo [启动] 运行测试程序...
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe" -m pytest tests/ -v
) else (
    echo [错误] 无效选择，默认运行主程序...
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe" main.py
)

echo.
echo ========================================
echo   程序已结束
echo ========================================
pause
