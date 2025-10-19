#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息处理API
接收客户端上报的消息，调用业务逻辑处理，返回结果
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class MessageRequest(BaseModel):
    """消息请求"""
    agent_id: str
    message: Dict
    timestamp: str


class MessageResponse(BaseModel):
    """消息响应"""
    action: str  # reply | ignore | transfer_human
    content: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict] = None


@router.post("/messages", response_model=MessageResponse)
async def process_message(request: Request, data: MessageRequest):
    """
    处理客户端上报的消息
    
    Args:
        data: 消息数据
    
    Returns:
        处理结果
    """
    logger.info(f"📨 收到消息: agent={data.agent_id}, msg_id={data.message.get('id', '')[:10]}...")
    
    try:
        # 获取消息服务
        message_service = request.app.state.message_service
        
        # 处理消息
        result = await message_service.process_message(
            agent_id=data.agent_id,
            message=data.message
        )
        
        logger.info(f"✅ 消息处理完成: action={result['action']}")
        
        return MessageResponse(**result)
    
    except Exception as e:
        logger.error(f"❌ 消息处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}/reply")
async def get_reply(request: Request, message_id: str):
    """获取消息的回复"""
    try:
        message_service = request.app.state.message_service
        
        # TODO: 从缓存或数据库获取回复
        reply = await message_service.get_cached_reply(message_id)
        
        if reply:
            return reply
        else:
            raise HTTPException(status_code=404, detail="回复未找到")
    
    except Exception as e:
        logger.error(f"获取回复失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_message(request: Request, data: Dict):
    """
    发送消息（服务器主动发送）
    
    Args:
        data: 包含chat_id和content
    
    Returns:
        发送结果
    """
    try:
        chat_id = data.get('chat_id')
        content = data.get('content')
        
        if not chat_id or not content:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # TODO: 实现主动发送逻辑
        # 可能需要通过WebSocket推送给对应的客户端
        
        return {
            'success': True,
            'message_id': 'generated_id'
        }
    
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

