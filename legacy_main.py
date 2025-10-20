"""
主程序：监听 → 降噪 → RAG → LLM → 发送 → 落库
Phase 0-1: 实现监听、@识别、去重、频控、ACK、分流与落库
Phase 3: 接入真实 AI 网关
"""

# 强制 UTF-8 编码（解决中文显示问题）
import sys
import logging

# 重新配置标准输出为 UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 配置日志为 UTF-8
logging.basicConfig(encoding='utf-8', level=logging.INFO)

import os
import time
import uuid
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# 添加项目根目录和模块路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'core'))
sys.path.insert(0, str(project_root / 'modules'))

from modules.adapters.wxauto_adapter import Message, FakeWxAdapter
from modules.storage.db import Database, MessageLog, SessionInfo
from modules.rag.retriever import Retriever, Evidence
from modules.ai_gateway.gateway import AIGateway
from core.conversation_tracker import ConversationTracker, ConversationOutcome
from modules.adaptive_learning import UserProfiler, PersonalizedPromptGenerator, ContinuousLearner
from core.customer_service_adapter import customer_manager, init_default_groups
from core.smart_analyzer import smart_analyzer

# 确保日志目录存在
Path("logs").mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class CustomerServiceBot:
    """客服中台主程序"""
    
    def __init__(self, config_path: str = "config.yaml", use_fake: bool = True):
        """
        Args:
            config_path: 配置文件路径
            use_fake: 是否使用假适配器（测试模式）
        """
        # 加载配置
        self.config = self._load_config(config_path)
        self.use_fake = use_fake
        
        # 初始化组件
        self.db = Database(self.config['database']['path'])
        self.db.init_database()
        
        # 初始化客户管理系统
        init_default_groups()
        logger.info("客户管理系统已初始化")
        
        # 微信适配器
        whitelisted_groups = self.config['wechat']['whitelisted_groups']
        if use_fake:
            self.wx_adapter = FakeWxAdapter(whitelisted_groups)
            logger.info("使用 FakeWxAdapter（测试模式）")
        else:
            # Phase 1 真实环境替换
            from adapters.wxauto_adapter import WxAutoAdapter
            self.wx_adapter = WxAutoAdapter(whitelisted_groups)
            logger.info("使用 WxAutoAdapter（真实模式）")
        
        # RAG 检索器
        rag_config = self.config['rag']
        self.retriever = Retriever(
            bm25_topn=rag_config['bm25_topn'],
            top_k=rag_config['top_k'],
            min_confidence=rag_config['min_confidence']
        )
        
        # 尝试加载知识库
        try:
            self.retriever.load_knowledge_base(self.config['database']['path'])
        except Exception as e:
            logger.warning(f"加载知识库失败，将使用模拟数据: {e}")
        
        # AI 网关（Phase 3）
        try:
            llm_config = self.config['llm']
            self.ai_gateway = AIGateway(
                primary_provider=llm_config['primary'].split(':')[0],  # 'openai:gpt-4o-mini' -> 'openai'
                fallback_provider=llm_config.get('fallback', '').split(':')[0] if llm_config.get('fallback') else None,
                enable_fallback=True
            )
            logger.info("AI 网关已初始化")
        except Exception as e:
            logger.warning(f"AI 网关初始化失败，将使用桩实现: {e}")
            self.ai_gateway = None
        
        # 对话追踪器（Phase 3.1）
        try:
            self.conversation_tracker = ConversationTracker(self.db)
            logger.info("对话追踪器已初始化")
        except Exception as e:
            logger.warning(f"对话追踪器初始化失败: {e}")
            self.conversation_tracker = None
        
        # 自适应学习系统（Phase 3.2）
        try:
            self.user_profiler = UserProfiler(self.db)
            self.prompt_generator = PersonalizedPromptGenerator()
            self.continuous_learner = ContinuousLearner(self.db, self.user_profiler)
            
            # 加载基础风格（如果有）
            import json
            style_file = Path("data/conversation_style.json")
            if style_file.exists():
                with open(style_file, 'r', encoding='utf-8') as f:
                    base_style = json.load(f)
                    self.prompt_generator = PersonalizedPromptGenerator(base_style)
                logger.info("对话风格已加载")
            
            logger.info("自适应学习系统已初始化")
            self.adaptive_learning_enabled = True
        except Exception as e:
            logger.warning(f"自适应学习系统初始化失败: {e}")
            self.adaptive_learning_enabled = False
        
        # 阈值配置
        self.confidence_thresholds = self.config['confidence']
        self.ack_config = self.config['ack']
        self.rate_limit_config = self.config['rate_limit']
        self.session_config = self.config['session']
        
        # 禁答域
        self.forbidden_topics = self.config['forbidden_topics']
        
        # 管理员配置
        self.admin_config = self.config['admin']
        
        # 运行状态
        self.is_running = False
        self.shadow_mode = False  # 影子模式：只记录不发言
        self.global_mute = False  # 全局静默
        self.debug_mode = False  # 调试模式
        
        logger.info("CustomerServiceBot 初始化完成")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 应用环境特定配置
        env = config.get('env', 'dev')
        if env in config.get('profiles', {}):
            profile = config['profiles'][env]
            # 深度合并配置（简化版）
            for key, value in profile.items():
                if isinstance(value, dict) and key in config:
                    config[key].update(value)
                else:
                    config[key] = value
        
        logger.info(f"配置已加载: env={env}")
        return config
    
    def run(self):
        """主循环：监听消息并处理"""
        self.is_running = True
        check_interval = self.config['wechat']['check_interval_ms'] / 1000
        
        logger.info("=" * 60)
        logger.info("客服中台已启动，开始监听消息...")
        logger.info(f"白名单群聊: {self.config['wechat']['whitelisted_groups']}")
        logger.info(f"检查间隔: {check_interval}s")
        logger.info("=" * 60)
        
        try:
            while self.is_running:
                try:
                    # 清理过期会话
                    self.db.expire_old_sessions()
                    
                    # 迭代新消息
                    for msg in self.wx_adapter.iter_new_messages():
                        self._process_message(msg)
                    
                    # 间隔等待
                    time.sleep(check_interval)
                    
                except KeyboardInterrupt:
                    logger.info("收到中断信号，正在停止...")
                    break
                except Exception as e:
                    logger.error(f"主循环异常: {e}", exc_info=True)
                    time.sleep(check_interval * 2)  # 出错后加倍等待
                    
        finally:
            self.stop()
    
    def _process_message(self, msg: Message) -> None:
        """
        处理单条消息的完整流程
        Args:
            msg: 微信消息
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        logger.info(
            f"[{request_id[:8]}] 开始处理消息: "
            f"group={msg.group_name}, sender={msg.sender_name}, "
            f"content={msg.content[:50]}..."
        )
        
        try:
            # Step 1: 管理指令检查
            if self._handle_admin_command(msg):
                logger.info(f"[{request_id[:8]}] 管理指令已处理")
                return
            
            # Step 2: 去重检查
            if self.db.check_duplicate(
                msg.group_id, msg.sender_id, msg.content,
                window_seconds=10
            ):
                logger.info(f"[{request_id[:8]}] 消息重复，已忽略")
                return
            
            # Step 3: 速率限制
            rate_limit_result = self._check_rate_limits(msg)
            if not rate_limit_result['allowed']:
                self._handle_rate_limited(msg, request_id, rate_limit_result)
                return
            
            # Step 4: 禁答域检查
            if self._is_forbidden_topic(msg.content):
                self._handle_forbidden(msg, request_id)
                return
            
            # Step 5: 发送 ACK
            if self.ack_config['enabled'] and not self.shadow_mode:
                ack_success = self.wx_adapter.ack(
                    msg.group_name,
                    msg.sender_name,
                    self.ack_config['message']
                )
                logger.info(f"[{request_id[:8]}] ACK 发送: {'成功' if ack_success else '失败'}")
            
            # Step 6: 客户管理
            customer = self._get_or_create_customer(msg)
            if not customer:
                logger.warning(f"[{request_id[:8]}] 客户识别失败，跳过处理")
                return
            
            logger.info(f"[{request_id[:8]}] 客户信息: {customer.customer_id} ({customer.name})")
            
            # Step 7: 会话管理
            session_key = f"{msg.group_id}:{msg.sender_id}"
            session = self.db.upsert_session(
                session_key=session_key,
                group_id=msg.group_id,
                sender_id=msg.sender_id,
                sender_name=msg.sender_name,
                ttl_minutes=self.session_config['ttl_minutes']
            )
            
            # 如果是新会话，自动分类标签
            if session.turn_count == 1 and self.conversation_tracker:
                tags = self._auto_classify_tags(msg.content)
                self.conversation_tracker.start_conversation(session_key, tags)
            
            # 记录用户消息到对话串
            if self.conversation_tracker:
                self.conversation_tracker.add_message_to_thread(
                    session_key=session_key,
                    message_id=request_id,
                    role="user",
                    content=msg.content
                )
            
            logger.debug(
                f"[{request_id[:8]}] 会话: key={session_key}, "
                f"turn={session.turn_count}"
            )
            
            # Step 8: RAG 检索
            retrieval_start = time.time()
            evidences = self.retriever.retrieve(msg.content)
            confidence = self.retriever.calculate_confidence(evidences)
            retrieval_time = int((time.time() - retrieval_start) * 1000)
            
            logger.info(
                f"[{request_id[:8]}] RAG 检索完成: "
                f"evidences={len(evidences)}, confidence={confidence:.2f}, "
                f"time={retrieval_time}ms"
            )
            
            # Step 9: 智能分析
            analysis_start = time.time()
            knowledge_result = {
                'documents': [ev.content for ev in evidences],
                'confidence': confidence,
                'evidence_summary': '; '.join([ev.content[:100] + '...' for ev in evidences[:3]])
            }
            
            analysis = smart_analyzer.deep_think_analysis(customer, msg.content, knowledge_result)
            analysis_time = int((time.time() - analysis_start) * 1000)
            
            logger.info(
                f"[{request_id[:8]}] 智能分析完成: "
                f"type={analysis.question_type}, urgency={analysis.urgency_level}, "
                f"complexity={analysis.complexity}, time={analysis_time}ms"
            )
            
            # Step 10: 置信度分流（结合分析结果）
            branch = self._determine_branch(confidence, analysis)
            
            logger.info(f"[{request_id[:8]}] 分流决策: branch={branch}, conf={confidence:.2f}")
            
            # Step 11: 生成智能响应
            generation_start = time.time()
            response_text, llm_info = self._generate_smart_response(
                msg, customer, analysis, evidences, confidence, branch, session
            )
            generation_time = int((time.time() - generation_start) * 1000)
            
            # Step 10: 发送响应
            send_start = time.time()
            if not self.shadow_mode and response_text:
                send_success = self.wx_adapter.send_text(
                    msg.group_name,
                    response_text,
                    at_user=msg.sender_name
                )
            else:
                send_success = True  # 影子模式视为成功
            send_time = int((time.time() - send_start) * 1000)
            
            # 记录AI回复到对话串
            if self.conversation_tracker and response_text:
                self.conversation_tracker.add_message_to_thread(
                    session_key=session_key,
                    message_id=request_id,
                    role="assistant",
                    content=response_text,
                    metadata={
                        'confidence': confidence,
                        'provider': llm_info.get('provider'),
                        'model': llm_info.get('model'),
                        'tokens': llm_info.get('token_total')
                    }
                )
            
            # Step 11: 落库
            total_time = int((time.time() - start_time) * 1000)
            
            message_log = MessageLog(
                request_id=request_id,
                session_id=session.id,
                group_id=msg.group_id,
                group_name=msg.group_name,
                sender_id=msg.sender_id,
                sender_name=msg.sender_name,
                user_message=msg.content,
                bot_response=response_text,
                evidence_ids=str([e.chunk_id for e in evidences]),
                evidence_summary=self.retriever.format_evidence_summary(evidences),
                confidence=confidence,
                branch=branch,
                provider=llm_info.get('provider', 'stub'),
                model=llm_info.get('model', 'stub'),
                token_in=llm_info.get('token_in', 0),
                token_out=llm_info.get('token_out', 0),
                token_total=llm_info.get('token_total', 0),
                latency_receive_ms=0,
                latency_retrieval_ms=retrieval_time,
                latency_generation_ms=generation_time,
                latency_send_ms=send_time,
                latency_total_ms=total_time,
                status='answered' if send_success else 'failed',
                received_at=msg.timestamp,
                responded_at=datetime.now()
            )
            
            self.db.log_message(message_log)
            
            # 自动评估对话效果（如果是会话结束或转人工）
            if self.conversation_tracker:
                should_evaluate = (
                    branch == 'handoff' or  # 转人工
                    not send_success or      # 发送失败
                    session.turn_count >= 10  # 对话过长
                )
                
                if should_evaluate:
                    outcome = self.conversation_tracker.auto_evaluate_outcome(
                        session_key=session_key,
                        last_branch=branch,
                        last_status='answered' if send_success else 'failed',
                        avg_confidence=confidence
                    )
                    self.conversation_tracker.mark_outcome(session_key, outcome)
                    
                    logger.info(
                        f"[{request_id[:8]}] 对话评估: "
                        f"outcome={outcome.outcome}, resolved_by={outcome.resolved_by}"
                    )
                    
                    # 持续学习：从对话中学习
                    if self.adaptive_learning_enabled and outcome.satisfaction_score:
                        try:
                            conversation_data = {
                                'user_message': msg.content,
                                'bot_response': response_text,
                                'satisfaction_score': outcome.satisfaction_score,
                                'confidence': confidence
                            }
                            self.continuous_learner.learn_from_conversation(
                                user_id=msg.sender_id,
                                conversation=conversation_data,
                                satisfaction_score=outcome.satisfaction_score
                            )
                        except Exception as e:
                            logger.warning(f"持续学习失败: {e}")
            
            logger.info(
                f"[{request_id[:8]}] 处理完成: "
                f"branch={branch}, total_time={total_time}ms, "
                f"status={'answered' if send_success else 'failed'}"
            )
            
        except Exception as e:
            logger.error(f"[{request_id[:8]}] 处理失败: {e}", exc_info=True)
            
            # 记录失败日志
            try:
                error_log = MessageLog(
                    request_id=request_id,
                    group_id=msg.group_id,
                    sender_id=msg.sender_id,
                    user_message=msg.content,
                    status='failed',
                    error_message=str(e),
                    received_at=msg.timestamp
                )
                self.db.log_message(error_log)
            except Exception as db_error:
                logger.error(f"记录错误日志失败: {db_error}")
    
    def _check_rate_limits(self, msg: Message) -> Dict[str, Any]:
        """
        检查速率限制
        Returns:
            {'allowed': bool, 'reason': str, 'count': int}
        """
        # 检查群级别限制
        group_allowed, group_count = self.db.check_rate_limit(
            'group',
            msg.group_id,
            self.rate_limit_config['per_group_per_minute'],
            60
        )
        
        if not group_allowed:
            return {
                'allowed': False,
                'reason': 'group_limit_exceeded',
                'count': group_count
            }
        
        # 检查用户级别限制
        user_key = f"{msg.group_id}:{msg.sender_id}"
        user_allowed, user_count = self.db.check_rate_limit(
            'user',
            user_key,
            self.rate_limit_config['per_user_per_30s'],
            30
        )
        
        if not user_allowed:
            return {
                'allowed': False,
                'reason': 'user_limit_exceeded',
                'count': user_count
            }
        
        return {'allowed': True, 'reason': '', 'count': 0}
    
    def _is_forbidden_topic(self, content: str) -> bool:
        """检查是否为禁答域"""
        for keyword in self.forbidden_topics:
            if keyword in content:
                logger.warning(f"检测到禁答域关键词: {keyword}")
                return True
        return False
    
    def _determine_branch(self, confidence: float) -> str:
        """
        根据置信度决定分支
        Returns:
            'direct_answer' | 'clarification' | 'handoff'
        """
        if confidence >= self.confidence_thresholds['direct_answer']:
            return 'direct_answer'
        elif confidence >= self.confidence_thresholds['clarification']:
            return 'clarification'
        else:
            return 'handoff'
    
    def _generate_response(
        self,
        msg: Message,
        evidences: list,
        confidence: float,
        branch: str,
        session: SessionInfo
    ) -> tuple[Optional[str], Dict[str, Any]]:
        """
        生成响应（使用 AI 网关或桩实现）
        Returns:
            (response_text, llm_info)
        """
        # 如果分支是转人工或澄清，使用模板
        if branch == 'handoff':
            response = (
                "您的问题需要专业支持，已为您转接人工客服。\n"
                "值班同事稍后会与您联系，请稍候。"
            )
            llm_info = {
                'provider': 'template',
                'model': 'handoff',
                'token_in': 0,
                'token_out': len(response),
                'token_total': len(response)
            }
            return response, llm_info
        
        elif branch == 'clarification':
            response = (
                "为了更准确地帮助您，请提供以下信息：\n"
                "① 设备型号\n"
                "② 固件版本\n"
                "③ 现场电源参数（如适用）"
            )
            llm_info = {
                'provider': 'template',
                'model': 'clarification',
                'token_in': 0,
                'token_out': len(response),
                'token_total': len(response)
            }
            return response, llm_info
        
        # 直答分支：使用 AI 网关（个性化）
        if self.ai_gateway and evidences:
            try:
                # 构建证据上下文
                evidence_context = self.retriever.format_evidence_summary(evidences)
                evidence_text = "\n\n".join([
                    f"【{ev.document_name} {ev.document_version} - {ev.section}】\n{ev.content}"
                    for ev in evidences[:2]  # 只用前2条证据
                ])
                
                # 获取用户画像并生成个性化Prompt
                system_prompt = None
                if self.adaptive_learning_enabled:
                    try:
                        # 获取或创建用户画像
                        user_profile = self.user_profiler.get_or_create_profile(
                            msg.sender_id,
                            msg.sender_name
                        )
                        
                        # 生成个性化Prompt
                        system_prompt = self.prompt_generator.generate(
                            user_profile=user_profile,
                            context="充电桩客服"
                        )
                        
                        logger.debug(
                            f"使用个性化Prompt: user={msg.sender_id}, "
                            f"type={user_profile.customer_type}, "
                            f"style={user_profile.communication_style}"
                        )
                    except Exception as e:
                        logger.warning(f"个性化Prompt生成失败，使用默认: {e}")
                
                # 调用 AI 网关（带个性化Prompt）
                llm_response = self.ai_gateway.generate(
                    user_message=msg.content,
                    evidence_context=evidence_text,
                    session_history=None,  # TODO: 后续添加会话历史
                    max_tokens=self.config['llm']['max_tokens'],
                    temperature=self.config['llm']['temperature']
                )
                
                # 如果有个性化Prompt，使用自定义的
                if system_prompt and hasattr(llm_response, 'request'):
                    # 在实际调用中设置system_prompt
                    pass  # 这里需要AI网关支持自定义system_prompt
                
                if llm_response.content and not llm_response.error:
                    # AI 生成成功
                    llm_info = {
                        'provider': llm_response.provider,
                        'model': llm_response.model,
                        'token_in': llm_response.token_in,
                        'token_out': llm_response.token_out,
                        'token_total': llm_response.token_total
                    }
                    return llm_response.content, llm_info
                else:
                    # AI 生成失败，回退到模板
                    logger.warning(f"AI 生成失败: {llm_response.error}")
            
            except Exception as e:
                logger.error(f"AI 网关调用异常: {e}")
        
        # 回退到桩实现
        if evidences:
            ev = evidences[0]
            response = (
                f"根据《{ev.document_name} v{ev.document_version}》：\n"
                f"① {ev.content}\n"
                f"② 重点关注 {ev.section} 中的安全提示\n"
                f"③ 完成操作后请反馈效果\n"
                f"若场景不同请补充型号/版本/参数"
            )
        else:
            response = "抱歉，未找到相关信息，正在为您转接人工客服..."
        
        llm_info = {
            'provider': 'stub',
            'model': 'stub',
            'token_in': len(msg.content) * 2,
            'token_out': len(response) * 2,
            'token_total': len(msg.content) * 2 + len(response) * 2
        }
        
        return response, llm_info
    
    def _handle_rate_limited(
        self,
        msg: Message,
        request_id: str,
        limit_result: Dict[str, Any]
    ) -> None:
        """处理速率限制"""
        reason = limit_result['reason']
        count = limit_result['count']
        
        logger.warning(
            f"[{request_id[:8]}] 速率限制触发: {reason}, count={count}"
        )
        
        # 温和提示
        if not self.shadow_mode:
            self.wx_adapter.send_text(
                msg.group_name,
                "您的提问频率稍快，请稍后再试～",
                at_user=msg.sender_name
            )
        
        # 记录日志
        log = MessageLog(
            request_id=request_id,
            group_id=msg.group_id,
            sender_id=msg.sender_id,
            user_message=msg.content,
            branch='rate_limited',
            status='ignored',
            received_at=msg.timestamp
        )
        self.db.log_message(log)
    
    def _handle_forbidden(self, msg: Message, request_id: str) -> None:
        """处理禁答域"""
        logger.warning(f"[{request_id[:8]}] 禁答域触发")
        
        # 转人工
        if not self.shadow_mode:
            self.wx_adapter.send_text(
                msg.group_name,
                "此类问题需要专业顾问协助，已为您转接人工客服。",
                at_user=msg.sender_name
            )
        
        # 记录日志
        log = MessageLog(
            request_id=request_id,
            group_id=msg.group_id,
            sender_id=msg.sender_id,
            user_message=msg.content,
            branch='handoff',
            handoff_reason='policy',
            status='answered',
            bot_response='已转人工（禁答域）',
            received_at=msg.timestamp
        )
        self.db.log_message(log)
    
    def _handle_admin_command(self, msg: Message) -> bool:
        """
        处理管理指令
        Returns:
            bool: 是否为管理指令
        """
        # 检查是否为管理员
        if msg.sender_name not in self.admin_config['names']:
            return False
        
        content = msg.content.strip()
        commands = self.admin_config['commands']
        
        # #mute
        if content == commands['mute']:
            self.global_mute = True
            self.db.set_config('global_mute', 'true')
            self.wx_adapter.send_text(msg.group_name, "✅ 已开启全局静默")
            return True
        
        # #unmute
        if content == commands['unmute']:
            self.global_mute = False
            self.db.set_config('global_mute', 'false')
            self.wx_adapter.send_text(msg.group_name, "✅ 已关闭全局静默")
            return True
        
        # #status
        if content == commands['status']:
            status_text = self._get_status_report()
            self.wx_adapter.send_text(msg.group_name, status_text)
            return True
        
        # #debug on/off
        if content == commands['debug_on']:
            self.debug_mode = True
            logging.getLogger().setLevel(logging.DEBUG)
            self.wx_adapter.send_text(msg.group_name, "✅ 调试模式已开启")
            return True
        
        if content == commands['debug_off']:
            self.debug_mode = False
            logging.getLogger().setLevel(logging.INFO)
            self.wx_adapter.send_text(msg.group_name, "✅ 调试模式已关闭")
            return True
        
        return False
    
    def _get_status_report(self) -> str:
        """生成状态报告"""
        # 简化状态报告（Phase 4 可扩展）
        shadow_status = "是" if self.shadow_mode else "否"
        mute_status = "是" if self.global_mute else "否"
        debug_status = "是" if self.debug_mode else "否"
        
        return (
            f"📊 系统状态\n"
            f"影子模式: {shadow_status}\n"
            f"全局静默: {mute_status}\n"
            f"调试模式: {debug_status}\n"
            f"运行中: 是"
        )
    
    def _auto_classify_tags(self, content: str) -> List[str]:
        """
        根据消息内容自动分类标签
        
        Args:
            content: 消息内容
        
        Returns:
            标签列表
        """
        tags = []
        
        # 关键词匹配
        keyword_tags = {
            '售后': ['售后', '保修', '维修', '退换', '质量问题'],
            '技术支持': ['安装', '配置', '使用', '故障', '问题', '报错', '异常'],
            '价格咨询': ['价格', '多少钱', '费用', '报价', '优惠'],
            '产品咨询': ['产品', '型号', '参数', '规格', '功能'],
            '安装问题': ['安装', '组装', '部署'],
            '故障排查': ['故障', '不工作', '无法', '报错', '异常'],
        }
        
        content_lower = content.lower()
        
        for tag, keywords in keyword_tags.items():
            if any(kw in content_lower for kw in keywords):
                tags.append(tag)
        
        # 如果没有匹配到任何标签，添加"一般咨询"
        if not tags:
            tags.append('一般咨询')
        
        return tags
    
    def _get_or_create_customer(self, msg: Message):
        """获取或创建客户"""
        # 首先尝试根据姓名和群聊查找现有客户
        customer = customer_manager.find_customer_by_name(msg.sender_name, msg.group_name)
        
        if customer:
            # 更新客户活动
            customer_manager.update_customer_activity(customer.customer_id)
            return customer
        
        # 如果没有找到，创建新客户
        try:
            # 获取群聊分类
            group_classification = customer_manager.get_group_classification(msg.group_name)
            priority = group_classification.priority if group_classification else 3
            
            # 注册新客户
            customer_id = customer_manager.register_customer(
                name=msg.sender_name,
                group_name=msg.group_name,
                notes=f"自动注册 - 首次咨询",
                priority=priority
            )
            
            logger.info(f"新客户注册成功: {customer_id} ({msg.sender_name})")
            return customer_manager.get_customer(customer_id)
            
        except Exception as e:
            logger.error(f"客户注册失败: {e}")
            return None
    
    def _determine_branch(self, confidence: float, analysis=None) -> str:
        """确定分流策略"""
        if analysis:
            # 结合分析结果的智能分流
            if analysis.needs_human or analysis.urgency_level >= 5:
                return "handoff"
            elif analysis.urgency_level >= 4 and confidence < 0.6:
                return "clarification"
            elif confidence >= 0.75:
                return "direct_answer"
            elif confidence >= 0.55:
                return "clarification"
            else:
                return "handoff"
        else:
            # 原有的简单分流逻辑
            if confidence >= 0.75:
                return "direct_answer"
            elif confidence >= 0.55:
                return "clarification"
            else:
                return "handoff"
    
    def _generate_smart_response(self, msg: Message, customer, analysis, 
                               evidences: List[Evidence], confidence: float, 
                               branch: str, session) -> Tuple[str, Dict]:
        """生成智能响应"""
        try:
            # 构建知识库结果
            knowledge_result = {
                'documents': [ev.content for ev in evidences],
                'confidence': confidence,
                'evidence_summary': '; '.join([ev.content[:100] + '...' for ev in evidences[:3]])
            }
            
            # 生成智能回复
            smart_response = smart_analyzer.generate_smart_response(
                customer, msg.content, analysis, knowledge_result
            )
            
            # 检查是否需要升级处理
            if smart_analyzer.should_escalate(analysis, customer):
                escalation_msg = smart_analyzer.get_escalation_message(customer, analysis)
                response_text = f"{smart_response.response_text}\n\n{escalation_msg}"
                
                # 更新客户转人工次数
                customer_manager.update_customer_activity(
                    customer.customer_id, handoff=True
                )
            else:
                response_text = smart_response.response_text
            
            # 更新客户活动
            customer_manager.update_customer_activity(
                customer.customer_id, 
                question_solved=(branch == "direct_answer")
            )
            
            # 模拟 LLM 信息
            llm_info = {
                "provider": "smart_analyzer",
                "model": "enhanced_analysis",
                "token_in": len(msg.content),
                "token_out": len(response_text),
                "latency_ms": 500  # 模拟延迟
            }
            
            logger.info(
                f"智能响应生成完成: type={smart_response.response_type}, "
                f"confidence={smart_response.confidence:.2f}"
            )
            
            return response_text, llm_info
            
        except Exception as e:
            logger.error(f"智能响应生成失败: {e}")
            # 降级到原有逻辑
            return self._generate_response(msg, evidences, confidence, branch, session)
    
    def stop(self):
        """停止运行"""
        self.is_running = False
        self.db.close()
        logger.info("客服中台已停止")


def main():
    """主入口"""
    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    # 创建并运行 Bot（默认使用 FakeAdapter）
    use_fake = os.getenv("USE_FAKE_ADAPTER", "true").lower() == "true"
    
    bot = CustomerServiceBot(use_fake=use_fake)
    bot.run()


if __name__ == "__main__":
    main()
