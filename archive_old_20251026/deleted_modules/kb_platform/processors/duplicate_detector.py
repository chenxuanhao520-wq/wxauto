"""
重复检测器
使用多种算法检测知识库中的重复内容，确保数据唯一性
"""
import logging
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class DuplicateMatch:
    """重复匹配结果"""
    chunk_id_1: str
    chunk_id_2: str
    similarity_score: float
    match_type: str  # exact, semantic, structural
    similarity_method: str
    content_1: str
    content_2: str


@dataclass
class DuplicateDetectionResult:
    """重复检测结果"""
    has_duplicates: bool
    total_duplicates: int
    duplicate_groups: List[List[str]]
    matches: List[DuplicateMatch]
    summary: str


class DuplicateDetector:
    """
    重复检测器
    
    功能：
    1. 精确重复检测（哈希比较）
    2. 语义相似度检测
    3. 结构化重复检测
    4. 多层次重复分析
    """
    
    def __init__(
        self,
        exact_threshold: float = 1.0,
        semantic_threshold: float = 0.85,
        structural_threshold: float = 0.9,
        min_content_length: int = 20
    ):
        """
        初始化重复检测器
        
        Args:
            exact_threshold: 精确重复阈值
            semantic_threshold: 语义相似度阈值
            structural_threshold: 结构化相似度阈值
            min_content_length: 最小内容长度（低于此长度不检测）
        """
        self.exact_threshold = exact_threshold
        self.semantic_threshold = semantic_threshold
        self.structural_threshold = structural_threshold
        self.min_content_length = min_content_length
        
        # 初始化TF-IDF向量化器（如果sklearn可用）
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words=None,  # 我们使用自定义停用词
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95
            )
            detection_method = "高精度TF-IDF算法"
        else:
            self.tfidf_vectorizer = None
            detection_method = "轻量级Jaccard算法"
        
        # 存储已处理的内容哈希
        self.content_hashes: Set[str] = set()
        
        logger.info(
            f"重复检测器初始化完成: "
            f"exact={exact_threshold}, semantic={semantic_threshold}, "
            f"structural={structural_threshold}, "
            f"方法={detection_method}"
        )
    
    async def detect_duplicates(
        self,
        chunks: List[Dict[str, Any]],
        methods: List[str] = None
    ) -> DuplicateDetectionResult:
        """
        检测重复内容
        
        Args:
            chunks: 知识块列表
            methods: 检测方法列表 ['exact', 'semantic', 'structural']
        
        Returns:
            重复检测结果
        """
        if not chunks:
            return DuplicateDetectionResult(
                has_duplicates=False,
                total_duplicates=0,
                duplicate_groups=[],
                matches=[],
                summary="没有内容需要检测"
            )
        
        # 过滤太短的内容
        valid_chunks = [
            chunk for chunk in chunks
            if len(chunk.get('content', '')) >= self.min_content_length
        ]
        
        if len(valid_chunks) != len(chunks):
            logger.warning(f"过滤了 {len(chunks) - len(valid_chunks)} 个太短的内容")
        
        if not valid_chunks:
            return DuplicateDetectionResult(
                has_duplicates=False,
                total_duplicates=0,
                duplicate_groups=[],
                matches=[],
                summary="所有内容都太短，跳过检测"
            )
        
        # 默认使用所有检测方法
        if methods is None:
            methods = ['exact', 'semantic', 'structural']
        
        all_matches = []
        
        # 1. 精确重复检测
        if 'exact' in methods:
            exact_matches = await self._detect_exact_duplicates(valid_chunks)
            all_matches.extend(exact_matches)
        
        # 2. 语义相似度检测
        if 'semantic' in methods:
            semantic_matches = await self._detect_semantic_duplicates(valid_chunks)
            all_matches.extend(semantic_matches)
        
        # 3. 结构化重复检测
        if 'structural' in methods:
            structural_matches = await self._detect_structural_duplicates(valid_chunks)
            all_matches.extend(structural_matches)
        
        # 去重和分组
        duplicate_groups = self._group_duplicates(all_matches)
        
        # 生成摘要
        summary = self._generate_summary(all_matches, duplicate_groups)
        
        result = DuplicateDetectionResult(
            has_duplicates=len(all_matches) > 0,
            total_duplicates=len(all_matches),
            duplicate_groups=duplicate_groups,
            matches=all_matches,
            summary=summary
        )
        
        logger.info(f"重复检测完成: 发现 {len(all_matches)} 个重复匹配")
        
        return result
    
    async def _detect_exact_duplicates(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[DuplicateMatch]:
        """检测精确重复"""
        matches = []
        content_hash_map = {}
        
        for chunk in chunks:
            content = chunk.get('content', '')
            chunk_id = chunk.get('chunk_id', '')
            
            # 计算内容哈希
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if content_hash in content_hash_map:
                # 发现精确重复
                existing_chunk = content_hash_map[content_hash]
                match = DuplicateMatch(
                    chunk_id_1=existing_chunk['chunk_id'],
                    chunk_id_2=chunk_id,
                    similarity_score=1.0,
                    match_type='exact',
                    similarity_method='hash',
                    content_1=existing_chunk['content'],
                    content_2=content
                )
                matches.append(match)
            else:
                content_hash_map[content_hash] = chunk
        
        return matches
    
    async def _detect_semantic_duplicates(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[DuplicateMatch]:
        """检测语义重复（智能降级）"""
        if len(chunks) < 2:
            return []
        
        # 根据sklearn可用性选择算法
        if SKLEARN_AVAILABLE and self.tfidf_vectorizer:
            return await self._sklearn_semantic_detection(chunks)
        else:
            return await self._lightweight_semantic_detection(chunks)
    
    async def _sklearn_semantic_detection(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[DuplicateMatch]:
        """高精度语义检测（使用sklearn TF-IDF）"""
        matches = []
        
        try:
            # 提取内容
            contents = [chunk.get('content', '') for chunk in chunks]
            chunk_ids = [chunk.get('chunk_id', '') for chunk in chunks]
            
            # TF-IDF向量化
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(contents)
            
            # 计算余弦相似度
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # 找出相似度超过阈值的对
            for i in range(len(chunks)):
                for j in range(i + 1, len(chunks)):
                    similarity = similarity_matrix[i][j]
                    
                    if similarity >= self.semantic_threshold:
                        match = DuplicateMatch(
                            chunk_id_1=chunk_ids[i],
                            chunk_id_2=chunk_ids[j],
                            similarity_score=float(similarity),
                            match_type='semantic',
                            similarity_method='tfidf_cosine',
                            content_1=contents[i],
                            content_2=contents[j]
                        )
                        matches.append(match)
            
        except Exception as e:
            logger.error(f"sklearn语义检测失败: {e}")
        
        return matches
    
    async def _lightweight_semantic_detection(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[DuplicateMatch]:
        """轻量级语义检测（使用Jaccard相似度）"""
        matches = []
        
        try:
            # 提取内容并分词
            chunk_words = []
            for chunk in chunks:
                content = chunk.get('content', '')
                words = set(content.lower().split())
                chunk_words.append(words)
            
            # 计算Jaccard相似度
            for i in range(len(chunks)):
                for j in range(i + 1, len(chunks)):
                    words1 = chunk_words[i]
                    words2 = chunk_words[j]
                    
                    if not words1 or not words2:
                        continue
                    
                    # Jaccard相似度 = 交集/并集
                    intersection = len(words1 & words2)
                    union = len(words1 | words2)
                    similarity = intersection / union if union > 0 else 0.0
                    
                    if similarity >= self.semantic_threshold:
                        match = DuplicateMatch(
                            chunk_id_1=chunks[i].get('chunk_id', ''),
                            chunk_id_2=chunks[j].get('chunk_id', ''),
                            similarity_score=similarity,
                            match_type='semantic',
                            similarity_method='jaccard',
                            content_1=chunks[i].get('content', ''),
                            content_2=chunks[j].get('content', '')
                        )
                        matches.append(match)
            
        except Exception as e:
            logger.error(f"轻量级语义检测失败: {e}")
        
        return matches
    
    async def _detect_structural_duplicates(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[DuplicateMatch]:
        """检测结构化重复"""
        matches = []
        
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                chunk1 = chunks[i]
                chunk2 = chunks[j]
                
                content1 = chunk1.get('content', '')
                content2 = chunk2.get('content', '')
                
                # 计算结构化相似度
                structural_similarity = self._calculate_structural_similarity(content1, content2)
                
                if structural_similarity >= self.structural_threshold:
                    match = DuplicateMatch(
                        chunk_id_1=chunk1.get('chunk_id', ''),
                        chunk_id_2=chunk2.get('chunk_id', ''),
                        similarity_score=structural_similarity,
                        match_type='structural',
                        similarity_method='sequence_matcher',
                        content_1=content1,
                        content_2=content2
                    )
                    matches.append(match)
        
        return matches
    
    def _calculate_structural_similarity(self, content1: str, content2: str) -> float:
        """计算结构化相似度"""
        # 使用SequenceMatcher计算相似度
        matcher = SequenceMatcher(None, content1, content2)
        return matcher.ratio()
    
    def _group_duplicates(self, matches: List[DuplicateMatch]) -> List[List[str]]:
        """将重复匹配分组"""
        # 构建图
        graph = {}
        for match in matches:
            chunk1 = match.chunk_id_1
            chunk2 = match.chunk_id_2
            
            if chunk1 not in graph:
                graph[chunk1] = set()
            if chunk2 not in graph:
                graph[chunk2] = set()
            
            graph[chunk1].add(chunk2)
            graph[chunk2].add(chunk1)
        
        # 使用DFS找连通分量
        visited = set()
        groups = []
        
        def dfs(node, group):
            if node in visited:
                return
            visited.add(node)
            group.append(node)
            for neighbor in graph.get(node, []):
                dfs(neighbor, group)
        
        for node in graph:
            if node not in visited:
                group = []
                dfs(node, group)
                if len(group) > 1:  # 只保留有重复的组
                    groups.append(group)
        
        return groups
    
    def _generate_summary(
        self,
        matches: List[DuplicateMatch],
        duplicate_groups: List[List[str]]
    ) -> str:
        """生成重复检测摘要"""
        if not matches:
            return "未发现重复内容"
        
        # 统计不同类型
        exact_count = sum(1 for m in matches if m.match_type == 'exact')
        semantic_count = sum(1 for m in matches if m.match_type == 'semantic')
        structural_count = sum(1 for m in matches if m.match_type == 'structural')
        
        summary_parts = [
            f"发现 {len(matches)} 个重复匹配",
            f"涉及 {len(duplicate_groups)} 个重复组",
            f"精确重复: {exact_count} 个",
            f"语义重复: {semantic_count} 个",
            f"结构化重复: {structural_count} 个"
        ]
        
        return "；".join(summary_parts)
    
    async def check_content_against_existing(
        self,
        content: str,
        chunk_id: str
    ) -> Dict[str, Any]:
        """
        检查单个内容是否与现有内容重复
        
        Args:
            content: 要检查的内容
            chunk_id: 内容ID
        
        Returns:
            检查结果
        """
        if len(content) < self.min_content_length:
            return {
                'is_duplicate': False,
                'reason': 'content_too_short'
            }
        
        # 计算内容哈希
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # 检查精确重复
        if content_hash in self.content_hashes:
            return {
                'is_duplicate': True,
                'duplicate_type': 'exact',
                'similarity_score': 1.0,
                'reason': 'exact_hash_match'
            }
        
        # 添加到已知哈希集合
        self.content_hashes.add(content_hash)
        
        return {
            'is_duplicate': False,
            'reason': 'no_duplicate_found'
        }
    
    def get_duplicate_statistics(self) -> Dict[str, Any]:
        """获取重复检测统计信息"""
        return {
            'total_content_hashes': len(self.content_hashes),
            'exact_threshold': self.exact_threshold,
            'semantic_threshold': self.semantic_threshold,
            'structural_threshold': self.structural_threshold,
            'min_content_length': self.min_content_length
        }
    
    async def cleanup_duplicate_hashes(self, chunk_ids: List[str]):
        """
        清理重复检测中的哈希记录
        
        Args:
            chunk_ids: 要清理的内容ID列表
        """
        # 这里可以实现更复杂的清理逻辑
        # 目前简化实现
        logger.info(f"清理重复检测记录: {len(chunk_ids)} 个内容")
    
    def reset(self):
        """重置重复检测器状态"""
        self.content_hashes.clear()
        logger.info("重复检测器状态已重置")
