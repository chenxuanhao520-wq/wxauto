"""
结构验证器
定义不同类型文档的必要字段和格式约束
"""
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FieldRequirement:
    """字段要求"""
    field_name: str
    field_type: str  # text, image, link, number, list
    required: bool
    description: str
    validation_pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    examples: List[str] = field(default_factory=list)


@dataclass
class DocumentTemplate:
    """文档模板"""
    template_id: str
    document_type: str
    display_name: str
    description: str
    required_fields: List[FieldRequirement]
    optional_fields: List[FieldRequirement]
    structure_rules: List[str]
    examples: List[str] = field(default_factory=list)


class StructureValidator:
    """
    结构验证器
    
    功能：
    1. 定义文档模板
    2. 验证必要字段
    3. 验证格式约束
    4. 生成反馈报告
    """
    
    def __init__(self):
        """初始化结构验证器"""
        # 定义各类文档模板
        self.templates = self._init_templates()
        
        logger.info(f"结构验证器初始化完成: {len(self.templates)} 个模板")
    
    def _init_templates(self) -> Dict[str, DocumentTemplate]:
        """初始化文档模板"""
        templates = {}
        
        # ==================== 产品信息文档模板 ====================
        templates['product_info'] = DocumentTemplate(
            template_id='product_info_v1',
            document_type='product_info',
            display_name='产品信息文档',
            description='产品的基本信息、技术规格、功能特性等',
            required_fields=[
                FieldRequirement(
                    field_name='产品名称',
                    field_type='text',
                    required=True,
                    description='产品的正式名称',
                    min_length=2,
                    max_length=100,
                    examples=['7kW交流充电桩', '120kW直流充电桩']
                ),
                FieldRequirement(
                    field_name='产品型号',
                    field_type='text',
                    required=True,
                    description='产品的型号或编号',
                    validation_pattern=r'^[A-Z0-9\-]+$',
                    examples=['AC-7KW-001', 'DC-120KW-PRO']
                ),
                FieldRequirement(
                    field_name='技术规格',
                    field_type='list',
                    required=True,
                    description='产品的主要技术参数',
                    examples=['额定功率: 7kW', '输入电压: 220V AC', '输出电压: 200-750V DC']
                ),
                FieldRequirement(
                    field_name='功能描述',
                    field_type='text',
                    required=True,
                    description='产品的主要功能和特性',
                    min_length=50,
                    examples=['支持APP远程监控、自动充电保护、智能计费等功能']
                ),
                FieldRequirement(
                    field_name='适用场景',
                    field_type='text',
                    required=True,
                    description='产品的应用场景',
                    examples=['家用充电', '商业充电站', '企业停车场']
                )
            ],
            optional_fields=[
                FieldRequirement(
                    field_name='产品图片',
                    field_type='image',
                    required=False,
                    description='产品外观图片'
                ),
                FieldRequirement(
                    field_name='价格信息',
                    field_type='text',
                    required=False,
                    description='产品价格范围'
                ),
                FieldRequirement(
                    field_name='相关链接',
                    field_type='link',
                    required=False,
                    description='产品详情页链接'
                )
            ],
            structure_rules=[
                '产品名称应出现在文档开头',
                '技术规格应以列表形式呈现',
                '每个技术参数应包含名称和数值单位'
            ]
        )
        
        # ==================== FAQ文档模板 ====================
        templates['faq'] = DocumentTemplate(
            template_id='faq_v1',
            document_type='faq',
            display_name='FAQ常见问题',
            description='常见问题和答案',
            required_fields=[
                FieldRequirement(
                    field_name='问题',
                    field_type='text',
                    required=True,
                    description='用户的常见问题（问法）',
                    min_length=5,
                    max_length=200,
                    examples=[
                        '充电桩如何安装？',
                        '充电桩故障灯红色是什么原因？',
                        '充电桩支持哪些车型？'
                    ]
                ),
                FieldRequirement(
                    field_name='简洁答案',
                    field_type='text',
                    required=True,
                    description='问题的简洁回答（1-2句话）',
                    min_length=10,
                    max_length=200,
                    examples=['充电桩需由专业人员安装，包括固定底座、连接电源线、通电测试三个步骤。']
                ),
                FieldRequirement(
                    field_name='详细说明',
                    field_type='text',
                    required=False,
                    description='问题的详细解答',
                    examples=['详细安装步骤：1. 关闭主电源...']
                )
            ],
            optional_fields=[
                FieldRequirement(
                    field_name='相关链接',
                    field_type='link',
                    required=False,
                    description='相关文档或操作指南链接',
                    examples=['https://docs.example.com/install-guide']
                ),
                FieldRequirement(
                    field_name='操作步骤',
                    field_type='list',
                    required=False,
                    description='具体的操作步骤列表',
                    examples=['1. 关闭电源', '2. 固定底座', '3. 连接线路']
                ),
                FieldRequirement(
                    field_name='相关FAQ',
                    field_type='list',
                    required=False,
                    description='相关的其他常见问题',
                    examples=['充电桩维护保养', '充电桩故障排查']
                )
            ],
            structure_rules=[
                '问题应以疑问句形式呈现',
                '简洁答案应控制在50字以内',
                '如有操作步骤，应使用编号列表',
                '相关链接应可访问'
            ]
        )
        
        # ==================== 操作文档模板 ====================
        templates['operation'] = DocumentTemplate(
            template_id='operation_v1',
            document_type='operation',
            display_name='操作指南文档',
            description='产品的操作步骤和使用指南',
            required_fields=[
                FieldRequirement(
                    field_name='操作标题',
                    field_type='text',
                    required=True,
                    description='操作的名称',
                    examples=['充电桩安装指南', '充电桩日常使用教程']
                ),
                FieldRequirement(
                    field_name='前置条件',
                    field_type='list',
                    required=True,
                    description='执行操作前需要满足的条件',
                    examples=['电源已准备', '工具已备齐', '阅读安全须知']
                ),
                FieldRequirement(
                    field_name='操作步骤',
                    field_type='list',
                    required=True,
                    description='详细的操作步骤（必须有序号）',
                    min_length=2,
                    examples=[
                        '1. 关闭主电源开关',
                        '2. 使用M6螺丝固定底座',
                        '3. 连接电源线到配电箱'
                    ]
                ),
                FieldRequirement(
                    field_name='预期结果',
                    field_type='text',
                    required=True,
                    description='操作完成后的预期结果',
                    examples=['充电桩指示灯正常闪烁，可以开始充电']
                )
            ],
            optional_fields=[
                FieldRequirement(
                    field_name='操作截图',
                    field_type='image',
                    required=False,
                    description='清晰的操作截图或示意图'
                ),
                FieldRequirement(
                    field_name='注意事项',
                    field_type='list',
                    required=False,
                    description='操作过程中需要注意的事项',
                    examples=['禁止带电操作', '确保通风良好']
                ),
                FieldRequirement(
                    field_name='常见问题',
                    field_type='list',
                    required=False,
                    description='操作过程中可能遇到的问题',
                    examples=['如果指示灯不亮，检查电源连接']
                ),
                FieldRequirement(
                    field_name='视频链接',
                    field_type='link',
                    required=False,
                    description='操作视频教程链接'
                )
            ],
            structure_rules=[
                '操作步骤必须使用数字编号',
                '每个步骤应简洁明确',
                '如有截图，应清晰标注关键区域',
                '注意事项应醒目展示'
            ]
        )
        
        # ==================== 技术文档模板 ====================
        templates['technical'] = DocumentTemplate(
            template_id='technical_v1',
            document_type='technical',
            display_name='技术文档',
            description='技术规格、接口文档、开发指南等',
            required_fields=[
                FieldRequirement(
                    field_name='文档标题',
                    field_type='text',
                    required=True,
                    description='技术文档的标题',
                    examples=['充电桩API接口文档', '充电桩通信协议说明']
                ),
                FieldRequirement(
                    field_name='技术概述',
                    field_type='text',
                    required=True,
                    description='技术的总体说明',
                    min_length=50,
                    examples=['本文档描述充电桩与后台系统的通信协议...']
                ),
                FieldRequirement(
                    field_name='详细说明',
                    field_type='text',
                    required=True,
                    description='详细的技术说明',
                    min_length=100
                )
            ],
            optional_fields=[
                FieldRequirement(
                    field_name='代码示例',
                    field_type='text',
                    required=False,
                    description='技术实现的代码示例'
                ),
                FieldRequirement(
                    field_name='参数说明',
                    field_type='list',
                    required=False,
                    description='参数列表和说明'
                ),
                FieldRequirement(
                    field_name='注意事项',
                    field_type='list',
                    required=False,
                    description='技术使用的注意事项'
                )
            ],
            structure_rules=[
                '技术术语应准确',
                '代码示例应可执行',
                '参数说明应完整'
            ]
        )
        
        # ==================== 通用文档模板 ====================
        templates['general'] = DocumentTemplate(
            template_id='general_v1',
            document_type='general',
            display_name='通用文档',
            description='不特定类型的一般文档',
            required_fields=[
                FieldRequirement(
                    field_name='标题',
                    field_type='text',
                    required=True,
                    description='文档标题',
                    min_length=2
                ),
                FieldRequirement(
                    field_name='内容',
                    field_type='text',
                    required=True,
                    description='文档主体内容',
                    min_length=50
                )
            ],
            optional_fields=[],
            structure_rules=[
                '内容应结构清晰',
                '段落分隔明确'
            ]
        )
        
        return templates
    
    async def validate(
        self,
        chunks: List[Dict[str, Any]],
        document_type: str
    ) -> Dict[str, Any]:
        """
        验证文档结构
        
        Args:
            chunks: 文档分块列表
            document_type: 文档类型
        
        Returns:
            验证结果
        """
        template = self.templates.get(document_type)
        
        if not template:
            return {
                'passed': True,
                'errors': [],
                'warnings': [f'文档类型 {document_type} 没有定义模板，跳过结构验证'],
                'missing_fields': []
            }
        
        # 合并所有chunk内容
        full_content = '\n'.join(chunk.get('content', '') for chunk in chunks)
        
        errors = []
        warnings = []
        missing_fields = []
        
        # 1. 验证必要字段
        for field_req in template.required_fields:
            field_found = self._check_field_presence(
                full_content,
                field_req
            )
            
            if not field_found:
                missing_fields.append(field_req.field_name)
                errors.append(f"缺少必要字段: {field_req.field_name} ({field_req.description})")
        
        # 2. 验证字段格式
        for field_req in template.required_fields + template.optional_fields:
            if self._check_field_presence(full_content, field_req):
                format_valid = self._validate_field_format(
                    full_content,
                    field_req
                )
                
                if not format_valid['valid']:
                    warnings.append(
                        f"字段 {field_req.field_name} 格式不符合要求: {format_valid['message']}"
                    )
        
        # 3. 验证结构规则
        for rule in template.structure_rules:
            rule_check = self._check_structure_rule(full_content, rule)
            if not rule_check['passed']:
                warnings.append(f"结构规则检查: {rule_check['message']}")
        
        passed = len(errors) == 0
        
        return {
            'passed': passed,
            'template': template.display_name,
            'errors': errors,
            'warnings': warnings,
            'missing_fields': missing_fields,
            'required_fields_count': len(template.required_fields),
            'found_fields_count': len(template.required_fields) - len(missing_fields)
        }
    
    def _check_field_presence(
        self,
        content: str,
        field_req: FieldRequirement
    ) -> bool:
        """检查字段是否存在"""
        # 简单实现：检查字段名是否出现
        field_patterns = [
            field_req.field_name,
            field_req.field_name.replace(' ', ''),
            field_req.field_name + ':',
            field_req.field_name + '：'
        ]
        
        return any(pattern in content for pattern in field_patterns)
    
    def _validate_field_format(
        self,
        content: str,
        field_req: FieldRequirement
    ) -> Dict[str, Any]:
        """验证字段格式"""
        # 简化实现
        if field_req.min_length:
            if len(content) < field_req.min_length:
                return {
                    'valid': False,
                    'message': f'内容长度不足{field_req.min_length}字符'
                }
        
        if field_req.validation_pattern:
            # 正则验证
            pass
        
        return {'valid': True, 'message': ''}
    
    def _check_structure_rule(
        self,
        content: str,
        rule: str
    ) -> Dict[str, Any]:
        """检查结构规则"""
        # 简化实现
        return {'passed': True, 'message': ''}
    
    def get_template(self, document_type: str) -> Optional[DocumentTemplate]:
        """获取文档模板"""
        return self.templates.get(document_type)
    
    def list_templates(self) -> List[DocumentTemplate]:
        """列出所有模板"""
        return list(self.templates.values())
