"""Read-only Zotero library access for the Prism workbench."""
from __future__ import annotations

import re
import shutil
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from ..core import DATA, expand_path, get_module, load_config

_CACHE_LOCK = threading.Lock()
_DB_LOCK = threading.RLock()
_CACHE: dict[str, Any] = {"at": 0.0, "items": []}
SNAPSHOT = DATA / "zotero.sqlite"


def _clean(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _year(value: str | None) -> str:
    if not value:
        return ""
    match = re.search(r"(19|20)\d{2}", value)
    return match.group(0) if match else value[:4]


def _db_source() -> Path | None:
    zotero = get_module("zotero")
    cfg = load_config()
    path = zotero.resolve_db(cfg["zotero"]["db"])
    if path.exists():
        return path
    env = expand_path("E:/XuLab in Westlake University/Zotero/zotero.sqlite")
    return env if env.exists() else None


def refresh_snapshot() -> Path:
    source = _db_source()
    if source is None:
        raise FileNotFoundError("找不到 Zotero 数据库，请在设置里指定 zotero.sqlite。")
    with _DB_LOCK:
        for suffix in ("", "-wal", "-shm"):
            src = Path(str(source) + suffix)
            dst = Path(str(SNAPSHOT) + suffix)
            if src.exists():
                tmp = Path(str(dst) + ".tmp")
                shutil.copy2(src, tmp)
                dst.unlink(missing_ok=True)
                tmp.replace(dst)
            else:
                dst.unlink(missing_ok=True)
        with _CACHE_LOCK:
            _CACHE["at"] = 0.0
    return SNAPSHOT


def _connect() -> sqlite3.Connection:
    if not SNAPSHOT.exists():
        refresh_snapshot()
    con = sqlite3.connect(f"file:{SNAPSHOT.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


ITEM_SQL = """
SELECT i.itemID, i.key, i.dateAdded, it.typeName,
  (SELECT v.value FROM itemData d JOIN fields f ON f.fieldID=d.fieldID
     JOIN itemDataValues v ON v.valueID=d.valueID
     WHERE d.itemID=i.itemID AND f.fieldName='title') AS title,
  (SELECT v.value FROM itemData d JOIN fields f ON f.fieldID=d.fieldID
     JOIN itemDataValues v ON v.valueID=d.valueID
     WHERE d.itemID=i.itemID AND f.fieldName='date') AS date,
  (SELECT v.value FROM itemData d JOIN fields f ON f.fieldID=d.fieldID
     JOIN itemDataValues v ON v.valueID=d.valueID
     WHERE d.itemID=i.itemID AND f.fieldName='publicationTitle') AS publication,
  (SELECT v.value FROM itemData d JOIN fields f ON f.fieldID=d.fieldID
     JOIN itemDataValues v ON v.valueID=d.valueID
     WHERE d.itemID=i.itemID AND f.fieldName='DOI') AS doi,
  (SELECT v.value FROM itemData d JOIN fields f ON f.fieldID=d.fieldID
     JOIN itemDataValues v ON v.valueID=d.valueID
     WHERE d.itemID=i.itemID AND f.fieldName='abstractNote') AS abstract,
  (SELECT GROUP_CONCAT(name, '; ') FROM (
     SELECT c.lastName || ', ' || c.firstName AS name
     FROM itemCreators ic JOIN creators c ON c.creatorID=ic.creatorID
     WHERE ic.itemID=i.itemID ORDER BY ic.orderIndex)) AS authors,
  (SELECT COUNT(*) FROM itemAnnotations a
     JOIN itemAttachments att ON att.itemID=a.parentItemID
     WHERE att.parentItemID=i.itemID) AS annotations,
  (SELECT COUNT(*) FROM itemAttachments att
     WHERE att.parentItemID=i.itemID AND att.contentType='application/pdf') AS pdfs
FROM items i JOIN itemTypes it ON it.itemTypeID=i.itemTypeID
WHERE it.typeName NOT IN ('attachment','note','annotation')
"""


def _row_to_item(row: sqlite3.Row) -> dict[str, Any]:
    authors = [a.strip() for a in (row["authors"] or "").split(";") if a.strip()]
    return {
        "id": row["itemID"],
        "key": row["key"],
        "type": row["typeName"],
        "title": _clean(row["title"]) or "Untitled",
        "year": _year(row["date"]),
        "date": (row["date"] or "")[:10],
        "publication": _clean(row["publication"]),
        "doi": row["doi"] or "",
        "abstract": _clean(row["abstract"]),
        "authors": authors,
        "firstAuthor": authors[0] if authors else "",
        "annotations": row["annotations"] or 0,
        "pdfs": row["pdfs"] or 0,
        "added": (row["dateAdded"] or "")[:10],
    }


def list_items(query: str = "", limit: int = 80) -> list[dict[str, Any]]:
    now = time.time()
    with _CACHE_LOCK:
        cached = _CACHE["items"]
        fresh = now - _CACHE["at"] < 90
    if not cached or not fresh:
        with _DB_LOCK, _connect() as con:
            rows = con.execute(ITEM_SQL + " ORDER BY i.dateAdded DESC").fetchall()
        items = [_row_to_item(row) for row in rows]
        with _CACHE_LOCK:
            _CACHE["items"] = items
            _CACHE["at"] = now
        cached = items
    if query:
        needle = query.lower()
        cached = [
            item
            for item in cached
            if needle in item["title"].lower()
            or needle in " ".join(item["authors"]).lower()
            or needle in item["publication"].lower()
            or needle in item["abstract"].lower()
        ]
    return cached[:limit]


def item_detail(item_id: int) -> dict[str, Any] | None:
    for item in list_items(limit=10000):
        if item["id"] == item_id:
            break
    else:
        return None
    with _DB_LOCK, _connect() as con:
        attachments = con.execute(
            """SELECT a.itemID, a.path, a.contentType, i.key
               FROM itemAttachments a JOIN items i ON i.itemID=a.itemID
               WHERE a.parentItemID=? AND a.contentType='application/pdf'""",
            (item_id,),
        ).fetchall()
        annotations = con.execute(
            """SELECT a.itemID, a.type, a.text, a.comment, a.color, a.pageLabel,
                      a.sortIndex, att.itemID AS attachmentID
               FROM itemAnnotations a
               JOIN itemAttachments att ON att.itemID=a.parentItemID
               WHERE att.parentItemID=?
               ORDER BY a.sortIndex""",
            (item_id,),
        ).fetchall()
        tags = con.execute(
            """SELECT t.name FROM itemTags it JOIN tags t ON t.tagID=it.tagID
               WHERE it.itemID=? ORDER BY t.name""",
            (item_id,),
        ).fetchall()
        collections = con.execute(
            """SELECT c.collectionName FROM collectionItems ci
               JOIN collections c ON c.collectionID=ci.collectionID
               WHERE ci.itemID=?""",
            (item_id,),
        ).fetchall()

    storage = (_db_source().parent / "storage") if _db_source() else Path("")
    pdfs = []
    for row in attachments:
        folder = storage / row["key"]
        found = sorted(folder.glob("*.pdf")) if folder.exists() else []
        if found:
            local = found[0]
        else:
            name = (row["path"] or "").split("storage:", 1)[-1]
            local = folder / name
        pdfs.append({"name": local.name, "exists": local.exists(), "path": str(local)})

    detail = dict(item)
    detail.update(
        {
            "pdfs": pdfs,
            "tags": [r["name"] for r in tags],
            "collections": [r["collectionName"] for r in collections],
            "annotationList": [
                {
                    "id": r["itemID"],
                    "type": r["type"],
                    "text": _clean(r["text"]),
                    "comment": _clean(r["comment"]),
                    "page": r["pageLabel"] or "",
                    "color": r["color"] or "",
                }
                for r in annotations
            ],
        }
    )
    return detail


def stats() -> dict[str, Any]:
    items = list_items(limit=10000)
    annotated = sum(1 for item in items if item["annotations"])
    years: dict[str, int] = {}
    for item in items:
        if item["year"]:
            years[item["year"]] = years.get(item["year"], 0) + 1
    return {
        "total": len(items),
        "annotated": annotated,
        "withPdf": sum(1 for item in items if item["pdfs"]),
        "recent": items[:6],
        "years": dict(sorted(years.items())[-8:]),
    }
