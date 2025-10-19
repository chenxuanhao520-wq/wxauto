#!/usr/bin/env python3
"""
带ETL流程的文档上传工具
完整的Extract-Transform-Load流程
"""
import sys
import argparse
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def upload_document_with_etl(
    file_path: str,
    document_type: str,
    auto_fix: bool = True,
    llm_enhancement: bool = False
):
    """
    使用ETL流程上传文档
    
    Args:
        file_path: 文件路径
        document_type: 文档类型（product_info, faq, operation, technical, general）
        auto_fix: 是否自动修复
        llm_enhancement: 是否使用LLM增强
    """
    print("=" * 80)
    print(f"📤 文档上传 - ETL流程处理")
    print("=" * 80)
    print(f"文件: {file_path}")
    print(f"类型: {document_type}")
    print(f"自动修复: {'启用' if auto_fix else '禁用'}")
    print(f"LLM增强: {'启用' if llm_enhancement else '禁用'}")
    print("=" * 80)
    
    try:
        # 导入必要模块
        from modules.kb_platform.etl import DocumentETLPipeline, StructureValidator, FormatNormalizer
        from modules.kb_platform.processors.document_processor import DocumentProcessor
        from modules.kb_platform.processors.content_cleaner import ContentCleaner
        from modules.kb_platform.processors.duplicate_detector import DuplicateDetector
        from modules.kb_platform.core.quality_controller import QualityController
        
        # 初始化组件
        print("\n📋 初始化ETL组件...")
        document_processor = DocumentProcessor()
        structure_validator = StructureValidator()
        format_normalizer = FormatNormalizer()
        content_cleaner = ContentCleaner()
        duplicate_detector = DuplicateDetector()
        
        # 如果启用LLM，初始化AI网关
        ai_gateway = None
        if llm_enhancement:
            try:
                from modules.ai_gateway import AIGateway
                ai_gateway = AIGateway()
                print("✅ AI网关已初始化（LLM增强启用）")
            except Exception as e:
                print(f"⚠️ AI网关初始化失败: {e}，LLM增强禁用")
                llm_enhancement = False
        
        quality_controller = QualityController(
            threshold=0.75,
            strict_mode=True,
            enable_auto_fix=auto_fix,
            enable_llm_fix=llm_enhancement,
            ai_gateway=ai_gateway
        )
        
        # 初始化ETL流水线
        etl_pipeline = DocumentETLPipeline(
            document_processor=document_processor,
            structure_validator=structure_validator,
            format_normalizer=format_normalizer,
            quality_controller=quality_controller,
            content_cleaner=content_cleaner,
            duplicate_detector=duplicate_detector
        )
        
        print("✅ ETL流水线初始化完成")
        
        # 执行ETL流程
        print("\n🔄 开始ETL处理...")
        result = await etl_pipeline.process_document(
            file_path=file_path,
            document_type=document_type,
            enable_auto_fix=auto_fix,
            enable_llm_enhancement=llm_enhancement
        )
        
        # 显示结果
        print("\n" + "=" * 80)
        if result.success:
            print("✅ 文档处理成功！")
            print("=" * 80)
            print(f"文档ID: {result.document_id}")
            print(f"文档类型: {result.document_type}")
            print(f"质量分数: {result.quality_score:.2f}")
            print(f"创建知识块: {len(result.transformed_chunks)}")
            print(f"处理时间: {result.processing_time:.2f}秒")
            
            if result.warnings:
                print(f"\n⚠️ 警告 ({len(result.warnings)}):")
                for warning in result.warnings:
                    print(f"  • {warning}")
            
            print("\n📊 验证报告:")
            if 'structure_validation' in result.validation_report:
                sv = result.validation_report['structure_validation']
                print(f"  • 结构验证: {'✅ 通过' if sv['passed'] else '❌ 失败'}")
            
            if 'quality_result' in result.validation_report:
                qr = result.validation_report['quality_result']
                print(f"  • 质量检查: {'✅ 通过' if qr['passed'] else '❌ 失败'}")
            
            if 'duplicate_result' in result.validation_report:
                dr = result.validation_report['duplicate_result']
                print(f"  • 重复检测: {'✅ 无重复' if not dr['has_duplicates'] else '❌ 有重复'}")
            
            print("\n📦 知识块示例（前3个）:")
            for i, chunk in enumerate(result.transformed_chunks[:3], 1):
                print(f"\n  知识块 {i}:")
                print(f"    ID: {chunk.get('chunk_id', '')}")
                print(f"    内容: {chunk.get('content', '')[:100]}...")
                if chunk.get('normalized'):
                    print(f"    结构化: ✅")
        
        else:
            print("❌ 文档处理失败！")
            print("=" * 80)
            print(f"文档类型: {result.document_type}")
            print(f"质量分数: {result.quality_score:.2f}")
            
            if result.errors:
                print(f"\n❌ 错误 ({len(result.errors)}):")
                for error in result.errors:
                    print(f"  • {error}")
            
            if result.warnings:
                print(f"\n⚠️ 警告 ({len(result.warnings)}):")
                for warning in result.warnings:
                    print(f"  • {warning}")
            
            print("\n💡 建议:")
            print("  1. 查看错误信息，补充缺失的必要字段")
            print("  2. 参考文档模板: docs/kb_platform/文档模板和示例.md")
            print("  3. 启用自动修复: --auto-fix")
            if not llm_enhancement:
                print("  4. 启用LLM增强: --llm-enhancement")
        
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='带ETL流程的文档上传工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 上传产品信息文档
  python scripts/upload_with_etl.py --file 产品手册.pdf --type product_info --auto-fix
  
  # 上传FAQ文档（启用LLM增强）
  python scripts/upload_with_etl.py --file FAQ.docx --type faq --auto-fix --llm-enhancement
  
  # 上传操作文档
  python scripts/upload_with_etl.py --file 安装指南.pdf --type operation --auto-fix

文档类型:
  product_info - 产品信息文档
  faq          - FAQ常见问题
  operation    - 操作指南文档
  technical    - 技术文档
  general      - 通用文档
        """
    )
    
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='文档文件路径'
    )
    
    parser.add_argument(
        '--type', '-t',
        required=True,
        choices=['product_info', 'faq', 'operation', 'technical', 'general'],
        help='文档类型'
    )
    
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='启用自动修复（规则+LLM）'
    )
    
    parser.add_argument(
        '--llm-enhancement',
        action='store_true',
        help='启用LLM增强（需要AI网关配置）'
    )
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not Path(args.file).exists():
        print(f"❌ 文件不存在: {args.file}")
        sys.exit(1)
    
    # 运行ETL流程
    asyncio.run(upload_document_with_etl(
        file_path=args.file,
        document_type=args.type,
        auto_fix=args.auto_fix,
        llm_enhancement=args.llm_enhancement
    ))


if __name__ == "__main__":
    main()
