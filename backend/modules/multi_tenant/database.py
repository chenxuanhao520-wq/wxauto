"""
多租户数据库架构设计
支持SQLite开发 + PostgreSQL生产的多租户方案
"""

import logging
from typing import Dict, Any, Optional, Union
from enum import Enum
from abc import ABC, abstractmethod
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """数据库类型"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class TenantIsolationStrategy(Enum):
    """租户隔离策略"""
    SHARED_DATABASE = "shared_database"      # 共享数据库，使用tenant_id字段
    SEPARATE_DATABASES = "separate_databases"  # 每个租户独立数据库
    SEPARATE_SCHEMAS = "separate_schemas"    # 每个租户独立Schema（PostgreSQL）


class MultiTenantDatabaseManager:
    """
    多租户数据库管理器
    
    支持：
    1. SQLite开发环境（单文件，简单部署）
    2. PostgreSQL生产环境（高性能，多租户）
    3. 自动数据库选择和切换
    4. 租户数据隔离
    """
    
    def __init__(self, 
                 database_type: Optional[DatabaseType] = None,
                 isolation_strategy: TenantIsolationStrategy = TenantIsolationStrategy.SHARED_DATABASE):
        """
        初始化多租户数据库管理器
        
        Args:
            database_type: 数据库类型（自动检测）
            isolation_strategy: 租户隔离策略
        """
        self.isolation_strategy = isolation_strategy
        
        # 自动检测数据库类型
        if database_type is None:
            self.database_type = self._detect_database_type()
        else:
            self.database_type = database_type
        
        # 初始化数据库连接
        self._init_database()
        
        logger.info(f"✅ 多租户数据库管理器初始化: {self.database_type.value}, 隔离策略: {isolation_strategy.value}")
    
    def _detect_database_type(self) -> DatabaseType:
        """自动检测数据库类型"""
        # 检查环境变量
        if os.getenv("DATABASE_URL"):
            if "postgresql" in os.getenv("DATABASE_URL", ""):
                return DatabaseType.POSTGRESQL
            elif "sqlite" in os.getenv("DATABASE_URL", ""):
                return DatabaseType.SQLITE
        
        # 检查Docker环境
        if os.path.exists("/.dockerenv"):
            return DatabaseType.POSTGRESQL
        
        # 默认使用SQLite（开发环境）
        return DatabaseType.SQLITE
    
    def _init_database(self):
        """初始化数据库连接"""
        if self.database_type == DatabaseType.SQLITE:
            self.db_manager = SQLiteTenantManager(self.isolation_strategy)
        elif self.database_type == DatabaseType.POSTGRESQL:
            self.db_manager = PostgreSQLTenantManager(self.isolation_strategy)
        else:
            raise ValueError(f"不支持的数据库类型: {self.database_type}")
    
    def create_tenant_database(self, tenant_id: str) -> bool:
        """为租户创建数据库"""
        return self.db_manager.create_tenant_database(tenant_id)
    
    def get_tenant_connection(self, tenant_id: str):
        """获取租户数据库连接"""
        return self.db_manager.get_tenant_connection(tenant_id)
    
    def execute_tenant_query(self, tenant_id: str, query: str, params: tuple = ()) -> list:
        """执行租户查询"""
        return self.db_manager.execute_tenant_query(tenant_id, query, params)
    
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """获取租户统计信息"""
        return self.db_manager.get_tenant_stats(tenant_id)


class BaseTenantManager(ABC):
    """租户数据库管理器基类"""
    
    def __init__(self, isolation_strategy: TenantIsolationStrategy):
        self.isolation_strategy = isolation_strategy
    
    @abstractmethod
    def create_tenant_database(self, tenant_id: str) -> bool:
        """创建租户数据库"""
        pass
    
    @abstractmethod
    def get_tenant_connection(self, tenant_id: str):
        """获取租户连接"""
        pass
    
    @abstractmethod
    def execute_tenant_query(self, tenant_id: str, query: str, params: tuple = ()) -> list:
        """执行租户查询"""
        pass
    
    @abstractmethod
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """获取租户统计"""
        pass


class SQLiteTenantManager(BaseTenantManager):
    """SQLite多租户管理器"""
    
    def __init__(self, isolation_strategy: TenantIsolationStrategy):
        super().__init__(isolation_strategy)
        self.tenant_databases = {}
        self.base_path = "data/tenants"
        os.makedirs(self.base_path, exist_ok=True)
    
    def create_tenant_database(self, tenant_id: str) -> bool:
        """为租户创建SQLite数据库"""
        try:
            if self.isolation_strategy == TenantIsolationStrategy.SEPARATE_DATABASES:
                # 每个租户独立数据库文件
                db_path = f"{self.base_path}/tenant_{tenant_id}.db"
                conn = sqlite3.connect(db_path)
                self._create_tenant_tables(conn, tenant_id)
                conn.close()
                
                self.tenant_databases[tenant_id] = db_path
                logger.info(f"✅ 创建租户SQLite数据库: {tenant_id} -> {db_path}")
                
            elif self.isolation_strategy == TenantIsolationStrategy.SHARED_DATABASE:
                # 共享数据库，使用tenant_id字段
                db_path = f"{self.base_path}/shared_tenants.db"
                conn = sqlite3.connect(db_path)
                self._create_shared_tables_with_tenant_id(conn)
                conn.close()
                
                logger.info(f"✅ 创建共享SQLite数据库: {db_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建租户数据库失败: {tenant_id}, {e}")
            return False
    
    def _create_tenant_tables(self, conn: sqlite3.Connection, tenant_id: str):
        """创建租户表结构"""
        cursor = conn.cursor()
        
        # 会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        
        # 消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        
        # 知识库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_key ON sessions(session_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_request ON messages(request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_id ON knowledge_chunks(chunk_id)")
        
        conn.commit()
    
    def _create_shared_tables_with_tenant_id(self, conn: sqlite3.Connection):
        """创建共享数据库表结构（带tenant_id字段）"""
        cursor = conn.cursor()
        
        # 会话表（带tenant_id）
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
        
        # 消息表（带tenant_id）
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
        
        # 创建租户索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON sessions(tenant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_tenant ON messages(tenant_id)")
        
        conn.commit()
    
    def get_tenant_connection(self, tenant_id: str) -> sqlite3.Connection:
        """获取租户数据库连接"""
        if self.isolation_strategy == TenantIsolationStrategy.SEPARATE_DATABASES:
            db_path = self.tenant_databases.get(tenant_id)
            if not db_path:
                raise ValueError(f"租户数据库不存在: {tenant_id}")
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
            
        elif self.isolation_strategy == TenantIsolationStrategy.SHARED_DATABASE:
            db_path = f"{self.base_path}/shared_tenants.db"
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
    
    def execute_tenant_query(self, tenant_id: str, query: str, params: tuple = ()) -> list:
        """执行租户查询"""
        with self.get_tenant_connection(tenant_id) as conn:
            cursor = conn.cursor()
            
            if self.isolation_strategy == TenantIsolationStrategy.SHARED_DATABASE:
                # 为查询添加tenant_id过滤条件
                if "WHERE" in query.upper():
                    query += f" AND tenant_id = ?"
                else:
                    query += f" WHERE tenant_id = ?"
                params = params + (tenant_id,)
            
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """获取租户统计信息"""
        try:
            # 会话数量
            sessions_query = "SELECT COUNT(*) as count FROM sessions"
            sessions_result = self.execute_tenant_query(tenant_id, sessions_query)
            session_count = sessions_result[0][0] if sessions_result else 0
            
            # 消息数量
            messages_query = "SELECT COUNT(*) as count FROM messages"
            messages_result = self.execute_tenant_query(tenant_id, messages_query)
            message_count = messages_result[0][0] if messages_result else 0
            
            # 知识库数量
            chunks_query = "SELECT COUNT(*) as count FROM knowledge_chunks"
            chunks_result = self.execute_tenant_query(tenant_id, chunks_query)
            chunk_count = chunks_result[0][0] if chunks_result else 0
            
            return {
                "tenant_id": tenant_id,
                "session_count": session_count,
                "message_count": message_count,
                "chunk_count": chunk_count,
                "database_type": "sqlite",
                "isolation_strategy": self.isolation_strategy.value
            }
            
        except Exception as e:
            logger.error(f"获取租户统计失败: {tenant_id}, {e}")
            return {"tenant_id": tenant_id, "error": str(e)}


class PostgreSQLTenantManager(BaseTenantManager):
    """PostgreSQL多租户管理器"""
    
    def __init__(self, isolation_strategy: TenantIsolationStrategy):
        super().__init__(isolation_strategy)
        self.database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/wxauto")
        self.tenant_schemas = {}
    
    def create_tenant_database(self, tenant_id: str) -> bool:
        """为租户创建PostgreSQL数据库或Schema"""
        try:
            if self.isolation_strategy == TenantIsolationStrategy.SEPARATE_DATABASES:
                # 每个租户独立数据库
                self._create_tenant_database(tenant_id)
                
            elif self.isolation_strategy == TenantIsolationStrategy.SEPARATE_SCHEMAS:
                # 每个租户独立Schema
                self._create_tenant_schema(tenant_id)
                
            elif self.isolation_strategy == TenantIsolationStrategy.SHARED_DATABASE:
                # 共享数据库，使用tenant_id字段
                self._create_shared_tables_with_tenant_id()
            
            logger.info(f"✅ 创建租户PostgreSQL数据库: {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建租户数据库失败: {tenant_id}, {e}")
            return False
    
    def _create_tenant_database(self, tenant_id: str):
        """创建租户独立数据库"""
        # 连接到默认数据库
        conn = psycopg2.connect(self.database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 创建租户数据库
        db_name = f"tenant_{tenant_id}"
        cursor.execute(f"CREATE DATABASE {db_name}")
        
        # 连接到新数据库并创建表
        tenant_url = self.database_url.rsplit('/', 1)[0] + f'/{db_name}'
        tenant_conn = psycopg2.connect(tenant_url)
        tenant_cursor = tenant_conn.cursor()
        
        self._create_tenant_tables(tenant_cursor)
        tenant_conn.commit()
        tenant_conn.close()
        
        self.tenant_databases[tenant_id] = tenant_url
        conn.close()
    
    def _create_tenant_schema(self, tenant_id: str):
        """创建租户独立Schema"""
        conn = psycopg2.connect(self.database_url)
        cursor = conn.cursor()
        
        # 创建Schema
        schema_name = f"tenant_{tenant_id}"
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        
        # 设置搜索路径
        cursor.execute(f"SET search_path TO {schema_name}")
        
        # 创建表
        self._create_tenant_tables(cursor)
        
        conn.commit()
        conn.close()
        
        self.tenant_schemas[tenant_id] = schema_name
    
    def _create_tenant_tables(self, cursor):
        """创建租户表结构"""
        # 会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                session_key VARCHAR(255) NOT NULL UNIQUE,
                group_id VARCHAR(255) NOT NULL,
                sender_id VARCHAR(255) NOT NULL,
                sender_name VARCHAR(255),
                customer_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                turn_count INTEGER DEFAULT 0,
                summary TEXT,
                status VARCHAR(50) DEFAULT 'active',
                metadata JSONB
            )
        """)
        
        # 消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                request_id VARCHAR(255) NOT NULL UNIQUE,
                session_id INTEGER REFERENCES sessions(id),
                group_id VARCHAR(255) NOT NULL,
                group_name VARCHAR(255),
                sender_id VARCHAR(255) NOT NULL,
                sender_name VARCHAR(255),
                user_message TEXT NOT NULL,
                user_message_hash VARCHAR(255),
                bot_response TEXT,
                evidence_ids JSONB,
                evidence_summary TEXT,
                confidence REAL,
                branch VARCHAR(100),
                handoff_reason VARCHAR(100),
                provider VARCHAR(100),
                model VARCHAR(100),
                token_in INTEGER DEFAULT 0,
                token_out INTEGER DEFAULT 0,
                token_total INTEGER DEFAULT 0,
                latency_receive_ms INTEGER,
                latency_retrieval_ms INTEGER,
                latency_generation_ms INTEGER,
                latency_send_ms INTEGER,
                latency_total_ms INTEGER,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                responded_at TIMESTAMP,
                status VARCHAR(50) DEFAULT 'pending',
                error_message TEXT,
                debug_info JSONB
            )
        """)
        
        # 知识库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id SERIAL PRIMARY KEY,
                chunk_id VARCHAR(255) NOT NULL UNIQUE,
                document_name VARCHAR(255) NOT NULL,
                document_version VARCHAR(100),
                section VARCHAR(255),
                content TEXT NOT NULL,
                embedding VECTOR(1536),  -- 假设使用1536维向量
                keywords TEXT,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_key ON sessions(session_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_request ON messages(request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_id ON knowledge_chunks(chunk_id)")
    
    def get_tenant_connection(self, tenant_id: str):
        """获取租户数据库连接"""
        if self.isolation_strategy == TenantIsolationStrategy.SEPARATE_DATABASES:
            tenant_url = self.tenant_databases.get(tenant_id)
            if not tenant_url:
                raise ValueError(f"租户数据库不存在: {tenant_id}")
            return psycopg2.connect(tenant_url, cursor_factory=RealDictCursor)
            
        elif self.isolation_strategy == TenantIsolationStrategy.SEPARATE_SCHEMAS:
            conn = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
            cursor = conn.cursor()
            schema_name = self.tenant_schemas.get(tenant_id)
            if schema_name:
                cursor.execute(f"SET search_path TO {schema_name}")
            return conn
            
        elif self.isolation_strategy == TenantIsolationStrategy.SHARED_DATABASE:
            return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
    
    def execute_tenant_query(self, tenant_id: str, query: str, params: tuple = ()) -> list:
        """执行租户查询"""
        with self.get_tenant_connection(tenant_id) as conn:
            cursor = conn.cursor()
            
            if self.isolation_strategy == TenantIsolationStrategy.SHARED_DATABASE:
                # 为查询添加tenant_id过滤条件
                if "WHERE" in query.upper():
                    query += f" AND tenant_id = %s"
                else:
                    query += f" WHERE tenant_id = %s"
                params = params + (tenant_id,)
            
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """获取租户统计信息"""
        try:
            # 会话数量
            sessions_query = "SELECT COUNT(*) as count FROM sessions"
            sessions_result = self.execute_tenant_query(tenant_id, sessions_query)
            session_count = sessions_result[0]['count'] if sessions_result else 0
            
            # 消息数量
            messages_query = "SELECT COUNT(*) as count FROM messages"
            messages_result = self.execute_tenant_query(tenant_id, messages_query)
            message_count = messages_result[0]['count'] if messages_result else 0
            
            # 知识库数量
            chunks_query = "SELECT COUNT(*) as count FROM knowledge_chunks"
            chunks_result = self.execute_tenant_query(tenant_id, chunks_query)
            chunk_count = chunks_result[0]['count'] if chunks_result else 0
            
            return {
                "tenant_id": tenant_id,
                "session_count": session_count,
                "message_count": message_count,
                "chunk_count": chunk_count,
                "database_type": "postgresql",
                "isolation_strategy": self.isolation_strategy.value
            }
            
        except Exception as e:
            logger.error(f"获取租户统计失败: {tenant_id}, {e}")
            return {"tenant_id": tenant_id, "error": str(e)}


# 使用示例
def setup_charging_pile_tenants():
    """设置充电桩行业租户数据库"""
    
    # 初始化多租户数据库管理器
    db_manager = MultiTenantDatabaseManager(
        isolation_strategy=TenantIsolationStrategy.SHARED_DATABASE
    )
    
    # 创建租户
    tenants = [
        "cp_beijing_001",    # 北京充电桩代理商
        "cp_shanghai_002",   # 上海充电桩服务商
        "cp_guangzhou_003"   # 广州充电桩运营商
    ]
    
    for tenant_id in tenants:
        success = db_manager.create_tenant_database(tenant_id)
        if success:
            stats = db_manager.get_tenant_stats(tenant_id)
            print(f"✅ 租户数据库创建成功: {tenant_id}")
            print(f"   统计信息: {stats}")
        else:
            print(f"❌ 租户数据库创建失败: {tenant_id}")
    
    return db_manager

