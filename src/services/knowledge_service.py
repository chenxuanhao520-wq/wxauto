from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class KnowledgeItem:
    doc_id: str
    content: str
    source: str
    metadata: Dict[str, Any]


class KnowledgeService:
    """知识库服务（抽象统一接口）

    目标：
    - 屏蔽底层实现（Chroma、本地检索、外部RAG、MCP-AIOCR产物）
    - 提供统一的索引与检索能力
    """

    def __init__(self, backend=None, config: Optional[Dict[str, Any]] = None):
        self.backend = backend
        self.config = config or {}

    def index(self, items: List[KnowledgeItem]) -> int:
        """批量索引，返回成功条数"""
        if not items:
            return 0
        if hasattr(self.backend, 'index'):
            return int(self.backend.index(items))
        # 默认内存实现
        if not hasattr(self, '_store'):
            self._store = []
        self._store.extend(items)
        return len(items)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """简单检索，返回统一结构：content, source, score"""
        if hasattr(self.backend, 'search'):
            return self.backend.search(query, top_k=top_k)
        if not hasattr(self, '_store'):
            return []
        # 朴素相似度：重叠词数量
        tokens = set(query.lower().split())
        scored = []
        for item in self._store:
            overlap = len(tokens & set(item.content.lower().split()))
            if overlap > 0:
                scored.append({
                    'content': item.content,
                    'source': item.source,
                    'score': float(overlap)
                })
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:top_k]

    def delete(self, doc_ids: List[str]) -> int:
        if hasattr(self.backend, 'delete'):
            return int(self.backend.delete(doc_ids))
        if not hasattr(self, '_store') or not self._store:
            return 0
        before = len(self._store)
        self._store = [it for it in self._store if it.doc_id not in set(doc_ids)]
        return before - len(self._store)
