"""Shared data and helpers for the Guess the Item 3.0 generator."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data" / "versions.json").read_text(encoding="utf-8"))

VERSIONS = [
    {
        "key": "1.21.11",
        "slug": "1_21_11",
        "pack_format": 94,
        "pack_format_minor": 1,
        "java": "1.21.11",
        "label": "1.21.11",
        "file": "Guess_the_item_1.21.11_v3.zip",
    },
    {
        "key": "26.2",
        "slug": "26_2",
        "pack_format": 107,
        "pack_format_minor": 1,
        "java": "26.2",
        "label": "26.2",
        "file": "Guess_the_item_26.2_v3.zip",
    },
    {
        "key": "26.3",
        "slug": "26_3",
        "pack_format": 121,
        "pack_format_minor": 0,
        "java": "26.3",
        "label": "26.3",
        "file": "Guess_the_item_26.3_v3.zip",
    },
]


def version_data(key: str) -> dict:
    return DATA[key]


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
DIM = "#5F7899"

# text display background, 0x7F alpha keeps the value inside a signed int
CARD_BG = 0x7F0B1220
CARD_BG_2 = 0x7F111C31
CHIP_BG = 0x7F16233A
RED_BG = 0x7F3A0B16
GREEN_BG = 0x7F0B2A1C

# board geometry -----------------------------------------------------------
TILE = 1.25
HALF = TILE * 8.0  # 10.0
BOARD_W = TILE * 16.0  # 20.0
PANEL_X = 15.0
PANEL_W = 7.6
PANEL_H = 23.6
MASK_Z = 0.10
ITEM_Z = 0.02
VIEW_Z = 30.0
VIEW_Y = 11.0
VIEW_PITCH = -17.0
VIEW_YAW = 180.0


def fnum(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text if text not in ("-0", "") else "0"


def tags(*values: str) -> str:
    return ",".join(f'"{v}"' for v in values)


def block_display(
    block: str,
    cx: float,
    cy: float,
    w: float,
    h: float,
    z: float,
    thick: float = 0.04,
    tag_list: tuple[str, ...] = ("gti.entity", "gti.decor"),
    extra: str = "",
    view_range: float = 4.0,
) -> str:
    x = cx - w / 2.0
    y = cy - h / 2.0
    extra_part = f",{extra}" if extra else ""
    return (
        f"summon block_display ~{fnum(x)} ~{fnum(y)} ~{fnum(z)} "
        f'{{Tags:[{tags(*tag_list)}],block_state:{{Name:"minecraft:{block}"}},'
        f"brightness:{{sky:15,block:15}},view_range:{fnum(view_range)}f,"
        f"transformation:{{scale:[{fnum(w)}f,{fnum(h)}f,{fnum(thick)}f],"
        f"translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}"
        f"{extra_part}}}"
    )


def text_display(
    component: dict | str,
    x: float,
    y: float,
    z: float,
    scale: float = 1.0,
    align: str = "center",
    background: int = 0,
    tag_list: tuple[str, ...] = ("gti.entity", "gti.text"),
    line_width: int = 1000,
    shadow: bool = True,
    extra: str = "",
    view_range: float = 4.0,
) -> str:
    if isinstance(component, dict):
        text = json.dumps(component, ensure_ascii=False, separators=(",", ":"))
    else:
        text = component
    extra_part = f",{extra}" if extra else ""
    return (
        f"summon text_display ~{fnum(x)} ~{fnum(y)} ~{fnum(z)} "
        f'{{Tags:[{tags(*tag_list)}],text:{text},background:{background},'
        f"shadow:{1 if shadow else 0}b,see_through:0b,alignment:\"{align}\","
        f"line_width:{line_width},brightness:{{sky:15,block:15}},view_range:{fnum(view_range)}f,"
        f"transformation:{{scale:[{fnum(scale)}f,{fnum(scale)}f,{fnum(scale)}f],"
        f"translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}"
        f"{extra_part}}}"
    )


def item_display(
    item: str,
    x: float,
    y: float,
    z: float,
    scale: float = 1.0,
    tag_list: tuple[str, ...] = ("gti.entity", "gti.icon"),
    extra: str = "",
    view_range: float = 4.0,
    rotation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
) -> str:
    extra_part = f",{extra}" if extra else ""
    return (
        f"summon item_display ~{fnum(x)} ~{fnum(y)} ~{fnum(z)} "
        f'{{Tags:[{tags(*tag_list)}],item:{{id:"minecraft:{item}",count:1}},'
        f'item_display:"gui",brightness:{{sky:15,block:15}},view_range:{fnum(view_range)}f,'
        f"transformation:{{scale:[{fnum(scale)}f,{fnum(scale)}f,0.001f],"
        f"translation:[0f,0f,0f],left_rotation:[{rotation[0]:g}f,{rotation[1]:g}f,{rotation[2]:g}f,{rotation[3]:g}f],"
        f"right_rotation:[0f,0f,0f,1f]}}"
        f"{extra_part}}}"
    )


def interaction(
    cx: float,
    cy: float,
    z: float,
    width: float,
    height: float,
    tag_list: tuple[str, ...],
) -> str:
    return (
        f"summon interaction ~{fnum(cx)} ~{fnum(cy)} ~{fnum(z)} "
        f'{{width:{fnum(width)}f,height:{fnum(height)}f,response:1b,Tags:[{tags(*tag_list)}]}}'
    )


def title_component(text: str, color: str = CYAN, bold: bool = True) -> dict:
    return {"text": text, "color": color, "bold": bold}


def line(text: str = "", color: str = WHITE, bold: bool = False) -> dict:
    comp = {"text": text, "color": color}
    if bold:
        comp["bold"] = True
    return comp


def mc(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"
