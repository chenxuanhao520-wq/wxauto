#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一系统监控器
整合系统监控、性能追踪、告警管理于一体
"""

import psutil
import logging
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import deque
from functools import wraps

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

@dataclass
class SystemMetrics:
    """系统指标快照"""
    # 系统资源
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    
    # 业务指标
    active_sessions: int = 0
    messages_1h: int = 0
    messages_24h: int = 0
    avg_response_ms: float = 0.0
    tokens_24h: int = 0
    
    # 时间戳
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AlertLevel(Enum):
    """告警级别"""
    INFO = "信息"
    WARNING = "警告"
    ERROR = "错误"
    CRITICAL = "严重"


@dataclass
class Alert:
    """告警"""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    metric_name: str = ""
    metric_value: float = 0.0


# ==================== 统一监控器 ====================

class SystemMonitor:
    """
    统一系统监控器
    
    功能：
    1. 系统资源监控（CPU、内存、磁盘）
    2. 业务指标监控（消息、响应、Token）
    3. 性能追踪（慢操作、失败）
    4. 告警管理（规则、通知）
    """
    
    def __init__(self, db=None, alert_callback: Callable = None):
        """
        初始化
        
        Args:
            db: 数据库实例
            alert_callback: 告警回调函数
        """
        self.db = db
        self.alert_callback = alert_callback
        
        # 指标历史（最近24小时，每分钟一个）
        self._metrics_history = deque(maxlen=1440)
        
        # 性能追踪
        self._operation_stats = {}  # {operation: {count, total_time, errors}}
        
        # 告警管理
        self._active_alerts = []
        self._alert_rules = self._init_alert_rules()
        self._last_alert_time = {}  # 告警抑制
    
    # ==================== 系统监控 ====================
    
    def collect_metrics(self) -> SystemMetrics:
        """采集系统指标"""
        # 系统资源
        cpu = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 业务指标
        business = self._get_business_metrics()
        
        metrics = SystemMetrics(
            cpu_percent=cpu,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            active_sessions=business['active_sessions'],
            messages_1h=business['messages_1h'],
            messages_24h=business['messages_24h'],
            avg_response_ms=business['avg_response_ms'],
            tokens_24h=business['tokens_24h']
        )
        
        # 保存历史
        self._metrics_history.append(metrics)
        
        # 检查告警
        self._check_alerts(metrics)
        
        return metrics
    
    def _get_business_metrics(self) -> Dict:
        """获取业务指标"""
        metrics = {
            'active_sessions': 0,
            'messages_1h': 0,
            'messages_24h': 0,
            'avg_response_ms': 0.0,
            'tokens_24h': 0
        }
        
        if not self.db:
            return metrics
        
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # 活跃会话
            cursor.execute("""
                SELECT COUNT(DISTINCT session_key)
                FROM sessions
                WHERE last_active_at >= datetime('now', '-30 minutes')
            """)
            row = cursor.fetchone()
            metrics['active_sessions'] = row[0] if row else 0
            
            # 消息数
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN received_at >= datetime('now', '-1 hour') THEN 1 ELSE 0 END),
                    SUM(CASE WHEN received_at >= datetime('now', '-24 hours') THEN 1 ELSE 0 END),
                    AVG(CASE WHEN received_at >= datetime('now', '-1 hour') THEN latency_ms ELSE NULL END)
                FROM messages
            """)
            row = cursor.fetchone()
            if row:
                metrics['messages_1h'] = row[0] or 0
                metrics['messages_24h'] = row[1] or 0
                metrics['avg_response_ms'] = row[2] or 0.0
            
            # Token使用
            cursor.execute("""
                SELECT SUM(tokens_total)
                FROM messages
                WHERE received_at >= datetime('now', '-24 hours')
            """)
            row = cursor.fetchone()
            metrics['tokens_24h'] = row[0] if row and row[0] else 0
            
            conn.close()
        except Exception as e:
            logger.warning(f"获取业务指标失败: {e}")
        
        return metrics
    
    def get_dashboard_data(self) -> Dict:
        """获取监控大盘数据"""
        latest = self.collect_metrics()
        
        return {
            'system': {
                'cpu': f"{latest.cpu_percent:.1f}%",
                'memory': f"{latest.memory_percent:.1f}%",
                'disk': f"{latest.disk_percent:.1f}%"
            },
            'business': {
                'active_sessions': latest.active_sessions,
                'messages_1h': latest.messages_1h,
                'messages_24h': latest.messages_24h,
                'avg_response_ms': f"{latest.avg_response_ms:.0f}ms",
                'tokens_24h': latest.tokens_24h,
                'cost_24h': f"¥{latest.tokens_24h / 1_000_000 * 0.1:.2f}"
            },
            'alerts': {
                'total': len(self._active_alerts),
                'critical': len([a for a in self._active_alerts if a.level == AlertLevel.CRITICAL]),
                'active': [{'level': a.level.value, 'title': a.title} for a in self._active_alerts[:5]]
            },
            'performance': self._get_performance_summary()
        }
    
    # ==================== 性能追踪 ====================
    
    def track_operation(self, operation: str):
        """
        性能追踪装饰器
        
        用法:
            @monitor.track_operation('llm_call')
            def call_llm():
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                error = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    duration_ms = (time.time() - start) * 1000
                    self._record_operation(operation, duration_ms, error is None)
                    
                    if duration_ms > 3000:
                        logger.warning(f"⚠️  慢操作: {operation} 耗时 {duration_ms:.0f}ms")
            
            return wrapper
        return decorator
    
    def _record_operation(self, operation: str, duration_ms: float, success: bool):
        """记录操作性能"""
        if operation not in self._operation_stats:
            self._operation_stats[operation] = {
                'count': 0,
                'total_time': 0,
                'errors': 0,
                'max_time': 0
            }
        
        stats = self._operation_stats[operation]
        stats['count'] += 1
        stats['total_time'] += duration_ms
        stats['max_time'] = max(stats['max_time'], duration_ms)
        if not success:
            stats['errors'] += 1
    
    def _get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if not self._operation_stats:
            return {}
        
        summary = {}
        for op, stats in self._operation_stats.items():
            summary[op] = {
                'count': stats['count'],
                'avg_ms': stats['total_time'] / stats['count'] if stats['count'] > 0 else 0,
                'max_ms': stats['max_time'],
                'error_rate': stats['errors'] / stats['count'] if stats['count'] > 0 else 0
            }
        
        return summary
    
    # ==================== 告警管理 ====================
    
    def _init_alert_rules(self) -> Dict:
        """初始化告警规则"""
        return {
            'cpu_high': {'threshold': 80, 'level': AlertLevel.WARNING},
            'memory_high': {'threshold': 85, 'level': AlertLevel.WARNING},
            'disk_full': {'threshold': 90, 'level': AlertLevel.ERROR},
            'response_slow': {'threshold': 5000, 'level': AlertLevel.WARNING},
        }
    
    def _check_alerts(self, metrics: SystemMetrics):
        """检查告警"""
        # CPU告警
        if metrics.cpu_percent > self._alert_rules['cpu_high']['threshold']:
            self._trigger_alert(
                AlertLevel.WARNING,
                'CPU使用率过高',
                f'当前: {metrics.cpu_percent:.1f}%',
                'cpu_percent',
                metrics.cpu_percent
            )
        
        # 内存告警
        if metrics.memory_percent > self._alert_rules['memory_high']['threshold']:
            self._trigger_alert(
                AlertLevel.WARNING,
                '内存使用率过高',
                f'当前: {metrics.memory_percent:.1f}%',
                'memory_percent',
                metrics.memory_percent
            )
        
        # 磁盘告警
        if metrics.disk_percent > self._alert_rules['disk_full']['threshold']:
            self._trigger_alert(
                AlertLevel.ERROR,
                '磁盘空间不足',
                f'当前: {metrics.disk_percent:.1f}%',
                'disk_percent',
                metrics.disk_percent
            )
        
        # 响应慢告警
        if metrics.avg_response_ms > self._alert_rules['response_slow']['threshold']:
            self._trigger_alert(
                AlertLevel.WARNING,
                '响应时间过慢',
                f'平均: {metrics.avg_response_ms:.0f}ms',
                'avg_response_ms',
                metrics.avg_response_ms
            )
    
    def _trigger_alert(self, level: AlertLevel, title: str, message: str,
                      metric_name: str, metric_value: float):
        """触发告警"""
        # 检查告警抑制（15分钟内不重复）
        alert_key = f"{metric_name}_{level.value}"
        if alert_key in self._last_alert_time:
            if datetime.now() - self._last_alert_time[alert_key] < timedelta(minutes=15):
                return
        
        alert = Alert(
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(),
            metric_name=metric_name,
            metric_value=metric_value
        )
        
        self._active_alerts.append(alert)
        self._last_alert_time[alert_key] = datetime.now()
        
        # 日志
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(level, logging.WARNING)
        
        logger.log(log_level, f"🚨 [{level.value}] {title}: {message}")
        
        # 回调通知
        if self.alert_callback:
            try:
                self.alert_callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")
    
    # ==================== 工具方法 ====================
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        latest = list(self._metrics_history)[-1] if self._metrics_history else None
        
        return {
            'metrics': {
                'cpu': latest.cpu_percent if latest else 0,
                'memory': latest.memory_percent if latest else 0,
                'disk': latest.disk_percent if latest else 0
            } if latest else {},
            'performance': self._get_performance_summary(),
            'alerts': {
                'total': len(self._active_alerts),
                'by_level': {
                    level.value: len([a for a in self._active_alerts if a.level == level])
                    for level in AlertLevel
                }
            }
        }


# 全局实例
_global_monitor = None


def get_system_monitor(db=None) -> SystemMonitor:
    """获取全局监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = SystemMonitor(db=db)
    return _global_monitor


# 使用示例
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    monitor = SystemMonitor()
    
    # 采集指标
    metrics = monitor.collect_metrics()
    print(f"CPU: {metrics.cpu_percent}%")
    print(f"内存: {metrics.memory_percent}%")
    print(f"磁盘: {metrics.disk_percent}%")
    
    # 性能追踪
    @monitor.track_operation('test_operation')
    def slow_operation():
        time.sleep(0.1)
        return "done"
    
    slow_operation()
    
    # 获取大盘数据
    dashboard = monitor.get_dashboard_data()
    print(f"\n监控大盘: {dashboard}")

