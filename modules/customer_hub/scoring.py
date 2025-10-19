"""
置信打分引擎
基于关键词、文件类型、工作时间、知识库匹配的综合打分
"""
import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from .types import Signal, Bucket, ScoringRules

logger = logging.getLogger(__name__)


class ScoringEngine:
    """打分引擎"""
    
    def __init__(self, rules: Optional[ScoringRules] = None):
        """
        初始化打分引擎
        
        Args:
            rules: 打分规则,如果为None则使用默认规则
        """
        self.rules = rules or ScoringRules()
        logger.info(
            f"打分引擎初始化: 白名单阈值={self.rules.white_promotion_threshold}, "
            f"灰名单下限={self.rules.gray_lower}"
        )
    
    def score_message(
        self,
        text: str,
        file_types: List[str],
        timestamp: datetime,
        kb_matched: bool = False
    ) -> Tuple[Signal, Dict[str, any]]:
        """
        对消息进行综合打分
        
        Args:
            text: 消息文本
            file_types: 文件类型列表
            timestamp: 消息时间戳
            kb_matched: 是否匹配到知识库
        
        Returns:
            (Signal对象, 详细信息字典)
        """
        # 1. 黑名单检查
        if self._check_blacklist(text):
            logger.debug(f"命中黑名单关键词,总分: 0")
            return self._create_black_signal(text, file_types)
        
        # 2. 关键词打分
        keyword_score, keyword_hits = self._score_keywords(text)
        
        # 3. 文件类型打分
        file_score = self._score_files(file_types)
        
        # 4. 工作时间打分
        worktime_score = self._score_worktime(timestamp)
        
        # 5. 知识库匹配打分
        kb_match_score = self.rules.kb_match_weight if kb_matched else 0
        
        # 6. 计算总分(上限100)
        total_score = min(100, keyword_score + file_score + worktime_score + kb_match_score)
        
        # 7. 判定白/灰/黑
        bucket = self._determine_bucket(total_score)
        
        # 8. 创建Signal对象
        signal = Signal(
            id="",  # 将在数据库层生成UUID
            thread_id="",  # 将在调用时设置
            keyword_hits=keyword_hits,
            file_types=file_types,
            worktime_score=worktime_score,
            kb_match_score=kb_match_score,
            total_score=total_score,
            bucket=bucket
        )
        
        # 详细信息
        details = {
            'keyword_score': keyword_score,
            'file_score': file_score,
            'worktime_score': worktime_score,
            'kb_match_score': kb_match_score,
            'total_score': total_score,
            'bucket': bucket.value,
            'timestamp': timestamp.isoformat()
        }
        
        logger.info(
            f"打分完成: 总分={total_score}, 桶={bucket.value}, "
            f"关键词={keyword_score}, 文件={file_score}, "
            f"工时={worktime_score}, KB={kb_match_score}"
        )
        
        return signal, details
    
    def _check_blacklist(self, text: str) -> bool:
        """
        检查是否命中黑名单关键词
        
        Args:
            text: 消息文本
        
        Returns:
            True=黑名单, False=通过
        """
        text_lower = text.lower()
        for keyword in self.rules.blacklist_keywords:
            if keyword in text_lower:
                logger.debug(f"命中黑名单关键词: {keyword}")
                return True
        return False
    
    def _score_keywords(self, text: str) -> Tuple[int, Dict[str, int]]:
        """
        关键词打分
        
        策略:
        - 每个关键词命中一次 +6分
        - 每个关键词最多贡献20分
        - 总分无上限(但会被总分100限制)
        
        Args:
            text: 消息文本
        
        Returns:
            (总得分, 命中次数字典)
        """
        keyword_score = 0
        keyword_hits = {}
        
        # 遍历所有关键词组
        for group_name, keywords in self.rules.keywords.items():
            for kw in keywords:
                # 正则匹配(忽略大小写)
                pattern = re.compile(re.escape(kw), re.IGNORECASE)
                matches = pattern.findall(text)
                hits = len(matches)
                
                if hits > 0:
                    # 每个关键词最多贡献20分
                    kw_score = min(20, hits * 6)
                    keyword_score += kw_score
                    keyword_hits[kw] = hits
                    
                    logger.debug(
                        f"关键词 '{kw}' 命中 {hits} 次, "
                        f"得分 {kw_score} (组: {group_name})"
                    )
        
        return keyword_score, keyword_hits
    
    def _score_files(self, file_types: List[str]) -> int:
        """
        文件类型打分
        
        Args:
            file_types: 文件类型列表 ['pdf', 'xls', ...]
        
        Returns:
            总得分
        """
        file_score = 0
        
        for ft in file_types:
            weight = self.rules.file_weights.get(ft.lower(), 0)
            file_score += weight
            
            if weight > 0:
                logger.debug(f"文件类型 '{ft}' 得分 {weight}")
        
        return file_score
    
    def _score_worktime(self, timestamp: datetime) -> int:
        """
        工作时间打分
        
        策略:
        - 工作时间内发送: 工作日 +12分, 周末 +4分
        - 非工作时间: 0分
        
        Args:
            timestamp: 消息时间戳
        
        Returns:
            得分
        """
        hour = timestamp.hour
        weekday = timestamp.weekday()  # 0=周一, 6=周日
        
        # 判断是否在工作时间内
        is_work_hour = (
            self.rules.work_start_hour <= hour <= self.rules.work_end_hour
        )
        
        # 判断是否周末
        is_weekend = weekday in [5, 6]  # 周六、周日
        
        if is_work_hour:
            if is_weekend:
                score = self.rules.weekend_bonus
                logger.debug(f"工作时间(周末) {hour}时, 得分 {score}")
            else:
                score = self.rules.weekday_bonus
                logger.debug(f"工作时间(工作日) {hour}时, 得分 {score}")
            return score
        else:
            logger.debug(f"非工作时间 {hour}时, 得分 0")
            return 0
    
    def _determine_bucket(self, total_score: int) -> Bucket:
        """
        根据总分判定白/灰/黑
        
        规则:
        - >= white_promotion_threshold (80) -> WHITE
        - >= gray_lower (60) -> GRAY
        - < gray_lower -> BLACK
        
        Args:
            total_score: 总分 0-100
        
        Returns:
            Bucket枚举
        """
        if total_score >= self.rules.white_promotion_threshold:
            return Bucket.WHITE
        elif total_score >= self.rules.gray_lower:
            return Bucket.GRAY
        else:
            return Bucket.BLACK
    
    def _create_black_signal(
        self, 
        text: str, 
        file_types: List[str]
    ) -> Tuple[Signal, Dict[str, any]]:
        """
        创建黑名单信号(总分0)
        
        Args:
            text: 消息文本
            file_types: 文件类型列表
        
        Returns:
            (Signal对象, 详细信息字典)
        """
        signal = Signal(
            id="",
            thread_id="",
            keyword_hits={},
            file_types=file_types,
            worktime_score=0,
            kb_match_score=0,
            total_score=0,
            bucket=Bucket.BLACK
        )
        
        details = {
            'keyword_score': 0,
            'file_score': 0,
            'worktime_score': 0,
            'kb_match_score': 0,
            'total_score': 0,
            'bucket': Bucket.BLACK.value,
            'reason': 'blacklist_keyword'
        }
        
        return signal, details
    
    def identify_trigger_type(self, keyword_hits: Dict[str, int]) -> Optional[str]:
        """
        根据关键词命中情况识别触发类型
        
        Args:
            keyword_hits: 关键词命中次数字典
        
        Returns:
            触发类型: '售前' | '售后' | '客户开发' | None
        """
        # 统计各组命中情况
        pre_hits = sum(
            count for kw, count in keyword_hits.items()
            if kw in self.rules.keywords.get('pre', [])
        )
        
        post_hits = sum(
            count for kw, count in keyword_hits.items()
            if kw in self.rules.keywords.get('post', [])
        )
        
        bizdev_hits = sum(
            count for kw, count in keyword_hits.items()
            if kw in self.rules.keywords.get('bizdev', [])
        )
        
        # 取命中最多的组
        max_hits = max(pre_hits, post_hits, bizdev_hits)
        
        if max_hits == 0:
            return None
        
        if pre_hits == max_hits:
            return '售前'
        elif post_hits == max_hits:
            return '售后'
        elif bizdev_hits == max_hits:
            return '客户开发'
        
        return None


# ==================== 默认实例 ====================

default_scoring_engine = ScoringEngine()

