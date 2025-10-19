"""
统一客户同步服务
实现ERP与本地数据库的双向自动同步
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from modules.storage.db import Database

from .erp_client import ERPClient
from .rule_engine import SyncRuleEngine
from .change_detector import ChangeDetector

logger = logging.getLogger(__name__)


class UnifiedCustomerSyncService:
    """统一客户同步服务"""
    
    def __init__(self, erp_client: ERPClient, rule_engine: SyncRuleEngine, 
                 change_detector: ChangeDetector):
        """
        初始化同步服务
        
        Args:
            erp_client: ERP客户端
            rule_engine: 规则引擎
            change_detector: 变更检测器
        """
        self.erp_client = erp_client
        self.rule_engine = rule_engine
        self.change_detector = change_detector
    
    def sync_from_erp(self, incremental: bool = True) -> Dict:
        """
        从ERP拉取客户数据到本地
        
        Args:
            incremental: 是否增量同步
            
        Returns:
            Dict: 同步结果统计
        """
        logger.info("[同步] ========== 开始从ERP拉取客户数据 ==========")
        
        start_time = datetime.now()
        stats = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0
        }
        
        try:
            # 1. 获取最后同步时间
            last_sync_time = None
            if incremental:
                last_sync_time = self._get_last_sync_time('erp_to_local')
                logger.info(f"[同步] 增量同步，最后同步时间: {last_sync_time}")
            
            # 2. 从ERP拉取客户
            page_index = 1
            page_size = 100
            
            while True:
                erp_customers = self.erp_client.get_customers(
                    updated_after=last_sync_time,
                    page_size=page_size,
                    page_index=page_index
                )
                
                if not erp_customers:
                    break
                
                logger.info(f"[同步] 第{page_index}页，获取到 {len(erp_customers)} 个客户")
                
                # 3. 逐个处理客户
                for erp_customer in erp_customers:
                    stats['total'] += 1
                    
                    try:
                        result = self._sync_single_customer_from_erp(erp_customer)
                        stats[result] += 1
                        
                    except Exception as e:
                        logger.error(f"[同步] 处理客户失败: {e}")
                        stats['failed'] += 1
                
                # 检查是否还有下一页
                if len(erp_customers) < page_size:
                    break
                
                page_index += 1
            
            # 4. 更新同步时间戳
            self._update_sync_timestamp('erp_to_local', start_time)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[同步] ========== ERP拉取完成，耗时{duration:.1f}秒 ==========")
            logger.info(f"[同步] 统计: {stats}")
            
            return stats
            
        except Exception as e:
            logger.error(f"[同步] ERP拉取异常: {e}")
            return stats
    
    def _sync_single_customer_from_erp(self, erp_customer: Dict) -> str:
        """
        同步单个客户从ERP到本地
        
        Returns:
            'created'/'updated'/'skipped'
        """
        erp_customer_id = erp_customer.get('ord')
        customer_name = erp_customer.get('name', '未知')
        
        # 查找本地记录
        local_customer = self._find_local_customer(
            erp_id=erp_customer_id,
            phone=erp_customer.get('mobile')
        )
        
        if local_customer:
            # 已存在：检测变更并融合
            changes = self.change_detector.detect_changes(
                erp_data=erp_customer,
                local_data=local_customer
            )
            
            if changes['has_changes']:
                # 获取需要更新的字段
                fields_to_update = self.change_detector.get_fields_to_pull(changes['changes'])
                
                if fields_to_update:
                    self._update_local_customer(local_customer['id'], fields_to_update, 'erp')
                    
                    # 记录变更历史
                    self.change_detector.log_changes(
                        local_customer['id'], 
                        changes['changes'],
                        'erp_to_local'
                    )
                    
                    logger.debug(f"[同步] 更新客户: {customer_name}, 变更字段: {list(fields_to_update.keys())}")
                    return 'updated'
            
            return 'skipped'
        
        else:
            # 不存在：创建新记录
            customer_id = self._create_local_customer_from_erp(erp_customer)
            
            if customer_id:
                logger.info(f"[同步] 创建新客户: {customer_name} (ERP ID: {erp_customer_id})")
                return 'created'
            else:
                return 'failed'
    
    def sync_to_erp(self, batch_size: int = 50) -> Dict:
        """
        推送本地数据到ERP
        
        Args:
            batch_size: 批量大小
            
        Returns:
            Dict: 同步结果统计
        """
        logger.info("[同步] ========== 开始推送数据到ERP ==========")
        
        start_time = datetime.now()
        stats = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0
        }
        
        try:
            # 1. 查找需要同步的客户
            pending_customers = self._get_pending_sync_customers(limit=batch_size)
            
            logger.info(f"[同步] 找到 {len(pending_customers)} 个待同步客户")
            
            # 2. 逐个评估和同步
            for customer in pending_customers:
                stats['total'] += 1
                
                try:
                    # 评估是否应该同步
                    evaluation = self.rule_engine.evaluate(customer)
                    
                    # 记录评估结果
                    self._log_sync_evaluation(customer['id'], evaluation)
                    
                    # 执行同步动作
                    if evaluation['action'] == 'CREATE':
                        success = self._create_in_erp(customer, evaluation)
                        if success:
                            stats['created'] += 1
                        else:
                            stats['failed'] += 1
                    
                    elif evaluation['action'] == 'UPDATE':
                        success = self._update_in_erp(customer, evaluation)
                        if success:
                            stats['updated'] += 1
                        else:
                            stats['failed'] += 1
                    
                    elif evaluation['action'] == 'SKIP':
                        stats['skipped'] += 1
                        self._mark_sync_skipped(customer['id'], evaluation['reason'])
                    
                except Exception as e:
                    logger.error(f"[同步] 处理客户失败: {e}")
                    stats['failed'] += 1
            
            # 3. 更新同步时间戳
            self._update_sync_timestamp('local_to_erp', start_time)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[同步] ========== ERP推送完成，耗时{duration:.1f}秒 ==========")
            logger.info(f"[同步] 统计: {stats}")
            
            return stats
            
        except Exception as e:
            logger.error(f"[同步] ERP推送异常: {e}")
            return stats
    
    def _create_in_erp(self, customer: Dict, evaluation: Dict) -> bool:
        """在ERP中创建新客户"""
        try:
            customer_name = customer.get('company_name') or customer.get('real_name') or customer.get('wechat_nickname')
            
            # 准备ERP客户数据
            erp_data = {
                'intsort': customer.get('erp_customer_type', 1),  # 1=单位 2=个人
                'name': customer_name,
                'person_name': customer.get('real_name') or customer.get('wechat_nickname'),
                'mobile': customer.get('phone'),
                'email': customer.get('email'),
                'weixinAcc': customer.get('wechat_id'),
                'address': customer.get('address'),
                'sort1': customer.get('erp_follow_level', '潜在客户'),
                'ly': self._get_source_enum('微信咨询'),
                'intro': f"来自微信客服中台，添加时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            # 调用ERP API创建客户
            erp_customer_id = self.erp_client.create_customer(erp_data)
            
            if erp_customer_id:
                # 回写ERP ID到本地
                self._update_local_customer(customer['id'], {
                    'erp_customer_id': erp_customer_id,
                    'erp_sync_status': 'synced',
                    'erp_sync_action': 'CREATE',
                    'erp_sync_rule': evaluation['matched_rule'],
                    'erp_sync_confidence': evaluation['confidence'],
                    'erp_last_pushed': datetime.now()
                }, 'system')
                
                # 记录同步日志
                self._log_sync_action(
                    customer_id=customer['id'],
                    direction='local_to_erp',
                    sync_type='push',
                    action='create',
                    result='success',
                    evaluation=evaluation,
                    erp_customer_id=erp_customer_id
                )
                
                logger.info(f"[同步] 创建ERP客户成功: {customer_name} -> ERP ID: {erp_customer_id}")
                return True
            else:
                # 同步失败
                self._mark_sync_failed(customer['id'], 'ERP创建客户失败')
                return False
                
        except Exception as e:
            logger.error(f"[同步] 创建ERP客户异常: {e}")
            self._mark_sync_failed(customer['id'], str(e))
            return False
    
    def _update_in_erp(self, customer: Dict, evaluation: Dict) -> bool:
        """更新ERP客户信息"""
        try:
            erp_customer_id = customer.get('erp_customer_id')
            
            if not erp_customer_id:
                logger.warning(f"[同步] 客户没有ERP ID，无法更新")
                return False
            
            # TODO: 检测哪些字段需要更新
            # 目前简化处理，只更新基本信息
            updates = {}
            
            if customer.get('phone'):
                updates['mobile'] = customer['phone']
            if customer.get('email'):
                updates['email'] = customer['email']
            if customer.get('address'):
                updates['address'] = customer['address']
            
            if not updates:
                logger.debug(f"[同步] 客户没有需要更新的字段")
                return True
            
            # 调用ERP API更新
            success = self.erp_client.update_customer(erp_customer_id, updates)
            
            if success:
                # 更新本地同步状态
                self._update_local_customer(customer['id'], {
                    'erp_sync_status': 'synced',
                    'erp_sync_action': 'UPDATE',
                    'erp_sync_rule': evaluation['matched_rule'],
                    'erp_last_pushed': datetime.now()
                }, 'system')
                
                # 记录同步日志
                self._log_sync_action(
                    customer_id=customer['id'],
                    direction='local_to_erp',
                    sync_type='push',
                    action='update',
                    result='success',
                    evaluation=evaluation,
                    erp_customer_id=erp_customer_id,
                    changed_fields=updates
                )
                
                logger.info(f"[同步] 更新ERP客户成功: ID={erp_customer_id}, 字段={list(updates.keys())}")
                return True
            else:
                self._mark_sync_failed(customer['id'], 'ERP更新客户失败')
                return False
                
        except Exception as e:
            logger.error(f"[同步] 更新ERP客户异常: {e}")
            self._mark_sync_failed(customer['id'], str(e))
            return False
    
    def _find_local_customer(self, erp_id: int = None, phone: str = None) -> Optional[Dict]:
        """查找本地客户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 优先用ERP ID匹配
            if erp_id:
                cursor.execute(
                    'SELECT * FROM customers_unified WHERE erp_customer_id = ?',
                    (erp_id,)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
            
            # 其次用手机号匹配
            if phone:
                cursor.execute(
                    'SELECT * FROM customers_unified WHERE phone = ?',
                    (phone,)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
            
            return None
            
        finally:
            conn.close()
    
    def _create_local_customer_from_erp(self, erp_customer: Dict) -> Optional[int]:
        """从ERP数据创建本地客户"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO customers_unified
                (erp_customer_id, erp_customer_code, company_name, company_name_source,
                 real_name, real_name_source, phone, phone_source, email, email_source,
                 address, address_source, wechat_id, erp_customer_type, 
                 erp_sync_status, erp_last_pulled, erp_updated_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                erp_customer.get('ord'),
                erp_customer.get('khid'),
                erp_customer.get('name'),
                'erp',
                erp_customer.get('person_name'),
                'erp',
                erp_customer.get('mobile'),
                'erp',
                erp_customer.get('email'),
                'erp',
                erp_customer.get('address'),
                'erp',
                erp_customer.get('weixinAcc'),
                erp_customer.get('intsort', 1),
                'synced',
                datetime.now(),
                datetime.now(),
                'erp_pull'
            ))
            
            customer_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return customer_id
            
        except Exception as e:
            logger.error(f"[同步] 创建本地客户失败: {e}")
            return None
    
    def _update_local_customer(self, customer_id: int, updates: Dict, source: str = 'system'):
        """更新本地客户"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 构建UPDATE SQL
            set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
            set_clause += ', updated_at = ?, updated_by = ?'
            
            values = list(updates.values()) + [datetime.now(), source, customer_id]
            
            cursor.execute(f'''
                UPDATE customers_unified
                SET {set_clause}
                WHERE id = ?
            ''', values)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"[同步] 更新本地客户失败: {e}")
    
    def _get_pending_sync_customers(self, limit: int = 50) -> List[Dict]:
        """获取待同步客户列表"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM customers_unified
                WHERE erp_sync_status IN ('pending', 'failed')
                  AND marked_as_invalid = 0
                ORDER BY 
                    CASE 
                        WHEN has_order OR has_contract OR has_payment THEN 1
                        WHEN data_quality_score >= 80 THEN 2
                        WHEN data_quality_score >= 50 THEN 3
                        ELSE 4
                    END,
                    data_quality_score DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def _get_last_sync_time(self, sync_type: str) -> Optional[datetime]:
        """获取最后同步时间"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            config_key = f'last_{sync_type}_time'
            cursor.execute(
                'SELECT config_value FROM erp_sync_config WHERE config_key = ?',
                (config_key,)
            )
            row = cursor.fetchone()
            
            if row and row[0]:
                return datetime.fromisoformat(row[0])
            
            return None
            
        finally:
            conn.close()
    
    def _update_sync_timestamp(self, sync_type: str, timestamp: datetime):
        """更新同步时间戳"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            config_key = f'last_{sync_type}_time'
            cursor.execute('''
                UPDATE erp_sync_config
                SET config_value = ?, updated_at = ?
                WHERE config_key = ?
            ''', (timestamp.isoformat(), datetime.now(), config_key))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def _log_sync_evaluation(self, customer_id: int, evaluation: Dict):
        """记录同步评估结果"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE customers_unified
                SET erp_sync_action = ?,
                    erp_sync_rule = ?,
                    erp_sync_confidence = ?
                WHERE id = ?
            ''', (
                evaluation['action'],
                evaluation['matched_rule'],
                evaluation['confidence'],
                customer_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"[同步] 记录评估结果失败: {e}")
    
    def _log_sync_action(self, customer_id: int, direction: str, sync_type: str,
                        action: str, result: str, evaluation: Dict,
                        erp_customer_id: int = None, changed_fields: Dict = None):
        """记录同步动作"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO erp_sync_logs
                (customer_id, sync_direction, sync_type, sync_action, sync_result,
                 matched_rule, rule_confidence, rule_reason, erp_customer_id, 
                 changed_fields, field_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_id,
                direction,
                sync_type,
                action,
                result,
                evaluation['matched_rule'],
                evaluation['confidence'],
                evaluation['reason'],
                erp_customer_id,
                json.dumps(changed_fields, ensure_ascii=False) if changed_fields else None,
                len(changed_fields) if changed_fields else 0
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"[同步] 记录同步日志失败: {e}")
    
    def _mark_sync_skipped(self, customer_id: int, reason: str):
        """标记为跳过同步"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE customers_unified
                SET erp_sync_status = 'skipped',
                    erp_sync_error = ?
                WHERE id = ?
            ''', (reason, customer_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"[同步] 标记跳过失败: {e}")
    
    def _mark_sync_failed(self, customer_id: int, error: str):
        """标记同步失败"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE customers_unified
                SET erp_sync_status = 'failed',
                    erp_sync_error = ?
                WHERE id = ?
            ''', (error, customer_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"[同步] 标记失败失败: {e}")
    
    def _get_source_enum(self, source_name: str) -> int:
        """获取客户来源枚举值"""
        # TODO: 从ERP获取枚举值
        # 目前返回固定值
        source_mapping = {
            '微信咨询': 484,  # 假设的枚举值
            '网站注册': 171,
            '朋友介绍': 172,
            '陌生开发': 173,
            '广告宣传': 174,
        }
        
        return source_mapping.get(source_name, 484)

