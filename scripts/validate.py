#!/usr/bin/env python3
"""Repository self-check that only uses the standard library.

Run from the repository root:

    python scripts/validate.py

It checks required files, JSON syntax, the phrase CSV schema and size,
portable config values, and relative Markdown links. It does not need
Anki, Zotero, a speech stack, or network access.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "LICENSE-CONTENT.md",
    "NOTICE.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "PRIVACY.md",
    "CITATION.cff",
    "config.json",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "setup_env.ps1",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    "assets/banner.svg",
    "assets/social-preview.png",
    "assets/social-preview.svg",
    "data/.gitkeep",
    "reports/.gitkeep",
    "vocab/anki_setup.py",
    "vocab/zotero_to_anki.py",
    "vocab/remind.ps1",
    "vocab/install_reminder.ps1",
    "vocab/README.md",
    "vocab/yomitan_setup.md",
    "writing/.vale.ini",
    "writing/README.md",
    "writing/ltex-settings.json",
    "writing/phrasebank/phrasebank_seed.csv",
    "writing/phrasebank/training_plan.md",
    "writing/phrasebank/paragraph_lab.md",
    "speaking/speak.py",
    "speaking/README.md",
    "speaking/pronunciation.json",
    "speaking/praat_analysis.praat",
    "speaking/buzz-and-praat.md",
    "speaking/mpvacious.md",
    "speaking/samples/sample_talk.md",
    "scripts/validate.py",
    "tests/test_speak.py",
    "tests/test_anki.py",
    "tests/test_zotero.py",
]

JSON_FILES = [
    "config.json",
    "writing/ltex-settings.json",
    "speaking/pronunciation.json",
]

PHRASE_CSV = ROOT / "writing" / "phrasebank" / "phrasebank_seed.csv"
PHRASE_FIELDS = ["section", "function", "chinese_cue", "template", "example", "source"]
PHRASE_SECTIONS = {"Introduction", "Methods", "Results", "Discussion", "Speaking"}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_ATTR_RE = re.compile(r'(?:src|href)=["\']([^"\']+)["\']')
SKIP_PREFIXES = ("http://", "https://", "mailto:", "data:", "#", "tel:")

errors: list[str] = []
warnings: list[str] = []


def error(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def check_required_files() -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            error(f"缺少必需文件：{rel}")


def check_json() -> None:
    for rel in JSON_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            error(f"JSON 解析失败：{rel}（第 {exc.lineno} 行：{exc.msg}）")


def check_config() -> None:
    path = ROOT / "config.json"
    if not path.exists():
        return
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for key in ("url",):
        if not cfg.get("anki", {}).get(key):
            error(f"config.json 缺少 anki.{key}")
    for key in ("vocab", "phrases", "listening"):
        deck = cfg.get("anki", {}).get("decks", {}).get(key, "")
        if not deck.startswith("Prism::"):
            error(f"config.json 的 anki.decks.{key} 应以 Prism:: 开头，实际为 {deck!r}")
    for key in ("vocab", "phrase", "listening"):
        if not cfg.get("anki", {}).get("models", {}).get(key):
            error(f"config.json 缺少 anki.models.{key}")
    db = cfg.get("zotero", {}).get("db", "")
    if "Users/" in db.replace("\\", "/"):
        warn("config.json 的 zotero.db 含绝对用户路径；建议用 ~/Zotero/zotero.sqlite")


def check_phrases() -> None:
    if not PHRASE_CSV.exists():
        return
    with PHRASE_CSV.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != PHRASE_FIELDS:
            error(f"句型 CSV 表头不符：{reader.fieldnames}")
            return
        rows = list(reader)
    if len(rows) != 40:
        error(f"句型 CSV 应为 40 行，实际 {len(rows)} 行")
    seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        section = (row.get("section") or "").strip()
        if section not in PHRASE_SECTIONS:
            error(f"句型 CSV 第 {index} 行 section 非法：{section!r}")
        for field in PHRASE_FIELDS:
            if not (row.get(field) or "").strip():
                error(f"句型 CSV 第 {index} 行 {field} 为空")
        template = (row.get("template") or "").strip()
        if template and template in seen:
            warn(f"句型 CSV 第 {index} 行 template 与前面重复：{template[:40]}")
        seen.add(template)


def check_links() -> None:
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts or ".venv" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            check_link(path, match.group(1))
        for match in HTML_ATTR_RE.finditer(text):
            check_link(path, match.group(1))


def check_link(source: Path, raw: str) -> None:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = target.split(" ", 1)[0]
    if not target or target.startswith(SKIP_PREFIXES):
        return
    if target.startswith("/"):
        return
    target = unquote(target.split("#", 1)[0])
    if not target:
        return
    resolved = (source.parent / target).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        warn(f"{source.relative_to(ROOT)}：链接指向仓库外，未检查：{raw}")
        return
    if not resolved.exists():
        error(f"{source.relative_to(ROOT)}：相对链接失效：{raw}")


def check_repo_hygiene() -> None:
    gitignore = ROOT / ".gitignore"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
        for pattern in ("data/*", "reports/*", "speaking/samples/*.wav", ".venv/"):
            if pattern not in text:
                warn(f".gitignore 未包含 {pattern}")
    for rel in ("data", "reports"):
        if any((ROOT / rel).glob("*.json")):
            warn(f"{rel}/ 内有本地数据；提交前确认未加密内容")


def main() -> int:
    check_required_files()
    check_json()
    check_config()
    check_phrases()
    check_links()
    check_repo_hygiene()

    for message in warnings:
        print(f"[warn] {message}")
    if errors:
        for message in errors:
            print(f"[error] {message}", file=sys.stderr)
        print(f"\n校验失败：{len(errors)} 个错误，{len(warnings)} 个警告。", file=sys.stderr)
        return 1
    print(f"校验通过：必需文件齐全，JSON/CSV 有效，相对链接可达（{len(warnings)} 个警告）。")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
