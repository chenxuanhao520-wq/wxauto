#!/usr/bin/env python3
"""
修复文件移动后的导入路径问题
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """修复单个文件中的导入路径"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复相对导入路径
        patterns = [
            # 修复 from modules. 导入
            (r'from modules\.', 'from modules.'),
            # 修复 import modules. 导入
            (r'import modules\.', 'import modules.'),
            # 修复相对路径导入
            (r'from \.\.\/modules', 'from modules'),
            (r'from \.\.modules', 'from modules'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复了 {file_path}")
            return True
        else:
            print(f"⏭️ 无需修复 {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 修复失败 {file_path}: {e}")
        return False

def fix_all_imports():
    """修复所有文件中的导入路径"""
    backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print("❌ backend目录不存在")
        return
    
    # 需要修复的文件类型
    file_extensions = ['.py']
    
    fixed_files = 0
    total_files = 0
    
    # 遍历所有Python文件
    for file_path in backend_dir.rglob('*.py'):
        total_files += 1
        if fix_imports_in_file(file_path):
            fixed_files += 1
    
    print(f"\n📊 修复统计:")
    print(f"   总文件数: {total_files}")
    print(f"   修复文件数: {fixed_files}")
    print(f"   无需修复: {total_files - fixed_files}")

def check_specific_issues():
    """检查特定的导入问题"""
    print("\n🔍 检查特定导入问题...")
    
    issues = []
    
    # 检查main.py中的导入
    main_py = Path("backend/main.py")
    if main_py.exists():
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查是否有错误的导入
        if 'from modules.' in content:
            print("✅ main.py中的modules导入路径正确")
        else:
            issues.append("main.py中缺少modules导入")
    
    # 检查测试文件
    test_dir = Path("backend/tests")
    if test_dir.exists():
        for test_file in test_dir.glob("test_*.py"):
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'from modules.' in content:
                print(f"✅ {test_file.name}中的modules导入路径正确")
            else:
                issues.append(f"{test_file.name}中缺少modules导入")
    
    if issues:
        print("\n❌ 发现的问题:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ 没有发现导入问题")

def create_fix_script():
    """创建修复脚本"""
    fix_script = '''#!/bin/bash

# 修复文件移动后的导入路径问题

echo "🔧 开始修复导入路径..."

# 1. 确保在backend目录中运行
cd backend

# 2. 设置Python路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 3. 运行Python修复脚本
python3 -c "
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path.cwd()))

# 测试导入
try:
    from modules.storage.unified_database import init_database_manager
    print('✅ 数据库模块导入成功')
except ImportError as e:
    print(f'❌ 数据库模块导入失败: {e}')

try:
    from modules.api.messages import router
    print('✅ API模块导入成功')
except ImportError as e:
    print(f'❌ API模块导入失败: {e}')

try:
    from modules.vector.pinecone_client import init_vector_search_service
    print('✅ 向量模块导入成功')
except ImportError as e:
    print(f'❌ 向量模块导入失败: {e}')
"

echo "🎉 导入路径修复完成！"
'''
    
    with open("fix_imports.sh", "w", encoding="utf-8") as f:
        f.write(fix_script)
    
    os.chmod("fix_imports.sh", 0o755)
    print("✅ 创建了修复脚本: fix_imports.sh")

if __name__ == "__main__":
    print("🔧 开始修复文件移动后的导入路径问题...")
    
    # 检查当前目录
    if not Path("backend").exists():
        print("❌ 请在项目根目录运行此脚本")
        exit(1)
    
    # 修复导入路径
    fix_all_imports()
    
    # 检查特定问题
    check_specific_issues()
    
    # 创建修复脚本
    create_fix_script()
    
    print("\n🎉 导入路径修复完成！")
    print("\n📋 后续步骤:")
    print("1. 运行: chmod +x fix_imports.sh")
    print("2. 运行: ./fix_imports.sh")
    print("3. 测试: cd backend && python3 main.py")
