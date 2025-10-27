#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能对话处理器 - 完整集成示例
展示如何使用上下文管理器处理实际对话
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

try:
    from .context_manager import (
        ContextManager,
        IntentClassifier,
        DialogueType
    )
except ImportError:
    from context_manager import (
        ContextManager,
        IntentClassifier,
        DialogueType
    )

logger = logging.getLogger(__name__)


class SmartDialogueHandler:
    """智能对话处理器（集成示例）"""
    
    def __init__(self, kb_service=None, erp_client=None, llm_client=None):
        """
        初始化对话处理器
        
        Args:
            kb_service: 知识库服务（可选）
            erp_client: ERP客户端（可选）
            llm_client: LLM客户端（可选）
        """
        # 核心组件
        self.context_mgr = ContextManager(max_age_minutes=30, hard_limit=20)
        self.classifier = IntentClassifier()
        
        # 外部服务（可选）
        self.kb_service = kb_service
        self.erp_client = erp_client
        self.llm_client = llm_client
        
        # 闲聊响应模板
        self.small_talk_templates = {
            '你好': '您好！有什么可以帮您的吗？😊',
            '您好': '您好！很高兴为您服务！',
            '谢谢': '不客气！很高兴能帮到您！',
            '感谢': '不用客气！有其他需要随时告诉我。',
            '再见': '再见！祝您生活愉快！👋',
            '拜拜': '拜拜！期待下次为您服务！',
            '好的': '嗯嗯，明白了！还有其他需要帮助的吗？',
            '收到': '好的！收到您的消息了。',
        }
    
    def process_message(self, contact_id: str, message: str, 
                       metadata: Dict = None) -> Dict:
        """
        处理用户消息（完整流程）
        
        Args:
            contact_id: 联系人ID
            message: 用户消息内容
            metadata: 附加元数据（可选）
        
        Returns:
            {
                'response': str,              # AI回复内容
                'type': str,                  # 对话类型
                'subtype': str,               # 子类型
                'action': str,                # 执行的动作
                'confidence': float,          # 置信度
                'context_length': int,        # 使用的上下文长度
                'topic_changed': bool,        # 是否主题切换
                'processing_time': float      # 处理时间（秒）
            }
        """
        start_time = datetime.now()
        
        # 1. 添加用户消息到上下文
        self.context_mgr.add_message(contact_id, message, role='user', metadata=metadata)
        
        # 2. 快速分类
        context_list = list(self.context_mgr.conversations.get(contact_id, []))
        classification = self.classifier.classify_detailed(message, context_list)
        
        dialogue_type = classification['type']
        subtype = classification['subtype']
        suggested_action = classification['suggested_action']
        confidence = classification['confidence']
        
        logger.info(
            f"[{contact_id}] 对话分类: {dialogue_type.value} - {subtype} "
            f"(置信度: {confidence:.2f})"
        )
        
        # 3. 检测主题切换
        topic_changed = self.context_mgr.check_topic_change(contact_id, message)
        
        if topic_changed:
            logger.info(f"[{contact_id}] 检测到主题切换，重置上下文")
            self.context_mgr.reset_context(contact_id, keep_summary=True)
            # 重新添加当前消息
            self.context_mgr.add_message(contact_id, message, role='user', metadata=metadata)
        
        # 4. 获取精简上下文
        relevant_context = self.context_mgr.get_relevant_context(
            contact_id,
            current_type=dialogue_type,
            max_tokens=2000
        )
        
        # 5. 根据对话类型处理
        if dialogue_type == DialogueType.SMALL_TALK:
            # 闲聊：使用模板快速响应
            response = self._handle_small_talk(message)
            action_taken = 'template_response'
        
        elif dialogue_type == DialogueType.CONSULTATION:
            # 咨询：查询知识库
            response = self._handle_consultation(
                message, relevant_context, suggested_action
            )
            action_taken = suggested_action or 'query_knowledge_base'
        
        elif dialogue_type == DialogueType.BUSINESS:
            # 业务：查询ERP
            response = self._handle_business(
                message, relevant_context, suggested_action
            )
            action_taken = suggested_action or 'query_erp'
        
        else:
            # 未知类型：通用处理
            response = self._handle_general(message, relevant_context)
            action_taken = 'general_llm'
        
        # 6. 保存AI回复到上下文
        self.context_mgr.add_message(contact_id, response, role='assistant')
        
        # 7. 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 8. 返回完整结果
        result = {
            'response': response,
            'type': dialogue_type.value,
            'subtype': subtype,
            'action': action_taken,
            'confidence': confidence,
            'context_length': len(relevant_context),
            'topic_changed': topic_changed,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(
            f"[{contact_id}] 处理完成: action={action_taken}, "
            f"context={len(relevant_context)}轮, time={processing_time:.3f}s"
        )
        
        return result
    
    def _handle_small_talk(self, message: str) -> str:
        """处理闲聊类对话"""
        # 使用模板匹配
        for keyword, response in self.small_talk_templates.items():
            if keyword in message:
                return response
        
        # 默认响应
        default_responses = [
            "嗯嗯，明白了！",
            "好的！还有其他需要帮助的吗？",
            "收到！😊"
        ]
        
        import random
        return random.choice(default_responses)
    
    def _handle_consultation(self, message: str, 
                            context: List[Dict],
                            suggested_action: str) -> str:
        """处理咨询类对话"""
        # 1. 获取结构化上下文
        contact_id = self._get_contact_id_from_context(context)
        structured_ctx = self.context_mgr.get_structured_context(contact_id)
        
        # 2. 查询知识库（如果有）
        if self.kb_service:
            try:
                kb_results = self.kb_service.search(
                    query=message,
                    top_k=3
                )
                kb_content = self._format_kb_results(kb_results)
            except Exception as e:
                logger.error(f"知识库查询失败: {e}")
                kb_content = "知识库暂时无法访问"
        else:
            kb_content = "（知识库服务未配置）"
        
        # 3. 构建LLM prompt（如果有）
        if self.llm_client:
            prompt = f"""你是一个专业的客服助手。

**对话摘要**: {structured_ctx['summary']}

**用户问题**: {message}

**知识库参考**:
{kb_content}

请基于知识库内容回答用户问题，保持专业和友好。如果知识库中没有相关信息，请诚实告知。
"""
            try:
                response = self.llm_client.generate(prompt, max_tokens=500)
                return response
            except Exception as e:
                logger.error(f"LLM调用失败: {e}")
                return "抱歉，我暂时无法回答这个问题，请稍后再试。"
        
        # 4. 降级处理：返回知识库结果
        if kb_content and kb_content != "知识库暂时无法访问":
            return f"根据我们的资料：\n\n{kb_content}\n\n还有其他问题吗？"
        
        return "抱歉，我暂时无法回答这个问题。您可以联系人工客服获取帮助。"
    
    def _handle_business(self, message: str, 
                        context: List[Dict],
                        suggested_action: str) -> str:
        """处理业务类对话"""
        # 获取结构化上下文
        contact_id = self._get_contact_id_from_context(context)
        structured_ctx = self.context_mgr.get_structured_context(contact_id)
        entities = structured_ctx['entities']
        
        # 根据建议动作查询ERP
        if not self.erp_client:
            return "抱歉，业务系统暂时无法访问，请稍后再试或联系人工客服。"
        
        try:
            if suggested_action == 'query_erp_order':
                # 订单查询
                order_no = entities.get('order_no', [None])[0]
                if order_no:
                    order_info = self.erp_client.get_order_detail(order_no)
                    return self._format_order_info(order_info)
                else:
                    return "请提供订单号，我帮您查询。格式如：WX20250119001"
            
            elif suggested_action == 'query_erp_inventory':
                # 库存查询
                product = entities.get('product', [None])[0]
                if product:
                    inventory = self.erp_client.get_inventory(product)
                    return f"产品 {product} 当前库存：{inventory.get('quantity', '未知')} 件"
                else:
                    return "请告诉我要查询哪个产品的库存？"
            
            elif suggested_action == 'query_erp_price':
                # 价格查询
                product = entities.get('product', [None])[0]
                if product:
                    price_info = self.erp_client.get_price(product)
                    return f"产品 {product} 价格：¥{price_info.get('price', '请咨询客服')}"
                else:
                    return "请告诉我要查询哪个产品的价格？"
            
            else:
                return "正在为您处理业务请求，请稍候..."
        
        except Exception as e:
            logger.error(f"ERP查询失败: {e}")
            return "抱歉，业务查询失败，请稍后再试或联系人工客服。"
    
    def _handle_general(self, message: str, context: List[Dict]) -> str:
        """通用LLM处理"""
        if not self.llm_client:
            return "收到您的消息，我们会尽快为您处理。"
        
        # 获取上下文摘要
        contact_id = self._get_contact_id_from_context(context)
        summary = self.context_mgr.get_context_summary(contact_id)
        
        prompt = f"""**对话摘要**: {summary}

**用户消息**: {message}

请给出专业、友好的回复。
"""
        
        try:
            return self.llm_client.generate(prompt)
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return "收到您的消息，我会尽快为您处理。"
    
    def _get_contact_id_from_context(self, context: List[Dict]) -> Optional[str]:
        """从上下文中获取联系人ID"""
        for conv_id, messages in self.context_mgr.conversations.items():
            if list(messages) == context:
                return conv_id
        return None
    
    def _format_kb_results(self, results: List[Dict]) -> str:
        """格式化知识库结果"""
        if not results:
            return "暂无相关资料"
        
        formatted = []
        for i, result in enumerate(results, 1):
            content = result.get('content', '')[:200]
            formatted.append(f"{i}. {content}")
        
        return "\n".join(formatted)
    
    def _format_order_info(self, order: Dict) -> str:
        """格式化订单信息"""
        return f"""📦 订单信息

订单号：{order.get('order_no', '未知')}
状态：{order.get('status', '未知')}
物流：{order.get('logistics', '暂无物流信息')}
预计送达：{order.get('eta', '请咨询客服')}

需要其他帮助吗？
"""
    
    def get_conversation_stats(self, contact_id: str) -> Dict:
        """获取对话统计信息"""
        if contact_id not in self.context_mgr.conversations:
            return {
                'total_messages': 0,
                'summary': '暂无对话记录'
            }
        
        messages = list(self.context_mgr.conversations[contact_id])
        structured = self.context_mgr.get_structured_context(contact_id)
        
        user_messages = sum(1 for m in messages if m.get('role') == 'user')
        assistant_messages = sum(1 for m in messages if m.get('role') == 'assistant')
        
        # 统计对话类型分布
        type_count = {}
        for msg in messages:
            msg_type = msg.get('type', 'unknown')
            type_count[msg_type] = type_count.get(msg_type, 0) + 1
        
        return {
            'total_messages': len(messages),
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'type_distribution': type_count,
            'entities': structured['entities'],
            'last_topic': structured['last_topic'],
            'summary': structured['summary']
        }


# ==================== 使用示例 ====================

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化处理器（不使用外部服务）
    handler = SmartDialogueHandler()
    
    contact_id = "wx_test_user"
    
    print("=" * 60)
    print("智能对话处理器测试")
    print("=" * 60)
    
    # 测试对话
    test_messages = [
        "你好",
        "你们的充电桩支持多少功率？",
        "安装需要什么条件？",
        "价格多少？",
        "对了，我想查一下订单WX20250119001的物流",
        "谢谢"
    ]
    
    for i, msg in enumerate(test_messages, 1):
        print(f"\n{'─' * 60}")
        print(f"第{i}轮对话")
        print(f"{'─' * 60}")
        print(f"👤 用户: {msg}")
        
        # 处理消息
        result = handler.process_message(contact_id, msg)
        
        print(f"🤖 AI: {result['response']}")
        print(f"\n📊 分析:")
        print(f"   - 类型: {result['type']} - {result['subtype']}")
        print(f"   - 动作: {result['action']}")
        print(f"   - 置信度: {result['confidence']:.2f}")
        print(f"   - 上下文: {result['context_length']}轮")
        print(f"   - 主题切换: {'是' if result['topic_changed'] else '否'}")
        print(f"   - 耗时: {result['processing_time']:.3f}秒")
    
    # 显示对话统计
    print(f"\n{'=' * 60}")
    print("对话统计")
    print(f"{'=' * 60}")
    stats = handler.get_conversation_stats(contact_id)
    print(f"总消息数: {stats['total_messages']}")
    print(f"用户消息: {stats['user_messages']}")
    print(f"AI消息: {stats['assistant_messages']}")
    print(f"类型分布: {stats['type_distribution']}")
    print(f"提取实体: {stats['entities']}")
    print(f"\n摘要:\n{stats['summary']}")

