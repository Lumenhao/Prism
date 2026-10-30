"""Prism local API + static workbench."""
from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .core import AUDIO, DATA, ROOT, jobs, load_config, save_config
from .services import anki, dashboard, library, speech, tools, writing

APP = FastAPI(title="Prism", version="0.3.1")
WEB = Path(__file__).resolve().parent / "web"
SCRIPTS = DATA / "scripts"
SCRIPTS.mkdir(parents=True, exist_ok=True)


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-.")
    return cleaned or "script.md"


def _scripts() -> list[dict[str, Any]]:
    rows = []
    sources = [(ROOT / "speaking" / "samples", "sample"), (SCRIPTS, "custom")]
    for folder, kind in sources:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            if path.name == "youglish.md":
                continue
            text = path.read_text(encoding="utf-8-sig")
            title = path.stem
            match = re.search(r"^title:\s*(.+)$", text, re.M)
            if match:
                title = match.group(1).strip()
            rows.append(
                {
                    "name": path.name,
                    "title": title,
                    "kind": kind,
                    "words": len(re.sub(r"^---.*?---", "", text, flags=re.S).split()),
                    "updated": time.strftime("%Y-%m-%d", time.localtime(path.stat().st_mtime)),
                }
            )
    return rows


def _script_path(name: str) -> Path:
    name = _safe_name(name)
    custom = SCRIPTS / name
    if custom.exists():
        return custom
    sample = ROOT / "speaking" / "samples" / name
    if sample.exists():
        return sample
    raise HTTPException(404, "脚本不存在")


@APP.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@APP.get("/api/overview")
def overview() -> dict[str, Any]:
    return dashboard.overview()


@APP.get("/api/library")
def library_list(q: str = "", limit: int = Query(80, ge=1, le=500)) -> dict[str, Any]:
    items = library.list_items(q, limit)
    return {"items": items, "total": len(items)}


@APP.get("/api/library/stats")
def library_stats() -> dict[str, Any]:
    return library.stats()


@APP.get("/api/library/{item_id}")
def library_detail(item_id: int) -> dict[str, Any]:
    detail = library.item_detail(item_id)
    if detail is None:
        raise HTTPException(404, "文献不存在")
    return detail


@APP.post("/api/library/refresh")
def library_refresh() -> dict[str, Any]:
    path = library.refresh_snapshot()
    return {"ok": True, "snapshot": str(path), "items": len(library.list_items(limit=10000))}


@APP.get("/api/anki/status")
def anki_status() -> dict[str, Any]:
    return anki.status()


@APP.post("/api/anki/launch")
def anki_launch() -> dict[str, Any]:
    try:
        result = anki.launch()
        anki.wait_ready(40)
        result["connected"] = True
        return result
    except anki.AnkiError as exc:
        raise HTTPException(503, str(exc)) from exc


@APP.post("/api/anki/quit")
def anki_quit() -> dict[str, Any]:
    return anki.quit_app()


@APP.post("/api/anki/setup")
def anki_setup() -> dict[str, str]:
    def task(progress):
        result = anki.setup(progress)
        dashboard.record("anki", "初始化牌组与句型卡", result)
        return result

    return {"jobId": jobs.submit("anki-setup", task)}


@APP.get("/api/anki/preview")
def anki_preview(include_untranslated: bool = False) -> dict[str, Any]:
    try:
        notes = anki.preview(include_untranslated, 200)
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
    return {"notes": notes, "count": len(notes)}


@APP.post("/api/anki/export")
def anki_export(payload: dict[str, Any] = Body(default={})) -> dict[str, str]:
    include = bool(payload.get("includeUntranslated"))
    update = bool(payload.get("update"))

    def task(progress):
        result = anki.export(include, update, progress)
        dashboard.record("vocab", "导出 Zotero 标注到 Anki", result)
        return result

    return {"jobId": jobs.submit("anki-export", task)}


@APP.get("/api/scripts")
def script_list() -> dict[str, Any]:
    return {"scripts": _scripts()}


@APP.get("/api/script")
def script_get(name: str = "sample_talk.md") -> dict[str, Any]:
    path = _script_path(name)
    return {"name": path.name, "text": path.read_text(encoding="utf-8-sig")}


@APP.put("/api/script")
def script_save(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    name = _safe_name(payload.get("name") or "working.md")
    text = payload.get("text", "")
    if len(text) > 200_000:
        raise HTTPException(413, "脚本过长")
    target = SCRIPTS / name
    target.write_text(text, encoding="utf-8")
    return {"saved": str(target), "name": target.name}


@APP.post("/api/speak/tts")
def speak_tts(payload: dict[str, Any] = Body(...)) -> dict[str, str]:
    text = payload.get("text", "")
    voice = payload.get("voice")
    speed = float(payload.get("speed", 0.95))
    lang = payload.get("lang", "a")

    def task(progress):
        result = speech.tts(text, voice, speed, lang, progress)
        dashboard.record("speak", "生成示范音", {"file": result["file"], "duration": result["duration"]})
        return result

    return {"jobId": jobs.submit("tts", task)}


@APP.get("/api/speak/links")
def speak_links(text: str, accent: str = "us", all: bool = False) -> dict[str, Any]:
    try:
        rows = speech.links(text, accent, all)
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
    return {"links": rows, "count": len(rows)}


@APP.post("/api/speak/analyze")
async def speak_analyze(
    audio: UploadFile = File(...),
    text: str = Form(...),
    model: str = Form("base.en"),
) -> dict[str, str]:
    suffix = Path(audio.filename or "take.wav").suffix.lower() or ".wav"
    if suffix not in {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}:
        raise HTTPException(415, "不支持的音频格式")
    name = f"take-{time.strftime('%Y%m%d-%H%M%S')}{suffix}"
    target = AUDIO / name
    with target.open("wb") as handle:
        shutil.copyfileobj(audio.file, handle)

    def task(progress):
        result = speech.analyze(target, text, model, progress)
        dashboard.record(
            "speak",
            "口语分析",
            {"wer": result["wer"], "wpm": result["wpm"], "file": name},
        )
        return result

    return {"jobId": jobs.submit("analyze", task), "audio": f"/media/audio/{name}"}


@APP.get("/api/speak/report")
def speak_report() -> dict[str, Any]:
    report = speech.latest_report()
    return report or {}


@APP.get("/api/speak/pronunciation")
def pronunciation() -> dict[str, Any]:
    return {"terms": speech.pronunciation()}


@APP.get("/api/write/phrases")
def write_phrases() -> dict[str, Any]:
    rows = writing.phrases()
    sections = sorted({row["section"] for row in rows})
    return {"phrases": rows, "sections": sections}


@APP.get("/api/write/suggest")
def write_suggest(q: str = "", limit: int = 6) -> dict[str, Any]:
    return {"phrases": writing.suggest(q, limit)}


@APP.post("/api/write/check")
def write_check(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    result = writing.check(payload.get("text", ""))
    dashboard.record("write", "写作检查", result.get("stats", {}))
    return result


@APP.get("/api/tools/status")
def tools_status() -> dict[str, Any]:
    return tools.status()


@APP.get("/api/settings")
def settings_get() -> dict[str, Any]:
    return load_config()


@APP.put("/api/settings")
def settings_put(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    cfg = load_config()
    anki_url = str(payload.get("ankiUrl", cfg["anki"]["url"])).strip()
    if not anki_url.startswith("http"):
        raise HTTPException(400, "AnkiConnect 地址必须以 http 开头")
    cfg["anki"]["url"] = anki_url.rstrip("/")
    cfg["system"]["anki_exe"] = str(payload.get("ankiExe", cfg["system"]["anki_exe"]))
    cfg["zotero"]["db"] = str(payload.get("zoteroDb", cfg["zotero"]["db"]))
    cfg["speech"]["kokoro_voice"] = str(payload.get("voice", cfg["speech"]["kokoro_voice"]))
    cfg["speech"]["whisper_model"] = str(payload.get("whisper", cfg["speech"]["whisper_model"]))
    save_config(cfg)
    return {"saved": True, "config": cfg}


@APP.post("/api/open")
def open_path(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    try:
        return tools.open_target(str(payload.get("kind", "suite")))
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@APP.post("/api/reveal")
def reveal(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    try:
        return tools.reveal(str(payload.get("path", "")))
    except (FileNotFoundError, PermissionError) as exc:
        raise HTTPException(400, str(exc)) from exc


@APP.post("/api/open-url")
def open_url(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    try:
        return tools.open_url(str(payload.get("url", "")))
    except PermissionError as exc:
        raise HTTPException(400, str(exc)) from exc


@APP.get("/api/jobs/{job_id}")
def job_get(job_id: str) -> JSONResponse:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "任务不存在")
    return JSONResponse(job)


@APP.get("/api/reports")
def reports() -> dict[str, Any]:
    rows = []
    for path in sorted((DATA / "reports").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append(
            {
                "file": path.name,
                "generated": data.get("generated"),
                "wer": data.get("wer"),
                "wpm": data.get("wpm"),
                "duration": data.get("duration"),
            }
        )
    return {"reports": rows[:20]}


@APP.get("/media/audio/{name}")
def media_audio(name: str):
    path = AUDIO / _safe_name(name)
    if not path.exists():
        raise HTTPException(404, "音频不存在")
    return FileResponse(path)


@APP.get("/")
def index():
    return FileResponse(WEB / "index.html")


APP.mount("/static", StaticFiles(directory=WEB), name="static")
