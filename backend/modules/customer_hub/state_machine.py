"""
会话状态机
基于"最后说话方 + SLA"自动计算会话状态
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

from .types import Thread, ThreadStatus, SLAConfig, Party

logger = logging.getLogger(__name__)


class StateMachine:
    """会话状态机"""
    
    def __init__(self, sla_config: Optional[SLAConfig] = None):
        """
        初始化状态机
        
        Args:
            sla_config: SLA配置,如果为None则使用默认配置
        """
        self.sla_config = sla_config or SLAConfig()
        logger.info(
            f"状态机初始化: need_reply={self.sla_config.need_reply_minutes}分钟, "
            f"follow_up={self.sla_config.follow_up_hours}小时"
        )
    
    def compute_status(self, thread: Thread, now: Optional[datetime] = None) -> ThreadStatus:
        """
        计算会话状态
        
        基于以下规则:
        1. 如果设定了唤醒点(snooze_at或follow_up_at)且已到时间 -> NEED_REPLY
        2. 如果最后是客户说话(them):
           - 超过need_reply_minutes -> OVERDUE
           - 未超过 -> NEED_REPLY
        3. 如果最后是我方说话(me):
           - 超过follow_up_hours -> NEED_REPLY (回弹)
           - 未超过 -> WAITING_THEM
        
        Args:
            thread: 会话对象
            now: 当前时间,默认为系统时间
        
        Returns:
            ThreadStatus: 计算后的状态
        """
        if now is None:
            now = datetime.now()
        
        # 检查唤醒点
        if thread.snooze_at and thread.snooze_at <= now:
            logger.debug(f"线程 {thread.id} 推迟时间已到,状态: NEED_REPLY")
            return ThreadStatus.NEED_REPLY
        
        if thread.follow_up_at and thread.follow_up_at <= now:
            logger.debug(f"线程 {thread.id} 跟进时间已到,状态: NEED_REPLY")
            return ThreadStatus.NEED_REPLY
        
        # 计算时间差
        time_diff = now - thread.last_msg_at
        diff_minutes = time_diff.total_seconds() / 60
        diff_hours = diff_minutes / 60
        
        # 根据最后说话方判断
        if thread.last_speaker == Party.THEM:
            # 客户最后发言
            if diff_minutes > self.sla_config.need_reply_minutes:
                logger.debug(
                    f"线程 {thread.id} 客户发言超时 "
                    f"{diff_minutes:.1f}分钟 > {self.sla_config.need_reply_minutes}分钟, "
                    f"状态: OVERDUE"
                )
                return ThreadStatus.OVERDUE
            else:
                return ThreadStatus.NEED_REPLY
        
        elif thread.last_speaker == Party.ME:
            # 我方最后发言
            if diff_hours > self.sla_config.follow_up_hours:
                logger.debug(
                    f"线程 {thread.id} 等待对方超时 "
                    f"{diff_hours:.1f}小时 > {self.sla_config.follow_up_hours}小时, "
                    f"状态: NEED_REPLY (回弹)"
                )
                return ThreadStatus.NEED_REPLY
            else:
                return ThreadStatus.WAITING_THEM
        
        # 默认返回原状态
        return thread.status
    
    def compute_next_times(
        self, 
        thread: Thread, 
        now: Optional[datetime] = None
    ) -> Dict[str, Optional[datetime]]:
        """
        计算下一个SLA时间点
        
        Args:
            thread: 会话对象
            now: 当前时间,默认为系统时间
        
        Returns:
            包含sla_at和follow_up_at的字典
        """
        if now is None:
            now = datetime.now()
        
        result = {
            'sla_at': None,
            'follow_up_at': None
        }
        
        if thread.last_speaker == Party.THEM:
            # 客户最后发言 -> 设置SLA截止时间
            sla_at = thread.last_msg_at + timedelta(
                minutes=self.sla_config.need_reply_minutes
            )
            result['sla_at'] = sla_at
            logger.debug(f"线程 {thread.id} SLA截止时间: {sla_at}")
        
        elif thread.last_speaker == Party.ME:
            # 我方最后发言 -> 设置跟进时间
            follow_up_at = thread.last_msg_at + timedelta(
                hours=self.sla_config.follow_up_hours
            )
            result['follow_up_at'] = follow_up_at
            logger.debug(f"线程 {thread.id} 跟进时间: {follow_up_at}")
        
        return result
    
    def update_thread_status(
        self, 
        thread: Thread, 
        now: Optional[datetime] = None
    ) -> Tuple[Thread, bool]:
        """
        更新会话状态和时间点
        
        Args:
            thread: 会话对象
            now: 当前时间,默认为系统时间
        
        Returns:
            (更新后的thread, 是否发生变化)
        """
        if now is None:
            now = datetime.now()
        
        old_status = thread.status
        
        # 计算新状态
        new_status = self.compute_status(thread, now)
        
        # 计算时间点
        next_times = self.compute_next_times(thread, now)
        
        # 更新thread对象
        thread.status = new_status
        thread.sla_at = next_times['sla_at']
        thread.follow_up_at = next_times['follow_up_at']
        thread.updated_at = now
        
        changed = old_status != new_status
        
        if changed:
            logger.info(
                f"线程 {thread.id} 状态变化: {old_status.value} -> {new_status.value}"
            )
        
        return thread, changed
    
    def snooze(
        self, 
        thread: Thread, 
        snooze_minutes: int = 60,
        now: Optional[datetime] = None
    ) -> Thread:
        """
        推迟处理(Snooze)
        
        Args:
            thread: 会话对象
            snooze_minutes: 推迟时长(分钟)
            now: 当前时间,默认为系统时间
        
        Returns:
            更新后的thread
        """
        if now is None:
            now = datetime.now()
        
        thread.snooze_at = now + timedelta(minutes=snooze_minutes)
        thread.status = ThreadStatus.SNOOZED
        thread.updated_at = now
        
        logger.info(
            f"线程 {thread.id} 已推迟至 {thread.snooze_at}, "
            f"推迟 {snooze_minutes} 分钟"
        )
        
        return thread
    
    def resolve(
        self, 
        thread: Thread,
        now: Optional[datetime] = None
    ) -> Thread:
        """
        标记为已解决
        
        Args:
            thread: 会话对象
            now: 当前时间,默认为系统时间
        
        Returns:
            更新后的thread
        """
        if now is None:
            now = datetime.now()
        
        thread.status = ThreadStatus.RESOLVED
        thread.updated_at = now
        
        # 清除所有时间点
        thread.sla_at = None
        thread.snooze_at = None
        thread.follow_up_at = None
        
        logger.info(f"线程 {thread.id} 已标记为已解决")
        
        return thread
    
    def mark_waiting(
        self, 
        thread: Thread,
        follow_up_hours: Optional[int] = None,
        now: Optional[datetime] = None
    ) -> Thread:
        """
        标记为等待对方回复
        
        Args:
            thread: 会话对象
            follow_up_hours: 跟进小时数,如果为None则使用配置值
            now: 当前时间,默认为系统时间
        
        Returns:
            更新后的thread
        """
        if now is None:
            now = datetime.now()
        
        if follow_up_hours is None:
            follow_up_hours = self.sla_config.follow_up_hours
        
        thread.status = ThreadStatus.WAITING_THEM
        thread.last_speaker = Party.ME
        thread.last_msg_at = now
        thread.follow_up_at = now + timedelta(hours=follow_up_hours)
        thread.sla_at = None
        thread.updated_at = now
        
        logger.info(
            f"线程 {thread.id} 标记为等待对方, "
            f"跟进时间: {thread.follow_up_at}"
        )
        
        return thread


# ==================== 默认实例 ====================

# 默认SLA配置
DEFAULT_SLA = SLAConfig(
    unseen_minutes=0,
    need_reply_minutes=30,
    follow_up_hours=48
)

# 默认状态机实例
default_state_machine = StateMachine(DEFAULT_SLA)

