-- ============================================
-- v3.1 数据库升级脚本
-- 新增对话效果追踪和完整对话保存
-- ============================================

-- 1. 扩展 sessions 表，添加对话效果追踪字段
ALTER TABLE sessions ADD COLUMN conversation_outcome TEXT;  -- 对话结果：solved | unsolved | transferred | abandoned
ALTER TABLE sessions ADD COLUMN outcome_reason TEXT;        -- 结果原因/备注
ALTER TABLE sessions ADD COLUMN satisfaction_score INTEGER; -- 满意度评分 1-5
ALTER TABLE sessions ADD COLUMN total_messages INTEGER DEFAULT 0; -- 总消息数
ALTER TABLE sessions ADD COLUMN ai_messages INTEGER DEFAULT 0;    -- AI回复数
ALTER TABLE sessions ADD COLUMN resolution_time_sec INTEGER;      -- 解决用时（秒）
ALTER TABLE sessions ADD COLUMN conversation_thread TEXT;  -- 完整对话串（JSON格式）
ALTER TABLE sessions ADD COLUMN tags TEXT;                 -- 标签（如：售后、技术支持、价格咨询等）
ALTER TABLE sessions ADD COLUMN resolved_by TEXT;          -- 解决方式：ai | human | self
ALTER TABLE sessions ADD COLUMN first_response_time_ms INTEGER; -- 首次响应时间（毫秒）
ALTER TABLE sessions ADD COLUMN last_message_at DATETIME;  -- 最后一条消息时间

-- 2. 扩展 messages 表，添加上下文和效果字段
ALTER TABLE messages ADD COLUMN conversation_context TEXT; -- 对话上下文（JSON格式，包含历史消息）
ALTER TABLE messages ADD COLUMN user_feedback TEXT;        -- 用户反馈（如：有用、无用、需要更多信息）
ALTER TABLE messages ADD COLUMN follow_up_needed BOOLEAN DEFAULT 0; -- 是否需要跟进
ALTER TABLE messages ADD COLUMN parent_message_id TEXT;    -- 父消息ID（用于关联多轮对话）
ALTER TABLE messages ADD COLUMN is_final_answer BOOLEAN DEFAULT 0;  -- 是否为最终答案

-- 3. 创建对话效果索引
CREATE INDEX IF NOT EXISTS idx_sessions_outcome ON sessions(conversation_outcome);
CREATE INDEX IF NOT EXISTS idx_sessions_resolved_by ON sessions(resolved_by);
CREATE INDEX IF NOT EXISTS idx_sessions_tags ON sessions(tags);
CREATE INDEX IF NOT EXISTS idx_messages_feedback ON messages(user_feedback);
CREATE INDEX IF NOT EXISTS idx_messages_follow_up ON messages(follow_up_needed);

-- 4. 创建对话效果统计视图
CREATE VIEW IF NOT EXISTS conversation_outcomes AS
SELECT 
    DATE(created_at) as date,
    conversation_outcome,
    resolved_by,
    tags,
    COUNT(*) as count,
    AVG(satisfaction_score) as avg_satisfaction,
    AVG(resolution_time_sec) as avg_resolution_time,
    AVG(turn_count) as avg_turns,
    AVG(total_messages) as avg_messages
FROM sessions
WHERE created_at >= datetime('now', '-30 days')
GROUP BY DATE(created_at), conversation_outcome, resolved_by, tags;

-- 5. 创建对话质量分析视图
CREATE VIEW IF NOT EXISTS conversation_quality AS
SELECT 
    s.session_key,
    s.group_name,
    s.sender_name,
    s.conversation_outcome,
    s.resolved_by,
    s.satisfaction_score,
    s.turn_count,
    s.total_messages,
    s.ai_messages,
    s.resolution_time_sec,
    s.tags,
    s.created_at,
    s.last_message_at,
    COUNT(m.id) as message_count,
    AVG(m.confidence) as avg_confidence,
    SUM(m.token_total) as total_tokens
FROM sessions s
LEFT JOIN messages m ON s.id = m.session_id
WHERE s.created_at >= datetime('now', '-30 days')
GROUP BY s.id;

-- 6. 初始化已有会话的字段（可选）
UPDATE sessions SET conversation_outcome = 'unknown' WHERE conversation_outcome IS NULL;
UPDATE sessions SET resolved_by = 'unknown' WHERE resolved_by IS NULL;
UPDATE sessions SET total_messages = 0 WHERE total_messages IS NULL;
UPDATE sessions SET ai_messages = 0 WHERE ai_messages IS NULL;

