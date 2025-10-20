"""客户数据仓储"""
import json
import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from src.models import Customer, GroupClassification


class CustomerRepository:
    """客户数据访问层（Repository模式）"""
    
    def __init__(self, db_path: str = "data/data.db"):
        self.db_path = db_path
        self._ensure_tables()
    
    def _ensure_tables(self):
        """确保数据库表存在"""
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
                    priority INTEGER DEFAULT 3,
                    erp_customer_code TEXT,
                    phone TEXT,
                    company_name TEXT
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
            
            conn.commit()
    
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """根据ID获取客户"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM customers WHERE customer_id = ?",
                (customer_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_customer(row)
            return None
    
    def find_by_name_and_group(self, name: str, group_name: str) -> Optional[Customer]:
        """根据姓名和群聊查找客户"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM customers WHERE name = ? AND group_name = ?",
                (name, group_name)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_customer(row)
            return None
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """列出所有客户"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM customers ORDER BY last_active DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            
            return [self._row_to_customer(row) for row in rows]
    
    def save(self, customer: Customer) -> bool:
        """保存客户（新增或更新）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO customers (
                    customer_id, name, group_name, group_type,
                    registration_time, last_active,
                    total_questions, solved_questions, handoff_count,
                    tags, notes, priority,
                    erp_customer_code, phone, company_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer.customer_id,
                customer.name,
                customer.group_name,
                customer.group_type,
                customer.registration_time,
                customer.last_active,
                customer.total_questions,
                customer.solved_questions,
                customer.handoff_count,
                json.dumps(customer.tags, ensure_ascii=False),
                customer.notes,
                customer.priority,
                customer.erp_customer_code,
                customer.phone,
                customer.company_name
            ))
            
            conn.commit()
            return True
    
    def delete(self, customer_id: str) -> bool:
        """删除客户"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_activity(self, customer_id: str, timestamp: datetime = None) -> bool:
        """更新客户活跃时间"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customers SET last_active = ? WHERE customer_id = ?",
                (timestamp, customer_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def increment_questions(self, customer_id: str, solved: bool = False) -> bool:
        """增加问题计数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if solved:
                cursor.execute(
                    "UPDATE customers SET total_questions = total_questions + 1, solved_questions = solved_questions + 1 WHERE customer_id = ?",
                    (customer_id,)
                )
            else:
                cursor.execute(
                    "UPDATE customers SET total_questions = total_questions + 1 WHERE customer_id = ?",
                    (customer_id,)
                )
            conn.commit()
            return cursor.rowcount > 0
    
    # Group Classification 方法
    
    def get_group_classification(self, group_name: str) -> Optional[GroupClassification]:
        """获取群聊分类"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM group_classifications WHERE group_name = ?",
                (group_name,)
            )
            row = cursor.fetchone()
            
            if row:
                return GroupClassification(
                    group_name=row['group_name'],
                    group_type=row['group_type'],
                    description=row['description'],
                    auto_response=bool(row['auto_response']),
                    require_customer_id=bool(row['require_customer_id']),
                    max_questions_per_day=row['max_questions_per_day'],
                    priority=row['priority']
                )
            return None
    
    def save_group_classification(self, group: GroupClassification) -> bool:
        """保存群聊分类"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO group_classifications (
                    group_name, group_type, description,
                    auto_response, require_customer_id,
                    max_questions_per_day, priority
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                group.group_name,
                group.group_type,
                group.description,
                group.auto_response,
                group.require_customer_id,
                group.max_questions_per_day,
                group.priority
            ))
            
            conn.commit()
            return True
    
    # 辅助方法
    
    def _row_to_customer(self, row: sqlite3.Row) -> Customer:
        """将数据库行转换为Customer对象"""
        return Customer(
            customer_id=row['customer_id'],
            name=row['name'],
            group_name=row['group_name'],
            group_type=row['group_type'],
            registration_time=datetime.fromisoformat(row['registration_time']),
            last_active=datetime.fromisoformat(row['last_active']),
            total_questions=row['total_questions'],
            solved_questions=row['solved_questions'],
            handoff_count=row['handoff_count'],
            tags=json.loads(row['tags']),
            notes=row['notes'],
            priority=row['priority'],
            erp_customer_code=row['erp_customer_code'],
            phone=row['phone'],
            company_name=row['company_name']
        )

