"""Environment and tool inventory shown on the Settings page."""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from . import anki, library
from ..core import MODELS, ROOT, SUITE, TOOLS, expand_path, load_config


def _dir_size(path: Path) -> str:
    if not path.exists():
        return ""
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    if total > 1_000_000_000:
        return f"{total / 1e9:.1f} GB"
    return f"{total / 1e6:.0f} MB"


def _find(*candidates: Path) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return None


def status() -> dict[str, Any]:
    cfg = load_config()
    anki_state = anki.status()
    zotero_path = library._db_source()
    anki_exe = _find(
        expand_path(cfg["system"].get("anki_exe", "")),
        TOOLS / "anki" / "anki.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Anki" / "anki.exe",
        Path("C:/Program Files/Anki/anki.exe"),
    )
    ffmpeg = _find(
        TOOLS / "ffmpeg" / "bin" / "ffmpeg.exe",
        TOOLS / "ffmpeg" / "ffmpeg.exe",
        Path(shutil.which("ffmpeg") or ""),
    )
    praat = _find(TOOLS / "praat" / "Praat.exe", TOOLS / "praat" / "praat.exe")
    vale = _find(TOOLS / "vale" / "vale.exe")
    espeak = _find(TOOLS / "espeak-ng" / "espeak-ng.exe")

    def python_module(name: str) -> bool:
        return importlib.util.find_spec(name) is not None

    rows = [
        {
            "id": "anki",
            "name": "Anki + AnkiConnect",
            "ok": anki_state["connected"],
            "detail": f"v{anki_state['version']}" if anki_state["connected"] else "未连接",
            "path": str(anki_exe) if anki_exe else "未安装",
            "hint": "点击“启动 Anki”，Prism 会加载本地 profile。",
        },
        {
            "id": "zotero",
            "name": "Zotero 文库",
            "ok": zotero_path is not None,
            "detail": f"{len(library.list_items(limit=10000))} 条文献" if zotero_path else "未找到",
            "path": str(zotero_path or cfg["zotero"]["db"]),
            "hint": "只读快照；不会修改你的 Zotero 数据。",
        },
        {
            "id": "kokoro",
            "name": "Kokoro 语音",
            "ok": python_module("kokoro") and python_module("soundfile"),
            "detail": "就绪" if python_module("kokoro") else "缺少依赖",
            "path": str(Path(sys.executable)),
            "hint": "首次合成会下载约 300 MB 模型到 E 盘。",
        },
        {
            "id": "whisper",
            "name": "faster-whisper",
            "ok": python_module("faster_whisper"),
            "detail": cfg["speech"]["whisper_model"],
            "path": str(Path(sys.executable)),
            "hint": "首次分析会下载 base.en 模型。",
        },
        {
            "id": "praat",
            "name": "Praat",
            "ok": python_module("parselmouth"),
            "detail": "parselmouth" if python_module("parselmouth") else "缺少依赖",
            "path": str(praat or "内置 parselmouth"),
            "hint": "声学指标在应用内计算，Praat 桌面版用于看曲线。",
        },
        {
            "id": "ffmpeg",
            "name": "FFmpeg",
            "ok": ffmpeg is not None,
            "detail": "就绪" if ffmpeg else "未安装",
            "path": str(ffmpeg or "未安装"),
            "hint": "用于把手机录音转成 wav。",
        },
        {
            "id": "vale",
            "name": "Vale",
            "ok": vale is not None,
            "detail": "就绪" if vale else "使用内置检查",
            "path": str(vale or "内置规则"),
            "hint": "Vale 未安装时，写作检查会退回内置规则。",
        },
        {
            "id": "espeak",
            "name": "espeak-ng",
            "ok": espeak is not None,
            "detail": "就绪" if espeak else "可选",
            "path": str(espeak or "未安装"),
            "hint": "Kokoro 遇到生词时需要；普通英文通常可直接合成。",
        },
    ]
    return {
        "rows": rows,
        "suite": str(SUITE),
        "models": _dir_size(MODELS),
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "project": str(ROOT),
    }


def open_target(kind: str) -> dict[str, Any]:
    import subprocess

    targets: dict[str, Path] = {
        "suite": SUITE,
        "project": ROOT,
        "data": ROOT / "data",
        "reports": ROOT / "data" / "reports",
        "audio": ROOT / "data" / "audio",
        "models": MODELS,
        "tools": TOOLS,
    }
    path = targets.get(kind)
    if path is None or not path.exists():
        raise FileNotFoundError(f"目录不存在：{kind}")
    subprocess.Popen(["explorer", str(path)])
    return {"opened": str(path)}


def reveal(path: str) -> dict[str, Any]:
    import os
    import subprocess

    target = Path(path).resolve()
    allowed = (Path("E:/XuLab in Westlake University/Zotero/storage").resolve(), ROOT.resolve(), SUITE.resolve())
    if not any(str(target).startswith(str(root)) for root in allowed):
        raise PermissionError("只能打开 Zotero 存储或 Prism 工作区内的文件。")
    if not target.exists():
        raise FileNotFoundError(str(target))
    if target.is_file():
        os.startfile(str(target))
        return {"opened": str(target)}
    subprocess.Popen(["explorer", str(target)])
    return {"revealed": str(target)}


def open_url(url: str) -> dict[str, Any]:
    import subprocess

    allowed = ("zotero://", "https://doi.org/", "https://youglish.com/", "https://www.zotero.org/")
    if not url.startswith(allowed):
        raise PermissionError("不允许打开这个地址。")
    subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)
    return {"opened": url}
