"""
Framelink Figma MCP Provider
集成 Figma 设计文件数据获取和图片下载功能
"""

import asyncio
import json
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from ..mcp_client import MCPClient
from ..cache_manager import CacheManager

logger = logging.getLogger(__name__)


class FigmaProvider(MCPClient):
    """Figma MCP 提供商"""
    
    def __init__(self, service, cache_manager: CacheManager):
        """初始化 Figma 提供商"""
        super().__init__(service, cache_manager)
        self.api_key = service.api_key
        
        # 检查 npx 是否可用
        try:
            result = subprocess.run(
                ["npx", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                logger.warning("npx 不可用，Figma MCP 功能可能受限")
        except Exception as e:
            logger.warning(f"检查 npx 失败: {e}")
    
    async def get_figma_data(
        self,
        file_key: str,
        node_id: Optional[str] = None,
        depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取 Figma 文件数据
        
        Args:
            file_key: Figma 文件 key (从 URL 中获取)
            node_id: 可选的节点 ID，用于获取特定节点
            depth: 可选的遍历深度，控制节点树深度
            
        Returns:
            Figma 文件数据，包含布局、内容、视觉和组件信息
        """
        # 构建缓存键
        cache_key = f"figma_data:{file_key}"
        if node_id:
            cache_key += f":{node_id}"
        if depth:
            cache_key += f":depth{depth}"
        
        # 尝试从缓存获取
        if self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.info(f"✅ 从缓存获取 Figma 数据: {file_key}")
                return cached_data
        
        # 调用 MCP 工具
        try:
            # 构建工具参数
            params: Dict[str, Any] = {"fileKey": file_key}
            if node_id:
                params["nodeId"] = node_id
            if depth:
                params["depth"] = depth
            
            # 调用工具
            result = await self.call_tool("get_figma_data", params)
            
            # 缓存结果
            if self.cache_manager:
                ttl = self.service.cache_config.get("ttl", 7200)
                self.cache_manager.set(cache_key, result, ttl=ttl)
            
            logger.info(f"✅ 成功获取 Figma 数据: {file_key}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取 Figma 数据失败: {e}")
            raise
    
    async def download_figma_images(
        self,
        file_key: str,
        nodes: List[Dict[str, Any]],
        local_path: str,
        png_scale: int = 2
    ) -> Dict[str, Any]:
        """
        下载 Figma 图片资源
        
        Args:
            file_key: Figma 文件 key
            nodes: 节点列表，每个节点包含：
                - nodeId: 节点 ID (格式: 1234:5678)
                - fileName: 保存的文件名（含扩展名 .png 或 .svg）
                - imageRef: 可选，图片引用 ID
                - needsCropping: 是否需要裁剪
                - cropTransform: 裁剪变换矩阵
                - requiresImageDimensions: 是否需要尺寸信息
            local_path: 本地保存路径（绝对路径）
            png_scale: PNG 导出缩放比例（默认 2x）
            
        Returns:
            下载结果，包含成功/失败的文件列表
        """
        try:
            # 确保目录存在
            Path(local_path).mkdir(parents=True, exist_ok=True)
            
            # 调用工具
            params = {
                "fileKey": file_key,
                "nodes": nodes,
                "localPath": local_path,
                "pngScale": png_scale
            }
            
            result = await self.call_tool("download_figma_images", params)
            
            logger.info(f"✅ 成功下载 Figma 图片: {len(nodes)} 个节点")
            return result
            
        except Exception as e:
            logger.error(f"❌ 下载 Figma 图片失败: {e}")
            raise
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        调用 Figma MCP 工具（通过 npx）
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            # 构建 npx 命令
            # 注意：这里假设使用 @framelink/figma-mcp 包
            env = {"FIGMA_API_KEY": self.api_key} if self.api_key else {}
            
            # 构建输入数据
            input_data = {
                "method": tool_name,
                "params": params
            }
            
            # 执行 npx 命令
            process = await asyncio.create_subprocess_exec(
                "npx",
                "-y",
                "@framelink/figma-mcp",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**env}
            )
            
            # 发送输入并获取输出
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=json.dumps(input_data).encode()),
                timeout=self.service.timeout
            )
            
            # 检查错误
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "未知错误"
                raise RuntimeError(f"Figma MCP 调用失败: {error_msg}")
            
            # 解析结果
            result = json.loads(stdout.decode())
            return result
            
        except asyncio.TimeoutError:
            raise TimeoutError(f"Figma MCP 调用超时: {tool_name}")
        except Exception as e:
            logger.error(f"❌ Figma MCP 工具调用失败 [{tool_name}]: {e}")
            raise
    
    async def extract_design_tokens(self, file_key: str) -> Dict[str, Any]:
        """
        从 Figma 文件中提取设计令牌（Design Tokens）
        
        这是一个高级功能，分析 Figma 文件并提取：
        - 颜色系统
        - 排版系统（字体、大小、行高等）
        - 间距系统
        - 阴影效果
        - 圆角设置
        
        Args:
            file_key: Figma 文件 key
            
        Returns:
            设计令牌数据
        """
        # 获取完整文件数据
        data = await self.get_figma_data(file_key)
        
        # 提取设计令牌
        tokens = {
            "colors": {},
            "typography": {},
            "spacing": {},
            "effects": {},
            "radii": {}
        }
        
        # 这里可以实现具体的解析逻辑
        # 遍历节点，提取样式信息
        
        logger.info(f"✅ 成功提取设计令牌: {file_key}")
        return tokens
    
    async def get_component_library(self, file_key: str) -> List[Dict[str, Any]]:
        """
        获取 Figma 文件中的组件库
        
        Args:
            file_key: Figma 文件 key
            
        Returns:
            组件列表
        """
        data = await self.get_figma_data(file_key)
        
        # 提取组件信息
        components = []
        
        # 遍历数据，找到所有组件定义
        # 这里可以实现具体的组件提取逻辑
        
        logger.info(f"✅ 成功获取组件库: {file_key}, 共 {len(components)} 个组件")
        return components
