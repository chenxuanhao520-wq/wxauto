"""
消息管理API - 统一消息处理接口
支持多租户、实时同步、AI智能回复
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, Field

from modules.storage.unified_database import UnifiedDatabaseManager, get_database_manager as get_database_manager_dep
from modules.vector.supabase_vector import VectorSearchService, get_vector_search_service as get_vector_search_service_dep
from modules.embeddings.unified_embedding_service import SmartEmbeddingService, get_embedding_service as get_embedding_service_dep
from modules.auth.supabase_auth import SupabaseAuth, get_auth as get_auth_dep

logger = logging.getLogger(__name__)

router = APIRouter()


# 请求/响应模型
class MessageRequest(BaseModel):
    """消息请求模型"""
    request_id: str = Field(..., description="请求ID")
    group_id: str = Field(..., description="群组ID")
    sender_id: str = Field(..., description="发送者ID")
    user_message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    group_name: Optional[str] = Field(None, description="群组名称")
    sender_name: Optional[str] = Field(None, description="发送者名称")


class MessageResponse(BaseModel):
    """消息响应模型"""
    request_id: str = Field(..., description="请求ID")
    bot_response: str = Field(..., description="机器人回复")
    confidence: float = Field(..., description="置信度")
    evidence_ids: Optional[List[str]] = Field(None, description="证据ID列表")
    evidence_summary: Optional[str] = Field(None, description="证据摘要")
    branch: str = Field(..., description="处理分支")
    provider: str = Field(..., description="AI提供商")
    model: str = Field(..., description="AI模型")
    token_in: int = Field(0, description="输入Token数")
    token_out: int = Field(0, description="输出Token数")
    latency_total_ms: int = Field(0, description="总延迟(毫秒)")
    status: str = Field("completed", description="处理状态")


class SessionInfo(BaseModel):
    """会话信息模型"""
    session_key: str = Field(..., description="会话键")
    group_id: str = Field(..., description="群组ID")
    sender_id: str = Field(..., description="发送者ID")
    sender_name: Optional[str] = Field(None, description="发送者名称")
    customer_name: Optional[str] = Field(None, description="客户名称")
    turn_count: int = Field(0, description="对话轮数")
    summary: Optional[str] = Field(None, description="会话摘要")
    status: str = Field("active", description="会话状态")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


# 消息处理服务
class MessageService:
    """消息处理服务"""
    
    def __init__(self, 
                 db_manager: UnifiedDatabaseManager,
                 vector_service: Optional[VectorSearchService] = None,
                 embedding_service: Optional[SmartEmbeddingService] = None):
        self.db_manager = db_manager
        self.vector_service = vector_service
        self.embedding_service = embedding_service
        
        logger.info("✅ 消息处理服务初始化完成")
    
    async def process_message(self, request: MessageRequest, tenant_id: str = "default") -> MessageResponse:
        """处理消息"""
        try:
            start_time = datetime.now()
            
            # 1. 记录消息
            message_data = {
                "request_id": request.request_id,
                "group_id": request.group_id,
                "sender_id": request.sender_id,
                "user_message": request.user_message,
                "session_id": request.session_id,
                "group_name": request.group_name,
                "sender_name": request.sender_name,
                "received_at": start_time.isoformat(),
                "status": "processing"
            }
            
            await self.db_manager.create_message(tenant_id, message_data)
            
            # 2. 生成AI回复
            bot_response, ai_metadata = await self._generate_ai_response(
                request.user_message, 
                tenant_id
            )
            
            # 3. 更新消息记录
            update_data = {
                "bot_response": bot_response,
                "provider": ai_metadata.get("provider", "unknown"),
                "model": ai_metadata.get("model", "unknown"),
                "token_in": ai_metadata.get("token_in", 0),
                "token_out": ai_metadata.get("token_out", 0),
                "confidence": ai_metadata.get("confidence", 0.0),
                "branch": ai_metadata.get("branch", "direct"),
                "evidence_ids": ai_metadata.get("evidence_ids"),
                "evidence_summary": ai_metadata.get("evidence_summary"),
                "status": "completed",
                "responded_at": datetime.now().isoformat()
            }
            
            await self.db_manager.update_message(
                tenant_id, 
                request.request_id, 
                update_data
            )
            
            # 4. 计算延迟
            end_time = datetime.now()
            latency_total_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return MessageResponse(
                request_id=request.request_id,
                bot_response=bot_response,
                confidence=ai_metadata.get("confidence", 0.0),
                evidence_ids=ai_metadata.get("evidence_ids"),
                evidence_summary=ai_metadata.get("evidence_summary"),
                branch=ai_metadata.get("branch", "direct"),
                provider=ai_metadata.get("provider", "unknown"),
                model=ai_metadata.get("model", "unknown"),
                token_in=ai_metadata.get("token_in", 0),
                token_out=ai_metadata.get("token_out", 0),
                latency_total_ms=latency_total_ms,
                status="completed"
            )
            
        except Exception as e:
            logger.error(f"❌ 消息处理失败: {e}")
            
            # 记录错误
            await self.db_manager.update_message(
                tenant_id,
                request.request_id,
                {
                    "status": "error",
                    "error_message": str(e),
                    "responded_at": datetime.now().isoformat()
                }
            )
            
            raise HTTPException(status_code=500, detail=f"消息处理失败: {e}")
    
    async def _generate_ai_response(self, message: str, tenant_id: str) -> tuple[str, Dict[str, Any]]:
        """生成AI回复"""
        try:
            # 这里应该集成AI Gateway
            # 暂时返回模拟回复
            bot_response = f"收到您的消息：{message}。我正在为您处理中..."
            
            metadata = {
                "provider": "qwen",
                "model": "qwen-turbo",
                "token_in": len(message),
                "token_out": len(bot_response),
                "confidence": 0.85,
                "branch": "direct",
                "evidence_ids": None,
                "evidence_summary": None
            }
            
            return bot_response, metadata
            
        except Exception as e:
            logger.error(f"❌ AI回复生成失败: {e}")
            raise


# API端点
@router.post("/process", response_model=MessageResponse)
async def process_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep),
    vector_service: Optional[VectorSearchService] = Depends(get_vector_search_service_dep),
    tenant_id: str = "default"
):
    """处理消息"""
    try:
        message_service = MessageService(db_manager, vector_service)
        response = await message_service.process_message(request, tenant_id)
        
        logger.info(f"✅ 消息处理完成: {request.request_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ 消息处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_key}", response_model=SessionInfo)
async def get_session(
    session_key: str,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep),
    tenant_id: str = "default"
):
    """获取会话信息"""
    try:
        session = await db_manager.get_session(tenant_id, session_key)
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return SessionInfo(**session)
        
    except Exception as e:
        logger.error(f"❌ 获取会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions", response_model=SessionInfo)
async def create_session(
    session_data: Dict[str, Any],
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep),
    tenant_id: str = "default"
):
    """创建会话"""
    try:
        session = await db_manager.create_session(tenant_id, session_data)
        
        logger.info(f"✅ 会话创建成功: {session.get('session_key')}")
        return SessionInfo(**session)
        
    except Exception as e:
        logger.error(f"❌ 会话创建失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages", response_model=List[Dict[str, Any]])
async def get_messages(
    session_id: Optional[str] = None,
    limit: int = 50,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep),
    tenant_id: str = "default"
):
    """获取消息列表"""
    try:
        messages = await db_manager.get_messages(tenant_id, session_id, limit)
        
        logger.info(f"✅ 获取消息列表: {len(messages)}条")
        return messages
        
    except Exception as e:
        logger.error(f"❌ 获取消息列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{request_id}", response_model=Dict[str, Any])
async def get_message(
    request_id: str,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep),
    tenant_id: str = "default"
):
    """获取单个消息"""
    try:
        message = await db_manager.get_message(tenant_id, request_id)
        
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        logger.info(f"✅ 获取消息: {request_id}")
        return message
        
    except Exception as e:
        logger.error(f"❌ 获取消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/messages/{request_id}")
async def update_message(
    request_id: str,
    updates: Dict[str, Any],
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep),
    tenant_id: str = "default"
):
    """更新消息"""
    try:
        success = await db_manager.update_message(tenant_id, request_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        logger.info(f"✅ 消息更新成功: {request_id}")
        return {"status": "success", "message": "消息更新成功"}
        
    except Exception as e:
        logger.error(f"❌ 消息更新失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages/{request_id}")
async def delete_message(
    request_id: str,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep),
    tenant_id: str = "default"
):
    """删除消息"""
    try:
        success = await db_manager.delete_message(tenant_id, request_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        logger.info(f"✅ 消息删除成功: {request_id}")
        return {"status": "success", "message": "消息删除成功"}
        
    except Exception as e:
        logger.error(f"❌ 消息删除失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any])
async def get_message_stats(
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep),
    tenant_id: str = "default"
):
    """获取消息统计"""
    try:
        stats = await db_manager.get_tenant_stats(tenant_id)
        
        logger.info(f"✅ 获取消息统计: {tenant_id}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ 获取消息统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
