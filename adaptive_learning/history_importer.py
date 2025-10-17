"""
历史聊天记录导入器
从微信聊天记录中提取对话风格
"""
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class HistoryImporter:
    """
    历史记录导入器
    
    支持：
    1. 微信备份数据库（MsgBackup.db）
    2. WeChatMsg导出的SQLite
    3. 文本格式的对话记录
    """
    
    def import_from_wechat_backup(
        self,
        backup_file: str,
        target_groups: List[str] = None
    ) -> List[Dict]:
        """
        从微信备份导入
        
        Args:
            backup_file: 微信备份文件路径
            target_groups: 目标群聊列表
        
        Returns:
            对话列表
        """
        if not Path(backup_file).exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_file}")
        
        try:
            conn = sqlite3.connect(backup_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查询消息（适配不同的备份格式）
            # 尝试常见的表结构
            conversations = []
            
            try:
                # 格式1：标准微信备份
                query = """
                    SELECT 
                        talker as chat_name,
                        content,
                        type,
                        createTime as timestamp,
                        isSend
                    FROM message
                    ORDER BY createTime
                """
                
                cursor.execute(query)
                
                for row in cursor.fetchall():
                    # 只处理文本消息
                    if row['type'] == 1:  # 1=文字
                        conversations.append({
                            'chat_name': row['chat_name'],
                            'content': row['content'],
                            'is_sent_by_me': row['isSend'] == 1,
                            'timestamp': row['timestamp']
                        })
            
            except sqlite3.Error:
                # 格式2：WeChatMsg导出
                try:
                    query = """
                        SELECT 
                            StrTalker as chat_name,
                            StrContent as content,
                            Type as type,
                            CreateTime as timestamp,
                            IsSender as is_sender
                        FROM MSG
                        WHERE Type = 1
                        ORDER BY CreateTime
                    """
                    
                    cursor.execute(query)
                    
                    for row in cursor.fetchall():
                        conversations.append({
                            'chat_name': row['chat_name'],
                            'content': row['content'],
                            'is_sent_by_me': row['is_sender'] == 1,
                            'timestamp': row['timestamp']
                        })
                
                except sqlite3.Error as e:
                    logger.error(f"无法解析备份文件：{e}")
                    raise ValueError("不支持的备份文件格式")
            
            conn.close()
            
            # 过滤目标群聊
            if target_groups:
                conversations = [
                    c for c in conversations
                    if c['chat_name'] in target_groups
                ]
            
            logger.info(f"导入历史记录成功：{len(conversations)}条消息")
            
            return conversations
            
        except Exception as e:
            logger.error(f"导入失败：{e}")
            raise
    
    def import_from_text(self, text_file: str) -> List[Dict]:
        """
        从文本文件导入
        
        格式：
        客户: 问题内容
        客服: 回答内容
        
        客户: ...
        客服: ...
        """
        conversations = []
        
        with open(text_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines) - 1:
            line = lines[i].strip()
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            
            if line.startswith('客户:') and next_line.startswith('客服:'):
                question = line.replace('客户:', '').strip()
                answer = next_line.replace('客服:', '').strip()
                
                conversations.append({
                    'question': question,
                    'answer': answer,
                    'is_qa_pair': True
                })
                
                i += 2
            else:
                i += 1
        
        logger.info(f"从文本导入：{len(conversations)}对对话")
        
        return conversations
    
    def extract_qa_pairs(self, conversations: List[Dict]) -> List[Dict]:
        """
        从对话流中提取Q&A对
        
        Args:
            conversations: 对话消息列表
        
        Returns:
            Q&A对列表
        """
        qa_pairs = []
        
        for i in range(len(conversations) - 1):
            current = conversations[i]
            next_msg = conversations[i + 1]
            
            # 客户问题 → 客服回答
            if (not current['is_sent_by_me'] and 
                next_msg['is_sent_by_me']):
                
                qa_pairs.append({
                    'question': current['content'],
                    'answer': next_msg['content'],
                    'timestamp': current['timestamp']
                })
        
        logger.info(f"提取Q&A对：{len(qa_pairs)}对")
        
        return qa_pairs
    
    def analyze_conversation_style(
        self,
        qa_pairs: List[Dict],
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        分析对话风格
        
        Args:
            qa_pairs: Q&A对列表
            use_llm: 是否使用大模型分析
        
        Returns:
            风格分析结果
        """
        if not qa_pairs:
            return {}
        
        if use_llm:
            return self._analyze_with_llm(qa_pairs)
        else:
            return self._analyze_with_rules(qa_pairs)
    
    def _analyze_with_llm(self, qa_pairs: List[Dict]) -> Dict:
        """使用大模型分析风格"""
        import random
        
        # 采样（避免太长）
        samples = random.sample(qa_pairs, min(30, len(qa_pairs)))
        
        # 构建对话文本
        dialogue_text = "\n\n".join([
            f"客户: {qa['question']}\n客服: {qa['answer']}"
            for qa in samples
        ])
        
        # 分析prompt
        analysis_prompt = f"""
分析以下客服对话，总结对话风格特征：

{dialogue_text}

请用JSON格式输出：
{{
  "tone": "正式/友好/随意",
  "common_phrases": ["常用词1", "常用词2", ...],
  "avg_length": 平均回复字数,
  "uses_emoji": true/false,
  "addressing": "称呼方式（您/你）",
  "response_pattern": "回复模式（简洁/详细）",
  "tone_keywords": "语气特点描述"
}}
"""
        
        try:
            from ai_gateway.gateway import AIGateway
            
            gateway = AIGateway(primary_provider="openai")
            response = gateway.generate(
                user_message=analysis_prompt,
                max_tokens=500
            )
            
            # 解析JSON
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                style = json.loads(json_match.group())
                logger.info("大模型分析风格完成")
                return style
            
        except Exception as e:
            logger.warning(f"大模型分析失败，使用规则分析: {e}")
        
        # 回退到规则分析
        return self._analyze_with_rules(qa_pairs)
    
    def _analyze_with_rules(self, qa_pairs: List[Dict]) -> Dict:
        """使用规则分析风格"""
        all_answers = [qa['answer'] for qa in qa_pairs]
        
        # 统计常用词
        from collections import Counter
        import re
        
        all_text = ' '.join(all_answers)
        words = re.findall(r'[\u4e00-\u9fa5]+', all_text)
        word_freq = Counter(words)
        common_phrases = [word for word, count in word_freq.most_common(20) if count > 2]
        
        # 平均长度
        avg_length = sum(len(answer) for answer in all_answers) / len(all_answers)
        
        # emoji使用
        uses_emoji = any(
            any(ord(c) > 0x1F600 for c in answer)
            for answer in all_answers
        )
        
        # 称呼方式
        addressing = "您" if "您" in all_text else "你"
        
        return {
            'tone': 'friendly',
            'common_phrases': common_phrases,
            'avg_length': int(avg_length),
            'uses_emoji': uses_emoji,
            'addressing': addressing,
            'response_pattern': 'concise' if avg_length < 150 else 'detailed',
            'tone_keywords': '友好、专业'
        }

