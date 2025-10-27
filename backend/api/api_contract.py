#!/usr/bin/env python3
"""
Wxauto Smart Service - 统一API契约定义
基于OpenAPI 3.0规范的接口定义
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import jwt
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = "wxauto-smart-service-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# 安全配置
security = HTTPBearer()

# 数据模型定义
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

class Statistics(BaseModel):
    """统计数据模型"""
    total_messages: int = Field(..., description="总消息数", ge=0)
    processed_messages: int = Field(..., description="已处理消息数", ge=0)
    error_rate: float = Field(..., description="错误率", ge=0.0, le=100.0)
    avg_response_time: float = Field(..., description="平均响应时间(秒)", ge=0.0)
    top_groups: List[Dict[str, Any]] = Field(default=[], description="活跃群聊排行")
    hourly_stats: List[Dict[str, Any]] = Field(default=[], description="小时统计")
    daily_stats: List[Dict[str, Any]] = Field(default=[], description="日统计")

class HeartbeatData(BaseModel):
    """心跳数据模型"""
    status: AgentStatus = Field(..., description="代理状态")
    timestamp: str = Field(..., description="心跳时间戳")
    config: ClientConfig = Field(..., description="当前配置")
    metrics: Optional[Dict[str, Any]] = Field(None, description="性能指标")

class ErrorReport(BaseModel):
    """错误报告模型"""
    error_id: str = Field(..., description="错误ID", example="err_123456")
    timestamp: str = Field(..., description="错误时间戳")
    level: str = Field(..., description="错误级别", example="ERROR")
    component: str = Field(..., description="组件名称", example="wxauto_agent")
    message: str = Field(..., description="错误消息")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    context: Optional[Dict[str, Any]] = Field(None, description="错误上下文")

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

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
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
    return {"agent_id": "default", "permissions": ["read", "write"]}

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

# 自定义OpenAPI文档
def custom_openapi(app: FastAPI):
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
        - 在请求头中添加: `Authorization: Bearer <token>`
        - Token通过登录接口获取
        
        ### Agent Key (本地代理)
        - 在请求头中添加: `Authorization: Bearer <agent_key>`
        - Agent Key在配置中设置
        
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
        {
            "name": "config",
            "description": "配置管理相关接口"
        },
        {
            "name": "monitor",
            "description": "监控相关接口"
        },
        {
            "name": "messages",
            "description": "消息相关接口"
        },
        {
            "name": "statistics",
            "description": "统计分析相关接口"
        },
        {
            "name": "agent",
            "description": "代理管理相关接口"
        },
        {
            "name": "logs",
            "description": "日志相关接口"
        },
        {
            "name": "health",
            "description": "健康检查相关接口"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# 错误处理装饰器
def handle_api_errors(func):
    """API错误处理装饰器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"服务器内部错误: {str(e)}"
            )
    return wrapper

# 请求ID中间件
@app.middleware("http")
async def add_request_id(request, call_next):
    """添加请求ID中间件"""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# 日志中间件
@app.middleware("http")
async def log_requests(request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    
    logger.info(f"请求开始: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"请求完成: {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

if __name__ == "__main__":
    app = create_app()
    app.openapi = custom_openapi(app)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
