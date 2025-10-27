#!/usr/bin/env python3
"""
简化功能测试 - 验证核心逻辑（不依赖外部包）
测试环境配置、API结构、依赖注入等核心逻辑
"""

import os
import sys
import logging
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_environment_config():
    """测试环境配置逻辑"""
    logger.info("🧪 测试环境配置逻辑...")
    
    try:
        # 清除环境变量
        os.environ.pop("SUPABASE_URL", None)
        os.environ.pop("SUPABASE_ANON_KEY", None)
        os.environ.pop("PINECONE_API_KEY", None)
        
        # 测试配置管理器（不依赖外部包）
        from modules.config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        configs = config_manager.configs
        
        # 验证默认配置
        assert "system_settings" in configs
        assert "supabase_settings" in configs
        assert "pinecone_settings" in configs
        assert "ai_settings" in configs
        
        logger.info(f"✅ 配置管理器初始化成功: {len(configs)}项配置")
        
        # 测试配置值获取
        system_config = config_manager.get_config_value("system_settings")
        assert system_config["app_name"] == "微信客服中台"
        assert system_config["version"] == "2.0.0"
        
        logger.info("✅ 配置值获取正常")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 环境配置测试失败: {e}")
        return False


def test_api_structure():
    """测试API结构"""
    logger.info("🧪 测试API结构...")
    
    try:
        # 测试API模块导入
        from modules.api import messages, config, health, tenants
        
        # 验证路由存在
        assert hasattr(messages, 'router')
        assert hasattr(config, 'router')
        assert hasattr(health, 'router')
        assert hasattr(tenants, 'router')
        
        logger.info("✅ API模块导入正常")
        
        # 测试数据模型
        from modules.api.messages import MessageRequest, MessageResponse
        from modules.api.config import ConfigRequest, ConfigResponse
        from modules.api.tenants import TenantRequest, TenantResponse
        
        # 验证模型字段
        message_req = MessageRequest(
            request_id="test",
            group_id="test_group",
            sender_id="test_user",
            user_message="test message"
        )
        
        assert message_req.request_id == "test"
        assert message_req.user_message == "test message"
        
        logger.info("✅ API数据模型正常")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API结构测试失败: {e}")
        return False


def test_dependency_injection():
    """测试依赖注入结构"""
    logger.info("🧪 测试依赖注入结构...")
    
    try:
        # 测试依赖函数定义
        from main import (
            get_database_manager_dep,
            get_vector_search_service_dep,
            get_embedding_service_dep,
            get_config_manager_dep,
            get_auth_service_dep,
            get_supabase_client_dep,
            get_realtime_service_dep
        )
        
        # 验证依赖函数可调用
        assert callable(get_database_manager_dep)
        assert callable(get_vector_search_service_dep)
        assert callable(get_embedding_service_dep)
        assert callable(get_config_manager_dep)
        assert callable(get_auth_service_dep)
        assert callable(get_supabase_client_dep)
        assert callable(get_realtime_service_dep)
        
        logger.info("✅ 依赖注入函数定义正常")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 依赖注入测试失败: {e}")
        return False


def test_config_validation():
    """测试配置验证逻辑"""
    logger.info("🧪 测试配置验证逻辑...")
    
    try:
        from modules.config.config_validator import ConfigValidator
        
        validator = ConfigValidator()
        
        # 测试配置验证方法
        assert hasattr(validator, 'test_config')
        assert hasattr(validator, '_test_supabase_config')
        assert hasattr(validator, '_test_pinecone_config')
        assert hasattr(validator, '_test_ai_config')
        
        logger.info("✅ 配置验证器结构正常")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置验证测试失败: {e}")
        return False


def test_service_layer():
    """测试服务层结构"""
    logger.info("🧪 测试服务层结构...")
    
    try:
        # 测试服务类定义
        from modules.api.messages import MessageService
        from modules.api.config import ConfigService
        from modules.api.tenants import TenantService
        from modules.api.health import HealthService
        
        # 验证服务类存在
        assert MessageService is not None
        assert ConfigService is not None
        assert TenantService is not None
        assert HealthService is not None
        
        logger.info("✅ 服务层结构正常")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 服务层测试失败: {e}")
        return False


def test_main_app_structure():
    """测试主应用结构"""
    logger.info("🧪 测试主应用结构...")
    
    try:
        # 测试主应用导入
        import main
        
        # 验证应用组件
        assert hasattr(main, 'app')
        assert hasattr(main, 'lifespan')
        assert hasattr(main, 'custom_openapi')
        
        logger.info("✅ 主应用结构正常")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 主应用结构测试失败: {e}")
        return False


def test_file_structure():
    """测试文件结构"""
    logger.info("🧪 测试文件结构...")
    
    try:
        # 验证关键文件存在
        required_files = [
            "main.py",
            "modules/api/messages.py",
            "modules/api/config.py",
            "modules/api/health.py",
            "modules/api/tenants.py",
            "modules/config/config_manager.py",
            "modules/config/config_validator.py",
            "modules/storage/unified_database.py",
            "modules/storage/supabase_client.py",
            "modules/vector/pinecone_client.py",
            "modules/embeddings/unified_embedding_service.py",
            "modules/realtime/supabase_realtime.py",
            "modules/auth/supabase_auth.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            # 从backend目录查找文件
            full_path = backend_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"❌ 缺少文件: {missing_files}")
            return False
        
        logger.info(f"✅ 所有关键文件存在: {len(required_files)}个文件")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 文件结构测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始运行简化功能测试...")
    
    tests = [
        ("环境配置逻辑", test_environment_config),
        ("API结构", test_api_structure),
        ("依赖注入结构", test_dependency_injection),
        ("配置验证逻辑", test_config_validation),
        ("服务层结构", test_service_layer),
        ("主应用结构", test_main_app_structure),
        ("文件结构", test_file_structure),
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
        logger.info("🎉 所有核心逻辑测试通过！系统结构正常")
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
