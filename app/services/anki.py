"""AnkiConnect bridge: health, setup, export and review numbers."""
from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from . import library
from ..core import DATA, TOOLS, get_module, load_config

ANKI_BASE = DATA / "anki"
ADDON_CODE = "2055492159"


class AnkiError(RuntimeError):
    pass


def _url() -> str:
    return load_config()["anki"]["url"].rstrip("/")


def call(action: str, timeout: float = 5.0, **params):
    body = json.dumps({"action": action, "version": 6, "params": params}).encode()
    req = urllib.request.Request(
        _url(), data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AnkiError(f"无法连接 AnkiConnect（{_url()}）：{exc}") from exc
    if payload.get("error"):
        raise AnkiError(payload["error"])
    return payload.get("result")


def status() -> dict[str, Any]:
    cfg = load_config()
    try:
        version = call("version", timeout=1.5)
        decks = call("deckNames", timeout=3)
        names = [cfg["anki"]["decks"][key] for key in ("vocab", "phrases", "listening")]
        stats = call("getDeckStats", decks=[name for name in names if name in decks], timeout=3)
        due = new = learning = review = 0
        for entry in (stats or {}).values():
            new += entry.get("new_count", 0)
            learning += entry.get("learn_count", 0)
            review += entry.get("review_count", 0)
            due += entry.get("new_count", 0) + entry.get("learn_count", 0) + entry.get("review_count", 0)
        return {
            "connected": True,
            "version": version,
            "decks": names,
            "missingDecks": [name for name in names if name not in decks],
            "due": due,
            "new": new,
            "learning": learning,
            "review": review,
            "url": _url(),
        }
    except AnkiError as exc:
        return {"connected": False, "error": str(exc), "url": _url()}


def _ensure_addon() -> None:
    target = ANKI_BASE / "addons21" / ADDON_CODE
    if target.exists():
        return
    source = TOOLS / "ankiconnect"
    if not source.exists():
        return
    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        if child.is_dir():
            shutil.copytree(child, target / child.name, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target / child.name)


def launch() -> dict[str, Any]:
    cfg = load_config()
    exe = Path(cfg["system"].get("anki_exe", ""))
    if not exe.exists():
        alt = TOOLS / "anki" / "anki.exe"
        exe = alt if alt.exists() else exe
    if not exe.exists():
        raise AnkiError("找不到 Anki，可在设置里指定 anki.exe。")
    ANKI_BASE.mkdir(parents=True, exist_ok=True)
    _ensure_addon()
    subprocess.Popen(
        [str(exe), "-b", str(ANKI_BASE)],
        cwd=str(exe.parent),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) | 0x00000008,
    )
    return {"launched": True, "exe": str(exe), "base": str(ANKI_BASE)}


def wait_ready(timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            call("version", timeout=1.0)
            return
        except AnkiError:
            time.sleep(0.8)
    raise AnkiError("Anki 已启动，但 AnkiConnect 在 30 秒内没有响应。请确认插件已启用。")


def quit_app() -> dict[str, Any]:
    try:
        call("guiExitAnki", timeout=2.0)
        return {"closed": True}
    except AnkiError:
        return {"closed": False}


def setup(progress: Callable[[str, float | None], None] | None = None) -> dict[str, Any]:
    progress = progress or (lambda *_: None)
    anki = get_module("anki")
    cfg = load_config()
    url = _url()
    progress("读取配置", 0.05)
    for old, new, count in anki.migrate_legacy_decks(url, cfg["anki"]["decks"]):
        progress(f"迁移旧牌组 {old} → {new}（{count} 张）", 0.15)
    made = []
    for key in ("vocab", "phrases", "listening"):
        deck = cfg["anki"]["decks"][key]
        if anki.ensure_deck(url, deck):
            made.append(deck)
    progress("创建笔记类型", 0.35)
    for name, spec in anki.MODELS.items():
        anki.ensure_model(url, name, spec)
    progress("导入 40 条句型", 0.65)
    added, skipped = anki.import_seed(
        url,
        cfg["anki"]["decks"]["phrases"],
        cfg["anki"]["models"]["phrase"],
        anki.DEFAULT_SEED,
        False,
    )
    progress("完成", 1.0)
    return {"decks": made, "seedAdded": added, "seedSkipped": skipped}


def due() -> dict[str, Any]:
    return status()


def preview(include_untranslated: bool = False, limit: int = 200) -> list[dict[str, Any]]:
    library.refresh_snapshot()
    zotero = get_module("zotero")
    cfg = load_config()
    rows = zotero.fetch_rows(library.SNAPSHOT, None, limit)
    selected = rows if include_untranslated else [r for r in rows if zotero.clean(r["comment"])]
    notes = [
        zotero.build_note(
            row, cfg["anki"]["decks"]["vocab"], cfg["anki"]["models"]["vocab"]
        )
        for row in selected
    ]
    return [
        {
            "id": note["_annotation_id"],
            "word": note["fields"]["Word"],
            "translation": note["fields"]["Translation"],
            "source": note["fields"]["Source"],
            "link": note["fields"]["Link"],
        }
        for note in notes
    ]


def export(
    include_untranslated: bool = False,
    update: bool = False,
    progress: Callable[[str, float | None], None] | None = None,
) -> dict[str, Any]:
    progress = progress or (lambda *_: None)
    progress("扫描 Zotero 标注", 0.1)
    library.refresh_snapshot()
    zotero = get_module("zotero")
    cfg = load_config()
    deck = cfg["anki"]["decks"]["vocab"]
    model = cfg["anki"]["models"]["vocab"]
    rows = zotero.fetch_rows(library.SNAPSHOT, None, None)
    translated = [r for r in rows if zotero.clean(r["comment"])]
    selected = rows if include_untranslated else translated
    notes = [zotero.build_note(r, deck, model) for r in selected]
    if not notes:
        return {
            "total": 0,
            "translated": 0,
            "added": 0,
            "duplicates": 0,
            "message": "没有带翻译的标注。可在 Zotero 里打开 PDF Translate，或勾选“包含未翻译”。",
        }

    progress("检查 AnkiConnect", 0.2)
    call("version", timeout=2.0)
    state_path = DATA / "anki_state.json"
    state = zotero.load_state(state_path)
    exported = state.setdefault("exported", {})
    pending = []
    for note in notes:
        ann_id = str(note["_annotation_id"])
        if ann_id in exported:
            if update:
                try:
                    call(
                        "updateNoteFields",
                        note={"id": exported[ann_id], "fields": note["fields"]},
                    )
                except AnkiError:
                    pass
            continue
        pending.append(note)
    progress(f"写入 {len(pending)} 张卡片", 0.55)
    payload = [{k: v for k, v in n.items() if k != "_annotation_id"} for n in pending]
    ready = pending
    if payload:
        try:
            flags = call("canAddNotes", notes=payload)
            ready = [note for note, ok in zip(pending, flags) if ok]
        except AnkiError:
            ready = pending
        ids = call("addNotes", notes=[{k: v for k, v in n.items() if k != "_annotation_id"} for n in ready]) if ready else []
    else:
        ids = []
    added = 0
    for note, note_id in zip(ready, ids):
        if note_id:
            exported[str(note["_annotation_id"])] = note_id
            added += 1
    zotero.save_state(state_path, state)
    progress("完成", 1.0)
    return {
        "total": len(rows),
        "translated": len(translated),
        "added": added,
        "duplicates": len(pending) - len(ready),
        "failed": len(ready) - added,
        "message": f"新增 {added} 张，重复 {len(pending) - len(ready)} 张。",
    }
