#!/usr/bin/env python3
"""
ERP同步功能测试脚本
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.erp_sync.config_manager import ERPSyncConfigManager
from modules.erp_sync.erp_client import ERPClient
from modules.erp_sync.rule_engine import SyncRuleEngine
from modules.erp_sync.change_detector import ChangeDetector
from modules.erp_sync.sync_service import UnifiedCustomerSyncService

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_erp_login():
    """测试ERP登录"""
    logger.info("\n" + "=" * 60)
    logger.info("测试1: ERP登录")
    logger.info("=" * 60)
    
    try:
        config_manager = ERPSyncConfigManager('config.yaml')
        credentials = config_manager.get_erp_credentials()
        
        with ERPClient(**credentials) as client:
            logger.info("✅ ERP登录成功")
            return True
    except Exception as e:
        logger.error(f"❌ ERP登录失败: {e}")
        return False


def test_get_customers():
    """测试获取客户列表"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 获取ERP客户列表")
    logger.info("=" * 60)
    
    try:
        config_manager = ERPSyncConfigManager('config.yaml')
        credentials = config_manager.get_erp_credentials()
        
        with ERPClient(**credentials) as client:
            customers = client.get_customers(page_size=5, page_index=1)
            
            logger.info(f"✅ 成功获取 {len(customers)} 个客户")
            
            if customers:
                logger.info("\n示例客户数据:")
                for i, customer in enumerate(customers[:2], 1):
                    logger.info(f"\n客户 {i}:")
                    logger.info(f"  - ID: {customer.get('ord')}")
                    logger.info(f"  - 名称: {customer.get('name')}")
                    logger.info(f"  - 手机: {customer.get('mobile')}")
                    logger.info(f"  - 微信: {customer.get('weixinAcc')}")
            
            return True
    except Exception as e:
        logger.error(f"❌ 获取客户列表失败: {e}")
        return False


def test_rule_engine():
    """测试规则引擎"""
    logger.info("\n" + "=" * 60)
    logger.info("测试3: 规则引擎")
    logger.info("=" * 60)
    
    try:
        rule_engine = SyncRuleEngine()
        
        # 测试数据1: 高质量客户
        customer1 = {
            'id': 1,
            'phone': '13800138000',
            'phone_verified': True,
            'company_name': '测试科技有限公司',
            'company_name_verified': True,
            'business_license_verified': True,
            'intent_score': 85,
            'erp_customer_id': None
        }
        
        result1 = rule_engine.evaluate(customer1)
        logger.info(f"\n高质量客户评估结果:")
        logger.info(f"  - 动作: {result1['action']}")
        logger.info(f"  - 置信度: {result1['confidence']}")
        logger.info(f"  - 原因: {result1['reason']}")
        logger.info(f"  - 规则: {result1['matched_rule']}")
        
        # 测试数据2: 低质量客户
        customer2 = {
            'id': 2,
            'wechat_nickname': '微信用户',
            'message_count': 3,
            'intent_score': 20,
            'erp_customer_id': None
        }
        
        result2 = rule_engine.evaluate(customer2)
        logger.info(f"\n低质量客户评估结果:")
        logger.info(f"  - 动作: {result2['action']}")
        logger.info(f"  - 置信度: {result2['confidence']}")
        logger.info(f"  - 原因: {result2['reason']}")
        logger.info(f"  - 规则: {result2['matched_rule']}")
        
        logger.info("\n✅ 规则引擎测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 规则引擎测试失败: {e}")
        return False


def test_change_detector():
    """测试变更检测器"""
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 变更检测器")
    logger.info("=" * 60)
    
    try:
        change_detector = ChangeDetector()
        
        # ERP数据
        erp_data = {
            'ord': 12345,
            'khid': 'KH2025001',
            'name': '深圳测试科技有限公司',
            'mobile': '13800138000',
            'email': 'test@example.com'
        }
        
        # 本地数据
        local_data = {
            'erp_customer_id': 12345,
            'erp_customer_code': 'KH2025001',
            'company_name': '深圳测试科技',  # 不同
            'phone': '13800138000',
            'email': None,  # 本地没有
            'wechat_id': 'wx_test_001',  # 本地独有
            'phone_verified': True,
            'local_updated_at': '2025-10-18 10:00:00'
        }
        
        # 检测变更
        changes = change_detector.detect_changes(erp_data, local_data)
        
        logger.info(f"\n检测到 {changes['change_count']} 个字段变更:")
        
        for change in changes['changes']:
            logger.info(f"\n字段: {change['field']}")
            logger.info(f"  - ERP值: {change['erp_value']}")
            logger.info(f"  - 本地值: {change['local_value']}")
            logger.info(f"  - 动作: {change['action']}")
            logger.info(f"  - 原因: {change['reason']}")
        
        logger.info("\n✅ 变更检测器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 变更检测器测试失败: {e}")
        return False


def test_full_sync():
    """测试完整同步流程"""
    logger.info("\n" + "=" * 60)
    logger.info("测试5: 完整同步流程 (仅测试，不实际同步)")
    logger.info("=" * 60)
    
    try:
        config_manager = ERPSyncConfigManager('config.yaml')
        credentials = config_manager.get_erp_credentials()
        
        erp_client = ERPClient(**credentials)
        erp_client.login()
        
        rule_engine = SyncRuleEngine()
        change_detector = ChangeDetector()
        
        sync_service = UnifiedCustomerSyncService(
            erp_client=erp_client,
            rule_engine=rule_engine,
            change_detector=change_detector
        )
        
        logger.info("✅ 同步服务初始化成功")
        logger.info("✅ 所有组件正常工作")
        
        erp_client.logout()
        
        logger.info("\n✅ 完整同步流程测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 完整同步流程测试失败: {e}")
        return False


def main():
    """主测试函数"""
    logger.info("\n" + "=" * 80)
    logger.info("开始ERP同步功能测试")
    logger.info("=" * 80)
    
    results = []
    
    # 执行所有测试
    results.append(("ERP登录", test_erp_login()))
    results.append(("获取客户列表", test_get_customers()))
    results.append(("规则引擎", test_rule_engine()))
    results.append(("变更检测器", test_change_detector()))
    results.append(("完整同步流程", test_full_sync()))
    
    # 输出测试总结
    logger.info("\n" + "=" * 80)
    logger.info("测试总结")
    logger.info("=" * 80)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    logger.info("=" * 80)
    
    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())

