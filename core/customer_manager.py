#!/usr/bin/env python3
"""
客户管理系统
实现客户编号管理、分类、智能分析等功能
"""

# 强制 UTF-8 编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class Customer:
    """客户信息"""
    customer_id: str          # KXXXX 格式
    name: str                 # 客户名称
    group_name: str           # 所属群聊
    group_type: str           # 群聊类型
    registration_time: datetime
    last_active: datetime
    total_questions: int = 0
    solved_questions: int = 0
    handoff_count: int = 0
    tags: List[str] = None
    notes: str = ""
    priority: int = 1         # 优先级 1-5
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class GroupClassification:
    """群聊分类"""
    group_name: str
    group_type: str           # vip, normal, test, internal
    description: str
    auto_response: bool = True
    require_customer_id: bool = True
    max_questions_per_day: int = 50
    priority: int = 3

class CustomerManager:
    """客户管理器"""
    
    def __init__(self, db_path: str = "data/data.db"):
        self.db_path = db_path
        self.customers: Dict[str, Customer] = {}
        self.groups: Dict[str, GroupClassification] = {}
        self._init_database()
        self._load_data()
    
    def _init_database(self):
        """初始化数据库表"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 客户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    group_name TEXT NOT NULL,
                    group_type TEXT NOT NULL,
                    registration_time DATETIME NOT NULL,
                    last_active DATETIME NOT NULL,
                    total_questions INTEGER DEFAULT 0,
                    solved_questions INTEGER DEFAULT 0,
                    handoff_count INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '[]',
                    notes TEXT DEFAULT '',
                    priority INTEGER DEFAULT 1
                )
            """)
            
            # 群聊分类表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_classifications (
                    group_name TEXT PRIMARY KEY,
                    group_type TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    auto_response BOOLEAN DEFAULT 1,
                    require_customer_id BOOLEAN DEFAULT 1,
                    max_questions_per_day INTEGER DEFAULT 50,
                    priority INTEGER DEFAULT 3
                )
            """)
            
            # 客户会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id TEXT NOT NULL,
                    session_id INTEGER NOT NULL,
                    question_type TEXT,
                    confidence_score REAL,
                    analysis_result TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
                )
            """)
            
            conn.commit()
    
    def _load_data(self):
        """加载数据"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 加载客户数据
            cursor.execute("SELECT * FROM customers")
            for row in cursor.fetchall():
                customer = Customer(
                    customer_id=row[0],
                    name=row[1],
                    group_name=row[2],
                    group_type=row[3],
                    registration_time=datetime.fromisoformat(row[4]),
                    last_active=datetime.fromisoformat(row[5]),
                    total_questions=row[6],
                    solved_questions=row[7],
                    handoff_count=row[8],
                    tags=json.loads(row[9]) if row[9] else [],
                    notes=row[10],
                    priority=row[11]
                )
                self.customers[customer.customer_id] = customer
            
            # 加载群聊分类
            cursor.execute("SELECT * FROM group_classifications")
            for row in cursor.fetchall():
                group = GroupClassification(
                    group_name=row[0],
                    group_type=row[1],
                    description=row[2],
                    auto_response=bool(row[3]),
                    require_customer_id=bool(row[4]),
                    max_questions_per_day=row[5],
                    priority=row[6]
                )
                self.groups[group.group_name] = group
    
    def generate_customer_id(self) -> str:
        """生成客户编号 KXXXX"""
        # 获取当前最大编号
        max_num = 0
        for customer_id in self.customers.keys():
            if customer_id.startswith('K') and len(customer_id) == 5:
                try:
                    num = int(customer_id[1:])
                    max_num = max(max_num, num)
                except ValueError:
                    continue
        
        # 生成新编号
        new_num = max_num + 1
        return f"K{new_num:04d}"
    
    def register_customer(self, name: str, group_name: str, 
                         notes: str = "", priority: int = 1) -> str:
        """注册新客户"""
        # 获取群聊类型
        group_type = "normal"
        if group_name in self.groups:
            group_type = self.groups[group_name].group_type
        
        # 生成客户编号
        customer_id = self.generate_customer_id()
        
        # 创建客户
        customer = Customer(
            customer_id=customer_id,
            name=name,
            group_name=group_name,
            group_type=group_type,
            registration_time=datetime.now(),
            last_active=datetime.now(),
            notes=notes,
            priority=priority
        )
        
        # 保存到数据库
        self._save_customer(customer)
        self.customers[customer_id] = customer
        
        return customer_id
    
    def _save_customer(self, customer: Customer):
        """保存客户到数据库"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO customers 
                (customer_id, name, group_name, group_type, registration_time, 
                 last_active, total_questions, solved_questions, handoff_count, 
                 tags, notes, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer.customer_id, customer.name, customer.group_name,
                customer.group_type, customer.registration_time.isoformat(),
                customer.last_active.isoformat(), customer.total_questions,
                customer.solved_questions, customer.handoff_count,
                json.dumps(customer.tags), customer.notes, customer.priority
            ))
            conn.commit()
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """获取客户信息"""
        return self.customers.get(customer_id)
    
    def find_customer_by_name(self, name: str, group_name: str) -> Optional[Customer]:
        """根据姓名和群聊查找客户"""
        for customer in self.customers.values():
            if customer.name == name and customer.group_name == group_name:
                return customer
        return None
    
    def update_customer_activity(self, customer_id: str, question_solved: bool = False, 
                                handoff: bool = False):
        """更新客户活动"""
        customer = self.get_customer(customer_id)
        if not customer:
            return
        
        customer.last_active = datetime.now()
        customer.total_questions += 1
        
        if question_solved:
            customer.solved_questions += 1
        
        if handoff:
            customer.handoff_count += 1
        
        self._save_customer(customer)
    
    def add_group_classification(self, group_name: str, group_type: str, 
                               description: str = "", **kwargs):
        """添加群聊分类"""
        group = GroupClassification(
            group_name=group_name,
            group_type=group_type,
            description=description,
            **kwargs
        )
        
        # 保存到数据库
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO group_classifications
                (group_name, group_type, description, auto_response, 
                 require_customer_id, max_questions_per_day, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                group.group_name, group.group_type, group.description,
                group.auto_response, group.require_customer_id,
                group.max_questions_per_day, group.priority
            ))
            conn.commit()
        
        self.groups[group_name] = group
    
    def get_group_classification(self, group_name: str) -> Optional[GroupClassification]:
        """获取群聊分类"""
        return self.groups.get(group_name)
    
    def analyze_customer_question(self, customer_id: str, question: str, 
                                knowledge_result: Dict) -> Dict[str, Any]:
        """分析客户问题"""
        customer = self.get_customer(customer_id)
        if not customer:
            return {"error": "客户不存在"}
        
        # 构建分析提示
        analysis_prompt = f"""
作为专业的客服分析系统，请深度分析以下客户问题：

客户信息：
- 客户编号：{customer.customer_id}
- 客户姓名：{customer.name}
- 群聊类型：{customer.group_type}
- 历史问题数：{customer.total_questions}
- 解决率：{customer.solved_questions}/{customer.total_questions}
- 优先级：{customer.priority}/5

客户问题：{question}

知识库检索结果：
- 相关文档数：{len(knowledge_result.get('documents', []))}
- 最高置信度：{knowledge_result.get('confidence', 0):.2f}
- 证据摘要：{knowledge_result.get('evidence_summary', '无')}

请提供以下分析：
1. 问题类型分类（技术问题/咨询问题/投诉问题/其他）
2. 紧急程度评估（1-5级）
3. 复杂度评估（简单/中等/复杂）
4. 是否需要人工介入（是/否）
5. 推荐回复策略
6. 客户满意度预测
7. 风险提示

请以JSON格式返回分析结果。
"""
        
        # 这里应该调用大模型进行分析
        # 暂时返回模拟结果
        analysis_result = {
            "question_type": "技术问题",
            "urgency_level": 3,
            "complexity": "中等",
            "needs_human": False,
            "recommended_strategy": "基于知识库提供详细解答",
            "satisfaction_prediction": 0.85,
            "risk_warning": "无特殊风险",
            "analysis_time": datetime.now().isoformat()
        }
        
        return analysis_result
    
    def get_customer_statistics(self) -> Dict[str, Any]:
        """获取客户统计信息"""
        total_customers = len(self.customers)
        vip_customers = sum(1 for c in self.customers.values() if c.group_type == "vip")
        active_customers = sum(1 for c in self.customers.values() 
                             if (datetime.now() - c.last_active).days <= 7)
        
        total_questions = sum(c.total_questions for c in self.customers.values())
        solved_questions = sum(c.solved_questions for c in self.customers.values())
        solve_rate = solved_questions / total_questions if total_questions > 0 else 0
        
        return {
            "total_customers": total_customers,
            "vip_customers": vip_customers,
            "active_customers": active_customers,
            "total_questions": total_questions,
            "solved_questions": solved_questions,
            "solve_rate": solve_rate,
            "groups_count": len(self.groups)
        }
    
    def get_customer_list(self, group_name: str = None, 
                         limit: int = 100) -> List[Customer]:
        """获取客户列表"""
        customers = list(self.customers.values())
        
        if group_name:
            customers = [c for c in customers if c.group_name == group_name]
        
        # 按最后活跃时间排序
        customers.sort(key=lambda c: c.last_active, reverse=True)
        
        return customers[:limit]

# 全局实例
customer_manager = CustomerManager()

def init_default_groups():
    """初始化默认群聊分类"""
    manager = customer_manager
    
    # VIP客户群
    manager.add_group_classification(
        group_name="VIP客户群",
        group_type="vip",
        description="VIP客户专属群聊",
        auto_response=True,
        require_customer_id=True,
        max_questions_per_day=100,
        priority=5
    )
    
    # 技术支持群
    manager.add_group_classification(
        group_name="技术支持群",
        group_type="normal",
        description="普通技术支持群聊",
        auto_response=True,
        require_customer_id=True,
        max_questions_per_day=50,
        priority=3
    )
    
    # 测试群
    manager.add_group_classification(
        group_name="测试群",
        group_type="test",
        description="系统测试群聊",
        auto_response=True,
        require_customer_id=False,
        max_questions_per_day=200,
        priority=1
    )

if __name__ == "__main__":
    # 初始化默认群聊分类
    init_default_groups()
    
    # 测试客户注册
    customer_id = customer_manager.register_customer(
        name="张三",
        group_name="技术支持群",
        notes="新客户，需要重点关注",
        priority=2
    )
    
    print(f"注册客户成功，编号：{customer_id}")
    
    # 显示统计信息
    stats = customer_manager.get_customer_statistics()
    print(f"客户统计：{stats}")
