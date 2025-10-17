"""
用户画像系统
自动构建和维护用户画像
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    user_name: Optional[str] = None
    
    # 基础属性
    customer_type: str = 'regular'  # vip/regular/new
    company_name: Optional[str] = None
    role: Optional[str] = None  # 运营商/车主/经销商/工程师
    
    # 沟通偏好
    communication_style: str = 'friendly'  # formal/friendly/casual
    preferred_response_style: str = 'concise'  # concise/detailed
    technical_level: str = 'medium'  # high/medium/low
    
    # 行为特征
    total_interactions: int = 0
    avg_satisfaction: Optional[float] = None
    common_topics: List[str] = None
    active_hours: List[int] = None
    
    # 学习到的偏好
    learned_preferences: Dict[str, Any] = None
    conversation_examples: List[Dict] = None  # 好的对话示例（Few-Shot）
    
    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_interaction_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.common_topics is None:
            self.common_topics = []
        if self.active_hours is None:
            self.active_hours = []
        if self.learned_preferences is None:
            self.learned_preferences = {}
        if self.conversation_examples is None:
            self.conversation_examples = []


class UserProfiler:
    """
    用户画像构建器
    
    功能：
    1. 自动构建用户画像
    2. 从对话中学习用户特征
    3. 动态更新画像
    """
    
    def __init__(self, db):
        """
        Args:
            db: Database实例
        """
        self.db = db
        self._init_profile_table()
    
    def _init_profile_table(self):
        """初始化用户画像表"""
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                user_name TEXT,
                customer_type TEXT DEFAULT 'regular',
                company_name TEXT,
                role TEXT,
                communication_style TEXT DEFAULT 'friendly',
                preferred_response_style TEXT DEFAULT 'concise',
                technical_level TEXT DEFAULT 'medium',
                total_interactions INTEGER DEFAULT 0,
                avg_satisfaction REAL,
                common_topics TEXT,
                active_hours TEXT,
                learned_preferences TEXT,
                conversation_examples TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_interaction_at DATETIME
            )
        """)
        
        conn.commit()
        logger.info("用户画像表初始化完成")
    
    def get_or_create_profile(self, user_id: str, user_name: str = None) -> UserProfile:
        """获取或创建用户画像"""
        profile = self.get_profile(user_id)
        
        if profile:
            return profile
        
        # 创建新画像
        new_profile = UserProfile(
            user_id=user_id,
            user_name=user_name,
            created_at=datetime.now()
        )
        
        self.save_profile(new_profile)
        logger.info(f"创建新用户画像: {user_id}")
        
        return new_profile
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?",
            (user_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # 解析JSON字段
        common_topics = json.loads(row['common_topics']) if row['common_topics'] else []
        active_hours = json.loads(row['active_hours']) if row['active_hours'] else []
        learned_preferences = json.loads(row['learned_preferences']) if row['learned_preferences'] else {}
        conversation_examples = json.loads(row['conversation_examples']) if row['conversation_examples'] else []
        
        return UserProfile(
            user_id=row['user_id'],
            user_name=row['user_name'],
            customer_type=row['customer_type'],
            company_name=row['company_name'],
            role=row['role'],
            communication_style=row['communication_style'],
            preferred_response_style=row['preferred_response_style'],
            technical_level=row['technical_level'],
            total_interactions=row['total_interactions'],
            avg_satisfaction=row['avg_satisfaction'],
            common_topics=common_topics,
            active_hours=active_hours,
            learned_preferences=learned_preferences,
            conversation_examples=conversation_examples,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            last_interaction_at=datetime.fromisoformat(row['last_interaction_at']) if row['last_interaction_at'] else None
        )
    
    def save_profile(self, profile: UserProfile):
        """保存用户画像"""
        conn = self.db.connect()
        cursor = conn.cursor()
        
        # 转换JSON字段
        common_topics_json = json.dumps(profile.common_topics, ensure_ascii=False)
        active_hours_json = json.dumps(profile.active_hours)
        learned_preferences_json = json.dumps(profile.learned_preferences, ensure_ascii=False)
        conversation_examples_json = json.dumps(profile.conversation_examples, ensure_ascii=False)
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_profiles
            (user_id, user_name, customer_type, company_name, role,
             communication_style, preferred_response_style, technical_level,
             total_interactions, avg_satisfaction,
             common_topics, active_hours, learned_preferences, conversation_examples,
             updated_at, last_interaction_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile.user_id,
            profile.user_name,
            profile.customer_type,
            profile.company_name,
            profile.role,
            profile.communication_style,
            profile.preferred_response_style,
            profile.technical_level,
            profile.total_interactions,
            profile.avg_satisfaction,
            common_topics_json,
            active_hours_json,
            learned_preferences_json,
            conversation_examples_json,
            datetime.now(),
            profile.last_interaction_at or datetime.now()
        ))
        
        conn.commit()
    
    def auto_detect_features(
        self,
        user_id: str,
        session_history: List[Dict]
    ) -> UserProfile:
        """
        从会话历史自动检测用户特征
        
        Args:
            user_id: 用户ID
            session_history: 会话历史
        
        Returns:
            UserProfile: 用户画像
        """
        profile = self.get_or_create_profile(user_id)
        
        if not session_history:
            return profile
        
        # 提取用户消息
        user_messages = [h.get('user_message', '') for h in session_history if h.get('user_message')]
        
        # 检测沟通风格
        profile.communication_style = self._detect_communication_style(user_messages)
        
        # 检测技术水平
        profile.technical_level = self._detect_technical_level(user_messages)
        
        # 提取常见话题
        profile.common_topics = self._extract_topics(user_messages)
        
        # 统计互动次数
        profile.total_interactions = len(session_history)
        
        # 提取活跃时段
        timestamps = [h.get('received_at') for h in session_history if h.get('received_at')]
        profile.active_hours = self._extract_active_hours(timestamps)
        
        # 保存
        self.save_profile(profile)
        
        logger.info(f"自动画像更新: {user_id}, style={profile.communication_style}, tech={profile.technical_level}")
        
        return profile
    
    def _detect_communication_style(self, messages: List[str]) -> str:
        """检测沟通风格"""
        if not messages:
            return 'friendly'
        
        # 分析指标
        text = ' '.join(messages)
        
        # 正式指标
        formal_words = ['您好', '请问', '麻烦', '感谢', '谢谢您']
        formal_count = sum(1 for word in formal_words if word in text)
        
        # 随意指标
        casual_words = ['哈哈', '嗯嗯', '好呀', '啊', '呢']
        casual_count = sum(1 for word in casual_words if word in text)
        
        # emoji
        has_emoji = any(c for msg in messages for c in msg if ord(c) > 0x1F600)
        
        # 判断
        if formal_count > casual_count and not has_emoji:
            return 'formal'
        elif casual_count > formal_count or has_emoji:
            return 'casual'
        else:
            return 'friendly'
    
    def _detect_technical_level(self, messages: List[str]) -> str:
        """检测技术水平"""
        if not messages:
            return 'medium'
        
        text = ' '.join(messages).lower()
        
        # 技术关键词
        high_tech_words = [
            'bms', 'can总线', '协议', '固件', '电压', '电流',
            '通信模块', '功率', '电阻', '接口', '参数'
        ]
        
        tech_count = sum(1 for word in high_tech_words if word in text)
        
        if tech_count >= 5:
            return 'high'
        elif tech_count >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _extract_topics(self, messages: List[str]) -> List[str]:
        """提取常见话题"""
        topics = []
        
        keyword_map = {
            '故障': '故障排查',
            '安装': '安装问题',
            '充电': '充电问题',
            '价格': '价格咨询',
            '维修': '维修保养'
        }
        
        text = ' '.join(messages)
        for keyword, topic in keyword_map.items():
            if keyword in text:
                topics.append(topic)
        
        return list(set(topics))[:5]
    
    def _extract_active_hours(self, timestamps: List) -> List[int]:
        """提取活跃时段"""
        hours = []
        
        for ts in timestamps:
            if isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    hours.append(dt.hour)
                except:
                    continue
            elif isinstance(ts, datetime):
                hours.append(ts.hour)
        
        # 统计出现频率最高的3个小时
        from collections import Counter
        if hours:
            most_common = Counter(hours).most_common(3)
            return [hour for hour, count in most_common]
        
        return []

