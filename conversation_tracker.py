"""
对话追踪器
用于追踪对话效果、保存完整对话串、评估结果
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConversationOutcome:
    """对话结果"""
    outcome: str  # solved | unsolved | transferred | abandoned
    reason: str   # 原因说明
    resolved_by: str  # ai | human | self
    satisfaction_score: Optional[int] = None  # 1-5分
    tags: Optional[List[str]] = None  # 标签


class ConversationTracker:
    """
    对话追踪器
    
    功能：
    1. 追踪对话效果（是否解决、如何解决）
    2. 保存完整对话串（支持上下文）
    3. 自动评估对话质量
    4. 生成对话摘要
    """
    
    def __init__(self, db):
        """
        初始化
        Args:
            db: Database 实例
        """
        self.db = db
    
    def start_conversation(self, session_key: str, tags: List[str] = None) -> None:
        """
        开始一个新对话，初始化标签
        
        Args:
            session_key: 会话键
            tags: 对话标签（如：售后、技术支持、价格咨询等）
        """
        if tags:
            self._update_session_field(session_key, 'tags', ','.join(tags))
            logger.info(f"对话开始: {session_key}, 标签: {tags}")
    
    def add_message_to_thread(
        self,
        session_key: str,
        message_id: str,
        role: str,  # user | assistant
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        将消息添加到对话串
        
        Args:
            session_key: 会话键
            message_id: 消息ID
            role: 角色（user/assistant）
            content: 消息内容
            metadata: 元数据（如：置信度、模型等）
        """
        # 获取当前对话串
        thread = self._get_conversation_thread(session_key)
        
        # 添加新消息
        message = {
            'id': message_id,
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        thread.append(message)
        
        # 保存对话串
        self._save_conversation_thread(session_key, thread)
        
        # 更新统计
        self._update_message_count(session_key, role)
    
    def mark_outcome(
        self,
        session_key: str,
        outcome: ConversationOutcome
    ) -> None:
        """
        标记对话结果
        
        Args:
            session_key: 会话键
            outcome: 对话结果
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        # 计算解决用时
        cursor.execute("""
            SELECT created_at, last_active_at 
            FROM sessions 
            WHERE session_key = ?
        """, (session_key,))
        
        row = cursor.fetchone()
        if row:
            created_at = datetime.fromisoformat(row[0]) if row[0] else None
            last_active_at = datetime.fromisoformat(row[1]) if row[1] else None
            
            resolution_time_sec = None
            if created_at and last_active_at:
                resolution_time_sec = int((last_active_at - created_at).total_seconds())
        
        # 更新结果
        cursor.execute("""
            UPDATE sessions 
            SET conversation_outcome = ?,
                outcome_reason = ?,
                resolved_by = ?,
                satisfaction_score = ?,
                tags = ?,
                resolution_time_sec = ?
            WHERE session_key = ?
        """, (
            outcome.outcome,
            outcome.reason,
            outcome.resolved_by,
            outcome.satisfaction_score,
            ','.join(outcome.tags) if outcome.tags else None,
            resolution_time_sec,
            session_key
        ))
        
        conn.commit()
        
        logger.info(
            f"对话结果已标记: {session_key}, "
            f"outcome={outcome.outcome}, resolved_by={outcome.resolved_by}"
        )
    
    def auto_evaluate_outcome(
        self,
        session_key: str,
        last_branch: str,
        last_status: str,
        avg_confidence: float
    ) -> ConversationOutcome:
        """
        自动评估对话结果
        
        Args:
            session_key: 会话键
            last_branch: 最后分支（direct_answer/clarification/handoff）
            last_status: 最后状态（answered/failed）
            avg_confidence: 平均置信度
        
        Returns:
            ConversationOutcome: 评估结果
        """
        # 根据最后的分支和状态判断结果
        if last_branch == 'handoff':
            # 转人工
            outcome = ConversationOutcome(
                outcome='transferred',
                reason='需要人工协助',
                resolved_by='human',
                tags=['转人工']
            )
        
        elif last_status == 'failed':
            # 失败
            outcome = ConversationOutcome(
                outcome='unsolved',
                reason='系统处理失败',
                resolved_by='unknown',
                tags=['失败']
            )
        
        elif last_branch == 'direct_answer' and avg_confidence >= 0.75:
            # 高置信度直答，视为已解决
            outcome = ConversationOutcome(
                outcome='solved',
                reason='AI直接解答',
                resolved_by='ai',
                satisfaction_score=4,  # 假设4分
                tags=['AI解决']
            )
        
        elif last_branch == 'clarification':
            # 澄清问题，未完全解决
            outcome = ConversationOutcome(
                outcome='unsolved',
                reason='需要用户提供更多信息',
                resolved_by='ai',
                satisfaction_score=3,
                tags=['待澄清']
            )
        
        else:
            # 其他情况
            outcome = ConversationOutcome(
                outcome='unknown',
                reason='无法判断',
                resolved_by='unknown'
            )
        
        return outcome
    
    def get_conversation_summary(self, session_key: str) -> Dict[str, Any]:
        """
        获取对话摘要
        
        Args:
            session_key: 会话键
        
        Returns:
            对话摘要（包含完整对话串、统计信息、结果等）
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        # 获取会话信息
        cursor.execute("""
            SELECT 
                session_key, group_name, sender_name, customer_name,
                conversation_outcome, outcome_reason, resolved_by,
                satisfaction_score, tags, turn_count, total_messages,
                ai_messages, resolution_time_sec, conversation_thread,
                created_at, last_active_at
            FROM sessions
            WHERE session_key = ?
        """, (session_key,))
        
        row = cursor.fetchone()
        if not row:
            return {}
        
        # 解析对话串
        thread = []
        if row[13]:  # conversation_thread
            try:
                thread = json.loads(row[13])
            except:
                pass
        
        summary = {
            'session_key': row[0],
            'group_name': row[1],
            'sender_name': row[2],
            'customer_name': row[3],
            'outcome': row[4],
            'outcome_reason': row[5],
            'resolved_by': row[6],
            'satisfaction_score': row[7],
            'tags': row[8].split(',') if row[8] else [],
            'turn_count': row[9],
            'total_messages': row[10],
            'ai_messages': row[11],
            'resolution_time_sec': row[12],
            'conversation_thread': thread,
            'created_at': row[14],
            'last_active_at': row[15]
        }
        
        # 获取消息统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(confidence) as avg_confidence,
                SUM(token_total) as total_tokens,
                AVG(latency_total_ms) as avg_latency
            FROM messages
            WHERE session_id = (SELECT id FROM sessions WHERE session_key = ?)
        """, (session_key,))
        
        stats_row = cursor.fetchone()
        if stats_row:
            summary['stats'] = {
                'total_messages': stats_row[0],
                'avg_confidence': stats_row[1],
                'total_tokens': stats_row[2],
                'avg_latency_ms': stats_row[3]
            }
        
        return summary
    
    def get_conversation_thread_for_context(
        self,
        session_key: str,
        max_turns: int = 5
    ) -> List[Dict[str, str]]:
        """
        获取对话历史用于上下文（供AI调用）
        
        Args:
            session_key: 会话键
            max_turns: 最大轮数
        
        Returns:
            对话历史 [{'role': 'user', 'content': '...'}, ...]
        """
        thread = self._get_conversation_thread(session_key)
        
        # 只取最近的 N 轮对话
        recent_thread = thread[-max_turns * 2:] if len(thread) > max_turns * 2 else thread
        
        # 转换为AI需要的格式
        context = []
        for msg in recent_thread:
            context.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        return context
    
    def export_conversation_for_bitable(self, session_key: str) -> Dict[str, Any]:
        """
        导出对话数据供多维表格使用
        
        Args:
            session_key: 会话键
        
        Returns:
            格式化的对话数据
        """
        summary = self.get_conversation_summary(session_key)
        
        if not summary:
            return {}
        
        # 格式化对话串为文本
        thread_text = self._format_thread_as_text(summary.get('conversation_thread', []))
        
        return {
            '会话ID': session_key,
            '群名称': summary.get('group_name'),
            '用户': summary.get('sender_name'),
            '客户名称': summary.get('customer_name'),
            '对话结果': summary.get('outcome'),
            '结果说明': summary.get('outcome_reason'),
            '解决方式': summary.get('resolved_by'),
            '满意度': summary.get('satisfaction_score'),
            '标签': ','.join(summary.get('tags', [])),
            '对话轮数': summary.get('turn_count'),
            '总消息数': summary.get('total_messages'),
            'AI消息数': summary.get('ai_messages'),
            '解决用时(秒)': summary.get('resolution_time_sec'),
            '完整对话': thread_text,
            '平均置信度': summary.get('stats', {}).get('avg_confidence'),
            '总Token数': summary.get('stats', {}).get('total_tokens'),
            '开始时间': summary.get('created_at'),
            '结束时间': summary.get('last_active_at')
        }
    
    # ==================== 私有方法 ====================
    
    def _get_conversation_thread(self, session_key: str) -> List[Dict]:
        """获取对话串"""
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT conversation_thread FROM sessions WHERE session_key = ?",
            (session_key,)
        )
        
        row = cursor.fetchone()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except:
                return []
        
        return []
    
    def _save_conversation_thread(self, session_key: str, thread: List[Dict]) -> None:
        """保存对话串"""
        thread_json = json.dumps(thread, ensure_ascii=False)
        
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions 
            SET conversation_thread = ?,
                last_message_at = ?
            WHERE session_key = ?
        """, (thread_json, datetime.now(), session_key))
        
        conn.commit()
    
    def _update_message_count(self, session_key: str, role: str) -> None:
        """更新消息计数"""
        conn = self.db.connect()
        cursor = conn.cursor()
        
        if role == 'user':
            cursor.execute("""
                UPDATE sessions 
                SET total_messages = total_messages + 1
                WHERE session_key = ?
            """, (session_key,))
        elif role == 'assistant':
            cursor.execute("""
                UPDATE sessions 
                SET total_messages = total_messages + 1,
                    ai_messages = ai_messages + 1
                WHERE session_key = ?
            """, (session_key,))
        
        conn.commit()
    
    def _update_session_field(self, session_key: str, field: str, value: Any) -> None:
        """更新会话字段"""
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            f"UPDATE sessions SET {field} = ? WHERE session_key = ?",
            (value, session_key)
        )
        
        conn.commit()
    
    def _format_thread_as_text(self, thread: List[Dict]) -> str:
        """将对话串格式化为文本"""
        if not thread:
            return ""
        
        lines = []
        for msg in thread:
            role = "用户" if msg['role'] == 'user' else "AI"
            timestamp = msg.get('timestamp', '')
            content = msg.get('content', '')
            
            lines.append(f"[{timestamp}] {role}: {content}")
        
        return "\n".join(lines)

