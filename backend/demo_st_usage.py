#!/usr/bin/env python3
"""
Sequential Thinking 工具使用示例（演示版）
展示如何调用 sequential-thinking 的各种工具

注意：这是一个演示示例，展示了如何使用 SequentialThinkingClient 的各个方法
实际运行需要配置有效的 QWEN_API_KEY
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_section(title: str):
    """打印章节标题"""
    print("\n" + "=" * 80)
    print(f"📌 {title}")
    print("=" * 80)


def print_code_block(code: str, language: str = "python"):
    """打印代码块"""
    print(f"```{language}")
    print(code)
    print("```")


def demo_introduction():
    """演示介绍"""
    print_section("Sequential Thinking 工具使用指南")
    
    print("""
Sequential Thinking 是阿里云通义千问提供的结构化思考工具，
它可以帮助你进行深度推理、问题分解、决策分析等复杂思维任务。

本示例将展示如何使用 SequentialThinkingClient 的所有工具方法。
    """)


def demo_basic_setup():
    """演示 1: 基础设置"""
    print_section("示例 1: 初始化 Sequential Thinking 客户端")
    
    print("\n📝 代码示例:\n")
    
    code = """from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2

# 初始化 MCP Manager（自动加载 config/mcp_config.yaml）
manager = MCPManagerV2(config_path="config/mcp_config.yaml")

# 获取 Sequential Thinking 客户端
st_client = manager.get_client('sequential_thinking')

# 检查客户端是否可用
if st_client:
    print("✅ Sequential Thinking 客户端已就绪")
else:
    print("❌ 客户端初始化失败")"""
    
    print_code_block(code)
    
    print("\n💡 说明:")
    print("  - MCPManagerV2 会自动从配置文件加载所有 MCP 服务")
    print("  - Sequential Thinking 服务需要配置 QWEN_API_KEY")
    print("  - 客户端支持自动重试和缓存机制")


def demo_sequential_thinking():
    """演示 2: 基础结构化思考"""
    print_section("示例 2: 使用 sequential_thinking() 进行结构化分析")
    
    print("\n🎯 使用场景:")
    print("  当你需要对一个问题进行结构化、多步骤的深度分析时使用")
    
    print("\n📝 代码示例:\n")
    
    code = """# 调用 sequential_thinking 方法
result = await st_client.sequential_thinking(
    problem="如何优化微信智能客服系统的响应时间？",
    context="当前平均响应时间3秒，目标是降到1秒以内",
    max_steps=5,              # 最多5个思考步骤
    thinking_style="analytical"  # 分析型思考风格
)

# 处理返回结果
if result.get("success"):
    print(f"结论: {result['conclusion']}")
    print(f"置信度: {result['confidence']}")
    
    # 遍历思考步骤
    for i, step in enumerate(result['thinking_steps'], 1):
        print(f"步骤 {i}: {step}")"""
    
    print_code_block(code)
    
    print("\n📊 参数说明:")
    print("  - problem (必填): 要分析的问题")
    print("  - context (可选): 背景上下文信息")
    print("  - max_steps (默认5): 最大思考步骤数")
    print("  - thinking_style (默认analytical): 思考风格")
    print("    可选值: analytical（分析型）, creative（创意型）, logical（逻辑型）")
    
    print("\n✅ 返回数据结构:")
    example_result = {
        "success": True,
        "problem": "如何优化响应时间？",
        "thinking_steps": [
            "步骤1: 分析当前瓶颈",
            "步骤2: 确定优化方向",
            "步骤3: 制定实施方案"
        ],
        "conclusion": "通过缓存和异步处理可以将响应时间降到1秒以内",
        "confidence": 0.85,
        "alternatives": ["方案A", "方案B"],
        "reasoning": "基于技术栈分析...",
        "metadata": {}
    }
    print_code_block(json.dumps(example_result, indent=2, ensure_ascii=False), "json")


def demo_problem_decomposition():
    """演示 3: 问题分解"""
    print_section("示例 3: 使用 problem_decomposition() 分解复杂问题")
    
    print("\n🎯 使用场景:")
    print("  当面对一个复杂的大问题，需要分解为多个可执行的子任务时使用")
    
    print("\n📝 代码示例:\n")
    
    code = """# 调用问题分解方法
result = await st_client.problem_decomposition(
    complex_problem="构建一个完整的智能客服中台系统",
    decomposition_level=5  # 分解为5个子问题
)

# 处理结果
if result.get("success"):
    print(f"共分解为 {len(result['sub_problems'])} 个子问题")
    
    for i, sub_problem in enumerate(result['sub_problems'], 1):
        print(f"\\n子问题 {i}:")
        print(f"  {sub_problem}")"""
    
    print_code_block(code)
    
    print("\n📊 参数说明:")
    print("  - complex_problem (必填): 需要分解的复杂问题")
    print("  - decomposition_level (默认3): 分解层级/子问题数量")
    
    print("\n✅ 返回数据结构:")
    example_result = {
        "success": True,
        "original_problem": "构建智能客服中台",
        "sub_problems": [
            "子问题1: 设计系统架构",
            "子问题2: 实现AI智能回复",
            "子问题3: 集成知识库检索",
            "子问题4: 开发客户管理功能",
            "子问题5: 部署与测试"
        ],
        "decomposition_level": 5,
        "total_steps": 7,
        "confidence": 0.9
    }
    print_code_block(json.dumps(example_result, indent=2, ensure_ascii=False), "json")


def demo_decision_analysis():
    """演示 4: 决策分析"""
    print_section("示例 4: 使用 decision_analysis() 进行决策分析")
    
    print("\n🎯 使用场景:")
    print("  当需要在多个方案中做出选择，进行结构化的决策分析时使用")
    
    print("\n📝 代码示例:\n")
    
    code = """# 调用决策分析方法
result = await st_client.decision_analysis(
    decision_context="选择向量数据库方案用于智能客服系统",
    options=[
        "Pinecone: 云服务，按量付费，月成本$70",
        "Supabase pgvector: 开源免费，需要自己优化",
        "Milvus: 高性能开源，需要独立部署"
    ],
    criteria=[
        "成本（一次性+运维）",
        "查询性能",
        "可维护性",
        "扩展性"
    ]
)

# 处理结果
if result.get("success"):
    print(f"推荐方案: {result['recommendation']}")
    print(f"置信度: {result['confidence']}")
    
    for analysis in result['analysis']:
        print(f"\\n分析: {analysis}")"""
    
    print_code_block(code)
    
    print("\n📊 参数说明:")
    print("  - decision_context (必填): 决策背景说明")
    print("  - options (必填): 可选方案列表")
    print("  - criteria (可选): 评估标准列表")
    
    print("\n✅ 返回数据结构:")
    example_result = {
        "success": True,
        "decision_context": "选择向量数据库方案",
        "options": ["Pinecone", "Supabase pgvector", "Milvus"],
        "criteria": ["成本", "性能", "可维护性", "扩展性"],
        "analysis": [
            "方案对比分析...",
            "成本效益评估...",
            "风险分析..."
        ],
        "recommendation": "推荐使用 Supabase pgvector，理由是...",
        "confidence": 0.88,
        "alternatives": ["如果预算充足可考虑 Pinecone"]
    }
    print_code_block(json.dumps(example_result, indent=2, ensure_ascii=False), "json")


def demo_creative_brainstorming():
    """演示 5: 创意头脑风暴"""
    print_section("示例 5: 使用 creative_brainstorming() 生成创意想法")
    
    print("\n🎯 使用场景:")
    print("  当需要针对某个主题进行创意发散、生成多个创新想法时使用")
    
    print("\n📝 代码示例:\n")
    
    code = """# 调用创意头脑风暴方法
result = await st_client.creative_brainstorming(
    topic="如何提升B2B客户的服务满意度",
    constraints=[
        "技术实现难度中等以下",
        "3个月内可以落地",
        "成本增加不超过20%"
    ],
    num_ideas=5  # 生成5个创意想法
)

# 处理结果
if result.get("success"):
    print(f"生成了 {result['total_generated']} 个创意想法")
    
    for i, idea in enumerate(result['ideas'], 1):
        print(f"\\n想法 {i}: {idea}")"""
    
    print_code_block(code)
    
    print("\n📊 参数说明:")
    print("  - topic (必填): 头脑风暴主题")
    print("  - constraints (可选): 约束条件列表")
    print("  - num_ideas (默认10): 期望生成的想法数量")
    
    print("\n✅ 返回数据结构:")
    example_result = {
        "success": True,
        "topic": "提升客户服务满意度",
        "constraints": ["中等难度", "3个月落地", "成本+20%"],
        "ideas": [
            "想法1: 智能预判客户需求",
            "想法2: 实时情绪分析",
            "想法3: 个性化服务推荐",
            "想法4: 自动问题分类",
            "想法5: 知识库智能更新"
        ],
        "total_generated": 5,
        "thinking_process": ["...", "..."],
        "confidence": 0.82
    }
    print_code_block(json.dumps(example_result, indent=2, ensure_ascii=False), "json")


def demo_health_check():
    """演示 6: 健康检查"""
    print_section("示例 6: 使用 health_check() 检查服务状态")
    
    print("\n🎯 使用场景:")
    print("  在使用服务前，检查 Sequential Thinking 服务是否可用")
    
    print("\n📝 代码示例:\n")
    
    code = """# 调用健康检查
health = await st_client.health_check()

if health['status'] == 'healthy':
    print("✅ Sequential Thinking 服务正常")
    print(f"可用工具数: {health['tools_available']}")
else:
    print("❌ 服务异常")
    print(f"错误: {health.get('error', '未知错误')}")"""
    
    print_code_block(code)
    
    print("\n✅ 返回数据结构:")
    example_result = {
        "status": "healthy",
        "service": "sequential_thinking",
        "tools_available": 4,
        "test_result": True,
        "message": "Sequential Thinking 服务正常"
    }
    print_code_block(json.dumps(example_result, indent=2, ensure_ascii=False), "json")


def demo_complete_example():
    """演示 7: 完整使用示例"""
    print_section("示例 7: 完整的实际应用示例")
    
    print("\n🎯 场景: 设计客户流失预警系统\n")
    
    code = """import asyncio
from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2


async def design_churn_prediction_system():
    \"\"\"设计客户流失预警系统\"\"\"
    
    # 1. 初始化客户端
    manager = MCPManagerV2(config_path="config/mcp_config.yaml")
    st_client = manager.get_client('sequential_thinking')
    
    # 2. 健康检查
    health = await st_client.health_check()
    if health['status'] != 'healthy':
        print("服务不可用")
        return
    
    # 3. 问题分解：将大问题分解为子任务
    print("\\n📋 步骤1: 问题分解")
    decomp_result = await st_client.problem_decomposition(
        complex_problem=\"\"\"
        设计一个客户流失预警系统，包括：
        - 数据指标体系
        - 预警规则引擎
        - 自动化挽留策略
        - 实施步骤
        \"\"\",
        decomposition_level=4
    )
    
    if decomp_result['success']:
        for sub in decomp_result['sub_problems']:
            print(f"  - {sub}")
    
    # 4. 决策分析：选择技术方案
    print("\\n⚖️ 步骤2: 技术方案选择")
    decision_result = await st_client.decision_analysis(
        decision_context="选择客户流失预测的机器学习方案",
        options=[
            "基于规则的评分系统（简单快速）",
            "传统机器学习模型（需要训练数据）",
            "LLM智能分析（成本较高但更灵活）"
        ],
        criteria=["实现难度", "准确率", "成本", "维护性"]
    )
    
    if decision_result['success']:
        print(f"  推荐: {decision_result['recommendation']}")
    
    # 5. 创意头脑风暴：挽留措施
    print("\\n💡 步骤3: 创意挽留措施")
    brainstorm_result = await st_client.creative_brainstorming(
        topic="自动化客户挽留措施",
        constraints=[
            "不打扰客户",
            "个性化程度高",
            "可自动执行"
        ],
        num_ideas=3
    )
    
    if brainstorm_result['success']:
        for idea in brainstorm_result['ideas']:
            print(f"  - {idea}")
    
    # 6. 结构化思考：制定实施计划
    print("\\n🎯 步骤4: 制定实施计划")
    plan_result = await st_client.sequential_thinking(
        problem=\"\"\"
        基于以上分析，制定客户流失预警系统的3个月实施计划，
        包括里程碑、资源需求、风险评估
        \"\"\",
        max_steps=6,
        thinking_style="analytical"
    )
    
    if plan_result['success']:
        print(f"  {plan_result['conclusion']}")
    
    print("\\n✅ 系统设计完成！")


# 运行示例
asyncio.run(design_churn_prediction_system())"""
    
    print_code_block(code)
    
    print("\n💡 这个示例展示了如何组合使用多个工具方法来解决复杂的实际问题。")


def demo_best_practices():
    """最佳实践建议"""
    print_section("最佳实践建议")
    
    print("""
1️⃣ **选择合适的工具方法**
   - 需要深度分析 → sequential_thinking()
   - 大问题拆解 → problem_decomposition()
   - 多方案选择 → decision_analysis()
   - 创意发散 → creative_brainstorming()

2️⃣ **优化参数设置**
   - max_steps: 一般5-8步足够，太多会影响性能
   - thinking_style: 根据问题类型选择合适的思考风格
   - num_ideas: 创意数量3-10个比较合适

3️⃣ **错误处理**
   - 始终检查 result['success'] 状态
   - 捕获异常并提供友好提示
   - 使用 health_check() 预检查服务状态

4️⃣ **性能优化**
   - 利用内置缓存机制（相同问题会命中缓存）
   - 合理设置超时时间
   - 避免在循环中频繁调用

5️⃣ **组合使用**
   - 多个工具方法可以组合使用
   - 按问题→分解→决策→实施的流程设计
   - 每个步骤的输出可以作为下一步的输入

6️⃣ **配置管理**
   - 确保 QWEN_API_KEY 已正确配置
   - 在 config/mcp_config.yaml 中调整服务参数
   - 生产环境建议启用缓存和限流
    """)


def main():
    """主函数"""
    print("\n" + "🌟" * 40)
    print("  Sequential Thinking 工具完整使用指南")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🌟" * 40)
    
    # 运行所有演示
    demo_introduction()
    demo_basic_setup()
    demo_sequential_thinking()
    demo_problem_decomposition()
    demo_decision_analysis()
    demo_creative_brainstorming()
    demo_health_check()
    demo_complete_example()
    demo_best_practices()
    
    print("\n" + "=" * 80)
    print("🎉 使用指南演示完成！")
    print("=" * 80)
    print("\n💡 提示: 这些代码示例可以直接在你的项目中使用")
    print("📝 记得先配置 QWEN_API_KEY 环境变量\n")


if __name__ == "__main__":
    main()
