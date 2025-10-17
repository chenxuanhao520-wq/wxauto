@echo off
chcp 65001 >nul
color 0A
cls

echo.
echo     ╔════════════════════════════════════════╗
echo     ║   微信客服中台 - 一键启动向导          ║
echo     ╚════════════════════════════════════════╝
echo.
echo   [√] 支持7个大模型（OpenAI/DeepSeek等）
echo   [√] 支持语音和图片识别
echo   [√] 支持飞书/钉钉数据同步
echo   [√] 完整的防封号机制
echo.
echo ════════════════════════════════════════════
echo.

:: 检查是否首次运行
if exist "data\data.db" goto already_setup

echo 检测到首次运行，开始自动安装...
echo.
pause

:: 运行安装
call setup.bat
if errorlevel 1 exit /b 1

echo.
echo ════════════════════════════════════════════
echo.

:already_setup

:: 配置向导
echo 正在启动配置向导...
echo.
call config_wizard.bat

:: 提示运行
echo.
echo ════════════════════════════════════════════
echo.
echo 准备就绪！
echo.
set /p START_NOW="是否立即启动系统？[Y/n]: "

if /i "%START_NOW%"=="n" (
    echo.
    echo 您可以稍后运行 start.bat 启动系统
    pause
    exit /b 0
)

:: 启动系统
call start.bat

