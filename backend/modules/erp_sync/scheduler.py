"""
ERP同步调度器
定时执行同步任务
"""

import schedule
import time
import logging
from threading import Thread
from datetime import datetime

from .sync_service import UnifiedCustomerSyncService

logger = logging.getLogger(__name__)


class ERPSyncScheduler:
    """ERP同步调度器"""
    
    def __init__(self, sync_service: UnifiedCustomerSyncService, config: dict):
        """
        初始化调度器
        
        Args:
            sync_service: 同步服务实例
            config: 配置字典
        """
        self.sync_service = sync_service
        self.config = config
        self.is_running = False
        self.thread = None
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("[调度器] 已经在运行中")
            return
        
        logger.info("[调度器] 启动ERP同步调度器...")
        
        # 配置定时任务
        self._setup_schedules()
        
        # 在后台线程运行
        self.is_running = True
        self.thread = Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("[调度器] ERP同步调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        logger.info("[调度器] 停止ERP同步调度器...")
        self.is_running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("[调度器] ERP同步调度器已停止")
    
    def _setup_schedules(self):
        """设置定时任务"""
        # 1. ERP拉取任务
        if self.config.get('erp_pull', {}).get('enabled', True):
            interval = self.config.get('erp_pull', {}).get('interval', 3600)  # 默认1小时
            schedule.every(interval).seconds.do(self.sync_from_erp_job)
            logger.info(f"[调度器] 设置ERP拉取任务: 每{interval}秒执行一次")
        
        # 2. ERP推送任务
        if self.config.get('erp_push', {}).get('enabled', True):
            interval = self.config.get('erp_push', {}).get('interval', 1800)  # 默认30分钟
            schedule.every(interval).seconds.do(self.sync_to_erp_job)
            logger.info(f"[调度器] 设置ERP推送任务: 每{interval}秒执行一次")
        
        # 3. 立即执行一次（可选）
        if self.config.get('run_on_start', False):
            logger.info("[调度器] 启动时立即执行一次同步")
            self.sync_from_erp_job()
            time.sleep(5)  # 等待5秒
            self.sync_to_erp_job()
    
    def _run_scheduler(self):
        """运行调度循环"""
        logger.info("[调度器] 调度循环已启动")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"[调度器] 调度循环异常: {e}")
                time.sleep(60)  # 发生异常时等待1分钟
        
        logger.info("[调度器] 调度循环已退出")
    
    def sync_from_erp_job(self):
        """ERP拉取任务"""
        try:
            logger.info(f"[调度器] 开始执行ERP拉取任务 - {datetime.now()}")
            
            stats = self.sync_service.sync_from_erp(incremental=True)
            
            logger.info(f"[调度器] ERP拉取任务完成: {stats}")
            
        except Exception as e:
            logger.error(f"[调度器] ERP拉取任务失败: {e}")
    
    def sync_to_erp_job(self):
        """ERP推送任务"""
        try:
            logger.info(f"[调度器] 开始执行ERP推送任务 - {datetime.now()}")
            
            batch_size = self.config.get('erp_push', {}).get('batch_size', 50)
            stats = self.sync_service.sync_to_erp(batch_size=batch_size)
            
            logger.info(f"[调度器] ERP推送任务完成: {stats}")
            
        except Exception as e:
            logger.error(f"[调度器] ERP推送任务失败: {e}")
    
    def trigger_sync_now(self, direction: str = 'both'):
        """
        立即触发同步
        
        Args:
            direction: 同步方向 'pull'/'push'/'both'
        """
        if direction in ['pull', 'both']:
            self.sync_from_erp_job()
        
        if direction in ['push', 'both']:
            self.sync_to_erp_job()

