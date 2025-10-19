#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库学习器
自动从对话中学习高质量Q&A，更新知识库
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class KnowledgePoint:
    """知识点"""
    question: str
    answer: str
    confidence: float
    type: str
    source_session: str
    created_at: str
    auto_approved: bool = False
    reviewed: bool = False
    useful_count: int = 0  # 被检索命中次数


class KnowledgeLearner:
    """知识库自动学习器"""
    
    def __init__(self, kb_service=None, db=None, review_threshold: float = 0.80):
        """
        初始化知识库学习器
        
        Args:
            kb_service: 知识库服务
            db: 数据库实例
            review_threshold: 自动入库的质量阈值（>= 此值自动入库）
        """
        self.kb_service = kb_service
        self.db = db
        self.review_threshold = review_threshold
        
        # 统计数据
        self.stats = {
            'total_extracted': 0,
            'auto_added': 0,
            'pending_review': 0,
            'rejected': 0
        }
    
    def process_knowledge_points(self, knowledge_points: List[Dict],
                                session_id: str) -> Dict:
        """
        处理知识点
        
        Args:
            knowledge_points: 知识点列表
            session_id: 来源会话ID
        
        Returns:
            处理结果统计
        """
        if not knowledge_points:
            logger.info(f"[{session_id}] 无有效知识点")
            return {'auto_added': 0, 'pending_review': 0}
        
        logger.info(f"[{session_id}] 处理 {len(knowledge_points)} 个知识点")
        
        auto_added = []
        pending_review = []
        rejected = []
        
        for kp in knowledge_points:
            confidence = kp['confidence']
            
            # 根据置信度决定处理方式
            if confidence >= self.review_threshold:
                # 高质量，自动入库
                success = self._add_to_knowledge_base(kp, session_id, auto_approved=True)
                if success:
                    auto_added.append(kp)
                    logger.info(f"✅ 自动入库: {kp['question'][:30]}... (置信度: {confidence:.2f})")
            
            elif confidence >= 0.70:
                # 中等质量，待审核
                self._add_to_review_queue(kp, session_id)
                pending_review.append(kp)
                logger.info(f"📋 待审核: {kp['question'][:30]}... (置信度: {confidence:.2f})")
            
            else:
                # 低质量，拒绝
                rejected.append(kp)
                logger.debug(f"❌ 拒绝: {kp['question'][:30]}... (置信度过低: {confidence:.2f})")
        
        # 更新统计
        self.stats['total_extracted'] += len(knowledge_points)
        self.stats['auto_added'] += len(auto_added)
        self.stats['pending_review'] += len(pending_review)
        self.stats['rejected'] += len(rejected)
        
        return {
            'auto_added': len(auto_added),
            'pending_review': len(pending_review),
            'rejected': len(rejected)
        }
    
    def _add_to_knowledge_base(self, kp: Dict, session_id: str, 
                               auto_approved: bool = False) -> bool:
        """
        添加到知识库
        
        Args:
            kp: 知识点
            session_id: 来源会话
            auto_approved: 是否自动批准
        
        Returns:
            是否成功
        """
        try:
            if self.kb_service:
                # 如果有知识库服务，添加到向量数据库
                self.kb_service.add_document(
                    content=kp['answer'],
                    metadata={
                        'question': kp['question'],
                        'type': kp['type'],
                        'source': 'conversation_learning',
                        'source_session': session_id,
                        'auto_approved': auto_approved,
                        'confidence': kp['confidence'],
                        'created_at': datetime.now().isoformat()
                    }
                )
            
            # 同时保存到数据库
            if self.db:
                self._save_to_db(kp, session_id, auto_approved)
            
            return True
        
        except Exception as e:
            logger.error(f"添加到知识库失败: {e}")
            return False
    
    def _save_to_db(self, kp: Dict, session_id: str, auto_approved: bool):
        """保存到数据库"""
        conn = self.db.connect()
        cursor = conn.cursor()
        
        # 创建知识点表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                confidence REAL,
                type TEXT,
                source_session TEXT,
                auto_approved INTEGER,
                reviewed INTEGER DEFAULT 0,
                useful_count INTEGER DEFAULT 0,
                created_at TEXT,
                reviewed_at TEXT,
                UNIQUE(question, answer)
            )
        """)
        
        try:
            cursor.execute("""
                INSERT INTO learned_knowledge 
                (question, answer, confidence, type, source_session, 
                 auto_approved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                kp['question'],
                kp['answer'],
                kp['confidence'],
                kp['type'],
                session_id,
                1 if auto_approved else 0,
                datetime.now().isoformat()
            ))
            
            conn.commit()
        except Exception as e:
            logger.warning(f"保存到数据库失败（可能重复）: {e}")
        finally:
            conn.close()
    
    def _add_to_review_queue(self, kp: Dict, session_id: str):
        """添加到待审核队列"""
        # 保存到数据库的待审核表
        if not self.db:
            return
        
        conn = self.db.connect()
        cursor = conn.cursor()
        
        # 创建待审核表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_review_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                confidence REAL,
                type TEXT,
                source_session TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                reviewed_at TEXT,
                reviewer TEXT,
                UNIQUE(question, answer)
            )
        """)
        
        try:
            cursor.execute("""
                INSERT INTO knowledge_review_queue
                (question, answer, confidence, type, source_session, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                kp['question'],
                kp['answer'],
                kp['confidence'],
                kp['type'],
                session_id,
                datetime.now().isoformat()
            ))
            
            conn.commit()
        except Exception as e:
            logger.warning(f"添加到审核队列失败: {e}")
        finally:
            conn.close()
    
    def get_review_queue(self, limit: int = 50) -> List[Dict]:
        """获取待审核队列"""
        if not self.db:
            return []
        
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, question, answer, confidence, type, 
                   source_session, created_at
            FROM knowledge_review_queue
            WHERE status = 'pending'
            ORDER BY confidence DESC, created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'question': row[1],
                'answer': row[2],
                'confidence': row[3],
                'type': row[4],
                'source_session': row[5],
                'created_at': row[6]
            }
            for row in rows
        ]
    
    def approve_knowledge(self, knowledge_id: int, reviewer: str = 'system') -> bool:
        """批准知识点"""
        if not self.db:
            return False
        
        conn = self.db.connect()
        cursor = conn.cursor()
        
        # 获取知识点
        cursor.execute("""
            SELECT question, answer, confidence, type, source_session
            FROM knowledge_review_queue
            WHERE id = ?
        """, (knowledge_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        
        kp = {
            'question': row[0],
            'answer': row[1],
            'confidence': row[2],
            'type': row[3]
        }
        
        # 添加到知识库
        success = self._add_to_knowledge_base(kp, row[4], auto_approved=False)
        
        if success:
            # 更新审核状态
            cursor.execute("""
                UPDATE knowledge_review_queue
                SET status = 'approved',
                    reviewed_at = ?,
                    reviewer = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), reviewer, knowledge_id))
            
            conn.commit()
        
        conn.close()
        return success
    
    def reject_knowledge(self, knowledge_id: int, reviewer: str = 'system') -> bool:
        """拒绝知识点"""
        if not self.db:
            return False
        
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE knowledge_review_queue
            SET status = 'rejected',
                reviewed_at = ?,
                reviewer = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), reviewer, knowledge_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_statistics(self) -> Dict:
        """获取学习统计"""
        stats = self.stats.copy()
        
        # 从数据库获取额外统计
        if self.db:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # 已学习知识点总数
            cursor.execute("SELECT COUNT(*) FROM learned_knowledge WHERE 1")
            stats['total_learned'] = cursor.fetchone()[0] if cursor.fetchone() else 0
            
            # 待审核数量
            cursor.execute("""
                SELECT COUNT(*) 
                FROM knowledge_review_queue 
                WHERE status = 'pending'
            """)
            stats['pending_count'] = cursor.fetchone()[0] if cursor.fetchone() else 0
            
            conn.close()
        
        return stats


# 使用示例
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # 模拟知识点
    knowledge_points = [
        {
            'question': '充电桩支持多少功率？',
            'answer': '我们支持7kW到120kW不等，可根据您的需求选择',
            'confidence': 0.85,
            'type': '产品咨询'
        },
        {
            'question': '安装需要什么条件？',
            'answer': '需要：1.固定停车位 2.物业同意 3.电力容量足够',
            'confidence': 0.90,
            'type': '使用咨询'
        }
    ]
    
    # 初始化学习器
    learner = KnowledgeLearner(review_threshold=0.80)
    
    # 处理知识点
    result = learner.process_knowledge_points(knowledge_points, 'test_session')
    
    print(f"处理结果:")
    print(f"  自动入库: {result['auto_added']}")
    print(f"  待审核: {result['pending_review']}")
    print(f"  拒绝: {result['rejected']}")
    
    # 统计
    stats = learner.get_statistics()
    print(f"\n学习统计: {stats}")

