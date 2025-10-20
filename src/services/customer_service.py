"""客户服务层（业务逻辑）"""
import re
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.models import Customer, GroupClassification
from src.repositories import CustomerRepository


class CustomerService:
    """客户管理服务（业务层）
    
    职责：
    - 客户生命周期管理
    - 客户分级与打标
    - 统计与分析
    - 与ERP系统同步（通过事件）
    """
    
    def __init__(self, repository: CustomerRepository):
        self.repo = repository
    
    # ============================================================
    # 客户基础操作
    # ============================================================
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """获取客户信息"""
        return self.repo.get_by_id(customer_id)
    
    def get_or_create_customer(
        self,
        name: str,
        group_name: str,
        notes: str = ""
    ) -> Customer:
        """获取或创建客户"""
        # 先尝试查找
        customer = self.repo.find_by_name_and_group(name, group_name)
        if customer:
            # 更新活跃时间
            self.repo.update_activity(customer.customer_id)
            return customer
        
        # 创建新客户
        return self._create_customer(name, group_name, notes)
    
    def _create_customer(
        self,
        name: str,
        group_name: str,
        notes: str = ""
    ) -> Customer:
        """创建新客户"""
        # 生成客户ID
        customer_id = self._generate_customer_id()
        
        # 获取群聊分类
        group_classification = self.repo.get_group_classification(group_name)
        group_type = group_classification.group_type if group_classification else "normal"
        priority = group_classification.priority if group_classification else 3
        
        # 创建客户对象
        now = datetime.now()
        customer = Customer(
            customer_id=customer_id,
            name=name,
            group_name=group_name,
            group_type=group_type,
            registration_time=now,
            last_active=now,
            notes=notes,
            priority=priority
        )
        
        # 保存到数据库
        self.repo.save(customer)
        
        return customer
    
    def update_customer(
        self,
        customer_id: str,
        **kwargs
    ) -> bool:
        """更新客户信息"""
        customer = self.repo.get_by_id(customer_id)
        if not customer:
            return False
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
        
        return self.repo.save(customer)
    
    def delete_customer(self, customer_id: str) -> bool:
        """删除客户"""
        return self.repo.delete(customer_id)
    
    def list_customers(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Customer]:
        """列出客户"""
        return self.repo.list_all(limit, offset)
    
    # ============================================================
    # 客户活动追踪
    # ============================================================
    
    def record_question(
        self,
        customer_id: str,
        solved: bool = False
    ) -> bool:
        """记录客户提问"""
        success = self.repo.increment_questions(customer_id, solved)
        if success:
            self.repo.update_activity(customer_id)
        return success
    
    def update_activity(self, customer_id: str) -> bool:
        """更新客户活跃时间"""
        return self.repo.update_activity(customer_id)
    
    # ============================================================
    # 客户分级与打标
    # ============================================================
    
    def classify_customer(self, customer: Customer) -> int:
        """客户分级（1-5，5最高）
        
        规则：
        - VIP群：4-5级
        - 高活跃度（>100问题）：4级
        - 中活跃度（>50问题）：3级
        - 低活跃度：2级
        - 新客户：1级
        """
        # VIP群直接高优先级
        if customer.group_type == "vip":
            return 5
        
        # 根据活跃度分级
        if customer.total_questions >= 100:
            return 4
        elif customer.total_questions >= 50:
            return 3
        elif customer.total_questions >= 10:
            return 2
        else:
            return 1
    
    def add_tag(self, customer_id: str, tag: str) -> bool:
        """添加标签"""
        customer = self.repo.get_by_id(customer_id)
        if not customer:
            return False
        
        if tag not in customer.tags:
            customer.tags.append(tag)
            return self.repo.save(customer)
        
        return True
    
    def remove_tag(self, customer_id: str, tag: str) -> bool:
        """移除标签"""
        customer = self.repo.get_by_id(customer_id)
        if not customer:
            return False
        
        if tag in customer.tags:
            customer.tags.remove(tag)
            return self.repo.save(customer)
        
        return True
    
    def auto_tag_by_content(self, customer_id: str, content: str) -> List[str]:
        """根据内容自动打标签"""
        tags = []
        
        # 产品相关
        if any(kw in content for kw in ['充电桩', '充电站', '设备']):
            tags.append('产品咨询')
        
        # 技术相关
        if any(kw in content for kw in ['故障', '报错', '不能用', '问题']):
            tags.append('技术支持')
        
        # 商务相关
        if any(kw in content for kw in ['价格', '报价', '合作', '订单']):
            tags.append('商务咨询')
        
        # 批量添加标签
        for tag in tags:
            self.add_tag(customer_id, tag)
        
        return tags
    
    # ============================================================
    # 群聊管理
    # ============================================================
    
    def get_group_classification(self, group_name: str) -> Optional[GroupClassification]:
        """获取群聊分类"""
        return self.repo.get_group_classification(group_name)
    
    def save_group_classification(self, group: GroupClassification) -> bool:
        """保存群聊分类"""
        return self.repo.save_group_classification(group)
    
    def init_default_groups(self):
        """初始化默认群聊分类"""
        default_groups = [
            GroupClassification(
                group_name="VIP客户群",
                group_type="vip",
                description="VIP客户专属服务",
                priority=5,
                max_questions_per_day=200
            ),
            GroupClassification(
                group_name="技术支持群",
                group_type="normal",
                description="技术支持与答疑",
                priority=4,
                max_questions_per_day=100
            ),
            GroupClassification(
                group_name="测试群",
                group_type="test",
                description="测试与调试",
                priority=2,
                max_questions_per_day=500,
                auto_response=True,
                require_customer_id=False
            )
        ]
        
        for group in default_groups:
            self.repo.save_group_classification(group)
    
    # ============================================================
    # 统计与分析
    # ============================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取客户统计信息"""
        all_customers = self.repo.list_all(limit=10000)
        
        total = len(all_customers)
        vip_count = sum(1 for c in all_customers if c.is_vip)
        active_count = sum(1 for c in all_customers if c.total_questions > 10)
        
        avg_questions = sum(c.total_questions for c in all_customers) / total if total > 0 else 0
        avg_satisfaction = sum(c.satisfaction_rate for c in all_customers) / total if total > 0 else 0
        
        return {
            'total_customers': total,
            'vip_customers': vip_count,
            'active_customers': active_count,
            'avg_questions_per_customer': round(avg_questions, 2),
            'avg_satisfaction_rate': round(avg_satisfaction * 100, 2)
        }
    
    # ============================================================
    # 辅助方法
    # ============================================================
    
    def _generate_customer_id(self) -> str:
        """生成客户ID（格式：KXXXX）"""
        import uuid
        # 使用时间戳 + 随机数生成唯一ID
        timestamp = int(datetime.now().timestamp() * 1000)
        random_part = str(uuid.uuid4())[:4]
        return f"K{timestamp % 100000:05d}"
    
    def _extract_phone(self, content: str) -> Optional[str]:
        """从文本中提取手机号"""
        pattern = r'1[3-9]\d{9}'
        match = re.search(pattern, content)
        return match.group() if match else None
    
    def _extract_company(self, content: str) -> Optional[str]:
        """从文本中提取公司名"""
        # 简单规则：包含"公司"/"企业"的短语
        pattern = r'([^\s，。；]{2,20}(?:公司|企业))'
        match = re.search(pattern, content)
        return match.group(1) if match else None

