#!/usr/bin/env python3
"""
环境变量验证脚本
确保所有必需的环境变量已正确设置
"""

import os
import sys
from pathlib import Path

# 必需的环境变量
REQUIRED_KEYS = [
    'QWEN_API_KEY',
    'JWT_SECRET_KEY',
]

# 推荐的环境变量
RECOMMENDED_KEYS = [
    'GLM_API_KEY',
    'DEEPSEEK_API_KEY',
    'ERP_USERNAME',
    'ERP_PASSWORD',
]

# 可选的环境变量
OPTIONAL_KEYS = [
    'OPENAI_API_KEY',
    'CLAUDE_API_KEY',
    'GEMINI_API_KEY',
    'MOONSHOT_API_KEY',
    'ERNIE_API_KEY',
    'ERP_BASE_URL',
    'POSTGRES_PASSWORD',
]


def check_env_variable(key: str) -> tuple[bool, str]:
    """
    检查环境变量
    
    Returns:
        (是否存在, 值的预览)
    """
    value = os.getenv(key)
    if not value:
        return False, ""
    
    # 隐藏敏感信息，只显示前4位和后4位
    if len(value) > 8:
        preview = f"{value[:4]}...{value[-4:]}"
    else:
        preview = "***"
    
    return True, preview


def validate_env():
    """验证所有环境变量"""
    print("\n" + "=" * 70)
    print("🔍 环境变量验证")
    print("=" * 70)
    
    # 检查必需的环境变量
    print("\n📋 必需的环境变量:")
    print("-" * 70)
    
    missing_required = []
    for key in REQUIRED_KEYS:
        exists, preview = check_env_variable(key)
        if exists:
            print(f"  ✅ {key:<25} {preview}")
        else:
            print(f"  ❌ {key:<25} 未设置")
            missing_required.append(key)
    
    # 检查推荐的环境变量
    print("\n💡 推荐的环境变量:")
    print("-" * 70)
    
    missing_recommended = []
    for key in RECOMMENDED_KEYS:
        exists, preview = check_env_variable(key)
        if exists:
            print(f"  ✅ {key:<25} {preview}")
        else:
            print(f"  ⚠️  {key:<25} 未设置")
            missing_recommended.append(key)
    
    # 检查可选的环境变量
    print("\n🔧 可选的环境变量:")
    print("-" * 70)
    
    set_optional = []
    for key in OPTIONAL_KEYS:
        exists, preview = check_env_variable(key)
        if exists:
            print(f"  ✅ {key:<25} {preview}")
            set_optional.append(key)
        else:
            print(f"  ⭕ {key:<25} 未设置（可选）")
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 总结")
    print("=" * 70)
    
    total = len(REQUIRED_KEYS) + len(RECOMMENDED_KEYS) + len(OPTIONAL_KEYS)
    set_count = (
        len(REQUIRED_KEYS) - len(missing_required) +
        len(RECOMMENDED_KEYS) - len(missing_recommended) +
        len(set_optional)
    )
    
    print(f"  已设置: {set_count}/{total} 个环境变量")
    print(f"  必需: {len(REQUIRED_KEYS) - len(missing_required)}/{len(REQUIRED_KEYS)}")
    print(f"  推荐: {len(RECOMMENDED_KEYS) - len(missing_recommended)}/{len(RECOMMENDED_KEYS)}")
    print(f"  可选: {len(set_optional)}/{len(OPTIONAL_KEYS)}")
    
    # 如果有缺失的必需环境变量，报错退出
    if missing_required:
        print("\n❌ 错误：缺少必需的环境变量")
        print("  请运行以下命令设置环境变量:")
        print("\n  # 使用提供的脚本:")
        print("  source set_env.sh")
        print("\n  # 或手动设置:")
        for key in missing_required:
            print(f"  export {key}='your_value_here'")
        print()
        sys.exit(1)
    
    # 如果有缺失的推荐环境变量，给出警告
    if missing_recommended:
        print("\n⚠️  警告：缺少推荐的环境变量")
        print("  这些功能可能无法正常工作:")
        if 'GLM_API_KEY' in missing_recommended:
            print("    - GLM (智谱AI) 模型调用")
        if 'DEEPSEEK_API_KEY' in missing_recommended:
            print("    - DeepSeek 模型调用")
        if 'ERP_USERNAME' in missing_recommended or 'ERP_PASSWORD' in missing_recommended:
            print("    - 智邦ERP 集成")
        print("\n  建议设置这些环境变量以启用完整功能。")
        print()
    
    # 如果所有必需和推荐的环境变量都设置了
    if not missing_required and not missing_recommended:
        print("\n✅ 所有必需和推荐的环境变量均已正确设置！")
        print("   系统已准备就绪，可以开始使用。")
        print()
        return True
    
    # 如果只是缺少推荐的环境变量
    if not missing_required:
        print("\n✅ 所有必需的环境变量均已设置")
        print("   系统可以启动，但部分功能可能受限。")
        print()
        return True
    
    return False


def main():
    """主函数"""
    try:
        result = validate_env()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  验证已取消")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

