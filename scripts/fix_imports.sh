#!/bin/bash

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
