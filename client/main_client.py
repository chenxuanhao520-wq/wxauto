#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信客服中台 - 轻量级客户端主程序
只负责UI自动化和与服务器通信
"""

import asyncio
import logging
import sys
import yaml
from pathlib import Path
from typing import Dict

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ✅ 修复：在导入阶段确保日志目录存在
Path("logs").mkdir(exist_ok=True)

from client.agent.wx_automation import WxAutomation
from client.api.server_client import ServerClient
from client.cache.local_cache import LocalCache
from client.monitor.heartbeat import HeartbeatMonitor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/client.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


class LightweightAgent:
    """轻量级客户端主类"""
    
    def __init__(self, config_file: str = "client/config/client_config.yaml"):
        """
        初始化客户端
        
        Args:
            config_file: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_file)
        
        # 初始化组件
        # ✅ 修复：传递白名单群聊列表（从配置读取或使用测试模式）
        whitelisted_groups = self.config.get('wechat', {}).get('whitelisted_groups', None)
        self.wx_automation = WxAutomation(whitelisted_groups=whitelisted_groups)
        self.server_client = ServerClient(
            base_url=self.config['server']['url'],
            agent_id=self.config['client']['agent_id'],
            api_key=self.config['client']['api_key']
        )
        self.local_cache = LocalCache(
            cache_dir=self.config['cache']['directory']
        )
        self.heartbeat = HeartbeatMonitor(
            server_client=self.server_client,
            interval=self.config['heartbeat']['interval']
        )
        
        # 运行状态
        self.is_running = False
        self.last_message_ids = set()  # 用于去重
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ 配置加载成功: {config_file}")
            return config
        except Exception as e:
            logger.error(f"❌ 配置加载失败: {e}")
            sys.exit(1)
    
    async def start(self):
        """启动客户端"""
        logger.info("="*60)
        logger.info("🚀 微信客服中台 - 轻量级客户端")
        logger.info(f"   客户端ID: {self.config['client']['agent_id']}")
        logger.info(f"   服务器: {self.config['server']['url']}")
        logger.info("="*60)
        
        # 1. 健康检查
        logger.info("[1/5] 服务器健康检查...")
        if not await self.server_client.health_check():
            logger.error("❌ 服务器不可用，请检查服务器是否启动")
            return
        logger.info("✅ 服务器健康")
        
        # 2. 认证
        logger.info("[2/5] 客户端认证...")
        token = await self.server_client.authenticate()
        if not token:
            logger.error("❌ 认证失败")
            return
        logger.info("✅ 认证成功")
        
        # 3. 启动心跳
        if self.config['heartbeat']['enabled']:
            logger.info("[3/5] 启动心跳监控...")
            self.heartbeat.set_status_callback(self._get_wx_status)
            await self.heartbeat.start()
        else:
            logger.info("[3/5] 心跳监控已禁用")
        
        # 4. 检查微信状态
        logger.info("[4/5] 检查微信状态...")
        wx_status = self.wx_automation.get_status()
        if not wx_status.get('online'):
            logger.warning("⚠️  微信未在线")
        else:
            logger.info("✅ 微信在线")
        
        # 5. 启动主循环
        logger.info("[5/5] 启动消息监听...")
        self.is_running = True
        
        try:
            await self._main_loop()
        except KeyboardInterrupt:
            logger.info("\n收到停止信号")
        finally:
            await self.stop()
    
    async def _main_loop(self):
        """主循环 - 监听和处理消息"""
        check_interval = self.config['wechat']['check_interval']
        
        logger.info("✅ 客户端运行中...")
        logger.info("   按 Ctrl+C 停止")
        logger.info("")
        
        while self.is_running:
            try:
                # 1. 获取微信新消息
                messages = self.wx_automation.get_new_messages()
                
                # 2. 处理每条新消息
                for msg in messages:
                    # 去重
                    if msg['id'] in self.last_message_ids:
                        continue
                    
                    self.last_message_ids.add(msg['id'])
                    logger.info(f"📨 收到消息: {msg['sender']}: {msg['content'][:30]}...")
                    
                    # 3. 保存到本地缓存
                    if self.config['cache']['enabled']:
                        self.local_cache.save_message(msg)
                    
                    # 4. 上报服务器并获取回复
                    result = await self.server_client.report_message(msg)
                    
                    if result:
                        # 5. 根据服务器指令执行操作
                        await self._handle_server_response(msg, result)
                    else:
                        # 服务器不可达，加入离线队列
                        if self.config['offline_queue']['enabled']:
                            self.local_cache.add_to_offline_queue(msg)
                            logger.warning("⚠️  服务器不可达，消息已加入离线队列")
                
                # 6. 处理离线队列
                await self._process_offline_queue()
                
                # 保持最近消息ID集合大小
                if len(self.last_message_ids) > 1000:
                    self.last_message_ids = set(list(self.last_message_ids)[-500:])
                
            except Exception as e:
                logger.error(f"主循环异常: {e}", exc_info=True)
                await self.server_client.report_error({
                    'type': 'main_loop_error',
                    'message': str(e)
                })
            
            # 等待下一次检查
            await asyncio.sleep(check_interval)
    
    async def _handle_server_response(self, message: Dict, response: Dict):
        """
        处理服务器响应
        
        Args:
            message: 原始消息
            response: 服务器响应
        """
        action = response.get('action', '')
        
        if action == 'reply':
            # 发送回复
            content = response.get('content', '')
            if content:
                success = self.wx_automation.send_message(message['chat_id'], content)
                if success:
                    logger.info(f"💬 已回复: {content[:30]}...")
                else:
                    logger.error("❌ 发送失败")
        
        elif action == 'ignore':
            # 忽略
            logger.debug("忽略此消息")
        
        elif action == 'transfer_human':
            # 转人工（客户端只记录，实际转接由服务器处理）
            logger.info("🔄 已标记为转人工")
        
        else:
            logger.warning(f"未知操作: {action}")
    
    async def _process_offline_queue(self):
        """处理离线消息队列"""
        if not self.config['offline_queue']['enabled']:
            return
        
        queue = self.local_cache.get_offline_queue()
        
        if not queue:
            return
        
        logger.info(f"处理离线队列: {len(queue)}条消息")
        
        processed = []
        for item in queue:
            msg = item['message']
            
            try:
                result = await self.server_client.report_message(msg)
                
                if result:
                    processed.append(item)
                    logger.info(f"✅ 离线消息已同步: {msg['id'][:10]}...")
                else:
                    # 增加重试次数
                    item['retry_count'] += 1
                    
                    if item['retry_count'] >= self.config['offline_queue']['retry_times']:
                        processed.append(item)
                        logger.warning(f"⚠️  消息重试次数超限，放弃: {msg['id'][:10]}...")
            
            except Exception as e:
                logger.error(f"处理离线消息失败: {e}")
        
        # 更新队列（移除已处理的）
        if processed:
            remaining = [item for item in queue if item not in processed]
            
            # ✅ 修复：保存更新后的队列
            if remaining:
                # 原子更新队列文件
                import json
                temp_file = self.local_cache.offline_queue_file.with_suffix('.tmp')
                json_data = json.dumps(remaining, ensure_ascii=False)
                encrypted = self.local_cache.cipher.encrypt(json_data.encode())
                temp_file.write_bytes(encrypted)
                temp_file.replace(self.local_cache.offline_queue_file)
                logger.info(f"✅ 离线队列已更新: 剩余 {len(remaining)} 条消息")
            else:
                self.local_cache.clear_offline_queue()
                logger.info("✅ 离线队列已清空")
    
    def _get_wx_status(self) -> Dict:
        """获取微信状态（用于心跳）"""
        status = self.wx_automation.get_status()
        return {
            'wx_online': status.get('online', False),
            'messages_processed': len(self.last_message_ids)
        }
    
    async def stop(self):
        """停止客户端"""
        logger.info("正在停止客户端...")
        
        self.is_running = False
        
        # 停止心跳
        if self.heartbeat:
            await self.heartbeat.stop()
        
        # 关闭服务器连接
        if self.server_client:
            await self.server_client.close()
        
        logger.info("✅ 客户端已停止")


async def main():
    """主入口"""
    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)
    
    # 创建客户端
    agent = LightweightAgent()
    
    # 启动
    await agent.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n程序已退出")

