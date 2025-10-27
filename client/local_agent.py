#!/usr/bin/env python3
"""
Wxauto Smart Service - 本地微信代理
负责微信自动化交互和消息处理
集成通信模块、错误监控、日志上报
"""

import os
import sys
import json
import time
import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import traceback
import uuid

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

# 导入项目模块
from modules.adapters.wxauto_adapter import WxAutoAdapter, Message
from modules.ai_gateway.ai_router import AIRouter
from modules.storage.unified_database import UnifiedDatabaseManager

# 导入通信模块
from communication_module import (
    ServerCommunication, 
    ServerConfig, 
    LogReporter, 
    ErrorMonitor,
    WindowsTaskScheduler
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wxauto_agent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """代理配置"""
    server_url: str = "http://localhost:8000"
    api_key: str = ""
    whitelist_groups: List[str] = None
    enable_humanize: bool = True
    auto_reply: bool = True
    ai_model: str = "qwen"
    ai_api_key: str = ""
    heartbeat_interval: int = 30
    log_level: str = "INFO"
    
    def __post_init__(self):
        if self.whitelist_groups is None:
            self.whitelist_groups = []


@dataclass
class AgentStatus:
    """代理状态"""
    running: bool = False
    wechat_connected: bool = False
    server_connected: bool = False
    message_count: int = 0
    error_count: int = 0
    start_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None


class LocalWeChatAgent:
    """本地微信代理"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_file()
        self.config = self._load_config()
        self.status = AgentStatus()
        
        # 初始化组件
        self.wx_adapter: Optional[WxAutoAdapter] = None
        self.ai_router: Optional[AIRouter] = None
        self.db_manager: Optional[UnifiedDatabaseManager] = None
        
        # 消息队列
        self.message_queue: List[Message] = []
        self.processed_messages: List[Dict] = []
        
        # 线程控制
        self.message_thread: Optional[threading.Thread] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.running = False
        
        # 初始化通信模块
        self.server_config = ServerConfig(
            base_url=self.config.server_url,
            api_key=self.config.api_key,
            heartbeat_interval=self.config.heartbeat_interval
        )
        self.communication = ServerCommunication(self.server_config)
        self.log_reporter = LogReporter(self.communication)
        self.error_monitor = ErrorMonitor(self.communication)
        self.task_scheduler = WindowsTaskScheduler(self.communication)
        
        logger.info("🚀 本地微信代理初始化完成")
    
    def _get_default_config_file(self) -> str:
        """获取默认配置文件路径"""
        config_dir = Path.home() / ".wxauto-smart-service"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "agent_config.json")
    
    def _load_config(self) -> AgentConfig:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return AgentConfig(**data)
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
        
        # 返回默认配置
        return AgentConfig()
    
    def _save_config(self) -> bool:
        """保存配置"""
        try:
            config_dir = Path(self.config_file).parent
            config_dir.mkdir(exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            # 更新配置
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            # 保存配置
            if self._save_config():
                logger.info("✅ 配置更新成功")
                return True
            else:
                logger.error("❌ 配置保存失败")
                return False
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def initialize_components(self) -> bool:
        """初始化组件"""
        try:
            # 初始化微信适配器
            self.wx_adapter = WxAutoAdapter(
                whitelisted_groups=self.config.whitelist_groups,
                enable_humanize=self.config.enable_humanize
            )
            
            # 初始化AI路由器
            if self.config.ai_api_key:
                self.ai_router = AIRouter()
                # 配置AI模型
                self.ai_router.set_model_config(
                    model_name=self.config.ai_model,
                    api_key=self.config.ai_api_key
                )
            
            # 初始化数据库管理器
            self.db_manager = UnifiedDatabaseManager()
            
            logger.info("✅ 组件初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 组件初始化失败: {e}")
            return False
    
    async def start(self) -> bool:
        """启动代理"""
        if self.running:
            logger.warning("⚠️ 代理已在运行中")
            return True
        
        try:
            # 初始化通信模块
            if not await self.communication.initialize():
                logger.error("❌ 通信模块初始化失败")
                return False
            
            self.status.server_connected = True
            
            # 初始化组件
            if not self.initialize_components():
                return False
            
            # 设置微信消息监听
            self.wx_adapter.setup_message_listeners()
            self.status.wechat_connected = True
            
            # 启动消息处理线程
            self.message_thread = threading.Thread(target=self._message_loop, daemon=True)
            self.message_thread.start()
            
            # 更新状态
            self.running = True
            self.status.running = True
            self.status.start_time = datetime.now()
            
            self.log_reporter.report_log("INFO", "agent", "本地微信代理启动成功")
            logger.info("🚀 本地微信代理启动成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动代理失败: {e}")
            self.status.error_count += 1
            self.error_monitor.report_error(
                str(uuid.uuid4()), "ERROR", "agent", 
                f"启动代理失败: {e}", traceback.format_exc()
            )
            return False
    
    async def stop(self) -> bool:
        """停止代理"""
        if not self.running:
            logger.warning("⚠️ 代理未在运行")
            return True
        
        try:
            # 停止运行标志
            self.running = False
            
            # 清理微信适配器
            if self.wx_adapter:
                self.wx_adapter.cleanup()
            
            # 等待线程结束
            if self.message_thread and self.message_thread.is_alive():
                self.message_thread.join(timeout=5)
            
            # 清理通信模块
            await self.communication.cleanup()
            
            # 更新状态
            self.status.running = False
            self.status.wechat_connected = False
            self.status.server_connected = False
            
            self.log_reporter.report_log("INFO", "agent", "本地微信代理已停止")
            logger.info("⏹️ 本地微信代理已停止")
            return True
            
        except Exception as e:
            logger.error(f"❌ 停止代理失败: {e}")
            self.error_monitor.report_error(
                str(uuid.uuid4()), "ERROR", "agent", 
                f"停止代理失败: {e}", traceback.format_exc()
            )
            return False
    
    def _message_loop(self):
        """消息处理循环"""
        logger.info("📨 消息处理循环启动")
        
        while self.running:
            try:
                # 检查新消息
                for message in self.wx_adapter.iter_new_messages():
                    self._process_message(message)
                
                # 短暂休眠
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ 消息处理错误: {e}")
                self.status.error_count += 1
                self.error_monitor.report_error(
                    str(uuid.uuid4()), "ERROR", "message_loop", 
                    f"消息处理错误: {e}", traceback.format_exc()
                )
                time.sleep(1)
    
    def _process_message(self, message: Message):
        """处理单个消息"""
        try:
            logger.info(f"📨 收到消息: {message.group_name} - {message.sender_name}: {message.content[:50]}...")
            
            # 更新消息计数
            self.status.message_count += 1
            
            # 记录消息日志
            self.log_reporter.report_log(
                "INFO", "message_processor", 
                f"收到消息: {message.group_name} - {message.sender_name}",
                {
                    "group_name": message.group_name,
                    "sender_name": message.sender_name,
                    "content_length": len(message.content),
                    "timestamp": message.timestamp.isoformat()
                }
            )
            
            # 存储消息到数据库
            if self.db_manager:
                self._save_message_to_db(message)
            
            # 队列消息到通信模块
            message_data = {
                "id": str(uuid.uuid4()),
                "timestamp": message.timestamp.isoformat(),
                "group_name": message.group_name,
                "sender_name": message.sender_name,
                "content": message.content,
                "status": "received"
            }
            self.communication.queue_message(message_data)
            
            # 自动回复
            if self.config.auto_reply and self.ai_router:
                self._auto_reply(message)
            
            # 记录处理的消息
            processed_msg = {
                'timestamp': datetime.now().isoformat(),
                'group_name': message.group_name,
                'sender_name': message.sender_name,
                'content': message.content,
                'status': 'processed'
            }
            self.processed_messages.append(processed_msg)
            
            # 保持最近100条记录
            if len(self.processed_messages) > 100:
                self.processed_messages.pop(0)
            
        except Exception as e:
            logger.error(f"❌ 处理消息失败: {e}")
            self.status.error_count += 1
            self.error_monitor.report_error(
                str(uuid.uuid4()), "ERROR", "message_processor", 
                f"处理消息失败: {e}", traceback.format_exc(),
                {"message_content": message.content[:100]}
            )
    
    def _auto_reply(self, message: Message):
        """自动回复"""
        try:
            # 生成AI回复
            response = self.ai_router.generate_response(
                user_message=message.content,
                context="微信客服场景"
            )
            
            if response:
                # 发送回复
                success = self.wx_adapter.send_text(
                    group_name=message.group_name,
                    text=response,
                    at_user=message.sender_name
                )
                
                if success:
                    logger.info(f"✅ 自动回复成功: {response[:50]}...")
                else:
                    logger.error("❌ 自动回复失败")
            
        except Exception as e:
            logger.error(f"❌ 自动回复错误: {e}")
            self.status.error_count += 1
    
    def _save_message_to_db(self, message: Message):
        """保存消息到数据库"""
        try:
            # 这里可以调用数据库API保存消息
            # 暂时记录到日志
            logger.debug(f"💾 保存消息到数据库: {message.group_name}")
        except Exception as e:
            logger.error(f"❌ 保存消息到数据库失败: {e}")
    
    def _heartbeat_loop(self):
        """心跳循环"""
        logger.info("💓 心跳循环启动")
        
        while self.running:
            try:
                # 发送心跳到服务器
                self._send_heartbeat()
                
                # 等待下次心跳
                time.sleep(self.config.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"❌ 心跳错误: {e}")
                self.status.error_count += 1
                time.sleep(5)
    
    def _send_heartbeat(self):
        """发送心跳"""
        try:
            import requests
            
            heartbeat_data = {
                'status': asdict(self.status),
                'timestamp': datetime.now().isoformat(),
                'config': asdict(self.config)
            }
            
            response = requests.post(
                f"{self.config.server_url}/api/agent/heartbeat",
                json=heartbeat_data,
                headers={'Authorization': f'Bearer {self.config.api_key}'},
                timeout=10
            )
            
            if response.status_code == 200:
                self.status.server_connected = True
                self.status.last_heartbeat = datetime.now()
                logger.debug("💓 心跳发送成功")
            else:
                self.status.server_connected = False
                logger.warning(f"⚠️ 心跳发送失败: {response.status_code}")
            
        except Exception as e:
            self.status.server_connected = False
            logger.error(f"❌ 心跳发送错误: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        uptime = "00:00:00"
        if self.status.start_time:
            runtime = datetime.now() - self.status.start_time
            hours, remainder = divmod(runtime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        return {
            'service_running': self.status.running,
            'wechat_connected': self.status.wechat_connected,
            'server_connected': self.status.server_connected,
            'message_count': self.status.message_count,
            'error_count': self.status.error_count,
            'uptime': uptime,
            'last_heartbeat': self.status.last_heartbeat.isoformat() if self.status.last_heartbeat else None,
            'config': asdict(self.config)
        }
    
    def get_recent_messages(self, limit: int = 50) -> List[Dict]:
        """获取最近消息"""
        return self.processed_messages[-limit:]
    
    def get_logs(self, limit: int = 100) -> List[Dict]:
        """获取日志"""
        # 这里可以从日志文件读取
        # 暂时返回空列表
        return []


class AgentAPI:
    """代理API服务"""
    
    def __init__(self, agent: LocalWeChatAgent):
        self.agent = agent
    
    def start_api_server(self, host: str = "localhost", port: int = 8001):
        """启动API服务器"""
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
        
        app = FastAPI(title="Wxauto Agent API", version="2.1.0")
        
        # CORS中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/api/status")
        async def get_status():
            """获取代理状态"""
            return self.agent.get_status()
        
        @app.get("/api/messages/recent")
        async def get_recent_messages(limit: int = 50):
            """获取最近消息"""
            return self.agent.get_recent_messages(limit)
        
        @app.get("/api/logs")
        async def get_logs(limit: int = 100):
            """获取日志"""
            return self.agent.get_logs(limit)
        
        @app.post("/api/config")
        async def update_config(config: Dict[str, Any]):
            """更新配置"""
            if self.agent.update_config(config):
                return {"success": True, "message": "配置更新成功"}
            else:
                raise HTTPException(status_code=500, detail="配置更新失败")
        
        @app.post("/api/start")
        async def start_agent():
            """启动代理"""
            if self.agent.start():
                return {"success": True, "message": "代理启动成功"}
            else:
                raise HTTPException(status_code=500, detail="代理启动失败")
        
        @app.post("/api/stop")
        async def stop_agent():
            """停止代理"""
            if self.agent.stop():
                return {"success": True, "message": "代理停止成功"}
            else:
                raise HTTPException(status_code=500, detail="代理停止失败")
        
        # 启动服务器
        logger.info(f"🌐 API服务器启动: http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Wxauto Smart Service 本地微信代理")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--api-host", default="localhost", help="API服务器主机")
    parser.add_argument("--api-port", type=int, default=8001, help="API服务器端口")
    parser.add_argument("--no-api", action="store_true", help="不启动API服务器")
    
    args = parser.parse_args()
    
    logger.info("🚀 启动Wxauto Smart Service本地代理")
    
    # 创建代理实例
    agent = LocalWeChatAgent(args.config)
    
    try:
        # 启动代理
        if await agent.start():
            logger.info("✅ 代理启动成功")
            
            if not args.no_api:
                # 启动API服务器
                api = AgentAPI(agent)
                api.start_api_server(args.api_host, args.api_port)
            else:
                logger.info("📱 按Ctrl+C停止代理")
                # 保持运行
                while True:
                    await asyncio.sleep(1)
        else:
            logger.error("❌ 代理启动失败")
            return 1
            
    except KeyboardInterrupt:
        logger.info("👋 收到停止信号")
    except Exception as e:
        logger.error(f"❌ 运行错误: {e}")
        return 1
    finally:
        # 停止代理
        await agent.stop()
        logger.info("👋 代理已停止")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
