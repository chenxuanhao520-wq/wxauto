#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心跳API
接收客户端心跳，监控客户端状态
"""

import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# 客户端状态存储（生产环境应使用Redis）
agent_status = {}


class HeartbeatRequest(BaseModel):
    """心跳请求"""
    agent_id: str
    status: Dict
    timestamp: str


@router.post("/heartbeat")
async def receive_heartbeat(data: HeartbeatRequest):
    """
    接收客户端心跳
    
    Args:
        data: 心跳数据
    
    Returns:
        确认响应
    """
    # 更新客户端状态
    agent_status[data.agent_id] = {
        'status': data.status,
        'last_heartbeat': datetime.now(),
        'timestamp': data.timestamp
    }
    
    logger.debug(f"💓 心跳: {data.agent_id}")
    
    return {
        'received': True,
        'server_time': datetime.now().isoformat()
    }


@router.get("/agents/status")
async def get_agents_status():
    """获取所有客户端状态"""
    return {
        'total': len(agent_status),
        'agents': agent_status
    }


@router.post("/errors")
async def receive_error(data: Dict):
    """
    接收客户端错误报告
    
    Args:
        data: 错误数据
    
    Returns:
        确认响应
    """
    agent_id = data.get('agent_id')
    error = data.get('error')
    
    logger.error(f"客户端错误 [{agent_id}]: {error}")
    
    # TODO: 保存到数据库，发送告警等
    
    return {
        'received': True,
        'error_id': 'generated_error_id'
    }

