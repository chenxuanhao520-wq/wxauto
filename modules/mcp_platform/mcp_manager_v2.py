"""
优化后的 MCP 中台管理器 v2.0
集成配置管理和智能缓存
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .config_manager import ConfigManager, get_config_manager
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


@dataclass
class MCPService:
    """MCP 服务配置"""
    name: str
    endpoint: str
    api_key: str
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    cache_config: Dict[str, Any] = field(default_factory=dict)


class MCPManagerV2:
    """优化后的 MCP 中台管理器"""
    
    def __init__(self, config_path: str = "config/mcp_config.yaml", env: str = None):
        """
        初始化 MCP 管理器
        
        Args:
            config_path: 配置文件路径
            env: 环境名称（dev/prod）
        """
        # 配置管理
        self.config_manager = get_config_manager(config_path, env)
        
        # 缓存管理
        cache_config = self.config_manager.get_cache_config()
        self.cache_manager = CacheManager(cache_config)
        
        # 服务和客户端
        self.services: Dict[str, MCPService] = {}
        self.clients: Dict[str, Any] = {}
        
        # 初始化服务
        self._init_services()
        
        logger.info(f"✅ MCP 中台管理器 v2.0 初始化完成，注册 {len(self.services)} 个服务")
    
    def _init_services(self):
        """从配置文件初始化服务"""
        global_config = self.config_manager.get_global_config()
        services_list = self.config_manager.list_services()
        
        for service_name in services_list:
            # 检查是否启用
            if not self.config_manager.is_service_enabled(service_name):
                logger.info(f"⏭️ 跳过禁用的服务: {service_name}")
                continue
            
            # 获取服务配置
            service_config = self.config_manager.get_service_config(service_name)
            cache_config = self.config_manager.get_service_cache_config(service_name)
            
            # 创建服务配置对象
            service = MCPService(
                name=service_name,
                endpoint=service_config.get('endpoint', ''),
                api_key=service_config.get('api_key', ''),
                enabled=service_config.get('enabled', True),
                timeout=service_config.get('timeout', global_config.get('default_timeout', 30)),
                max_retries=service_config.get('max_retries', global_config.get('default_retries', 3)),
                metadata=service_config.get('metadata', {}),
                cache_config=cache_config
            )
            
            self.services[service_name] = service
            logger.info(f"✅ 服务注册成功: {service_name} (缓存: {'启用' if cache_config.get('enabled', True) else '禁用'})")
    
    def get_service(self, name: str) -> Optional[MCPService]:
        """获取 MCP 服务配置"""
        return self.services.get(name)
    
    def get_client(self, name: str):
        """
        获取 MCP 客户端（带缓存）
        
        Args:
            name: 服务名称
            
        Returns:
            MCP 客户端实例
        """
        if name not in self.clients:
            service = self.get_service(name)
            if not service:
                raise ValueError(f"MCP 服务不存在: {name}")
            
            if not service.enabled:
                raise ValueError(f"MCP 服务已禁用: {name}")
            
            # 根据服务类型创建客户端
            if name == "aiocr":
                from .aiocr_client import AIOCRClient
                self.clients[name] = AIOCRClient(service, self.cache_manager)
            elif name == "sequential_thinking":
                from .sequential_thinking_client import SequentialThinkingClient
                self.clients[name] = SequentialThinkingClient(service, self.cache_manager)
            else:
                from .mcp_client import MCPClient
                self.clients[name] = MCPClient(service, self.cache_manager)
            
            logger.debug(f"📦 客户端创建成功: {name}")
        
        return self.clients[name]
    
    def list_services(self) -> List[Dict[str, Any]]:
        """列出所有服务"""
        return [
            {
                "name": name,
                "enabled": service.enabled,
                "endpoint": service.endpoint,
                "description": service.metadata.get("description", ""),
                "supported_formats": service.metadata.get("supported_formats", []),
                "tools": service.metadata.get("tools", []),
                "cache_enabled": service.cache_config.get("enabled", True),
                "cache_ttl": service.cache_config.get("ttl", 3600)
            }
            for name, service in self.services.items()
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        results = {}
        
        for name, service in self.services.items():
            if not service.enabled:
                results[name] = {"status": "disabled", "message": "服务已禁用"}
                continue
            
            try:
                # 简单的健康检查：验证服务配置和API密钥
                if service.api_key:
                    results[name] = {
                        "status": "healthy", 
                        "message": "服务配置正常",
                        "endpoint": service.endpoint,
                        "api_key_configured": True,
                        "cache_enabled": service.cache_config.get("enabled", True)
                    }
                else:
                    results[name] = {
                        "status": "error", 
                        "message": "API密钥未配置"
                    }
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_stats = self.cache_manager.get_stats()
        
        return {
            "total_services": len(self.services),
            "enabled_services": sum(1 for s in self.services.values() if s.enabled),
            "disabled_services": sum(1 for s in self.services.values() if not s.enabled),
            "cache_stats": cache_stats,
            "services": self.list_services()
        }
    
    def clear_cache(self):
        """清空所有缓存"""
        self.cache_manager.clear()
        logger.info("🗑️ 所有 MCP 缓存已清空")
    
    def reload_config(self):
        """重新加载配置"""
        logger.info("🔄 重新加载 MCP 配置...")
        self.config_manager.reload()
        self.services.clear()
        self.clients.clear()
        self._init_services()
        logger.info("✅ MCP 配置重新加载完成")
    
    def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """获取特定服务的统计信息"""
        service = self.get_service(service_name)
        if not service:
            return {"error": f"服务不存在: {service_name}"}
        
        # 这里可以添加服务特定的统计信息
        # 目前返回基本信息
        return {
            "name": service.name,
            "enabled": service.enabled,
            "endpoint": service.endpoint,
            "timeout": service.timeout,
            "max_retries": service.max_retries,
            "cache_config": service.cache_config
        }
    
    def __repr__(self) -> str:
        cache_stats = self.cache_manager.get_stats()
        return f"<MCPManagerV2(services={len(self.services)}, cache_hit_rate={cache_stats['hit_rate']})>"


# 全局 MCP 管理器实例（单例模式）
_mcp_manager_instance: Optional[MCPManagerV2] = None


def get_mcp_manager(config_path: str = "config/mcp_config.yaml", env: str = None) -> MCPManagerV2:
    """
    获取 MCP 管理器实例（单例）
    
    Args:
        config_path: 配置文件路径
        env: 环境名称
        
    Returns:
        MCPManagerV2 实例
    """
    global _mcp_manager_instance
    
    if _mcp_manager_instance is None:
        _mcp_manager_instance = MCPManagerV2(config_path, env)
    
    return _mcp_manager_instance

