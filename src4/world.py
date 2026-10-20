"""World shell: sandstone wall, block frame, bedrock board, attempt strip, console."""

from __future__ import annotations

from model import (
    AQUA,
    BLUE,
    COLS,
    CYAN,
    FRAME_BOTTOM,
    FRAME_LEFT,
    FRAME_RIGHT,
    FRAME_TOP,
    GOLD,
    GREEN,
    MAGENTA,
    MUTED,
    RED,
    ROWS,
    STRIP_LEFT,
    STRIP_MAX,
    STRIP_PITCH,
    STRIP_Y,
    WALL_BOTTOM,
    WALL_LEFT,
    WALL_RIGHT,
    WALL_TOP,
    WHITE,
    X0,
    Y0,
    Z_ART,
    Z_BACKING,
    Z_CLICK,
    Z_SHUTTER,
    Z_STONE,
    block_display,
    fnum,
    gradient,
    interaction,
    line,
    text_display,
)

CONSOLE_X = 10.4
INFO_X = -10.5


def cell_index(col: int, row: int) -> int:
    return row * COLS + col


def _set_id(x: float, y: float, z: float, tag: str, value: int) -> str:
    return (
        f"execute positioned ~{fnum(x)} ~{fnum(y)} ~{fnum(z)} run "
        f"scoreboard players set @e[tag={tag},sort=nearest,limit=1] gti.id {value}"
    )


def build_world(vd: dict) -> list[str]:
    out: list[str] = []

    # -- wall panels ----------------------------------------------------
    out.append(block_display("smooth_sandstone", -10.5, (WALL_BOTTOM + WALL_TOP) / 2, -0.42,
                             4.4, WALL_TOP - WALL_BOTTOM + 1, 0.55,
                             ("gti.entity", "gti.wall")))
    out.append(block_display("smooth_sandstone", 10.5, (WALL_BOTTOM + WALL_TOP) / 2, -0.42,
                             4.4, WALL_TOP - WALL_BOTTOM + 1, 0.55,
                             ("gti.entity", "gti.wall")))
    out.append(block_display("smooth_sandstone", 0, 23.9, -0.42, 18.8, 7.6, 0.55,
                             ("gti.entity", "gti.wall")))
    out.append(block_display("smooth_sandstone", 0, 1.2, -0.42, 18.8, 2.6, 0.55,
                             ("gti.entity", "gti.wall")))
    # brick seams so the big panels read as blocks
    for y in range(WALL_BOTTOM + 1, WALL_TOP, 2):
        for x in (-12.62, 12.62):
            out.append(block_display("cut_sandstone", x, y + 0.5, 0.04, 1.2, 0.16, 0.10,
                                     ("gti.entity", "gti.wall")))
    # crisp block ring around the window (flush with the 16x16 board)
    columns = int(FRAME_RIGHT - FRAME_LEFT) + 1
    for index in range(columns):
        x = FRAME_LEFT + index
        for y in (FRAME_BOTTOM, FRAME_TOP):
            out.append(block_display("cut_sandstone", x, y, Z_STONE, 1.0, 1.0, 0.62,
                                     ("gti.entity", "gti.frame")))
    for y in range(int(FRAME_BOTTOM) + 1, int(FRAME_TOP)):
        for x in (FRAME_LEFT, FRAME_RIGHT):
            out.append(block_display("cut_sandstone", x, y, Z_STONE, 1.0, 1.0, 0.62,
                                     ("gti.entity", "gti.frame")))
    for cx in (FRAME_LEFT, FRAME_RIGHT):
        for cy in (FRAME_BOTTOM, FRAME_TOP):
            out.append(block_display("chiseled_sandstone", cx, cy, Z_STONE + 0.04,
                                     1.0, 1.0, 0.68, ("gti.entity", "gti.frame")))
    # thin dark reveal, tucked behind the ring so it never covers the art
    for index in range(columns):
        x = FRAME_LEFT + index
        for y in (FRAME_BOTTOM - 0.02, FRAME_TOP + 0.02):
            out.append(block_display("polished_deepslate", x, y, Z_STONE - 0.06,
                                     0.9, 0.16, 0.4, ("gti.entity", "gti.frame")))
    for y in range(int(FRAME_BOTTOM) + 1, int(FRAME_TOP)):
        for x in (FRAME_LEFT - 0.02, FRAME_RIGHT + 0.02):
            out.append(block_display("polished_deepslate", x, y, Z_STONE - 0.06,
                                     0.16, 0.9, 0.4, ("gti.entity", "gti.frame")))
    # plinth
    for x in range(WALL_LEFT, WALL_RIGHT + 1):
        out.append(block_display("stone_bricks", x, 0.5, 0.55, 1.0, 1.0, 1.1,
                                 ("gti.entity", "gti.wall")))
        out.append(block_display("polished_deepslate", x, 0.5, 1.14, 0.98, 0.2, 0.06,
                                 ("gti.entity", "gti.wall")))

    # -- backing + cells -------------------------------------------------
    out.append(block_display("black_concrete", 0, Y0 + 7.5, Z_BACKING,
                             16.8, 16.8, 0.16, ("gti.entity", "gti.decor"),
                             extra="brightness:{sky:0,block:0}"))
    for row in range(ROWS):
        for col in range(COLS):
            x = X0 + col
            y = Y0 + row
            index = cell_index(col, row)
            out.append(block_display("bedrock", x, y, Z_ART, 1.0, 1.0, 1.0,
                                     ("gti.entity", "gti.cell", f"gti.col{col}")))
            out.append(_set_id(x, y, Z_ART, "gti.cell", index))
            out.append(interaction(x, y, Z_CLICK, 0.98, 0.98,
                                   ("gti.entity", "gti.click", f"gti.col{col}")))
            out.append(_set_id(x, y, Z_CLICK, "gti.click", index))

    # -- bedrock curtain -------------------------------------------------
    for col in range(COLS):
        x = X0 + col
        out.append(
            block_display("bedrock", x, Y0 + 7.5, Z_SHUTTER, 1.0, 16.0, 0.3,
                          ("gti.entity", "gti.shutter", f"gti.col{col}"),
                          transformation={
                              "scale": [1.0, 16.0, 0.3],
                              "translation": [0.0, 17.4, 0.0],
                          })
        )

    # -- attempt strip ---------------------------------------------------
    out.append(block_display("black_concrete", 0, STRIP_Y, 0.24, 17.4, 1.66, 0.08,
                             ("gti.entity", "gti.strip")))
    for index in range(STRIP_MAX):
        x = STRIP_LEFT + (index + 0.5) * STRIP_PITCH
        out.append(block_display("black_concrete", x, STRIP_Y, 0.30, 0.42, 1.36, 0.10,
                                 ("gti.entity", "gti.strip")))
        out.append(block_display("structure_void", x, STRIP_Y, 0.38, 0.30, 1.12, 0.10,
                                 ("gti.entity", "gti.strip", "gti.pip")))
        out.append(_set_id(x, STRIP_Y, 0.38, "gti.pip", index))
    out.append(text_display(line("LIMIT", MUTED, True), STRIP_LEFT - 0.85, STRIP_Y, 0.46,
                            0.42, tag_list=("gti.entity", "gti.strip"), align="right"))
    return out


def world_text(vd: dict) -> list[str]:
    """Static titles plus the dynamic HUD labels."""
    version = vd["label"]
    count = vd["count"]
    out: list[str] = []

    out.append(text_display(gradient("GUESS THE ITEM", CYAN, MAGENTA), 0, 25.0, 0.40,
                            1.95, tag_list=("gti.entity", "gti.text")))
    out.append(text_display(line(f"MINECRAFT {version}   •   {count} ITEMS   •   BLOCK EDITION",
                                 MUTED, True), 0, 23.7, 0.40, 0.60,
                            tag_list=("gti.entity", "gti.text")))
    out.append(text_display(line("REVEAL THE PICTURE  •  GUESS THE ITEM", BLUE, True),
                            0, 23.05, 0.40, 0.54, tag_list=("gti.entity", "gti.text")))

    out.append(text_display(line("READY", AQUA, True), 0, 20.25, 0.46, 0.62,
                            tag_list=("gti.entity", "gti.text", "gti.hud.hint")))
    out.append(text_display(line("", GREEN, True), 0, 0.80, 1.30, 0.52,
                            tag_list=("gti.entity", "gti.text", "gti.hud.status")))

    labels = [
        ("ROUND", "gti.hud.round", GOLD, "—"),
        ("USED", "gti.hud.used", RED, "0"),
        ("LEFT", "gti.hud.left", GREEN, "∞"),
        ("FOUND", "gti.hud.found", CYAN, "0/256"),
        ("TIME", "gti.hud.time", BLUE, "0:00"),
    ]
    for i, (label, tag, color, initial) in enumerate(labels):
        y = 15.2 - i * 2.55
        out.append(text_display(line(label, MUTED, True), INFO_X, y + 0.62, 0.46, 0.48,
                                tag_list=("gti.entity", "gti.text")))
        out.append(text_display(line(initial, color, True), INFO_X, y - 0.30, 0.46, 1.05,
                                tag_list=("gti.entity", "gti.text", tag)))

    buttons = [
        ("GUESS", "gti.control.guess", "lime_concrete"),
        ("REVEAL", "gti.control.reveal", "cyan_concrete"),
        ("HINT", "gti.control.hint", "yellow_concrete"),
        ("MENU", "gti.control.menu", "magenta_concrete"),
    ]
    for i, (label, tag, block) in enumerate(buttons):
        y = 14.8 - i * 3.0
        out.append(block_display("polished_blackstone", CONSOLE_X, y, 0.62, 3.0, 1.7, 0.22,
                                 ("gti.entity", "gti.console")))
        out.append(block_display(block, CONSOLE_X, y, 0.74, 2.7, 1.34, 0.12,
                                 ("gti.entity", "gti.console")))
        out.append(text_display(line(label, WHITE, True), CONSOLE_X, y, 0.90, 0.70,
                                tag_list=("gti.entity", "gti.text")))
        out.append(interaction(CONSOLE_X, y, 1.06, 2.9, 1.7, ("gti.entity", "gti.control", tag)))
    return out
