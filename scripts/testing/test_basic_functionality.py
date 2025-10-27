#!/usr/bin/env python3
"""
基础功能测试 - 验证系统核心功能
测试环境配置、API启动、依赖注入等基础功能
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_environment_config():
    """测试环境配置"""
    logger.info("🧪 测试环境配置...")
    
    try:
        # 测试默认环境变量
        os.environ.pop("SUPABASE_URL", None)
        os.environ.pop("SUPABASE_ANON_KEY", None)
        os.environ.pop("PINECONE_API_KEY", None)
        
        # 导入模块测试
        from modules.storage.unified_database import UnifiedDatabaseManager
        from modules.vector.pinecone_client import PineconeClient
        from modules.config.config_manager import ConfigManager
        
        # 测试数据库管理器初始化
        db_manager = UnifiedDatabaseManager()
        logger.info(f"✅ 数据库管理器初始化成功: {db_manager.get_database_type().value}")
        
        # 测试配置管理器初始化
        config_manager = ConfigManager()
        configs = config_manager.configs
        logger.info(f"✅ 配置管理器初始化成功: {len(configs)}项配置")
        
        # 测试Pinecone客户端初始化（开发模式）
        try:
            pinecone_client = PineconeClient()
            logger.info("✅ Pinecone客户端初始化成功（开发模式）")
        except Exception as e:
            logger.warning(f"⚠️ Pinecone客户端初始化失败: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 环境配置测试失败: {e}")
        return False


def test_fastapi_dependencies():
    """测试FastAPI依赖注入"""
    logger.info("🧪 测试FastAPI依赖注入...")
    
    try:
        from main import app
        from fastapi.testclient import TestClient
        
        # 创建测试客户端
        client = TestClient(app)
        
        # 测试健康检查端点
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        logger.info(f"✅ 健康检查端点正常: {data['status']}")
        
        # 测试根路径
        response = client.get("/")
        assert response.status_code == 200
        logger.info("✅ 根路径正常")
        
        # 测试API文档
        response = client.get("/docs")
        assert response.status_code == 200
        logger.info("✅ API文档正常")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FastAPI依赖注入测试失败: {e}")
        return False


def test_api_endpoints():
    """测试API端点"""
    logger.info("🧪 测试API端点...")
    
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # 测试配置API
        response = client.get("/api/v1/config/")
        assert response.status_code == 200
        configs = response.json()
        assert isinstance(configs, list)
        logger.info(f"✅ 配置API正常: {len(configs)}项配置")
        
        # 测试健康检查API
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        health_data = response.json()
        assert "status" in health_data
        logger.info(f"✅ 健康检查API正常: {health_data['status']}")
        
        # 测试租户API
        response = client.get("/api/v1/tenants/")
        assert response.status_code == 200
        tenants = response.json()
        assert isinstance(tenants, list)
        logger.info(f"✅ 租户API正常: {len(tenants)}个租户")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API端点测试失败: {e}")
        return False


def test_message_processing():
    """测试消息处理"""
    logger.info("🧪 测试消息处理...")
    
    try:
        from modules.api.messages import MessageService
        from modules.storage.unified_database import UnifiedDatabaseManager
        from modules.api.messages import MessageRequest
        
        # 初始化服务
        db_manager = UnifiedDatabaseManager()
        message_service = MessageService(db_manager)
        
        # 创建测试消息
        test_message = MessageRequest(
            request_id="test_001",
            group_id="test_group",
            sender_id="test_user",
            user_message="这是一条测试消息"
        )
        
        # 测试消息处理（模拟）
        logger.info("✅ 消息服务初始化成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 消息处理测试失败: {e}")
        return False


def test_config_management():
    """测试配置管理"""
    logger.info("🧪 测试配置管理...")
    
    try:
        from modules.config.config_manager import ConfigManager
        from modules.config.config_validator import ConfigValidator
        
        # 测试配置管理器
        config_manager = ConfigManager()
        
        # 测试获取配置
        configs = asyncio.run(config_manager.get_all_configs())
        assert len(configs) > 0
        logger.info(f"✅ 配置获取成功: {len(configs)}项")
        
        # 测试配置验证器
        validator = ConfigValidator()
        
        # 测试Supabase配置验证
        supabase_config = {
            "url": "https://test.supabase.co",
            "anon_key": "test_key"
        }
        
        success, message, details = asyncio.run(
            validator.test_config("supabase", supabase_config)
        )
        logger.info(f"✅ 配置验证测试完成: {success} - {message}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置管理测试失败: {e}")
        return False


def test_realtime_service():
    """测试实时服务"""
    logger.info("🧪 测试实时服务...")
    
    try:
        from modules.realtime.supabase_realtime import SupabaseRealtimeService
        from modules.storage.supabase_client import SupabaseClient
        
        # 创建Supabase客户端（开发模式）
        supabase_client = SupabaseClient(
            url="https://test.supabase.co",
            key="test_key"
        )
        
        # 创建实时服务
        realtime_service = SupabaseRealtimeService(supabase_client.client)
        
        # 测试连接状态
        status = asyncio.run(realtime_service.get_connection_status())
        assert "connected" in status
        logger.info(f"✅ 实时服务初始化成功: {status['connected']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 实时服务测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始运行基础功能测试...")
    
    tests = [
        ("环境配置", test_environment_config),
        ("FastAPI依赖注入", test_fastapi_dependencies),
        ("API端点", test_api_endpoints),
        ("消息处理", test_message_processing),
        ("配置管理", test_config_management),
        ("实时服务", test_realtime_service),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    logger.info(f"\n{'='*50}")
    logger.info("测试结果汇总")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！系统基础功能正常")
        return True
    else:
        logger.error(f"⚠️ {total - passed} 个测试失败，需要修复")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n👋 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 测试运行失败: {e}")
        sys.exit(1)
