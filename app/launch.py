"""Start the Prism server and open it as a desktop window."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
sys.path.insert(0, str(ROOT))
SUITE = Path(os.environ.get("LUMEN_SUITE", "E:/LumenSuite"))

if sys.stdout is None or sys.stderr is None:
    log_dir = ROOT / "data"
    log_dir.mkdir(parents=True, exist_ok=True)
    stream = open(log_dir / "launch.log", "a", buffering=1, encoding="utf-8")
    sys.stdout = sys.stdout or stream
    sys.stderr = sys.stderr or stream

for key, value in {
    "HF_HOME": SUITE / "models" / "hf",
    "HF_ENDPOINT": "https://hf-mirror.com",
    "HF_HUB_DISABLE_XET": "1",
    "XDG_CACHE_HOME": SUITE / "cache",
    "TORCH_HOME": SUITE / "models" / "torch",
    "PIP_CACHE_DIR": SUITE / "cache" / "pip",
    "UV_CACHE_DIR": SUITE / "cache" / "uv",
}.items():
    os.environ.setdefault(key, str(value))


def api_ready(port: int) -> bool:
    import http.client

    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2.0)
        conn.request("GET", "/api/health")
        response = conn.getresponse()
        response.read(1)
        conn.close()
        return response.status == 200
    except Exception:
        return False


def serve(port: int) -> None:
    import traceback

    import uvicorn

    try:
        uvicorn.run("app.server:APP", host="127.0.0.1", port=port, log_level="warning")
    except Exception:
        traceback.print_exc()


def open_browser(url: str) -> None:
    edge = next(
        (
            Path(path)
            for path in (
                r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
                r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
            )
            if Path(path).exists()
        ),
        None,
    )
    profile = SUITE / "data" / "edge-profile"
    profile.mkdir(parents=True, exist_ok=True)
    if edge:
        subprocess.Popen(
            [
                str(edge),
                f"--app={url}",
                f"--user-data-dir={profile}",
                "--window-size=1440,920",
                "--disable-features=Translate,msEdgeSidebarV2",
                "--no-first-run",
            ]
        )
    else:
        import webbrowser

        webbrowser.open(url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prism desktop launcher")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PRISM_PORT", "7317")))
    parser.add_argument("--browser", action="store_true", help="open in Edge app window")
    args = parser.parse_args()
    port = args.port
    url = f"http://127.0.0.1:{port}"

    if not api_ready(port):
        threading.Thread(target=serve, args=(port,), daemon=True).start()
    for _ in range(120):
        if api_ready(port):
            break
        time.sleep(0.2)
    else:
        print("Prism server did not start", file=sys.stderr)
        sys.exit(1)

    if args.browser:
        open_browser(url)
        return

    try:
        import webview

        window = webview.create_window(
            "Prism",
            url,
            width=1440,
            height=920,
            min_size=(1080, 700),
            background_color="#14161b",
        )
        webview.start()
        del window
    except Exception:
        import traceback

        traceback.print_exc()
        open_browser(url)


if __name__ == "__main__":
    main()
