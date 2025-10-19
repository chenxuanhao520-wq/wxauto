"""
变更检测器
检测ERP数据和本地数据的差异，智能决定采用哪个数据源
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ChangeDetector:
    """变更检测器"""
    
    # 字段优先级定义（数字越大优先级越高）
    FIELD_PRIORITY = {
        'phone': 10,                    # 手机号最重要
        'company_name': 9,
        'real_name': 8,
        'email': 7,
        'address': 6,
        'business_license_info': 5,
        'erp_customer_code': 4,
        'wechat_id': 3,
        'wechat_nickname': 1,           # 微信昵称优先级最低
    }
    
    # 字段来源优先策略
    FIELD_SOURCE_STRATEGY = {
        # 核心字段：ERP优先（除非本地已验证）
        'phone': 'erp_unless_verified',
        'company_name': 'erp_unless_verified',
        'real_name': 'erp_unless_verified',
        'erp_customer_code': 'erp_always',
        'erp_customer_id': 'erp_always',
        
        # 补充字段：本地优先
        'wechat_id': 'local_always',
        'wechat_nickname': 'local_always',
        'wechat_avatar': 'local_always',
        'intent_score': 'local_always',
        'message_count': 'local_always',
        
        # 其他字段：最新的优先
        'email': 'latest',
        'address': 'latest',
    }
    
    def __init__(self):
        pass
    
    def detect_changes(self, erp_data: Dict, local_data: Dict) -> Dict:
        """
        检测ERP数据和本地数据的差异
        
        Args:
            erp_data: 从ERP拉取的数据
            local_data: 本地数据库中的数据
            
        Returns:
            {
                'has_changes': bool,
                'changes': [
                    {
                        'field': str,
                        'erp_value': any,
                        'local_value': any,
                        'priority': int,
                        'action': 'take_erp'/'take_local'/'merge'/'skip',
                        'reason': str
                    }
                ]
            }
        """
        changes = []
        
        # 映射ERP字段到本地字段
        field_mapping = {
            'ord': 'erp_customer_id',
            'khid': 'erp_customer_code',
            'name': 'company_name',
            'person_name': 'real_name',
            'mobile': 'phone',
            'email': 'email',
            'address': 'address',
            'weixinAcc': 'wechat_id',
        }
        
        # 检查所有字段
        for erp_field, local_field in field_mapping.items():
            erp_value = erp_data.get(erp_field)
            local_value = local_data.get(local_field)
            
            # 规范化值（空字符串视为None）
            erp_value = self._normalize_value(erp_value)
            local_value = self._normalize_value(local_value)
            
            # 如果值不同，记录变更
            if erp_value != local_value:
                action, reason = self._decide_value_source(
                    local_field, erp_value, local_value, local_data
                )
                
                changes.append({
                    'field': local_field,
                    'erp_field': erp_field,
                    'erp_value': erp_value,
                    'local_value': local_value,
                    'priority': self.FIELD_PRIORITY.get(local_field, 0),
                    'action': action,
                    'reason': reason
                })
        
        # 按优先级排序
        changes.sort(key=lambda x: x['priority'], reverse=True)
        
        return {
            'has_changes': len(changes) > 0,
            'changes': changes,
            'change_count': len(changes)
        }
    
    def _normalize_value(self, value):
        """规范化值"""
        if value is None or value == '' or value == 'None':
            return None
        if isinstance(value, str):
            return value.strip()
        return value
    
    def _decide_value_source(self, field: str, erp_value, local_value, 
                            local_data: Dict) -> tuple:
        """
        决定采用哪个数据源的值
        
        Returns:
            (action, reason): 动作和原因
        """
        strategy = self.FIELD_SOURCE_STRATEGY.get(field, 'latest')
        
        # 策略1: ERP永远优先
        if strategy == 'erp_always':
            if erp_value and not local_value:
                return ('take_erp', 'ERP有值，本地无值')
            elif erp_value and local_value and erp_value != local_value:
                return ('take_erp', 'ERP字段永远为准')
            else:
                return ('skip', '无需变更')
        
        # 策略2: 本地永远优先
        elif strategy == 'local_always':
            if local_value and not erp_value:
                return ('take_local', '本地有值，ERP无值，需推送')
            elif local_value:
                return ('skip', '本地字段优先，无需从ERP更新')
            elif erp_value:
                return ('take_erp', 'ERP有值，本地无值')
            else:
                return ('skip', '双方都无值')
        
        # 策略3: ERP优先，但本地已验证则本地优先
        elif strategy == 'erp_unless_verified':
            verified_field = f"{field}_verified"
            is_verified = local_data.get(verified_field, False)
            
            if not erp_value and local_value:
                # ERP空，本地有
                if is_verified:
                    return ('take_local', '本地已验证，需推送到ERP')
                else:
                    return ('skip', '本地未验证，暂不推送')
            
            elif erp_value and not local_value:
                # ERP有，本地空
                return ('take_erp', 'ERP有值，从ERP拉取')
            
            elif erp_value and local_value and erp_value != local_value:
                # 都有值但不同
                if is_verified:
                    return ('take_local', '本地已验证，以本地为准')
                else:
                    return ('take_erp', '本地未验证，以ERP为准')
            
            else:
                return ('skip', '无需变更')
        
        # 策略4: 最新的优先
        elif strategy == 'latest':
            local_updated = local_data.get('local_updated_at')
            erp_updated = local_data.get('erp_updated_at')
            
            if not erp_value and local_value:
                return ('take_local', '本地有值，ERP无值')
            elif erp_value and not local_value:
                return ('take_erp', 'ERP有值，本地无值')
            elif erp_value and local_value and erp_value != local_value:
                # 比较时间戳
                if local_updated and erp_updated:
                    if local_updated > erp_updated:
                        return ('take_local', '本地更新时间更晚')
                    else:
                        return ('take_erp', 'ERP更新时间更晚')
                else:
                    return ('merge', '无法判断，需人工决策')
            else:
                return ('skip', '无需变更')
        
        return ('skip', '未知策略')
    
    def get_fields_to_push(self, changes: List[Dict]) -> Dict:
        """
        获取需要推送到ERP的字段
        
        Args:
            changes: 变更列表
            
        Returns:
            Dict: 需要推送的字段字典 {local_field: value}
        """
        fields_to_push = {}
        
        for change in changes:
            if change['action'] == 'take_local':
                field = change['field']
                value = change['local_value']
                
                # 映射回ERP字段名
                erp_field = change.get('erp_field', field)
                fields_to_push[erp_field] = value
        
        return fields_to_push
    
    def get_fields_to_pull(self, changes: List[Dict]) -> Dict:
        """
        获取需要从ERP拉取的字段
        
        Args:
            changes: 变更列表
            
        Returns:
            Dict: 需要更新的本地字段字典 {local_field: value}
        """
        fields_to_pull = {}
        
        for change in changes:
            if change['action'] == 'take_erp':
                field = change['field']
                value = change['erp_value']
                fields_to_pull[field] = value
        
        return fields_to_pull
    
    def log_changes(self, customer_id: int, changes: List[Dict], 
                    sync_direction: str = 'bidirectional'):
        """
        记录变更到数据库
        
        Args:
            customer_id: 客户ID
            changes: 变更列表
            sync_direction: 同步方向
        """
        from storage.db import get_db_connection
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            for change in changes:
                if change['action'] == 'skip':
                    continue
                
                field = change['field']
                old_value = change['local_value']
                new_value = change['erp_value'] if change['action'] == 'take_erp' else change['local_value']
                source = 'erp' if change['action'] == 'take_erp' else 'local'
                
                cursor.execute('''
                    INSERT INTO field_change_history
                    (customer_id, field_name, old_value, new_value, 
                     value_source, change_type, change_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer_id,
                    field,
                    str(old_value) if old_value is not None else None,
                    str(new_value) if new_value is not None else None,
                    source,
                    'merge',
                    change['reason']
                ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"[变更检测] 记录了 {len(changes)} 个字段变更")
            
        except Exception as e:
            logger.error(f"[变更检测] 记录变更失败: {e}")

