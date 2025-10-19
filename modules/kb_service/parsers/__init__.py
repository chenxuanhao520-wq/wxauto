"""
文档解析器模块
"""
from .base_parser import BaseParser
from .pdf_parser import PDFParser
from .doc_parser import DocParser
from .image_parser import ImageParser

__all__ = ['BaseParser', 'PDFParser', 'DocParser', 'ImageParser']

