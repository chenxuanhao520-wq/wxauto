@echo off
chcp 65001 >nul
echo ========================================
echo   安装多模态支持（语音+图片）
echo ========================================
echo.
echo 此脚本将安装：
echo   - PaddleOCR（图片文字识别）
echo   - FunASR（语音识别，可选）
echo.
echo 注意：首次运行会下载模型文件（约500MB-1GB）
echo       需要稳定的网络连接
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

echo.
echo [1/3] 安装 PaddleOCR（图片识别）...
pip install paddleocr paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [警告] PaddleOCR 安装失败
    echo 您可以稍后手动安装：pip install paddleocr
) else (
    echo PaddleOCR 安装完成 ✓
)

echo.
echo [2/3] 安装文档解析工具...
pip install pymupdf python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple
echo 文档解析工具安装完成 ✓

echo.
echo [3/3] 安装 FunASR（语音识别）...
echo.
set /p INSTALL_ASR="是否安装FunASR？(如不需要语音识别可跳过) [Y/n]: "
if /i "%INSTALL_ASR%"=="n" goto skip_asr

echo 正在安装 FunASR（可能需要较长时间）...
pip install funasr -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [警告] FunASR 安装失败
    echo 您可以稍后手动安装：pip install funasr
) else (
    echo FunASR 安装完成 ✓
)

:skip_asr

echo.
echo ========================================
echo   多模态支持安装完成！
echo ========================================
echo.
echo 现在您可以：
echo   - 处理客户发送的语音消息
echo   - 识别故障截图中的文字
echo   - 上传PDF、DOC等格式的文档
echo.
echo 测试方法：
echo   python upload_documents.py upload --file your_file.pdf
echo.
pause

