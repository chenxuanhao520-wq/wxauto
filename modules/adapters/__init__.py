"""适配器模块：微信消息收发抽象与实现"""
from .wxauto_adapter import Message, WxAutoAdapter, FakeWxAdapter

__all__ = ["Message", "WxAutoAdapter", "FakeWxAdapter"]
