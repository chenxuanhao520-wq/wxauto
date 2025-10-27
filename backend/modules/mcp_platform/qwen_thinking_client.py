"""
通义千问深度思考客户端
使用普通 API 实现类似 MCP Sequential Thinking 的功能
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx

logger = logging.getLogger(__name__)


class QwenThinkingClient:
    """通义千问深度思考客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.model = "qwen-plus"  # 使用 qwen-plus 获得更好的推理能力
        
    async def sequential_thinking(
        self, 
        problem: str,
        context: Optional[str] = None,
        max_steps: int = 5,
        thinking_style: str = "analytical"
    ) -> Dict[str, Any]:
        """
        顺序思考 - 结构化问题分析
        
        Args:
            problem: 要分析的问题
            context: 上下文信息（可选）
            max_steps: 最大思考步骤数
            thinking_style: 思考风格
            
        Returns:
            思考结果字典
        """
        try:
            logger.info(f"🧠 开始深度思考: {problem[:50]}...")
            
            # 构建思考提示词
            system_prompt = self._build_thinking_prompt(thinking_style, max_steps)
            
            user_message = f"""问题：{problem}

{f'背景信息：{context}' if context else ''}

请进行深度的、结构化的思考分析。"""
            
            # 调用通义千问 API
            response = await self._call_qwen_api(system_prompt, user_message)
            
            if response.get("success"):
                thinking_text = response.get("text", "")
                
                # 解析思考步骤
                thinking_steps = self._parse_thinking_steps(thinking_text)
                
                # 提取结论
                conclusion = self._extract_conclusion(thinking_text)
                
                return {
                    "success": True,
                    "problem": problem,
                    "thinking_steps": thinking_steps,
                    "conclusion": conclusion,
                    "confidence": 0.85,  # 基于 qwen-plus 的置信度
                    "full_text": thinking_text,
                    "model": self.model,
                    "usage": response.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "problem": problem,
                    "error": response.get("error", "API 调用失败")
                }
        
        except Exception as e:
            logger.error(f"❌ 深度思考异常: {e}")
            return {
                "success": False,
                "problem": problem,
                "error": str(e)
            }
    
    async def problem_decomposition(
        self, 
        complex_problem: str,
        decomposition_level: int = 3
    ) -> Dict[str, Any]:
        """
        问题分解 - 将复杂问题分解为子问题
        
        Args:
            complex_problem: 复杂问题
            decomposition_level: 分解层级
            
        Returns:
            分解结果字典
        """
        system_prompt = """你是一个问题分解专家。请将复杂问题分解为可执行的子问题。

要求：
1. 每个子问题应该独立且可执行
2. 子问题之间应该有逻辑关系
3. 分解应该全面且结构化
4. 使用编号列表格式输出"""

        user_message = f"""请将以下复杂问题分解为 {decomposition_level} 个关键子问题：

{complex_problem}

请提供详细的分解分析。"""
        
        response = await self._call_qwen_api(system_prompt, user_message)
        
        if response.get("success"):
            text = response.get("text", "")
            sub_problems = self._parse_sub_problems(text)
            
            return {
                "success": True,
                "original_problem": complex_problem,
                "sub_problems": sub_problems,
                "decomposition_level": decomposition_level,
                "analysis": text,
                "usage": response.get("usage", {})
            }
        else:
            return {
                "success": False,
                "original_problem": complex_problem,
                "error": response.get("error", "分解失败")
            }
    
    async def decision_analysis(
        self,
        decision_context: str,
        options: List[str],
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        决策分析 - 结构化决策过程
        
        Args:
            decision_context: 决策背景
            options: 可选方案列表
            criteria: 评估标准列表
            
        Returns:
            决策分析结果
        """
        system_prompt = """你是一个决策分析专家。请进行全面的决策分析。

分析维度：
1. 方案优劣势分析
2. 风险评估
3. 成本效益分析
4. 可行性评估
5. 推荐方案及理由"""

        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        criteria_text = f"\n评估标准：{', '.join(criteria)}" if criteria else ""
        
        user_message = f"""决策背景：
{decision_context}

可选方案：
{options_text}
{criteria_text}

请进行全面的决策分析。"""
        
        response = await self._call_qwen_api(system_prompt, user_message)
        
        if response.get("success"):
            text = response.get("text", "")
            recommendation = self._extract_recommendation(text)
            
            return {
                "success": True,
                "decision_context": decision_context,
                "options": options,
                "criteria": criteria,
                "analysis": text,
                "recommendation": recommendation,
                "confidence": 0.85,
                "usage": response.get("usage", {})
            }
        else:
            return {
                "success": False,
                "decision_context": decision_context,
                "error": response.get("error", "分析失败")
            }
    
    async def creative_brainstorming(
        self,
        topic: str,
        num_ideas: int = 5,
        constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        创意头脑风暴
        
        Args:
            topic: 头脑风暴主题
            num_ideas: 生成创意数量
            constraints: 约束条件
            
        Returns:
            创意列表
        """
        system_prompt = """你是一个创意思维专家。请进行发散性思考，生成创新的想法。

要求：
1. 想法应该创新且可行
2. 提供详细的实现思路
3. 考虑实际应用场景"""

        constraints_text = f"\n约束条件：{', '.join(constraints)}" if constraints else ""
        
        user_message = f"""主题：{topic}

请生成 {num_ideas} 个创新想法。{constraints_text}"""
        
        response = await self._call_qwen_api(system_prompt, user_message)
        
        if response.get("success"):
            text = response.get("text", "")
            ideas = self._parse_ideas(text, num_ideas)
            
            return {
                "success": True,
                "topic": topic,
                "ideas": ideas,
                "num_ideas": len(ideas),
                "usage": response.get("usage", {})
            }
        else:
            return {
                "success": False,
                "topic": topic,
                "error": response.get("error", "生成失败")
            }
    
    def _build_thinking_prompt(self, style: str, max_steps: int) -> str:
        """构建思考提示词"""
        style_prompts = {
            "analytical": "你是一个分析型思考专家，擅长逻辑推理和数据分析。",
            "creative": "你是一个创造型思考专家，擅长发散思维和创新思考。",
            "logical": "你是一个逻辑型思考专家，擅长严密的逻辑推理。",
            "practical": "你是一个实践型思考专家，擅长从实际出发解决问题。"
        }
        
        base_prompt = style_prompts.get(style, style_prompts["analytical"])
        
        return f"""{base_prompt}

请对问题进行深度的、结构化的思考分析。

思考要求：
1. 分步骤进行思考（最多{max_steps}步）
2. 每个步骤要有明确的推理过程
3. 考虑多个角度和可能性
4. 最后给出清晰的结论

输出格式：
【步骤1】...
【步骤2】...
...
【结论】..."""
    
    async def _call_qwen_api(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """调用通义千问 API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            },
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "text": data["output"]["text"],
                        "usage": data.get("usage", {})
                    }
                else:
                    error_data = response.json()
                    return {
                        "success": False,
                        "error": error_data.get("message", f"HTTP {response.status_code}")
                    }
        
        except Exception as e:
            logger.error(f"API 调用异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_thinking_steps(self, text: str) -> List[Dict[str, str]]:
        """解析思考步骤"""
        steps = []
        lines = text.split('\n')
        current_step = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if '【步骤' in line or '步骤' in line[:10]:
                if current_step:
                    steps.append({
                        "step": current_step,
                        "content": '\n'.join(current_content).strip()
                    })
                current_step = line
                current_content = []
            elif current_step and line:
                current_content.append(line)
        
        if current_step:
            steps.append({
                "step": current_step,
                "content": '\n'.join(current_content).strip()
            })
        
        return steps if steps else [{"step": "分析", "content": text}]
    
    def _extract_conclusion(self, text: str) -> str:
        """提取结论"""
        for marker in ['【结论】', '结论：', '总结：', '综上所述']:
            if marker in text:
                parts = text.split(marker)
                if len(parts) > 1:
                    return parts[-1].strip()
        
        # 如果没有明确标记，返回最后一段
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return paragraphs[-1] if paragraphs else text[-200:]
    
    def _parse_sub_problems(self, text: str) -> List[Dict[str, str]]:
        """解析子问题"""
        sub_problems = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # 匹配编号格式：1. 或 1、 或 （1）
            if line and (line[0].isdigit() or line.startswith('（')):
                sub_problems.append({
                    "problem": line,
                    "priority": len(sub_problems) + 1
                })
        
        return sub_problems if sub_problems else [{"problem": text, "priority": 1}]
    
    def _extract_recommendation(self, text: str) -> str:
        """提取推荐方案"""
        for marker in ['推荐', '建议', '最佳方案', '优选']:
            if marker in text:
                # 找到标记后的段落
                idx = text.find(marker)
                remaining = text[idx:]
                paragraphs = remaining.split('\n\n')
                if paragraphs:
                    return paragraphs[0].strip()
        
        return "请参考详细分析"
    
    def _parse_ideas(self, text: str, num_ideas: int) -> List[Dict[str, str]]:
        """解析创意列表"""
        ideas = []
        lines = text.split('\n')
        current_idea = None
        current_desc = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or '、' in line[:5] or '.' in line[:5]):
                if current_idea:
                    ideas.append({
                        "idea": current_idea,
                        "description": '\n'.join(current_desc).strip()
                    })
                current_idea = line
                current_desc = []
            elif current_idea and line:
                current_desc.append(line)
        
        if current_idea:
            ideas.append({
                "idea": current_idea,
                "description": '\n'.join(current_desc).strip()
            })
        
        return ideas[:num_ideas] if ideas else [{"idea": text, "description": ""}]
