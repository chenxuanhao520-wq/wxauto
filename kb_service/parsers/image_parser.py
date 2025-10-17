"""
图片解析器（OCR）
"""
import logging
from typing import Dict, Any, List

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class ImageParser(BaseParser):
    """图片OCR解析器"""
    
    def __init__(self, lang: str = 'ch'):
        """
        Args:
            lang: 语言（ch=中文, en=英文）
        """
        self.lang = lang
        self._ocr = None
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析图片文件"""
        if not self.validate_file(file_path):
            raise ValueError(f"文件不存在或格式不支持: {file_path}")
        
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError("PaddleOCR未安装，请运行: pip install paddleocr")
        
        # 初始化OCR（懒加载）
        if self._ocr is None:
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                show_log=False
            )
        
        # OCR识别
        result = self._ocr.ocr(file_path, cls=True)
        
        # 提取文本
        text_lines = []
        if result and result[0]:
            for line in result[0]:
                if len(line) >= 2:
                    text = line[1][0]
                    confidence = line[1][1]
                    
                    # 只保留置信度>0.5的文本
                    if confidence > 0.5:
                        text_lines.append(text)
        
        text = "\n".join(text_lines)
        
        metadata = {
            'ocr_method': 'PaddleOCR',
            'lang': self.lang,
            'lines_count': len(text_lines)
        }
        
        logger.info(f"图片解析成功: {file_path}, {len(text)}字符")
        
        return {
            'text': text,
            'metadata': metadata
        }
    
    def supported_formats(self) -> List[str]:
        """支持的格式"""
        return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

