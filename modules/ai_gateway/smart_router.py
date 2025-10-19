"""
智能模型路由器
根据问题复杂度、任务类型、上下文长度自动选择最优模型
"""
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelProfile:
    """模型画像"""
    provider: str
    model: str
    cost_per_1k_input: float  # 每1000 tokens输入成本（元）
    cost_per_1k_output: float  # 每1000 tokens输出成本（元）
    avg_latency_ms: int
    max_context: int
    strengths: List[str]
    weaknesses: List[str]
    best_for_tasks: List[str]


class SmartModelRouter:
    """
    智能模型路由器
    
    功能：
    1. 分析问题复杂度
    2. 识别任务类型
    3. 评估上下文长度
    4. 智能选择最优模型
    5. 成本优化
    """
    
    def __init__(self):
        """初始化路由器"""
        # 定义模型画像
        self.model_profiles = self._init_model_profiles()
        
        # 路由规则
        self.routing_rules = self._init_routing_rules()
        
        # 复杂度关键词
        self.complexity_keywords = self._init_complexity_keywords()
        
        logger.info("智能模型路由器初始化完成")
    
    def _init_model_profiles(self) -> Dict[str, ModelProfile]:
        """初始化模型画像"""
        return {
            'qwen-turbo': ModelProfile(
                provider='qwen',
                model='qwen-turbo',
                cost_per_1k_input=0.0006,  # ¥0.6/百万
                cost_per_1k_output=0.0024,  # ¥2.4/百万
                avg_latency_ms=800,
                max_context=8000,
                strengths=['速度快', '成本低', '简单问答'],
                weaknesses=['复杂推理能力弱'],
                best_for_tasks=['simple_qa', 'product_inquiry', 'quick_response']
            ),
            'qwen-plus': ModelProfile(
                provider='qwen',
                model='qwen-plus',
                cost_per_1k_input=0.0012,  # ¥1.2/百万
                cost_per_1k_output=0.0048,  # ¥4.8/百万
                avg_latency_ms=1000,
                max_context=32000,
                strengths=['能力均衡', '性价比高', '总结能力强'],
                weaknesses=['不是最快也不是最准'],
                best_for_tasks=['general_qa', 'summary', 'explanation']
            ),
            'qwen-max': ModelProfile(
                provider='qwen',
                model='qwen-max',
                cost_per_1k_input=0.0024,  # ¥2.4/百万
                cost_per_1k_output=0.0096,  # ¥9.6/百万
                avg_latency_ms=1200,
                max_context=128000,
                strengths=['长文本', '总结最强', '多模态'],
                weaknesses=['成本最高'],
                best_for_tasks=['long_summary', 'multimodal', 'document_analysis']
            ),
            'deepseek': ModelProfile(
                provider='deepseek',
                model='deepseek-chat',
                cost_per_1k_input=0.001,  # ¥0.5-2/百万（缓存）
                cost_per_1k_output=0.008,  # ¥8/百万
                avg_latency_ms=1500,
                max_context=64000,
                strengths=['最准确', '幻觉少', '复杂推理强', '事实性好'],
                weaknesses=['速度稍慢'],
                best_for_tasks=['complex_reasoning', 'critical_qa', 'troubleshooting']
            )
        }
    
    def _init_routing_rules(self) -> List[Dict[str, Any]]:
        """初始化路由规则"""
        return [
            {
                'rule_id': 'long_document_summary',
                'priority': 1,
                'conditions': {
                    'task_type': 'summary',
                    'min_context_length': 2000
                },
                'target_model': 'qwen-max',
                'reason': '长文档总结，Qwen-max能力最强'
            },
            {
                'rule_id': 'multimodal_task',
                'priority': 2,
                'conditions': {
                    'has_image': True
                },
                'target_model': 'qwen-max',
                'reason': '多模态任务，Qwen-max支持图片'
            },
            {
                'rule_id': 'complex_reasoning',
                'priority': 3,
                'conditions': {
                    'min_complexity': 0.7
                },
                'target_model': 'deepseek',
                'reason': '复杂推理，DeepSeek准确性最高'
            },
            {
                'rule_id': 'critical_qa',
                'priority': 4,
                'conditions': {
                    'is_critical': True
                },
                'target_model': 'deepseek',
                'reason': '关键问题，需要最高准确性'
            },
            {
                'rule_id': 'medium_complexity',
                'priority': 5,
                'conditions': {
                    'min_complexity': 0.4,
                    'max_complexity': 0.7
                },
                'target_model': 'qwen-plus',
                'reason': '中等难度，平衡性价比'
            },
            {
                'rule_id': 'simple_qa',
                'priority': 6,
                'conditions': {
                    'max_complexity': 0.4
                },
                'target_model': 'qwen-turbo',
                'reason': '简单问答，快速便宜'
            }
        ]
    
    def _init_complexity_keywords(self) -> Dict[str, List[str]]:
        """初始化复杂度关键词"""
        return {
            'simple': ['是什么', '多少钱', '在哪里', '有没有', '可以吗'],
            'medium': ['如何', '怎么', '什么时候', '为何', '哪个好'],
            'complex': ['为什么', '对比', '分析', '评估', '建议', '如果...那么'],
            'summary': ['总结', '归纳', '概括', '提炼', '要点'],
            'reasoning': ['排查', '诊断', '判断', '推理', '解释原因']
        }
    
    async def route(
        self,
        question: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        智能路由选择最优模型
        
        Args:
            question: 用户问题
            context: 知识库上下文
            metadata: 元数据（可包含is_critical等标记）
        
        Returns:
            {
                'model_key': str,  # 选择的模型
                'provider': str,
                'model': str,
                'reason': str,  # 选择原因
                'estimated_cost': float,  # 预估成本
                'estimated_latency': int  # 预估延迟
            }
        """
        metadata = metadata or {}
        
        # 1. 分析任务
        task_type = self._classify_task(question)
        complexity = self._analyze_complexity(question)
        context_length = len(context) if context else 0
        has_image = metadata.get('has_image', False)
        is_critical = metadata.get('is_critical', False)
        
        # 2. 应用路由规则
        for rule in sorted(self.routing_rules, key=lambda x: x['priority']):
            conditions = rule['conditions']
            
            # 检查所有条件
            if self._check_conditions(
                conditions,
                task_type=task_type,
                complexity=complexity,
                context_length=context_length,
                has_image=has_image,
                is_critical=is_critical
            ):
                model_key = rule['target_model']
                profile = self.model_profiles[model_key]
                
                # 估算成本
                estimated_cost = self._estimate_cost(
                    profile,
                    question,
                    context
                )
                
                logger.info(
                    f"路由决策: {model_key} (复杂度={complexity:.2f}, "
                    f"任务={task_type}, 原因={rule['reason']})"
                )
                
                return {
                    'model_key': model_key,
                    'provider': profile.provider,
                    'model': profile.model,
                    'reason': rule['reason'],
                    'estimated_cost': estimated_cost,
                    'estimated_latency': profile.avg_latency_ms,
                    'task_type': task_type,
                    'complexity': complexity
                }
        
        # 默认：Qwen-turbo
        default_profile = self.model_profiles['qwen-turbo']
        return {
            'model_key': 'qwen-turbo',
            'provider': default_profile.provider,
            'model': default_profile.model,
            'reason': '默认选择',
            'estimated_cost': self._estimate_cost(default_profile, question, context),
            'estimated_latency': default_profile.avg_latency_ms
        }
    
    def _classify_task(self, question: str) -> str:
        """分类任务类型"""
        question_lower = question.lower()
        
        # 检查总结任务
        if any(kw in question for kw in self.complexity_keywords['summary']):
            return 'summary'
        
        # 检查推理任务
        if any(kw in question for kw in self.complexity_keywords['reasoning']):
            return 'reasoning'
        
        # 默认为问答
        return 'qa'
    
    def _analyze_complexity(self, question: str) -> float:
        """
        分析问题复杂度
        
        Returns:
            float: 0-1之间的复杂度分数
        """
        score = 0.0
        
        # 1. 问题长度（20%权重）
        length_score = min(len(question) / 100, 1.0) * 0.2
        score += length_score
        
        # 2. 问题数量（20%权重）
        question_count = question.count('？') + question.count('?')
        if question_count > 1:
            score += 0.2
        
        # 3. 逻辑词（30%权重）
        logic_words = ['如果', '那么', '为什么', '怎么办', '原因', '导致']
        logic_count = sum(1 for word in logic_words if word in question)
        score += min(logic_count / 3, 1.0) * 0.3
        
        # 4. 推理词（30%权重）
        reasoning_words = ['对比', '分析', '评估', '建议', '判断', '排查', '诊断']
        reasoning_count = sum(1 for word in reasoning_words if word in question)
        score += min(reasoning_count / 3, 1.0) * 0.3
        
        return min(score, 1.0)
    
    def _check_conditions(
        self,
        conditions: Dict[str, Any],
        **kwargs
    ) -> bool:
        """检查条件是否满足"""
        for key, value in conditions.items():
            if key == 'task_type':
                if kwargs.get('task_type') != value:
                    return False
            
            elif key == 'min_context_length':
                if kwargs.get('context_length', 0) < value:
                    return False
            
            elif key == 'min_complexity':
                if kwargs.get('complexity', 0) < value:
                    return False
            
            elif key == 'max_complexity':
                if kwargs.get('complexity', 1) > value:
                    return False
            
            elif key == 'has_image':
                if kwargs.get('has_image', False) != value:
                    return False
            
            elif key == 'is_critical':
                if kwargs.get('is_critical', False) != value:
                    return False
        
        return True
    
    def _estimate_cost(
        self,
        profile: ModelProfile,
        question: str,
        context: Optional[str]
    ) -> float:
        """估算成本（元）"""
        # 简单估算tokens
        input_tokens = len(question) // 2
        if context:
            input_tokens += len(context) // 2
        
        output_tokens = 200  # 假设平均输出200 tokens
        
        # 计算成本
        input_cost = (input_tokens / 1000) * profile.cost_per_1k_input
        output_cost = (output_tokens / 1000) * profile.cost_per_1k_output
        
        return input_cost + output_cost
    
    def get_model_stats(self) -> Dict[str, Any]:
        """获取模型统计信息"""
        return {
            'total_models': len(self.model_profiles),
            'models': {
                key: {
                    'provider': profile.provider,
                    'model': profile.model,
                    'cost_per_1k_avg': (profile.cost_per_1k_input + profile.cost_per_1k_output) / 2,
                    'latency_ms': profile.avg_latency_ms,
                    'best_for': profile.best_for_tasks
                }
                for key, profile in self.model_profiles.items()
            }
        }
