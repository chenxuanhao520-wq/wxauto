#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API
处理客户端认证和Token管理
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

logger = logging.getLogger(__name__)

router = APIRouter()

# JWT配置（生产环境应从环境变量读取）
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时


class LoginRequest(BaseModel):
    """登录请求"""
    agent_id: str
    api_key: str


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """
    客户端登录
    
    Args:
        data: 登录数据
    
    Returns:
        访问令牌
    """
    logger.info(f"登录请求: agent_id={data.agent_id}")
    
    # TODO: 验证agent_id和api_key
    # 这里简化处理，生产环境应从数据库验证
    valid_agents = {
        "agent_001": "your-api-key-here",
        "agent_002": "another-api-key"
    }
    
    if data.agent_id not in valid_agents:
        logger.warning(f"未知的客户端: {data.agent_id}")
        raise HTTPException(status_code=401, detail="客户端ID无效")
    
    if valid_agents[data.agent_id] != data.api_key:
        logger.warning(f"API Key错误: {data.agent_id}")
        raise HTTPException(status_code=401, detail="API Key错误")
    
    # 生成JWT Token
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": data.agent_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.info(f"✅ 登录成功: {data.agent_id}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """刷新Token"""
    try:
        # 验证并解码Token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        agent_id = payload.get("sub")
        
        # 生成新Token
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_token_data = {
            "sub": agent_id,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        new_token = jwt.encode(new_token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return TokenResponse(
            access_token=new_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token无效")

