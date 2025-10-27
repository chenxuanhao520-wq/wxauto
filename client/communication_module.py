#!/usr/bin/env python3
"""
Wxauto Smart Service - 本地代理通信模块
负责与后端服务器的所有通信，支持扩展和错误处理
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from queue import Queue, Empty

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """服务器配置"""
    base_url: str = "http://localhost:8000"
    api_key: str = ""
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    heartbeat_interval: int = 30


@dataclass
class CommunicationMetrics:
    """通信指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None
    last_success: Optional[datetime] = None


class ServerCommunication:
    """服务器通信模块"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.metrics = CommunicationMetrics()
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_connected = False
        self.last_heartbeat = None
        self.error_callbacks: List[Callable] = []
        self.success_callbacks: List[Callable] = []
        
        # 消息队列
        self.message_queue = Queue()
        self.log_queue = Queue()
        self.error_queue = Queue()
        
        # 后台线程
        self._background_threads = []
        self._running = False
        
        logger.info(f"🔗 服务器通信模块初始化: {config.base_url}")
    
    async def initialize(self) -> bool:
        """初始化通信模块"""
        try:
            # 创建HTTP会话
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "WxautoAgent/2.1.0"
                }
            )
            
            # 测试连接
            if await self._test_connection():
                self.is_connected = True
                self._start_background_tasks()
                logger.info("✅ 服务器通信模块初始化成功")
                return True
            else:
                logger.error("❌ 服务器连接测试失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 通信模块初始化失败: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        self._running = False
        
        # 等待后台线程结束
        for thread in self._background_threads:
            thread.join(timeout=5)
        
        # 关闭HTTP会话
        if self.session:
            await self.session.close()
        
        logger.info("🧹 服务器通信模块已清理")
    
    async def _test_connection(self) -> bool:
        """测试服务器连接"""
        try:
            async with self.session.get(f"{self.config.base_url}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ 服务器连接成功: {data.get('version', 'unknown')}")
                    return True
                else:
                    logger.error(f"❌ 服务器响应错误: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ 连接测试失败: {e}")
            return False
    
    def _start_background_tasks(self):
        """启动后台任务"""
        self._running = True
        
        # 心跳任务
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        self._background_threads.append(heartbeat_thread)
        
        # 消息上传任务
        message_thread = threading.Thread(target=self._message_upload_loop, daemon=True)
        message_thread.start()
        self._background_threads.append(message_thread)
        
        # 日志上传任务
        log_thread = threading.Thread(target=self._log_upload_loop, daemon=True)
        log_thread.start()
        self._background_threads.append(log_thread)
        
        # 错误上报任务
        error_thread = threading.Thread(target=self._error_report_loop, daemon=True)
        error_thread.start()
        self._background_threads.append(error_thread)
    
    def _heartbeat_loop(self):
        """心跳循环"""
        logger.info("💓 心跳循环启动")
        
        while self._running:
            try:
                # 准备心跳数据
                heartbeat_data = {
                    "status": {
                        "service_running": True,
                        "wechat_connected": True,
                        "server_connected": self.is_connected,
                        "message_count": self.metrics.total_requests,
                        "error_count": self.metrics.failed_requests,
                        "uptime": self._get_uptime(),
                        "last_heartbeat": datetime.now().isoformat(),
                        "version": "2.1.0"
                    },
                    "timestamp": datetime.now().isoformat(),
                    "metrics": asdict(self.metrics)
                }
                
                # 发送心跳
                asyncio.run(self._send_heartbeat(heartbeat_data))
                
                # 等待下次心跳
                time.sleep(self.config.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"❌ 心跳循环错误: {e}")
                time.sleep(5)
    
    async def _send_heartbeat(self, data: Dict[str, Any]) -> bool:
        """发送心跳"""
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/agent/heartbeat",
                json=data
            ) as response:
                if response.status == 200:
                    self.last_heartbeat = datetime.now()
                    self.metrics.successful_requests += 1
                    self._trigger_success_callbacks("heartbeat")
                    return True
                else:
                    self.metrics.failed_requests += 1
                    self._trigger_error_callbacks(f"心跳失败: {response.status}")
                    return False
        except Exception as e:
            self.metrics.failed_requests += 1
            self._trigger_error_callbacks(f"心跳错误: {e}")
            return False
    
    def _message_upload_loop(self):
        """消息上传循环"""
        logger.info("📨 消息上传循环启动")
        
        while self._running:
            try:
                # 批量处理消息
                messages = []
                for _ in range(10):  # 每次最多处理10条消息
                    try:
                        message = self.message_queue.get_nowait()
                        messages.append(message)
                    except Empty:
                        break
                
                if messages:
                    asyncio.run(self._upload_messages(messages))
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"❌ 消息上传循环错误: {e}")
                time.sleep(5)
    
    async def _upload_messages(self, messages: List[Dict[str, Any]]) -> bool:
        """上传消息"""
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/messages/batch",
                json={"messages": messages}
            ) as response:
                if response.status == 200:
                    self.metrics.successful_requests += 1
                    logger.info(f"✅ 上传 {len(messages)} 条消息成功")
                    return True
                else:
                    self.metrics.failed_requests += 1
                    logger.error(f"❌ 消息上传失败: {response.status}")
                    return False
        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error(f"❌ 消息上传错误: {e}")
            return False
    
    def _log_upload_loop(self):
        """日志上传循环"""
        logger.info("📋 日志上传循环启动")
        
        while self._running:
            try:
                # 批量处理日志
                logs = []
                for _ in range(20):  # 每次最多处理20条日志
                    try:
                        log = self.log_queue.get_nowait()
                        logs.append(log)
                    except Empty:
                        break
                
                if logs:
                    asyncio.run(self._upload_logs(logs))
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                logger.error(f"❌ 日志上传循环错误: {e}")
                time.sleep(10)
    
    async def _upload_logs(self, logs: List[Dict[str, Any]]) -> bool:
        """上传日志"""
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/logs/batch",
                json={"logs": logs}
            ) as response:
                if response.status == 200:
                    self.metrics.successful_requests += 1
                    logger.debug(f"✅ 上传 {len(logs)} 条日志成功")
                    return True
                else:
                    self.metrics.failed_requests += 1
                    logger.error(f"❌ 日志上传失败: {response.status}")
                    return False
        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error(f"❌ 日志上传错误: {e}")
            return False
    
    def _error_report_loop(self):
        """错误上报循环"""
        logger.info("🚨 错误上报循环启动")
        
        while self._running:
            try:
                # 处理错误
                errors = []
                for _ in range(5):  # 每次最多处理5个错误
                    try:
                        error = self.error_queue.get_nowait()
                        errors.append(error)
                    except Empty:
                        break
                
                if errors:
                    asyncio.run(self._report_errors(errors))
                
                time.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                logger.error(f"❌ 错误上报循环错误: {e}")
                time.sleep(15)
    
    async def _report_errors(self, errors: List[Dict[str, Any]]) -> bool:
        """上报错误"""
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/errors/batch",
                json={"errors": errors}
            ) as response:
                if response.status == 200:
                    self.metrics.successful_requests += 1
                    logger.info(f"✅ 上报 {len(errors)} 个错误成功")
                    return True
                else:
                    self.metrics.failed_requests += 1
                    logger.error(f"❌ 错误上报失败: {response.status}")
                    return False
        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error(f"❌ 错误上报错误: {e}")
            return False
    
    # 公共接口方法
    def queue_message(self, message: Dict[str, Any]):
        """队列消息"""
        self.message_queue.put(message)
        self.metrics.total_requests += 1
    
    def queue_log(self, log: Dict[str, Any]):
        """队列日志"""
        self.log_queue.put(log)
    
    def queue_error(self, error: Dict[str, Any]):
        """队列错误"""
        self.error_queue.put(error)
        self.metrics.failed_requests += 1
    
    def add_error_callback(self, callback: Callable):
        """添加错误回调"""
        self.error_callbacks.append(callback)
    
    def add_success_callback(self, callback: Callable):
        """添加成功回调"""
        self.success_callbacks.append(callback)
    
    def _trigger_error_callbacks(self, error_message: str):
        """触发错误回调"""
        for callback in self.error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                logger.error(f"❌ 错误回调执行失败: {e}")
    
    def _trigger_success_callbacks(self, event_type: str):
        """触发成功回调"""
        for callback in self.success_callbacks:
            try:
                callback(event_type)
            except Exception as e:
                logger.error(f"❌ 成功回调执行失败: {e}")
    
    def _get_uptime(self) -> str:
        """获取运行时间"""
        # 这里应该从代理启动时间计算
        return "02:30:45"  # 示例
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取通信指标"""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (
                self.metrics.successful_requests / max(self.metrics.total_requests, 1) * 100
            ),
            "avg_response_time": self.metrics.avg_response_time,
            "is_connected": self.is_connected,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }


class WindowsTaskScheduler:
    """Windows任务调度器扩展"""
    
    def __init__(self, communication: ServerCommunication):
        self.communication = communication
        self.scheduled_tasks = {}
    
    def schedule_task(self, task_name: str, schedule: str, task_data: Dict[str, Any]):
        """调度任务"""
        # 这里可以集成Windows任务调度器
        # 暂时简化实现
        self.scheduled_tasks[task_name] = {
            "schedule": schedule,
            "data": task_data,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"📅 任务已调度: {task_name} - {schedule}")
    
    def cancel_task(self, task_name: str):
        """取消任务"""
        if task_name in self.scheduled_tasks:
            del self.scheduled_tasks[task_name]
            logger.info(f"❌ 任务已取消: {task_name}")


class LogReporter:
    """日志上报器"""
    
    def __init__(self, communication: ServerCommunication):
        self.communication = communication
        self.log_buffer = []
        self.buffer_size = 100
    
    def report_log(self, level: str, component: str, message: str, details: Optional[Dict] = None):
        """上报日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "component": component,
            "message": message,
            "details": details or {}
        }
        
        self.log_buffer.append(log_entry)
        
        # 如果缓冲区满了，立即上报
        if len(self.log_buffer) >= self.buffer_size:
            self._flush_logs()
    
    def _flush_logs(self):
        """刷新日志缓冲区"""
        if self.log_buffer:
            for log in self.log_buffer:
                self.communication.queue_log(log)
            self.log_buffer.clear()


class ErrorMonitor:
    """错误监控器"""
    
    def __init__(self, communication: ServerCommunication):
        self.communication = communication
        self.error_count = 0
        self.last_error_time = None
    
    def report_error(self, error_id: str, level: str, component: str, 
                    message: str, stack_trace: Optional[str] = None, 
                    context: Optional[Dict] = None):
        """上报错误"""
        error_entry = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "component": component,
            "message": message,
            "stack_trace": stack_trace,
            "context": context or {}
        }
        
        self.communication.queue_error(error_entry)
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        logger.error(f"🚨 错误已上报: {error_id} - {message}")


# 使用示例
async def main():
    """使用示例"""
    # 创建配置
    config = ServerConfig(
        base_url="http://localhost:8000",
        api_key="your-api-key"
    )
    
    # 创建通信模块
    comm = ServerCommunication(config)
    
    # 添加回调
    comm.add_error_callback(lambda msg: logger.error(f"通信错误: {msg}"))
    comm.add_success_callback(lambda event: logger.info(f"通信成功: {event}"))
    
    # 初始化
    if await comm.initialize():
        # 创建扩展模块
        scheduler = WindowsTaskScheduler(comm)
        log_reporter = LogReporter(comm)
        error_monitor = ErrorMonitor(comm)
        
        # 使用示例
        log_reporter.report_log("INFO", "test", "测试日志")
        error_monitor.report_error("err_001", "ERROR", "test", "测试错误")
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("👋 收到退出信号")
        finally:
            await comm.cleanup()
    else:
        logger.error("❌ 通信模块初始化失败")


if __name__ == "__main__":
    asyncio.run(main())
