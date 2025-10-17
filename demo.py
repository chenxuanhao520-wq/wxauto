"""
演示脚本：展示客服中台的完整功能
可在无真实微信环境下运行
"""

# 强制 UTF-8 编码（解决中文显示问题）
import sys
import logging

# 重新配置标准输出为 UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from main import CustomerServiceBot
import time


def demo_basic_flow():
    """演示基础流程：@识别、ACK、分流、回答"""
    print("=" * 60)
    print("演示 1：基础对话流程")
    print("=" * 60)
    
    bot = CustomerServiceBot(use_fake=True)
    
    # 场景 1：高置信度问题（直答）
    print("\n>>> 场景 1：高置信度问题（如何安装设备？）")
    bot.wx_adapter.inject_message(
        group_name='技术支持群',
        sender_name='张三',
        content='如何安装设备？',
        is_at_me=True
    )
    
    for msg in bot.wx_adapter.iter_new_messages():
        bot._process_message(msg)
    
    # 场景 2：中等置信度问题（澄清）
    print("\n>>> 场景 2：中等置信度问题（设备故障）")
    bot.wx_adapter.clear_sent_messages()
    bot.wx_adapter.inject_message(
        group_name='技术支持群',
        sender_name='李四',
        content='设备出现故障怎么办？',
        is_at_me=True
    )
    
    for msg in bot.wx_adapter.iter_new_messages():
        bot._process_message(msg)
    
    # 场景 3：禁答域（转人工）
    print("\n>>> 场景 3：禁答域问题（价格）")
    bot.wx_adapter.clear_sent_messages()
    bot.wx_adapter.inject_message(
        group_name='技术支持群',
        sender_name='王五',
        content='你们的价格是多少？',
        is_at_me=True
    )
    
    for msg in bot.wx_adapter.iter_new_messages():
        bot._process_message(msg)
    
    bot.db.close()


def demo_dedup_and_rate_limit():
    """演示去重与速率限制"""
    print("\n" + "=" * 60)
    print("演示 2：去重与速率限制")
    print("=" * 60)
    
    bot = CustomerServiceBot(use_fake=True)
    
    # 场景 1：重复消息去重
    print("\n>>> 场景 1：发送重复消息（应该被去重）")
    for i in range(2):
        bot.wx_adapter.inject_message(
            group_name='技术支持群',
            sender_name='张三',
            content='重复的问题',
            is_at_me=True
        )
    
    processed = 0
    for msg in bot.wx_adapter.iter_new_messages():
        bot._process_message(msg)
        processed += 1
    
    print(f"  → 实际处理: {processed} 条（第二条被去重）")
    
    # 场景 2：速率限制
    print("\n>>> 场景 2：连续发送多条消息（触发速率限制）")
    bot.wx_adapter.clear_sent_messages()
    
    for i in range(4):
        bot.wx_adapter.inject_message(
            group_name='技术支持群',
            sender_name='频繁提问者',
            content=f'问题 {i}',
            is_at_me=True
        )
    
    for msg in bot.wx_adapter.iter_new_messages():
        bot._process_message(msg)
    
    sent = bot.wx_adapter.get_sent_messages()
    rate_limited = sum(1 for s in sent if '频率稍快' in s['text'])
    print(f"  → 速率限制触发: {rate_limited} 次")
    
    bot.db.close()


def demo_session_management():
    """演示会话管理"""
    print("\n" + "=" * 60)
    print("演示 3：会话管理与摘要")
    print("=" * 60)
    
    bot = CustomerServiceBot(use_fake=True)
    
    # 同一用户多轮对话
    print("\n>>> 场景：多轮对话（会话 turn_count 增加）")
    
    for i in range(3):
        bot.wx_adapter.clear_sent_messages()
        bot.wx_adapter.inject_message(
            group_name='技术支持群',
            sender_name='张三',
            content=f'这是第 {i+1} 轮提问',
            is_at_me=True
        )
        
        for msg in bot.wx_adapter.iter_new_messages():
            bot._process_message(msg)
    
    # 查询会话信息
    session = bot.db.get_session('技术支持群:张三')
    print(f"\n  → 会话轮数: {session.turn_count}")
    print(f"  → 会话状态: {session.status}")
    
    bot.db.close()


def demo_admin_commands():
    """演示管理指令"""
    print("\n" + "=" * 60)
    print("演示 4：管理指令")
    print("=" * 60)
    
    bot = CustomerServiceBot(use_fake=True)
    
    # #status
    print("\n>>> 场景 1：查看系统状态")
    bot.wx_adapter.inject_message(
        group_name='技术支持群',
        sender_name='管理员',
        content='#status',
        is_at_me=True
    )
    
    for msg in bot.wx_adapter.iter_new_messages():
        bot._process_message(msg)
    
    # #mute
    print("\n>>> 场景 2：开启全局静默")
    bot.wx_adapter.clear_sent_messages()
    bot.wx_adapter.inject_message(
        group_name='技术支持群',
        sender_name='管理员',
        content='#mute',
        is_at_me=True
    )
    
    for msg in bot.wx_adapter.iter_new_messages():
        bot._process_message(msg)
    
    print(f"  → 全局静默状态: {bot.global_mute}")
    
    bot.db.close()


def demo_export():
    """演示导出功能"""
    print("\n" + "=" * 60)
    print("演示 5：导出 CSV")
    print("=" * 60)
    
    bot = CustomerServiceBot(use_fake=True)
    
    # 生成一些测试数据
    print("\n>>> 生成测试消息...")
    for i in range(5):
        bot.wx_adapter.inject_message(
            group_name='技术支持群',
            sender_name=f'用户{i}',
            content=f'测试问题 {i}',
            is_at_me=True
        )
    
    for msg in bot.wx_adapter.iter_new_messages():
        bot._process_message(msg)
    
    # 导出
    print("\n>>> 导出 CSV...")
    export_path = bot.db.export_to_csv('exports/demo_logs.csv')
    print(f"  → 导出成功: {export_path}")
    
    # 读取并显示前几行
    with open(export_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
        print(f"  → 总行数: {len(lines)} (含表头)")
        print(f"  → 表头: {lines[0].strip()[:100]}...")
    
    bot.db.close()


def main():
    """运行所有演示"""
    print("\n" + "🚀 " * 20)
    print("微信群聊客服中台 - 功能演示")
    print("🚀 " * 20)
    
    try:
        demo_basic_flow()
        demo_dedup_and_rate_limit()
        demo_session_management()
        demo_admin_commands()
        demo_export()
        
        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
