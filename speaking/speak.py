#!/usr/bin/env python3
"""speak.py - Kokoro model audio, YouGlish links, Whisper + Praat review.

Examples:
  python speaking/speak.py tts speaking/samples/sample_talk.md --out speaking/samples/sample_talk.wav --chunks
  python speaking/speak.py links speaking/samples/sample_talk.md --out speaking/samples/youglish.md
  python speaking/speak.py check speaking/samples/take1.wav --script speaking/samples/sample_talk.md
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent

FILLERS = {"um", "uh", "erm", "er", "ah", "hmm", "mm"}
DISCOURSE = {"like", "basically", "actually", "literally", "honestly"}

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "than", "so", "because",
    "as", "of", "to", "in", "on", "at", "by", "for", "with", "from", "into",
    "about", "over", "under", "between", "through", "during", "before", "after",
    "is", "are", "was", "were", "be", "been", "being", "am",
    "do", "does", "did", "have", "has", "had",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "this", "that", "these", "those",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "not", "no", "yes", "there", "here", "which", "who", "whom", "whose", "what",
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "only", "own", "same", "too", "very",
    "just", "also", "now", "one", "two", "three",
}

NUM_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
    "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18",
    "nineteen": "19", "twenty": "20", "thirty": "30", "forty": "40",
    "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80",
    "ninety": "90", "hundred": "100", "thousand": "1000",
}


def load_config() -> dict:
    path = PROJECT / "config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"config.json 解析失败：{exc}")


def load_pronunciation() -> dict[str, str]:
    path = ROOT / "pronunciation.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return {k: v for k, v in data.items() if not k.startswith("_") and isinstance(v, str)}


FRONT_MATTER = re.compile(r"\A---[ \t]*\r?\n.*?(?:\r?\n)---[ \t]*(?:\r?\n|\Z)", re.S)


def strip_front_matter(text: str) -> str:
    return FRONT_MATTER.sub("", text.lstrip("\ufeff\x00 "), count=1)


def read_markdown(path: str | Path) -> str:
    return strip_front_matter(Path(path).read_text(encoding="utf-8-sig"))


def clean_markdown(text: str) -> str:
    text = strip_front_matter(text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"^\s{0,3}>.*(?:\n|$)", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def apply_pronunciation(text: str, mapping: dict[str, str]) -> str:
    for token in sorted(mapping, key=len, reverse=True):
        pattern = r"(?<![A-Za-z0-9])" + re.escape(token) + r"(?![A-Za-z0-9])"
        text = re.sub(pattern, mapping[token], text)
    return text


def norm_token(token: str) -> str:
    token = token.lower().replace("’", "'").replace("‘", "'")
    token = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", token)
    token = token.strip("'")
    return NUM_WORDS.get(token, token)


def tokenize(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", text)
    return [t for t in (norm_token(x) for x in raw) if t]


def term_keys(mapping: dict[str, str]) -> set[str]:
    keys: set[str] = set()
    for token in mapping:
        key = norm_token(token)
        keys.add(key)
        keys.add(key.replace("-", ""))
    return keys


def is_term(token: str, keys: set[str]) -> bool:
    return token in keys or token.replace("-", "") in keys


# ---------------------------------------------------------------- TTS


def cmd_tts(args: argparse.Namespace) -> None:
    cfg = load_config()
    voice = args.voice or cfg.get("speech", {}).get("kokoro_voice", "af_heart")
    text = clean_markdown(read_markdown(args.script))
    spoken = apply_pronunciation(text, load_pronunciation())
    blocks = paragraphs(spoken)
    if not blocks:
        sys.exit("脚本为空。")

    if args.dry_run:
        print(spoken)
        count = len(spoken.split())
        print(f"\n[words] {count}  [est @150 wpm] {count / 150:.1f} min")
        return

    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except ImportError as exc:
        sys.exit(
            f"缺少依赖：{exc}\n"
            "先运行 .\\setup_env.ps1，然后 .\\.venv\\Scripts\\python speaking\\speak.py ..."
        )

    pipeline = KPipeline(lang_code=args.lang)
    sr = 24000
    gap = np.zeros(int(sr * 0.35), dtype=np.float32)
    rendered: list[tuple[int, "np.ndarray"]] = []

    for idx, block in enumerate(blocks, 1):
        parts = []
        for _, _, audio in pipeline(block, voice=voice, speed=args.speed):
            if hasattr(audio, "detach"):
                audio = audio.detach().cpu().numpy()
            parts.append(np.asarray(audio, dtype=np.float32))
        if not parts:
            continue
        chunk = np.concatenate(parts)
        peak = float(np.max(np.abs(chunk))) if chunk.size else 0.0
        if peak > 0:
            chunk = chunk * (0.95 / peak)
        rendered.append((idx, chunk))

    if not rendered:
        sys.exit("Kokoro 没有生成音频。检查网络、voice 名称和 espeak-ng 安装。")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    full = np.concatenate([np.concatenate([c, gap]) for _, c in rendered])
    sf.write(out, full, sr, subtype="PCM_16")
    duration = len(full) / sr

    if args.chunks:
        for idx, chunk in rendered:
            chunk_path = out.with_name(f"{out.stem}-{idx:02d}{out.suffix}")
            sf.write(chunk_path, chunk, sr, subtype="PCM_16")
        print(f"分段：{len(rendered)} 个，前缀 {out.stem}-NN{out.suffix}")

    print(f"已写入：{out}")
    print(f"时长：{duration:.1f} s   voice={voice}   speed={args.speed}   sr={sr}")


# ------------------------------------------------------------- YouGlish


def sentence_for(term: str, text: str) -> str:
    pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])")
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if pattern.search(sentence):
            return " ".join(sentence.split())
    return ""


def marked_terms(text: str) -> list[str]:
    found = re.findall(r"\[\[([^\]]+)\]\]", text)
    unique: list[str] = []
    seen: set[str] = set()
    for item in found:
        key = item.strip().lower()
        if item.strip() and key not in seen:
            seen.add(key)
            unique.append(item.strip())
    return unique


def candidate_terms(text: str) -> list[str]:
    plain = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9-]*", plain)
    picked: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        low = token.lower()
        if low in STOPWORDS or low in seen:
            continue
        useful = (
            (token.isupper() and len(token) >= 2)
            or any(ch.isdigit() for ch in token)
            or "-" in token
            or len(token) >= 10
        )
        if useful:
            seen.add(low)
            picked.append(token)
    return picked[:40]


def cmd_links(args: argparse.Namespace) -> None:
    raw = read_markdown(args.script)
    text = clean_markdown(raw)
    terms = marked_terms(raw)
    source = "[[...]] 标记"
    if args.all or not terms:
        existing = {t.lower() for t in terms}
        terms += [t for t in candidate_terms(text) if t.lower() not in existing]
        source = "[[...]] 标记 + 自动候选" if marked_terms(raw) else "自动候选（未发现标记）"

    if not terms:
        sys.exit("脚本里没有可检索的词。用 [[term]] 标记，或使用 --all。")

    rows = []
    for term in terms:
        context = sentence_for(term, text)
        url = "https://youglish.com/pronounce/" + urllib.parse.quote(term, safe="") + f"/english/{args.accent}"
        rows.append((term, context, url))

    lines = [
        "# YouGlish 练习清单",
        "",
        f"- 脚本：`{Path(args.script).name}`",
        f"- 来源：{source}",
        f"- 口音筛选：`{args.accent}`（只是检索条件，不是质量等级）",
        "",
        "> 每个词先听 3 个片段：第 1 个跟读，第 2 个只听节奏，第 3 个关掉页面自己复述。",
        "",
        "| # | 词/短语 | 上下文 | YouGlish |",
        "|---|---------|--------|----------|",
    ]
    for idx, (term, context, url) in enumerate(rows, 1):
        safe_context = context.replace("|", "\\|")
        if len(safe_context) > 160:
            safe_context = safe_context[:157] + "..."
        lines.append(f"| {idx} | **{term}** | {safe_context} | [听]({url}) |")

    output = "\n".join(lines) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
        print(f"已写入：{out}（{len(rows)} 条）")
    else:
        print(output)


# ----------------------------------------------------------------- check


def resolve_model(model_name: str) -> str:
    """Prefer a model already unpacked under <suite>/models/whisper."""
    direct = Path(model_name)
    if direct.exists():
        return str(direct)
    suite = Path(os.environ.get("PRISM_SUITE", PROJECT.parent))
    local = suite / "models" / "whisper" / model_name
    if (local / "model.bin").exists():
        return str(local)
    return model_name


def transcribe(audio: Path, model_name: str) -> tuple[list[dict], object]:
    from faster_whisper import WhisperModel

    model = WhisperModel(resolve_model(model_name), device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(audio), language="en", word_timestamps=True, vad_filter=True, beam_size=5
    )
    words: list[dict] = []
    for seg in segments:
        if seg.words:
            for word in seg.words:
                words.append(
                    {
                        "text": word.word,
                        "start": float(word.start),
                        "end": float(word.end),
                        "prob": getattr(word, "probability", None),
                    }
                )
        else:
            for token in seg.text.split():
                words.append(
                    {"text": token, "start": float(seg.start), "end": float(seg.end), "prob": None}
                )
    return words, info


def prosody(audio: Path) -> dict:
    import numpy as np
    import parselmouth
    from parselmouth.praat import call

    sound = parselmouth.Sound(str(audio))
    duration = float(sound.get_total_duration())
    pitch = sound.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=500)
    freqs = pitch.selected_array["frequency"]
    voiced = freqs[freqs > 0]
    intensity = sound.to_intensity(minimum_pitch=75)
    levels = intensity.values[0]
    levels = levels[np.isfinite(levels)]

    pauses: list[tuple[float, float]] = []
    try:
        grid = call(sound, "To TextGrid (silences)", -25.0, 0.3, 0.1, "silent", "sounding")
        count = int(call(grid, "Get number of intervals", 1))
        for index in range(1, count + 1):
            if call(grid, "Get label of interval", 1, index) == "silent":
                start = float(call(grid, "Get starting time of interval", 1, index))
                end = float(call(grid, "Get end time of interval", 1, index))
                pauses.append((start, end))
    except Exception:
        grid = None

    pause_total = sum(end - start for start, end in pauses)
    return {
        "duration": duration,
        "pitch_mean": float(np.mean(voiced)) if voiced.size else 0.0,
        "pitch_p10": float(np.percentile(voiced, 10)) if voiced.size else 0.0,
        "pitch_p90": float(np.percentile(voiced, 90)) if voiced.size else 0.0,
        "intensity_mean": float(np.mean(levels)) if levels.size else 0.0,
        "pauses": pauses,
        "pause_total": pause_total,
        "voiced_duration": max(duration - pause_total, 0.0),
        "grid": grid,
    }


def align(ref: list[str], hyp: list[str]) -> tuple[list[dict], int, int, int]:
    matcher = difflib.SequenceMatcher(None, ref, hyp, autojunk=False)
    blocks: list[dict] = []
    subs = dels = ins = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        a = i2 - i1
        b = j2 - j1
        if tag == "replace":
            subs += min(a, b)
            dels += max(0, a - b)
            ins += max(0, b - a)
        elif tag == "delete":
            dels += a
        elif tag == "insert":
            ins += b
        blocks.append({"type": tag, "ref": ref[i1:i2], "hyp": hyp[j1:j2]})
    return blocks, subs, dels, ins


def meaningful(block: dict) -> bool:
    ref = [w for w in block["ref"] if w not in STOPWORDS]
    hyp = [w for w in block["hyp"] if w not in STOPWORDS]
    return bool(ref or hyp)


def cmd_check(args: argparse.Namespace) -> None:
    audio = Path(args.audio)
    if not audio.exists():
        sys.exit(f"找不到音频：{audio}")

    cfg = load_config()
    model_name = args.model or cfg.get("speech", {}).get("whisper_model", "base.en")
    script = clean_markdown(read_markdown(args.script))
    ref_tokens = tokenize(script)
    if not ref_tokens:
        sys.exit("脚本没有可比较的词。")

    asr_words: list[dict] = []
    asr_note = ""
    try:
        asr_words, info = transcribe(audio, model_name)
    except ImportError:
        asr_note = "未安装 faster-whisper，本次只做 Praat 声学指标。"
    except Exception as exc:
        asr_note = f"转写失败（{type(exc).__name__}: {exc}），本次只做 Praat 声学指标。"

    flat: list[dict] = []
    for word in asr_words:
        tokens = tokenize(word["text"])
        for token in tokens:
            flat.append({**word, "tok": token})
    hyp_tokens = [item["tok"] for item in flat]

    blocks: list[dict] = []
    subs = dels = ins = 0
    wer = 0.0
    content_wer = 0.0
    if flat:
        blocks, subs, dels, ins = align(ref_tokens, hyp_tokens)
        wer = (subs + dels + ins) / len(ref_tokens)
        ref_content = [t for t in ref_tokens if t not in STOPWORDS]
        hyp_content = [t for t in hyp_tokens if t not in STOPWORDS]
        if ref_content:
            _, cs, cd, ci = align(ref_content, hyp_content)
            content_wer = (cs + cd + ci) / len(ref_content)

    metrics = None
    prosody_note = ""
    try:
        metrics = prosody(audio)
    except ImportError:
        prosody_note = "未安装 praat-parselmouth，跳过音高、强度和停顿分析。"
    except Exception as exc:
        prosody_note = f"Praat 分析失败（{type(exc).__name__}: {exc}）。"

    duration = metrics["duration"] if metrics else 0.0
    voiced = metrics["voiced_duration"] if metrics else 0.0
    wpm = (len(ref_tokens) / (voiced / 60)) if voiced > 1 else 0.0
    pauses = metrics["pauses"] if metrics else []
    long_pauses = [(s, e) for s, e in pauses if e - s >= 1.0]
    pause_rate = (len(pauses) / (duration / 60)) if duration > 1 else 0.0
    pitch_range = (metrics["pitch_p90"] - metrics["pitch_p10"]) if metrics else 0.0
    fillers = [t for t in hyp_tokens if t in FILLERS]
    discourse = [t for t in hyp_tokens if t in DISCOURSE]

    keys = term_keys(load_pronunciation())
    issues = [
        block
        for block in blocks
        if meaningful(block)
        and not (block["ref"] and all(is_term(t, keys) for t in block["ref"]))
    ]
    term_issues = [
        block for block in blocks if block["ref"] and any(is_term(t, keys) for t in block["ref"])
    ]

    actions: list[str] = []
    if content_wer > 0.2 and flat:
        actions.append(f"内容词错误率 {content_wer * 100:.1f}%，先逐条听缺失的实词：是发音、连读还是用词问题。")
    if wpm > 175:
        actions.append(f"发声语速 {wpm:.0f} wpm 偏快；把关键句前的停顿拉长到 0.5-0.8 s。")
    elif 0 < wpm < 105:
        actions.append(f"发声语速 {wpm:.0f} wpm 偏慢；先删掉句中的犹豫停顿，再整体提速 10%。")
    if len(long_pauses) >= 2:
        actions.append(f"有 {len(long_pauses)} 次超过 1 s 的停顿；把长句拆成两个短句，或提前标记换气点。")
    if fillers:
        actions.append(f"检测到 {len(fillers)} 个填充词（{', '.join(sorted(set(fillers)))}）；每句开头先停 0.3 s 再开口。")
    if not actions and metrics and metrics["pitch_mean"] > 0 and pitch_range < 40:
        actions.append(f"音高 p10-p90 仅 {pitch_range:.0f} Hz，听感可能偏平；每个段落给一个重读词。")
    if not actions:
        if not metrics and not flat:
            actions.append("本机没有可用的分析依赖；先按 speaking/README.md 建好 .venv，或直接用 Buzz + Praat 检查。")
        else:
            actions.append("本轮没有明显硬伤；下一次换一位听众或换一个主题，检查迁移。")

    out = Path(args.out) if args.out else PROJECT / "reports" / f"check-{audio.stem}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# 口语复盘 - {audio.stem}",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 音频：`{audio}`",
        f"- 脚本：`{Path(args.script).name}`",
        f"- ASR：`{model_name}`" + ("（未运行）" if asr_note else ""),
        "",
    ]
    if asr_note:
        lines += [f"> {asr_note}", ""]
    if prosody_note:
        lines += [f"> {prosody_note}", ""]

    lines += ["## 一句话结论", ""]
    summary = []
    if metrics:
        summary.append(f"{duration:.1f} s，发声语速 {wpm:.0f} wpm，停顿 {len(pauses)} 次")
    if flat:
        summary.append(f"WER {wer * 100:.1f}%")
    lines += ["；".join(summary) + "。" if summary else "本机缺少分析依赖，未生成指标。", ""]
    lines += ["**优先修三件事**", ""]
    for idx, action in enumerate(actions[:3], 1):
        lines.append(f"{idx}. {action}")
    lines.append("")

    if metrics:
        lines += [
            "## 客观指标",
            "",
            "| 指标 | 数值 | 参考（不是及格线） |",
            "|------|------|--------------------|",
            f"| 总时长 | {duration:.1f} s | - |",
            f"| 发声语速 | {wpm:.0f} wpm | 清晰学术讲述常见 110-160 |",
            f"| 停顿次数 | {len(pauses)}（{pause_rate:.1f}/min） | 越少越连贯，但需保留换气 |",
            f"| 最长停顿 | {(max((e - s for s, e in pauses), default=0)):.1f} s | 关键句前 0.5-0.8 s 是有效停顿 |",
            f"| 音高均值 | {metrics['pitch_mean']:.0f} Hz | 因人而异 |",
            f"| 音高 p10-p90 | {metrics['pitch_p10']:.0f}-{metrics['pitch_p90']:.0f} Hz（跨度 {pitch_range:.0f}） | 跨度过小可能显得平 |",
            f"| 强度均值 | {metrics['intensity_mean']:.1f} dB | 受录音增益影响，只做同设备比较 |",
            "",
        ]
    if flat:
        lines += [
            "## 识别对齐",
            "",
            f"- 脚本词数：{len(ref_tokens)}",
            f"- WER：**{wer * 100:.1f}%**（替换 {subs}，缺失 {dels}，多出 {ins}）",
            f"- 内容词错误率：**{content_wer * 100:.1f}%**（已去掉功能词）",
            f"- 填充/话语标记：{len(fillers)} + {len(discourse)}（ASR 可能漏记，数值是下限）",
            "",
            "> WER 不是发音分数。ASR 对术语、数字、口音都会出错；先听报告里的差异，再判断是谁的问题。",
            "",
        ]
        if issues:
            lines += ["| 脚本 | 识别为 | 类型 |", "|------|--------|------|"]
            for block in issues[:20]:
                ref_text = " ".join(block["ref"]) or "-"
                hyp_text = " ".join(block["hyp"]) or "-"
                label = {"replace": "替换/听错", "delete": "缺失", "insert": "多出"}[block["type"]]
                lines.append(f"| {ref_text} | {hyp_text} | {label} |")
            if len(issues) > 20:
                lines.append(f"\n> 另有 {len(issues) - 20} 条未列出。")
            lines.append("")
        if term_issues:
            terms = sorted({t for block in term_issues for t in block["ref"] if is_term(t, keys)})
            lines += [
                "## 术语复核",
                "",
                "ASR 对专业词不可靠，下面这些地方需要人耳回听，不要直接算作发音错误：",
                "",
                "- " + "、".join(f"`{t}`" for t in terms),
                "",
            ]
        low_conf = [w for w in asr_words if w.get("prob") is not None and w["prob"] < 0.5]
        if low_conf:
            lines += ["## ASR 低置信词（先回听，再判断）", ""]
            for word in low_conf[:12]:
                lines.append(f"- `{word['text'].strip()}` @ {word['start']:.1f}s（p={word['prob']:.2f}）")
            lines.append("")

    lines += [
        "## 下一步",
        "",
        "1. 只挑上面 1-2 项，重录同一段 60-90 秒；",
        "2. 换一位真人听众，请对方复述主旨和一个细节；",
        "3. 把这次反复出错的 1-3 个词块加入 Anki（`Prism::Vocab` 或 `Phrases`）。",
        "",
        "> 自动指标只描述声音信号，不证明对方听懂了。最终证据仍然是听众能否复述、追问和执行。",
        "",
    ]

    out.write_text("\n".join(lines), encoding="utf-8")

    if args.textgrid and metrics and metrics.get("grid") is not None:
        grid_path = out.with_suffix(".TextGrid")
        try:
            from parselmouth.praat import call

            call(metrics["grid"], "Save as text file", str(grid_path))
            print(f"TextGrid：{grid_path}")
        except Exception as exc:
            print(f"TextGrid 未保存：{exc}")

    print(f"已写入：{out}")
    if flat:
        print(f"WER {wer * 100:.1f}%   内容词错误率 {content_wer * 100:.1f}%   语速 {wpm:.0f} wpm")
    else:
        print("未生成转写指标。")


# ------------------------------------------------------------------ CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kokoro / YouGlish / Whisper + Praat 口语工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    tts = sub.add_parser("tts", help="用 Kokoro 生成示范音")
    tts.add_argument("script")
    tts.add_argument("--out", required=True)
    tts.add_argument("--voice")
    tts.add_argument("--speed", type=float, default=0.95)
    tts.add_argument("--lang", default="a", choices=["a", "b"], help="a=美音，b=英音")
    tts.add_argument("--chunks", action="store_true", help="同时输出逐段音频")
    tts.add_argument("--dry-run", action="store_true", help="只打印替换后的文本")
    tts.set_defaults(func=cmd_tts)

    links = sub.add_parser("links", help="生成 YouGlish 练习清单")
    links.add_argument("script")
    links.add_argument("--out")
    links.add_argument("--accent", default="us", choices=["us", "uk", "aus"])
    links.add_argument("--all", action="store_true", help="除标记外加入自动候选")
    links.set_defaults(func=cmd_links)

    check = sub.add_parser("check", help="转写对齐 + Praat 声学复盘")
    check.add_argument("audio")
    check.add_argument("--script", required=True)
    check.add_argument("--out")
    check.add_argument("--model", help="faster-whisper 模型，默认读 config.json")
    check.add_argument("--textgrid", action="store_true", help="同时保存停顿 TextGrid")
    check.set_defaults(func=cmd_check)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
