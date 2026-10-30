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
RAW = ROOT / "data" / "shots"
DOCS = ROOT / "assets" / "screenshots"
SITE = ROOT / "site" / "assets"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
BASE = "http://127.0.0.1:7317/"

ROUTES = [
    ("overview", "overview"),
    ("library", "library"),
    ("speak", "speak"),
    ("report", "speak/analyze"),
    ("write", "write"),
    ("vocab", "vocab"),
    ("settings", "settings"),
]
# The landing page swaps screenshots with its own theme, so every view is shot twice.
# The dark pass keeps the bare file name so the existing docs links stay valid.
SHOTS = [
    (f"{name}-light" if theme == "light" else name, f"{BASE}?theme={theme}#/{route}")
    for name, route in ROUTES
    for theme in ("dark", "light")
]
# The extension popup only exists inside a browser, so the fixture in scripts/ fakes one.
SHOTS.append(("clip", (ROOT / "scripts" / "clip-preview.html").as_uri()))

WIDTH, HEIGHT, SCALE = 1440, 900, 2


def capture(name: str, url: str, timeout: int = 90) -> Path:
    raw = RAW / f"raw-{name}.png"
    profile = Path(tempfile.mkdtemp(prefix="prism-shot-"))
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
        final = DOCS / f"{name}.png"
        im.save(final, optimize=True)
        im.save(SITE / f"{name}.webp", quality=82, method=6)
        if name == "overview":  # social preview wants a PNG
            im.save(SITE / "overview.png", optimize=True)
        return final
    finally:
        shutil.rmtree(profile, ignore_errors=True)
        raw.unlink(missing_ok=True)


def main() -> int:
    for folder in (RAW, DOCS, SITE):
        folder.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    for name, url in SHOTS:
        if only and name not in only:
            continue
        path = capture(name, url)
        print(f"{path.name}: {Image.open(path).size}")


if __name__ == "__main__":
    raise SystemExit(main())
