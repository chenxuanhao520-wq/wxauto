-- ============================================
-- 微信客服中台数据库初始化脚本
-- SQLite 3.x
-- ============================================

-- 会话表：追踪群聊中的用户会话
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_key TEXT NOT NULL UNIQUE,  -- 格式: {group_id}:{sender_id}
    group_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    sender_name TEXT,
    customer_name TEXT,  -- 绑定的客户名称（通过 #bind 设置）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,  -- TTL 过期时间
    turn_count INTEGER DEFAULT 0,
    summary TEXT,  -- 滚动摘要 ≤200字
    status TEXT DEFAULT 'active',  -- active | expired | handed_off
    metadata TEXT  -- JSON 扩展字段
);

CREATE INDEX IF NOT EXISTS idx_sessions_key ON sessions(session_key);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_group ON sessions(group_id);

-- 消息表：全量日志（包含请求、回答、证据、时延）
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    session_id INTEGER,
    group_id TEXT NOT NULL,
    group_name TEXT,
    sender_id TEXT NOT NULL,
    sender_name TEXT,
    
    -- 消息内容
    user_message TEXT NOT NULL,
    user_message_hash TEXT,  -- 用于去重
    bot_response TEXT,
    
    -- RAG 相关
    evidence_ids TEXT,  -- JSON 数组：关联的证据 chunk IDs
    evidence_summary TEXT,  -- 证据摘要（文档名、版本、段落）
    confidence REAL,  -- 置信度 0-1
    
    -- 分流与路由
    branch TEXT,  -- direct_answer | clarification | handoff | rate_limited | forbidden
    handoff_reason TEXT,  -- policy | low_confidence | failure | user_request
    
    -- AI 网关信息
    provider TEXT,  -- openai | deepseek | fallback
    model TEXT,
    token_in INTEGER DEFAULT 0,
    token_out INTEGER DEFAULT 0,
    token_total INTEGER DEFAULT 0,
    
    -- 时延分析（毫秒）
    latency_receive_ms INTEGER,  -- 接收到消息的时延
    latency_retrieval_ms INTEGER,  -- RAG 检索时延
    latency_generation_ms INTEGER,  -- LLM 生成时延
    latency_send_ms INTEGER,  -- 发送响应时延
    latency_total_ms INTEGER,  -- 总时延
    
    -- 时间戳
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    responded_at DATETIME,
    
    -- 状态与调试
    status TEXT DEFAULT 'pending',  -- pending | acked | answered | failed | ignored
    error_message TEXT,
    debug_info TEXT,  -- JSON：详细调试信息
    
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_request ON messages(request_id);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_group ON messages(group_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_received ON messages(received_at);
CREATE INDEX IF NOT EXISTS idx_messages_branch ON messages(branch);
CREATE INDEX IF NOT EXISTS idx_messages_hash ON messages(user_message_hash);

-- 知识库分块表（Phase 2 实现，现在建表占位）
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id TEXT NOT NULL UNIQUE,
    document_name TEXT NOT NULL,
    document_version TEXT,
    section TEXT,  -- 章节/段落
    content TEXT NOT NULL,
    embedding BLOB,  -- 向量存储（可选）
    keywords TEXT,  -- BM25 关键词
    metadata TEXT,  -- JSON 扩展字段
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON knowledge_chunks(document_name);
CREATE INDEX IF NOT EXISTS idx_chunks_id ON knowledge_chunks(chunk_id);

-- 速率限制追踪表（内存优先，持久化备份）
CREATE TABLE IF NOT EXISTS rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,  -- group | user | global
    entity_id TEXT NOT NULL,
    window_start DATETIME NOT NULL,
    request_count INTEGER DEFAULT 1,
    last_request_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(entity_type, entity_id, window_start)
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_entity ON rate_limits(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start);

-- 管理指令日志
CREATE TABLE IF NOT EXISTS admin_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT NOT NULL,
    operator TEXT NOT NULL,
    group_id TEXT,
    args TEXT,  -- JSON
    result TEXT,
    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_commands_time ON admin_commands(executed_at);

-- 系统配置表（运行时动态配置）
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 初始化系统配置
INSERT OR IGNORE INTO system_config (key, value, description) VALUES
    ('shadow_mode', 'false', '影子模式：只记录不发言'),
    ('global_mute', 'false', '全局静默'),
    ('debug_mode', 'false', '调试模式：输出详细日志'),
    ('last_health_check', '', '最后一次健康检查时间'),
    ('health_status', 'unknown', '健康状态：healthy | degraded | down');

-- 性能统计视图（用于日报、监控）
CREATE VIEW IF NOT EXISTS performance_stats AS
SELECT 
    DATE(received_at) as date,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN status = 'answered' THEN 1 END) as answered,
    COUNT(CASE WHEN branch = 'handoff' THEN 1 END) as handoffs,
    AVG(latency_total_ms) as avg_latency_ms,
    AVG(token_total) as avg_tokens,
    AVG(confidence) as avg_confidence,
    provider,
    branch
FROM messages
WHERE received_at >= datetime('now', '-30 days')
GROUP BY DATE(received_at), provider, branch;

-- 会话统计视图
CREATE VIEW IF NOT EXISTS session_stats AS
SELECT 
    group_id,
    COUNT(*) as total_sessions,
    AVG(turn_count) as avg_turns,
    COUNT(CASE WHEN status = 'handed_off' THEN 1 END) as handoff_count
FROM sessions
WHERE created_at >= datetime('now', '-30 days')
GROUP BY group_id;
