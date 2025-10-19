#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整集成示例：上下文管理 + 会话生命周期
展示如何将两个系统完美结合使用
"""

import logging
import time
from typing import Dict
from datetime import datetime

# 导入核心组件
from context_manager import ContextManager, DialogueType
from session_lifecycle import SessionLifecycleManager, SessionConfig, SessionState

try:
    from dialogue_handler_example import SmartDialogueHandler
except ImportError:
    SmartDialogueHandler = None

logger = logging.getLogger(__name__)


class EnhancedDialogueSystem:
    """增强型对话系统（集成上下文管理 + 会话生命周期）"""
    
    def __init__(self, kb_service=None, erp_client=None, llm_client=None):
        """
        初始化增强型对话系统
        
        Args:
            kb_service: 知识库服务
            erp_client: ERP客户端
            llm_client: LLM客户端
        """
        # 1. 上下文管理器
        self.context_mgr = ContextManager(
            max_age_minutes=30,
            hard_limit=20
        )
        
        # 2. 会话生命周期管理器
        session_config = SessionConfig(
            # 超时配置
            idle_timeout=5,
            dormant_timeout=15,
            expire_timeout=30,
            
            # 提示配置（温和友好）
            send_idle_prompt=True,
            send_dormant_prompt=False,
            send_expire_notice=False,
            
            idle_prompt="还在吗？如果需要帮助，随时告诉我哦~ 😊",
            
            # 按对话类型自定义超时
            custom_timeouts={
                '闲聊类': {
                    'idle': 2,
                    'dormant': 5,
                    'expire': 10
                },
                '咨询类': {
                    'idle': 5,
                    'dormant': 15,
                    'expire': 30
                },
                '业务类': {
                    'idle': 10,
                    'dormant': 20,
                    'expire': 60
                }
            }
        )
        
        self.session_mgr = SessionLifecycleManager(
            config=session_config,
            message_sender=self._send_message
        )
        
        # 3. 对话处理器
        if SmartDialogueHandler:
            self.dialogue_handler = SmartDialogueHandler(
                kb_service=kb_service,
                erp_client=erp_client,
                llm_client=llm_client
            )
        else:
            self.dialogue_handler = None
        
        # 4. 消息发送队列（用于延迟发送）
        self.message_queue = []
        
        # 启动会话监控
        self.session_mgr.start_monitoring()
        logger.info("✅ 增强型对话系统已启动")
    
    def process_message(self, contact_id: str, message: str) -> Dict:
        """
        处理消息（完整流程）
        
        Args:
            contact_id: 联系人ID
            message: 用户消息
        
        Returns:
            处理结果
        """
        start_time = datetime.now()
        
        # 1. 检查会话状态
        session_state = self.session_mgr.get_session_state(contact_id)
        is_new_session = self.session_mgr.is_new_session(
            contact_id,
            threshold_minutes=30
        )
        
        logger.info(
            f"[{contact_id}] 收到消息: {message[:30]}... "
            f"(会话状态: {session_state.value if session_state else '新会话'})"
        )
        
        # 2. 处理会话恢复
        recovery_message = None
        if is_new_session and session_state is not None:
            # 新会话开始
            recovery_message = "欢迎！有什么可以帮您的吗？😊"
        elif session_state == SessionState.DORMANT:
            # 从休眠恢复
            summary = self.session_mgr.get_session_summary(contact_id)
            recovery_message = f"欢迎回来！{summary}"
        elif session_state == SessionState.EXPIRED:
            # 从过期恢复
            recovery_message = "好久不见！有什么可以帮您的吗？"
        
        if recovery_message:
            self._send_message(contact_id, recovery_message)
        
        # 3. 处理消息（使用对话处理器）
        if self.dialogue_handler:
            result = self.dialogue_handler.process_message(contact_id, message)
        else:
            # 降级处理：简单回复
            result = {
                'response': "收到您的消息！",
                'type': '未知类',
                'subtype': None,
                'action': 'simple_response',
                'confidence': 0.0,
                'context_length': 0,
                'topic_changed': False,
                'processing_time': 0.0
            }
        
        # 4. 更新会话活动
        self.session_mgr.update_activity(
            contact_id,
            dialogue_type=result['type'],
            metadata={
                'subtype': result['subtype'],
                'topic_changed': result['topic_changed']
            }
        )
        
        # 5. 处理主题切换
        if result.get('topic_changed'):
            logger.info(f"[{contact_id}] 检测到主题切换，标记新会话段落")
            # 可以在这里添加分段标记（用于内部分析）
        
        # 6. 发送回复
        self._send_message(contact_id, result['response'])
        
        # 7. 添加统计信息
        processing_time = (datetime.now() - start_time).total_seconds()
        result.update({
            'session_state': session_state.value if session_state else '新会话',
            'is_new_session': is_new_session,
            'total_processing_time': processing_time
        })
        
        logger.info(
            f"[{contact_id}] 处理完成: type={result['type']}, "
            f"state={result['session_state']}, time={processing_time:.3f}s"
        )
        
        return result
    
    def _send_message(self, contact_id: str, message: str):
        """
        发送消息（这里是占位函数，实际应该调用微信发送接口）
        
        Args:
            contact_id: 联系人ID
            message: 消息内容
        """
        # 记录到队列（实际使用时替换为真实的微信发送）
        self.message_queue.append({
            'contact_id': contact_id,
            'message': message,
            'timestamp': datetime.now()
        })
        
        print(f"📤 [{contact_id}] {message}")
    
    def get_statistics(self) -> Dict:
        """获取系统统计信息"""
        # 会话统计
        session_stats = {
            'total_sessions': len(self.session_mgr.sessions),
            'active': sum(1 for s in self.session_mgr.sessions.values() 
                         if s['state'] == SessionState.ACTIVE),
            'idle': sum(1 for s in self.session_mgr.sessions.values() 
                       if s['state'] == SessionState.IDLE),
            'dormant': sum(1 for s in self.session_mgr.sessions.values() 
                          if s['state'] == SessionState.DORMANT),
            'expired': sum(1 for s in self.session_mgr.sessions.values() 
                          if s['state'] == SessionState.EXPIRED)
        }
        
        # 上下文统计
        context_stats = {
            'total_conversations': len(self.context_mgr.conversations),
            'avg_context_length': sum(
                len(msgs) for msgs in self.context_mgr.conversations.values()
            ) / len(self.context_mgr.conversations) if self.context_mgr.conversations else 0
        }
        
        # 消息统计
        message_stats = {
            'total_sent': len(self.message_queue),
            'recent_10': self.message_queue[-10:] if self.message_queue else []
        }
        
        return {
            'sessions': session_stats,
            'context': context_stats,
            'messages': message_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup_and_stop(self):
        """清理资源并停止"""
        # 清理过期会话
        cleaned = self.session_mgr.cleanup_expired()
        logger.info(f"清理了 {cleaned} 个过期会话")
        
        # 清理过期上下文
        cleaned_ctx = self.context_mgr.cleanup_expired()
        logger.info(f"清理了 {cleaned_ctx} 个过期上下文")
        
        # 停止监控
        self.session_mgr.stop_monitoring()
        logger.info("✅ 系统已停止")


# ==================== 测试示例 ====================

def simulate_conversation_scenarios():
    """模拟各种对话场景"""
    
    print("\n" + "=" * 70)
    print("🚀 增强型对话系统测试")
    print("=" * 70 + "\n")
    
    # 初始化系统
    system = EnhancedDialogueSystem()
    
    contact_id = "wx_test_user"
    
    # ========== 场景1: 正常对话 ==========
    print("\n📋 场景1: 正常对话流程")
    print("-" * 70)
    
    scenarios = [
        ("你好", "闲聊"),
        ("你们的充电桩支持多少功率？", "产品咨询"),
        ("安装需要什么条件？", "咨询延续"),
        ("价格多少？", "价格咨询"),
    ]
    
    for i, (msg, desc) in enumerate(scenarios, 1):
        print(f"\n第{i}轮 - {desc}")
        print(f"👤 用户: {msg}")
        
        result = system.process_message(contact_id, msg)
        
        print(f"🤖 AI: {result['response'][:80]}...")
        print(f"📊 类型: {result['type']} | "
              f"上下文: {result['context_length']}轮 | "
              f"会话: {result['session_state']}")
        
        time.sleep(0.5)  # 模拟对话间隔
    
    # ========== 场景2: 主题切换 ==========
    print("\n\n📋 场景2: 主题切换")
    print("-" * 70)
    
    msg = "对了，我想查一下订单WX20250119001的物流"
    print(f"\n👤 用户: {msg}")
    
    result = system.process_message(contact_id, msg)
    
    print(f"🤖 AI: {result['response'][:80]}...")
    print(f"📊 主题切换: {'✅ 是' if result['topic_changed'] else '❌ 否'} | "
          f"类型: {result['type']}")
    
    # ========== 场景3: 会话状态展示 ==========
    print("\n\n📋 场景3: 会话状态统计")
    print("-" * 70)
    
    stats = system.get_statistics()
    
    print(f"\n会话统计:")
    print(f"  - 总会话数: {stats['sessions']['total_sessions']}")
    print(f"  - 活跃: {stats['sessions']['active']}")
    print(f"  - 空闲: {stats['sessions']['idle']}")
    print(f"  - 休眠: {stats['sessions']['dormant']}")
    
    print(f"\n上下文统计:")
    print(f"  - 对话数: {stats['context']['total_conversations']}")
    print(f"  - 平均长度: {stats['context']['avg_context_length']:.1f}轮")
    
    print(f"\n消息统计:")
    print(f"  - 发送总数: {stats['messages']['total_sent']}")
    
    # ========== 场景4: 模拟超时（简化演示） ==========
    print("\n\n📋 场景4: 会话生命周期（简化演示）")
    print("-" * 70)
    
    print("\n💡 实际使用中：")
    print("  - 5分钟无消息 → 空闲状态，发送温和提示")
    print("  - 15分钟无消息 → 休眠状态，后台标记")
    print("  - 30分钟无消息 → 过期状态，清理上下文")
    print("\n  （由于演示限制，这里不等待真实时间）")
    
    # 获取会话信息
    session_info = system.session_mgr.get_session_info(contact_id)
    if session_info:
        print(f"\n当前会话信息:")
        print(f"  - 创建时间: {session_info['created_at'].strftime('%H:%M:%S')}")
        print(f"  - 消息数: {session_info['message_count']}")
        print(f"  - 当前状态: {session_info['state'].value}")
        print(f"  - 对话类型: {session_info['dialogue_type']}")
    
    # ========== 清理 ==========
    print("\n\n🧹 清理资源...")
    system.cleanup_and_stop()
    
    print("\n✅ 测试完成！")
    print("=" * 70 + "\n")


def show_usage_example():
    """展示实际使用示例代码"""
    
    print("\n" + "=" * 70)
    print("📖 实际使用示例")
    print("=" * 70 + "\n")
    
    example_code = '''
# 1. 初始化系统
from conversation_context.complete_integration_example import EnhancedDialogueSystem

system = EnhancedDialogueSystem(
    kb_service=your_kb_service,
    erp_client=your_erp_client,
    llm_client=your_llm_client
)

# 2. 处理微信消息
def on_wechat_message(contact_id, message):
    """微信消息回调"""
    result = system.process_message(contact_id, message)
    
    # 系统会自动：
    # - 检测会话状态
    # - 管理上下文
    # - 检测主题切换
    # - 发送超时提示
    # - 返回AI回复
    
    return result

# 3. 定期清理（建议每小时执行一次）
@scheduler.task('interval', hours=1)
def cleanup_task():
    system.cleanup_and_stop()

# 4. 查看统计
stats = system.get_statistics()
print(f"活跃会话: {stats['sessions']['active']}")
'''
    
    print(example_code)


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    simulate_conversation_scenarios()
    
    # 展示使用示例
    show_usage_example()

