#!/usr/bin/env python3
"""
测试 MCP 中台优化效果
验证配置管理和智能缓存功能
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

async def test_config_manager():
    """测试配置管理器"""
    print("\n" + "=" * 60)
    print("🧪 测试 1: 配置管理器")
    print("=" * 60)
    
    try:
        from modules.mcp_platform.config_manager import ConfigManager
        
        # 创建配置管理器
        config_manager = ConfigManager()
        print("✅ 配置管理器创建成功")
        
        # 测试获取配置
        global_config = config_manager.get_global_config()
        print(f"✅ 全局配置: {global_config}")
        
        # 测试获取服务列表
        services = config_manager.list_services()
        print(f"✅ 已配置服务: {services}")
        
        # 测试获取服务配置
        aiocr_config = config_manager.get_service_config("aiocr")
        print(f"✅ AIOCR 配置: 端点={aiocr_config.get('endpoint', 'N/A')[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_manager():
    """测试缓存管理器"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: 缓存管理器")
    print("=" * 60)
    
    try:
        from modules.mcp_platform.cache_manager import CacheManager
        
        # 创建缓存管理器
        cache_manager = CacheManager()
        print("✅ 缓存管理器创建成功")
        
        # 测试缓存设置和获取
        cache_manager.set("test_key", "test_value", ttl=10)
        value = cache_manager.get("test_key")
        assert value == "test_value", "缓存值不匹配"
        print("✅ 缓存设置/获取测试通过")
        
        # 测试缓存键生成
        key1 = cache_manager._generate_cache_key("aiocr", "doc_recognition", url="test.pdf")
        key2 = cache_manager._generate_cache_key("aiocr", "doc_recognition", url="test.pdf")
        assert key1 == key2, "相同参数应生成相同的缓存键"
        print("✅ 缓存键生成测试通过")
        
        # 测试统计信息
        stats = cache_manager.get_stats()
        print(f"✅ 缓存统计: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ 缓存管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mcp_manager_v2():
    """测试优化后的 MCP 管理器"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: MCP 管理器 V2")
    print("=" * 60)
    
    try:
        from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2
        
        # 创建管理器
        manager = MCPManagerV2()
        print("✅ MCP 管理器 V2 创建成功")
        
        # 测试服务列表
        services = manager.list_services()
        print(f"✅ 注册服务数量: {len(services)}")
        for service in services:
            print(f"  - {service['name']}: {service['description']}")
        
        # 测试健康检查
        health = manager.health_check()
        print(f"✅ 健康检查: {health}")
        
        # 测试统计信息
        stats = manager.get_stats()
        print(f"✅ 系统统计:")
        print(f"  - 总服务数: {stats['total_services']}")
        print(f"  - 启用服务: {stats['enabled_services']}")
        print(f"  - 缓存状态: {stats['cache_stats']}")
        
        return True
    except Exception as e:
        print(f"❌ MCP 管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_performance():
    """测试缓存性能"""
    print("\n" + "=" * 60)
    print("🧪 测试 4: 缓存性能测试")
    print("=" * 60)
    
    try:
        from modules.mcp_platform.cache_manager import CacheManager
        
        cache_manager = CacheManager()
        
        # 模拟API调用函数
        async def mock_api_call(url: str):
            """模拟耗时的 API 调用"""
            await asyncio.sleep(0.1)  # 模拟 100ms 延迟
            return f"结果: {url}"
        
        # 测试URL
        test_url = "https://example.com/test.pdf"
        
        # 第一次调用（无缓存）
        print("\n📝 第一次调用（无缓存）:")
        start = time.time()
        result1 = await mock_api_call(test_url)
        time1 = time.time() - start
        print(f"  ⏱️  耗时: {time1:.3f}秒")
        print(f"  📦 结果: {result1}")
        
        # 存入缓存
        cache_key = cache_manager._generate_cache_key("aiocr", "doc_recognition", url=test_url)
        cache_manager.set(cache_key, result1, ttl=60)
        
        # 第二次调用（有缓存）
        print("\n📝 第二次调用（有缓存）:")
        start = time.time()
        cached_result = cache_manager.get(cache_key)
        time2 = time.time() - start
        print(f"  ⏱️  耗时: {time2:.3f}秒")
        print(f"  📦 结果: {cached_result}")
        
        # 性能提升
        if time1 > 0:
            improvement = (1 - time2 / time1) * 100
            speedup = time1 / time2 if time2 > 0 else float('inf')
            print(f"\n✅ 性能提升: {improvement:.1f}%")
            print(f"✅ 加速比: {speedup:.1f}x")
        
        # 缓存统计
        stats = cache_manager.get_stats()
        print(f"\n📊 缓存统计:")
        print(f"  - 总请求: {stats['total_requests']}")
        print(f"  - 缓存命中: {stats['cache_hits']}")
        print(f"  - 缓存未命中: {stats['cache_misses']}")
        print(f"  - 命中率: {stats['hit_rate']}")
        
        return True
    except Exception as e:
        print(f"❌ 缓存性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("\n🚀 MCP 中台优化测试")
    print("=" * 60)
    print("📅 测试时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("🎯 目标: 验证配置管理和智能缓存功能")
    
    # 运行所有测试
    results = {}
    
    results['配置管理器'] = await test_config_manager()
    results['缓存管理器'] = await test_cache_manager()
    results['MCP管理器V2'] = await test_mcp_manager_v2()
    results['缓存性能'] = await test_cache_performance()
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！MCP 中台优化成功！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查日志")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

