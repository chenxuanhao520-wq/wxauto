# 更新日志

## v2.0.0 - 2025-10-16

### 🎉 重大更新：完成 Phase 2-4

这是一个重大版本更新，完成了原计划的 Phase 2、3、4 所有功能。系统现已具备完整的 AI 客服能力。

### ✨ 新增功能

#### 1. AI 网关（Phase 3）
- ✅ **OpenAI 集成**：支持 gpt-4o-mini 及其他模型
- ✅ **DeepSeek 备用**：主备切换，自动降级
- ✅ **Token 计量**：准确统计输入/输出 token
- ✅ **超时处理**：30 秒超时，自动重试
- ✅ **错误恢复**：所有提供商失败后回退到模板响应

**文件**：
- `ai_gateway/types.py` - 数据类型定义
- `ai_gateway/base.py` - 基类抽象
- `ai_gateway/llm_provider.py` - OpenAI/DeepSeek 实现
- `ai_gateway/gateway.py` - 网关主逻辑

#### 2. RAG 检索器（Phase 2）
- ✅ **BM25 检索**：基于关键词的语义检索
- ✅ **知识库管理**：支持从数据库加载/保存
- ✅ **置信度计算**：TF-IDF 简化评分
- ✅ **证据引用**：格式化输出，包含文档名、版本、章节

**文件**：
- `rag/retriever.py` - 完整实现（替换原有桩代码）

#### 3. 知识库管理工具（Phase 4）
- ✅ **添加文档**：支持批量添加知识块
- ✅ **列出文档**：查看所有已添加的文档
- ✅ **测试检索**：实时测试检索效果
- ✅ **示例数据**：内置 3 份示例文档（安装/故障/维护）

**文件**：
- `kb_manager.py` - 知识库管理命令行工具

**使用方法**：
```bash
# 添加示例文档
python kb_manager.py --action add

# 列出所有文档
python kb_manager.py --action list

# 测试检索
python kb_manager.py --action search --query "如何安装设备"
```

#### 4. 运维工具（Phase 4）
- ✅ **健康检查**：检查数据库、AI网关、知识库、日志状态
- ✅ **性能报告**：生成统计报告（总请求、分支分布、AI提供商）
- ✅ **日志轮转**：自动归档超过阈值的日志文件
- ✅ **数据清理**：清理过期会话和旧消息

**文件**：
- `ops_tools.py` - 运维命令行工具

**使用方法**：
```bash
# 健康检查
python ops_tools.py health

# 性能报告（最近7天）
python ops_tools.py report --days 7

# 日志轮转
python ops_tools.py rotate --max-log-size 50

# 清理90天前数据
python ops_tools.py cleanup --days 90
```

#### 5. 配置文件完善
- ✅ `.env.example` - 环境变量配置示例（已创建但被忽略）
- ✅ `.gitignore` - Git 忽略规则更新

### 🔧 改进优化

#### main.py 集成
- 集成 AI 网关，替换原有桩响应
- 自动加载知识库
- 增强错误处理，AI 失败时回退到模板
- 保持向后兼容（无 API Key 时仍可运行）

#### 测试增强
- 新增 `tests/test_ai_gateway.py`（8 个测试）
- 支持真实 API 测试（需设置 OPENAI_API_KEY）
- 支持桩测试（无 API Key 时）

#### 文档更新
- README.md 全面更新
  - 添加知识库初始化步骤
  - 添加运维工具使用说明
  - 更新环境变量配置
  - 更新开发路线图（标记已完成）
- quickstart.py 更新
  - 增加知识库初始化步骤
  - 更新后续步骤说明

### 📊 统计数据

**代码量**：
- 新增代码：约 1500 行
- AI 网关：~600 行
- RAG 更新：~200 行
- 知识库管理：~200 行
- 运维工具：~300 行
- 测试代码：~150 行

**测试覆盖**：
- AI 网关测试：8 个
- 原有测试：36 个（全部通过）
- 总计：44 个测试

**功能完成度**：
- Phase 0: ✅ 100%
- Phase 1: ✅ 100%
- Phase 2: ✅ 100%（BM25 检索）
- Phase 3: ✅ 100%（AI 网关）
- Phase 4: ✅ 95%（运维工具完成，Web 后台待定）

### 🚀 使用指南

#### 快速开始（完整流程）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行快速启动（自动初始化）
python quickstart.py

# 3. 初始化知识库
python kb_manager.py --action add

# 4. 设置环境变量
export OPENAI_API_KEY=sk-your-key-here

# 5. 运行主程序
python main.py
```

#### 真实环境部署

```bash
# Windows 环境
set USE_FAKE_ADAPTER=false
set OPENAI_API_KEY=sk-xxxxx
set DEEPSEEK_API_KEY=sk-xxxxx  # 可选

# 运行
python main.py
```

### ⚠️ 注意事项

1. **API Key 必需**：
   - 需要 OpenAI API Key 才能使用真实 AI 功能
   - 未设置时会回退到模板响应
   - DeepSeek API Key 可选（作为备用）

2. **知识库初始化**：
   - 首次运行建议执行 `python kb_manager.py --action add`
   - 或运行 `python quickstart.py` 自动初始化

3. **向后兼容**：
   - 所有新功能都是可选的
   - 未配置 AI 时系统仍可正常运行（使用模板）
   - 知识库为空时使用模拟数据

### 🐛 已知问题

1. **.env.example 被忽略**：
   - 文件已创建但被 .gitignore 忽略
   - 需要手动创建或参考文档配置环境变量

2. **main.py 仍然超长**：
   - 当前 600+ 行（超过 400 行规范）
   - 建议后续重构时拆分

3. **向量检索未实现**：
   - 当前仅支持 BM25 关键词检索
   - 向量嵌入和重排列入未来增强计划

### 🔮 未来计划

- [ ] 向量嵌入检索（提升检索精度）
- [ ] 会话历史管理（多轮对话）
- [ ] 图片/语音识别（OCR/ASR）
- [ ] 多维表格对接（飞书/钉钉）
- [ ] Web 管理后台
- [ ] 重构 main.py（拆分 handler）

---

## v1.0.0 - 2025-10-16

### 初始版本（Phase 0-1）

- ✅ 项目脚手架
- ✅ 数据库设计与实现
- ✅ 微信适配器（真实 + 测试）
- ✅ 消息监听与发送
- ✅ @识别、去重、频控
- ✅ ACK 确认机制
- ✅ 会话管理（TTL 15分钟）
- ✅ 置信度分流
- ✅ 管理指令
- ✅ 禁答域保护
- ✅ 全量日志落库
- ✅ CSV 导出功能
- ✅ 36 个单元测试（100% 通过）

详见 `DELIVERY_SUMMARY.md`

