#!/usr/bin/env python3
"""
智能分析模块
实现大模型深度思考、问题分析、智能回复等功能
"""

# 强制 UTF-8 编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from customer_manager import Customer, customer_manager
from modules.ai_gateway.gateway import AIGateway

@dataclass
class AnalysisResult:
    """分析结果"""
    question_type: str          # 问题类型
    urgency_level: int         # 紧急程度 1-5
    complexity: str            # 复杂度
    needs_human: bool          # 是否需要人工
    confidence: float          # 分析置信度
    recommended_strategy: str  # 推荐策略
    satisfaction_prediction: float  # 满意度预测
    risk_warning: str          # 风险提示
    key_points: List[str]      # 关键要点
    suggested_tags: List[str]  # 建议标签

@dataclass
class SmartResponse:
    """智能回复"""
    response_text: str         # 回复内容
    response_type: str         # 回复类型
    evidence_used: List[str]   # 使用的证据
    confidence: float          # 回复置信度
    follow_up_suggestions: List[str]  # 后续建议
    escalation_needed: bool    # 是否需要升级

class SmartAnalyzer:
    """智能分析器"""
    
    def __init__(self):
        self.ai_gateway = AIGateway()
        self.analysis_cache = {}  # 分析结果缓存
    
    def deep_think_analysis(self, customer: Customer, question: str, 
                          knowledge_result: Dict) -> AnalysisResult:
        """深度思考分析"""
        
        # 构建分析提示
        analysis_prompt = self._build_analysis_prompt(
            customer, question, knowledge_result
        )
        
        try:
            # 调用大模型进行分析
            response = self.ai_gateway.generate_response(
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            # 解析分析结果
            analysis_data = self._parse_analysis_response(response.content)
            
            # 创建分析结果对象
            result = AnalysisResult(
                question_type=analysis_data.get("question_type", "未知"),
                urgency_level=analysis_data.get("urgency_level", 3),
                complexity=analysis_data.get("complexity", "中等"),
                needs_human=analysis_data.get("needs_human", False),
                confidence=analysis_data.get("confidence", 0.7),
                recommended_strategy=analysis_data.get("recommended_strategy", "标准回复"),
                satisfaction_prediction=analysis_data.get("satisfaction_prediction", 0.8),
                risk_warning=analysis_data.get("risk_warning", "无"),
                key_points=analysis_data.get("key_points", []),
                suggested_tags=analysis_data.get("suggested_tags", [])
            )
            
            # 缓存分析结果
            cache_key = f"{customer.customer_id}_{hash(question)}"
            self.analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"深度分析失败: {e}")
            # 返回默认分析结果
            return self._get_default_analysis(customer, question)
    
    def _build_analysis_prompt(self, customer: Customer, question: str, 
                             knowledge_result: Dict) -> str:
        """构建分析提示"""
        
        # 客户历史信息
        customer_history = f"""
客户档案：
- 编号：{customer.customer_id}
- 姓名：{customer.name}
- 群聊：{customer.group_name} ({customer.group_type})
- 注册时间：{customer.registration_time.strftime('%Y-%m-%d')}
- 历史问题：{customer.total_questions} 个
- 解决率：{customer.solved_questions}/{customer.total_questions} ({customer.solved_questions/customer.total_questions*100:.1f}% if customer.total_questions > 0 else 0)
- 转人工次数：{customer.handoff_count}
- 优先级：{customer.priority}/5
- 标签：{', '.join(customer.tags)}
"""
        
        # 知识库信息
        knowledge_info = f"""
知识库检索结果：
- 检索到 {len(knowledge_result.get('documents', []))} 个相关文档
- 最高置信度：{knowledge_result.get('confidence', 0):.2f}
- 证据摘要：{knowledge_result.get('evidence_summary', '无相关证据')}
"""
        
        # 分析要求
        analysis_requirements = """
请作为专业的客服分析系统，对客户问题进行深度分析。

分析维度：
1. 问题分类：技术问题/产品咨询/服务投诉/功能请求/其他
2. 紧急程度：1(低)-5(高)
3. 复杂度：简单/中等/复杂
4. 处理策略：自动回复/人工介入/升级处理
5. 满意度预测：0.0-1.0
6. 风险评估：潜在风险提示
7. 关键要点：问题的核心要点
8. 建议标签：用于分类和跟踪

请以JSON格式返回分析结果：
{
    "question_type": "技术问题",
    "urgency_level": 3,
    "complexity": "中等",
    "needs_human": false,
    "confidence": 0.85,
    "recommended_strategy": "基于知识库提供详细解答",
    "satisfaction_prediction": 0.85,
    "risk_warning": "无特殊风险",
    "key_points": ["设备安装", "配置问题"],
    "suggested_tags": ["安装", "配置", "技术支持"]
}
"""
        
        return f"{customer_history}\n\n当前问题：{question}\n\n{knowledge_info}\n\n{analysis_requirements}"
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """解析分析响应"""
        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 如果没有找到JSON，尝试从文本中提取信息
                return self._extract_info_from_text(response_text)
        except Exception as e:
            print(f"解析分析响应失败: {e}")
            return self._get_default_analysis_data()
    
    def _extract_info_from_text(self, text: str) -> Dict:
        """从文本中提取分析信息"""
        # 简单的关键词匹配提取
        result = self._get_default_analysis_data()
        
        # 问题类型识别
        if any(word in text.lower() for word in ['技术', '故障', '错误', 'bug']):
            result["question_type"] = "技术问题"
        elif any(word in text.lower() for word in ['价格', '费用', '收费']):
            result["question_type"] = "产品咨询"
        elif any(word in text.lower() for word in ['投诉', '不满', '问题']):
            result["question_type"] = "服务投诉"
        
        # 紧急程度识别
        if any(word in text.lower() for word in ['紧急', 'urgent', '立即']):
            result["urgency_level"] = 5
        elif any(word in text.lower() for word in ['尽快', '重要']):
            result["urgency_level"] = 4
        
        return result
    
    def _get_default_analysis_data(self) -> Dict:
        """获取默认分析数据"""
        return {
            "question_type": "技术问题",
            "urgency_level": 3,
            "complexity": "中等",
            "needs_human": False,
            "confidence": 0.7,
            "recommended_strategy": "标准回复",
            "satisfaction_prediction": 0.8,
            "risk_warning": "无",
            "key_points": [],
            "suggested_tags": []
        }
    
    def _get_default_analysis(self, customer: Customer, question: str) -> AnalysisResult:
        """获取默认分析结果"""
        return AnalysisResult(
            question_type="技术问题",
            urgency_level=3,
            complexity="中等",
            needs_human=False,
            confidence=0.5,
            recommended_strategy="标准回复",
            satisfaction_prediction=0.7,
            risk_warning="分析失败，使用默认策略",
            key_points=[],
            suggested_tags=[]
        )
    
    def generate_smart_response(self, customer: Customer, question: str,
                              analysis: AnalysisResult, knowledge_result: Dict) -> SmartResponse:
        """生成智能回复"""
        
        # 构建回复提示
        response_prompt = self._build_response_prompt(
            customer, question, analysis, knowledge_result
        )
        
        try:
            # 调用大模型生成回复
            response = self.ai_gateway.generate_response(
                messages=[{"role": "user", "content": response_prompt}],
                max_tokens=600,
                temperature=0.4
            )
            
            # 解析回复内容
            response_data = self._parse_response(response.content)
            
            # 创建智能回复对象
            smart_response = SmartResponse(
                response_text=response_data.get("response", "抱歉，我暂时无法回答您的问题。"),
                response_type=response_data.get("type", "standard"),
                evidence_used=response_data.get("evidence", []),
                confidence=response_data.get("confidence", 0.7),
                follow_up_suggestions=response_data.get("follow_up", []),
                escalation_needed=analysis.needs_human
            )
            
            return smart_response
            
        except Exception as e:
            print(f"生成智能回复失败: {e}")
            return self._get_default_response(customer, question, analysis)
    
    def _build_response_prompt(self, customer: Customer, question: str,
                             analysis: AnalysisResult, knowledge_result: Dict) -> str:
        """构建回复提示"""
        
        prompt = f"""
作为专业的客服助手，请为客户生成合适的回复。

客户信息：
- 编号：{customer.customer_id}
- 姓名：{customer.name}
- 群聊类型：{customer.group_type}
- 优先级：{customer.priority}/5

问题分析：
- 问题类型：{analysis.question_type}
- 紧急程度：{analysis.urgency_level}/5
- 复杂度：{analysis.complexity}
- 置信度：{analysis.confidence:.2f}

知识库证据：
{knowledge_result.get('evidence_summary', '无相关证据')}

回复要求：
1. 语气要专业、友好、耐心
2. 针对客户优先级调整回复详细程度
3. 使用知识库证据支持回答
4. 提供清晰的步骤指导
5. 如有必要，建议人工介入
6. 结尾提供后续帮助建议

请生成回复内容，并以JSON格式返回：
{{
    "response": "回复内容",
    "type": "standard|detailed|escalation",
    "evidence": ["使用的证据1", "使用的证据2"],
    "confidence": 0.85,
    "follow_up": ["后续建议1", "后续建议2"]
}}
"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """解析回复内容"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "response": response_text,
                    "type": "standard",
                    "evidence": [],
                    "confidence": 0.7,
                    "follow_up": []
                }
        except Exception as e:
            print(f"解析回复失败: {e}")
            return {
                "response": response_text,
                "type": "standard",
                "evidence": [],
                "confidence": 0.5,
                "follow_up": []
            }
    
    def _get_default_response(self, customer: Customer, question: str,
                            analysis: AnalysisResult) -> SmartResponse:
        """获取默认回复"""
        return SmartResponse(
            response_text="感谢您的咨询，我正在为您查找相关信息，请稍等片刻。",
            response_type="standard",
            evidence_used=[],
            confidence=0.5,
            follow_up_suggestions=["如有其他问题，请随时联系"],
            escalation_needed=analysis.needs_human
        )
    
    def should_escalate(self, analysis: AnalysisResult, customer: Customer) -> bool:
        """判断是否需要升级处理"""
        # VIP客户优先处理
        if customer.group_type == "vip" and analysis.urgency_level >= 4:
            return True
        
        # 高紧急程度问题
        if analysis.urgency_level >= 5:
            return True
        
        # 客户明确要求人工
        if analysis.needs_human:
            return True
        
        # 客户历史转人工次数过多
        if customer.handoff_count >= 3:
            return True
        
        return False
    
    def get_escalation_message(self, customer: Customer, analysis: AnalysisResult) -> str:
        """获取升级处理消息"""
        if customer.group_type == "vip":
            return f"尊敬的VIP客户{customer.name}，您的问题已升级到专属客服团队，我们将优先为您处理。"
        else:
            return f"{customer.name}，您的问题比较复杂，已为您转接专业客服，请稍等片刻。"

# 全局实例
smart_analyzer = SmartAnalyzer()

if __name__ == "__main__":
    # 测试智能分析
    from customer_manager import customer_manager
    
    # 获取测试客户
    customers = customer_manager.get_customer_list(limit=1)
    if customers:
        customer = customers[0]
        
        # 测试问题
        question = "我的设备无法正常启动，显示错误代码E03"
        
        # 模拟知识库结果
        knowledge_result = {
            "documents": ["设备故障排除指南"],
            "confidence": 0.8,
            "evidence_summary": "E03错误通常是通信故障，需要检查连接"
        }
        
        # 进行深度分析
        analysis = smart_analyzer.deep_think_analysis(customer, question, knowledge_result)
        print(f"分析结果：{analysis}")
        
        # 生成智能回复
        response = smart_analyzer.generate_smart_response(customer, question, analysis, knowledge_result)
        print(f"智能回复：{response.response_text}")
    else:
        print("没有找到测试客户")
