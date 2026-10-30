"""Render the two Prism window icons (one per theme) into assets/.

The caption and taskbar paint whatever ICO we hand them, so the artwork has to
carry its own background: a dark tile disappears in the light caption and a
light tile disappears in the dark one.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
SIZE = 512
SUPERSAMPLE = 4

THEMES = {
    "dark": {
        "tile": "#101218",
        "edge": "#262b35",
        "prism": "#e8a091",
        "beam": "#f4efe6",
        "spectrum": ["#d9b26f", "#83b7a8", "#a79bd8", "#e8a091"],
    },
    "light": {
        "tile": "#f5f2ec",
        "edge": "#d7d1c5",
        "prism": "#b85c4a",
        "beam": "#2b2f36",
        "spectrum": ["#96701c", "#3c7c6b", "#6a5aa6", "#b85c4a"],
    },
}


def line(draw: ImageDraw.ImageDraw, x1, y1, x2, y2, width, colour):
    draw.line((x1, y1, x2, y2), fill=colour, width=width)
    r = width / 2
    for cx, cy in ((x1, y1), (x2, y2)):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=colour)


def render(theme: dict[str, str | list[str]]) -> Image.Image:
    canvas = Image.new("RGBA", (SIZE * SUPERSAMPLE,) * 2, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    s = SIZE * SUPERSAMPLE
    radius = int(s * 0.225)
    draw.rounded_rectangle((0, 0, s - 1, s - 1), radius=radius, fill=theme["tile"], outline=theme["edge"], width=int(s * 0.012))

    stroke = int(s * 0.062)
    apex, left, right = (s * 0.5, s * 0.155), (s * 0.21, s * 0.82), (s * 0.79, s * 0.82)
    for a, b in ((apex, left), (left, right), (right, apex)):
        line(draw, a[0], a[1], b[0], b[1], stroke, theme["prism"])

    beam_y = s * 0.52
    line(draw, s * 0.085, beam_y, s * 0.335, beam_y, int(s * 0.055), theme["beam"])

    origin = (s * 0.665, s * 0.505)
    for colour, angle in zip(theme["spectrum"], (-16.0, -1.0, 14.0, 29.0)):
        rad = math.radians(angle)
        end = (origin[0] + math.cos(rad) * s * 0.30, origin[1] + math.sin(rad) * s * 0.30)
        line(draw, origin[0], origin[1], end[0], end[1], int(s * 0.05), colour)

    return canvas.resize((SIZE, SIZE), Image.LANCZOS)


def write(name: str, image: Image.Image) -> Path:
    path = OUT / name
    image.save(path)
    if name.endswith(".ico"):
        image.save(path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for theme, name in (("dark", "prism-dark"), ("light", "prism-light")):
        image = render(THEMES[theme])
        print(write(f"{name}.png", image))
        print(write(f"{name}.ico", image))
    dark = render(THEMES["dark"])
    print(write("prism.png", dark))
    print(write("prism.ico", dark))
    dark.resize((64, 64), Image.LANCZOS).save(OUT / "prism-64.png")
    print(OUT / "prism-64.png")


if __name__ == "__main__":
    main()
