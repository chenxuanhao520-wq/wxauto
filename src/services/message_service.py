"""消息处理服务（业务编排层）"""
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.services.customer_service import CustomerService
from src.models import Customer


@dataclass
class MessageContext:
    """消息上下文"""
    request_id: str
    message: str
    sender_name: str
    sender_id: str
    group_name: str
    group_id: str
    customer: Optional[Customer] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MessageResponse:
    """消息响应"""
    request_id: str
    response_text: str
    branch: str  # direct_answer | clarification | handoff | forbidden | rate_limited
    confidence: float
    evidence: List[Dict[str, Any]] = None
    latency_ms: int = 0
    provider: str = ""
    model: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'response_text': self.response_text,
            'branch': self.branch,
            'confidence': self.confidence,
            'evidence': self.evidence or [],
            'latency_ms': self.latency_ms,
            'provider': self.provider,
            'model': self.model
        }


class MessageService:
    """消息处理服务（编排层）
    
    职责：
    - 消息处理流程编排
    - 客户识别与管理
    - RAG检索协调
    - AI调用协调
    - 速率限制与禁答域检查
    - 统一错误处理
    """
    
    def __init__(
        self,
        customer_service: CustomerService,
        rag_retriever=None,
        ai_gateway=None,
        config: Dict[str, Any] = None
    ):
        self.customer_service = customer_service
        self.rag = rag_retriever
        self.ai_gateway = ai_gateway
        self.config = config or {}
        
        # 速率限制器（简化版，可扩展为Redis）
        self.rate_limiter = {}
    
    async def process_message(self, context: MessageContext) -> MessageResponse:
        """处理消息的完整流程
        
        流程：
        1. 客户识别/创建
        2. 管理员指令检查
        3. 去重检查（由调用方负责）
        4. 速率限制检查
        5. 禁答域检查
        6. RAG知识检索
        7. AI生成回复
        8. 记录客户活动
        """
        start_time = time.time()
        
        try:
            # Step 1: 客户识别
            customer = self.customer_service.get_or_create_customer(
                name=context.sender_name,
                group_name=context.group_name,
                notes=f"首次咨询于 {context.timestamp}"
            )
            context.customer = customer
            
            # Step 2: 管理员指令检查
            if self._is_admin_command(context.message):
                return self._handle_admin_command(context)
            
            # Step 3: 速率限制检查
            if not self._check_rate_limit(context):
                return MessageResponse(
                    request_id=context.request_id,
                    response_text="您的提问频率过高，请稍后再试。",
                    branch="rate_limited",
                    confidence=1.0,
                    latency_ms=int((time.time() - start_time) * 1000)
                )
            
            # Step 4: 禁答域检查
            if self._is_forbidden_topic(context.message):
                return MessageResponse(
                    request_id=context.request_id,
                    response_text="抱歉，该问题涉及敏感话题，请联系人工客服。",
                    branch="forbidden",
                    confidence=1.0,
                    latency_ms=int((time.time() - start_time) * 1000)
                )
            
            # Step 5: RAG检索（如果可用）
            evidence = []
            confidence = 0.5
            if self.rag:
                try:
                    evidence = await self._retrieve_knowledge(context.message)
                    if evidence:
                        confidence = evidence[0].get('score', 0.5)
                except Exception as e:
                    print(f"RAG检索失败: {e}")
            
            # Step 6: AI生成回复（如果可用）
            response_text = "收到您的问题，我们会尽快回复。"
            provider = "default"
            model = "default"
            
            if self.ai_gateway:
                try:
                    ai_response = await self._generate_ai_response(
                        context.message,
                        evidence,
                        context.customer
                    )
                    response_text = ai_response.get('text', response_text)
                    provider = ai_response.get('provider', provider)
                    model = ai_response.get('model', model)
                    confidence = ai_response.get('confidence', confidence)
                except Exception as e:
                    print(f"AI生成失败: {e}")
            
            # Step 7: 确定分支
            branch = self._determine_branch(confidence)
            
            # Step 8: 记录客户活动
            solved = (branch == "direct_answer")
            self.customer_service.record_question(customer.customer_id, solved=solved)
            
            # Step 9: 自动打标签
            self.customer_service.auto_tag_by_content(customer.customer_id, context.message)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return MessageResponse(
                request_id=context.request_id,
                response_text=response_text,
                branch=branch,
                confidence=confidence,
                evidence=evidence,
                latency_ms=latency_ms,
                provider=provider,
                model=model
            )
        
        except Exception as e:
            print(f"消息处理异常: {e}")
            return MessageResponse(
                request_id=context.request_id,
                response_text="抱歉，系统遇到错误，请稍后再试。",
                branch="error",
                confidence=0.0,
                latency_ms=int((time.time() - start_time) * 1000)
            )
    
    # ============================================================
    # 私有方法
    # ============================================================
    
    def _is_admin_command(self, message: str) -> bool:
        """检查是否为管理员指令"""
        admin_commands = self.config.get('admin', {}).get('commands', {})
        return any(message.startswith(cmd) for cmd in admin_commands.values())
    
    def _handle_admin_command(self, context: MessageContext) -> MessageResponse:
        """处理管理员指令"""
        # 简化实现，实际应检查权限
        return MessageResponse(
            request_id=context.request_id,
            response_text="管理员指令已执行。",
            branch="admin_command",
            confidence=1.0
        )
    
    def _check_rate_limit(self, context: MessageContext) -> bool:
        """检查速率限制"""
        rate_limit = self.config.get('rate_limit', {})
        per_user_limit = rate_limit.get('per_user_per_30s', 1)
        
        # 简化实现：内存计数（生产环境应使用Redis）
        key = f"{context.group_id}:{context.sender_id}"
        now = time.time()
        
        if key not in self.rate_limiter:
            self.rate_limiter[key] = []
        
        # 清理30秒前的记录
        self.rate_limiter[key] = [t for t in self.rate_limiter[key] if now - t < 30]
        
        # 检查是否超限
        if len(self.rate_limiter[key]) >= per_user_limit:
            return False
        
        # 记录本次请求
        self.rate_limiter[key].append(now)
        return True
    
    def _is_forbidden_topic(self, message: str) -> bool:
        """检查是否为禁答域"""
        forbidden_topics = self.config.get('forbidden_topics', [])
        return any(topic in message for topic in forbidden_topics)
    
    async def _retrieve_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """RAG知识检索"""
        if not self.rag:
            return []
        
        # 调用RAG检索器
        results = self.rag.retrieve(query)
        
        # 格式化为统一格式
        evidence = []
        for result in results[:4]:  # 取前4个
            evidence.append({
                'content': result.get('content', ''),
                'source': result.get('source', ''),
                'score': result.get('score', 0.0)
            })
        
        return evidence
    
    async def _generate_ai_response(
        self,
        query: str,
        evidence: List[Dict[str, Any]],
        customer: Customer
    ) -> Dict[str, Any]:
        """AI生成回复"""
        if not self.ai_gateway:
            return {'text': '抱歉，AI服务暂不可用。'}
        
        # 构建提示词
        system_prompt = self.config.get('ai', {}).get('system_prompt', '')
        evidence_text = '\n'.join([f"- {e['content']}" for e in evidence[:3]])
        
        prompt = f"""
用户问题：{query}

相关知识：
{evidence_text}

请基于上述知识回答用户问题。
"""
        
        # 调用AI网关
        response = await self.ai_gateway.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=self.config.get('ai', {}).get('max_tokens', 512)
        )
        
        return response
    
    def _determine_branch(self, confidence: float) -> str:
        """确定分流分支"""
        thresholds = self.config.get('confidence', {})
        direct_answer_threshold = thresholds.get('direct_answer', 0.75)
        clarification_threshold = thresholds.get('clarification', 0.55)
        
        if confidence >= direct_answer_threshold:
            return "direct_answer"
        elif confidence >= clarification_threshold:
            return "clarification"
        else:
            return "handoff"

