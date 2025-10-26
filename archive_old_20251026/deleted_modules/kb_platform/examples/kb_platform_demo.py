#!/usr/bin/env python3
"""
KB中台演示程序
展示强治理知识库平台的完整功能
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.kb_platform import KBPlatform

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_kb_platform():
    """演示KB中台功能"""
    print("=" * 80)
    print("🏗️ KB中台 - 强治理知识库平台演示")
    print("=" * 80)
    
    # 1. 初始化KB中台
    print("\n📋 1. 初始化KB中台...")
    kb_platform = KBPlatform(
        db_path="data/kb_platform_demo.db",
        quality_threshold=0.75,
        enable_llm_optimization=True,
        enable_duplicate_detection=True
    )
    print("✅ KB中台初始化完成")
    
    # 2. 演示文档上传（模拟）
    print("\n📄 2. 演示文档上传和强治理流程...")
    
    # 模拟高质量文档
    high_quality_content = """
    充电桩安装指南
    
    安装前准备：
    1. 确认电源符合220V±10%要求
    2. 环境温度控制在0-40℃范围内
    3. 确保通风良好，无尘环境
    
    安装步骤：
    1. 关闭主电源开关
    2. 使用M6螺丝固定底座
    3. 连接电源线到配电箱
    4. 通电测试设备运行状态
    
    注意事项：
    - 禁止带电操作
    - 安装完成后进行功能测试
    - 如有异常立即断电并联系售后
    """
    
    # 模拟低质量文档
    low_quality_content = """
    嗯，那个，充电桩怎么装呢，就是...很简单的，大概就是插上电就行了，
    然后那个...应该就能用了吧，嗯...就是这样，很简单很简单的。
    """
    
    # 模拟重复文档
    duplicate_content = """
    充电桩安装指南
    
    安装前准备：
    1. 确认电源符合220V±10%要求
    2. 环境温度控制在0-40℃范围内
    3. 确保通风良好，无尘环境
    """
    
    # 上传高质量文档
    print("\n📤 上传高质量文档...")
    result1 = await kb_platform.upload_document(
        file_path="demo_high_quality.txt",
        title="充电桩安装指南",
        category="技术文档",
        tags=["充电桩", "安装", "指南"]
    )
    print(f"✅ 高质量文档处理结果: {result1}")
    
    # 上传低质量文档
    print("\n📤 上传低质量文档...")
    result2 = await kb_platform.upload_document(
        file_path="demo_low_quality.txt",
        title="充电桩安装说明",
        category="技术文档"
    )
    print(f"⚠️ 低质量文档处理结果: {result2}")
    
    # 上传重复文档
    print("\n📤 上传重复文档...")
    result3 = await kb_platform.upload_document(
        file_path="demo_duplicate.txt",
        title="充电桩安装指南（重复）",
        category="技术文档"
    )
    print(f"❌ 重复文档处理结果: {result3}")
    
    # 3. 演示质量报告
    print("\n📊 3. 生成质量报告...")
    quality_report = await kb_platform.get_quality_report()
    print(f"📈 质量报告: {quality_report}")
    
    # 4. 演示知识库统计
    print("\n📈 4. 获取知识库统计...")
    stats = await kb_platform.get_knowledge_stats()
    print(f"📊 统计信息: {stats}")
    
    # 5. 演示搜索功能
    print("\n🔍 5. 演示知识库搜索...")
    search_results = await kb_platform.search_knowledge(
        query="充电桩安装步骤",
        top_k=3,
        min_quality=0.7
    )
    print(f"🔎 搜索结果: {search_results}")
    
    # 6. 演示清理功能
    print("\n🧹 6. 演示低质量数据清理...")
    cleanup_result = await kb_platform.cleanup_low_quality_data(threshold=0.6)
    print(f"🗑️ 清理结果: {cleanup_result}")
    
    print("\n" + "=" * 80)
    print("🎉 KB中台演示完成！")
    print("=" * 80)


async def demo_quality_control():
    """演示质量控制功能"""
    print("\n" + "=" * 60)
    print("🎯 质量控制演示")
    print("=" * 60)
    
    from modules.kb_platform.validators.quality_validator import QualityValidator
    from modules.kb_platform.processors.content_cleaner import ContentCleaner
    from modules.kb_platform.processors.duplicate_detector import DuplicateDetector
    
    # 初始化组件
    quality_validator = QualityValidator(min_score_threshold=0.75)
    content_cleaner = ContentCleaner()
    duplicate_detector = DuplicateDetector()
    
    # 测试内容
    test_contents = [
        {
            'content': '充电桩安装步骤：1.关闭电源 2.固定底座 3.连接线路 4.通电测试',
            'chunk_id': 'test_1'
        },
        {
            'content': '嗯，那个，就是...充电桩怎么装呢，大概就是插上电就行了吧',
            'chunk_id': 'test_2'
        },
        {
            'content': '充电桩安装步骤：1.关闭电源 2.固定底座 3.连接线路 4.通电测试',
            'chunk_id': 'test_3'
        }
    ]
    
    # 1. 内容清洗演示
    print("\n🧹 内容清洗演示...")
    for i, test_content in enumerate(test_contents):
        cleaning_result = await content_cleaner.clean_content(test_content['content'])
        print(f"内容 {i+1}: {test_content['content'][:30]}...")
        print(f"清洗后: {cleaning_result['content'][:30]}...")
        print(f"质量提升: {cleaning_result['quality_score']:.2f}")
        print()
    
    # 2. 质量验证演示
    print("\n📊 质量验证演示...")
    quality_reports = await quality_validator.batch_evaluate_chunks(test_contents)
    for report in quality_reports:
        print(f"知识块 {report.chunk_id}:")
        print(f"  综合分数: {report.overall_score:.2f}")
        print(f"  通过阈值: {'✅' if report.passed_threshold else '❌'}")
        print(f"  优势: {', '.join(report.strengths) if report.strengths else '无'}")
        print(f"  劣势: {', '.join(report.weaknesses) if report.weaknesses else '无'}")
        print()
    
    # 3. 重复检测演示
    print("\n🔍 重复检测演示...")
    duplicate_result = await duplicate_detector.detect_duplicates(test_contents)
    print(f"发现重复: {'是' if duplicate_result.has_duplicates else '否'}")
    print(f"重复数量: {duplicate_result.total_duplicates}")
    print(f"重复组: {duplicate_result.duplicate_groups}")
    print(f"摘要: {duplicate_result.summary}")


async def demo_integration_with_existing_system():
    """演示与现有系统的集成"""
    print("\n" + "=" * 60)
    print("🔗 与现有系统集成演示")
    print("=" * 60)
    
    # 这里展示如何将KB中台集成到现有的RAG系统中
    print("\n📋 集成方案:")
    print("1. 替换现有的 document_processor.py")
    print("2. 在消息处理流程中添加质量控制")
    print("3. 使用KB中台的强治理能力")
    print("4. 保持与现有RAG检索器的兼容性")
    
    print("\n🔄 集成后的处理流程:")
    print("文档上传 → KB中台强治理 → 高质量知识库 → RAG检索 → AI回复")
    
    print("\nGeneration of integration code:")
    integration_code = '''
# 在 server/services/message_service.py 中集成KB中台

from modules.kb_platform import KBPlatform

class MessageService:
    def __init__(self):
        # 初始化KB中台
        self.kb_platform = KBPlatform(
            db_path="data/kb_platform.db",
            quality_threshold=0.75,
            enable_llm_optimization=True,
            enable_duplicate_detection=True
        )
    
    async def process_message(self, message):
        # 原有的消息处理逻辑...
        
        # 如果需要添加新知识到知识库
        if self.should_add_to_knowledge_base(message):
            result = await self.kb_platform.upload_document(
                file_path=message.content,
                title=message.title,
                category=message.category
            )
            
            if not result['success']:
                logger.warning(f"知识库添加失败: {result['errors']}")
        
        # 继续原有流程...
    '''
    
    print(integration_code)


async def main():
    """主函数"""
    try:
        # 演示KB中台核心功能
        await demo_kb_platform()
        
        # 演示质量控制功能
        await demo_quality_control()
        
        # 演示系统集成
        await demo_integration_with_existing_system()
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
