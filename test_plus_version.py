#!/usr/bin/env python3
"""
双版本检测工具

检测 wxauto 开源版和 Plus版 (wxautox) 的安装和功能
支持智能版本选择和降级策略
"""

import sys
import logging
import yaml

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_open_source_import():
    """测试开源版导入"""
    try:
        from wxauto import WeChat
        logger.info("✅ wxauto (开源版) 导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ wxauto (开源版) 导入失败: {e}")
        logger.error("💡 解决方案: pip install wxauto")
        return False

def test_plus_import():
    """测试Plus版导入"""
    try:
        from wxautox4 import WeChat
        logger.info("✅ wxautox4 (Plus版) 导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ wxautox4 (Plus版) 导入失败: {e}")
        logger.error("💡 解决方案:")
        logger.error("   1. pip install wxautox")
        logger.error("   2. wxautox -a [激活码]")
        logger.error("   3. 购买地址: https://docs.wxauto.org/plus.html")
        return False

def test_adapter_auto_strategy():
    """测试自动检测策略"""
    try:
        from modules.adapters.wxauto_adapter import WxAutoAdapter
        
        # 测试自动检测策略
        adapter = WxAutoAdapter(
            whitelisted_groups=["测试群"],
            version_strategy="auto",
            prefer_plus=True,
            fallback_enabled=True
        )
        
        version_info = adapter.get_version_info()
        status = adapter.get_version_status()
        
        logger.info(f"✅ 自动检测策略成功")
        logger.info(f"📋 当前版本: {status}")
        logger.info(f"📊 版本信息: {version_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 自动检测策略失败: {e}")
        return False

def test_adapter_plus_strategy():
    """测试强制Plus版策略"""
    try:
        from modules.adapters.wxauto_adapter import WxAutoAdapter
        
        # 测试强制Plus版策略
        adapter = WxAutoAdapter(
            whitelisted_groups=["测试群"],
            version_strategy="plus",
            fallback_enabled=True
        )
        
        if adapter.is_plus:
            logger.info("✅ 强制Plus版策略成功")
            return True
        else:
            logger.warning("⚠️  强制Plus版策略降级到开源版")
            return True  # 降级成功也算成功
            
    except Exception as e:
        logger.error(f"❌ 强制Plus版策略失败: {e}")
        return False

def test_adapter_open_source_strategy():
    """测试强制开源版策略"""
    try:
        from modules.adapters.wxauto_adapter import WxAutoAdapter
        
        # 测试强制开源版策略
        adapter = WxAutoAdapter(
            whitelisted_groups=["测试群"],
            version_strategy="open_source"
        )
        
        if not adapter.is_plus:
            logger.info("✅ 强制开源版策略成功")
            return True
        else:
            logger.warning("⚠️  强制开源版策略使用了Plus版")
            return False
            
    except Exception as e:
        logger.error(f"❌ 强制开源版策略失败: {e}")
        return False

def test_config_loading():
    """测试配置文件加载"""
    try:
        with open('client/config/client_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        wechat_config = config.get('wechat', {})
        version_strategy = wechat_config.get('version_strategy', 'auto')
        prefer_plus = wechat_config.get('prefer_plus', True)
        fallback_enabled = wechat_config.get('fallback_enabled', True)
        
        logger.info(f"✅ 配置文件加载成功")
        logger.info(f"📋 版本策略: {version_strategy}")
        logger.info(f"📋 优先Plus版: {prefer_plus}")
        logger.info(f"📋 允许降级: {fallback_enabled}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置文件加载失败: {e}")
        return False

def test_requirements():
    """测试依赖文件"""
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_wxauto = 'wxauto' in content
        has_wxautox = 'wxautox' in content
        
        logger.info(f"✅ requirements.txt 检查完成")
        logger.info(f"📋 包含 wxauto: {has_wxauto}")
        logger.info(f"📋 包含 wxautox: {has_wxautox}")
        
        return has_wxauto and has_wxautox
        
    except Exception as e:
        logger.error(f"❌ requirements.txt 读取失败: {e}")
        return False

def test_version_comparison():
    """测试版本对比功能"""
    try:
        from modules.adapters.wxauto_adapter import WxAutoAdapter
        
        # 测试版本信息获取
        adapter = WxAutoAdapter(whitelisted_groups=["测试群"])
        
        version_info = adapter.get_version_info()
        status = adapter.get_version_status()
        suggestion = adapter.suggest_upgrade()
        
        logger.info(f"✅ 版本对比功能测试成功")
        logger.info(f"📊 版本信息: {version_info}")
        logger.info(f"📊 版本状态: {status}")
        logger.info(f"📊 升级建议: {suggestion}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 版本对比功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("🧪 开始测试双版本功能...")
    logger.info("=" * 60)
    
    tests = [
        ("开源版导入测试", test_open_source_import),
        ("Plus版导入测试", test_plus_import),
        ("自动检测策略测试", test_adapter_auto_strategy),
        ("强制Plus版策略测试", test_adapter_plus_strategy),
        ("强制开源版策略测试", test_adapter_open_source_strategy),
        ("配置文件测试", test_config_loading),
        ("依赖文件测试", test_requirements),
        ("版本对比功能测试", test_version_comparison),
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
    logger.info("\n" + "=" * 60)
    logger.info("📊 测试结果汇总:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 总体结果: {passed}/{total} 通过")
    
    # 版本建议
    logger.info("\n💡 版本建议:")
    if passed >= 6:
        logger.info("✅ 双版本功能正常，推荐使用自动检测策略")
        logger.info("📖 详细说明: 📋双版本使用指南.md")
        return 0
    else:
        logger.error("⚠️  部分功能异常，请检查安装和配置")
        logger.error("📖 解决方案: 📋双版本使用指南.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
