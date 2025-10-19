# 📘 ETL流程和文档规范完整方案

## 🎯 设计目标

建立严格的文档ETL流程和结构化规范，确保：
1. **格式统一**：不同类型文档遵循统一标准
2. **必要字段完整**：关键信息不缺失
3. **质量可控**：自动检测和修复
4. **便于检索**：优化大模型检索效果

---

## 🔄 完整ETL流程

### 流程图

```
文档上传
    ↓
┌──────────────────────────────────────┐
│ Phase 1: Extract（提取）              │
│ • 解析文档（PDF/DOCX/Excel等）        │
│ • 提取原始内容                        │
│ • 生成初始chunks                      │
└────────────┬─────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│ Phase 2: Validate Structure（结构验证）│
│ • 检查文档类型                        │
│ • 验证必要字段                        │
│ • 检查格式约束                        │
└────────────┬─────────────────────────┘
             ↓
         是否通过？
         ├─ NO → 生成反馈 → 自动修复？
         │                  ├─ YES → Phase 3
         │                  └─ NO → 返回错误
         └─ YES ↓
┌──────────────────────────────────────┐
│ Phase 3: Transform（转换）            │
│ • 内容清洗                            │
│ • 格式标准化                          │
│ • 结构化提取                          │
│ • LLM优化（可选）                     │
└────────────┬─────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│ Phase 4: Quality Check（质量检查）    │
│ • 多维度质量评估                      │
│ • 信息完整性检查                      │
│ • 可读性分析                          │
└────────────┬─────────────────────────┘
             ↓
         质量合格？
         ├─ NO → 自动修复？
         │       ├─ YES → LLM辅助修复 → Phase 5
         │       └─ NO → 返回质量报告
         └─ YES ↓
┌──────────────────────────────────────┐
│ Phase 5: Duplicate Check（重复检测）  │
│ • 精确重复（哈希）                    │
│ • 语义重复（gensim）                  │
│ • 结构重复（difflib）                 │
└────────────┬─────────────────────────┘
             ↓
         有重复？
         ├─ YES → 返回重复报告 → 人工决策
         └─ NO ↓
┌──────────────────────────────────────┐
│ Phase 6: Load（加载）                 │
│ • 生成标准JSON                        │
│ • 添加元数据                          │
│ • 入库知识库                          │
└──────────────────────────────────────┘
```

---

## 📋 文档类型和模板

### 1. 产品信息文档

#### 必要字段 ⭐⭐⭐⭐⭐

| 字段名 | 类型 | 说明 | 示例 | 验证规则 |
|--------|------|------|------|---------|
| 产品名称 | text | 产品正式名称 | "7kW交流充电桩" | 2-100字符 |
| 产品型号 | text | 产品型号编号 | "AC-7KW-001" | 字母数字组合 |
| 技术规格 | list | 主要技术参数 | ["额定功率: 7kW", "输入电压: 220V"] | 至少3项 |
| 功能描述 | text | 主要功能特性 | "支持APP远程监控..." | 50-500字符 |
| 适用场景 | list | 应用场景 | ["家用充电", "商业充电站"] | 至少1项 |

#### 可选字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 产品图片 | image | 产品外观图片 |
| 价格信息 | text | 价格范围 |
| 相关链接 | link | 产品详情页 |

#### 标准格式示例

```markdown
# 7kW交流充电桩

**产品型号**: AC-7KW-001

## 技术规格
- 额定功率: 7kW
- 输入电压: 220V AC ±10%
- 输出电压: 200-750V DC
- 充电接口: 国标GB/T
- 防护等级: IP54
- 工作温度: -20℃ ~ 50℃

## 功能描述
支持APP远程监控、自动充电保护、智能计费、故障自诊断等功能。

## 适用场景
- 家用充电（私人车库）
- 商业充电站（公共停车场）
- 企业停车场（员工充电）

## 价格信息
市场参考价: ¥998 - ¥1,998

## 相关链接
- 产品详情: https://example.com/product/ac-7kw
- 用户手册: https://example.com/manual/ac-7kw
```

---

### 2. FAQ文档

#### 必要字段 ⭐⭐⭐⭐⭐

| 字段名 | 类型 | 说明 | 示例 | 验证规则 |
|--------|------|------|------|---------|
| 问题（问法） | text | 用户常见问题 | "充电桩如何安装？" | 5-200字符，疑问句 |
| 简洁答案 | text | 1-2句话回答 | "需由专业人员安装..." | 10-200字符 |

#### 可选字段（强烈推荐）

| 字段名 | 类型 | 说明 | 重要性 |
|--------|------|------|--------|
| 问法变体 | list | 不同的问法 | ⭐⭐⭐⭐⭐ |
| 详细答案 | text | 详细解答 | ⭐⭐⭐⭐ |
| 操作步骤 | list | 具体步骤 | ⭐⭐⭐⭐⭐ |
| 相关链接 | link | 参考文档链接 | ⭐⭐⭐⭐ |
| 相关FAQ | list | 关联问题 | ⭐⭐⭐ |

#### 标准格式示例

```markdown
## FAQ: 充电桩安装

### 问题
充电桩如何安装？

### 问法变体
- 充电桩怎么装？
- 充电桩安装步骤是什么？
- 如何安装充电桩？
- 充电桩安装流程

### 简洁答案
充电桩需由专业人员安装，包括固定底座、连接电源线、通电测试三个主要步骤。

### 详细答案
充电桩安装是一个专业操作，需要电工资质。安装过程包括现场勘查、底座固定、电源连接、功能测试等环节。建议联系我们的专业安装团队，确保安装安全和设备正常运行。

### 操作步骤
1. 现场勘查，确认安装位置和电源条件
2. 关闭主电源，确保安全
3. 使用膨胀螺栓固定充电桩底座
4. 连接电源线到配电箱（需专业电工）
5. 接地线连接
6. 通电测试，检查指示灯和功能
7. 安装验收，确认正常运行

### 相关链接
- [安装视频教程](https://example.com/video/install)
- [安装规范文档](https://example.com/docs/install-spec)

### 相关FAQ
- 充电桩安装需要什么条件？
- 充电桩安装费用多少？
- 充电桩安装后如何验收？

### 标签
安装、充电桩、操作指南
```

---

### 3. 操作文档

#### 必要字段 ⭐⭐⭐⭐⭐

| 字段名 | 类型 | 说明 | 示例 | 验证规则 |
|--------|------|------|------|---------|
| 操作标题 | text | 操作名称 | "充电桩安装指南" | 5-100字符 |
| 前置条件 | list | 操作前准备 | ["电源准备", "工具准备"] | 至少1项 |
| 操作步骤 | list | 详细步骤 | ["1. 关闭电源", "2. 固定底座"] | 至少2步，必须编号 |
| 预期结果 | text | 操作完成后结果 | "指示灯正常闪烁" | 10-200字符 |

#### 可选字段（强烈推荐）

| 字段名 | 类型 | 说明 | 重要性 |
|--------|------|------|--------|
| 操作截图 | image | 清晰截图/示意图 | ⭐⭐⭐⭐⭐ |
| 注意事项 | list | 安全警告等 | ⭐⭐⭐⭐⭐ |
| 常见问题 | list | 操作中可能遇到的问题 | ⭐⭐⭐⭐ |
| 视频链接 | link | 操作视频教程 | ⭐⭐⭐⭐ |

#### 标准格式示例

```markdown
# 充电桩安装操作指南

## 前置条件
- ✅ 已准备220V电源（±10%）
- ✅ 已准备工具：十字螺丝刀、电笔、膨胀螺栓M6×4
- ✅ 已阅读安全操作规范
- ✅ 环境温度0-40℃，通风良好

## 操作步骤

### 1. 关闭主电源
![关闭电源](images/step1_power_off.jpg)
- 找到配电箱主开关
- 确认指示灯熄灭
- 使用电笔确认无电

### 2. 固定充电桩底座
![固定底座](images/step2_mount.jpg)
- 在墙面标记安装位置（距地面1.2-1.5米）
- 使用冲击钻打孔（深度60mm）
- 插入膨胀螺栓
- 固定充电桩底座，确保水平

### 3. 连接电源线
![连接电源](images/step3_wiring.jpg)
- 按照颜色连接：火线（红）、零线（蓝）、地线（黄绿）
- 使用绝缘胶带包裹接头
- 固定线路，避免悬空

### 4. 通电测试
![通电测试](images/step4_test.jpg)
- 合上主电源开关
- 观察充电桩指示灯（绿灯闪烁为正常）
- 使用测试卡测试充电功能

## 预期结果
✅ 充电桩指示灯绿灯闪烁
✅ 使用测试卡可正常充电
✅ 无异常声音或气味
✅ 触摸外壳无明显发热

## 注意事项
⚠️ **禁止带电操作**
⚠️ 必须由持证电工进行电源连接
⚠️ 安装前务必检查电源规格
⚠️ 安装完成后进行完整功能测试

## 常见问题

### Q: 指示灯不亮怎么办？
A: 检查电源连接是否正确，确认主开关已打开

### Q: 充电测试失败？
A: 检查充电接口是否插紧，确认车辆电池管理系统正常

## 视频教程
🎥 [充电桩安装完整视频](https://example.com/video/install-guide)

## 相关文档
- [充电桩技术规格](doc://product-spec)
- [安全操作规范](doc://safety-guide)
- [验收标准](doc://acceptance-criteria)
```

---

## 📊 文档验证规则

### 产品信息文档验证

```python
# 验证规则
validation_rules = {
    'product_info': {
        'required_fields': {
            '产品名称': {
                'type': 'text',
                'min_length': 2,
                'max_length': 100,
                'pattern': None
            },
            '产品型号': {
                'type': 'text',
                'pattern': r'^[A-Z0-9\-]+$',
                'example': 'AC-7KW-001'
            },
            '技术规格': {
                'type': 'list',
                'min_items': 3,
                'item_pattern': r'.+[：:].+',  # 必须包含参数名和值
                'examples': ['额定功率: 7kW', '输入电压: 220V']
            },
            '功能描述': {
                'type': 'text',
                'min_length': 50,
                'max_length': 500
            },
            '适用场景': {
                'type': 'list',
                'min_items': 1
            }
        },
        'structure_rules': [
            '产品名称应出现在文档开头',
            '技术规格应以列表形式呈现',
            '每个技术参数应包含名称和数值单位'
        ]
    }
}

# 验证示例
def validate_product_info(content):
    errors = []
    warnings = []
    
    # 检查产品名称
    if '产品名称' not in content:
        errors.append("缺少必要字段: 产品名称")
    
    # 检查技术规格
    specs = extract_specifications(content)
    if len(specs) < 3:
        errors.append(f"技术规格不足3项（当前: {len(specs)}）")
    
    # 检查每个规格是否包含单位
    for spec in specs:
        if not re.search(r'\d+\s*(kW|V|A|℃|mm)', spec):
            warnings.append(f"技术规格缺少单位: {spec}")
    
    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }
```

### FAQ文档验证

```python
# 验证规则
validation_rules = {
    'faq': {
        'required_fields': {
            '问题': {
                'type': 'text',
                'min_length': 5,
                'max_length': 200,
                'must_end_with': ['？', '?'],  # 必须是疑问句
                'examples': ['充电桩如何安装？']
            },
            '简洁答案': {
                'type': 'text',
                'min_length': 10,
                'max_length': 100,  # 强制简洁
                'preferred_length': 50
            }
        },
        'recommended_fields': {
            '操作步骤': {
                'type': 'list',
                'importance': 'high',
                'format': 'numbered',  # 必须带编号
                'examples': ['1. 关闭电源', '2. 固定底座']
            },
            '相关链接': {
                'type': 'link',
                'importance': 'high',
                'format': 'url',
                'validation': 'must_be_valid_url'
            }
        },
        'structure_rules': [
            '问题必须以疑问词或？结尾',
            '简洁答案应控制在50字以内',
            '如有操作步骤，必须使用数字编号（1. 2. 3.）',
            '相关链接必须可访问'
        ]
    }
}

# 验证示例
def validate_faq(content):
    errors = []
    warnings = []
    
    # 1. 检查问题格式
    question = extract_question(content)
    if not question:
        errors.append("缺少必要字段: 问题")
    elif not question.endswith(('？', '?')):
        errors.append("问题必须以疑问号结尾")
    
    # 2. 检查简洁答案
    short_answer = extract_short_answer(content)
    if not short_answer:
        errors.append("缺少必要字段: 简洁答案")
    elif len(short_answer) > 100:
        warnings.append(f"简洁答案过长（{len(short_answer)}字符），建议控制在50字以内")
    
    # 3. 检查操作步骤格式
    steps = extract_steps(content)
    if steps:
        for step in steps:
            if not re.match(r'^\d+[\.、]', step):
                warnings.append(f"操作步骤缺少编号: {step[:20]}...")
    else:
        warnings.append("建议添加操作步骤（如适用）")
    
    # 4. 检查相关链接
    links = extract_links(content)
    if not links:
        warnings.append("建议添加相关链接或操作指南")
    
    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }
```

### 操作文档验证

```python
# 验证规则
validation_rules = {
    'operation': {
        'required_fields': {
            '操作标题': {'type': 'text'},
            '前置条件': {
                'type': 'list',
                'min_items': 1,
                'examples': ['电源准备', '工具准备']
            },
            '操作步骤': {
                'type': 'list',
                'min_items': 2,
                'format': 'numbered',  # 必须编号
                'must_have_images': False  # 如果True，强制要求每步有图
            },
            '预期结果': {
                'type': 'text',
                'min_length': 10
            }
        },
        'recommended_fields': {
            '操作截图': {
                'importance': 'critical',  # 操作文档强烈建议有截图
                'quality': 'clear',  # 必须清晰
                'annotations': 'required'  # 应有标注
            },
            '注意事项': {
                'importance': 'high',
                'highlight': True  # 应醒目显示
            }
        },
        'structure_rules': [
            '操作步骤必须使用数字编号（1. 2. 3.）',
            '每个步骤应简洁明确（建议20-50字）',
            '如有截图，应清晰标注关键区域',
            '注意事项应使用⚠️或其他醒目标记',
            '前置条件应完整列出',
            '预期结果应可验证'
        ]
    }
}

# 验证示例
def validate_operation(content):
    errors = []
    warnings = []
    
    # 1. 检查操作步骤
    steps = extract_numbered_steps(content)
    if len(steps) < 2:
        errors.append(f"操作步骤不足2步（当前: {len(steps)}）")
    
    # 2. 检查步骤格式
    for i, step in enumerate(steps, 1):
        if not step.startswith(f"{i}."):
            errors.append(f"步骤{i}编号不正确")
        
        if len(step) < 10:
            warnings.append(f"步骤{i}描述过于简单")
        elif len(step) > 200:
            warnings.append(f"步骤{i}描述过长，建议拆分")
    
    # 3. 检查截图
    screenshots = extract_screenshots(content)
    if len(screenshots) == 0:
        warnings.append("⚠️ 操作文档强烈建议配图，当前未检测到截图")
    elif len(screenshots) < len(steps):
        warnings.append(f"截图数量({len(screenshots)})少于步骤数({len(steps)})，建议每步配图")
    
    # 4. 检查注意事项
    notes = extract_notes(content)
    if len(notes) == 0:
        warnings.append("建议添加注意事项或安全警告")
    
    # 5. 检查前置条件
    prerequisites = extract_prerequisites(content)
    if len(prerequisites) == 0:
        errors.append("缺少前置条件说明")
    
    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'suggestions': [
            '每个操作步骤配一张清晰截图' if len(screenshots) < len(steps) else None,
            '为关键操作添加视频教程链接'
        ]
    }
```

---

## 🚀 ETL处理示例

### 示例1: 产品信息文档

**输入文档**（原始PDF/DOCX）：
```
7kW交流充电桩

这个产品很不错的，就是那种可以充电的桩子，嗯...

规格：
7kW
220V

功能：能充电

使用：家里用
```

**ETL处理过程**：

```python
# Phase 1: Extract（提取）
extracted = {
    'content': '原始内容...',
    'chunks': [...]
}

# Phase 2: Validate Structure（结构验证）
validation_result = {
    'passed': False,
    'errors': [
        '缺少必要字段: 产品型号',
        '技术规格不足3项（当前: 2）',
        '功能描述过于简单（当前: 4字符，要求: 50字符）'
    ],
    'warnings': [
        '技术规格缺少单位说明',
        '建议补充适用场景的详细说明'
    ],
    'missing_fields': ['产品型号', '适用场景详细说明']
}

# Phase 3: Auto Fix（自动修复）
# 调用大模型补充缺失信息
llm_prompt = """
请补充以下产品信息文档的缺失内容：

原始内容：
7kW交流充电桩
规格：7kW, 220V
功能：能充电
使用：家里用

缺少的必要字段：
1. 产品型号（格式：字母数字组合，如AC-7KW-001）
2. 详细的技术规格（至少3项，需包含单位）
3. 详细的功能描述（至少50字）
4. 适用场景的详细说明

要求：
- 根据"7kW交流充电桩"这个产品名称
- 补充合理的产品型号
- 完善技术规格（功率、电压、接口、防护等级、工作温度等）
- 详细描述功能特性
- 说明适用场景

请输出标准格式的完整产品信息文档。
"""

# LLM返回
llm_fixed_content = """
# 7kW交流充电桩

**产品型号**: AC-7KW-001

## 技术规格
- 额定功率: 7kW
- 输入电压: 220V AC ±10%
- 输出电压: 200-750V DC
- 充电接口: 国标GB/T
- 防护等级: IP54
- 工作温度: -20℃ ~ 50℃

## 功能描述
支持APP远程监控、自动充电保护、智能计费、故障自诊断、充电预约、电量统计等功能。

## 适用场景
- 家用充电（私人车库、别墅）
- 商业充电站（公共停车场、购物中心）
- 企业停车场（员工充电、车队管理）
"""

# Phase 4: Quality Check（质量检查）
quality_result = {
    'passed': True,
    'quality_score': 0.88,
    'issues': []
}

# Phase 5: Duplicate Check（重复检测）
duplicate_result = {
    'has_duplicates': False
}

# Phase 6: Load（加载）
final_chunk = {
    'chunk_id': 'doc_abc123_chunk_001',
    'document_type': 'product_info',
    'content': '产品: 7kW交流充电桩\n型号: AC-7KW-001\n规格: 额定功率: 7kW; 输入电压: 220V AC...',
    'structured_data': {
        'product_name': '7kW交流充电桩',
        'product_model': 'AC-7KW-001',
        'specifications': ['额定功率: 7kW', '输入电压: 220V AC ±10%', ...],
        'features': '支持APP远程监控、自动充电保护...',
        'usage_scenarios': ['家用充电', '商业充电站', '企业停车场']
    },
    'metadata': {
        'etl_processed': True,
        'auto_fixed': True,
        'llm_enhanced': True,
        'quality_score': 0.88
    }
}
```

**ETL成本**：
- 规则验证: 0.1秒
- LLM修复: 3秒，¥0.001
- 总计: 3.1秒，¥0.001

---

### 示例2: FAQ文档

**输入文档**（低质量）：
```
充电桩咋装？
找人装呗
```

**ETL处理**：

```python
# Phase 2: Validate Structure
validation_result = {
    'passed': False,
    'errors': [
        '问题格式不规范（使用了口语化表达"咋"）',
        '简洁答案过于简单（4字符，要求: 10字符）',
        '缺少操作步骤',
        '缺少相关链接'
    ]
}

# Phase 3: Auto Fix（LLM修复）
llm_prompt = """
请将以下低质量FAQ改写为标准格式：

原始内容：
Q: 充电桩咋装？
A: 找人装呗

要求：
1. 问题使用规范语言（避免口语化）
2. 提供详细的简洁答案（50字左右）
3. 添加具体的操作步骤
4. 添加相关链接建议

请按照标准FAQ格式输出。
"""

# LLM返回（标准格式）
llm_fixed_content = """
## FAQ: 充电桩安装

### 问题
充电桩如何安装？

### 问法变体
- 充电桩怎么装？
- 充电桩安装步骤是什么？
- 如何正确安装充电桩？

### 简洁答案
充电桩需由具备电工资质的专业人员安装，包括现场勘查、底座固定、电源连接、功能测试等步骤，建议联系官方安装服务。

### 操作步骤
1. 现场勘查，确认安装位置和电源条件
2. 关闭主电源，确保操作安全
3. 使用膨胀螺栓固定充电桩底座
4. 连接电源线到配电箱（需持证电工操作）
5. 接地线连接
6. 通电测试，检查功能正常
7. 安装验收

### 相关链接
- [安装视频教程](doc://install-video)
- [安装规范文档](doc://install-spec)

### 相关FAQ
- 充电桩安装需要什么条件？
- 充电桩安装费用多少？
"""

# 质量提升
质量分数: 0.3 → 0.90 (提升200%)
```

---

## 📊 统一输出格式

### 知识库标准JSON格式

```json
{
    "chunk_id": "doc_abc123_chunk_001",
    "document_id": "doc_abc123",
    "document_type": "faq",
    
    "content": "问题: 充电桩如何安装？\n答案: 充电桩需由专业人员安装...\n步骤: 1. 现场勘查; 2. 关闭电源...",
    
    "structured_data": {
        "type": "faq",
        "question": "充电桩如何安装？",
        "question_variations": ["充电桩怎么装？", "如何正确安装充电桩？"],
        "short_answer": "充电桩需由具备电工资质的专业人员安装...",
        "detailed_answer": "充电桩安装是一个专业操作...",
        "steps": [
            "现场勘查，确认安装位置和电源条件",
            "关闭主电源，确保操作安全",
            "..."
        ],
        "related_links": [
            "doc://install-video",
            "doc://install-spec"
        ],
        "related_faqs": [
            "充电桩安装需要什么条件？",
            "充电桩安装费用多少？"
        ]
    },
    
    "keywords": ["充电桩", "安装", "操作步骤", "专业人员"],
    "entities": ["7kW", "220V", "电工资质"],
    
    "quality_score": 0.90,
    "quality_checks": {
        "structure_validation": "passed",
        "content_quality": 0.90,
        "format_consistency": "passed",
        "duplicate_check": "passed"
    },
    
    "metadata": {
        "etl_processed": true,
        "auto_fixed": true,
        "llm_enhanced": true,
        "fixes_applied": ["补充问法变体", "详细化答案", "添加操作步骤"],
        "created_at": "2025-01-19T10:00:00",
        "last_updated": "2025-01-19T10:00:00",
        "version": "1.0"
    },
    
    "retrieval_optimized": {
        "primary_keywords": ["充电桩", "安装"],
        "secondary_keywords": ["专业", "电工", "步骤"],
        "search_hints": ["安装", "怎么装", "如何安装"],
        "token_count": 150
    }
}
```

---

## 🎯 反馈机制

### 质量不合格反馈示例

```json
{
    "document_id": "doc_xyz789",
    "validation_status": "failed",
    "overall_score": 0.65,
    
    "issues": [
        {
            "issue_id": "missing_field_001",
            "severity": "critical",
            "field": "产品型号",
            "message": "缺少必要字段: 产品型号",
            "suggestion": "请补充产品型号（格式：字母数字组合，如AC-7KW-001）",
            "auto_fixable": true,
            "llm_can_help": true
        },
        {
            "issue_id": "quality_low_002",
            "severity": "high",
            "field": "功能描述",
            "message": "功能描述过于简单（4字符，要求: 50字符）",
            "suggestion": "请详细描述产品功能特性，建议包含：远程监控、充电保护、智能计费等",
            "auto_fixable": true,
            "llm_can_help": true
        },
        {
            "issue_id": "format_003",
            "severity": "medium",
            "field": "技术规格",
            "message": "技术规格缺少单位说明",
            "suggestion": "每个技术参数应包含单位（如：7kW、220V、IP54）",
            "auto_fixable": true,
            "llm_can_help": false
        }
    ],
    
    "fix_options": [
        {
            "option": "auto_fix_with_llm",
            "description": "使用大模型自动补充缺失信息",
            "estimated_cost": "¥0.001",
            "estimated_time": "3-5秒",
            "confidence": 0.85,
            "requires_review": false
        },
        {
            "option": "auto_fix_with_rules",
            "description": "使用规则引擎自动修复格式问题",
            "estimated_cost": "¥0",
            "estimated_time": "0.5秒",
            "confidence": 0.95,
            "requires_review": false
        },
        {
            "option": "manual_fix",
            "description": "人工修复",
            "estimated_cost": "人工成本",
            "estimated_time": "5-10分钟",
            "confidence": 1.0,
            "requires_review": true
        }
    ],
    
    "recommended_action": "auto_fix_with_llm",
    
    "feedback_message": """
❌ 文档质量验证失败（分数: 0.65/1.00）

发现 3 个问题：

1. 🔴 Critical - 缺少必要字段: 产品型号
   建议: 请补充产品型号（格式：字母数字组合，如AC-7KW-001）
   [可自动修复]

2. 🟠 High - 功能描述过于简单（4字符，要求: 50字符）
   建议: 请详细描述产品功能特性
   [可自动修复]

3. 🟡 Medium - 技术规格缺少单位说明
   建议: 每个技术参数应包含单位（如：7kW、220V）
   [可自动修复]

推荐操作：
✅ 使用大模型自动修复（预计3-5秒，成本¥0.001）
   或
📝 人工修改后重新上传
    """
}
```

---

## 💡 总结

### ETL流程特点

✅ **6个阶段严格把关**：
1. Extract - 多格式解析（pandas + Parser）
2. Validate Structure - 必要字段验证
3. Transform - 清洗和标准化
4. Quality Check - 质量评估
5. Duplicate Check - 重复检测（difflib + gensim）
6. Load - 统一格式输出

✅ **智能反馈机制**：
- 详细的问题报告
- 严重级别分类
- 修复建议
- 多种修复选项

✅ **格式约束严格**：
- 产品信息：5个必要字段
- FAQ：问法+简洁答案（强制）+ 步骤/链接（推荐）
- 操作文档：步骤编号+截图（强烈推荐）+注意事项

✅ **统一输出格式**：
- 标准JSON结构
- 结构化数据 + 原始内容
- 元数据完整
- 适配检索优化

---

**这是一个业界顶级的ETL和文档规范方案！** 🚀
