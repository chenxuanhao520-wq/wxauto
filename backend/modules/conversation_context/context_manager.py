#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能对话上下文管理器
实现高效的上下文管理，降低token消耗，提高对话质量
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional, Set
from collections import deque
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


class DialogueType(Enum):
    """对话类型枚举"""
    SMALL_TALK = "闲聊类"
    CONSULTATION = "咨询类"
    BUSINESS = "业务类"
    UNKNOWN = "未知类"


# 不同对话类型的上下文窗口大小
CONTEXT_WINDOW_SIZE = {
    DialogueType.SMALL_TALK: 1,      # 闲聊只需最近1轮
    DialogueType.CONSULTATION: 5,    # 咨询保留5轮
    DialogueType.BUSINESS: 3,        # 业务保留3轮
    DialogueType.UNKNOWN: 3,         # 未知保留3轮
}


class IntentClassifier:
    """对话意图快速分类器"""
    
    def __init__(self):
        # 闲聊关键词
        self.small_talk_keywords = [
            '你好', '您好', '早上好', '晚上好', '谢谢', '感谢',
            '好的', '嗯', '哦', '是的', '明白了', '收到',
            '天气', '心情', '再见', '拜拜', '晚安', '早安'
        ]
        
        # 咨询关键词
        self.consultation_keywords = [
            '怎么', '如何', '什么', '哪个', '哪种', '为什么', '怎样',
            '支持', '功能', '特点', '区别', '对比', '优势',
            '使用方法', '操作步骤', '说明', '介绍', '教程',
            '政策', '规定', '要求', '条件', '流程', '方法'
        ]
        
        # 业务关键词
        self.business_keywords = [
            '订单', '库存', '价格', '报价', '发货', '物流', '快递',
            '账单', '付款', '退款', '发票', '合同', '签约',
            '查询', '修改', '取消', '确认', '下单', '购买'
        ]
        
        # 数字/日期模式
        self.number_pattern = re.compile(r'\d{3,}')  # 3位以上数字
        self.date_pattern = re.compile(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}')
        self.money_pattern = re.compile(r'[¥$￥]\s*\d+(\.\d{2})?|(\d+(\.\d{2})?)\s*元')
    
    def classify(self, message: str, context: List[Dict] = None) -> Tuple[DialogueType, float]:
        """
        快速分类对话类型
        
        Args:
            message: 用户消息
            context: 最近对话历史
        
        Returns:
            (对话类型, 置信度)
        """
        message_lower = message.lower()
        
        # 1. 超短消息判断
        if len(message) <= 5:
            if any(kw in message for kw in self.small_talk_keywords):
                return DialogueType.SMALL_TALK, 0.9
        
        # 2. 关键词匹配评分
        small_talk_score = sum(1 for kw in self.small_talk_keywords if kw in message)
        consultation_score = sum(1 for kw in self.consultation_keywords if kw in message)
        business_score = sum(1 for kw in self.business_keywords if kw in message)
        
        # 3. 特征加权
        if self.number_pattern.search(message):
            business_score += 1.5
        if self.date_pattern.search(message):
            business_score += 1.5
        if self.money_pattern.search(message):
            business_score += 2
        
        # 咨询类：包含疑问词
        if any(q in message for q in ['？', '?', '吗', '呢', '么']):
            consultation_score += 1
        
        # 4. 上下文延续性
        if context and len(context) > 0:
            last_type = context[-1].get('type')
            if last_type == DialogueType.BUSINESS.value:
                business_score += 1.5
            elif last_type == DialogueType.CONSULTATION.value:
                consultation_score += 1.0
        
        # 5. 决策
        scores = {
            DialogueType.SMALL_TALK: small_talk_score,
            DialogueType.CONSULTATION: consultation_score,
            DialogueType.BUSINESS: business_score
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return DialogueType.UNKNOWN, 0.0
        
        dialogue_type = max(scores, key=scores.get)
        confidence = scores[dialogue_type] / (sum(scores.values()) + 1)
        
        return dialogue_type, confidence
    
    def classify_detailed(self, message: str, context: List[Dict] = None) -> Dict:
        """
        详细分类（包含子类型和建议动作）
        
        Returns:
            {
                'type': DialogueType,
                'subtype': str,
                'confidence': float,
                'suggested_action': str
            }
        """
        dialogue_type, confidence = self.classify(message, context)
        
        result = {
            'type': dialogue_type,
            'confidence': confidence,
            'subtype': None,
            'suggested_action': None
        }
        
        # 细分子类型和建议动作
        if dialogue_type == DialogueType.CONSULTATION:
            if any(kw in message for kw in ['产品', '功能', '特点', '支持', '性能']):
                result['subtype'] = '产品咨询'
                result['suggested_action'] = 'query_knowledge_base'
            elif any(kw in message for kw in ['安装', '使用', '操作', '步骤', '教程']):
                result['subtype'] = '使用咨询'
                result['suggested_action'] = 'query_knowledge_base'
            elif any(kw in message for kw in ['政策', '价格', '费用', '收费', '多少钱']):
                result['subtype'] = '价格咨询'
                result['suggested_action'] = 'query_knowledge_base'
            else:
                result['subtype'] = '一般咨询'
                result['suggested_action'] = 'query_knowledge_base'
        
        elif dialogue_type == DialogueType.BUSINESS:
            if any(kw in message for kw in ['订单', '发货', '物流', '快递']):
                result['subtype'] = '订单查询'
                result['suggested_action'] = 'query_erp_order'
            elif any(kw in message for kw in ['库存', '现货', '有货', '缺货']):
                result['subtype'] = '库存查询'
                result['suggested_action'] = 'query_erp_inventory'
            elif any(kw in message for kw in ['报价', '价格', '多少钱', '费用']):
                result['subtype'] = '价格查询'
                result['suggested_action'] = 'query_erp_price'
            elif any(kw in message for kw in ['发票', '账单', '付款', '退款']):
                result['subtype'] = '财务查询'
                result['suggested_action'] = 'query_erp_finance'
            else:
                result['subtype'] = '一般业务'
                result['suggested_action'] = 'query_erp_general'
        
        elif dialogue_type == DialogueType.SMALL_TALK:
            result['suggested_action'] = 'simple_response'
        
        return result


class TopicChangeDetector:
    """主题切换检测器"""
    
    def __init__(self):
        self.topic_change_signals = [
            '对了', '另外', '还有', '换个问题', '顺便问',
            '不说这个了', '说说', '问一下', '再问',
            '话说', '对啦', '还想问'
        ]
    
    def detect_topic_change(self, current_msg: str, 
                           previous_messages: List[Dict]) -> bool:
        """
        检测是否发生主题切换
        
        Returns:
            True表示主题已切换
        """
        if not previous_messages:
            return False
        
        # 1. 显式主题切换信号
        if any(signal in current_msg for signal in self.topic_change_signals):
            logger.info(f"检测到显式主题切换信号: {current_msg[:20]}")
            return True
        
        # 2. 提取关键词对比
        current_keywords = self._extract_keywords(current_msg)
        
        # 最近3条用户消息的关键词
        recent_keywords = set()
        count = 0
        for msg in reversed(previous_messages):
            if msg.get('role') == 'user':
                recent_keywords.update(self._extract_keywords(msg['content']))
                count += 1
                if count >= 3:
                    break
        
        # 关键词重合度
        if current_keywords and recent_keywords:
            overlap = len(current_keywords & recent_keywords)
            overlap_ratio = overlap / len(current_keywords)
            
            if overlap_ratio < 0.25:
                logger.info(f"关键词重合度低({overlap_ratio:.2f})，判定为主题切换")
                return True
        
        # 3. 对话类型突变
        if len(previous_messages) >= 2:
            # 获取最近2条相同类型
            user_messages = [m for m in previous_messages if m.get('role') == 'user']
            if len(user_messages) >= 2:
                prev_type = user_messages[-1].get('type')
                prev_prev_type = user_messages[-2].get('type')
                
                if prev_type and prev_type == prev_prev_type:
                    classifier = IntentClassifier()
                    current_type, _ = classifier.classify(current_msg, previous_messages)
                    
                    if current_type.value != prev_type:
                        logger.info(f"对话类型突变: {prev_type} -> {current_type.value}")
                        return True
        
        return False
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """提取关键词（简化版）"""
        # 移除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 简单分词
        words = set(text.split())
        
        # 停用词
        stopwords = {
            '的', '了', '吗', '呢', '啊', '是', '在', '有', '个',
            '我', '你', '他', '她', '它', '我们', '你们', '他们',
            '这', '那', '这个', '那个', '什么', '怎么', '为什么',
            '一', '一个', '两', '三', '能', '会', '要', '想'
        }
        
        keywords = {w for w in words if w not in stopwords and len(w) >= 2}
        
        return keywords


class ContextCompressor:
    """上下文压缩器"""
    
    def __init__(self):
        self.entity_patterns = {
            'phone': re.compile(r'1[3-9]\d{9}'),
            'order_no': re.compile(r'[A-Z]{2}\d{8,}|\d{10,}'),
            'date': re.compile(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}'),
            'money': re.compile(r'[¥$￥]?\s*\d+(\.\d{2})?\s*元?'),
            'product': re.compile(r'(充电桩|电表|设备|产品|型号)\s*[A-Z0-9-]+'),
        }
    
    def extract_key_entities(self, messages: List[Dict]) -> Dict[str, List[str]]:
        """提取关键实体"""
        entities = {key: set() for key in self.entity_patterns.keys()}
        
        for msg in messages:
            content = msg.get('content', '')
            for entity_type, pattern in self.entity_patterns.items():
                matches = pattern.findall(content)
                if matches:
                    # 处理可能的元组结果
                    if isinstance(matches[0], tuple):
                        matches = [m[0] if m[0] else m for m in matches]
                    entities[entity_type].update(matches)
        
        return {k: list(v) for k, v in entities.items() if v}
    
    def compress_context(self, messages: List[Dict], max_length: int = 500) -> str:
        """
        压缩上下文为简短摘要
        
        Args:
            messages: 消息列表
            max_length: 最大字符数
        
        Returns:
            压缩后的上下文描述
        """
        if not messages:
            return ""
        
        # 提取关键实体
        entities = self.extract_key_entities(messages)
        
        # 提取问题
        questions = []
        for msg in messages:
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                if any(q in content for q in ['？', '?', '吗', '呢']):
                    questions.append(content[:50])
        
        # 构建摘要
        summary_parts = []
        
        # 对话轮数
        user_count = sum(1 for m in messages if m.get('role') == 'user')
        summary_parts.append(f"[共{user_count}轮对话]")
        
        # 关键实体
        if entities:
            entity_str = []
            if entities.get('phone'):
                entity_str.append(f"客户:{entities['phone'][0]}")
            if entities.get('order_no'):
                entity_str.append(f"订单:{entities['order_no'][0]}")
            if entities.get('product'):
                entity_str.append(f"产品:{entities['product'][0]}")
            
            if entity_str:
                summary_parts.append(" | ".join(entity_str))
        
        # 主要问题
        if questions:
            summary_parts.append(f"主要问题: {' / '.join(questions[:2])}")
        
        # 最后一轮对话
        if messages:
            last_msg = messages[-1]
            summary_parts.append(
                f"\n最近({last_msg.get('role', 'unknown')}): "
                f"{last_msg.get('content', '')[:100]}"
            )
        
        summary = "\n".join(summary_parts)
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
    
    def get_structured_context(self, messages: List[Dict]) -> Dict:
        """获取结构化上下文"""
        entities = self.extract_key_entities(messages)
        
        questions = [
            msg.get('content', '')
            for msg in messages
            if msg.get('role') == 'user' and any(q in msg.get('content', '') for q in ['？', '?'])
        ]
        
        last_topic = messages[-1].get('subtype', '未知') if messages else '未知'
        
        return {
            'entities': entities,
            'questions': questions[-5:],
            'last_topic': last_topic,
            'summary': self.compress_context(messages),
            'message_count': len(messages)
        }


class ContextManager:
    """智能上下文管理器"""
    
    def __init__(self, max_age_minutes: int = 30, hard_limit: int = 20):
        """
        初始化
        
        Args:
            max_age_minutes: 上下文最大保留时间（分钟）
            hard_limit: 单个对话的硬上限轮数
        """
        self.conversations = {}  # {contact_id: deque([messages])}
        self.max_age = timedelta(minutes=max_age_minutes)
        self.hard_limit = hard_limit
        
        self.classifier = IntentClassifier()
        self.topic_detector = TopicChangeDetector()
        self.compressor = ContextCompressor()
    
    def add_message(self, contact_id: str, message: str, 
                   role: str = 'user', metadata: Dict = None):
        """添加消息到上下文"""
        if contact_id not in self.conversations:
            self.conversations[contact_id] = deque(maxlen=self.hard_limit)
        
        # 分类消息
        context_list = list(self.conversations[contact_id])
        classification = self.classifier.classify_detailed(message, context_list)
        
        msg_obj = {
            'role': role,
            'content': message,
            'timestamp': datetime.now(),
            'type': classification['type'].value,
            'subtype': classification['subtype'],
            'confidence': classification.get('confidence', 0.0),
            'metadata': metadata or {}
        }
        
        self.conversations[contact_id].append(msg_obj)
        
        logger.debug(
            f"添加消息: contact={contact_id}, type={classification['type'].value}, "
            f"subtype={classification['subtype']}"
        )
    
    def get_relevant_context(self, contact_id: str, 
                           current_type: DialogueType = None,
                           max_tokens: int = 2000) -> List[Dict]:
        """
        获取相关上下文（智能筛选）
        
        Args:
            contact_id: 联系人ID
            current_type: 当前对话类型
            max_tokens: 最大token数
        
        Returns:
            精简后的上下文列表
        """
        if contact_id not in self.conversations:
            return []
        
        all_messages = list(self.conversations[contact_id])
        
        # 1. 时间过滤
        now = datetime.now()
        valid_messages = [
            msg for msg in all_messages
            if now - msg['timestamp'] < self.max_age
        ]
        
        if not valid_messages:
            return []
        
        # 2. 确定窗口大小
        if current_type:
            window_size = CONTEXT_WINDOW_SIZE.get(current_type, 5)
        else:
            last_type_str = valid_messages[-1]['type']
            try:
                last_type = DialogueType(last_type_str)
                window_size = CONTEXT_WINDOW_SIZE.get(last_type, 5)
            except ValueError:
                window_size = 5
        
        # 3. 滑动窗口
        windowed_messages = valid_messages[-window_size:]
        
        # 4. Token控制
        estimated_tokens = sum(len(msg['content']) // 2 for msg in windowed_messages)
        
        while estimated_tokens > max_tokens and len(windowed_messages) > 1:
            windowed_messages.pop(0)
            estimated_tokens = sum(len(msg['content']) // 2 for msg in windowed_messages)
        
        logger.debug(
            f"上下文筛选: {len(all_messages)}条 -> {len(windowed_messages)}条, "
            f"约{estimated_tokens} tokens"
        )
        
        return windowed_messages
    
    def check_topic_change(self, contact_id: str, message: str) -> bool:
        """检查主题是否切换"""
        if contact_id not in self.conversations:
            return False
        
        context = list(self.conversations[contact_id])
        return self.topic_detector.detect_topic_change(message, context)
    
    def reset_context(self, contact_id: str, keep_summary: bool = True):
        """
        重置上下文
        
        Args:
            contact_id: 联系人ID
            keep_summary: 是否保留摘要
        """
        if contact_id not in self.conversations:
            return
        
        if keep_summary:
            old_context = list(self.conversations[contact_id])
            summary = self.compressor.compress_context(old_context)
            
            # 重置并添加摘要
            self.conversations[contact_id] = deque(maxlen=self.hard_limit)
            self.conversations[contact_id].append({
                'role': 'system',
                'content': f"[历史对话摘要] {summary}",
                'timestamp': datetime.now(),
                'type': 'summary',
                'subtype': None,
                'metadata': {}
            })
            logger.info(f"重置上下文(保留摘要): {contact_id}")
        else:
            self.conversations[contact_id] = deque(maxlen=self.hard_limit)
            logger.info(f"重置上下文(完全清空): {contact_id}")
    
    def get_context_summary(self, contact_id: str) -> str:
        """获取上下文摘要"""
        if contact_id not in self.conversations:
            return "这是新对话的开始。"
        
        messages = list(self.conversations[contact_id])
        return self.compressor.compress_context(messages)
    
    def get_structured_context(self, contact_id: str) -> Dict:
        """获取结构化上下文"""
        if contact_id not in self.conversations:
            return {
                'entities': {},
                'questions': [],
                'last_topic': '未知',
                'summary': '新对话',
                'message_count': 0
            }
        
        messages = list(self.conversations[contact_id])
        return self.compressor.get_structured_context(messages)
    
    def cleanup_expired(self):
        """清理过期对话"""
        now = datetime.now()
        expired_contacts = []
        
        for contact_id, messages in self.conversations.items():
            if messages:
                last_msg_time = messages[-1]['timestamp']
                if now - last_msg_time > self.max_age:
                    expired_contacts.append(contact_id)
        
        for contact_id in expired_contacts:
            del self.conversations[contact_id]
            logger.info(f"清理过期对话: {contact_id}")
        
        return len(expired_contacts)


# 示例使用
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    # 初始化
    context_mgr = ContextManager(max_age_minutes=30)
    
    contact_id = "wx_user_123"
    
    # 模拟对话
    context_mgr.add_message(contact_id, "你好", role='user')
    context_mgr.add_message(contact_id, "您好！有什么可以帮您的吗？", role='assistant')
    
    context_mgr.add_message(contact_id, "你们的充电桩支持多少功率？", role='user')
    context_mgr.add_message(contact_id, "我们支持7kW到120kW不等", role='assistant')
    
    context_mgr.add_message(contact_id, "安装需要什么条件？", role='user')
    
    # 获取上下文
    context = context_mgr.get_relevant_context(
        contact_id,
        current_type=DialogueType.CONSULTATION
    )
    
    print(f"\n上下文轮数: {len(context)}")
    print(f"\n摘要:\n{context_mgr.get_context_summary(contact_id)}")
    
    # 结构化上下文
    structured = context_mgr.get_structured_context(contact_id)
    print(f"\n结构化上下文:")
    print(f"  - 主题: {structured['last_topic']}")
    print(f"  - 问题数: {len(structured['questions'])}")
    print(f"  - 实体: {structured['entities']}")
    
    # 测试主题切换
    print("\n测试主题切换:")
    changed = context_mgr.check_topic_change(contact_id, "对了，我想查一下订单状态")
    print(f"  - 主题切换: {changed}")

