#!/usr/bin/env python3
"""
Plus版本功能测试脚本

测试 wxautox (Plus版) 的安装和基本功能
"""

import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_plus_import():
    """测试Plus版导入"""
    try:
        from wxautox4 import WeChat
        logger.info("✅ wxautox4 导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ wxautox4 导入失败: {e}")
        logger.error("💡 解决方案:")
        logger.error("   1. pip install wxautox")
        logger.error("   2. wxautox -a [激活码]")
        logger.error("   3. 购买地址: https://docs.wxauto.org/plus.html")
        return False

def test_adapter_initialization():
    """测试适配器初始化"""
    try:
        from modules.adapters.wxauto_adapter import WxAutoAdapter
        
        # 测试Plus版初始化
        adapter = WxAutoAdapter(
            whitelisted_groups=["测试群"],
            use_plus=True
        )
        
        if adapter.is_plus:
            logger.info("✅ 适配器使用Plus版成功")
            logger.info(f"📋 Plus版状态: {adapter.is_plus}")
            return True
        else:
            logger.warning("⚠️  适配器未使用Plus版")
            return False
            
    except Exception as e:
        logger.error(f"❌ 适配器初始化失败: {e}")
        return False

def test_config_loading():
    """测试配置文件加载"""
    try:
        import yaml
        
        with open('client/config/client_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        use_plus = config.get('wechat', {}).get('use_plus', False)
        
        if use_plus:
            logger.info("✅ 配置文件已启用Plus版")
            return True
        else:
            logger.warning("⚠️  配置文件未启用Plus版")
            return False
            
    except Exception as e:
        logger.error(f"❌ 配置文件加载失败: {e}")
        return False

def test_requirements():
    """测试依赖文件"""
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'wxautox' in content:
            logger.info("✅ requirements.txt 包含 wxautox")
            return True
        else:
            logger.warning("⚠️  requirements.txt 未包含 wxautox")
            return False
            
    except Exception as e:
        logger.error(f"❌ requirements.txt 读取失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("🧪 开始测试 Plus版本功能...")
    logger.info("=" * 50)
    
    tests = [
        ("Plus版导入测试", test_plus_import),
        ("适配器初始化测试", test_adapter_initialization),
        ("配置文件测试", test_config_loading),
        ("依赖文件测试", test_requirements),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} 异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    logger.info("\n" + "=" * 50)
    logger.info("📊 测试结果汇总:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 总体结果: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！Plus版本配置正确")
        return 0
    else:
        logger.error("⚠️  部分测试失败，请检查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
