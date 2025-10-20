"""
客户服务适配器 - 兼容旧接口
为旧代码提供向后兼容性，同时使用新的服务层
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Customer as NewCustomer, GroupClassification as NewGroupClassification
from src.repositories import CustomerRepository
from src.services import CustomerService

# 为了向后兼容，使用别名
Customer = NewCustomer
GroupClassification = NewGroupClassification


class CustomerManager:
    """客户管理器（适配器模式 - 兼容旧接口）
    
    这是一个适配器，将旧的customer_manager接口映射到新的CustomerService
    """
    
    def __init__(self, db_path: str = "data/data.db"):
        self.db_path = db_path
        self.repo = CustomerRepository(db_path)
        self.service = CustomerService(self.repo)
        
        # 为了兼容，保留这些属性
        self.customers = {}  # 已废弃，但保留以防旧代码引用
        self.groups = {}     # 已废弃，但保留以防旧代码引用
    
    # ============================================================
    # 兼容旧接口
    # ============================================================
    
    def get_customer(self, customer_id: str):
        """获取客户（兼容旧接口）"""
        return self.service.get_customer(customer_id)
    
    def register_customer(self, name: str, group_name: str, notes: str = "", priority: int = 3) -> str:
        """注册新客户（兼容旧接口）"""
        customer = self.service._create_customer(name, group_name, notes)
        if priority != 3:
            self.service.update_customer(customer.customer_id, priority=priority)
        return customer.customer_id
    
    def find_customer_by_name(self, name: str, group_name: str):
        """根据姓名查找客户（兼容旧接口）"""
        return self.repo.find_by_name_and_group(name, group_name)
    
    def update_customer_activity(self, customer_id: str):
        """更新客户活跃时间（兼容旧接口）"""
        return self.service.update_activity(customer_id)
    
    def add_customer_tag(self, customer_id: str, tag: str):
        """添加标签（兼容旧接口）"""
        return self.service.add_tag(customer_id, tag)
    
    def get_group_classification(self, group_name: str):
        """获取群聊分类（兼容旧接口）"""
        return self.service.get_group_classification(group_name)
    
    def get_all_customers(self):
        """获取所有客户（兼容旧接口）"""
        return self.service.list_customers(limit=10000)
    
    def save(self):
        """保存（兼容旧接口 - 新架构下不需要显式保存）"""
        pass  # 新架构自动保存，保留此方法仅为兼容
    
    def load(self):
        """加载（兼容旧接口 - 新架构下不需要显式加载）"""
        pass  # 新架构自动加载，保留此方法仅为兼容


# 全局实例（兼容旧代码）
customer_manager = CustomerManager()


def init_default_groups():
    """初始化默认群聊分类（兼容旧接口）"""
    customer_manager.service.init_default_groups()

