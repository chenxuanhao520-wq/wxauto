"""
文档处理中心
统一处理多种格式的文档，提取文本并分段
支持 MCP AIOCR 服务
"""
import logging
import re
import asyncio
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
    
    def __init__(self, use_ocr: bool = True, use_mcp_aiocr: bool = True):
        """
        初始化文档处理器
        
        Args:
            use_ocr: 是否启用本地OCR（用于扫描版PDF和图片）
            use_mcp_aiocr: 是否启用 MCP AIOCR 服务
        """
        self.use_ocr = use_ocr
        self.use_mcp_aiocr = use_mcp_aiocr
        
        # 初始化各种解析器
        self.parsers = {
            'pdf': PDFParser(use_ocr=use_ocr),
            'doc': DocParser(),
            'image': ImageParser(lang='ch')
        }
        
        # 初始化 MCP AIOCR 客户端
        self.mcp_aiocr = None
        if use_mcp_aiocr:
            try:
                from modules.mcp_platform import MCPManager
                mcp_manager = MCPManager()
                self.mcp_aiocr = mcp_manager.get_client("aiocr")
                logger.info("✅ MCP AIOCR 客户端初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ MCP AIOCR 初始化失败，将使用本地解析: {e}")
                self.use_mcp_aiocr = False
        
        logger.info(f"文档处理器初始化完成 (OCR: {use_ocr}, MCP AIOCR: {use_mcp_aiocr})")
    
    def process_file(
        self,
        file_path: str,
        document_name: Optional[str] = None,
        document_version: str = "v1.0",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        use_mcp_aiocr: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            document_name: 文档名称（可选，默认使用文件名）
            document_version: 文档版本
            chunk_size: 分段大小（字符数）
            chunk_overlap: 分段重叠（字符数）
            use_mcp_aiocr: 是否使用 MCP AIOCR（可选，默认使用全局设置）
        
        Returns:
            {
                'document_name': str,
                'document_version': str,
                'chunks': List[Dict],  # 分段列表
                'metadata': Dict,      # 文档元数据
                'processing_method': str  # 处理方法：'mcp_aiocr' | 'local'
            }
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 确定文档名称
        if not document_name:
            document_name = path.stem
        
        # 决定是否使用 MCP AIOCR
        should_use_mcp = use_mcp_aiocr if use_mcp_aiocr is not None else self.use_mcp_aiocr
        
        # 尝试使用 MCP AIOCR
        if should_use_mcp and self.mcp_aiocr:
            try:
                logger.info(f"🤖 使用 MCP AIOCR 处理文档: {file_path}")
                result = asyncio.run(self._process_with_mcp_aiocr(
                    file_path, document_name, document_version, chunk_size, chunk_overlap
                ))
                if result:
                    return result
            except Exception as e:
                logger.warning(f"⚠️ MCP AIOCR 处理失败，降级到本地解析: {e}")
        
        # 使用本地解析器
        logger.info(f"📄 使用本地解析器处理文档: {file_path}")
        return self._process_with_local_parser(
            file_path, document_name, document_version, chunk_size, chunk_overlap
        )
    
    async def _process_with_mcp_aiocr(
        self, file_path: str, document_name: str, document_version: str,
        chunk_size: int, chunk_overlap: int
    ) -> Optional[Dict[str, Any]]:
        """使用 MCP AIOCR 处理文档"""
        try:
            # 尝试文档识别
            result = await self.mcp_aiocr.doc_recognition(file_path)
            
            if not result.get("success"):
                logger.warning(f"MCP AIOCR 识别失败: {result.get('error')}")
                return None
            
            text = result["content"]
            metadata = result.get("metadata", {})
            metadata.update({
                "processing_method": "mcp_aiocr",
                "aiocr_metadata": result.get("metadata", {}),
                "file_size": result.get("file_size", 0),
                "format": result.get("format", "")
            })
            
            # 智能分段
            chunks = self._split_into_chunks(
                text=text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                document_name=document_name,
                document_version=document_version
            )
            
            logger.info(f"✅ MCP AIOCR 处理完成: {document_name}, {len(text)}字符 → {len(chunks)}个分段")
            
            return {
                'document_name': document_name,
                'document_version': document_version,
                'chunks': chunks,
                'metadata': metadata,
                'total_chars': len(text),
                'processing_method': 'mcp_aiocr'
            }
            
        except Exception as e:
            logger.error(f"❌ MCP AIOCR 处理异常: {e}")
            return None
    
    def _process_with_local_parser(
        self, file_path: str, document_name: str, document_version: str,
        chunk_size: int, chunk_overlap: int
    ) -> Dict[str, Any]:
        """使用本地解析器处理文档"""
        path = Path(file_path)
        
        # 根据文件格式选择解析器
        parser = self._get_parser(path.suffix.lower())
        if not parser:
            raise ValueError(f"不支持的文件格式: {path.suffix}")
        
        # 解析文档
        parsed = parser.parse(file_path)
        
        text = parsed['text']
        metadata = parsed.get('metadata', {})
        metadata.update({
            "processing_method": "local"
        })
        
        # 智能分段
        chunks = self._split_into_chunks(
            text=text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            document_name=document_name,
            document_version=document_version
        )
        
        logger.info(f"✅ 本地解析完成: {document_name}, {len(text)}字符 → {len(chunks)}个分段")
        
        return {
            'document_name': document_name,
            'document_version': document_version,
            'chunks': chunks,
            'metadata': metadata,
            'total_chars': len(text),
            'processing_method': 'local'
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
    
    async def batch_process_files(
        self,
        file_paths: List[str],
        document_version: str = "v1.0",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        use_mcp_aiocr: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        批量处理文件
        
        Args:
            file_paths: 文件路径列表
            document_version: 文档版本
            chunk_size: 分段大小
            chunk_overlap: 分段重叠
            use_mcp_aiocr: 是否使用 MCP AIOCR
        
        Returns:
            处理结果列表
        """
        results = []
        
        logger.info(f"📦 开始批量处理 {len(file_paths)} 个文件")
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                logger.info(f"处理文件 {i}/{len(file_paths)}: {file_path}")
                
                result = self.process_file(
                    file_path=file_path,
                    document_version=document_version,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    use_mcp_aiocr=use_mcp_aiocr
                )
                
                results.append(result)
                
                # 避免请求过于频繁
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ 处理文件失败: {file_path}, {e}")
                results.append({
                    "error": str(e),
                    "file_path": file_path,
                    "success": False
                })
        
        success_count = sum(1 for r in results if r.get("success", True) and "error" not in r)
        logger.info(f"✅ 批量处理完成: {success_count}/{len(file_paths)} 成功")
        
        return results
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的文件格式"""
        local_formats = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.bmp']
        
        mcp_formats = []
        if self.mcp_aiocr:
            try:
                mcp_formats = self.mcp_aiocr.get_supported_formats()
            except:
                pass
        
        return {
            "local": local_formats,
            "mcp_aiocr": mcp_formats,
            "combined": list(set(local_formats + [f".{fmt}" for fmt in mcp_formats]))
        }
    
    def is_mcp_aiocr_available(self) -> bool:
        """检查 MCP AIOCR 是否可用"""
        return self.mcp_aiocr is not None and self.use_mcp_aiocr
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            "local_parsers": {
                "pdf": "available" if self.parsers.get('pdf') else "unavailable",
                "doc": "available" if self.parsers.get('doc') else "unavailable", 
                "image": "available" if self.parsers.get('image') else "unavailable"
            },
            "mcp_aiocr": {
                "enabled": self.use_mcp_aiocr,
                "client_available": self.mcp_aiocr is not None
            }
        }
        
        # 检查 MCP AIOCR 健康状态
        if self.mcp_aiocr:
            try:
                mcp_health = await self.mcp_aiocr.health_check()
                health["mcp_aiocr"]["status"] = mcp_health.get("status", "unknown")
            except Exception as e:
                health["mcp_aiocr"]["status"] = "error"
                health["mcp_aiocr"]["error"] = str(e)
        
        return health

