"""
持续学习模块
从每次对话中学习，越用越好
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ContinuousLearner:
    """
    持续学习系统
    
    功能：
    1. 从每次对话中学习用户偏好
    2. 更新用户画像
    3. 优化对话策略
    """
    
    def __init__(self, db, profiler):
        """
        Args:
            db: Database实例
            profiler: UserProfiler实例
        """
        self.db = db
        self.profiler = profiler
    
    def learn_from_conversation(
        self,
        user_id: str,
        conversation: Dict[str, Any],
        satisfaction_score: Optional[int] = None
    ):
        """
        从单次对话中学习
        
        Args:
            user_id: 用户ID
            conversation: 对话数据
            satisfaction_score: 满意度评分（1-5）
        """
        profile = self.profiler.get_or_create_profile(user_id)
        
        # 更新互动次数
        profile.total_interactions += 1
        
        # 更新平均满意度
        if satisfaction_score:
            if profile.avg_satisfaction:
                # 移动平均
                profile.avg_satisfaction = (
                    profile.avg_satisfaction * 0.9 + satisfaction_score * 0.1
                )
            else:
                profile.avg_satisfaction = float(satisfaction_score)
        
        # 如果是高质量对话（满意度≥4），保存为示例
        if satisfaction_score and satisfaction_score >= 4:
            self._add_good_example(profile, conversation)
        
        # 学习偏好
        self._learn_preferences(profile, conversation, satisfaction_score)
        
        # 更新时间
        profile.last_interaction_at = datetime.now()
        
        # 保存
        self.profiler.save_profile(profile)
        
        logger.info(
            f"从对话学习: user={user_id}, "
            f"satisfaction={satisfaction_score}, "
            f"examples={len(profile.conversation_examples)}"
        )
    
    def _add_good_example(self, profile, conversation):
        """添加好的对话示例"""
        example = {
            'question': conversation.get('user_message', ''),
            'answer': conversation.get('bot_response', ''),
            'satisfaction': conversation.get('satisfaction_score'),
            'confidence': conversation.get('confidence'),
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加到示例列表
        if not profile.conversation_examples:
            profile.conversation_examples = []
        
        profile.conversation_examples.append(example)
        
        # 保持最新的10条
        profile.conversation_examples = profile.conversation_examples[-10:]
    
    def _learn_preferences(self, profile, conversation, satisfaction):
        """学习用户偏好"""
        if not profile.learned_preferences:
            profile.learned_preferences = {}
        
        user_message = conversation.get('user_message', '')
        bot_response = conversation.get('bot_response', '')
        
        # 学习：是否喜欢emoji
        if satisfaction and satisfaction >= 4:
            has_emoji = any(ord(c) > 0x1F600 for c in bot_response)
            if 'likes_emoji' not in profile.learned_preferences:
                profile.learned_preferences['likes_emoji'] = has_emoji
        
        # 学习：是否喜欢分步骤
        if '①' in bot_response or '1.' in bot_response:
            if satisfaction and satisfaction >= 4:
                profile.learned_preferences['prefers_steps'] = True
        
        # 学习：是否着急（响应时间要求）
        if any(word in user_message for word in ['快', '急', '等不了', '赶时间']):
            profile.learned_preferences['urgent_responses'] = True
        
        # 学习：是否喜欢数据
        if any(word in user_message for word in ['数据', '统计', '多少次', '频率']):
            if satisfaction and satisfaction >= 4:
                profile.learned_preferences['prefers_data'] = True
    
    def batch_optimize_weekly(self):
        """每周批量优化"""
        logger.info("开始每周批量学习...")
        
        # 1. 查询本周所有对话
        conn = self.db.connect()
        cursor = conn.cursor()
        
        week_ago = datetime.now() - timedelta(days=7)
        
        cursor.execute("""
            SELECT 
                sender_id,
                user_message,
                bot_response,
                satisfaction_score,
                confidence,
                received_at
            FROM messages
            WHERE received_at >= ?
            AND satisfaction_score IS NOT NULL
            ORDER BY satisfaction_score DESC, received_at DESC
        """, (week_ago,))
        
        rows = cursor.fetchall()
        
        # 2. 按用户分组
        by_user = {}
        for row in rows:
            user_id = row['sender_id']
            if user_id not in by_user:
                by_user[user_id] = []
            
            by_user[user_id].append({
                'user_message': row['user_message'],
                'bot_response': row['bot_response'],
                'satisfaction_score': row['satisfaction_score'],
                'confidence': row['confidence'],
                'received_at': row['received_at']
            })
        
        # 3. 更新每个用户的画像
        updated_count = 0
        for user_id, conversations in by_user.items():
            # 重新检测特征
            profile = self.profiler.auto_detect_features(user_id, conversations)
            
            # 更新示例
            good_convs = [c for c in conversations if c.get('satisfaction_score', 0) >= 4]
            for conv in good_convs[:5]:
                self._add_good_example(profile, conv)
            
            self.profiler.save_profile(profile)
            updated_count += 1
        
        logger.info(f"每周批量学习完成：更新了{updated_count}个用户画像")
        
        return updated_count

