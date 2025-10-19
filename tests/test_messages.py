#!/usr/bin/env python3
"""
Test Messages Script - Simulate real group chat messages
"""

# Force UTF-8 encoding
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.adapters.wxauto_adapter import FakeWxAdapter

def test_messages():
    """Test various types of messages"""
    
    print("🎯 Starting message processing test...")
    print("=" * 50)
    
    # Create fake adapter
    adapter = FakeWxAdapter(whitelisted_groups=["技术支持群", "VIP客户群"])
    
    # Test message list
    test_messages = [
        {
            "group": "技术支持群",
            "sender": "张三",
            "content": "@小助手 如何安装设备？",
            "description": "High confidence question"
        },
        {
            "group": "技术支持群", 
            "sender": "李四",
            "content": "@小助手 设备出现故障怎么办？",
            "description": "Medium confidence question"
        },
        {
            "group": "技术支持群",
            "sender": "王五", 
            "content": "@小助手 你们的价格是多少？",
            "description": "Forbidden topic (price)"
        },
        {
            "group": "技术支持群",
            "sender": "赵六",
            "content": "@小助手 #status",
            "description": "Admin command"
        },
        {
            "group": "VIP客户群",
            "sender": "VIP客户",
            "content": "@小助手 紧急问题，需要帮助！",
            "description": "VIP group message"
        }
    ]
    
    # Send test messages
    for i, msg in enumerate(test_messages, 1):
        print(f"\n📤 Test {i}: {msg['description']}")
        print(f"   Group: {msg['group']}")
        print(f"   Sender: {msg['sender']}")
        print(f"   Content: {msg['content']}")
        
        # Inject message
        adapter.inject_message(
            group_name=msg['group'],
            sender_name=msg['sender'],
            content=msg['content'],
            is_at_me=True
        )
        
        print(f"   ✅ Message sent")
        
        # Wait for processing
        time.sleep(2)
        
        # Get responses
        responses = list(adapter.iter_new_messages())
        if responses:
            for response in responses:
                print(f"   🤖 Bot reply: {response.content}")
        else:
            print(f"   ⏳ Waiting for processing...")
        
        print("-" * 30)
    
    print("\n🎉 Test completed!")
    print("\n💡 Tips:")
    print("   - Check the main program window for detailed processing logs")
    print("   - Database records all messages and responses")
    print("   - Use #status to check system status")

if __name__ == "__main__":
    test_messages()
