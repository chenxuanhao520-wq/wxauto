"""
首轮对话智能路由器
判断首轮对话是否需要调用大模型，优化成本
"""
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FirstTurnDecision:
    """首轮判断结果"""
    use_llm: bool
    reason: str
    suggested_action: str  # rule_engine | template_assembly | llm_light | llm_strong | query_erp
    suggested_model: Optional[str] = None
    suggested_response: Optional[str] = None
    confidence: float = 0.0


class FirstTurnRouter:
    """
    首轮对话智能路由器
    
    功能：
    1. 识别简单问候（规则引擎处理）
    2. 识别业务查询（ERP系统处理）
    3. 基于知识库置信度分流
    4. 智能选择是否调用大模型
    
    目标：
    - 35%请求不调用大模型（节省成本）
    - 40%请求用便宜模型
    - 25%请求用强模型
    - 用户体验不打折
    """
    
    def __init__(self):
        """初始化首轮路由器"""
        # 简单问候规则库
        self.simple_greetings = {
            '你好': '您好！我是AI客服助手，很高兴为您服务！有什么可以帮您的吗？',
            '您好': '您好！我是AI客服助手，很高兴为您服务！有什么可以帮您的吗？',
            '在吗': '在的！请问有什么可以帮您？',
            '在不在': '在的！请问有什么可以帮您？',
            '你好吗': '我很好，谢谢！有什么可以帮您的吗？',
            '谢谢': '不客气！还有其他需要帮助的吗？',
            '感谢': '不客气！还有其他需要帮助的吗？',
            'hi': '您好！有什么可以帮您？',
            'hello': '您好！有什么可以帮您？',
            '早上好': '早上好！有什么可以帮您？',
            '晚上好': '晚上好！有什么可以帮您？',
            '你是谁': '我是AI客服助手，专门为您解答产品相关问题。',
            '什么': '请问您想了解什么呢？我可以帮您解答产品、使用、售后等方面的问题。'
        }
        
        # 业务查询模式
        self.business_patterns = {
            'order_query': {
                'pattern': r'(订单|单号).*?([A-Z]{2}\d{8,}|\d{10,})',
                'action': 'query_erp_order',
                'response_template': '正在为您查询订单{order_no}的信息...'
            },
            'logistics_query': {
                'pattern': r'(物流|快递|发货|配送).*?(\d{10,})?',
                'action': 'query_erp_logistics',
                'response_template': '正在为您查询物流信息...'
            },
            'invoice_query': {
                'pattern': r'(发票|开票|票据)',
                'action': 'query_erp_invoice',
                'response_template': '正在为您查询发票信息...'
            }
        }
        
        # 转人工关键词
        self.transfer_keywords = [
            '人工', '转人工', '人工客服', '转接', '找人',
            '投诉', '经理', '主管', '领导'
        ]
        
        logger.info("首轮智能路由器初始化完成")
    
    async def decide(
        self,
        message: str,
        evidences: Optional[List] = None,
        kb_confidence: float = 0.0
    ) -> FirstTurnDecision:
        """
        判断首轮对话的处理方式
        
        Args:
            message: 用户消息
            evidences: 知识库检索结果
            kb_confidence: 知识库置信度
        
        Returns:
            FirstTurnDecision: 判断结果
        """
        message_clean = message.strip()
        
        # 1. 简单问候检查（20%场景）
        if message_clean in self.simple_greetings:
            logger.info(f"✅ 简单问候: {message_clean}")
            return FirstTurnDecision(
                use_llm=False,
                reason='简单问候，规则引擎处理',
                suggested_action='rule_engine',
                suggested_response=self.simple_greetings[message_clean],
                confidence=1.0
            )
        
        # 2. 超短消息检查
        if len(message_clean) <= 3:
            logger.info(f"✅ 超短消息: {message_clean}")
            return FirstTurnDecision(
                use_llm=False,
                reason='超短消息，规则引擎处理',
                suggested_action='rule_engine',
                suggested_response='您好！请问有什么可以帮您的吗？',
                confidence=0.9
            )
        
        # 3. 转人工请求检查
        if any(keyword in message for keyword in self.transfer_keywords):
            logger.info(f"✅ 转人工请求: {message[:30]}...")
            return FirstTurnDecision(
                use_llm=False,
                reason='用户请求人工客服',
                suggested_action='transfer_human',
                suggested_response='正在为您转接人工客服，请稍候...',
                confidence=1.0
            )
        
        # 4. 业务查询检查（5%场景）
        for query_type, config in self.business_patterns.items():
            match = re.search(config['pattern'], message)
            if match:
                logger.info(f"✅ 业务查询: {query_type}")
                
                # 提取参数
                params = match.groups() if match.groups() else None
                response = config['response_template']
                if params and len(params) > 1:
                    response = response.format(order_no=params[1])
                
                return FirstTurnDecision(
                    use_llm=False,
                    reason=f'业务查询（{query_type}），ERP系统处理',
                    suggested_action=config['action'],
                    suggested_response=response,
                    confidence=0.95
                )
        
        # 5. 知识库置信度分流（75%场景）
        if evidences and kb_confidence > 0:
            
            if kb_confidence >= 0.95:
                # 超高置信度：模板组装（10%场景）
                logger.info(f"✅ 知识库超高置信度: {kb_confidence:.2f}")
                return FirstTurnDecision(
                    use_llm=False,
                    reason=f'知识库超高置信度（{kb_confidence:.2f}），模板组装',
                    suggested_action='template_assembly',
                    confidence=kb_confidence
                )
            
            elif kb_confidence >= 0.75:
                # 中等置信度：轻量LLM（40%场景）
                logger.info(f"🤖 知识库中等置信度: {kb_confidence:.2f}，使用轻量LLM")
                return FirstTurnDecision(
                    use_llm=True,
                    reason=f'知识库中等置信度（{kb_confidence:.2f}），轻量LLM组织答案',
                    suggested_action='llm_light',
                    suggested_model='qwen-turbo',
                    confidence=kb_confidence
                )
            
            else:
                # 低置信度：强LLM（25%场景）
                logger.info(f"🤖 知识库低置信度: {kb_confidence:.2f}，使用强LLM")
                return FirstTurnDecision(
                    use_llm=True,
                    reason=f'知识库低置信度（{kb_confidence:.2f}），强LLM深度理解',
                    suggested_action='llm_strong',
                    suggested_model='deepseek',
                    confidence=kb_confidence
                )
        
        # 6. 默认：使用LLM
        logger.info(f"🤖 无知识库证据，使用LLM")
        return FirstTurnDecision(
            use_llm=True,
            reason='无知识库证据，LLM生成回答',
            suggested_action='llm_light',
            suggested_model='qwen-turbo',
            confidence=0.5
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'simple_greetings_count': len(self.simple_greetings),
            'business_patterns_count': len(self.business_patterns),
            'transfer_keywords_count': len(self.transfer_keywords)
        }
