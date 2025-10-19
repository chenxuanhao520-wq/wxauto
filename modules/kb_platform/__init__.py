"""
KB中台 - 知识库强治理平台
保证知识库数据质量，确保进入知识库的资料都是高质量、清洗过且符合大模型检索的
"""
from .core.kb_platform import KBPlatform
from .core.data_governance import DataGovernance
from .core.quality_controller import QualityController
from .processors.document_processor import DocumentProcessor
from .processors.content_cleaner import ContentCleaner
from .processors.duplicate_detector import DuplicateDetector
from .processors.llm_optimizer import LLMOptimizer
from .validators.structure_validator import StructureValidator
from .validators.quality_validator import QualityValidator
from .storage.kb_storage import KBStorage
from .api.kb_api import KBAPI

__all__ = [
    'KBPlatform',
    'DataGovernance', 
    'QualityController',
    'DocumentProcessor',
    'ContentCleaner',
    'DuplicateDetector',
    'LLMOptimizer',
    'StructureValidator',
    'QualityValidator',
    'KBStorage',
    'KBAPI'
]

__version__ = '1.0.0'
