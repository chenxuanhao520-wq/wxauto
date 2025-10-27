#!/usr/bin/env python3
"""
数据迁移脚本 - SQLite到Supabase
将现有的SQLite数据迁移到Supabase数据库
"""

import os
import sys
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.storage.unified_database import get_database_manager, init_database_manager

logger = logging.getLogger(__name__)


class DataMigrator:
    """数据迁移器"""
    
    def __init__(self, sqlite_path: str = "data/data.db"):
        self.sqlite_path = sqlite_path
        self.db_manager = get_database_manager()
        
        logger.info(f"✅ 数据迁移器初始化: {sqlite_path}")
    
    def check_sqlite_exists(self) -> bool:
        """检查SQLite数据库是否存在"""
        return Path(self.sqlite_path).exists()
    
    def get_sqlite_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """从SQLite获取所有数据"""
        if not self.check_sqlite_exists():
            logger.warning(f"SQLite数据库不存在: {self.sqlite_path}")
            return {}
        
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        data = {}
        
        try:
            # 获取会话数据
            cursor.execute("SELECT * FROM sessions")
            sessions = [dict(row) for row in cursor.fetchall()]
            data['sessions'] = sessions
            logger.info(f"✅ 获取会话数据: {len(sessions)}条")
            
            # 获取消息数据
            cursor.execute("SELECT * FROM messages")
            messages = [dict(row) for row in cursor.fetchall()]
            data['messages'] = messages
            logger.info(f"✅ 获取消息数据: {len(messages)}条")
            
            # 获取知识库数据
            try:
                cursor.execute("SELECT * FROM knowledge_chunks")
                chunks = [dict(row) for row in cursor.fetchall()]
                data['knowledge_chunks'] = chunks
                logger.info(f"✅ 获取知识库数据: {len(chunks)}条")
            except sqlite3.OperationalError:
                logger.info("知识库表不存在，跳过")
                data['knowledge_chunks'] = []
            
            # 获取速率限制数据
            try:
                cursor.execute("SELECT * FROM rate_limits")
                rate_limits = [dict(row) for row in cursor.fetchall()]
                data['rate_limits'] = rate_limits
                logger.info(f"✅ 获取速率限制数据: {len(rate_limits)}条")
            except sqlite3.OperationalError:
                logger.info("速率限制表不存在，跳过")
                data['rate_limits'] = []
            
            # 获取系统配置数据
            try:
                cursor.execute("SELECT * FROM system_config")
                configs = [dict(row) for row in cursor.fetchall()]
                data['system_config'] = configs
                logger.info(f"✅ 获取系统配置数据: {len(configs)}条")
            except sqlite3.OperationalError:
                logger.info("系统配置表不存在，跳过")
                data['system_config'] = []
            
        except Exception as e:
            logger.error(f"❌ 获取SQLite数据失败: {e}")
            return {}
        finally:
            conn.close()
        
        return data
    
    def convert_datetime_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """转换datetime字段为ISO格式字符串"""
        converted = data.copy()
        
        datetime_fields = ['created_at', 'last_active_at', 'expires_at', 'received_at', 'responded_at', 'window_start', 'last_request_at', 'updated_at']
        
        for field in datetime_fields:
            if field in converted and converted[field]:
                try:
                    if isinstance(converted[field], str):
                        # 尝试解析为datetime对象
                        dt = datetime.fromisoformat(converted[field].replace('Z', '+00:00'))
                        converted[field] = dt.isoformat()
                    elif isinstance(converted[field], datetime):
                        converted[field] = converted[field].isoformat()
                except (ValueError, TypeError) as e:
                    logger.warning(f"日期字段转换失败: {field}={converted[field]}, {e}")
                    converted[field] = None
        
        return converted
    
    async def migrate_sessions(self, sessions: List[Dict[str, Any]]) -> int:
        """迁移会话数据"""
        migrated_count = 0
        
        for session in sessions:
            try:
                # 转换datetime字段
                session_data = self.convert_datetime_fields(session)
                
                # 移除id字段（让数据库自动生成）
                if 'id' in session_data:
                    del session_data['id']
                
                # 创建会话
                result = await self.db_manager.create_session(session_data)
                if result:
                    migrated_count += 1
                    logger.debug(f"✅ 会话迁移成功: {session_data.get('session_key')}")
                else:
                    logger.warning(f"⚠️ 会话迁移失败: {session_data.get('session_key')}")
                    
            except Exception as e:
                logger.error(f"❌ 会话迁移失败: {session.get('session_key')}, {e}")
        
        logger.info(f"✅ 会话迁移完成: {migrated_count}/{len(sessions)}")
        return migrated_count
    
    async def migrate_messages(self, messages: List[Dict[str, Any]]) -> int:
        """迁移消息数据"""
        migrated_count = 0
        
        for message in messages:
            try:
                # 转换datetime字段
                message_data = self.convert_datetime_fields(message)
                
                # 移除id字段（让数据库自动生成）
                if 'id' in message_data:
                    del message_data['id']
                
                # 创建消息
                result = await self.db_manager.create_message(message_data)
                if result:
                    migrated_count += 1
                    logger.debug(f"✅ 消息迁移成功: {message_data.get('request_id')}")
                else:
                    logger.warning(f"⚠️ 消息迁移失败: {message_data.get('request_id')}")
                    
            except Exception as e:
                logger.error(f"❌ 消息迁移失败: {message.get('request_id')}, {e}")
        
        logger.info(f"✅ 消息迁移完成: {migrated_count}/{len(messages)}")
        return migrated_count
    
    async def migrate_knowledge_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """迁移知识库数据"""
        migrated_count = 0
        
        for chunk in chunks:
            try:
                # 转换datetime字段
                chunk_data = self.convert_datetime_fields(chunk)
                
                # 移除id字段（让数据库自动生成）
                if 'id' in chunk_data:
                    del chunk_data['id']
                
                # 创建知识库块
                result = await self.db_manager.create_message(chunk_data)  # 使用消息表存储
                if result:
                    migrated_count += 1
                    logger.debug(f"✅ 知识库块迁移成功: {chunk_data.get('chunk_id')}")
                else:
                    logger.warning(f"⚠️ 知识库块迁移失败: {chunk_data.get('chunk_id')}")
                    
            except Exception as e:
                logger.error(f"❌ 知识库块迁移失败: {chunk.get('chunk_id')}, {e}")
        
        logger.info(f"✅ 知识库迁移完成: {migrated_count}/{len(chunks)}")
        return migrated_count
    
    async def migrate_rate_limits(self, rate_limits: List[Dict[str, Any]]) -> int:
        """迁移速率限制数据"""
        migrated_count = 0
        
        for rate_limit in rate_limits:
            try:
                # 转换datetime字段
                rate_limit_data = self.convert_datetime_fields(rate_limit)
                
                # 移除id字段（让数据库自动生成）
                if 'id' in rate_limit_data:
                    del rate_limit_data['id']
                
                # 创建速率限制记录
                result = await self.db_manager.create_message(rate_limit_data)  # 使用消息表存储
                if result:
                    migrated_count += 1
                    logger.debug(f"✅ 速率限制迁移成功: {rate_limit_data.get('entity_type')}:{rate_limit_data.get('entity_id')}")
                else:
                    logger.warning(f"⚠️ 速率限制迁移失败: {rate_limit_data.get('entity_type')}:{rate_limit_data.get('entity_id')}")
                    
            except Exception as e:
                logger.error(f"❌ 速率限制迁移失败: {rate_limit.get('entity_type')}:{rate_limit.get('entity_id')}, {e}")
        
        logger.info(f"✅ 速率限制迁移完成: {migrated_count}/{len(rate_limits)}")
        return migrated_count
    
    async def migrate_system_config(self, configs: List[Dict[str, Any]]) -> int:
        """迁移系统配置数据"""
        migrated_count = 0
        
        for config in configs:
            try:
                # 设置环境变量
                key = config.get('key')
                value = config.get('value')
                
                if key and value:
                    os.environ[key] = value
                    migrated_count += 1
                    logger.debug(f"✅ 系统配置迁移成功: {key}={value}")
                else:
                    logger.warning(f"⚠️ 系统配置迁移失败: {config}")
                    
            except Exception as e:
                logger.error(f"❌ 系统配置迁移失败: {config}, {e}")
        
        logger.info(f"✅ 系统配置迁移完成: {migrated_count}/{len(configs)}")
        return migrated_count
    
    async def migrate_all(self) -> Dict[str, int]:
        """迁移所有数据"""
        logger.info("🚀 开始数据迁移...")
        
        # 获取SQLite数据
        sqlite_data = self.get_sqlite_data()
        if not sqlite_data:
            logger.error("❌ 没有数据可迁移")
            return {}
        
        # 迁移结果统计
        results = {}
        
        # 迁移会话
        if 'sessions' in sqlite_data and sqlite_data['sessions']:
            results['sessions'] = await self.migrate_sessions(sqlite_data['sessions'])
        
        # 迁移消息
        if 'messages' in sqlite_data and sqlite_data['messages']:
            results['messages'] = await self.migrate_messages(sqlite_data['messages'])
        
        # 迁移知识库
        if 'knowledge_chunks' in sqlite_data and sqlite_data['knowledge_chunks']:
            results['knowledge_chunks'] = await self.migrate_knowledge_chunks(sqlite_data['knowledge_chunks'])
        
        # 迁移速率限制
        if 'rate_limits' in sqlite_data and sqlite_data['rate_limits']:
            results['rate_limits'] = await self.migrate_rate_limits(sqlite_data['rate_limits'])
        
        # 迁移系统配置
        if 'system_config' in sqlite_data and sqlite_data['system_config']:
            results['system_config'] = await self.migrate_system_config(sqlite_data['system_config'])
        
        logger.info("🎉 数据迁移完成!")
        return results
    
    def backup_sqlite(self, backup_path: str = None) -> str:
        """备份SQLite数据库"""
        if not self.check_sqlite_exists():
            logger.warning("SQLite数据库不存在，无需备份")
            return ""
        
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/data_backup_{timestamp}.db"
        
        import shutil
        shutil.copy2(self.sqlite_path, backup_path)
        logger.info(f"✅ SQLite数据库已备份到: {backup_path}")
        return backup_path
    
    def verify_migration(self) -> Dict[str, Any]:
        """验证迁移结果"""
        logger.info("🔍 验证迁移结果...")
        
        # 获取SQLite数据统计
        sqlite_data = self.get_sqlite_data()
        sqlite_stats = {
            'sessions': len(sqlite_data.get('sessions', [])),
            'messages': len(sqlite_data.get('messages', [])),
            'knowledge_chunks': len(sqlite_data.get('knowledge_chunks', [])),
            'rate_limits': len(sqlite_data.get('rate_limits', [])),
            'system_config': len(sqlite_data.get('system_config', []))
        }
        
        # 获取Supabase数据统计
        import asyncio
        supabase_stats = asyncio.run(self.db_manager.get_stats())
        
        verification_result = {
            'sqlite_stats': sqlite_stats,
            'supabase_stats': supabase_stats,
            'migration_success': True,
            'verification_time': datetime.now().isoformat()
        }
        
        # 检查关键数据是否迁移成功
        if sqlite_stats['sessions'] > 0 and supabase_stats.get('session_count', 0) == 0:
            verification_result['migration_success'] = False
            verification_result['error'] = "会话数据迁移失败"
        
        if sqlite_stats['messages'] > 0 and supabase_stats.get('message_count', 0) == 0:
            verification_result['migration_success'] = False
            verification_result['error'] = "消息数据迁移失败"
        
        logger.info(f"✅ 验证完成: {verification_result}")
        return verification_result


async def main():
    """主函数"""
    print("🚀 SQLite到Supabase数据迁移工具")
    print("=" * 50)
    
    # 检查环境变量
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        print("❌ Supabase配置不完整")
        print("请设置以下环境变量:")
        print("  SUPABASE_URL=https://your-project.supabase.co")
        print("  SUPABASE_ANON_KEY=your_supabase_anon_key")
        return False
    
    # 初始化数据库管理器
    init_database_manager()
    
    # 创建迁移器
    migrator = DataMigrator()
    
    # 检查SQLite数据库
    if not migrator.check_sqlite_exists():
        print("❌ SQLite数据库不存在")
        print(f"请检查路径: {migrator.sqlite_path}")
        return False
    
    print(f"✅ 找到SQLite数据库: {migrator.sqlite_path}")
    
    # 备份SQLite数据库
    backup_path = migrator.backup_sqlite()
    if backup_path:
        print(f"✅ 已备份SQLite数据库: {backup_path}")
    
    # 开始迁移
    print("🔄 开始数据迁移...")
    results = await migrator.migrate_all()
    
    # 显示迁移结果
    print("\n📊 迁移结果:")
    for table, count in results.items():
        print(f"  {table}: {count}条")
    
    # 验证迁移
    print("\n🔍 验证迁移结果...")
    verification = migrator.verify_migration()
    
    if verification['migration_success']:
        print("✅ 数据迁移成功!")
        print(f"  SQLite统计: {verification['sqlite_stats']}")
        print(f"  Supabase统计: {verification['supabase_stats']}")
    else:
        print("❌ 数据迁移失败!")
        print(f"  错误: {verification.get('error', '未知错误')}")
        return False
    
    return True


if __name__ == "__main__":
    import asyncio
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    # 运行迁移
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 数据迁移完成!")
        print("现在可以设置 DATABASE_TYPE=supabase 使用Supabase数据库")
    else:
        print("\n❌ 数据迁移失败!")
        sys.exit(1)
