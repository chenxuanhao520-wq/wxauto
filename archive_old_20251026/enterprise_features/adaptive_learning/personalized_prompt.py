"""
个性化Prompt生成器
根据用户画像动态生成System Prompt
"""
import logging
from typing import Dict, Any, Optional

from .user_profiler import UserProfile

logger = logging.getLogger(__name__)


class PersonalizedPromptGenerator:
    """
    个性化Prompt生成器
    
    根据用户画像生成个性化的System Prompt
    """
    
    def __init__(self, base_style: Optional[Dict] = None):
        """
        Args:
            base_style: 基础对话风格（从历史记录学习）
        """
        self.base_style = base_style or self._get_default_style()
    
    def generate(
        self,
        user_profile: UserProfile,
        context: str = "充电桩客服"
    ) -> str:
        """
        生成个性化System Prompt
        
        Args:
            user_profile: 用户画像
            context: 对话场景
        
        Returns:
            个性化的System Prompt
        """
        prompt_parts = []
        
        # 1. 基础角色
        prompt_parts.append(f"你是{context}，负责解答客户问题。\n")
        
        # 2. 客户类型调整
        prompt_parts.append(self._get_customer_type_instruction(user_profile))
        
        # 3. 技术水平调整
        prompt_parts.append(self._get_technical_level_instruction(user_profile))
        
        # 4. 沟通风格调整
        prompt_parts.append(self._get_communication_style_instruction(user_profile))
        
        # 5. 个性化偏好
        prompt_parts.append(self._get_learned_preferences_instruction(user_profile))
        
        # 6. Few-Shot示例（如果有）
        if user_profile.conversation_examples:
            prompt_parts.append(self._get_fewshot_examples(user_profile))
        
        # 7. 基础风格（从历史学习）
        if self.base_style:
            prompt_parts.append(self._get_base_style_instruction())
        
        prompt = "\n".join(prompt_parts)
        
        logger.debug(f"生成个性化Prompt: user={user_profile.user_id}, type={user_profile.customer_type}")
        
        return prompt
    
    def _get_customer_type_instruction(self, profile: UserProfile) -> str:
        """客户类型指令"""
        if profile.customer_type == 'vip':
            return f"""
【VIP客户】{profile.company_name or ''}
- 称呼：尊敬的{profile.user_name or '客户'}
- 优先级：最高
- 语气：正式、尊重、耐心
- 特别注意：详细解答，主动提供额外帮助
"""
        elif profile.customer_type == 'new':
            return """
【新客户】
- 称呼：您
- 语气：友好、欢迎
- 特别注意：多一些问候和引导，建立信任
"""
        else:
            return """
【普通客户】
- 称呼：您/你（灵活）
- 语气：友好、专业
"""
    
    def _get_technical_level_instruction(self, profile: UserProfile) -> str:
        """技术水平指令"""
        if profile.technical_level == 'high':
            return """
【技术水平：高】
- 可以使用专业术语（BMS、CAN总线、通信协议等）
- 回答简洁，直接给出技术方案
- 可以深入技术细节
"""
        elif profile.technical_level == 'low':
            return """
【技术水平：低】
- 避免专业术语，用通俗语言解释
- 分步骤详细说明，每步都要清楚
- 必要时提供图片说明链接
- 多用比喻和类比
"""
        else:
            return """
【技术水平：中等】
- 适度使用专业术语，但要解释
- 分步骤说明，清晰明了
- 平衡专业性和易懂性
"""
    
    def _get_communication_style_instruction(self, profile: UserProfile) -> str:
        """沟通风格指令"""
        styles = {
            'formal': """
【沟通风格：正式】
- 使用书面语，避免口语
- 不使用语气词（呢、哦、啊等）
- 不使用emoji
- 结构清晰，逻辑严谨
""",
            'friendly': """
【沟通风格：友好】
- 适当使用语气词（呢、哦、～等）
- 可以用一些emoji（😊 👍 ✅）
- 语气亲切但不失专业
- 像朋友一样交流
""",
            'casual': """
【沟通风格：随意】
- 多用口语化表达
- 多用语气词（嗯嗯、好呀、哈哈等）
- 可以用emoji
- 轻松自然的对话
"""
        }
        
        return styles.get(profile.communication_style, styles['friendly'])
    
    def _get_learned_preferences_instruction(self, profile: UserProfile) -> str:
        """学习到的偏好指令"""
        if not profile.learned_preferences:
            return ""
        
        prefs = profile.learned_preferences
        instruction = "\n【学习到的偏好】\n"
        
        if prefs.get('likes_emoji'):
            instruction += "- 这个用户喜欢emoji，适当使用\n"
        
        if prefs.get('prefers_steps'):
            instruction += "- 这个用户喜欢分步骤说明，使用①②③\n"
        
        if prefs.get('prefers_data'):
            instruction += "- 这个用户喜欢看数据，提供具体数字和统计\n"
        
        if prefs.get('urgent_responses'):
            instruction += "- 这个用户通常比较着急，回答要快速直接\n"
        
        return instruction
    
    def _get_fewshot_examples(self, profile: UserProfile) -> str:
        """Few-Shot示例"""
        if not profile.conversation_examples:
            return ""
        
        instruction = "\n【参考对话示例】（请模仿这种风格回答）\n\n"
        
        for i, example in enumerate(profile.conversation_examples[:5], 1):
            instruction += f"示例{i}：\n"
            instruction += f"客户: {example['question']}\n"
            instruction += f"客服: {example['answer']}\n\n"
        
        return instruction
    
    def _get_base_style_instruction(self) -> str:
        """基础风格指令（从历史记录学习）"""
        if not self.base_style:
            return ""
        
        instruction = "\n【整体风格要求】\n"
        
        if self.base_style.get('common_phrases'):
            phrases = ', '.join(self.base_style['common_phrases'][:10])
            instruction += f"- 常用表达：{phrases}\n"
        
        if self.base_style.get('avg_length'):
            instruction += f"- 回答长度：约{self.base_style['avg_length']}字\n"
        
        if self.base_style.get('tone_keywords'):
            instruction += f"- 语气特点：{self.base_style['tone_keywords']}\n"
        
        return instruction
    
    def _get_default_style(self) -> Dict:
        """默认风格"""
        return {
            'common_phrases': ['好的', '您', '请', '帮您', '建议'],
            'avg_length': 150,
            'tone_keywords': '专业、友好'
        }

