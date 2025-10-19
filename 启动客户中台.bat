@echo off
chcp 65001 >nul
title 客户中台 - Customer Hub

echo ====================================
echo   客户中台启动脚本
echo ====================================
echo.

echo [1/3] 检查数据库...
if not exist "data" mkdir data
if not exist "data\data.db" (
    echo 首次运行，初始化数据库...
    sqlite3 data\data.db < sql\upgrade_customer_hub.sql
)

echo [2/3] 运行测试...
python test_customer_hub.py
if %errorlevel% neq 0 (
    echo 测试失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo [3/3] 启动 Web 服务...
echo.
echo 🎯 客户中台已启动！
echo.
echo 📱 访问地址:
echo    http://localhost:5000/customer-hub.html
echo.
echo 📡 API 文档:
echo    http://localhost:5000/api/hub/health
echo.
echo ⌨️  按 Ctrl+C 停止服务
echo.

python web_frontend.py

pause

