#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一错误处理器
提供统一的异常处理、重试机制、错误日志记录等
"""

import logging
import time
import functools
from typing import Callable, Optional, Type, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """错误分类"""
    NETWORK = "网络错误"
    DATABASE = "数据库错误"
    LLM_API = "大模型API错误"
    ERP_API = "ERP API错误"
    VALIDATION = "数据验证错误"
    BUSINESS_LOGIC = "业务逻辑错误"
    SYSTEM = "系统错误"
    UNKNOWN = "未知错误"


@dataclass
class ErrorContext:
    """错误上下文"""
    category: ErrorCategory
    operation: str
    error_type: str
    error_message: str
    timestamp: datetime
    retry_count: int = 0
    resolved: bool = False
    metadata: dict = None


class RetryConfig:
    """重试配置"""
    
    def __init__(self, 
                 max_attempts: int = 3,
                 initial_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_backoff: bool = True,
                 backoff_factor: float = 2.0):
        """
        初始化重试配置
        
        Args:
            max_attempts: 最大重试次数
            initial_delay: 初始延迟（秒）
            max_delay: 最大延迟（秒）
            exponential_backoff: 是否使用指数退避
            backoff_factor: 退避因子
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_backoff = exponential_backoff
        self.backoff_factor = backoff_factor
    
    def get_delay(self, attempt: int) -> float:
        """计算延迟时间"""
        if self.exponential_backoff:
            delay = self.initial_delay * (self.backoff_factor ** attempt)
        else:
            delay = self.initial_delay
        
        return min(delay, self.max_delay)


class ErrorHandler:
    """错误处理器"""
    
    # 默认重试配置
    DEFAULT_RETRY_CONFIGS = {
        ErrorCategory.NETWORK: RetryConfig(max_attempts=3, initial_delay=2.0),
        ErrorCategory.LLM_API: RetryConfig(max_attempts=3, initial_delay=1.0),
        ErrorCategory.ERP_API: RetryConfig(max_attempts=2, initial_delay=3.0),
        ErrorCategory.DATABASE: RetryConfig(max_attempts=2, initial_delay=1.0),
    }
    
    def __init__(self, db=None):
        """
        初始化错误处理器
        
        Args:
            db: 数据库实例（用于记录错误日志）
        """
        self.db = db
        self.error_history = []
        self._create_error_log_table()
    
    def _create_error_log_table(self):
        """创建错误日志表"""
        if not self.db:
            return
        
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    operation TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    retry_count INTEGER,
                    resolved INTEGER,
                    metadata TEXT,
                    created_at TEXT
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_logs_created_at 
                ON error_logs(created_at)
            """)
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.warning(f"创建错误日志表失败: {e}")
    
    def with_retry(self, 
                   category: ErrorCategory = ErrorCategory.UNKNOWN,
                   retry_config: RetryConfig = None,
                   on_retry: Callable = None,
                   on_failure: Callable = None):
        """
        重试装饰器
        
        用法:
            @error_handler.with_retry(
                category=ErrorCategory.LLM_API,
                on_retry=lambda e, attempt: print(f"重试 {attempt}")
            )
            def call_llm_api():
                ...
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 获取重试配置
                config = retry_config or self.DEFAULT_RETRY_CONFIGS.get(
                    category, 
                    RetryConfig()
                )
                
                last_error = None
                
                for attempt in range(config.max_attempts):
                    try:
                        result = func(*args, **kwargs)
                        
                        # 如果之前失败过，记录恢复
                        if attempt > 0:
                            logger.info(
                                f"✅ 重试成功: {func.__name__} "
                                f"(第{attempt + 1}次尝试)"
                            )
                        
                        return result
                    
                    except Exception as e:
                        last_error = e
                        
                        # 记录错误
                        error_ctx = self._create_error_context(
                            category=category,
                            operation=func.__name__,
                            error=e,
                            retry_count=attempt
                        )
                        self._log_error(error_ctx)
                        
                        # 最后一次尝试失败
                        if attempt == config.max_attempts - 1:
                            logger.error(
                                f"❌ 重试失败: {func.__name__} "
                                f"({config.max_attempts}次尝试后仍失败)"
                            )
                            
                            # 调用失败回调
                            if on_failure:
                                try:
                                    on_failure(e, attempt + 1)
                                except:
                                    pass
                            
                            raise
                        
                        # 计算延迟
                        delay = config.get_delay(attempt)
                        
                        logger.warning(
                            f"⚠️  操作失败，{delay:.1f}秒后重试: {func.__name__} "
                            f"(第{attempt + 1}/{config.max_attempts}次尝试)"
                        )
                        
                        # 调用重试回调
                        if on_retry:
                            try:
                                on_retry(e, attempt + 1)
                            except:
                                pass
                        
                        time.sleep(delay)
                
                # 理论上不会到这里
                raise last_error
            
            return wrapper
        return decorator
    
    def safe_execute(self,
                    func: Callable,
                    category: ErrorCategory = ErrorCategory.UNKNOWN,
                    default_return: Any = None,
                    log_error: bool = True) -> Any:
        """
        安全执行函数（捕获所有异常）
        
        Args:
            func: 要执行的函数
            category: 错误分类
            default_return: 发生错误时的默认返回值
            log_error: 是否记录错误
        
        Returns:
            函数返回值或默认值
        """
        try:
            return func()
        except Exception as e:
            if log_error:
                error_ctx = self._create_error_context(
                    category=category,
                    operation=func.__name__,
                    error=e
                )
                self._log_error(error_ctx)
            
            logger.error(f"安全执行失败: {func.__name__}: {e}")
            return default_return
    
    def _create_error_context(self,
                             category: ErrorCategory,
                             operation: str,
                             error: Exception,
                             retry_count: int = 0) -> ErrorContext:
        """创建错误上下文"""
        return ErrorContext(
            category=category,
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=datetime.now(),
            retry_count=retry_count,
            metadata={
                'traceback': None  # TODO: 添加堆栈跟踪
            }
        )
    
    def _log_error(self, error_ctx: ErrorContext):
        """记录错误日志"""
        # 1. 添加到内存历史
        self.error_history.append(error_ctx)
        
        # 2. 保存到数据库
        if self.db:
            try:
                import json
                conn = self.db.connect()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO error_logs 
                    (category, operation, error_type, error_message,
                     retry_count, resolved, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    error_ctx.category.value,
                    error_ctx.operation,
                    error_ctx.error_type,
                    error_ctx.error_message,
                    error_ctx.retry_count,
                    1 if error_ctx.resolved else 0,
                    json.dumps(error_ctx.metadata) if error_ctx.metadata else None,
                    error_ctx.timestamp.isoformat()
                ))
                
                conn.commit()
                conn.close()
            
            except Exception as e:
                logger.warning(f"保存错误日志失败: {e}")
    
    def get_error_stats(self, hours: int = 24) -> dict:
        """
        获取错误统计
        
        Args:
            hours: 统计最近多少小时
        
        Returns:
            统计数据
        """
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [
            e for e in self.error_history
            if e.timestamp >= cutoff_time
        ]
        
        # 按分类统计
        by_category = {}
        for error in recent_errors:
            category = error.category.value
            if category not in by_category:
                by_category[category] = 0
            by_category[category] += 1
        
        # 按操作统计
        by_operation = {}
        for error in recent_errors:
            op = error.operation
            if op not in by_operation:
                by_operation[op] = 0
            by_operation[op] += 1
        
        return {
            'total_errors': len(recent_errors),
            'by_category': by_category,
            'by_operation': by_operation,
            'most_common_error': max(by_operation, key=by_operation.get) if by_operation else None
        }


# 全局错误处理器实例
_global_handler = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_handler
    
    if _global_handler is None:
        _global_handler = ErrorHandler()
    
    return _global_handler


# 使用示例
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    handler = ErrorHandler()
    
    # 示例1: 使用重试装饰器
    @handler.with_retry(
        category=ErrorCategory.NETWORK,
        on_retry=lambda e, attempt: print(f"  重试第{attempt}次...")
    )
    def unstable_network_call():
        import random
        if random.random() < 0.7:  # 70%失败率
            raise ConnectionError("网络连接失败")
        return "Success!"
    
    try:
        result = unstable_network_call()
        print(f"结果: {result}")
    except:
        print("最终失败")
    
    # 示例2: 安全执行
    result = handler.safe_execute(
        lambda: 1 / 0,  # 故意制造错误
        category=ErrorCategory.SYSTEM,
        default_return="默认值"
    )
    print(f"\n安全执行结果: {result}")
    
    # 统计
    stats = handler.get_error_stats()
    print(f"\n错误统计: {stats}")

