"""
RAG 与置信度分流测试
覆盖：三段阈值、证据格式化
"""
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.rag.retriever import Retriever, Evidence


@pytest.fixture
def retriever():
    """RAG 检索器 fixture"""
    return Retriever(
        bm25_topn=50,
        top_k=4,
        min_confidence=0.75
    )


def test_retriever_initialization(retriever):
    """测试检索器初始化"""
    assert retriever.bm25_topn == 50
    assert retriever.top_k == 4
    assert retriever.min_confidence == 0.75


def test_retrieve_high_confidence(retriever):
    """测试高置信度查询（安装类问题）"""
    question = "如何安装设备？"
    evidences = retriever.retrieve(question, k=3)
    
    assert len(evidences) > 0
    assert all(isinstance(e, Evidence) for e in evidences)
    
    # 检查证据结构
    ev = evidences[0]
    assert ev.chunk_id is not None
    assert ev.document_name is not None
    assert ev.content is not None
    assert 0 <= ev.score <= 1


def test_retrieve_medium_confidence(retriever):
    """测试中等置信度查询（故障类问题）"""
    question = "设备出现故障怎么办？"
    evidences = retriever.retrieve(question, k=3)
    
    assert len(evidences) > 0
    
    # 计算置信度
    confidence = retriever.calculate_confidence(evidences)
    assert 0.55 <= confidence < 0.75  # 应该落在中等区间


def test_retrieve_low_confidence(retriever):
    """测试低置信度查询（禁答域）"""
    question = "你们的产品价格是多少？"
    evidences = retriever.retrieve(question, k=3)
    
    # 可能返回证据，但置信度很低
    confidence = retriever.calculate_confidence(evidences) if evidences else 0.0
    assert confidence < 0.55  # 应该落在低置信度区间


def test_confidence_calculation_empty(retriever):
    """测试空证据列表的置信度"""
    confidence = retriever.calculate_confidence([])
    assert confidence == 0.0


def test_confidence_calculation_with_evidences(retriever):
    """测试有证据的置信度计算"""
    evidences = [
        Evidence(
            chunk_id="1",
            document_name="测试文档",
            document_version="v1.0",
            section="第1章",
            content="内容1",
            score=0.9
        ),
        Evidence(
            chunk_id="2",
            document_name="测试文档",
            document_version="v1.0",
            section="第2章",
            content="内容2",
            score=0.7
        )
    ]
    
    confidence = retriever.calculate_confidence(evidences)
    assert 0.7 <= confidence <= 0.9  # 应该基于得分范围


def test_evidence_summary_formatting(retriever):
    """测试证据摘要格式化"""
    evidences = [
        Evidence(
            chunk_id="1",
            document_name="产品手册",
            document_version="v2.1",
            section="安装指南",
            content="安装步骤...",
            score=0.9
        ),
        Evidence(
            chunk_id="2",
            document_name="故障排查",
            document_version="v1.5",
            section="常见问题",
            content="问题描述...",
            score=0.8
        )
    ]
    
    summary = retriever.format_evidence_summary(evidences)
    
    # 检查格式
    assert "1." in summary
    assert "2." in summary
    assert "产品手册" in summary
    assert "v2.1" in summary
    assert "安装指南" in summary
    assert "故障排查" in summary
    assert "v1.5" in summary


def test_evidence_summary_empty(retriever):
    """测试空证据摘要"""
    summary = retriever.format_evidence_summary([])
    assert summary == "无相关证据"


def test_retrieve_with_custom_k(retriever):
    """测试自定义 k 值"""
    question = "测试问题"
    
    # k=2
    evidences = retriever.retrieve(question, k=2)
    assert len(evidences) <= 2
    
    # k=5
    evidences = retriever.retrieve(question, k=5)
    assert len(evidences) <= 5


def test_evidence_score_ordering(retriever):
    """测试证据得分排序"""
    question = "如何配置系统？"
    evidences = retriever.retrieve(question, k=3)
    
    if len(evidences) > 1:
        # 验证得分降序排列
        for i in range(len(evidences) - 1):
            assert evidences[i].score >= evidences[i + 1].score


def test_confidence_thresholds():
    """测试置信度三段阈值逻辑"""
    # 模拟分流决策
    def determine_branch(confidence: float) -> str:
        if confidence >= 0.75:
            return 'direct_answer'
        elif confidence >= 0.55:
            return 'clarification'
        else:
            return 'handoff'
    
    # 高置信度 -> 直答
    assert determine_branch(0.85) == 'direct_answer'
    assert determine_branch(0.75) == 'direct_answer'
    
    # 中等置信度 -> 澄清
    assert determine_branch(0.65) == 'clarification'
    assert determine_branch(0.55) == 'clarification'
    
    # 低置信度 -> 转人工
    assert determine_branch(0.50) == 'handoff'
    assert determine_branch(0.30) == 'handoff'


def test_evidence_data_structure():
    """测试证据数据结构完整性"""
    evidence = Evidence(
        chunk_id="test_001",
        document_name="测试文档",
        document_version="v1.0",
        section="第1章",
        content="这是测试内容",
        score=0.85,
        keywords=["测试", "关键词"]
    )
    
    assert evidence.chunk_id == "test_001"
    assert evidence.document_name == "测试文档"
    assert evidence.document_version == "v1.0"
    assert evidence.section == "第1章"
    assert evidence.content == "这是测试内容"
    assert evidence.score == 0.85
    assert evidence.keywords == ["测试", "关键词"]


def test_retriever_stub_behavior(retriever):
    """测试检索器桩行为的一致性"""
    # 相同问题多次查询应该返回相同结果
    question = "测试一致性"
    
    evidences1 = retriever.retrieve(question, k=3)
    evidences2 = retriever.retrieve(question, k=3)
    
    assert len(evidences1) == len(evidences2)
    
    # 验证基本一致性（桩实现可能有随机性，这里只检查数量）
    for e1, e2 in zip(evidences1, evidences2):
        assert e1.document_name == e2.document_name
        assert abs(e1.score - e2.score) < 0.01  # 得分应该接近


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
