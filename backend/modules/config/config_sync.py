#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置同步服务
提供配置的实时同步、版本管理和客户端更新功能
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, asdict
import websockets
from fastapi import WebSocket, WebSocketDisconnect
# import redis.asyncio as redis  # 暂时注释掉，使用内存替代

logger = logging.getLogger(__name__)


@dataclass
class ConfigChange:
    """配置变更记录"""
    id: str
    category: str
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_by: str
    change_reason: Optional[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ConfigSyncMessage:
    """配置同步消息"""
    type: str  # 'config_update', 'config_delete', 'config_batch_update'
    category: str
    key: Optional[str]
    value: Optional[str]
    configs: Optional[Dict[str, str]]  # 批量更新时使用
    timestamp: datetime
    version: str
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ConfigSyncManager:
    """配置同步管理器"""
    
    def __init__(self):
        self.connected_clients: Set[WebSocket] = set()
        self.config_version = "1.0.0"
        self.redis_client = None
        self.sync_channel = "config_sync"
        self._init_redis()
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            # 暂时使用内存替代Redis
            self.redis_client = None
            logger.info("✅ Redis连接初始化成功（内存模式）")
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败: {e}")
            self.redis_client = None
    
    async def connect_client(self, websocket: WebSocket):
        """客户端连接"""
        await websocket.accept()
        self.connected_clients.add(websocket)
        logger.info(f"✅ 客户端已连接，当前连接数: {len(self.connected_clients)}")
        
        # 发送当前配置版本
        await websocket.send_text(json.dumps({
            'type': 'version_info',
            'version': self.config_version,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def disconnect_client(self, websocket: WebSocket):
        """客户端断开连接"""
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
        logger.info(f"✅ 客户端已断开，当前连接数: {len(self.connected_clients)}")
    
    async def broadcast_config_update(self, category: str, key: str, value: str):
        """广播配置更新"""
        try:
            message = ConfigSyncMessage(
                type='config_update',
                category=category,
                key=key,
                value=value,
                configs=None,
                timestamp=datetime.now(),
                version=self.config_version
            )
            
            message_data = json.dumps(message.to_dict())
            
            # 广播给所有连接的客户端
            disconnected_clients = set()
            for client in self.connected_clients:
                try:
                    await client.send_text(message_data)
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                    disconnected_clients.add(client)
            
            # 清理断开的连接
            for client in disconnected_clients:
                await self.disconnect_client(client)
            
            # 发布到Redis频道
            if self.redis_client:
                await self.redis_client.publish(self.sync_channel, message_data)
            
            logger.info(f"✅ 配置更新已广播: {category}.{key}")
            
        except Exception as e:
            logger.error(f"广播配置更新失败: {e}")
    
    async def broadcast_config_batch_update(self, configs: Dict[str, Dict[str, str]]):
        """广播批量配置更新"""
        try:
            message = ConfigSyncMessage(
                type='config_batch_update',
                category='all',
                key=None,
                value=None,
                configs=configs,
                timestamp=datetime.now(),
                version=self.config_version
            )
            
            message_data = json.dumps(message.to_dict())
            
            # 广播给所有连接的客户端
            disconnected_clients = set()
            for client in self.connected_clients:
                try:
                    await client.send_text(message_data)
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                    disconnected_clients.add(client)
            
            # 清理断开的连接
            for client in disconnected_clients:
                await self.disconnect_client(client)
            
            # 发布到Redis频道
            if self.redis_client:
                await self.redis_client.publish(self.sync_channel, message_data)
            
            logger.info(f"✅ 批量配置更新已广播: {len(configs)}个分类")
            
        except Exception as e:
            logger.error(f"广播批量配置更新失败: {e}")
    
    async def handle_client_message(self, websocket: WebSocket, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # 心跳检测
                await websocket.send_text(json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
            
            elif message_type == 'request_config':
                # 请求配置
                await self.send_current_config(websocket)
            
            elif message_type == 'config_applied':
                # 客户端确认配置已应用
                logger.info(f"✅ 客户端确认配置已应用: {data.get('client_id')}")
            
            else:
                logger.warning(f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("无效的JSON消息")
        except Exception as e:
            logger.error(f"处理客户端消息失败: {e}")
    
    async def send_current_config(self, websocket: WebSocket):
        """发送当前配置"""
        try:
            # 从数据库获取当前配置
            from modules.config.config_manager import config_manager
            categories = await config_manager.get_categories()
            
            # 构建配置数据
            config_data = {}
            for category in categories:
                config_data[category.name] = {}
                for item in category.items:
                    config_data[category.name][item.key] = item.value
            
            message = ConfigSyncMessage(
                type='config_sync',
                category='all',
                key=None,
                value=None,
                configs=config_data,
                timestamp=datetime.now(),
                version=self.config_version
            )
            
            await websocket.send_text(json.dumps(message.to_dict()))
            logger.info("✅ 当前配置已发送给客户端")
            
        except Exception as e:
            logger.error(f"发送当前配置失败: {e}")
    
    async def start_redis_listener(self):
        """启动Redis监听器"""
        if not self.redis_client:
            return
        
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(self.sync_channel)
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        
                        # 转发给所有连接的客户端
                        disconnected_clients = set()
                        for client in self.connected_clients:
                            try:
                                await client.send_text(message['data'])
                            except Exception as e:
                                logger.error(f"转发消息失败: {e}")
                                disconnected_clients.add(client)
                        
                        # 清理断开的连接
                        for client in disconnected_clients:
                            await self.disconnect_client(client)
                            
                    except Exception as e:
                        logger.error(f"处理Redis消息失败: {e}")
                        
        except Exception as e:
            logger.error(f"Redis监听器启动失败: {e}")


class ConfigVersionManager:
    """配置版本管理器"""
    
    def __init__(self):
        self.version_history = []
        self.current_version = "1.0.0"
    
    def create_version(self, changes: List[ConfigChange], reason: str = None) -> str:
        """创建新版本"""
        try:
            # 生成新版本号
            major, minor, patch = map(int, self.current_version.split('.'))
            patch += 1
            new_version = f"{major}.{minor}.{patch}"
            
            # 创建版本记录
            version_record = {
                'version': new_version,
                'changes': [change.to_dict() for change in changes],
                'reason': reason,
                'created_at': datetime.now().isoformat(),
                'created_by': changes[0].changed_by if changes else 'system'
            }
            
            self.version_history.append(version_record)
            self.current_version = new_version
            
            logger.info(f"✅ 新版本已创建: {new_version}")
            return new_version
            
        except Exception as e:
            logger.error(f"创建版本失败: {e}")
            return self.current_version
    
    def get_version_history(self, limit: int = 10) -> List[Dict]:
        """获取版本历史"""
        return self.version_history[-limit:]
    
    def get_version_diff(self, version1: str, version2: str) -> Dict[str, Any]:
        """获取版本差异"""
        try:
            v1_record = next((v for v in self.version_history if v['version'] == version1), None)
            v2_record = next((v for v in self.version_history if v['version'] == version2), None)
            
            if not v1_record or not v2_record:
                return {'error': '版本不存在'}
            
            # 计算差异
            v1_changes = {f"{c['category']}.{c['key']}": c['new_value'] for c in v1_record['changes']}
            v2_changes = {f"{c['category']}.{c['key']}": c['new_value'] for c in v2_record['changes']}
            
            diff = {
                'added': {k: v for k, v in v2_changes.items() if k not in v1_changes},
                'modified': {k: v for k, v in v2_changes.items() if k in v1_changes and v1_changes[k] != v},
                'removed': {k: v for k, v in v1_changes.items() if k not in v2_changes}
            }
            
            return diff
            
        except Exception as e:
            logger.error(f"获取版本差异失败: {e}")
            return {'error': str(e)}


class ConfigBackupManager:
    """配置备份管理器"""
    
    def __init__(self):
        self.backup_dir = "backups/config"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    async def create_backup(self, config_data: Dict[str, Any], reason: str = None) -> str:
        """创建配置备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"config_backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            backup_data = {
                'version': '1.0.0',
                'timestamp': datetime.now().isoformat(),
                'reason': reason,
                'config': config_data
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 配置备份已创建: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"创建配置备份失败: {e}")
            return None
    
    async def restore_backup(self, backup_path: str) -> bool:
        """恢复配置备份"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            config_data = backup_data['config']
            
            # 恢复配置
            from modules.config.config_manager import config_manager
            for category_name, configs in config_data.items():
                for key, value in configs.items():
                    await config_manager.update_config(category_name, key, value, "backup_restore")
            
            logger.info(f"✅ 配置已从备份恢复: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"恢复配置备份失败: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, str]]:
        """列出所有备份"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, filename)
                    stat = os.stat(filepath)
                    backups.append({
                        'filename': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
            
            return sorted(backups, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"列出备份失败: {e}")
            return []


# 全局实例
config_sync_manager = ConfigSyncManager()
config_version_manager = ConfigVersionManager()
config_backup_manager = ConfigBackupManager()


async def start_config_sync_service():
    """启动配置同步服务"""
    try:
        # 启动Redis监听器
        asyncio.create_task(config_sync_manager.start_redis_listener())
        
        logger.info("✅ 配置同步服务已启动")
        
    except Exception as e:
        logger.error(f"启动配置同步服务失败: {e}")


async def sync_config_to_clients(category: str, key: str, value: str):
    """同步配置到客户端"""
    await config_sync_manager.broadcast_config_update(category, key, value)


async def sync_all_configs_to_clients():
    """同步所有配置到客户端"""
    try:
        from modules.config.config_manager import config_manager
        categories = await config_manager.get_categories()
        
        config_data = {}
        for category in categories:
            config_data[category.name] = {}
            for item in category.items:
                config_data[category.name][item.key] = item.value
        
        await config_sync_manager.broadcast_config_batch_update(config_data)
        
    except Exception as e:
        logger.error(f"同步所有配置失败: {e}")
