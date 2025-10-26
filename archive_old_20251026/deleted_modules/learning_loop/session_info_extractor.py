#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话信息提取器
从对话中提取结构化信息、实体、知识点等
"""

import re
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SessionEndTrigger(Enum):
    """会话结束触发原因"""
    TIMEOUT_EXPIRED = "超时过期"
    USER_EXPLICIT = "用户明确结束"
    BUSINESS_COMPLETE = "业务完成"
    TOPIC_CHANGED = "主题切换"
    HANDOFF_HUMAN = "转人工"
    ERROR_ABORT = "异常中断"


@dataclass
class ExtractedInfo:
    """提取的会话信息"""
    # 基础信息
    session_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    message_count: int
    turn_count: int
    dialogue_type: str
    end_trigger: SessionEndTrigger
    
    # 实体信息
    entities: Dict[str, List[str]] = field(default_factory=dict)
    
    # 对话分析
    main_topic: str = ""
    topic_changes: int = 0
    sentiment: str = "neutral"
    avg_confidence: float = 0.0
    
    # 知识点
    knowledge_points: List[Dict] = field(default_factory=list)
    
    # 质量评分
    quality_score: int = 0
    quality_grade: str = "C"
    
    # 学习数据
    should_learn: bool = False
    training_examples: List[Dict] = field(default_factory=list)


class SessionInfoExtractor:
    """会话信息提取器"""
    
    def __init__(self):
        """初始化提取器"""
        # 实体识别模式
        self.entity_patterns = {
            'phone': re.compile(r'1[3-9]\d{9}'),
            'order_no': re.compile(r'[A-Z]{2}\d{8,}|\d{10,}'),
            'date': re.compile(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}'),
            'money': re.compile(r'[¥$￥]?\s*\d+(\.\d{2})?\s*元?'),
            'product': re.compile(r'(充电桩|电表|设备|产品|型号)\s*[A-Z0-9-]+'),
            'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
        }
        
        # 用户明确结束信号
        self.end_signals = [
            '谢谢', '拜拜', '再见', '解决了', '好了', 
            '明白了谢谢', '知道了', '不用了', '可以了'
        ]
        
        # 业务完成信号
        self.business_complete_signals = [
            '已下单', '订单确认', '支付成功', '已解决',
            '搞定了', '成功了', '可以了', '完成了'
        ]
        
        # 情感词典
        self.positive_words = ['好', '谢谢', '满意', '不错', '可以', '解决了', '棒', '赞']
        self.negative_words = ['不行', '不好', '垃圾', '差', '烂', '退货', '投诉']
    
    def extract_from_session(self, 
                            messages: List[Dict],
                            session_info: Dict,
                            end_trigger: SessionEndTrigger) -> ExtractedInfo:
        """
        从会话中提取完整信息
        
        Args:
            messages: 消息列表
            session_info: 会话信息
            end_trigger: 结束触发原因
        
        Returns:
            提取的结构化信息
        """
        # 1. 基础信息
        basic_info = self._extract_basic_info(messages, session_info, end_trigger)
        
        # 2. 实体提取
        entities = self._extract_entities(messages)
        
        # 3. 对话分析
        dialogue_analysis = self._analyze_dialogue(messages)
        
        # 4. 知识点提取
        knowledge_points = self._extract_knowledge_points(messages)
        
        # 5. 质量评分
        quality = self._calculate_quality(messages, dialogue_analysis, end_trigger)
        
        # 6. 学习数据生成
        learning_data = self._generate_learning_data(knowledge_points, quality['total_score'])
        
        # 组装完整信息
        extracted = ExtractedInfo(
            session_id=basic_info['session_id'],
            start_time=basic_info['start_time'],
            end_time=basic_info['end_time'],
            duration_seconds=basic_info['duration_seconds'],
            message_count=basic_info['message_count'],
            turn_count=basic_info['turn_count'],
            dialogue_type=basic_info['dialogue_type'],
            end_trigger=end_trigger,
            entities=entities,
            main_topic=dialogue_analysis['main_topic'],
            topic_changes=dialogue_analysis['topic_changes'],
            sentiment=dialogue_analysis['sentiment'],
            avg_confidence=dialogue_analysis['avg_confidence'],
            knowledge_points=knowledge_points,
            quality_score=quality['total_score'],
            quality_grade=quality['grade'],
            should_learn=learning_data['should_learn'],
            training_examples=learning_data['training_examples']
        )
        
        logger.info(
            f"[{extracted.session_id}] 信息提取完成: "
            f"知识点={len(knowledge_points)}, "
            f"质量={quality['total_score']}分({quality['grade']})"
        )
        
        return extracted
    
    def _extract_basic_info(self, messages: List[Dict], 
                           session_info: Dict,
                           end_trigger: SessionEndTrigger) -> Dict:
        """提取基础信息"""
        user_messages = [m for m in messages if m.get('role') == 'user']
        
        return {
            'session_id': session_info.get('contact_id', ''),
            'start_time': session_info.get('created_at', datetime.now()),
            'end_time': datetime.now(),
            'duration_seconds': (datetime.now() - session_info.get('created_at', datetime.now())).total_seconds(),
            'message_count': len(messages),
            'turn_count': len(user_messages),
            'dialogue_type': session_info.get('dialogue_type', '未知类')
        }
    
    def _extract_entities(self, messages: List[Dict]) -> Dict[str, List[str]]:
        """提取实体"""
        entities = {key: set() for key in self.entity_patterns.keys()}
        
        for msg in messages:
            content = msg.get('content', '')
            
            for entity_type, pattern in self.entity_patterns.items():
                matches = pattern.findall(content)
                if matches:
                    # 处理可能的元组结果
                    if matches and isinstance(matches[0], tuple):
                        matches = [m[0] if m[0] else m for m in matches]
                    entities[entity_type].update(str(m) for m in matches)
        
        # 转为列表并去除空值
        return {k: list(v) for k, v in entities.items() if v}
    
    def _analyze_dialogue(self, messages: List[Dict]) -> Dict:
        """分析对话特征"""
        user_messages = [m for m in messages if m.get('role') == 'user']
        ai_messages = [m for m in messages if m.get('role') == 'assistant']
        
        # 提取主题
        all_subtypes = [m.get('subtype') for m in messages if m.get('subtype')]
        main_topic = max(set(all_subtypes), key=all_subtypes.count) if all_subtypes else '未知'
        
        # 情感分析
        sentiment = self._analyze_sentiment(user_messages)
        
        # 平均置信度
        confidences = [m.get('confidence', 0) for m in ai_messages if m.get('confidence')]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            'main_topic': main_topic,
            'topic_changes': len(set(all_subtypes)),
            'sentiment': sentiment,
            'avg_confidence': avg_confidence,
            'user_avg_length': sum(len(m.get('content', '')) for m in user_messages) / len(user_messages) if user_messages else 0,
            'ai_avg_length': sum(len(m.get('content', '')) for m in ai_messages) / len(ai_messages) if ai_messages else 0
        }
    
    def _analyze_sentiment(self, user_messages: List[Dict]) -> str:
        """分析用户情感"""
        all_content = ' '.join(m.get('content', '') for m in user_messages)
        
        positive_count = sum(1 for word in self.positive_words if word in all_content)
        negative_count = sum(1 for word in self.negative_words if word in all_content)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_knowledge_points(self, messages: List[Dict]) -> List[Dict]:
        """提取知识点（高质量Q&A对）"""
        knowledge_points = []
        
        for i in range(len(messages) - 1):
            if messages[i].get('role') == 'user' and messages[i+1].get('role') == 'assistant':
                question = messages[i].get('content', '')
                answer = messages[i+1].get('content', '')
                confidence = messages[i+1].get('confidence', 0)
                
                # 判断是否是有效的知识点
                if self._is_valid_qa_pair(question, answer, confidence):
                    knowledge_points.append({
                        'question': question,
                        'answer': answer,
                        'confidence': confidence,
                        'type': messages[i].get('subtype', '一般咨询'),
                        'timestamp': messages[i].get('timestamp', datetime.now().isoformat())
                    })
        
        logger.info(f"提取到 {len(knowledge_points)} 个有效知识点")
        return knowledge_points
    
    def _is_valid_qa_pair(self, question: str, answer: str, confidence: float) -> bool:
        """判断是否是有效的Q&A对"""
        # 条件1: 问题包含疑问词
        if not any(q in question for q in ['？', '?', '怎么', '如何', '什么', '哪个', '吗']):
            return False
        
        # 条件2: 回答不是错误信息
        error_keywords = ['抱歉', '无法', '暂时', '失败', '错误', '系统异常', '未配置']
        if any(kw in answer for kw in error_keywords):
            return False
        
        # 条件3: 置信度足够高
        if confidence < 0.7:
            return False
        
        # 条件4: 回答长度合理（不能太短）
        if len(answer) < 20:
            return False
        
        # 条件5: 回答不是简单的重复
        if answer.lower() == question.lower():
            return False
        
        return True
    
    def _calculate_quality(self, messages: List[Dict],
                          analysis: Dict,
                          end_trigger: SessionEndTrigger) -> Dict:
        """计算对话质量评分"""
        score = 0
        max_score = 100
        
        # 1. 会话完整性 (20分)
        if end_trigger in [SessionEndTrigger.USER_EXPLICIT, SessionEndTrigger.BUSINESS_COMPLETE]:
            score += 20  # 正常结束
        elif end_trigger == SessionEndTrigger.TIMEOUT_EXPIRED:
            score += 10  # 超时结束
        else:
            score += 5   # 其他情况
        
        # 2. 对话质量 (30分)
        avg_confidence = analysis.get('avg_confidence', 0)
        score += int(avg_confidence * 30)
        
        # 3. 用户满意度 (20分)
        sentiment = analysis.get('sentiment', 'neutral')
        sentiment_score = {'positive': 20, 'neutral': 10, 'negative': 0}
        score += sentiment_score.get(sentiment, 10)
        
        # 4. 问题解决 (30分)
        last_messages = messages[-3:] if len(messages) >= 3 else messages
        solved_keywords = ['解决了', '好了', '可以了', '成功了', '谢谢', '明白了']
        
        has_solved_signal = any(
            any(kw in m.get('content', '') for kw in solved_keywords)
            for m in last_messages
            if m.get('role') == 'user'
        )
        
        if has_solved_signal:
            score += 30
        elif len(messages) >= 3:
            score += 10  # 至少有互动
        
        # 获取评级
        grade = self._get_grade(score)
        
        return {
            'total_score': min(score, max_score),
            'grade': grade,
            'components': {
                'completeness': 20 if end_trigger in [SessionEndTrigger.USER_EXPLICIT, SessionEndTrigger.BUSINESS_COMPLETE] else 10,
                'quality': int(avg_confidence * 30),
                'sentiment': sentiment_score.get(sentiment, 10),
                'resolution': 30 if has_solved_signal else 0
            }
        }
    
    @staticmethod
    def _get_grade(score: int) -> str:
        """获取质量等级"""
        if score >= 90:
            return 'S'  # 优秀
        elif score >= 80:
            return 'A'  # 良好
        elif score >= 70:
            return 'B'  # 中等
        elif score >= 60:
            return 'C'  # 及格
        else:
            return 'D'  # 待改进
    
    def _generate_learning_data(self, knowledge_points: List[Dict], 
                                quality_score: int) -> Dict:
        """生成学习数据"""
        # 只有高质量对话才用于学习
        if quality_score < 60:
            return {
                'should_learn': False,
                'reason': '质量评分过低',
                'training_examples': []
            }
        
        # 生成训练数据格式（OpenAI Fine-tuning格式）
        training_examples = []
        for kp in knowledge_points:
            if kp['confidence'] >= 0.75:  # 高置信度的才用于训练
                training_examples.append({
                    'messages': [
                        {'role': 'user', 'content': kp['question']},
                        {'role': 'assistant', 'content': kp['answer']}
                    ],
                    'quality': kp['confidence'],
                    'topic': kp['type']
                })
        
        return {
            'should_learn': len(training_examples) > 0,
            'training_examples': training_examples,
            'knowledge_count': len(knowledge_points)
        }
    
    def should_end_session(self, 
                          last_message: str,
                          dialogue_type: str,
                          session_state: str) -> tuple[bool, Optional[SessionEndTrigger]]:
        """
        判断会话是否应该结束
        
        Args:
            last_message: 最后一条消息
            dialogue_type: 对话类型
            session_state: 会话状态
        
        Returns:
            (是否结束, 触发原因)
        """
        # 1. 超时判断
        if session_state == 'EXPIRED':
            return True, SessionEndTrigger.TIMEOUT_EXPIRED
        
        # 2. 用户明确结束信号
        if any(signal in last_message for signal in self.end_signals):
            # 确认后面没有新问题
            if '？' not in last_message and '吗' not in last_message:
                return True, SessionEndTrigger.USER_EXPLICIT
        
        # 3. 业务完成信号
        if dialogue_type == '业务类':
            if any(signal in last_message for signal in self.business_complete_signals):
                return True, SessionEndTrigger.BUSINESS_COMPLETE
        
        # 4. 转人工
        if '人工' in last_message or '转接' in last_message:
            return False, None  # 不结束，等待人工接入
        
        return False, None


# 使用示例
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # 模拟消息
    messages = [
        {'role': 'user', 'content': '你们的充电桩支持多少功率？', 'subtype': '产品咨询', 'timestamp': datetime.now().isoformat()},
        {'role': 'assistant', 'content': '我们支持7kW到120kW不等...', 'confidence': 0.85, 'timestamp': datetime.now().isoformat()},
        {'role': 'user', 'content': '安装需要什么条件？', 'subtype': '使用咨询', 'timestamp': datetime.now().isoformat()},
        {'role': 'assistant', 'content': '安装需要：1.固定停车位...', 'confidence': 0.90, 'timestamp': datetime.now().isoformat()},
        {'role': 'user', 'content': '好的，明白了，谢谢', 'timestamp': datetime.now().isoformat()},
    ]
    
    session_info = {
        'contact_id': 'test_user',
        'created_at': datetime.now(),
        'dialogue_type': '咨询类'
    }
    
    # 提取信息
    extractor = SessionInfoExtractor()
    extracted = extractor.extract_from_session(
        messages,
        session_info,
        SessionEndTrigger.USER_EXPLICIT
    )
    
    print(f"会话ID: {extracted.session_id}")
    print(f"对话类型: {extracted.dialogue_type}")
    print(f"知识点数: {len(extracted.knowledge_points)}")
    print(f"质量评分: {extracted.quality_score}分 ({extracted.quality_grade})")
    print(f"应学习: {extracted.should_learn}")
    print(f"训练样本: {len(extracted.training_examples)}个")

