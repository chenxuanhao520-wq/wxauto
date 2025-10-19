"""
格式标准化器
将不同格式的文档统一标准化为知识库格式
"""
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class FormatNormalizer:
    """
    格式标准化器
    
    功能：
    1. 统一文档格式
    2. 提取结构化字段
    3. 标准化输出格式
    4. 适配不同文档类型
    """
    
    def __init__(self):
        """初始化格式标准化器"""
        # 定义标准输出格式
        self.standard_formats = self._init_standard_formats()
        
        logger.info("格式标准化器初始化完成")
    
    def _init_standard_formats(self) -> Dict[str, Dict[str, Any]]:
        """初始化标准格式"""
        return {
            'product_info': {
                'format_name': '产品信息标准格式',
                'template': {
                    'type': 'product_info',
                    'product_name': '',
                    'product_model': '',
                    'specifications': [],
                    'features': '',
                    'usage_scenarios': [],
                    'price_range': '',
                    'images': [],
                    'links': []
                }
            },
            'faq': {
                'format_name': 'FAQ标准格式',
                'template': {
                    'type': 'faq',
                    'question': '',
                    'question_variations': [],  # 问法变体
                    'short_answer': '',  # 简洁答案
                    'detailed_answer': '',  # 详细答案
                    'steps': [],  # 操作步骤
                    'related_links': [],  # 相关链接
                    'related_faqs': [],  # 相关FAQ
                    'tags': []  # 标签
                }
            },
            'operation': {
                'format_name': '操作文档标准格式',
                'template': {
                    'type': 'operation',
                    'operation_title': '',
                    'prerequisites': [],  # 前置条件
                    'steps': [],  # 操作步骤
                    'expected_result': '',  # 预期结果
                    'screenshots': [],  # 截图
                    'notes': [],  # 注意事项
                    'troubleshooting': [],  # 常见问题
                    'video_links': []  # 视频链接
                }
            },
            'technical': {
                'format_name': '技术文档标准格式',
                'template': {
                    'type': 'technical',
                    'title': '',
                    'overview': '',
                    'content': '',
                    'code_examples': [],
                    'parameters': [],
                    'notes': []
                }
            }
        }
    
    async def normalize(
        self,
        chunk: Dict[str, Any],
        document_type: str
    ) -> Dict[str, Any]:
        """
        标准化文档格式
        
        Args:
            chunk: 原始chunk
            document_type: 文档类型
        
        Returns:
            标准化后的chunk
        """
        content = chunk.get('content', '')
        
        # 根据文档类型选择标准化方法
        if document_type == 'product_info':
            normalized = await self._normalize_product_info(content)
        elif document_type == 'faq':
            normalized = await self._normalize_faq(content)
        elif document_type == 'operation':
            normalized = await self._normalize_operation(content)
        elif document_type == 'technical':
            normalized = await self._normalize_technical(content)
        else:
            normalized = await self._normalize_general(content)
        
        # 更新chunk
        chunk['normalized'] = normalized
        chunk['normalized_at'] = datetime.now().isoformat()
        
        return chunk
    
    async def _normalize_product_info(self, content: str) -> Dict[str, Any]:
        """标准化产品信息"""
        normalized = {
            'type': 'product_info',
            'product_name': self._extract_product_name(content),
            'product_model': self._extract_product_model(content),
            'specifications': self._extract_specifications(content),
            'features': self._extract_features(content),
            'usage_scenarios': self._extract_usage_scenarios(content),
            'price_range': self._extract_price_range(content),
            'original_content': content
        }
        
        return normalized
    
    async def _normalize_faq(self, content: str) -> Dict[str, Any]:
        """标准化FAQ"""
        normalized = {
            'type': 'faq',
            'question': self._extract_question(content),
            'question_variations': self._extract_question_variations(content),
            'short_answer': self._extract_short_answer(content),
            'detailed_answer': self._extract_detailed_answer(content),
            'steps': self._extract_steps(content),
            'related_links': self._extract_links(content),
            'original_content': content
        }
        
        return normalized
    
    async def _normalize_operation(self, content: str) -> Dict[str, Any]:
        """标准化操作文档"""
        normalized = {
            'type': 'operation',
            'operation_title': self._extract_operation_title(content),
            'prerequisites': self._extract_prerequisites(content),
            'steps': self._extract_numbered_steps(content),
            'expected_result': self._extract_expected_result(content),
            'notes': self._extract_notes(content),
            'original_content': content
        }
        
        return normalized
    
    async def _normalize_technical(self, content: str) -> Dict[str, Any]:
        """标准化技术文档"""
        normalized = {
            'type': 'technical',
            'title': self._extract_title(content),
            'overview': self._extract_overview(content),
            'content': content,
            'code_examples': self._extract_code_examples(content),
            'parameters': self._extract_parameters(content),
            'original_content': content
        }
        
        return normalized
    
    async def _normalize_general(self, content: str) -> Dict[str, Any]:
        """标准化通用文档"""
        return {
            'type': 'general',
            'content': content,
            'original_content': content
        }
    
    # ==================== 提取方法 ====================
    
    def _extract_product_name(self, content: str) -> str:
        """提取产品名称"""
        # 尝试从第一行或标题中提取
        lines = content.split('\n')
        for line in lines[:3]:
            line = line.strip()
            if line and not line.startswith('#'):
                # 移除常见的前缀词
                line = re.sub(r'^(产品名称|名称)[：:]\s*', '', line)
                if len(line) > 2 and len(line) < 100:
                    return line
        return ''
    
    def _extract_product_model(self, content: str) -> str:
        """提取产品型号"""
        # 匹配常见的型号格式
        patterns = [
            r'型号[：:]\s*([A-Z0-9\-]+)',
            r'产品型号[：:]\s*([A-Z0-9\-]+)',
            r'Model[：:]\s*([A-Z0-9\-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return ''
    
    def _extract_specifications(self, content: str) -> List[str]:
        """提取技术规格"""
        specs = []
        
        # 查找技术规格部分
        spec_section = re.search(
            r'(技术规格|规格参数|技术参数)[：:](.*?)(?=\n\n|\Z)',
            content,
            re.DOTALL
        )
        
        if spec_section:
            spec_text = spec_section.group(2)
            # 提取列表项
            spec_items = re.findall(r'[-•▪]\s*(.+)', spec_text)
            specs.extend(spec_items)
        
        return specs
    
    def _extract_features(self, content: str) -> str:
        """提取功能描述"""
        feature_patterns = [
            r'功能[描述]*[：:](.*?)(?=\n\n|\Z)',
            r'特性[：:](.*?)(?=\n\n|\Z)',
            r'产品特点[：:](.*?)(?=\n\n|\Z)'
        ]
        
        for pattern in feature_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_usage_scenarios(self, content: str) -> List[str]:
        """提取适用场景"""
        scenarios = []
        
        scenario_section = re.search(
            r'(适用场景|应用场景)[：:](.*?)(?=\n\n|\Z)',
            content,
            re.DOTALL
        )
        
        if scenario_section:
            scenario_text = scenario_section.group(2)
            scenario_items = re.findall(r'[-•▪]\s*(.+)', scenario_text)
            scenarios.extend(scenario_items)
        
        return scenarios
    
    def _extract_price_range(self, content: str) -> str:
        """提取价格范围"""
        price_patterns = [
            r'价格[：:]\s*([¥\$\d,.\-~至]+)',
            r'售价[：:]\s*([¥\$\d,.\-~至]+)',
            r'报价[：:]\s*([¥\$\d,.\-~至]+)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return ''
    
    def _extract_question(self, content: str) -> str:
        """提取问题"""
        # 查找问题标记
        question_patterns = [
            r'[问Q][：:]\s*(.+?)(?=\n|$)',
            r'^(.+?[？?])(?=\n|$)'
        ]
        
        for pattern in question_patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        # 如果找不到，取第一行
        first_line = content.split('\n')[0].strip()
        if first_line:
            return first_line
        
        return ''
    
    def _extract_question_variations(self, content: str) -> List[str]:
        """提取问法变体"""
        # 查找"相关问法"或"其他问法"
        variations = []
        
        variation_section = re.search(
            r'(相关问法|其他问法|问法变体)[：:](.*?)(?=\n\n|\Z)',
            content,
            re.DOTALL
        )
        
        if variation_section:
            var_text = variation_section.group(2)
            var_items = re.findall(r'[-•▪]\s*(.+)', var_text)
            variations.extend(var_items)
        
        return variations
    
    def _extract_short_answer(self, content: str) -> str:
        """提取简洁答案"""
        # 查找答案标记
        answer_patterns = [
            r'[答A][：:]\s*(.+?)(?=\n\n|\Z)',
            r'简洁答案[：:]\s*(.+?)(?=\n\n|\Z)'
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                answer = match.group(1).strip()
                # 取前100字符作为简洁答案
                return answer[:100] + '...' if len(answer) > 100 else answer
        
        return ''
    
    def _extract_detailed_answer(self, content: str) -> str:
        """提取详细答案"""
        # 查找详细说明
        detailed_patterns = [
            r'详细[说明解答][：:](.*?)(?=\n\n相关链接|\n\n操作步骤|\Z)',
            r'详细答案[：:](.*?)(?=\n\n|\Z)'
        ]
        
        for pattern in detailed_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_steps(self, content: str) -> List[str]:
        """提取步骤"""
        return self._extract_numbered_steps(content)
    
    def _extract_numbered_steps(self, content: str) -> List[str]:
        """提取编号步骤"""
        # 匹配各种步骤格式
        step_patterns = [
            r'\d+[\.、]\s*(.+?)(?=\n\d+[\.、]|\n\n|\Z)',
            r'步骤\d+[：:]\s*(.+?)(?=\n步骤|\n\n|\Z)'
        ]
        
        steps = []
        for pattern in step_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                steps.extend([m.strip() for m in matches])
                break
        
        return steps
    
    def _extract_links(self, content: str) -> List[str]:
        """提取链接"""
        # 匹配URL
        url_pattern = r'https?://[^\s<>"]+'
        links = re.findall(url_pattern, content)
        
        return list(set(links))  # 去重
    
    def _extract_operation_title(self, content: str) -> str:
        """提取操作标题"""
        return self._extract_title(content)
    
    def _extract_prerequisites(self, content: str) -> List[str]:
        """提取前置条件"""
        prereq_section = re.search(
            r'(前置条件|准备工作|操作前准备)[：:](.*?)(?=\n\n|\Z)',
            content,
            re.DOTALL
        )
        
        if prereq_section:
            prereq_text = prereq_section.group(2)
            prereq_items = re.findall(r'[-•▪\d+\.]\s*(.+)', prereq_text)
            return prereq_items
        
        return []
    
    def _extract_expected_result(self, content: str) -> str:
        """提取预期结果"""
        result_patterns = [
            r'预期结果[：:]\s*(.+?)(?=\n\n|\Z)',
            r'操作结果[：:]\s*(.+?)(?=\n\n|\Z)',
            r'完成后[：:]\s*(.+?)(?=\n\n|\Z)'
        ]
        
        for pattern in result_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_notes(self, content: str) -> List[str]:
        """提取注意事项"""
        notes_section = re.search(
            r'(注意事项|注意|警告)[：:](.*?)(?=\n\n|\Z)',
            content,
            re.DOTALL
        )
        
        if notes_section:
            notes_text = notes_section.group(2)
            note_items = re.findall(r'[-•▪\d+\.]\s*(.+)', notes_text)
            return note_items
        
        return []
    
    def _extract_title(self, content: str) -> str:
        """提取标题"""
        # 尝试从Markdown标题提取
        title_match = re.search(r'^#+\s*(.+)$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
        
        # 否则取第一行
        first_line = content.split('\n')[0].strip()
        return first_line if len(first_line) < 100 else ''
    
    def _extract_overview(self, content: str) -> str:
        """提取概述"""
        overview_patterns = [
            r'概述[：:]\s*(.+?)(?=\n\n|\Z)',
            r'简介[：:]\s*(.+?)(?=\n\n|\Z)',
            r'说明[：:]\s*(.+?)(?=\n\n|\Z)'
        ]
        
        for pattern in overview_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_code_examples(self, content: str) -> List[str]:
        """提取代码示例"""
        # 匹配代码块
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
        return code_blocks
    
    def _extract_parameters(self, content: str) -> List[Dict[str, str]]:
        """提取参数说明"""
        params = []
        
        param_section = re.search(
            r'(参数说明|参数列表)[：:](.*?)(?=\n\n|\Z)',
            content,
            re.DOTALL
        )
        
        if param_section:
            param_text = param_section.group(2)
            # 匹配参数行：参数名: 说明
            param_items = re.findall(r'[-•▪]\s*(\w+)[：:]\s*(.+)', param_text)
            for name, desc in param_items:
                params.append({
                    'name': name.strip(),
                    'description': desc.strip()
                })
        
        return params
    
    def to_knowledge_base_format(
        self,
        normalized_chunk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        转换为知识库最终格式
        
        Args:
            normalized_chunk: 标准化后的chunk
        
        Returns:
            知识库格式的chunk
        """
        normalized = normalized_chunk.get('normalized', {})
        doc_type = normalized.get('type', 'general')
        
        # 构建知识库格式
        kb_chunk = {
            'chunk_id': normalized_chunk.get('chunk_id', ''),
            'document_type': doc_type,
            'content': self._build_content_for_retrieval(normalized, doc_type),
            'structured_data': normalized,
            'keywords': self._extract_keywords(normalized),
            'metadata': {
                'normalized': True,
                'normalized_at': normalized_chunk.get('normalized_at', ''),
                'quality_score': normalized_chunk.get('quality_score', 0.0),
                'etl_processed': True
            }
        }
        
        return kb_chunk
    
    def _build_content_for_retrieval(
        self,
        normalized: Dict[str, Any],
        doc_type: str
    ) -> str:
        """构建适合检索的内容"""
        if doc_type == 'faq':
            # FAQ格式：问题 + 简洁答案 + 详细答案
            parts = []
            if normalized.get('question'):
                parts.append(f"问题: {normalized['question']}")
            if normalized.get('short_answer'):
                parts.append(f"答案: {normalized['short_answer']}")
            if normalized.get('steps'):
                parts.append(f"步骤: {'; '.join(normalized['steps'])}")
            return '\n'.join(parts)
        
        elif doc_type == 'product_info':
            # 产品信息格式：产品名 + 型号 + 规格 + 功能
            parts = []
            if normalized.get('product_name'):
                parts.append(f"产品: {normalized['product_name']}")
            if normalized.get('product_model'):
                parts.append(f"型号: {normalized['product_model']}")
            if normalized.get('specifications'):
                parts.append(f"规格: {'; '.join(normalized['specifications'])}")
            if normalized.get('features'):
                parts.append(f"功能: {normalized['features']}")
            return '\n'.join(parts)
        
        elif doc_type == 'operation':
            # 操作文档格式：标题 + 步骤
            parts = []
            if normalized.get('operation_title'):
                parts.append(f"操作: {normalized['operation_title']}")
            if normalized.get('steps'):
                parts.append(f"步骤:\n{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(normalized['steps']))}")
            return '\n'.join(parts)
        
        else:
            # 通用格式
            return normalized.get('original_content', '')
    
    def _extract_keywords(self, normalized: Dict[str, Any]) -> List[str]:
        """从标准化数据中提取关键词"""
        keywords = []
        
        # 根据文档类型提取关键词
        doc_type = normalized.get('type', 'general')
        
        if doc_type == 'product_info':
            if normalized.get('product_name'):
                keywords.append(normalized['product_name'])
            if normalized.get('product_model'):
                keywords.append(normalized['product_model'])
        
        elif doc_type == 'faq':
            question = normalized.get('question', '')
            # 从问题中提取关键词
            keywords.extend(re.findall(r'\b\w{2,}\b', question))
        
        return list(set(keywords))[:10]  # 去重并限制数量
