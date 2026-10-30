"""Shared paths, config, module loading and background jobs for Prism."""
from __future__ import annotations

import importlib.util
import json
import os
import queue
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
DATA = ROOT / "data"
AUDIO = DATA / "audio"
REPORTS = DATA / "reports"
CONFIG_PATH = ROOT / "config.json"
SUITE = Path(os.environ.get("LUMEN_SUITE", "E:/LumenSuite"))
TOOLS = SUITE / "tools"
MODELS = SUITE / "models"

for directory in (DATA, AUDIO, REPORTS, TOOLS, MODELS):
    directory.mkdir(parents=True, exist_ok=True)

# Keep every download inside the suite folder, even when Prism is launched
# from Explorer without the .bat wrapper.
os.environ.setdefault("HF_HOME", str(MODELS / "hf"))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("XDG_CACHE_HOME", str(SUITE / "cache"))
os.environ.setdefault("TORCH_HOME", str(MODELS / "torch"))
os.environ.setdefault("PIP_CACHE_DIR", str(SUITE / "cache" / "pip"))
os.environ.setdefault("UV_CACHE_DIR", str(SUITE / "cache" / "uv"))

DEFAULT_CONFIG: dict[str, Any] = {
    "app": {"port": 7317, "name": "Prism"},
    "anki": {
        "url": "http://127.0.0.1:8765",
        "decks": {
            "vocab": "PaperToTalk::Vocab",
            "phrases": "PaperToTalk::Phrases",
            "listening": "PaperToTalk::Listening",
        },
        "models": {"vocab": "AE Vocab", "phrase": "AE Phrase", "listening": "AE Subs"},
    },
    "zotero": {"db": "~/Zotero/zotero.sqlite"},
    "system": {"anki_exe": str(TOOLS / "anki" / "anki.exe")},
    "speech": {"kokoro_voice": "af_heart", "whisper_model": "base.en"},
}


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(DEFAULT_CONFIG))
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    for key, value in cfg.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_modules: dict[str, Any] = {}
_import_lock = threading.Lock()


def get_module(name: str):
    with _import_lock:
        if name in _modules:
            return _modules[name]
        paths = {
            "speak": ROOT / "speaking" / "speak.py",
            "zotero": ROOT / "vocab" / "zotero_to_anki.py",
            "anki": ROOT / "vocab" / "anki_setup.py",
        }
        module = _load_module(name, paths[name])
        _modules[name] = module
        return module


def expand_path(value: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(value)))


class JobManager:
    """Tiny in-process job runner so the UI can poll long model downloads."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._events: queue.Queue[tuple[str, Callable[[dict], None]]] = queue.Queue()
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        while True:
            job_id, fn = self._events.get()
            job = self._jobs[job_id]
            job["status"] = "running"
            job["started"] = time.time()
            try:
                job["result"] = fn(lambda message, pct=None: self._progress(job_id, message, pct))
                job["status"] = "done"
            except Exception as exc:  # surface the message in the UI
                job["status"] = "error"
                job["error"] = f"{type(exc).__name__}: {exc}"
            finally:
                job["finished"] = time.time()

    def _progress(self, job_id: str, message: str, pct: float | None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job["message"] = message
                if pct is not None:
                    job["progress"] = max(0.0, min(1.0, pct))

    def submit(self, kind: str, fn: Callable[[Callable], Any]) -> str:
        job_id = uuid.uuid4().hex[:12]
        self._jobs[job_id] = {
            "id": job_id,
            "kind": kind,
            "status": "queued",
            "progress": 0.0,
            "message": "Queued",
            "result": None,
            "error": None,
            "created": time.time(),
        }
        self._events.put((job_id, fn))
        return job_id

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None


jobs = JobManager()
