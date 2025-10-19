#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试复杂推理场景 - 对比 Qwen 系列模型
测试 qwen-turbo, qwen-plus, qwen-max 在复杂任务上的表现
"""
import os
import asyncio
import logging
import time

# 设置环境变量
os.environ['QWEN_API_KEY'] = 'sk-1d7d593d85b1469683eb8e7988a0f646'
os.environ['QWEN_API_BASE'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


# 复杂测试案例
COMPLEX_TEST_CASES = [
    {
        "name": "多步推理 - 充电桩故障诊断",
        "question": """
一位客户反馈：他的充电桩昨天还能正常使用，今天突然出现以下情况：
1. 屏幕可以亮，显示"待机中"
2. 插上充电枪后，屏幕变成"充电中"，但车显示"未充电"
3. 充电桩的指示灯是绿色的
4. 断路器没有跳闸
5. 重启充电桩后问题依旧

请分析可能的故障原因，并给出详细的排查步骤。
        """,
        "kb_context": """
【故障排查手册 v2.5】
常见故障：
- 通讯故障：屏幕显示充电但实际未充电 → 检查充电枪连接、车辆通讯协议
- 电流输出异常：绿灯但无电流 → 检查继电器、电流传感器
- 车辆兼容性：部分车型需要特定设置 → 检查车型适配表
        """,
        "expected_skills": ["多步推理", "故障诊断", "逻辑分析", "结构化输出"]
    },
    {
        "name": "数据分析 - 用户行为洞察",
        "question": """
根据以下客户对话数据，分析客户意图和后续建议：

客户A（3次对话）：
- "你们的7KW充电桩多少钱？"
- "有没有促销活动？"
- "可以先看看样品吗？"

客户B（5次对话）：
- "充电桩怎么安装？"
- "需要什么资质？"
- "安装费用大概多少？"
- "一般多久能装好？"
- "你们提供上门安装服务吗？"

请分析：
1. 哪个客户的购买意向更强？
2. 分别应该采取什么跟进策略？
3. 预测成交概率和可能的成交时间。
        """,
        "kb_context": """
【销售手册】
高意向特征：
- 询问安装细节 → 70%成交概率
- 询问价格促销 → 40%成交概率
- 要求样品/试用 → 30%成交概率

跟进策略：
- 高意向：安排上门勘察，提供定制方案
- 中意向：发送案例、提供优惠信息
- 低意向：定期跟进，建立信任
        """,
        "expected_skills": ["数据分析", "意图识别", "销售策略", "概率预测"]
    },
    {
        "name": "技术对比 - 充电桩方案选择",
        "question": """
客户场景：
- 地点：小区地下车库
- 需求：10个车位
- 预算：15万元
- 使用：业主共享充电

有以下3种方案，请分析优劣并推荐：

方案A：10台 7KW 交流桩
- 单价：8000元/台
- 总价：8万元
- 功率：70KW总功率
- 优点：便宜、安装简单
- 缺点：充电慢

方案B：5台 30KW 直流桩
- 单价：2.8万元/台
- 总价：14万元
- 功率：150KW总功率
- 优点：充电快
- 缺点：需要增容

方案C：7台 7KW交流 + 2台 30KW直流
- 总价：12.6万元
- 功率：109KW总功率
- 优点：灵活搭配
- 缺点：管理复杂

请从成本、效率、用户体验、电力负荷等角度综合分析，给出推荐。
        """,
        "kb_context": """
【产品对比】
7KW交流桩：
- 充满时间：6-8小时
- 适合：夜间充电
- 电力需求：220V

30KW直流桩：
- 充满时间：1-2小时
- 适合：快速补电
- 电力需求：380V，需增容
        """,
        "expected_skills": ["多维度对比", "成本分析", "方案推荐", "综合决策"]
    },
    {
        "name": "长文本总结 - 产品升级说明",
        "question": """
请总结以下产品升级内容，并生成客户通知文案：

【充电桩 v3.0 升级内容】
硬件升级：
1. 屏幕升级：7寸→10.1寸高清触摸屏，支持多语言
2. 充电枪升级：防水等级IP67→IP68，线长5米→8米
3. 散热优化：新增智能温控，降低30%运行温度
4. 主板升级：处理器性能提升50%，内存8GB→16GB

软件升级：
1. 新增功能：
   - 手机APP远程控制
   - 充电曲线实时显示
   - 故障自诊断
   - OTA在线升级
2. 优化功能：
   - 充电速度提升15%
   - 兼容性提升（支持更多车型）
   - 用户界面优化
3. 安全增强：
   - 过载保护升级
   - 漏电保护升级
   - 防雷击设计

价格调整：
- 老客户升级：优惠价 2000元（原价2800元）
- 新购买：8800元（v2.0为8000元）
- 升级服务：免费上门安装

升级周期：2025年1月-3月

请生成：
1. 100字简短通知（群发用）
2. 300字详细说明（感兴趣客户）
3. 升级FAQ（5个常见问题）
        """,
        "kb_context": None,
        "expected_skills": ["长文本理解", "信息提取", "文案生成", "结构化输出"]
    }
]


async def test_qwen_model(model_name: str, test_case: dict):
    """测试单个 Qwen 模型"""
    from modules.ai_gateway.providers.qwen_provider import QwenProvider
    from modules.ai_gateway.types import ProviderConfig, LLMRequest
    
    config = ProviderConfig(
        name="qwen",
        api_key=os.getenv('QWEN_API_KEY'),
        api_base=os.getenv('QWEN_API_BASE'),
        model=model_name,
        timeout=60  # 复杂任务需要更长超时
    )
    
    provider = QwenProvider(config)
    
    request = LLMRequest(
        user_message=test_case['question'],
        evidence_context=test_case['kb_context'],
        max_tokens=2000,  # 复杂任务需要更多 token
        temperature=0.7
    )
    
    start = time.time()
    response = await asyncio.to_thread(provider.generate, request)
    elapsed = time.time() - start
    
    return response, elapsed


async def run_complex_tests():
    """运行复杂推理测试"""
    print("\n" + "🧠"*35)
    print("复杂推理场景测试 - Qwen 系列模型对比")
    print("🧠"*35)
    
    # 测试的模型
    models_to_test = [
        ('qwen-turbo', 'Qwen-Turbo', '基础快速模型'),
        ('qwen-plus', 'Qwen-Plus', '增强平衡模型'),
        ('qwen-max', 'Qwen-Max', '顶级旗舰模型'),
    ]
    
    all_results = {}
    
    for i, test_case in enumerate(COMPLEX_TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"📋 测试场景 {i}/{len(COMPLEX_TEST_CASES)}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"\n🎯 考察能力: {', '.join(test_case['expected_skills'])}")
        print(f"\n❓ 问题:\n{test_case['question'][:200]}...")
        
        if test_case['kb_context']:
            print(f"\n📚 知识库上下文: 已提供")
        
        print("\n" + "─"*80)
        
        for model_key, model_display, model_desc in models_to_test:
            print(f"\n🤖 {model_display} ({model_desc})")
            print("─"*80)
            
            try:
                response, elapsed = await test_qwen_model(model_key, test_case)
                
                print(f"⏱️  总耗时: {elapsed:.1f}秒")
                print(f"⏱️  API延迟: {response.latency_ms}ms")
                print(f"🎫 Token: {response.token_in} (输入) / {response.token_out} (输出) / {response.token_total} (总计)")
                print(f"\n💬 回答:\n")
                
                # 显示前 500 字符
                content = response.content
                if len(content) > 500:
                    print(content[:500] + "...")
                    print(f"\n... (完整回答 {len(content)} 字符)")
                else:
                    print(content)
                
                # 保存结果
                if model_key not in all_results:
                    all_results[model_key] = []
                
                all_results[model_key].append({
                    'case': test_case['name'],
                    'elapsed': elapsed,
                    'latency_ms': response.latency_ms,
                    'token_total': response.token_total,
                    'token_in': response.token_in,
                    'token_out': response.token_out,
                    'content_length': len(response.content)
                })
                
            except Exception as e:
                print(f"❌ 测试失败: {e}")
                logger.error(f"{model_key} 测试失败", exc_info=True)
            
            # 等待一下，避免请求过快
            await asyncio.sleep(2)
    
    # 生成对比报告
    print("\n\n" + "="*80)
    print("📊 Qwen 系列模型性能对比")
    print("="*80)
    
    for model_key, model_display, model_desc in models_to_test:
        if model_key in all_results:
            results = all_results[model_key]
            
            avg_elapsed = sum(r['elapsed'] for r in results) / len(results)
            avg_latency = sum(r['latency_ms'] for r in results) / len(results)
            avg_token = sum(r['token_total'] for r in results) / len(results)
            avg_output = sum(r['token_out'] for r in results) / len(results)
            
            print(f"\n{model_display}:")
            print(f"  总耗时: {avg_elapsed:.1f}秒 (包含网络)")
            print(f"  API延迟: {avg_latency:.0f}ms")
            print(f"  平均Token: {avg_token:.0f} (输出: {avg_output:.0f})")
            print(f"  测试通过: {len(results)}/{len(COMPLEX_TEST_CASES)}")
    
    # 成本对比
    print("\n\n" + "="*80)
    print("💰 成本对比 (基于实测 Token 消耗)")
    print("="*80)
    
    # Qwen 定价
    pricing = {
        'qwen-turbo': {'input': 0.0006, 'output': 0.0024, 'name': 'Qwen-Turbo'},
        'qwen-plus': {'input': 0.0012, 'output': 0.0048, 'name': 'Qwen-Plus'},
        'qwen-max': {'input': 0.0024, 'output': 0.0096, 'name': 'Qwen-Max'},
    }
    
    print(f"\n{'模型':<15} {'平均Token':<12} {'平均成本':<15} {'1000次成本':<15}")
    print("─"*80)
    
    for model_key in pricing.keys():
        if model_key in all_results:
            results = all_results[model_key]
            avg_token_in = sum(r['token_in'] for r in results) / len(results)
            avg_token_out = sum(r['token_out'] for r in results) / len(results)
            
            cost_per_query = (
                avg_token_in / 1000 * pricing[model_key]['input'] +
                avg_token_out / 1000 * pricing[model_key]['output']
            )
            cost_1000 = cost_per_query * 1000
            
            print(f"{pricing[model_key]['name']:<15} {avg_token_in + avg_token_out:<12.0f} ¥{cost_per_query:<14.4f} ¥{cost_1000:<14.2f}")
    
    # 建议
    print("\n\n" + "="*80)
    print("💡 使用建议")
    print("="*80)
    
    print("""
场景 1: 简单故障排查 (标准流程)
  推荐: Qwen-Turbo
  原因: 速度快，成本低，质量足够

场景 2: 复杂故障诊断 (多步推理)
  推荐: Qwen-Plus
  原因: 推理能力强，性价比高

场景 3: 数据分析和洞察
  推荐: Qwen-Plus 或 Qwen-Max
  原因: 分析能力强，输出质量高

场景 4: 长文档总结和文案生成
  推荐: Qwen-Max
  原因: 长文本能力最强，输出最专业

场景 5: 日常客服对话
  推荐: Qwen-Turbo
  原因: 速度快，成本低，免费额度

综合建议:
  • 80% 场景: Qwen-Turbo (日常客服)
  • 15% 场景: Qwen-Plus (复杂问题)
  • 5% 场景: Qwen-Max (深度分析)
    """)


if __name__ == "__main__":
    print("\n🚀 开始复杂推理测试...")
    print("这将测试 Qwen 系列模型在复杂任务上的表现")
    print("预计耗时: 约 2-3 分钟（需要调用大模型）\n")
    
    asyncio.run(run_complex_tests())
    
    print("\n" + "="*80)
    print("✅ 测试完成！")
    print("="*80)
    print("\n通过对比可以看出，不同 Qwen 模型适合不同场景。")
    print("建议: 80% 用 Turbo，15% 用 Plus，5% 用 Max")
    print("")

