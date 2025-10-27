-- 配置管理系统数据库表
-- 用于存储所有第三方服务配置

-- 配置分类表
CREATE TABLE IF NOT EXISTS config_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 配置项表
CREATE TABLE IF NOT EXISTS config_items (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES config_categories(id),
    key VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    value_type VARCHAR(20) DEFAULT 'string', -- string, number, boolean, json, password
    is_required BOOLEAN DEFAULT false,
    is_encrypted BOOLEAN DEFAULT false,
    default_value TEXT,
    validation_regex VARCHAR(500),
    help_text TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category_id, key)
);

-- 配置值表
CREATE TABLE IF NOT EXISTS config_values (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES config_items(id),
    value TEXT,
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 配置历史表
CREATE TABLE IF NOT EXISTS config_history (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES config_items(id),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100),
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 服务状态表
CREATE TABLE IF NOT EXISTS service_status (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'unknown', -- unknown, healthy, warning, error
    last_check TIMESTAMPTZ,
    error_message TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入配置分类
INSERT INTO config_categories (name, display_name, description, icon, sort_order) VALUES
('system', '系统配置', '基础系统参数配置', 'settings', 1),
('supabase', 'Supabase数据库', 'Supabase云数据库配置', 'database', 2),
('pinecone', 'Pinecone向量库', 'Pinecone向量数据库配置', 'vector', 3),
('ai_models', 'AI模型服务', '各种AI模型API配置', 'brain', 4),
('wechat', '微信配置', '微信相关配置', 'wechat', 5),
('monitoring', '监控配置', '系统监控和告警配置', 'monitor', 6),
('security', '安全配置', '安全相关配置', 'security', 7)
ON CONFLICT (name) DO NOTHING;

-- 插入系统配置项
INSERT INTO config_items (category_id, key, display_name, description, value_type, is_required, default_value, help_text, sort_order) VALUES
((SELECT id FROM config_categories WHERE name = 'system'), 'app_name', '应用名称', '系统应用名称', 'string', true, '微信客服中台', '用于显示的系统名称', 1),
((SELECT id FROM config_categories WHERE name = 'system'), 'app_version', '应用版本', '系统版本号', 'string', true, '2.0.0', '当前系统版本', 2),
((SELECT id FROM config_categories WHERE name = 'system'), 'debug_mode', '调试模式', '是否启用调试模式', 'boolean', false, 'false', '启用后显示详细日志', 3),
((SELECT id FROM config_categories WHERE name = 'system'), 'log_level', '日志级别', '系统日志级别', 'string', false, 'INFO', 'DEBUG, INFO, WARNING, ERROR', 4)
ON CONFLICT (category_id, key) DO NOTHING;

-- 插入Supabase配置项
INSERT INTO config_items (category_id, key, display_name, description, value_type, is_required, is_encrypted, validation_regex, help_text, sort_order) VALUES
((SELECT id FROM config_categories WHERE name = 'supabase'), 'url', 'Supabase URL', 'Supabase项目URL', 'string', true, false, '^https://[a-zA-Z0-9-]+\\.supabase\\.co$', '格式: https://your-project.supabase.co', 1),
((SELECT id FROM config_categories WHERE name = 'supabase'), 'anon_key', '匿名密钥', 'Supabase匿名密钥', 'password', true, true, '^[a-zA-Z0-9._-]+$', '用于客户端访问的密钥', 2),
((SELECT id FROM config_categories WHERE name = 'supabase'), 'service_role_key', '服务角色密钥', 'Supabase服务角色密钥', 'password', false, true, '^[a-zA-Z0-9._-]+$', '用于服务端访问的密钥（可选）', 3)
ON CONFLICT (category_id, key) DO NOTHING;

-- 插入Pinecone配置项
INSERT INTO config_items (category_id, key, display_name, description, value_type, is_required, is_encrypted, validation_regex, help_text, sort_order) VALUES
((SELECT id FROM config_categories WHERE name = 'pinecone'), 'api_key', 'API密钥', 'Pinecone API密钥', 'password', true, true, '^[a-zA-Z0-9-]+$', '从Pinecone控制台获取', 1),
((SELECT id FROM config_categories WHERE name = 'pinecone'), 'environment', '环境', 'Pinecone环境', 'string', true, false, '^[a-zA-Z0-9-]+$', '如: us-west1-gcp-free', 2),
((SELECT id FROM config_categories WHERE name = 'pinecone'), 'index_name', '索引名称', 'Pinecone索引名称', 'string', true, false, '^[a-zA-Z0-9-_]+$', '向量索引名称', 3)
ON CONFLICT (category_id, key) DO NOTHING;

-- 插入AI模型配置项
INSERT INTO config_items (category_id, key, display_name, description, value_type, is_required, is_encrypted, help_text, sort_order) VALUES
((SELECT id FROM config_categories WHERE name = 'ai_models'), 'openai_api_key', 'OpenAI API密钥', 'OpenAI API密钥', 'password', false, true, '用于OpenAI模型调用', 1),
((SELECT id FROM config_categories WHERE name = 'ai_models'), 'deepseek_api_key', 'DeepSeek API密钥', 'DeepSeek API密钥', 'password', false, true, '用于DeepSeek模型调用', 2),
((SELECT id FROM config_categories WHERE name = 'ai_models'), 'qwen_api_key', '通义千问API密钥', '通义千问API密钥', 'password', false, true, '用于通义千问模型调用', 3),
((SELECT id FROM config_categories WHERE name = 'ai_models'), 'zhipuai_api_key', '智谱AI API密钥', '智谱AI API密钥', 'password', false, true, '用于智谱AI模型调用', 4)
ON CONFLICT (category_id, key) DO NOTHING;

-- 插入微信配置项
INSERT INTO config_items (category_id, key, display_name, description, value_type, is_required, default_value, help_text, sort_order) VALUES
((SELECT id FROM config_categories WHERE name = 'wechat'), 'whitelisted_groups', '白名单群聊', '允许处理的群聊列表', 'json', false, '[]', 'JSON格式的群聊名称列表', 1),
((SELECT id FROM config_categories WHERE name = 'wechat'), 'check_interval', '检查间隔', '消息检查间隔（秒）', 'number', false, '1', '检查新消息的时间间隔', 2),
((SELECT id FROM config_categories WHERE name = 'wechat'), 'plus_mode', 'Plus模式', '是否启用Plus模式', 'boolean', false, 'true', '启用微信Plus版功能', 3)
ON CONFLICT (category_id, key) DO NOTHING;

-- 插入监控配置项
INSERT INTO config_items (category_id, key, display_name, description, value_type, is_required, default_value, help_text, sort_order) VALUES
((SELECT id FROM config_categories WHERE name = 'monitoring'), 'enable_monitoring', '启用监控', '是否启用系统监控', 'boolean', false, 'true', '启用系统性能监控', 1),
((SELECT id FROM config_categories WHERE name = 'monitoring'), 'monitor_interval', '监控间隔', '监控检查间隔（秒）', 'number', false, '30', '监控数据收集间隔', 2),
((SELECT id FROM config_categories WHERE name = 'monitoring'), 'alert_email', '告警邮箱', '告警通知邮箱', 'string', false, '', '系统告警通知邮箱', 3)
ON CONFLICT (category_id, key) DO NOTHING;

-- 插入安全配置项
INSERT INTO config_items (category_id, key, display_name, description, value_type, is_required, default_value, help_text, sort_order) VALUES
((SELECT id FROM config_categories WHERE name = 'security'), 'enable_encryption', '启用加密', '是否启用数据加密', 'boolean', false, 'true', '启用敏感数据加密', 1),
((SELECT id FROM config_categories WHERE name = 'security'), 'session_timeout', '会话超时', '会话超时时间（分钟）', 'number', false, '60', '用户会话超时时间', 2),
((SELECT id FROM config_categories WHERE name = 'security'), 'max_login_attempts', '最大登录尝试', '最大登录尝试次数', 'number', false, '5', '防止暴力破解', 3)
ON CONFLICT (category_id, key) DO NOTHING;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_config_values_item_id ON config_values(item_id);
CREATE INDEX IF NOT EXISTS idx_config_values_active ON config_values(is_active);
CREATE INDEX IF NOT EXISTS idx_config_history_item_id ON config_history(item_id);
CREATE INDEX IF NOT EXISTS idx_config_history_created_at ON config_history(created_at);

-- 启用行级安全
ALTER TABLE config_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE config_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE config_values ENABLE ROW LEVEL SECURITY;
ALTER TABLE config_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_status ENABLE ROW LEVEL SECURITY;

-- 创建策略（允许所有操作，生产环境需要更严格的策略）
CREATE POLICY "Allow all operations" ON config_categories FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON config_items FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON config_values FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON config_history FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON service_status FOR ALL USING (true);
