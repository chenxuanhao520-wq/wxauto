@echo off
chcp 65001 >nul
echo ========================================
echo   微信客服中台 - 一键安装脚本
echo ========================================
echo.

REM 检查 Python 是否已安装
echo [1/6] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装！
    echo.
    echo 请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo ⚠️ 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo ✅ Python 已安装
python --version
echo.

REM 检查 pip
echo [2/6] 检查 pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip 不可用
    echo 正在安装 pip...
    python -m ensurepip --default-pip
)
echo ✅ pip 可用
echo.

REM 升级 pip
echo [3/6] 升级 pip...
python -m pip install --upgrade pip --quiet
echo ✅ pip 已升级
echo.

REM 安装核心依赖
echo [4/6] 安装核心依赖...
echo 正在安装: pyyaml, requests, openai, pytest
python -m pip install pyyaml requests openai pytest --quiet
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    echo 尝试使用国内镜像...
    python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyyaml requests openai pytest
)
echo ✅ 核心依赖安装完成
echo.

REM 创建数据目录
echo [5/6] 初始化数据库...
if not exist "data" mkdir data
python -c "from storage.db import Database; db=Database('data/data.db'); db.init_database(); db.close()"
if %errorlevel% equ 0 (
    echo ✅ 数据库初始化成功
) else (
    echo ⚠️ 数据库初始化可能失败，但继续...
)
echo.

REM 运行演示
echo [6/6] 运行功能演示...
python demo.py
echo.

REM 安装完成
echo ========================================
echo   🎉 安装完成！
echo ========================================
echo.
echo 后续步骤:
echo.
echo 1. 测试模式（无需配置）:
echo    python main.py
echo.
echo 2. 真实模式（需要配置 API Key）:
echo    set DEEPSEEK_API_KEY=sk-your-key
echo    set USE_FAKE_ADAPTER=false
echo    python main.py
echo.
echo 3. 查看知识库:
echo    python kb_manager.py --action list
echo.
echo 4. 健康检查:
echo    python ops_tools.py health
echo.
echo 5. 查看完整文档:
echo    - 本地运行指南.md
echo    - FINAL_GUIDE.md
echo    - START_HERE.md
echo.
echo ========================================
pause

