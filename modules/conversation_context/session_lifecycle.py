#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能会话生命周期管理
支持多级超时、温和提示、自动清理
"""

import logging
from enum import Enum
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading
import time

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """会话状态"""
    ACTIVE = "活跃中"           # 正在对话
    IDLE = "空闲中"             # 短时间无消息
    DORMANT = "休眠中"          # 较长时间无消息
    EXPIRED = "已过期"          # 超过最大时间，需要清理
    CLOSED = "已关闭"           # 用户主动结束


@dataclass
class SessionConfig:
    """会话配置"""
    # 超时时间（分钟）
    idle_timeout: int = 5           # 空闲超时（触发温和提示）
    dormant_timeout: int = 15       # 休眠超时（后台标记，不提示）
    expire_timeout: int = 30        # 过期超时（清理上下文）
    
    # 提示配置
    send_idle_prompt: bool = True   # 是否发送空闲提示
    send_dormant_prompt: bool = False  # 是否发送休眠提示
    send_expire_notice: bool = False   # 是否发送过期通知
    
    # 提示内容
    idle_prompt: str = "还在吗？如果需要帮助，随时告诉我哦~ 😊"
    dormant_prompt: str = "已经一段时间没有消息了，我会在这里等您~ 有需要随时找我！"
    expire_notice: str = "很久没有您的消息了，本次会话已结束。下次需要帮助时再来找我吧！👋"
    
    # 根据对话类型使用不同超时
    custom_timeouts: Dict[str, Dict[str, int]] = None


class SessionLifecycleManager:
    """会话生命周期管理器"""
    
    def __init__(self, config: SessionConfig = None, 
                 message_sender: Callable = None):
        """
        初始化会话生命周期管理器
        
        Args:
            config: 会话配置
            message_sender: 消息发送函数 func(contact_id, message)
        """
        self.config = config or SessionConfig()
        self.message_sender = message_sender
        
        # 会话状态追踪
        self.sessions = {}  # {contact_id: SessionInfo}
        
        # 启动后台监控线程
        self._running = False
        self._monitor_thread = None
        
    def start_monitoring(self):
        """启动后台监控"""
        if self._running:
            logger.warning("监控线程已经在运行")
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_sessions,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("会话生命周期监控已启动")
    
    def stop_monitoring(self):
        """停止后台监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("会话生命周期监控已停止")
    
    def update_activity(self, contact_id: str, 
                       dialogue_type: str = None,
                       metadata: Dict = None):
        """
        更新会话活动时间
        
        Args:
            contact_id: 联系人ID
            dialogue_type: 对话类型（用于自定义超时）
            metadata: 附加元数据
        """
        now = datetime.now()
        
        if contact_id not in self.sessions:
            # 新会话
            self.sessions[contact_id] = {
                'contact_id': contact_id,
                'state': SessionState.ACTIVE,
                'dialogue_type': dialogue_type,
                'created_at': now,
                'last_activity': now,
                'last_state_change': now,
                'idle_prompted': False,
                'dormant_prompted': False,
                'message_count': 0,
                'metadata': metadata or {}
            }
            logger.info(f"[{contact_id}] 新会话创建")
        else:
            # 更新现有会话
            session = self.sessions[contact_id]
            
            # 如果从休眠/过期状态恢复，记录日志
            if session['state'] in [SessionState.DORMANT, SessionState.EXPIRED]:
                logger.info(
                    f"[{contact_id}] 会话从 {session['state'].value} "
                    f"恢复到 {SessionState.ACTIVE.value}"
                )
            
            session['state'] = SessionState.ACTIVE
            session['last_activity'] = now
            session['last_state_change'] = now
            session['dialogue_type'] = dialogue_type or session.get('dialogue_type')
            session['message_count'] = session.get('message_count', 0) + 1
            
            # 重置提示标记
            session['idle_prompted'] = False
            session['dormant_prompted'] = False
    
    def get_session_state(self, contact_id: str) -> Optional[SessionState]:
        """获取会话状态"""
        if contact_id not in self.sessions:
            return None
        return self.sessions[contact_id]['state']
    
    def get_session_info(self, contact_id: str) -> Optional[Dict]:
        """获取会话完整信息"""
        return self.sessions.get(contact_id)
    
    def is_new_session(self, contact_id: str, 
                      threshold_minutes: int = None) -> bool:
        """
        判断是否是新会话
        
        Args:
            contact_id: 联系人ID
            threshold_minutes: 判断阈值（分钟），超过此时间算新会话
        
        Returns:
            True表示新会话
        """
        if contact_id not in self.sessions:
            return True
        
        session = self.sessions[contact_id]
        
        # 已关闭/过期的算新会话
        if session['state'] in [SessionState.CLOSED, SessionState.EXPIRED]:
            return True
        
        # 检查时间间隔
        if threshold_minutes:
            threshold = timedelta(minutes=threshold_minutes)
            time_since_last = datetime.now() - session['last_activity']
            return time_since_last > threshold
        
        return False
    
    def close_session(self, contact_id: str, 
                     reason: str = "user_initiated",
                     send_notice: bool = False):
        """
        关闭会话
        
        Args:
            contact_id: 联系人ID
            reason: 关闭原因
            send_notice: 是否发送通知
        """
        if contact_id not in self.sessions:
            return
        
        session = self.sessions[contact_id]
        session['state'] = SessionState.CLOSED
        session['last_state_change'] = datetime.now()
        session['close_reason'] = reason
        
        logger.info(f"[{contact_id}] 会话已关闭，原因: {reason}")
        
        if send_notice and self.message_sender:
            self.message_sender(
                contact_id,
                "本次会话已结束，感谢您的咨询！有需要随时找我~ 👋"
            )
    
    def cleanup_expired(self) -> int:
        """清理过期会话"""
        now = datetime.now()
        expired_contacts = []
        
        for contact_id, session in self.sessions.items():
            # 已关闭的会话，超过1小时后删除
            if session['state'] == SessionState.CLOSED:
                if now - session['last_state_change'] > timedelta(hours=1):
                    expired_contacts.append(contact_id)
            
            # 过期会话，超过清理时间后删除
            elif session['state'] == SessionState.EXPIRED:
                # 过期后再保留1小时，然后删除
                if now - session['last_state_change'] > timedelta(hours=1):
                    expired_contacts.append(contact_id)
        
        for contact_id in expired_contacts:
            del self.sessions[contact_id]
            logger.info(f"[{contact_id}] 会话已清理")
        
        return len(expired_contacts)
    
    def get_session_summary(self, contact_id: str) -> str:
        """获取会话摘要（用于恢复时展示）"""
        if contact_id not in self.sessions:
            return "这是新对话的开始。"
        
        session = self.sessions[contact_id]
        
        # 计算会话时长
        duration = datetime.now() - session['created_at']
        duration_str = self._format_duration(duration)
        
        # 计算空闲时长
        idle_duration = datetime.now() - session['last_activity']
        idle_str = self._format_duration(idle_duration)
        
        parts = [
            f"上次会话: {duration_str}前开始",
            f"消息数: {session.get('message_count', 0)}条",
            f"空闲时长: {idle_str}"
        ]
        
        if session.get('dialogue_type'):
            parts.append(f"对话类型: {session['dialogue_type']}")
        
        return " | ".join(parts)
    
    def _monitor_sessions(self):
        """后台监控会话状态（在独立线程中运行）"""
        logger.info("会话监控线程启动")
        
        while self._running:
            try:
                self._check_all_sessions()
            except Exception as e:
                logger.error(f"会话监控出错: {e}", exc_info=True)
            
            # 每30秒检查一次
            time.sleep(30)
        
        logger.info("会话监控线程停止")
    
    def _check_all_sessions(self):
        """检查所有会话的状态"""
        now = datetime.now()
        
        for contact_id, session in list(self.sessions.items()):
            # 跳过已关闭的会话
            if session['state'] == SessionState.CLOSED:
                continue
            
            # 计算空闲时长
            idle_time = (now - session['last_activity']).total_seconds() / 60
            
            # 获取超时配置（支持按对话类型自定义）
            timeouts = self._get_timeouts(session.get('dialogue_type'))
            
            # 检查是否过期
            if idle_time >= timeouts['expire']:
                if session['state'] != SessionState.EXPIRED:
                    self._transition_to_expired(contact_id, session)
            
            # 检查是否休眠
            elif idle_time >= timeouts['dormant']:
                if session['state'] != SessionState.DORMANT:
                    self._transition_to_dormant(contact_id, session)
            
            # 检查是否空闲
            elif idle_time >= timeouts['idle']:
                if session['state'] != SessionState.IDLE:
                    self._transition_to_idle(contact_id, session)
    
    def _get_timeouts(self, dialogue_type: str = None) -> Dict[str, int]:
        """获取超时配置"""
        # 默认超时
        timeouts = {
            'idle': self.config.idle_timeout,
            'dormant': self.config.dormant_timeout,
            'expire': self.config.expire_timeout
        }
        
        # 自定义超时（按对话类型）
        if dialogue_type and self.config.custom_timeouts:
            custom = self.config.custom_timeouts.get(dialogue_type, {})
            timeouts.update(custom)
        
        return timeouts
    
    def _transition_to_idle(self, contact_id: str, session: Dict):
        """转换到空闲状态"""
        session['state'] = SessionState.IDLE
        session['last_state_change'] = datetime.now()
        
        logger.info(f"[{contact_id}] 会话进入空闲状态")
        
        # 发送温和提示（只发一次）
        if self.config.send_idle_prompt and not session['idle_prompted']:
            if self.message_sender:
                self.message_sender(contact_id, self.config.idle_prompt)
                session['idle_prompted'] = True
                logger.info(f"[{contact_id}] 已发送空闲提示")
    
    def _transition_to_dormant(self, contact_id: str, session: Dict):
        """转换到休眠状态"""
        session['state'] = SessionState.DORMANT
        session['last_state_change'] = datetime.now()
        
        logger.info(f"[{contact_id}] 会话进入休眠状态")
        
        # 发送休眠提示（可选）
        if self.config.send_dormant_prompt and not session['dormant_prompted']:
            if self.message_sender:
                self.message_sender(contact_id, self.config.dormant_prompt)
                session['dormant_prompted'] = True
                logger.info(f"[{contact_id}] 已发送休眠提示")
    
    def _transition_to_expired(self, contact_id: str, session: Dict):
        """转换到过期状态"""
        session['state'] = SessionState.EXPIRED
        session['last_state_change'] = datetime.now()
        
        logger.info(f"[{contact_id}] 会话已过期")
        
        # 发送过期通知（可选）
        if self.config.send_expire_notice:
            if self.message_sender:
                self.message_sender(contact_id, self.config.expire_notice)
                logger.info(f"[{contact_id}] 已发送过期通知")
    
    @staticmethod
    def _format_duration(duration: timedelta) -> str:
        """格式化时长"""
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}秒"
        elif total_seconds < 3600:
            return f"{total_seconds // 60}分钟"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"
        else:
            days = total_seconds // 86400
            return f"{days}天"


# ==================== 使用示例 ====================

def example_message_sender(contact_id: str, message: str):
    """示例消息发送函数"""
    print(f"📤 发送给 {contact_id}: {message}")


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建自定义配置
    config = SessionConfig(
        idle_timeout=2,      # 测试用：2分钟空闲
        dormant_timeout=5,   # 测试用：5分钟休眠
        expire_timeout=10,   # 测试用：10分钟过期
        send_idle_prompt=True,
        send_dormant_prompt=False,
        send_expire_notice=True,
        # 按对话类型自定义超时
        custom_timeouts={
            '业务类': {
                'idle': 3,      # 业务类3分钟空闲
                'dormant': 10,  # 10分钟休眠
                'expire': 30    # 30分钟过期
            },
            '闲聊类': {
                'idle': 1,      # 闲聊类1分钟空闲
                'dormant': 3,   # 3分钟休眠
                'expire': 5     # 5分钟过期
            }
        }
    )
    
    # 初始化管理器
    manager = SessionLifecycleManager(
        config=config,
        message_sender=example_message_sender
    )
    
    # 启动监控
    manager.start_monitoring()
    
    print("\n" + "=" * 60)
    print("会话生命周期管理器测试")
    print("=" * 60 + "\n")
    
    # 模拟会话
    contact_id = "wx_test_user"
    
    # 第1条消息
    print("📨 用户发送消息: 你好")
    manager.update_activity(contact_id, dialogue_type='闲聊类')
    print(f"   状态: {manager.get_session_state(contact_id).value}\n")
    
    # 第2条消息
    print("📨 用户发送消息: 你们的产品怎么样？")
    manager.update_activity(contact_id, dialogue_type='咨询类')
    print(f"   状态: {manager.get_session_state(contact_id).value}\n")
    
    # 查看会话信息
    info = manager.get_session_info(contact_id)
    print(f"📊 会话信息:")
    print(f"   - 创建时间: {info['created_at'].strftime('%H:%M:%S')}")
    print(f"   - 消息数: {info['message_count']}")
    print(f"   - 当前状态: {info['state'].value}")
    print(f"   - 对话类型: {info['dialogue_type']}\n")
    
    # 获取摘要
    summary = manager.get_session_summary(contact_id)
    print(f"📝 会话摘要: {summary}\n")
    
    # 判断是否新会话
    is_new = manager.is_new_session(contact_id, threshold_minutes=1)
    print(f"❓ 是否新会话: {is_new}\n")
    
    print("💡 监控线程正在后台运行...")
    print("   - 2分钟后会话将进入空闲状态")
    print("   - 5分钟后会话将进入休眠状态")
    print("   - 10分钟后会话将过期\n")
    
    # 模拟等待（实际使用时不需要）
    print("⏳ 等待30秒查看状态变化...\n")
    time.sleep(30)
    
    # 查看状态
    current_state = manager.get_session_state(contact_id)
    print(f"📊 当前状态: {current_state.value}\n")
    
    # 停止监控
    print("🛑 停止监控...")
    manager.stop_monitoring()
    
    print("\n✅ 测试完成")

