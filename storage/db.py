"""
SQLite 数据库封装
职责：连接管理、会话CRUD、消息日志、导出CSV
"""
import hashlib
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """会话信息"""
    session_key: str
    group_id: str
    sender_id: str
    sender_name: Optional[str] = None
    customer_name: Optional[str] = None
    turn_count: int = 0
    summary: Optional[str] = None
    status: str = "active"
    expires_at: Optional[datetime] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None


@dataclass
class MessageLog:
    """消息日志记录"""
    request_id: str
    group_id: str
    sender_id: str
    user_message: str
    
    # 可选字段
    session_id: Optional[int] = None
    group_name: Optional[str] = None
    sender_name: Optional[str] = None
    bot_response: Optional[str] = None
    user_message_hash: Optional[str] = None
    
    # RAG
    evidence_ids: Optional[str] = None  # JSON array
    evidence_summary: Optional[str] = None
    confidence: Optional[float] = None
    
    # 路由
    branch: Optional[str] = None
    handoff_reason: Optional[str] = None
    
    # AI
    provider: Optional[str] = None
    model: Optional[str] = None
    token_in: int = 0
    token_out: int = 0
    token_total: int = 0
    
    # 时延
    latency_receive_ms: Optional[int] = None
    latency_retrieval_ms: Optional[int] = None
    latency_generation_ms: Optional[int] = None
    latency_send_ms: Optional[int] = None
    latency_total_ms: Optional[int] = None
    
    # 状态
    status: str = "pending"
    error_message: Optional[str] = None
    debug_info: Optional[str] = None
    
    received_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None


class Database:
    """SQLite 数据库管理器"""
    
    def __init__(self, db_path: str = "data/data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        
    def connect(self) -> sqlite3.Connection:
        """建立数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self.conn.row_factory = sqlite3.Row
            logger.info(f"数据库已连接: {self.db_path}")
        return self.conn
    
    def init_database(self, sql_file: str = "sql/init.sql") -> None:
        """初始化数据库表结构"""
        conn = self.connect()
        sql_path = Path(sql_file)
        
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL 初始化文件不存在: {sql_file}")
        
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        try:
            conn.executescript(sql_script)
            conn.commit()
            logger.info("数据库表结构初始化成功")
        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("数据库连接已关闭")
    
    # ==================== 会话管理 ====================
    
    def upsert_session(
        self,
        session_key: str,
        group_id: str,
        sender_id: str,
        sender_name: Optional[str] = None,
        ttl_minutes: int = 15
    ) -> SessionInfo:
        """
        创建或更新会话
        Args:
            session_key: 会话唯一键 (格式: {group_id}:{sender_id})
            group_id: 群ID
            sender_id: 发送者ID
            sender_name: 发送者昵称
            ttl_minutes: 会话TTL（分钟）
        Returns:
            SessionInfo: 会话信息
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        now = datetime.now()
        expires_at = now + timedelta(minutes=ttl_minutes)
        
        # 尝试插入，如果冲突则更新
        try:
            # 创建新会话
            cursor.execute("""
                INSERT INTO sessions 
                (session_key, group_id, sender_id, sender_name, expires_at, turn_count)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (session_key, group_id, sender_id, sender_name, expires_at))
            conn.commit()
            
            session_id = cursor.lastrowid
            turn_count = 1
            created_at = now
            logger.info(f"新会话已创建: {session_key}")
            
        except sqlite3.IntegrityError:
            # 会话已存在，执行更新
            cursor.execute("""
                UPDATE sessions 
                SET last_active_at = ?,
                    expires_at = ?,
                    turn_count = turn_count + 1,
                    status = 'active'
                WHERE session_key = ?
            """, (now, expires_at, session_key))
            conn.commit()
            
            # 查询更新后的数据
            cursor.execute(
                "SELECT * FROM sessions WHERE session_key = ?",
                (session_key,)
            )
            updated_row = cursor.fetchone()
            
            session_id = updated_row['id']
            turn_count = updated_row['turn_count']
            created_at = datetime.fromisoformat(updated_row['created_at'])
            logger.debug(f"会话已更新: {session_key}, turn={turn_count}")
        
        return SessionInfo(
            id=session_id,
            session_key=session_key,
            group_id=group_id,
            sender_id=sender_id,
            sender_name=sender_name,
            turn_count=turn_count,
            expires_at=expires_at,
            created_at=created_at,
            last_active_at=now
        )
    
    def get_session(self, session_key: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM sessions WHERE session_key = ?",
            (session_key,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return SessionInfo(
            id=row['id'],
            session_key=row['session_key'],
            group_id=row['group_id'],
            sender_id=row['sender_id'],
            sender_name=row['sender_name'],
            customer_name=row['customer_name'],
            turn_count=row['turn_count'],
            summary=row['summary'],
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            last_active_at=datetime.fromisoformat(row['last_active_at']) if row['last_active_at'] else None,
            expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None
        )
    
    def update_summary(self, session_key: str, summary: str) -> None:
        """更新会话摘要（≤200字）"""
        if len(summary) > 200:
            summary = summary[:200]
            logger.warning(f"会话摘要被截断到200字: {session_key}")
        
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions 
            SET summary = ?
            WHERE session_key = ?
        """, (summary, session_key))
        
        conn.commit()
        logger.debug(f"会话摘要已更新: {session_key}")
    
    def bind_customer(self, session_key: str, customer_name: str) -> None:
        """绑定客户名称（通过 #bind 指令）"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions 
            SET customer_name = ?
            WHERE session_key = ?
        """, (customer_name, session_key))
        
        conn.commit()
        logger.info(f"客户名称已绑定: {session_key} -> {customer_name}")
    
    def expire_old_sessions(self) -> int:
        """清理过期会话，返回清理数量"""
        conn = self.connect()
        cursor = conn.cursor()
        
        now = datetime.now()
        cursor.execute("""
            UPDATE sessions 
            SET status = 'expired'
            WHERE expires_at < ? AND status = 'active'
        """, (now,))
        
        count = cursor.rowcount
        conn.commit()
        
        if count > 0:
            logger.info(f"已清理 {count} 个过期会话")
        
        return count
    
    # ==================== 消息日志 ====================
    
    def log_message(self, msg: MessageLog) -> Optional[int]:
        """
        记录消息日志
        Args:
            msg: MessageLog 对象
        Returns:
            Optional[int]: 插入的消息ID，失败返回None
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # 自动计算消息哈希（用于去重）
        if not msg.user_message_hash:
            msg.user_message_hash = self._hash_message(
                msg.group_id, msg.sender_id, msg.user_message
            )
        
        # 自动设置接收时间
        if not msg.received_at:
            msg.received_at = datetime.now()
        
        # 转换为字典并准备插入
        data = asdict(msg)
        
        # 构建插入语句
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = list(data.values())
        
        try:
            cursor.execute(
                f"INSERT INTO messages ({columns}) VALUES ({placeholders})",
                values
            )
            msg_id = cursor.lastrowid
            conn.commit()
            
            logger.debug(
                f"消息已记录: request_id={msg.request_id}, "
                f"group={msg.group_id}, sender={msg.sender_id}"
            )
            return msg_id
            
        except sqlite3.IntegrityError as e:
            logger.warning(f"消息重复或冲突: {msg.request_id}, {e}")
            raise
    
    def update_message(
        self,
        request_id: str,
        **kwargs
    ) -> None:
        """
        更新消息记录
        Args:
            request_id: 请求ID
            **kwargs: 要更新的字段
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        if not kwargs:
            return
        
        # 构建更新语句
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [request_id]
        
        cursor.execute(
            f"UPDATE messages SET {set_clause} WHERE request_id = ?",
            values
        )
        conn.commit()
        
        logger.debug(f"消息已更新: {request_id}, fields={list(kwargs.keys())}")
    
    def get_message(self, request_id: str) -> Optional[Dict[str, Any]]:
        """获取消息记录"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM messages WHERE request_id = ?",
            (request_id,)
        )
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def check_duplicate(
        self,
        group_id: str,
        sender_id: str,
        message: str,
        window_seconds: int = 10
    ) -> bool:
        """
        检查消息是否重复（10秒窗口）
        Args:
            group_id: 群ID
            sender_id: 发送者ID
            message: 消息文本
            window_seconds: 去重窗口（秒）
        Returns:
            bool: True=重复，False=新消息
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        msg_hash = self._hash_message(group_id, sender_id, message)
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM messages
            WHERE user_message_hash = ?
            AND received_at > ?
        """, (msg_hash, cutoff_time))
        
        row = cursor.fetchone()
        count = row['count'] if row else 0
        
        return count > 0
    
    # ==================== 速率限制 ====================
    
    def check_rate_limit(
        self,
        entity_type: str,
        entity_id: str,
        limit: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        检查速率限制
        Args:
            entity_type: 类型 (group | user | global)
            entity_id: 实体ID
            limit: 请求限制数
            window_seconds: 时间窗口（秒）
        Returns:
            (is_allowed, current_count)
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        # 查询当前窗口内的请求数
        cursor.execute("""
            SELECT SUM(request_count) as total FROM rate_limits
            WHERE entity_type = ? 
            AND entity_id = ?
            AND window_start >= ?
        """, (entity_type, entity_id, window_start))
        
        row = cursor.fetchone()
        current_count = int(row['total']) if row and row['total'] else 0
        
        is_allowed = current_count < limit
        
        if is_allowed:
            # 更新或插入速率记录
            cursor.execute("""
                INSERT INTO rate_limits 
                (entity_type, entity_id, window_start, request_count, last_request_at)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(entity_type, entity_id, window_start)
                DO UPDATE SET 
                    request_count = request_count + 1,
                    last_request_at = ?
            """, (entity_type, entity_id, now, now, now))
            
            conn.commit()
            current_count += 1
        
        return is_allowed, current_count
    
    # ==================== 系统配置 ====================
    
    def get_config(self, key: str) -> Optional[str]:
        """获取系统配置"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT value FROM system_config WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        
        return row['value'] if row else None
    
    def set_config(self, key: str, value: str) -> None:
        """设置系统配置"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_config (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value = ?, updated_at = ?
        """, (key, value, datetime.now(), value, datetime.now()))
        
        conn.commit()
        logger.info(f"系统配置已更新: {key} = {value}")
    
    # ==================== 导出功能 ====================
    
    def export_to_csv(
        self,
        output_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        导出消息日志为CSV
        Args:
            output_path: 输出文件路径
            start_date: 开始日期
            end_date: 结束日期
        Returns:
            str: 导出的文件路径
        """
        import csv
        
        conn = self.connect()
        cursor = conn.cursor()
        
        # 构建查询条件
        query = "SELECT * FROM messages WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND received_at >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND received_at <= ?"
            params.append(end_date)
        
        query += " ORDER BY received_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            logger.warning("没有数据可导出")
            return output_path
        
        # 写入CSV
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            
            for row in rows:
                writer.writerow(dict(row))
        
        logger.info(f"已导出 {len(rows)} 条记录到: {output_path}")
        return str(output_file)
    
    # ==================== 辅助方法 ====================
    
    @staticmethod
    def _hash_message(group_id: str, sender_id: str, message: str) -> str:
        """生成消息哈希（用于去重）"""
        content = f"{group_id}:{sender_id}:{message}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
