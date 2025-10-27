"""
增强版OCR处理器 - PaddleOCR-VL多模态集成
专为充电桩行业文档处理优化，支持复杂文档的一体化解析
"""

import logging
import asyncio
import json
import base64
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class EnhancedOCRProcessor:
    """
    增强版OCR处理器 - PaddleOCR-VL多模态版本
    
    核心特性：
    1. PaddleOCR-VL - 多模态文档理解（主要）
    2. PP-OCRv5 - 高精度文字识别（备选）
    3. PP-StructureV3 - 版面分析（备选）
    4. 充电桩行业定制优化
    5. 109种语言支持
    6. 一体化复杂文档处理
    """
    
    def __init__(self, 
                 use_gpu: bool = True,
                 lang: str = 'ch',
                 primary_mode: str = 'vl',
                 enable_fallback: bool = True):
        """
        初始化增强版OCR处理器 - PaddleOCR-VL优先
        
        Args:
            use_gpu: 是否使用GPU加速
            lang: 识别语言（支持109种语言）
            primary_mode: 主要模式 (vl/structure/ocr)
            enable_fallback: 启用降级机制
        """
        self.use_gpu = use_gpu
        self.lang = lang
        self.primary_mode = primary_mode
        self.enable_fallback = enable_fallback
        
        # 初始化各种引擎
        self.vl_engine = None          # PaddleOCR-VL（主要）
        self.ocr_engine = None        # PP-OCRv5（备选）
        self.structure_engine = None # PP-StructureV3（备选）
        
        # 充电桩行业关键词
        self.charging_pile_keywords = {
            'technical': ['充电桩', '充电站', '充电设备', '功率', '电压', '电流', '充电速度'],
            'installation': ['安装', '施工', '布线', '接地', '防护', '安全距离'],
            'maintenance': ['维护', '保养', '检修', '故障', '维修', '更换'],
            'certification': ['认证', '证书', '检测', '标准', '合规', '资质'],
            'safety': ['安全', '防护', '绝缘', '漏电', '过载', '短路']
        }
        
        logger.info(f"🚀 PaddleOCR-VL多模态处理器初始化 (GPU: {use_gpu}, 语言: {lang}, 主模式: {primary_mode})")
    
    def _init_ocr_engine(self):
        """初始化基础OCR引擎"""
        if self.ocr_engine is None:
            try:
                from paddleocr import PaddleOCR
                
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.lang,
                    use_gpu=self.use_gpu,
                    show_log=False
                )
                logger.info("✅ PP-OCRv5 引擎初始化成功")
            except Exception as e:
                logger.error(f"❌ OCR引擎初始化失败: {e}")
                raise
    
    def _init_structure_engine(self):
        """初始化版面分析引擎"""
        if self.structure_engine is None and self.enable_structure:
            try:
                from paddleocr import PPStructure
                
                self.structure_engine = PPStructure(
                    table_engine=True,
                    ocr_engine=True,
                    layout_engine=True,
                    use_gpu=self.use_gpu,
                    show_log=False
                )
                logger.info("✅ PP-StructureV3 引擎初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 版面分析引擎初始化失败: {e}")
                self.enable_structure = False
    
    def _init_chat_engine(self):
        """初始化文档理解引擎"""
        if self.chat_engine is None and self.enable_chat:
            try:
                from paddleocr import PaddleOCRVL
                
                self.chat_engine = PaddleOCRVL()
                logger.info("✅ PP-ChatOCRv4 引擎初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 文档理解引擎初始化失败: {e}")
                self.enable_chat = False
    
    def _init_vl_engine(self):
        """初始化PaddleOCR-VL多模态引擎（主要）"""
        if self.vl_engine is None:
            try:
                from paddleocr import PaddleOCRVL
                
                self.vl_engine = PaddleOCRVL()
                logger.info("✅ PaddleOCR-VL 多模态引擎初始化成功")
            except Exception as e:
                logger.error(f"❌ PaddleOCR-VL 引擎初始化失败: {e}")
                if self.enable_fallback:
                    logger.info("🔄 启用降级机制，将使用备选引擎")
                else:
                    raise
    
    async def process_document(self, 
                             file_path: Union[str, Path],
                             processing_mode: str = "auto",
                             enable_multimodal: bool = True) -> Dict[str, Any]:
        """
        处理文档 - PaddleOCR-VL多模态优先
        
        Args:
            file_path: 文件路径
            processing_mode: 处理模式 (auto/vl/structure/ocr)
            enable_multimodal: 是否启用多模态处理
            
        Returns:
            处理结果字典
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"📄 开始处理文档: {file_path.name}")
        
        # 根据文件类型和处理模式选择最佳方案
        if processing_mode == "auto":
            processing_mode = self._determine_best_mode(file_path)
        
        result = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "processing_mode": processing_mode,
            "success": False,
            "content": "",
            "metadata": {},
            "multimodal_data": {},
            "industry_analysis": {}
        }
        
        try:
            # PaddleOCR-VL多模态处理（主要）
            if processing_mode == "vl" and enable_multimodal:
                result = await self._process_with_vl_multimodal(file_path, result)
            # 版面分析处理（备选）
            elif processing_mode == "structure":
                result = await self._process_with_structure(file_path, result)
            # 基础OCR处理（备选）
            else:
                result = await self._process_with_ocr(file_path, result)
            
            # 充电桩行业分析
            if result["success"]:
                result["industry_analysis"] = self._analyze_charging_pile_content(result["content"])
            
            result["success"] = True
            logger.info(f"✅ 文档处理完成: {file_path.name} (模式: {processing_mode})")
            
        except Exception as e:
            logger.error(f"❌ 文档处理失败: {file_path.name}, {e}")
            result["error"] = str(e)
            
            # 降级处理
            if self.enable_fallback and processing_mode != "ocr":
                logger.info(f"🔄 尝试降级处理: {file_path.name}")
                try:
                    result = await self._process_with_ocr(file_path, result)
                    result["success"] = True
                    result["fallback_used"] = True
                    logger.info(f"✅ 降级处理成功: {file_path.name}")
                except Exception as fallback_error:
                    logger.error(f"❌ 降级处理也失败: {fallback_error}")
                    result["fallback_error"] = str(fallback_error)
        
        return result
    
    def _determine_best_mode(self, file_path: Path) -> str:
        """根据文件类型确定最佳处理模式 - PaddleOCR-VL优先"""
        ext = file_path.suffix.lower()
        
        # 优先使用PaddleOCR-VL多模态处理
        if ext in ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return "vl"
        
        # 其他文件使用基础OCR
        else:
            return "ocr"
    
    async def _process_with_structure(self, 
                                    file_path: Path, 
                                    result: Dict[str, Any],
                                    extract_tables: bool,
                                    extract_layout: bool) -> Dict[str, Any]:
        """使用版面分析处理文档"""
        self._init_structure_engine()
        
        if not self.structure_engine:
            raise RuntimeError("版面分析引擎未初始化")
        
        # 版面分析
        structure_result = self.structure_engine(str(file_path))
        
        # 提取文本内容
        text_parts = []
        tables = []
        layout_info = {}
        
        for item in structure_result:
            if item['type'] == 'text':
                text_parts.append(item['res']['text'])
            elif item['type'] == 'table' and extract_tables:
                table_data = self._extract_table_data(item['res'])
                tables.append(table_data)
            elif item['type'] == 'layout' and extract_layout:
                layout_info[item['bbox']] = {
                    'type': item['type'],
                    'confidence': item.get('confidence', 0.0)
                }
        
        result["content"] = "\n".join(text_parts)
        result["tables"] = tables
        result["layout"] = layout_info
        result["metadata"]["structure_analysis"] = True
        
        return result
    
    async def _process_with_vl_multimodal(self, 
                                        file_path: Path, 
                                        result: Dict[str, Any]) -> Dict[str, Any]:
        """使用PaddleOCR-VL多模态处理文档（主要方法）"""
        self._init_vl_engine()
        
        if not self.vl_engine:
            raise RuntimeError("PaddleOCR-VL引擎未初始化")
        
        logger.info(f"🤖 使用PaddleOCR-VL多模态处理: {file_path.name}")
        
        # PaddleOCR-VL多模态处理
        vl_result = self.vl_engine.predict(str(file_path))
        
        # 提取多模态结果
        content_parts = []
        multimodal_data = {
            "text_elements": [],
            "table_elements": [],
            "formula_elements": [],
            "chart_elements": [],
            "layout_info": {}
        }
        
        for item in vl_result:
            # 提取文本内容
            if hasattr(item, 'text') and item.text:
                content_parts.append(item.text)
            
            # 提取多模态元素信息
            if hasattr(item, 'type'):
                element_type = item.type
                element_data = {
                    "type": element_type,
                    "content": getattr(item, 'text', ''),
                    "bbox": getattr(item, 'bbox', []),
                    "confidence": getattr(item, 'confidence', 0.0)
                }
                
                if element_type == 'text':
                    multimodal_data["text_elements"].append(element_data)
                elif element_type == 'table':
                    multimodal_data["table_elements"].append(element_data)
                elif element_type == 'formula':
                    multimodal_data["formula_elements"].append(element_data)
                elif element_type == 'chart':
                    multimodal_data["chart_elements"].append(element_data)
        
        result["content"] = "\n".join(content_parts)
        result["multimodal_data"] = multimodal_data
        result["metadata"]["vl_multimodal"] = True
        result["metadata"]["elements_count"] = {
            "text": len(multimodal_data["text_elements"]),
            "table": len(multimodal_data["table_elements"]),
            "formula": len(multimodal_data["formula_elements"]),
            "chart": len(multimodal_data["chart_elements"])
        }
        
        logger.info(f"✅ PaddleOCR-VL处理完成: {len(content_parts)}个文本块, "
                   f"{len(multimodal_data['table_elements'])}个表格, "
                   f"{len(multimodal_data['formula_elements'])}个公式")
        
        return result
    
    async def _process_with_ocr(self, 
                               file_path: Path, 
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """使用基础OCR处理文档"""
        self._init_ocr_engine()
        
        if not self.ocr_engine:
            raise RuntimeError("OCR引擎未初始化")
        
        # OCR识别
        ocr_result = self.ocr_engine.ocr(str(file_path), cls=True)
        
        # 提取文本
        text_lines = []
        if ocr_result and ocr_result[0]:
            for line in ocr_result[0]:
                if len(line) >= 2:
                    text = line[1][0]
                    confidence = line[1][1]
                    
                    # 只保留置信度>0.5的文本
                    if confidence > 0.5:
                        text_lines.append(text)
        
        result["content"] = "\n".join(text_lines)
        result["metadata"]["ocr_analysis"] = True
        
        return result
    
    def _extract_table_data(self, table_result: Dict) -> Dict[str, Any]:
        """提取表格数据"""
        try:
            # 解析表格结构
            table_data = {
                "rows": len(table_result.get('html', '').split('<tr>')) - 1,
                "html": table_result.get('html', ''),
                "text": table_result.get('text', ''),
                "confidence": table_result.get('confidence', 0.0)
            }
            
            # 提取表格文本内容
            if 'html' in table_result:
                # 简单的HTML表格解析
                html_content = table_result['html']
                # 这里可以添加更复杂的表格解析逻辑
                table_data["parsed_data"] = self._parse_html_table(html_content)
            
            return table_data
        except Exception as e:
            logger.warning(f"表格数据提取失败: {e}")
            return {"error": str(e)}
    
    def _parse_html_table(self, html_content: str) -> List[List[str]]:
        """解析HTML表格"""
        # 简单的HTML表格解析实现
        # 实际应用中可以使用BeautifulSoup等库
        rows = []
        # 这里添加具体的解析逻辑
        return rows
    
    async def _analyze_with_chat(self, content: str, file_path: Path) -> Dict[str, Any]:
        """使用文档理解分析内容"""
        if not self.chat_engine:
            return {}
        
        try:
            # 文档理解分析
            analysis_result = self.chat_engine.predict(str(file_path))
            
            return {
                "summary": analysis_result.get("summary", ""),
                "key_points": analysis_result.get("key_points", []),
                "document_type": analysis_result.get("document_type", ""),
                "confidence": analysis_result.get("confidence", 0.0)
            }
        except Exception as e:
            logger.warning(f"文档理解分析失败: {e}")
            return {"error": str(e)}
    
    def _analyze_charging_pile_content(self, content: str) -> Dict[str, Any]:
        """充电桩行业内容分析"""
        analysis = {
            "industry_type": "unknown",
            "document_category": "unknown",
            "technical_keywords": [],
            "safety_keywords": [],
            "compliance_keywords": [],
            "confidence": 0.0
        }
        
        content_lower = content.lower()
        
        # 分析行业类型
        for category, keywords in self.charging_pile_keywords.items():
            found_keywords = [kw for kw in keywords if kw in content_lower]
            if found_keywords:
                analysis[f"{category}_keywords"] = found_keywords
                analysis["confidence"] += len(found_keywords) * 0.1
        
        # 确定文档类别
        if analysis["technical_keywords"]:
            analysis["document_category"] = "technical"
        elif analysis["safety_keywords"]:
            analysis["document_category"] = "safety"
        elif analysis["compliance_keywords"]:
            analysis["document_category"] = "compliance"
        
        analysis["confidence"] = min(analysis["confidence"], 1.0)
        
        return analysis
    
    async def batch_process(self, 
                          file_paths: List[Union[str, Path]],
                          processing_mode: str = "auto") -> List[Dict[str, Any]]:
        """批量处理文档"""
        results = []
        
        logger.info(f"📦 开始批量处理 {len(file_paths)} 个文件")
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                logger.info(f"处理文件 {i}/{len(file_paths)}: {file_path}")
                
                result = await self.process_document(
                    file_path=file_path,
                    processing_mode=processing_mode
                )
                
                results.append(result)
                
                # 避免处理过于频繁
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ 处理文件失败: {file_path}, {e}")
                results.append({
                    "file_path": str(file_path),
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r.get("success", False))
        logger.info(f"✅ 批量处理完成: {success_count}/{len(file_paths)} 成功")
        
        return results
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的文件格式"""
        return {
            "ocr": ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
            "structure": ['.pdf', '.jpg', '.jpeg', '.png'],
            "vl": ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
            "all": ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.doc', '.docx']
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            "ocr_engine": "unavailable",
            "structure_engine": "unavailable", 
            "chat_engine": "unavailable",
            "vl_engine": "unavailable",
            "gpu_available": False,
            "overall_status": "unhealthy"
        }
        
        try:
            # 检查OCR引擎
            self._init_ocr_engine()
            if self.ocr_engine:
                health["ocr_engine"] = "available"
            
            # 检查版面分析引擎
            if self.enable_structure:
                self._init_structure_engine()
                if self.structure_engine:
                    health["structure_engine"] = "available"
            
            # 检查文档理解引擎
            if self.enable_chat:
                self._init_chat_engine()
                if self.chat_engine:
                    health["chat_engine"] = "available"
            
            # 检查多模态引擎
            if self.enable_vl:
                self._init_vl_engine()
                if self.vl_engine:
                    health["vl_engine"] = "available"
            
            # 检查GPU
            try:
                import paddle
                health["gpu_available"] = paddle.is_compiled_with_cuda()
            except:
                pass
            
            # 计算整体状态
            available_engines = sum(1 for status in health.values() 
                                  if status == "available")
            if available_engines >= 1:
                health["overall_status"] = "healthy"
            
        except Exception as e:
            health["error"] = str(e)
        
        return health
