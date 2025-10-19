"""
三大触发器: 售前、售后、客户开发
基于LLM的智能表单提取和回复生成
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .types import TriggerOutput, TriggerLabel

logger = logging.getLogger(__name__)


# ==================== LLM 提示词模板 ====================

PROMPT_PRE_SALES = """你是一位经验丰富的售前工程师。请从以下客户对话中提取"询价要素表"，并输出JSON格式的结构化数据。

**要提取的字段：**
- 功率(kW): 充电桩功率
- 枪型: 如 GB/T, CCS, CHAdeMO, Type2
- 输入电压: 如 380V三相, 220V单相
- 配电: 如 三相/单相/容量
- 附件: 如 立柱/线缆/刷卡/云平台
- 交付地: 客户所在地区
- 期望交期: 交付时间要求
- 数量: 采购数量
- 发票要求: 如 普票/专票/不开票

**任务：**
1. 提取上述字段，未提及的字段标记为 null
2. 生成"澄清问题清单"（3-8条），针对缺失或不明确的信息
3. 草拟一段中文回复，包含：
   - 感谢客户咨询
   - 复述已提供的核心参数
   - 提出澄清问题
   - 可选方案说明
   - 建议的下一步行动

**原始对话：**
{text}

**请按以下JSON格式输出：**
```json
{{
  "form": {{
    "功率_kW": null,
    "枪型": null,
    "输入电压": null,
    "配电": null,
    "附件": null,
    "交付地": null,
    "期望交期": null,
    "数量": null,
    "发票要求": null
  }},
  "clarification_questions": [
    "问题1",
    "问题2",
    "..."
  ],
  "reply_draft": "感谢您的咨询！根据您提供的信息... [澄清问题] ... [可选方案] ... [下一步]"
}}
```
"""

PROMPT_AFTER_SALES = """你是一位专业的售后工程师。请从以下客户对话中识别并提取"工单信息"，输出JSON格式的结构化数据。

**要提取的字段：**
- 设备序列号: 设备SN或编号
- 固件版本: 软件/固件版本号
- 运行环境: 如 温度/电压/通信状态
- 故障现象: 具体故障描述
- 发生时间: 故障开始时间
- 频率: 偶发/频繁/持续
- 报警码: 如 E103, F201 等
- 已尝试步骤: 客户已执行的操作
- 现场照片数量: 客户提供的图片数
- 紧急程度: S(高)/M(中)/L(低)

**任务：**
1. 提取上述字段，未提及的字段标记为 null
2. 给出分级排查步骤：
   - S1远程: 可远程指导的步骤
   - S2现场: 需现场处理的步骤
3. 草拟标准沟通话术（简短中文）：
   - 确认故障信息
   - 安抚客户情绪
   - 说明排查计划
   - 预估解决时间

**原始对话：**
{text}

**请按以下JSON格式输出：**
```json
{{
  "form": {{
    "设备序列号": null,
    "固件版本": null,
    "运行环境": null,
    "故障现象": null,
    "发生时间": null,
    "频率": null,
    "报警码": null,
    "已尝试步骤": null,
    "现场照片数量": 0,
    "紧急程度": "M"
  }},
  "troubleshooting": {{
    "S1_remote": ["步骤1", "步骤2", "..."],
    "S2_onsite": ["步骤1", "步骤2", "..."]
  }},
  "reply_draft": "感谢您的反馈！我们已收到您的工单... [确认信息] ... [排查计划] ... [预估时间]"
}}
```
"""

PROMPT_BIZDEV = """你是一位资深的渠道拓展经理。请从以下对话中判断线索级别并提取"商务开发信息"，输出JSON格式的结构化数据。

**要提取的字段：**
- 线索级别: A(高)/B(中)/C(低)
- 对方角色: 如 直客/集成商/代理商/经销商
- 涉及区域: 目标市场区域
- 合作诉求: 具体合作意向
- 是否需资质材料: true/false
- 建议下一步: 如 15分钟内电话/24小时后跟进
- 资料包清单: 需要准备的材料

**任务：**
1. 提取上述字段，未提及的字段标记为 null
2. 判断线索质量并给出级别(A/B/C)
3. 生成两段中文脚本：
   - 首次触达: 初次联系的话术
   - 次日跟进: 第二天跟进的话术

**原始对话：**
{text}

**请按以下JSON格式输出：**
```json
{{
  "form": {{
    "线索级别": "B",
    "对方角色": null,
    "涉及区域": null,
    "合作诉求": null,
    "是否需资质材料": false,
    "建议下一步": null,
    "资料包清单": []
  }},
  "scripts": {{
    "first_contact": "您好！感谢您对我们产品的关注... [建立信任] ... [了解需求] ... [下一步]",
    "follow_up": "您好！继续我们昨天的话题... [回顾需求] ... [提供方案] ... [促成合作]"
  }},
  "reply_draft": "您好！非常高兴收到您的合作意向... [首次触达内容]"
}}
```
"""


# ==================== 触发器类 ====================

class TriggerEngine:
    """触发引擎 - 调用LLM生成结构化输出"""
    
    def __init__(self, llm_client=None):
        """
        初始化触发引擎
        
        Args:
            llm_client: LLM客户端,需要实现 generate(prompt) -> str 方法
        """
        self.llm_client = llm_client
        logger.info("触发引擎初始化")
    
    async def trigger_pre_sales(
        self, 
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TriggerOutput:
        """
        触发售前场景
        
        Args:
            text: 对话文本
            context: 上下文信息(可选)
        
        Returns:
            TriggerOutput对象
        """
        logger.info("触发售前场景")
        
        # 构建提示词
        prompt = PROMPT_PRE_SALES.format(text=text)
        
        # 调用LLM
        if self.llm_client:
            response = await self.llm_client.generate(prompt)
            result = self._parse_llm_response(response)
        else:
            # 无LLM时返回模拟数据
            result = self._mock_pre_sales_output(text)
        
        # 构建输出
        output = TriggerOutput(
            form=result.get('form', {}),
            reply_draft=result.get('reply_draft', ''),
            labels=[TriggerLabel.PRE_SALES]
        )
        
        logger.info(f"售前触发完成, 表单字段数: {len(output.form)}")
        return output
    
    async def trigger_after_sales(
        self, 
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TriggerOutput:
        """
        触发售后场景
        
        Args:
            text: 对话文本
            context: 上下文信息(可选)
        
        Returns:
            TriggerOutput对象
        """
        logger.info("触发售后场景")
        
        # 构建提示词
        prompt = PROMPT_AFTER_SALES.format(text=text)
        
        # 调用LLM
        if self.llm_client:
            response = await self.llm_client.generate(prompt)
            result = self._parse_llm_response(response)
        else:
            # 无LLM时返回模拟数据
            result = self._mock_after_sales_output(text)
        
        # 构建输出
        output = TriggerOutput(
            form=result.get('form', {}),
            reply_draft=result.get('reply_draft', ''),
            labels=[TriggerLabel.AFTER_SALES]
        )
        
        logger.info(f"售后触发完成, 表单字段数: {len(output.form)}")
        return output
    
    async def trigger_bizdev(
        self, 
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TriggerOutput:
        """
        触发客户开发场景
        
        Args:
            text: 对话文本
            context: 上下文信息(可选)
        
        Returns:
            TriggerOutput对象
        """
        logger.info("触发客户开发场景")
        
        # 构建提示词
        prompt = PROMPT_BIZDEV.format(text=text)
        
        # 调用LLM
        if self.llm_client:
            response = await self.llm_client.generate(prompt)
            result = self._parse_llm_response(response)
        else:
            # 无LLM时返回模拟数据
            result = self._mock_bizdev_output(text)
        
        # 构建输出
        output = TriggerOutput(
            form=result.get('form', {}),
            reply_draft=result.get('reply_draft', ''),
            labels=[TriggerLabel.BIZ_DEV]
        )
        
        logger.info(f"客户开发触发完成, 表单字段数: {len(output.form)}")
        return output
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM返回的JSON响应
        
        Args:
            response: LLM响应文本
        
        Returns:
            解析后的字典
        """
        try:
            # 提取JSON部分(去除markdown代码块)
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.rfind('```')
                json_str = response[json_start:json_end].strip()
            elif '```' in response:
                json_start = response.find('```') + 3
                json_end = response.rfind('```')
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            # 解析JSON
            result = json.loads(json_str)
            return result
        
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            return {
                'form': {},
                'reply_draft': response  # 降级返回原文
            }
    
    # ==================== 模拟输出(用于测试) ====================
    
    def _mock_pre_sales_output(self, text: str) -> Dict[str, Any]:
        """模拟售前输出"""
        return {
            'form': {
                '功率_kW': 320 if '320' in text else None,
                '枪型': '双枪' if '双枪' in text else None,
                '输入电压': '380V三相',
                '配电': None,
                '附件': None,
                '交付地': None,
                '期望交期': None,
                '数量': None,
                '发票要求': '专票' if '专票' in text else None
            },
            'clarification_questions': [
                '请问您需要的充电桩安装在什么场景？(公共/私人/商业)',
                '配电容量是否已确认？',
                '是否需要配套立柱和线缆？',
                '交付地址在哪个城市？'
            ],
            'reply_draft': '感谢您的咨询！根据您提供的信息,您需要320kW双枪充电桩,开具专票。为了给您准确报价,请您补充以下信息:1)安装场景 2)配电容量 3)是否需要立柱线缆 4)交付地址。我们会在收到信息后第一时间为您提供详细方案和报价。'
        }
    
    def _mock_after_sales_output(self, text: str) -> Dict[str, Any]:
        """模拟售后输出"""
        return {
            'form': {
                '设备序列号': None,
                '固件版本': None,
                '运行环境': None,
                '故障现象': '报警码E103,无法充电' if 'E103' in text else None,
                '发生时间': None,
                '频率': '持续',
                '报警码': 'E103' if 'E103' in text else None,
                '已尝试步骤': '已重启' if '重启' in text else None,
                '现场照片数量': 0,
                '紧急程度': 'S'
            },
            'troubleshooting': {
                'S1_remote': [
                    '检查设备显示屏报警码详情',
                    '查看通信指示灯状态',
                    '确认输入电压是否正常',
                    '尝试软重启(长按5秒)'
                ],
                'S2_onsite': [
                    '检查主控板连接线',
                    '测量输入输出电压',
                    '更换通信模块',
                    '升级固件版本'
                ]
            },
            'reply_draft': '感谢您的反馈！我们已收到您关于报警码E103的工单。根据初步判断,可能是通信模块故障。请先尝试以下步骤:1)检查设备显示屏详细信息 2)确认输入电压 3)软重启设备。如问题未解决,我们将安排工程师2小时内与您联系进行远程排查,必要时48小时内上门处理。'
        }
    
    def _mock_bizdev_output(self, text: str) -> Dict[str, Any]:
        """模拟客户开发输出"""
        return {
            'form': {
                '线索级别': 'B',
                '对方角色': '代理商' if '代理' in text else None,
                '涉及区域': None,
                '合作诉求': '了解代理政策和返点' if '返点' in text else None,
                '是否需资质材料': True,
                '建议下一步': '15分钟内电话联系',
                '资料包清单': ['公司简介', '产品手册', '代理政策', '成功案例']
            },
            'scripts': {
                'first_contact': '您好!感谢您对我们充电桩产品的关注。我是负责渠道合作的XX,很高兴有机会与您交流合作事宜。我们目前在全国范围内寻找优质代理伙伴,提供有竞争力的代理政策和全方位支持。方便的话,我想了解一下您所在的区域和具体合作意向,以便为您定制最合适的方案。',
                'follow_up': '您好!继续我们昨天关于代理合作的话题。根据您的需求,我已准备好相关资料包,包括代理政策、返点机制、区域保护等详细信息。同时,我们近期在您所在区域有成功案例可以分享。您看今天下午方便沟通吗?我可以详细介绍我们的支持体系。'
            },
            'reply_draft': '您好!非常高兴收到您的合作意向。我们公司是国内领先的充电桩制造商,目前正在全国范围内招募优质代理商。针对您提到的代理和返点政策,我会尽快整理详细资料发送给您。同时,我想进一步了解您所在的区域和目标客户群体,以便为您制定最合适的合作方案。稍后我会电话与您联系,期待我们的合作!'
        }


# ==================== 默认实例 ====================

default_trigger_engine = TriggerEngine()

