"""
数据访问层 - Repository Pattern
负责 Contact、Thread、Signal 的数据库操作
"""
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .types import (
    Contact, Thread, Signal, TriggerOutput, 
    ContactType, ContactSource, Party, ThreadStatus, 
    Bucket, TriggerLabel, ThreadStatistics
)

logger = logging.getLogger(__name__)


class CustomerHubRepository:
    """客户中台数据仓库"""
    
    def __init__(self, db_path: str = "data/data.db"):
        """
        初始化仓库
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        logger.info(f"数据仓库初始化: {db_path}")
    
    def connect(self) -> sqlite3.Connection:
        """建立数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self.conn.row_factory = sqlite3.Row
            logger.debug("数据库连接已建立")
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("数据库连接已关闭")
    
    # ==================== Contact 操作 ====================
    
    def create_contact(self, contact: Contact) -> Contact:
        """
        创建联系人
        
        Args:
            contact: Contact对象(id可为空,将自动生成)
        
        Returns:
            创建后的Contact对象(带id)
        """
        if not contact.id:
            contact.id = str(uuid4())
        
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contacts 
            (id, wx_id, remark, k_code, source, type, confidence, owner, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contact.id, contact.wx_id, contact.remark, contact.k_code,
            contact.source.value, contact.type.value, contact.confidence,
            contact.owner, contact.created_at, contact.updated_at
        ))
        
        conn.commit()
        logger.info(f"联系人已创建: {contact.id}, wx_id={contact.wx_id}")
        
        return contact
    
    def get_contact_by_id(self, contact_id: str) -> Optional[Contact]:
        """根据ID获取联系人"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_contact(row)
    
    def get_contact_by_wx_id(self, wx_id: str) -> Optional[Contact]:
        """根据微信ID获取联系人"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM contacts WHERE wx_id = ?", (wx_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_contact(row)
    
    def update_contact(self, contact: Contact) -> Contact:
        """更新联系人"""
        contact.updated_at = datetime.now()
        
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE contacts 
            SET remark = ?, k_code = ?, source = ?, type = ?, 
                confidence = ?, owner = ?, updated_at = ?
            WHERE id = ?
        """, (
            contact.remark, contact.k_code, contact.source.value,
            contact.type.value, contact.confidence, contact.owner,
            contact.updated_at, contact.id
        ))
        
        conn.commit()
        logger.info(f"联系人已更新: {contact.id}")
        
        return contact
    
    def promote_to_customer(
        self, 
        contact_id: str, 
        k_code: str, 
        owner: Optional[str] = None
    ) -> Contact:
        """
        升级为正式客户(建档)
        
        Args:
            contact_id: 联系人ID
            k_code: K编码
            owner: 负责人
        
        Returns:
            更新后的Contact
        """
        contact = self.get_contact_by_id(contact_id)
        if not contact:
            raise ValueError(f"联系人不存在: {contact_id}")
        
        contact.k_code = k_code
        contact.type = ContactType.CUSTOMER
        contact.confidence = 100
        if owner:
            contact.owner = owner
        
        self.update_contact(contact)
        
        logger.info(f"联系人已升级为客户: {contact_id}, K编码={k_code}")
        return contact
    
    # ==================== Thread 操作 ====================
    
    def create_thread(self, thread: Thread) -> Thread:
        """
        创建会话线程
        
        Args:
            thread: Thread对象(id可为空,将自动生成)
        
        Returns:
            创建后的Thread对象(带id)
        """
        if not thread.id:
            thread.id = str(uuid4())
        
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO threads 
            (id, contact_id, last_speaker, last_msg_at, status, bucket,
             sla_at, snooze_at, follow_up_at, topic, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            thread.id, thread.contact_id, thread.last_speaker.value,
            thread.last_msg_at, thread.status.value, thread.bucket.value,
            thread.sla_at, thread.snooze_at, thread.follow_up_at,
            thread.topic, thread.created_at, thread.updated_at
        ))
        
        conn.commit()
        logger.info(f"会话线程已创建: {thread.id}, contact={thread.contact_id}")
        
        return thread
    
    def get_thread_by_id(self, thread_id: str) -> Optional[Thread]:
        """根据ID获取会话线程"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM threads WHERE id = ?", (thread_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_thread(row)
    
    def get_thread_by_contact(self, contact_id: str) -> Optional[Thread]:
        """
        根据联系人ID获取最新的会话线程
        
        Args:
            contact_id: 联系人ID
        
        Returns:
            最新的Thread对象,如果不存在则返回None
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM threads 
            WHERE contact_id = ? 
            ORDER BY last_msg_at DESC 
            LIMIT 1
        """, (contact_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_thread(row)
    
    def update_thread(self, thread: Thread) -> Thread:
        """更新会话线程"""
        thread.updated_at = datetime.now()
        
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE threads 
            SET last_speaker = ?, last_msg_at = ?, status = ?, bucket = ?,
                sla_at = ?, snooze_at = ?, follow_up_at = ?, topic = ?, updated_at = ?
            WHERE id = ?
        """, (
            thread.last_speaker.value, thread.last_msg_at, 
            thread.status.value, thread.bucket.value,
            thread.sla_at, thread.snooze_at, thread.follow_up_at,
            thread.topic, thread.updated_at, thread.id
        ))
        
        conn.commit()
        logger.info(f"会话线程已更新: {thread.id}, status={thread.status.value}")
        
        return thread
    
    def get_unknown_pool(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取未知池(灰名单且未处理/需回复的会话)
        
        Args:
            limit: 最大数量
        
        Returns:
            会话列表(包含联系人和信号信息)
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT * FROM unknown_pool 
            LIMIT {limit}
        """)
        
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'thread_id': row['id'],
                'contact_id': row['contact_id'],
                'wx_id': row['wx_id'],
                'remark': row['remark'],
                'last_speaker': row['last_speaker'],
                'last_msg_at': row['last_msg_at'],
                'status': row['status'],
                'topic': row['topic'],
                'total_score': row['total_score'],
                'keyword_hits': json.loads(row['keyword_hits']) if row['keyword_hits'] else {},
                'file_types': json.loads(row['file_types']) if row['file_types'] else []
            })
        
        logger.info(f"未知池查询完成: {len(result)} 条记录")
        return result
    
    def get_today_todo(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取今日待办(所有未处理/需回复/逾期的会话)
        
        Args:
            limit: 最大数量
        
        Returns:
            会话列表
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT * FROM today_todo 
            LIMIT {limit}
        """)
        
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'thread_id': row['id'],
                'contact_id': row['contact_id'],
                'wx_id': row['wx_id'],
                'remark': row['remark'],
                'k_code': row['k_code'],
                'last_speaker': row['last_speaker'],
                'last_msg_at': row['last_msg_at'],
                'status': row['status'],
                'bucket': row['bucket'],
                'sla_at': row['sla_at'],
                'topic': row['topic'],
                'priority': row['priority']
            })
        
        logger.info(f"今日待办查询完成: {len(result)} 条记录")
        return result
    
    def get_thread_statistics(self) -> ThreadStatistics:
        """获取会话统计"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'UNSEEN' THEN 1 ELSE 0 END) as unseen,
                SUM(CASE WHEN status = 'NEED_REPLY' THEN 1 ELSE 0 END) as need_reply,
                SUM(CASE WHEN status = 'WAITING_THEM' THEN 1 ELSE 0 END) as waiting_them,
                SUM(CASE WHEN status = 'OVERDUE' THEN 1 ELSE 0 END) as overdue,
                SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN status = 'SNOOZED' THEN 1 ELSE 0 END) as snoozed
            FROM threads
        """)
        
        row = cursor.fetchone()
        
        return ThreadStatistics(
            total=row['total'] or 0,
            unseen=row['unseen'] or 0,
            need_reply=row['need_reply'] or 0,
            waiting_them=row['waiting_them'] or 0,
            overdue=row['overdue'] or 0,
            resolved=row['resolved'] or 0,
            snoozed=row['snoozed'] or 0
        )
    
    # ==================== Signal 操作 ====================
    
    def create_signal(self, signal: Signal) -> Signal:
        """
        创建信号/打分记录
        
        Args:
            signal: Signal对象(id可为空,将自动生成)
        
        Returns:
            创建后的Signal对象(带id)
        """
        if not signal.id:
            signal.id = str(uuid4())
        
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO signals 
            (id, thread_id, keyword_hits, file_types, worktime_score, 
             kb_match_score, total_score, bucket, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal.id, signal.thread_id,
            json.dumps(signal.keyword_hits, ensure_ascii=False),
            json.dumps(signal.file_types, ensure_ascii=False),
            signal.worktime_score, signal.kb_match_score,
            signal.total_score, signal.bucket.value, signal.created_at
        ))
        
        conn.commit()
        logger.info(
            f"信号已创建: {signal.id}, "
            f"thread={signal.thread_id}, score={signal.total_score}"
        )
        
        return signal
    
    def get_latest_signal(self, thread_id: str) -> Optional[Signal]:
        """获取线程的最新信号"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM signals 
            WHERE thread_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (thread_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_signal(row)
    
    # ==================== TriggerOutput 操作 ====================
    
    def save_trigger_output(
        self, 
        thread_id: str, 
        trigger_type: str,
        output: TriggerOutput,
        confidence: Optional[float] = None
    ) -> str:
        """
        保存触发器输出
        
        Args:
            thread_id: 会话ID
            trigger_type: 触发类型
            output: TriggerOutput对象
            confidence: 置信度
        
        Returns:
            输出ID
        """
        output_id = str(uuid4())
        
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trigger_outputs 
            (id, thread_id, trigger_type, form_data, reply_draft, labels, confidence, used, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
        """, (
            output_id, thread_id, trigger_type,
            json.dumps(output.form, ensure_ascii=False),
            output.reply_draft,
            ','.join([label.value for label in output.labels]),
            confidence, datetime.now()
        ))
        
        conn.commit()
        logger.info(f"触发器输出已保存: {output_id}, type={trigger_type}")
        
        return output_id
    
    def get_trigger_output(self, thread_id: str, used: bool = False) -> Optional[Dict[str, Any]]:
        """获取线程的最新触发器输出"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trigger_outputs 
            WHERE thread_id = ? AND used = ?
            ORDER BY created_at DESC 
            LIMIT 1
        """, (thread_id, 1 if used else 0))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            'id': row['id'],
            'thread_id': row['thread_id'],
            'trigger_type': row['trigger_type'],
            'form_data': json.loads(row['form_data']),
            'reply_draft': row['reply_draft'],
            'labels': row['labels'].split(',') if row['labels'] else [],
            'confidence': row['confidence'],
            'used': bool(row['used']),
            'created_at': row['created_at']
        }
    
    def mark_trigger_used(self, output_id: str):
        """标记触发器输出为已使用"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE trigger_outputs SET used = 1 WHERE id = ?",
            (output_id,)
        )
        
        conn.commit()
        logger.info(f"触发器输出已标记为已使用: {output_id}")
    
    # ==================== 辅助方法 ====================
    
    def _row_to_contact(self, row) -> Contact:
        """将数据库行转换为Contact对象"""
        return Contact(
            id=row['id'],
            wx_id=row['wx_id'],
            remark=row['remark'],
            k_code=row['k_code'],
            source=ContactSource(row['source']),
            type=ContactType(row['type']),
            confidence=row['confidence'],
            owner=row['owner'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.now()
        )
    
    def _row_to_thread(self, row) -> Thread:
        """将数据库行转换为Thread对象"""
        return Thread(
            id=row['id'],
            contact_id=row['contact_id'],
            last_speaker=Party(row['last_speaker']),
            last_msg_at=datetime.fromisoformat(row['last_msg_at']) if row['last_msg_at'] else datetime.now(),
            status=ThreadStatus(row['status']),
            bucket=Bucket(row['bucket']),
            sla_at=datetime.fromisoformat(row['sla_at']) if row['sla_at'] else None,
            snooze_at=datetime.fromisoformat(row['snooze_at']) if row['snooze_at'] else None,
            follow_up_at=datetime.fromisoformat(row['follow_up_at']) if row['follow_up_at'] else None,
            topic=row['topic'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.now()
        )
    
    def _row_to_signal(self, row) -> Signal:
        """将数据库行转换为Signal对象"""
        return Signal(
            id=row['id'],
            thread_id=row['thread_id'],
            keyword_hits=json.loads(row['keyword_hits']) if row['keyword_hits'] else {},
            file_types=json.loads(row['file_types']) if row['file_types'] else [],
            worktime_score=row['worktime_score'],
            kb_match_score=row['kb_match_score'],
            total_score=row['total_score'],
            bucket=Bucket(row['bucket']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now()
        )


# ==================== 默认实例 ====================

default_repository = CustomerHubRepository()

