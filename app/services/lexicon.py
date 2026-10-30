"""Offline English-Chinese lookup plus the browser clipping inbox.

The dictionary lives under the suite folder and is only ever read; the words you
select land in `data/clips.jsonl` and reach Anki through AnkiConnect on this box.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
import uuid
from contextlib import closing
from typing import Any

from ..core import DATA, MODELS, load_config

DB_PATH = MODELS / "ecdict" / "ecdict.sqlite"
CLIPS_PATH = DATA / "clips.jsonl"
MAX_WORD = 120
MAX_CONTEXT = 600
_lock = threading.Lock()

EXCHANGE_LABELS = {
    "0": "原型",
    "1": "过去式",
    "2": "过去分词",
    "3": "三单",
    "4": "现在分词",
    "5": "复数",
    "6": "比较级",
    "7": "最高级",
    "p": "过去式",
    "d": "过去分词",
    "i": "现在分词",
    "s": "复数/三单",
    "r": "比较级",
    "t": "最高级",
}
TAG_LABELS = {
    "cet4": "CET4",
    "cet6": "CET6",
    "ky": "考研",
    "toefl": "TOEFL",
    "ielts": "IELTS",
    "gre": "GRE",
    "sat": "SAT",
    "frq": "高频",
    "bk": "书刊",
}


def installed() -> bool:
    return DB_PATH.exists()


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=3)
    connection.row_factory = sqlite3.Row
    return connection


def normalize(query: str) -> str:
    return re.sub(r"\s+", " ", query or "").strip(" \t\r\n\"'“”‘’()[]{}.,;:!?—–-·、。")


def _entry(row: sqlite3.Row | None, matched: str) -> dict[str, Any] | None:
    if row is None:
        return None
    exchange = []
    for part in (row["exchange"] or "").split("/"):
        if ":" not in part:
            continue
        kind, value = part.split(":", 1)
        label = EXCHANGE_LABELS.get(kind.strip().lower())
        if label and value:
            exchange.append(f"{label} {value}")
    tags = [TAG_LABELS.get(t, t) for t in (row["tags"] or "").split() if t]
    return {
        "word": row["word"],
        "matched": matched,
        "phonetic": row["phonetic"] or "",
        "translation": row["translation"] or "",
        "definition": row["definition"] or "",
        "tags": tags,
        "exchange": exchange,
        "collins": row["collins"] or 0,
        "oxford": bool(row["oxford"]),
        "source": "ECDICT（本机）",
    }


def lookup(query: str) -> dict[str, Any]:
    """Find a word or short phrase; case-insensitive, then longest common prefix."""
    cleaned = normalize(query)
    if not cleaned:
        return {"query": query, "entry": None, "installed": installed()}
    if not installed():
        return {"query": cleaned, "entry": None, "installed": False}
    with _lock, closing(_connect()) as connection:
        for candidate, how in (
            (cleaned, "exact"),
            (cleaned.lower(), "lower"),
            (cleaned.capitalize(), "capitalized"),
        ):
            row = connection.execute(
                "SELECT * FROM words WHERE word = ? COLLATE NOCASE ORDER BY (word = ?) DESC, LENGTH(word) LIMIT 1",
                (candidate, cleaned),
            ).fetchone()
            if row:
                entry = _entry(row, how)
                if entry:
                    return {"query": cleaned, "entry": entry, "installed": True}
    return {"query": cleaned, "entry": None, "installed": True}


def _read_clips() -> list[dict[str, Any]]:
    if not CLIPS_PATH.exists():
        return []
    rows = []
    for line in CLIPS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and record.get("id"):
            rows.append(record)
    return rows


def _write_clips(rows: list[dict[str, Any]]) -> None:
    CLIPS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CLIPS_PATH.with_suffix(".jsonl.tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(CLIPS_PATH)


def add_clip(payload: dict[str, Any]) -> dict[str, Any]:
    word = normalize(str(payload.get("word") or ""))[:MAX_WORD]
    if not word:
        raise ValueError("没有内容可保存。")
    record = {
        "id": uuid.uuid4().hex[:12],
        "word": word,
        "context": str(payload.get("context") or "")[:MAX_CONTEXT],
        "url": str(payload.get("url") or "")[:500],
        "title": str(payload.get("title") or "")[:200],
        "translation": str(payload.get("translation") or "")[:1200],
        "phonetic": str(payload.get("phonetic") or "")[:120],
        "ts": time.time(),
        "status": "new",
    }
    with _lock:
        rows = _read_clips()
        rows.append(record)
        _write_clips(rows)
    return record


def clips(limit: int = 200) -> dict[str, Any]:
    with _lock:
        rows = _read_clips()
    rows.sort(key=lambda r: r.get("ts") or 0, reverse=True)
    fresh = [r for r in rows if r.get("status") != "imported"]
    return {
        "items": rows[:limit],
        "total": len(rows),
        "pending": len(fresh),
        "imported": len(rows) - len(fresh),
        "dictInstalled": installed(),
    }


def drop(ids: list[str]) -> int:
    wanted = set(ids)
    with _lock:
        rows = _read_clips()
        kept = [r for r in rows if r["id"] not in wanted]
        removed = len(rows) - len(kept)
        if removed:
            _write_clips(kept)
    return removed


def _note(record: dict[str, Any], deck: str, model: str) -> dict[str, Any]:
    from urllib.parse import urlparse

    host = urlparse(record.get("url") or "").netloc or record.get("title") or "浏览器划词"
    added = time.strftime("%Y-%m-%d", time.localtime(record.get("ts") or time.time()))
    return {
        "deckName": deck,
        "modelName": model,
        "tags": ["web-clip", "prism"],
        "fields": {
            "Word": record["word"],
            "Translation": record.get("translation") or "",
            "Context": record.get("context") or "",
            "Source": host,
            "Link": record.get("url") or "",
            "Audio": "",
            "Added": added,
        },
    }


def import_clips(ids: list[str] | None = None) -> dict[str, Any]:
    """Push pending clips into Prism::Vocab through AnkiConnect."""
    from . import anki

    cfg = load_config()
    deck = cfg["anki"]["decks"]["vocab"]
    model = cfg["anki"]["models"]["vocab"]
    with _lock:
        rows = _read_clips()
    wanted = set(ids or [])
    pending = [
        r
        for r in rows
        if r.get("status") != "imported" and (not wanted or r["id"] in wanted)
    ]
    if not pending:
        return {"added": 0, "duplicates": 0, "failed": 0, "message": "收件箱里没有待写入的条目。"}

    anki.call("version", timeout=3.0)
    # canAddNotes answers false for every note when the deck is missing, which
    # would otherwise be reported as "all of them are duplicates".
    if deck not in set(anki.call("deckNames")):
        anki.call("createDeck", deck=deck)
    if model not in set(anki.call("modelNames")):
        raise anki.AnkiError(f"笔记类型 {model} 还不存在：先在 Vocab 页点「初始化牌组」。")
    pairs = [(record, _note(record, deck, model)) for record in pending]
    try:
        flags = anki.call("canAddNotes", notes=[note for _, note in pairs])
    except anki.AnkiError:
        flags = [True] * len(pairs)
    ready = [(record, note) for (record, note), ok in zip(pairs, flags) if ok]
    returned = anki.call("addNotes", notes=[note for _, note in ready]) if ready else []
    by_id = {row["id"]: row for row in rows}
    added = 0
    for (record, _), note_id in zip(ready, returned):
        if not note_id:
            continue
        target = by_id.get(record["id"])
        if target is not None:
            target["status"] = "imported"
            target["noteId"] = note_id
        added += 1
    with _lock:
        _write_clips(rows)
    duplicates = len(pairs) - len(ready)
    failed = len(ready) - added
    return {
        "added": added,
        "duplicates": duplicates,
        "failed": failed,
        "message": f"新增 {added} 张，重复 {duplicates} 张。",
    }
