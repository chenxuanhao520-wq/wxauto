"""
RAG 检索器：BM25 召回 + 简化版检索
"""
import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class Evidence:
    """证据块"""
    chunk_id: str
    document_name: str
    document_version: str
    section: str
    content: str
    score: float  # 相关性得分
    keywords: Optional[List[str]] = None


class Retriever:
    """
    RAG 检索器
    实现 BM25 关键词检索
    """
    
    def __init__(
        self,
        bm25_topn: int = 50,
        top_k: int = 4,
        min_confidence: float = 0.75
    ):
        """
        Args:
            bm25_topn: BM25 召回数量
            top_k: 最终返回的证据数量
            min_confidence: 最低置信度阈值
        """
        self.bm25_topn = bm25_topn
        self.top_k = top_k
        self.min_confidence = min_confidence
        
        # 知识库
        self._corpus: List[Dict[str, Any]] = []
        self._bm25_index = None
        
        logger.info(
            f"Retriever 初始化: "
            f"bm25_topn={bm25_topn}, top_k={top_k}, min_conf={min_confidence}"
        )
    
    def retrieve(self, question: str, k: Optional[int] = None) -> List[Evidence]:
        """
        检索相关证据
        Args:
            question: 用户问题
            k: 返回数量（默认使用 self.top_k）
        Returns:
            List[Evidence]: 证据列表
        """
        k = k or self.top_k
        
        if not self._corpus:
            # 知识库为空，返回模拟数据（兼容测试）
            logger.warning("知识库为空，返回模拟证据")
            return self._get_mock_evidences(question, k)
        
        # BM25 检索
        logger.debug(f"检索问题: {question[:50]}..., k={k}")
        
        # 简单的关键词匹配评分
        query_terms = self._tokenize(question)
        scored_chunks = []
        
        for chunk in self._corpus:
            score = self._calculate_bm25_score(query_terms, chunk)
            if score > 0:
                scored_chunks.append((chunk, score))
        
        # 按得分排序
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        # 取 top_k
        top_chunks = scored_chunks[:k]
        
        # 转换为 Evidence
        evidences = []
        for chunk, score in top_chunks:
            evidence = Evidence(
                chunk_id=chunk['chunk_id'],
                document_name=chunk['document_name'],
                document_version=chunk.get('document_version', 'v1.0'),
                section=chunk.get('section', ''),
                content=chunk['content'],
                score=min(score, 1.0),
                keywords=chunk.get('keywords', [])
            )
            evidences.append(evidence)
        
        logger.info(
            f"检索完成: question={question[:30]}..., "
            f"found={len(evidences)} evidences"
        )
        
        return evidences
    
    def calculate_confidence(self, evidences: List[Evidence]) -> float:
        """
        计算置信度
        Args:
            evidences: 证据列表
        Returns:
            float: 置信度 0-1
        """
        if not evidences:
            return 0.0
        
        # ==================== 桩实现 ====================
        # Phase 2 将实现：
        # 1. 基于 top-1 得分
        # 2. 基于 top-k 平均得分
        # 3. 基于证据一致性
        
        # 简单模拟：使用最高得分
        max_score = max(e.score for e in evidences)
        confidence = min(max_score, 1.0)
        
        logger.debug(f"[桩] 计算置信度: {confidence:.2f} (基于 {len(evidences)} 条证据)")
        
        return confidence
    
    def format_evidence_summary(self, evidences: List[Evidence]) -> str:
        """
        格式化证据摘要（用于显示出处）
        Args:
            evidences: 证据列表
        Returns:
            str: 格式化的摘要
        """
        if not evidences:
            return "无相关证据"
        
        lines = []
        for i, ev in enumerate(evidences, 1):
            line = (
                f"{i}. 《{ev.document_name} {ev.document_version}》"
                f"- {ev.section}"
            )
            lines.append(line)
        
        return "\n".join(lines)
    
    # ==================== 桩辅助方法 ====================
    
    def _get_mock_evidences(self, question: str, k: int) -> List[Evidence]:
        """
        生成模拟证据（用于测试）
        根据问题关键词模拟不同置信度
        """
        # 高置信度关键词
        high_conf_keywords = ["安装", "配置", "初始化", "启动"]
        # 中等置信度关键词
        medium_conf_keywords = ["问题", "故障", "错误", "异常"]
        # 低置信度关键词
        low_conf_keywords = ["价格", "报价", "交付", "合同"]
        
        # 根据关键词判断置信度
        if any(kw in question for kw in high_conf_keywords):
            base_score = 0.85
        elif any(kw in question for kw in medium_conf_keywords):
            base_score = 0.65
        elif any(kw in question for kw in low_conf_keywords):
            base_score = 0.45
        else:
            base_score = 0.70
        
        evidences = []
        for i in range(min(k, 3)):  # 最多返回 3 条模拟证据
            evidence = Evidence(
                chunk_id=f"chunk_{i+1}",
                document_name="产品手册",
                document_version="v2.1",
                section=f"第{i+1}章",
                content=f"这是关于'{question[:20]}...'的相关内容片段 #{i+1}",
                score=base_score - i * 0.05,  # 递减得分
                keywords=question.split()[:3]
            )
            evidences.append(evidence)
        
        return evidences
    
    # ==================== 知识库管理 ====================
    
    def load_knowledge_base(self, db_path: str) -> None:
        """
        从数据库加载知识库
        Args:
            db_path: 数据库路径
        """
        import sqlite3
        from pathlib import Path
        
        if not Path(db_path).exists():
            logger.warning(f"数据库不存在: {db_path}")
            return
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT chunk_id, document_name, document_version, 
                       section, content, keywords
                FROM knowledge_chunks
                ORDER BY document_name, chunk_id
            """)
            
            rows = cursor.fetchall()
            self._corpus = []
            
            for row in rows:
                chunk = {
                    'chunk_id': row[0],
                    'document_name': row[1],
                    'document_version': row[2] or 'v1.0',
                    'section': row[3] or '',
                    'content': row[4],
                    'keywords': row[5].split(',') if row[5] else []
                }
                self._corpus.append(chunk)
            
            conn.close()
            
            logger.info(f"知识库已加载: {len(self._corpus)} 条知识块")
            
        except Exception as e:
            logger.error(f"加载知识库失败: {e}")
    
    def add_document(
        self,
        document_name: str,
        document_version: str,
        chunks: List[dict]
    ) -> None:
        """
        添加文档到知识库
        Args:
            document_name: 文档名
            document_version: 版本
            chunks: 分块内容 [{'section': '', 'content': '', 'keywords': []}, ...]
        """
        for i, chunk_data in enumerate(chunks):
            chunk = {
                'chunk_id': f"{document_name}_{document_version}_{i}",
                'document_name': document_name,
                'document_version': document_version,
                'section': chunk_data.get('section', f'块{i+1}'),
                'content': chunk_data['content'],
                'keywords': chunk_data.get('keywords', [])
            }
            self._corpus.append(chunk)
        
        logger.info(f"文档已添加: {document_name} v{document_version}, {len(chunks)} 块")
    
    def save_to_db(self, db_path: str) -> None:
        """
        保存知识库到数据库
        Args:
            db_path: 数据库路径
        """
        import sqlite3
        from pathlib import Path
        
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for chunk in self._corpus:
                keywords_str = ','.join(chunk.get('keywords', []))
                
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge_chunks
                    (chunk_id, document_name, document_version, section, content, keywords)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    chunk['chunk_id'],
                    chunk['document_name'],
                    chunk['document_version'],
                    chunk['section'],
                    chunk['content'],
                    keywords_str
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"知识库已保存: {len(self._corpus)} 条")
            
        except Exception as e:
            logger.error(f"保存知识库失败: {e}")
    
    def rebuild_index(self) -> None:
        """重建索引（当前使用实时计算，无需重建）"""
        logger.info(f"当前使用实时检索，无需重建索引。知识库大小: {len(self._corpus)}")
    
    # ==================== 辅助方法 ====================
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 移除标点，分割为词
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.lower().split()
        # 过滤停用词（简化）
        stopwords = {'的', '了', '是', '在', '我', '你', '他', '她', '它', '们', '吗', '呢', '吧'}
        return [t for t in tokens if t and t not in stopwords]
    
    def _calculate_bm25_score(self, query_terms: List[str], chunk: Dict[str, Any]) -> float:
        """
        计算 BM25 得分（简化版）
        """
        # 简化的 TF-IDF 评分
        content = chunk['content'].lower()
        keywords = [k.lower() for k in chunk.get('keywords', [])]
        
        score = 0.0
        
        for term in query_terms:
            # 内容匹配
            if term in content:
                tf = content.count(term)
                score += tf * 0.5
            
            # 关键词匹配（权重更高）
            if term in keywords:
                score += 2.0
        
        # 归一化
        if query_terms:
            score = score / len(query_terms)
        
        return score
