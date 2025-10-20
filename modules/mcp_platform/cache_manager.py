"""
智能缓存管理器
提供多级缓存、智能缓存键生成、统计监控等功能
"""

import hashlib
import json
import logging
from typing import Optional, Any, Dict, Callable
from datetime import datetime, timedelta
from functools import wraps
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheManager:
    """智能缓存管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化缓存管理器
        
        Args:
            config: 缓存配置字典
        """
        self.config = config or {}
        self.backend = self.config.get('backend', 'memory')
        
        # 内存缓存（使用 OrderedDict 实现 LRU）
        max_size = self.config.get('memory', {}).get('max_size', 1000)
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.expiry: Dict[str, datetime] = {}
        self.max_size = max_size
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'errors': 0
        }
        
        # 初始化后端
        self._init_backend()
        
        logger.info(f"✅ 缓存管理器初始化成功 (后端: {self.backend}, 最大容量: {max_size})")
    
    def _init_backend(self):
        """初始化缓存后端"""
        if self.backend == 'redis':
            try:
                import redis
                redis_config = self.config.get('redis', {})
                self.redis_client = redis.Redis(
                    host=redis_config.get('host', 'localhost'),
                    port=redis_config.get('port', 6379),
                    db=redis_config.get('db', 0),
                    password=redis_config.get('password', None),
                    decode_responses=True,
                    max_connections=redis_config.get('max_connections', 10)
                )
                # 测试连接
                self.redis_client.ping()
                logger.info(f"✅ Redis 缓存后端连接成功")
            except Exception as e:
                logger.warning(f"⚠️ Redis 连接失败，回退到内存缓存: {e}")
                self.backend = 'memory'
    
    def _generate_cache_key(self, service: str, method: str, *args, **kwargs) -> str:
        """
        生成缓存键
        基于服务名、方法名和参数生成唯一的缓存键
        
        Args:
            service: 服务名称
            method: 方法名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键字符串
        """
        # 过滤掉不应该影响缓存键的参数
        filtered_kwargs = {
            k: v for k, v in kwargs.items() 
            if k not in ['use_cache', 'cache_ttl', 'force_refresh']
        }
        
        # 构建键数据
        key_data = {
            'service': service,
            'method': method,
            'args': args,
            'kwargs': filtered_kwargs
        }
        
        # 序列化并哈希
        try:
            key_json = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
            key_hash = hashlib.md5(key_json.encode('utf-8')).hexdigest()
            
            # 生成可读的缓存键
            cache_key = f"mcp:{service}:{method}:{key_hash}"
            return cache_key
        except Exception as e:
            logger.error(f"❌ 缓存键生成失败: {e}")
            # 降级方案：使用简单哈希
            simple_key = f"{service}:{method}:{hash(str(args) + str(filtered_kwargs))}"
            return hashlib.md5(simple_key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        try:
            if self.backend == 'memory':
                return self._get_from_memory(key)
            elif self.backend == 'redis':
                return self._get_from_redis(key)
        except Exception as e:
            logger.error(f"❌ 获取缓存失败: {e}")
            self.stats['errors'] += 1
            return None
    
    def _get_from_memory(self, key: str) -> Optional[Any]:
        """从内存缓存获取"""
        # 检查是否过期
        if key in self.expiry:
            if datetime.now() > self.expiry[key]:
                # 已过期，删除
                del self.cache[key]
                del self.expiry[key]
                self.stats['evictions'] += 1
                self.stats['misses'] += 1
                logger.debug(f"⏰ 缓存过期: {key[:50]}...")
                return None
        
        # 获取值
        if key in self.cache:
            # LRU：将访问的项移到末尾
            self.cache.move_to_end(key)
            value = self.cache[key]
            self.stats['hits'] += 1
            logger.debug(f"✅ 缓存命中: {key[:50]}...")
            return value
        else:
            self.stats['misses'] += 1
            logger.debug(f"❌ 缓存未命中: {key[:50]}...")
            return None
    
    def _get_from_redis(self, key: str) -> Optional[Any]:
        """从 Redis 获取"""
        try:
            value = self.redis_client.get(key)
            if value:
                self.stats['hits'] += 1
                logger.debug(f"✅ Redis 缓存命中: {key[:50]}...")
                return json.loads(value)
            else:
                self.stats['misses'] += 1
                logger.debug(f"❌ Redis 缓存未命中: {key[:50]}...")
                return None
        except Exception as e:
            logger.error(f"❌ Redis 获取失败: {e}")
            self.stats['errors'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        try:
            if self.backend == 'memory':
                self._set_to_memory(key, value, ttl)
            elif self.backend == 'redis':
                self._set_to_redis(key, value, ttl)
            
            self.stats['sets'] += 1
            logger.debug(f"💾 缓存设置: {key[:50]}... (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"❌ 设置缓存失败: {e}")
            self.stats['errors'] += 1
    
    def _set_to_memory(self, key: str, value: Any, ttl: int):
        """设置到内存缓存"""
        # 如果缓存已满，删除最旧的项（LRU）
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.expiry:
                del self.expiry[oldest_key]
            self.stats['evictions'] += 1
            logger.debug(f"🗑️ LRU淘汰: {oldest_key[:50]}...")
        
        # 设置缓存
        self.cache[key] = value
        self.cache.move_to_end(key)  # 移到末尾（最新）
        self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    def _set_to_redis(self, key: str, value: Any, ttl: int):
        """设置到 Redis"""
        try:
            value_json = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(key, ttl, value_json)
        except Exception as e:
            logger.error(f"❌ Redis 设置失败: {e}")
            self.stats['errors'] += 1
    
    def delete(self, key: str):
        """删除缓存"""
        try:
            if self.backend == 'memory':
                if key in self.cache:
                    del self.cache[key]
                if key in self.expiry:
                    del self.expiry[key]
            elif self.backend == 'redis':
                self.redis_client.delete(key)
            
            logger.debug(f"🗑️ 缓存删除: {key[:50]}...")
        except Exception as e:
            logger.error(f"❌ 删除缓存失败: {e}")
            self.stats['errors'] += 1
    
    def clear(self):
        """清空所有缓存"""
        try:
            if self.backend == 'memory':
                self.cache.clear()
                self.expiry.clear()
            elif self.backend == 'redis':
                # 只删除 mcp: 前缀的键
                pattern = "mcp:*"
                for key in self.redis_client.scan_iter(pattern):
                    self.redis_client.delete(key)
            
            logger.info("🗑️ 缓存已清空")
        except Exception as e:
            logger.error(f"❌ 清空缓存失败: {e}")
            self.stats['errors'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            'backend': self.backend,
            'total_requests': total_requests,
            'cache_hits': self.stats['hits'],
            'cache_misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.1f}%",
            'hit_rate_value': hit_rate,
            'sets': self.stats['sets'],
            'evictions': self.stats['evictions'],
            'errors': self.stats['errors'],
            'cache_size': len(self.cache) if self.backend == 'memory' else 'N/A',
            'max_size': self.max_size if self.backend == 'memory' else 'N/A'
        }
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'errors': 0
        }
        logger.info("📊 缓存统计已重置")
    
    def cached(self, service_name: str, method_name: str, ttl: int = 3600):
        """
        缓存装饰器
        
        Args:
            service_name: 服务名称
            method_name: 方法名称
            ttl: 缓存有效期（秒）
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 检查是否禁用缓存
                use_cache = kwargs.get('use_cache', True)
                force_refresh = kwargs.get('force_refresh', False)
                
                if not use_cache or force_refresh:
                    return await func(*args, **kwargs)
                
                # 生成缓存键
                cache_key = self._generate_cache_key(
                    service_name, 
                    method_name, 
                    *args, 
                    **kwargs
                )
                
                # 尝试从缓存获取
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 调用原函数
                result = await func(*args, **kwargs)
                
                # 存入缓存
                cache_ttl = kwargs.get('cache_ttl', ttl)
                self.set(cache_key, result, cache_ttl)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 同步版本
                use_cache = kwargs.get('use_cache', True)
                force_refresh = kwargs.get('force_refresh', False)
                
                if not use_cache or force_refresh:
                    return func(*args, **kwargs)
                
                cache_key = self._generate_cache_key(
                    service_name, 
                    method_name, 
                    *args, 
                    **kwargs
                )
                
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                result = func(*args, **kwargs)
                cache_ttl = kwargs.get('cache_ttl', ttl)
                self.set(cache_key, result, cache_ttl)
                
                return result
            
            # 检查是否是异步函数
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        return f"<CacheManager(backend={self.backend}, size={stats['cache_size']}, hit_rate={stats['hit_rate']})>"

