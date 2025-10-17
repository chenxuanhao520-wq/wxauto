"""
数据库功能单元测试
覆盖：表创建、会话CRUD、消息日志、去重、速率限制
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.db import Database, MessageLog, SessionInfo


@pytest.fixture
def temp_db():
    """临时数据库 fixture"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = Database(db_path)
    db.init_database()
    
    yield db
    
    db.close()
    Path(db_path).unlink()


def test_database_initialization(temp_db):
    """测试数据库初始化"""
    conn = temp_db.connect()
    cursor = conn.cursor()
    
    # 检查关键表是否存在
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
        "('sessions', 'messages', 'knowledge_chunks', 'rate_limits')"
    )
    tables = [row['name'] for row in cursor.fetchall()]
    
    assert 'sessions' in tables
    assert 'messages' in tables
    assert 'knowledge_chunks' in tables
    assert 'rate_limits' in tables


def test_session_upsert(temp_db):
    """测试会话创建与更新"""
    session_key = "test_group:test_user"
    
    # 创建新会话
    session1 = temp_db.upsert_session(
        session_key=session_key,
        group_id="test_group",
        sender_id="test_user",
        sender_name="测试用户",
        ttl_minutes=15
    )
    
    assert session1.id is not None
    assert session1.session_key == session_key
    assert session1.turn_count == 1
    assert session1.status == 'active'
    
    # 更新现有会话
    session2 = temp_db.upsert_session(
        session_key=session_key,
        group_id="test_group",
        sender_id="test_user",
        sender_name="测试用户",
        ttl_minutes=15
    )
    
    assert session2.id == session1.id
    assert session2.turn_count == 2  # 轮数增加


def test_session_summary(temp_db):
    """测试会话摘要更新"""
    session_key = "test_group:test_user"
    
    temp_db.upsert_session(
        session_key=session_key,
        group_id="test_group",
        sender_id="test_user"
    )
    
    # 更新摘要
    summary = "用户询问安装问题，已提供解决方案"
    temp_db.update_summary(session_key, summary)
    
    # 验证
    session = temp_db.get_session(session_key)
    assert session is not None
    assert session.summary == summary


def test_session_summary_truncation(temp_db):
    """测试摘要超长截断"""
    session_key = "test_group:test_user"
    
    temp_db.upsert_session(
        session_key=session_key,
        group_id="test_group",
        sender_id="test_user"
    )
    
    # 超过200字的摘要
    long_summary = "测" * 250
    temp_db.update_summary(session_key, long_summary)
    
    # 验证截断到200字
    session = temp_db.get_session(session_key)
    assert len(session.summary) == 200


def test_message_logging(temp_db):
    """测试消息日志记录"""
    msg = MessageLog(
        request_id="test_req_123",
        group_id="test_group",
        sender_id="test_user",
        user_message="如何安装设备？",
        group_name="技术支持群",
        sender_name="张三",
        bot_response="请参考安装手册第3章",
        confidence=0.85,
        branch="direct_answer",
        provider="openai",
        token_in=10,
        token_out=20,
        token_total=30
    )
    
    # 记录消息
    msg_id = temp_db.log_message(msg)
    assert msg_id is not None
    
    # 查询消息
    saved_msg = temp_db.get_message("test_req_123")
    assert saved_msg is not None
    assert saved_msg['user_message'] == "如何安装设备？"
    assert saved_msg['confidence'] == 0.85
    assert saved_msg['branch'] == "direct_answer"


def test_message_update(temp_db):
    """测试消息更新"""
    msg = MessageLog(
        request_id="test_req_456",
        group_id="test_group",
        sender_id="test_user",
        user_message="测试问题",
        status="pending"
    )
    
    temp_db.log_message(msg)
    
    # 更新状态和响应
    temp_db.update_message(
        request_id="test_req_456",
        status="answered",
        bot_response="这是答案",
        responded_at=datetime.now()
    )
    
    # 验证
    saved_msg = temp_db.get_message("test_req_456")
    assert saved_msg['status'] == "answered"
    assert saved_msg['bot_response'] == "这是答案"


def test_duplicate_detection(temp_db):
    """测试消息去重"""
    group_id = "test_group"
    sender_id = "test_user"
    message = "重复的消息内容"
    
    # 第一次不重复
    is_dup1 = temp_db.check_duplicate(group_id, sender_id, message, window_seconds=10)
    assert is_dup1 is False
    
    # 记录消息
    msg = MessageLog(
        request_id="dup_test_1",
        group_id=group_id,
        sender_id=sender_id,
        user_message=message
    )
    temp_db.log_message(msg)
    
    # 10秒内重复
    is_dup2 = temp_db.check_duplicate(group_id, sender_id, message, window_seconds=10)
    assert is_dup2 is True


def test_rate_limiting(temp_db):
    """测试速率限制"""
    entity_type = "user"
    entity_id = "test_user"
    limit = 3
    window_seconds = 60
    
    # 前3次应该允许
    for i in range(3):
        allowed, count = temp_db.check_rate_limit(
            entity_type, entity_id, limit, window_seconds
        )
        assert allowed is True
        assert count == i + 1
    
    # 第4次应该被限制
    allowed, count = temp_db.check_rate_limit(
        entity_type, entity_id, limit, window_seconds
    )
    assert allowed is False
    assert count == 3  # 计数不再增加


def test_system_config(temp_db):
    """测试系统配置读写"""
    # 写入配置
    temp_db.set_config('test_key', 'test_value')
    
    # 读取配置
    value = temp_db.get_config('test_key')
    assert value == 'test_value'
    
    # 更新配置
    temp_db.set_config('test_key', 'updated_value')
    value = temp_db.get_config('test_key')
    assert value == 'updated_value'
    
    # 读取不存在的配置
    value = temp_db.get_config('non_existent_key')
    assert value is None


def test_export_to_csv(temp_db, tmp_path):
    """测试导出 CSV"""
    # 插入测试消息
    for i in range(5):
        msg = MessageLog(
            request_id=f"export_test_{i}",
            group_id="test_group",
            sender_id="test_user",
            user_message=f"测试消息 {i}"
        )
        temp_db.log_message(msg)
    
    # 导出
    output_path = tmp_path / "export_test.csv"
    result_path = temp_db.export_to_csv(str(output_path))
    
    assert Path(result_path).exists()
    
    # 验证内容
    with open(result_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
        assert len(lines) == 6  # 1 header + 5 rows


def test_session_expiration(temp_db):
    """测试会话过期清理"""
    # 创建一个已过期的会话
    session_key = "expired_session:user1"
    session = temp_db.upsert_session(
        session_key=session_key,
        group_id="test_group",
        sender_id="user1",
        ttl_minutes=0  # 立即过期
    )
    
    # 手动设置过期时间为过去
    conn = temp_db.connect()
    cursor = conn.cursor()
    past_time = datetime.now() - timedelta(minutes=1)
    cursor.execute(
        "UPDATE sessions SET expires_at = ? WHERE session_key = ?",
        (past_time, session_key)
    )
    conn.commit()
    
    # 清理过期会话
    count = temp_db.expire_old_sessions()
    assert count == 1
    
    # 验证状态已更新
    session = temp_db.get_session(session_key)
    assert session.status == 'expired'


def test_customer_binding(temp_db):
    """测试客户名称绑定"""
    session_key = "test_group:test_user"
    
    temp_db.upsert_session(
        session_key=session_key,
        group_id="test_group",
        sender_id="test_user"
    )
    
    # 绑定客户
    customer_name = "某某科技有限公司"
    temp_db.bind_customer(session_key, customer_name)
    
    # 验证
    session = temp_db.get_session(session_key)
    assert session.customer_name == customer_name


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
