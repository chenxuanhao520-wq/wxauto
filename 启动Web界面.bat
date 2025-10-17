@echo off
chcp 65001 >nul
echo ========================================
echo   微信客服中台 - Web 管理界面
echo ========================================
echo.

REM 设置 UTF-8 环境变量
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONPATH=%CD%

echo [信息] 正在启动 Web 管理界面...
echo [信息] Python 路径: C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe
echo.

echo 🚀 启动中...
echo.

REM 启动 Web 前端
"C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe" web_frontend.py

echo.
echo ========================================
echo   Web 界面已停止
echo ========================================
pause
