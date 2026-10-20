"""Shared constants, geometry and entity builders for Guess the Item 4.0."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data" / "versions.json").read_text(encoding="utf-8"))
PALETTE = json.loads((ROOT / "data" / "palette.json").read_text(encoding="utf-8"))
ART = json.loads((ROOT / "data" / "art.json").read_text(encoding="utf-8"))

VERSIONS = [
    {
        "key": "1.21.11",
        "slug": "1_21_11",
        "pack_format": 94,
        "pack_format_minor": 1,
        "label": "1.21.11",
        "file": "Guess_the_item_1.21.11_v4.zip",
    },
    {
        "key": "26.2",
        "slug": "26_2",
        "pack_format": 107,
        "pack_format_minor": 1,
        "label": "26.2",
        "file": "Guess_the_item_26.2_v4.zip",
    },
    {
        "key": "26.3",
        "slug": "26_3",
        "pack_format": 121,
        "pack_format_minor": 0,
        "label": "26.3",
        "file": "Guess_the_item_26.3_v4.zip",
    },
]

# ---- palette -------------------------------------------------------------
CYAN = "#45E9E0"
AQUA = "#61EDE5"
BLUE = "#79C4F8"
PURPLE = "#B295FF"
MAGENTA = "#F47BC6"
GOLD = "#F6CF84"
RED = "#FF8996"
GREEN = "#8BE28B"
WHITE = "#F2F7FF"
MUTED = "#8FA8C8"

# ---- board metrics -------------------------------------------------------
COLS = 16
ROWS = 16
CELLS = COLS * ROWS

X0 = -(COLS - 1) / 2.0          # -7.5  centre of the left column
Y0 = 3.0                        # centre of the bottom row of the window
Z_ART = 0.00                    # art / bedrock cell plane
Z_BACKING = -0.34               # dark backing behind the cells
Z_CLICK = 0.62                  # clickable interaction plane
Z_SHUTTER = 0.86                # bedrock curtain in front of the board
Z_STONE = 0.16                  # stone frame ring

WALL_LEFT = -12
WALL_RIGHT = 12                 # inclusive block columns
WALL_BOTTOM = 0
WALL_TOP = 26

FRAME_LEFT = -8.5
FRAME_RIGHT = 8.5
FRAME_BOTTOM = 2
FRAME_TOP = 19

STRIP_Y = 21.6                  # centre of the attempt pips
STRIP_LEFT = -8.0
STRIP_PITCH = 0.5
STRIP_MAX = 32

VIEW_Z = 30.0
VIEW_YAW = 180.0
VIEW_PITCH = -17.0


def fnum(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text if text not in ("-0", "") else "0"


def tags(*values: str) -> str:
    return ",".join(f'"{v}"' for v in values)


def _tup(values) -> str:
    return "[" + ",".join(f"{fnum(v)}f" for v in values) + "]"


def block_display(
    block: str,
    cx: float,
    cy: float,
    cz: float,
    sx: float,
    sy: float,
    sz: float,
    tag_list: tuple[str, ...],
    *,
    extra: str = "",
    view_range: float = 4.0,
    pivot_center: bool = True,
    transformation: dict | None = None,
) -> str:
    """Summon a block display; by default the given point is the cube centre."""
    ox = cx - sx / 2.0 if pivot_center else cx
    oy = cy - sy / 2.0 if pivot_center else cy
    oz = cz - sz / 2.0 if pivot_center else cz
    extra_part = f",{extra}" if extra else ""
    if transformation is None:
        transform = (
            f"{{scale:{_tup((sx, sy, sz))},translation:[0f,0f,0f],"
            f"left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}"
        )
    else:
        scale = transformation.get("scale", [sx, sy, sz])
        translation = transformation.get("translation", [0.0, 0.0, 0.0])
        transform = (
            f"{{scale:{_tup(scale)},translation:{_tup(translation)},"
            f"left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}"
        )
    return (
        f"summon block_display ~{fnum(ox)} ~{fnum(oy)} ~{fnum(oz)} "
        f'{{Tags:[{tags(*tag_list)}],block_state:{{Name:"minecraft:{block}"}},'
        f"brightness:{{sky:15,block:15}},view_range:{fnum(view_range)}f,"
        f"transformation:{transform}"
        f"{extra_part}}}"
    )


def text_display(
    component,
    x: float,
    y: float,
    z: float,
    scale: float = 1.0,
    *,
    tag_list: tuple[str, ...] = ("gti.entity", "gti.text"),
    extra: str = "",
    extra_scale: tuple[float, float, float] | None = None,
    align: str = "center",
    line_width: int = 1000,
    shadow: bool = True,
) -> str:
    if isinstance(component, (dict, list)):
        text = json.dumps(component, ensure_ascii=False, separators=(",", ":"))
    else:
        text = component
    sx, sy, sz = extra_scale or (scale, scale, scale)
    extra_part = f",{extra}" if extra else ""
    return (
        f"summon text_display ~{fnum(x)} ~{fnum(y)} ~{fnum(z)} "
        f'{{Tags:[{tags(*tag_list)}],text:{text},background:0,'
        f"shadow:{1 if shadow else 0}b,see_through:0b,alignment:\"{align}\","
        f"line_width:{line_width},brightness:{{sky:15,block:15}},"
        f"view_range:8f,transformation:{{scale:{_tup((sx, sy, sz))},"
        f"translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}"
        f"{extra_part}}}"
    )


def interaction(
    cx: float,
    cy: float,
    cz: float,
    width: float,
    height: float,
    tag_list: tuple[str, ...],
    *,
    extra: str = "",
) -> str:
    extra_part = f",{extra}" if extra else ""
    return (
        f"summon interaction ~{fnum(cx)} ~{fnum(cy)} ~{fnum(cz)} "
        f"{{width:{fnum(width)}f,height:{fnum(height)}f,response:1b,"
        f"Tags:[{tags(*tag_list)}]{extra_part}}}"
    )


def line(text: str = "", color: str = WHITE, bold: bool = False) -> dict:
    comp: dict = {"text": text, "color": color}
    if bold:
        comp["bold"] = True
    return comp


def gradient(text: str, start: str, end: str, bold: bool = True) -> dict:
    """Character-by-character colour gradient as an ``extra`` list."""
    sr, sg, sb = (int(start[i : i + 2], 16) for i in (1, 3, 5))
    er, eg, eb = (int(end[i : i + 2], 16) for i in (1, 3, 5))
    parts = []
    span = max(1, len(text) - 1)
    for index, char in enumerate(text):
        t = index / span
        r = round(sr + (er - sr) * t)
        g = round(sg + (eg - sg) * t)
        b = round(sb + (eb - sb) * t)
        comp: dict = {"text": char, "color": f"#{r:02X}{g:02X}{b:02X}"}
        if bold:
            comp["bold"] = True
        parts.append(comp)
    return {"text": "", "extra": parts}


def mc(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"
