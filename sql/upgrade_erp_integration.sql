-- ERP集成数据库升级脚本
-- 版本: v3.0
-- 创建时间: 2025-10-18
-- 说明: 支持ERP双向同步、智能融合、规则引擎

-- =============================================
-- 1. 统一客户表（融合ERP和微信数据）
-- =============================================

CREATE TABLE IF NOT EXISTS customers_unified (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- ========== 唯一标识 ==========
    erp_customer_id INTEGER UNIQUE,                    -- ERP客户ID（权威标识）
    erp_customer_code VARCHAR(50),                     -- ERP客户编号（如：KH2025001）
    wechat_id VARCHAR(100) UNIQUE,                     -- 微信ID
    
    -- ========== 基础信息（多源融合）==========
    -- 公司名称
    company_name VARCHAR(200),
    company_name_source VARCHAR(20) DEFAULT 'unknown', -- 来源：erp/wechat/ai/manual
    company_name_verified BOOLEAN DEFAULT 0,
    company_name_verified_at DATETIME,
    
    -- 真实姓名
    real_name VARCHAR(100),
    real_name_source VARCHAR(20) DEFAULT 'unknown',
    
    -- 手机号
    phone VARCHAR(20),
    phone_source VARCHAR(20) DEFAULT 'unknown',
    phone_verified BOOLEAN DEFAULT 0,
    phone_verified_at DATETIME,
    
    -- 邮箱
    email VARCHAR(100),
    email_source VARCHAR(20) DEFAULT 'unknown',
    email_verified BOOLEAN DEFAULT 0,
    
    -- 地址
    address TEXT,
    address_source VARCHAR(20) DEFAULT 'unknown',
    
    -- ========== 微信特有字段 ==========
    wechat_nickname VARCHAR(200),                      -- 微信昵称
    wechat_avatar VARCHAR(500),                        -- 微信头像URL
    wechat_remark VARCHAR(200),                        -- 微信备注名
    
    -- ========== ERP特有字段 ==========
    erp_customer_type INTEGER DEFAULT 1,               -- 1=单位客户 2=个人客户
    erp_customer_category VARCHAR(100),                -- 客户分类（树结构）
    erp_follow_level VARCHAR(50),                      -- 跟进程度
    erp_source VARCHAR(50),                            -- 客户来源（ERP中的枚举值）
    erp_value_assessment VARCHAR(50),                  -- 价值评估
    erp_industry VARCHAR(50),                          -- 客户行业
    erp_region VARCHAR(50),                            -- 客户区域
    
    -- ========== AI提取的补充信息 ==========
    extracted_company_info TEXT,                       -- JSON: 从聊天提取的公司信息
    extracted_product_interest TEXT,                   -- JSON: 感兴趣的产品列表
    extracted_needs TEXT,                              -- JSON: 提取的需求信息
    business_license_info TEXT,                        -- JSON: 营业执照OCR信息
    business_license_path VARCHAR(500),                -- 营业执照图片路径
    business_license_verified BOOLEAN DEFAULT 0,
    
    -- ========== 商业意向评分 ==========
    intent_score FLOAT DEFAULT 0.0,                    -- 商业意向分数 0-100
    intent_level VARCHAR(20),                          -- high/medium/low
    intent_signals TEXT,                               -- JSON: 意向信号列表
    intent_updated_at DATETIME,
    
    -- ========== 互动统计 ==========
    message_count INTEGER DEFAULT 0,                   -- 消息总数
    conversation_days INTEGER DEFAULT 0,               -- 沟通天数
    first_contact_time DATETIME,                       -- 首次联系时间
    last_contact_time DATETIME,                        -- 最后联系时间
    last_message_content TEXT,                         -- 最后一条消息
    
    -- ========== 业务标记 ==========
    has_order BOOLEAN DEFAULT 0,                       -- 是否有订单
    has_contract BOOLEAN DEFAULT 0,                    -- 是否有合同
    has_payment BOOLEAN DEFAULT 0,                     -- 是否有付款
    marked_as_important BOOLEAN DEFAULT 0,             -- 标记为重要客户
    marked_as_invalid BOOLEAN DEFAULT 0,               -- 标记为无效客户
    has_quote_request BOOLEAN DEFAULT 0,               -- 有询价请求
    
    -- ========== 数据质量评估 ==========
    data_quality_score FLOAT DEFAULT 0.0,              -- 数据质量分数 0-100
    data_completeness FLOAT DEFAULT 0.0,               -- 数据完整度 0-1
    quality_issues TEXT,                               -- JSON: 质量问题列表
    
    -- ========== 同步状态 ==========
    erp_sync_status VARCHAR(20) DEFAULT 'pending',     -- pending/synced/failed/skipped
    erp_sync_action VARCHAR(20),                       -- create/update/skip
    erp_sync_rule VARCHAR(100),                        -- 匹配的同步规则
    erp_sync_confidence FLOAT,                         -- 同步置信度
    erp_sync_error TEXT,                               -- 同步错误信息
    
    erp_last_pulled DATETIME,                          -- 最后从ERP拉取时间
    erp_last_pushed DATETIME,                          -- 最后推送到ERP时间
    
    local_updated_at DATETIME,                         -- 本地最后更新时间
    erp_updated_at DATETIME,                           -- ERP最后更新时间（来自ERP）
    
    -- ========== 元数据 ==========
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system',
    updated_by VARCHAR(100) DEFAULT 'system',
    
    -- ========== 索引 ==========
    CONSTRAINT unique_erp_id UNIQUE (erp_customer_id),
    CONSTRAINT unique_wechat_id UNIQUE (wechat_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_customers_erp_id ON customers_unified(erp_customer_id);
CREATE INDEX IF NOT EXISTS idx_customers_wechat_id ON customers_unified(wechat_id);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers_unified(phone);
CREATE INDEX IF NOT EXISTS idx_customers_sync_status ON customers_unified(erp_sync_status);
CREATE INDEX IF NOT EXISTS idx_customers_quality_score ON customers_unified(data_quality_score);
CREATE INDEX IF NOT EXISTS idx_customers_intent_score ON customers_unified(intent_score);

-- =============================================
-- 2. 同步日志表
-- =============================================

CREATE TABLE IF NOT EXISTS erp_sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    customer_id INTEGER,                               -- 关联客户ID
    sync_direction VARCHAR(20) NOT NULL,               -- erp_to_local/local_to_erp/bidirectional
    sync_type VARCHAR(20) NOT NULL,                    -- pull/push/merge
    
    -- 同步详情
    sync_action VARCHAR(20),                           -- create/update/skip/delete
    sync_result VARCHAR(20) NOT NULL,                  -- success/failed/partial
    
    changed_fields TEXT,                               -- JSON: 变更的字段列表
    field_count INTEGER DEFAULT 0,                     -- 变更字段数量
    
    -- 规则信息
    matched_rule VARCHAR(100),                         -- 匹配的规则名称
    rule_confidence FLOAT,                             -- 规则置信度
    rule_reason TEXT,                                  -- 规则判定原因
    
    -- ERP交互信息
    erp_customer_id INTEGER,                           -- ERP客户ID
    erp_request TEXT,                                  -- 发送给ERP的请求（JSON）
    erp_response TEXT,                                 -- ERP返回的响应（JSON）
    
    -- 错误信息
    error_message TEXT,
    error_code VARCHAR(50),
    error_stack TEXT,
    
    -- 性能指标
    sync_duration_ms INTEGER,                          -- 同步耗时（毫秒）
    retry_count INTEGER DEFAULT 0,                     -- 重试次数
    
    -- 元数据
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    synced_by VARCHAR(100) DEFAULT 'system',
    
    FOREIGN KEY (customer_id) REFERENCES customers_unified(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sync_logs_customer ON erp_sync_logs(customer_id);
CREATE INDEX IF NOT EXISTS idx_sync_logs_direction ON erp_sync_logs(sync_direction);
CREATE INDEX IF NOT EXISTS idx_sync_logs_result ON erp_sync_logs(sync_result);
CREATE INDEX IF NOT EXISTS idx_sync_logs_time ON erp_sync_logs(synced_at);

-- =============================================
-- 3. 字段变更历史表
-- =============================================

CREATE TABLE IF NOT EXISTS field_change_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    customer_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    
    old_value TEXT,
    new_value TEXT,
    value_source VARCHAR(20),                          -- erp/wechat/ai/manual
    
    change_type VARCHAR(20),                           -- update/create/delete/merge
    change_reason TEXT,                                -- 变更原因
    
    changed_by VARCHAR(100) DEFAULT 'system',
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers_unified(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_field_history_customer ON field_change_history(customer_id, field_name);
CREATE INDEX IF NOT EXISTS idx_field_history_time ON field_change_history(changed_at);

-- =============================================
-- 4. ERP同步配置表
-- =============================================

CREATE TABLE IF NOT EXISTS erp_sync_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string',          -- string/int/float/json/boolean
    
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认配置
INSERT OR IGNORE INTO erp_sync_config (config_key, config_value, config_type, description) VALUES
('erp_pull_enabled', 'true', 'boolean', '是否启用从ERP拉取数据'),
('erp_pull_interval', '3600', 'int', 'ERP拉取间隔（秒）'),
('erp_push_enabled', 'true', 'boolean', '是否启用推送到ERP'),
('erp_push_interval', '1800', 'int', 'ERP推送间隔（秒）'),
('auto_sync_enabled', 'true', 'boolean', '是否启用自动同步'),
('min_quality_score', '60', 'float', '同步的最低质量分数'),
('min_intent_score', '50', 'float', '同步的最低意向分数'),
('batch_size', '50', 'int', '批量同步数量'),
('last_erp_pull_time', '', 'string', '最后ERP拉取时间'),
('last_erp_push_time', '', 'string', '最后ERP推送时间');

-- =============================================
-- 5. 同步规则表
-- =============================================

CREATE TABLE IF NOT EXISTS erp_sync_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    rule_name VARCHAR(100) UNIQUE NOT NULL,
    rule_type VARCHAR(50) NOT NULL,                    -- mandatory/high_quality/medium_quality/low_quality
    rule_priority INTEGER DEFAULT 0,                   -- 优先级（越大越优先）
    
    rule_conditions TEXT NOT NULL,                     -- JSON: 规则条件
    rule_action VARCHAR(20) NOT NULL,                  -- CREATE/UPDATE/SKIP
    
    is_active BOOLEAN DEFAULT 1,
    description TEXT,
    
    match_count INTEGER DEFAULT 0,                     -- 匹配次数统计
    success_count INTEGER DEFAULT 0,                   -- 成功次数
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认规则
INSERT OR IGNORE INTO erp_sync_rules (rule_name, rule_type, rule_priority, rule_conditions, rule_action, description) VALUES
('mandatory_has_order', 'mandatory', 100, '{"has_order": true}', 'CREATE', '客户已下单，强制同步'),
('mandatory_has_contract', 'mandatory', 100, '{"has_contract": true}', 'CREATE', '客户已签合同，强制同步'),
('mandatory_has_payment', 'mandatory', 100, '{"has_payment": true}', 'CREATE', '客户已付款，强制同步'),
('mandatory_marked_important', 'mandatory', 100, '{"marked_as_important": true}', 'CREATE', '标记为重要客户，强制同步'),

('high_quality_verified', 'high_quality', 80, '{"phone_verified": true, "company_name_verified": true, "min_intent_score": 80}', 'CREATE', '高质量客户：信息已验证+高意向'),
('high_quality_license', 'high_quality', 75, '{"business_license_verified": true, "min_quality_score": 80}', 'CREATE', '高质量客户：营业执照已验证'),

('medium_phone_quote', 'medium_quality', 50, '{"phone_verified": true, "has_quote_request": true}', 'CREATE', '中等质量：有手机号+明确询价'),
('medium_company_license', 'medium_quality', 50, '{"company_name": "not_empty", "business_license_uploaded": true}', 'CREATE', '中等质量：公司名+营业执照'),
('medium_deep_engagement', 'medium_quality', 45, '{"min_conversation_days": 7, "min_message_count": 50}', 'CREATE', '中等质量：深度沟通'),

('low_no_info', 'low_quality', 0, '{"no_basic_info": true}', 'SKIP', '低质量：无基本信息'),
('low_intent', 'low_quality', 0, '{"max_intent_score": 30}', 'SKIP', '低质量：意向过低'),
('low_engagement', 'low_quality', 0, '{"max_message_count": 5}', 'SKIP', '低质量：互动太少'),
('low_marked_invalid', 'low_quality', 0, '{"marked_as_invalid": true}', 'SKIP', '低质量：已标记无效');

-- =============================================
-- 6. ERP API调用日志表
-- =============================================

CREATE TABLE IF NOT EXISTS erp_api_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    api_endpoint VARCHAR(200) NOT NULL,
    http_method VARCHAR(10) DEFAULT 'POST',
    
    request_params TEXT,                               -- JSON: 请求参数
    request_headers TEXT,                              -- JSON: 请求头
    
    response_status INTEGER,                           -- HTTP状态码
    response_body TEXT,                                -- 响应体
    response_time_ms INTEGER,                          -- 响应时间（毫秒）
    
    is_success BOOLEAN,
    error_message TEXT,
    
    called_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    called_by VARCHAR(100) DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON erp_api_logs(api_endpoint);
CREATE INDEX IF NOT EXISTS idx_api_logs_time ON erp_api_logs(called_at);
CREATE INDEX IF NOT EXISTS idx_api_logs_success ON erp_api_logs(is_success);

-- =============================================
-- 7. 创建视图
-- =============================================

-- 待同步客户视图
CREATE VIEW IF NOT EXISTS v_pending_sync_customers AS
SELECT 
    c.*,
    CASE 
        WHEN c.has_order OR c.has_contract OR c.has_payment THEN 'mandatory'
        WHEN c.data_quality_score >= 80 THEN 'high_quality'
        WHEN c.data_quality_score >= 50 THEN 'medium_quality'
        ELSE 'low_quality'
    END as sync_priority,
    CASE
        WHEN c.erp_customer_id IS NULL THEN 'CREATE'
        WHEN c.local_updated_at > c.erp_last_pushed THEN 'UPDATE'
        ELSE 'SKIP'
    END as recommended_action
FROM customers_unified c
WHERE c.erp_sync_status IN ('pending', 'failed')
  AND c.marked_as_invalid = 0
ORDER BY 
    CASE sync_priority
        WHEN 'mandatory' THEN 1
        WHEN 'high_quality' THEN 2
        WHEN 'medium_quality' THEN 3
        ELSE 4
    END,
    c.data_quality_score DESC;

-- 同步统计视图
CREATE VIEW IF NOT EXISTS v_sync_statistics AS
SELECT 
    DATE(synced_at) as sync_date,
    sync_direction,
    sync_result,
    COUNT(*) as count,
    AVG(sync_duration_ms) as avg_duration_ms
FROM erp_sync_logs
GROUP BY DATE(synced_at), sync_direction, sync_result;

-- =============================================
-- 8. 数据迁移（如果有旧表）
-- =============================================

-- 从旧的customers表迁移数据到customers_unified
-- 注意：根据实际情况调整
-- INSERT INTO customers_unified (wechat_id, wechat_nickname, phone, company_name, created_at)
-- SELECT wechat_id, nickname, phone, company_name, created_at
-- FROM customers
-- WHERE NOT EXISTS (SELECT 1 FROM customers_unified WHERE customers_unified.wechat_id = customers.wechat_id);

-- =============================================
-- 9. 触发器（自动更新时间戳）
-- =============================================

CREATE TRIGGER IF NOT EXISTS update_customers_unified_timestamp 
AFTER UPDATE ON customers_unified
FOR EACH ROW
BEGIN
    UPDATE customers_unified 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_sync_config_timestamp 
AFTER UPDATE ON erp_sync_config
FOR EACH ROW
BEGIN
    UPDATE erp_sync_config 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- =============================================
-- 完成
-- =============================================

-- 输出成功信息
SELECT 'ERP集成数据库升级完成！' as message;
SELECT 'Tables created: ' || COUNT(*) as info FROM sqlite_master WHERE type='table' AND name LIKE '%erp%' OR name = 'customers_unified';

