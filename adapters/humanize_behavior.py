"""
拟人化行为模块
通过模拟人类行为特征，降低被微信检测的风险
"""
import time
import random
import logging
from datetime import datetime, time as dt_time
from typing import Optional

logger = logging.getLogger(__name__)


class HumanizeBehavior:
    """
    拟人化行为控制器
    
    功能：
    1. 随机延迟
    2. 模拟打字速度
    3. 非规律性操作
    4. 作息时间控制
    5. 行为特征随机化
    """
    
    def __init__(
        self,
        enable: bool = True,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        typing_speed_chars_per_sec: float = 8.0,  # 每秒8个字（人类平均）
        enable_rest_time: bool = True
    ):
        """
        初始化拟人化控制器
        
        Args:
            enable: 是否启用拟人化
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            typing_speed_chars_per_sec: 打字速度（字符/秒）
            enable_rest_time: 是否启用作息控制
        """
        self.enable = enable
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.typing_speed = typing_speed_chars_per_sec
        self.enable_rest_time = enable_rest_time
        
        # 统计数据
        self.total_operations = 0
        self.total_delay_time = 0.0
        
        logger.info(
            f"拟人化行为已{'启用' if enable else '禁用'}: "
            f"delay={min_delay}-{max_delay}s, typing_speed={typing_speed_chars_per_sec}字/秒"
        )
    
    def before_send(self, message: str) -> None:
        """
        发送消息前的延迟
        模拟：思考时间 + 打字时间
        
        Args:
            message: 要发送的消息
        """
        if not self.enable:
            return
        
        # 1. 思考延迟（随机）
        think_delay = random.uniform(self.min_delay, self.max_delay)
        
        # 2. 打字延迟（根据消息长度）
        typing_delay = len(message) / self.typing_speed
        
        # 3. 添加一点随机性（±20%）
        typing_delay *= random.uniform(0.8, 1.2)
        
        total_delay = think_delay + typing_delay
        
        # 4. 偶尔"思考"更久（10%概率）
        if random.random() < 0.1:
            extra_delay = random.uniform(2, 5)
            total_delay += extra_delay
            logger.debug(f"额外思考时间: {extra_delay:.1f}秒")
        
        logger.debug(
            f"发送前延迟: {total_delay:.2f}秒 "
            f"(思考={think_delay:.1f}s + 打字={typing_delay:.1f}s)"
        )
        
        time.sleep(total_delay)
        
        self.total_operations += 1
        self.total_delay_time += total_delay
    
    def before_check_messages(self) -> bool:
        """
        检查消息前的延迟
        返回：是否应该继续（考虑作息时间）
        
        Returns:
            bool: True=继续，False=跳过此次检查
        """
        if not self.enable:
            return True
        
        # 1. 随机延迟（避免精确时间间隔）
        delay = random.uniform(0.3, 1.2)
        time.sleep(delay)
        
        # 2. 检查是否在作息时间内
        if self.enable_rest_time:
            if not self._is_active_time():
                logger.debug("当前非活跃时间，跳过检查")
                return False
        
        # 3. 偶尔"走神"（5%概率）
        if random.random() < 0.05:
            distraction_time = random.uniform(10, 60)
            logger.debug(f"模拟走神: {distraction_time:.0f}秒")
            time.sleep(distraction_time)
        
        return True
    
    def should_respond_now(self) -> bool:
        """
        判断是否应该立即响应
        模拟人可能在忙，有时需要晚点回复
        
        Returns:
            bool: True=立即响应，False=延迟响应
        """
        if not self.enable:
            return True
        
        # 深夜降低响应率（70%不响应）
        if self._is_late_night():
            if random.random() < 0.7:
                logger.info("深夜模式：暂不响应")
                return False
        
        # 工作时间外降低响应率（30%不响应）
        if not self._is_work_time():
            if random.random() < 0.3:
                logger.debug("非工作时间：延迟响应")
                return False
        
        # 偶尔"没看到"消息（5%概率）
        if random.random() < 0.05:
            logger.debug("模拟未看到消息")
            return False
        
        return True
    
    def get_ack_message(self) -> str:
        """
        获取ACK确认消息（随机变化）
        
        Returns:
            ACK消息
        """
        templates = [
            "收到，正在查询...",
            "好的，让我看看",
            "稍等，查一下资料",
            "嗯，我帮你查查",
            "收到，稍等片刻",
            "明白了，马上处理",
            "好的，等我一下",
        ]
        
        return random.choice(templates)
    
    def add_humanized_text(self, text: str) -> str:
        """
        为文本添加拟人化元素
        
        Args:
            text: 原始文本
        
        Returns:
            拟人化后的文本
        """
        if not self.enable:
            return text
        
        # 开头语气词（30%概率）
        if random.random() < 0.3:
            greetings = ["嗯", "好的", "明白了", "这样啊"]
            text = f"{random.choice(greetings)}，{text}"
        
        # 结尾语气词（20%概率）
        if random.random() < 0.2:
            endings = ["～", "哦", "呢", ""]
            text = f"{text}{random.choice(endings)}"
        
        # 偶尔添加emoji（10%概率）
        if random.random() < 0.1:
            emojis = ["😊", "👍", "✅", ""]
            text = f"{text} {random.choice(emojis)}"
        
        return text
    
    def _is_active_time(self) -> bool:
        """判断是否在活跃时间（8:00-23:00）"""
        current_hour = datetime.now().hour
        return 8 <= current_hour < 23
    
    def _is_work_time(self) -> bool:
        """判断是否在工作时间（9:00-18:00）"""
        current_hour = datetime.now().hour
        return 9 <= current_hour < 18
    
    def _is_late_night(self) -> bool:
        """判断是否是深夜（0:00-7:00）"""
        current_hour = datetime.now().hour
        return 0 <= current_hour < 7
    
    def get_stats(self) -> Dict[str, float]:
        """获取统计信息"""
        avg_delay = (
            self.total_delay_time / self.total_operations
            if self.total_operations > 0 else 0
        )
        
        return {
            'total_operations': self.total_operations,
            'total_delay_time': self.total_delay_time,
            'avg_delay_per_operation': avg_delay
        }

