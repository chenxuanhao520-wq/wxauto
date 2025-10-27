"""
ERP同步配置管理器
"""

import yaml
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ERPSyncConfigManager:
    """ERP同步配置管理器"""
    
    def __init__(self, config_file: str = 'config.yaml'):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            config_path = Path(self.config_file)
            
            if not config_path.exists():
                logger.warning(f"[配置] 配置文件不存在: {self.config_file}，使用默认配置")
                self.config = self._get_default_config()
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
            
            # 提取ERP集成配置
            self.config = full_config.get('erp_integration', {})
            
            # 合并默认配置
            default_config = self._get_default_config()
            self.config = self._merge_config(default_config, self.config)
            
            logger.info(f"[配置] 配置加载成功: {self.config_file}")
            
        except Exception as e:
            logger.error(f"[配置] 加载配置失败: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'enabled': True,
            'base_url': 'http://ls1.jmt.ink:46088',
            'auth': {
                'username': '',
                'password': '',
                'auto_login': True
            },
            'erp_pull': {
                'enabled': True,
                'interval': 3600,  # 秒
                'batch_size': 100,
                'incremental': True
            },
            'erp_push': {
                'enabled': True,
                'interval': 1800,  # 秒
                'batch_size': 50,
                'auto_sync': True
            },
            'rules': {
                'mandatory_sync': {
                    'enabled': True
                },
                'high_quality_sync': {
                    'enabled': True,
                    'min_quality_score': 80
                },
                'medium_quality_sync': {
                    'enabled': True
                },
                'low_quality_skip': {
                    'enabled': True
                }
            },
            'conflict_resolution': {
                'strategy': 'priority_based',
                'core_fields': ['phone', 'company_name', 'erp_customer_code'],
                'local_priority_fields': ['wechat_id', 'wechat_nickname', 'intent_score']
            },
            'data_quality': {
                'min_score_for_sync': 60,
                'verify_before_sync': True,
                'auto_fix_format': True
            },
            'run_on_start': False,
            'logging': {
                'level': 'INFO',
                'file': 'logs/erp_sync.log'
            }
        }
    
    def _merge_config(self, default: Dict, user: Dict) -> Dict:
        """合并配置（用户配置覆盖默认配置）"""
        result = default.copy()
        
        for key, value in user.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的路径，如 'erp_pull.interval'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 读取完整配置
            with open(self.config_file, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f) or {}
            
            # 更新ERP集成部分
            full_config['erp_integration'] = self.config
            
            # 写回文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(full_config, f, allow_unicode=True, default_flow_style=False)
            
            logger.info(f"[配置] 配置已保存: {self.config_file}")
            
        except Exception as e:
            logger.error(f"[配置] 保存配置失败: {e}")
    
    def is_enabled(self) -> bool:
        """检查ERP集成是否启用"""
        return self.get('enabled', True)
    
    def get_erp_credentials(self) -> Dict:
        """获取ERP登录凭证"""
        return {
            'base_url': self.get('base_url'),
            'username': self.get('auth.username'),
            'password': self.get('auth.password')
        }

