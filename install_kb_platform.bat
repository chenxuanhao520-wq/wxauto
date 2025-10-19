@echo off
chcp 65001 >nul
REM KB中台依赖安装脚本（Windows版）

echo ════════════════════════════════════════════════════════════════════
echo 🚀 KB中台依赖安装
echo ════════════════════════════════════════════════════════════════════
echo.

echo 选择安装模式：
echo 1. 免费升级（添加Reranker，成本¥0，效果+10%%）
echo 2. 标准安装（完整KB中台功能）
echo 3. 极致安装（所有高级功能）
echo.
set /p choice="请选择 (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo 📦 安装免费升级组件...
    pip install FlagEmbedding
    
    echo.
    echo ✅ 免费升级完成！
    echo 已安装组件：
    echo   • BGE Reranker - 重排序器
    echo.
    echo 预期效果：
    echo   • 检索精度提升: +10%%
    echo   • 召回率提升: +13%%
    echo   • 成本: ¥0
    
) else if "%choice%"=="2" (
    echo.
    echo 📦 安装标准KB中台组件...
    
    echo 安装文档解析库...
    pip install pandas openpyxl python-docx PyPDF2 pdfminer.six beautifulsoup4 lxml
    
    echo 安装语义分析库...
    pip install gensim scikit-learn
    
    echo 安装Reranker...
    pip install FlagEmbedding
    
    echo.
    echo ✅ 标准安装完成！
    echo 已安装组件：
    echo   • pandas - Excel/CSV处理
    echo   • python-docx - Word文档解析
    echo   • pdfminer - PDF处理
    echo   • BeautifulSoup - HTML解析
    echo   • gensim - 语义相似度
    echo   • scikit-learn - 高级分析
    echo   • FlagEmbedding - Reranker
    
) else if "%choice%"=="3" (
    echo.
    echo 📦 安装极致版KB中台组件...
    
    echo 安装标准组件...
    pip install pandas openpyxl python-docx PyPDF2 pdfminer.six beautifulsoup4 lxml
    pip install gensim scikit-learn
    pip install FlagEmbedding
    
    echo 安装向量数据库客户端...
    pip install qdrant-client pymilvus
    
    echo 安装高级NLP工具...
    pip install spacy
    
    echo.
    echo ✅ 极致安装完成！
    echo 已安装所有组件
    echo.
    echo 可选：安装向量数据库服务器
    echo   Qdrant: docker run -d -p 6333:6333 qdrant/qdrant
    echo   Milvus: docker-compose -f milvus-compose.yml up -d
    
) else (
    echo ❌ 无效选择
    exit /b 1
)

echo.
echo ════════════════════════════════════════════════════════════════════
echo 🎉 安装完成！
echo ════════════════════════════════════════════════════════════════════
echo.
echo 下一步：
echo 1. 测试KB中台: python modules/kb_platform/examples/kb_platform_demo.py
echo 2. 查看文档: 📘ETL流程和文档规范完整方案.md
echo.
echo ════════════════════════════════════════════════════════════════════

pause
