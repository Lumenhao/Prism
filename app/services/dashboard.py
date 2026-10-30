"""Overview data for the Prism dashboard."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any

from . import anki, library, speech, writing
from ..core import DATA, ROOT

ACTIVITY = DATA / "activity.jsonl"
SCRIPT = ROOT / "speaking" / "samples" / "sample_talk.md"


def record(kind: str, label: str, detail: dict[str, Any] | None = None) -> None:
    entry = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "kind": kind,
        "label": label,
        "detail": detail or {},
    }
    with ACTIVITY.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def activity(limit: int = 40) -> list[dict[str, Any]]:
    if not ACTIVITY.exists():
        return []
    rows = []
    for line in ACTIVITY.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(rows))


def _streak(days: set[date]) -> int:
    cursor = date.today()
    if cursor not in days:
        cursor -= timedelta(days=1)
    count = 0
    while cursor in days:
        count += 1
        cursor -= timedelta(days=1)
    return count


def overview() -> dict[str, Any]:
    rows = activity(400)
    days = {datetime.fromisoformat(row["at"]).date() for row in rows}
    week = []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        week.append(
            {
                "day": day.strftime("%a"),
                "date": day.isoformat(),
                "count": sum(
                    1 for row in rows if datetime.fromisoformat(row["at"]).date() == day
                ),
            }
        )
    items = library.list_items(limit=10000)
    annotated = [item for item in items if item["annotations"]]
    report = speech.latest_report()
    script_words = 0
    if SCRIPT.exists():
        script_words = len(SCRIPT.read_text(encoding="utf-8").split())
    return {
        "streak": _streak(days),
        "week": week,
        "sessions": len(rows),
        "library": {
            "total": len(items),
            "annotated": len(annotated),
            "recent": items[:5],
        },
        "anki": anki.status(),
        "lastReport": report,
        "scriptWords": script_words,
        "phrases": len(writing.phrases()),
        "activity": rows[:8],
        "today": sum(
            1 for row in rows if datetime.fromisoformat(row["at"]).date() == date.today()
        ),
    }
