"""
ERP同步模块
实现微信客服中台与智邦ERP的双向自动同步

模块结构：
- erp_client.py: ERP API客户端
- rule_engine.py: 同步规则引擎
- change_detector.py: 变更检测器
- sync_service.py: 同步服务
- scheduler.py: 定时任务调度
"""

__version__ = "1.0.0"
__author__ = "wxauto-erp-integration"

from .erp_client import ERPClient
from .rule_engine import SyncRuleEngine
from .change_detector import ChangeDetector
from .sync_service import UnifiedCustomerSyncService
from .scheduler import ERPSyncScheduler

__all__ = [
    'ERPClient',
    'SyncRuleEngine',
    'ChangeDetector',
    'UnifiedCustomerSyncService',
    'ERPSyncScheduler'
]

