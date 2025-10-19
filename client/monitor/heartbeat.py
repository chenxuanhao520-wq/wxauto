#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心跳监控
保持与服务器的连接，上报客户端状态
"""

import logging
import asyncio
from typing import Dict, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    """心跳监控器"""
    
    def __init__(self, server_client, interval: int = 30):
        """
        初始化心跳监控
        
        Args:
            server_client: 服务器客户端实例
            interval: 心跳间隔（秒）
        """
        self.server_client = server_client
        self.interval = interval
        self.is_running = False
        self._task = None
        
        # 状态回调
        self.status_callback: Callable = None
    
    def set_status_callback(self, callback: Callable):
        """设置状态回调函数"""
        self.status_callback = callback
    
    async def start(self):
        """启动心跳监控"""
        if self.is_running:
            logger.warning("心跳监控已在运行")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"✅ 心跳监控已启动（间隔:{self.interval}秒）")
    
    async def stop(self):
        """停止心跳监控"""
        self.is_running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("心跳监控已停止")
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.is_running:
            try:
                # 收集状态
                status = self._collect_status()
                
                # 发送心跳
                success = await self.server_client.send_heartbeat(status)
                
                if success:
                    logger.debug("心跳发送成功")
                else:
                    logger.warning("心跳发送失败")
                
            except Exception as e:
                logger.error(f"心跳异常: {e}")
            
            # 等待下一个心跳
            await asyncio.sleep(self.interval)
    
    def _collect_status(self) -> Dict:
        """
        收集客户端状态
        
        Returns:
            状态数据
        """
        import psutil
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
        }
        
        # 如果有自定义状态回调，调用它
        if self.status_callback:
            try:
                custom_status = self.status_callback()
                status.update(custom_status)
            except Exception as e:
                logger.error(f"状态回调失败: {e}")
        
        return status

