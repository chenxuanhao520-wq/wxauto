#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信客服中台 - 服务器端主程序
FastAPI应用 - 处理所有业务逻辑
"""

import sys
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ✅ 修复：在导入阶段确保日志目录存在
Path("logs").mkdir(exist_ok=True)

from server.api import messages, auth, heartbeat, stats
from server.services.message_service import MessageService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/server.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    logger.info("="*60)
    logger.info("🚀 微信客服中台服务器启动")
    logger.info("="*60)
    
    # 初始化服务
    message_service = MessageService()
    app.state.message_service = message_service
    
    logger.info("✅ 服务初始化完成")
    
    yield
    
    # 关闭时
    logger.info("服务器关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title="微信客服中台服务器",
    description="处理AI对话、知识检索、规则引擎等复杂业务",
    version="2.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    logger.debug(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(messages.router, prefix="/api/v1", tags=["消息处理"])
app.include_router(heartbeat.router, prefix="/api/v1", tags=["心跳"])
app.include_router(stats.router, prefix="/api/v1", tags=["统计"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "微信客服中台服务器",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "wx-customer-service",
        "version": "2.0.0"
    }


import uvicorn
from src.api.http_api import app


def main(host: str = "0.0.0.0", port: int = 8000):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()

