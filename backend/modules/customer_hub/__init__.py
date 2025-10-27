"""
客户中台模块
Customer Hub - 基于"最后说话方 + SLA"的客户分级系统
"""

from .types import (
    Party, ThreadStatus, Bucket, ContactType, ContactSource,
    TriggerLabel, Contact, Thread, Signal, SLAConfig, 
    TriggerOutput, ScoringRules, InboundMessage
)

__all__ = [
    'Party', 'ThreadStatus', 'Bucket', 'ContactType', 'ContactSource',
    'TriggerLabel', 'Contact', 'Thread', 'Signal', 'SLAConfig',
    'TriggerOutput', 'ScoringRules', 'InboundMessage'
]

