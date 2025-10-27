#!/usr/bin/env python3
"""
Wxauto 智能客服中台 - 统一API服务入口
云原生架构：Supabase + Pinecone + AI Gateway
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# FastAPI 相关
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入核心模块
from modules.storage.unified_database import init_database_manager, get_database_manager
from modules.vector.pinecone_client import init_vector_search_service, get_vector_search_service
from modules.embeddings.unified_embedding_service import init_embedding_service, get_embedding_service
from modules.config.config_manager import init_config_manager, get_config_manager
from modules.auth.supabase_auth import init_auth, get_auth
from modules.storage.supabase_client import init_supabase_client, get_supabase_client

# 导入API路由
from modules.api.messages import router as messages_router
from modules.api.config import router as config_router
from modules.api.health import router as health_router
from modules.api.tenants import router as tenants_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局服务实例
app_state = {
    "database_manager": None,
    "vector_search_service": None,
    "embedding_service": None,
    "config_manager": None,
    "auth_service": None,
    "supabase_client": None,
    "realtime_client": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动 Wxauto 智能客服中台...")
    
    try:
        # 1. 初始化配置管理器
        logger.info("📋 初始化配置管理器...")
        config_manager = init_config_manager()
        app_state["config_manager"] = config_manager
        
        # 2. 初始化 Supabase 客户端
        logger.info("🗄️ 初始化 Supabase 客户端...")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.warning("⚠️ Supabase配置不完整，使用默认配置")
            supabase_url = "https://your-project.supabase.co"
            supabase_key = "your_supabase_anon_key"
            supabase_service_key = "your_supabase_service_role_key"
        
        init_supabase_client(supabase_url, supabase_key, supabase_service_key)
        app_state["supabase_client"] = get_supabase_client()
        
        # 3. 初始化数据库管理器
        logger.info("💾 初始化数据库管理器...")
        init_database_manager()
        app_state["database_manager"] = get_database_manager()
        
        # 4. 初始化认证服务
        logger.info("🔐 初始化认证服务...")
        init_auth(app_state["supabase_client"].client)
        app_state["auth_service"] = get_auth()
        
        # 5. 初始化向量搜索服务
        logger.info("🔍 初始化向量搜索服务...")
        try:
            init_vector_search_service()
            app_state["vector_search_service"] = get_vector_search_service()
            logger.info("✅ 向量搜索服务初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 向量搜索服务初始化失败: {e}")
            logger.info("💡 向量搜索功能将不可用")
        
        # 6. 初始化嵌入服务
        logger.info("🧠 初始化嵌入服务...")
        try:
            init_embedding_service()
            app_state["embedding_service"] = get_embedding_service()
            logger.info("✅ 嵌入服务初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 嵌入服务初始化失败: {e}")
            logger.info("💡 嵌入功能将不可用")
        
        # 7. 初始化实时服务
        logger.info("⚡ 初始化实时服务...")
        try:
            from modules.realtime.supabase_realtime import init_realtime_service, get_realtime_service
            init_realtime_service(app_state["supabase_client"].client)
            app_state["realtime_client"] = get_realtime_service()
            logger.info("✅ 实时服务初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 实时服务初始化失败: {e}")
            logger.info("💡 实时功能将不可用")
        
        logger.info("🎉 所有服务初始化完成！")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        raise
    finally:
        logger.info("👋 服务正在关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title="Wxauto 智能客服中台 API",
    description="基于 Supabase + Pinecone + AI Gateway 的云原生智能客服系统",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 依赖注入
def get_database_manager_dep():
    """获取数据库管理器依赖"""
    return app_state["database_manager"]


def get_vector_search_service_dep():
    """获取向量搜索服务依赖"""
    return app_state["vector_search_service"]


def get_embedding_service_dep():
    """获取嵌入服务依赖"""
    return app_state["embedding_service"]


def get_config_manager_dep():
    """获取配置管理器依赖"""
    return app_state["config_manager"]


def get_auth_service_dep():
    """获取认证服务依赖"""
    return app_state["auth_service"]


def get_supabase_client_dep():
    """获取 Supabase 客户端依赖"""
    return app_state["supabase_client"]


def get_realtime_service_dep():
    """获取实时服务依赖"""
    return app_state["realtime_client"]


# 注册路由
app.include_router(
    messages_router,
    prefix="/api/v1/messages",
    tags=["消息管理"],
    dependencies=[Depends(get_database_manager_dep)]
)

app.include_router(
    config_router,
    prefix="/api/v1/config",
    tags=["配置管理"],
    dependencies=[Depends(get_config_manager_dep)]
)

app.include_router(
    health_router,
    prefix="/api/v1/health",
    tags=["健康检查"]
)

app.include_router(
    tenants_router,
    prefix="/api/v1/tenants",
    tags=["租户管理"],
    dependencies=[Depends(get_database_manager_dep)]
)


# 静态文件服务
if Path("web/static").exists():
    app.mount("/static", StaticFiles(directory="web/static"), name="static")


# 根路径 - 返回配置管理界面
@app.get("/", response_class=HTMLResponse)
async def root():
    """返回配置管理界面"""
    try:
        config_template = Path("web/templates/config_management.html")
        if config_template.exists():
            return config_template.read_text(encoding="utf-8")
        else:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Wxauto 智能客服中台</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>🚀 Wxauto 智能客服中台</h1>
                <p>版本: 2.0.0</p>
                <p>架构: 云原生 (Supabase + Pinecone + AI Gateway)</p>
                <ul>
                    <li><a href="/docs">API 文档</a></li>
                    <li><a href="/redoc">ReDoc 文档</a></li>
                    <li><a href="/api/v1/health">健康检查</a></li>
                </ul>
            </body>
            </html>
            """
    except Exception as e:
        logger.error(f"❌ 返回根页面失败: {e}")
        return f"<h1>错误</h1><p>{e}</p>"


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查各个服务状态
        services_status = {
            "database": app_state["database_manager"] is not None,
            "vector_search": app_state["vector_search_service"] is not None,
            "embedding": app_state["embedding_service"] is not None,
            "config": app_state["config_manager"] is not None,
            "auth": app_state["auth_service"] is not None,
            "supabase": app_state["supabase_client"] is not None,
            "realtime": app_state["realtime_client"] is not None
        }
        
        all_healthy = all(services_status.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "version": "2.0.0",
            "services": services_status,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }


# 自定义 OpenAPI 文档
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Wxauto 智能客服中台 API",
        version="2.0.0",
        description="""
        ## Wxauto 智能客服中台 API
        
        基于云原生架构的智能客服系统，集成：
        - **Supabase**: 数据库和实时同步
        - **Pinecone**: 向量搜索和RAG
        - **AI Gateway**: 多模型智能路由
        - **配置管理**: 统一配置和实时同步
        
        ### 主要功能
        - 📱 微信消息处理
        - 🧠 AI智能回复
        - 🔍 知识库检索
        - ⚙️ 配置管理
        - 👥 多租户支持
        - 📊 实时监控
        """,
        routes=app.routes,
    )
    
    # 添加服务器信息
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "开发环境"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 启动服务器: http://{host}:{port}")
    logger.info(f"📚 API文档: http://{host}:{port}/docs")
    logger.info(f"🔧 配置管理: http://{host}:{port}/")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )