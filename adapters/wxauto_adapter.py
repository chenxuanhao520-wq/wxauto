"""
wxauto 适配器：唯一与 PC 微信耦合的文件
职责：消息监听、发送、@识别、ACK
"""
import re
import time
import random
import logging
from dataclasses import dataclass
from typing import List, Optional, Iterator, Any
from datetime import datetime

from .humanize_behavior import HumanizeBehavior

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """微信消息结构"""
    group_id: str
    group_name: str
    sender_id: str
    sender_name: str
    content: str
    timestamp: datetime
    is_at_me: bool = False
    raw_content: str = ""  # 原始内容（含@符号）


class WxAutoAdapter:
    """
    wxauto 真实适配器
    注意：仅在 Windows + PC 微信环境下可用
    """
    
    def __init__(
        self,
        whitelisted_groups: List[str],
        enable_humanize: bool = True
    ):
        """
        Args:
            whitelisted_groups: 白名单群聊列表
            enable_humanize: 是否启用拟人化（防封号）
        """
        self.whitelisted_groups = whitelisted_groups
        self.my_name: Optional[str] = None
        self._wx: Any = None  # wxauto.WeChat 对象
        self._last_messages: dict = {}  # 记录每个群的最后消息时间，用于去重
        
        # 拟人化行为控制器
        self.humanize = HumanizeBehavior(enable=enable_humanize)
        
        try:
            from wxauto import WeChat  # type: ignore
            self._wx = WeChat()
            logger.info("wxauto 已初始化")
        except ImportError:
            logger.error("wxauto 未安装，请运行: pip install wxauto")
            raise
        except Exception as e:
            logger.error(f"wxauto 初始化失败: {e}")
            raise
    
    def get_my_name(self) -> str:
        """获取当前登录微信的昵称"""
        if self.my_name:
            return self.my_name
        
        try:
            # wxauto 可能提供获取当前用户信息的方法
            # 这里使用占位逻辑，实际需要根据 wxauto API 调整
            self.my_name = self._wx.GetUserName() if hasattr(self._wx, 'GetUserName') else "小助手"
            logger.info(f"当前登录微信昵称: {self.my_name}")
        except Exception as e:
            logger.warning(f"无法获取微信昵称，使用默认值: {e}")
            self.my_name = "小助手"
        
        return self.my_name if self.my_name else "小助手"
    
    def focus_chat(self, chat_name: str) -> bool:
        """
        切换到指定群聊
        Args:
            chat_name: 群聊名称
        Returns:
            bool: 是否成功
        """
        try:
            self._wx.ChatWith(chat_name)
            logger.debug(f"已切换到群聊: {chat_name}")
            return True
        except Exception as e:
            logger.error(f"切换群聊失败: {chat_name}, {e}")
            return False
    
    def iter_new_messages(self) -> Iterator[Message]:
        """
        迭代获取白名单群的新消息
        仅返回被 @ 的消息
        Yields:
            Message: 新消息对象
        """
        my_name = self.get_my_name()
        
        for group_name in self.whitelisted_groups:
            try:
                if not self.focus_chat(group_name):
                    continue
                
                # 获取最新消息
                msgs = self._wx.GetAllMessage()
                
                if not msgs:
                    continue
                
                # 处理消息列表
                for msg_data in msgs:
                    # wxauto 返回的消息格式（需根据实际API调整）:
                    # msg_data = [发送者, 内容, 时间戳]
                    if len(msg_data) < 2:
                        continue
                    
                    sender_name = str(msg_data[0]).strip()
                    content = str(msg_data[1]).strip()
                    
                    # 跳过自己的消息
                    if sender_name == my_name:
                        continue
                    
                    # 检查是否被 @
                    is_at_me, clean_content = self._check_at_me(content, my_name)
                    
                    if not is_at_me:
                        continue
                    
                    # 构建消息对象
                    msg = Message(
                        group_id=self._normalize_group_id(group_name),
                        group_name=group_name,
                        sender_id=self._normalize_sender_id(sender_name),
                        sender_name=sender_name,
                        content=clean_content,
                        raw_content=content,
                        timestamp=datetime.now(),
                        is_at_me=True
                    )
                    
                    # 简单去重：检查是否已处理过相同内容
                    msg_key = f"{group_name}:{sender_name}:{clean_content}"
                    if msg_key in self._last_messages:
                        last_time = self._last_messages[msg_key]
                        if (datetime.now() - last_time).total_seconds() < 5:
                            continue
                    
                    self._last_messages[msg_key] = datetime.now()
                    
                    logger.info(
                        f"收到@消息: group={group_name}, "
                        f"sender={sender_name}, content={clean_content[:50]}..."
                    )
                    
                    yield msg
                    
            except Exception as e:
                logger.error(f"获取群消息失败: {group_name}, {e}")
                continue
    
    def send_text(
        self,
        group_name: str,
        text: str,
        at_user: Optional[str] = None
    ) -> bool:
        """
        发送文本消息（拟人化）
        Args:
            group_name: 群聊名称
            text: 消息文本
            at_user: @的用户名（可选）
        Returns:
            bool: 是否成功
        """
        try:
            if not self.focus_chat(group_name):
                return False
            
            # 拟人化：发送前延迟（模拟思考和打字）
            self.humanize.before_send(text)
            
            # 拟人化：添加语气词等
            text = self.humanize.add_humanized_text(text)
            
            # 如果需要 @用户，添加前缀
            if at_user:
                text = f"@{at_user} {text}"
            
            self._wx.SendMsg(text)
            logger.info(f"消息已发送: group={group_name}, len={len(text)}")
            return True
            
        except Exception as e:
            logger.error(f"发送消息失败: {group_name}, {e}")
            return False
    
    def ack(
        self,
        group_name: str,
        sender_name: str,
        ack_text: str = "收到，处理中……"
    ) -> bool:
        """
        发送 ACK 确认消息（拟人化）
        Args:
            group_name: 群聊名称
            sender_name: 被 @ 的用户名
            ack_text: ACK 文本（可选，默认随机）
        Returns:
            bool: 是否成功
        """
        # 使用随机的ACK消息
        if ack_text == "收到，处理中……":
            ack_text = self.humanize.get_ack_message()
        
        return self.send_text(group_name, ack_text, at_user=sender_name)
    
    def _check_at_me(self, content: str, my_name: str) -> tuple[bool, str]:
        """
        检查消息是否 @ 了我，并返回清理后的内容
        Args:
            content: 原始消息内容
            my_name: 我的昵称
        Returns:
            (is_at_me, clean_content)
        """
        # 匹配 @昵称（允许空格、表情等变体）
        # 示例：@小助手、@小助手  、@ 小助手
        pattern = rf"@\s*{re.escape(my_name)}\b"
        
        match = re.search(pattern, content)
        if not match:
            return False, content
        
        # 移除 @ 部分
        clean_content = re.sub(pattern, "", content).strip()
        
        return True, clean_content
    
    @staticmethod
    def _normalize_group_id(group_name: str) -> str:
        """将群名转换为群ID（简化版，实际可能需要哈希或映射）"""
        return group_name.replace(" ", "_").lower()
    
    @staticmethod
    def _normalize_sender_id(sender_name: str) -> str:
        """将发送者名称转换为ID"""
        return sender_name.replace(" ", "_").lower()


class FakeWxAdapter:
    """
    假微信适配器（用于测试）
    可在无 wxauto 环境下运行单元测试
    """
    
    def __init__(self, whitelisted_groups: List[str]):
        self.whitelisted_groups = whitelisted_groups
        self.my_name = "测试助手"
        self.message_queue: List[Message] = []
        self.sent_messages: List[dict] = []
        
        logger.info("FakeWxAdapter 已初始化（测试模式）")
    
    def get_my_name(self) -> str:
        """获取当前登录微信的昵称"""
        return self.my_name
    
    def focus_chat(self, chat_name: str) -> bool:
        """切换到指定群聊"""
        logger.debug(f"[FAKE] 切换群聊: {chat_name}")
        return chat_name in self.whitelisted_groups
    
    def iter_new_messages(self) -> Iterator[Message]:
        """
        迭代获取新消息（从队列中读取）
        Yields:
            Message: 新消息
        """
        while self.message_queue:
            msg = self.message_queue.pop(0)
            logger.debug(f"[FAKE] 返回消息: {msg.sender_name}: {msg.content}")
            yield msg
    
    def send_text(
        self,
        group_name: str,
        text: str,
        at_user: Optional[str] = None
    ) -> bool:
        """发送文本消息（记录到发送列表）"""
        full_text = f"@{at_user} {text}" if at_user else text
        
        self.sent_messages.append({
            "group_name": group_name,
            "text": full_text,
            "at_user": at_user,
            "timestamp": datetime.now()
        })
        
        logger.info(f"[FAKE] 发送消息: group={group_name}, text={full_text[:50]}...")
        return True
    
    def ack(
        self,
        group_name: str,
        sender_name: str,
        ack_text: str = "收到,处理中……"
    ) -> bool:
        """发送 ACK"""
        return self.send_text(group_name, ack_text, at_user=sender_name)
    
    # ==================== 测试辅助方法 ====================
    
    def inject_message(
        self,
        group_name: str,
        sender_name: str,
        content: str,
        is_at_me: bool = True
    ) -> None:
        """
        注入测试消息
        Args:
            group_name: 群名
            sender_name: 发送者
            content: 内容
            is_at_me: 是否@我
        """
        msg = Message(
            group_id=group_name.replace(" ", "_").lower(),
            group_name=group_name,
            sender_id=sender_name.replace(" ", "_").lower(),
            sender_name=sender_name,
            content=content,
            raw_content=f"@{self.my_name} {content}" if is_at_me else content,
            timestamp=datetime.now(),
            is_at_me=is_at_me
        )
        
        self.message_queue.append(msg)
        logger.debug(f"[FAKE] 注入消息: {sender_name}: {content}")
    
    def get_sent_messages(self) -> List[dict]:
        """获取所有已发送的消息"""
        return self.sent_messages.copy()
    
    def clear_sent_messages(self) -> None:
        """清空发送记录"""
        self.sent_messages.clear()
