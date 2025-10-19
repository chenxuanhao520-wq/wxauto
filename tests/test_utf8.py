#!/usr/bin/env python3
"""
UTF-8 编码测试脚本
"""

# 强制 UTF-8 编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

print("🎉 UTF-8 编码测试")
print("中文显示正常")
print("Emoji 表情: 🚀 🤖 ✅ ❌")
print("特殊字符: ★ ☆ ♠ ♣ ♥ ♦")
print("测试完成！")
