#!/usr/bin/env python3
"""
测试消息脚本 - 模拟真实的群聊消息
"""

# 强制 UTF-8 编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from adapters.wxauto_adapter import FakeWxAdapter

def test_messages():
    """测试各种类型的消息"""
    
    print("🎯 开始测试消息处理...")
    print("=" * 50)
    
    # 创建假适配器
    adapter = FakeWxAdapter(whitelisted_groups=["技术支持群", "VIP客户群"])
    
    # 测试消息列表
    test_messages = [
        {
            "group": "技术支持群",
            "sender": "张三",
            "content": "@小助手 如何安装设备？",
            "description": "高置信度问题"
        },
        {
            "group": "技术支持群", 
            "sender": "李四",
            "content": "@小助手 设备出现故障怎么办？",
            "description": "中等置信度问题"
        },
        {
            "group": "技术支持群",
            "sender": "王五", 
            "content": "@小助手 你们的价格是多少？",
            "description": "禁答域问题（价格）"
        },
        {
            "group": "技术支持群",
            "sender": "赵六",
            "content": "@小助手 #status",
            "description": "管理指令"
        },
        {
            "group": "VIP客户群",
            "sender": "VIP客户",
            "content": "@小助手 紧急问题，需要帮助！",
            "description": "VIP群消息"
        }
    ]
    
    # 发送测试消息
    for i, msg in enumerate(test_messages, 1):
        print(f"\n📤 测试 {i}: {msg['description']}")
        print(f"   群聊: {msg['group']}")
        print(f"   发送者: {msg['sender']}")
        print(f"   内容: {msg['content']}")
        
        # 注入消息
        adapter.inject_message(
            group_name=msg['group'],
            sender_name=msg['sender'],
            content=msg['content'],
            is_at_me=True
        )
        
        print(f"   ✅ 消息已发送")
        
        # 等待处理
        time.sleep(2)
        
        # 获取响应
        responses = list(adapter.iter_new_messages())
        if responses:
            for response in responses:
                print(f"   🤖 机器人回复: {response.content}")
        else:
            print(f"   ⏳ 等待处理中...")
        
        print("-" * 30)
    
    print("\n🎉 测试完成！")
    print("\n💡 提示：")
    print("   - 查看主程序窗口可以看到详细的处理日志")
    print("   - 数据库会记录所有消息和响应")
    print("   - 可以使用 #status 查看系统状态")

if __name__ == "__main__":
    test_messages()
