"""
LLM优化器
专门针对大模型检索优化知识库内容，提升检索效果和Token效率
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
import json

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """优化结果"""
    original_content: str
    optimized_content: str
    optimization_type: str
    token_savings: int
    quality_improvement: float
    retrieval_score: float


class LLMOptimizer:
    """
    LLM优化器
    
    功能：
    1. 内容结构优化（提升检索效率）
    2. Token使用优化（降低成本）
    3. 关键词提取和增强
    4. 上下文适配优化
    5. 检索友好性改进
    """
    
    def __init__(
        self,
        target_token_limit: int = 512,
        enable_keyword_extraction: bool = True,
        enable_structure_optimization: bool = True,
        enable_retrieval_optimization: bool = True
    ):
        """
        初始化LLM优化器
        
        Args:
            target_token_limit: 目标Token限制
            enable_keyword_extraction: 是否启用关键词提取
            enable_structure_optimization: 是否启用结构优化
            enable_retrieval_optimization: 是否启用检索优化
        """
        self.target_token_limit = target_token_limit
        self.enable_keyword_extraction = enable_keyword_extraction
        self.enable_structure_optimization = enable_structure_optimization
        self.enable_retrieval_optimization = enable_retrieval_optimization
        
        # 初始化优化规则
        self.optimization_rules = self._init_optimization_rules()
        
        # 关键词模式
        self.keyword_patterns = self._init_keyword_patterns()
        
        # 检索优化模板
        self.retrieval_templates = self._init_retrieval_templates()
        
        logger.info(
            f"LLM优化器初始化完成: target_tokens={target_token_limit}, "
            f"keyword_extraction={enable_keyword_extraction}"
        )
    
    def _init_optimization_rules(self) -> List[Dict[str, Any]]:
        """初始化优化规则"""
        return [
            {
                'name': 'extract_key_information',
                'description': '提取关键信息',
                'priority': 1,
                'enabled': True
            },
            {
                'name': 'optimize_sentence_structure',
                'description': '优化句子结构',
                'priority': 2,
                'enabled': True
            },
            {
                'name': 'enhance_keywords',
                'description': '增强关键词',
                'priority': 3,
                'enabled': True
            },
            {
                'name': 'improve_retrieval_format',
                'description': '改进检索格式',
                'priority': 4,
                'enabled': True
            },
            {
                'name': 'compress_redundant_info',
                'description': '压缩冗余信息',
                'priority': 5,
                'enabled': True
            }
        ]
    
    def _init_keyword_patterns(self) -> Dict[str, List[str]]:
        """初始化关键词模式"""
        return {
            'technical_terms': [
                r'配置|安装|设置|初始化',
                r'故障|错误|异常|问题',
                r'性能|优化|提升|改进',
                r'安全|权限|认证|授权'
            ],
            'action_words': [
                r'点击|选择|输入|设置',
                r'查看|检查|确认|验证',
                r'启动|停止|重启|运行',
                r'创建|删除|修改|更新'
            ],
            'product_terms': [
                r'充电桩|设备|系统|软件',
                r'接口|API|服务|模块',
                r'数据库|缓存|存储|文件'
            ]
        }
    
    def _init_retrieval_templates(self) -> Dict[str, str]:
        """初始化检索优化模板"""
        return {
            'qa_format': "Q: {question}\nA: {answer}",
            'instruction_format': "指令: {instruction}\n步骤: {steps}",
            'troubleshoot_format': "问题: {problem}\n解决方案: {solution}",
            'feature_format': "功能: {feature}\n描述: {description}\n用法: {usage}"
        }
    
    async def optimize_chunks(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        优化知识块列表
        
        Args:
            chunks: 原始知识块列表
        
        Returns:
            优化后的知识块列表
        """
        if not chunks:
            return []
        
        optimized_chunks = []
        
        for chunk in chunks:
            try:
                optimization_result = await self.optimize_single_chunk(chunk)
                
                # 更新chunk信息
                optimized_chunk = chunk.copy()
                optimized_chunk.update({
                    'content': optimization_result.optimized_content,
                    'original_content': optimization_result.original_content,
                    'optimization_applied': optimization_result.optimization_type,
                    'token_savings': optimization_result.token_savings,
                    'quality_improvement': optimization_result.quality_improvement,
                    'retrieval_score': optimization_result.retrieval_score,
                    'llm_optimized': True
                })
                
                optimized_chunks.append(optimized_chunk)
                
            except Exception as e:
                logger.error(f"优化知识块失败 {chunk.get('chunk_id', '')}: {e}")
                # 保留原始chunk
                optimized_chunks.append(chunk)
        
        logger.info(f"LLM优化完成: {len(optimized_chunks)} 个知识块")
        
        return optimized_chunks
    
    async def optimize_single_chunk(
        self,
        chunk: Dict[str, Any]
    ) -> OptimizationResult:
        """
        优化单个知识块
        
        Args:
            chunk: 知识块数据
        
        Returns:
            优化结果
        """
        original_content = chunk.get('content', '')
        if not original_content:
            return OptimizationResult(
                original_content='',
                optimized_content='',
                optimization_type='none',
                token_savings=0,
                quality_improvement=0.0,
                retrieval_score=0.0
            )
        
        optimized_content = original_content
        optimization_steps = []
        
        # 1. 提取关键信息
        if self.enable_keyword_extraction:
            key_info = await self._extract_key_information(original_content)
            if key_info:
                optimized_content = key_info
                optimization_steps.append('key_information_extraction')
        
        # 2. 优化句子结构
        if self.enable_structure_optimization:
            structured_content = await self._optimize_sentence_structure(optimized_content)
            if structured_content != optimized_content:
                optimized_content = structured_content
                optimization_steps.append('sentence_structure_optimization')
        
        # 3. 增强关键词
        enhanced_content = await self._enhance_keywords(optimized_content)
        if enhanced_content != optimized_content:
            optimized_content = enhanced_content
            optimization_steps.append('keyword_enhancement')
        
        # 4. 改进检索格式
        if self.enable_retrieval_optimization:
            retrieval_content = await self._improve_retrieval_format(optimized_content)
            if retrieval_content != optimized_content:
                optimized_content = retrieval_content
                optimization_steps.append('retrieval_format_improvement')
        
        # 5. 压缩冗余信息
        compressed_content = await self._compress_redundant_info(optimized_content)
        if compressed_content != optimized_content:
            optimized_content = compressed_content
            optimization_steps.append('redundant_info_compression')
        
        # 计算优化指标
        token_savings = self._calculate_token_savings(original_content, optimized_content)
        quality_improvement = self._calculate_quality_improvement(original_content, optimized_content)
        retrieval_score = self._calculate_retrieval_score(optimized_content)
        
        optimization_type = '|'.join(optimization_steps) if optimization_steps else 'none'
        
        return OptimizationResult(
            original_content=original_content,
            optimized_content=optimized_content,
            optimization_type=optimization_type,
            token_savings=token_savings,
            quality_improvement=quality_improvement,
            retrieval_score=retrieval_score
        )
    
    async def _extract_key_information(self, content: str) -> str:
        """提取关键信息"""
        # 识别内容类型并提取关键信息
        if self._is_qa_content(content):
            return self._extract_qa_key_info(content)
        elif self._is_instruction_content(content):
            return self._extract_instruction_key_info(content)
        elif self._is_troubleshoot_content(content):
            return self._extract_troubleshoot_key_info(content)
        else:
            return self._extract_general_key_info(content)
    
    def _is_qa_content(self, content: str) -> bool:
        """判断是否为问答内容"""
        qa_indicators = ['问：', '答：', 'Q:', 'A:', '问题', '答案', '解答']
        return any(indicator in content for indicator in qa_indicators)
    
    def _is_instruction_content(self, content: str) -> bool:
        """判断是否为指令内容"""
        instruction_indicators = ['步骤', '操作', '方法', '流程', '如何', '怎样']
        return any(indicator in content for indicator in instruction_indicators)
    
    def _is_troubleshoot_content(self, content: str) -> bool:
        """判断是否为故障排查内容"""
        troubleshoot_indicators = ['故障', '错误', '异常', '问题', '解决', '排查']
        return any(indicator in content for indicator in troubleshoot_indicators)
    
    def _extract_qa_key_info(self, content: str) -> str:
        """提取问答关键信息"""
        lines = content.split('\n')
        question = ""
        answer = ""
        
        for line in lines:
            line = line.strip()
            if any(q in line for q in ['问：', 'Q:', '问题']):
                question = line
            elif any(a in line for a in ['答：', 'A:', '答案']):
                answer = line
        
        if question and answer:
            return f"Q: {question}\nA: {answer}"
        
        return content
    
    def _extract_instruction_key_info(self, content: str) -> str:
        """提取指令关键信息"""
        # 提取步骤和要点
        steps = re.findall(r'\d+[\.、]\s*([^\n]+)', content)
        if steps:
            return "步骤: " + " | ".join(steps[:3])  # 最多3个步骤
        
        return content
    
    def _extract_troubleshoot_key_info(self, content: str) -> str:
        """提取故障排查关键信息"""
        # 提取问题描述和解决方案
        problem_match = re.search(r'问题[：:]\s*([^\n]+)', content)
        solution_match = re.search(r'解决[：:]\s*([^\n]+)', content)
        
        if problem_match and solution_match:
            return f"问题: {problem_match.group(1)}\n解决: {solution_match.group(1)}"
        
        return content
    
    def _extract_general_key_info(self, content: str) -> str:
        """提取一般内容关键信息"""
        # 提取前几句作为关键信息
        sentences = re.split(r'[。！？]', content)
        key_sentences = [s.strip() for s in sentences[:2] if s.strip()]
        
        if key_sentences:
            return '。'.join(key_sentences) + '。'
        
        return content
    
    async def _optimize_sentence_structure(self, content: str) -> str:
        """优化句子结构"""
        # 简化复杂句子
        sentences = re.split(r'[。！？]', content)
        optimized_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 简化长句子
            if len(sentence) > 50:
                # 提取关键部分
                simplified = self._simplify_sentence(sentence)
                optimized_sentences.append(simplified)
            else:
                optimized_sentences.append(sentence)
        
        return '。'.join(optimized_sentences) + '。'
    
    def _simplify_sentence(self, sentence: str) -> str:
        """简化句子"""
        # 移除冗余修饰词
        redundant_words = ['非常', '特别', '十分', '相当', '比较', '很']
        for word in redundant_words:
            sentence = sentence.replace(word, '')
        
        # 提取核心信息
        # 这里可以实现更复杂的句子简化逻辑
        return sentence[:50] + '...' if len(sentence) > 50 else sentence
    
    async def _enhance_keywords(self, content: str) -> str:
        """增强关键词"""
        enhanced_content = content
        
        # 为关键词添加标记
        for category, patterns in self.keyword_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, enhanced_content)
                for match in matches:
                    keyword = match.group()
                    # 可以选择是否添加特殊标记
                    # enhanced_content = enhanced_content.replace(keyword, f"【{keyword}】")
                    pass
        
        return enhanced_content
    
    async def _improve_retrieval_format(self, content: str) -> str:
        """改进检索格式"""
        # 根据内容类型选择合适的模板
        if self._is_qa_content(content):
            return self._format_as_qa(content)
        elif self._is_instruction_content(content):
            return self._format_as_instruction(content)
        elif self._is_troubleshoot_content(content):
            return self._format_as_troubleshoot(content)
        else:
            return content
    
    def _format_as_qa(self, content: str) -> str:
        """格式化为问答形式"""
        return content  # 已经在提取阶段处理
    
    def _format_as_instruction(self, content: str) -> str:
        """格式化为指令形式"""
        steps = re.findall(r'\d+[\.、]\s*([^\n]+)', content)
        if steps:
            formatted_steps = '\n'.join([f"{i+1}. {step}" for i, step in enumerate(steps)])
            return f"操作步骤:\n{formatted_steps}"
        return content
    
    def _format_as_troubleshoot(self, content: str) -> str:
        """格式化为故障排查形式"""
        return content  # 已经在提取阶段处理
    
    async def _compress_redundant_info(self, content: str) -> str:
        """压缩冗余信息"""
        # 移除重复的词汇
        words = content.split()
        seen_words = set()
        compressed_words = []
        
        for word in words:
            if word not in seen_words or len(word) > 2:  # 保留重要词汇
                compressed_words.append(word)
                seen_words.add(word)
        
        return ' '.join(compressed_words)
    
    def _calculate_token_savings(self, original: str, optimized: str) -> int:
        """计算Token节省"""
        # 简化计算：按字符数估算Token
        original_tokens = len(original) // 4  # 粗略估算
        optimized_tokens = len(optimized) // 4
        
        return max(0, original_tokens - optimized_tokens)
    
    def _calculate_quality_improvement(self, original: str, optimized: str) -> float:
        """计算质量改进"""
        # 基于多个因素计算质量改进
        improvements = []
        
        # 1. 信息密度改进
        original_density = len(re.findall(r'\b\w+\b', original)) / len(original)
        optimized_density = len(re.findall(r'\b\w+\b', optimized)) / len(optimized)
        density_improvement = optimized_density - original_density
        improvements.append(density_improvement)
        
        # 2. 结构清晰度改进
        original_structure = self._calculate_structure_score(original)
        optimized_structure = self._calculate_structure_score(optimized)
        structure_improvement = optimized_structure - original_structure
        improvements.append(structure_improvement)
        
        # 3. 关键词密度改进
        original_keyword_density = self._calculate_keyword_density(original)
        optimized_keyword_density = self._calculate_keyword_density(optimized)
        keyword_improvement = optimized_keyword_density - original_keyword_density
        improvements.append(keyword_improvement)
        
        return sum(improvements) / len(improvements)
    
    def _calculate_structure_score(self, content: str) -> float:
        """计算结构清晰度分数"""
        # 检查是否有明确的结构标记
        structure_indicators = ['1.', '2.', '3.', '步骤', '要点', '注意']
        score = 0.0
        
        for indicator in structure_indicators:
            if indicator in content:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_keyword_density(self, content: str) -> float:
        """计算关键词密度"""
        total_words = len(re.findall(r'\b\w+\b', content))
        if total_words == 0:
            return 0.0
        
        keyword_count = 0
        for category, patterns in self.keyword_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content)
                keyword_count += len(matches)
        
        return keyword_count / total_words
    
    def _calculate_retrieval_score(self, content: str) -> float:
        """计算检索友好性分数"""
        score = 0.0
        
        # 1. 关键词密度
        keyword_density = self._calculate_keyword_density(content)
        score += keyword_density * 0.4
        
        # 2. 信息完整性
        info_completeness = self._calculate_info_completeness(content)
        score += info_completeness * 0.3
        
        # 3. 结构化程度
        structure_score = self._calculate_structure_score(content)
        score += structure_score * 0.3
        
        return min(score, 1.0)
    
    def _calculate_info_completeness(self, content: str) -> float:
        """计算信息完整性"""
        # 检查是否包含关键信息要素
        completeness_indicators = ['什么', '如何', '为什么', '哪里', '何时']
        score = 0.0
        
        for indicator in completeness_indicators:
            if indicator in content:
                score += 0.2
        
        return min(score, 1.0)
    
    async def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return {
            'target_token_limit': self.target_token_limit,
            'enable_keyword_extraction': self.enable_keyword_extraction,
            'enable_structure_optimization': self.enable_structure_optimization,
            'enable_retrieval_optimization': self.enable_retrieval_optimization,
            'optimization_rules_count': len(self.optimization_rules),
            'keyword_patterns_count': sum(len(patterns) for patterns in self.keyword_patterns.values())
        }
