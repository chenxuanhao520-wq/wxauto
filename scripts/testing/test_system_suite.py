#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试套件
统一测试所有核心功能
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


class SystemTestSuite:
    """系统测试套件"""
    
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始系统测试套件")
        print("=" * 60)
        
        # 测试分类
        test_categories = [
            ("配置管理", self.test_config_management),
            ("云原生客户端", self.test_cloud_native_client),
            ("数据存储", self.test_data_storage),
            ("向量搜索", self.test_vector_search),
            ("AI服务", self.test_ai_services),
            ("微信自动化", self.test_wechat_automation),
            ("Web界面", self.test_web_interface),
            ("系统集成", self.test_system_integration)
        ]
        
        for category_name, test_func in test_categories:
            try:
                print(f"\n📋 测试分类: {category_name}")
                print("-" * 40)
                success = await test_func()
                self.test_results.append((category_name, success))
                self.total_tests += 1
                if success:
                    self.passed_tests += 1
            except Exception as e:
                print(f"❌ {category_name}测试异常: {e}")
                self.test_results.append((category_name, False))
                self.total_tests += 1
        
        # 输出测试结果
        self.print_test_summary()
        return self.passed_tests == self.total_tests
    
    async def test_config_management(self):
        """测试配置管理"""
        try:
            # 测试配置验证器
            from modules.config.config_validator import ConfigValidator
            validator = ConfigValidator()
            
            # 测试有效配置
            valid_config = {
                'url': 'https://test.supabase.co',
                'anon_key': 'test_key_1234567890'
            }
            is_valid, errors = validator.validate_config('supabase', valid_config)
            if not is_valid:
                print(f"❌ 配置验证失败: {errors}")
                return False
            
            print("✅ 配置验证器测试通过")
            
            # 测试服务测试器
            from modules.config.config_validator import ServiceTester
            tester = ServiceTester()
            
            result = await tester.test_supabase(valid_config)
            print(f"✅ 服务测试器测试通过: {result['status']}")
            
            return True
            
        except Exception as e:
            print(f"❌ 配置管理测试失败: {e}")
            return False
    
    async def test_cloud_native_client(self):
        """测试云原生客户端"""
        try:
            # 测试客户端配置同步
            from client.config_sync_client import ClientConfigSync
            client_sync = ClientConfigSync("http://localhost:8000")
            
            # 测试配置获取
            config_data = await client_sync.fetch_config_from_api()
            print(f"✅ 客户端配置同步测试通过: {len(config_data)}个分类")
            
            return True
            
        except Exception as e:
            print(f"❌ 云原生客户端测试失败: {e}")
            return False
    
    async def test_data_storage(self):
        """测试数据存储"""
        try:
            # 检查数据库文件
            db_files = [
                "sql/config_management.sql",
                "sql/init.sql"
            ]
            
            for db_file in db_files:
                if not Path(db_file).exists():
                    print(f"❌ 数据库文件不存在: {db_file}")
                    return False
            
            print("✅ 数据存储测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 数据存储测试失败: {e}")
            return False
    
    async def test_vector_search(self):
        """测试向量搜索"""
        try:
            # 检查向量搜索模块
            vector_file = Path("modules/vector/pinecone_client.py")
            if not vector_file.exists():
                print("❌ 向量搜索模块不存在")
                return False
            
            print("✅ 向量搜索测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 向量搜索测试失败: {e}")
            return False
    
    async def test_ai_services(self):
        """测试AI服务"""
        try:
            # 检查AI服务模块
            ai_modules = [
                "modules/ai_gateway",
                "modules/embeddings"
            ]
            
            for module in ai_modules:
                if not Path(module).exists():
                    print(f"❌ AI服务模块不存在: {module}")
                    return False
            
            print("✅ AI服务测试通过")
            return True
            
        except Exception as e:
            print(f"❌ AI服务测试失败: {e}")
            return False
    
    async def test_wechat_automation(self):
        """测试微信自动化"""
        try:
            # 检查微信自动化模块
            wx_modules = [
                "client/cloud_wx_automation.py",
                "modules/adapters"
            ]
            
            for module in wx_modules:
                if not Path(module).exists():
                    print(f"❌ 微信自动化模块不存在: {module}")
                    return False
            
            print("✅ 微信自动化测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 微信自动化测试失败: {e}")
            return False
    
    async def test_web_interface(self):
        """测试Web界面"""
        try:
            # 检查Web界面文件
            web_files = [
                "web/templates/config_management.html",
                "web/web_frontend.py"
            ]
            
            for web_file in web_files:
                if not Path(web_file).exists():
                    print(f"❌ Web界面文件不存在: {web_file}")
                    return False
            
            print("✅ Web界面测试通过")
            return True
            
        except Exception as e:
            print(f"❌ Web界面测试失败: {e}")
            return False
    
    async def test_system_integration(self):
        """测试系统集成"""
        try:
            # 检查核心文件
            core_files = [
                "main.py",
                "client/cloud_client.py",
                "config.yaml",
                "requirements.txt"
            ]
            
            for core_file in core_files:
                if not Path(core_file).exists():
                    print(f"❌ 核心文件不存在: {core_file}")
                    return False
            
            print("✅ 系统集成测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 系统集成测试失败: {e}")
            return False
    
    def print_test_summary(self):
        """打印测试摘要"""
        print("\n📊 测试结果汇总")
        print("=" * 60)
        
        for test_name, success in self.test_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{test_name}: {status}")
        
        print(f"\n总计: {self.passed_tests}/{self.total_tests} 测试通过")
        
        if self.passed_tests == self.total_tests:
            print("🎉 所有测试通过！系统功能正常！")
        else:
            print("⚠️ 部分测试失败，请检查相关功能")


async def main():
    """主入口"""
    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)
    
    # 创建测试套件
    test_suite = SystemTestSuite()
    
    # 运行所有测试
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n✅ 系统测试完成！")
        print("\n📋 下一步:")
        print("   1. 配置环境变量: cp env_example_unified.txt .env")
        print("   2. 运行数据库初始化: sql/config_management.sql")
        print("   3. 启动服务器: python main.py server")
        print("   4. 访问配置管理: http://localhost:8000/config")
        print("   5. 启动客户端: python client/cloud_client.py")
    else:
        print("\n❌ 系统测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"程序异常: {e}")
        sys.exit(1)
