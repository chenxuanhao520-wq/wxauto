"""客户相关数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Customer:
    """客户信息模型"""
    customer_id: str
    name: str
    group_name: str
    group_type: str
    registration_time: datetime
    last_active: datetime
    total_questions: int = 0
    solved_questions: int = 0
    handoff_count: int = 0
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    priority: int = 3  # 1-5，3为默认
    
    # ERP 集成字段（可选）
    erp_customer_code: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    
    @property
    def satisfaction_rate(self) -> float:
        """客户满意度（基于解决率）"""
        if self.total_questions == 0:
            return 0.0
        return self.solved_questions / self.total_questions
    
    @property
    def is_vip(self) -> bool:
        """是否为VIP客户"""
        return self.priority >= 4
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'customer_id': self.customer_id,
            'name': self.name,
            'group_name': self.group_name,
            'group_type': self.group_type,
            'registration_time': self.registration_time.isoformat(),
            'last_active': self.last_active.isoformat(),
            'total_questions': self.total_questions,
            'solved_questions': self.solved_questions,
            'handoff_count': self.handoff_count,
            'tags': self.tags,
            'notes': self.notes,
            'priority': self.priority,
            'erp_customer_code': self.erp_customer_code,
            'phone': self.phone,
            'company_name': self.company_name,
            'satisfaction_rate': self.satisfaction_rate,
            'is_vip': self.is_vip
        }


@dataclass
class GroupClassification:
    """群聊分类模型"""
    group_name: str
    group_type: str  # vip, normal, test, internal
    description: str = ""
    auto_response: bool = True
    require_customer_id: bool = True
    max_questions_per_day: int = 50
    priority: int = 3
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'group_name': self.group_name,
            'group_type': self.group_type,
            'description': self.description,
            'auto_response': self.auto_response,
            'require_customer_id': self.require_customer_id,
            'max_questions_per_day': self.max_questions_per_day,
            'priority': self.priority
        }

