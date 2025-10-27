"""
客户中台核心数据类型
基于"最后说话方 + SLA"状态机
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Literal
from enum import Enum


# ==================== 枚举类型 ====================

class Party(str, Enum):
    """对话方"""
    ME = "me"           # 我方
    THEM = "them"       # 客户


class ThreadStatus(str, Enum):
    """会话状态"""
    UNSEEN = "UNSEEN"               # 未处理
    NEED_REPLY = "NEED_REPLY"       # 需回复(客户最后发言)
    WAITING_THEM = "WAITING_THEM"   # 等待对方(我方最后发言)
    OVERDUE = "OVERDUE"             # 逾期未回复
    RESOLVED = "RESOLVED"           # 已解决
    SNOOZED = "SNOOZED"             # 已推迟


class Bucket(str, Enum):
    """名单分类"""
    WHITE = "WHITE"     # 白名单(已建档客户)
    GRAY = "GRAY"       # 灰名单(潜在客户,未建档)
    BLACK = "BLACK"     # 黑名单(个人会话,不处理)


class ContactType(str, Enum):
    """联系人类型"""
    CUSTOMER = "customer"   # 已建档客户
    LEAD = "lead"           # 潜在客户
    VENDOR = "vendor"       # 供应商
    PERSONAL = "personal"   # 个人
    UNKNOWN = "unknown"     # 未知


class ContactSource(str, Enum):
    """联系人来源"""
    WECHAT = "wechat"
    MANUAL = "manual"
    IMPORT = "import"


class TriggerLabel(str, Enum):
    """触发场景标签"""
    PRE_SALES = "售前"          # 售前咨询
    AFTER_SALES = "售后"        # 售后支持
    BIZ_DEV = "客户开发"        # 渠道拓展


# ==================== 数据类 ====================

@dataclass
class Contact:
    """联系人/客户"""
    id: str                         # UUID
    wx_id: str                      # 微信唯一标识
    remark: Optional[str] = None    # 微信备注
    k_code: Optional[str] = None    # K编码 (如: K3208-渝A-张三-VIP-微信)
    source: ContactSource = ContactSource.WECHAT
    type: ContactType = ContactType.UNKNOWN
    confidence: int = 0             # 置信度 0-100
    owner: Optional[str] = None     # 负责人
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SLAConfig:
    """SLA配置"""
    unseen_minutes: int = 0         # 未处理进入NEED_REPLY的阈值(通常0)
    need_reply_minutes: int = 30    # 客户最后发言后需回复SLA(分钟)
    follow_up_hours: int = 48       # 我方最后发言后回弹窗口(小时)


@dataclass
class Thread:
    """会话线程"""
    id: str                             # UUID
    contact_id: str                     # 联系人ID
    last_speaker: Party                 # 最后说话方
    last_msg_at: datetime               # 最后消息时间
    status: ThreadStatus                # 状态
    bucket: Bucket                      # 白/灰/黑名单
    
    # SLA时间点
    sla_at: Optional[datetime] = None       # 需回复的截止时间
    snooze_at: Optional[datetime] = None    # 稍后处理唤醒时间
    follow_up_at: Optional[datetime] = None # 等待对方的回弹时间
    
    # 其他
    topic: Optional[str] = None             # LLM摘要
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Signal:
    """信号/打分结果"""
    id: str                         # UUID
    thread_id: str                  # 会话ID
    
    # 打分维度
    keyword_hits: Dict[str, int] = field(default_factory=dict)  # 关键词命中次数
    file_types: List[str] = field(default_factory=list)         # 文件类型
    worktime_score: int = 0         # 工作时间得分 0-40
    kb_match_score: int = 0         # 知识库匹配得分 0-30
    
    # 综合
    total_score: int = 0            # 总分 0-100
    bucket: Bucket = Bucket.BLACK   # 判定结果
    
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TriggerOutput:
    """触发器输出"""
    form: Dict                      # 表单数据(询价要素/工单/线索)
    reply_draft: str                # 回复草稿
    labels: List[TriggerLabel]      # 标签


# ==================== 规则配置 ====================

@dataclass
class ScoringRules:
    """打分规则"""
    # 关键词分组
    keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        "pre": [
            "报价", "价格", "参数", "型号", "交期", "样机", 
            "招标", "折扣", "含税", "EXW", "FOB", "功率", "枪型"
        ],
        "post": [
            "故障", "报错", "报警码", "返修", "保修", "上门", 
            "无法充电", "安装", "调试", "工单", "序列号"
        ],
        "bizdev": [
            "代理", "渠道", "合作", "资质", "样板", 
            "分销", "招募", "返点", "区域"
        ]
    })
    
    # 文件权重
    file_weights: Dict[str, int] = field(default_factory=lambda: {
        "pdf": 10, "xls": 12, "xlsx": 12, "doc": 6, 
        "docx": 6, "cad": 15, "jpg": 4, "png": 4
    })
    
    # 工作时间
    work_start_hour: int = 8
    work_end_hour: int = 20
    weekday_bonus: int = 12
    weekend_bonus: int = 4
    
    # 知识库匹配权重
    kb_match_weight: int = 20
    
    # 阈值
    white_promotion_threshold: int = 80     # 升白阈值
    gray_lower: int = 60                     # 灰名单下限
    
    # 黑名单关键词(直接拉黑)
    blacklist_keywords: List[str] = field(default_factory=lambda: [
        "吃饭", "撸串", "喝酒", "打球", "游戏", "电影"
    ])


# ==================== 统计类型 ====================

@dataclass
class ThreadStatistics:
    """会话统计"""
    total: int = 0
    unseen: int = 0
    need_reply: int = 0
    waiting_them: int = 0
    overdue: int = 0
    resolved: int = 0
    snoozed: int = 0


@dataclass
class DailyMetrics:
    """每日指标"""
    date: str
    unknown_pool_count: int         # 未知池数量
    promoted_count: int             # 建档数量
    clear_rate: float               # 清零率
    avg_response_time_min: float    # 平均响应时间(分钟)
    overdue_count: int              # 逾期数量


# ==================== 消息采样 ====================

@dataclass
class InboundMessage:
    """入站消息(连接器抽象)"""
    wx_id: str              # 微信ID
    thread_id: str          # 会话ID
    text: Optional[str]     # 文本内容
    file_types: List[str]   # 文件类型列表
    timestamp: datetime     # 时间戳
    last_speaker: Party     # 最后说话方

