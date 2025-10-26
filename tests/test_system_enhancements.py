#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统增强功能测试
测试监控、错误处理、性能优化等新增功能
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
import time
from core.system_monitor import SystemMonitor, get_system_monitor
from core.error_handler import ErrorHandler, ErrorCategory
from core.performance_optimizer import CacheManager, get_cache
# from modules.learning_loop import KnowledgeLearner  # 已废弃


class TestSystemMonitor(unittest.TestCase):
    """测试系统监控"""
    
    def setUp(self):
        self.monitor = SystemMonitor()
    
    def test_collect_metrics(self):
        """测试指标采集"""
        metrics = self.monitor.collect_metrics()
        
        self.assertGreaterEqual(metrics.cpu_percent, 0)
        self.assertGreaterEqual(metrics.memory_percent, 0)
        self.assertGreaterEqual(metrics.disk_percent, 0)
    
    def test_performance_tracking(self):
        """测试性能追踪"""
        @self.monitor.track_operation('test_op')
        def test_func():
            time.sleep(0.01)
            return "done"
        
        result = test_func()
        self.assertEqual(result, "done")
        
        # 检查统计
        dashboard = self.monitor.get_dashboard_data()
        self.assertIn('performance', dashboard)
    
    def test_global_instance(self):
        """测试全局实例"""
        monitor1 = get_system_monitor()
        monitor2 = get_system_monitor()
        self.assertIs(monitor1, monitor2)


class TestErrorHandler(unittest.TestCase):
    """测试错误处理"""
    
    def setUp(self):
        self.handler = ErrorHandler()
    
    def test_safe_execute(self):
        """测试安全执行"""
        # 成功情况
        result = self.handler.safe_execute(
            lambda: 10 + 20,
            default_return=0
        )
        self.assertEqual(result, 30)
        
        # 失败情况
        result = self.handler.safe_execute(
            lambda: 1 / 0,
            default_return=-1
        )
        self.assertEqual(result, -1)
    
    def test_retry_decorator(self):
        """测试重试装饰器"""
        attempts = [0]
        
        @self.handler.with_retry(category=ErrorCategory.NETWORK)
        def unstable_func():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("网络错误")
            return "success"
        
        result = unstable_func()
        self.assertEqual(result, "success")
        self.assertGreaterEqual(attempts[0], 2)


class TestCacheManager(unittest.TestCase):
    """测试缓存管理"""
    
    def setUp(self):
        self.cache = CacheManager(default_ttl=60, max_size=10)
    
    def test_cache_operations(self):
        """测试缓存基本操作"""
        # 设置
        self.cache.set('key1', 'value1')
        
        # 获取
        value = self.cache.get('key1')
        self.assertEqual(value, 'value1')
        
        # 不存在的键
        value = self.cache.get('nonexistent')
        self.assertIsNone(value)
    
    def test_cache_decorator(self):
        """测试缓存装饰器"""
        call_count = [0]
        
        @self.cache.cached(ttl=10)
        def expensive_func(x):
            call_count[0] += 1
            return x * 2
        
        # 第一次调用
        result1 = expensive_func(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count[0], 1)
        
        # 第二次调用（缓存命中）
        result2 = expensive_func(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count[0], 1)  # 没有增加
    
    def test_cache_stats(self):
        """测试缓存统计"""
        self.cache.set('k1', 'v1')
        self.cache.get('k1')  # hit
        self.cache.get('k2')  # miss
        
        stats = self.cache.get_stats()
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
    
    def test_global_cache(self):
        """测试全局缓存"""
        cache1 = get_cache()
        cache2 = get_cache()
        self.assertIs(cache1, cache2)


# class TestKnowledgeLearner(unittest.TestCase):
#     """测试知识学习器 - 已废弃"""
#     
#     def setUp(self):
#         self.learner = KnowledgeLearner(review_threshold=0.80)
#     
#     def test_process_knowledge(self):
#         """测试知识点处理"""
#         knowledge_points = [
#             {
#                 'question': '产品价格是多少？',
#                 'answer': '基础版998元',
#                 'confidence': 0.85,
#                 'type': '价格咨询'
#             }
#         ]
#         
#         result = self.learner.process_knowledge_points(
#             knowledge_points,
#             'test_session'
#         )
#         
#         self.assertIn('auto_added', result)
#         self.assertIn('pending_review', result)


if __name__ == '__main__':
    unittest.main()

