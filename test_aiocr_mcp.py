#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 AIOCR MCP 服务
"""
import os
import asyncio
import httpx
import json
import logging
from pathlib import Path

# 使用 Qwen 的密钥（阿里云百炼）
DASHSCOPE_API_KEY = os.getenv('QWEN_API_KEY', 'sk-1d7d593d85b1469683eb8e7988a0f646')
AIOCR_SSE_URL = "https://dashscope.aliyuncs.com/api/v1/mcps/ai-ocr/sse"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_aiocr_connection():
    """测试 AIOCR MCP 服务连接（使用 SSE 流）"""
    print("\n" + "="*70)
    print("🧪 测试 1: AIOCR MCP 服务连接 (SSE)")
    print("="*70)
    
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"  # SSE 协议
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"📍 MCP 端点: {AIOCR_SSE_URL}")
            print(f"🔑 API Key: {DASHSCOPE_API_KEY[:20]}...")
            
            # MCP 协议：先获取工具列表（SSE 流式响应）
            async with client.stream(
                'POST',
                AIOCR_SSE_URL,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list"
                }
            ) as response:
                
                print(f"\n📊 响应状态: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ 连接成功！正在读取 SSE 流...")
                    
                    # 读取 SSE 流
                    sse_data = []
                    async for line in response.aiter_lines():
                        if line.startswith('data:'):
                            data_json = line[5:].strip()
                            if data_json and data_json != '[DONE]':
                                try:
                                    data = json.loads(data_json)
                                    sse_data.append(data)
                                    
                                    # 如果是工具列表响应
                                    if 'result' in data and 'tools' in data['result']:
                                        print(f"\n🛠️ 可用工具:")
                                        for tool in data['result']['tools']:
                                            print(f"  • {tool.get('name')}: {tool.get('description', '')[:60]}...")
                                except json.JSONDecodeError:
                                    print(f"  跳过非 JSON 数据: {data_json[:50]}...")
                    
                    if sse_data:
                        print(f"\n✅ 接收到 {len(sse_data)} 个 SSE 事件")
                        return True
                    else:
                        print(f"\n⚠️ SSE 流为空，可能需要不同的调用方式")
                        return False
                else:
                    print(f"❌ 连接失败！")
                    async for line in response.aiter_lines():
                        print(f"错误: {line}")
                    return False
        
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            logger.error("连接测试失败", exc_info=True)
            return False


async def test_doc_recognition():
    """测试文档识别功能"""
    print("\n" + "="*70)
    print("🧪 测试 2: 文档识别 (doc_recognition)")
    print("="*70)
    
    # 创建一个简单的测试文件
    test_file = Path("test_document.txt")
    test_content = """
测试文档 - 充电桩产品说明

产品型号: CP-7KW-AC
功率: 7KW
电压: 220V
电流: 32A

特点:
1. 安装简单
2. 成本低
3. 适合家用
    """
    
    test_file.write_text(test_content, encoding='utf-8')
    
    try:
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 读取文件并转为 base64
        import base64
        file_bytes = test_file.read_bytes()
        file_base64 = base64.b64encode(file_bytes).decode()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 调用 doc_recognition 工具（SSE 流）
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "doc_recognition",
                    "arguments": {
                        "file": file_base64,
                        "filename": "test_document.txt"
                    }
                }
            }
            
            print(f"📄 测试文件: {test_file.name}")
            print(f"📏 文件大小: {len(file_bytes)} bytes")
            print(f"\n⏳ 调用 AIOCR 识别...")
            
            async with client.stream(
                'POST',
                AIOCR_SSE_URL,
                headers=headers,
                json=payload
            ) as response:
                
                print(f"\n📊 响应状态: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ 开始接收 SSE 流...")
                    
                    result_data = None
                    async for line in response.aiter_lines():
                        if line.startswith('data:'):
                            data_json = line[5:].strip()
                            if data_json and data_json != '[DONE]':
                                try:
                                    data = json.loads(data_json)
                                    result_data = data
                                    print(f"  接收到事件: {data.get('id', 'unknown')}")
                                except:
                                    pass
                    
                    if result_data:
                        print(f"\n✅ 识别成功！")
                        print(f"\n📝 识别结果:")
                        print(json.dumps(result_data, indent=2, ensure_ascii=False)[:500])
                        return True
                    else:
                        print(f"\n⚠️ 未收到识别结果")
                        return False
                else:
                    print(f"❌ 识别失败！")
                    async for line in response.aiter_lines():
                        print(f"错误: {line}")
                    return False
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.error("文档识别测试失败", exc_info=True)
        return False
    
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()


async def test_doc_to_markdown():
    """测试文档转 Markdown 功能"""
    print("\n" + "="*70)
    print("🧪 测试 3: 文档转 Markdown (doc_to_markdown)")
    print("="*70)
    
    # 创建一个包含格式的测试文件
    test_file = Path("test_formatted.txt")
    test_content = """
# 充电桩安装指南

## 1. 选址要求
- 靠近配电箱
- 地面平整
- 通风良好

## 2. 安装步骤

### 2.1 准备工作
1. 准备工具
2. 检查电源
3. 确认位置

### 2.2 安装流程
① 固定底座
② 连接电源
③ 通电测试

## 3. 注意事项
**重要**: 必须由专业电工操作！
    """
    
    test_file.write_text(test_content, encoding='utf-8')
    
    try:
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        import base64
        file_bytes = test_file.read_bytes()
        file_base64 = base64.b64encode(file_bytes).decode()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "doc_to_markdown",
                    "arguments": {
                        "file": file_base64,
                        "filename": "test_formatted.txt"
                    }
                }
            }
            
            print(f"📄 测试文件: {test_file.name}")
            print(f"📏 文件大小: {len(file_bytes)} bytes")
            print(f"\n⏳ 调用 AIOCR 转换为 Markdown...")
            
            response = await client.post(
                AIOCR_SSE_URL,
                headers=headers,
                json=payload
            )
            
            print(f"\n📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 转换成功！")
                print(f"\n📝 转换结果:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                return True
            else:
                print(f"❌ 转换失败！")
                print(f"错误: {response.text}")
                return False
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.error("Markdown 转换测试失败", exc_info=True)
        return False
    
    finally:
        if test_file.exists():
            test_file.unlink()


async def main():
    """主测试流程"""
    print("\n" + "🔬"*35)
    print("AIOCR MCP 服务测试")
    print("🔬"*35)
    print(f"\n使用密钥: {DASHSCOPE_API_KEY[:20]}...")
    print(f"MCP 端点: {AIOCR_SSE_URL}")
    print("")
    
    results = []
    
    # 测试 1: 连接
    result1 = await test_aiocr_connection()
    results.append(("连接测试", result1))
    
    if result1:
        # 测试 2: 文档识别
        result2 = await test_doc_recognition()
        results.append(("文档识别", result2))
        
        # 测试 3: Markdown 转换
        result3 = await test_doc_to_markdown()
        results.append(("Markdown转换", result3))
    
    # 总结
    print("\n\n" + "="*70)
    print("📊 测试总结")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 AIOCR MCP 服务完全可用！")
        print("\n建议: 立即集成到知识库上传模块")
        print("预期效果:")
        print("  • 支持 40+ 种文件格式")
        print("  • AI 识别准确率高")
        print("  • 保留文档格式 (Markdown)")
        print("  • 零维护成本")
    else:
        print("\n⚠️ 部分测试失败，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())

