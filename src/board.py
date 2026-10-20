"""In-world board, HUD and visual effect generation."""

from __future__ import annotations

import json
import math

from model import (
    AQUA,
    BLUE,
    BOARD_W,
    CARD_BG,
    CARD_BG_2,
    CHIP_BG,
    CYAN,
    DIM,
    GOLD,
    GREEN,
    HALF,
    ITEM_Z,
    MAGENTA,
    MASK_Z,
    MUTED,
    PANEL_H,
    PANEL_W,
    PANEL_X,
    PURPLE,
    RED,
    RED_BG,
    TILE,
    WHITE,
    block_display,
    fnum,
    interaction,
    item_display,
    line,
    mc,
    text_display,
    title_component,
)


def _hex_mix(a: str, b: str, t: float) -> str:
    a = a.lstrip("#")
    b = b.lstrip("#")
    ca = [int(a[i : i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i : i + 2], 16) for i in (0, 2, 4)]
    cc = [round(ca[i] + (cb[i] - ca[i]) * t) for i in range(3)]
    return "#" + "".join(f"{v:02X}" for v in cc)


HEADER_TEXT = "GUESS THE ITEM"


def header_lines() -> list[str]:
    out: list[str] = []
    letters = [c for c in HEADER_TEXT if c != " "]
    count = len(letters)
    for idx, ch in enumerate(letters):
        t = idx / max(1, count - 1)
        color = _hex_mix(CYAN, MAGENTA, t)
        x = -8.55 + idx * 1.315
        comp = {"text": ch, "color": color, "bold": True}
        out.append(
            text_display(
                comp,
                x,
                11.45,
                0.35,
                scale=2.15,
                tag_list=("gti.entity", "gti.letter", "gti.text"),
            )
        )
        out.append(
            f"execute positioned ~{fnum(x)} ~11.45 ~0.35 run "
            f"scoreboard players set @e[tag=gti.letter,sort=nearest,limit=1] gti.id {idx}"
        )
    return out


def build_lines(vd: dict, count: int) -> list[str]:
    c = count
    deco: list[str] = ['summon marker ~ ~ ~ {Tags:["gti.entity","gti.anchor"]}']

    # deep backdrop ------------------------------------------------------
    deco += [
        block_display("black_concrete", 0, 0, 23.4, 23.4, -0.36, 0.10, ("gti.entity", "gti.decor")),
        block_display("blue_concrete", 0, 0, 22.5, 22.5, -0.30, 0.08, ("gti.entity", "gti.decor")),
        block_display("purple_concrete", 0, 0, 21.5, 21.5, -0.24, 0.07, ("gti.entity", "gti.decor", "gti.pulse.b")),
        block_display("black_concrete", 0, 0, 20.9, 20.9, -0.21, 0.06, ("gti.entity", "gti.decor")),
        block_display("tinted_glass", 0, 0, 20.6, 20.6, -0.17, 0.04, ("gti.entity", "gti.decor")),
        # outer glowing frame
        block_display("sea_lantern", 0, 10.55, 22.0, 0.16, 0.01, 0.06, ("gti.entity", "gti.decor", "gti.pulse.a")),
        block_display("sea_lantern", 0, -10.55, 22.0, 0.16, 0.01, 0.06, ("gti.entity", "gti.decor", "gti.pulse.a")),
        block_display("sea_lantern", -10.55, 0, 0.16, 22.0, 0.01, 0.06, ("gti.entity", "gti.decor", "gti.pulse.a")),
        block_display("sea_lantern", 10.55, 0, 0.16, 22.0, 0.01, 0.06, ("gti.entity", "gti.decor", "gti.pulse.a")),
        # inner accent rails
        block_display("cyan_concrete", 0, 10.2, 20.6, 0.10, 0.06, 0.04, ("gti.entity", "gti.decor", "gti.pulse.c")),
        block_display("cyan_concrete", 0, -10.2, 20.6, 0.10, 0.06, 0.04, ("gti.entity", "gti.decor", "gti.pulse.c")),
        block_display("cyan_concrete", -10.2, 0, 0.10, 20.6, 0.06, 0.04, ("gti.entity", "gti.decor", "gti.pulse.c")),
        block_display("cyan_concrete", 10.2, 0, 0.10, 20.6, 0.06, 0.04, ("gti.entity", "gti.decor", "gti.pulse.c")),
        # corner gems
        block_display("magenta_concrete", 0, 10.2, 0.85, 0.85, 0.08, 0.06, ("gti.entity", "gti.decor", "gti.pulse.b")),
        block_display("magenta_concrete", 0, -10.2, 0.85, 0.85, 0.08, 0.06, ("gti.entity", "gti.decor", "gti.pulse.b")),
        block_display("magenta_concrete", -10.2, 0, 0.85, 0.85, 0.08, 0.06, ("gti.entity", "gti.decor", "gti.pulse.b")),
        block_display("magenta_concrete", 10.2, 0, 0.85, 0.85, 0.08, 0.06, ("gti.entity", "gti.decor", "gti.pulse.b")),
        # corner brackets
        block_display("light_blue_concrete", -9.55, 9.95, 1.25, 0.12, 0.12, 0.04, ("gti.entity", "gti.decor")),
        block_display("light_blue_concrete", -9.95, 9.55, 0.12, 1.25, 0.12, 0.04, ("gti.entity", "gti.decor")),
        block_display("light_blue_concrete", 9.55, 9.95, 1.25, 0.12, 0.12, 0.04, ("gti.entity", "gti.decor")),
        block_display("light_blue_concrete", 9.95, 9.55, 0.12, 1.25, 0.12, 0.04, ("gti.entity", "gti.decor")),
        block_display("light_blue_concrete", -9.55, -9.95, 1.25, 0.12, 0.12, 0.04, ("gti.entity", "gti.decor")),
        block_display("light_blue_concrete", -9.95, -9.55, 0.12, 1.25, 0.12, 0.04, ("gti.entity", "gti.decor")),
        block_display("light_blue_concrete", 9.55, -9.95, 1.25, 0.12, 0.12, 0.04, ("gti.entity", "gti.decor")),
        block_display("light_blue_concrete", 9.95, -9.55, 0.12, 1.25, 0.12, 0.04, ("gti.entity", "gti.decor")),
        # floating shards around the frame
        block_display("ochre_froglight", -11.4, 7.2, 0.30, 0.30, -0.05, 0.30, ("gti.entity", "gti.decor")),
        block_display("pearlescent_froglight", -11.4, -7.2, 0.30, 0.30, -0.05, 0.30, ("gti.entity", "gti.decor")),
        block_display("ochre_froglight", 18.9, 7.2, 0.30, 0.30, -0.05, 0.30, ("gti.entity", "gti.decor")),
        block_display("pearlescent_froglight", 18.9, -7.2, 0.30, 0.30, -0.05, 0.30, ("gti.entity", "gti.decor")),
        # the answer item
        item_display("ender_eye", 0, 0, ITEM_Z, 20.0, ("gti.entity", "gti.item")),
    ]

    # panel -------------------------------------------------------------
    pw = PANEL_W
    ph = PANEL_H
    panel = [
        block_display("tinted_glass", PANEL_X, 0, pw, ph, -0.16, 0.06, ("gti.entity", "gti.panel")),
        block_display("cyan_concrete", PANEL_X, 11.55, pw, 0.16, 0.02, 0.05, ("gti.entity", "gti.panel", "gti.pulse.c")),
        block_display("magenta_concrete", PANEL_X, -11.55, pw, 0.16, 0.02, 0.05, ("gti.entity", "gti.panel", "gti.pulse.b")),
        block_display("black_concrete", PANEL_X - 3.25, 10.9, 0.09, 1.2, 0.03, 0.04, ("gti.entity", "gti.panel")),
        # stats card
        block_display("tinted_glass", PANEL_X, 4.35, 7.0, 8.5, -0.06, 0.04, ("gti.entity", "gti.panel")),
        # hint card
        block_display("tinted_glass", PANEL_X, -11.05, 7.0, 1.15, -0.06, 0.04, ("gti.entity", "gti.panel")),
        # budget bar backdrop
        block_display("black_concrete", PANEL_X, 0.16, 6.6, 0.22, -0.04, 0.03, ("gti.entity", "gti.panel")),
    ]
    for idx in range(10):
        panel.append(
            block_display(
                "gray_concrete",
                PANEL_X - 2.99 + idx * 0.665,
                0.16,
                0.56,
                0.14,
                -0.01,
                0.03,
                ("gti.entity", "gti.panel", "gti.budgetseg"),
            )
        )
        panel.append(
            f"execute positioned ~{fnum(PANEL_X - 2.99 + idx * 0.665)} ~0.16 ~-0.01 run "
            f"scoreboard players set @e[tag=gti.budgetseg,sort=nearest,limit=1] gti.id {idx}"
        )

    rows = [
        ("PRÓBY", "guesses"),
        ("PIKSELE", "pixels"),
        ("BŁĘDY", "wrong"),
        ("CZAS", "time"),
        ("PACZKA", "batch"),
        ("BUDŻET", "budget"),
    ]
    row_tags = []
    for idx, (label, key) in enumerate(rows):
        y = 7.9 - idx * 1.4
        panel.append(
            text_display(
                line(label, MUTED, True),
                PANEL_X - 3.05,
                y - 0.12,
                0.04,
                scale=0.58,
                align="left",
                tag_list=("gti.entity", "gti.text", "gti.panel"),
            )
        )
        panel.append(
            text_display(
                line("0", WHITE, True),
                PANEL_X + 3.05,
                y - 0.14,
                0.04,
                scale=1.02,
                align="right",
                tag_list=("gti.entity", "gti.text", "gti.panel", f"gti.hud.{key}"),
            )
        )
        row_tags.append(key)

    # buttons -----------------------------------------------------------
    buttons = [
        ("ODKRYJ PACZKĘ", "amethyst_shard", "reveal", CYAN, "gti.control.reveal"),
        ("ZGADUJ Z RĘKI", "iron_sword", "guess", GOLD, "gti.control.guess"),
        ("MENU GRY", "book", "menu", PURPLE, "gti.control.menu"),
        ("PODPOWIEDŹ", "spyglass", "hint", MAGENTA, "gti.control.hint"),
    ]
    button_y = [-1.5, -4.1, -6.7, -9.3]
    for (label, icon, key, color, control_tag), by in zip(buttons, button_y):
        panel += [
            block_display("gray_concrete", PANEL_X, by, 6.7, 2.0, -0.03, 0.05, ("gti.entity", "gti.panel")),
            block_display(color_block(color), PANEL_X - 3.28, by, 0.14, 2.0, 0.03, 0.05, ("gti.entity", "gti.panel")),
            item_display(icon, PANEL_X - 2.45, by, 0.06, 1.45, ("gti.entity", "gti.panel", "gti.icon")),
            text_display(
                line(label, WHITE, True),
                PANEL_X + 0.35,
                by - 0.16,
                0.06,
                scale=0.9,
                tag_list=("gti.entity", "gti.text", "gti.panel", f"gti.btn.{key}"),
            ),
            interaction(PANEL_X, by, 0.28, 6.7, 2.0, ("gti.entity", "gti.control", control_tag)),
        ]

    # status / header ---------------------------------------------------
    panel += [
        text_display(
            title_component("PANEL GRY", CYAN),
            PANEL_X - 0.65,
            10.75,
            0.05,
            scale=1.05,
            tag_list=("gti.entity", "gti.text", "gti.panel"),
        ),
        text_display(
            line("GOTOWA", PURPLE, True),
            PANEL_X - 0.9,
            9.65,
            0.06,
            scale=0.64,
            background=CHIP_BG,
            tag_list=("gti.entity", "gti.text", "gti.panel", "gti.hud.status"),
        ),
        text_display(
            line("II", WHITE, True),
            PANEL_X + 3.05,
            10.7,
            0.06,
            scale=0.72,
            background=CHIP_BG,
            tag_list=("gti.entity", "gti.text", "gti.panel"),
        ),
        interaction(PANEL_X + 3.05, 10.8, 0.28, 1.05, 1.15, ("gti.entity", "gti.control", "gti.control.pause")),
        text_display(
            line("BRAK PODPOWIEDZI", GOLD),
            PANEL_X,
            -11.3,
            0.05,
            scale=0.56,
            tag_list=("gti.entity", "gti.text", "gti.panel", "gti.hud.hint"),
        ),
        text_display(
            line("RĘCZNIE", PURPLE),
            PANEL_X,
            0.55,
            0.05,
            scale=0.52,
            tag_list=("gti.entity", "gti.text", "gti.panel", "gti.hud.timer"),
        ),
    ]

    # bottom stat cards --------------------------------------------------
    cards = [
        ("PRÓBY", "guesses", GOLD, -7.5),
        ("PIKSELE", "pixels", CYAN, -2.5),
        ("BŁĘDY", "wrong", RED, 2.5),
        ("CZAS", "time", BLUE, 7.5),
    ]
    bottom = []
    for label, key, color, x in cards:
        bottom += [
            block_display("tinted_glass", x, -12.05, 4.55, 1.95, -0.10, 0.05, ("gti.entity", "gti.decor")),
            text_display(
                line(label, MUTED, True),
                x,
                -11.55,
                0.03,
                scale=0.5,
                tag_list=("gti.entity", "gti.text", "gti.decor"),
            ),
            text_display(
                line("0", color, True),
                x,
                -12.55,
                0.03,
                scale=1.2,
                tag_list=("gti.entity", "gti.text", "gti.decor", f"gti.hud.b.{key}"),
            ),
        ]

    # progress meter (left side) ----------------------------------------
    meter = [
        text_display(
            line("POSTĘP", MUTED, True),
            -11.45,
            -10.55,
            0.03,
            scale=0.5,
            tag_list=("gti.entity", "gti.text", "gti.decor", "gti.hud.progress"),
        )
    ]
    seg_colors = [
        "cyan_concrete",
        "cyan_concrete",
        "cyan_concrete",
        "cyan_concrete",
        "light_blue_concrete",
        "light_blue_concrete",
        "light_blue_concrete",
        "light_blue_concrete",
        "blue_concrete",
        "blue_concrete",
        "blue_concrete",
        "blue_concrete",
        "purple_concrete",
        "purple_concrete",
        "purple_concrete",
        "purple_concrete",
        "magenta_concrete",
        "magenta_concrete",
        "magenta_concrete",
        "magenta_concrete",
    ]
    for idx in range(20):
        y = -9.35 + idx * 0.97
        meter.append(
            block_display(
                "gray_concrete",
                -11.45,
                y,
                0.5,
                0.79,
                0.03,
                0.04,
                ("gti.entity", "gti.decor", "gti.seg"),
            )
        )
        meter.append(
            f"execute positioned ~-11.45 ~{fnum(y)} ~0.03 run "
            f"scoreboard players set @e[tag=gti.seg,sort=nearest,limit=1] gti.id {idx}"
        )
        meter.append(
            f'data modify entity @e[tag=gti.seg,scores={{gti.id:{idx}}},limit=1] block_state.Name '
            f'set value "minecraft:{seg_colors[idx]}"'
        )

    # header, subtitle, caption -----------------------------------------
    header = [
        text_display(
            line(f"PIXEL REVEAL   •   {c} PRZEDMIOTÓW   •   JAVA {vd['label']}", MUTED),
            0,
            10.35,
            0.35,
            scale=0.7,
            tag_list=("gti.entity", "gti.text", "gti.decor"),
        ),
        text_display(
            line("WYBIERZ RUNDĘ", MUTED),
            0,
            -13.45,
            0.04,
            scale=0.66,
            tag_list=("gti.entity", "gti.text", "gti.decor", "gti.hud.answer"),
        ),
        text_display(
            line("LPM / PPM na kafelku   •   przedmiot w ręce + ZGADUJ", DIM),
            0,
            -14.15,
            0.04,
            scale=0.53,
            tag_list=("gti.entity", "gti.text", "gti.decor"),
        ),
    ]

    # overlays -----------------------------------------------------------
    overlays = [
        text_display(
            title_component("3", GOLD),
            0,
            -0.5,
            0.95,
            scale=0.01,
            tag_list=("gti.entity", "gti.text", "gti.overlay", "gti.overlay.count"),
        ),
        text_display(
            title_component("PRZYGOTUJ SIĘ", WHITE),
            0,
            4.2,
            0.95,
            scale=0.01,
            tag_list=("gti.entity", "gti.text", "gti.overlay", "gti.overlay.title"),
        ),
        text_display(
            line("Zgadnij przedmiot po fragmentach ikony", MUTED),
            0,
            2.6,
            0.95,
            scale=0.01,
            tag_list=("gti.entity", "gti.text", "gti.overlay", "gti.overlay.sub"),
        ),
        text_display(
            title_component("NIE TEN ITEM", RED),
            0,
            7.2,
            1.05,
            scale=0.01,
            background=RED_BG,
            tag_list=("gti.entity", "gti.text", "gti.overlay", "gti.overlay.bad"),
        ),
    ]

    # shutter ------------------------------------------------------------
    shutter = []
    for idx in range(8):
        y = 10.3 - idx * 2.6
        shutter.append(
            block_display(
                "black_concrete",
                0,
                y,
                21.2,
                0.02,
                0.56,
                0.04,
                ("gti.entity", "gti.decor", "gti.shutter"),
            )
        )
        shutter.append(
            f"execute positioned ~0 ~{fnum(y)} ~0.56 run "
            f"scoreboard players set @e[tag=gti.shutter,sort=nearest,limit=1] gti.id {idx}"
        )

    # scanner, runners, halo --------------------------------------------
    effects = [
        block_display(
            "cyan_stained_glass", 0, 0, 20.9, 0.07, 0.42, 0.02,
            ("gti.entity", "gti.decor", "gti.scan"),
        ),
        item_display("end_rod", -10.0, 10.0, 0.55, 0.45, ("gti.entity", "gti.decor", "gti.run0")),
        item_display("end_rod", 10.0, -10.0, 0.55, 0.45, ("gti.entity", "gti.decor", "gti.run1")),
    ]
    for idx in range(12):
        effects.append(
            item_display(
                "firework_star",
                0,
                0,
                0.85,
                0.01,
                ("gti.entity", "gti.decor", "gti.halo"),
                extra='billboard:"center"',
            )
        )
        effects.append(
            f"execute positioned ~0 ~0 ~0.85 run "
            f"scoreboard players set @e[tag=gti.halo,sort=nearest,limit=1] gti.id {idx}"
        )

    functions = [
        "scoreboard players set #pulse gti.var 0",
        "scoreboard players set #shutter gti.var 0",
        "scoreboard players set #bob gti.var 0",
        "scoreboard players set #sway gti.var 0",
        "scoreboard players set #scan gti.var 0",
        "scoreboard players set #run0 gti.var 0",
        "scoreboard players set #run1 gti.var 40",
        "scoreboard players set #halo gti.var 0",
    ]
    return deco + panel + bottom + meter + header + header_lines() + overlays + shutter + effects + functions


def color_block(hex_color: str) -> str:
    """Map an accent colour to the nearest concrete block."""
    palette = {
        "#45E9E0": "cyan_concrete",
        "#61EDE5": "cyan_concrete",
        "#79C4F8": "light_blue_concrete",
        "#B295FF": "purple_concrete",
        "#F47BC6": "pink_concrete",
        "#FFD47E": "yellow_concrete",
        "#F6CF84": "yellow_concrete",
        "#FF8996": "red_concrete",
        "#8BE28B": "lime_concrete",
        "#F2F7FF": "white_concrete",
        "#8FA8C8": "light_gray_concrete",
        "#5F7899": "gray_concrete",
    }
    return palette.get(hex_color.upper(), "light_blue_concrete")


def column_lines(col: int) -> list[str]:
    out: list[str] = []
    for row in range(16):
        x = (col - 7.5) * TILE
        y = (7.5 - row) * TILE
        idx = row * 16 + col
        z = MASK_Z + ((col + row) % 2) * 0.001
        out.append(
            block_display(
                "black_concrete",
                x,
                y,
                1.27,
                1.27,
                z,
                0.055,
                ("gti.entity", "gti.mask", f"gti.col{col}", f"gti.row{row}"),
            )
        )
        out.append(
            f"execute positioned ~{fnum(x - 0.635)} ~{fnum(y - 0.635)} ~{fnum(z)} run "
            f"scoreboard players set @e[tag=gti.mask,sort=nearest,limit=1] gti.id {idx}"
        )
        out.append(
            interaction(x, y, 0.34, 1.22, 1.22, ("gti.entity", "gti.pixel", f"gti.col{col}", f"gti.row{row}"))
        )
        out.append(
            f"execute positioned ~{fnum(x)} ~{fnum(y)} ~0.34 run "
            f"scoreboard players set @e[tag=gti.pixel,sort=nearest,limit=1] gti.id {idx}"
        )
    return out


def ring_storage() -> list[dict]:
    pts = []
    n = 20
    half = 10.9
    for i in range(n):
        pts.append({"x": f"{-half + i * (2 * half / n):.2f}", "y": f"{half:.2f}"})
    for i in range(n):
        pts.append({"x": f"{half:.2f}", "y": f"{half - i * (2 * half / n):.2f}"})
    for i in range(n):
        pts.append({"x": f"{half - i * (2 * half / n):.2f}", "y": f"{-half:.2f}"})
    for i in range(n):
        pts.append({"x": f"{-half:.2f}", "y": f"{-half + i * (2 * half / n):.2f}"})
    return pts


def sway_storage() -> list[list[float]]:
    quats = []
    for i in range(12):
        angle = math.radians(-5.0 + (i % 5) * 2.5)
        quats.append([0.0, 0.0, round(math.sin(angle / 2), 6), round(math.cos(angle / 2), 6)])
    return quats


def bob_storage() -> list[list[float]]:
    frames = []
    for f in range(8):
        phase = f / 8 * math.tau
        frames.append([round(math.sin(phase + i * 0.55) * 0.10, 3) for i in range(14)])
    return frames


def halo_storage() -> list[list[list[float]]]:
    frames = []
    for f in range(36):
        frame = []
        for i in range(12):
            angle = math.tau * (i / 12 + f / 36)
            frame.append(
                [
                    round(math.cos(angle) * 13.6, 3),
                    round(math.sin(angle) * 13.6, 3),
                    round(0.75 + math.sin(angle * 2) * 0.12, 3),
                ]
            )
        frames.append(frame)
    return frames


def snbt_floats(value) -> str:
    if isinstance(value, list):
        return "[" + ",".join(snbt_floats(v) for v in value) + "]"
    return f"{float(value):.5f}f"


def visual_functions(vd: dict) -> dict[str, str]:
    ring = json.dumps(ring_storage(), separators=(",", ":"))
    sway = snbt_floats(sway_storage())
    bob = json.dumps(bob_storage(), separators=(",", ":"))
    halo = snbt_floats(halo_storage())

    f: dict[str, str] = {}

    f["visual/setup"] = mc(
        [
            f"data modify storage gti:fx ring set value {ring}",
            f"data modify storage gti:fx sway set value {sway}",
            f"data modify storage gti:fx bob set value {bob}",
            f"data modify storage gti:fx halo set value {halo}",
            "data modify storage gti:fx args set value []",
            "data modify storage gti:fx bobargs set value []",
            "data modify storage gti:fx quat set value [0f,0f,0f,1f]",
            "scoreboard players set #eighty gti.var 80",
            "scoreboard players set #ten gti.var 10",
            "scoreboard players set #hundred gti.var 100",
            "scoreboard players set #twelve gti.var 12",
            "scoreboard players set #eight gti.var 8",
            "scoreboard players set #two gti.var 2",
            "scoreboard players set #halo_max gti.var 36",
        ]
    )

    f["visual/tick"] = mc(
        [
            "execute unless score #state gti.var matches 2..3 run function gti:visual/scan",
            "execute if score #state gti.var matches 0..2 run function gti:visual/runners",
            "execute if score #state gti.var matches 1 run return 0",
            "execute if score #state gti.var matches 3 run return 0",
            "execute if score #clock gti.var matches 0 run function gti:visual/sway",
        ]
    )

    f["visual/runners"] = mc(
        [
            "scoreboard players add #run0 gti.var 1",
            "scoreboard players operation #run1 gti.var = #run0 gti.var",
            "scoreboard players add #run1 gti.var 40",
            "scoreboard players operation #run0 gti.var %= #eighty gti.var",
            "scoreboard players operation #run1 gti.var %= #eighty gti.var",
            "execute store result storage gti:fx frame int 1 run scoreboard players get #run0 gti.var",
            "function gti:visual/ring_pick with storage gti:fx",
            "function gti:visual/ring_apply0 with storage gti:fx args",
            "execute store result storage gti:fx frame int 1 run scoreboard players get #run1 gti.var",
            "function gti:visual/ring_pick with storage gti:fx",
            "function gti:visual/ring_apply1 with storage gti:fx args",
        ]
    )
    f["visual/ring_pick"] = mc(
        ["$data modify storage gti:fx args set from storage gti:fx ring[$(frame)]"]
    )
    f["visual/ring_apply0"] = mc(
        ["$execute at @e[tag=gti.anchor,limit=1] run tp @e[tag=gti.run0,limit=1] ~$(x) ~$(y) ~0.55"]
    )
    f["visual/ring_apply1"] = mc(
        ["$execute at @e[tag=gti.anchor,limit=1] run tp @e[tag=gti.run1,limit=1] ~$(x) ~$(y) ~0.55"]
    )

    f["visual/scan"] = mc(
        [
            "scoreboard players add #scan gti.var 3",
            "execute if score #scan gti.var matches 200.. run scoreboard players set #scan gti.var 0",
            "scoreboard players operation #scan_y gti.var = #scan gti.var",
            "execute if score #scan gti.var matches 101.. run scoreboard players set #scan_y gti.var 200",
            "execute if score #scan gti.var matches 101.. run scoreboard players operation #scan_y gti.var -= #scan gti.var",
            "scoreboard players operation #scan_y gti.var *= #ten gti.var",
            "scoreboard players remove #scan_y gti.var 1000",
            "execute store result entity @e[tag=gti.scan,limit=1] transformation.translation[1] float 0.01 run scoreboard players get #scan_y gti.var",
        ]
    )

    f["visual/sway"] = mc(
        [
            "scoreboard players add #sway gti.var 1",
            "scoreboard players operation #sway gti.var %= #twelve gti.var",
            "execute store result storage gti:fx frame int 1 run scoreboard players get #sway gti.var",
            "function gti:visual/sway_pick with storage gti:fx",
            "function gti:visual/sway_apply",
        ]
    )
    f["visual/sway_pick"] = mc(
        ["$data modify storage gti:fx quat set from storage gti:fx sway[$(frame)]"]
    )
    f["visual/sway_apply"] = mc(
        [
            "data modify entity @e[tag=gti.item,limit=1] transformation.left_rotation set from storage gti:fx quat",
        ]
    )

    f["visual/bob"] = mc(
        [
            "scoreboard players add #bob gti.var 1",
            "scoreboard players operation #bob gti.var %= #eight gti.var",
            "execute store result storage gti:fx frame int 1 run scoreboard players get #bob gti.var",
            "function gti:visual/bob_pick with storage gti:fx",
            "function gti:visual/bob_apply",
        ]
    )
    f["visual/bob_pick"] = mc(
        ["$data modify storage gti:fx bobargs set from storage gti:fx bob[$(frame)]"]
    )
    bob_apply = []
    for i in range(14):
        bob_apply.append(
            f"execute store result entity @e[tag=gti.letter,scores={{gti.id:{i}}},limit=1] "
            f"transformation.translation[1] float 1 run data get storage gti:fx bobargs[{i}]"
        )
    f["visual/bob_apply"] = mc(bob_apply)

    f["visual/pulse"] = mc(
        [
            "scoreboard players add #pulse gti.var 1",
            "scoreboard players operation #pulse gti.var %= #two gti.var",
            'execute as @e[tag=gti.pulse.a] run data modify entity @s block_state.Name set value "minecraft:sea_lantern"',
            'execute if score #pulse gti.var matches 0 as @e[tag=gti.pulse.b] run data modify entity @s block_state.Name set value "minecraft:magenta_concrete"',
            'execute if score #pulse gti.var matches 1 as @e[tag=gti.pulse.b] run data modify entity @s block_state.Name set value "minecraft:pink_concrete"',
            'execute if score #pulse gti.var matches 0 as @e[tag=gti.pulse.c] run data modify entity @s block_state.Name set value "minecraft:cyan_concrete"',
            'execute if score #pulse gti.var matches 1 as @e[tag=gti.pulse.c] run data modify entity @s block_state.Name set value "minecraft:light_blue_concrete"',
        ]
    )

    f["visual/shutter_close"] = mc(
        [
            f'execute if score #shutter gti.var matches {i}.. run data merge entity @e[tag=gti.shutter,scores={{gti.id:{i}}},limit=1] '
            f"{{start_interpolation:0,interpolation_duration:5,transformation:{{scale:[21.2f,2.55f,0.04f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}}}"
            for i in range(8)
        ]
    )
    f["visual/shutter_open"] = mc(
        [
            f'execute if score #shutter gti.var matches {i}.. run data merge entity @e[tag=gti.shutter,scores={{gti.id:{i}}},limit=1] '
            f"{{start_interpolation:0,interpolation_duration:4,transformation:{{scale:[21.2f,0.02f,0.04f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}}}"
            for i in range(8)
        ]
    )
    f["visual/shutter_reset"] = mc(
        [
            "scoreboard players set #shutter gti.var 0",
            'execute as @e[tag=gti.shutter] run data modify entity @s transformation.scale set value [21.2f,0.02f,0.04f]',
        ]
    )

    f["visual/halo"] = mc(
        [
            "scoreboard players add #halo gti.var 1",
            "scoreboard players operation #halo gti.var %= #halo_max gti.var",
            "execute store result storage gti:fx frame int 1 run scoreboard players get #halo gti.var",
            "function gti:visual/halo_pick with storage gti:fx",
            "function gti:visual/halo_apply",
        ]
    )
    f["visual/halo_pick"] = mc(
        ["$data modify storage gti:fx args set from storage gti:fx halo[$(frame)]"]
    )
    halo_apply = []
    for i in range(12):
        halo_apply.append(
            f"data modify entity @e[tag=gti.halo,scores={{gti.id:{i}}},limit=1] transformation.translation set from storage gti:fx args[{i}]"
        )
        halo_apply.append(
            f"data modify entity @e[tag=gti.halo,scores={{gti.id:{i}}},limit=1] transformation.scale set value [0.75f,0.75f,0.001f]"
        )
    f["visual/halo_apply"] = mc(halo_apply)

    f["visual/halo_reset"] = mc(
        [
            "execute as @e[tag=gti.halo] run data modify entity @s transformation.scale set value [0.01f,0.01f,0.001f]",
            "scoreboard players set #halo gti.var 0",
        ]
    )

    f["visual/particles_idle"] = mc(
        [
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:electric_spark ~ ~ ~ 9.5 9.5 0.2 0.01 3 force @a[tag=gti.player]",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:end_rod ~ ~9.6 ~0.4 8.5 0.2 0.05 0.002 2 force @a[tag=gti.player]",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:dust{color:[0.27,0.91,0.88],scale:0.9} ~ ~ ~0.5 9.5 9.5 0.1 0 3 force @a[tag=gti.player]",
        ]
    )

    f["visual/confetti"] = mc(
        [
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:firework ~ ~10 ~0.7 10 2 0.4 0.16 80 force @a[tag=gti.player]",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:crit ~ ~8 ~0.7 9 4 0.4 0.08 40 force @a[tag=gti.player]",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:happy_villager ~ ~6 ~0.7 8 3 0.4 0.03 25 force @a[tag=gti.player]",
        ]
    )

    return f


def hud_functions(vd: dict, count: int) -> dict[str, str]:
    f: dict[str, str] = {}

    f["internal/hud"] = mc(
        [
            "scoreboard players operation #seconds gti.var = #time gti.var",
            "scoreboard players operation #seconds gti.var /= #twenty gti.var",
            "scoreboard players operation #mins gti.var = #seconds gti.var",
            "scoreboard players operation #mins gti.var /= #sixty gti.var",
            "scoreboard players operation #secs gti.var = #seconds gti.var",
            "scoreboard players operation #secs gti.var %= #sixty gti.var",
            "scoreboard players operation #remaining gti.var = #limit gti.var",
            "scoreboard players operation #remaining gti.var -= #cost gti.var",
            "execute if score #remaining gti.var matches ..-1 run scoreboard players set #remaining gti.var 0",
            "execute if score #limit gti.var matches 0 run scoreboard players set #remaining gti.var 0",
            "execute store result storage gti:ui guesses int 1 run scoreboard players get #guesses gti.var",
            "execute store result storage gti:ui pixels int 1 run scoreboard players get #pixels gti.var",
            "execute store result storage gti:ui wrong int 1 run scoreboard players get #wrong gti.var",
            "execute store result storage gti:ui batch int 1 run scoreboard players get #batch gti.var",
            "execute store result storage gti:ui limit int 1 run scoreboard players get #limit gti.var",
            "execute store result storage gti:ui cost int 1 run scoreboard players get #cost gti.var",
            "execute store result storage gti:ui mins int 1 run scoreboard players get #mins gti.var",
            "execute store result storage gti:ui secs int 1 run scoreboard players get #secs gti.var",
            "execute store result storage gti:ui round int 1 run scoreboard players get #round gti.var",
            "execute store result storage gti:ui hint_stage int 1 run scoreboard players get #hint_stage gti.var",
            "execute store result storage gti:ui pixels int 1 run scoreboard players get #pixels gti.var",
            "data modify storage gti:ui mm0 set value \"\"",
            "data modify storage gti:ui ss0 set value \"\"",
            "execute if score #mins gti.var matches ..9 run data modify storage gti:ui mm0 set value \"0\"",
            "execute if score #secs gti.var matches ..9 run data modify storage gti:ui ss0 set value \"0\"",
            "data modify storage gti:ui limit_label set value \"∞\"",
            "execute if score #limit gti.var matches 1.. run function gti:visual/set_limit_label with storage gti:ui",
            "function gti:visual/set_time with storage gti:ui",
            "data modify storage gti:ui mode set value \"RĘCZNIE\"",
            "execute if score #reveal_mode gti.var matches 1 run data modify storage gti:ui mode set value \"PO BŁĘDZIE\"",
            "execute if score #reveal_mode gti.var matches 2 run data modify storage gti:ui mode set value \"AUTO\"",
            "data modify storage gti:ui status set value \"GOTOWA\"",
            "execute if score #state gti.var matches 1 run data modify storage gti:ui status set value \"INTRO\"",
            "execute if score #state gti.var matches 2 run data modify storage gti:ui status set value \"LIVE\"",
            "execute if score #state gti.var matches 3 run data modify storage gti:ui status set value \"FINALE\"",
            "execute if score #paused gti.var matches 1 run data modify storage gti:ui status set value \"PAUZA\"",
            "scoreboard players set #timer_left gti.var 0",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_left gti.var = #interval gti.var",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_left gti.var -= #timer gti.var",
            "execute if score #timer_left gti.var matches ..-1 run scoreboard players set #timer_left gti.var 0",
            "scoreboard players operation #timer_left gti.var /= #twenty gti.var",
            "execute store result storage gti:ui timer_seconds int 1 run scoreboard players get #timer_left gti.var",
            "data modify storage gti:ui answer set from storage gti:cfg answer",
            "data modify storage gti:ui hint set from storage gti:cfg hint",
            "execute if score #hint_stage gti.var matches 0 run data modify storage gti:ui hint set value \"BRAK PODPOWIEDZI\"",
            "execute if score #hints_enabled gti.var matches 0 run data modify storage gti:ui hint set value \"PODPOWIEDZI WYŁĄCZONE\"",
            "data modify storage gti:ui reveal_label set value \"ODKRYJ ×\"",
            "execute store result storage gti:ui batch int 1 run scoreboard players get #batch gti.var",
            "function gti:visual/fmt_labels with storage gti:ui",
            "function gti:visual/hud_apply with storage gti:ui",
            "function gti:visual/progress",
            "function gti:visual/budget",
            "execute if score #state gti.var matches 2 run function gti:ui/actionbar",
            "execute if score #state gti.var matches 2 run function gti:internal/bossbars",
        ]
    )

    f["visual/set_limit_label"] = mc(
        ["$data modify storage gti:ui limit_label set value \"$(limit)\""]
    )
    f["visual/set_time"] = mc(
        ["$data modify storage gti:ui time set value \"$(mm0)$(mins):$(ss0)$(secs)\""]
    )
    f["visual/fmt_timer"] = mc(
        ["$data modify storage gti:ui timer_label set value \"AUTO • $(timer_seconds)s\""]
    )
    f["visual/fmt_labels"] = mc(
        [
            "$data modify storage gti:ui reveal_label set value \"ODKRYJ ×$(batch)\"",
            "$data modify storage gti:ui hint_label set value \"PODPOWIEDŹ $(hint_stage)/3\"",
            "$data modify storage gti:ui budget_label set value \"$(cost) / $(limit_label)\"",
            "$data modify storage gti:ui progress_label set value \"POSTĘP $(pixels)/256\"",
            "$data modify storage gti:ui round_label set value \"RUNDA $(round) • $(status)\"",
            "$data modify storage gti:ui answer_line set value \"ODPOWIEDŹ: $(answer)\"",
        ]
    )

    lines = [
        '$data modify entity @e[tag=gti.hud.guesses,limit=1] text set value [{"text":"$(guesses)","color":"#F2F7FF","bold":true}]',
        '$data modify entity @e[tag=gti.hud.pixels,limit=1] text set value [{"text":"$(pixels)","color":"#61EDE5","bold":true},{"text":" / 256","color":"#5F7899"}]',
        '$data modify entity @e[tag=gti.hud.wrong,limit=1] text set value [{"text":"$(wrong)","color":"#FF8996","bold":true}]',
        '$data modify entity @e[tag=gti.hud.time,limit=1] text set value [{"text":"$(time)","color":"#79C4F8","bold":true}]',
        '$data modify entity @e[tag=gti.hud.batch,limit=1] text set value [{"text":"×$(batch)","color":"#B295FF","bold":true}]',
        '$data modify entity @e[tag=gti.hud.budget,limit=1] text set value [{"text":"$(budget_label)","color":"#F6CF84","bold":true}]',
        '$data modify entity @e[tag=gti.hud.b.guesses,limit=1] text set value [{"text":"$(guesses)","color":"#F6CF84","bold":true}]',
        '$data modify entity @e[tag=gti.hud.b.pixels,limit=1] text set value [{"text":"$(pixels)","color":"#61EDE5","bold":true}]',
        '$data modify entity @e[tag=gti.hud.b.wrong,limit=1] text set value [{"text":"$(wrong)","color":"#FF8996","bold":true}]',
        '$data modify entity @e[tag=gti.hud.b.time,limit=1] text set value [{"text":"$(time)","color":"#79C4F8","bold":true}]',
        '$data modify entity @e[tag=gti.hud.status,limit=1] text set value [{"text":"$(round_label)","color":"#B295FF","bold":true}]',
        '$data modify entity @e[tag=gti.hud.hint,limit=1] text set value [{"text":"$(hint)","color":"#F6CF84"}]',
        '$data modify entity @e[tag=gti.hud.answer,limit=1] text set value [{"text":"$(answer_line)","color":"#8FA8C8"}]',
        '$data modify entity @e[tag=gti.hud.progress,limit=1] text set value [{"text":"$(progress_label)","color":"#8FA8C8","bold":true}]',
        '$data modify entity @e[tag=gti.btn.reveal,limit=1] text set value [{"text":"$(reveal_label)","color":"#F2F7FF","bold":true}]',
        '$data modify entity @e[tag=gti.btn.hint,limit=1] text set value [{"text":"$(hint_label)","color":"#F2F7FF","bold":true}]',
        '$data modify entity @e[tag=gti.hud.timer,limit=1] text set value [{"text":"$(timer_label)","color":"#B295FF"}]',
    ]
    f["visual/hud_apply"] = mc(lines)

    f["visual/progress"] = mc(
        [
            (
                f'execute if score #pixels gti.var matches {min(256, (i + 1) * 256 // 20)}.. run '
                f'data modify entity @e[tag=gti.seg,scores={{gti.id:{i}}},limit=1] block_state.Name '
                f'set value "minecraft:{seg_color(i)}"'
            )
            for i in range(20)
        ]
        + [
            (
                f'execute if score #pixels gti.var matches ..{max(0, (i + 1) * 256 // 20 - 1)} run '
                f'data modify entity @e[tag=gti.seg,scores={{gti.id:{i}}},limit=1] block_state.Name '
                f'set value "minecraft:gray_concrete"'
            )
            for i in range(20)
        ]
    )

    f["visual/budget"] = mc(
        [
            "scoreboard players set #filled gti.var 10",
            "execute if score #limit gti.var matches 1.. run scoreboard players operation #filled gti.var = #remaining gti.var",
            "execute if score #limit gti.var matches 1.. run scoreboard players operation #filled gti.var *= #ten gti.var",
            "execute if score #limit gti.var matches 1.. run scoreboard players operation #filled gti.var /= #limit gti.var",
            "execute if score #filled gti.var matches 11.. run scoreboard players set #filled gti.var 10",
            "execute if score #filled gti.var matches ..-1 run scoreboard players set #filled gti.var 0",
        ]
        + [
            (
                f'execute if score #filled gti.var matches {i + 1}.. run '
                f'data modify entity @e[tag=gti.budgetseg,scores={{gti.id:{i}}},limit=1] block_state.Name '
                f'set value "minecraft:{budget_color(i)}"'
            )
            for i in range(10)
        ]
        + [
            (
                f'execute if score #filled gti.var matches ..{i} run '
                f'data modify entity @e[tag=gti.budgetseg,scores={{gti.id:{i}}},limit=1] block_state.Name '
                f'set value "minecraft:black_concrete"'
            )
            for i in range(10)
        ]
    )

    f["internal/bossbars"] = mc(
        [
            "scoreboard players operation #remaining_boss gti.var = #limit gti.var",
            "scoreboard players operation #remaining_boss gti.var -= #cost gti.var",
            "execute if score #remaining_boss gti.var matches ..-1 run scoreboard players set #remaining_boss gti.var 0",
            "execute if score #limit gti.var matches 0 run scoreboard players set #remaining_boss gti.var 1",
            "execute if score #limit gti.var matches 1.. store result bossbar gti:budget max run scoreboard players get #limit gti.var",
            "execute if score #limit gti.var matches 1.. store result bossbar gti:budget value run scoreboard players get #remaining_boss gti.var",
            "execute if score #limit gti.var matches 0 run bossbar set gti:budget max 1",
            "execute if score #limit gti.var matches 0 run bossbar set gti:budget value 1",
            "bossbar set gti:budget players @a[tag=gti.player]",
            "bossbar set gti:budget visible true",
            "bossbar set gti:budget color blue",
            "execute if score #limit gti.var matches 1.. if score #remaining_boss gti.var matches ..8 run bossbar set gti:budget color red",
            "execute if score #limit gti.var matches 1.. if score #remaining_boss gti.var matches 9..24 run bossbar set gti:budget color yellow",
            "execute if score #reveal_mode gti.var matches 2 run bossbar set gti:timer players @a[tag=gti.player]",
            "execute if score #reveal_mode gti.var matches 2 run bossbar set gti:timer visible true",
            "execute if score #reveal_mode gti.var matches 2 run bossbar set gti:timer max 100",
            "scoreboard players set #timer_bar gti.var 0",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_bar gti.var = #interval gti.var",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_bar gti.var -= #timer gti.var",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_bar gti.var *= #hundred gti.var",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_bar gti.var /= #interval gti.var",
            "execute if score #reveal_mode gti.var matches 2 store result bossbar gti:timer value run scoreboard players get #timer_bar gti.var",
        ]
    )

    return f


def seg_color(i: int) -> str:
    return [
        "cyan_concrete",
        "cyan_concrete",
        "cyan_concrete",
        "cyan_concrete",
        "light_blue_concrete",
        "light_blue_concrete",
        "light_blue_concrete",
        "light_blue_concrete",
        "blue_concrete",
        "blue_concrete",
        "blue_concrete",
        "blue_concrete",
        "purple_concrete",
        "purple_concrete",
        "purple_concrete",
        "purple_concrete",
        "magenta_concrete",
        "magenta_concrete",
        "magenta_concrete",
        "magenta_concrete",
    ][i]


def budget_color(i: int) -> str:
    if i < 5:
        return "lime_concrete"
    if i < 8:
        return "yellow_concrete"
    return "red_concrete"
