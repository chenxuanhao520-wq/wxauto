# 企业版功能归档

本目录包含暂时归档的企业版功能模块，这些模块将在 v3.0 企业版中重新启用。

## 归档模块

### 1. adaptive_learning/
**功能**：自适应学习与个性化  
**状态**：功能未完全成熟，暂不适合专业版  
**计划**：v3.0 企业版重新启用  
**包含**：
- `user_profiler.py` - 用户画像
- `personalized_prompt.py` - 个性化提示词
- `continuous_learner.py` - 持续学习
- `history_importer.py` - 历史导入

### 2. integrations/
**功能**：多维表格集成（飞书/钉钉）  
**状态**：集成不稳定，API频繁变更  
**计划**：v3.0 企业版作为插件提供  
**包含**：
- `feishu_bitable.py` - 飞书多维表格
- `dingtalk_bitable.py` - 钉钉多维表格

### 3. multimodal/
**功能**：多模态处理（图片/语音）  
**状态**：已被 MCP AIOCR 替代  
**计划**：废弃或整合到 MCP 中  
**包含**：
- `image_handler.py` - 图片处理
- `audio_handler.py` - 音频处理

## 归档原因

1. **产品定位收缩**：v2.0 专注于专业版（Mid-Market），企业版功能暂缓
2. **技术成熟度**：部分模块尚未达到生产就绪状态
3. **维护成本**：减少主分支复杂度，聚焦核心价值

## 恢复方式

如需恢复某个模块到主分支：
```bash
# 示例：恢复 adaptive_learning
cp -r archive/enterprise_features/adaptive_learning modules/
git add modules/adaptive_learning
git commit -m "feat: 恢复自适应学习模块"
```

## 相关文档

- 重构方案：📋系统性重构方案_v1.0.md
- 产品线规划：Section 1.2
- 企业版路线图：待定

---
**归档日期**: 2025-10-20  
**归档版本**: v2.0-phase1  
**负责人**: AI Architect

