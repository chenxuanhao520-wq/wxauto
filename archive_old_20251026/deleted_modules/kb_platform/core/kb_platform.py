"""
KB中台核心平台
统一管理知识库的强治理流程
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from .data_governance import DataGovernance
from .quality_controller import QualityController
from ..processors.document_processor import DocumentProcessor
from ..processors.content_cleaner import ContentCleaner
from ..processors.duplicate_detector import DuplicateDetector
from ..processors.llm_optimizer import LLMOptimizer
from ..validators.structure_validator import StructureValidator
from ..validators.quality_validator import QualityValidator
from ..storage.kb_storage import KBStorage

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """文档元数据"""
    document_id: str
    title: str
    version: str
    source_type: str  # pdf, doc, web, manual
    upload_time: datetime
    file_size: int
    language: str = "zh-CN"
    category: str = "general"
    tags: List[str] = None
    quality_score: float = 0.0
    processing_status: str = "pending"  # pending, processing, completed, failed
    error_message: str = None


@dataclass
class ChunkMetadata:
    """知识块元数据"""
    chunk_id: str
    document_id: str
    section: str
    content: str
    cleaned_content: str
    keywords: List[str]
    entities: List[str]
    quality_score: float
    llm_optimized: bool
    duplicate_check_passed: bool
    created_at: datetime
    updated_at: datetime


class KBPlatform:
    """
    KB中台核心平台
    
    功能：
    1. 统一入口管理所有知识库操作
    2. 强制执行数据质量治理
    3. 提供完整的文档处理流水线
    4. 确保数据符合大模型检索要求
    """
    
    def __init__(
        self,
        db_path: str = "data/kb_platform.db",
        quality_threshold: float = 0.75,
        enable_llm_optimization: bool = True,
        enable_duplicate_detection: bool = True
    ):
        """
        初始化KB中台
        
        Args:
            db_path: 数据库路径
            quality_threshold: 质量阈值（低于此值的数据将被拒绝）
            enable_llm_optimization: 是否启用LLM优化
            enable_duplicate_detection: 是否启用重复检测
        """
        self.db_path = db_path
        self.quality_threshold = quality_threshold
        
        # 初始化核心组件
        self.data_governance = DataGovernance()
        self.quality_controller = QualityController(threshold=quality_threshold)
        self.storage = KBStorage(db_path)
        
        # 初始化处理器
        self.document_processor = DocumentProcessor()
        self.content_cleaner = ContentCleaner()
        self.duplicate_detector = DuplicateDetector() if enable_duplicate_detection else None
        self.llm_optimizer = LLMOptimizer() if enable_llm_optimization else None
        
        # 初始化验证器
        self.structure_validator = StructureValidator()
        self.quality_validator = QualityValidator()
        
        logger.info(f"KB中台初始化完成: threshold={quality_threshold}")
    
    async def upload_document(
        self,
        file_path: str,
        title: Optional[str] = None,
        category: str = "general",
        tags: List[str] = None,
        force_override: bool = False
    ) -> Dict[str, Any]:
        """
        上传文档到知识库（强治理流程）
        
        Args:
            file_path: 文件路径
            title: 文档标题（可选）
            category: 文档分类
            tags: 标签列表
            force_override: 是否强制覆盖（跳过重复检测）
        
        Returns:
            {
                'success': bool,
                'document_id': str,
                'chunks_created': int,
                'quality_score': float,
                'warnings': List[str],
                'errors': List[str]
            }
        """
        logger.info(f"开始处理文档: {file_path}")
        
        try:
            # 1. 创建文档元数据
            document_metadata = await self._create_document_metadata(
                file_path, title, category, tags
            )
            
            # 2. 文档结构验证
            structure_result = await self.structure_validator.validate_file(file_path)
            if not structure_result['valid']:
                return {
                    'success': False,
                    'document_id': None,
                    'chunks_created': 0,
                    'quality_score': 0.0,
                    'warnings': [],
                    'errors': structure_result['errors']
                }
            
            # 3. 文档解析
            parsed_result = await self.document_processor.process_file(file_path)
            if not parsed_result['success']:
                return {
                    'success': False,
                    'document_id': document_metadata.document_id,
                    'chunks_created': 0,
                    'quality_score': 0.0,
                    'warnings': [],
                    'errors': parsed_result['errors']
                }
            
            # 4. 内容清洗
            cleaned_chunks = []
            for chunk in parsed_result['chunks']:
                cleaned = await self.content_cleaner.clean_content(chunk['content'])
                chunk['cleaned_content'] = cleaned['content']
                chunk['cleaning_info'] = cleaned['info']
                cleaned_chunks.append(chunk)
            
            # 5. 重复检测（如果启用）
            if self.duplicate_detector and not force_override:
                duplicate_result = await self._check_duplicates(cleaned_chunks)
                if duplicate_result['has_duplicates']:
                    return {
                        'success': False,
                        'document_id': document_metadata.document_id,
                        'chunks_created': 0,
                        'quality_score': 0.0,
                        'warnings': [],
                        'errors': [f"检测到重复内容: {duplicate_result['duplicate_summary']}"]
                    }
            
            # 6. 质量评估
            quality_results = []
            for chunk in cleaned_chunks:
                quality_score = await self.quality_validator.evaluate_chunk(chunk)
                chunk['quality_score'] = quality_score
                quality_results.append(quality_score)
            
            # 7. 质量过滤
            high_quality_chunks = [
                chunk for chunk in cleaned_chunks 
                if chunk['quality_score'] >= self.quality_threshold
            ]
            
            low_quality_count = len(cleaned_chunks) - len(high_quality_chunks)
            
            # 8. LLM优化（如果启用）
            if self.llm_optimizer and high_quality_chunks:
                optimized_chunks = await self.llm_optimizer.optimize_chunks(high_quality_chunks)
                high_quality_chunks = optimized_chunks
            
            # 9. 存储到知识库
            await self.storage.store_document(document_metadata, high_quality_chunks)
            
            # 10. 更新统计信息
            await self.data_governance.record_upload_stats(
                document_id=document_metadata.document_id,
                total_chunks=len(cleaned_chunks),
                accepted_chunks=len(high_quality_chunks),
                avg_quality=sum(quality_results) / len(quality_results) if quality_results else 0.0
            )
            
            logger.info(
                f"文档处理完成: {document_metadata.document_id}, "
                f"接受 {len(high_quality_chunks)}/{len(cleaned_chunks)} 个知识块"
            )
            
            return {
                'success': True,
                'document_id': document_metadata.document_id,
                'chunks_created': len(high_quality_chunks),
                'quality_score': sum(quality_results) / len(quality_results) if quality_results else 0.0,
                'warnings': [
                    f"过滤了 {low_quality_count} 个低质量知识块" if low_quality_count > 0 else None,
                    f"平均质量分: {sum(quality_results) / len(quality_results):.2f}" if quality_results else None
                ],
                'errors': []
            }
            
        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            return {
                'success': False,
                'document_id': None,
                'chunks_created': 0,
                'quality_score': 0.0,
                'warnings': [],
                'errors': [str(e)]
            }
    
    async def search_knowledge(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        min_quality: float = None
    ) -> Dict[str, Any]:
        """
        搜索知识库
        
        Args:
            query: 搜索查询
            filters: 过滤条件
            top_k: 返回数量
            min_quality: 最低质量要求
        
        Returns:
            {
                'results': List[ChunkMetadata],
                'total_found': int,
                'search_time': float
            }
        """
        min_quality = min_quality or self.quality_threshold
        
        results = await self.storage.search_chunks(
            query=query,
            filters=filters,
            top_k=top_k,
            min_quality=min_quality
        )
        
        return results
    
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return await self.data_governance.get_knowledge_stats()
    
    async def get_quality_report(self) -> Dict[str, Any]:
        """获取质量报告"""
        return await self.quality_controller.generate_quality_report()
    
    async def cleanup_low_quality_data(self, threshold: float = None) -> Dict[str, Any]:
        """
        清理低质量数据
        
        Args:
            threshold: 质量阈值，低于此值的数据将被清理
        
        Returns:
            清理统计信息
        """
        threshold = threshold or self.quality_threshold
        
        cleanup_result = await self.storage.cleanup_low_quality_chunks(threshold)
        
        logger.info(f"清理完成: 删除了 {cleanup_result['deleted_count']} 个低质量知识块")
        
        return cleanup_result
    
    # ==================== 私有方法 ====================
    
    async def _create_document_metadata(
        self,
        file_path: str,
        title: Optional[str],
        category: str,
        tags: List[str]
    ) -> DocumentMetadata:
        """创建文档元数据"""
        from pathlib import Path
        import hashlib
        
        path = Path(file_path)
        
        # 生成文档ID
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        document_id = f"doc_{file_hash[:12]}"
        
        return DocumentMetadata(
            document_id=document_id,
            title=title or path.stem,
            version="v1.0",
            source_type=path.suffix.lower().lstrip('.'),
            upload_time=datetime.now(),
            file_size=path.stat().st_size,
            category=category,
            tags=tags or [],
            processing_status="pending"
        )
    
    async def _check_duplicates(self, chunks: List[Dict]) -> Dict[str, Any]:
        """检查重复内容"""
        if not self.duplicate_detector:
            return {'has_duplicates': False, 'duplicate_summary': ''}
        
        duplicate_result = await self.duplicate_detector.detect_duplicates(chunks)
        
        return {
            'has_duplicates': duplicate_result['has_duplicates'],
            'duplicate_summary': duplicate_result.get('summary', '')
        }
