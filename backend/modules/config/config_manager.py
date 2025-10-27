"""
配置管理器 - 统一配置管理
支持多环境配置、实时同步、配置验证
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import json

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.configs = {}
        self._load_default_configs()
        
        logger.info("✅ 配置管理器初始化完成")
    
    def _load_default_configs(self):
        """加载默认配置"""
        try:
            # 从环境变量加载配置
            self.configs = {
                "system_settings": {
                    "app_name": "微信客服中台",
                    "version": "2.0.0",
                    "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
                    "log_level": os.getenv("LOG_LEVEL", "INFO")
                },
                "supabase_settings": {
                    "url": os.getenv("SUPABASE_URL", ""),
                    "anon_key": os.getenv("SUPABASE_ANON_KEY", ""),
                    "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
                },
                "pinecone_settings": {
                    "api_key": os.getenv("PINECONE_API_KEY", ""),
                    "environment": os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp-free"),
                    "index_name": os.getenv("PINECONE_INDEX_NAME", "wxauto-knowledge")
                },
                "ai_settings": {
                    "primary_provider": os.getenv("AI_PRIMARY_PROVIDER", "qwen"),
                    "primary_model": os.getenv("AI_PRIMARY_MODEL", "qwen-turbo"),
                    "fallback_provider": os.getenv("AI_FALLBACK_PROVIDER", "glm"),
                    "fallback_model": os.getenv("AI_FALLBACK_MODEL", "glm-4-flash")
                },
                "wechat_settings": {
                    "whitelisted_groups": ["技术支持群", "VIP客户群", "测试群"],
                    "check_interval_ms": 500,
                    "max_retries": 3
                },
                "monitoring_settings": {
                    "health_check_interval": 30,
                    "metrics_collection": True,
                    "alert_thresholds": {
                        "cpu_percent": 80,
                        "memory_percent": 90,
                        "disk_percent": 95
                    }
                }
            }
            
            logger.info(f"✅ 默认配置加载完成: {len(self.configs)}项")
            
        except Exception as e:
            logger.error(f"❌ 默认配置加载失败: {e}")
            self.configs = {}
    
    async def get_all_configs(self) -> List[Dict[str, Any]]:
        """获取所有配置"""
        try:
            configs = []
            for key, value in self.configs.items():
                configs.append({
                    "id": key,
                    "key": key,
                    "value": value,
                    "description": self._get_config_description(key),
                    "is_sensitive": self._is_sensitive_config(key),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })
            
            return configs
            
        except Exception as e:
            logger.error(f"❌ 获取所有配置失败: {e}")
            return []
    
    async def get_config(self, key: str) -> Optional[Dict[str, Any]]:
        """获取单个配置"""
        try:
            if key in self.configs:
                return {
                    "id": key,
                    "key": key,
                    "value": self.configs[key],
                    "description": self._get_config_description(key),
                    "is_sensitive": self._is_sensitive_config(key),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取配置失败: {e}")
            return None
    
    async def create_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建配置"""
        try:
            key = config_data["key"]
            value = config_data["value"]
            
            self.configs[key] = value
            
            logger.info(f"✅ 配置创建成功: {key}")
            return {
                "id": key,
                "key": key,
                "value": value,
                "description": config_data.get("description"),
                "is_sensitive": config_data.get("is_sensitive", False),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 配置创建失败: {e}")
            raise
    
    async def update_config(self, key: str, config_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新配置"""
        try:
            if key in self.configs:
                # 更新配置值
                if "value" in config_data:
                    self.configs[key] = config_data["value"]
                
                logger.info(f"✅ 配置更新成功: {key}")
                return {
                    "id": key,
                    "key": key,
                    "value": self.configs[key],
                    "description": config_data.get("description"),
                    "is_sensitive": config_data.get("is_sensitive", False),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ 配置更新失败: {e}")
            raise
    
    async def delete_config(self, key: str) -> bool:
        """删除配置"""
        try:
            if key in self.configs:
                del self.configs[key]
                logger.info(f"✅ 配置删除成功: {key}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ 配置删除失败: {e}")
            return False
    
    def _get_config_description(self, key: str) -> str:
        """获取配置描述"""
        descriptions = {
            "system_settings": "系统基本设置",
            "supabase_settings": "Supabase数据库配置",
            "pinecone_settings": "Pinecone向量数据库配置",
            "ai_settings": "AI模型配置",
            "wechat_settings": "微信配置",
            "monitoring_settings": "监控配置"
        }
        return descriptions.get(key, "配置项")
    
    def _is_sensitive_config(self, key: str) -> bool:
        """判断是否为敏感配置"""
        sensitive_keys = [
            "supabase_settings",
            "pinecone_settings",
            "ai_settings"
        ]
        return key in sensitive_keys
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.configs.get(key, default)
    
    def set_config_value(self, key: str, value: Any):
        """设置配置值"""
        self.configs[key] = value
        logger.debug(f"配置值已更新: {key}")
    
    def export_configs(self) -> Dict[str, Any]:
        """导出配置"""
        return {
            "configs": self.configs,
            "exported_at": datetime.now().isoformat(),
            "total_count": len(self.configs)
        }
    
    def import_configs(self, configs_data: Dict[str, Any]) -> Dict[str, Any]:
        """导入配置"""
        try:
            configs = configs_data.get("configs", {})
            
            imported_count = 0
            for key, value in configs.items():
                self.configs[key] = value
                imported_count += 1
            
            logger.info(f"✅ 配置导入成功: {imported_count}项")
            return {
                "status": "success",
                "imported_count": imported_count,
                "total_count": len(configs)
            }
            
        except Exception as e:
            logger.error(f"❌ 配置导入失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def init_config_manager():
    """初始化全局配置管理器"""
    global _config_manager
    _config_manager = ConfigManager()
    logger.info("✅ 全局配置管理器初始化完成")
    return _config_manager