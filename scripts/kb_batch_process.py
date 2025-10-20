import os
import sys
import json
import time
import hashlib
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

# 允许从项目根目录运行
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.mcp_platform.mcp_manager_v2 import get_mcp_manager

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SUPPORTED_EXTS = {"pdf","doc","docx","ppt","pptx","xls","xlsx","txt","md","html","json","jpeg","jpg","png","bmp","gif","svg","webp","tiff"}


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


async def process_file(aiocr, file_path: Path, out_dirs: Dict[str, Path], run_id: str) -> Dict[str, Any]:
	start = time.time()
	file_hash = sha256_file(file_path)
	ext = file_path.suffix.lower().lstrip('.')
	status = "ok"
	ocr_conf = None
	md_content = None
	text_content = None
	error = None

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

		# 置信度（若云侧返回可解析metadata，这里简单占位）
		ocr_conf = 0.9 if (md_content or text_content) else 0.0

		# 写文件
		md_out = out_dirs["md"] / f"{file_path.stem}_{file_hash[:8]}.md"
		txt_out = out_dirs["txt"] / f"{file_path.stem}_{file_hash[:8]}.txt"
		if md_content:
			md_out.write_text(md_content, encoding="utf-8")
		if text_content:
			txt_out.write_text(text_content, encoding="utf-8")

		elapsed = time.time() - start
		return {
			"status": status,
			"source_path": str(file_path),
			"file_hash": file_hash,
			"format": ext,
			"ocr_confidence": ocr_conf,
			"markdown": str(md_out) if md_content else None,
			"text": str(txt_out) if text_content else None,
			"run_id": run_id,
			"elapsed_sec": round(elapsed, 3),
		}

	except Exception as e:
		error = str(e)
		logger.error(f"处理失败: {file_path} - {error}")
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

	files: List[Path] = []
	for p in in_dir.rglob('*'):
		if p.is_file() and p.suffix.lower().lstrip('.') in SUPPORTED_EXTS:
			files.append(p)

	logger.info(f"待处理文件数: {len(files)} | run_id={run_id}")

	results: List[Dict[str, Any]] = []
	for p in files:
		res = await process_file(aiocr, p, out_dirs, run_id)
		results.append(res)
		await asyncio.sleep(0.5)

	# 汇总与QC
	ok = sum(1 for r in results if r.get("status") == "ok")
	failed = [r for r in results if r.get("status") == "failed"]
	need_review = [r for r in results if (r.get("ocr_confidence") or 0) < 0.7 and r.get("status") == "ok"]

	(out_dirs["root"] / "meta.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in results), encoding="utf-8")
	(out_dirs["qc"] / "failed.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in failed), encoding="utf-8")
	(out_dirs["qc"] / "need_review.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in need_review), encoding="utf-8")

	stats = {
		"run_id": run_id,
		"total": len(results),
		"ok": ok,
		"failed": len(failed),
		"need_review": len(need_review),
	}
	(out_dirs["root"] / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
	logger.info(f"完成：ok={ok} failed={len(failed)} need_review={len(need_review)} | 产物目录: {out_dirs['root']}")


if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("--input", help="输入目录（默认 kb_materials/input）", default="")
	args = parser.parse_args()
	asyncio.run(main(args.input))
