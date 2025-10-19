"""
动态知识库更新器
负责知识库的自动化更新、版本管理和增量同步
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

# 尝试导入difflib和gensim
from difflib import SequenceMatcher, unified_diff

try:
    from gensim import corpora, models, similarities
    GENSIM_AVAILABLE = True
except ImportError:
    GENSIM_AVAILABLE = False
    corpora = None
    models = None
    similarities = None

logger = logging.getLogger(__name__)


@dataclass
class UpdateOperation:
    """更新操作"""
    operation_id: str
    operation_type: str  # add, update, delete, merge
    target_chunk_ids: List[str]
    new_content: Optional[str]
    old_content: Optional[str]
    reason: str
    confidence: float
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UpdateResult:
    """更新结果"""
    success: bool
    operations_performed: List[UpdateOperation]
    chunks_added: int
    chunks_updated: int
    chunks_deleted: int
    chunks_merged: int
    total_changes: int
    summary: str


class DynamicKBUpdater:
    """
    动态知识库更新器
    
    功能：
    1. 增量更新检测
    2. 版本差异分析（difflib）
    3. 语义相似度分析（gensim可选）
    4. 智能合并策略
    5. 自动化更新流程
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.85,
        use_gensim: bool = True,
        auto_merge: bool = True
    ):
        """
        初始化动态更新器
        
        Args:
            similarity_threshold: 相似度阈值
            use_gensim: 是否使用gensim（更精确的语义分析）
            auto_merge: 是否自动合并相似内容
        """
        self.similarity_threshold = similarity_threshold
        self.use_gensim = use_gensim and GENSIM_AVAILABLE
        self.auto_merge = auto_merge
        
        # 初始化gensim模型（如果可用）
        self.dictionary = None
        self.tfidf_model = None
        self.similarity_index = None
        
        if self.use_gensim:
            logger.info("✅ 使用gensim进行语义分析")
        else:
            logger.info("⚠️ gensim未安装，使用difflib进行文本对比")
        
        logger.info("动态知识库更新器初始化完成")
    
    async def detect_updates(
        self,
        new_chunks: List[Dict[str, Any]],
        existing_chunks: List[Dict[str, Any]]
    ) -> List[UpdateOperation]:
        """
        检测需要更新的内容
        
        Args:
            new_chunks: 新上传的内容块
            existing_chunks: 已存在的内容块
        
        Returns:
            更新操作列表
        """
        operations = []
        
        # 1. 检测新增内容
        add_operations = await self._detect_additions(new_chunks, existing_chunks)
        operations.extend(add_operations)
        
        # 2. 检测更新内容
        update_operations = await self._detect_updates(new_chunks, existing_chunks)
        operations.extend(update_operations)
        
        # 3. 检测需要合并的内容
        if self.auto_merge:
            merge_operations = await self._detect_merges(new_chunks, existing_chunks)
            operations.extend(merge_operations)
        
        # 4. 检测过时内容（可选）
        delete_operations = await self._detect_obsolete(new_chunks, existing_chunks)
        operations.extend(delete_operations)
        
        logger.info(f"更新检测完成: 发现 {len(operations)} 个操作")
        
        return operations
    
    async def apply_updates(
        self,
        operations: List[UpdateOperation],
        kb_storage
    ) -> UpdateResult:
        """
        应用更新操作
        
        Args:
            operations: 更新操作列表
            kb_storage: 知识库存储
        
        Returns:
            更新结果
        """
        chunks_added = 0
        chunks_updated = 0
        chunks_deleted = 0
        chunks_merged = 0
        
        for operation in operations:
            try:
                if operation.operation_type == 'add':
                    await kb_storage.add_chunk(operation.new_content)
                    chunks_added += 1
                
                elif operation.operation_type == 'update':
                    await kb_storage.update_chunk(
                        operation.target_chunk_ids[0],
                        operation.new_content
                    )
                    chunks_updated += 1
                
                elif operation.operation_type == 'delete':
                    for chunk_id in operation.target_chunk_ids:
                        await kb_storage.delete_chunk(chunk_id)
                    chunks_deleted += len(operation.target_chunk_ids)
                
                elif operation.operation_type == 'merge':
                    await kb_storage.merge_chunks(
                        operation.target_chunk_ids,
                        operation.new_content
                    )
                    chunks_merged += 1
                
            except Exception as e:
                logger.error(f"应用操作失败 {operation.operation_id}: {e}")
        
        total_changes = chunks_added + chunks_updated + chunks_deleted + chunks_merged
        
        summary = (
            f"新增 {chunks_added} 个, "
            f"更新 {chunks_updated} 个, "
            f"删除 {chunks_deleted} 个, "
            f"合并 {chunks_merged} 个"
        )
        
        return UpdateResult(
            success=True,
            operations_performed=operations,
            chunks_added=chunks_added,
            chunks_updated=chunks_updated,
            chunks_deleted=chunks_deleted,
            chunks_merged=chunks_merged,
            total_changes=total_changes,
            summary=summary
        )
    
    async def _detect_additions(
        self,
        new_chunks: List[Dict[str, Any]],
        existing_chunks: List[Dict[str, Any]]
    ) -> List[UpdateOperation]:
        """检测新增内容"""
        operations = []
        
        # 构建已存在内容的哈希集合
        existing_content_hashes = {
            self._content_hash(chunk.get('content', ''))
            for chunk in existing_chunks
        }
        
        for new_chunk in new_chunks:
            new_content = new_chunk.get('content', '')
            new_hash = self._content_hash(new_content)
            
            # 精确匹配检查
            if new_hash not in existing_content_hashes:
                # 语义相似度检查
                is_similar = await self._is_semantically_similar(
                    new_content, existing_chunks
                )
                
                if not is_similar:
                    operation = UpdateOperation(
                        operation_id=f"add_{new_chunk.get('chunk_id', '')}",
                        operation_type='add',
                        target_chunk_ids=[],
                        new_content=new_content,
                        old_content=None,
                        reason='新内容，不与现有内容重复',
                        confidence=0.95
                    )
                    operations.append(operation)
        
        return operations
    
    async def _detect_updates(
        self,
        new_chunks: List[Dict[str, Any]],
        existing_chunks: List[Dict[str, Any]]
    ) -> List[UpdateOperation]:
        """检测内容更新"""
        operations = []
        
        for new_chunk in new_chunks:
            new_content = new_chunk.get('content', '')
            
            # 找到最相似的现有内容
            most_similar, similarity = await self._find_most_similar(
                new_content, existing_chunks
            )
            
            if most_similar and 0.7 <= similarity < 0.95:
                # 使用difflib分析差异
                old_content = most_similar.get('content', '')
                diff = self._calculate_diff(old_content, new_content)
                
                # 判断是否是有意义的更新
                if self._is_meaningful_update(diff):
                    operation = UpdateOperation(
                        operation_id=f"update_{most_similar.get('chunk_id', '')}",
                        operation_type='update',
                        target_chunk_ids=[most_similar.get('chunk_id', '')],
                        new_content=new_content,
                        old_content=old_content,
                        reason=f'内容更新（相似度{similarity:.2f}）',
                        confidence=similarity
                    )
                    operations.append(operation)
        
        return operations
    
    async def _detect_merges(
        self,
        new_chunks: List[Dict[str, Any]],
        existing_chunks: List[Dict[str, Any]]
    ) -> List[UpdateOperation]:
        """检测需要合并的内容"""
        operations = []
        
        # 找出高度相似但不完全相同的内容组
        for new_chunk in new_chunks:
            new_content = new_chunk.get('content', '')
            similar_chunks = []
            
            for existing_chunk in existing_chunks:
                existing_content = existing_chunk.get('content', '')
                similarity = self._calculate_text_similarity(new_content, existing_content)
                
                if 0.85 <= similarity < 0.95:
                    similar_chunks.append(existing_chunk)
            
            # 如果找到多个相似内容，建议合并
            if len(similar_chunks) > 1:
                # 合并所有相似内容
                merged_content = self._merge_contents(
                    new_content,
                    [chunk.get('content', '') for chunk in similar_chunks]
                )
                
                operation = UpdateOperation(
                    operation_id=f"merge_{new_chunk.get('chunk_id', '')}",
                    operation_type='merge',
                    target_chunk_ids=[chunk.get('chunk_id', '') for chunk in similar_chunks],
                    new_content=merged_content,
                    old_content=None,
                    reason=f'合并 {len(similar_chunks)} 个相似内容',
                    confidence=0.85
                )
                operations.append(operation)
        
        return operations
    
    async def _detect_obsolete(
        self,
        new_chunks: List[Dict[str, Any]],
        existing_chunks: List[Dict[str, Any]]
    ) -> List[UpdateOperation]:
        """检测过时内容"""
        operations = []
        
        # 简化实现：检测长时间未更新且没有相似新内容的chunk
        # 实际应用中需要更复杂的逻辑
        
        return operations
    
    async def _is_semantically_similar(
        self,
        new_content: str,
        existing_chunks: List[Dict[str, Any]]
    ) -> bool:
        """检查是否与现有内容语义相似"""
        for existing_chunk in existing_chunks:
            existing_content = existing_chunk.get('content', '')
            similarity = await self._calculate_semantic_similarity(
                new_content, existing_content
            )
            
            if similarity >= self.similarity_threshold:
                return True
        
        return False
    
    async def _find_most_similar(
        self,
        content: str,
        chunks: List[Dict[str, Any]]
    ) -> tuple:
        """找到最相似的内容块"""
        if not chunks:
            return None, 0.0
        
        max_similarity = 0.0
        most_similar = None
        
        for chunk in chunks:
            chunk_content = chunk.get('content', '')
            similarity = await self._calculate_semantic_similarity(content, chunk_content)
            
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar = chunk
        
        return most_similar, max_similarity
    
    async def _calculate_semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """计算语义相似度"""
        if self.use_gensim and GENSIM_AVAILABLE:
            return self._gensim_similarity(text1, text2)
        else:
            return self._calculate_text_similarity(text1, text2)
    
    def _gensim_similarity(self, text1: str, text2: str) -> float:
        """使用gensim计算语义相似度"""
        # 简化实现，实际使用时需要训练模型
        # 这里使用TF-IDF作为示例
        
        try:
            # 分词
            texts = [text1.split(), text2.split()]
            
            # 创建字典
            dictionary = corpora.Dictionary(texts)
            
            # 创建语料库
            corpus = [dictionary.doc2bow(text) for text in texts]
            
            # TF-IDF模型
            tfidf = models.TfidfModel(corpus)
            corpus_tfidf = tfidf[corpus]
            
            # 计算相似度
            index = similarities.MatrixSimilarity(corpus_tfidf)
            sims = index[corpus_tfidf[0]]
            
            return float(sims[1]) if len(sims) > 1 else 0.0
            
        except Exception as e:
            logger.error(f"gensim相似度计算失败: {e}")
            return self._calculate_text_similarity(text1, text2)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（使用difflib）"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _calculate_diff(self, old: str, new: str) -> List[str]:
        """计算文本差异"""
        return list(unified_diff(
            old.splitlines(),
            new.splitlines(),
            lineterm=''
        ))
    
    def _is_meaningful_update(self, diff: List[str]) -> bool:
        """判断是否是有意义的更新"""
        # 过滤掉只是格式变化的更新
        meaningful_changes = [
            line for line in diff
            if line.startswith('+') or line.startswith('-')
        ]
        
        return len(meaningful_changes) > 2  # 至少有实质性改动
    
    def _merge_contents(self, new_content: str, existing_contents: List[str]) -> str:
        """合并多个内容"""
        # 简化实现：保留最长的版本并补充其他版本的独特信息
        all_contents = [new_content] + existing_contents
        
        # 按长度排序，保留最长的作为基础
        all_contents.sort(key=len, reverse=True)
        base_content = all_contents[0]
        
        # 提取其他版本的独特句子
        unique_sentences = set()
        for content in all_contents[1:]:
            sentences = content.split('。')
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and sentence not in base_content:
                    unique_sentences.add(sentence)
        
        # 合并
        if unique_sentences:
            merged = base_content + '\n\n补充信息：\n' + '。'.join(unique_sentences)
            return merged
        
        return base_content
    
    def _content_hash(self, content: str) -> str:
        """计算内容哈希"""
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def build_gensim_index(self, chunks: List[Dict[str, Any]]):
        """构建gensim索引（可选优化）"""
        if not self.use_gensim:
            return
        
        try:
            # 提取文本
            texts = [chunk.get('content', '').split() for chunk in chunks]
            
            # 创建字典
            self.dictionary = corpora.Dictionary(texts)
            
            # 创建语料库
            corpus = [self.dictionary.doc2bow(text) for text in texts]
            
            # 训练TF-IDF模型
            self.tfidf_model = models.TfidfModel(corpus)
            corpus_tfidf = self.tfidf_model[corpus]
            
            # 创建相似度索引
            self.similarity_index = similarities.MatrixSimilarity(corpus_tfidf)
            
            logger.info(f"gensim索引构建完成: {len(chunks)} 个文档")
            
        except Exception as e:
            logger.error(f"gensim索引构建失败: {e}")
