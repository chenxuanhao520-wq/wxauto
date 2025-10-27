#!/usr/bin/env python3
"""
检查文件移动后代码实现是否受影响
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖包是否安装"""
    print("🔍 检查依赖包...")
    
    required_packages = [
        'fastapi',
        'uvicorn', 
        'supabase',
        'pinecone-client',
        'psycopg2-binary'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    else:
        print("✅ 所有依赖包已安装")
        return True

def check_imports():
    """检查导入路径"""
    print("\n🔍 检查导入路径...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ backend目录不存在")
        return False
    
    # 切换到backend目录
    os.chdir(backend_dir)
    
    # 添加当前目录到Python路径
    sys.path.insert(0, str(Path.cwd()))
    
    test_imports = [
        ("modules.storage.unified_database", "数据库模块"),
        ("modules.api.messages", "消息API模块"),
        ("modules.api.config", "配置API模块"),
        ("modules.api.health", "健康检查API模块"),
        ("modules.api.tenants", "租户API模块"),
        ("modules.vector.pinecone_client", "向量搜索模块"),
        ("modules.embeddings.unified_embedding_service", "嵌入服务模块"),
        ("modules.auth.supabase_auth", "认证模块"),
        ("modules.config.config_manager", "配置管理模块"),
        ("modules.realtime.supabase_realtime", "实时服务模块"),
    ]
    
    failed_imports = []
    
    for module_name, description in test_imports:
        try:
            __import__(module_name)
            print(f"✅ {description} 导入成功")
        except ImportError as e:
            print(f"❌ {description} 导入失败: {e}")
            failed_imports.append((module_name, str(e)))
        except Exception as e:
            print(f"⚠️ {description} 导入异常: {e}")
            failed_imports.append((module_name, str(e)))
    
    if failed_imports:
        print(f"\n❌ 导入失败详情:")
        for module_name, error in failed_imports:
            print(f"   - {module_name}: {error}")
        return False
    else:
        print("✅ 所有模块导入成功")
        return True

def check_main_app():
    """检查主应用是否能正常创建"""
    print("\n🔍 检查主应用...")
    
    try:
        # 尝试导入main模块
        import main
        print("✅ main.py 导入成功")
        
        # 检查app对象
        if hasattr(main, 'app'):
            print("✅ FastAPI应用对象存在")
        else:
            print("❌ FastAPI应用对象不存在")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ main.py 导入失败: {e}")
        return False

def check_config_files():
    """检查配置文件"""
    print("\n🔍 检查配置文件...")
    
    config_files = [
        "config.yaml",
        "requirements.txt",
        "README.md"
    ]
    
    missing_files = []
    
    for file_name in config_files:
        if Path(file_name).exists():
            print(f"✅ {file_name} 存在")
        else:
            print(f"❌ {file_name} 不存在")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n❌ 缺少配置文件: {', '.join(missing_files)}")
        return False
    else:
        print("✅ 所有配置文件存在")
        return True

def check_frontend():
    """检查前端项目"""
    print("\n🔍 检查前端项目...")
    
    frontend_dir = Path("../frontend")
    if not frontend_dir.exists():
        print("❌ frontend目录不存在")
        return False
    
    frontend_files = [
        "package.json",
        "vite.config.ts",
        "tsconfig.json",
        "index.html",
        "src/main.tsx",
        "src/App.tsx"
    ]
    
    missing_files = []
    
    for file_name in frontend_files:
        file_path = frontend_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name} 存在")
        else:
            print(f"❌ {file_name} 不存在")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n❌ 前端缺少文件: {', '.join(missing_files)}")
        return False
    else:
        print("✅ 前端项目文件完整")
        return True

def main():
    """主检查函数"""
    print("🔧 检查文件移动后代码实现是否受影响...")
    
    # 检查当前目录
    if not Path("backend").exists():
        print("❌ 请在项目根目录运行此脚本")
        return False
    
    results = []
    
    # 检查依赖
    results.append(check_dependencies())
    
    # 检查导入
    results.append(check_imports())
    
    # 检查主应用
    results.append(check_main_app())
    
    # 检查配置文件
    results.append(check_config_files())
    
    # 检查前端
    results.append(check_frontend())
    
    # 总结
    print("\n📊 检查结果:")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("✅ 所有检查通过！文件移动没有影响代码实现")
        print("\n🚀 可以正常启动服务:")
        print("   cd backend && python3 main.py")
        print("   cd frontend && npm install && npm run dev")
        return True
    else:
        print(f"❌ {total - passed}/{total} 项检查失败")
        print("\n🔧 需要修复的问题:")
        if not results[0]:
            print("   - 安装依赖: pip install -r requirements.txt")
        if not results[1]:
            print("   - 修复导入路径问题")
        if not results[2]:
            print("   - 修复主应用问题")
        if not results[3]:
            print("   - 补充缺失的配置文件")
        if not results[4]:
            print("   - 补充缺失的前端文件")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
