"""
AIOCR MCP 客户端
基于阿里云百炼 AIOCR 服务
"""

import json
import base64
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import httpx

from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class AIOCRClient(MCPClient):
    """AIOCR MCP 客户端"""
    
    def __init__(self, service):
        super().__init__(service)
        self.supported_formats = service.metadata.get("supported_formats", [])
        self.tools = service.metadata.get("tools", [])
    
    async def doc_recognition(self, file_path: Union[str, Path], filename: Optional[str] = None) -> Dict[str, Any]:
        """
        文档识别 - 将文档转换为文本
        
        Args:
            file_path: 文件路径
            filename: 文件名（可选）
            
        Returns:
            识别结果字典
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            filename = filename or file_path.name
            
            # 检查文件格式
            file_ext = file_path.suffix.lower().lstrip('.')
            if file_ext not in self.supported_formats:
                logger.warning(f"文件格式可能不支持: {file_ext}")
            
            # 读取文件并编码
            file_bytes = file_path.read_bytes()
            file_base64 = base64.b64encode(file_bytes).decode()
            
            logger.info(f"📄 开始识别文档: {filename} ({len(file_bytes)} bytes)")
            
            # 调用 MCP 服务
            result = await self._call_tool(
                "doc_recognition",
                {
                    "file": file_base64,
                    "filename": filename
                }
            )
            
            if result and "content" in result:
                logger.info(f"✅ 文档识别成功: {filename}")
                return {
                    "success": True,
                    "filename": filename,
                    "content": result["content"],
                    "metadata": result.get("metadata", {}),
                    "file_size": len(file_bytes),
                    "format": file_ext
                }
            else:
                logger.error(f"❌ 文档识别失败: {filename}")
                return {
                    "success": False,
                    "filename": filename,
                    "error": "识别结果为空",
                    "file_size": len(file_bytes),
                    "format": file_ext
                }
        
        except Exception as e:
            logger.error(f"❌ 文档识别异常: {e}")
            return {
                "success": False,
                "filename": str(file_path),
                "error": str(e)
            }
    
    async def doc_to_markdown(self, file_path: Union[str, Path], filename: Optional[str] = None) -> Dict[str, Any]:
        """
        文档转 Markdown - 保留格式的文档转换
        
        Args:
            file_path: 文件路径
            filename: 文件名（可选）
            
        Returns:
            转换结果字典
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            filename = filename or file_path.name
            
            # 读取文件并编码
            file_bytes = file_path.read_bytes()
            file_base64 = base64.b64encode(file_bytes).decode()
            
            logger.info(f"📄 开始转换文档为 Markdown: {filename} ({len(file_bytes)} bytes)")
            
            # 调用 MCP 服务
            result = await self._call_tool(
                "doc_to_markdown",
                {
                    "file": file_base64,
                    "filename": filename
                }
            )
            
            if result and "content" in result:
                logger.info(f"✅ 文档转换成功: {filename}")
                return {
                    "success": True,
                    "filename": filename,
                    "content": result["content"],
                    "metadata": result.get("metadata", {}),
                    "file_size": len(file_bytes),
                    "format": "markdown"
                }
            else:
                logger.error(f"❌ 文档转换失败: {filename}")
                return {
                    "success": False,
                    "filename": filename,
                    "error": "转换结果为空",
                    "file_size": len(file_bytes)
                }
        
        except Exception as e:
            logger.error(f"❌ 文档转换异常: {e}")
            return {
                "success": False,
                "filename": str(file_path),
                "error": str(e)
            }
    
    async def batch_process(self, file_paths: List[Union[str, Path]], 
                          output_format: str = "text") -> List[Dict[str, Any]]:
        """
        批量处理文档
        
        Args:
            file_paths: 文件路径列表
            output_format: 输出格式 ("text" 或 "markdown")
            
        Returns:
            处理结果列表
        """
        results = []
        
        logger.info(f"📦 开始批量处理 {len(file_paths)} 个文件，格式: {output_format}")
        
        for file_path in file_paths:
            try:
                if output_format == "markdown":
                    result = await self.doc_to_markdown(file_path)
                else:
                    result = await self.doc_recognition(file_path)
                
                results.append(result)
                
                # 避免请求过于频繁
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ 批量处理失败: {file_path}, {e}")
                results.append({
                    "success": False,
                    "filename": str(file_path),
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r.get("success", False))
        logger.info(f"✅ 批量处理完成: {success_count}/{len(file_paths)} 成功")
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 尝试获取工具列表
            tools = await self._list_tools()
            
            return {
                "status": "healthy",
                "service": "aiocr",
                "tools_available": len(tools),
                "supported_formats": len(self.supported_formats),
                "message": "AIOCR 服务正常"
            }
        except Exception as e:
            return {
                "status": "error",
                "service": "aiocr",
                "error": str(e),
                "message": "AIOCR 服务异常"
            }
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return self.supported_formats.copy()
    
    def is_format_supported(self, file_ext: str) -> bool:
        """检查文件格式是否支持"""
        return file_ext.lower() in self.supported_formats
