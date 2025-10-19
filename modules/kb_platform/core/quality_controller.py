"""
质量控制器 - 极致质量保证
负责严格的质量控制、问题检测、反馈生成和智能修复
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """质量问题"""
    issue_id: str
    issue_type: str  # missing_info, duplicate, low_quality, format_error, incomplete
    severity: str  # critical, high, medium, low
    description: str
    affected_chunks: List[str]
    auto_fixable: bool
    fix_suggestion: str
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class QualityFeedback:
    """质量反馈报告"""
    document_id: str
    overall_score: float
    passed: bool
    issues: List[QualityIssue]
    warnings: List[str]
    fix_suggestions: List[str]
    auto_fix_available: bool
    manual_review_required: bool
    feedback_message: str


@dataclass
class AutoFixResult:
    """自动修复结果"""
    success: bool
    original_content: str
    fixed_content: str
    fix_method: str  # rule_based, llm_assisted, hybrid
    confidence: float
    changes_made: List[str]
    requires_human_review: bool


class QualityController:
    """
    质量控制器
    
    功能：
    1. 严格质量检测
    2. 智能问题识别
    3. 生成详细反馈
    4. 大模型辅助修复
    5. 动态质量标准
    """
    
    def __init__(
        self,
        threshold: float = 0.75,
        strict_mode: bool = True,
        enable_auto_fix: bool = True,
        enable_llm_fix: bool = True,
        ai_gateway=None
    ):
        """
        初始化质量控制器
        
        Args:
            threshold: 质量阈值
            strict_mode: 严格模式（更严格的检查）
            enable_auto_fix: 是否启用自动修复
            enable_llm_fix: 是否启用大模型修复
            ai_gateway: AI网关（用于大模型修复）
        """
        self.threshold = threshold
        self.strict_mode = strict_mode
        self.enable_auto_fix = enable_auto_fix
        self.enable_llm_fix = enable_llm_fix
        self.ai_gateway = ai_gateway
        
        # 初始化检测规则
        self.detection_rules = self._init_detection_rules()
        
        # 关键信息检测模式
        self.key_info_patterns = self._init_key_info_patterns()
        
        # 修复策略
        self.fix_strategies = self._init_fix_strategies()
        
        logger.info(
            f"质量控制器初始化完成: strict={strict_mode}, "
            f"auto_fix={enable_auto_fix}, llm_fix={enable_llm_fix}"
        )
    
    def _init_detection_rules(self) -> List[Dict[str, Any]]:
        """初始化检测规则"""
        return [
            {
                'rule_id': 'missing_key_info',
                'name': '缺失关键信息',
                'severity': 'critical',
                'description': '文档缺少必要的关键信息',
                'auto_fixable': True
            },
            {
                'rule_id': 'incomplete_content',
                'name': '内容不完整',
                'severity': 'high',
                'description': '文档内容不完整或被截断',
                'auto_fixable': True
            },
            {
                'rule_id': 'poor_structure',
                'name': '结构混乱',
                'severity': 'medium',
                'description': '文档结构不清晰或缺少层次',
                'auto_fixable': True
            },
            {
                'rule_id': 'duplicate_content',
                'name': '重复内容',
                'severity': 'high',
                'description': '与已有文档重复',
                'auto_fixable': False
            },
            {
                'rule_id': 'low_information_density',
                'name': '信息密度低',
                'severity': 'medium',
                'description': '有效信息太少，充斥冗余内容',
                'auto_fixable': True
            },
            {
                'rule_id': 'inconsistent_format',
                'name': '格式不一致',
                'severity': 'low',
                'description': '文档格式不符合标准',
                'auto_fixable': True
            }
        ]
    
    def _init_key_info_patterns(self) -> Dict[str, List[str]]:
        """初始化关键信息检测模式"""
        return {
            '技术文档': [
                '功能描述', '使用方法', '参数说明', '示例代码', '注意事项'
            ],
            '产品手册': [
                '产品名称', '技术规格', '安装步骤', '使用说明', '维护保养'
            ],
            '故障排查': [
                '问题描述', '故障现象', '原因分析', '解决方案', '预防措施'
            ],
            '操作指南': [
                '操作步骤', '前置条件', '操作说明', '预期结果', '异常处理'
            ]
        }
    
    def _init_fix_strategies(self) -> Dict[str, Dict[str, Any]]:
        """初始化修复策略"""
        return {
            'missing_key_info': {
                'priority': 1,
                'method': 'llm_assisted',
                'prompt_template': '文档缺少{missing_fields}，请根据上下文补充这些信息'
            },
            'incomplete_content': {
                'priority': 2,
                'method': 'llm_assisted',
                'prompt_template': '文档内容不完整，请补充完整的内容'
            },
            'poor_structure': {
                'priority': 3,
                'method': 'rule_based',
                'actions': ['add_headings', 'organize_sections', 'add_numbering']
            },
            'low_information_density': {
                'priority': 4,
                'method': 'llm_assisted',
                'prompt_template': '提取核心信息，去除冗余内容，保持简洁专业'
            },
            'inconsistent_format': {
                'priority': 5,
                'method': 'rule_based',
                'actions': ['standardize_format', 'fix_punctuation', 'normalize_spacing']
            }
        }
    
    async def inspect_document(
        self,
        document: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        category: str = 'general'
    ) -> QualityFeedback:
        """
        深度检查文档质量
        
        Args:
            document: 文档元数据
            chunks: 文档分块列表
            category: 文档类别
        
        Returns:
            详细的质量反馈报告
        """
        logger.info(f"开始深度质量检查: {document.get('title', 'unknown')}")
        
        issues = []
        warnings = []
        fix_suggestions = []
        
        # 1. 检测缺失关键信息
        missing_info_issues = await self._detect_missing_key_info(chunks, category)
        issues.extend(missing_info_issues)
        
        # 2. 检测内容完整性
        completeness_issues = await self._detect_incomplete_content(chunks)
        issues.extend(completeness_issues)
        
        # 3. 检测结构质量
        structure_issues = await self._detect_structure_problems(chunks)
        issues.extend(structure_issues)
        
        # 4. 检测信息密度
        density_issues = await self._detect_low_density(chunks)
        issues.extend(density_issues)
        
        # 5. 检测格式一致性
        format_issues = await self._detect_format_inconsistency(chunks)
        issues.extend(format_issues)
        
        # 计算综合分数
        overall_score = self._calculate_overall_score(issues, chunks)
        
        # 判断是否通过
        passed = overall_score >= self.threshold and not any(
            issue.severity == 'critical' for issue in issues
        )
        
        # 生成修复建议
        for issue in issues:
            if issue.auto_fixable:
                fix_suggestions.append(f"{issue.description} - 可自动修复")
            else:
                fix_suggestions.append(f"{issue.description} - 需人工处理")
        
        # 判断是否有自动修复可用
        auto_fix_available = any(issue.auto_fixable for issue in issues)
        
        # 判断是否需要人工审核
        manual_review_required = any(
            issue.severity in ['critical', 'high'] for issue in issues
        )
        
        # 生成反馈消息
        feedback_message = self._generate_feedback_message(
            overall_score, issues, passed
        )
        
        feedback = QualityFeedback(
            document_id=document.get('document_id', ''),
            overall_score=overall_score,
            passed=passed,
            issues=issues,
            warnings=warnings,
            fix_suggestions=fix_suggestions,
            auto_fix_available=auto_fix_available,
            manual_review_required=manual_review_required,
            feedback_message=feedback_message
        )
        
        logger.info(
            f"质量检查完成: score={overall_score:.2f}, "
            f"issues={len(issues)}, passed={passed}"
        )
        
        return feedback
    
    async def auto_fix_issues(
        self,
        chunks: List[Dict[str, Any]],
        issues: List[QualityIssue]
    ) -> List[AutoFixResult]:
        """
        自动修复质量问题
        
        Args:
            chunks: 文档分块
            issues: 质量问题列表
        
        Returns:
            修复结果列表
        """
        if not self.enable_auto_fix:
            logger.warning("自动修复未启用")
            return []
        
        fix_results = []
        
        # 按优先级排序问题
        sorted_issues = sorted(
            [i for i in issues if i.auto_fixable],
            key=lambda x: self.fix_strategies.get(x.issue_type, {}).get('priority', 99)
        )
        
        for issue in sorted_issues:
            try:
                # 获取修复策略
                strategy = self.fix_strategies.get(issue.issue_type)
                if not strategy:
                    continue
                
                # 根据修复方法选择修复函数
                if strategy['method'] == 'llm_assisted' and self.enable_llm_fix:
                    fix_result = await self._llm_assisted_fix(chunks, issue, strategy)
                elif strategy['method'] == 'rule_based':
                    fix_result = await self._rule_based_fix(chunks, issue, strategy)
                elif strategy['method'] == 'hybrid':
                    fix_result = await self._hybrid_fix(chunks, issue, strategy)
                else:
                    continue
                
                if fix_result:
                    fix_results.append(fix_result)
                
            except Exception as e:
                logger.error(f"修复问题失败 {issue.issue_id}: {e}")
        
        logger.info(f"自动修复完成: {len(fix_results)} 个问题已修复")
        
        return fix_results
    
    async def _llm_assisted_fix(
        self,
        chunks: List[Dict[str, Any]],
        issue: QualityIssue,
        strategy: Dict[str, Any]
    ) -> Optional[AutoFixResult]:
        """大模型辅助修复"""
        if not self.ai_gateway:
            logger.warning("AI网关未配置，无法使用大模型修复")
            return None
        
        # 找到受影响的chunk
        affected_chunk = None
        for chunk in chunks:
            if chunk.get('chunk_id') in issue.affected_chunks:
                affected_chunk = chunk
                break
        
        if not affected_chunk:
            return None
        
        original_content = affected_chunk.get('content', '')
        
        # 构建修复提示词
        prompt_template = strategy.get('prompt_template', '')
        
        # 根据问题类型定制提示词
        if issue.issue_type == 'missing_key_info':
            missing_fields = issue.description.split('缺少')[1] if '缺少' in issue.description else '关键信息'
            prompt = f"""请分析并补充以下文档内容：

原始内容：
{original_content}

问题：缺少{missing_fields}

要求：
1. 根据上下文推断并补充缺失的{missing_fields}
2. 保持原有内容的准确性
3. 补充的内容要专业、准确
4. 保持文档结构清晰

请输出完整的修复后内容。"""
        
        elif issue.issue_type == 'incomplete_content':
            prompt = f"""请补充完整以下不完整的文档内容：

原始内容：
{original_content}

问题：{issue.description}

要求：
1. 分析内容缺失的部分
2. 根据上下文补充完整
3. 保持逻辑连贯
4. 确保信息准确

请输出完整的内容。"""
        
        elif issue.issue_type == 'low_information_density':
            prompt = f"""请优化以下内容的信息密度：

原始内容：
{original_content}

问题：{issue.description}

要求：
1. 提取核心信息
2. 去除冗余和废话
3. 保持专业性
4. 简洁明了

请输出优化后的内容。"""
        
        else:
            prompt = prompt_template.format(content=original_content)
        
        try:
            # 调用大模型
            response = await self.ai_gateway.generate(
                prompt=prompt,
                temperature=0.3,  # 降低温度，更保守
                max_tokens=2000
            )
            
            fixed_content = response.get('content', '')
            
            if not fixed_content or fixed_content == original_content:
                return None
            
            # 评估修复质量
            confidence = await self._evaluate_fix_quality(
                original_content, fixed_content, issue
            )
            
            # 记录修改
            changes_made = [
                f"修复类型: {issue.issue_type}",
                f"修复方法: LLM辅助",
                f"置信度: {confidence:.2f}"
            ]
            
            return AutoFixResult(
                success=True,
                original_content=original_content,
                fixed_content=fixed_content,
                fix_method='llm_assisted',
                confidence=confidence,
                changes_made=changes_made,
                requires_human_review=confidence < 0.8
            )
            
        except Exception as e:
            logger.error(f"大模型修复失败: {e}")
            return None
    
    async def _rule_based_fix(
        self,
        chunks: List[Dict[str, Any]],
        issue: QualityIssue,
        strategy: Dict[str, Any]
    ) -> Optional[AutoFixResult]:
        """基于规则的修复"""
        affected_chunk = None
        for chunk in chunks:
            if chunk.get('chunk_id') in issue.affected_chunks:
                affected_chunk = chunk
                break
        
        if not affected_chunk:
            return None
        
        original_content = affected_chunk.get('content', '')
        fixed_content = original_content
        changes_made = []
        
        # 执行规则修复动作
        actions = strategy.get('actions', [])
        
        for action in actions:
            if action == 'add_headings':
                fixed_content, changed = self._add_headings(fixed_content)
                if changed:
                    changes_made.append("添加标题")
            
            elif action == 'organize_sections':
                fixed_content, changed = self._organize_sections(fixed_content)
                if changed:
                    changes_made.append("组织章节")
            
            elif action == 'add_numbering':
                fixed_content, changed = self._add_numbering(fixed_content)
                if changed:
                    changes_made.append("添加编号")
            
            elif action == 'standardize_format':
                fixed_content, changed = self._standardize_format(fixed_content)
                if changed:
                    changes_made.append("标准化格式")
            
            elif action == 'fix_punctuation':
                fixed_content, changed = self._fix_punctuation(fixed_content)
                if changed:
                    changes_made.append("修复标点")
            
            elif action == 'normalize_spacing':
                fixed_content, changed = self._normalize_spacing(fixed_content)
                if changed:
                    changes_made.append("规范化空格")
        
        if fixed_content == original_content:
            return None
        
        return AutoFixResult(
            success=True,
            original_content=original_content,
            fixed_content=fixed_content,
            fix_method='rule_based',
            confidence=0.95,  # 规则修复置信度较高
            changes_made=changes_made,
            requires_human_review=False
        )
    
    async def _hybrid_fix(
        self,
        chunks: List[Dict[str, Any]],
        issue: QualityIssue,
        strategy: Dict[str, Any]
    ) -> Optional[AutoFixResult]:
        """混合修复（规则+大模型）"""
        # 先使用规则修复
        rule_result = await self._rule_based_fix(chunks, issue, strategy)
        
        if not rule_result:
            return None
        
        # 如果规则修复效果不理想，使用大模型增强
        if rule_result.confidence < 0.8 and self.enable_llm_fix:
            llm_result = await self._llm_assisted_fix(chunks, issue, strategy)
            if llm_result and llm_result.confidence > rule_result.confidence:
                llm_result.fix_method = 'hybrid'
                llm_result.changes_made.extend(rule_result.changes_made)
                return llm_result
        
        return rule_result
    
    async def _detect_missing_key_info(
        self,
        chunks: List[Dict[str, Any]],
        category: str
    ) -> List[QualityIssue]:
        """检测缺失的关键信息"""
        issues = []
        
        # 获取该类别应有的关键信息
        required_fields = self.key_info_patterns.get(category, [])
        if not required_fields:
            return issues
        
        # 合并所有chunk内容
        full_content = '\n'.join(chunk.get('content', '') for chunk in chunks)
        
        # 检测缺失字段
        missing_fields = []
        for field in required_fields:
            # 简化检测：检查关键词是否出现
            if field not in full_content and not any(
                keyword in full_content for keyword in field.split()
            ):
                missing_fields.append(field)
        
        if missing_fields:
            issue = QualityIssue(
                issue_id=f"missing_info_{category}",
                issue_type='missing_key_info',
                severity='critical' if len(missing_fields) > 2 else 'high',
                description=f"缺少关键信息: {', '.join(missing_fields)}",
                affected_chunks=[chunk.get('chunk_id', '') for chunk in chunks],
                auto_fixable=True,
                fix_suggestion=f"建议补充: {', '.join(missing_fields)}"
            )
            issues.append(issue)
        
        return issues
    
    async def _detect_incomplete_content(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[QualityIssue]:
        """检测不完整内容"""
        issues = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            
            # 检查是否被截断
            is_truncated = (
                content.endswith('...') or
                content.endswith('。。。') or
                len(content) < 50 or
                not content.strip()
            )
            
            if is_truncated:
                issue = QualityIssue(
                    issue_id=f"incomplete_{chunk.get('chunk_id', '')}",
                    issue_type='incomplete_content',
                    severity='high',
                    description='内容不完整或被截断',
                    affected_chunks=[chunk.get('chunk_id', '')],
                    auto_fixable=True,
                    fix_suggestion='建议补充完整内容'
                )
                issues.append(issue)
        
        return issues
    
    async def _detect_structure_problems(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[QualityIssue]:
        """检测结构问题"""
        issues = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            
            # 检查是否缺少结构
            has_structure = (
                '1.' in content or '2.' in content or  # 编号
                '#' in content or  # 标题
                '\n\n' in content  # 段落分隔
            )
            
            if not has_structure and len(content) > 200:
                issue = QualityIssue(
                    issue_id=f"structure_{chunk.get('chunk_id', '')}",
                    issue_type='poor_structure',
                    severity='medium',
                    description='缺少清晰的结构层次',
                    affected_chunks=[chunk.get('chunk_id', '')],
                    auto_fixable=True,
                    fix_suggestion='建议添加编号或标题'
                )
                issues.append(issue)
        
        return issues
    
    async def _detect_low_density(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[QualityIssue]:
        """检测低信息密度"""
        issues = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            words = content.split()
            
            if len(words) == 0:
                continue
            
            # 简单检测：计算有效词汇比例
            filler_words = {'嗯', '啊', '呃', '那个', '这个', '就是', '然后'}
            filler_count = sum(1 for word in words if word in filler_words)
            
            density = 1 - (filler_count / len(words))
            
            if density < 0.7:
                issue = QualityIssue(
                    issue_id=f"density_{chunk.get('chunk_id', '')}",
                    issue_type='low_information_density',
                    severity='medium',
                    description=f'信息密度低（{density:.1%}），冗余内容过多',
                    affected_chunks=[chunk.get('chunk_id', '')],
                    auto_fixable=True,
                    fix_suggestion='建议去除冗余，提取核心信息'
                )
                issues.append(issue)
        
        return issues
    
    async def _detect_format_inconsistency(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[QualityIssue]:
        """检测格式不一致"""
        issues = []
        
        # 检查标点符号一致性
        punctuation_styles = set()
        for chunk in chunks:
            content = chunk.get('content', '')
            if '。' in content:
                punctuation_styles.add('chinese')
            if '.' in content and not '。' in content:
                punctuation_styles.add('english')
        
        if len(punctuation_styles) > 1:
            issue = QualityIssue(
                issue_id='format_punctuation',
                issue_type='inconsistent_format',
                severity='low',
                description='标点符号风格不一致（中英文混用）',
                affected_chunks=[chunk.get('chunk_id', '') for chunk in chunks],
                auto_fixable=True,
                fix_suggestion='建议统一使用中文标点'
            )
            issues.append(issue)
        
        return issues
    
    def _calculate_overall_score(
        self,
        issues: List[QualityIssue],
        chunks: List[Dict[str, Any]]
    ) -> float:
        """计算综合质量分数"""
        if not issues:
            return 1.0
        
        # 基础分
        score = 1.0
        
        # 根据问题严重程度扣分
        severity_weights = {
            'critical': 0.3,
            'high': 0.15,
            'medium': 0.08,
            'low': 0.03
        }
        
        for issue in issues:
            weight = severity_weights.get(issue.severity, 0.05)
            score -= weight
        
        return max(0.0, score)
    
    def _generate_feedback_message(
        self,
        score: float,
        issues: List[QualityIssue],
        passed: bool
    ) -> str:
        """生成反馈消息"""
        if passed:
            return f"✅ 文档质量合格（分数: {score:.2f}），可以入库"
        
        message_parts = [
            f"❌ 文档质量不合格（分数: {score:.2f}），需要改进",
            f"\n发现 {len(issues)} 个质量问题："
        ]
        
        for i, issue in enumerate(issues, 1):
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '⚪'
            }.get(issue.severity, '⚪')
            
            message_parts.append(
                f"\n{i}. {severity_emoji} {issue.description}"
            )
            if issue.auto_fixable:
                message_parts.append(" [可自动修复]")
        
        return ''.join(message_parts)
    
    async def _evaluate_fix_quality(
        self,
        original: str,
        fixed: str,
        issue: QualityIssue
    ) -> float:
        """评估修复质量"""
        # 简化评估逻辑
        if not fixed or fixed == original:
            return 0.0
        
        # 基础分
        confidence = 0.6
        
        # 长度合理性
        if len(fixed) > len(original) * 0.8:
            confidence += 0.1
        
        # 是否包含关键改进
        if issue.issue_type == 'missing_key_info':
            # 检查是否补充了内容
            if len(fixed) > len(original):
                confidence += 0.2
        
        elif issue.issue_type == 'low_information_density':
            # 检查是否压缩了内容
            if len(fixed) < len(original):
                confidence += 0.2
        
        return min(confidence, 1.0)
    
    # 规则修复辅助方法
    
    def _add_headings(self, content: str) -> Tuple[str, bool]:
        """添加标题"""
        # 简化实现
        return content, False
    
    def _organize_sections(self, content: str) -> Tuple[str, bool]:
        """组织章节"""
        # 简化实现
        return content, False
    
    def _add_numbering(self, content: str) -> Tuple[str, bool]:
        """添加编号"""
        # 简化实现
        return content, False
    
    def _standardize_format(self, content: str) -> Tuple[str, bool]:
        """标准化格式"""
        # 简化实现
        return content, False
    
    def _fix_punctuation(self, content: str) -> Tuple[str, bool]:
        """修复标点"""
        # 简化实现
        return content, False
    
    def _normalize_spacing(self, content: str) -> Tuple[str, bool]:
        """规范化空格"""
        import re
        fixed = re.sub(r'\s+', ' ', content)
        return fixed, fixed != content
