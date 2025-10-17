@echo off
chcp 65001 >nul
echo ========================================
echo   打包为 EXE 可执行文件
echo ========================================
echo.
echo 此脚本将使用 PyInstaller 将系统打包为exe文件
echo 打包后可以在没有Python环境的Windows电脑上运行
echo.
pause

:: 激活虚拟环境
if exist "venv\" (
    call venv\Scripts\activate.bat
) else (
    echo [错误] 请先运行 setup.bat
    pause
    exit /b 1
)

:: 安装PyInstaller
echo [1/3] 安装 PyInstaller...
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [错误] PyInstaller 安装失败
    pause
    exit /b 1
)
echo.

:: 创建spec文件
echo [2/3] 创建打包配置...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo block_cipher = None
echo.
echo a = Analysis^(
echo     ['main.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ^('config.yaml', '.'^),
echo         ^('sql/*.sql', 'sql'^),
echo     ],
echo     hiddenimports=[
echo         'yaml',
echo         'requests',
echo         'sqlite3',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^)
echo.
echo pyz = PYZ^(a.pure, a.zipped_data, cipher=block_cipher^)
echo.
echo exe = EXE^(
echo     pyz,
echo     a.scripts,
echo     [],
echo     exclude_binaries=True,
echo     name='WeChatCustomerService',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     console=True,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     icon='icon.ico'  # 如果有图标
echo ^)
echo.
echo coll = COLLECT^(
echo     exe,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     name='WeChatCustomerService',
echo ^)
) > main.spec

echo 配置文件已创建 ✓
echo.

:: 开始打包
echo [3/3] 开始打包（可能需要5-10分钟）...
echo.
pyinstaller main.spec --clean

if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 可执行文件位置：
echo   dist\WeChatCustomerService\WeChatCustomerService.exe
echo.
echo 使用方法：
echo   1. 将整个 dist\WeChatCustomerService 目录复制到目标电脑
echo   2. 确保目录包含：
echo      - WeChatCustomerService.exe
echo      - config.yaml
echo      - data\ 目录（会自动创建）
echo   3. 双击运行 WeChatCustomerService.exe
echo.
echo 注意：
echo   - 仍需要在Windows系统运行
echo   - 仍需要PC微信（如使用真实模式）
echo   - 需要配置环境变量（API Key等）
echo.
pause

