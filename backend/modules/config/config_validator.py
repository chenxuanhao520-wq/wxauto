"""
配置验证器 - 配置验证和测试
支持连接测试、配置验证、服务健康检查
"""

import logging
from typing import Dict, Any, Optional, Tuple
import httpx
import os

logger = logging.getLogger(__name__)


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        """初始化配置验证器"""
        logger.info("✅ 配置验证器初始化完成")
    
    async def test_config(self, config_type: str, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        测试配置
        
        Args:
            config_type: 配置类型
            config_data: 配置数据
            
        Returns:
            (是否成功, 消息, 详细信息)
        """
        try:
            if config_type == "supabase":
                return await self._test_supabase_config(config_data)
            elif config_type == "vector":
                return await self._test_vector_config(config_data)
            elif config_type == "ai":
                return await self._test_ai_config(config_data)
            elif config_type == "wechat":
                return await self._test_wechat_config(config_data)
            else:
                return False, f"不支持的配置类型: {config_type}", None
                
        except Exception as e:
            logger.error(f"❌ 配置测试失败: {e}")
            return False, f"配置测试失败: {e}", None
    
    async def _test_supabase_config(self, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """测试Supabase配置"""
        try:
            url = config_data.get("url", "")
            anon_key = config_data.get("anon_key", "")
            
            if not url or not anon_key:
                return False, "Supabase URL和匿名密钥不能为空", None
            
            # 测试连接
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{url}/rest/v1/",
                    headers={
                        "apikey": anon_key,
                        "Authorization": f"Bearer {anon_key}"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return True, "Supabase连接测试成功", {
                        "url": url,
                        "status_code": response.status_code,
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                else:
                    return False, f"Supabase连接失败: HTTP {response.status_code}", {
                        "url": url,
                        "status_code": response.status_code,
                        "error": response.text
                    }
                    
        except Exception as e:
            logger.error(f"❌ Supabase配置测试失败: {e}")
            return False, f"Supabase连接测试失败: {e}", None
    
    async def _test_vector_config(self, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """测试Supabase pgvector配置"""
        try:
            vector_type = config_data.get("type", "")
            table_name = config_data.get("table_name", "")
            
            if vector_type != "supabase_pgvector":
                return False, "仅支持Supabase pgvector", None
            
            if not table_name:
                return False, "向量表名不能为空", None
            
            # 测试Supabase连接（向量数据库使用相同的Supabase连接）
            try:
                from modules.storage.supabase_client import get_supabase_client
                
                supabase = get_supabase_client()
                if not supabase:
                    return False, "Supabase客户端未初始化", None
                
                # 测试向量表是否存在
                result = supabase.table(table_name).select("id").limit(1).execute()
                
                return True, "Supabase pgvector配置测试成功", {
                    "table_name": table_name,
                    "type": vector_type
                }
                
            except Exception as e:
                return False, f"Supabase pgvector连接测试失败: {e}", None
                
        except Exception as e:
            logger.error(f"❌ 向量数据库配置测试失败: {e}")
            return False, f"向量数据库连接测试失败: {e}", None
    
    async def _test_ai_config(self, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """测试AI配置"""
        try:
            primary_provider = config_data.get("primary_provider", "")
            primary_model = config_data.get("primary_model", "")
            
            if not primary_provider or not primary_model:
                return False, "AI提供商和模型不能为空", None
            
            # 根据提供商测试
            if primary_provider == "qwen":
                return await self._test_qwen_config(config_data)
            elif primary_provider == "glm":
                return await self._test_glm_config(config_data)
            elif primary_provider == "openai":
                return await self._test_openai_config(config_data)
            else:
                return False, f"不支持的AI提供商: {primary_provider}", None
                
        except Exception as e:
            logger.error(f"❌ AI配置测试失败: {e}")
            return False, f"AI配置测试失败: {e}", None
    
    async def _test_qwen_config(self, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """测试Qwen配置"""
        try:
            api_key = os.getenv("QWEN_API_KEY", "")
            
            if not api_key:
                return False, "Qwen API密钥未设置", None
            
            # 测试API调用
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config_data.get("primary_model", "qwen-turbo"),
                        "input": {
                            "messages": [{"role": "user", "content": "测试"}]
                        }
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return True, "Qwen API测试成功", {
                        "provider": "qwen",
                        "model": config_data.get("primary_model"),
                        "status_code": response.status_code
                    }
                else:
                    return False, f"Qwen API测试失败: HTTP {response.status_code}", {
                        "provider": "qwen",
                        "model": config_data.get("primary_model"),
                        "status_code": response.status_code,
                        "error": response.text
                    }
                    
        except Exception as e:
            logger.error(f"❌ Qwen配置测试失败: {e}")
            return False, f"Qwen API测试失败: {e}", None
    
    async def _test_glm_config(self, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """测试GLM配置"""
        try:
            api_key = os.getenv("GLM_API_KEY", "")
            
            if not api_key:
                return False, "GLM API密钥未设置", None
            
            # GLM API测试
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config_data.get("primary_model", "glm-4-flash"),
                        "messages": [{"role": "user", "content": "测试"}],
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return True, "GLM API测试成功", {
                        "provider": "glm",
                        "model": config_data.get("primary_model"),
                        "status_code": response.status_code
                    }
                else:
                    return False, f"GLM API测试失败: HTTP {response.status_code}", {
                        "provider": "glm",
                        "model": config_data.get("primary_model"),
                        "status_code": response.status_code,
                        "error": response.text
                    }
                    
        except Exception as e:
            logger.error(f"❌ GLM配置测试失败: {e}")
            return False, f"GLM API测试失败: {e}", None
    
    async def _test_openai_config(self, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """测试OpenAI配置"""
        try:
            api_key = os.getenv("OPENAI_API_KEY", "")
            
            if not api_key:
                return False, "OpenAI API密钥未设置", None
            
            # OpenAI API测试
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config_data.get("primary_model", "gpt-3.5-turbo"),
                        "messages": [{"role": "user", "content": "测试"}],
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return True, "OpenAI API测试成功", {
                        "provider": "openai",
                        "model": config_data.get("primary_model"),
                        "status_code": response.status_code
                    }
                else:
                    return False, f"OpenAI API测试失败: HTTP {response.status_code}", {
                        "provider": "openai",
                        "model": config_data.get("primary_model"),
                        "status_code": response.status_code,
                        "error": response.text
                    }
                    
        except Exception as e:
            logger.error(f"❌ OpenAI配置测试失败: {e}")
            return False, f"OpenAI API测试失败: {e}", None
    
    async def _test_wechat_config(self, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """测试微信配置"""
        try:
            whitelisted_groups = config_data.get("whitelisted_groups", [])
            check_interval_ms = config_data.get("check_interval_ms", 500)
            
            if not whitelisted_groups:
                return False, "微信白名单群组不能为空", None
            
            return True, "微信配置验证成功", {
                "whitelisted_groups": whitelisted_groups,
                "check_interval_ms": check_interval_ms,
                "groups_count": len(whitelisted_groups)
            }
            
        except Exception as e:
            logger.error(f"❌ 微信配置测试失败: {e}")
            return False, f"微信配置测试失败: {e}", None
    
    async def validate_all_configs(self, configs: Dict[str, Any]) -> Dict[str, Any]:
        """验证所有配置"""
        try:
            results = {}
            
            for config_type, config_data in configs.items():
                success, message, details = await self.test_config(config_type, config_data)
                results[config_type] = {
                    "success": success,
                    "message": message,
                    "details": details
                }
            
            # 计算整体状态
            all_success = all(result["success"] for result in results.values())
            
            return {
                "overall_success": all_success,
                "results": results,
                "total_configs": len(configs),
                "successful_configs": sum(1 for result in results.values() if result["success"])
            }
            
        except Exception as e:
            logger.error(f"❌ 配置验证失败: {e}")
            return {
                "overall_success": False,
                "error": str(e),
                "results": {}
            }