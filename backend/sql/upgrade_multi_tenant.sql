"""
多租户数据库升级脚本
为现有系统添加多租户支持
"""

-- ============================================
-- 多租户架构数据库升级脚本
-- 为现有系统添加租户隔离支持
-- ============================================

-- 1. 创建租户表
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,                    -- 租户唯一标识
    name TEXT NOT NULL,                      -- 租户名称
    tier TEXT NOT NULL DEFAULT 'basic',     -- 租户等级: basic/pro/enterprise
    status TEXT NOT NULL DEFAULT 'trial',    -- 状态: trial/active/suspended/expired
    config TEXT,                             -- 租户配置 (JSON)
    resources TEXT,                          -- 资源限制 (JSON)
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME                      -- 过期时间
);

CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_tier ON tenants(tier);

-- 2. 创建租户用户表
CREATE TABLE IF NOT EXISTS tenant_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,                 -- 租户ID
    user_id TEXT NOT NULL,                   -- 用户ID
    role TEXT NOT NULL DEFAULT 'user',      -- 角色: admin/manager/user/viewer
    permissions TEXT,                        -- 权限列表 (JSON)
    status TEXT NOT NULL DEFAULT 'active',   -- 状态: active/inactive
    added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    UNIQUE(tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_users_user ON tenant_users(user_id);

-- 3. 创建租户API密钥表
CREATE TABLE IF NOT EXISTS tenant_api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,                 -- 租户ID
    key_name TEXT NOT NULL,                  -- 密钥名称
    api_key TEXT NOT NULL UNIQUE,            -- API密钥
    permissions TEXT,                        -- 权限列表 (JSON)
    status TEXT NOT NULL DEFAULT 'active',  -- 状态: active/inactive
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME,
    expires_at DATETIME,                     -- 过期时间
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON tenant_api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON tenant_api_keys(api_key);

-- 4. 为现有表添加租户ID字段
-- 注意：这些ALTER TABLE语句在某些SQLite版本中可能不支持
-- 如果支持，执行以下语句；否则需要重建表

-- 为sessions表添加tenant_id字段
-- ALTER TABLE sessions ADD COLUMN tenant_id TEXT;
-- CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON sessions(tenant_id);

-- 为messages表添加tenant_id字段  
-- ALTER TABLE messages ADD COLUMN tenant_id TEXT;
-- CREATE INDEX IF NOT EXISTS idx_messages_tenant ON messages(tenant_id);

-- 为knowledge_chunks表添加tenant_id字段
-- ALTER TABLE knowledge_chunks ADD COLUMN tenant_id TEXT;
-- CREATE INDEX IF NOT EXISTS idx_chunks_tenant ON knowledge_chunks(tenant_id);

-- 为contacts表添加tenant_id字段
-- ALTER TABLE contacts ADD COLUMN tenant_id TEXT;
-- CREATE INDEX IF NOT EXISTS idx_contacts_tenant ON contacts(tenant_id);

-- 为threads表添加tenant_id字段
-- ALTER TABLE threads ADD COLUMN tenant_id TEXT;
-- CREATE INDEX IF NOT EXISTS idx_threads_tenant ON threads(tenant_id);

-- 5. 创建租户资源使用统计表
CREATE TABLE IF NOT EXISTS tenant_resource_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,                 -- 租户ID
    resource_type TEXT NOT NULL,             -- 资源类型: api_calls/storage_mb/groups/users
    usage_count INTEGER NOT NULL DEFAULT 0,  -- 使用量
    usage_date DATE NOT NULL,                -- 统计日期
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    UNIQUE(tenant_id, resource_type, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_resource_usage_tenant ON tenant_resource_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_resource_usage_date ON tenant_resource_usage(usage_date);

-- 6. 创建租户配置历史表
CREATE TABLE IF NOT EXISTS tenant_config_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,                 -- 租户ID
    config_snapshot TEXT NOT NULL,            -- 配置快照 (JSON)
    version TEXT NOT NULL,                    -- 版本号
    change_reason TEXT,                       -- 变更原因
    changed_by TEXT,                          -- 变更人
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_config_history_tenant ON tenant_config_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_config_history_version ON tenant_config_history(version);

-- 7. 插入默认租户（用于现有数据迁移）
INSERT OR IGNORE INTO tenants (
    id, 
    name, 
    tier, 
    status, 
    config, 
    resources
) VALUES (
    'default_tenant',
    '默认租户',
    'basic',
    'active',
    '{
        "ai": {
            "provider": "qwen",
            "model": "qwen-turbo",
            "max_tokens": 512,
            "temperature": 0.3
        },
        "rag": {
            "top_k": 4,
            "min_confidence": 0.75
        },
        "rate_limits": {
            "per_group_per_minute": 20,
            "per_user_per_30s": 1,
            "global_per_minute": 100
        }
    }',
    '{
        "max_groups": 10,
        "max_users": 100,
        "max_documents": 1000,
        "max_storage_mb": 1024,
        "api_calls_per_day": 10000
    }'
);

-- 8. 创建租户管理视图
CREATE VIEW IF NOT EXISTS tenant_overview AS
SELECT 
    t.id,
    t.name,
    t.tier,
    t.status,
    COUNT(DISTINCT tu.user_id) as user_count,
    COUNT(DISTINCT tak.api_key) as api_key_count,
    t.created_at,
    t.expires_at
FROM tenants t
LEFT JOIN tenant_users tu ON t.id = tu.tenant_id AND tu.status = 'active'
LEFT JOIN tenant_api_keys tak ON t.id = tak.tenant_id AND tak.status = 'active'
GROUP BY t.id, t.name, t.tier, t.status, t.created_at, t.expires_at;

-- 9. 创建租户资源使用视图
CREATE VIEW IF NOT EXISTS tenant_resource_summary AS
SELECT 
    t.id as tenant_id,
    t.name as tenant_name,
    t.tier,
    SUM(CASE WHEN tru.resource_type = 'api_calls' THEN tru.usage_count ELSE 0 END) as total_api_calls,
    SUM(CASE WHEN tru.resource_type = 'storage_mb' THEN tru.usage_count ELSE 0 END) as total_storage_mb,
    SUM(CASE WHEN tru.resource_type = 'groups' THEN tru.usage_count ELSE 0 END) as total_groups,
    SUM(CASE WHEN tru.resource_type = 'users' THEN tru.usage_count ELSE 0 END) as total_users
FROM tenants t
LEFT JOIN tenant_resource_usage tru ON t.id = tru.tenant_id
WHERE tru.usage_date >= date('now', '-30 days')  -- 最近30天
GROUP BY t.id, t.name, t.tier;

-- 10. 创建触发器：自动更新租户统计
CREATE TRIGGER IF NOT EXISTS update_tenant_stats_after_user_add
AFTER INSERT ON tenant_users
BEGIN
    UPDATE tenant_resource_usage 
    SET usage_count = usage_count + 1
    WHERE tenant_id = NEW.tenant_id 
    AND resource_type = 'users' 
    AND usage_date = date('now');
END;

CREATE TRIGGER IF NOT EXISTS update_tenant_stats_after_user_remove
AFTER DELETE ON tenant_users
BEGIN
    UPDATE tenant_resource_usage 
    SET usage_count = usage_count - 1
    WHERE tenant_id = OLD.tenant_id 
    AND resource_type = 'users' 
    AND usage_date = date('now');
END;

-- 11. 创建租户配置变更触发器
CREATE TRIGGER IF NOT EXISTS log_tenant_config_change
AFTER UPDATE OF config ON tenants
BEGIN
    INSERT INTO tenant_config_history (
        tenant_id,
        config_snapshot,
        version,
        change_reason,
        changed_by
    ) VALUES (
        NEW.id,
        NEW.config,
        '1.0',
        'Configuration updated',
        'system'
    );
END;

-- 12. 创建租户数据迁移函数（SQLite不支持函数，这里提供SQL模板）
-- 将现有数据迁移到默认租户
-- UPDATE sessions SET tenant_id = 'default_tenant' WHERE tenant_id IS NULL;
-- UPDATE messages SET tenant_id = 'default_tenant' WHERE tenant_id IS NULL;
-- UPDATE knowledge_chunks SET tenant_id = 'default_tenant' WHERE tenant_id IS NULL;
-- UPDATE contacts SET tenant_id = 'default_tenant' WHERE tenant_id IS NULL;
-- UPDATE threads SET tenant_id = 'default_tenant' WHERE tenant_id IS NULL;

-- 13. 创建租户隔离检查约束
-- 注意：SQLite不支持CHECK约束，这里提供逻辑约束说明
-- 所有查询都应该包含 tenant_id 过滤条件
-- 例如：SELECT * FROM sessions WHERE tenant_id = ? AND group_id = ?

-- 14. 创建租户数据清理函数
-- 删除过期租户的数据（需要应用程序逻辑实现）
-- DELETE FROM sessions WHERE tenant_id IN (SELECT id FROM tenants WHERE status = 'expired');
-- DELETE FROM messages WHERE tenant_id IN (SELECT id FROM tenants WHERE status = 'expired');
-- DELETE FROM knowledge_chunks WHERE tenant_id IN (SELECT id FROM tenants WHERE status = 'expired');

-- 15. 创建租户备份表（用于数据恢复）
CREATE TABLE IF NOT EXISTS tenant_backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    backup_type TEXT NOT NULL,               -- full/incremental
    backup_data TEXT NOT NULL,               -- 备份数据 (JSON)
    backup_size INTEGER,                     -- 备份大小
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_backups_tenant ON tenant_backups(tenant_id);
CREATE INDEX IF NOT EXISTS idx_backups_type ON tenant_backups(backup_type);

-- 完成多租户架构升级
-- 注意：执行此脚本后，需要：
-- 1. 更新应用程序代码以支持租户隔离
-- 2. 迁移现有数据到默认租户
-- 3. 更新API接口以包含租户认证
-- 4. 测试多租户功能

