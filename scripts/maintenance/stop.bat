@echo off
chcp 65001 >nul
echo ========================================
echo   停止微信客服中台
echo ========================================
echo.

:: 查找Python进程
echo 正在查找运行中的进程...
tasklist | findstr /i "python.exe" >nul
if errorlevel 1 (
    echo 未找到运行中的程序
    pause
    exit /b 0
)

:: 显示进程
echo.
echo 找到以下Python进程：
tasklist | findstr /i "python.exe"
echo.

:: 确认
set /p CONFIRM="是否要停止所有Python进程？[Y/n]: "
if /i "%CONFIRM%"=="n" (
    echo 已取消
    pause
    exit /b 0
)

:: 停止进程
echo.
echo 正在停止进程...
taskkill /f /im python.exe >nul 2>&1

echo.
echo ========================================
echo   程序已停止
echo ========================================
pause

