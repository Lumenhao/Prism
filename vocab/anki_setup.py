#!/usr/bin/env python3
"""Create the PaperToTalk decks/note types in Anki and import the phrase seed.

Requires Anki + AnkiConnect (add-on code 2055492159) running on localhost.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config.json"
DEFAULT_SEED = ROOT / "writing" / "phrasebank" / "phrasebank_seed.csv"

CSS = """
.card {
  font-family: "Segoe UI", "Noto Sans", "Helvetica Neue", Arial, sans-serif;
  font-size: 21px;
  line-height: 1.55;
  color: #1f2933;
  background: #fbfbf8;
  text-align: left;
  padding: 18px 20px;
}
.nightMode .card, .night_mode .card {
  color: #e6e6e6;
  background: #1f2328;
}
.word { font-size: 30px; font-weight: 600; margin-bottom: 10px; }
.cue { font-size: 26px; font-weight: 600; margin-bottom: 6px; }
.func { font-size: 14px; letter-spacing: .04em; text-transform: uppercase; color: #7b8794; }
.context, .example { color: #52606d; font-style: italic; margin-top: 10px; }
.nightMode .context, .nightMode .example { color: #b8c1cc; }
.trans { font-size: 25px; color: #0b6e4f; margin-top: 6px; }
.nightMode .trans { color: #7bd88f; }
.template { font-size: 23px; margin-top: 6px; }
.mine { margin-top: 10px; padding: 8px 10px; border-left: 3px solid #0b6e4f; background: rgba(11,110,79,.07); }
.meta { margin-top: 14px; font-size: 14px; color: #7b8794; }
.meta a { color: #2563eb; }
hr#answer { border: 0; border-top: 1px solid #d9e2ec; margin: 14px 0; }
"""

MODELS = {
    "AE Vocab": {
        "fields": ["Word", "Translation", "Context", "Source", "Link", "Audio", "Added"],
        "front": """<div class="word">{{Word}}</div>
{{#Audio}}<div>{{Audio}}</div>{{/Audio}}
{{#Context}}<div class="context">{{Context}}</div>{{/Context}}""",
        "back": """{{FrontSide}}
<hr id=answer>
<div class="trans">{{Translation}}</div>
{{#Source}}<div class="meta">{{Source}}</div>{{/Source}}
{{#Link}}<div class="meta"><a href="{{Link}}">source</a></div>{{/Link}}""",
    },
    "AE Phrase": {
        "fields": ["Function", "ChineseCue", "Template", "Example", "Source", "MySentence"],
        "front": """<div class="cue">{{ChineseCue}}</div>
<div class="func">{{Function}}</div>""",
        "back": """{{FrontSide}}
<hr id=answer>
<div class="template">{{Template}}</div>
{{#Example}}<div class="example">{{Example}}</div>{{/Example}}
{{#MySentence}}<div class="mine">{{MySentence}}</div>{{/MySentence}}
{{#Source}}<div class="meta">{{Source}}</div>{{/Source}}""",
    },
    "AE Subs": {
        "fields": ["Expression", "Meaning", "Audio", "Image", "Source"],
        "front": """<div class="word">{{Expression}}</div>
{{#Audio}}<div>{{Audio}}</div>{{/Audio}}""",
        "back": """{{FrontSide}}
<hr id=answer>
{{#Meaning}}<div class="trans">{{Meaning}}</div>{{/Meaning}}
{{#Image}}<div>{{Image}}</div>{{/Image}}
{{#Source}}<div class="meta">{{Source}}</div>{{/Source}}""",
    },
}


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
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise AnkiError(
            f"无法连接 AnkiConnect（{url}）。请先打开 Anki，并安装 AnkiConnect 插件"
            "（工具 → 插件 → 获取插件，代码 2055492159），然后重启 Anki。"
        ) from exc
    data = json.loads(body)
    if data.get("error"):
        raise AnkiError(str(data["error"]))
    return data.get("result")


def tagify(text: str) -> str:
    return re.sub(r"[^\w:.-]+", "_", text.strip(), flags=re.UNICODE).strip("_") or "misc"


def ensure_deck(url: str, deck: str) -> bool:
    if deck in call(url, "deckNames"):
        return False
    call(url, "createDeck", deck=deck)
    return True


def ensure_model(url: str, name: str, spec: dict) -> bool:
    if name in call(url, "modelNames"):
        return False
    call(
        url,
        "createModel",
        modelName=name,
        inOrderFields=spec["fields"],
        css=CSS,
        isCloze=False,
        cardTemplates=[{"Name": "Card 1", "Front": spec["front"], "Back": spec["back"]}],
    )
    return True


def import_seed(url: str, deck: str, model: str, path: Path, dry_run: bool) -> tuple[int, int]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    notes = []
    for row in rows:
        notes.append(
            {
                "deckName": deck,
                "modelName": model,
                "fields": {
                    "Function": (row.get("function") or "").strip(),
                    "ChineseCue": (row.get("chinese_cue") or "").strip(),
                    "Template": (row.get("template") or "").strip(),
                    "Example": (row.get("example") or "").strip(),
                    "Source": (row.get("source") or "").strip(),
                    "MySentence": "",
                },
                "tags": ["phrasebank", "seed", "section::" + tagify(row.get("section") or "misc")],
                # Function is the first field and repeats across sections, so let
                # Anki accept the seed as a batch instead of treating it as dupes.
                "options": {"allowDuplicate": True, "duplicateScope": "deck"},
            }
        )
    if not notes:
        return 0, 0
    if dry_run:
        for n in notes[:5]:
            print("  DRY", n["fields"]["ChineseCue"], "→", n["fields"]["Template"])
        print(f"  DRY 共 {len(notes)} 张卡片，未写入 Anki")
        return 0, 0

    # Re-running the seed must not pile up copies: match on the template text.
    try:
        ids = call(url, "findNotes", query=f'deck:"{deck}"')
        existing = {
            (n.get("fields", {}).get("Template", {}).get("value") or "").strip()
            for n in call(url, "notesInfo", notes=ids)
        } if ids else set()
    except AnkiError:
        existing = set()
    notes = [n for n in notes if n["fields"]["Template"] not in existing]
    if not notes:
        return 0, 0

    try:
        can_add = call(url, "canAddNotes", notes=notes)
    except AnkiError:
        can_add = [True] * len(notes)
    pending = [n for n, ok in zip(notes, can_add) if ok]
    skipped = len(notes) - len(pending)
    if not pending:
        return 0, skipped

    ids = call(url, "addNotes", notes=pending)
    added = sum(1 for i in ids if i)
    skipped += sum(1 for i in ids if not i)
    return added, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--no-seed", action="store_true", help="只建牌组/笔记类型，不导入句型")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true", help="只检查连接和现有牌组")
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    url = cfg["anki"]["url"]
    decks = cfg["anki"]["decks"]
    models = cfg["anki"]["models"]

    try:
        version = call(url, "version")
        print(f"AnkiConnect v{version} 已连接：{url}")
    except AnkiError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1

    if args.check:
        existing = call(url, "deckNames")
        for label, deck in decks.items():
            print(f"  {label:10s} {deck:36s} {'OK' if deck in existing else '缺失'}")
        existing_models = call(url, "modelNames")
        for label, model in models.items():
            print(f"  {label:10s} {model:36s} {'OK' if model in existing_models else '缺失'}")
        return 0

    for label, deck in decks.items():
        created = ensure_deck(url, deck)
        print(f"{'创建' if created else '已存在'}牌组：{deck}")

    for label, model in models.items():
        created = ensure_model(url, model, MODELS[model])
        print(f"{'创建' if created else '已存在'}笔记类型：{model}")

    if not args.no_seed and args.seed.exists():
        added, skipped = import_seed(
            url, decks["phrases"], models["phrase"], args.seed, args.dry_run
        )
        print(f"句型种子：新增 {added} 张，跳过 {skipped} 张（重复或已存在）")
    elif not args.seed.exists():
        print(f"[提示] 未找到种子文件：{args.seed}")

    print("\n完成。下一步：")
    print("  1. 在 Anki 里打开 Tools → Manage note types，确认 3 个 AE 笔记类型存在。")
    print("  2. 设置复习上限（可选）：PaperToTalk 牌组 → Options → New cards/day ≈ 10。")
    print("  3. 运行 vocab/zotero_to_anki.py --dry-run 查看 Zotero 标注。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
