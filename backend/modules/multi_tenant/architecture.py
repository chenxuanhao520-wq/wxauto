"""
多租户架构设计方案
支持充电桩行业多代理商独立部署和数据隔离
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TenantStatus(Enum):
    """租户状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    TRIAL = "trial"


class TenantTier(Enum):
    """租户等级"""
    BASIC = "basic"        # 基础版
    PROFESSIONAL = "pro"   # 专业版
    ENTERPRISE = "enterprise"  # 企业版


class MultiTenantArchitecture:
    """
    多租户架构设计
    
    支持：
    1. 数据隔离（每个租户独立数据）
    2. 配置隔离（每个租户独立配置）
    3. 资源隔离（每个租户独立资源限制）
    4. 权限管理（租户内用户权限）
    """
    
    def __init__(self):
        self.tenant_configs = {}
        self.tenant_resources = {}
        self.tenant_users = {}
    
    def create_tenant(self, 
                     tenant_id: str,
                     tenant_name: str,
                     tier: TenantTier = TenantTier.BASIC,
                     config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        创建新租户
        
        Args:
            tenant_id: 租户唯一标识
            tenant_name: 租户名称
            tier: 租户等级
            config: 租户配置
            
        Returns:
            租户信息
        """
        tenant_info = {
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "tier": tier.value,
            "status": TenantStatus.TRIAL.value,
            "created_at": datetime.now().isoformat(),
            "expires_at": None,
            "config": config or self._get_default_config(tier),
            "resources": self._get_default_resources(tier),
            "users": [],
            "api_keys": []
        }
        
        self.tenant_configs[tenant_id] = tenant_info
        logger.info(f"✅ 创建租户: {tenant_id} ({tenant_name})")
        
        return tenant_info
    
    def _get_default_config(self, tier: TenantTier) -> Dict[str, Any]:
        """获取默认租户配置"""
        base_config = {
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
        }
        
        # 根据等级调整配置
        if tier == TenantTier.PROFESSIONAL:
            base_config["rate_limits"]["global_per_minute"] = 500
            base_config["ai"]["max_tokens"] = 1024
        elif tier == TenantTier.ENTERPRISE:
            base_config["rate_limits"]["global_per_minute"] = 1000
            base_config["ai"]["max_tokens"] = 2048
            base_config["rag"]["top_k"] = 8
        
        return base_config
    
    def _get_default_resources(self, tier: TenantTier) -> Dict[str, Any]:
        """获取默认资源限制"""
        resources = {
            "max_groups": 10,
            "max_users": 100,
            "max_documents": 1000,
            "max_storage_mb": 1024,
            "api_calls_per_day": 10000
        }
        
        if tier == TenantTier.PROFESSIONAL:
            resources.update({
                "max_groups": 50,
                "max_users": 500,
                "max_documents": 5000,
                "max_storage_mb": 10240,
                "api_calls_per_day": 50000
            })
        elif tier == TenantTier.ENTERPRISE:
            resources.update({
                "max_groups": 200,
                "max_users": 2000,
                "max_documents": 20000,
                "max_storage_mb": 102400,
                "api_calls_per_day": 200000
            })
        
        return resources
    
    def add_user_to_tenant(self, 
                          tenant_id: str,
                          user_id: str,
                          role: str = "user",
                          permissions: Optional[List[str]] = None) -> bool:
        """
        添加用户到租户
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            role: 用户角色
            permissions: 权限列表
            
        Returns:
            是否成功
        """
        if tenant_id not in self.tenant_configs:
            logger.error(f"租户不存在: {tenant_id}")
            return False
        
        user_info = {
            "user_id": user_id,
            "role": role,
            "permissions": permissions or self._get_default_permissions(role),
            "added_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        if tenant_id not in self.tenant_users:
            self.tenant_users[tenant_id] = []
        
        self.tenant_users[tenant_id].append(user_info)
        self.tenant_configs[tenant_id]["users"].append(user_id)
        
        logger.info(f"✅ 添加用户到租户: {user_id} -> {tenant_id}")
        return True
    
    def _get_default_permissions(self, role: str) -> List[str]:
        """获取默认权限"""
        permissions_map = {
            "admin": ["read", "write", "delete", "manage_users", "manage_config"],
            "manager": ["read", "write", "manage_users"],
            "user": ["read", "write"],
            "viewer": ["read"]
        }
        return permissions_map.get(role, ["read"])
    
    def get_tenant_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """获取租户配置"""
        return self.tenant_configs.get(tenant_id)
    
    def update_tenant_config(self, 
                            tenant_id: str,
                            config_updates: Dict[str, Any]) -> bool:
        """更新租户配置"""
        if tenant_id not in self.tenant_configs:
            return False
        
        # 深度合并配置
        current_config = self.tenant_configs[tenant_id]["config"]
        self._deep_merge(current_config, config_updates)
        
        logger.info(f"✅ 更新租户配置: {tenant_id}")
        return True
    
    def _deep_merge(self, base: Dict, updates: Dict):
        """深度合并字典"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def check_resource_limits(self, tenant_id: str, resource_type: str) -> bool:
        """检查资源限制"""
        if tenant_id not in self.tenant_configs:
            return False
        
        resources = self.tenant_configs[tenant_id]["resources"]
        current_usage = self.tenant_resources.get(tenant_id, {})
        
        if resource_type in resources:
            limit = resources[resource_type]
            current = current_usage.get(resource_type, 0)
            return current < limit
        
        return True
    
    def increment_resource_usage(self, tenant_id: str, resource_type: str, amount: int = 1):
        """增加资源使用量"""
        if tenant_id not in self.tenant_resources:
            self.tenant_resources[tenant_id] = {}
        
        current = self.tenant_resources[tenant_id].get(resource_type, 0)
        self.tenant_resources[tenant_id][resource_type] = current + amount
    
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """获取租户统计信息"""
        if tenant_id not in self.tenant_configs:
            return {}
        
        config = self.tenant_configs[tenant_id]
        usage = self.tenant_resources.get(tenant_id, {})
        
        return {
            "tenant_id": tenant_id,
            "tenant_name": config["tenant_name"],
            "tier": config["tier"],
            "status": config["status"],
            "resource_usage": usage,
            "resource_limits": config["resources"],
            "user_count": len(config["users"]),
            "created_at": config["created_at"]
        }


class TenantDatabaseManager:
    """
    租户数据库管理器
    
    实现数据隔离：
    1. 每个租户独立数据库
    2. 或者使用租户ID字段隔离
    """
    
    def __init__(self, isolation_strategy: str = "shared_database"):
        """
        初始化
        
        Args:
            isolation_strategy: 隔离策略
                - "shared_database": 共享数据库，使用tenant_id字段隔离
                - "separate_databases": 每个租户独立数据库
        """
        self.isolation_strategy = isolation_strategy
        self.tenant_databases = {}
    
    def get_database_path(self, tenant_id: str) -> str:
        """获取租户数据库路径"""
        if self.isolation_strategy == "separate_databases":
            return f"data/tenant_{tenant_id}.db"
        else:
            return "data/shared_tenant.db"
    
    def create_tenant_tables(self, tenant_id: str):
        """为租户创建表结构"""
        if self.isolation_strategy == "separate_databases":
            # 每个租户独立数据库
            db_path = self.get_database_path(tenant_id)
            self._create_tables_with_tenant_id(db_path, tenant_id)
        else:
            # 共享数据库，使用tenant_id字段
            self._create_shared_tables_with_tenant_id()
    
    def _create_tables_with_tenant_id(self, db_path: str, tenant_id: str):
        """创建带租户ID的表结构"""
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 会话表（带租户ID）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                session_key TEXT NOT NULL UNIQUE,
                group_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                sender_name TEXT,
                customer_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                turn_count INTEGER DEFAULT 0,
                summary TEXT,
                status TEXT DEFAULT 'active',
                metadata TEXT
            )
        """)
        
        # 消息表（带租户ID）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                request_id TEXT NOT NULL UNIQUE,
                session_id INTEGER,
                group_id TEXT NOT NULL,
                group_name TEXT,
                sender_id TEXT NOT NULL,
                sender_name TEXT,
                user_message TEXT NOT NULL,
                user_message_hash TEXT,
                bot_response TEXT,
                evidence_ids TEXT,
                evidence_summary TEXT,
                confidence REAL,
                branch TEXT,
                handoff_reason TEXT,
                provider TEXT,
                model TEXT,
                token_in INTEGER DEFAULT 0,
                token_out INTEGER DEFAULT 0,
                token_total INTEGER DEFAULT 0,
                latency_receive_ms INTEGER,
                latency_retrieval_ms INTEGER,
                latency_generation_ms INTEGER,
                latency_send_ms INTEGER,
                latency_total_ms INTEGER,
                received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                responded_at DATETIME,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                debug_info TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        # 知识库表（带租户ID）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                chunk_id TEXT NOT NULL UNIQUE,
                document_name TEXT NOT NULL,
                document_version TEXT,
                section TEXT,
                content TEXT NOT NULL,
                embedding BLOB,
                keywords TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON sessions(tenant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_tenant ON messages(tenant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_tenant ON knowledge_chunks(tenant_id)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 为租户 {tenant_id} 创建数据库表结构")
    
    def _create_shared_tables_with_tenant_id(self):
        """创建共享数据库表结构（带租户ID字段）"""
        # 这里会修改现有的表结构，添加tenant_id字段
        pass


class TenantConfigManager:
    """
    租户配置管理器
    
    支持：
    1. 每个租户独立配置
    2. 配置继承和覆盖
    3. 配置版本管理
    """
    
    def __init__(self):
        self.tenant_configs = {}
        self.config_templates = {}
    
    def create_config_template(self, template_name: str, config: Dict[str, Any]):
        """创建配置模板"""
        self.config_templates[template_name] = {
            "config": config,
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        logger.info(f"✅ 创建配置模板: {template_name}")
    
    def apply_template_to_tenant(self, tenant_id: str, template_name: str, overrides: Optional[Dict] = None):
        """将模板应用到租户"""
        if template_name not in self.config_templates:
            logger.error(f"配置模板不存在: {template_name}")
            return False
        
        template_config = self.config_templates[template_name]["config"].copy()
        
        # 应用覆盖配置
        if overrides:
            self._deep_merge(template_config, overrides)
        
        self.tenant_configs[tenant_id] = {
            "config": template_config,
            "template": template_name,
            "applied_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        logger.info(f"✅ 为租户 {tenant_id} 应用配置模板: {template_name}")
        return True
    
    def get_tenant_config(self, tenant_id: str, key_path: Optional[str] = None) -> Any:
        """获取租户配置"""
        if tenant_id not in self.tenant_configs:
            return None
        
        config = self.tenant_configs[tenant_id]["config"]
        
        if key_path:
            # 支持点号路径，如 "ai.primary.model"
            keys = key_path.split(".")
            for key in keys:
                if isinstance(config, dict) and key in config:
                    config = config[key]
                else:
                    return None
        
        return config
    
    def update_tenant_config(self, tenant_id: str, key_path: str, value: Any) -> bool:
        """更新租户配置"""
        if tenant_id not in self.tenant_configs:
            return False
        
        config = self.tenant_configs[tenant_id]["config"]
        keys = key_path.split(".")
        
        # 导航到目标位置
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置值
        config[keys[-1]] = value
        
        logger.info(f"✅ 更新租户配置: {tenant_id}.{key_path} = {value}")
        return True
    
    def _deep_merge(self, base: Dict, updates: Dict):
        """深度合并字典"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value


# 使用示例
def create_charging_pile_tenants():
    """创建充电桩行业租户示例"""
    
    # 初始化多租户架构
    mt_arch = MultiTenantArchitecture()
    db_manager = TenantDatabaseManager()
    config_manager = TenantConfigManager()
    
    # 创建配置模板
    charging_pile_template = {
        "ai": {
            "provider": "qwen",
            "model": "qwen-turbo",
            "system_prompt": "你是充电桩技术专家，负责解答充电桩相关问题。"
        },
        "rag": {
            "top_k": 5,
            "min_confidence": 0.8,
            "rerank_model": "bge-reranker-base"
        },
        "rate_limits": {
            "per_group_per_minute": 30,
            "per_user_per_30s": 2,
            "global_per_minute": 200
        },
        "charging_pile": {
            "fault_codes_enabled": True,
            "maintenance_reminders": True,
            "parts_inventory": True
        }
    }
    
    config_manager.create_config_template("charging_pile_pro", charging_pile_template)
    
    # 创建租户
    tenants = [
        {
            "tenant_id": "cp_beijing_001",
            "tenant_name": "北京充电桩代理商",
            "tier": TenantTier.PROFESSIONAL
        },
        {
            "tenant_id": "cp_shanghai_002", 
            "tenant_name": "上海充电桩服务商",
            "tier": TenantTier.ENTERPRISE
        },
        {
            "tenant_id": "cp_guangzhou_003",
            "tenant_name": "广州充电桩运营商",
            "tier": TenantTier.BASIC
        }
    ]
    
    for tenant_info in tenants:
        # 创建租户
        tenant = mt_arch.create_tenant(**tenant_info)
        
        # 应用配置模板
        config_manager.apply_template_to_tenant(
            tenant["tenant_id"], 
            "charging_pile_pro"
        )
        
        # 创建数据库表
        db_manager.create_tenant_tables(tenant["tenant_id"])
        
        # 添加管理员用户
        mt_arch.add_user_to_tenant(
            tenant["tenant_id"],
            f"admin_{tenant['tenant_id']}",
            role="admin"
        )
        
        print(f"✅ 创建租户: {tenant['tenant_name']} ({tenant['tenant_id']})")
    
    return mt_arch, db_manager, config_manager

