#!/usr/bin/env python3
"""
调试 MCP 配置问题
"""

import os
from dotenv import load_dotenv
from modules.mcp_platform.config_manager import get_config_manager

# 加载环境变量
load_dotenv()

print("=" * 60)
print("🔍 MCP 配置调试")
print("=" * 60)

# 检查环境变量
print("\n📋 环境变量:")
qwen_key = os.getenv('QWEN_API_KEY', '未设置')
print(f"   QWEN_API_KEY: {qwen_key[:20]}..." if qwen_key != '未设置' else "   QWEN_API_KEY: 未设置")

# 加载配置
print("\n📄 加载配置文件...")
config_manager = get_config_manager("config/mcp_config.yaml")

# 检查服务配置
print("\n🛠️  Sequential Thinking 配置:")
st_config = config_manager.get_service_config('sequential_thinking')
print(f"   enabled: {st_config.get('enabled')}")
print(f"   endpoint: {st_config.get('endpoint')}")
api_key = st_config.get('api_key', '')
print(f"   api_key: {api_key[:20]}..." if len(api_key) > 20 else f"   api_key: '{api_key}'")

# 检查 AIOCR 配置
print("\n📄 AIOCR 配置:")
aiocr_config = config_manager.get_service_config('aiocr')
print(f"   enabled: {aiocr_config.get('enabled')}")
print(f"   endpoint: {aiocr_config.get('endpoint')}")
api_key_aiocr = aiocr_config.get('api_key', '')
print(f"   api_key: {api_key_aiocr[:20]}..." if len(api_key_aiocr) > 20 else f"   api_key: '{api_key_aiocr}'")

print("\n" + "=" * 60)
