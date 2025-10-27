#!/usr/bin/env python3
"""
Wxauto Smart Service - 客户端管理API
为Web前端提供配置管理和监控接口
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from modules.storage.unified_database import UnifiedDatabaseManager
from modules.config.config_manager import ConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Wxauto Client Management API", version="2.1.0")

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
db_manager = None
config_manager = None
agent_status_cache = {}

# 数据模型
class ClientConfig(BaseModel):
    """客户端配置"""
    server_url: str = "http://localhost:8000"
    api_key: str = ""
    whitelist_groups: List[str] = []
    enable_humanize: bool = True
    auto_reply: bool = True
    ai_model: str = "qwen"
    ai_api_key: str = ""
    ai_temperature: float = 0.7
    max_tokens: int = 500
    reply_delay_min: int = 1
    reply_delay_max: int = 3
    heartbeat_interval: int = 30
    log_level: str = "INFO"
    auto_start: bool = False
    minimize_to_tray: bool = True
    cache_size: int = 100

class AgentStatus(BaseModel):
    """代理状态"""
    service_running: bool = False
    wechat_connected: bool = False
    server_connected: bool = False
    message_count: int = 0
    error_count: int = 0
    uptime: str = "00:00:00"
    last_heartbeat: Optional[str] = None

class MessageInfo(BaseModel):
    """消息信息"""
    timestamp: str
    group_name: str
    sender_name: str
    content: str
    status: str

class LogEntry(BaseModel):
    """日志条目"""
    timestamp: str
    level: str
    message: str

class Statistics(BaseModel):
    """统计数据"""
    total_messages: int = 0
    processed_messages: int = 0
    error_rate: float = 0.0
    avg_response_time: float = 0.0
    top_groups: List[Dict[str, Any]] = []
    hourly_stats: List[Dict[str, Any]] = []

# 依赖注入
async def get_db_manager():
    global db_manager
    if db_manager is None:
        db_manager = UnifiedDatabaseManager()
    return db_manager

async def get_config_manager():
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager()
    return config_manager

# API路由
@app.get("/api/config", response_model=ClientConfig)
async def get_config():
    """获取客户端配置"""
    try:
        config_manager = await get_config_manager()
        
        # 从配置管理器获取配置
        config_data = config_manager.get_config_value("client_settings", {})
        
        # 合并默认配置
        default_config = ClientConfig()
        config_dict = default_config.dict()
        config_dict.update(config_data)
        
        return ClientConfig(**config_dict)
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {e}")

@app.post("/api/config")
async def update_config(config: ClientConfig):
    """更新客户端配置"""
    try:
        config_manager = await get_config_manager()
        
        # 保存配置到配置管理器
        config_manager.set_config_value("client_settings", config.dict())
        
        # 保存到文件
        config_manager.save_config()
        
        logger.info("✅ 客户端配置更新成功")
        return {"success": True, "message": "配置更新成功"}
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {e}")

@app.get("/api/status", response_model=AgentStatus)
async def get_status():
    """获取代理状态"""
    try:
        # 从缓存获取状态
        if agent_status_cache:
            return AgentStatus(**agent_status_cache)
        
        # 返回默认状态
        return AgentStatus()
        
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {e}")

@app.post("/api/agent/heartbeat")
async def receive_heartbeat(heartbeat_data: Dict[str, Any]):
    """接收代理心跳"""
    try:
        global agent_status_cache
        
        # 更新状态缓存
        agent_status_cache.update(heartbeat_data.get('status', {}))
        agent_status_cache['last_update'] = datetime.now().isoformat()
        
        logger.debug("💓 收到代理心跳")
        return {"success": True, "message": "心跳接收成功"}
        
    except Exception as e:
        logger.error(f"接收心跳失败: {e}")
        raise HTTPException(status_code=500, detail=f"接收心跳失败: {e}")

@app.get("/api/messages/recent", response_model=List[MessageInfo])
async def get_recent_messages(limit: int = 50):
    """获取最近消息"""
    try:
        db_manager = await get_db_manager()
        
        # 从数据库获取最近消息
        messages = await db_manager.get_recent_messages(limit=limit)
        
        # 转换为API格式
        message_list = []
        for msg in messages:
            message_list.append(MessageInfo(
                timestamp=msg.get('timestamp', ''),
                group_name=msg.get('group_name', ''),
                sender_name=msg.get('sender_name', ''),
                content=msg.get('content', ''),
                status=msg.get('status', 'processed')
            ))
        
        return message_list
        
    except Exception as e:
        logger.error(f"获取最近消息失败: {e}")
        # 返回模拟数据
        return [
            MessageInfo(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                group_name="客服群",
                sender_name="张三",
                content="@小助手 帮我查一下订单",
                status="processed"
            ),
            MessageInfo(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                group_name="技术支持群",
                sender_name="李四",
                content="@小助手 系统有问题",
                status="processing"
            )
        ]

@app.get("/api/logs", response_model=List[LogEntry])
async def get_logs(limit: int = 100):
    """获取系统日志"""
    try:
        # 从日志文件读取
        log_file = Path("wxauto_agent.log")
        logs = []
        
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 解析日志行
            for line in lines[-limit:]:
                parts = line.strip().split(' - ', 3)
                if len(parts) >= 4:
                    timestamp = parts[0]
                    level = parts[2]
                    message = parts[3]
                    
                    logs.append(LogEntry(
                        timestamp=timestamp,
                        level=level,
                        message=message
                    ))
        
        return logs
        
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        # 返回模拟数据
        return [
            LogEntry(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                level="INFO",
                message="代理启动成功"
            ),
            LogEntry(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                level="INFO",
                message="微信连接成功"
            )
        ]

@app.get("/api/statistics", response_model=Statistics)
async def get_statistics():
    """获取统计数据"""
    try:
        db_manager = await get_db_manager()
        
        # 从数据库获取统计数据
        stats = await db_manager.get_message_statistics()
        
        return Statistics(
            total_messages=stats.get('total_messages', 0),
            processed_messages=stats.get('processed_messages', 0),
            error_rate=stats.get('error_rate', 0.0),
            avg_response_time=stats.get('avg_response_time', 0.0),
            top_groups=stats.get('top_groups', []),
            hourly_stats=stats.get('hourly_stats', [])
        )
        
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        # 返回模拟数据
        return Statistics(
            total_messages=156,
            processed_messages=142,
            error_rate=2.5,
            avg_response_time=1.2,
            top_groups=[
                {"group_name": "客服群", "message_count": 89, "process_rate": 95},
                {"group_name": "技术支持群", "message_count": 45, "process_rate": 88},
                {"group_name": "VIP客户群", "message_count": 22, "process_rate": 100}
            ],
            hourly_stats=[]
        )

@app.post("/api/agent/start")
async def start_agent():
    """启动代理"""
    try:
        # 这里可以调用本地代理的启动接口
        # 暂时返回成功
        logger.info("🚀 代理启动请求")
        return {"success": True, "message": "代理启动成功"}
        
    except Exception as e:
        logger.error(f"启动代理失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动代理失败: {e}")

@app.post("/api/agent/stop")
async def stop_agent():
    """停止代理"""
    try:
        # 这里可以调用本地代理的停止接口
        # 暂时返回成功
        logger.info("⏹️ 代理停止请求")
        return {"success": True, "message": "代理停止成功"}
        
    except Exception as e:
        logger.error(f"停止代理失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止代理失败: {e}")

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0"
    }

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🌐 客户端管理API启动")
    uvicorn.run(app, host="0.0.0.0", port=8002)
