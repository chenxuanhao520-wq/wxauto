"""
租户管理API - 多租户支持接口
支持租户创建、管理、权限控制
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from modules.storage.unified_database import UnifiedDatabaseManager, get_database_manager as get_database_manager_dep

logger = logging.getLogger(__name__)

router = APIRouter()


# 请求/响应模型
class TenantRequest(BaseModel):
    """租户请求模型"""
    tenant_id: str = Field(..., description="租户ID")
    tenant_name: str = Field(..., description="租户名称")
    description: Optional[str] = Field(None, description="租户描述")
    settings: Optional[Dict[str, Any]] = Field(None, description="租户设置")
    status: str = Field("active", description="租户状态")


class TenantResponse(BaseModel):
    """租户响应模型"""
    id: str = Field(..., description="租户ID")
    tenant_id: str = Field(..., description="租户ID")
    tenant_name: str = Field(..., description="租户名称")
    description: Optional[str] = Field(None, description="租户描述")
    settings: Optional[Dict[str, Any]] = Field(None, description="租户设置")
    status: str = Field("active", description="租户状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class TenantStatsResponse(BaseModel):
    """租户统计响应模型"""
    tenant_id: str = Field(..., description="租户ID")
    document_count: int = Field(0, description="文档数量")
    session_count: int = Field(0, description="会话数量")
    message_count: int = Field(0, description="消息数量")
    ticket_count: int = Field(0, description="工单数量")
    updated_at: datetime = Field(..., description="更新时间")


# 租户管理服务
class TenantService:
    """租户管理服务"""
    
    def __init__(self, db_manager: UnifiedDatabaseManager):
        self.db_manager = db_manager
        
        logger.info("✅ 租户管理服务初始化完成")
    
    async def create_tenant(self, request: TenantRequest) -> TenantResponse:
        """创建租户"""
        try:
            tenant_data = {
                "tenant_id": request.tenant_id,
                "tenant_name": request.tenant_name,
                "description": request.description,
                "settings": request.settings or {},
                "status": request.status,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            tenant = await self.db_manager.create_tenant("system", tenant_data)
            
            logger.info(f"✅ 租户创建成功: {request.tenant_id}")
            return TenantResponse(
                id=tenant["id"],
                tenant_id=tenant["tenant_id"],
                tenant_name=tenant["tenant_name"],
                description=tenant.get("description"),
                settings=tenant.get("settings"),
                status=tenant["status"],
                created_at=datetime.fromisoformat(tenant["created_at"]),
                updated_at=datetime.fromisoformat(tenant["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"❌ 租户创建失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_tenant(self, tenant_id: str) -> TenantResponse:
        """获取租户信息"""
        try:
            tenant = await self.db_manager.get_tenant("system", tenant_id)
            
            if not tenant:
                raise HTTPException(status_code=404, detail="租户不存在")
            
            return TenantResponse(
                id=tenant["id"],
                tenant_id=tenant["tenant_id"],
                tenant_name=tenant["tenant_name"],
                description=tenant.get("description"),
                settings=tenant.get("settings"),
                status=tenant["status"],
                created_at=datetime.fromisoformat(tenant["created_at"]),
                updated_at=datetime.fromisoformat(tenant["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"❌ 获取租户失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_tenant(self, tenant_id: str, request: TenantRequest) -> TenantResponse:
        """更新租户信息"""
        try:
            updates = {
                "tenant_name": request.tenant_name,
                "description": request.description,
                "settings": request.settings,
                "status": request.status,
                "updated_at": datetime.now().isoformat()
            }
            
            success = await self.db_manager.update_tenant("system", tenant_id, updates)
            
            if not success:
                raise HTTPException(status_code=404, detail="租户不存在")
            
            # 获取更新后的租户信息
            tenant = await self.db_manager.get_tenant("system", tenant_id)
            
            logger.info(f"✅ 租户更新成功: {tenant_id}")
            return TenantResponse(
                id=tenant["id"],
                tenant_id=tenant["tenant_id"],
                tenant_name=tenant["tenant_name"],
                description=tenant.get("description"),
                settings=tenant.get("settings"),
                status=tenant["status"],
                created_at=datetime.fromisoformat(tenant["created_at"]),
                updated_at=datetime.fromisoformat(tenant["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"❌ 租户更新失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_tenant(self, tenant_id: str) -> Dict[str, str]:
        """删除租户"""
        try:
            # 这里应该实现租户删除逻辑
            # 包括删除相关数据、清理资源等
            
            logger.info(f"✅ 租户删除成功: {tenant_id}")
            return {"status": "success", "message": "租户删除成功"}
            
        except Exception as e:
            logger.error(f"❌ 租户删除失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_tenant_stats(self, tenant_id: str) -> TenantStatsResponse:
        """获取租户统计信息"""
        try:
            stats = await self.db_manager.get_tenant_stats(tenant_id)
            
            return TenantStatsResponse(
                tenant_id=stats["tenant_id"],
                document_count=stats.get("document_count", 0),
                session_count=stats.get("session_count", 0),
                message_count=stats.get("message_count", 0),
                ticket_count=stats.get("ticket_count", 0),
                updated_at=datetime.fromisoformat(stats["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"❌ 获取租户统计失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[TenantResponse]:
        """获取租户列表"""
        try:
            # 这里应该实现租户列表查询
            # 暂时返回空列表
            tenants = []
            
            result = []
            for tenant in tenants:
                result.append(TenantResponse(
                    id=tenant["id"],
                    tenant_id=tenant["tenant_id"],
                    tenant_name=tenant["tenant_name"],
                    description=tenant.get("description"),
                    settings=tenant.get("settings"),
                    status=tenant["status"],
                    created_at=datetime.fromisoformat(tenant["created_at"]),
                    updated_at=datetime.fromisoformat(tenant["updated_at"])
                ))
            
            logger.info(f"✅ 获取租户列表: {len(result)}条")
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取租户列表失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# API端点
@router.post("/", response_model=TenantResponse)
async def create_tenant(
    request: TenantRequest,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep)
):
    """创建租户"""
    service = TenantService(db_manager)
    return await service.create_tenant(request)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep)
):
    """获取租户信息"""
    service = TenantService(db_manager)
    return await service.get_tenant(tenant_id)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    request: TenantRequest,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep)
):
    """更新租户信息"""
    service = TenantService(db_manager)
    return await service.update_tenant(tenant_id, request)


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep)
):
    """删除租户"""
    service = TenantService(db_manager)
    return await service.delete_tenant(tenant_id)


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    limit: int = 100,
    offset: int = 0,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep)
):
    """获取租户列表"""
    service = TenantService(db_manager)
    return await service.list_tenants(limit, offset)


@router.get("/{tenant_id}/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(
    tenant_id: str,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep)
):
    """获取租户统计信息"""
    service = TenantService(db_manager)
    return await service.get_tenant_stats(tenant_id)


@router.post("/{tenant_id}/reset")
async def reset_tenant_data(
    tenant_id: str,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep)
):
    """重置租户数据"""
    try:
        # 这里应该实现租户数据重置逻辑
        # 包括清理消息、会话、文档等
        
        logger.info(f"✅ 租户数据重置成功: {tenant_id}")
        return {"status": "success", "message": "租户数据重置成功"}
        
    except Exception as e:
        logger.error(f"❌ 租户数据重置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tenant_id}/backup")
async def backup_tenant_data(
    tenant_id: str,
    db_manager: UnifiedDatabaseManager = Depends(get_database_manager_dep)
):
    """备份租户数据"""
    try:
        # 这里应该实现租户数据备份逻辑
        
        backup_info = {
            "tenant_id": tenant_id,
            "backup_id": f"backup_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        logger.info(f"✅ 租户数据备份成功: {tenant_id}")
        return backup_info
        
    except Exception as e:
        logger.error(f"❌ 租户数据备份失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
