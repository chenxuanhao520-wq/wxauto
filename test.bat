@echo off
chcp 65001 >nul
echo ========================================
echo   运行测试和健康检查
echo ========================================
echo.

:: 激活虚拟环境
if exist "venv\" (
    call venv\Scripts\activate.bat
) else (
    echo [错误] 请先运行 setup.bat
    pause
    exit /b 1
)

echo [1/3] 运行单元测试...
echo.
python -m pytest tests/ -v --tb=short
if errorlevel 1 (
    echo.
    echo [警告] 部分测试失败
    echo.
)

echo.
echo [2/3] 运行健康检查...
echo.
python ops_tools.py health

echo.
echo [3/3] 测试知识库检索...
echo.
python kb_manager.py --action search --query "如何安装设备"

echo.
echo ========================================
echo   测试完成
echo ========================================
pause

