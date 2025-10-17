"""
企业微信适配器（备用方案）
官方API，不会被封号
"""
import os
import logging
from typing import List, Optional, Iterator, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class WeWorkAdapter:
    """
    企业微信适配器
    
    优势：
    - 官方API，完全合规
    - 不会封号
    - 功能稳定
    
    要求：
    - 需要企业认证
    - 需要创建企业微信应用
    - 用户需要在企业微信中
    """
    
    def __init__(
        self,
        corp_id: Optional[str] = None,
        corp_secret: Optional[str] = None,
        agent_id: Optional[int] = None
    ):
        """
        初始化企业微信适配器
        
        Args:
            corp_id: 企业ID
            corp_secret: 应用密钥
            agent_id: 应用ID
        """
        self.corp_id = corp_id or os.getenv("WEWORK_CORP_ID")
        self.corp_secret = corp_secret or os.getenv("WEWORK_CORP_SECRET")
        self.agent_id = agent_id or int(os.getenv("WEWORK_AGENT_ID", "0"))
        
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        
        if not all([self.corp_id, self.corp_secret, self.agent_id]):
            logger.warning("企业微信未完全配置，部分功能不可用")
        else:
            logger.info("企业微信适配器初始化成功")
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return all([self.corp_id, self.corp_secret, self.agent_id])
    
    def _get_access_token(self) -> Optional[str]:
        """
        获取access_token
        有效期2小时，自动缓存
        """
        import time
        
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            import requests
            
            url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                "corpid": self.corp_id,
                "corpsecret": self.corp_secret
            }
            
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                self.access_token = result['access_token']
                # 提前10分钟刷新
                self.token_expires_at = time.time() + 7200 - 600
                logger.info("企业微信 access_token 获取成功")
                return self.access_token
            else:
                logger.error(f"企业微信 access_token 获取失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"获取企业微信 access_token 异常: {e}")
            return None
    
    def send_message(
        self,
        user_id: str,
        content: str,
        msg_type: str = "text"
    ) -> bool:
        """
        发送消息
        
        Args:
            user_id: 用户ID
            content: 消息内容
            msg_type: 消息类型（text/markdown等）
        
        Returns:
            bool: 是否成功
        """
        if not self.is_configured():
            logger.warning("企业微信未配置，无法发送消息")
            return False
        
        access_token = self._get_access_token()
        if not access_token:
            return False
        
        try:
            import requests
            
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send"
            params = {"access_token": access_token}
            
            payload = {
                "touser": user_id,
                "msgtype": msg_type,
                "agentid": self.agent_id,
                msg_type: {
                    "content": content
                }
            }
            
            response = requests.post(url, params=params, json=payload, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"企业微信消息发送成功: user={user_id}")
                return True
            else:
                logger.error(f"企业微信消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"企业微信消息发送异常: {e}")
            return False
    
    def send_group_message(
        self,
        chat_id: str,
        content: str
    ) -> bool:
        """
        发送群聊消息
        
        Args:
            chat_id: 群聊ID
            content: 消息内容
        
        Returns:
            bool: 是否成功
        """
        if not self.is_configured():
            return False
        
        access_token = self._get_access_token()
        if not access_token:
            return False
        
        try:
            import requests
            
            url = f"https://qyapi.weixin.qq.com/cgi-bin/appchat/send"
            params = {"access_token": access_token}
            
            payload = {
                "chatid": chat_id,
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            response = requests.post(url, params=params, json=payload, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"企业微信群消息发送成功: chat={chat_id}")
                return True
            else:
                logger.error(f"企业微信群消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"企业微信群消息发送异常: {e}")
            return False

