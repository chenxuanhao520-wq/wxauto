"""
集成模块
支持飞书、钉钉等外部系统集成
"""

from .feishu_bitable import feishu_client, feishu_sync
from .dingtalk_bitable import dingtalk_client, dingtalk_sync

__all__ = [
    'feishu_client',
    'feishu_sync',
    'dingtalk_client',
    'dingtalk_sync'
]