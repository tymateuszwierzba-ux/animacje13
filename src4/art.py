"""Bakes the per-version item data: artwork arrays, id list, hint metadata."""

from __future__ import annotations

from model import ART, PALETTE, mc

CATS = ["blocks", "equipment", "food", "mobs", "materials", "other"]
PALETTE_NAMES = ["black_concrete"] + list(PALETTE["blocks"])  # 0 = transparent


def _key(item_id: str) -> str:
    return item_id.replace(":", "_").replace("/", "_")


def _mask(name: str) -> str:
    base = name.split(":", 1)[-1]
    dots = "•" * max(0, len(base) - 2)
    return base[0].upper() + dots + (base[-1].upper() if len(base) > 1 else "")


def _chunks(lines: list[str], size: int) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for index, line in enumerate(lines):
        out.setdefault(index // size, []).append(line)
    return out


def art_functions(vd: dict) -> dict[str, str]:
    items = vd["items"]
    out: dict[str, str] = {}

    out["data/palette"] = mc([
        "data modify storage gti:art palette set value "
        + "["
        + ",".join(f'"{name}"' for name in PALETTE_NAMES)
        + "]"
    ])

    art_lines = []
    ids_lines = []
    meta_lines = []
    for item in items:
        item_id = item["id"]
        pixels = ART[item_id]
        art_lines.append(
            f'data modify storage gti:art {_key(item_id)} set value ['
            + ",".join(str(v) for v in pixels)
            + "]"
        )
        ids_lines.append(f'data modify storage gti:items ids append value "{item_id}"')
        meta_lines.append(
            f'data modify storage gti:items by_id."{item_id}" set value '
            f'{{cat:{CATS.index(item["cat"])},len:{len(item_id.split(":")[1])},'
            f'first:"{item["letters"][0]}",mask:"{_mask(item_id)}",'
            f'key:"{item["key"]}",ak:"{_key(item_id)}",eq:-1}}'
        )

    for chunk, lines in _chunks(art_lines, 140).items():
        out[f"data/art/{chunk}"] = mc(lines)
    for chunk, lines in _chunks(ids_lines, 400).items():
        out[f"data/ids/{chunk}"] = mc(lines)
    for chunk, lines in _chunks(meta_lines, 250).items():
        out[f"data/meta/{chunk}"] = mc(lines)

    init = ["function gti:data/palette", "data modify storage gti:items ids set value []"]
    init += [f"function gti:data/art/{c}" for c in sorted(_chunks(art_lines, 140))]
    init += [f"function gti:data/ids/{c}" for c in sorted(_chunks(ids_lines, 400))]
    init += [f"function gti:data/meta/{c}" for c in sorted(_chunks(meta_lines, 250))]
    init += [
        "function gti:data/equiv",
        "function gti:data/cats",
        f"scoreboard players set #data_count gti.var {len(items)}",
        "scoreboard players set #maxpix gti.var 256",
    ]
    out["data/init"] = mc(init)

    # catalogue arrays (all + one per category, in category order)
    cat_lines = {name: [] for name in ["all"] + CATS}
    for item in items:
        cat_lines["all"].append(f'data modify storage gti:cat all append value "{item["id"]}"')
        cat_lines[item["cat"]].append(
            f'data modify storage gti:cat {item["cat"]} append value "{item["id"]}"'
        )
    reset = [f"data modify storage gti:cat {name} set value []" for name in ["all"] + CATS]
    out["data/cats"] = mc(
        reset
        + [line for name in ["all"] + CATS for line in cat_lines[name]]
    )

    # equivalence groups -> per-id integer in the meta table
    groups = vd["equivalents"]
    eq_lines = []
    for index, group in enumerate(groups, start=1):
        for item_id in group:
            eq_lines.append(
                f'data modify storage gti:items by_id."{item_id}".eq set value {index}'
            )
    out["data/equiv"] = mc(eq_lines)

    return out
