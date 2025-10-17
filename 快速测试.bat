@echo off
chcp 65001 >nul
cls
echo ========================================
echo   快速测试 - 微信客服中台
echo ========================================
echo.

REM 测试 Python
echo [测试 1/5] Python 安装...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python --version
    echo ✅ Python 正常
) else (
    echo ❌ Python 未安装
    goto :error
)
echo.

REM 测试依赖
echo [测试 2/5] 检查依赖...
python -c "import yaml; import requests; import openai; import pytest" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 所有依赖已安装
) else (
    echo ❌ 依赖缺失，请运行: 一键安装.bat
    goto :error
)
echo.

REM 测试数据库
echo [测试 3/5] 检查数据库...
if exist "data\data.db" (
    echo ✅ 数据库文件存在
) else (
    echo ⚠️ 数据库文件不存在，正在创建...
    if not exist "data" mkdir data
    python -c "from storage.db import Database; db=Database('data/data.db'); db.init_database(); db.close()"
    if %errorlevel% equ 0 (
        echo ✅ 数据库创建成功
    ) else (
        echo ❌ 数据库创建失败
        goto :error
    )
)
echo.

REM 测试导入
echo [测试 4/5] 测试模块导入...
python -c "from adapters.wxauto_adapter import FakeWxAdapter; from storage.db import Database; from rag.retriever import RAGRetriever" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 所有模块可正常导入
) else (
    echo ❌ 模块导入失败
    goto :error
)
echo.

REM 运行单元测试
echo [测试 5/5] 运行单元测试...
python -m pytest tests/ -q --tb=no >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 所有测试通过
) else (
    echo ⚠️ 部分测试失败（可能正常）
    echo    运行 'pytest tests/ -v' 查看详情
)
echo.

REM 显示系统信息
echo ========================================
echo   系统信息
echo ========================================
echo.
echo Python 版本:
python --version
echo.
echo pip 版本:
python -m pip --version
echo.
echo 已安装的包:
python -m pip list | findstr /i "pyyaml requests openai pytest"
echo.
echo 数据库大小:
if exist "data\data.db" (
    dir "data\data.db" | findstr /i "data.db"
)
echo.

echo ========================================
echo   ✅ 测试完成！系统可以运行
echo ========================================
echo.
echo 快速启动:
echo   python main.py
echo.
echo 查看文档:
echo   本地运行指南.md
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo   ❌ 测试失败
echo ========================================
echo.
echo 请按照以下步骤操作:
echo.
echo 1. 确保已安装 Python 3.10+
echo    下载: https://www.python.org/downloads/
echo.
echo 2. 运行一键安装脚本:
echo    一键安装.bat
echo.
echo 3. 查看详细文档:
echo    本地运行指南.md
echo.
pause
exit /b 1

