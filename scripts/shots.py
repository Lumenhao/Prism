"""Capture UI screenshots with headless Edge and downscale for docs."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "shots"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
BASE = "http://127.0.0.1:7317/"

SHOTS = [
    ("overview", "overview", "dark"),
    ("overview-light", "overview", "light"),
    ("library", "library", "dark"),
    ("speak", "speak", "dark"),
    ("report", "speak/analyze", "dark"),
    ("write", "write", "dark"),
    ("vocab", "vocab", "dark"),
    ("settings", "settings", "dark"),
    ("library-light", "library", "light"),
]

WIDTH, HEIGHT, SCALE = 1440, 900, 2


def capture(name: str, route: str, theme: str, timeout: int = 90) -> Path:
    raw = OUT / f"raw-{name}.png"
    profile = Path(tempfile.mkdtemp(prefix="prism-shot-"))
    url = f"{BASE}?theme={theme}#/{route}"
    cmd = [
        str(EDGE),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--disable-extensions",
        f"--force-device-scale-factor={SCALE}",
        f"--window-size={WIDTH},{HEIGHT}",
        "--virtual-time-budget=12000",
        f"--user-data-dir={profile}",
        f"--screenshot={raw}",
        url,
    ]
    try:
        subprocess.run(cmd, check=False, timeout=timeout, capture_output=True)
        deadline = time.time() + 5
        while time.time() < deadline and not raw.exists():
            time.sleep(0.2)
        if not raw.exists():
            raise SystemExit(f"capture failed: {name}")
        im = Image.open(raw).convert("RGB")
        target = (WIDTH, HEIGHT)
        if im.size != target:
            im = im.resize(target, Image.LANCZOS)
        final = OUT / f"{name}.png"
        im.save(final, optimize=True)
        return final
    finally:
        shutil.rmtree(profile, ignore_errors=True)
        raw.unlink(missing_ok=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    for name, route, theme in SHOTS:
        if only and name not in only:
            continue
        path = capture(name, route, theme)
        print(f"{path.name}: {Image.open(path).size}")


if __name__ == "__main__":
    raise SystemExit(main())
