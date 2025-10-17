"""
文档解析器基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path


class BaseParser(ABC):
    """文档解析器基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析文档
        
        Args:
            file_path: 文件路径
        
        Returns:
            {
                'text': str,           # 提取的文本
                'metadata': dict,      # 元数据
                'sections': list       # 章节信息（可选）
            }
        """
        pass
    
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """返回支持的文件格式"""
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """验证文件是否存在且格式支持"""
        path = Path(file_path)
        
        if not path.exists():
            return False
        
        suffix = path.suffix.lower()
        return suffix in self.supported_formats()

