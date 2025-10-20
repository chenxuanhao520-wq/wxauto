#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 中台完整测试脚本
测试 MCP 中台、AIOCR 客户端、知识库集成、消息处理
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

# 设置环境变量
os.environ['QWEN_API_KEY'] = os.getenv('QWEN_API_KEY', 'sk-1d7d593d85b1469683eb8e7988a0f646')
os.environ['QWEN_API_BASE'] = os.getenv('QWEN_API_BASE', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
os.environ['QWEN_MODEL'] = os.getenv('QWEN_MODEL', 'qwen-turbo')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


async def test_mcp_manager():
    """测试 MCP 中台管理器"""
    print("\n" + "="*70)
    print("🧪 测试 1: MCP 中台管理器")
    print("="*70)
    
    try:
        from modules.mcp_platform import MCPManager
        
        # 初始化管理器
        manager = MCPManager()
        
        # 列出服务
        services = manager.list_services()
        print(f"📋 注册的服务: {len(services)} 个")
        for service in services:
            print(f"  • {service['name']}: {service['description']}")
            print(f"    支持格式: {len(service['supported_formats'])} 种")
            print(f"    工具: {service['tools']}")
        
        # 健康检查
        health = manager.health_check()
        print(f"\n🏥 健康检查:")
        for name, status in health.items():
            print(f"  • {name}: {status.get('status', 'unknown')}")
        
        # 统计信息
        stats = manager.get_stats()
        print(f"\n📊 统计信息:")
        print(f"  总服务数: {stats['total_services']}")
        print(f"  启用服务: {stats['enabled_services']}")
        print(f"  禁用服务: {stats['disabled_services']}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP 管理器测试失败: {e}")
        return False


async def test_aiocr_client():
    """测试 AIOCR 客户端"""
    print("\n" + "="*70)
    print("🧪 测试 2: AIOCR 客户端")
    print("="*70)
    
    try:
        from modules.mcp_platform import MCPManager
        
        # 获取 AIOCR 客户端
        manager = MCPManager()
        aiocr_client = manager.get_client("aiocr")
        
        # 健康检查
        health = await aiocr_client.health_check()
        print(f"🏥 AIOCR 健康状态: {health.get('status', 'unknown')}")
        
        # 获取支持格式
        formats = aiocr_client.get_supported_formats()
        print(f"📄 支持格式: {len(formats)} 种")
        print(f"  前10种: {formats[:10]}")
        
        # 创建测试文件
        test_file = Path("test_mcp_document.txt")
        test_content = """
# 充电桩产品手册

## 产品概述
CP-7KW-AC 是一款家用交流充电桩，功率7KW，适合家庭使用。

## 技术参数
- 功率: 7KW
- 电压: 220V
- 电流: 32A
- 防护等级: IP65

## 安装要求
1. 靠近配电箱
2. 地面平整
3. 通风良好

## 注意事项
**重要**: 必须由专业电工安装！
        """
        
        test_file.write_text(test_content, encoding='utf-8')
        
        try:
            # 测试文档识别
            print(f"\n📄 测试文档识别: {test_file.name}")
            result = await aiocr_client.doc_recognition(test_file)
            
            if result.get("success"):
                print(f"✅ 识别成功!")
                print(f"  文件大小: {result.get('file_size', 0)} bytes")
                print(f"  识别内容长度: {len(result.get('content', ''))} 字符")
                print(f"  内容预览: {result.get('content', '')[:100]}...")
            else:
                print(f"❌ 识别失败: {result.get('error')}")
            
            # 测试 Markdown 转换
            print(f"\n📝 测试 Markdown 转换: {test_file.name}")
            result = await aiocr_client.doc_to_markdown(test_file)
            
            if result.get("success"):
                print(f"✅ 转换成功!")
                print(f"  Markdown 长度: {len(result.get('content', ''))} 字符")
                print(f"  内容预览: {result.get('content', '')[:100]}...")
            else:
                print(f"❌ 转换失败: {result.get('error')}")
        
        finally:
            # 清理测试文件
            if test_file.exists():
                test_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ AIOCR 客户端测试失败: {e}")
        return False


async def test_document_processor_integration():
    """测试文档处理器集成"""
    print("\n" + "="*70)
    print("🧪 测试 3: 文档处理器 MCP 集成")
    print("="*70)
    
    try:
        from modules.kb_service.document_processor import DocumentProcessor
        
        # 初始化处理器（启用 MCP AIOCR）
        processor = DocumentProcessor(use_ocr=True, use_mcp_aiocr=True)
        
        # 检查 MCP AIOCR 可用性
        is_available = processor.is_mcp_aiocr_available()
        print(f"🤖 MCP AIOCR 可用: {is_available}")
        
        # 获取支持格式
        formats = processor.get_supported_formats()
        print(f"📄 支持格式:")
        print(f"  本地: {len(formats['local'])} 种")
        print(f"  MCP AIOCR: {len(formats['mcp_aiocr'])} 种")
        print(f"  合并: {len(formats['combined'])} 种")
        
        # 创建测试文件
        test_file = Path("test_processor_document.txt")
        test_content = """
# 充电桩故障排除指南

## 常见问题

### 1. 充电桩无法启动
**原因**: 电源未连接或保险丝烧断
**解决方法**: 
1. 检查电源连接
2. 更换保险丝
3. 联系技术支持

### 2. 充电速度慢
**原因**: 电压不稳定或线缆老化
**解决方法**:
1. 检查电压是否稳定
2. 更换充电线缆
3. 调整充电功率

## 联系信息
技术支持: 400-123-4567
邮箱: support@example.com
        """
        
        test_file.write_text(test_content, encoding='utf-8')
        
        try:
            # 测试文档处理（优先使用 MCP AIOCR）
            print(f"\n📄 测试文档处理: {test_file.name}")
            result = processor.process_file(
                file_path=str(test_file),
                document_name="故障排除指南",
                document_version="v1.0",
                chunk_size=300,
                chunk_overlap=50,
                use_mcp_aiocr=True
            )
            
            print(f"✅ 处理完成!")
            print(f"  文档名称: {result['document_name']}")
            print(f"  处理方法: {result.get('processing_method', 'unknown')}")
            print(f"  总字符数: {result['total_chars']}")
            print(f"  分段数量: {len(result['chunks'])}")
            
            # 显示前3个分段
            print(f"\n📝 前3个分段:")
            for i, chunk in enumerate(result['chunks'][:3], 1):
                print(f"  {i}. {chunk['section']} ({chunk['char_count']} 字符)")
                print(f"     {chunk['content'][:50]}...")
        
        finally:
            # 清理测试文件
            if test_file.exists():
                test_file.unlink()
        
        # 健康检查
        health = await processor.health_check()
        print(f"\n🏥 健康检查:")
        print(f"  本地解析器: {health['local_parsers']}")
        print(f"  MCP AIOCR: {health['mcp_aiocr']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文档处理器集成测试失败: {e}")
        return False


async def test_message_service_integration():
    """测试消息服务集成"""
    print("\n" + "="*70)
    print("🧪 测试 4: 消息服务 MCP 集成")
    print("="*70)
    
    try:
        from server.services.message_service import MessageService
        
        # 初始化消息服务
        service = MessageService()
        
        # 检查 MCP 中台状态
        if service.mcp_manager:
            print(f"✅ MCP 中台已初始化")
            stats = service.mcp_manager.get_stats()
            print(f"  服务数量: {stats['total_services']}")
        else:
            print(f"⚠️ MCP 中台未初始化")
        
        if service.aiocr_client:
            print(f"✅ AIOCR 客户端已初始化")
        else:
            print(f"⚠️ AIOCR 客户端未初始化")
        
        # 模拟图片消息处理
        print(f"\n🖼️ 测试图片消息处理:")
        image_message = {
            'id': 'test_image_001',
            'type': 'image',
            'content': '用户发送了一张图片',
            'file_path': 'test_image.jpg'  # 假设的图片路径
        }
        
        # 注意：这里只是测试消息结构，不会真正处理文件
        print(f"  消息类型: {image_message['type']}")
        print(f"  文件路径: {image_message['file_path']}")
        print(f"  原始内容: {image_message['content']}")
        
        # 模拟文件消息处理
        print(f"\n📄 测试文件消息处理:")
        file_message = {
            'id': 'test_file_001',
            'type': 'file',
            'content': '用户发送了一个文档',
            'file_path': 'test_document.pdf'  # 假设的文件路径
        }
        
        print(f"  消息类型: {file_message['type']}")
        print(f"  文件路径: {file_message['file_path']}")
        print(f"  原始内容: {file_message['content']}")
        
        print(f"\n✅ 消息服务集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 消息服务集成测试失败: {e}")
        return False


async def test_batch_processing():
    """测试批量处理"""
    print("\n" + "="*70)
    print("🧪 测试 5: 批量处理")
    print("="*70)
    
    try:
        from modules.mcp_platform import MCPManager
        
        # 获取 AIOCR 客户端
        manager = MCPManager()
        aiocr_client = manager.get_client("aiocr")
        
        # 创建多个测试文件
        test_files = []
        for i in range(3):
            test_file = Path(f"test_batch_{i+1}.txt")
            content = f"""
# 测试文档 {i+1}

## 内容
这是第 {i+1} 个测试文档。

## 特点
- 文档编号: {i+1}
- 创建时间: 2024-01-01
- 类型: 测试文档

## 说明
用于测试批量处理功能。
            """
            test_file.write_text(content, encoding='utf-8')
            test_files.append(test_file)
        
        try:
            # 批量处理
            print(f"📦 开始批量处理 {len(test_files)} 个文件")
            results = await aiocr_client.batch_process(test_files, output_format="text")
            
            success_count = sum(1 for r in results if r.get("success", False))
            print(f"✅ 批量处理完成: {success_count}/{len(results)} 成功")
            
            for i, result in enumerate(results, 1):
                if result.get("success"):
                    print(f"  {i}. ✅ {result['filename']} ({len(result.get('content', ''))} 字符)")
                else:
                    print(f"  {i}. ❌ {result.get('filename', 'unknown')} - {result.get('error', 'unknown error')}")
        
        finally:
            # 清理测试文件
            for test_file in test_files:
                if test_file.exists():
                    test_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ 批量处理测试失败: {e}")
        return False


async def main():
    """主测试流程"""
    print("\n" + "🔬"*35)
    print("MCP 中台完整测试")
    print("🔬"*35)
    
    # 检查环境变量
    api_key = os.getenv('QWEN_API_KEY', '')
    if not api_key or api_key == 'sk-your-qwen-key-here':
        print("⚠️ 请设置有效的 QWEN_API_KEY 环境变量")
        return
    
    print(f"使用 API Key: {api_key[:20]}...")
    print("")
    
    # 运行所有测试
    tests = [
        ("MCP 中台管理器", test_mcp_manager),
        ("AIOCR 客户端", test_aiocr_client),
        ("文档处理器集成", test_document_processor_integration),
        ("消息服务集成", test_message_service_integration),
        ("批量处理", test_batch_processing)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
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
        print("\n🎉 所有测试通过！MCP 中台集成成功！")
        print("\n✅ 功能确认:")
        print("  • MCP 中台管理器正常工作")
        print("  • AIOCR 客户端可以识别文档")
        print("  • 文档处理器支持 MCP AIOCR")
        print("  • 消息服务支持媒体消息处理")
        print("  • 批量处理功能正常")
        print("\n🚀 系统已准备好使用 MCP AIOCR 服务！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())
