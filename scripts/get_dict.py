#!/usr/bin/env python3
"""Download ECDICT and build the local lookup index used by the clip extension.

    python scripts/get_dict.py            # download if missing, then index
    python scripts/get_dict.py --check    # report what is on disk

Everything stays inside the suite folder (default E:/LumenSuite/models/ecdict),
and the result is used offline: Prism never sends the words you look up anywhere.
"""
from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

URL = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv"
LICENSE = "https://github.com/skywind3000/ECDICT"
SUITE = Path(os.environ.get("LUMEN_SUITE", "E:/LumenSuite"))
HERE = SUITE / "models" / "ecdict"
CSV_PATH = HERE / "ecdict.csv"
DB_PATH = HERE / "ecdict.sqlite"
MIN_CSV_BYTES = 40_000_000
MIN_DB_BYTES = 40_000_000
BATCH = 20_000

SCHEMA = """
CREATE TABLE IF NOT EXISTS words (
    word TEXT PRIMARY KEY,
    phonetic TEXT,
    translation TEXT,
    definition TEXT,
    tags TEXT,
    exchange TEXT,
    bnc INTEGER,
    frq INTEGER,
    oxford INTEGER,
    collins INTEGER
);
CREATE INDEX IF NOT EXISTS words_lower ON words (word COLLATE NOCASE);
"""


def log(message: str, done: float | None = None) -> None:
    stamp = f"[{done * 100:5.1f}%] " if done is not None else ""
    print(f"{stamp}{message}", flush=True)


def emit(progress: Callable | None, message: str, done: float | None = None) -> None:
    log(message, done)
    if progress:
        progress(message, done)


def download(url: str = URL, force: bool = False, progress: Callable | None = None) -> bool:
    if not force and CSV_PATH.exists() and CSV_PATH.stat().st_size >= MIN_CSV_BYTES:
        emit(progress, f"词典已存在：{CSV_PATH}（{CSV_PATH.stat().st_size // 1048576} MB）")
        return False
    HERE.mkdir(parents=True, exist_ok=True)
    target = CSV_PATH.with_suffix(".csv.part")
    emit(progress, f"下载 ECDICT：{url}")
    request = urllib.request.Request(url, headers={"User-Agent": "Prism"})
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as fh:
            total = int(response.headers.get("content-length") or 0)
            got = 0
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                fh.write(chunk)
                got += len(chunk)
                if total:
                    emit(progress, f"已下载 {got // 1048576} / {total // 1048576} MB", 0.1 + 0.5 * got / total)
    except (urllib.error.URLError, OSError) as exc:
        target.unlink(missing_ok=True)
        raise SystemExit(f"下载失败：{exc}\n网络不通时可换镜像：--url <ecdict.csv 的地址>") from exc
    if target.stat().st_size < MIN_CSV_BYTES:
        target.unlink(missing_ok=True)
        raise SystemExit(f"下载不完整（{target.stat().st_size} 字节），已放弃。")
    target.replace(CSV_PATH)
    emit(progress, f"下载完成：{CSV_PATH.stat().st_size // 1048576} MB，用时 {time.time() - started:.0f} s", 0.6)
    return True


def split_translation(value: str) -> str:
    """ECDICT stores line breaks as the two characters backslash-n."""
    return value.replace("\\n", "\n").strip()


def num(value: str) -> int:
    return int(value) if value.strip().isdigit() else 0


def build(force: bool = False, progress: Callable | None = None) -> int:
    if not CSV_PATH.exists():
        raise SystemExit(f"缺少 {CSV_PATH}，先运行本脚本下载。")
    if DB_PATH.exists() and not force:
        fresh = DB_PATH.stat().st_size > MIN_DB_BYTES and DB_PATH.stat().st_mtime > CSV_PATH.stat().st_mtime
        if fresh:
            connection = sqlite3.connect(DB_PATH)
            count = connection.execute("SELECT COUNT(*) FROM words").fetchone()[0]
            connection.close()
            emit(progress, f"索引已存在：{count} 个词条（{DB_PATH.stat().st_size // 1048576} MB）", 1.0)
            return count
        DB_PATH.unlink()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.executescript(SCHEMA)
    total = 0
    rows: list[tuple] = []
    started = time.time()
    csv.field_size_limit(1 << 26)
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            word = (row.get("word") or "").strip()
            if not word:
                continue
            rows.append(
                (
                    word,
                    (row.get("phonetic") or "").strip(),
                    split_translation(row.get("translation") or ""),
                    split_translation(row.get("definition") or ""),
                    (row.get("tag") or "").strip(),
                    (row.get("exchange") or "").strip(),
                    num(row.get("bnc") or ""),
                    num(row.get("frq") or ""),
                    1 if num(row.get("oxford") or "") else 0,
                    num(row.get("collins") or ""),
                )
            )
            total += 1
            if len(rows) >= BATCH:
                connection.executemany("INSERT OR REPLACE INTO words VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
                rows.clear()
                if total % 200_000 == 0:
                    emit(progress, f"已索引 {total} 条", 0.6 + 0.4 * total / 770_000)
    if rows:
        connection.executemany("INSERT OR REPLACE INTO words VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    connection.commit()
    count = connection.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    connection.close()
    size = DB_PATH.stat().st_size // 1048576
    emit(progress, f"索引完成：{count} 个词条，{size} MB，用时 {time.time() - started:.0f} s", 1.0)
    return count


def check() -> int:
    if not DB_PATH.exists():
        log(f"未安装：{DB_PATH} 不存在，运行 python scripts/get_dict.py")
        return 1
    connection = sqlite3.connect(DB_PATH)
    count = connection.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    connection.close()
    log(f"{DB_PATH}：{count} 个词条，{DB_PATH.stat().st_size // 1048576} MB")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="获取 Prism 的本地英汉词典")
    parser.add_argument("--url", default=URL, help=f"csv 地址（默认 {URL}）")
    parser.add_argument("--force", action="store_true", help="重新下载并重建索引")
    parser.add_argument("--check", action="store_true", help="只报告当前状态")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.check:
        return check()
    download(args.url, args.force)
    build(args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
