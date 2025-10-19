"""
文档处理中心
统一处理多种格式的文档，提取文本并分段
"""
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from .parsers import PDFParser, DocParser, ImageParser

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    文档处理中心
    
    功能：
    1. 支持多种格式（PDF、DOC、DOCX、图片）
    2. 自动提取文本
    3. 智能分段
    4. 生成元数据
    """
    
    def __init__(self, use_ocr: bool = True):
        """
        初始化文档处理器
        
        Args:
            use_ocr: 是否启用OCR（用于扫描版PDF和图片）
        """
        self.use_ocr = use_ocr
        
        # 初始化各种解析器
        self.parsers = {
            'pdf': PDFParser(use_ocr=use_ocr),
            'doc': DocParser(),
            'image': ImageParser(lang='ch')
        }
        
        logger.info("文档处理器初始化完成")
    
    def process_file(
        self,
        file_path: str,
        document_name: Optional[str] = None,
        document_version: str = "v1.0",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> Dict[str, Any]:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            document_name: 文档名称（可选，默认使用文件名）
            document_version: 文档版本
            chunk_size: 分段大小（字符数）
            chunk_overlap: 分段重叠（字符数）
        
        Returns:
            {
                'document_name': str,
                'document_version': str,
                'chunks': List[Dict],  # 分段列表
                'metadata': Dict       # 文档元数据
            }
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 确定文档名称
        if not document_name:
            document_name = path.stem
        
        # 根据文件格式选择解析器
        parser = self._get_parser(path.suffix.lower())
        if not parser:
            raise ValueError(f"不支持的文件格式: {path.suffix}")
        
        # 解析文档
        logger.info(f"开始处理文档: {file_path}")
        parsed = parser.parse(file_path)
        
        text = parsed['text']
        metadata = parsed.get('metadata', {})
        
        # 智能分段
        chunks = self._split_into_chunks(
            text=text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            document_name=document_name,
            document_version=document_version
        )
        
        logger.info(
            f"文档处理完成: {document_name}, "
            f"{len(text)}字符 → {len(chunks)}个分段"
        )
        
        return {
            'document_name': document_name,
            'document_version': document_version,
            'chunks': chunks,
            'metadata': metadata,
            'total_chars': len(text)
        }
    
    def _get_parser(self, file_extension: str):
        """根据文件扩展名获取解析器"""
        if file_extension == '.pdf':
            return self.parsers['pdf']
        elif file_extension in ['.doc', '.docx']:
            return self.parsers['doc']
        elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
            return self.parsers['image']
        else:
            return None
    
    def _split_into_chunks(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        document_name: str,
        document_version: str
    ) -> List[Dict[str, Any]]:
        """
        智能分段
        
        策略：
        1. 优先按章节分段
        2. 长段落按字数分段
        3. 保留上下文重叠
        """
        # 先按段落分割
        paragraphs = self._split_by_paragraphs(text)
        
        chunks = []
        current_chunk = ""
        current_section = "正文"
        chunk_id = 0
        
        for para in paragraphs:
            # 检查是否是章节标题
            section_title = self._extract_section_title(para)
            if section_title:
                # 保存当前chunk
                if current_chunk.strip():
                    chunks.append(self._create_chunk(
                        chunk_id=f"{document_name}_{document_version}_{chunk_id}",
                        document_name=document_name,
                        document_version=document_version,
                        section=current_section,
                        content=current_chunk.strip()
                    ))
                    chunk_id += 1
                
                current_section = section_title
                current_chunk = ""
                continue
            
            # 累积段落
            if len(current_chunk) + len(para) > chunk_size:
                # 当前chunk已满，保存
                if current_chunk.strip():
                    chunks.append(self._create_chunk(
                        chunk_id=f"{document_name}_{document_version}_{chunk_id}",
                        document_name=document_name,
                        document_version=document_version,
                        section=current_section,
                        content=current_chunk.strip()
                    ))
                    chunk_id += 1
                
                # 开始新chunk（保留重叠）
                if chunk_overlap > 0:
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + para
                else:
                    current_chunk = para
            else:
                current_chunk += para + "\n"
        
        # 保存最后一个chunk
        if current_chunk.strip():
            chunks.append(self._create_chunk(
                chunk_id=f"{document_name}_{document_version}_{chunk_id}",
                document_name=document_name,
                document_version=document_version,
                section=current_section,
                content=current_chunk.strip()
            ))
        
        return chunks
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        # 按双换行或多个换行分割
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _extract_section_title(self, text: str) -> Optional[str]:
        """提取章节标题"""
        # 匹配常见的标题格式
        patterns = [
            r'^#+\s+(.+)$',  # Markdown: ## 标题
            r'^\[第.+章\](.+)$',  # [第1章] 标题
            r'^第.+[章节]\s*[：:]\s*(.+)$',  # 第1章：标题
            r'^\d+\.?\s+(.+)$',  # 1. 标题 或 1 标题
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text.strip())
            if match:
                return match.group(1).strip()
        
        return None
    
    def _create_chunk(
        self,
        chunk_id: str,
        document_name: str,
        document_version: str,
        section: str,
        content: str
    ) -> Dict[str, Any]:
        """创建分段对象"""
        # 提取关键词（简单实现）
        keywords = self._extract_keywords(content)
        
        return {
            'chunk_id': chunk_id,
            'document_name': document_name,
            'document_version': document_version,
            'section': section,
            'content': content,
            'keywords': keywords,
            'char_count': len(content)
        }
    
    def _extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """
        提取关键词（简化版）
        
        Args:
            text: 文本
            top_k: 返回数量
        
        Returns:
            关键词列表
        """
        # 移除标点
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 分词
        words = text.lower().split()
        
        # 停用词
        stopwords = {
            '的', '了', '是', '在', '我', '你', '他', '她', '它', '们',
            '吗', '呢', '吧', '啊', '和', '与', '或', '但', '而', '等'
        }
        
        # 过滤并统计
        word_freq = {}
        for word in words:
            if word and word not in stopwords and len(word) > 1:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 排序取top_k
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:top_k]]
        
        return keywords

