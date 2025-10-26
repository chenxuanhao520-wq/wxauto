"""
内容清洗器
负责清洗和标准化知识库内容，确保符合大模型检索要求
"""
import logging
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CleaningResult:
    """清洗结果"""
    original_content: str
    cleaned_content: str
    cleaning_applied: List[str]
    quality_improvement: float
    char_count_change: int


class ContentCleaner:
    """
    内容清洗器
    
    功能：
    1. 标准化文本格式
    2. 移除冗余信息
    3. 优化可读性
    4. 提取关键信息
    5. 适配大模型检索
    """
    
    def __init__(self):
        """初始化内容清洗器"""
        # 定义清洗规则
        self.cleaning_rules = self._init_cleaning_rules()
        
        # 停用词列表
        self.stopwords = self._init_stopwords()
        
        # 特殊字符处理规则
        self.special_char_rules = self._init_special_char_rules()
        
        logger.info("内容清洗器初始化完成")
    
    def _init_cleaning_rules(self) -> List[Dict[str, Any]]:
        """初始化清洗规则"""
        return [
            {
                'name': 'remove_extra_whitespace',
                'description': '移除多余空白字符',
                'pattern': r'\s+',
                'replacement': ' ',
                'priority': 1
            },
            {
                'name': 'normalize_punctuation',
                'description': '标准化标点符号',
                'pattern': r'[，。！？；：]',
                'replacement': lambda m: self._normalize_punctuation(m.group()),
                'priority': 2
            },
            {
                'name': 'remove_page_numbers',
                'description': '移除页码',
                'pattern': r'^\s*\d+\s*$',
                'replacement': '',
                'priority': 3
            },
            {
                'name': 'remove_headers_footers',
                'description': '移除页眉页脚',
                'pattern': r'^(第\d+页|Page \d+|共\d+页).*$',
                'replacement': '',
                'priority': 4,
                'flags': re.MULTILINE
            },
            {
                'name': 'clean_table_formatting',
                'description': '清理表格格式',
                'pattern': r'[\|\+\-\s]{3,}',
                'replacement': '',
                'priority': 5
            },
            {
                'name': 'remove_repeated_chars',
                'description': '移除重复字符',
                'pattern': r'(.)\1{2,}',
                'replacement': r'\1\1',
                'priority': 6
            },
            {
                'name': 'normalize_quotes',
                'description': '标准化引号',
                'pattern': r'[""''`]',
                'replacement': '"',
                'priority': 7
            },
            {
                'name': 'remove_control_chars',
                'description': '移除控制字符',
                'pattern': r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]',
                'replacement': '',
                'priority': 8
            }
        ]
    
    def _init_stopwords(self) -> set:
        """初始化停用词"""
        return {
            # 中文停用词
            '的', '了', '是', '在', '我', '你', '他', '她', '它', '们',
            '这', '那', '这', '那', '个', '一', '二', '三', '四', '五',
            '六', '七', '八', '九', '十', '百', '千', '万', '亿',
            '很', '非常', '特别', '十分', '相当', '比较', '更', '最',
            '和', '与', '或', '但', '而', '因为', '所以', '如果', '虽然',
            '可以', '能够', '应该', '必须', '需要', '想要', '希望',
            '什么', '怎么', '为什么', '哪里', '何时', '谁', '多少',
            '啊', '吧', '呢', '吗', '呀', '哦', '嗯', '唉',
            # 英文停用词
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
    
    def _init_special_char_rules(self) -> Dict[str, str]:
        """初始化特殊字符处理规则"""
        return {
            # 全角转半角
            '（': '(', '）': ')', '【': '[', '】': ']',
            '《': '"', '》': '"', '「': '"', '」': '"',
            '，': ',', '。': '.', '！': '!', '？': '?',
            '：': ':', '；': ';', '、': ',',
            # 其他特殊字符
            '…': '...', '—': '-', '–': '-', '～': '~',
            '×': 'x', '÷': '/', '±': '+/-', '°': '度'
        }
    
    async def clean_content(
        self,
        content: str,
        apply_all_rules: bool = True,
        custom_rules: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        清洗内容
        
        Args:
            content: 原始内容
            apply_all_rules: 是否应用所有规则
            custom_rules: 自定义清洗规则
        
        Returns:
            {
                'content': str,  # 清洗后的内容
                'info': Dict,    # 清洗信息
                'quality_score': float  # 质量评分
            }
        """
        if not content or not content.strip():
            return {
                'content': '',
                'info': {'error': '内容为空'},
                'quality_score': 0.0
            }
        
        original_content = content
        cleaned_content = content
        applied_rules = []
        quality_improvements = []
        
        try:
            # 应用标准清洗规则
            if apply_all_rules:
                for rule in sorted(self.cleaning_rules, key=lambda x: x['priority']):
                    try:
                        before_content = cleaned_content
                        cleaned_content = await self._apply_rule(rule, cleaned_content)
                        
                        if cleaned_content != before_content:
                            applied_rules.append(rule['name'])
                            quality_improvements.append(rule['name'])
                        
                    except Exception as e:
                        logger.warning(f"应用清洗规则失败 {rule['name']}: {e}")
            
            # 应用自定义规则
            if custom_rules:
                for rule in custom_rules:
                    try:
                        before_content = cleaned_content
                        cleaned_content = await self._apply_rule(rule, cleaned_content)
                        
                        if cleaned_content != before_content:
                            applied_rules.append(f"custom_{rule.get('name', 'rule')}")
                        
                    except Exception as e:
                        logger.warning(f"应用自定义规则失败: {e}")
            
            # 最终标准化
            cleaned_content = self._final_normalization(cleaned_content)
            
            # 计算质量改进
            quality_score = self._calculate_content_quality(cleaned_content)
            original_quality = self._calculate_content_quality(original_content)
            quality_improvement = quality_score - original_quality
            
            # 生成清洗信息
            cleaning_info = {
                'original_length': len(original_content),
                'cleaned_length': len(cleaned_content),
                'length_change': len(cleaned_content) - len(original_content),
                'applied_rules': applied_rules,
                'quality_improvement': quality_improvement,
                'original_quality': original_quality,
                'final_quality': quality_score
            }
            
            logger.debug(
                f"内容清洗完成: {len(original_content)} -> {len(cleaned_content)} 字符, "
                f"质量提升: {quality_improvement:.2f}"
            )
            
            return {
                'content': cleaned_content,
                'info': cleaning_info,
                'quality_score': quality_score
            }
            
        except Exception as e:
            logger.error(f"内容清洗失败: {e}")
            return {
                'content': original_content,
                'info': {'error': str(e)},
                'quality_score': 0.0
            }
    
    async def _apply_rule(self, rule: Dict[str, Any], content: str) -> str:
        """应用单个清洗规则"""
        pattern = rule['pattern']
        replacement = rule['replacement']
        flags = rule.get('flags', 0)
        
        if callable(replacement):
            # 使用函数替换
            return re.sub(pattern, replacement, content, flags=flags)
        else:
            # 直接字符串替换
            return re.sub(pattern, replacement, content, flags=flags)
    
    def _normalize_punctuation(self, punct: str) -> str:
        """标准化标点符号"""
        punct_map = {
            '，': ',', '。': '.', '！': '!', '？': '?',
            '；': ';', '：': ':'
        }
        return punct_map.get(punct, punct)
    
    def _final_normalization(self, content: str) -> str:
        """最终标准化处理"""
        # 移除首尾空白
        content = content.strip()
        
        # 移除多余空行（最多保留一个空行）
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # 标准化段落间距
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 移除行首行尾空白
        lines = content.split('\n')
        lines = [line.strip() for line in lines]
        content = '\n'.join(lines)
        
        return content
    
    def _calculate_content_quality(self, content: str) -> float:
        """
        计算内容质量分数
        
        Args:
            content: 内容文本
        
        Returns:
            float: 质量分数 (0-1)
        """
        if not content or not content.strip():
            return 0.0
        
        score = 0.0
        
        # 1. 长度合理性 (20%)
        length_score = self._calculate_length_score(content)
        score += length_score * 0.2
        
        # 2. 可读性 (30%)
        readability_score = self._calculate_readability_score(content)
        score += readability_score * 0.3
        
        # 3. 信息密度 (25%)
        information_density = self._calculate_information_density(content)
        score += information_density * 0.25
        
        # 4. 格式规范性 (25%)
        format_score = self._calculate_format_score(content)
        score += format_score * 0.25
        
        return min(score, 1.0)
    
    def _calculate_length_score(self, content: str) -> float:
        """计算长度合理性分数"""
        length = len(content)
        
        if length < 10:
            return 0.0  # 太短
        elif length < 50:
            return 0.3  # 较短
        elif length < 200:
            return 1.0  # 理想长度
        elif length < 500:
            return 0.8  # 稍长
        elif length < 1000:
            return 0.6  # 较长
        else:
            return 0.4  # 太长
    
    def _calculate_readability_score(self, content: str) -> float:
        """计算可读性分数"""
        # 简化版可读性计算
        sentences = re.split(r'[.!?。！？]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # 平均句长
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
        
        # 理想句长：20-40字符
        if 20 <= avg_sentence_length <= 40:
            return 1.0
        elif 15 <= avg_sentence_length <= 50:
            return 0.8
        elif 10 <= avg_sentence_length <= 60:
            return 0.6
        else:
            return 0.4
    
    def _calculate_information_density(self, content: str) -> float:
        """计算信息密度"""
        # 统计有效词汇
        words = re.findall(r'\b\w+\b', content)
        
        if not words:
            return 0.0
        
        # 去除停用词
        meaningful_words = [w for w in words if w.lower() not in self.stopwords]
        
        # 信息密度 = 有效词汇 / 总词汇
        density = len(meaningful_words) / len(words)
        
        return min(density * 2, 1.0)  # 放大并限制在1.0以内
    
    def _calculate_format_score(self, content: str) -> float:
        """计算格式规范性分数"""
        score = 1.0
        
        # 检查多余空白
        if re.search(r'\s{3,}', content):
            score -= 0.2
        
        # 检查特殊字符
        special_chars = re.findall(r'[^\w\s\u4e00-\u9fff.,!?;:()\-]', content)
        if special_chars:
            score -= min(len(special_chars) * 0.1, 0.5)
        
        # 检查重复内容
        if re.search(r'(.)\1{3,}', content):
            score -= 0.3
        
        return max(score, 0.0)
    
    async def batch_clean_content(
        self,
        contents: List[str],
        apply_all_rules: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量清洗内容
        
        Args:
            contents: 内容列表
            apply_all_rules: 是否应用所有规则
        
        Returns:
            清洗结果列表
        """
        tasks = [
            self.clean_content(content, apply_all_rules)
            for content in contents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        cleaned_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量清洗第{i}个内容失败: {result}")
                cleaned_results.append({
                    'content': contents[i],
                    'info': {'error': str(result)},
                    'quality_score': 0.0
                })
            else:
                cleaned_results.append(result)
        
        return cleaned_results
