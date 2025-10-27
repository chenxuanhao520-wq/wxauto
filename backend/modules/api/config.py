"""
配置管理API - 统一配置管理接口
支持实时同步、多环境配置、配置验证
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from modules.config.config_manager import ConfigManager, get_config_manager as get_config_manager_dep
from modules.config.config_validator import ConfigValidator

logger = logging.getLogger(__name__)

router = APIRouter()


# 请求/响应模型
class ConfigRequest(BaseModel):
    """配置请求模型"""
    key: str = Field(..., description="配置键")
    value: Dict[str, Any] = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    is_sensitive: bool = Field(False, description="是否敏感")


class ConfigResponse(BaseModel):
    """配置响应模型"""
    id: str = Field(..., description="配置ID")
    key: str = Field(..., description="配置键")
    value: Dict[str, Any] = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    is_sensitive: bool = Field(False, description="是否敏感")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ConfigTestRequest(BaseModel):
    """配置测试请求模型"""
    config_type: str = Field(..., description="配置类型")
    config_data: Dict[str, Any] = Field(..., description="配置数据")


class ConfigTestResponse(BaseModel):
    """配置测试响应模型"""
    success: bool = Field(..., description="测试是否成功")
    message: str = Field(..., description="测试结果消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


# 配置管理服务
class ConfigService:
    """配置管理服务"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.validator = ConfigValidator()
        
        logger.info("✅ 配置管理服务初始化完成")
    
    async def get_all_configs(self) -> List[ConfigResponse]:
        """获取所有配置"""
        try:
            configs = await self.config_manager.get_all_configs()
            
            result = []
            for config in configs:
                result.append(ConfigResponse(
                    id=config["id"],
                    key=config["key"],
                    value=config["value"],
                    description=config.get("description"),
                    is_sensitive=config.get("is_sensitive", False),
                    created_at=datetime.fromisoformat(config["created_at"]),
                    updated_at=datetime.fromisoformat(config["updated_at"])
                ))
            
            logger.info(f"✅ 获取所有配置: {len(result)}条")
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取配置失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_config(self, key: str) -> ConfigResponse:
        """获取单个配置"""
        try:
            config = await self.config_manager.get_config(key)
            
            if not config:
                raise HTTPException(status_code=404, detail="配置不存在")
            
            return ConfigResponse(
                id=config["id"],
                key=config["key"],
                value=config["value"],
                description=config.get("description"),
                is_sensitive=config.get("is_sensitive", False),
                created_at=datetime.fromisoformat(config["created_at"]),
                updated_at=datetime.fromisoformat(config["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"❌ 获取配置失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def create_config(self, request: ConfigRequest) -> ConfigResponse:
        """创建配置"""
        try:
            config_data = {
                "key": request.key,
                "value": request.value,
                "description": request.description,
                "is_sensitive": request.is_sensitive
            }
            
            config = await self.config_manager.create_config(config_data)
            
            logger.info(f"✅ 配置创建成功: {request.key}")
            return ConfigResponse(
                id=config["id"],
                key=config["key"],
                value=config["value"],
                description=config.get("description"),
                is_sensitive=config.get("is_sensitive", False),
                created_at=datetime.fromisoformat(config["created_at"]),
                updated_at=datetime.fromisoformat(config["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"❌ 配置创建失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_config(self, key: str, request: ConfigRequest) -> ConfigResponse:
        """更新配置"""
        try:
            config_data = {
                "value": request.value,
                "description": request.description,
                "is_sensitive": request.is_sensitive
            }
            
            config = await self.config_manager.update_config(key, config_data)
            
            if not config:
                raise HTTPException(status_code=404, detail="配置不存在")
            
            logger.info(f"✅ 配置更新成功: {key}")
            return ConfigResponse(
                id=config["id"],
                key=config["key"],
                value=config["value"],
                description=config.get("description"),
                is_sensitive=config.get("is_sensitive", False),
                created_at=datetime.fromisoformat(config["created_at"]),
                updated_at=datetime.fromisoformat(config["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"❌ 配置更新失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_config(self, key: str) -> Dict[str, str]:
        """删除配置"""
        try:
            success = await self.config_manager.delete_config(key)
            
            if not success:
                raise HTTPException(status_code=404, detail="配置不存在")
            
            logger.info(f"✅ 配置删除成功: {key}")
            return {"status": "success", "message": "配置删除成功"}
            
        except Exception as e:
            logger.error(f"❌ 配置删除失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def test_config(self, request: ConfigTestRequest) -> ConfigTestResponse:
        """测试配置"""
        try:
            success, message, details = await self.validator.test_config(
                request.config_type,
                request.config_data
            )
            
            logger.info(f"✅ 配置测试完成: {request.config_type}")
            return ConfigTestResponse(
                success=success,
                message=message,
                details=details
            )
            
        except Exception as e:
            logger.error(f"❌ 配置测试失败: {e}")
            return ConfigTestResponse(
                success=False,
                message=f"配置测试失败: {e}",
                details=None
            )


# API端点
@router.get("/", response_model=List[ConfigResponse])
async def get_all_configs(
    config_manager: ConfigManager = Depends(get_config_manager_dep)
):
    """获取所有配置"""
    service = ConfigService(config_manager)
    return await service.get_all_configs()


@router.get("/{key}", response_model=ConfigResponse)
async def get_config(
    key: str,
    config_manager: ConfigManager = Depends(get_config_manager_dep)
):
    """获取单个配置"""
    service = ConfigService(config_manager)
    return await service.get_config(key)


@router.post("/", response_model=ConfigResponse)
async def create_config(
    request: ConfigRequest,
    config_manager: ConfigManager = Depends(get_config_manager_dep)
):
    """创建配置"""
    service = ConfigService(config_manager)
    return await service.create_config(request)


@router.put("/{key}", response_model=ConfigResponse)
async def update_config(
    key: str,
    request: ConfigRequest,
    config_manager: ConfigManager = Depends(get_config_manager_dep)
):
    """更新配置"""
    service = ConfigService(config_manager)
    return await service.update_config(key, request)


@router.delete("/{key}")
async def delete_config(
    key: str,
    config_manager: ConfigManager = Depends(get_config_manager_dep)
):
    """删除配置"""
    service = ConfigService(config_manager)
    return await service.delete_config(key)


@router.post("/test", response_model=ConfigTestResponse)
async def test_config(
    request: ConfigTestRequest,
    config_manager: ConfigManager = Depends(get_config_manager_dep)
):
    """测试配置"""
    service = ConfigService(config_manager)
    return await service.test_config(request)


@router.get("/export/json")
async def export_configs_json(
    config_manager: ConfigManager = Depends(get_config_manager_dep)
):
    """导出配置为JSON"""
    try:
        configs = await config_manager.get_all_configs()
        
        # 过滤敏感信息
        export_configs = []
        for config in configs:
            export_config = {
                "key": config["key"],
                "value": config["value"],
                "description": config.get("description"),
                "is_sensitive": config.get("is_sensitive", False)
            }
            
            # 如果是敏感配置，隐藏值
            if config.get("is_sensitive", False):
                export_config["value"] = "***HIDDEN***"
            
            export_configs.append(export_config)
        
        logger.info(f"✅ 配置导出成功: {len(export_configs)}条")
        return {
            "configs": export_configs,
            "exported_at": datetime.now().isoformat(),
            "total_count": len(export_configs)
        }
        
    except Exception as e:
        logger.error(f"❌ 配置导出失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/json")
async def import_configs_json(
    configs_data: Dict[str, Any],
    config_manager: ConfigManager = Depends(get_config_manager_dep)
):
    """从JSON导入配置"""
    try:
        configs = configs_data.get("configs", [])
        
        imported_count = 0
        failed_count = 0
        
        for config in configs:
            try:
                await config_manager.create_config(config)
                imported_count += 1
            except Exception as e:
                logger.warning(f"⚠️ 配置导入失败: {config.get('key')} - {e}")
                failed_count += 1
        
        logger.info(f"✅ 配置导入完成: 成功{imported_count}条, 失败{failed_count}条")
        return {
            "status": "success",
            "imported_count": imported_count,
            "failed_count": failed_count,
            "total_count": len(configs)
        }
        
    except Exception as e:
        logger.error(f"❌ 配置导入失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/status")
async def get_sync_status(
    config_manager: ConfigManager = Depends(get_config_manager_dep)
):
    """获取配置同步状态"""
    try:
        # 这里应该返回实时同步状态
        # 暂时返回模拟数据
        return {
            "sync_enabled": True,
            "last_sync": datetime.now().isoformat(),
            "connected_clients": 0,
            "pending_changes": 0
        }
        
    except Exception as e:
        logger.error(f"❌ 获取同步状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
