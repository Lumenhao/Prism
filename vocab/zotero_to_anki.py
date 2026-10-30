#!/usr/bin/env python3
"""Export Zotero PDF annotations (with translated comments) into Anki.

Workflow:
  1. In Zotero, install/enable the PDF Translate plugin and turn on
     "Automatically Translate Annotation" so the translation is written
     into the annotation comment.
  2. Keep Anki open with AnkiConnect.
  3. Run: python vocab/zotero_to_anki.py --dry-run
     then: python vocab/zotero_to_anki.py

The script never writes to Zotero: it reads a temporary snapshot of zotero.sqlite.
"""
from __future__ import annotations

import argparse
import atexit
import csv
import html
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config.json"
DEFAULT_STATE = ROOT / "data" / "zotero_export_state.json"
TAG_RE = re.compile(r"<[^>]+>")


def expand_path(value: str) -> Path:
    """Expand ~ and environment variables so config.json stays portable."""
    return Path(os.path.expanduser(os.path.expandvars(value)))


def parse_zotero_data_dir(prefs_text: str) -> Path | None:
    """Read extensions.zotero.dataDir from a Zotero prefs.js file."""
    match = re.search(
        r'"extensions\.zotero\.dataDir"\s*,\s*"((?:[^"\\]|\\.)*)"',
        prefs_text,
    )
    if not match:
        return None
    raw = match.group(1).replace("\\\\", "\\")
    # prefs.js carries Windows separators; on POSIX a backslash is part of the name, so
    # normalise here rather than letting a Linux run read a Windows path as one filename.
    return Path(raw.replace("\\", "/"))


def find_zotero_db() -> Path | None:
    """Locate zotero.sqlite in every Zotero profile known to this user."""
    roots: list[Path] = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        roots.append(Path(appdata) / "Zotero" / "Zotero" / "Profiles")
    roots.append(Path.home() / "Library" / "Application Support" / "Zotero" / "Profiles")
    roots.append(Path.home() / ".zotero" / "zotero" / "Profiles")
    for root in roots:
        if not root.is_dir():
            continue
        for prefs in sorted(root.glob("*/prefs.js")):
            try:
                data_dir = parse_zotero_data_dir(prefs.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            if data_dir:
                candidate = data_dir / "zotero.sqlite"
                if candidate.exists():
                    return candidate
    return None


def resolve_db(cfg_value: str) -> Path:
    """ZOTERO_DB > configured path > auto-detected Zotero profile."""
    override = os.environ.get("ZOTERO_DB")
    if override:
        return expand_path(override)
    configured = expand_path(cfg_value)
    if configured.exists():
        return configured
    detected = find_zotero_db()
    return detected or configured


class AnkiError(RuntimeError):
    pass


def call(url: str, action: str, **params):
    payload = {"action": action, "version": 6, "params": params}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise AnkiError(
            f"无法连接 AnkiConnect（{url}）。请打开 Anki 并安装 AnkiConnect（代码 2055492159）。"
        ) from exc
    if data.get("error"):
        raise AnkiError(str(data["error"]))
    return data.get("result")


def clean(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = TAG_RE.sub(" ", value)
    value = value.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


def snapshot_db(db_path: Path) -> Path:
    """Copy zotero.sqlite plus its WAL so Zotero can stay open.

    Opening the live DB read-only blocks while Zotero holds a write lock, so we
    copy the three files into a temp directory. SQLite replays the copied WAL
    when the snapshot is opened, which keeps recent annotations visible.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="zotero_snapshot_"))
    target = tmpdir / "zotero.sqlite"
    copied = False
    try:
        for suffix in ("", "-wal", "-shm"):
            source = Path(str(db_path) + suffix)
            if source.exists():
                shutil.copy2(source, Path(str(target) + suffix))
                copied = True
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    if not copied:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise FileNotFoundError(f"找不到 Zotero 数据库：{db_path}")
    atexit.register(shutil.rmtree, tmpdir, ignore_errors=True)
    return target


def fetch_rows(snapshot: Path, since: str | None, limit: int | None):
    con = sqlite3.connect(snapshot)
    con.row_factory = sqlite3.Row
    sql = """
    SELECT
      a.itemID                AS annotation_id,
      a.text                  AS text,
      a.comment               AS comment,
      a.pageLabel             AS page,
      i.dateAdded             AS added,
      paper.key               AS paper_key,
      (SELECT v.value FROM itemData d
         JOIN itemDataValues v ON v.valueID = d.valueID
        WHERE d.itemID = COALESCE(att.parentItemID, a.parentItemID)
          AND d.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'title')) AS title,
      (SELECT v.value FROM itemData d
         JOIN itemDataValues v ON v.valueID = d.valueID
        WHERE d.itemID = COALESCE(att.parentItemID, a.parentItemID)
          AND d.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'DOI')) AS doi
    FROM itemAnnotations a
    JOIN items i ON i.itemID = a.itemID
    LEFT JOIN itemAttachments att ON att.itemID = a.parentItemID
    LEFT JOIN items paper ON paper.itemID = COALESCE(att.parentItemID, a.parentItemID)
    WHERE TRIM(COALESCE(a.text, '')) <> ''
    """
    params: list[str] = []
    if since:
        sql += " AND i.dateAdded >= ?"
        params.append(since if len(since) > 10 else since + " 00:00:00")
    sql += " ORDER BY i.dateAdded ASC, a.itemID ASC"
    if limit:
        sql += " LIMIT ?"
        params.append(str(limit))
    rows = [dict(r) for r in con.execute(sql, params)]
    con.close()
    return rows


def build_note(row: dict, deck: str, model: str) -> dict:
    text = clean(row["text"])
    translation = clean(row["comment"])
    title = clean(row["title"]) or "Unknown source"
    page = clean(row["page"])
    source = f"{title} (p. {page})" if page else title
    link = ""
    if row["paper_key"]:
        link = f"zotero://select/library/items/{row['paper_key']}"
    elif row["doi"]:
        link = "https://doi.org/" + clean(row["doi"])
    added = (row["added"] or "")[:10]
    tags = ["zotero", "auto"]
    if not translation:
        tags.append("needs_translation")
    return {
        "deckName": deck,
        "modelName": model,
        "fields": {
            "Word": text,
            "Translation": translation,
            "Context": "",
            "Source": source,
            "Link": link,
            "Audio": "",
            "Added": added,
        },
        "tags": tags,
        "options": {"allowDuplicate": False, "duplicateScope": "deck"},
        "_annotation_id": row["annotation_id"],
    }


def load_state(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"exported": {}}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def write_tsv(path: Path, notes: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["Word", "Translation", "Source", "Link", "Added", "AnnotationID"])
        for note in notes:
            f = note["fields"]
            writer.writerow(
                [f["Word"], f["Translation"], f["Source"], f["Link"], f["Added"], note["_annotation_id"]]
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--since", help="只导出该日期之后的标注，例如 2026-10-01")
    parser.add_argument("--limit", type=int, help="最多处理多少条（调试用）")
    parser.add_argument("--include-untranslated", action="store_true", help="连没有翻译注释的标注也导出")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写 Anki")
    parser.add_argument("--update", action="store_true", help="更新已导出卡片的字段（不新建）")
    parser.add_argument("--offline", action="store_true", help="不连接 Anki，只导出 TSV")
    parser.add_argument("--tsv", type=Path, help="同时写出一份可手动导入 Anki 的 TSV")
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    db_path = resolve_db(cfg["zotero"]["db"])
    if not db_path.exists():
        print(f"[错误] 找不到 Zotero 数据库：{db_path}", file=sys.stderr)
        print("       请在 config.json 填写路径，或设置环境变量 ZOTERO_DB。", file=sys.stderr)
        return 1
    print(f"Zotero 数据库：{db_path}")

    url = cfg["anki"]["url"]
    deck = cfg["anki"]["decks"]["vocab"]
    model = cfg["anki"]["models"]["vocab"]

    snapshot = snapshot_db(db_path)
    try:
        rows = fetch_rows(snapshot, args.since, args.limit)
    finally:
        snapshot.unlink(missing_ok=True)

    translated = [r for r in rows if clean(r["comment"])]
    selected = rows if args.include_untranslated else translated
    notes = [build_note(r, deck, model) for r in selected]

    print(f"Zotero 标注：有文字 {len(rows)} 条，其中带翻译注释 {len(translated)} 条。")
    if not translated:
        print("[提示] 没有带翻译的标注。在 Zotero → PDF Translate 设置里打开")
        print("       “Automatically Translate Annotation”，翻译会写入标注注释。")
        print("       现有标注也可以手动翻译后重跑；或加 --include-untranslated 先导出原文。")
    if not notes:
        return 0

    if args.tsv:
        write_tsv(args.tsv, notes)
        print(f"已写出 TSV：{args.tsv}")

    if args.dry_run:
        print(f"\n预览（共 {len(notes)} 条，前 8 条）：")
        for note in notes[:8]:
            f = note["fields"]
            print(f"  [{note['_annotation_id']}] {f['Word'][:60]!r} → {f['Translation'][:40]!r}")
            print(f"       {f['Source']}  {f['Link']}")
        print("\n未写入 Anki（--dry-run）。")
        return 0

    state = load_state(args.state)
    exported = state.setdefault("exported", {})
    pending = []
    for note in notes:
        ann_id = str(note["_annotation_id"])
        if ann_id in exported and not args.update:
            continue
        if ann_id in exported and args.update and not args.offline:
            try:
                call(
                    url,
                    "updateNoteFields",
                    note={"id": exported[ann_id], "fields": note["fields"]},
                )
                print(f"更新 {ann_id} -> note {exported[ann_id]}")
            except AnkiError as exc:
                print(f"[警告] 更新 {ann_id} 失败：{exc}")
            continue
        pending.append(note)

    if args.offline:
        print(f"离线模式：待写入 {len(pending)} 条（未连接 Anki）。")
        return 0

    if not pending:
        print("没有需要新增的标注（都已在 state 里）。")
        return 0

    try:
        call(url, "version")
        payload = [{k: v for k, v in n.items() if k != "_annotation_id"} for n in pending]
        try:
            can_add = call(url, "canAddNotes", notes=payload)
        except AnkiError:
            can_add = [True] * len(payload)
        ready = [n for n, ok in zip(pending, can_add) if ok]
        duplicates = len(pending) - len(ready)
        if ready:
            ids = call(
                url,
                "addNotes",
                notes=[{k: v for k, v in n.items() if k != "_annotation_id"} for n in ready],
            )
        else:
            ids = []
    except AnkiError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        if args.tsv:
            print("TSV 已生成，可手动导入。")
            return 0
        return 1

    added = 0
    failed = 0
    for note, note_id in zip(ready, ids):
        if note_id:
            exported[str(note["_annotation_id"])] = note_id
            added += 1
        else:
            failed += 1
    save_state(args.state, state)

    print(
        f"完成：新增 {added} 张，重复 {duplicates} 张，失败 {failed} 张；"
        f"state 已写入 {args.state}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
