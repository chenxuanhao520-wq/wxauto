"""
统一嵌入服务 - 支持多个第三方API提供商
支持降级、缓存、批量处理、成本监控
"""

import logging
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import asyncio
import time
import os
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class EmbeddingService(ABC):
    """嵌入服务抽象基类"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """获取向量维度"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI嵌入服务"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.dimension = 1536 if "3-small" in model else 3072 if "3-large" in model else 1536
        
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI库未安装: pip install openai")
    
    async def embed_text(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI嵌入失败: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI批量嵌入失败: {e}")
            raise
    
    def get_dimension(self) -> int:
        return self.dimension
    
    def get_provider_name(self) -> str:
        return f"OpenAI-{self.model}"


class ZhipuAIEmbeddingService(EmbeddingService):
    """智谱AI嵌入服务 - 中文效果最佳"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.dimension = 1024
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
        
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests库未安装: pip install requests")
    
    async def embed_text(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "embedding-2",
                "input": text
            }
            
            response = self.requests.post(self.base_url, headers=headers, json=data)
            result = response.json()
            
            if "data" in result and result["data"]:
                return result["data"][0]["embedding"]
            else:
                raise Exception(f"智谱AI API错误: {result}")
                
        except Exception as e:
            logger.error(f"智谱AI嵌入失败: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "embedding-2",
                "input": texts
            }
            
            response = self.requests.post(self.base_url, headers=headers, json=data)
            result = response.json()
            
            if "data" in result and result["data"]:
                return [item["embedding"] for item in result["data"]]
            else:
                raise Exception(f"智谱AI API错误: {result}")
                
        except Exception as e:
            logger.error(f"智谱AI批量嵌入失败: {e}")
            raise
    
    def get_dimension(self) -> int:
        return self.dimension
    
    def get_provider_name(self) -> str:
        return "ZhipuAI-embedding-2"


class DeepSeekEmbeddingService(EmbeddingService):
    """DeepSeek嵌入服务 - 中英兼顾"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.dimension = 1536
        
        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
        except ImportError:
            raise ImportError("OpenAI库未安装: pip install openai")
    
    async def embed_text(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        try:
            response = await self.client.embeddings.create(
                model="deepseek-embedding-v1",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"DeepSeek嵌入失败: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        try:
            response = await self.client.embeddings.create(
                model="deepseek-embedding-v1",
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"DeepSeek批量嵌入失败: {e}")
            raise
    
    def get_dimension(self) -> int:
        return self.dimension
    
    def get_provider_name(self) -> str:
        return "DeepSeek-embedding-v1"


class QwenEmbeddingService(EmbeddingService):
    """通义千问嵌入服务 - 技术文档处理更准"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.dimension = 1024
        
        try:
            import dashscope
            self.dashscope = dashscope
        except ImportError:
            raise ImportError("DashScope库未安装: pip install dashscope")
    
    async def embed_text(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        try:
            response = self.dashscope.TextEmbedding.call(
                model="text-embedding-v2",
                input=text
            )
            
            if response.status_code == 200:
                return response.output["embeddings"][0]["embedding"]
            else:
                raise Exception(f"通义千问API错误: {response.message}")
                
        except Exception as e:
            logger.error(f"通义千问嵌入失败: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        try:
            response = self.dashscope.TextEmbedding.call(
                model="text-embedding-v2",
                input=texts
            )
            
            if response.status_code == 200:
                return [item["embedding"] for item in response.output["embeddings"]]
            else:
                raise Exception(f"通义千问API错误: {response.message}")
                
        except Exception as e:
            logger.error(f"通义千问批量嵌入失败: {e}")
            raise
    
    def get_dimension(self) -> int:
        return self.dimension
    
    def get_provider_name(self) -> str:
        return "Qwen-text-embedding-v2"


class SmartEmbeddingService:
    """
    智能嵌入服务 - 自动语言检测和提供商切换
    
    特性：
    1. 自动检测文本语言
    2. 根据语言选择最佳提供商
    3. 多提供商降级机制
    4. 缓存和成本监控
    5. 充电桩行业优化
    """
    
    def __init__(self, 
                 providers: Dict[str, EmbeddingService],
                 language_rules: Dict[str, str] = None,
                 enable_cache: bool = True,
                 cache_ttl: int = 3600):
        """
        初始化智能嵌入服务
        
        Args:
            providers: 提供商字典 {"zhipuai": service, "qwen": service, ...}
            language_rules: 语言规则 {"chinese": "zhipuai", "english": "deepseek", ...}
            enable_cache: 是否启用缓存
            cache_ttl: 缓存TTL（秒）
        """
        self.providers = providers
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        
        # 默认语言规则（基于您的分析）
        self.language_rules = language_rules or {
            "chinese": "zhipuai",      # 中文优先智谱AI
            "english": "deepseek",     # 英文优先DeepSeek
            "mixed": "zhipuai",        # 混合语言优先智谱AI
            "default": "zhipuai"       # 默认智谱AI
        }
        
        # 缓存
        self.text_cache: Dict[str, Dict[str, Any]] = {}
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "language_detections": {},
            "provider_usage": {},
            "total_tokens": 0,
            "total_cost": 0.0,
            "errors": 0
        }
        
        logger.info(f"✅ 智能嵌入服务初始化: {len(providers)}个提供商")
    
    def _detect_language(self, text: str) -> str:
        """
        检测文本语言
        
        Args:
            text: 输入文本
        
        Returns:
            语言类型: "chinese", "english", "mixed"
        """
        # 简单的语言检测（基于字符统计）
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return "default"
        
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars
        
        if chinese_ratio > 0.7:
            return "chinese"
        elif english_ratio > 0.7:
            return "english"
        else:
            return "mixed"
    
    def _get_best_provider(self, language: str) -> Optional[EmbeddingService]:
        """
        根据语言获取最佳提供商
        
        Args:
            language: 语言类型
        
        Returns:
            最佳提供商实例
        """
        # 获取推荐提供商
        recommended = self.language_rules.get(language, self.language_rules["default"])
        
        # 检查提供商是否可用
        if recommended in self.providers:
            return self.providers[recommended]
        
        # 降级到其他可用提供商
        for provider_name in ["zhipuai", "qwen", "deepseek", "openai"]:
            if provider_name in self.providers:
                logger.warning(f"提供商 {recommended} 不可用，降级到 {provider_name}")
                return self.providers[provider_name]
        
        return None
    
    async def embed_text(self, text: str, force_provider: str = None) -> List[float]:
        """
        生成单个文本的嵌入向量
        
        Args:
            text: 输入文本
            force_provider: 强制使用指定提供商
        
        Returns:
            嵌入向量
        """
        # 检查缓存
        if self.enable_cache and text in self.text_cache:
            cache_data = self.text_cache[text]
            if time.time() - cache_data["timestamp"] < self.cache_ttl:
                self.stats["cache_hits"] += 1
                logger.debug(f"缓存命中: {text[:30]}...")
                return cache_data["embedding"]
        
        # 选择提供商
        if force_provider and force_provider in self.providers:
            provider = self.providers[force_provider]
            provider_name = force_provider
        else:
            language = self._detect_language(text)
            provider = self._get_best_provider(language)
            provider_name = provider.get_provider_name() if provider else "unknown"
            
            # 统计语言检测
            self.stats["language_detections"][language] = self.stats["language_detections"].get(language, 0) + 1
        
        if not provider:
            raise Exception("没有可用的嵌入提供商")
        
        # 生成嵌入
        try:
            embedding = await provider.embed_text(text)
            
            # 缓存结果
            if self.enable_cache:
                self.text_cache[text] = {
                    "embedding": embedding,
                    "timestamp": time.time(),
                    "provider": provider_name,
                    "language": language if not force_provider else "forced"
                }
            
            # 统计
            self.stats["total_requests"] += 1
            self.stats["provider_usage"][provider_name] = self.stats["provider_usage"].get(provider_name, 0) + 1
            self._estimate_cost(provider, text)
            
            logger.debug(f"嵌入成功: {provider_name}, 语言: {language if not force_provider else 'forced'}")
            
            return embedding
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"嵌入失败: {provider_name}, 错误: {e}")
            raise
    
    async def embed_batch(self, texts: List[str], force_provider: str = None) -> List[List[float]]:
        """
        批量生成嵌入向量
        
        Args:
            texts: 文本列表
            force_provider: 强制使用指定提供商
        
        Returns:
            嵌入向量列表
        """
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # 检查缓存
        for i, text in enumerate(texts):
            if self.enable_cache and text in self.text_cache:
                cache_data = self.text_cache[text]
                if time.time() - cache_data["timestamp"] < self.cache_ttl:
                    embeddings.append(cache_data["embedding"])
                    self.stats["cache_hits"] += 1
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
                    embeddings.append(None)
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                embeddings.append(None)
        
        # 批量生成未缓存的
        if uncached_texts:
            # 选择提供商
            if force_provider and force_provider in self.providers:
                provider = self.providers[force_provider]
                provider_name = force_provider
            else:
                # 检测主要语言
                languages = [self._detect_language(text) for text in uncached_texts]
                main_language = max(set(languages), key=languages.count)
                provider = self._get_best_provider(main_language)
                provider_name = provider.get_provider_name() if provider else "unknown"
                
                # 统计语言检测
                for lang in languages:
                    self.stats["language_detections"][lang] = self.stats["language_detections"].get(lang, 0) + 1
            
            if not provider:
                raise Exception("没有可用的嵌入提供商")
            
            try:
                batch_embeddings = await provider.embed_batch(uncached_texts)
                
                for i, idx in enumerate(uncached_indices):
                    embeddings[idx] = batch_embeddings[i]
                    
                    # 缓存结果
                    if self.enable_cache:
                        self.text_cache[uncached_texts[i]] = {
                            "embedding": batch_embeddings[i],
                            "timestamp": time.time(),
                            "provider": provider_name,
                            "language": languages[i] if not force_provider else "forced"
                        }
                
                # 统计
                self.stats["total_requests"] += len(texts)
                self.stats["provider_usage"][provider_name] = self.stats["provider_usage"].get(provider_name, 0) + len(uncached_texts)
                self._estimate_cost(provider, "", sum(len(text) for text in uncached_texts))
                
                logger.debug(f"批量嵌入成功: {provider_name}, 数量: {len(uncached_texts)}")
                
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"批量嵌入失败: {provider_name}, 错误: {e}")
                raise
        
        return embeddings
    
    def _estimate_cost(self, provider: EmbeddingService, text: str = "", tokens: int = 0):
        """估算API调用成本"""
        if tokens == 0:
            tokens = len(text)
        
        self.stats["total_tokens"] += tokens
        
        # 成本估算（基于您的分析）
        provider_name = provider.get_provider_name()
        if "ZhipuAI" in provider_name:
            cost = tokens * 0.001 / 1000  # ¥0.001/1K tokens
        elif "Qwen" in provider_name:
            cost = tokens * 0.0015 / 1000  # ¥0.0015/1K tokens
        elif "DeepSeek" in provider_name:
            cost = tokens * 0.002 / 1000  # ¥0.002/1K tokens
        elif "OpenAI" in provider_name:
            cost = tokens * 0.02 / 1000000  # $0.02/1M tokens
        else:
            cost = 0.0
        
        self.stats["total_cost"] += cost
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        # 返回主要提供商的维度
        if "zhipuai" in self.providers:
            return self.providers["zhipuai"].get_dimension()
        elif "qwen" in self.providers:
            return self.providers["qwen"].get_dimension()
        else:
            return 1024  # 默认维度
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats.update({
            "cache_hit_rate": stats["cache_hits"] / max(stats["total_requests"], 1),
            "error_rate": stats["errors"] / max(stats["total_requests"], 1),
            "cached_texts": len(self.text_cache),
            "available_providers": list(self.providers.keys()),
            "language_rules": self.language_rules
        })
        return stats
    
    def clear_cache(self):
        """清除缓存"""
        self.text_cache.clear()
        logger.info("智能嵌入缓存已清除")


# 全局嵌入服务实例
_embedding_service: Optional[SmartEmbeddingService] = None


def get_embedding_service() -> SmartEmbeddingService:
    """获取全局嵌入服务实例"""
    global _embedding_service
    if _embedding_service is None:
        raise RuntimeError("嵌入服务未初始化")
    return _embedding_service


def init_embedding_service(providers: Dict[str, EmbeddingService] = None,
                         language_rules: Dict[str, str] = None):
    """初始化全局智能嵌入服务"""
    global _embedding_service
    
    if providers is None:
        # 默认提供商配置
        providers = {}
        
        # 智谱AI（主要）
        if os.getenv("ZHIPUAI_API_KEY"):
            providers["zhipuai"] = ZhipuAIEmbeddingService(os.getenv("ZHIPUAI_API_KEY"))
        
        # 通义千问（备用）
        if os.getenv("QWEN_API_KEY"):
            providers["qwen"] = QwenEmbeddingService(os.getenv("QWEN_API_KEY"))
        
        # DeepSeek（中英混合）
        if os.getenv("DEEPSEEK_API_KEY"):
            providers["deepseek"] = DeepSeekEmbeddingService(os.getenv("DEEPSEEK_API_KEY"))
        
        # OpenAI（海外）
        if os.getenv("OPENAI_API_KEY"):
            providers["openai"] = OpenAIEmbeddingService(os.getenv("OPENAI_API_KEY"))
    
def init_embedding_service():
    """初始化全局嵌入服务"""
    global _embedding_service
    if _embedding_service is not None:
        return _embedding_service
    
    # 创建提供商字典
    providers = {}
    
    # 智谱AI（中文优化）
    if os.getenv("GLM_API_KEY"):
        providers["glm"] = GLMEmbeddingService(os.getenv("GLM_API_KEY"))
    
    # 通义千问（备用）
    if os.getenv("QWEN_API_KEY"):
        providers["qwen"] = QwenEmbeddingService(os.getenv("QWEN_API_KEY"))
    
    # DeepSeek（中英混合）
    if os.getenv("DEEPSEEK_API_KEY"):
        providers["deepseek"] = DeepSeekEmbeddingService(os.getenv("DEEPSEEK_API_KEY"))
    
    # OpenAI（海外）
    if os.getenv("OPENAI_API_KEY"):
        providers["openai"] = OpenAIEmbeddingService(os.getenv("OPENAI_API_KEY"))
    
    _embedding_service = SmartEmbeddingService(
        providers=providers,
        language_rules=language_rules
    )
    logger.info("✅ 全局智能嵌入服务初始化完成")
    return _embedding_service
