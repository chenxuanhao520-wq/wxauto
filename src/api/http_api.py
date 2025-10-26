from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from src.services.customer_service import CustomerService
from src.repositories.customer_repository import CustomerRepository
from src.services.message_service import MessageService, MessageContext
from src.services.knowledge_service import KnowledgeService


app = FastAPI(title="Wxauto API", version="3.2")


class MessageRequest(BaseModel):
    message: str
    sender_name: str
    sender_id: str
    group_name: str = ""
    group_id: str = ""


class MessageResult(BaseModel):
    request_id: str
    response_text: str
    branch: str
    confidence: float
    latency_ms: int


# 依赖实例（最小可运行，真实项目中通过DI容器构造）
customer_repository = CustomerRepository()
customer_service = CustomerService(repository=customer_repository)
knowledge_service = KnowledgeService()
message_service = MessageService(
    customer_service=customer_service,
    rag_retriever=knowledge_service,
    ai_gateway=None,
    config={}
)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/messages", response_model=MessageResult)
async def handle_message(req: MessageRequest) -> MessageResult:
    context = MessageContext(
        request_id=req.sender_id,
        message=req.message,
        sender_name=req.sender_name,
        sender_id=req.sender_id,
        group_name=req.group_name,
        group_id=req.group_id,
    )
    res = await message_service.process_message(context)
    return MessageResult(
        request_id=res.request_id,
        response_text=res.response_text,
        branch=res.branch,
        confidence=res.confidence,
        latency_ms=res.latency_ms,
    )
