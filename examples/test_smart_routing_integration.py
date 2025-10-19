#!/usr/bin/env python3
"""
测试智能路由集成
验证智能路由在实际消息处理中的效果
"""
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_ai_gateway_with_routing():
    """测试AI网关的智能路由功能"""
    print("=" * 80)
    print("🧪 测试AI网关智能路由")
    print("=" * 80)
    
    # 设置测试环境变量
    import os
    os.environ['ENABLE_SMART_ROUTING'] = 'true'
    os.environ['PRIMARY_PROVIDER'] = 'qwen'
    os.environ['PRIMARY_MODEL'] = 'qwen-turbo'
    os.environ['FALLBACK_PROVIDER'] = 'deepseek'
    
    # 初始化AI网关
    from modules.ai_gateway.gateway import AIGateway
    
    print("\n📋 初始化AI网关...")
    gateway = AIGateway(
        primary_provider='qwen',
        primary_model='qwen-turbo',
        fallback_provider='deepseek',
        enable_smart_routing=True
    )
    
    # 健康检查
    health = gateway.health_check()
    print(f"\n💊 健康检查:")
    print(f"  智能路由: {'✅ 启用' if health['smart_routing_enabled'] else '❌ 禁用'}")
    print(f"  可用提供商: {health['total_providers']}")
    
    if health.get('routing_providers'):
        print(f"\n  路由提供商:")
        for provider in health['routing_providers']:
            status = '✅' if provider['available'] else '❌'
            print(f"    {status} {provider['key']}: {provider['name']}")
    
    # 测试用例
    test_cases = [
        {
            'question': '充电桩多少钱？',
            'context': '7kW充电桩价格998元',
            'expected_model': 'qwen-turbo',
            'description': '简单问答'
        },
        {
            'question': '充电桩如何安装？请详细说明。',
            'context': None,
            'expected_model': 'qwen-plus',
            'description': '中等难度'
        },
        {
            'question': '充电桩红灯亮且有异响是什么原因？应该怎么排查？',
            'context': None,
            'expected_model': 'deepseek',
            'description': '复杂故障排查'
        }
    ]
    
    print("\n" + "=" * 80)
    print("📋 测试智能路由决策")
    print("=" * 80)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {case['description']}")
        print(f"问题: {case['question']}")
        print(f"期望模型: {case['expected_model']}")
        
        # 构建路由元数据
        metadata = {
            'is_critical': '故障' in case['question'] or '异常' in case['question']
        }
        
        try:
            # 调用生成（智能路由会自动选择模型）
            response = await gateway.generate(
                user_message=case['question'],
                evidence_context=case['context'],
                metadata=metadata
            )
            
            print(f"实际选择: {response.model}")
            print(f"提供商: {response.provider}")
            print(f"延迟: {response.latency_ms}ms")
            print(f"Tokens: {response.token_total}")
            
            if hasattr(response, 'routing_info') and response.routing_info:
                routing_info = response.routing_info
                print(f"路由原因: {routing_info.get('reason', 'N/A')}")
                print(f"复杂度: {routing_info.get('complexity', 0):.2f}")
            
            # 检查是否符合预期
            is_correct = case['expected_model'] in response.model.lower()
            print(f"结果: {'✅ 符合预期' if is_correct else '⚠️  与预期不同'}")
            
        except Exception as e:
            print(f"❌ 调用失败: {e}")
    
    print("\n" + "=" * 80)


async def test_message_service_with_routing():
    """测试消息服务的智能路由集成"""
    print("\n" + "=" * 80)
    print("🧪 测试消息服务智能路由集成")
    print("=" * 80)
    
    try:
        from server.services.message_service import MessageService
        
        print("\n📋 初始化消息服务...")
        service = MessageService()
        
        # 测试消息
        test_messages = [
            {
                'id': 'msg_001',
                'content': '充电桩有什么功能？',
                'sender': '用户A',
                'chat_id': 'chat_001',
                'type': 'text'
            },
            {
                'id': 'msg_002',
                'content': '充电桩红灯亮且有异响，可能是什么原因？如何排查？',
                'sender': '用户B',
                'chat_id': 'chat_002',
                'type': 'text'
            }
        ]
        
        for message in test_messages:
            print(f"\n处理消息: {message['content']}")
            
            result = await service.process_message(
                agent_id='agent_001',
                message=message
            )
            
            print(f"回复动作: {result.get('action')}")
            print(f"回复内容: {result.get('content', '')[:100]}...")
            print(f"使用模型: {result.get('model_used', 'N/A')}")
            
            if result.get('routing_info'):
                routing_info = result['routing_info']
                print(f"路由信息: 复杂度={routing_info.get('complexity', 0):.2f}")
        
        print("\n✅ 消息服务智能路由测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_routing_stats():
    """测试路由统计"""
    print("\n" + "=" * 80)
    print("📊 智能路由统计信息")
    print("=" * 80)
    
    from modules.ai_gateway.gateway import AIGateway
    
    gateway = AIGateway(
        primary_provider='qwen',
        primary_model='qwen-turbo',
        fallback_provider='deepseek',
        enable_smart_routing=True
    )
    
    # 获取路由统计
    stats = gateway.get_routing_stats()
    
    print(f"\n智能路由启用: {stats['smart_routing_enabled']}")
    
    if stats.get('router_stats'):
        router_stats = stats['router_stats']
        print(f"总模型数: {router_stats['total_models']}")
        
        print(f"\n模型信息:")
        for model_key, info in router_stats['models'].items():
            print(f"\n  {model_key}:")
            print(f"    提供商: {info['provider']}")
            print(f"    模型: {info['model']}")
            print(f"    平均成本: ¥{info['cost_per_1k_avg']:.4f}/1K tokens")
            print(f"    延迟: {info['latency_ms']}ms")
            print(f"    最适合: {', '.join(info['best_for'])}")


async def main():
    """主测试函数"""
    try:
        # 测试1: AI网关智能路由
        await test_ai_gateway_with_routing()
        
        # 测试2: 消息服务集成
        # await test_message_service_with_routing()
        
        # 测试3: 路由统计
        await test_routing_stats()
        
        print("\n" + "=" * 80)
        print("🎉 所有测试完成！")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
