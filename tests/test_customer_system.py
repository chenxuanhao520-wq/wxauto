#!/usr/bin/env python3
"""
测试客户管理和智能分析系统
"""

# 强制 UTF-8 编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.customer_manager import customer_manager, init_default_groups
from smart_analyzer import smart_analyzer

def test_customer_management():
    """测试客户管理功能"""
    print("🧪 测试客户管理系统...")
    
    # 初始化默认群聊分类
    init_default_groups()
    print("✅ 默认群聊分类已初始化")
    
    # 注册测试客户
    customer_id1 = customer_manager.register_customer(
        name="张三",
        group_name="技术支持群",
        notes="测试客户1",
        priority=2
    )
    print(f"✅ 注册客户1: {customer_id1}")
    
    customer_id2 = customer_manager.register_customer(
        name="李四",
        group_name="VIP客户群",
        notes="VIP测试客户",
        priority=5
    )
    print(f"✅ 注册客户2: {customer_id2}")
    
    # 测试客户查找
    customer = customer_manager.find_customer_by_name("张三", "技术支持群")
    if customer:
        print(f"✅ 找到客户: {customer.customer_id} ({customer.name})")
    else:
        print("❌ 客户查找失败")
    
    # 测试客户活动更新
    customer_manager.update_customer_activity(customer_id1, question_solved=True)
    customer_manager.update_customer_activity(customer_id2, handoff=True)
    print("✅ 客户活动已更新")
    
    # 显示统计信息
    stats = customer_manager.get_customer_statistics()
    print(f"📊 客户统计: {stats}")
    
    return customer_id1, customer_id2

def test_smart_analysis():
    """测试智能分析功能"""
    print("\n🧠 测试智能分析系统...")
    
    # 获取测试客户
    customers = customer_manager.get_customer_list(limit=1)
    if not customers:
        print("❌ 没有找到测试客户")
        return
    
    customer = customers[0]
    print(f"📋 测试客户: {customer.customer_id} ({customer.name})")
    
    # 模拟问题
    question = "我的设备无法正常启动，显示错误代码E03，请帮忙解决"
    
    # 模拟知识库结果
    knowledge_result = {
        "documents": [
            "设备故障排除指南：E03错误通常是通信故障",
            "常见问题解决方案：检查设备连接和电源",
            "技术支持流程：联系技术支持团队"
        ],
        "confidence": 0.85,
        "evidence_summary": "E03错误通常是通信故障，需要检查设备连接和电源状态"
    }
    
    # 进行深度分析
    print("🔍 进行深度分析...")
    analysis = smart_analyzer.deep_think_analysis(customer, question, knowledge_result)
    
    print(f"📊 分析结果:")
    print(f"   问题类型: {analysis.question_type}")
    print(f"   紧急程度: {analysis.urgency_level}/5")
    print(f"   复杂度: {analysis.complexity}")
    print(f"   需要人工: {'是' if analysis.needs_human else '否'}")
    print(f"   置信度: {analysis.confidence:.2f}")
    print(f"   推荐策略: {analysis.recommended_strategy}")
    print(f"   满意度预测: {analysis.satisfaction_prediction:.2f}")
    
    # 生成智能回复
    print("\n💬 生成智能回复...")
    smart_response = smart_analyzer.generate_smart_response(
        customer, question, analysis, knowledge_result
    )
    
    print(f"🤖 智能回复:")
    print(f"   回复类型: {smart_response.response_type}")
    print(f"   回复内容: {smart_response.response_text}")
    print(f"   置信度: {smart_response.confidence:.2f}")
    print(f"   是否需要升级: {'是' if smart_response.escalation_needed else '否'}")
    
    # 检查是否需要升级处理
    should_escalate = smart_analyzer.should_escalate(analysis, customer)
    print(f"🔄 升级判断: {'需要' if should_escalate else '不需要'}")
    
    if should_escalate:
        escalation_msg = smart_analyzer.get_escalation_message(customer, analysis)
        print(f"📞 升级消息: {escalation_msg}")

def test_integration():
    """测试集成功能"""
    print("\n🔗 测试系统集成...")
    
    # 模拟消息处理流程
    from modules.adapters.wxauto_adapter import FakeWxAdapter, Message
    
    # 创建假适配器
    adapter = FakeWxAdapter(whitelisted_groups=["技术支持群", "VIP客户群"])
    
    # 模拟消息
    test_messages = [
        {
            "group": "技术支持群",
            "sender": "王五",
            "content": "@小助手 设备安装遇到问题，请指导"
        },
        {
            "group": "VIP客户群", 
            "sender": "VIP客户",
            "content": "@小助手 紧急问题，设备故障影响生产"
        }
    ]
    
    for i, msg_data in enumerate(test_messages, 1):
        print(f"\n📤 测试消息 {i}:")
        print(f"   群聊: {msg_data['group']}")
        print(f"   发送者: {msg_data['sender']}")
        print(f"   内容: {msg_data['content']}")
        
        # 注入消息
        adapter.inject_message(
            group_name=msg_data['group'],
            sender_name=msg_data['sender'],
            content=msg_data['content'],
            is_at_me=True
        )
        
        # 等待处理
        time.sleep(1)
        
        # 查找客户
        customer = customer_manager.find_customer_by_name(
            msg_data['sender'], msg_data['group']
        )
        
        if customer:
            print(f"✅ 客户识别: {customer.customer_id}")
            print(f"   群聊类型: {customer.group_type}")
            print(f"   优先级: {customer.priority}")
        else:
            print("❌ 客户识别失败")

def main():
    """主测试函数"""
    print("🚀 开始测试客户管理和智能分析系统")
    print("=" * 60)
    
    try:
        # 测试客户管理
        customer_id1, customer_id2 = test_customer_management()
        
        # 测试智能分析
        test_smart_analysis()
        
        # 测试集成功能
        test_integration()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("\n💡 功能说明:")
        print("   1. 客户自动注册和管理")
        print("   2. 群聊分类和优先级管理")
        print("   3. 智能问题分析和分类")
        print("   4. 基于分析结果的智能回复")
        print("   5. 自动升级处理判断")
        print("   6. 客户活动统计和追踪")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
