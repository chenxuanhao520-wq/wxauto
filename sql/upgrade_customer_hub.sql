-- 客户中台数据库升级脚本
-- 新增 Thread、Signal、Contact 表

-- ==================== 联系人表 ====================
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,                    -- UUID
    wx_id TEXT UNIQUE NOT NULL,             -- 微信唯一标识
    remark TEXT,                            -- 微信备注
    k_code TEXT,                            -- K编码 (K3208-渝A-张三-VIP-微信)
    source TEXT NOT NULL DEFAULT 'wechat', -- 来源: wechat/manual/import
    type TEXT NOT NULL DEFAULT 'unknown',   -- 类型: customer/lead/vendor/personal/unknown
    confidence INTEGER NOT NULL DEFAULT 0,  -- 置信度 0-100
    owner TEXT,                             -- 负责人
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contacts_wx_id ON contacts(wx_id);
CREATE INDEX IF NOT EXISTS idx_contacts_k_code ON contacts(k_code);
CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(type);

-- ==================== 会话线程表 ====================
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,                    -- UUID
    contact_id TEXT NOT NULL,               -- 联系人ID
    last_speaker TEXT NOT NULL,             -- 最后说话方: me/them
    last_msg_at DATETIME NOT NULL,          -- 最后消息时间
    status TEXT NOT NULL,                   -- 状态: UNSEEN/NEED_REPLY/WAITING_THEM/OVERDUE/RESOLVED/SNOOZED
    bucket TEXT NOT NULL,                   -- 白/灰/黑: WHITE/GRAY/BLACK
    
    -- SLA 时间点
    sla_at DATETIME,                        -- 需回复的截止时间
    snooze_at DATETIME,                     -- 稍后处理唤醒时间
    follow_up_at DATETIME,                  -- 等待对方的回弹时间
    
    -- 其他
    topic TEXT,                             -- LLM摘要
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE INDEX IF NOT EXISTS idx_threads_contact_id ON threads(contact_id);
CREATE INDEX IF NOT EXISTS idx_threads_status ON threads(status);
CREATE INDEX IF NOT EXISTS idx_threads_bucket ON threads(bucket);
CREATE INDEX IF NOT EXISTS idx_threads_last_msg_at ON threads(last_msg_at);
CREATE INDEX IF NOT EXISTS idx_threads_sla_at ON threads(sla_at);

-- ==================== 信号/打分表 ====================
CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY,                    -- UUID
    thread_id TEXT NOT NULL,                -- 会话ID
    
    -- 打分维度
    keyword_hits TEXT,                      -- 关键词命中次数 (JSON)
    file_types TEXT,                        -- 文件类型列表 (JSON)
    worktime_score INTEGER NOT NULL DEFAULT 0,  -- 工作时间得分 0-40
    kb_match_score INTEGER NOT NULL DEFAULT 0,  -- 知识库匹配得分 0-30
    
    -- 综合
    total_score INTEGER NOT NULL DEFAULT 0, -- 总分 0-100
    bucket TEXT NOT NULL,                   -- 判定结果: WHITE/GRAY/BLACK
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (thread_id) REFERENCES threads(id)
);

CREATE INDEX IF NOT EXISTS idx_signals_thread_id ON signals(thread_id);
CREATE INDEX IF NOT EXISTS idx_signals_total_score ON signals(total_score);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at);

-- ==================== 触发器输出表 ====================
CREATE TABLE IF NOT EXISTS trigger_outputs (
    id TEXT PRIMARY KEY,                    -- UUID
    thread_id TEXT NOT NULL,                -- 会话ID
    trigger_type TEXT NOT NULL,             -- 触发类型: 售前/售后/客户开发
    
    -- 输出内容
    form_data TEXT NOT NULL,                -- 表单数据 (JSON)
    reply_draft TEXT NOT NULL,              -- 回复草稿
    labels TEXT,                            -- 标签列表 (逗号分隔)
    
    -- 元数据
    confidence REAL,                        -- 置信度
    used BOOLEAN NOT NULL DEFAULT 0,        -- 是否已使用
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (thread_id) REFERENCES threads(id)
);

CREATE INDEX IF NOT EXISTS idx_trigger_outputs_thread_id ON trigger_outputs(thread_id);
CREATE INDEX IF NOT EXISTS idx_trigger_outputs_used ON trigger_outputs(used);

-- ==================== 每日指标表 ====================
CREATE TABLE IF NOT EXISTS daily_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,              -- 日期 YYYY-MM-DD
    
    unknown_pool_count INTEGER DEFAULT 0,   -- 未知池数量
    promoted_count INTEGER DEFAULT 0,       -- 建档数量
    clear_rate REAL DEFAULT 0,              -- 清零率
    avg_response_time_min REAL DEFAULT 0,   -- 平均响应时间(分钟)
    overdue_count INTEGER DEFAULT 0,        -- 逾期数量
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date);

-- ==================== 视图：未知池 ====================
-- 未知池：灰名单 + 未处理/需回复的会话
CREATE VIEW IF NOT EXISTS unknown_pool AS
SELECT 
    t.id,
    t.contact_id,
    c.wx_id,
    c.remark,
    t.last_speaker,
    t.last_msg_at,
    t.status,
    t.topic,
    s.total_score,
    s.keyword_hits,
    s.file_types
FROM threads t
JOIN contacts c ON t.contact_id = c.id
LEFT JOIN signals s ON t.id = s.thread_id
WHERE t.bucket = 'GRAY'
  AND t.status IN ('UNSEEN', 'NEED_REPLY', 'OVERDUE')
ORDER BY s.total_score DESC, t.last_msg_at DESC;

-- ==================== 视图：今日待办 ====================
CREATE VIEW IF NOT EXISTS today_todo AS
SELECT 
    t.id,
    t.contact_id,
    c.wx_id,
    c.remark,
    c.k_code,
    t.last_speaker,
    t.last_msg_at,
    t.status,
    t.bucket,
    t.sla_at,
    t.topic,
    CASE 
        WHEN t.status = 'OVERDUE' THEN 1
        WHEN t.status = 'NEED_REPLY' THEN 2
        WHEN t.status = 'UNSEEN' THEN 3
        ELSE 4
    END as priority
FROM threads t
JOIN contacts c ON t.contact_id = c.id
WHERE t.status IN ('UNSEEN', 'NEED_REPLY', 'OVERDUE', 'SNOOZED')
  AND (t.snooze_at IS NULL OR t.snooze_at <= datetime('now'))
ORDER BY priority, t.last_msg_at;

-- ==================== 完成 ====================
-- 数据库版本标记
INSERT OR REPLACE INTO system_config (key, value, updated_at) 
VALUES ('db_version', 'customer_hub_v1', datetime('now'));

