#!/usr/bin/env python3
"""
Wxauto Smart Service - 完善的后端API
支持JWT认证、CORS、错误监控、日志上报
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import jwt
import logging
import asyncio
from pathlib import Path
import json
import uuid

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = "wxauto-smart-service-secret-key-2025"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# 安全配置
security = HTTPBearer()

# 数据模型
class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名", example="admin")
    password: str = Field(..., description="密码", example="password")

class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")

class ClientConfig(BaseModel):
    """客户端配置模型"""
    server_url: str = Field(..., description="后端服务器地址", example="http://localhost:8000")
    api_key: str = Field(..., description="API密钥", example="your-api-key")
    whitelist_groups: List[str] = Field(default=[], description="白名单群聊", example=["客服群", "技术支持群"])
    enable_humanize: bool = Field(default=True, description="启用拟人化行为")
    auto_reply: bool = Field(default=True, description="启用自动回复")
    ai_model: str = Field(default="qwen", description="AI模型", example="qwen")
    ai_api_key: str = Field(..., description="AI API密钥")
    ai_temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="AI创造性程度")
    max_tokens: int = Field(default=500, ge=1, le=4000, description="最大回复长度")
    reply_delay_min: int = Field(default=1, ge=0, description="最小回复延迟(秒)")
    reply_delay_max: int = Field(default=3, ge=0, description="最大回复延迟(秒)")
    heartbeat_interval: int = Field(default=30, ge=10, le=300, description="心跳间隔(秒)")
    log_level: str = Field(default="INFO", description="日志级别", example="INFO")
    auto_start: bool = Field(default=False, description="开机自启动")
    minimize_to_tray: bool = Field(default=True, description="最小化到系统托盘")
    cache_size: int = Field(default=100, ge=10, le=1000, description="本地缓存大小(MB)")

class AgentStatus(BaseModel):
    """代理状态模型"""
    service_running: bool = Field(..., description="服务运行状态")
    wechat_connected: bool = Field(..., description="微信连接状态")
    server_connected: bool = Field(..., description="服务器连接状态")
    message_count: int = Field(..., description="今日消息数量", ge=0)
    error_count: int = Field(..., description="错误数量", ge=0)
    uptime: str = Field(..., description="运行时间", example="02:30:45")
    last_heartbeat: Optional[str] = Field(None, description="最后心跳时间")
    version: str = Field(default="2.1.0", description="代理版本")
    system_info: Optional[Dict[str, Any]] = Field(None, description="系统信息")

class MessageInfo(BaseModel):
    """消息信息模型"""
    id: str = Field(..., description="消息ID", example="msg_123456")
    timestamp: str = Field(..., description="时间戳", example="2025-10-27T19:30:00Z")
    group_name: str = Field(..., description="群聊名称", example="客服群")
    sender_name: str = Field(..., description="发送者名称", example="张三")
    content: str = Field(..., description="消息内容", example="@小助手 帮我查一下订单")
    status: str = Field(..., description="处理状态", example="processed")
    response: Optional[str] = Field(None, description="回复内容")
    processing_time: Optional[float] = Field(None, description="处理时间(秒)")

class LogEntry(BaseModel):
    """日志条目模型"""
    timestamp: str = Field(..., description="时间戳", example="2025-10-27T19:30:00Z")
    level: str = Field(..., description="日志级别", example="INFO")
    component: str = Field(..., description="组件名称", example="wxauto_agent")
    message: str = Field(..., description="日志消息", example="代理启动成功")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")

class ErrorReport(BaseModel):
    """错误报告模型"""
    error_id: str = Field(..., description="错误ID", example="err_123456")
    timestamp: str = Field(..., description="错误时间戳")
    level: str = Field(..., description="错误级别", example="ERROR")
    component: str = Field(..., description="组件名称", example="wxauto_agent")
    message: str = Field(..., description="错误消息")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    context: Optional[Dict[str, Any]] = Field(None, description="错误上下文")

class BatchLogRequest(BaseModel):
    """批量日志请求"""
    logs: List[LogEntry] = Field(..., description="日志列表")

class BatchErrorRequest(BaseModel):
    """批量错误请求"""
    errors: List[ErrorReport] = Field(..., description="错误列表")

class BatchMessageRequest(BaseModel):
    """批量消息请求"""
    messages: List[MessageInfo] = Field(..., description="消息列表")

class APIResponse(BaseModel):
    """统一API响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")

# JWT工具函数
def create_access_token(data: dict) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """验证JWT令牌"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_agent_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """验证Agent Key"""
    # 这里可以实现Agent Key验证逻辑
    # 暂时简化处理
    agent_key = credentials.credentials
    if agent_key == "default-agent-key":
        return {"agent_id": "default", "permissions": ["read", "write"]}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent Key无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 创建FastAPI应用
def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="Wxauto Smart Service API",
        description="微信智能客服中台 - 统一API接口",
        version="2.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # 前端开发服务器
            "http://localhost:3001",  # 前端备用端口
            "https://yourdomain.com",  # 生产环境域名
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    return app

# 创建应用实例
app = create_app()

# 请求ID中间件
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """添加请求ID中间件"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# 日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = datetime.now()
    
    logger.info(f"请求开始: {request.method} {request.url.path} - {request.state.request_id}")
    
    response = await call_next(request)
    
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"请求完成: {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s - {request.state.request_id}")
    
    return response

# 认证相关接口
@app.post("/api/auth/login", response_model=LoginResponse, tags=["auth"])
async def login(login_data: LoginRequest):
    """用户登录"""
    # 这里应该验证用户名和密码
    # 暂时简化处理
    if login_data.username == "admin" and login_data.password == "password":
        access_token = create_access_token(
            data={"sub": login_data.username, "type": "user"}
        )
        return LoginResponse(
            access_token=access_token,
            expires_in=JWT_EXPIRATION_HOURS * 3600
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

@app.post("/api/auth/agent-login", response_model=LoginResponse, tags=["auth"])
async def agent_login(agent_key: str):
    """代理登录"""
    if agent_key == "default-agent-key":
        access_token = create_access_token(
            data={"sub": "agent", "type": "agent"}
        )
        return LoginResponse(
            access_token=access_token,
            expires_in=JWT_EXPIRATION_HOURS * 3600
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent Key无效"
        )

# 配置管理接口
@app.get("/api/config", response_model=ClientConfig, tags=["config"])
async def get_config(current_user: dict = Depends(verify_jwt_token)):
    """获取客户端配置"""
    # 这里应该从数据库或配置文件读取
    return ClientConfig(
        server_url="http://localhost:8000",
        api_key="default-api-key",
        whitelist_groups=["客服群", "技术支持群"],
        ai_api_key="your-ai-api-key"
    )

@app.post("/api/config", response_model=APIResponse, tags=["config"])
async def update_config(
    config: ClientConfig, 
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_jwt_token)
):
    """更新客户端配置"""
    # 这里应该保存到数据库或配置文件
    background_tasks.add_task(save_config_to_storage, config.dict())
    
    return APIResponse(
        success=True,
        message="配置更新成功",
        data=config.dict()
    )

# 监控接口
@app.get("/api/status", response_model=AgentStatus, tags=["monitor"])
async def get_status(current_user: dict = Depends(verify_jwt_token)):
    """获取代理状态"""
    # 这里应该从代理获取实时状态
    return AgentStatus(
        service_running=True,
        wechat_connected=True,
        server_connected=True,
        message_count=156,
        error_count=2,
        uptime="02:30:45"
    )

@app.post("/api/agent/heartbeat", response_model=APIResponse, tags=["monitor"])
async def receive_heartbeat(
    heartbeat_data: dict,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_agent_key)
):
    """接收代理心跳"""
    # 处理心跳数据
    background_tasks.add_task(process_heartbeat, heartbeat_data)
    
    return APIResponse(
        success=True,
        message="心跳接收成功"
    )

# 消息接口
@app.get("/api/messages/recent", response_model=List[MessageInfo], tags=["messages"])
async def get_recent_messages(
    limit: int = 50,
    current_user: dict = Depends(verify_jwt_token)
):
    """获取最近消息"""
    # 这里应该从数据库获取
    return [
        MessageInfo(
            id="msg_001",
            timestamp=datetime.now().isoformat(),
            group_name="客服群",
            sender_name="张三",
            content="@小助手 帮我查一下订单",
            status="processed",
            response="好的，正在查询...",
            processing_time=1.2
        )
    ]

@app.post("/api/messages/batch", response_model=APIResponse, tags=["messages"])
async def upload_messages(
    batch_data: BatchMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_agent_key)
):
    """批量上传消息"""
    background_tasks.add_task(process_messages, batch_data.messages)
    
    return APIResponse(
        success=True,
        message=f"成功接收 {len(batch_data.messages)} 条消息"
    )

# 日志接口
@app.get("/api/logs", response_model=List[LogEntry], tags=["logs"])
async def get_logs(
    limit: int = 100,
    level: Optional[str] = None,
    current_user: dict = Depends(verify_jwt_token)
):
    """获取系统日志"""
    # 这里应该从日志文件或数据库读取
    return [
        LogEntry(
            timestamp=datetime.now().isoformat(),
            level="INFO",
            component="wxauto_agent",
            message="代理启动成功"
        )
    ]

@app.post("/api/logs/batch", response_model=APIResponse, tags=["logs"])
async def upload_logs(
    batch_data: BatchLogRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_agent_key)
):
    """批量上传日志"""
    background_tasks.add_task(process_logs, batch_data.logs)
    
    return APIResponse(
        success=True,
        message=f"成功接收 {len(batch_data.logs)} 条日志"
    )

# 错误接口
@app.post("/api/errors/batch", response_model=APIResponse, tags=["logs"])
async def upload_errors(
    batch_data: BatchErrorRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_jwt_token)
):
    """批量上传错误"""
    background_tasks.add_task(process_errors, batch_data.errors)
    
    return APIResponse(
        success=True,
        message=f"成功接收 {len(batch_data.errors)} 个错误"
    )

# 统计接口
@app.get("/api/statistics", response_model=Dict[str, Any], tags=["statistics"])
async def get_statistics(current_user: dict = Depends(verify_jwt_token)):
    """获取统计数据"""
    return {
        "total_messages": 156,
        "processed_messages": 142,
        "error_rate": 2.5,
        "avg_response_time": 1.2,
        "top_groups": [
            {"group_name": "客服群", "message_count": 89, "process_rate": 95},
            {"group_name": "技术支持群", "message_count": 45, "process_rate": 88}
        ]
    }

# 健康检查
@app.get("/api/health", tags=["health"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0",
        "uptime": "02:30:45"
    }

# 后台任务
async def save_config_to_storage(config: dict):
    """保存配置到存储"""
    logger.info("💾 保存配置到存储")
    # 这里实现配置保存逻辑

async def process_heartbeat(heartbeat_data: dict):
    """处理心跳数据"""
    logger.info("💓 处理心跳数据")
    # 这里实现心跳处理逻辑

async def process_messages(messages: List[MessageInfo]):
    """处理消息"""
    logger.info(f"📨 处理 {len(messages)} 条消息")
    # 这里实现消息处理逻辑

async def process_logs(logs: List[LogEntry]):
    """处理日志"""
    logger.info(f"📋 处理 {len(logs)} 条日志")
    # 这里实现日志处理逻辑

async def process_errors(errors: List[ErrorReport]):
    """处理错误"""
    logger.info(f"🚨 处理 {len(errors)} 个错误")
    # 这里实现错误处理逻辑

# 自定义OpenAPI文档
def custom_openapi():
    """自定义OpenAPI文档"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Wxauto Smart Service API",
        version="2.1.0",
        description="""
        # Wxauto Smart Service API
        
        微信智能客服中台的统一API接口，提供配置管理、监控、统计等功能。
        
        ## 认证方式
        
        ### JWT Token (Web前端)
        - 通过 `/api/auth/login` 获取访问令牌
        - 在请求头中添加: `Authorization: Bearer <token>`
        
        ### Agent Key (本地代理)
        - 通过 `/api/auth/agent-login` 获取访问令牌
        - 在请求头中添加: `Authorization: Bearer <agent_key>`
        
        ## 错误处理
        
        所有API都返回统一的错误格式：
        ```json
        {
            "success": false,
            "message": "错误描述",
            "data": null,
            "timestamp": "2025-10-27T19:30:00Z",
            "request_id": "req_123456"
        }
        ```
        
        ## 状态码
        
        - `200`: 成功
        - `400`: 请求参数错误
        - `401`: 未授权
        - `403`: 禁止访问
        - `404`: 资源不存在
        - `500`: 服务器内部错误
        """,
        routes=app.routes,
    )
    
    # 添加安全定义
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Token认证"
        },
        "AgentKeyAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "AgentKey",
            "description": "Agent Key认证"
        }
    }
    
    # 添加标签
    openapi_schema["tags"] = [
        {"name": "auth", "description": "认证相关接口"},
        {"name": "config", "description": "配置管理相关接口"},
        {"name": "monitor", "description": "监控相关接口"},
        {"name": "messages", "description": "消息相关接口"},
        {"name": "statistics", "description": "统计分析相关接口"},
        {"name": "logs", "description": "日志相关接口"},
        {"name": "health", "description": "健康检查相关接口"}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# 设置自定义OpenAPI
app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    logger.info("🌐 启动Wxauto Smart Service API服务器")
    uvicorn.run(app, host="0.0.0.0", port=8002)
