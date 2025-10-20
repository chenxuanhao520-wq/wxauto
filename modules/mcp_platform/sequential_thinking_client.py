"""
Sequential Thinking MCP 客户端
基于阿里云百炼 Sequential Thinking 服务
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
import httpx

from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class SequentialThinkingClient(MCPClient):
    """Sequential Thinking MCP 客户端"""
    
    def __init__(self, service):
        super().__init__(service)
        self.tools = service.metadata.get("tools", [])
        self.description = service.metadata.get("description", "Sequential Thinking 服务")
    
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
            thinking_style: 思考风格 (analytical, creative, logical, etc.)
            
        Returns:
            思考结果字典
        """
        try:
            logger.info(f"🧠 开始顺序思考分析: {problem[:50]}...")
            
            # 构建思考参数
            thinking_params = {
                "problem": problem,
                "context": context or "",
                "max_steps": max_steps,
                "thinking_style": thinking_style,
                "include_reasoning": True,
                "include_alternatives": True
            }
            
            # 调用 MCP 服务
            result = await self._call_tool(
                "sequential_thinking",
                thinking_params
            )
            
            if result and "thinking_steps" in result:
                logger.info(f"✅ 顺序思考完成: {len(result.get('thinking_steps', []))} 个步骤")
                return {
                    "success": True,
                    "problem": problem,
                    "thinking_steps": result.get("thinking_steps", []),
                    "conclusion": result.get("conclusion", ""),
                    "confidence": result.get("confidence", 0.0),
                    "alternatives": result.get("alternatives", []),
                    "reasoning": result.get("reasoning", ""),
                    "metadata": result.get("metadata", {})
                }
            else:
                logger.warning(f"⚠️ 顺序思考返回格式异常")
                return {
                    "success": False,
                    "problem": problem,
                    "error": "返回格式异常",
                    "raw_result": result
                }
        
        except Exception as e:
            logger.error(f"❌ 顺序思考异常: {e}")
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
        try:
            logger.info(f"🔍 开始问题分解: {complex_problem[:50]}...")
            
            # 调用顺序思考进行问题分解
            result = await self.sequential_thinking(
                problem=f"请将以下复杂问题分解为 {decomposition_level} 个子问题：{complex_problem}",
                context="这是一个问题分解任务，需要结构化思考",
                max_steps=decomposition_level + 2,
                thinking_style="analytical"
            )
            
            if result.get("success"):
                # 提取分解的子问题
                thinking_steps = result.get("thinking_steps", [])
                sub_problems = []
                
                for step in thinking_steps:
                    if "sub_problem" in step or "子问题" in step.get("content", ""):
                        sub_problems.append(step)
                
                return {
                    "success": True,
                    "original_problem": complex_problem,
                    "sub_problems": sub_problems,
                    "decomposition_level": decomposition_level,
                    "total_steps": len(thinking_steps),
                    "confidence": result.get("confidence", 0.0)
                }
            else:
                return result
        
        except Exception as e:
            logger.error(f"❌ 问题分解异常: {e}")
            return {
                "success": False,
                "original_problem": complex_problem,
                "error": str(e)
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
        try:
            logger.info(f"⚖️ 开始决策分析: {decision_context[:50]}...")
            
            # 构建决策分析问题
            decision_problem = f"""
决策背景：{decision_context}

可选方案：
{chr(10).join([f"{i+1}. {option}" for i, option in enumerate(options)])}

{f'评估标准：{", ".join(criteria)}' if criteria else ''}

请进行结构化的决策分析，包括：
1. 方案分析
2. 风险评估
3. 推荐方案
4. 实施建议
            """
            
            result = await self.sequential_thinking(
                problem=decision_problem,
                context="这是一个决策分析任务",
                max_steps=6,
                thinking_style="analytical"
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "decision_context": decision_context,
                    "options": options,
                    "criteria": criteria,
                    "analysis": result.get("thinking_steps", []),
                    "recommendation": result.get("conclusion", ""),
                    "confidence": result.get("confidence", 0.0),
                    "alternatives": result.get("alternatives", [])
                }
            else:
                return result
        
        except Exception as e:
            logger.error(f"❌ 决策分析异常: {e}")
            return {
                "success": False,
                "decision_context": decision_context,
                "error": str(e)
            }
    
    async def creative_brainstorming(
        self,
        topic: str,
        constraints: Optional[List[str]] = None,
        num_ideas: int = 10
    ) -> Dict[str, Any]:
        """
        创意头脑风暴 - 生成创新想法
        
        Args:
            topic: 主题
            constraints: 约束条件
            num_ideas: 期望想法数量
            
        Returns:
            头脑风暴结果
        """
        try:
            logger.info(f"💡 开始创意头脑风暴: {topic[:50]}...")
            
            brainstorming_problem = f"""
主题：{topic}

{f'约束条件：{", ".join(constraints)}' if constraints else ''}

请进行创意头脑风暴，生成 {num_ideas} 个创新想法。
每个想法应该包括：
1. 核心概念
2. 实现方式
3. 潜在价值
4. 挑战与风险
            """
            
            result = await self.sequential_thinking(
                problem=brainstorming_problem,
                context="这是一个创意头脑风暴任务",
                max_steps=num_ideas + 2,
                thinking_style="creative"
            )
            
            if result.get("success"):
                # 提取创意想法
                ideas = []
                thinking_steps = result.get("thinking_steps", [])
                
                for step in thinking_steps:
                    if "idea" in step.get("content", "").lower() or "想法" in step.get("content", ""):
                        ideas.append(step)
                
                return {
                    "success": True,
                    "topic": topic,
                    "constraints": constraints,
                    "ideas": ideas[:num_ideas],
                    "total_generated": len(ideas),
                    "thinking_process": thinking_steps,
                    "confidence": result.get("confidence", 0.0)
                }
            else:
                return result
        
        except Exception as e:
            logger.error(f"❌ 创意头脑风暴异常: {e}")
            return {
                "success": False,
                "topic": topic,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试简单的顺序思考
            test_result = await self.sequential_thinking(
                problem="测试问题：1+1等于多少？",
                max_steps=2
            )
            
            return {
                "status": "healthy",
                "service": "sequential_thinking",
                "tools_available": len(self.tools),
                "test_result": test_result.get("success", False),
                "message": "Sequential Thinking 服务正常"
            }
        except Exception as e:
            return {
                "status": "error",
                "service": "sequential_thinking",
                "error": str(e),
                "message": "Sequential Thinking 服务异常"
            }
