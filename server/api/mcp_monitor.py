"""
MCP 中台监控端点
提供 MCP 服务的统计、健康检查和缓存管理
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp", tags=["MCP监控"])

# 全局 MCP Manager 实例（将在 main_server.py 中初始化）
_mcp_manager = None


def init_mcp_manager(manager):
    """初始化 MCP Manager"""
    global _mcp_manager
    _mcp_manager = manager
    logger.info("✅ MCP 监控端点初始化完成")


@router.get("/stats")
async def get_mcp_stats() -> Dict[str, Any]:
    """
    获取 MCP 统计信息
    
    Returns:
        MCP 系统统计数据
    """
    if not _mcp_manager:
        raise HTTPException(status_code=503, detail="MCP Manager 未初始化")
    
    try:
        stats = _mcp_manager.get_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取 MCP 统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_mcp_health() -> Dict[str, Any]:
    """
    获取 MCP 健康状态
    
    Returns:
        各个 MCP 服务的健康状态
    """
    if not _mcp_manager:
        raise HTTPException(status_code=503, detail="MCP Manager 未初始化")
    
    try:
        health = _mcp_manager.health_check()
        return {
            "success": True,
            "data": health
        }
    except Exception as e:
        logger.error(f"MCP 健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def get_mcp_services() -> Dict[str, Any]:
    """
    获取 MCP 服务列表
    
    Returns:
        已注册的 MCP 服务列表
    """
    if not _mcp_manager:
        raise HTTPException(status_code=503, detail="MCP Manager 未初始化")
    
    try:
        services = _mcp_manager.list_services()
        return {
            "success": True,
            "data": services
        }
    except Exception as e:
        logger.error(f"获取服务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_mcp_cache() -> Dict[str, Any]:
    """
    清空 MCP 缓存
    
    Returns:
        操作结果
    """
    if not _mcp_manager:
        raise HTTPException(status_code=503, detail="MCP Manager 未初始化")
    
    try:
        _mcp_manager.clear_cache()
        return {
            "success": True,
            "message": "MCP 缓存已清空"
        }
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    获取缓存统计信息
    
    Returns:
        缓存统计数据
    """
    if not _mcp_manager:
        raise HTTPException(status_code=503, detail="MCP Manager 未初始化")
    
    try:
        stats = _mcp_manager.get_stats()
        cache_stats = stats.get("cache_stats", {})
        return {
            "success": True,
            "data": cache_stats
        }
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/reload")
async def reload_config() -> Dict[str, Any]:
    """
    重新加载 MCP 配置
    
    Returns:
        操作结果
    """
    if not _mcp_manager:
        raise HTTPException(status_code=503, detail="MCP Manager 未初始化")
    
    try:
        _mcp_manager.reload_config()
        return {
            "success": True,
            "message": "MCP 配置已重新加载"
        }
    except Exception as e:
        logger.error(f"重新加载配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

