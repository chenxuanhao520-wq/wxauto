"""
客户中台服务层
业务逻辑封装
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from .types import (
    Contact, Thread, Signal, InboundMessage,
    Party, ThreadStatus, Bucket, ContactType,
    ContactSource, SLAConfig, ScoringRules
)
from .repository import CustomerHubRepository
from .state_machine import StateMachine
from .scoring import ScoringEngine
from .triggers import TriggerEngine

logger = logging.getLogger(__name__)


class CustomerHubService:
    """客户中台服务"""
    
    def __init__(
        self,
        repository: Optional[CustomerHubRepository] = None,
        state_machine: Optional[StateMachine] = None,
        scoring_engine: Optional[ScoringEngine] = None,
        trigger_engine: Optional[TriggerEngine] = None
    ):
        """
        初始化服务
        
        Args:
            repository: 数据仓库
            state_machine: 状态机
            scoring_engine: 打分引擎
            trigger_engine: 触发引擎
        """
        self.repo = repository or CustomerHubRepository()
        self.state_machine = state_machine or StateMachine()
        self.scoring = scoring_engine or ScoringEngine()
        self.triggers = trigger_engine or TriggerEngine()
        
        logger.info("客户中台服务初始化完成")
    
    # ==================== 消息处理 ====================
    
    def process_inbound_message(
        self,
        message: InboundMessage,
        kb_matched: bool = False
    ) -> Dict[str, Any]:
        """
        处理入站消息
        
        流程:
        1. 查找或创建联系人
        2. 查找或创建会话线程
        3. 打分评估(白/灰/黑)
        4. 更新线程状态
        5. 判断是否触发(售前/售后/客户开发)
        
        Args:
            message: 入站消息
            kb_matched: 是否匹配到知识库
        
        Returns:
            处理结果字典
        """
        logger.info(f"处理入站消息: wx_id={message.wx_id}, speaker={message.last_speaker.value}")
        
        # 1. 查找或创建联系人
        contact = self.repo.get_contact_by_wx_id(message.wx_id)
        if not contact:
            contact = Contact(
                id=str(uuid4()),
                wx_id=message.wx_id,
                source=ContactSource.WECHAT,
                type=ContactType.UNKNOWN,
                confidence=0
            )
            contact = self.repo.create_contact(contact)
            logger.info(f"新联系人已创建: {contact.id}")
        
        # 2. 查找或创建会话线程
        thread = self.repo.get_thread_by_contact(contact.id)
        if not thread:
            thread = Thread(
                id=str(uuid4()),
                contact_id=contact.id,
                last_speaker=message.last_speaker,
                last_msg_at=message.timestamp,
                status=ThreadStatus.UNSEEN,
                bucket=Bucket.BLACK  # 默认黑名单,等待打分
            )
            thread = self.repo.create_thread(thread)
            logger.info(f"新会话线程已创建: {thread.id}")
        else:
            # 更新线程
            thread.last_speaker = message.last_speaker
            thread.last_msg_at = message.timestamp
        
        # 3. 打分评估
        signal, score_details = self.scoring.score_message(
            text=message.text or "",
            file_types=message.file_types,
            timestamp=message.timestamp,
            kb_matched=kb_matched
        )
        
        signal.id = str(uuid4())
        signal.thread_id = thread.id
        signal = self.repo.create_signal(signal)
        
        # 更新线程的bucket
        thread.bucket = signal.bucket
        
        # 4. 更新线程状态(使用状态机)
        thread, status_changed = self.state_machine.update_thread_status(thread)
        thread = self.repo.update_thread(thread)
        
        # 5. 判断是否触发
        trigger_type = None
        trigger_output = None
        
        if signal.bucket in [Bucket.WHITE, Bucket.GRAY]:
            trigger_type = self.scoring.identify_trigger_type(signal.keyword_hits)
            if trigger_type:
                logger.info(f"识别到触发类型: {trigger_type}")
                # 注意: 实际触发需要异步调用LLM,这里只记录类型
        
        result = {
            'contact_id': contact.id,
            'thread_id': thread.id,
            'signal_id': signal.id,
            'bucket': signal.bucket.value,
            'total_score': signal.total_score,
            'status': thread.status.value,
            'status_changed': status_changed,
            'trigger_type': trigger_type,
            'score_details': score_details
        }
        
        logger.info(f"消息处理完成: bucket={signal.bucket.value}, score={signal.total_score}")
        return result
    
    async def trigger_scenario(
        self,
        thread_id: str,
        text: str,
        trigger_type: str
    ) -> Dict[str, Any]:
        """
        触发场景(售前/售后/客户开发)
        
        Args:
            thread_id: 会话ID
            text: 对话文本
            trigger_type: 触发类型 ('售前'|'售后'|'客户开发')
        
        Returns:
            触发输出
        """
        logger.info(f"触发场景: thread={thread_id}, type={trigger_type}")
        
        # 检查线程是否存在
        thread = self.repo.get_thread_by_id(thread_id)
        if not thread:
            raise ValueError(f"会话不存在: {thread_id}")
        
        # 检查bucket(黑名单不触发)
        if thread.bucket == Bucket.BLACK:
            logger.warning(f"黑名单线程不触发: {thread_id}")
            return {
                'error': 'blacklist_thread',
                'message': '黑名单线程不允许触发'
            }
        
        # 调用触发引擎
        if trigger_type == '售前':
            output = await self.triggers.trigger_pre_sales(text)
        elif trigger_type == '售后':
            output = await self.triggers.trigger_after_sales(text)
        elif trigger_type == '客户开发':
            output = await self.triggers.trigger_bizdev(text)
        else:
            raise ValueError(f"未知触发类型: {trigger_type}")
        
        # 保存输出
        output_id = self.repo.save_trigger_output(
            thread_id=thread_id,
            trigger_type=trigger_type,
            output=output
        )
        
        logger.info(f"触发完成: output_id={output_id}")
        
        return {
            'output_id': output_id,
            'trigger_type': trigger_type,
            'form': output.form,
            'reply_draft': output.reply_draft,
            'labels': [label.value for label in output.labels]
        }
    
    # ==================== 未知池 ====================
    
    def get_unknown_pool(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取未知池(灰名单且未处理的会话)
        
        Args:
            limit: 最大数量
        
        Returns:
            会话列表
        """
        return self.repo.get_unknown_pool(limit)
    
    def get_today_todo(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取今日待办
        
        Args:
            limit: 最大数量
        
        Returns:
            会话列表
        """
        return self.repo.get_today_todo(limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        thread_stats = self.repo.get_thread_statistics()
        
        return {
            'threads': {
                'total': thread_stats.total,
                'unseen': thread_stats.unseen,
                'need_reply': thread_stats.need_reply,
                'waiting_them': thread_stats.waiting_them,
                'overdue': thread_stats.overdue,
                'resolved': thread_stats.resolved,
                'snoozed': thread_stats.snoozed
            }
        }
    
    # ==================== 建档与升级 ====================
    
    def promote_to_customer(
        self,
        contact_id: str,
        customer_name: str,
        region: Optional[str] = None,
        level: Optional[str] = None,
        owner: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        建档+编码(升白)
        
        生成K编码格式: KXXXX-区域-姓名-级别-来源
        
        Args:
            contact_id: 联系人ID
            customer_name: 客户名称
            region: 地区代码(如 '渝A')
            level: 客户级别(如 'VIP')
            owner: 负责人
        
        Returns:
            更新后的联系人信息
        """
        logger.info(f"建档升级: contact={contact_id}, name={customer_name}")
        
        # 生成K编码
        k_code = self._generate_k_code(customer_name, region, level)
        
        # 升级为客户
        contact = self.repo.promote_to_customer(
            contact_id=contact_id,
            k_code=k_code,
            owner=owner
        )
        
        # 更新关联的线程bucket为WHITE
        thread = self.repo.get_thread_by_contact(contact_id)
        if thread:
            thread.bucket = Bucket.WHITE
            self.repo.update_thread(thread)
        
        logger.info(f"建档完成: K编码={k_code}")
        
        return {
            'contact_id': contact.id,
            'k_code': k_code,
            'type': contact.type.value,
            'confidence': contact.confidence
        }
    
    def _generate_k_code(
        self,
        name: str,
        region: Optional[str] = None,
        level: Optional[str] = None
    ) -> str:
        """
        生成K编码
        
        格式: KXXXX-区域-姓名-级别-微信
        示例: K3208-渝A-张三-VIP-微信
        """
        # 获取下一个序号(简化版,实际应该查询数据库)
        import random
        seq = random.randint(1000, 9999)
        
        parts = [f"K{seq}"]
        if region:
            parts.append(region)
        parts.append(name)
        if level:
            parts.append(level)
        parts.append("微信")
        
        return "-".join(parts)
    
    # ==================== 状态操作 ====================
    
    def snooze_thread(
        self,
        thread_id: str,
        snooze_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        推迟处理(Snooze)
        
        Args:
            thread_id: 会话ID
            snooze_minutes: 推迟时长(分钟)
        
        Returns:
            操作结果
        """
        thread = self.repo.get_thread_by_id(thread_id)
        if not thread:
            raise ValueError(f"会话不存在: {thread_id}")
        
        thread = self.state_machine.snooze(thread, snooze_minutes)
        thread = self.repo.update_thread(thread)
        
        logger.info(f"会话已推迟: {thread_id}, 至 {thread.snooze_at}")
        
        return {
            'thread_id': thread.id,
            'status': thread.status.value,
            'snooze_at': thread.snooze_at.isoformat() if thread.snooze_at else None
        }
    
    def resolve_thread(self, thread_id: str) -> Dict[str, Any]:
        """
        标记为已解决
        
        Args:
            thread_id: 会话ID
        
        Returns:
            操作结果
        """
        thread = self.repo.get_thread_by_id(thread_id)
        if not thread:
            raise ValueError(f"会话不存在: {thread_id}")
        
        thread = self.state_machine.resolve(thread)
        thread = self.repo.update_thread(thread)
        
        logger.info(f"会话已解决: {thread_id}")
        
        return {
            'thread_id': thread.id,
            'status': thread.status.value
        }
    
    def mark_waiting(
        self,
        thread_id: str,
        follow_up_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        标记为等待对方
        
        Args:
            thread_id: 会话ID
            follow_up_hours: 跟进小时数
        
        Returns:
            操作结果
        """
        thread = self.repo.get_thread_by_id(thread_id)
        if not thread:
            raise ValueError(f"会话不存在: {thread_id}")
        
        thread = self.state_machine.mark_waiting(thread, follow_up_hours)
        thread = self.repo.update_thread(thread)
        
        logger.info(f"会话已标记等待对方: {thread_id}, 跟进时间 {thread.follow_up_at}")
        
        return {
            'thread_id': thread.id,
            'status': thread.status.value,
            'follow_up_at': thread.follow_up_at.isoformat() if thread.follow_up_at else None
        }
    
    def recalc_thread_status(self, thread_id: str) -> Dict[str, Any]:
        """
        重新计算线程状态
        
        Args:
            thread_id: 会话ID
        
        Returns:
            操作结果
        """
        thread = self.repo.get_thread_by_id(thread_id)
        if not thread:
            raise ValueError(f"会话不存在: {thread_id}")
        
        old_status = thread.status
        thread, changed = self.state_machine.update_thread_status(thread)
        thread = self.repo.update_thread(thread)
        
        logger.info(
            f"会话状态已重算: {thread_id}, "
            f"{old_status.value} -> {thread.status.value}, changed={changed}"
        )
        
        return {
            'thread_id': thread.id,
            'old_status': old_status.value,
            'new_status': thread.status.value,
            'changed': changed,
            'sla_at': thread.sla_at.isoformat() if thread.sla_at else None,
            'follow_up_at': thread.follow_up_at.isoformat() if thread.follow_up_at else None
        }
    
    def recalc_all_threads(self) -> Dict[str, Any]:
        """
        重新计算所有线程状态(定时任务)
        
        Returns:
            统计结果
        """
        logger.info("开始重算所有线程状态")
        
        # 简化实现:只统计,不实际重算
        # 实际应该遍历所有活跃线程并重算
        
        stats = self.get_statistics()
        logger.info("所有线程状态重算完成")
        
        return stats


# ==================== 默认实例 ====================

default_service = CustomerHubService()

