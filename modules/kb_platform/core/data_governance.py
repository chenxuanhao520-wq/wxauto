"""
数据治理模块
负责知识库数据的治理策略、统计分析和质量控制
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class GovernanceRule:
    """治理规则"""
    rule_id: str
    name: str
    description: str
    rule_type: str  # quality, duplicate, format, content
    threshold: float
    enabled: bool = True
    created_at: datetime = None


@dataclass
class UploadStats:
    """上传统计"""
    document_id: str
    upload_time: datetime
    total_chunks: int
    accepted_chunks: int
    rejected_chunks: int
    avg_quality: float
    processing_time: float


class DataGovernance:
    """
    数据治理核心类
    
    功能：
    1. 定义和执行治理规则
    2. 统计分析知识库质量
    3. 监控数据健康状态
    4. 提供治理建议
    """
    
    def __init__(self):
        """初始化数据治理"""
        self.governance_rules = self._init_default_rules()
        self.upload_stats: List[UploadStats] = []
        
        logger.info("数据治理模块初始化完成")
    
    def _init_default_rules(self) -> List[GovernanceRule]:
        """初始化默认治理规则"""
        rules = [
            GovernanceRule(
                rule_id="quality_threshold",
                name="质量阈值规则",
                description="知识块质量分数必须达到阈值",
                rule_type="quality",
                threshold=0.75
            ),
            GovernanceRule(
                rule_id="duplicate_check",
                name="重复检测规则",
                description="禁止重复内容进入知识库",
                rule_type="duplicate",
                threshold=0.9
            ),
            GovernanceRule(
                rule_id="min_length",
                name="最小长度规则",
                description="知识块内容不能太短",
                rule_type="format",
                threshold=10  # 最少10个字符
            ),
            GovernanceRule(
                rule_id="max_length",
                name="最大长度规则",
                description="知识块内容不能太长",
                rule_type="format",
                threshold=2000  # 最多2000个字符
            ),
            GovernanceRule(
                rule_id="content_quality",
                name="内容质量规则",
                description="内容必须包含有效信息",
                rule_type="content",
                threshold=0.6
            )
        ]
        
        return rules
    
    async def apply_governance_rules(
        self,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        应用治理规则
        
        Args:
            chunks: 知识块列表
        
        Returns:
            {
                'accepted_chunks': List[Dict],
                'rejected_chunks': List[Dict],
                'rule_violations': Dict[str, List],
                'governance_summary': Dict
            }
        """
        accepted_chunks = []
        rejected_chunks = []
        rule_violations = {rule.rule_id: [] for rule in self.governance_rules if rule.enabled}
        
        for chunk in chunks:
            chunk_violations = []
            chunk_accepted = True
            
            # 应用所有启用的规则
            for rule in self.governance_rules:
                if not rule.enabled:
                    continue
                
                violation = await self._check_rule_violation(rule, chunk)
                if violation:
                    chunk_violations.append(violation)
                    rule_violations[rule.rule_id].append(violation)
                    chunk_accepted = False
            
            # 根据规则结果分类
            if chunk_accepted:
                accepted_chunks.append(chunk)
            else:
                chunk['violations'] = chunk_violations
                rejected_chunks.append(chunk)
        
        # 生成治理摘要
        governance_summary = {
            'total_chunks': len(chunks),
            'accepted_chunks': len(accepted_chunks),
            'rejected_chunks': len(rejected_chunks),
            'acceptance_rate': len(accepted_chunks) / len(chunks) if chunks else 0,
            'rule_violation_counts': {
                rule_id: len(violations) 
                for rule_id, violations in rule_violations.items()
            }
        }
        
        logger.info(
            f"治理规则应用完成: {len(accepted_chunks)}/{len(chunks)} 通过 "
            f"({governance_summary['acceptance_rate']:.1%})"
        )
        
        return {
            'accepted_chunks': accepted_chunks,
            'rejected_chunks': rejected_chunks,
            'rule_violations': rule_violations,
            'governance_summary': governance_summary
        }
    
    async def record_upload_stats(
        self,
        document_id: str,
        total_chunks: int,
        accepted_chunks: int,
        avg_quality: float,
        processing_time: float = 0.0
    ):
        """记录上传统计"""
        stats = UploadStats(
            document_id=document_id,
            upload_time=datetime.now(),
            total_chunks=total_chunks,
            accepted_chunks=accepted_chunks,
            rejected_chunks=total_chunks - accepted_chunks,
            avg_quality=avg_quality,
            processing_time=processing_time
        )
        
        self.upload_stats.append(stats)
        
        # 保持最近1000条记录
        if len(self.upload_stats) > 1000:
            self.upload_stats = self.upload_stats[-1000:]
    
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        if not self.upload_stats:
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'avg_acceptance_rate': 0.0,
                'avg_quality_score': 0.0,
                'recent_trends': {}
            }
        
        # 基础统计
        total_documents = len(self.upload_stats)
        total_chunks = sum(stats.total_chunks for stats in self.upload_stats)
        total_accepted = sum(stats.accepted_chunks for stats in self.upload_stats)
        
        avg_acceptance_rate = total_accepted / total_chunks if total_chunks > 0 else 0
        avg_quality_score = sum(stats.avg_quality for stats in self.upload_stats) / total_documents
        
        # 最近趋势（最近30天）
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_stats = [s for s in self.upload_stats if s.upload_time >= thirty_days_ago]
        
        recent_trends = {
            'documents_last_30d': len(recent_stats),
            'chunks_last_30d': sum(s.total_chunks for s in recent_stats),
            'avg_quality_last_30d': sum(s.avg_quality for s in recent_stats) / len(recent_stats) if recent_stats else 0
        }
        
        return {
            'total_documents': total_documents,
            'total_chunks': total_chunks,
            'total_accepted_chunks': total_accepted,
            'avg_acceptance_rate': avg_acceptance_rate,
            'avg_quality_score': avg_quality_score,
            'recent_trends': recent_trends,
            'governance_rules': [
                {
                    'rule_id': rule.rule_id,
                    'name': rule.name,
                    'enabled': rule.enabled,
                    'threshold': rule.threshold
                }
                for rule in self.governance_rules
            ]
        }
    
    async def generate_governance_report(self) -> Dict[str, Any]:
        """生成治理报告"""
        stats = await self.get_knowledge_stats()
        
        # 规则违规分析
        rule_performance = {}
        for rule in self.governance_rules:
            if rule.enabled:
                # 这里可以添加更详细的规则性能分析
                rule_performance[rule.rule_id] = {
                    'name': rule.name,
                    'threshold': rule.threshold,
                    'violation_rate': 0.0  # 需要从实际数据计算
                }
        
        # 质量趋势分析
        quality_trends = self._analyze_quality_trends()
        
        # 治理建议
        recommendations = await self._generate_recommendations(stats)
        
        return {
            'report_time': datetime.now().isoformat(),
            'summary': stats,
            'rule_performance': rule_performance,
            'quality_trends': quality_trends,
            'recommendations': recommendations
        }
    
    async def _check_rule_violation(
        self,
        rule: GovernanceRule,
        chunk: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """检查规则违规"""
        try:
            if rule.rule_type == "quality":
                if chunk.get('quality_score', 0) < rule.threshold:
                    return {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.name,
                        'violation_type': 'quality_threshold',
                        'actual_value': chunk.get('quality_score', 0),
                        'threshold': rule.threshold,
                        'message': f"质量分数 {chunk.get('quality_score', 0):.2f} 低于阈值 {rule.threshold}"
                    }
            
            elif rule.rule_type == "format":
                content = chunk.get('content', '')
                if rule.rule_id == "min_length" and len(content) < rule.threshold:
                    return {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.name,
                        'violation_type': 'min_length',
                        'actual_value': len(content),
                        'threshold': rule.threshold,
                        'message': f"内容长度 {len(content)} 低于最小长度 {rule.threshold}"
                    }
                elif rule.rule_id == "max_length" and len(content) > rule.threshold:
                    return {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.name,
                        'violation_type': 'max_length',
                        'actual_value': len(content),
                        'threshold': rule.threshold,
                        'message': f"内容长度 {len(content)} 超过最大长度 {rule.threshold}"
                    }
            
            elif rule.rule_type == "content":
                # 内容质量检查（简化版）
                content = chunk.get('content', '')
                if len(content.strip()) == 0:
                    return {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.name,
                        'violation_type': 'empty_content',
                        'actual_value': 0,
                        'threshold': rule.threshold,
                        'message': "内容为空"
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"检查规则违规失败: {e}")
            return None
    
    def _analyze_quality_trends(self) -> Dict[str, Any]:
        """分析质量趋势"""
        if not self.upload_stats:
            return {}
        
        # 按时间分组分析
        daily_quality = {}
        for stats in self.upload_stats:
            date_key = stats.upload_time.date().isoformat()
            if date_key not in daily_quality:
                daily_quality[date_key] = []
            daily_quality[date_key].append(stats.avg_quality)
        
        # 计算每日平均质量
        daily_avg_quality = {
            date: sum(qualities) / len(qualities)
            for date, qualities in daily_quality.items()
        }
        
        return {
            'daily_quality': daily_avg_quality,
            'trend_direction': 'stable'  # 简化实现
        }
    
    async def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成治理建议"""
        recommendations = []
        
        if stats['avg_acceptance_rate'] < 0.8:
            recommendations.append(
                "文档接受率较低，建议检查文档质量和治理规则设置"
            )
        
        if stats['avg_quality_score'] < 0.7:
            recommendations.append(
                "平均质量分数偏低，建议优化文档预处理流程"
            )
        
        if stats['recent_trends']['documents_last_30d'] == 0:
            recommendations.append(
                "最近30天没有新文档上传，建议检查上传流程"
            )
        
        return recommendations
