"""
钉钉多维表格（智能表格）集成
用于将消息日志同步到钉钉智能表格，实现数据分析和可视化
"""
import os
import time
import hmac
import hashlib
import base64
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)


class DingtalkBitable:
    """
    钉钉多维表格集成
    
    功能：
    1. 自动同步消息日志到钉钉表格
    2. 支持批量写入
    3. 支持字段映射配置
    """
    
    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        base_id: Optional[str] = None,
        table_id: Optional[str] = None
    ):
        """
        初始化钉钉多维表格客户端
        
        Args:
            app_key: 钉钉应用 App Key
            app_secret: 钉钉应用 App Secret
            base_id: 多维表格 base ID
            table_id: 数据表 ID
        """
        self.app_key = app_key or os.getenv("DINGTALK_APP_KEY")
        self.app_secret = app_secret or os.getenv("DINGTALK_APP_SECRET")
        self.base_id = base_id or os.getenv("DINGTALK_BASE_ID")
        self.table_id = table_id or os.getenv("DINGTALK_TABLE_ID")
        
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        
        if self.app_key and self.app_secret:
            logger.info("钉钉多维表格集成初始化成功")
        else:
            logger.warning("钉钉多维表格未配置，功能不可用")
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return all([self.app_key, self.app_secret, self.base_id, self.table_id])
    
    def _get_access_token(self) -> Optional[str]:
        """
        获取访问令牌
        token 有效期 2 小时，自动缓存
        """
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            import requests
            
            url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
            
            payload = {
                "appKey": self.app_key,
                "appSecret": self.app_secret
            }
            
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if 'accessToken' in result:
                self.access_token = result['accessToken']
                # token 有效期 2 小时，提前 10 分钟刷新
                self.token_expires_at = time.time() + 7200 - 600
                logger.info("钉钉 access_token 获取成功")
                return self.access_token
            else:
                logger.error(f"钉钉 access_token 获取失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"获取钉钉 access_token 异常: {e}")
            return None
    
    def add_record(self, record: Dict[str, Any]) -> bool:
        """
        添加单条记录到钉钉表格
        
        Args:
            record: 记录数据
        
        Returns:
            bool: 是否成功
        """
        if not self.is_configured():
            logger.warning("钉钉多维表格未配置，跳过写入")
            return False
        
        access_token = self._get_access_token()
        if not access_token:
            return False
        
        try:
            import requests
            
            url = f"https://api.dingtalk.com/v1.0/notable/bases/{self.base_id}/tables/{self.table_id}/records"
            
            headers = {
                "x-acs-dingtalk-access-token": access_token,
                "Content-Type": "application/json"
            }
            
            # 转换记录格式
            fields = self._convert_record(record)
            
            payload = {
                "fields": fields
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            result = response.json()
            
            if response.status_code == 200 and 'id' in result:
                logger.info(f"钉钉表格写入成功: record_id={result['id']}")
                return True
            else:
                logger.error(f"钉钉表格写入失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"钉钉表格写入异常: {e}")
            return False
    
    def add_records(self, records: List[Dict[str, Any]]) -> bool:
        """
        批量添加记录到钉钉表格
        
        Args:
            records: 记录列表
        
        Returns:
            bool: 是否成功
        """
        if not self.is_configured():
            logger.warning("钉钉多维表格未配置，跳过写入")
            return False
        
        if not records:
            return True
        
        access_token = self._get_access_token()
        if not access_token:
            return False
        
        try:
            import requests
            
            url = f"https://api.dingtalk.com/v1.0/notable/bases/{self.base_id}/tables/{self.table_id}/records/batch"
            
            headers = {
                "x-acs-dingtalk-access-token": access_token,
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
            
            if response.status_code == 200:
                logger.info(f"钉钉表格批量写入成功: {len(records)} 条记录")
                return True
            else:
                logger.error(f"钉钉表格批量写入失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"钉钉表格批量写入异常: {e}")
            return False
    
    def _convert_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换记录格式，适配钉钉多维表格字段类型
        
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
                
                # 时间格式转换（钉钉使用毫秒时间戳）
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
    
    def sync_from_database(self, db_path: str, since: Optional[datetime] = None) -> int:
        """
        从数据库同步记录到钉钉表格
        
        Args:
            db_path: 数据库路径
            since: 起始时间（可选）
        
        Returns:
            int: 同步的记录数
        """
        if not self.is_configured():
            logger.warning("钉钉多维表格未配置，跳过同步")
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
            
            logger.info(f"钉钉表格同步完成: {total_synced}/{len(records)} 条记录")
            return total_synced
            
        except Exception as e:
            logger.error(f"钉钉表格同步异常: {e}")
            return 0

