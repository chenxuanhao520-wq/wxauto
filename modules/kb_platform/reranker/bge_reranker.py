"""
BGE重排序器 - 免费提升检索精度10%+
"""
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 尝试导入FlagEmbedding
try:
    from FlagEmbedding import FlagReranker
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    FlagReranker = None


@dataclass
class RerankResult:
    """重排序结果"""
    text: str
    score: float
    original_rank: int
    new_rank: int
    metadata: Dict[str, Any] = None


class BGEReranker:
    """
    BGE重排序器
    
    功能：
    - 对粗排结果进行精排
    - 提升Top10准确率
    - 免费本地部署
    - 效果提升10-30%
    
    使用场景：
    粗排（向量检索100条） → 精排（重排序10条） → 返回
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        use_fp16: bool = True,
        batch_size: int = 32
    ):
        """
        初始化重排序器
        
        Args:
            model_name: 模型名称
            use_fp16: 是否使用FP16（节省显存）
            batch_size: 批处理大小
        """
        self.model_name = model_name
        self.use_fp16 = use_fp16
        self.batch_size = batch_size
        self._model = None
        
        if not RERANKER_AVAILABLE:
            logger.warning(
                "FlagEmbedding未安装，重排序功能不可用。"
                "安装命令: pip install FlagEmbedding"
            )
        
        logger.info(f"BGE重排序器初始化: {model_name}")
    
    def _load_model(self):
        """懒加载模型"""
        if self._model is not None:
            return
        
        if not RERANKER_AVAILABLE:
            raise ImportError(
                "FlagEmbedding未安装，无法使用重排序功能。"
                "请运行: pip install FlagEmbedding"
            )
        
        logger.info("加载BGE Reranker模型（首次加载会下载）...")
        
        self._model = FlagReranker(
            self.model_name,
            use_fp16=self.use_fp16
        )
        
        logger.info("BGE Reranker模型加载完成")
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10,
        return_documents: bool = True
    ) -> List[RerankResult]:
        """
        重排序文档
        
        Args:
            query: 查询文本
            documents: 候选文档列表
            top_k: 返回数量
            return_documents: 是否返回文档内容
        
        Returns:
            重排序后的结果列表
        """
        if not documents:
            return []
        
        # 加载模型
        self._load_model()
        
        # 构造query-doc对
        pairs = [[query, doc] for doc in documents]
        
        # 批量计算分数
        try:
            scores = self._model.compute_score(pairs, batch_size=self.batch_size)
            
            # 确保scores是列表
            if not isinstance(scores, list):
                scores = [scores]
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            # 降级：返回原始顺序
            scores = list(range(len(documents), 0, -1))
        
        # 创建结果
        results = []
        for i, (doc, score) in enumerate(zip(documents, scores)):
            results.append({
                'index': i,
                'text': doc,
                'score': float(score),
                'original_rank': i + 1
            })
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 添加新排名
        for new_rank, result in enumerate(results[:top_k], 1):
            result['new_rank'] = new_rank
        
        # 转换为RerankResult对象
        rerank_results = [
            RerankResult(
                text=r['text'],
                score=r['score'],
                original_rank=r['original_rank'],
                new_rank=r['new_rank']
            )
            for r in results[:top_k]
        ]
        
        logger.info(
            f"重排序完成: {len(documents)}条 → Top{top_k}, "
            f"最高分: {results[0]['score']:.3f}"
        )
        
        return rerank_results
    
    def rerank_with_metadata(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        text_field: str = 'content',
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        重排序带元数据的候选结果
        
        Args:
            query: 查询文本
            candidates: 候选结果列表（包含元数据）
            text_field: 文本字段名
            top_k: 返回数量
        
        Returns:
            重排序后的结果（保留元数据）
        """
        if not candidates:
            return []
        
        # 提取文本
        texts = [c.get(text_field, '') for c in candidates]
        
        # 重排序
        rerank_results = self.rerank(query, texts, top_k=top_k)
        
        # 匹配回原始候选
        final_results = []
        for rr in rerank_results:
            # 找到对应的原始候选
            for i, candidate in enumerate(candidates):
                if candidate.get(text_field, '') == rr.text:
                    result = candidate.copy()
                    result['rerank_score'] = rr.score
                    result['original_rank'] = rr.original_rank
                    result['new_rank'] = rr.new_rank
                    final_results.append(result)
                    break
        
        return final_results
    
    def is_available(self) -> bool:
        """检查重排序是否可用"""
        return RERANKER_AVAILABLE
