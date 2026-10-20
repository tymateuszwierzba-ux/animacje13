"""Assemble the three Guess the Item 4.0 datapack zips."""

from __future__ import annotations

import json
import shutil
import struct
import zipfile
import zlib
from pathlib import Path

import game
import ui
from dataset import CATEGORY_LABELS, CATEGORY_ORDER, grouped
from model import VERSIONS

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build4"

DESCRIPTION = {
    "1.21.11": "Guess the Item 4.0 • 1504 items • bedrock board • max-attempt strip",
    "26.2": "Guess the Item 4.0 • 1536 items • bedrock board • max-attempt strip",
    "26.3": "Guess the Item 4.0 • 1657 items • bedrock board • max-attempt strip",
}


def pack_meta(vd: dict) -> dict:
    return {
        "pack": {
            "description": DESCRIPTION[vd["label"]],
            "min_format": [vd["pack_format"], vd["pack_format_minor"]],
            "max_format": [vd["pack_format"], vd["pack_format_minor"]],
        }
    }


def png_icon() -> bytes:
    """128x128 icon: dark card, gradient frame, bedrock-ish checker."""
    w = h = 128
    px = [[(8, 12, 22, 255) for _ in range(w)] for _ in range(h)]

    def rect(x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(h, y1)):
            for x in range(max(0, x0), min(w, x1)):
                px[y][x] = color

    def lerp(a, b, t):
        return tuple(max(0, min(255, int(round(a[i] + (b[i] - a[i]) * t)))) for i in range(3))

    cyan = (69, 233, 224)
    magenta = (244, 123, 198)
    for i in range(9):
        c = lerp(cyan, magenta, i / 8) + (255,)
        rect(4 + i, 4 + i, w - 4 - i, 5 + i, c)
        rect(4 + i, h - 5 - i, w - 4 - i, h - 4 - i, c)
        rect(4 + i, 4 + i, 5 + i, h - 4 - i, c)
        rect(w - 5 - i, 4 + i, w - 4 - i, h - 4 - i, c)
    rect(14, 14, w - 14, h - 14, (13, 20, 34, 255))

    # bedrock 8x8 checker in the middle
    tone = [(96, 96, 100), (56, 56, 60), (120, 120, 124), (72, 72, 76)]
    cell = 12
    for gy in range(8):
        for gx in range(8):
            color = tone[(gx * 7 + gy * 5 + (gx ^ gy)) % 4] + (255,)
            rect(16 + gx * cell, 16 + gy * cell, 16 + (gx + 1) * cell, 16 + (gy + 1) * cell, color)
    # magenta crack
    for step in range(48):
        x = 16 + step * 2
        y = 16 + int(step * 1.6)
        rect(x, y, x + 5, y + 5, (244, 123, 198, 255))
        rect(x + 2, y + 2, x + 5, y + 5, (255, 255, 255, 255))

    raw = bytearray()
    for row in px:
        raw.append(0)
        for r, g, b, a in row:
            raw += bytes((r, g, b, a))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def readme(vd: dict) -> str:
    version = vd["label"]
    count = vd["count"]
    cats = vd["categories"]
    cat_lines = "\n".join(f"| {CATEGORY_LABELS[cat].title()} | {cats[cat]} |" for cat in CATEGORY_ORDER)
    return f"""# GUESS THE ITEM 4.0
### BLOCK BOARD • BEDROCK SHIELD • MAX-ATTEMPT STRIP • Minecraft Java {version}

Guess the hidden item from the pixels you carve out of a **bedrock wall**. The board is
built from real blocks: every cell is a bedrock block, and revealing a cell swaps it for
the matching coloured block until the item icon is complete.
**{count} items**, {len(CATEGORY_ORDER)} categories, dialog GUI, hints, attempt limit and stats.
No mods, no resource pack, no plugins.

## Install

1. Drop the ZIP (do not unpack) into:
   - single player: `.minecraft/saves/WORLD/datapacks/`
   - server: `WORLD/datapacks/`
2. In the Overworld, on flat open ground, run as operator:
   ```mcfunction
   /reload
   /function gti:setup
   ```
3. The wall is built 30 blocks north of you and the camera turns to face it.
4. Open the menu and press **START ROUND**.

`/function gti:remove` removes the board and every effect, `/function gti:view` re-centres
the camera, `/function gti:start` starts a round without clicking.

## Controls

| Action | How |
|---|---|
| Crack a cell | left or right click the bedrock wall |
| Reveal cells at random | **REVEAL** on the wall console or `/trigger gti_reveal set 1` |
| Guess | hold the item in your main hand and press **GUESS** or `/trigger gti_guess set 1` |
| Hint (3 levels) | **HINT** or `/trigger gti_hint set 1` |
| Menu / dialogs | **MENU**, `/function gti:menu` or `/trigger gti_menu set 1` |
| New round | **START ROUND** or `/trigger gti_next set 1` |
| Stop | `/function gti:stop` |

Dialog ids use the namespace form (`gti:menu`, `gti:host`, ...), trigger objectives use
underscores (`gti_menu`, `gti_next`, ...), so there is no dot/colon mix-up.

## The LIMIT strip

Above the wall sits a hotbar-like strip: the **maximum attempt counter**.

- it only appears when you set a limit (settings slider `Max attempts`, 0 = unlimited) and
  shows exactly as many sockets as that limit (up to {32}), centred over the wall,
- every revealed cell uses one pip, a wrong guess uses three, a hint uses two,
- pips stay lime, then turn yellow, orange and red as the budget drains,
- when the last pip is used the round ends and the answer is revealed.

## GUI

| Dialog | Contents |
|---|---|
| `gti:menu` | start, reveal, guess, hint, stats, host panel, catalogue, rules |
| `gti:host` | start/stop, settings, catalogue, held item, random answer, typed id, presets, stats |
| `gti:settings` | max attempts, cells per click, free cells, time limit, reveal mode, hints |
| `gti:rules` | short rules and scoring |
| `gti:stats` | personal stats and reset |
| `gti:item_id` | type any item id as the answer |
| `gti:catalogue/index` + `gti:catalogue/<category>/<page>` | every item id, {24} per page |
| `gti:summary` | end-of-round summary |

## Scoring

- revealed cell: **1 attempt**, wrong guess: **3 attempts**, hint: **2 attempts**,
- the answer may also be a variant of the item (copper vs waxed copper, stone bricks vs
  infested stone bricks) - {len(vd['equivalents'])} equivalence groups are included,
- unlimited mode (limit 0) still tracks attempts for the personal best,
- personal best = fewest attempts in a solved round; ties are broken by fewer revealed cells.

## Categories

| Category | Items |
|---|---|
{cat_lines}

## Files

```
pack.mcmeta                   pack format {vd['pack_format']}.{vd['pack_format_minor']}
pack.png                      generated icon
README_EN.md                  this file
ITEM_LIST.txt                 every id and English name
data/gti/function/            logic, animations, art data, world build
data/gti/dialog/              dialogs (menu, host, settings, catalogue, ...)
data/gti/tags/item/           answers + equivalence tags
data/minecraft/tags/function  load + tick
```

## Notes

- Build the board in the **Overworld**; the pack refuses other dimensions.
- `/function gti:setup` needs operator rights. Players without OP can use the wall console
  and the `/trigger gti_*` objectives.
- The board is meant for a flat area with about 30 blocks of free space in front of the wall.
"""


def item_list(vd: dict) -> str:
    groups = grouped(vd["label"])
    lines = [f"GUESS THE ITEM 4.0 - {vd['label']} - {vd['count']} items", ""]
    for cat in CATEGORY_ORDER:
        lines.append(f"== {CATEGORY_LABELS[cat].title()} ({len(groups[cat])}) ==")
        for item in groups[cat]:
            lines.append(f"{item['id']:44s} {item['name']}")
        lines.append("")
    return "\n".join(lines)


def tag(values: list[str]) -> dict:
    return {"values": values}


def build_version(vd: dict) -> None:
    files: dict[str, bytes] = {}
    files["pack.mcmeta"] = json.dumps(pack_meta(vd), ensure_ascii=False, indent=2).encode()
    files["pack.png"] = png_icon()
    files["README_EN.md"] = readme(vd).encode()
    files["ITEM_LIST.txt"] = item_list(vd).encode()

    functions = game.game_functions(vd)
    functions.update(ui.ui_functions(vd))
    for name, body in functions.items():
        files[f"data/gti/function/{name}.mcfunction"] = body.encode()

    for name, dialog in ui.dialogs(vd).items():
        files[f"data/gti/dialog/{name}.json"] = json.dumps(dialog, ensure_ascii=False).encode()

    items = vd["items"]
    files["data/gti/tags/item/answers.json"] = json.dumps(
        tag([item["id"] for item in items]), ensure_ascii=False).encode()
    for index, group in enumerate(vd["equivalents"]):
        files[f"data/gti/tags/item/equivalent/g{index}.json"] = json.dumps(
            tag(group), ensure_ascii=False).encode()

    files["data/minecraft/tags/function/load.json"] = json.dumps({"values": ["gti:load"]}).encode()
    files["data/minecraft/tags/function/tick.json"] = json.dumps({"values": ["gti:tick"]}).encode()

    target = BUILD / vd["label"]
    if target.exists():
        shutil.rmtree(target)
    for path, data in files.items():
        full = target / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)

    zip_path = ROOT / vd["file"]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(files):
            info = zipfile.ZipInfo(path, date_time=(2026, 10, 20, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, files[path])
    print(f"{zip_path.name}: {zip_path.stat().st_size / 1024:.0f} KiB, {vd['count']} items, "
          f"{len(functions)} functions, {len(ui.dialogs(vd))} dialogs")


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    for entry in VERSIONS:
        from model import DATA

        base = DATA[entry["label"]]
        merged = {**entry, **{k: base[k] for k in ("count", "items", "categories", "equivalents")}}
        build_version(merged)


if __name__ == "__main__":
    main()
