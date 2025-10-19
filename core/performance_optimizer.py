#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化器（精简版）
提供缓存和数据库优化功能
"""

import logging
import hashlib
from typing import Any, Callable, Optional, Dict
from datetime import datetime, timedelta
from functools import wraps
import threading

logger = logging.getLogger(__name__)


# ==================== 缓存管理器 ====================

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        """
        初始化缓存管理器
        
        Args:
            default_ttl: 默认过期时间（秒）
            max_size: 最大缓存项数
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache = {}  # {key: (value, expire_time)}
        self._lock = threading.RLock()
        self._stats = {'hits': 0, 'misses': 0, 'evictions': 0}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            value, expire_time = self._cache[key]
            
            # 检查是否过期
            if datetime.now() > expire_time:
                del self._cache[key]
                self._stats['misses'] += 1
                return None
            
            self._stats['hits'] += 1
            return value
    
    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        with self._lock:
            # 检查容量
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_oldest()
            
            expire_time = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
            self._cache[key] = (value, expire_time)
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("缓存已清空")
    
    def _evict_oldest(self):
        """驱逐最旧的项"""
        if not self._cache:
            return
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]
        self._stats['evictions'] += 1
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self._lock:
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total if total > 0 else 0
            
            return {
                'size': len(self._cache),
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': hit_rate
            }
    
    def cached(self, ttl: int = None):
        """缓存装饰器"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = self._generate_key(func.__name__, args, kwargs)
                
                # 尝试从缓存获取
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def _generate_key(func_name: str, args, kwargs) -> str:
        """生成缓存键"""
        key_parts = [func_name]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()


# ==================== 数据库优化器 ====================

class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self, db):
        """初始化"""
        self.db = db
    
    def optimize_indexes(self):
        """优化索引"""
        if not self.db:
            return
        
        logger.info("优化数据库索引...")
        conn = self.db.connect()
        cursor = conn.cursor()
        
        # 核心索引
        indexes = [
            ("idx_messages_session", "messages", "session_key"),
            ("idx_messages_time", "messages", "received_at"),
            ("idx_sessions_contact", "sessions", "contact_id"),
        ]
        
        created = 0
        for idx_name, table, column in indexes:
            try:
                cursor.execute(f"""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name=?
                """, (idx_name,))
                
                if not cursor.fetchone():
                    cursor.execute(f"CREATE INDEX {idx_name} ON {table}({column})")
                    created += 1
                    logger.info(f"  ✅ 创建索引: {idx_name}")
            except Exception as e:
                logger.warning(f"  ⚠️  索引失败: {idx_name}")
        
        conn.commit()
        conn.close()
        logger.info(f"索引优化完成，新建 {created} 个")
    
    def cleanup_old_data(self, days: int = 90):
        """清理旧数据"""
        if not self.db:
            return
        
        logger.info(f"清理 {days} 天前的数据...")
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM messages
            WHERE received_at < datetime('now', ?)
        """, (f'-{days} days',))
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        logger.info(f"✅ 清理完成: 删除 {deleted} 条消息")
        return deleted


# ==================== 全局工具 ====================

# 全局缓存实例
_global_cache = None


def get_cache() -> CacheManager:
    """获取全局缓存"""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache


# 使用示例
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    cache = get_cache()
    
    # 缓存装饰器
    @cache.cached(ttl=10)
    def test_func(x):
        print(f"执行计算: {x}")
        return x * 2
    
    print(test_func(5))  # 执行
    print(test_func(5))  # 缓存命中
    print(f"缓存统计: {cache.get_stats()}")

