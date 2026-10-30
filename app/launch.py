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
ICON = ROOT / "assets" / "prism.ico"

# Windows caption colors are COLORREF values (0x00BBGGRR), not RGB.
CAPTION_COLORS = {
    "dark": {"caption": 0x0016110F, "text": 0x00DDE5E9, "border": 0x00352B26},
    "light": {"caption": 0x00F0F5F7, "text": 0x002D2623, "border": 0x00CBD7DD},
}

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


def find_window(title: str) -> int | None:
    """Locate our top-level window without touching WinForms from another thread."""
    import ctypes

    user32 = ctypes.windll.user32
    found: list[int] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if buffer.value == title:
            found.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(callback, None)
    return found[0] if found else None


def apply_caption(hwnd: int, theme: str) -> None:
    """Paint the native caption to match the workbench instead of the OS theme."""
    import ctypes

    colors = CAPTION_COLORS.get(theme, CAPTION_COLORS["dark"])
    dark = 1 if theme != "light" else 0
    dwm = ctypes.windll.dwmapi
    for attribute, value in ((20, dark), (35, colors["caption"]), (36, colors["text"]), (34, colors["border"])):
        dwm.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(ctypes.c_int(value)), ctypes.sizeof(ctypes.c_int))

    if ICON.exists():
        user32 = ctypes.windll.user32
        load = user32.LoadImageW
        load.restype = ctypes.c_void_p
        for kind in (1, 0):  # ICON_BIG, ICON_SMALL
            handle = load(None, str(ICON), 1, 0, 0, 0x00000010 | 0x00000040)
            if handle:
                user32.SendMessageW(hwnd, 0x0080, kind, ctypes.c_void_p(handle))


def set_app_identity() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Lumenhao.Prism")
    except Exception:
        pass


class ThemeBridge:
    """Called from JS so the caption follows the in-app theme."""

    def __init__(self) -> None:
        self.theme = "dark"
        self.hwnd: int | None = None

    def _attach(self, hwnd: int | None) -> None:
        self.hwnd = hwnd
        if hwnd:
            apply_caption(hwnd, self.theme)

    def set_theme(self, theme: str) -> bool:
        self.theme = "light" if theme == "light" else "dark"
        if self.hwnd:
            apply_caption(self.hwnd, self.theme)
        return True


def screen_size() -> tuple[float, float]:
    try:
        import ctypes

        scale = ctypes.windll.user32.GetDpiForSystem() / 96
        return ctypes.windll.user32.GetSystemMetrics(0) / scale, ctypes.windll.user32.GetSystemMetrics(1) / scale
    except Exception:
        return 1920.0, 1080.0


def attach_chrome(bridge: ThemeBridge) -> None:
    for _ in range(60):
        hwnd = find_window("Prism")
        if hwnd:
            bridge._attach(hwnd)
            return
        time.sleep(0.25)


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
    set_app_identity()
    if os.environ.get("PRISM_HIDE_CONSOLE") == "1" and os.name == "nt":
        try:
            import ctypes

            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass

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

    bridge = ThemeBridge()
    try:
        import webview

        screen_w, screen_h = screen_size()
        width = int(min(1440, max(1024, screen_w * 0.92)))
        height = int(min(920, max(640, screen_h * 0.86)))
        window = webview.create_window(
            "Prism",
            url,
            width=width,
            height=height,
            x=max(0, int((screen_w - width) / 2)),
            y=max(0, int((screen_h - height) / 2)),
            min_size=(min(1080, width), min(660, height)),
            background_color="#0f1116",
            js_api=bridge,
        )
        threading.Thread(target=attach_chrome, args=(bridge,), daemon=True).start()
        webview.start(icon=str(ICON) if ICON.exists() else None)
        del window
    except Exception:
        import traceback

        traceback.print_exc()
        open_browser(url)


if __name__ == "__main__":
    main()
