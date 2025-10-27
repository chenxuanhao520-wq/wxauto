"""
充电桩行业文档模板和处理器
基于PaddleOCR-VL的行业定制化处理
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ChargingPileDocumentProcessor:
    """
    充电桩行业文档处理器
    
    专门处理充电桩行业相关文档：
    1. 技术手册和规格书
    2. 安装指南和施工图纸
    3. 维护手册和故障排除
    4. 认证证书和检测报告
    5. 培训材料和操作手册
    """
    
    def __init__(self):
        self.document_templates = self._init_document_templates()
        self.industry_keywords = self._init_industry_keywords()
        self.processing_rules = self._init_processing_rules()
    
    def _init_document_templates(self) -> Dict[str, Dict[str, Any]]:
        """初始化文档模板"""
        return {
            "technical_manual": {
                "name": "技术手册",
                "keywords": ["技术规格", "参数", "性能指标", "技术参数", "规格书"],
                "sections": ["产品概述", "技术参数", "安装要求", "操作说明", "维护保养"],
                "priority": 1
            },
            "installation_guide": {
                "name": "安装指南",
                "keywords": ["安装", "施工", "布线", "接地", "安装步骤", "施工图纸"],
                "sections": ["安装前准备", "安装步骤", "接线说明", "调试测试", "验收标准"],
                "priority": 2
            },
            "maintenance_manual": {
                "name": "维护手册",
                "keywords": ["维护", "保养", "检修", "故障", "维修", "更换"],
                "sections": ["日常维护", "定期保养", "故障诊断", "维修步骤", "备件清单"],
                "priority": 3
            },
            "certification": {
                "name": "认证证书",
                "keywords": ["认证", "证书", "检测", "标准", "合规", "资质"],
                "sections": ["证书信息", "检测标准", "有效期", "认证机构", "适用范围"],
                "priority": 4
            },
            "training_material": {
                "name": "培训材料",
                "keywords": ["培训", "操作", "手册", "指南", "教程", "学习"],
                "sections": ["培训目标", "操作流程", "注意事项", "考核标准", "参考资料"],
                "priority": 5
            }
        }
    
    def _init_industry_keywords(self) -> Dict[str, List[str]]:
        """初始化行业关键词"""
        return {
            "equipment": [
                "充电桩", "充电站", "充电设备", "充电终端", "充电枪", "充电线缆",
                "充电模块", "充电控制器", "充电管理系统", "充电桩主机"
            ],
            "technical": [
                "功率", "电压", "电流", "充电速度", "充电效率", "功率因数",
                "输入电压", "输出电压", "额定功率", "最大功率", "充电功率",
                "AC", "DC", "交流", "直流", "快充", "慢充", "超充"
            ],
            "installation": [
                "安装", "施工", "布线", "接地", "防护", "安全距离",
                "安装位置", "安装高度", "安装角度", "安装环境", "安装要求",
                "电缆", "线缆", "接线", "配电", "配电箱", "配电柜"
            ],
            "safety": [
                "安全", "防护", "绝缘", "漏电", "过载", "短路", "过压", "欠压",
                "过流", "欠流", "过温", "防雷", "防潮", "防火", "防爆",
                "安全距离", "安全防护", "安全措施", "安全标准"
            ],
            "maintenance": [
                "维护", "保养", "检修", "故障", "维修", "更换", "清洁",
                "检查", "测试", "调试", "校准", "升级", "更新",
                "故障代码", "故障诊断", "故障排除", "故障处理"
            ],
            "standards": [
                "标准", "规范", "要求", "认证", "检测", "测试", "验证",
                "国标", "行标", "企标", "国际标准", "行业标准",
                "GB", "IEC", "UL", "CE", "CCC", "FCC"
            ]
        }
    
    def _init_processing_rules(self) -> Dict[str, Any]:
        """初始化处理规则"""
        return {
            "ocr_settings": {
                "confidence_threshold": 0.7,
                "language_priority": ["ch", "en"],
                "enable_table_detection": True,
                "enable_formula_detection": True,
                "enable_chart_detection": True
            },
            "content_extraction": {
                "extract_tables": True,
                "extract_formulas": True,
                "extract_charts": True,
                "preserve_layout": True,
                "extract_metadata": True
            },
            "industry_analysis": {
                "enable_keyword_extraction": True,
                "enable_category_classification": True,
                "enable_priority_scoring": True,
                "enable_compliance_check": True
            }
        }
    
    def analyze_document_type(self, content: str, file_name: str) -> Dict[str, Any]:
        """分析文档类型"""
        analysis = {
            "document_type": "unknown",
            "confidence": 0.0,
            "matched_keywords": [],
            "suggested_sections": [],
            "priority": 0
        }
        
        content_lower = content.lower()
        file_name_lower = file_name.lower()
        
        # 检查每种文档类型
        for doc_type, template in self.document_templates.items():
            keyword_matches = []
            
            # 检查关键词匹配
            for keyword in template["keywords"]:
                if keyword in content_lower or keyword in file_name_lower:
                    keyword_matches.append(keyword)
            
            # 计算匹配度
            match_ratio = len(keyword_matches) / len(template["keywords"])
            
            if match_ratio > analysis["confidence"]:
                analysis["document_type"] = doc_type
                analysis["confidence"] = match_ratio
                analysis["matched_keywords"] = keyword_matches
                analysis["suggested_sections"] = template["sections"]
                analysis["priority"] = template["priority"]
        
        return analysis
    
    def extract_industry_keywords(self, content: str) -> Dict[str, List[str]]:
        """提取行业关键词"""
        extracted_keywords = {}
        content_lower = content.lower()
        
        for category, keywords in self.industry_keywords.items():
            found_keywords = [kw for kw in keywords if kw in content_lower]
            if found_keywords:
                extracted_keywords[category] = found_keywords
        
        return extracted_keywords
    
    def process_multimodal_data(self, multimodal_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理多模态数据"""
        processed_data = {
            "text_content": "",
            "tables": [],
            "formulas": [],
            "charts": [],
            "technical_data": {},
            "safety_info": [],
            "compliance_info": []
        }
        
        # 处理文本元素
        if "text_elements" in multimodal_data:
            text_parts = []
            for element in multimodal_data["text_elements"]:
                text_parts.append(element["content"])
            processed_data["text_content"] = "\n".join(text_parts)
        
        # 处理表格元素
        if "table_elements" in multimodal_data:
            for table in multimodal_data["table_elements"]:
                table_info = {
                    "content": table["content"],
                    "confidence": table["confidence"],
                    "type": self._classify_table_type(table["content"])
                }
                processed_data["tables"].append(table_info)
        
        # 处理公式元素
        if "formula_elements" in multimodal_data:
            for formula in multimodal_data["formula_elements"]:
                formula_info = {
                    "content": formula["content"],
                    "confidence": formula["confidence"],
                    "type": self._classify_formula_type(formula["content"])
                }
                processed_data["formulas"].append(formula_info)
        
        # 处理图表元素
        if "chart_elements" in multimodal_data:
            for chart in multimodal_data["chart_elements"]:
                chart_info = {
                    "content": chart["content"],
                    "confidence": chart["confidence"],
                    "type": self._classify_chart_type(chart["content"])
                }
                processed_data["charts"].append(chart_info)
        
        # 提取技术数据
        processed_data["technical_data"] = self._extract_technical_data(processed_data["text_content"])
        
        # 提取安全信息
        processed_data["safety_info"] = self._extract_safety_info(processed_data["text_content"])
        
        # 提取合规信息
        processed_data["compliance_info"] = self._extract_compliance_info(processed_data["text_content"])
        
        return processed_data
    
    def _classify_table_type(self, table_content: str) -> str:
        """分类表格类型"""
        content_lower = table_content.lower()
        
        if any(kw in content_lower for kw in ["功率", "电压", "电流", "参数"]):
            return "technical_specs"
        elif any(kw in content_lower for kw in ["安装", "施工", "步骤"]):
            return "installation_steps"
        elif any(kw in content_lower for kw in ["故障", "代码", "排除"]):
            return "troubleshooting"
        elif any(kw in content_lower for kw in ["维护", "保养", "检查"]):
            return "maintenance_schedule"
        else:
            return "general"
    
    def _classify_formula_type(self, formula_content: str) -> str:
        """分类公式类型"""
        content_lower = formula_content.lower()
        
        if any(kw in content_lower for kw in ["功率", "p=", "w="]):
            return "power_calculation"
        elif any(kw in content_lower for kw in ["电压", "u=", "v="]):
            return "voltage_calculation"
        elif any(kw in content_lower for kw in ["电流", "i=", "a="]):
            return "current_calculation"
        elif any(kw in content_lower for kw in ["效率", "η=", "efficiency"]):
            return "efficiency_calculation"
        else:
            return "general"
    
    def _classify_chart_type(self, chart_content: str) -> str:
        """分类图表类型"""
        content_lower = chart_content.lower()
        
        if any(kw in content_lower for kw in ["曲线", "曲线图", "chart"]):
            return "curve_chart"
        elif any(kw in content_lower for kw in ["柱状", "柱状图", "bar"]):
            return "bar_chart"
        elif any(kw in content_lower for kw in ["饼图", "pie", "比例"]):
            return "pie_chart"
        elif any(kw in content_lower for kw in ["流程图", "flow", "步骤"]):
            return "flow_chart"
        else:
            return "general"
    
    def _extract_technical_data(self, content: str) -> Dict[str, Any]:
        """提取技术数据"""
        technical_data = {
            "power_ratings": [],
            "voltage_levels": [],
            "current_levels": [],
            "efficiency_values": [],
            "temperature_ranges": []
        }
        
        # 提取功率数据
        import re
        power_pattern = r'(\d+(?:\.\d+)?)\s*(?:kW|kw|千瓦|功率)'
        technical_data["power_ratings"] = re.findall(power_pattern, content)
        
        # 提取电压数据
        voltage_pattern = r'(\d+(?:\.\d+)?)\s*(?:V|v|伏|电压)'
        technical_data["voltage_levels"] = re.findall(voltage_pattern, content)
        
        # 提取电流数据
        current_pattern = r'(\d+(?:\.\d+)?)\s*(?:A|a|安|电流)'
        technical_data["current_levels"] = re.findall(current_pattern, content)
        
        return technical_data
    
    def _extract_safety_info(self, content: str) -> List[str]:
        """提取安全信息"""
        safety_info = []
        content_lower = content.lower()
        
        safety_keywords = self.industry_keywords["safety"]
        for keyword in safety_keywords:
            if keyword in content_lower:
                # 提取包含该关键词的句子
                sentences = content.split('。')
                for sentence in sentences:
                    if keyword in sentence:
                        safety_info.append(sentence.strip())
        
        return safety_info[:10]  # 限制数量
    
    def _extract_compliance_info(self, content: str) -> List[str]:
        """提取合规信息"""
        compliance_info = []
        content_lower = content.lower()
        
        compliance_keywords = self.industry_keywords["standards"]
        for keyword in compliance_keywords:
            if keyword in content_lower:
                # 提取包含该关键词的句子
                sentences = content.split('。')
                for sentence in sentences:
                    if keyword in sentence:
                        compliance_info.append(sentence.strip())
        
        return compliance_info[:10]  # 限制数量
    
    def generate_document_summary(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成文档摘要"""
        summary = {
            "document_type": "unknown",
            "industry_category": "charging_pile",
            "key_features": [],
            "technical_highlights": [],
            "safety_highlights": [],
            "compliance_highlights": [],
            "processing_quality": "unknown",
            "recommendations": []
        }
        
        # 分析文档类型
        doc_analysis = self.analyze_document_type(
            ocr_result.get("content", ""),
            ocr_result.get("file_name", "")
        )
        summary["document_type"] = doc_analysis["document_type"]
        
        # 处理多模态数据
        if "multimodal_data" in ocr_result:
            processed_data = self.process_multimodal_data(ocr_result["multimodal_data"])
            
            # 提取关键特征
            if processed_data["tables"]:
                summary["key_features"].append(f"包含{len(processed_data['tables'])}个表格")
            if processed_data["formulas"]:
                summary["key_features"].append(f"包含{len(processed_data['formulas'])}个公式")
            if processed_data["charts"]:
                summary["key_features"].append(f"包含{len(processed_data['charts'])}个图表")
            
            # 技术亮点
            if processed_data["technical_data"]["power_ratings"]:
                summary["technical_highlights"].append(f"功率规格: {processed_data['technical_data']['power_ratings']}")
            if processed_data["technical_data"]["voltage_levels"]:
                summary["technical_highlights"].append(f"电压等级: {processed_data['technical_data']['voltage_levels']}")
            
            # 安全亮点
            if processed_data["safety_info"]:
                summary["safety_highlights"] = processed_data["safety_info"][:3]
            
            # 合规亮点
            if processed_data["compliance_info"]:
                summary["compliance_highlights"] = processed_data["compliance_info"][:3]
        
        # 处理质量评估
        confidence = ocr_result.get("industry_analysis", {}).get("confidence", 0.0)
        if confidence > 0.8:
            summary["processing_quality"] = "excellent"
        elif confidence > 0.6:
            summary["processing_quality"] = "good"
        elif confidence > 0.4:
            summary["processing_quality"] = "fair"
        else:
            summary["processing_quality"] = "poor"
        
        # 生成建议
        if summary["processing_quality"] == "poor":
            summary["recommendations"].append("建议重新扫描或使用更高质量的原始文档")
        if not summary["technical_highlights"]:
            summary["recommendations"].append("建议补充技术参数信息")
        if not summary["safety_highlights"]:
            summary["recommendations"].append("建议补充安全相关信息")
        
        return summary

