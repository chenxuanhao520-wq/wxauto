import os
import sys
import json
import time
import hashlib
import asyncio
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from difflib import SequenceMatcher

# 允许从项目根目录运行
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.mcp_platform.mcp_manager_v2 import get_mcp_manager

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# 质控配置
SUPPORTED_EXTS = {"pdf","doc","docx","ppt","pptx","xls","xlsx","txt","md","html","json","jpeg","jpg","png","bmp","gif","svg","webp","tiff"}
OCR_CONFIDENCE_THRESHOLD = 0.7  # OCR置信度阈值
SIMILARITY_THRESHOLD = 0.85  # 内容相似度阈值（去重）
ENABLE_REDACTION = True  # 是否启用脱敏

# 敏感信息正则
SENSITIVE_PATTERNS = {
    "phone": re.compile(r'1[3-9]\d{9}'),
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "id_card": re.compile(r'\b\d{17}[\dXx]\b'),
    "bank_card": re.compile(r'\b\d{16,19}\b'),
}


def sha256_file(path: Path) -> str:
	h = hashlib.sha256()
	with path.open("rb") as f:
		for chunk in iter(lambda: f.read(8192), b""):
			h.update(chunk)
	return h.hexdigest()


def ensure_dirs(base: Path) -> Dict[str, Path]:
	out = base / "output"
	(out / "markdown").mkdir(parents=True, exist_ok=True)
	(out / "text").mkdir(parents=True, exist_ok=True)
	(out / "logs").mkdir(parents=True, exist_ok=True)
	(out / "qc").mkdir(parents=True, exist_ok=True)
	return {
		"root": out,
		"md": out / "markdown",
		"txt": out / "text",
		"logs": out / "logs",
		"qc": out / "qc",
	}


def detect_sensitive_info(text: str) -> Dict[str, List[str]]:
	"""检测敏感信息"""
	hits = {}
	for name, pattern in SENSITIVE_PATTERNS.items():
		matches = pattern.findall(text)
		if matches:
			hits[name] = matches
	return hits


def redact_sensitive_info(text: str) -> Tuple[str, Dict[str, int]]:
	"""脱敏处理，返回脱敏后文本和命中统计"""
	redacted = text
	stats = {}
	
	for name, pattern in SENSITIVE_PATTERNS.items():
		matches = pattern.findall(redacted)
		if matches:
			stats[name] = len(matches)
			if name == "phone":
				redacted = pattern.sub(lambda m: m.group()[:3] + "****" + m.group()[-4:], redacted)
			elif name == "email":
				redacted = pattern.sub(lambda m: m.group().split('@')[0][:2] + "***@" + m.group().split('@')[1], redacted)
			elif name == "id_card":
				redacted = pattern.sub(lambda m: m.group()[:6] + "********" + m.group()[-4:], redacted)
			elif name == "bank_card":
				redacted = pattern.sub(lambda m: m.group()[:4] + "****" + m.group()[-4:], redacted)
	
	return redacted, stats


def content_similarity(text1: str, text2: str) -> float:
	"""计算内容相似度"""
	if not text1 or not text2:
		return 0.0
	# 取前1000字符计算相似度
	s1 = text1[:1000].strip()
	s2 = text2[:1000].strip()
	return SequenceMatcher(None, s1, s2).ratio()


class DuplicateChecker:
	"""重复检测器"""
	def __init__(self):
		self.seen_hashes: Set[str] = set()
		self.seen_contents: List[Tuple[str, str]] = []  # (file_path, content_preview)
	
	def is_duplicate(self, file_path: str, file_hash: str, content: str) -> Tuple[bool, str]:
		"""检查是否重复，返回(是否重复, 原因)"""
		# Hash重复
		if file_hash in self.seen_hashes:
			return True, f"文件Hash重复: {file_hash[:8]}"
		
		# 内容相似度检测
		content_preview = content[:1000] if content else ""
		for seen_path, seen_content in self.seen_contents:
			similarity = content_similarity(content_preview, seen_content)
			if similarity >= SIMILARITY_THRESHOLD:
				return True, f"内容相似度 {similarity:.2%} >= {SIMILARITY_THRESHOLD:.0%}，与 {Path(seen_path).name} 重复"
		
		# 记录
		self.seen_hashes.add(file_hash)
		if content_preview:
			self.seen_contents.append((file_path, content_preview))
		
		return False, ""


async def process_file(aiocr, file_path: Path, out_dirs: Dict[str, Path], run_id: str, dup_checker: DuplicateChecker) -> Dict[str, Any]:
	start = time.time()
	file_hash = sha256_file(file_path)
	ext = file_path.suffix.lower().lstrip('.')
	status = "ok"
	ocr_conf = None
	md_content = None
	text_content = None
	error = None
	qc_flags = []
	sensitive_hits = {}

	try:
		# 优先转 Markdown
		md_res = await aiocr.doc_to_markdown(str(file_path), filename=file_path.name, use_cache=True)
		if md_res.get("success"):
			md_content = md_res.get("content")
			# 兜底纯文本
			text_res = await aiocr.doc_recognition(str(file_path), filename=file_path.name, use_cache=True)
			if text_res.get("success"):
				text_content = text_res.get("content")
			else:
				text_content = md_content
		else:
			# 直接纯文本
			text_res = await aiocr.doc_recognition(str(file_path), filename=file_path.name, use_cache=True)
			if text_res.get("success"):
				text_content = text_res.get("content")
			else:
				raise RuntimeError(text_res.get("error") or "OCR失败")

		# 简单清洗（可扩展：页眉/页脚/水印/空行）
		def _clean(s: str) -> str:
			return '\n'.join([line.rstrip() for line in (s or "").splitlines() if line.strip()])

		md_content = _clean(md_content) if md_content else None
		text_content = _clean(text_content) if text_content else None

		# 重复检测
		is_dup, dup_reason = dup_checker.is_duplicate(str(file_path), file_hash, text_content or "")
		if is_dup:
			qc_flags.append(f"重复: {dup_reason}")
			status = "duplicate"
			logger.warning(f"⚠️ 重复文件: {file_path.name} - {dup_reason}")

		# 敏感信息检测与脱敏
		if ENABLE_REDACTION and text_content:
			sensitive_hits = detect_sensitive_info(text_content)
			if sensitive_hits:
				qc_flags.append(f"检测到敏感信息: {', '.join(sensitive_hits.keys())}")
				text_content, redact_stats = redact_sensitive_info(text_content)
				if md_content:
					md_content, _ = redact_sensitive_info(md_content)
				logger.info(f"🔒 脱敏: {file_path.name} - {redact_stats}")

		# 置信度（若云侧返回可解析metadata，这里简单占位）
		ocr_conf = 0.9 if (md_content or text_content) else 0.0
		
		# 置信度检查
		if ocr_conf < OCR_CONFIDENCE_THRESHOLD:
			qc_flags.append(f"OCR置信度过低: {ocr_conf:.2f} < {OCR_CONFIDENCE_THRESHOLD}")
			status = "need_review"

		# 写文件
		md_out = out_dirs["md"] / f"{file_path.stem}_{file_hash[:8]}.md"
		txt_out = out_dirs["txt"] / f"{file_path.stem}_{file_hash[:8]}.txt"
		if md_content and status != "duplicate":
			md_out.write_text(md_content, encoding="utf-8")
		if text_content and status != "duplicate":
			txt_out.write_text(text_content, encoding="utf-8")

		elapsed = time.time() - start
		return {
			"status": status,
			"source_path": str(file_path),
			"file_hash": file_hash,
			"format": ext,
			"ocr_confidence": ocr_conf,
			"qc_flags": qc_flags,
			"sensitive_hits": list(sensitive_hits.keys()) if sensitive_hits else [],
			"markdown": str(md_out) if md_content and status != "duplicate" else None,
			"text": str(txt_out) if text_content and status != "duplicate" else None,
			"run_id": run_id,
			"elapsed_sec": round(elapsed, 3),
		}

	except Exception as e:
		error = str(e)
		logger.error(f"❌ 处理失败: {file_path} - {error}")
		return {
			"status": "failed",
			"source_path": str(file_path),
			"file_hash": file_hash,
			"format": ext,
			"error": error,
			"run_id": run_id,
		}


async def main(input_dir: str, base_dir: str = "kb_materials"):
	base = ROOT / base_dir
	in_dir = base / "input"
	if input_dir:
		in_dir = Path(input_dir)

	out_dirs = ensure_dirs(base)
	run_id = str(int(time.time()))

	mcp = get_mcp_manager()
	aiocr = mcp.get_client("aiocr")
	dup_checker = DuplicateChecker()

	# 扫描文件（白名单过滤）
	files: List[Path] = []
	skipped = []
	for p in in_dir.rglob('*'):
		if p.is_file():
			ext = p.suffix.lower().lstrip('.')
			if ext in SUPPORTED_EXTS:
				files.append(p)
			else:
				skipped.append((str(p), f"不支持的格式: {ext}"))

	logger.info(f"📋 待处理文件数: {len(files)} | 跳过: {len(skipped)} | run_id={run_id}")
	if skipped:
		logger.warning(f"⚠️ 跳过文件示例: {skipped[:3]}")

	results: List[Dict[str, Any]] = []
	for p in files:
		res = await process_file(aiocr, p, out_dirs, run_id, dup_checker)
		results.append(res)
		await asyncio.sleep(0.5)

	# 汇总与QC
	ok = sum(1 for r in results if r.get("status") == "ok")
	failed = [r for r in results if r.get("status") == "failed"]
	need_review = [r for r in results if r.get("status") == "need_review"]
	duplicates = [r for r in results if r.get("status") == "duplicate"]
	with_sensitive = [r for r in results if r.get("sensitive_hits")]

	# 写输出
	(out_dirs["root"] / "meta.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in results), encoding="utf-8")
	if failed:
		(out_dirs["qc"] / "failed.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in failed), encoding="utf-8")
	if need_review:
		(out_dirs["qc"] / "need_review.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in need_review), encoding="utf-8")
	if duplicates:
		(out_dirs["qc"] / "duplicates.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in duplicates), encoding="utf-8")
	if skipped:
		(out_dirs["qc"] / "skipped.jsonl").write_text("\n".join(json.dumps({"path": p, "reason": r}, ensure_ascii=False) for p, r in skipped), encoding="utf-8")

	stats = {
		"run_id": run_id,
		"total": len(results),
		"ok": ok,
		"failed": len(failed),
		"need_review": len(need_review),
		"duplicates": len(duplicates),
		"with_sensitive_info": len(with_sensitive),
		"skipped": len(skipped),
	}
	(out_dirs["root"] / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
	
	logger.info(f"""
✅ 批处理完成
━━━━━━━━━━━━━━━━━━━━━━━━
  总数: {len(results)}
  成功: {ok}
  失败: {len(failed)}
  需复核: {len(need_review)}
  重复: {len(duplicates)}
  含敏感信息: {len(with_sensitive)}
  跳过: {len(skipped)}
━━━━━━━━━━━━━━━━━━━━━━━━
  产物目录: {out_dirs['root']}
""")


if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("--input", help="输入目录（默认 kb_materials/input）", default="")
	args = parser.parse_args()
	asyncio.run(main(args.input))
