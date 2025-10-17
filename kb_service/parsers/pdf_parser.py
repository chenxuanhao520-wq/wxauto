"""
PDF 解析器
支持：文字版PDF、扫描版PDF（OCR）
"""
import logging
from typing import Dict, Any, List
from pathlib import Path

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """
    PDF 解析器
    优先使用 PyMuPDF（快速），失败则使用 OCR
    """
    
    def __init__(self, use_ocr: bool = True):
        """
        Args:
            use_ocr: 是否启用OCR（用于扫描版PDF）
        """
        self.use_ocr = use_ocr
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析PDF文件"""
        if not self.validate_file(file_path):
            raise ValueError(f"文件不存在或格式不支持: {file_path}")
        
        # 尝试使用 PyMuPDF 提取文本
        try:
            text, metadata = self._parse_with_pymupdf(file_path)
            
            if text.strip():
                logger.info(f"PDF解析成功（PyMuPDF）: {file_path}")
                return {
                    'text': text,
                    'metadata': metadata,
                    'method': 'pymupdf'
                }
        except Exception as e:
            logger.warning(f"PyMuPDF解析失败: {e}")
        
        # 回退到OCR
        if self.use_ocr:
            try:
                text, metadata = self._parse_with_ocr(file_path)
                logger.info(f"PDF解析成功（OCR）: {file_path}")
                return {
                    'text': text,
                    'metadata': metadata,
                    'method': 'ocr'
                }
            except Exception as e:
                logger.error(f"OCR解析失败: {e}")
                raise
        
        raise ValueError(f"PDF解析失败: {file_path}")
    
    def _parse_with_pymupdf(self, file_path: str) -> tuple[str, Dict]:
        """使用 PyMuPDF 提取文本"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF未安装，请运行: pip install pymupdf")
        
        doc = fitz.open(file_path)
        
        text_parts = []
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(f"[第{page_num}页]\n{page_text}")
        
        metadata = {
            'page_count': doc.page_count,
            'title': doc.metadata.get('title', ''),
            'author': doc.metadata.get('author', ''),
            'creator': doc.metadata.get('creator', '')
        }
        
        doc.close()
        
        text = "\n\n".join(text_parts)
        return text, metadata
    
    def _parse_with_ocr(self, file_path: str) -> tuple[str, Dict]:
        """使用 OCR 提取文本（扫描版PDF）"""
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError("PaddleOCR未安装，请运行: pip install paddleocr")
        
        # 初始化 PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
        
        # 将PDF转为图片
        import fitz
        doc = fitz.open(file_path)
        
        text_parts = []
        for page_num in range(doc.page_count):
            # 渲染页面为图片
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2倍分辨率
            
            # 保存临时图片
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                pix.save(tmp.name)
                
                # OCR识别
                result = ocr.ocr(tmp.name, cls=True)
                
                # 提取文本
                page_text = []
                if result and result[0]:
                    for line in result[0]:
                        if len(line) >= 2:
                            page_text.append(line[1][0])
                
                if page_text:
                    text_parts.append(f"[第{page_num + 1}页]\n" + "\n".join(page_text))
                
                # 删除临时文件
                Path(tmp.name).unlink()
        
        doc.close()
        
        metadata = {
            'page_count': doc.page_count,
            'ocr_method': 'PaddleOCR'
        }
        
        text = "\n\n".join(text_parts)
        return text, metadata
    
    def supported_formats(self) -> List[str]:
        """支持的格式"""
        return ['.pdf']

