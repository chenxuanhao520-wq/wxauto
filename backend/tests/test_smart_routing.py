#!/usr/bin/env python3
"""
测试智能路由器
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.ai_gateway.smart_router import SmartModelRouter


async def test_smart_routing():
    """测试智能路由"""
    print("=" * 80)
    print("🧪 智能模型路由器测试")
    print("=" * 80)
    
    router = SmartModelRouter()
    
    # 测试用例
    test_cases = [
        {
            'question': '充电桩多少钱？',
            'context': '7kW充电桩价格998元',
            'expected': 'qwen-turbo',
            'description': '简单问答'
        },
        {
            'question': '充电桩如何安装？请详细说明步骤。',
            'context': '安装指南...（500字）',
            'expected': 'qwen-plus',
            'description': '中等难度'
        },
        {
            'question': '如果充电桩红灯亮且有异响，可能是什么原因？应该如何排查？',
            'context': '故障排查手册...（1000字）',
            'expected': 'deepseek',
            'description': '复杂推理'
        },
        {
            'question': '请总结充电桩产品手册的核心要点',
            'context': '产品手册...（3000字）',
            'expected': 'qwen-max',
            'description': '长文总结'
        },
        {
            'question': '充电桩有什么功能？',
            'context': '产品功能列表...',
            'expected': 'qwen-turbo',
            'description': '简单咨询'
        },
        {
            'question': '对比7kW和120kW充电桩的优缺点，给出购买建议',
            'context': '两种型号对比表...（800字）',
            'expected': 'deepseek',
            'description': '对比分析'
        }
    ]
    
    print("\n📋 测试用例:\n")
    
    correct = 0
    total = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        print(f"测试 {i}: {case['description']}")
        print(f"问题: {case['question']}")
        
        # 路由
        routing_result = await router.route(
            question=case['question'],
            context=case['context']
        )
        
        selected_model = routing_result['model_key']
        expected_model = case['expected']
        
        is_correct = selected_model == expected_model
        if is_correct:
            correct += 1
        
        print(f"选择模型: {selected_model} {'✅' if is_correct else f'❌ (期望: {expected_model})'}")
        print(f"原因: {routing_result['reason']}")
        print(f"复杂度: {routing_result.get('complexity', 0):.2f}")
        print(f"预估成本: ¥{routing_result['estimated_cost']:.6f}")
        print(f"预估延迟: {routing_result['estimated_latency']}ms")
        print()
    
    # 统计
    print("=" * 80)
    print(f"✅ 测试完成: {correct}/{total} 正确 ({correct/total*100:.1f}%)")
    print("=" * 80)
    
    # 显示模型统计
    print("\n📊 模型画像:")
    stats = router.get_model_stats()
    for model_key, info in stats['models'].items():
        print(f"\n{model_key}:")
        print(f"  提供商: {info['provider']}")
        print(f"  模型: {info['model']}")
        print(f"  平均成本: ¥{info['cost_per_1k_avg']:.4f}/1K tokens")
        print(f"  平均延迟: {info['latency_ms']}ms")
        print(f"  最适合: {', '.join(info['best_for'])}")


async def test_cost_comparison():
    """测试成本对比"""
    print("\n" + "=" * 80)
    print("💰 成本对比测试（1000次/天）")
    print("=" * 80)
    
    router = SmartModelRouter()
    
    # 模拟1000次问答
    total_cost_qwen_turbo = 0
    total_cost_qwen_plus = 0
    total_cost_deepseek = 0
    total_cost_smart = 0
    
    # 简化模拟
    simulated_questions = [
        ('简单', 0.2, 500),  # 简单问答，50%
        ('中等', 0.5, 800),  # 中等难度，30%
        ('复杂', 0.8, 1000)  # 复杂推理，20%
    ]
    
    for question_type, complexity, context_len in simulated_questions:
        if question_type == '简单':
            count = 500
        elif question_type == '中等':
            count = 300
        else:
            count = 200
        
        # 计算各方案成本
        total_tokens = context_len + 200  # 输出200 tokens
        
        # Qwen-turbo方案
        cost_turbo = count * (context_len/1000 * 0.0006 + 200/1000 * 0.0024)
        total_cost_qwen_turbo += cost_turbo
        
        # Qwen-plus方案
        cost_plus = count * (context_len/1000 * 0.0012 + 200/1000 * 0.0048)
        total_cost_qwen_plus += cost_plus
        
        # DeepSeek方案
        cost_deepseek = count * (context_len/1000 * 0.001 + 200/1000 * 0.008)
        total_cost_deepseek += cost_deepseek
        
        # 智能路由方案
        if question_type == '简单':
            cost_smart = cost_turbo
        elif question_type == '中等':
            cost_smart = cost_plus
        else:
            cost_smart = cost_deepseek
        
        total_cost_smart += cost_smart
    
    print("\n💰 每天成本对比:")
    print(f"Qwen-turbo全用: ¥{total_cost_qwen_turbo:.2f}/天 = ¥{total_cost_qwen_turbo*30:.2f}/月")
    print(f"Qwen-plus全用: ¥{total_cost_qwen_plus:.2f}/天 = ¥{total_cost_qwen_plus*30:.2f}/月")
    print(f"DeepSeek全用: ¥{total_cost_deepseek:.2f}/天 = ¥{total_cost_deepseek*30:.2f}/月")
    print(f"智能路由方案: ¥{total_cost_smart:.2f}/天 = ¥{total_cost_smart*30:.2f}/月 ⭐")
    
    print(f"\n💡 智能路由相比DeepSeek全用节省: {(total_cost_deepseek - total_cost_smart)/total_cost_deepseek*100:.1f}%")


async def main():
    """主函数"""
    # 测试路由逻辑
    await test_smart_routing()
    
    # 测试成本对比
    await test_cost_comparison()


if __name__ == "__main__":
    asyncio.run(main())
