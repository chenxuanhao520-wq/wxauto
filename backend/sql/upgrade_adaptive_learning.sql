-- ============================================
-- 自适应学习模块数据库升级脚本
-- 添加用户画像和对话风格学习
-- ============================================

-- 创建用户画像表
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    user_name TEXT,
    
    -- 基础属性
    customer_type TEXT DEFAULT 'regular',  -- vip/regular/new
    company_name TEXT,
    role TEXT,  -- 运营商/车主/经销商/工程师
    
    -- 沟通偏好
    communication_style TEXT DEFAULT 'friendly',  -- formal/friendly/casual
    preferred_response_style TEXT DEFAULT 'concise',  -- concise/detailed
    technical_level TEXT DEFAULT 'medium',  -- high/medium/low
    
    -- 行为特征
    total_interactions INTEGER DEFAULT 0,
    avg_satisfaction REAL,
    common_topics TEXT,  -- JSON array
    active_hours TEXT,   -- JSON array [9,10,14,15]
    
    -- 学习到的偏好
    learned_preferences TEXT,  -- JSON对象
    conversation_examples TEXT,  -- JSON array，Few-Shot示例
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_interaction_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_type ON user_profiles(customer_type);
CREATE INDEX IF NOT EXISTS idx_user_profiles_updated ON user_profiles(updated_at);

-- 创建对话风格配置表
CREATE TABLE IF NOT EXISTS conversation_styles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    style_name TEXT NOT NULL UNIQUE,  -- default/formal/friendly等
    style_config TEXT NOT NULL,  -- JSON配置
    usage_count INTEGER DEFAULT 0,
    avg_satisfaction REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认风格
INSERT OR IGNORE INTO conversation_styles (style_name, style_config) VALUES
('default', '{"tone": "friendly", "common_phrases": ["好的", "您", "请"], "avg_length": 150}'),
('formal', '{"tone": "formal", "common_phrases": ["您好", "请问", "感谢"], "avg_length": 200}'),
('casual', '{"tone": "casual", "common_phrases": ["嗯嗯", "好呀", "哈哈"], "avg_length": 100}');

-- 扩展messages表，添加个性化相关字段
ALTER TABLE messages ADD COLUMN user_profile_snapshot TEXT;  -- 使用时的画像快照
ALTER TABLE messages ADD COLUMN personalized_prompt_used TEXT;  -- 使用的个性化Prompt
ALTER TABLE messages ADD COLUMN style_version TEXT;  -- 风格版本号

-- 创建学习日志表（用于追踪学习效果）
CREATE TABLE IF NOT EXISTS learning_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    learning_type TEXT,  -- profile_update/style_learn/preference_learn
    before_value TEXT,
    after_value TEXT,
    trigger_conversation_id TEXT,
    learning_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_learning_logs_user ON learning_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_logs_type ON learning_logs(learning_type);
CREATE INDEX IF NOT EXISTS idx_learning_logs_time ON learning_logs(created_at);

-- 创建用户画像统计视图
CREATE VIEW IF NOT EXISTS user_profile_stats AS
SELECT 
    customer_type,
    COUNT(*) as user_count,
    AVG(total_interactions) as avg_interactions,
    AVG(avg_satisfaction) as avg_satisfaction,
    communication_style,
    technical_level
FROM user_profiles
GROUP BY customer_type, communication_style, technical_level;

