# 📘 知识库素材准备与质控 SOP（MCP + Cursor）

本SOP面向“将原始文档（含图片/PDF/Office等）加工为高质量可检索知识库条目”的端到端流程，依托 Cursor 调用 MCP（AIOCR + Sequential Thinking）与本地 RAG 组件。目标：高可用、高一致、可追溯。

---

## 1. 输入与范围
- 输入：文件夹中的原始素材（PDF、DOCX、PPTX、图片、扫描件等）
- 输出：
  - Markdown 文档（结构化、可阅读）
  - 纯文本内容（用于嵌入/检索）
  - 元数据（来源、时间、版本、置信度、脱敏标记）
  - 质控清单（通过/告警/失败）

## 2. 工具与组件
- MCP 服务：
  - aiocr：`doc_recognition`（纯文本）、`doc_to_markdown`（结构保留）
  - sequential_thinking：用于流程策略与异常解释（可选）
- 本地组件：
  - `modules/mcp_platform/mcp_manager_v2.py`（统一管理服务与缓存）
  - `kb_service`（入库脚本；若无则以导出文件替代）
  - `config.yaml`（OCR、嵌入、RAG 阈值等）

## 3. 质量控制（QC）策略
- 类型白名单：仅允许常见办公与图片格式；其它格式标为“审阅”
- 去重策略：同名/同Hash/同首段落85%相似度视为重复
- OCR 置信度阈值：低于阈值（如 <0.7）进入“需复核”
- 敏感信息脱敏：手机号/邮箱/身份证/地址，采用正则+字典表规则
- 页级失败兜底：`doc_to_markdown` 失败→回退 `doc_recognition`；再失败→标记失败，保存原文件路径与日志
- 缓存策略：AIOCR 结果根据文件 Hash + 文件名缓存（TTL 1h-24h 按需配置）

## 4. 处理流程
1) 扫描输入目录，过滤白名单格式
2) 计算文件Hash，命中缓存则读取缓存
3) 优先 `doc_to_markdown`→成功即产出 Markdown；失败回退 `doc_recognition`
4) 清洗：
   - 页眉/页脚/目录/水印裁剪
   - 正则清除重复空行、乱码、扫描噪点
   - 中英混排空格修正
5) 脱敏与审计：标记敏感项，输出 `redact=true/false` 与 `sensitive_hits`
6) 切块：按标题/段落/长度（如 800-1200 tokens）切分
7) 生成元数据：`source_path`、`file_hash`、`processed_at`、`format`、`ocr_confidence`、`redact`、`pipeline_version`
8) 产物落盘：`output/markdown/`、`output/text/`、`output/meta.jsonl`、`output/qc_report.csv`
9) 可选入库：调用 `kb_service` 将文本与元数据入向量库

## 5. 目录结构（建议）
```
kb_materials/
  input/
  output/
    markdown/
    text/
    logs/
    qc/
  tmp/
```

## 6. 配置关键点（对齐当前代码）
- OCR：`config.yaml` 中 `ocr.timeout_ms`、`provider_order`；MCP 端在 `config/mcp_config.yaml` 配置 aiocr TTL/重试
- 嵌入：`embedding.model=bge-m3`，`rag.top_k=4`、`min_confidence=0.75`
- 速率限制：批量时每 0.5s 间隔，避免触发云侧限流

## 7. 失败与复核
- 失败文件：写入 `output/qc/failed.jsonl`（含错误信息）
- 低置信度：写入 `output/qc/need_review.jsonl`，并保留原图页引用
- 人工复核入口：按 `qc_report.csv` 的 `status in (need_review, failed)` 优先处理

## 8. 审计与追溯
- 每次运行生成 `run_id`（timestamp+随机串）
- 产物与日志包含 `run_id`，支持回放
- 输出 `stats.json`：总数/成功/失败/复核/平均耗时/缓存命中率

## 9. 安全与合规
- 所有密钥从环境变量注入（参见 `scripts/validate_env.py`）
- 严禁将原始敏感数据上传到外部，无需 OCR 的可本地化处理

## 10. 上线检查表
- 环境变量已设置（QWEN_API_KEY 等）
- `config/mcp_config.yaml` 中 aiocr 服务已启用且 TTL 合理
- `kb_materials/input` 中素材准备完毕
- 输出目录有写权限

---

本SOP可配合后续批处理脚本自动执行，保留所有质控与追溯产物，以便快速定位问题并复跑。
