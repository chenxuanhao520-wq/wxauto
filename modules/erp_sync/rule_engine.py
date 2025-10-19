"""
同步规则引擎
基于规则自动判定客户是否应该同步到ERP
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from modules.storage.db import Database

logger = logging.getLogger(__name__)


class SyncRule:
    """同步规则基类"""
    
    def __init__(self, rule_name: str, rule_type: str, priority: int, 
                 conditions: Dict, action: str, description: str = ''):
        self.rule_name = rule_name
        self.rule_type = rule_type
        self.priority = priority
        self.conditions = conditions
        self.action = action
        self.description = description
    
    def match(self, customer: Dict) -> Dict:
        """
        检查客户是否匹配此规则
        
        Args:
            customer: 客户数据字典
            
        Returns:
            {
                'matched': bool,
                'action': str,
                'confidence': float,
                'reason': str
            }
        """
        raise NotImplementedError


class MandatorySyncRule(SyncRule):
    """强制同步规则 - 最高优先级"""
    
    def match(self, customer: Dict) -> Dict:
        """检查强制同步条件"""
        
        # 检查是否有订单
        if customer.get('has_order'):
            return {
                'matched': True,
                'action': 'CREATE' if not customer.get('erp_customer_id') else 'UPDATE',
                'confidence': 1.0,
                'reason': '客户已下单，必须同步到ERP'
            }
        
        # 检查是否有合同
        if customer.get('has_contract'):
            return {
                'matched': True,
                'action': 'CREATE' if not customer.get('erp_customer_id') else 'UPDATE',
                'confidence': 1.0,
                'reason': '客户已签合同，必须同步到ERP'
            }
        
        # 检查是否已付款
        if customer.get('has_payment'):
            return {
                'matched': True,
                'action': 'CREATE' if not customer.get('erp_customer_id') else 'UPDATE',
                'confidence': 1.0,
                'reason': '客户已付款，必须同步到ERP'
            }
        
        # 检查是否标记为重要客户
        if customer.get('marked_as_important'):
            return {
                'matched': True,
                'action': 'CREATE' if not customer.get('erp_customer_id') else 'UPDATE',
                'confidence': 1.0,
                'reason': '销售标记为重要客户'
            }
        
        return {'matched': False}


class HighQualitySyncRule(SyncRule):
    """高质量自动同步规则"""
    
    def match(self, customer: Dict) -> Dict:
        """检查高质量条件"""
        
        # 计算数据质量分数
        quality_score = self._calculate_quality_score(customer)
        
        # 高质量：≥80分
        if quality_score >= 80:
            return {
                'matched': True,
                'action': 'CREATE' if not customer.get('erp_customer_id') else 'UPDATE',
                'confidence': quality_score / 100,
                'reason': f'高质量客户（{quality_score:.0f}分），自动同步'
            }
        
        return {'matched': False}
    
    def _calculate_quality_score(self, customer: Dict) -> float:
        """计算数据质量分数 0-100"""
        score = 0.0
        
        # 1. 手机号（30分）
        if customer.get('phone'):
            if customer.get('phone_verified'):
                score += 30
            else:
                score += 15
        
        # 2. 公司名称（30分）
        company_name = customer.get('company_name', '')
        if company_name and len(company_name) >= 4:
            # 排除明显的个人名称
            if not any(kw in company_name for kw in ['先生', '女士', '老板', '小姐']):
                if customer.get('company_name_verified'):
                    score += 30
                else:
                    score += 20
        
        # 3. 营业执照（20分）
        if customer.get('business_license_verified'):
            score += 20
        elif customer.get('business_license_path'):
            score += 10
        
        # 4. 商业意向（20分）
        intent_score = customer.get('intent_score', 0)
        if intent_score >= 80:
            score += 20
        elif intent_score >= 60:
            score += 15
        elif intent_score >= 40:
            score += 10
        
        return score


class MediumQualitySyncRule(SyncRule):
    """中等质量条件同步规则"""
    
    def match(self, customer: Dict) -> Dict:
        """检查中等质量条件"""
        
        # 组合1: 手机号 + 明确询价
        if customer.get('phone') and customer.get('has_quote_request'):
            return {
                'matched': True,
                'action': 'CREATE' if not customer.get('erp_customer_id') else 'UPDATE',
                'confidence': 0.75,
                'reason': '有手机号且明确询价'
            }
        
        # 组合2: 公司名 + 营业执照
        if customer.get('company_name') and customer.get('business_license_path'):
            return {
                'matched': True,
                'action': 'CREATE' if not customer.get('erp_customer_id') else 'UPDATE',
                'confidence': 0.8,
                'reason': '公司信息完整（有公司名和营业执照）'
            }
        
        # 组合3: 持续深度沟通
        if (customer.get('conversation_days', 0) >= 7 and 
            customer.get('message_count', 0) >= 50):
            return {
                'matched': True,
                'action': 'CREATE' if not customer.get('erp_customer_id') else 'UPDATE',
                'confidence': 0.7,
                'reason': f"持续深度沟通（{customer.get('conversation_days')}天，{customer.get('message_count')}条消息）"
            }
        
        return {'matched': False}


class LowQualitySkipRule(SyncRule):
    """低质量跳过规则"""
    
    def match(self, customer: Dict) -> Dict:
        """检查是否应该跳过"""
        
        # 无基本信息
        if (not customer.get('phone') and 
            not customer.get('company_name') and 
            not customer.get('real_name')):
            return {
                'matched': True,
                'action': 'SKIP',
                'confidence': 0.0,
                'reason': '信息不足（无手机号、公司名、真实姓名）'
            }
        
        # 意向过低
        if customer.get('intent_score', 0) < 30:
            return {
                'matched': True,
                'action': 'SKIP',
                'confidence': 0.0,
                'reason': f"商业意向过低（{customer.get('intent_score', 0):.0f}分）"
            }
        
        # 互动太少
        if customer.get('message_count', 0) < 5:
            return {
                'matched': True,
                'action': 'SKIP',
                'confidence': 0.0,
                'reason': f"互动次数不足（{customer.get('message_count', 0)}条消息）"
            }
        
        # 标记为无效
        if customer.get('marked_as_invalid'):
            return {
                'matched': True,
                'action': 'SKIP',
                'confidence': 0.0,
                'reason': '已标记为无效客户'
            }
        
        return {'matched': False}


class SyncRuleEngine:
    """同步规则引擎"""
    
    def __init__(self):
        self.rules: List[SyncRule] = []
        self._load_rules_from_db()
    
    def _load_rules_from_db(self):
        """从数据库加载规则"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT rule_name, rule_type, rule_priority, rule_conditions, 
                       rule_action, description
                FROM erp_sync_rules
                WHERE is_active = 1
                ORDER BY rule_priority DESC
            ''')
            
            db_rules = cursor.fetchall()
            conn.close()
            
            logger.info(f"[规则引擎] 从数据库加载了 {len(db_rules)} 条规则")
            
            # 创建规则实例
            self.rules = []
            
            for rule_data in db_rules:
                rule_name = rule_data[0]
                rule_type = rule_data[1]
                priority = rule_data[2]
                conditions = json.loads(rule_data[3]) if rule_data[3] else {}
                action = rule_data[4]
                description = rule_data[5]
                
                # 根据类型创建对应的规则实例
                if rule_type == 'mandatory':
                    rule = MandatorySyncRule(rule_name, rule_type, priority, 
                                            conditions, action, description)
                elif rule_type == 'high_quality':
                    rule = HighQualitySyncRule(rule_name, rule_type, priority,
                                               conditions, action, description)
                elif rule_type == 'medium_quality':
                    rule = MediumQualitySyncRule(rule_name, rule_type, priority,
                                                 conditions, action, description)
                elif rule_type == 'low_quality':
                    rule = LowQualitySkipRule(rule_name, rule_type, priority,
                                             conditions, action, description)
                else:
                    continue
                
                self.rules.append(rule)
            
        except Exception as e:
            logger.error(f"[规则引擎] 加载规则失败: {e}")
            # 使用默认规则
            self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认规则（如果数据库加载失败）"""
        self.rules = [
            MandatorySyncRule('mandatory', 'mandatory', 100, {}, 'CREATE', '强制同步'),
            HighQualitySyncRule('high_quality', 'high_quality', 80, {}, 'CREATE', '高质量同步'),
            MediumQualitySyncRule('medium_quality', 'medium_quality', 50, {}, 'CREATE', '中等质量同步'),
            LowQualitySkipRule('low_quality', 'low_quality', 0, {}, 'SKIP', '低质量跳过'),
        ]
        logger.info("[规则引擎] 使用默认规则")
    
    def evaluate(self, customer: Dict) -> Dict:
        """
        评估客户是否应该同步到ERP
        
        Args:
            customer: 客户数据字典
            
        Returns:
            {
                'action': 'CREATE'/'UPDATE'/'SKIP',
                'confidence': float,
                'reason': str,
                'matched_rule': str
            }
        """
        # 按优先级顺序检查规则
        for rule in self.rules:
            result = rule.match(customer)
            
            if result.get('matched'):
                # 更新规则匹配统计
                self._update_rule_stats(rule.rule_name)
                
                return {
                    'action': result['action'],
                    'confidence': result['confidence'],
                    'reason': result['reason'],
                    'matched_rule': rule.rule_name
                }
        
        # 默认：跳过
        return {
            'action': 'SKIP',
            'confidence': 0.0,
            'reason': '未匹配任何规则',
            'matched_rule': 'default'
        }
    
    def _update_rule_stats(self, rule_name: str):
        """更新规则匹配统计"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE erp_sync_rules
                SET match_count = match_count + 1
                WHERE rule_name = ?
            ''', (rule_name,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"[规则引擎] 更新规则统计失败: {e}")
    
    def add_rule(self, rule: SyncRule):
        """添加自定义规则"""
        self.rules.append(rule)
        # 按优先级重新排序
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def reload_rules(self):
        """重新加载规则（用于动态更新）"""
        self._load_rules_from_db()

