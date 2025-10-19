"""
质量验证器
负责评估知识库内容的质量，确保只有高质量内容进入知识库
"""
import logging
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """质量指标"""
    readability_score: float
    information_density: float
    structure_quality: float
    language_quality: float
    completeness_score: float
    overall_score: float


@dataclass
class QualityReport:
    """质量报告"""
    chunk_id: str
    overall_score: float
    metrics: QualityMetrics
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    passed_threshold: bool


class QualityValidator:
    """
    质量验证器
    
    功能：
    1. 多维度质量评估
    2. 可读性分析
    3. 信息密度计算
    4. 结构质量检查
    5. 语言质量评估
    """
    
    def __init__(
        self,
        min_score_threshold: float = 0.75,
        enable_readability_check: bool = True,
        enable_structure_check: bool = True,
        enable_language_check: bool = True
    ):
        """
        初始化质量验证器
        
        Args:
            min_score_threshold: 最低质量分数阈值
            enable_readability_check: 是否启用可读性检查
            enable_structure_check: 是否启用结构检查
            enable_language_check: 是否启用语言检查
        """
        self.min_score_threshold = min_score_threshold
        self.enable_readability_check = enable_readability_check
        self.enable_structure_check = enable_structure_check
        self.enable_language_check = enable_language_check
        
        # 初始化评估规则
        self.evaluation_rules = self._init_evaluation_rules()
        
        # 质量关键词
        self.quality_indicators = self._init_quality_indicators()
        
        # 低质量指标
        self.low_quality_indicators = self._init_low_quality_indicators()
        
        logger.info(
            f"质量验证器初始化完成: threshold={min_score_threshold}, "
            f"readability={enable_readability_check}, structure={enable_structure_check}"
        )
    
    def _init_evaluation_rules(self) -> List[Dict[str, Any]]:
        """初始化评估规则"""
        return [
            {
                'name': 'length_appropriateness',
                'weight': 0.15,
                'min_length': 20,
                'max_length': 1000,
                'optimal_range': (50, 300)
            },
            {
                'name': 'sentence_complexity',
                'weight': 0.20,
                'max_sentence_length': 50,
                'optimal_sentence_count': (2, 8)
            },
            {
                'name': 'vocabulary_diversity',
                'weight': 0.15,
                'min_unique_words': 5,
                'min_word_diversity': 0.3
            },
            {
                'name': 'information_density',
                'weight': 0.25,
                'min_keyword_density': 0.1,
                'max_redundancy': 0.3
            },
            {
                'name': 'structure_clarity',
                'weight': 0.25,
                'require_clear_structure': True,
                'prefer_numbered_lists': True
            }
        ]
    
    def _init_quality_indicators(self) -> Dict[str, List[str]]:
        """初始化质量指标"""
        return {
            'technical_terms': [
                '配置', '安装', '设置', '初始化', '启动', '运行',
                '故障', '错误', '异常', '问题', '解决', '排查',
                '性能', '优化', '提升', '改进', '增强', '升级',
                '安全', '权限', '认证', '授权', '加密', '验证'
            ],
            'action_words': [
                '点击', '选择', '输入', '设置', '配置', '安装',
                '查看', '检查', '确认', '验证', '测试', '调试',
                '创建', '删除', '修改', '更新', '保存', '导出',
                '导入', '同步', '备份', '恢复', '清理', '优化'
            ],
            'quality_markers': [
                '重要', '注意', '警告', '提示', '建议', '推荐',
                '必须', '需要', '应该', '可以', '可能', '建议',
                '正确', '错误', '有效', '无效', '成功', '失败'
            ]
        }
    
    def _init_low_quality_indicators(self) -> Dict[str, List[str]]:
        """初始化低质量指标"""
        return {
            'redundant_words': [
                '非常', '特别', '十分', '相当', '比较', '很', '超级',
                '然后', '接着', '接下来', '之后', '之后', '然后'
            ],
            'vague_terms': [
                '大概', '可能', '也许', '或许', '应该', '好像', '似乎',
                '差不多', '基本上', '一般来说', '通常情况下'
            ],
            'filler_words': [
                '嗯', '啊', '哦', '呃', '那个', '这个', '就是', '然后',
                '所以', '因为', '但是', '不过', '其实', '实际上'
            ],
            'poor_structure': [
                '没有标点', '句子过长', '结构混乱', '逻辑不清'
            ]
        }
    
    async def evaluate_chunk(
        self,
        chunk: Dict[str, Any]
    ) -> QualityReport:
        """
        评估知识块质量
        
        Args:
            chunk: 知识块数据
        
        Returns:
            质量报告
        """
        content = chunk.get('content', '')
        chunk_id = chunk.get('chunk_id', '')
        
        if not content or not content.strip():
            return QualityReport(
                chunk_id=chunk_id,
                overall_score=0.0,
                metrics=QualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                strengths=[],
                weaknesses=['内容为空'],
                recommendations=['提供有效内容'],
                passed_threshold=False
            )
        
        try:
            # 计算各项质量指标
            readability_score = await self._calculate_readability_score(content)
            information_density = await self._calculate_information_density(content)
            structure_quality = await self._calculate_structure_quality(content)
            language_quality = await self._calculate_language_quality(content)
            completeness_score = await self._calculate_completeness_score(content)
            
            # 计算综合分数
            overall_score = self._calculate_overall_score(
                readability_score, information_density, structure_quality,
                language_quality, completeness_score
            )
            
            # 创建质量指标对象
            metrics = QualityMetrics(
                readability_score=readability_score,
                information_density=information_density,
                structure_quality=structure_quality,
                language_quality=language_quality,
                completeness_score=completeness_score,
                overall_score=overall_score
            )
            
            # 分析优势和劣势
            strengths, weaknesses = self._analyze_strengths_weaknesses(
                content, metrics
            )
            
            # 生成改进建议
            recommendations = self._generate_recommendations(
                content, metrics, weaknesses
            )
            
            # 判断是否通过阈值
            passed_threshold = overall_score >= self.min_score_threshold
            
            report = QualityReport(
                chunk_id=chunk_id,
                overall_score=overall_score,
                metrics=metrics,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                passed_threshold=passed_threshold
            )
            
            logger.debug(
                f"质量评估完成: {chunk_id}, 分数={overall_score:.2f}, "
                f"通过={passed_threshold}"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"质量评估失败 {chunk_id}: {e}")
            return QualityReport(
                chunk_id=chunk_id,
                overall_score=0.0,
                metrics=QualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                strengths=[],
                weaknesses=[f'评估失败: {str(e)}'],
                recommendations=['修复内容格式'],
                passed_threshold=False
            )
    
    async def _calculate_readability_score(self, content: str) -> float:
        """计算可读性分数"""
        if not self.enable_readability_check:
            return 1.0
        
        score = 0.0
        
        # 1. 句子长度合理性 (30%)
        sentence_score = self._calculate_sentence_length_score(content)
        score += sentence_score * 0.3
        
        # 2. 词汇复杂度 (25%)
        vocabulary_score = self._calculate_vocabulary_complexity_score(content)
        score += vocabulary_score * 0.25
        
        # 3. 段落结构 (25%)
        paragraph_score = self._calculate_paragraph_structure_score(content)
        score += paragraph_score * 0.25
        
        # 4. 标点符号使用 (20%)
        punctuation_score = self._calculate_punctuation_score(content)
        score += punctuation_score * 0.2
        
        return min(score, 1.0)
    
    async def _calculate_information_density(self, content: str) -> float:
        """计算信息密度"""
        if not content:
            return 0.0
        
        # 1. 关键词密度
        keyword_density = self._calculate_keyword_density(content)
        
        # 2. 信息完整性
        information_completeness = self._calculate_information_completeness(content)
        
        # 3. 冗余度（越低越好）
        redundancy_score = 1.0 - self._calculate_redundancy_score(content)
        
        # 综合计算
        density_score = (keyword_density * 0.4 + 
                        information_completeness * 0.4 + 
                        redundancy_score * 0.2)
        
        return min(density_score, 1.0)
    
    async def _calculate_structure_quality(self, content: str) -> float:
        """计算结构质量"""
        if not self.enable_structure_check:
            return 1.0
        
        score = 0.0
        
        # 1. 逻辑结构 (40%)
        logical_structure = self._calculate_logical_structure_score(content)
        score += logical_structure * 0.4
        
        # 2. 格式规范性 (30%)
        format_score = self._calculate_format_score(content)
        score += format_score * 0.3
        
        # 3. 层次清晰度 (30%)
        hierarchy_score = self._calculate_hierarchy_score(content)
        score += hierarchy_score * 0.3
        
        return min(score, 1.0)
    
    async def _calculate_language_quality(self, content: str) -> float:
        """计算语言质量"""
        if not self.enable_language_check:
            return 1.0
        
        score = 1.0
        
        # 1. 语法正确性
        grammar_errors = self._count_grammar_errors(content)
        grammar_score = max(0.0, 1.0 - grammar_errors * 0.1)
        score *= grammar_score
        
        # 2. 用词准确性
        word_accuracy = self._calculate_word_accuracy_score(content)
        score *= word_accuracy
        
        # 3. 表达清晰度
        clarity_score = self._calculate_clarity_score(content)
        score *= clarity_score
        
        return min(score, 1.0)
    
    async def _calculate_completeness_score(self, content: str) -> float:
        """计算完整性分数"""
        if not content:
            return 0.0
        
        score = 0.0
        
        # 1. 信息完整性 (50%)
        info_completeness = self._calculate_information_completeness(content)
        score += info_completeness * 0.5
        
        # 2. 上下文完整性 (30%)
        context_completeness = self._calculate_context_completeness(content)
        score += context_completeness * 0.3
        
        # 3. 逻辑完整性 (20%)
        logic_completeness = self._calculate_logic_completeness(content)
        score += logic_completeness * 0.2
        
        return min(score, 1.0)
    
    def _calculate_sentence_length_score(self, content: str) -> float:
        """计算句子长度分数"""
        sentences = re.split(r'[。！？]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # 计算平均句长
        avg_length = sum(len(s) for s in sentences) / len(sentences)
        
        # 理想句长：20-40字符
        if 20 <= avg_length <= 40:
            return 1.0
        elif 15 <= avg_length <= 50:
            return 0.8
        elif 10 <= avg_length <= 60:
            return 0.6
        else:
            return 0.4
    
    def _calculate_vocabulary_complexity_score(self, content: str) -> float:
        """计算词汇复杂度分数"""
        words = re.findall(r'\b\w+\b', content)
        if not words:
            return 0.0
        
        # 计算词汇多样性
        unique_words = set(words)
        diversity = len(unique_words) / len(words)
        
        # 理想多样性：0.6-0.8
        if 0.6 <= diversity <= 0.8:
            return 1.0
        elif 0.5 <= diversity <= 0.9:
            return 0.8
        else:
            return 0.6
    
    def _calculate_paragraph_structure_score(self, content: str) -> float:
        """计算段落结构分数"""
        paragraphs = content.split('\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if not paragraphs:
            return 0.0
        
        score = 0.0
        
        # 段落长度合理性
        for para in paragraphs:
            if 50 <= len(para) <= 200:
                score += 1.0
            elif 30 <= len(para) <= 300:
                score += 0.7
            else:
                score += 0.4
        
        return score / len(paragraphs)
    
    def _calculate_punctuation_score(self, content: str) -> float:
        """计算标点符号使用分数"""
        # 检查标点符号使用是否合理
        punctuation_count = len(re.findall(r'[。！？，；：]', content))
        sentence_count = len(re.findall(r'[。！？]', content))
        
        if sentence_count == 0:
            return 0.0
        
        # 理想标点比例：每句2-4个标点
        ideal_ratio = 3.0
        actual_ratio = punctuation_count / sentence_count
        
        if 2.0 <= actual_ratio <= 4.0:
            return 1.0
        elif 1.0 <= actual_ratio <= 5.0:
            return 0.8
        else:
            return 0.6
    
    def _calculate_keyword_density(self, content: str) -> float:
        """计算关键词密度"""
        total_words = len(re.findall(r'\b\w+\b', content))
        if total_words == 0:
            return 0.0
        
        keyword_count = 0
        for category, keywords in self.quality_indicators.items():
            for keyword in keywords:
                keyword_count += content.count(keyword)
        
        return min(keyword_count / total_words, 1.0)
    
    def _calculate_information_completeness(self, content: str) -> float:
        """计算信息完整性"""
        completeness_indicators = ['什么', '如何', '为什么', '哪里', '何时', '谁']
        score = 0.0
        
        for indicator in completeness_indicators:
            if indicator in content:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_redundancy_score(self, content: str) -> float:
        """计算冗余度分数"""
        words = content.split()
        if not words:
            return 0.0
        
        # 检查重复词汇
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 计算重复率
        total_words = len(words)
        repeated_words = sum(count for count in word_freq.values() if count > 1)
        redundancy_ratio = repeated_words / total_words
        
        return min(redundancy_ratio, 1.0)
    
    def _calculate_logical_structure_score(self, content: str) -> float:
        """计算逻辑结构分数"""
        score = 0.0
        
        # 检查是否有明确的逻辑结构
        if re.search(r'\d+[\.、]', content):  # 编号列表
            score += 0.3
        if re.search(r'[首先|其次|最后|然后]', content):  # 顺序词
            score += 0.3
        if re.search(r'[因为|所以|但是|然而]', content):  # 逻辑词
            score += 0.2
        if re.search(r'[总结|结论|要点]', content):  # 总结词
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_format_score(self, content: str) -> float:
        """计算格式分数"""
        score = 1.0
        
        # 检查格式问题
        if re.search(r'\s{3,}', content):  # 多余空白
            score -= 0.2
        if re.search(r'[^\w\s\u4e00-\u9fff.,!?;:()\-]', content):  # 特殊字符
            score -= 0.1
        if not re.search(r'[。！？]', content):  # 缺少句号
            score -= 0.3
        
        return max(score, 0.0)
    
    def _calculate_hierarchy_score(self, content: str) -> float:
        """计算层次清晰度分数"""
        score = 0.0
        
        # 检查层次结构
        if re.search(r'^#+\s', content, re.MULTILINE):  # Markdown标题
            score += 0.4
        if re.search(r'^\d+[\.、]', content, re.MULTILINE):  # 编号
            score += 0.3
        if re.search(r'^[•·▪▫]\s', content, re.MULTILINE):  # 列表
            score += 0.3
        
        return min(score, 1.0)
    
    def _count_grammar_errors(self, content: str) -> int:
        """统计语法错误数量"""
        error_count = 0
        
        # 检查常见语法错误
        if re.search(r'[，。]+\s*[，。]+', content):  # 重复标点
            error_count += 1
        if re.search(r'[a-zA-Z]+[，。][a-zA-Z]+', content):  # 中英文标点混用
            error_count += 1
        if re.search(r'\s+[，。！？]', content):  # 标点前有空格
            error_count += 1
        
        return error_count
    
    def _calculate_word_accuracy_score(self, content: str) -> float:
        """计算用词准确性分数"""
        score = 1.0
        
        # 检查用词问题
        for category, words in self.low_quality_indicators.items():
            for word in words:
                if word in content:
                    score -= 0.05  # 每个问题词汇扣分
        
        return max(score, 0.0)
    
    def _calculate_clarity_score(self, content: str) -> float:
        """计算表达清晰度分数"""
        score = 1.0
        
        # 检查表达问题
        vague_count = sum(content.count(word) for word in self.low_quality_indicators['vague_terms'])
        if vague_count > 2:
            score -= 0.2
        
        filler_count = sum(content.count(word) for word in self.low_quality_indicators['filler_words'])
        if filler_count > 1:
            score -= 0.1
        
        return max(score, 0.0)
    
    def _calculate_context_completeness(self, content: str) -> float:
        """计算上下文完整性"""
        # 检查是否有足够的上下文信息
        context_indicators = ['在', '当', '如果', '由于', '根据', '按照']
        context_count = sum(content.count(indicator) for indicator in context_indicators)
        
        if context_count >= 2:
            return 1.0
        elif context_count >= 1:
            return 0.7
        else:
            return 0.5
    
    def _calculate_logic_completeness(self, content: str) -> float:
        """计算逻辑完整性"""
        # 检查逻辑完整性
        logic_indicators = ['因为', '所以', '但是', '然而', '因此', '所以']
        logic_count = sum(content.count(indicator) for indicator in logic_indicators)
        
        if logic_count >= 1:
            return 1.0
        else:
            return 0.6
    
    def _calculate_overall_score(
        self,
        readability: float,
        information_density: float,
        structure_quality: float,
        language_quality: float,
        completeness_score: float
    ) -> float:
        """计算综合分数"""
        weights = [0.2, 0.25, 0.2, 0.2, 0.15]
        scores = [readability, information_density, structure_quality, language_quality, completeness_score]
        
        weighted_score = sum(w * s for w, s in zip(weights, scores))
        return min(weighted_score, 1.0)
    
    def _analyze_strengths_weaknesses(
        self,
        content: str,
        metrics: QualityMetrics
    ) -> Tuple[List[str], List[str]]:
        """分析优势和劣势"""
        strengths = []
        weaknesses = []
        
        # 分析各项指标
        if metrics.readability_score >= 0.8:
            strengths.append("可读性良好")
        elif metrics.readability_score < 0.6:
            weaknesses.append("可读性较差")
        
        if metrics.information_density >= 0.8:
            strengths.append("信息密度高")
        elif metrics.information_density < 0.6:
            weaknesses.append("信息密度不足")
        
        if metrics.structure_quality >= 0.8:
            strengths.append("结构清晰")
        elif metrics.structure_quality < 0.6:
            weaknesses.append("结构混乱")
        
        if metrics.language_quality >= 0.8:
            strengths.append("语言规范")
        elif metrics.language_quality < 0.6:
            weaknesses.append("语言质量不佳")
        
        if metrics.completeness_score >= 0.8:
            strengths.append("信息完整")
        elif metrics.completeness_score < 0.6:
            weaknesses.append("信息不完整")
        
        return strengths, weaknesses
    
    def _generate_recommendations(
        self,
        content: str,
        metrics: QualityMetrics,
        weaknesses: List[str]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if "可读性较差" in weaknesses:
            recommendations.append("简化句子结构，控制句长在20-40字符")
        
        if "信息密度不足" in weaknesses:
            recommendations.append("增加关键词密度，减少冗余信息")
        
        if "结构混乱" in weaknesses:
            recommendations.append("使用编号列表或分段来改善结构")
        
        if "语言质量不佳" in weaknesses:
            recommendations.append("检查语法错误，使用更准确的词汇")
        
        if "信息不完整" in weaknesses:
            recommendations.append("补充必要的上下文信息和逻辑关系")
        
        # 基于具体指标的改进建议
        if metrics.readability_score < 0.7:
            recommendations.append("考虑使用更简洁的表达方式")
        
        if metrics.information_density < 0.7:
            recommendations.append("提取核心信息，去除无关内容")
        
        return recommendations
    
    async def batch_evaluate_chunks(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[QualityReport]:
        """批量评估知识块质量"""
        tasks = [self.evaluate_chunk(chunk) for chunk in chunks]
        reports = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        valid_reports = []
        for i, report in enumerate(reports):
            if isinstance(report, Exception):
                logger.error(f"批量评估第{i}个知识块失败: {report}")
                # 创建默认的低质量报告
                default_report = QualityReport(
                    chunk_id=chunks[i].get('chunk_id', f'chunk_{i}'),
                    overall_score=0.0,
                    metrics=QualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                    strengths=[],
                    weaknesses=['评估失败'],
                    recommendations=['修复内容格式'],
                    passed_threshold=False
                )
                valid_reports.append(default_report)
            else:
                valid_reports.append(report)
        
        return valid_reports
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        return {
            'min_score_threshold': self.min_score_threshold,
            'enable_readability_check': self.enable_readability_check,
            'enable_structure_check': self.enable_structure_check,
            'enable_language_check': self.enable_language_check,
            'evaluation_rules_count': len(self.evaluation_rules),
            'quality_indicators_count': sum(len(indicators) for indicators in self.quality_indicators.values()),
            'low_quality_indicators_count': sum(len(indicators) for indicators in self.low_quality_indicators.values())
        }
