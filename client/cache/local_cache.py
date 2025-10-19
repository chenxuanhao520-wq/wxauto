#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地加密缓存
用于离线消息队列和临时数据存储
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class LocalCache:
    """本地加密缓存"""
    
    def __init__(self, cache_dir: str = "client_cache", encryption_key: Optional[bytes] = None):
        """
        初始化本地缓存
        
        Args:
            cache_dir: 缓存目录
            encryption_key: 加密密钥（AES-256）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 加密
        if encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            # ✅ 修复：先检查是否存在已有密钥
            key_file = self.cache_dir / '.key'
            if key_file.exists():
                # 读取现有密钥
                key = key_file.read_bytes()
                self.cipher = Fernet(key)
                logger.info("✅ 加载现有加密密钥")
            else:
                # 生成新密钥
                key = Fernet.generate_key()
                self.cipher = Fernet(key)
                # 保存密钥
                key_file.write_bytes(key)
                logger.info("✅ 生成新的加密密钥")
        
        # 离线消息队列文件
        self.offline_queue_file = self.cache_dir / 'offline_queue.enc'
    
    def save_message(self, message: Dict) -> bool:
        """
        保存消息到缓存（加密）
        
        Args:
            message: 消息数据
        
        Returns:
            是否成功
        """
        try:
            # 添加时间戳
            message['cached_at'] = datetime.now().isoformat()
            
            # 序列化
            json_data = json.dumps(message, ensure_ascii=False)
            
            # 加密
            encrypted = self.cipher.encrypt(json_data.encode())
            
            # 保存到文件
            cache_file = self.cache_dir / f"{message['id']}.enc"
            cache_file.write_bytes(encrypted)
            
            logger.debug(f"消息已缓存: {message['id']}")
            return True
        
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
            return False
    
    def load_message(self, message_id: str) -> Optional[Dict]:
        """
        加载缓存的消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            消息数据
        """
        try:
            cache_file = self.cache_dir / f"{message_id}.enc"
            
            if not cache_file.exists():
                return None
            
            # 读取加密数据
            encrypted = cache_file.read_bytes()
            
            # 解密
            decrypted = self.cipher.decrypt(encrypted)
            
            # 反序列化
            message = json.loads(decrypted.decode())
            
            return message
        
        except Exception as e:
            logger.error(f"加载消息失败: {e}")
            return None
    
    def add_to_offline_queue(self, message: Dict) -> bool:
        """
        添加到离线消息队列
        
        Args:
            message: 消息数据
        
        Returns:
            是否成功
        """
        try:
            # 加载现有队列
            queue = self.get_offline_queue()
            
            # 添加新消息
            queue.append({
                'message': message,
                'queued_at': datetime.now().isoformat(),
                'retry_count': 0
            })
            
            # 序列化并加密
            json_data = json.dumps(queue, ensure_ascii=False)
            encrypted = self.cipher.encrypt(json_data.encode())
            
            # 保存
            self.offline_queue_file.write_bytes(encrypted)
            
            logger.info(f"消息已加入离线队列: {len(queue)}条")
            return True
        
        except Exception as e:
            logger.error(f"添加离线队列失败: {e}")
            return False
    
    def get_offline_queue(self) -> List[Dict]:
        """
        获取离线消息队列
        
        Returns:
            消息列表
        """
        try:
            if not self.offline_queue_file.exists():
                return []
            
            # 读取并解密
            encrypted = self.offline_queue_file.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            
            # 反序列化
            queue = json.loads(decrypted.decode())
            
            return queue
        
        except Exception as e:
            logger.error(f"读取离线队列失败: {e}")
            return []
    
    def clear_offline_queue(self) -> bool:
        """清空离线队列"""
        try:
            if self.offline_queue_file.exists():
                self.offline_queue_file.unlink()
            logger.info("离线队列已清空")
            return True
        except Exception as e:
            logger.error(f"清空队列失败: {e}")
            return False
    
    def cleanup_old_cache(self, days: int = 7) -> int:
        """
        清理旧缓存
        
        Args:
            days: 保留天数
        
        Returns:
            删除的文件数
        """
        from datetime import timedelta
        
        count = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            for cache_file in self.cache_dir.glob('*.enc'):
                if cache_file.stat().st_mtime < cutoff_date.timestamp():
                    cache_file.unlink()
                    count += 1
            
            logger.info(f"清理了 {count} 个旧缓存文件")
            return count
        
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return count

