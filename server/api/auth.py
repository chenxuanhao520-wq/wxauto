#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API
处理客户端认证和Token管理
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

logger = logging.getLogger(__name__)

router = APIRouter()

# ✅ 修复：从环境变量读取配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production-at-least-32-chars")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24小时

# ✅ 修复：从环境变量读取有效客户端凭据
def _load_valid_agents():
    """从环境变量加载有效的客户端凭据"""
    credentials_str = os.getenv("VALID_AGENT_CREDENTIALS", "agent_001:test-api-key-001")
    valid_agents = {}
    for pair in credentials_str.split(","):
        if ":" in pair:
            agent_id, api_key = pair.strip().split(":", 1)
            valid_agents[agent_id] = api_key
    return valid_agents

VALID_AGENTS = _load_valid_agents()

# ✅ 添加：HTTP Bearer 认证
security = HTTPBearer()


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
    
    # ✅ 修复：从环境变量读取的凭据验证
    if data.agent_id not in VALID_AGENTS:
        logger.warning(f"未知的客户端: {data.agent_id}")
        raise HTTPException(status_code=401, detail="客户端ID无效")
    
    if VALID_AGENTS[data.agent_id] != data.api_key:
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


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    ✅ 新增：验证 JWT Token 的依赖函数
    
    Args:
        credentials: HTTP Bearer 凭据
    
    Returns:
        解码后的 payload
    
    Raises:
        HTTPException: Token 无效或过期
    """
    token = credentials.credentials
    
    try:
        # 验证并解码 JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        agent_id = payload.get("sub")
        
        if not agent_id:
            raise HTTPException(status_code=401, detail="Token payload 无效")
        
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token 已过期")
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.JWTError as e:
        logger.warning(f"Token 验证失败: {e}")
        raise HTTPException(status_code=401, detail="Token 无效")


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

