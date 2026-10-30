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
ICONS = {"dark": ROOT / "assets" / "prism-dark.ico", "light": ROOT / "assets" / "prism-light.ico"}

# Keep these in sync with the CSS custom properties in app/web/styles.css.
CAPTION = {
    "dark": {"bg": "#0f1116", "text": "#e9e5dd", "border": "#262b35", "dark": True},
    "light": {"bg": "#f5f2ec", "text": "#22262d", "border": "#d7d1c5", "dark": False},
}

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_NONE = 1

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


def cref(value: str) -> int:
    """Windows caption colors are COLORREF (0x00BBGGRR), not the palette's RGB order."""
    r, g, b = int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)
    return (b << 16) | (g << 8) | r


def find_own_window() -> int | None:
    """Our own window, by process id: Prism.bat titles its console 'Prism' too."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    me = os.getpid()
    found: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value != me:
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if buffer.value == "Prism":
            found.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(callback, 0)
    return found[0] if found else None


def set_icon(hwnd: int, theme: str) -> None:
    import ctypes
    from ctypes import wintypes

    path = ICONS.get(theme, ICONS["dark"])
    if not path.exists():
        return
    user32 = ctypes.windll.user32
    load = user32.LoadImageW
    load.restype = ctypes.c_void_p
    for kind in (1, 0):  # ICON_BIG (taskbar), ICON_SMALL (caption)
        handle = load(None, str(path), 1, 0, 0, 0x00000010 | 0x00000040)
        if handle:
            user32.SendMessageW(wintypes.HWND(hwnd), 0x0080, kind, ctypes.c_void_p(handle))


def apply_caption(hwnd: int, theme: str) -> None:
    """Paint the native caption to match the workbench instead of the OS theme."""
    import ctypes
    from ctypes import wintypes

    colors = CAPTION.get(theme, CAPTION["dark"])
    handle = wintypes.HWND(hwnd)
    dwm = ctypes.windll.dwmapi
    # A backdrop (Mica/Auto) repaints the caption from the desktop, so it has to go.
    for attribute, value in (
        (DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if colors["dark"] else 0),
        (DWMWA_SYSTEMBACKDROP_TYPE, DWMSBT_NONE),
        (DWMWA_CAPTION_COLOR, cref(colors["bg"])),
        (DWMWA_TEXT_COLOR, cref(colors["text"])),
        (DWMWA_BORDER_COLOR, cref(colors["border"])),
    ):
        dwm.DwmSetWindowAttribute(handle, attribute, ctypes.byref(ctypes.c_int(value)), ctypes.sizeof(ctypes.c_int))
    set_icon(hwnd, theme)


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

    def bind(self, hwnd: int) -> None:
        self.hwnd = hwnd
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
    """Claim the caption away from pywebview, which paints it from the OS theme."""
    for _ in range(80):
        try:
            import webview

            form = getattr(webview.windows[0], "native", None) if webview.windows else None
            hwnd = int(form.Handle.ToInt64()) if form is not None else None
        except Exception:
            hwnd = None
        if not hwnd:
            hwnd = find_own_window()
        if hwnd:
            if form is not None:
                # pywebview calls this on startup and on every OS theme change.
                form.update_title_bar_theme = lambda: apply_caption(hwnd, bridge.theme)
            bridge.bind(hwnd)
            return
        time.sleep(0.2)


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
        profile = SUITE / "data" / "webview"
        profile.mkdir(parents=True, exist_ok=True)
        webview.start(
            icon=str(ICONS["dark"]) if ICONS["dark"].exists() else None,
            private_mode=False,
            storage_path=str(profile),
        )
        del window
    except Exception:
        import traceback

        traceback.print_exc()
        open_browser(url)


if __name__ == "__main__":
    main()
