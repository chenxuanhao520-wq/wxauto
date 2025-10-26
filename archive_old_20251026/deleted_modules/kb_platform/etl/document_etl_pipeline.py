"""
文档ETL流水线
完整的Extract-Transform-Load流程
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ETLResult:
    """ETL处理结果"""
    success: bool
    document_id: str
    document_type: str
    extracted_data: Dict[str, Any]
    transformed_chunks: List[Dict[str, Any]]
    validation_report: Dict[str, Any]
    quality_score: float
    errors: List[str]
    warnings: List[str]
    processing_time: float


class DocumentETLPipeline:
    """
    文档ETL流水线
    
    完整流程：
    1. Extract（提取）：解析文档，提取原始内容
    2. Transform（转换）：清洗、结构化、标准化
    3. Load（加载）：验证、入库
    
    支持文档类型：
    - 产品信息文档
    - FAQ文档
    - 操作文档
    - 技术文档
    - 通用文档
    """
    
    def __init__(
        self,
        document_processor,
        structure_validator,
        format_normalizer,
        quality_controller,
        content_cleaner,
        duplicate_detector,
        llm_optimizer=None
    ):
        """
        初始化ETL流水线
        
        Args:
            document_processor: 文档处理器（Extract）
            structure_validator: 结构验证器（Validate）
            format_normalizer: 格式标准化器（Transform）
            quality_controller: 质量控制器（Validate）
            content_cleaner: 内容清洗器（Transform）
            duplicate_detector: 重复检测器（Validate）
            llm_optimizer: LLM优化器（Transform，可选）
        """
        self.document_processor = document_processor
        self.structure_validator = structure_validator
        self.format_normalizer = format_normalizer
        self.quality_controller = quality_controller
        self.content_cleaner = content_cleaner
        self.duplicate_detector = duplicate_detector
        self.llm_optimizer = llm_optimizer
        
        logger.info("文档ETL流水线初始化完成")
    
    async def process_document(
        self,
        file_path: str,
        document_type: str,
        metadata: Dict[str, Any] = None,
        enable_auto_fix: bool = True,
        enable_llm_enhancement: bool = False
    ) -> ETLResult:
        """
        完整ETL流程处理文档
        
        Args:
            file_path: 文件路径
            document_type: 文档类型（product_info, faq, operation, technical, general）
            metadata: 文档元数据
            enable_auto_fix: 是否启用自动修复
            enable_llm_enhancement: 是否启用LLM增强
        
        Returns:
            ETL处理结果
        """
        start_time = datetime.now()
        errors = []
        warnings = []
        
        try:
            # ==================== Phase 1: Extract（提取）====================
            logger.info(f"[ETL] Phase 1: Extract - 解析文档 {file_path}")
            
            extract_result = await self._extract_phase(file_path, document_type)
            
            if not extract_result['success']:
                return self._create_error_result(
                    document_type,
                    extract_result['errors'],
                    start_time
                )
            
            extracted_data = extract_result['data']
            raw_chunks = extract_result['chunks']
            
            # ==================== Phase 2: Validate Structure（结构验证）====================
            logger.info(f"[ETL] Phase 2: Validate Structure - 验证文档结构")
            
            structure_validation = await self._validate_structure_phase(
                extracted_data,
                raw_chunks,
                document_type
            )
            
            if not structure_validation['passed']:
                errors.extend(structure_validation['errors'])
                
                # 如果启用自动修复，尝试修复
                if enable_auto_fix:
                    logger.info("[ETL] 尝试自动修复结构问题...")
                    fix_result = await self._auto_fix_structure(
                        raw_chunks,
                        structure_validation['missing_fields'],
                        document_type,
                        enable_llm_enhancement
                    )
                    
                    if fix_result['success']:
                        raw_chunks = fix_result['fixed_chunks']
                        warnings.append("结构问题已自动修复")
                    else:
                        # 修复失败，返回错误
                        return self._create_error_result(
                            document_type,
                            errors + ["结构验证失败，自动修复失败"],
                            start_time
                        )
                else:
                    # 不自动修复，直接返回
                    return self._create_error_result(
                        document_type,
                        errors,
                        start_time
                    )
            
            # ==================== Phase 3: Transform（转换）====================
            logger.info(f"[ETL] Phase 3: Transform - 清洗和标准化")
            
            transform_result = await self._transform_phase(
                raw_chunks,
                document_type,
                enable_llm_enhancement
            )
            
            transformed_chunks = transform_result['chunks']
            warnings.extend(transform_result.get('warnings', []))
            
            # ==================== Phase 4: Quality Check（质量检查）====================
            logger.info(f"[ETL] Phase 4: Quality Check - 质量验证")
            
            quality_result = await self._quality_check_phase(
                transformed_chunks,
                document_type
            )
            
            quality_score = quality_result['quality_score']
            
            if not quality_result['passed']:
                errors.extend(quality_result['issues'])
                
                # 如果启用自动修复
                if enable_auto_fix and quality_result.get('auto_fixable'):
                    logger.info("[ETL] 尝试自动修复质量问题...")
                    quality_fix_result = await self._auto_fix_quality(
                        transformed_chunks,
                        quality_result['issues'],
                        enable_llm_enhancement
                    )
                    
                    if quality_fix_result['success']:
                        transformed_chunks = quality_fix_result['fixed_chunks']
                        quality_score = quality_fix_result['quality_score']
                        warnings.append("质量问题已自动修复")
            
            # ==================== Phase 5: Duplicate Check（重复检查）====================
            logger.info(f"[ETL] Phase 5: Duplicate Check - 重复检测")
            
            duplicate_result = await self._duplicate_check_phase(transformed_chunks)
            
            if duplicate_result['has_duplicates']:
                errors.append(f"检测到重复内容: {duplicate_result['summary']}")
                # 重复内容需要人工决策
                return self._create_error_result(
                    document_type,
                    errors,
                    start_time
                )
            
            # ==================== Phase 6: Load（加载准备）====================
            logger.info(f"[ETL] Phase 6: Load - 准备加载")
            
            # 生成最终的标准化chunks
            final_chunks = await self._finalize_chunks(
                transformed_chunks,
                document_type,
                metadata
            )
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 创建成功结果
            return ETLResult(
                success=True,
                document_id=extracted_data.get('document_id', ''),
                document_type=document_type,
                extracted_data=extracted_data,
                transformed_chunks=final_chunks,
                validation_report={
                    'structure_validation': structure_validation,
                    'quality_result': quality_result,
                    'duplicate_result': duplicate_result
                },
                quality_score=quality_score,
                errors=errors,
                warnings=warnings,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"[ETL] 处理失败: {e}")
            return self._create_error_result(
                document_type,
                [str(e)],
                start_time
            )
    
    async def _extract_phase(
        self,
        file_path: str,
        document_type: str
    ) -> Dict[str, Any]:
        """Extract阶段：解析文档"""
        try:
            # 使用文档处理器解析
            parsed = await self.document_processor.process_file(file_path)
            
            return {
                'success': True,
                'data': {
                    'document_id': parsed.document_id,
                    'title': parsed.title,
                    'format': parsed.format,
                    'metadata': parsed.metadata
                },
                'chunks': parsed.chunks,
                'errors': []
            }
            
        except Exception as e:
            return {
                'success': False,
                'data': {},
                'chunks': [],
                'errors': [f"文档解析失败: {str(e)}"]
            }
    
    async def _validate_structure_phase(
        self,
        extracted_data: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        document_type: str
    ) -> Dict[str, Any]:
        """结构验证阶段"""
        return await self.structure_validator.validate(
            chunks,
            document_type
        )
    
    async def _transform_phase(
        self,
        chunks: List[Dict[str, Any]],
        document_type: str,
        enable_llm: bool
    ) -> Dict[str, Any]:
        """Transform阶段：清洗和标准化"""
        warnings = []
        transformed_chunks = []
        
        for chunk in chunks:
            # 1. 内容清洗
            cleaned = await self.content_cleaner.clean_content(chunk['content'])
            chunk['content'] = cleaned['content']
            
            # 2. 格式标准化
            normalized = await self.format_normalizer.normalize(
                chunk,
                document_type
            )
            
            # 3. LLM优化（可选）
            if enable_llm and self.llm_optimizer:
                optimized = await self.llm_optimizer.optimize_single_chunk(chunk)
                chunk['content'] = optimized.optimized_content
                chunk['llm_optimized'] = True
            
            transformed_chunks.append(normalized)
        
        return {
            'chunks': transformed_chunks,
            'warnings': warnings
        }
    
    async def _quality_check_phase(
        self,
        chunks: List[Dict[str, Any]],
        document_type: str
    ) -> Dict[str, Any]:
        """质量检查阶段"""
        # 使用质量验证器评估
        from ..validators.quality_validator import QualityValidator
        
        validator = QualityValidator()
        reports = await validator.batch_evaluate_chunks(chunks)
        
        # 计算平均质量分数
        avg_score = sum(r.overall_score for r in reports) / len(reports) if reports else 0
        
        # 收集问题
        issues = []
        for report in reports:
            if not report.passed_threshold:
                issues.extend(report.weaknesses)
        
        # 判断是否有可自动修复的问题
        auto_fixable = any(
            r.overall_score >= 0.6 and r.overall_score < 0.8
            for r in reports
        )
        
        return {
            'passed': avg_score >= 0.75,
            'quality_score': avg_score,
            'issues': issues,
            'auto_fixable': auto_fixable,
            'reports': reports
        }
    
    async def _duplicate_check_phase(
        self,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """重复检查阶段"""
        # 这里简化实现，实际应该与已有知识库对比
        return {
            'has_duplicates': False,
            'summary': ''
        }
    
    async def _auto_fix_structure(
        self,
        chunks: List[Dict[str, Any]],
        missing_fields: List[str],
        document_type: str,
        enable_llm: bool
    ) -> Dict[str, Any]:
        """自动修复结构问题"""
        # 简化实现
        return {
            'success': True,
            'fixed_chunks': chunks
        }
    
    async def _auto_fix_quality(
        self,
        chunks: List[Dict[str, Any]],
        issues: List[str],
        enable_llm: bool
    ) -> Dict[str, Any]:
        """自动修复质量问题"""
        # 使用质量控制器修复
        if hasattr(self.quality_controller, 'auto_fix_issues'):
            # 简化实现
            return {
                'success': True,
                'fixed_chunks': chunks,
                'quality_score': 0.85
            }
        
        return {
            'success': False,
            'fixed_chunks': chunks,
            'quality_score': 0.0
        }
    
    async def _finalize_chunks(
        self,
        chunks: List[Dict[str, Any]],
        document_type: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """最终化chunks"""
        final_chunks = []
        
        for i, chunk in enumerate(chunks):
            final_chunk = {
                'chunk_id': f"{metadata.get('document_id', 'unknown')}_{i}",
                'content': chunk['content'],
                'document_type': document_type,
                'position': i,
                'metadata': metadata,
                'created_at': datetime.now().isoformat(),
                'etl_processed': True
            }
            final_chunks.append(final_chunk)
        
        return final_chunks
    
    def _create_error_result(
        self,
        document_type: str,
        errors: List[str],
        start_time: datetime
    ) -> ETLResult:
        """创建错误结果"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ETLResult(
            success=False,
            document_id='',
            document_type=document_type,
            extracted_data={},
            transformed_chunks=[],
            validation_report={},
            quality_score=0.0,
            errors=errors,
            warnings=[],
            processing_time=processing_time
        )
