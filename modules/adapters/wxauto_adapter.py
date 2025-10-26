"""
wxauto 适配器：唯一与 PC 微信耦合的文件
职责：消息监听、发送、@识别、ACK

参考文档: https://github.com/cluic/wxauto
Plus版本支持: 高级功能、稳定性和性能优化
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
    msg_type: str = "text"  # 消息类型: text, image, video 等


class WxAutoAdapter:
    """
    wxauto 真实适配器（标准版 + Plus版）
    注意：仅在 Windows + PC 微信环境下可用
    
    基于官方 wxauto 文档优化:
    https://github.com/cluic/wxauto
    
    Plus版本特性:
    - 更稳定的消息监听
    - 更高性能的消息处理
    - 支持更多消息类型
    - 更好的错误恢复机制
    """
    
    def __init__(
        self,
        whitelisted_groups: List[str],
        enable_humanize: bool = True,
        version_strategy: str = "auto",  # auto, plus, open_source
        prefer_plus: bool = True,         # 是否优先使用Plus版
        fallback_enabled: bool = True     # 是否允许降级
    ):
        """
        初始化wxauto适配器 - 支持双版本智能选择
        
        Args:
            whitelisted_groups: 白名单群聊列表
            enable_humanize: 是否启用拟人化（防封号）
            version_strategy: 版本选择策略
                - "auto": 自动检测，优先Plus版
                - "plus": 强制使用Plus版
                - "open_source": 强制使用开源版
            prefer_plus: 是否优先使用Plus版（仅在auto模式下有效）
            fallback_enabled: 是否允许降级（仅在plus模式下有效）
        """
        self.whitelisted_groups = whitelisted_groups
        self.my_name: Optional[str] = None
        self._wx: Any = None  # wxauto.WeChat 对象
        self._listening_chats: dict = {}  # 已监听的群聊
        
        # 版本管理
        self.version_strategy = version_strategy
        self.prefer_plus = prefer_plus
        self.fallback_enabled = fallback_enabled
        self.is_plus: bool = False  # 是否为Plus版本
        self.version_info: dict = {}  # 版本信息
        
        # 拟人化行为控制器
        self.humanize = HumanizeBehavior(enable=enable_humanize)
        
        # 初始化wxauto
        self._init_wxauto()
    
    def _init_wxauto(self):
        """
        智能版本检测和初始化
        
        支持三种策略:
        1. auto: 自动检测，优先Plus版，可降级
        2. plus: 强制Plus版，失败则报错
        3. open_source: 强制开源版
        """
        logger.info(f"🔍 版本策略: {self.version_strategy}")
        
        if self.version_strategy == "plus":
            self._init_plus_only()
        elif self.version_strategy == "open_source":
            self._init_open_source_only()
        else:  # auto
            self._init_auto_detect()
    
    def _init_plus_only(self):
        """强制使用Plus版"""
        try:
            from wxautox4 import WeChat
            self._wx = WeChat()
            self.is_plus = True
            self.version_info = {
                "version": "plus",
                "package": "wxautox4",
                "status": "active"
            }
            logger.info("✅ 使用 wxautox4 (Plus版) - 强制模式")
            logger.info("📋 Plus版特性: 更高性能、更稳定、更多功能")
        except ImportError:
            if self.fallback_enabled:
                logger.warning("⚠️  Plus版不可用，尝试降级到开源版...")
                self._init_open_source()
            else:
                logger.error("❌ wxautox4 未安装！")
                logger.error("📦 请安装Plus版: pip install wxautox")
                logger.error("🔑 请激活Plus版: wxautox -a [激活码]")
                logger.error("📖 购买地址: https://docs.wxauto.org/plus.html")
                raise ImportError("wxautox4 未安装，请安装并激活Plus版")
        except Exception as e:
            logger.error(f"❌ wxautox4 初始化失败: {e}")
            if self.fallback_enabled:
                logger.warning("⚠️  尝试降级到开源版...")
                self._init_open_source()
            else:
                raise
    
    def _init_open_source_only(self):
        """强制使用开源版"""
        try:
            from wxauto import WeChat
            self._wx = WeChat()
            self.is_plus = False
            self.version_info = {
                "version": "open_source",
                "package": "wxauto",
                "status": "active"
            }
            logger.info("✅ 使用 wxauto (开源版) - 强制模式")
            logger.info("💡 提示: 可升级到Plus版获得更好性能")
        except ImportError:
            logger.error("❌ wxauto 未安装！")
            logger.error("💡 解决方案: pip install wxauto")
            raise
        except Exception as e:
            logger.error(f"❌ wxauto 初始化失败: {e}")
            raise
    
    def _init_auto_detect(self):
        """自动检测版本"""
        # 1. 优先尝试Plus版
        if self.prefer_plus:
            try:
                from wxautox4 import WeChat
                self._wx = WeChat()
                self.is_plus = True
                self.version_info = {
                    "version": "plus",
                    "package": "wxautox4",
                    "status": "active",
                    "strategy": "auto_preferred"
                }
                logger.info("✅ 使用 wxautox4 (Plus版) - 自动检测")
                logger.info("📋 Plus版特性: 更高性能、更稳定、更多功能")
                return
            except ImportError:
                logger.info("ℹ️  wxautox4 未安装，尝试开源版...")
            except Exception as e:
                logger.warning(f"⚠️  wxautox4 初始化失败: {e}，尝试开源版...")
        
        # 2. 降级到开源版
        self._init_open_source()
    
    def _init_open_source(self):
        """初始化开源版"""
        try:
            from wxauto import WeChat
            self._wx = WeChat()
            self.is_plus = False
            self.version_info = {
                "version": "open_source",
                "package": "wxauto",
                "status": "active",
                "strategy": "fallback"
            }
            logger.info("✅ 使用 wxauto (开源版)")
            logger.info("💡 提示: 可升级到Plus版获得更好性能")
            logger.info("📖 购买地址: https://docs.wxauto.org/plus.html")
        except ImportError:
            logger.error("❌ wxauto 未安装！")
            logger.error("💡 解决方案: pip install wxauto")
            raise
        except Exception as e:
            logger.error(f"❌ wxauto 初始化失败: {e}")
            raise
    
    def get_version_info(self) -> dict:
        """获取当前版本信息"""
        return self.version_info.copy()
    
    def get_version_status(self) -> str:
        """获取版本状态描述"""
        if self.is_plus:
            return "Plus版 (高性能)"
        else:
            return "开源版 (基础功能)"
    
    def suggest_upgrade(self) -> str:
        """获取升级建议"""
        if not self.is_plus:
            return "💡 建议升级到Plus版获得更好性能和更多功能\n📖 购买地址: https://docs.wxauto.org/plus.html"
        return "✅ 已使用Plus版，享受最佳性能"
    
    def _has_plus_feature(self, feature_name: str) -> bool:
        """
        检查是否支持Plus版本的高级功能
        
        Args:
            feature_name: 功能名称
        
        Returns:
            bool: 是否支持
        """
        if not self.is_plus or not self._wx:
            return False
        
        # 检查是否有特定的方法或属性
        return hasattr(self._wx, feature_name)
    
    def get_my_name(self) -> str:
        """获取当前登录微信的昵称"""
        if self.my_name:
            return self.my_name
        
        try:
            # wxauto 的 GetUserName() 方法
            self.my_name = self._wx.GetUserName()
            logger.info(f"当前登录微信昵称: {self.my_name}")
        except Exception as e:
            logger.warning(f"无法获取微信昵称，使用默认值: {e}")
            self.my_name = "小助手"
        
        return self.my_name if self.my_name else "小助手"
    
    def setup_message_listeners(self):
        """
        为所有白名单群聊设置消息监听
        
        基于官方文档的监听机制:
        https://github.com/cluic/wxauto#2-监听消息
        """
        my_name = self.get_my_name()
        
        for group_name in self.whitelisted_groups:
            if group_name in self._listening_chats:
                continue
            
            try:
                # 消息处理函数
                def on_message(msg, chat):
                    """消息处理回调"""
                    try:
                        # 检查是否@我
                        is_at_me, clean_content = self._check_at_me(msg.content, my_name)
                        
                        if not is_at_me:
                            return
                        
                        # 构建消息对象
                        message = Message(
                            group_id=self._normalize_group_id(group_name),
                            group_name=group_name,
                            sender_id=self._normalize_sender_id(msg.sender),
                            sender_name=msg.sender,
                            content=clean_content,
                            raw_content=msg.content,
                            timestamp=datetime.now(),
                            is_at_me=True,
                            msg_type=getattr(msg, 'type', 'text')
                        )
                        
                        # 将消息存储到队列
                        if not hasattr(self, '_message_queue'):
                            self._message_queue = []
                        self._message_queue.append(message)
                        
                        logger.info(
                            f"收到@消息: {group_name} - {msg.sender}: {clean_content[:50]}..."
                        )
                        
                    except Exception as e:
                        logger.error(f"处理消息失败: {e}")
                
                # 添加监听
                self._wx.AddListenChat(nickname=group_name, callback=on_message)
                self._listening_chats[group_name] = on_message
                
                logger.info(f"✅ 已为群聊添加监听: {group_name}")
                
            except Exception as e:
                logger.error(f"添加监听失败: {group_name}, {e}")
    
    def iter_new_messages(self) -> Iterator[Message]:
        """
        迭代获取新消息（从消息队列中取出）
        
        Yields:
            Message: 新消息对象
        """
        # 初始化消息队列
        if not hasattr(self, '_message_queue'):
            self._message_queue = []
        
        # 返回队列中的所有消息
        while self._message_queue:
            yield self._message_queue.pop(0)
    
    def send_text(
        self,
        group_name: str,
        text: str,
        at_user: Optional[str] = None
    ) -> bool:
        """
        发送文本消息（拟人化）
        
        基于官方文档:
        https://github.com/cluic/wxauto#1-基本使用
        
        Args:
            group_name: 群聊名称
            text: 消息文本
            at_user: @的用户名（可选）
        
        Returns:
            bool: 是否成功
        """
        try:
            # 拟人化：发送前延迟（模拟思考和打字）
            self.humanize.before_send(text)
            
            # 拟人化：添加语气词等
            text = self.humanize.add_humanized_text(text)
            
            # 如果需要 @用户，添加前缀
            if at_user:
                text = f"@{at_user} {text}"
            
            # 基于官方API: wx.SendMsg("你好", who="张三")
            self._wx.SendMsg(text, who=group_name)
            
            logger.info(f"✅ 消息已发送: group={group_name}, len={len(text)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 发送消息失败: {group_name}, {e}")
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
    
    def get_current_chat_messages(self) -> List[Any]:
        """
        获取当前聊天窗口的所有消息
        
        基于官方文档:
        https://github.com/cluic/wxauto#获取当前聊天窗口消息
        
        Returns:
            List[Any]: 消息列表
        """
        try:
            msgs = self._wx.GetAllMessage()
            return msgs if msgs else []
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            return []
    
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
    
    def cleanup(self):
        """清理资源，移除所有监听"""
        for group_name, callback in self._listening_chats.items():
            try:
                self._wx.RemoveListenChat(nickname=group_name)
                logger.info(f"已移除监听: {group_name}")
            except Exception as e:
                logger.error(f"移除监听失败: {group_name}, {e}")
        
        self._listening_chats.clear()


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
