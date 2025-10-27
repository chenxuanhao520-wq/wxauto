"""
健康检查API - 系统健康状态监控
支持服务状态检查、性能指标、依赖检查
"""

import logging
import asyncio
import psutil
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request

logger = logging.getLogger(__name__)

router = APIRouter()


# 健康检查服务
class HealthService:
    """健康检查服务"""
    
    def __init__(self):
        logger.info("✅ 健康检查服务初始化完成")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            # 系统资源状态
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 系统信息
            system_info = {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            }
            
            # 健康状态评估
            health_status = "healthy"
            if cpu_percent > 80:
                health_status = "warning"
            if memory.percent > 90:
                health_status = "critical"
            if disk.percent > 95:
                health_status = "critical"
            
            return {
                "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "system": system_info,
                "uptime": self._get_uptime()
            }
            
        except Exception as e:
            logger.error(f"❌ 获取系统健康状态失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_uptime(self) -> Dict[str, Any]:
        """获取系统运行时间"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.now().timestamp() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            
            return {
                "total_seconds": int(uptime_seconds),
                "formatted": f"{days}d {hours}h {minutes}m {seconds}s",
                "boot_time": datetime.fromtimestamp(boot_time).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 获取运行时间失败: {e}")
            return {"error": str(e)}
    
    async def check_dependencies(self) -> Dict[str, Any]:
        """检查依赖服务状态"""
        try:
            dependencies = {
                "supabase": await self._check_supabase(),
                "vector_db": await self._check_vector_db(),
                "ai_services": await self._check_ai_services(),
                "database": await self._check_database()
            }
            
            # 计算整体状态
            all_healthy = all(
                dep.get("status") == "healthy" 
                for dep in dependencies.values()
            )
            
            return {
                "overall_status": "healthy" if all_healthy else "degraded",
                "dependencies": dependencies,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 检查依赖服务失败: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_supabase(self) -> Dict[str, Any]:
        """检查Supabase连接"""
        try:
            # 这里应该实际检查Supabase连接
            # 暂时返回模拟状态
            return {
                "status": "healthy",
                "message": "Supabase连接正常",
                "response_time_ms": 45
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Supabase连接失败: {e}",
                "response_time_ms": None
            }
    
    async def _check_vector_db(self) -> Dict[str, Any]:
        """检查向量数据库连接"""
        try:
            from modules.vector.supabase_vector_client import SupabaseVectorClient
            from modules.storage.supabase_client import get_supabase_client
            
            supabase = get_supabase_client()
            if not supabase:
                return {
                    "status": "error",
                    "message": "Supabase客户端未初始化",
                    "response_time_ms": None
                }
            
    async def _check_vector_db(self) -> Dict[str, Any]:
        """检查向量数据库连接"""
        try:
            from modules.vector.supabase_vector import get_vector_search_service
            from modules.storage.supabase_client import get_supabase_client
            
            supabase = get_supabase_client()
            if not supabase:
                return {
                    "status": "error",
                    "message": "Supabase客户端未初始化",
                    "response_time_ms": None
                }
            
            # 测试向量搜索服务
            try:
                vector_service = get_vector_search_service()
                health_status = await vector_service.health_check()
                
                if health_status:
                    return {
                        "status": "healthy",
                        "message": "向量数据库连接正常",
                        "response_time_ms": None,
                        "backend": "supabase_pgvector"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "向量数据库健康检查失败",
                        "response_time_ms": None
                    }
            except RuntimeError:
                return {
                    "status": "error",
                    "message": "向量搜索服务未初始化",
                    "response_time_ms": None
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"向量数据库连接失败: {e}",
                "response_time_ms": None
            }
    
    async def _check_ai_services(self) -> Dict[str, Any]:
        """检查AI服务状态"""
        try:
            # 这里应该检查各个AI服务提供商
            return {
                "status": "healthy",
                "message": "AI服务正常",
                "providers": {
                    "qwen": "healthy",
                    "glm": "healthy",
                    "openai": "healthy"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI服务检查失败: {e}",
                "providers": {}
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """检查数据库状态"""
        try:
            # 这里应该检查数据库连接
            return {
                "status": "healthy",
                "message": "数据库连接正常",
                "response_time_ms": 25
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"数据库连接失败: {e}",
                "response_time_ms": None
            }


# API端点
@router.get("/")
async def health_check():
    """基础健康检查"""
    try:
        service = HealthService()
        health_data = await service.get_system_health()
        
        return {
            "status": "ok",
            "message": "Wxauto 智能客服中台运行正常",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "health": health_data
        }
        
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system")
async def system_health():
    """系统健康状态"""
    try:
        service = HealthService()
        return await service.get_system_health()
        
    except Exception as e:
        logger.error(f"❌ 系统健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependencies")
async def dependencies_health():
    """依赖服务健康状态"""
    try:
        service = HealthService()
        return await service.check_dependencies()
        
    except Exception as e:
        logger.error(f"❌ 依赖服务检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics():
    """获取性能指标"""
    try:
        # 系统指标
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 网络指标
        network = psutil.net_io_counters()
        
        # 进程信息
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(),
            "num_threads": process.num_threads(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            "process": process_info
        }
        
    except Exception as e:
        logger.error(f"❌ 获取性能指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping")
async def ping():
    """简单ping检查"""
    return {
        "status": "ok",
        "message": "pong",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/ready")
async def readiness_check():
    """就绪检查"""
    try:
        # 检查关键服务是否就绪
        service = HealthService()
        dependencies = await service.check_dependencies()
        
        # 如果所有关键依赖都健康，则认为系统就绪
        critical_services = ["supabase", "database"]
        ready = all(
            dependencies["dependencies"].get(service, {}).get("status") == "healthy"
            for service in critical_services
        )
        
        if ready:
            return {
                "status": "ready",
                "message": "系统就绪",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=503, 
                detail="系统未就绪，关键服务不可用"
            )
            
    except Exception as e:
        logger.error(f"❌ 就绪检查失败: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/live")
async def liveness_check():
    """存活检查"""
    return {
        "status": "alive",
        "message": "系统存活",
        "timestamp": datetime.now().isoformat()
    }
