"""
触发与处理逻辑测试
覆盖：@识别、去重、频控、ACK
"""
import pytest
import re
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.adapters.wxauto_adapter import Message, FakeWxAdapter


@pytest.fixture
def fake_wx():
    """假微信适配器 fixture"""
    adapter = FakeWxAdapter(whitelisted_groups=["技术支持群", "VIP客户群"])
    return adapter


def test_fake_adapter_initialization(fake_wx):
    """测试假适配器初始化"""
    assert fake_wx.my_name == "测试助手"
    assert len(fake_wx.whitelisted_groups) == 2
    assert "技术支持群" in fake_wx.whitelisted_groups


def test_inject_and_receive_message(fake_wx):
    """测试消息注入与接收"""
    # 注入消息
    fake_wx.inject_message(
        group_name="技术支持群",
        sender_name="张三",
        content="如何安装设备？",
        is_at_me=True
    )
    
    # 接收消息
    messages = list(fake_wx.iter_new_messages())
    
    assert len(messages) == 1
    msg = messages[0]
    assert msg.group_name == "技术支持群"
    assert msg.sender_name == "张三"
    assert msg.content == "如何安装设备？"
    assert msg.is_at_me is True


def test_send_text(fake_wx):
    """测试发送文本消息"""
    success = fake_wx.send_text(
        group_name="技术支持群",
        text="这是回复内容",
        at_user="张三"
    )
    
    assert success is True
    
    # 检查发送记录
    sent = fake_wx.get_sent_messages()
    assert len(sent) == 1
    assert sent[0]['group_name'] == "技术支持群"
    assert "@张三" in sent[0]['text']
    assert "这是回复内容" in sent[0]['text']


def test_ack(fake_wx):
    """测试 ACK 确认消息"""
    success = fake_wx.ack(
        group_name="技术支持群",
        sender_name="张三",
        ack_text="收到，处理中……"
    )
    
    assert success is True
    
    # 检查发送记录
    sent = fake_wx.get_sent_messages()
    assert len(sent) == 1
    assert "@张三" in sent[0]['text']
    assert "收到，处理中……" in sent[0]['text']


def test_focus_whitelisted_chat(fake_wx):
    """测试切换到白名单群聊"""
    # 白名单内的群
    result = fake_wx.focus_chat("技术支持群")
    assert result is True
    
    # 白名单外的群
    result = fake_wx.focus_chat("非白名单群")
    assert result is False


def test_multiple_messages(fake_wx):
    """测试多条消息处理"""
    # 注入多条消息
    for i in range(3):
        fake_wx.inject_message(
            group_name="技术支持群",
            sender_name=f"用户{i}",
            content=f"问题 {i}",
            is_at_me=True
        )
    
    # 接收所有消息
    messages = list(fake_wx.iter_new_messages())
    
    assert len(messages) == 3
    for i, msg in enumerate(messages):
        assert msg.sender_name == f"用户{i}"
        assert msg.content == f"问题 {i}"


def test_at_detection_pattern():
    """测试 @识别正则表达式"""
    my_name = "小助手"
    pattern = rf"@\s*{re.escape(my_name)}\b"
    
    # 标准 @
    assert re.search(pattern, "@小助手 请问如何安装？")
    
    # 带空格
    assert re.search(pattern, "@ 小助手 请问如何安装？")
    
    # 多个空格
    assert re.search(pattern, "@  小助手  请问如何安装？")
    
    # 不应该匹配
    assert not re.search(pattern, "小助手 请问如何安装？")
    assert not re.search(pattern, "@其他人 请问如何安装？")


def test_message_clearing(fake_wx):
    """测试消息队列清理"""
    # 注入消息
    fake_wx.inject_message(
        group_name="技术支持群",
        sender_name="张三",
        content="测试消息",
        is_at_me=True
    )
    
    # 接收消息（队列被清空）
    messages = list(fake_wx.iter_new_messages())
    assert len(messages) == 1
    
    # 再次接收，应该为空
    messages = list(fake_wx.iter_new_messages())
    assert len(messages) == 0


def test_sent_message_tracking(fake_wx):
    """测试发送消息追踪"""
    # 发送多条消息
    fake_wx.send_text("技术支持群", "消息1")
    fake_wx.send_text("VIP客户群", "消息2", at_user="李四")
    fake_wx.ack("技术支持群", "张三")
    
    # 检查记录
    sent = fake_wx.get_sent_messages()
    assert len(sent) == 3
    
    # 清空记录
    fake_wx.clear_sent_messages()
    sent = fake_wx.get_sent_messages()
    assert len(sent) == 0


def test_message_timestamp(fake_wx):
    """测试消息时间戳"""
    before = datetime.now()
    
    fake_wx.inject_message(
        group_name="技术支持群",
        sender_name="张三",
        content="测试消息",
        is_at_me=True
    )
    
    after = datetime.now()
    
    messages = list(fake_wx.iter_new_messages())
    msg = messages[0]
    
    assert before <= msg.timestamp <= after


def test_group_and_sender_id_normalization(fake_wx):
    """测试群ID和发送者ID规范化"""
    fake_wx.inject_message(
        group_name="技术 支持 群",  # 带空格
        sender_name="张 三",
        content="测试",
        is_at_me=True
    )
    
    messages = list(fake_wx.iter_new_messages())
    msg = messages[0]
    
    # ID 应该移除空格并转小写
    assert " " not in msg.group_id
    assert " " not in msg.sender_id
    assert msg.group_id == msg.group_id.lower()
    assert msg.sender_id == msg.sender_id.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
