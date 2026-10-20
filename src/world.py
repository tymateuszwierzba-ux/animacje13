"""Holographic board, side panel and HUD geometry.

Everything is emitted for `gti:internal/build`, which runs while the command
context sits on the board anchor.  The anchor is 30 blocks north of the player
and 11 blocks up, so the whole scene hangs in the air in front of them.
"""

from __future__ import annotations

import math

from model import (
    BLUE,
    CHIP_BG,
    CYAN,
    DIM,
    GOLD,
    GREEN,
    MAGENTA,
    MUTED,
    PANEL_X,
    PURPLE,
    RED,
    RED_BG,
    WHITE,
    block_display,
    fnum,
    interaction,
    item_display,
    line,
    text_display,
    title_component,
)

TILES = 16
TILE = 1.25
HALF = TILES * TILE / 2.0  # 10.0
MASK_Z = 0.10
ITEM_Z = 0.02
FRAME_Y = HALF + 0.55  # 10.55
PANEL_W = 8.8
PANEL_H = 23.6
PANEL_CX = 15.35
BOTTOM_Y = -13.15

HEADER_TEXT = "GUESS THE ITEM"


def color_block(hex_color: str) -> str:
    palette = {
        CYAN.upper(): "cyan_concrete",
        "#61EDE5": "cyan_concrete",
        BLUE.upper(): "light_blue_concrete",
        PURPLE.upper(): "purple_concrete",
        MAGENTA.upper(): "pink_concrete",
        GOLD.upper(): "yellow_concrete",
        RED.upper(): "red_concrete",
        GREEN.upper(): "lime_concrete",
        WHITE.upper(): "white_concrete",
        MUTED.upper(): "light_gray_concrete",
        DIM.upper(): "gray_concrete",
    }
    return palette.get(hex_color.upper(), "light_blue_concrete")


def _mix(a: str, b: str, t: float) -> str:
    a = a.lstrip("#")
    b = b.lstrip("#")
    ca = [int(a[i : i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i : i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(ca[i] + (cb[i] - ca[i]) * t):02X}" for i in range(3))


def header_lines() -> list[str]:
    out = []
    letters = [c for c in HEADER_TEXT if c != " "]
    for idx, ch in enumerate(letters):
        color = _mix(CYAN, MAGENTA, idx / (len(letters) - 1))
        x = -8.9 + idx * 1.36
        out.append(
            text_display(
                {"text": ch, "color": color, "bold": True},
                x,
                12.55,
                0.30,
                scale=2.0,
                tag_list=("gti.entity", "gti.letter", "gti.text"),
                view_range=8.0,
            )
        )
        out.append(
            f"execute positioned ~{fnum(x)} ~12.55 ~0.30 run "
            f"scoreboard players set @e[tag=gti.letter,sort=nearest,limit=1] gti.id {idx}"
        )
    return out


def build_world(vd: dict) -> list[str]:
    count = vd["count"]
    out: list[str] = ['summon marker ~ ~ ~ {Tags:["gti.entity","gti.anchor"]}']

    # -- backdrop -------------------------------------------------------
    out += [
        block_display("black_concrete", 0, 0, 24.8, 24.8, -0.44, 0.08, ("gti.entity", "gti.decor")),
        block_display("blue_concrete", 0, 0, 23.8, 23.8, -0.40, 0.06, ("gti.entity", "gti.decor", "gti.pulse.b")),
        block_display("purple_concrete", 0, 0, 23.0, 23.0, -0.36, 0.05, ("gti.entity", "gti.decor", "gti.pulse.c")),
        block_display("black_concrete", 0, 0, 22.3, 22.3, -0.31, 0.05, ("gti.entity", "gti.decor")),
        block_display("tinted_glass", 0, 0, 21.7, 21.7, -0.25, 0.04, ("gti.entity", "gti.decor")),
        # outer neon frame
        block_display("sea_lantern", 0, FRAME_Y, 21.4, 0.18, 0.00, 0.06, ("gti.entity", "gti.decor", "gti.pulse.a")),
        block_display("sea_lantern", 0, -FRAME_Y, 21.4, 0.18, 0.00, 0.06, ("gti.entity", "gti.decor", "gti.pulse.a")),
        block_display("sea_lantern", -FRAME_Y, 0, 0.18, 21.4, 0.00, 0.06, ("gti.entity", "gti.decor", "gti.pulse.a")),
        block_display("sea_lantern", FRAME_Y, 0, 0.18, 21.4, 0.00, 0.06, ("gti.entity", "gti.decor", "gti.pulse.a")),
        # inner rails
        block_display("cyan_concrete", 0, 10.22, 20.55, 0.10, 0.04, 0.04, ("gti.entity", "gti.decor", "gti.pulse.c")),
        block_display("cyan_concrete", 0, -10.22, 20.55, 0.10, 0.04, 0.04, ("gti.entity", "gti.decor", "gti.pulse.c")),
        block_display("cyan_concrete", -10.22, 0, 0.10, 20.55, 0.04, 0.04, ("gti.entity", "gti.decor", "gti.pulse.c")),
        block_display("cyan_concrete", 10.22, 0, 0.10, 20.55, 0.04, 0.04, ("gti.entity", "gti.decor", "gti.pulse.c")),
        # corner gems
        block_display("magenta_concrete", -10.22, 10.22, 0.95, 0.95, 0.09, 0.05, ("gti.entity", "gti.decor", "gti.pulse.b")),
        block_display("magenta_concrete", 10.22, 10.22, 0.95, 0.95, 0.09, 0.05, ("gti.entity", "gti.decor", "gti.pulse.b")),
        block_display("magenta_concrete", -10.22, -10.22, 0.95, 0.95, 0.09, 0.05, ("gti.entity", "gti.decor", "gti.pulse.b")),
        block_display("magenta_concrete", 10.22, -10.22, 0.95, 0.95, 0.09, 0.05, ("gti.entity", "gti.decor", "gti.pulse.b")),
        # corner brackets
        *[
            block_display("light_blue_concrete", sx * 9.55, sy * 9.98, 1.35, 0.12, 0.13, 0.04, ("gti.entity", "gti.decor"))
            for sx, sy in ((-1, 1), (1, 1), (-1, -1), (1, -1))
        ],
        *[
            block_display("light_blue_concrete", sx * 9.98, sy * 9.55, 0.12, 1.35, 0.13, 0.04, ("gti.entity", "gti.decor"))
            for sx, sy in ((-1, 1), (1, 1), (-1, -1), (1, -1))
        ],
        # floating shards
        block_display("ochre_froglight", -11.25, 9.85, 0.30, 0.30, 0.06, 0.30, ("gti.entity", "gti.decor")),
        block_display("pearlescent_froglight", -11.25, -9.85, 0.30, 0.30, 0.06, 0.30, ("gti.entity", "gti.decor")),
        block_display("ochre_froglight", 19.85, 9.85, 0.30, 0.30, 0.06, 0.30, ("gti.entity", "gti.decor")),
        block_display("pearlescent_froglight", 19.85, -9.85, 0.30, 0.30, 0.06, 0.30, ("gti.entity", "gti.decor")),
        # the answer
        item_display(
            "ender_eye",
            0,
            0,
            ITEM_Z,
            20.0,
            ("gti.entity", "gti.item"),
            view_range=8.0,
            rotation=(0.0, 1.0, 0.0, 0.0),
        ),
    ]

    # -- panel ----------------------------------------------------------
    panel = [
        block_display("tinted_glass", PANEL_CX, 0, PANEL_W, PANEL_H, -0.18, 0.06, ("gti.entity", "gti.panel")),
        block_display("black_concrete", PANEL_CX, 0, PANEL_W - 0.35, PANEL_H - 0.35, -0.13, 0.04, ("gti.entity", "gti.panel")),
        block_display("cyan_concrete", PANEL_CX, 11.7, PANEL_W, 0.16, 0.01, 0.05, ("gti.entity", "gti.panel", "gti.pulse.c")),
        block_display("magenta_concrete", PANEL_CX, -11.7, PANEL_W, 0.16, 0.01, 0.05, ("gti.entity", "gti.panel", "gti.pulse.b")),
        block_display("tinted_glass", PANEL_CX, 4.95, PANEL_W - 0.5, 7.55, -0.06, 0.04, ("gti.entity", "gti.panel")),
        block_display("tinted_glass", PANEL_CX, -11.05, PANEL_W - 0.5, 1.35, -0.06, 0.04, ("gti.entity", "gti.panel")),
        block_display("black_concrete", PANEL_CX, 0.78, PANEL_W - 1.8, 0.24, -0.03, 0.03, ("gti.entity", "gti.panel")),
    ]
    for idx in range(10):
        x = PANEL_CX - 3.05 + idx * 0.678
        panel.append(
            block_display(
                "gray_concrete",
                x,
                0.78,
                0.58,
                0.17,
                0.0,
                0.03,
                ("gti.entity", "gti.panel", "gti.budgetseg"),
            )
        )
        panel.append(
            f"execute positioned ~{fnum(x)} ~0.78 ~0.0 run "
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
    for idx, (label, key) in enumerate(rows):
        y = 8.15 - idx * 1.3
        panel += [
            text_display(
                line(label, MUTED, True),
                11.55,
                y,
                0.05,
                scale=0.58,
                align="left",
                tag_list=("gti.entity", "gti.text", "gti.panel"),
            ),
            text_display(
                line("0", WHITE, True),
                19.25,
                y,
                0.05,
                scale=0.92,
                align="right",
                tag_list=("gti.entity", "gti.text", "gti.panel", f"gti.hud.{key}"),
            ),
        ]

    buttons = [
        ("ODKRYJ", "amethyst_shard", "reveal", CYAN, "gti.control.reveal"),
        ("ZGADUJ", "iron_sword", "guess", GOLD, "gti.control.guess"),
        ("MENU", "book", "menu", PURPLE, "gti.control.menu"),
        ("PODPOWIEDŹ", "spyglass", "hint", MAGENTA, "gti.control.hint"),
    ]
    for bidx, ((label, icon, key, color, ctrl), by) in enumerate(zip(buttons, (-1.55, -4.1, -6.65, -9.2))):
        panel += [
            block_display("gray_concrete", PANEL_CX, by, PANEL_W - 0.55, 2.2, -0.02, 0.05, ("gti.entity", "gti.panel", f"gti.btnbg.{key}")),
            block_display(color_block(color), 11.25, by, 0.16, 2.2, 0.03, 0.05, ("gti.entity", "gti.panel", f"gti.stripe.{key}")),
            item_display(icon, 12.35, by, 0.06, 1.55, ("gti.entity", "gti.panel", "gti.icon", f"gti.icon.{key}")),
            text_display(
                line(label, WHITE, True),
                15.55,
                by,
                0.06,
                scale=0.95,
                tag_list=("gti.entity", "gti.text", "gti.panel", f"gti.btn.{key}"),
            ),
            interaction(PANEL_CX, by, 0.30, PANEL_W - 0.55, 2.2, ("gti.entity", "gti.control", ctrl, f"gti.ctrl.{key}")),
        ]

    panel += [
        text_display(
            title_component("PANEL GRY", CYAN),
            PANEL_CX,
            11.05,
            0.06,
            scale=1.05,
            tag_list=("gti.entity", "gti.text", "gti.panel"),
        ),
        text_display(
            line("RUNDA 0", PURPLE, True),
            14.55,
            9.72,
            0.06,
            scale=0.62,
            background=CHIP_BG,
            tag_list=("gti.entity", "gti.text", "gti.panel", "gti.hud.status"),
        ),
        text_display(
            line("II", WHITE, True),
            18.65,
            10.95,
            0.06,
            scale=0.68,
            background=CHIP_BG,
            tag_list=("gti.entity", "gti.text", "gti.panel"),
        ),
        interaction(18.65, 10.95, 0.30, 1.15, 1.2, ("gti.entity", "gti.control", "gti.control.pause")),
        text_display(
            line("BRAK PODPOWIEDZI", GOLD),
            PANEL_CX,
            -11.05,
            0.05,
            scale=0.55,
            tag_list=("gti.entity", "gti.text", "gti.panel", "gti.hud.hint"),
        ),
        text_display(
            line("RĘCZNIE", PURPLE),
            PANEL_CX,
            0.25,
            0.05,
            scale=0.52,
            tag_list=("gti.entity", "gti.text", "gti.panel", "gti.hud.timer"),
        ),
    ]

    # -- bottom cards ---------------------------------------------------
    cards = [
        ("PRÓBY", "guesses", GOLD, -8.55),
        ("PIKSELE", "pixels", CYAN, -2.85),
        ("BŁĘDY", "wrong", RED, 2.85),
        ("CZAS", "time", BLUE, 8.55),
    ]
    bottom = []
    for label, key, color, x in cards:
        bottom += [
            block_display("tinted_glass", x, BOTTOM_Y, 5.25, 2.05, -0.10, 0.05, ("gti.entity", "gti.decor")),
            text_display(
                line(label, MUTED, True),
                x,
                BOTTOM_Y + 0.52,
                0.03,
                scale=0.5,
                tag_list=("gti.entity", "gti.text", "gti.decor"),
            ),
            text_display(
                line("0", color, True),
                x,
                BOTTOM_Y - 0.42,
                0.03,
                scale=1.15,
                tag_list=("gti.entity", "gti.text", "gti.decor", f"gti.hud.b.{key}"),
            ),
        ]

    # -- progress meter (left of the board) -----------------------------
    meter = [
        text_display(
            line("POSTĘP", MUTED, True),
            -11.55,
            -10.35,
            0.04,
            scale=0.52,
            tag_list=("gti.entity", "gti.text", "gti.decor"),
        ),
        text_display(
            line("0 / 256", MUTED, True),
            -11.55,
            -11.05,
            0.04,
            scale=0.46,
            tag_list=("gti.entity", "gti.text", "gti.decor", "gti.hud.progress"),
        ),
    ]
    for idx in range(20):
        y = -9.35 + idx * 0.95
        meter.append(
            block_display(
                "gray_concrete",
                -11.55,
                y,
                0.55,
                0.82,
                0.04,
                0.04,
                ("gti.entity", "gti.decor", "gti.seg"),
            )
        )
        meter.append(
            f"execute positioned ~-11.55 ~{fnum(y)} ~0.04 run "
            f"scoreboard players set @e[tag=gti.seg,sort=nearest,limit=1] gti.id {idx}"
        )

    # -- captions, header, subtitle -------------------------------------
    captions = [
        text_display(
            line("PIXEL REVEAL   •   " + f"{count} PRZEDMIOTÓW" + f"   •   JAVA {vd['label']}", MUTED),
            0,
            10.85,
            0.30,
            scale=0.72,
            tag_list=("gti.entity", "gti.text", "gti.decor"),
        ),
        text_display(
            line("ODPOWIEDŹ UKRYTA", MUTED),
            0,
            -11.0,
            0.04,
            scale=0.72,
            tag_list=("gti.entity", "gti.text", "gti.decor", "gti.hud.answer"),
        ),
        text_display(
            line("Witaj! Kliknij kafelek, aby odsłonić fragment ikony.", DIM),
            0,
            -11.72,
            0.04,
            scale=0.56,
            tag_list=("gti.entity", "gti.text", "gti.decor", "gti.hud.event"),
        ),
    ]

    # -- overlays -------------------------------------------------------
    overlays = [
        text_display(
            title_component("3", GOLD),
            0,
            -0.2,
            0.93,
            scale=0.01,
            tag_list=("gti.entity", "gti.text", "gti.overlay", "gti.overlay.count"),
            view_range=8.0,
        ),
        text_display(
            title_component("PRZYGOTUJ SIĘ", WHITE),
            0,
            3.4,
            0.93,
            scale=0.01,
            tag_list=("gti.entity", "gti.text", "gti.overlay", "gti.overlay.title"),
            view_range=8.0,
        ),
        text_display(
            line("Losowanie przedmiotu z pełnej puli", MUTED),
            0,
            1.9,
            0.93,
            scale=0.01,
            tag_list=("gti.entity", "gti.text", "gti.overlay", "gti.overlay.sub"),
            view_range=8.0,
        ),
        text_display(
            title_component("NIE TEN ITEM", RED),
            0,
            8.3,
            0.94,
            scale=0.01,
            background=RED_BG,
            tag_list=("gti.entity", "gti.text", "gti.overlay", "gti.overlay.bad"),
            view_range=8.0,
        ),
    ]

    # -- shutter --------------------------------------------------------
    shutter = []
    for idx in range(8):
        y = 10.3 - idx * 2.6
        shutter.append(
            block_display(
                "black_concrete",
                0,
                y,
                21.4,
                2.55,
                0.62,
                0.04,
                ("gti.entity", "gti.decor", "gti.shutter"),
            )
        )
        shutter.append(
            f"execute positioned ~0 ~{fnum(y)} ~0.62 run "
            f"scoreboard players set @e[tag=gti.shutter,sort=nearest,limit=1] gti.id {idx}"
        )

    # -- scanner, runners, halo -----------------------------------------
    effects = [
        block_display(
            "cyan_stained_glass",
            0,
            0,
            20.9,
            0.08,
            0.45,
            0.02,
            ("gti.entity", "gti.decor", "gti.scan"),
        ),
        item_display("end_rod", -10.0, 10.0, 0.58, 0.45, ("gti.entity", "gti.decor", "gti.run0")),
        item_display("end_rod", 10.0, -10.0, 0.58, 0.45, ("gti.entity", "gti.decor", "gti.run1")),
    ]
    for idx in range(12):
        effects.append(
            item_display(
                "firework_star",
                0,
                0,
                0.88,
                0.01,
                ("gti.entity", "gti.decor", "gti.halo"),
                extra='billboard:"center"',
            )
        )
        effects.append(
            f"execute positioned ~0 ~0 ~0.88 run "
            f"scoreboard players set @e[tag=gti.halo,sort=nearest,limit=1] gti.id {idx}"
        )

    resets = [
        "scoreboard players set #pulse gti.var 0",
        "scoreboard players set #shutter gti.var 0",
        "scoreboard players set #bob gti.var 0",
        "scoreboard players set #sway gti.var 0",
        "scoreboard players set #scan gti.var 0",
        "scoreboard players set #run0 gti.var 0",
        "scoreboard players set #run1 gti.var 40",
        "scoreboard players set #halo gti.var 0",
    ]
    columns = [f"function gti:internal/columns/{i}" for i in range(TILES)]
    pixels = [f"function gti:internal/pixels/{i}" for i in range(TILES)]

    return (
        out
        + panel
        + bottom
        + meter
        + captions
        + header_lines()
        + overlays
        + shutter
        + effects
        + resets
        + columns
        + pixels
    )


def mask_lines(col: int) -> list[str]:
    out = []
    for row in range(TILES):
        x = (col - 7.5) * TILE
        y = (7.5 - row) * TILE
        idx = row * TILES + col
        z = MASK_Z + ((col + row) % 2) * 0.001
        out.append(
            block_display(
                "black_concrete",
                x,
                y,
                1.26,
                1.26,
                z,
                0.055,
                ("gti.entity", "gti.mask", f"gti.col{col}", f"gti.row{row}"),
            )
        )
        out.append(
            f"execute positioned ~{fnum(x - 0.63)} ~{fnum(y - 0.63)} ~{fnum(z)} run "
            f"scoreboard players set @e[tag=gti.mask,sort=nearest,limit=1] gti.id {idx}"
        )
    return out


def pixel_lines(col: int) -> list[str]:
    out = []
    for row in range(TILES):
        x = (col - 7.5) * TILE
        y = (7.5 - row) * TILE
        idx = row * TILES + col
        out.append(
            interaction(
                x,
                y,
                0.34,
                1.22,
                1.22,
                ("gti.entity", "gti.pixel", f"gti.col{col}", f"gti.row{row}"),
            )
        )
        out.append(
            f"execute positioned ~{fnum(x)} ~{fnum(y)} ~0.34 run "
            f"scoreboard players set @e[tag=gti.pixel,sort=nearest,limit=1] gti.id {idx}"
        )
    return out


def ripple_bands() -> list[list[int]]:
    bands: list[list[int]] = [[] for _ in range(8)]
    for row in range(TILES):
        for col in range(TILES):
            bands[min(7, (col + row) // 4)].append(row * TILES + col)
    return bands


def ripple_lines() -> dict[str, str]:
    """Colour sweep used during the intro (masks only, no spoilers)."""
    colors = ["cyan_concrete", "light_blue_concrete", "blue_concrete", "purple_concrete", "magenta_concrete", "pink_concrete"]
    out: dict[str, str] = {}
    bands = ripple_bands()
    for idx, tiles in enumerate(bands):
        color = colors[idx % len(colors)]
        out[f"visual/ripple_{idx}"] = _mc(
            [
                f'data modify entity @e[tag=gti.mask,scores={{gti.id={tile}}},limit=1] block_state.Name set value "minecraft:{color}"'
                for tile in tiles
            ]
        )
        out[f"visual/ripple_clear_{idx}"] = _mc(
            [
                f'data modify entity @e[tag=gti.mask,scores={{gti.id={tile}}},limit=1] block_state.Name set value "minecraft:black_concrete"'
                for tile in tiles
            ]
        )
    return out


def _mc(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"
