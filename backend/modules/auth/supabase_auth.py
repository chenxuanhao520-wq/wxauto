"""
Supabase认证中间件 - 统一认证和授权
支持JWT验证、多租户权限、角色管理
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client

logger = logging.getLogger(__name__)

# JWT Bearer认证
security = HTTPBearer()


class SupabaseAuth:
    """
    Supabase认证中间件
    
    特性：
    1. JWT令牌验证
    2. 多租户权限控制
    3. 角色管理
    4. 会话管理
    5. 权限缓存
    """
    
    def __init__(self, supabase_client):
        """
        初始化认证中间件
        
        Args:
            supabase_client: Supabase客户端（可以是Client实例或SupabaseClient包装器）
        """
        # 处理不同类型的客户端
        if hasattr(supabase_client, 'client'):
            # 如果是SupabaseClient包装器，获取内部的Client
            self.supabase = supabase_client.client
        else:
            # 如果是原生Client，直接使用
            self.supabase = supabase_client
            
        self.jwt_secret = None  # 从Supabase获取JWT密钥
        
        logger.info("✅ Supabase认证中间件初始化完成")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """验证JWT令牌"""
        try:
            # 从Supabase获取JWT密钥
            if not self.jwt_secret:
                self.jwt_secret = await self._get_jwt_secret()
            
            # 解码JWT令牌
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=["HS256"],
                options={"verify_exp": True}
            )
            
            # 验证用户状态
            user_id = payload.get('sub')
            if not user_id:
                raise HTTPException(status_code=401, detail="无效的令牌")
            
            # 获取用户信息
            user_info = await self._get_user_info(user_id)
            if not user_info:
                raise HTTPException(status_code=401, detail="用户不存在")
            
            # 检查用户状态
            if user_info.get('status') != 'active':
                raise HTTPException(status_code=403, detail="用户已被禁用")
            
            return {
                'user_id': user_id,
                'tenant_id': user_info.get('tenant_id'),
                'role': user_info.get('role'),
                'permissions': user_info.get('permissions', []),
                'exp': payload.get('exp'),
                'iat': payload.get('iat')
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="令牌已过期")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="无效的令牌")
        except Exception as e:
            logger.error(f"❌ 令牌验证失败: {e}")
            raise HTTPException(status_code=401, detail="认证失败")
    
    async def _get_jwt_secret(self) -> str:
        """获取JWT密钥"""
        try:
            # 从Supabase项目设置获取JWT密钥
            # 这里需要根据实际情况调整
            return "your-jwt-secret"  # 实际使用时从环境变量或Supabase获取
        except Exception as e:
            logger.error(f"❌ 获取JWT密钥失败: {e}")
            raise
    
    async def _get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            result = self.supabase.table('users')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ 获取用户信息失败: {e}")
            return None
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """获取当前用户（FastAPI依赖）"""
        token = credentials.credentials
        return await self.verify_token(token)
    
    async def require_tenant(self, user_info: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """要求租户权限"""
        if not user_info.get('tenant_id'):
            raise HTTPException(status_code=403, detail="需要租户权限")
        return user_info
    
    async def require_role(self, required_roles: List[str], 
                          user_info: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """要求特定角色"""
        user_role = user_info.get('role')
        if user_role not in required_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"需要角色权限: {required_roles}, 当前角色: {user_role}"
            )
        return user_info
    
    async def require_permission(self, required_permission: str,
                               user_info: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """要求特定权限"""
        user_permissions = user_info.get('permissions', [])
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"需要权限: {required_permission}"
            )
        return user_info
    
    # ==================== 权限管理 ====================
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        try:
            result = self.supabase.table('users').insert(user_data).execute()
            logger.info(f"✅ 用户创建成功: {user_data.get('user_id')}")
            return result.data[0]
        except Exception as e:
            logger.error(f"❌ 用户创建失败: {e}")
            raise
    
    async def update_user_role(self, user_id: str, tenant_id: str, new_role: str) -> bool:
        """更新用户角色"""
        try:
            result = self.supabase.table('users')\
                .update({'role': new_role})\
                .eq('user_id', user_id)\
                .eq('tenant_id', tenant_id)\
                .execute()
            
            logger.info(f"✅ 用户角色更新成功: {user_id} -> {new_role}")
            return True
        except Exception as e:
            logger.error(f"❌ 用户角色更新失败: {e}")
            return False
    
    async def grant_permission(self, user_id: str, tenant_id: str, permission: str) -> bool:
        """授予权限"""
        try:
            # 获取用户当前权限
            user_info = await self._get_user_info(user_id)
            if not user_info:
                return False
            
            current_permissions = user_info.get('permissions', [])
            if permission not in current_permissions:
                current_permissions.append(permission)
                
                result = self.supabase.table('users')\
                    .update({'permissions': current_permissions})\
                    .eq('user_id', user_id)\
                    .eq('tenant_id', tenant_id)\
                    .execute()
                
                logger.info(f"✅ 权限授予成功: {user_id} -> {permission}")
                return True
            
            return True
        except Exception as e:
            logger.error(f"❌ 权限授予失败: {e}")
            return False
    
    async def revoke_permission(self, user_id: str, tenant_id: str, permission: str) -> bool:
        """撤销权限"""
        try:
            # 获取用户当前权限
            user_info = await self._get_user_info(user_id)
            if not user_info:
                return False
            
            current_permissions = user_info.get('permissions', [])
            if permission in current_permissions:
                current_permissions.remove(permission)
                
                result = self.supabase.table('users')\
                    .update({'permissions': current_permissions})\
                    .eq('user_id', user_id)\
                    .eq('tenant_id', tenant_id)\
                    .execute()
                
                logger.info(f"✅ 权限撤销成功: {user_id} -> {permission}")
                return True
            
            return True
        except Exception as e:
            logger.error(f"❌ 权限撤销失败: {e}")
            return False
    
    # ==================== 会话管理 ====================
    
    async def create_session(self, user_id: str, tenant_id: str, 
                           session_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户会话"""
        try:
            session_data.update({
                'user_id': user_id,
                'tenant_id': tenant_id,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
            })
            
            result = self.supabase.table('user_sessions').insert(session_data).execute()
            logger.info(f"✅ 用户会话创建成功: {user_id}")
            return result.data[0]
        except Exception as e:
            logger.error(f"❌ 用户会话创建失败: {e}")
            raise
    
    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """验证会话"""
        try:
            result = self.supabase.table('user_sessions')\
                .select('*')\
                .eq('session_id', session_id)\
                .eq('status', 'active')\
                .execute()
            
            if not result.data:
                return None
            
            session = result.data[0]
            
            # 检查会话是否过期
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.now() > expires_at:
                # 标记会话为过期
                await self.expire_session(session_id)
                return None
            
            return session
        except Exception as e:
            logger.error(f"❌ 会话验证失败: {e}")
            return None
    
    async def expire_session(self, session_id: str) -> bool:
        """使会话过期"""
        try:
            result = self.supabase.table('user_sessions')\
                .update({'status': 'expired'})\
                .eq('session_id', session_id)\
                .execute()
            
            logger.info(f"✅ 会话过期成功: {session_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 会话过期失败: {e}")
            return False
    
    # ==================== 权限检查装饰器 ====================
    
    def require_tenant_access(self, tenant_id: str):
        """要求租户访问权限的装饰器"""
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # 从参数中获取用户信息
                user_info = kwargs.get('current_user')
                if not user_info:
                    raise HTTPException(status_code=401, detail="需要认证")
                
                if user_info.get('tenant_id') != tenant_id:
                    raise HTTPException(status_code=403, detail="无权限访问该租户")
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_admin_role(self):
        """要求管理员角色的装饰器"""
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                user_info = kwargs.get('current_user')
                if not user_info:
                    raise HTTPException(status_code=401, detail="需要认证")
                
                if user_info.get('role') != 'admin':
                    raise HTTPException(status_code=403, detail="需要管理员权限")
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator


# 全局认证实例
_auth_instance: Optional[SupabaseAuth] = None


def get_auth() -> SupabaseAuth:
    """获取全局认证实例"""
    global _auth_instance
    if _auth_instance is None:
        raise RuntimeError("认证中间件未初始化")
    return _auth_instance


def init_auth(supabase_client: Client):
    """初始化全局认证中间件"""
    global _auth_instance
    _auth_instance = SupabaseAuth(supabase_client)
    logger.info("✅ 全局认证中间件初始化完成")

