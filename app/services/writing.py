"""Phrasebank and conservative writing checks for Prism."""
from __future__ import annotations

import csv
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ..core import ROOT, TOOLS

CSV_PATH = ROOT / "writing" / "phrasebank" / "phrasebank_seed.csv"
VALE_INI = ROOT / "writing" / ".vale.ini"
VAGUE = {
    "very", "really", "quite", "rather", "somewhat", "a lot", "lots of",
    "obviously", "clearly", "of course", "interesting", "nice", "good", "bad",
    "big", "small", "thing", "things", "stuff", "etc.",
}
CONTRACTIONS = ["don't", "doesn't", "can't", "won't", "isn't", "aren't", "it's", "that's", "we're", "i'm"]
TERM_PAIRS = [
    (r"\bh-BN\b", "hBN", "六方氮化硼统一写作 hBN"),
    (r"\bF4TCNQ\b", "F4-TCNQ", "分子名统一写作 F4-TCNQ"),
    (r"\bSio2\b|\bSiO2\b", "SiO₂", "二氧化硅统一写作 SiO₂"),
]


def phrases() -> list[dict[str, Any]]:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for index, row in enumerate(rows, 1):
        row["id"] = index
    return rows


def _vale(text: str) -> list[dict[str, Any]] | None:
    vale = TOOLS / "vale" / "vale.exe"
    if not vale.exists():
        return None
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "paragraph.txt"
        target.write_text(text, encoding="utf-8")
        try:
            result = subprocess.run(
                [str(vale), "--config", str(VALE_INI), "--output", "JSON", str(target)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        try:
            payload = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            return None
        issues = []
        for _file, alerts in payload.items():
            for alert in alerts:
                issues.append(
                    {
                        "line": alert.get("Line", 1),
                        "column": alert.get("Span", [1, 1])[0],
                        "severity": alert.get("Severity", "warning"),
                        "message": alert.get("Message", ""),
                        "rule": alert.get("Check", ""),
                        "suggestion": alert.get("Action", {}).get("Name", ""),
                    }
                )
        return issues


def _builtin(text: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    lines = text.splitlines() or [""]
    for number, line in enumerate(lines, 1):
        for word in VAGUE:
            for match in re.finditer(rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])", line, re.I):
                issues.append(
                    {
                        "line": number,
                        "column": match.start() + 1,
                        "severity": "suggestion",
                        "message": f"“{match.group(0)}”偏口语或模糊，换成可检验的表述。",
                        "rule": "Clarity",
                    }
                )
        for contraction in CONTRACTIONS:
            for match in re.finditer(rf"(?<![A-Za-z]){re.escape(contraction)}(?![A-Za-z])", line, re.I):
                issues.append(
                    {
                        "line": number,
                        "column": match.start() + 1,
                        "severity": "warning",
                        "message": f"学术写作中避免缩写 “{match.group(0)}”。",
                        "rule": "Contractions",
                    }
                )
        for pattern, preferred, message in TERM_PAIRS:
            for match in re.finditer(pattern, line):
                if match.group(0) != preferred:
                    issues.append(
                        {
                            "line": number,
                            "column": match.start() + 1,
                            "severity": "error",
                            "message": message,
                            "rule": "Terminology",
                            "suggestion": preferred,
                        }
                    )
        lowered = line.lower()
        if re.search(r"\b(is|are|was|were|be|been|being)\s+\w+ed\b", lowered):
            issues.append(
                {
                    "line": number,
                    "column": 1,
                    "severity": "suggestion",
                    "message": "疑似被动语态；确认动作执行者是否重要。",
                    "rule": "Passive",
                }
            )
    for number, paragraph in enumerate(re.split(r"\n\s*\n", text), 1):
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
            words = re.findall(r"[A-Za-z][A-Za-z'-]*", sentence)
            if len(words) > 38:
                issues.append(
                    {
                        "line": number,
                        "column": 1,
                        "severity": "warning",
                        "message": f"句子有 {len(words)} 个词，建议拆成两句。",
                        "rule": "SentenceLength",
                    }
                )
    return issues


def check(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        return {"issues": [], "stats": {}, "engine": "none"}
    vale_issues = _vale(text)
    issues = vale_issues if vale_issues is not None else _builtin(text)
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'./-]*", text)
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    long_sentences = sum(
        1 for s in sentences if len(re.findall(r"[A-Za-z][A-Za-z'-]*", s)) > 35
    )
    passive = len(re.findall(r"\b(?:is|are|was|were|be|been|being)\s+\w+ed\b", text, re.I))
    return {
        "issues": issues[:80],
        "engine": "vale" if vale_issues is not None else "builtin",
        "stats": {
            "words": len(words),
            "sentences": len(sentences),
            "avgSentence": round(len(words) / len(sentences), 1) if sentences else 0,
            "longSentences": long_sentences,
            "passive": passive,
            "errors": sum(1 for i in issues if i["severity"] == "error"),
            "warnings": sum(1 for i in issues if i["severity"] == "warning"),
        },
    }


def suggest(query: str, limit: int = 6) -> list[dict[str, Any]]:
    query = query.lower().strip()
    rows = phrases()
    if not query:
        return rows[:limit]
    scored = []
    for row in rows:
        haystack = " ".join(row.values()).lower()
        score = sum(1 for token in re.findall(r"[a-z\u4e00-\u9fff]+", query) if token in haystack)
        if score:
            scored.append((score, row))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [row for _, row in scored[:limit]] or rows[:limit]
