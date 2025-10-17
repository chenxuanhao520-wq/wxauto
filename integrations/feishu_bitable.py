"""
飞书多维表格集成
用于将消息日志同步到飞书多维表格，实现数据分析和可视化
"""
import os
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FeishuBitable:
    """
    飞书多维表格集成
    
    功能：
    1. 自动同步消息日志到飞书表格
    2. 支持批量写入
    3. 支持字段映射配置
    """
    
    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        bitable_token: Optional[str] = None,
        table_id: Optional[str] = None
    ):
        """
        初始化飞书多维表格客户端
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            bitable_token: 多维表格 token
            table_id: 数据表 ID
        """
        self.app_id = app_id or os.getenv("FEISHU_APP_ID")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET")
        self.bitable_token = bitable_token or os.getenv("FEISHU_BITABLE_TOKEN")
        self.table_id = table_id or os.getenv("FEISHU_TABLE_ID")
        
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        
        if self.app_id and self.app_secret:
            logger.info("飞书多维表格集成初始化成功")
        else:
            logger.warning("飞书多维表格未配置，功能不可用")
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return all([self.app_id, self.app_secret, self.bitable_token, self.table_id])
    
    def _get_access_token(self) -> Optional[str]:
        """
        获取访问令牌
        token 有效期 2 小时，自动缓存
        """
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            import requests
            
            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            
            payload = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result['tenant_access_token']
                # token 有效期 2 小时，提前 10 分钟刷新
                self.token_expires_at = time.time() + 7200 - 600
                logger.info("飞书 access_token 获取成功")
                return self.access_token
            else:
                logger.error(f"飞书 access_token 获取失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"获取飞书 access_token 异常: {e}")
            return None
    
    def add_record(self, record: Dict[str, Any]) -> bool:
        """
        添加单条记录到飞书表格
        
        Args:
            record: 记录数据，字段名需要与表格字段对应
        
        Returns:
            bool: 是否成功
        """
        if not self.is_configured():
            logger.warning("飞书多维表格未配置，跳过写入")
            return False
        
        access_token = self._get_access_token()
        if not access_token:
            return False
        
        try:
            import requests
            
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.bitable_token}/tables/{self.table_id}/records"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 转换记录格式
            fields = self._convert_record(record)
            
            payload = {
                "fields": fields
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"飞书表格写入成功: record_id={result['data']['record']['record_id']}")
                return True
            else:
                logger.error(f"飞书表格写入失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"飞书表格写入异常: {e}")
            return False
    
    def add_records(self, records: List[Dict[str, Any]]) -> bool:
        """
        批量添加记录到飞书表格
        
        Args:
            records: 记录列表
        
        Returns:
            bool: 是否成功
        """
        if not self.is_configured():
            logger.warning("飞书多维表格未配置，跳过写入")
            return False
        
        if not records:
            return True
        
        access_token = self._get_access_token()
        if not access_token:
            return False
        
        try:
            import requests
            
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.bitable_token}/tables/{self.table_id}/records/batch_create"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 转换记录格式
            records_data = [
                {"fields": self._convert_record(record)}
                for record in records
            ]
            
            payload = {
                "records": records_data
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"飞书表格批量写入成功: {len(records)} 条记录")
                return True
            else:
                logger.error(f"飞书表格批量写入失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"飞书表格批量写入异常: {e}")
            return False
    
    def _convert_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换记录格式，适配飞书多维表格字段类型
        
        Args:
            record: 原始记录
        
        Returns:
            转换后的字段数据
        """
        fields = {}
        
        # 字段映射和类型转换
        field_mapping = {
            'request_id': '请求ID',
            'session_id': '会话ID',
            'group_name': '群名称',
            'sender_name': '发送者',
            'user_message': '用户消息',
            'bot_response': 'AI回复',
            'confidence': '置信度',
            'branch': '分支',
            'provider': 'AI提供商',
            'model': '模型',
            'token_total': 'Token总数',
            'latency_total_ms': '总时延(ms)',
            'status': '状态',
            'received_at': '接收时间',
            'responded_at': '响应时间'
        }
        
        for src_key, dst_key in field_mapping.items():
            if src_key in record and record[src_key] is not None:
                value = record[src_key]
                
                # 时间格式转换
                if src_key in ['received_at', 'responded_at']:
                    if isinstance(value, datetime):
                        value = int(value.timestamp() * 1000)
                    elif isinstance(value, str):
                        try:
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            value = int(dt.timestamp() * 1000)
                        except:
                            value = None
                
                if value is not None:
                    fields[dst_key] = value
        
        return fields
    
    def sync_conversations_from_database(self, db_path: str, since: Optional[datetime] = None) -> int:
        """
        从数据库同步对话级别数据到飞书表格
        
        Args:
            db_path: 数据库路径
            since: 起始时间（可选）
        
        Returns:
            int: 同步的对话数
        """
        if not self.is_configured():
            logger.warning("飞书多维表格未配置，跳过同步")
            return 0
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查询对话级别数据
            query = """
                SELECT 
                    session_key, group_name, sender_name, customer_name,
                    conversation_outcome, outcome_reason, resolved_by,
                    satisfaction_score, tags, turn_count, total_messages,
                    ai_messages, resolution_time_sec, conversation_thread,
                    created_at, last_active_at
                FROM sessions
                WHERE 1=1
            """
            params = []
            
            if since:
                query += " AND created_at >= ?"
                params.append(since)
            
            query += " ORDER BY created_at DESC LIMIT 1000"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            if not rows:
                logger.info("没有需要同步的对话")
                return 0
            
            # 转换为字典列表
            conversations = []
            for row in rows:
                conv = {
                    'session_key': row['session_key'],
                    'group_name': row['group_name'],
                    'sender_name': row['sender_name'],
                    'customer_name': row['customer_name'],
                    'conversation_outcome': row['conversation_outcome'],
                    'outcome_reason': row['outcome_reason'],
                    'resolved_by': row['resolved_by'],
                    'satisfaction_score': row['satisfaction_score'],
                    'tags': row['tags'],
                    'turn_count': row['turn_count'],
                    'total_messages': row['total_messages'],
                    'ai_messages': row['ai_messages'],
                    'resolution_time_sec': row['resolution_time_sec'],
                    'conversation_thread': row['conversation_thread'],
                    'created_at': row['created_at'],
                    'last_active_at': row['last_active_at']
                }
                conversations.append(conv)
            
            # 批量写入（每批 500 条）
            batch_size = 500
            total_synced = 0
            
            for i in range(0, len(conversations), batch_size):
                batch = conversations[i:i + batch_size]
                records = [self._convert_conversation_record(conv) for conv in batch]
                
                if self.add_records(records):
                    total_synced += len(batch)
                else:
                    logger.error(f"批次 {i // batch_size + 1} 同步失败")
            
            logger.info(f"飞书表格对话同步完成: {total_synced}/{len(conversations)} 条")
            return total_synced
            
        except Exception as e:
            logger.error(f"飞书表格对话同步异常: {e}")
            return 0
    
    def _convert_conversation_record(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换对话记录格式
        
        Args:
            conversation: 对话数据
        
        Returns:
            转换后的字段数据
        """
        fields = {}
        
        # 字段映射
        field_mapping = {
            'session_key': '会话ID',
            'group_name': '群名称',
            'sender_name': '用户',
            'customer_name': '客户名称',
            'conversation_outcome': '对话结果',
            'outcome_reason': '结果说明',
            'resolved_by': '解决方式',
            'satisfaction_score': '满意度',
            'tags': '标签',
            'turn_count': '对话轮数',
            'total_messages': '总消息数',
            'ai_messages': 'AI消息数',
            'resolution_time_sec': '解决用时(秒)',
            'conversation_thread': '完整对话',
            'created_at': '开始时间',
            'last_active_at': '结束时间'
        }
        
        for src_key, dst_key in field_mapping.items():
            if src_key in conversation and conversation[src_key] is not None:
                value = conversation[src_key]
                
                # 时间格式转换
                if src_key in ['created_at', 'last_active_at']:
                    if isinstance(value, datetime):
                        value = int(value.timestamp() * 1000)
                    elif isinstance(value, str):
                        try:
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            value = int(dt.timestamp() * 1000)
                        except:
                            value = None
                
                # 对话串转换为文本
                elif src_key == 'conversation_thread' and value:
                    try:
                        import json
                        thread = json.loads(value) if isinstance(value, str) else value
                        lines = []
                        for msg in thread:
                            role = "用户" if msg['role'] == 'user' else "AI"
                            lines.append(f"{role}: {msg['content']}")
                        value = "\n".join(lines)
                    except:
                        value = str(value)
                
                if value is not None:
                    fields[dst_key] = value
        
        return fields
    
    def sync_from_database(self, db_path: str, since: Optional[datetime] = None) -> int:
        """
        从数据库同步记录到飞书表格
        
        Args:
            db_path: 数据库路径
            since: 起始时间（可选），只同步此时间之后的记录
        
        Returns:
            int: 同步的记录数
        """
        if not self.is_configured():
            logger.warning("飞书多维表格未配置，跳过同步")
            return 0
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 构建查询
            query = """
                SELECT 
                    request_id, session_id, group_name, sender_name,
                    user_message, bot_response, confidence, branch,
                    provider, model, token_total, latency_total_ms,
                    status, received_at, responded_at
                FROM messages
                WHERE 1=1
            """
            params = []
            
            if since:
                query += " AND received_at >= ?"
                params.append(since)
            
            query += " ORDER BY received_at DESC LIMIT 1000"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            if not rows:
                logger.info("没有需要同步的记录")
                return 0
            
            # 转换为字典列表
            records = [dict(row) for row in rows]
            
            # 批量写入（每批 500 条）
            batch_size = 500
            total_synced = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                if self.add_records(batch):
                    total_synced += len(batch)
                else:
                    logger.error(f"批次 {i // batch_size + 1} 同步失败")
            
            logger.info(f"飞书表格同步完成: {total_synced}/{len(records)} 条记录")
            return total_synced
            
        except Exception as e:
            logger.error(f"飞书表格同步异常: {e}")
            return 0

