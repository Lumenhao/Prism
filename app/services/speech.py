"""Kokoro, YouGlish and Whisper/Praat services for Prism."""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any, Callable

from ..core import AUDIO, REPORTS, get_module, load_config

_PIPELINE = None
_PIPELINE_KEY = ""


def _speak():
    return get_module("speak")


def _text_from(value: str) -> str:
    if value.startswith("file:"):
        path = Path(value[5:])
        return _speak().read_markdown(path)
    return value


def clean_script(value: str) -> str:
    return _speak().clean_markdown(_text_from(value))


def links(value: str, accent: str = "us", include_candidates: bool = False) -> list[dict[str, Any]]:
    speak = _speak()
    raw = _text_from(value)
    text = speak.clean_markdown(raw)
    terms = speak.marked_terms(raw)
    if include_candidates or not terms:
        existing = {term.lower() for term in terms}
        terms += [t for t in speak.candidate_terms(text) if t.lower() not in existing]
    rows = []
    for term in terms:
        rows.append(
            {
                "term": term,
                "context": speak.sentence_for(term, text),
                "url": "https://youglish.com/pronounce/"
                + urllib.parse.quote(term, safe="")
                + f"/english/{accent}",
            }
        )
    return rows


def pronunciation() -> list[dict[str, str]]:
    speak = _speak()
    return [{"term": key, "say": value} for key, value in speak.load_pronunciation().items()]


def tts(
    value: str,
    voice: str | None = None,
    speed: float = 0.95,
    lang: str = "a",
    progress: Callable[[str, float | None], None] | None = None,
) -> dict[str, Any]:
    progress = progress or (lambda *_: None)
    speak = _speak()
    cfg = load_config()
    voice = voice or cfg["speech"]["kokoro_voice"]
    text = speak.clean_markdown(_text_from(value))
    spoken = speak.apply_pronunciation(text, speak.load_pronunciation())
    blocks = speak.paragraphs(spoken)
    if not blocks:
        raise ValueError("脚本为空。")
    key = hashlib.sha1(f"{voice}|{speed}|{lang}|{spoken}".encode()).hexdigest()[:12]
    out = AUDIO / f"tts-{key}.wav"
    if out.exists():
        info = _audio_meta(out)
        info.update({"cached": True, "voice": voice, "speed": speed})
        return info

    progress("加载 Kokoro（首次会下载模型）", 0.1)
    global _PIPELINE, _PIPELINE_KEY
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    if _PIPELINE is None or _PIPELINE_KEY != lang:
        _PIPELINE = KPipeline(lang_code=lang)
        _PIPELINE_KEY = lang
    progress("合成语音", 0.35)

    sr = 24000
    gap = np.zeros(int(sr * 0.35), dtype=np.float32)
    rendered = []
    total = max(len(blocks), 1)
    for index, block in enumerate(blocks, 1):
        parts = []
        for _, _, audio in _PIPELINE(block, voice=voice, speed=speed):
            if hasattr(audio, "detach"):
                audio = audio.detach().cpu().numpy()
            parts.append(np.asarray(audio, dtype=np.float32))
        if parts:
            chunk = np.concatenate(parts)
            peak = float(np.max(np.abs(chunk))) if chunk.size else 0.0
            if peak > 0:
                chunk = chunk * (0.95 / peak)
            rendered.append(chunk)
        progress(f"第 {index}/{total} 段", 0.35 + 0.55 * index / total)

    if not rendered:
        raise RuntimeError("Kokoro 没有生成音频。检查网络或 espeak-ng。")
    full = np.concatenate([np.concatenate([chunk, gap]) for chunk in rendered])
    AUDIO.mkdir(parents=True, exist_ok=True)
    sf.write(out, full, sr, subtype="PCM_16")
    for old in AUDIO.glob("tts-*.wav"):
        if old != out and time.time() - old.stat().st_mtime > 7 * 86400:
            old.unlink(missing_ok=True)
    info = _audio_meta(out)
    info.update({"cached": False, "voice": voice, "speed": speed, "words": len(text.split())})
    progress("完成", 1.0)
    return info


def _audio_meta(path: Path) -> dict[str, Any]:
    import soundfile as sf

    info = sf.info(str(path))
    return {
        "file": path.name,
        "path": str(path),
        "url": f"/media/audio/{path.name}",
        "duration": float(info.duration),
        "sampleRate": info.samplerate,
    }


def waveform(path: Path, points: int = 320) -> list[float]:
    import numpy as np
    import soundfile as sf

    data, _ = sf.read(str(path), dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if mono.size == 0:
        return []
    chunk = max(1, mono.size // points)
    trimmed = mono[: chunk * points].reshape(points, chunk)
    peaks = np.max(np.abs(trimmed), axis=1)
    peak = float(peaks.max()) or 1.0
    return [round(float(value / peak), 3) for value in peaks]


def pitch_curve(path: Path, step: float = 0.03, points: int = 260) -> list[float]:
    import numpy as np
    import parselmouth

    sound = parselmouth.Sound(str(path))
    pitch = sound.to_pitch(time_step=step, pitch_floor=75, pitch_ceiling=500)
    freqs = pitch.selected_array["frequency"]
    freqs = np.where(freqs > 0, freqs, np.nan)
    if np.all(np.isnan(freqs)):
        return []
    idx = np.linspace(0, len(freqs) - 1, min(points, len(freqs))).astype(int)
    sampled = freqs[idx]
    low = float(np.nanpercentile(sampled, 5))
    high = float(np.nanpercentile(sampled, 95))
    span = high - low or 1.0
    return [None if np.isnan(v) else round(float((v - low) / span), 3) for v in sampled]


def analyze(
    audio_path: Path,
    script: str,
    model_name: str | None = None,
    progress: Callable[[str, float | None], None] | None = None,
) -> dict[str, Any]:
    progress = progress or (lambda *_: None)
    speak = _speak()
    cfg = load_config()
    model_name = model_name or cfg["speech"]["whisper_model"]
    text = speak.clean_markdown(_text_from(script))
    ref_tokens = speak.tokenize(text)
    if not ref_tokens:
        raise ValueError("脚本没有可比较的词。")

    progress("加载 Whisper 模型（首次会下载）", 0.1)
    asr_note = ""
    asr_words: list[dict] = []
    try:
        asr_words, _info = speak.transcribe(audio_path, model_name)
    except Exception as exc:
        asr_note = f"转写失败（{type(exc).__name__}: {exc}）"
    progress("对齐脚本", 0.62)

    flat = []
    for word in asr_words:
        for token in speak.tokenize(word["text"]):
            flat.append({**word, "tok": token})
    hyp_tokens = [item["tok"] for item in flat]
    blocks: list[dict] = []
    wer = content_wer = 0.0
    subs = dels = ins = 0
    if flat:
        blocks, subs, dels, ins = speak.align(ref_tokens, hyp_tokens)
        wer = (subs + dels + ins) / len(ref_tokens)
        ref_content = [t for t in ref_tokens if t not in speak.STOPWORDS]
        hyp_content = [t for t in hyp_tokens if t not in speak.STOPWORDS]
        if ref_content:
            _, cs, cd, ci = speak.align(ref_content, hyp_content)
            content_wer = (cs + cd + ci) / len(ref_content)

    progress("测量音高、强度与停顿", 0.78)
    metrics = None
    prosody_note = ""
    try:
        metrics = speak.prosody(audio_path)
    except Exception as exc:
        prosody_note = f"Praat 分析失败（{type(exc).__name__}: {exc}）"

    duration = metrics["duration"] if metrics else 0.0
    voiced = metrics["voiced_duration"] if metrics else 0.0
    wpm = (len(ref_tokens) / (voiced / 60)) if voiced > 1 else 0.0
    pauses = metrics["pauses"] if metrics else []
    long_pauses = [(s, e) for s, e in pauses if e - s >= 1.0]
    pause_rate = (len(pauses) / (duration / 60)) if duration > 1 else 0.0
    pitch_range = (metrics["pitch_p90"] - metrics["pitch_p10"]) if metrics else 0.0
    fillers = [t for t in hyp_tokens if t in speak.FILLERS]
    discourse = [t for t in hyp_tokens if t in speak.DISCOURSE]

    keys = speak.term_keys(speak.load_pronunciation())
    issues = [
        block
        for block in blocks
        if speak.meaningful(block)
        and not (block["ref"] and all(speak.is_term(t, keys) for t in block["ref"]))
    ]
    term_issues = [
        block for block in blocks if block["ref"] and any(speak.is_term(t, keys) for t in block["ref"])
    ]

    actions: list[str] = []
    if asr_note:
        actions.append("转写失败，WER 与缺失词不作结论；先修好 Whisper 模型，再看流利度。")
    if content_wer > 0.2 and flat:
        actions.append(f"内容词错误率 {content_wer * 100:.1f}%，先逐条听缺失的实词。")
    if wpm > 175:
        actions.append(f"发声语速 {wpm:.0f} wpm 偏快；在关键句前留 0.5–0.8 s 停顿。")
    elif 0 < wpm < 105:
        actions.append(f"发声语速 {wpm:.0f} wpm 偏慢；先删句中犹豫，再整体提速 10%。")
    if len(long_pauses) >= 2:
        actions.append(f"有 {len(long_pauses)} 次超过 1 s 的停顿；把长句拆短或标换气点。")
    if fillers:
        actions.append(f"检测到 {len(fillers)} 个填充词（{', '.join(sorted(set(fillers)))}）。")
    if not actions and metrics and metrics["pitch_mean"] > 0 and pitch_range < 40:
        actions.append(f"音高跨度仅 {pitch_range:.0f} Hz，每个段落给一个重读词。")
    if not actions:
        actions.append("本轮没有明显硬伤；下一次换一位听众，检查迁移。")

    progress("生成报告", 0.94)
    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "model": model_name,
        "asrNote": asr_note,
        "prosodyNote": prosody_note,
        "duration": round(duration, 2),
        "wpm": round(wpm, 1),
        "pauseRate": round(pause_rate, 1),
        "longPauses": len(long_pauses),
        "pauses": [[round(s, 2), round(e, 2)] for s, e in pauses],
        "pitchMean": round(metrics["pitch_mean"], 1) if metrics else 0,
        "pitchLow": round(metrics["pitch_p10"], 1) if metrics else 0,
        "pitchHigh": round(metrics["pitch_p90"], 1) if metrics else 0,
        "pitchRange": round(pitch_range, 1),
        "intensity": round(metrics["intensity_mean"], 1) if metrics else 0,
        "wer": round(wer, 4),
        "contentWer": round(content_wer, 4),
        "refWords": len(ref_tokens),
        "subs": subs,
        "dels": dels,
        "ins": ins,
        "fillers": len(fillers),
        "discourse": len(discourse),
        "actions": actions[:3],
        "issues": [
            {
                "ref": " ".join(block["ref"]),
                "hyp": " ".join(block["hyp"]),
                "type": block["type"],
            }
            for block in issues[:30]
        ],
        "terms": sorted({t for block in term_issues for t in block["ref"] if speak.is_term(t, keys)}),
        "waveform": _safe(waveform, audio_path, []),
        "pitch": _safe(pitch_curve, audio_path, []),
        "audioUrl": f"/media/audio/{audio_path.name}",
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", audio_path.stem)[:60]
    (REPORTS / f"{stem}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    progress("完成", 1.0)
    return report


def _safe(fn, path, default):
    try:
        return fn(path)
    except Exception:
        return default


def latest_report() -> dict[str, Any] | None:
    files = sorted(REPORTS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    try:
        report = json.loads(files[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    report["reportFile"] = files[0].name
    return report
