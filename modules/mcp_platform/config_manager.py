"""
MCP 配置管理器
负责加载和管理 MCP 中台的配置
"""

import yaml
import os
import re
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """MCP 配置管理器"""
    
    def __init__(self, config_path: str = "config/mcp_config.yaml", env: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
            env: 环境名称（dev/prod），默认从环境变量 MCP_ENV 读取
        """
        self.config_path = Path(config_path)
        self.env = env or os.getenv("MCP_ENV", "dev")
        self.config: Dict[str, Any] = {}
        
        # 加载配置
        self._load_config()
        
        logger.info(f"✅ 配置管理器初始化成功 (环境: {self.env}, 配置文件: {self.config_path})")
    
    def _load_config(self):
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # 替换环境变量
            self._replace_env_vars(self.config)
            
            # 应用环境特定配置
            self._apply_profile_config()
            
            logger.info(f"📄 配置文件加载成功: {self.config_path}")
            
        except yaml.YAMLError as e:
            logger.error(f"❌ 配置文件解析失败: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ 配置文件加载失败: {e}")
            raise
    
    def _replace_env_vars(self, obj):
        """
        递归替换环境变量
        支持 ${VAR_NAME} 和 ${VAR_NAME:default_value} 格式
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._replace_env_vars(value)
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # 匹配 ${VAR_NAME} 或 ${VAR_NAME:default}
            pattern = r'\$\{([^:}]+)(?::([^}]+))?\}'
            
            def replacer(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) else ''
                return os.getenv(var_name, default_value)
            
            obj = re.sub(pattern, replacer, obj)
        
        return obj
    
    def _apply_profile_config(self):
        """应用环境特定配置"""
        profiles = self.config.get('profiles', {})
        env_config = profiles.get(self.env, {})
        
        if env_config:
            # 深度合并环境配置到主配置
            self._deep_merge(self.config.get('mcp_platform', {}), env_config)
            logger.info(f"🔧 应用环境配置: {self.env}")
    
    def _deep_merge(self, base: Dict, override: Dict):
        """深度合并字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def reload(self):
        """重新加载配置"""
        logger.info("🔄 重新加载配置...")
        self._load_config()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号路径）
        
        Args:
            key_path: 配置键路径，如 "mcp_platform.global.default_timeout"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置"""
        return self.config.get('mcp_platform', {}).get('global', {})
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """获取服务配置"""
        return self.config.get('mcp_platform', {}).get('services', {}).get(service_name, {})
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return self.config.get('mcp_platform', {}).get('cache', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.config.get('mcp_platform', {}).get('monitoring', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return self.config.get('mcp_platform', {}).get('performance', {})
    
    def list_services(self) -> list:
        """列出所有已配置的服务"""
        services = self.config.get('mcp_platform', {}).get('services', {})
        return list(services.keys())
    
    def is_service_enabled(self, service_name: str) -> bool:
        """检查服务是否启用"""
        service_config = self.get_service_config(service_name)
        return service_config.get('enabled', False)
    
    def get_service_cache_config(self, service_name: str) -> Dict[str, Any]:
        """获取服务的缓存配置"""
        service_config = self.get_service_config(service_name)
        return service_config.get('cache', {})
    
    def is_cache_enabled(self, service_name: str = None) -> bool:
        """
        检查缓存是否启用
        
        Args:
            service_name: 服务名称，如果为 None 则检查全局配置
        """
        if service_name:
            cache_config = self.get_service_cache_config(service_name)
            return cache_config.get('enabled', True)
        else:
            global_config = self.get_global_config()
            return global_config.get('cache_enabled', True)
    
    def get_cache_ttl(self, service_name: str) -> int:
        """获取服务的缓存 TTL"""
        cache_config = self.get_service_cache_config(service_name)
        return cache_config.get('ttl', 3600)
    
    def to_dict(self) -> Dict[str, Any]:
        """导出配置为字典"""
        return self.config.copy()
    
    def __repr__(self) -> str:
        return f"<ConfigManager(env={self.env}, config_path={self.config_path})>"


# 全局配置管理器实例（单例模式）
_config_manager_instance: Optional[ConfigManager] = None


def get_config_manager(config_path: str = "config/mcp_config.yaml", env: str = None) -> ConfigManager:
    """
    获取配置管理器实例（单例）
    
    Args:
        config_path: 配置文件路径
        env: 环境名称
        
    Returns:
        ConfigManager 实例
    """
    global _config_manager_instance
    
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager(config_path, env)
    
    return _config_manager_instance

