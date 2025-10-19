#!/usr/bin/env python3
"""
同步管理器
管理客户信息在本地数据库、飞书、钉钉之间的自动同步
"""

# 强制 UTF-8 编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from customer_manager import customer_manager
from modules.integrations.feishu_bitable import feishu_sync
from modules.integrations.dingtalk_bitable import dingtalk_sync

class SyncManager:
    """同步管理器"""
    
    def __init__(self, sync_interval: int = 300):
        """
        初始化同步管理器
        
        Args:
            sync_interval: 同步间隔（秒），默认5分钟
        """
        self.sync_interval = sync_interval
        self.is_running = False
        self.sync_thread = None
        self.last_sync_time = None
        self.sync_enabled = {
            'feishu': False,
            'dingtalk': False
        }
        
        # 检测集成配置
        self._detect_integrations()
    
    def _detect_integrations(self):
        """检测已配置的集成"""
        import os
        
        # 检测飞书配置
        if os.getenv('FEISHU_APP_ID') and os.getenv('FEISHU_APP_SECRET') and \
           os.getenv('FEISHU_BITABLE_TOKEN') and os.getenv('FEISHU_TABLE_ID'):
            self.sync_enabled['feishu'] = True
            print("✅ 飞书集成已启用")
        
        # 检测钉钉配置
        if os.getenv('DINGTALK_APP_KEY') and os.getenv('DINGTALK_APP_SECRET') and \
           os.getenv('DINGTALK_BASE_ID') and os.getenv('DINGTALK_TABLE_ID'):
            self.sync_enabled['dingtalk'] = True
            print("✅ 钉钉集成已启用")
        
        if not any(self.sync_enabled.values()):
            print("⚠️  未检测到任何外部集成配置")
    
    def sync_from_external(self) -> Dict[str, any]:
        """
        从外部系统同步客户信息到本地
        
        Returns:
            同步结果统计
        """
        stats = {
            'feishu': {'total': 0, 'new': 0, 'updated': 0},
            'dingtalk': {'total': 0, 'new': 0, 'updated': 0}
        }
        
        # 从飞书同步
        if self.sync_enabled['feishu']:
            try:
                feishu_customers = feishu_sync.sync_customers_from_feishu()
                stats['feishu']['total'] = len(feishu_customers)
                
                for customer in feishu_customers:
                    result = self._import_customer(customer)
                    if result == 'new':
                        stats['feishu']['new'] += 1
                    elif result == 'updated':
                        stats['feishu']['updated'] += 1
                
                print(f"📥 飞书同步完成: {stats['feishu']}")
                
            except Exception as e:
                print(f"飞书同步失败: {e}")
        
        # 从钉钉同步
        if self.sync_enabled['dingtalk']:
            try:
                dingtalk_customers = dingtalk_sync.sync_customers_from_dingtalk()
                stats['dingtalk']['total'] = len(dingtalk_customers)
                
                for customer in dingtalk_customers:
                    result = self._import_customer(customer)
                    if result == 'new':
                        stats['dingtalk']['new'] += 1
                    elif result == 'updated':
                        stats['dingtalk']['updated'] += 1
                
                print(f"📥 钉钉同步完成: {stats['dingtalk']}")
                
            except Exception as e:
                print(f"钉钉同步失败: {e}")
        
        self.last_sync_time = datetime.now()
        return stats
    
    def _import_customer(self, external_customer: Dict) -> str:
        """
        导入外部客户信息
        
        Args:
            external_customer: 外部客户数据
            
        Returns:
            'new'|'updated'|'skipped'
        """
        customer_id = external_customer.get('customer_id')
        name = external_customer.get('name')
        group_name = external_customer.get('group_name')
        
        if not customer_id or not name or not group_name:
            return 'skipped'
        
        # 检查客户是否已存在
        existing = customer_manager.get_customer(customer_id)
        
        if existing:
            # 更新现有客户信息
            existing.notes = external_customer.get('notes', existing.notes)
            existing.priority = external_customer.get('priority', existing.priority)
            
            # 更新标签
            if external_customer.get('tags'):
                existing.tags = list(set(existing.tags + external_customer.get('tags')))
            
            customer_manager._save_customer(existing)
            return 'updated'
        else:
            # 注册新客户（使用外部编号）
            try:
                # 直接使用外部编号
                from customer_manager import Customer
                new_customer = Customer(
                    customer_id=customer_id,
                    name=name,
                    group_name=group_name,
                    group_type=self._get_group_type(group_name),
                    registration_time=datetime.now(),
                    last_active=datetime.now(),
                    notes=external_customer.get('notes', '从外部系统同步'),
                    priority=external_customer.get('priority', 3),
                    tags=external_customer.get('tags', [])
                )
                
                customer_manager._save_customer(new_customer)
                customer_manager.customers[customer_id] = new_customer
                
                return 'new'
                
            except Exception as e:
                print(f"导入客户失败 {customer_id}: {e}")
                return 'skipped'
    
    def _get_group_type(self, group_name: str) -> str:
        """获取群聊类型"""
        group_classification = customer_manager.get_group_classification(group_name)
        return group_classification.group_type if group_classification else 'normal'
    
    def sync_to_external(self, customer_ids: List[str] = None) -> Dict[str, any]:
        """
        同步本地客户信息到外部系统
        
        Args:
            customer_ids: 要同步的客户编号列表，None表示同步全部
            
        Returns:
            同步结果统计
        """
        stats = {
            'feishu': {'success': 0, 'failed': 0},
            'dingtalk': {'success': 0, 'failed': 0}
        }
        
        # 获取要同步的客户
        if customer_ids:
            customers = [customer_manager.get_customer(cid) for cid in customer_ids]
            customers = [c for c in customers if c]  # 过滤 None
        else:
            customers = customer_manager.get_customer_list(limit=1000)
        
        # 构建客户数据
        customer_data_list = []
        for customer in customers:
            customer_data = {
                'customer_id': customer.customer_id,
                'name': customer.name,
                'group_name': customer.group_name,
                'wechat_remark': customer.name,
                'priority': customer.priority,
                'notes': customer.notes,
                'total_questions': customer.total_questions,
                'solved_questions': customer.solved_questions,
                'handoff_count': customer.handoff_count,
                'last_active': customer.last_active.isoformat(),
                'tags': customer.tags
            }
            customer_data_list.append(customer_data)
        
        # 同步到飞书
        if self.sync_enabled['feishu']:
            try:
                result = feishu_sync.batch_sync_to_feishu(customer_data_list)
                stats['feishu'] = result
                print(f"📤 飞书同步完成: {result}")
            except Exception as e:
                print(f"飞书同步失败: {e}")
        
        # 同步到钉钉
        if self.sync_enabled['dingtalk']:
            try:
                result = dingtalk_sync.batch_sync_to_dingtalk(customer_data_list)
                stats['dingtalk'] = result
                print(f"📤 钉钉同步完成: {result}")
            except Exception as e:
                print(f"钉钉同步失败: {e}")
        
        return stats
    
    def start_auto_sync(self):
        """启动自动同步"""
        if self.is_running:
            print("自动同步已在运行")
            return
        
        if not any(self.sync_enabled.values()):
            print("未配置任何外部集成，无法启动自动同步")
            return
        
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        print(f"✅ 自动同步已启动，间隔：{self.sync_interval}秒")
    
    def stop_auto_sync(self):
        """停止自动同步"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("⏹️  自动同步已停止")
    
    def _sync_loop(self):
        """同步循环"""
        while self.is_running:
            try:
                print(f"\n🔄 开始定时同步 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
                
                # 从外部系统同步到本地
                from_external_stats = self.sync_from_external()
                
                # 从本地同步到外部系统
                to_external_stats = self.sync_to_external()
                
                print(f"✅ 同步完成")
                
            except Exception as e:
                print(f"同步循环异常: {e}")
            
            # 等待下一次同步
            for _ in range(self.sync_interval):
                if not self.is_running:
                    break
                time.sleep(1)
    
    def manual_sync(self, direction: str = 'both') -> Dict:
        """
        手动触发同步
        
        Args:
            direction: 'from'(从外部到本地), 'to'(从本地到外部), 'both'(双向)
            
        Returns:
            同步结果
        """
        result = {}
        
        if direction in ['from', 'both']:
            result['from_external'] = self.sync_from_external()
        
        if direction in ['to', 'both']:
            result['to_external'] = self.sync_to_external()
        
        return result
    
    def get_sync_status(self) -> Dict:
        """获取同步状态"""
        return {
            'is_running': self.is_running,
            'sync_interval': self.sync_interval,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'enabled_integrations': self.sync_enabled,
            'total_customers': len(customer_manager.customers)
        }

# 全局实例
sync_manager = SyncManager()

if __name__ == "__main__":
    # 测试同步功能
    print("🧪 测试同步管理器...")
    
    # 获取同步状态
    status = sync_manager.get_sync_status()
    print(f"📊 同步状态: {status}")
    
    # 手动触发同步
    print("\n🔄 执行手动同步...")
    result = sync_manager.manual_sync('from')
    print(f"同步结果: {result}")
    
    # 显示客户统计
    stats = customer_manager.get_customer_statistics()
    print(f"\n📊 客户统计: {stats}")
