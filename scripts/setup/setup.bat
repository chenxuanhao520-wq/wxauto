@echo off
chcp 65001 >nul
echo ========================================
echo   微信客服中台 - 安装脚本
echo ========================================
echo.
echo 此脚本将自动完成以下操作：
echo 1. 创建Python虚拟环境
echo 2. 安装所有依赖
echo 3. 初始化数据库
echo 4. 添加示例知识库
echo.
pause

:: 检查Python
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python！
    echo 请先安装 Python 3.10 或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo Python 检查通过 ✓
echo.

:: 创建虚拟环境
echo [2/6] 创建虚拟环境...
if exist "venv\" (
    echo 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    echo 虚拟环境创建完成 ✓
)
echo.

:: 激活虚拟环境
echo [3/6] 激活虚拟环境...
call venv\Scripts\activate.bat
echo.

:: 安装基础依赖
echo [4/6] 安装基础依赖（核心功能）...
pip install pyyaml requests openai pytest -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [错误] 依赖安装失败！
    pause
    exit /b 1
)
echo 基础依赖安装完成 ✓
echo.

:: 询问是否安装多模态支持
echo [5/6] 多模态支持（语音+图片识别）...
echo.
set /p INSTALL_MULTIMODAL="是否安装多模态支持？(推荐) [Y/n]: "
if /i "%INSTALL_MULTIMODAL%"=="n" goto skip_multimodal

echo 正在安装多模态依赖（可能需要5-10分钟）...
pip install paddleocr paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
echo PaddleOCR 安装完成 ✓

echo.
echo 注意：FunASR安装可能较慢，如需要请手动安装：
echo   pip install funasr
echo.

:skip_multimodal

:: 初始化数据库
echo [6/6] 初始化数据库...
if not exist "data\" mkdir data
if not exist "logs\" mkdir logs
if not exist "exports\" mkdir exports

python -c "from storage.db import Database; db=Database('data/data.db'); db.init_database(); db.close()"
if errorlevel 1 (
    echo [错误] 数据库初始化失败！
    pause
    exit /b 1
)
echo 数据库初始化完成 ✓
echo.

:: 添加示例知识库
echo 添加示例知识库...
python kb_manager.py --action add
echo.

:: 完成
echo ========================================
echo   安装完成！✓
echo ========================================
echo.
echo 后续步骤：
echo.
echo 1. 配置大模型 API Key（必需）：
echo    set DEEPSEEK_API_KEY=sk-your-deepseek-key
echo    或
echo    set OPENAI_API_KEY=sk-your-openai-key
echo.
echo 2. 配置微信模式：
echo    测试模式（无需真实微信）：
echo      set USE_FAKE_ADAPTER=true
echo    真实模式（需要PC微信）：
echo      set USE_FAKE_ADAPTER=false
echo.
echo 3. 运行系统：
echo    双击 start.bat
echo    或运行：python main.py
echo.
echo 4. 查看文档：
echo    START_HERE.md - 快速开始
echo    FINAL_GUIDE.md - 完整指南
echo.
pause

