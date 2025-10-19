#!/usr/bin/env python3
"""
ERP同步服务启动脚本
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from erp_sync.config_manager import ERPSyncConfigManager
from erp_sync.erp_client import ERPClient
from erp_sync.rule_engine import SyncRuleEngine
from erp_sync.change_detector import ChangeDetector
from erp_sync.sync_service import UnifiedCustomerSyncService
from erp_sync.scheduler import ERPSyncScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/erp_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("ERP智能同步服务启动")
    logger.info("=" * 60)
    
    try:
        # 1. 加载配置
        logger.info("[启动] 加载配置...")
        config_manager = ERPSyncConfigManager('config.yaml')
        
        if not config_manager.is_enabled():
            logger.warning("[启动] ERP集成未启用，退出")
            return
        
        # 2. 初始化ERP客户端
        logger.info("[启动] 初始化ERP客户端...")
        credentials = config_manager.get_erp_credentials()
        
        if not credentials['username'] or not credentials['password']:
            logger.error("[启动] ERP用户名或密码未配置，请检查config.yaml")
            logger.info("[启动] 配置路径: erp_integration.auth.username 和 erp_integration.auth.password")
            return
        
        erp_client = ERPClient(
            base_url=credentials['base_url'],
            username=credentials['username'],
            password=credentials['password']
        )
        
        # 登录ERP
        if not erp_client.login():
            logger.error("[启动] ERP登录失败，请检查用户名和密码")
            return
        
        # 3. 初始化规则引擎
        logger.info("[启动] 初始化规则引擎...")
        rule_engine = SyncRuleEngine()
        
        # 4. 初始化变更检测器
        logger.info("[启动] 初始化变更检测器...")
        change_detector = ChangeDetector()
        
        # 5. 初始化同步服务
        logger.info("[启动] 初始化同步服务...")
        sync_service = UnifiedCustomerSyncService(
            erp_client=erp_client,
            rule_engine=rule_engine,
            change_detector=change_detector
        )
        
        # 6. 启动调度器
        logger.info("[启动] 启动调度器...")
        scheduler = ERPSyncScheduler(
            sync_service=sync_service,
            config=config_manager.config
        )
        scheduler.start()
        
        logger.info("=" * 60)
        logger.info("✅ ERP智能同步服务已启动")
        logger.info("=" * 60)
        logger.info(f"ERP拉取间隔: {config_manager.get('erp_pull.interval')}秒")
        logger.info(f"ERP推送间隔: {config_manager.get('erp_push.interval')}秒")
        logger.info("按 Ctrl+C 停止服务")
        logger.info("=" * 60)
        
        # 保持运行
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n[停止] 收到停止信号...")
            scheduler.stop()
            erp_client.logout()
            logger.info("[停止] ERP同步服务已停止")
    
    except Exception as e:
        logger.error(f"[错误] 启动失败: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

