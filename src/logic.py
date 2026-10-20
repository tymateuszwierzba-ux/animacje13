"""Game data, state machine, HUD and visual-effect functions."""

from __future__ import annotations

import json
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
    PURPLE,
    RED,
    WHITE,
    fnum,
    mc,
)

TILES = 16
PIXELS = TILES * TILES
CATS = ["blocks", "equipment", "food", "mobs", "materials", "other"]
CAT_LABELS = [
    "BLOKI I BUDOWANIE",
    "BROŃ, NARZĘDZIA, PANCERZ",
    "JEDZENIE I ROŚLINY",
    "MOBY I JAJKA",
    "SUROWCE I SKŁADNIKI",
    "POZOSTAŁE PRZEDMIOTY",
]

CAT_COLORS = ["#61EDE5", "#F6CF84", "#8BE28B", "#F47BC6", "#B295FF", "#FF8996"]


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------------
# item data
# ---------------------------------------------------------------------------


def data_functions(vd: dict) -> dict[str, str]:
    items = vd["items"]
    out: dict[str, str] = {}
    chunks: dict[int, list[str]] = {}
    meta_chunks: dict[int, list[str]] = {}

    for idx, item in enumerate(items):
        base = item["id"].split(":", 1)[1]
        chunks.setdefault(idx // 320, []).append(
            f'data modify storage gti:items ids append value "{item["id"]}"'
        )
        mask = base[0] + "•" * max(0, len(base) - 2) + (base[-1] if len(base) > 1 else "")
        meta = (
            f'{{cat:{CATS.index(item["cat"])},len:{len(base)},first:"{base[0].upper()}",'
            f'mask:"{mask}",key:"{item["key"]}",eq:{item.get("eq", -1)}}}'
        )
        meta_chunks.setdefault(idx // 320, []).append(
            f'data modify storage gti:items by_id."{item["id"]}" set value {meta}'
        )

    for key, lines in chunks.items():
        out[f"data/items/{key}"] = mc(lines)
    for key, lines in meta_chunks.items():
        out[f"data/meta/{key}"] = mc(lines)

    init = ["data modify storage gti:items ids set value []"]
    init += [f"function gti:data/items/{key}" for key in sorted(chunks)]
    init += [f"function gti:data/meta/{key}" for key in sorted(meta_chunks)]
    init += [
        f"scoreboard players set #data_count gti.var {len(items)}".replace("gti.var", "gti.var"),
        f"scoreboard players set #maxpix gti.var {PIXELS}",
    ]
    out["data/init"] = mc(init)

    out["data/random_index"] = mc(
        [
            "execute store result score #random gti.var run random value 0..$count".replace(
                "$count", "{count}"
            ),
            "scoreboard players operation #random gti.var %= #data_count gti.var",
            "scoreboard players add #random gti.var 1",
            "execute if score #random gti.var = #last_index gti.var run scoreboard players add #random gti.var 1",
            "execute if score #random gti.var > #data_count gti.var run scoreboard players set #random gti.var 1",
            "scoreboard players operation #last_index gti.var = #random gti.var",
            "scoreboard players remove #random gti.var 1",
            "execute store result storage gti:ctx index int 1 run scoreboard players get #random gti.var",
        ]
    ).replace("{count}", str(len(items) - 1))

    out["data/pick"] = mc(
        ['$data modify storage gti:ctx id set from storage gti:items ids[$(index)]']
    )
    out["data/apply"] = mc(
        [
            '$data modify entity @e[tag=gti.item,limit=1] item set value {id:"$(id)",count:1}',
            "execute as @e[tag=gti.item] run data modify entity @s transformation set value "
            "{scale:[20f,20f,0.001f],translation:[0f,0f,0f],"
            "left_rotation:[0f,1f,0f,0f],right_rotation:[0f,0f,0f,1f]}",
        ]
    )
    out["data/lookup"] = mc(
        [
            '$data modify storage gti:ctx meta set from storage gti:items by_id."$(id)"',
            "data modify storage gti:cfg meta set from storage gti:ctx meta",
            "data modify storage gti:cfg answer_key set from storage gti:ctx meta.key",
            "execute store result score #eq_answer gti.var run data get storage gti:ctx meta.eq",
            "execute store result score #hint_cat gti.var run data get storage gti:ctx meta.cat",
        ]
    )
    out["data/random_answer"] = mc(
        [
            "function gti:data/random_index",
            "function gti:data/pick with storage gti:ctx",
            "data modify storage gti:cfg answer set from storage gti:ctx id",
            "function gti:data/lookup with storage gti:ctx",
            "function gti:data/apply with storage gti:ctx",
        ]
    )
    out["data/fixed_answer"] = mc(
        [
            "data modify storage gti:ctx id set from storage gti:config fixed.id",
            "function gti:data/lookup with storage gti:ctx",
            "data modify storage gti:cfg answer set from storage gti:config fixed.id",
            "data modify entity @e[tag=gti.item,limit=1] item set from storage gti:config fixed",
            "execute as @e[tag=gti.item] run data modify entity @s transformation set value "
            "{scale:[20f,20f,0.001f],translation:[0f,0f,0f],"
            "left_rotation:[0f,1f,0f,0f],right_rotation:[0f,0f,0f,1f]}",
        ]
    )
    out["data/set_answer"] = mc(
        [
            "scoreboard players set #hint_stage gti.var 0",
            "scoreboard players set #eq_answer gti.var -1",
            'data modify storage gti:cfg hint set value "BRAK PODPOWIEDZI"',
            "execute if score #source gti.var matches 0 run function gti:data/random_answer",
            "execute if score #source gti.var matches 1 run function gti:data/fixed_answer",
        ]
    )
    out["data/set_fixed"] = mc(
        [
            "scoreboard players set #source gti.var 1",
            'data modify storage gti:config fixed.id set from storage gti:tmp id',
            'data modify storage gti:config fixed.count set value 1',
            'data modify storage gti:tmp msg set value ""',
            'execute if data storage gti:tmp {manual:1b} run data modify storage gti:tmp msg set value "Ustawiono hasło z ręki."',
            'execute if data storage gti:tmp {manual:0b} run data modify storage gti:tmp msg set value "Ustawiono hasło z katalogu."',
            "function gti:visual/event with storage gti:tmp",
            "tellraw @s [{\"text\":\"✔ \",\"color\":\"#8BE28B\"},{\"nbt\":\"msg\",\"storage\":\"gti:tmp\",\"color\":\"#F2F7FF\"},{\"text\":\" Hasło: \",\"color\":\"gray\"},{\"nbt\":\"id\",\"storage\":\"gti:tmp\",\"color\":\"#61EDE5\"}]",
        ]
    )
    return out


# ---------------------------------------------------------------------------
# visual storage and effects
# ---------------------------------------------------------------------------


def ring_storage() -> list[dict]:
    pts = []
    n = 20
    half = 10.95
    for i in range(n):
        pts.append({"x": round(-half + i * (2 * half / n), 3), "y": half})
    for i in range(n):
        pts.append({"x": half, "y": round(half - i * (2 * half / n), 3)})
    for i in range(n):
        pts.append({"x": round(half - i * (2 * half / n), 3), "y": -half})
    for i in range(n):
        pts.append({"x": -half, "y": round(-half + i * (2 * half / n), 3)})
    return pts


def sway_storage() -> list[list[float]]:
    quats = []
    for i in range(12):
        angle = math.radians(-6.0 + (i % 7) * 2.0)
        # 180 deg yaw (so the GUI sprite faces the player) times a small z twist
        yaw = math.pi
        qy = (0.0, math.sin(yaw / 2), 0.0, math.cos(yaw / 2))
        qz = (0.0, 0.0, math.sin(angle / 2), math.cos(angle / 2))
        x1, y1, z1, w1 = qy
        x2, y2, z2, w2 = qz
        q = (
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        )
        quats.append([round(v, 5) for v in q])
    return quats


def bob_storage() -> list[list[float]]:
    frames = []
    for f in range(8):
        phase = f / 8 * math.tau
        frames.append([round(math.sin(phase + i * 0.55) * 0.11, 3) for i in range(14)])
    return frames


def halo_storage() -> list[list[list[float]]]:
    frames = []
    for f in range(36):
        frame = []
        for i in range(12):
            angle = math.tau * (i / 12 + f / 36)
            frame.append(
                [
                    round(math.cos(angle) * 13.6, 2),
                    round(math.sin(angle) * 13.6, 2),
                    round(0.9 + math.sin(angle * 2) * 0.15, 2),
                ]
            )
        frames.append(frame)
    return frames


def _floats(value) -> str:
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_floats(v) for v in value) + "]"
    return f"{float(value):.5f}f"


def visual_functions(vd: dict) -> dict[str, str]:
    f: dict[str, str] = {}

    setup = [
        "data modify storage gti:fx ring set value []",
        "data modify storage gti:fx bob set value []",
        "data modify storage gti:fx sway set value []",
        "data modify storage gti:fx halo set value []",
        "data modify storage gti:fx args set value []",
        "data modify storage gti:fx bobargs set value []",
        "data modify storage gti:fx quat set value [0f,0f,0f,1f]",
        "scoreboard players set #eighty gti.var 80",
        "scoreboard players set #ten gti.var 10",
        "scoreboard players set #hundred gti.var 100",
        "scoreboard players set #twelve gti.var 12",
        "scoreboard players set #eight gti.var 8",
        "scoreboard players set #two gti.var 2",
        "scoreboard players set #three gti.var 3",
        "scoreboard players set #twenty gti.var 20",
        "scoreboard players set #sixty gti.var 60",
        "scoreboard players set #thousand gti.var 1000",
        "scoreboard players set #halo_max gti.var 36",
    ]
    setup += [f"data modify storage gti:fx ring append value {_json(p)}" for p in ring_storage()]
    setup += [f"data modify storage gti:fx bob append value {_floats(p)}" for p in bob_storage()]
    setup += [f"data modify storage gti:fx sway append value {_floats(p)}" for p in sway_storage()]
    setup += [f"data modify storage gti:fx halo append value {_floats(p)}" for p in halo_storage()]
    f["visual/setup"] = mc(setup)

    f["visual/tick"] = mc(
        [
            "execute unless score #state gti.var matches 2..3 run function gti:visual/scan",
            "execute if score #state gti.var matches 0..2 run function gti:visual/runners",
            "execute if score #state gti.var matches 3 run function gti:visual/finale_fx",
            "execute if score #clock gti.var matches 0 unless score #state gti.var matches 1 run function gti:visual/sway",
        ]
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
    f["visual/ring_pick"] = mc(["$data modify storage gti:fx args set from storage gti:fx ring[$(frame)]"])
    f["visual/ring_apply0"] = mc(
        ["$execute at @e[tag=gti.anchor,limit=1] run tp @e[tag=gti.run0,limit=1] ~$(x) ~$(y) ~0.58"]
    )
    f["visual/ring_apply1"] = mc(
        ["$execute at @e[tag=gti.anchor,limit=1] run tp @e[tag=gti.run1,limit=1] ~$(x) ~$(y) ~0.58"]
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
    f["visual/sway_pick"] = mc(["$data modify storage gti:fx quat set from storage gti:fx sway[$(frame)]"])
    f["visual/sway_apply"] = mc(
        ["data modify entity @e[tag=gti.item,limit=1] transformation.left_rotation set from storage gti:fx quat"]
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
    f["visual/bob_pick"] = mc(["$data modify storage gti:fx bobargs set from storage gti:fx bob[$(frame)]"])
    f["visual/bob_apply"] = mc(
        [
            f"execute store result entity @e[tag=gti.letter,scores={{gti.id={i}}},limit=1] transformation.translation[1] float 1 run data get storage gti:fx bobargs[{i}]"
            for i in range(14)
        ]
    )

    f["visual/pulse"] = mc(
        [
            "scoreboard players add #pulse gti.var 1",
            "scoreboard players operation #pulse gti.var %= #two gti.var",
            'execute if score #pulse gti.var matches 0 as @e[tag=gti.pulse.b] run data modify entity @s block_state.Name set value "minecraft:purple_concrete"',
            'execute if score #pulse gti.var matches 1 as @e[tag=gti.pulse.b] run data modify entity @s block_state.Name set value "minecraft:magenta_concrete"',
            'execute if score #pulse gti.var matches 0 as @e[tag=gti.pulse.c] run data modify entity @s block_state.Name set value "minecraft:cyan_concrete"',
            'execute if score #pulse gti.var matches 1 as @e[tag=gti.pulse.c] run data modify entity @s block_state.Name set value "minecraft:light_blue_concrete"',
        ]
    )

    f["visual/shutter_open"] = mc(
        [
            'execute as @e[tag=gti.shutter] run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{scale:[21.4f,2.55f,0.04f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}'
        ]
    )
    f["visual/shutter_close"] = mc(
        [
            'execute as @e[tag=gti.shutter] run data merge entity @s {start_interpolation:0,interpolation_duration:4,transformation:{scale:[21.4f,2.55f,0.04f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}'
        ]
    )
    f["visual/shutter_open_all"] = mc(
        [
            'execute as @e[tag=gti.shutter] run data merge entity @s {start_interpolation:0,interpolation_duration:6,transformation:{scale:[21.4f,0.02f,0.04f],translation:[0f,11.5f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}'
        ]
    )
    for k in range(8):
        f[f"visual/shutter_open_{k}"] = mc(
            [
                f'execute as @e[tag=gti.shutter,scores={{gti.id={k}}},limit=1] run data merge entity @s {{start_interpolation:0,interpolation_duration:5,transformation:{{scale:[21.4f,0.02f,0.04f],translation:[0f,11.5f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}}}'
            ]
        )
        f[f"visual/shutter_close_{k}"] = mc(
            [
                f'execute as @e[tag=gti.shutter,scores={{gti.id={k}}},limit=1] run data merge entity @s {{start_interpolation:0,interpolation_duration:4,transformation:{{scale:[21.4f,2.55f,0.04f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}}}'
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
    f["visual/halo_pick"] = mc(["$data modify storage gti:fx args set from storage gti:fx halo[$(frame)]"])
    halo_apply = []
    for i in range(12):
        halo_apply += [
            f"data modify entity @e[tag=gti.halo,scores={{gti.id={i}}},limit=1] transformation.translation set from storage gti:fx args[{i}]",
            f"data modify entity @e[tag=gti.halo,scores={{gti.id={i}}},limit=1] transformation.scale set value [0.7f,0.7f,0.001f]",
        ]
    f["visual/halo_apply"] = mc(halo_apply)
    f["visual/halo_reset"] = mc(
        [
            "execute as @e[tag=gti.halo] run data modify entity @s transformation.scale set value [0.01f,0.01f,0.001f]",
            "scoreboard players set #halo gti.var 0",
        ]
    )

    f["visual/confetti"] = mc(
        [
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:firework ~ ~10.5 ~0.9 9.5 2.5 0.4 0.2 90 force @a[tag=gti.player]",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:crit ~ ~8 ~0.9 9.5 4 0.4 0.08 45 force @a[tag=gti.player]",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:happy_villager ~ ~6 ~0.9 9 3.5 0.4 0.03 25 force @a[tag=gti.player]",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:electric_spark ~ ~11 ~0.9 10 1 0.2 0.1 25 force @a[tag=gti.player]",
        ]
    )

    f["visual/finale_fx"] = mc(
        [
            "execute if score #result gti.var matches 1 run function gti:visual/halo",
            "execute if score #result gti.var matches 1 if score #anim gti.var matches 30 run function gti:visual/confetti",
            "execute if score #result gti.var matches 1 if score #anim gti.var matches 55 run function gti:visual/confetti",
            "execute if score #result gti.var matches 1 if score #anim gti.var matches 80 run function gti:visual/confetti",
        ]
    )

    f["visual/particles_idle"] = mc(
        [
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:electric_spark ~ ~ ~0.5 9.8 9.8 0.3 0.01 4 force @a[tag=gti.player]",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:end_rod ~ ~9.8 ~0.4 9.5 0.2 0.05 0.003 2 force @a[tag=gti.player]",
        ]
    )

    f["visual/event"] = mc(
        [
            '$data modify entity @e[tag=gti.hud.event,limit=1] text set value [{"text":"$(msg)","color":"#8FA8C8"}]'
        ]
    )
    f["visual/answer_caption"] = mc(
        [
            '$data modify entity @e[tag=gti.hud.answer,limit=1] text set value [{"text":"ODPOWIEDŹ: ","color":"#8FA8C8","bold":true},{"translate":"$(key)","color":"#F6CF84","bold":true}]'
        ]
    )
    f["visual/answer_hidden"] = mc(
        [
            'data modify entity @e[tag=gti.hud.answer,limit=1] text set value [{"text":"ODPOWIEDŹ UKRYTA","color":"#8FA8C8"}]'
        ]
    )
    return f


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------


def hud_functions(vd: dict) -> dict[str, str]:
    f: dict[str, str] = {}
    count = vd["count"]

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
            'data modify storage gti:ui mm0 set value ""',
            'data modify storage gti:ui ss0 set value ""',
            'execute if score #mins gti.var matches ..9 run data modify storage gti:ui mm0 set value "0"',
            'execute if score #secs gti.var matches ..9 run data modify storage gti:ui ss0 set value "0"',
            'data modify storage gti:ui limit_label set value "∞"',
            "execute if score #limit gti.var matches 1.. run function gti:visual/set_limit_label with storage gti:ui",
            "function gti:visual/set_time with storage gti:ui",
            'data modify storage gti:ui mode set value "RĘCZNIE"',
            'execute if score #reveal_mode gti.var matches 1 run data modify storage gti:ui mode set value "PO BŁĘDZIE"',
            'execute if score #reveal_mode gti.var matches 2 run data modify storage gti:ui mode set value "AUTO"',
            'data modify storage gti:ui status set value "GOTOWA"',
            'execute if score #state gti.var matches 1 run data modify storage gti:ui status set value "INTRO"',
            'execute if score #state gti.var matches 2 run data modify storage gti:ui status set value "LIVE"',
            'execute if score #state gti.var matches 3 run data modify storage gti:ui status set value "FINALE"',
            'execute if score #paused gti.var matches 1 run data modify storage gti:ui status set value "PAUZA"',
            "scoreboard players set #timer_left gti.var 0",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_left gti.var = #interval gti.var",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_left gti.var -= #timer gti.var",
            "execute if score #timer_left gti.var matches ..-1 run scoreboard players set #timer_left gti.var 0",
            "scoreboard players operation #timer_left gti.var /= #twenty gti.var",
            "execute store result storage gti:ui timer_seconds int 1 run scoreboard players get #timer_left gti.var",
            "data modify storage gti:ui answer set from storage gti:cfg answer",
            "data modify storage gti:ui hint set from storage gti:cfg hint",
            'execute if score #hint_stage gti.var matches 0 run data modify storage gti:ui hint set value "BRAK PODPOWIEDZI"',
            'execute if score #hints_enabled gti.var matches 0 run data modify storage gti:ui hint set value "PODPOWIEDZI WYŁĄCZONE"',
            'data modify storage gti:ui timer_label set value "RĘCZNIE"',
            'execute if score #reveal_mode gti.var matches 1 run data modify storage gti:ui timer_label set value "PO BŁĘDZIE"',
            'execute if score #reveal_mode gti.var matches 2 run function gti:visual/fmt_timer with storage gti:ui',
            "function gti:visual/fmt_labels with storage gti:ui",
            "function gti:visual/hud_apply with storage gti:ui",
            "function gti:visual/progress",
            "function gti:visual/budget",
            "execute if score #state gti.var matches 2..3 run function gti:internal/bossbars",
        ]
    )

    f["visual/set_limit_label"] = mc(['$data modify storage gti:ui limit_label set value "$(limit)"'])
    f["visual/set_time"] = mc(['$data modify storage gti:ui time set value "$(mm0)$(mins):$(ss0)$(secs)"'])
    f["visual/fmt_timer"] = mc(['$data modify storage gti:ui timer_label set value "AUTO • $(timer_seconds)s"'])
    f["visual/fmt_labels"] = mc(
        [
            '$data modify storage gti:ui reveal_label set value "ODKRYJ ×$(batch)"',
            '$data modify storage gti:ui hint_label set value "PODPOWIEDŹ $(hint_stage)/3"',
            '$data modify storage gti:ui budget_label set value "$(cost) / $(limit_label)"',
            '$data modify storage gti:ui progress_label set value "$(pixels) / 256"',
            '$data modify storage gti:ui round_label set value "RUNDA $(round) • $(status)"',
            '$data modify storage gti:ui answer_line set value "ODPOWIEDŹ: $(answer)"',
        ]
    )

    f["visual/hud_apply"] = mc(
        [
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
            '$data modify entity @e[tag=gti.hud.progress,limit=1] text set value [{"text":"$(progress_label)","color":"#8FA8C8","bold":true}]',
            '$data modify entity @e[tag=gti.btn.reveal,limit=1] text set value [{"text":"$(reveal_label)","color":"#F2F7FF","bold":true}]',
            '$data modify entity @e[tag=gti.btn.hint,limit=1] text set value [{"text":"$(hint_label)","color":"#F2F7FF","bold":true}]',
            '$data modify entity @e[tag=gti.hud.timer,limit=1] text set value [{"text":"$(timer_label)","color":"#B295FF"}]',
        ]
    )

    colors = [
        "cyan_concrete", "cyan_concrete", "cyan_concrete", "light_blue_concrete",
        "light_blue_concrete", "light_blue_concrete", "blue_concrete", "blue_concrete",
        "blue_concrete", "purple_concrete", "purple_concrete", "purple_concrete",
        "magenta_concrete", "magenta_concrete", "magenta_concrete", "pink_concrete",
        "pink_concrete", "pink_concrete", "pink_concrete", "pink_concrete",
    ]
    progress = [
        "scoreboard players set #filled gti.var 0",
        "execute if score #pixels gti.var matches 1.. run scoreboard players operation #filled gti.var = #pixels gti.var",
        "scoreboard players operation #filled gti.var *= #twenty gti.var",
        "scoreboard players operation #filled gti.var /= #maxpix gti.var",
    ]
    for i in range(20):
        progress.append(
            f'execute if score #filled gti.var matches {i + 1}.. run data modify entity @e[tag=gti.seg,scores={{gti.id={i}}},limit=1] block_state.Name set value "minecraft:{colors[i]}"'
        )
        progress.append(
            f'execute if score #filled gti.var matches ..{i} run data modify entity @e[tag=gti.seg,scores={{gti.id={i}}},limit=1] block_state.Name set value "minecraft:gray_concrete"'
        )
    f["visual/progress"] = mc(progress)

    budget = [
        "scoreboard players set #filled gti.var 10",
        "execute if score #limit gti.var matches 1.. run scoreboard players operation #filled gti.var = #remaining gti.var",
        "execute if score #limit gti.var matches 1.. run scoreboard players operation #filled gti.var *= #ten gti.var",
        "execute if score #limit gti.var matches 1.. run scoreboard players operation #filled gti.var /= #limit gti.var",
        "execute if score #filled gti.var matches 11.. run scoreboard players set #filled gti.var 10",
        "execute if score #filled gti.var matches ..-1 run scoreboard players set #filled gti.var 0",
    ]
    shades = [
        "lime_concrete", "lime_concrete", "lime_concrete", "yellow_concrete",
        "yellow_concrete", "yellow_concrete", "orange_concrete", "orange_concrete",
        "red_concrete", "red_concrete",
    ]
    for i in range(10):
        budget.append(
            f'execute if score #filled gti.var matches {i + 1}.. run data modify entity @e[tag=gti.budgetseg,scores={{gti.id={i}}},limit=1] block_state.Name set value "minecraft:{shades[i]}"'
        )
        budget.append(
            f'execute if score #filled gti.var matches ..{i} run data modify entity @e[tag=gti.budgetseg,scores={{gti.id={i}}},limit=1] block_state.Name set value "minecraft:black_concrete"'
        )
    f["visual/budget"] = mc(budget)

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
            "bossbar set gti:budget color green",
            "execute if score #limit gti.var matches 1.. if score #remaining_boss gti.var matches ..8 run bossbar set gti:budget color red",
            "execute if score #limit gti.var matches 1.. if score #remaining_boss gti.var matches 9..24 run bossbar set gti:budget color yellow",
            "execute if score #limit gti.var matches 0 run bossbar set gti:budget visible false",
            "execute if score #limit gti.var matches 1.. run bossbar set gti:budget visible true",
            "execute if score #reveal_mode gti.var matches 2 run bossbar set gti:timer players @a[tag=gti.player]",
            "execute if score #reveal_mode gti.var matches 2 run bossbar set gti:timer visible true",
            "execute if score #reveal_mode gti.var matches 0..1 run bossbar set gti:timer visible false",
            "bossbar set gti:timer max 100",
            "scoreboard players set #timer_bar gti.var 0",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_bar gti.var = #interval gti.var",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_bar gti.var -= #timer gti.var",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_bar gti.var *= #hundred gti.var",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players operation #timer_bar gti.var /= #interval gti.var",
            "execute if score #reveal_mode gti.var matches 2 store result bossbar gti:timer value run scoreboard players get #timer_bar gti.var",
        ]
    )
    return f
