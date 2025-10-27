"""
数据库模块 - 兼容性包装器
使用统一数据库管理器，支持SQLite和Supabase
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# 导入统一数据库管理器
from .unified_database import get_database_manager, init_database_manager

# 保持原有的数据类定义以保持兼容性
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
    """
    数据库兼容性包装器
    使用统一数据库管理器，保持原有API接口
    """
    
    def __init__(self, db_path: str = "data/data.db"):
        """
        初始化数据库（兼容性构造函数）
        
        Args:
            db_path: 数据库路径（仅SQLite使用，Supabase忽略此参数）
        """
        self.db_path = db_path
        self.db_manager = get_database_manager()
        
        logger.info(f"✅ 数据库包装器初始化: {self.db_manager.get_database_type().value}")
    
    def connect(self):
        """兼容性方法 - 统一数据库管理器不需要显式连接"""
        return self
    
    def init_database(self, sql_file: str = "sql/init.sql") -> None:
        """初始化数据库表结构（兼容性方法）"""
        logger.info("数据库表结构初始化（由统一数据库管理器自动处理）")
    
    def close(self):
        """兼容性方法 - 统一数据库管理器不需要显式关闭"""
        logger.debug("数据库连接关闭（由统一数据库管理器自动处理）")
    
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
        创建或更新会话（同步版本，保持兼容性）
        使用统一数据库管理器的同步方法
        """
        try:
            # 使用统一数据库管理器的同步方法
            session_data = {
                "session_key": session_key,
                "group_id": group_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "expires_at": (datetime.now() + timedelta(minutes=ttl_minutes)).isoformat(),
                "turn_count": 1,
                "status": "active"
            }
            
            # 调用同步方法（内部处理异步调用）
            result = self.db_manager.create_session_sync("default", session_data)
            
            if result:
                return SessionInfo(
                    id=result.get("id"),
                    session_key=result["session_key"],
                    group_id=result["group_id"],
                    sender_id=result["sender_id"],
                    sender_name=result.get("sender_name"),
                    customer_name=result.get("customer_name"),
                    turn_count=result.get("turn_count", 1),
                    summary=result.get("summary"),
                    status=result.get("status", "active"),
                    expires_at=datetime.fromisoformat(result["expires_at"]) if result.get("expires_at") else None,
                    created_at=datetime.fromisoformat(result["created_at"]) if result.get("created_at") else datetime.now(),
                    last_active_at=datetime.fromisoformat(result["last_active_at"]) if result.get("last_active_at") else datetime.now()
                )
            else:
                # 返回默认会话信息
                return SessionInfo(
                    session_key=session_key,
                    group_id=group_id,
                    sender_id=sender_id,
                    sender_name=sender_name,
                    expires_at=datetime.now() + timedelta(minutes=ttl_minutes),
                    created_at=datetime.now(),
                    last_active_at=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"❌ 会话创建失败: {e}")
            # 返回默认会话信息
            return SessionInfo(
                session_key=session_key,
                group_id=group_id,
                sender_id=sender_id,
                sender_name=sender_name,
                expires_at=datetime.now() + timedelta(minutes=ttl_minutes),
                created_at=datetime.now(),
                last_active_at=datetime.now()
            )
    
    def get_session(self, session_key: str) -> Optional[SessionInfo]:
        """获取会话信息（同步版本，保持兼容性）"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sessions WHERE session_key = ?", (session_key,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
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
                    expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    last_active_at=datetime.fromisoformat(row['last_active_at']) if row['last_active_at'] else None
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取会话失败: {e}")
            return None
    
    def update_summary(self, session_key: str, summary: str) -> None:
        """更新会话摘要（同步版本，保持兼容性）"""
        try:
            import sqlite3
            
            if len(summary) > 200:
                summary = summary[:200]
                logger.warning(f"会话摘要被截断到200字: {session_key}")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("UPDATE sessions SET summary = ? WHERE session_key = ?", (summary, session_key))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.debug(f"会话摘要已更新: {session_key}")
            else:
                logger.warning(f"会话摘要更新失败: {session_key}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ 更新会话摘要失败: {e}")
    
    def bind_customer(self, session_key: str, customer_name: str) -> None:
        """绑定客户名称（同步版本，保持兼容性）"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("UPDATE sessions SET customer_name = ? WHERE session_key = ?", (customer_name, session_key))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"客户名称已绑定: {session_key} -> {customer_name}")
            else:
                logger.warning(f"客户名称绑定失败: {session_key}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ 绑定客户名称失败: {e}")
    
    def expire_old_sessions(self) -> int:
        """清理过期会话（同步版本，保持兼容性）"""
        # 简化实现，实际应用中可能需要更复杂的逻辑
        logger.info("过期会话清理（由统一数据库管理器自动处理）")
        return 0
    
    # ==================== 消息日志 ====================
    
    def log_message(self, msg: MessageLog) -> Optional[int]:
        """
        记录消息日志（同步版本，保持兼容性）
        """
        try:
            import sqlite3
            import hashlib
            
            # 自动计算消息哈希（用于去重）
            if not msg.user_message_hash:
                content = f"{msg.group_id}:{msg.sender_id}:{msg.user_message}"
                msg.user_message_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # 自动设置接收时间
            if not msg.received_at:
                msg.received_at = datetime.now()
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 创建消息表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL UNIQUE,
                    session_id INTEGER,
                    group_id TEXT NOT NULL,
                    group_name TEXT,
                    sender_id TEXT NOT NULL,
                    sender_name TEXT,
                    user_message TEXT NOT NULL,
                    user_message_hash TEXT,
                    bot_response TEXT,
                    evidence_ids TEXT,
                    evidence_summary TEXT,
                    confidence REAL,
                    branch TEXT,
                    handoff_reason TEXT,
                    provider TEXT,
                    model TEXT,
                    token_in INTEGER DEFAULT 0,
                    token_out INTEGER DEFAULT 0,
                    token_total INTEGER DEFAULT 0,
                    latency_receive_ms INTEGER,
                    latency_retrieval_ms INTEGER,
                    latency_generation_ms INTEGER,
                    latency_send_ms INTEGER,
                    latency_total_ms INTEGER,
                    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    responded_at DATETIME,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    debug_info TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # 插入消息
            cursor.execute("""
                INSERT INTO messages 
                (request_id, session_id, group_id, group_name, sender_id, sender_name, 
                 user_message, user_message_hash, bot_response, evidence_ids, evidence_summary,
                 confidence, branch, handoff_reason, provider, model, token_in, token_out, token_total,
                 latency_receive_ms, latency_retrieval_ms, latency_generation_ms, latency_send_ms, latency_total_ms,
                 received_at, responded_at, status, error_message, debug_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                msg.request_id, msg.session_id, msg.group_id, msg.group_name, msg.sender_id, msg.sender_name,
                msg.user_message, msg.user_message_hash, msg.bot_response, msg.evidence_ids, msg.evidence_summary,
                msg.confidence, msg.branch, msg.handoff_reason, msg.provider, msg.model, msg.token_in, msg.token_out, msg.token_total,
                msg.latency_receive_ms, msg.latency_retrieval_ms, msg.latency_generation_ms, msg.latency_send_ms, msg.latency_total_ms,
                msg.received_at, msg.responded_at, msg.status, msg.error_message, msg.debug_info
            ))
            
            conn.commit()
            message_id = cursor.lastrowid
            
            conn.close()
            
            logger.debug(f"消息记录成功: {msg.request_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"❌ 消息记录失败: {e}")
            return None
    
    def update_message(self, request_id: str, **kwargs) -> None:
        """更新消息记录（同步版本，保持兼容性）"""
        try:
            import sqlite3
            
            if not kwargs:
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 构建更新语句
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [request_id]
            
            cursor.execute(f"UPDATE messages SET {set_clause} WHERE request_id = ?", values)
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.debug(f"消息已更新: {request_id}, fields={list(kwargs.keys())}")
            else:
                logger.warning(f"消息更新失败: {request_id}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ 更新消息失败: {e}")
    
    def get_message(self, request_id: str) -> Optional[Dict[str, Any]]:
        """获取消息记录（同步版本，保持兼容性）"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM messages WHERE request_id = ?", (request_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"❌ 获取消息失败: {e}")
            return None
    
    def check_duplicate(
        self,
        group_id: str,
        sender_id: str,
        message: str,
        window_seconds: int = 10
    ) -> bool:
        """检查消息是否重复（同步版本，保持兼容性）"""
        try:
            import sqlite3
            import hashlib
            
            msg_hash = hashlib.md5(f"{group_id}:{sender_id}:{message}".encode('utf-8')).hexdigest()
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM messages 
                WHERE user_message_hash = ? AND received_at > ?
            """, (msg_hash, cutoff_time))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"❌ 检查重复消息失败: {e}")
            return False
    
    # ==================== 速率限制 ====================
    
    def check_rate_limit(
        self,
        entity_type: str,
        entity_id: str,
        limit: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """检查速率限制（同步版本，保持兼容性）"""
        try:
            import sqlite3
            
            now = datetime.now()
            window_start = now - timedelta(seconds=window_seconds)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建速率限制表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    window_start DATETIME NOT NULL,
                    request_count INTEGER DEFAULT 1,
                    last_request_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(entity_type, entity_id, window_start)
                )
            """)
            
            # 查询当前窗口内的请求数
            cursor.execute("""
                SELECT SUM(request_count) as total FROM rate_limits
                WHERE entity_type = ? AND entity_id = ? AND window_start >= ?
            """, (entity_type, entity_id, window_start))
            
            row = cursor.fetchone()
            current_count = int(row[0]) if row and row[0] else 0
            
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
            
            conn.close()
            
            return is_allowed, current_count
            
        except Exception as e:
            logger.error(f"❌ 速率限制检查失败: {e}")
            return False, 0
    
    # ==================== 系统配置 ====================
    
    def get_config(self, key: str) -> Optional[str]:
        """获取系统配置（简化实现）"""
        import os
        return os.getenv(key)
    
    def set_config(self, key: str, value: str) -> None:
        """设置系统配置（简化实现）"""
        import os
        os.environ[key] = value
        logger.info(f"系统配置已更新: {key} = {value}")
    
    # ==================== 导出功能 ====================
    
    def export_to_csv(
        self,
        output_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """导出消息日志为CSV（同步版本，保持兼容性）"""
        try:
            import sqlite3
            import csv
            from pathlib import Path
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查询消息
            query = "SELECT * FROM messages"
            params = []
            
            if start_date or end_date:
                conditions = []
                if start_date:
                    conditions.append("received_at >= ?")
                    params.append(start_date)
                if end_date:
                    conditions.append("received_at <= ?")
                    params.append(end_date)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY received_at DESC LIMIT 10000"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            if not rows:
                logger.warning("没有数据可导出")
                return output_path
            
            # 写入CSV
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows([dict(row) for row in rows])
            
            logger.info(f"已导出 {len(rows)} 条记录到: {output_path}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"❌ 导出CSV失败: {e}")
            return output_path
    
    # ==================== 辅助方法 ====================
    
    @staticmethod
    def _hash_message(group_id: str, sender_id: str, message: str) -> str:
        """生成消息哈希（用于去重）"""
        import hashlib
        content = f"{group_id}:{sender_id}:{message}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()


# 延迟初始化数据库管理器（避免导入时自动初始化）
# init_database_manager()  # 注释掉自动初始化