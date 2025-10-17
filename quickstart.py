#!/usr/bin/env python3
"""
快速启动脚本
自动检查环境、初始化数据库、运行测试与演示
"""
import sys
import os
from pathlib import Path

# 确保在项目根目录
os.chdir(Path(__file__).parent)


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_dependencies():
    """检查依赖"""
    print_header("1. 检查依赖")
    
    missing = []
    
    try:
        import yaml
        print("✅ pyyaml")
    except ImportError:
        missing.append("pyyaml")
        print("❌ pyyaml (缺失)")
    
    try:
        import requests
        print("✅ requests")
    except ImportError:
        missing.append("requests")
        print("❌ requests (缺失)")
    
    try:
        import pytest
        print("✅ pytest")
    except ImportError:
        missing.append("pytest")
        print("❌ pytest (缺失)")
    
    if missing:
        print(f"\n⚠️  缺少依赖: {', '.join(missing)}")
        print(f"   请运行: pip install {' '.join(missing)}")
        return False
    
    print("\n✅ 所有依赖已安装")
    return True


def init_database():
    """初始化数据库"""
    print_header("2. 初始化数据库")
    
    try:
        from storage.db import Database
        
        Path("data").mkdir(exist_ok=True)
        db = Database("data/data.db")
        db.init_database()
        db.close()
        
        print("✅ 数据库初始化成功: data/data.db")
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False


def run_tests():
    """运行测试"""
    print_header("3. 运行单元测试")
    
    try:
        import pytest
        
        result = pytest.main([
            "tests/",
            "-v",
            "--tb=short",
            "-x"  # 遇到失败立即停止
        ])
        
        if result == 0:
            print("\n✅ 所有测试通过")
            return True
        else:
            print(f"\n❌ 测试失败 (退出码: {result})")
            return False
            
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        return False


def run_demo():
    """运行演示"""
    print_header("4. 运行功能演示")
    
    try:
        import demo
        demo.main()
        return True
        
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def init_knowledge_base():
    """初始化知识库"""
    print_header("5. 初始化知识库")
    
    try:
        # 检查知识库是否已存在
        from storage.db import Database
        db = Database("data/data.db")
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge_chunks")
        count = cursor.fetchone()[0]
        db.close()
        
        if count > 0:
            print(f"✅ 知识库已存在 ({count} 个知识块)")
            return True
        
        print("知识库为空，正在添加示例文档...")
        import subprocess
        result = subprocess.run(
            ['python3', 'kb_manager.py', '--action', 'add'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ 知识库初始化成功")
            return True
        else:
            print(f"⚠️  知识库初始化失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"⚠️  知识库初始化失败: {e}")
        return False


def show_next_steps():
    """显示后续步骤"""
    print_header("🎉 快速启动完成！")
    
    print("后续步骤:")
    print("")
    print("1. 【测试模式】运行主程序:")
    print("   python3 main.py")
    print("")
    print("2. 【真实模式】Windows + PC 微信 + AI:")
    print("   set USE_FAKE_ADAPTER=false")
    print("   set OPENAI_API_KEY=sk-your-key-here")
    print("   python main.py")
    print("")
    print("3. 【管理知识库】:")
    print("   python kb_manager.py --action list")
    print("   python kb_manager.py --action search --query '如何安装'")
    print("")
    print("4. 【运维工具】:")
    print("   python ops_tools.py health")
    print("   python ops_tools.py report --days 7")
    print("")
    print("5. 查看文档:")
    print("   - README.md：完整使用指南")
    print("   - DELIVERY_SUMMARY.md：交付总结")
    print("")
    print("6. 查看数据:")
    print("   sqlite3 data/data.db")
    print("   SELECT * FROM sessions;")
    print("")
    print("注意：Phase 2-4 已完成！")
    print("   ✅ RAG 检索器（BM25）")
    print("   ✅ AI 网关（OpenAI + DeepSeek）")
    print("   ✅ 知识库管理")
    print("   ✅ 运维工具")
    print("")


def main():
    """主函数"""
    print("\n" + "🚀 " * 20)
    print("  微信群聊客服中台 - 快速启动")
    print("🚀 " * 20)
    
    # 1. 检查依赖
    if not check_dependencies():
        print("\n❌ 请先安装依赖后再运行")
        sys.exit(1)
    
    # 2. 初始化数据库
    if not init_database():
        print("\n❌ 数据库初始化失败")
        sys.exit(1)
    
    # 3. 运行测试
    if not run_tests():
        print("\n⚠️  测试失败，但继续演示")
    
    # 4. 运行演示
    if not run_demo():
        print("\n❌ 演示失败")
        sys.exit(1)
    
    # 5. 初始化知识库
    if not init_knowledge_base():
        print("\n⚠️  知识库初始化失败，但继续")
    
    # 6. 显示后续步骤
    show_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
