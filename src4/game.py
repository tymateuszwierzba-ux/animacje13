"""Game logic, world build calls, attempts strip, finale and triggers."""

from __future__ import annotations

from art import CATS, art_functions
from model import (
    CELLS,
    COLS,
    ROWS,
    STRIP_MAX,
    mc,
)
from world import build_world, world_text

TRIGGERS = [
    ("gti_next", "gti:start"),
    ("gti_reveal", "gti:reveal/request"),
    ("gti_guess", "gti:guess/request"),
    ("gti_hint", "gti:hint/request"),
    ("gti_menu", "gti:ui/menu"),
    ("gti_host", "gti:ui/host"),
    ("gti_settings", "gti:ui/settings"),
    ("gti_stats", "gti:ui/stats"),
    ("gti_browse", "gti:ui/browse"),
    ("gti_summary", "gti:ui/summary"),
    ("gti_rules", "gti:ui/rules"),
    ("gti_stop", "gti:stop"),
    ("gti_hand", "gti:data/hand"),
    ("gti_random", "gti:data/random_lock"),
    ("gti_pick", "gti:data/pick"),
    ("gti_easy", "gti:preset/chill"),
    ("gti_normal", "gti:preset/normal"),
    ("gti_hard", "gti:preset/hard"),
    ("gti_default", "gti:preset/default"),
]

TONES = [
    ("red_concrete", "red"),
    ("orange_concrete", "orange"),
    ("yellow_concrete", "yellow"),
    ("lime_concrete", "lime"),
]


def _constants() -> list[str]:
    values = {
        "#zero": 0,
        "#one": 1,
        "#two": 2,
        "#three": 3,
        "#eight": 8,
        "#ten": 10,
        "#sixteen": 16,
        "#twenty": 20,
        "#thirty": 30,
        "#thirtytwo": STRIP_MAX,
        "#sixty": 60,
        "#hundred": 100,
        "#tenk": 10000,
        "#maxpix": CELLS,
    }
    return [f"scoreboard players set {name} gti.var {value}" for name, value in values.items()]


def _defaults() -> list[str]:
    return [
        "scoreboard players set #limit gti.var 16",
        "scoreboard players set #batch gti.var 3",
        "scoreboard players set #initial gti.var 4",
        "scoreboard players set #mode gti.var 1",
        "scoreboard players set #hints_on gti.var 1",
        "scoreboard players set #timer_sec gti.var 0",
        "data modify storage gti:cfg settings set value {limit:16,batch:3,initial:4,mode:\"peek\",timer:0,hints:1b}",
        'data modify storage gti:cfg hint set value "NO HINT YET"',
        'data modify storage gti:cfg status set value "PRESS START"',
        'data modify storage gti:cfg answer set value "minecraft:diamond"',
        'data modify storage gti:cfg art_key set value "minecraft_diamond"',
        'data modify storage gti:cfg mode_str set value "peek"',
        'data modify storage gti:cfg cat_names set value ["BLOCKS","EQUIPMENT","FOOD","MOBS","MATERIALS","OTHER"]',
    ]


def _strip_functions() -> dict[str, str]:
    out: dict[str, str] = {}
    hide: list[str] = []
    hide.append(
        'execute if score #limit gti.var matches 1.. run data merge entity '
        '@e[tag=gti.stripbar,limit=1] {block_state:{Name:"minecraft:black_concrete"}}'
    )
    hide.append(
        'execute unless score #limit gti.var matches 1.. run data merge entity '
        '@e[tag=gti.stripbar,limit=1] {block_state:{Name:"minecraft:structure_void"}}'
    )
    hide.append(
        'execute if score #limit gti.var matches 1.. as @e[tag=gti.socket] run '
        'data merge entity @s {block_state:{Name:"minecraft:black_concrete"}}'
    )
    hide.append(
        'execute unless score #limit gti.var matches 1.. as @e[tag=gti.socket] run '
        'data merge entity @s {block_state:{Name:"minecraft:structure_void"}}'
    )
    hide.append(
        'execute if score #limit gti.var matches 1.. run data merge entity '
        '@e[tag=gti.piplabel,limit=1] {text:{"text":"LIMIT","color":"#8FA8C8","bold":true}}'
    )
    hide.append(
        'execute unless score #limit gti.var matches 1.. run data merge entity '
        '@e[tag=gti.piplabel,limit=1] {text:""}'
    )
    for index in range(STRIP_MAX):
        hide.append(
            f"execute if score #limit gti.var matches ..{index} run "
            f"data merge entity @e[tag=gti.pip,scores={{gti.id={index}}},limit=1] "
            f'{{block_state:{{Name:"minecraft:structure_void"}}}}'
        )
    out["strip/hide"] = mc(hide)

    for tone, (block, _name) in enumerate(TONES):
        lines: list[str] = []
        for index in range(STRIP_MAX):
            visible = (
                f"if score #pad gti.var matches ..{index} "
                f"if score #pad_end gti.var matches {index + 1}.. "
            )
            lines.append(
                f"execute {visible}if score #left_end gti.var matches {index + 1}.. run data merge entity "
                f"@e[tag=gti.pip,scores={{gti.id={index}}},limit=1] "
                f'{{block_state:{{Name:"minecraft:{block}"}}}}'
            )
            lines.append(
                f"execute {visible}unless score #left_end gti.var matches {index + 1}.. run data merge entity "
                f"@e[tag=gti.pip,scores={{gti.id={index}}},limit=1] "
                f'{{block_state:{{Name:"minecraft:gray_concrete"}}}}'
            )
        out[f"strip/tone{tone}"] = mc(lines)

    out["strip/refresh"] = mc([
        "scoreboard players operation #left gti.var = #limit gti.var",
        "scoreboard players operation #left gti.var -= #used gti.var",
        "execute if score #left gti.var matches ..0 run scoreboard players set #left gti.var 0",
        "function gti:strip/hide",
        "execute unless score #limit gti.var matches 1.. run return 0",
        "scoreboard players operation #pad gti.var = #thirtytwo gti.var",
        "scoreboard players operation #pad gti.var -= #limit gti.var",
        "scoreboard players operation #pad gti.var /= #two gti.var",
        "scoreboard players operation #pad_end gti.var = #pad gti.var",
        "scoreboard players operation #pad_end gti.var += #limit gti.var",
        "scoreboard players operation #left_end gti.var = #pad gti.var",
        "scoreboard players operation #left_end gti.var += #left gti.var",
        "scoreboard players set #tone gti.var 0",
        "scoreboard players operation #tmp gti.var = #left gti.var",
        "scoreboard players operation #tmp gti.var *= #three gti.var",
        "scoreboard players operation #tmp gti.var /= #limit gti.var",
        "execute if score #tmp gti.var matches 1.. run scoreboard players set #tone gti.var 1",
        "execute if score #tmp gti.var matches 2.. run scoreboard players set #tone gti.var 2",
        "execute if score #tmp gti.var matches 3.. run scoreboard players set #tone gti.var 3",
        "execute if score #tone gti.var matches 0 run function gti:strip/tone0",
        "execute if score #tone gti.var matches 1 run function gti:strip/tone1",
        "execute if score #tone gti.var matches 2 run function gti:strip/tone2",
        "execute if score #tone gti.var matches 3 run function gti:strip/tone3",
    ])
    return out


def game_functions(vd: dict) -> dict[str, str]:
    count = vd["count"]
    f: dict[str, str] = {}
    f.update(art_functions(vd))
    f.update(_strip_functions())

    # ---------------------------------------------------------------- load
    triggers = [f"scoreboard objectives add {name} trigger" for name, _ in TRIGGERS]
    dummies = [
        "scoreboard objectives add gti.var dummy",
        "scoreboard objectives add gti.id dummy",
        "scoreboard objectives add gti.age dummy",
        "scoreboard objectives add gti.wins dummy",
        "scoreboard objectives add gti.best dummy",
        "scoreboard objectives add gti.tries dummy",
        "scoreboard objectives add gti.rounds dummy",
        "scoreboard objectives add gti.streak dummy",
        "scoreboard objectives add gti.best_streak dummy",
    ]
    f["load"] = mc(
        triggers
        + dummies
        + [
            'bossbar add gti:timer {"text":"TIME LEFT","color":"red"}',
            "execute unless score #data_ver gti.var matches 4 run function gti:init",
            "scoreboard players set #data_ver gti.var 4",
            "function gti:init/fast",
            f'tellraw @a [{{"text":"[Guess the Item] ","color":"#45E9E0","bold":true}},'
            f'{{"text":"4.0  •  {vd["label"]}  •  {count} items","color":"gray"}}]',
            'tellraw @a [{"text":"/function gti:setup","color":"#61EDE5","click_event":'
            '{"action":"suggest_command","command":"/function gti:setup"}},'
            '{"text":"   •   ","color":"dark_gray"},'
            '{"text":"/function gti:menu","color":"#F47BC6","click_event":'
            '{"action":"run_command","command":"function gti:menu"}},'
            '{"text":"  (dialogs without OP use /trigger gti_menu)","color":"gray"}]',
        ]
    )

    # ---------------------------------------------------------------- init
    init = _constants() + [
        "execute unless score #v4 gti.var matches 1 run function gti:init/defaults",
        "scoreboard players set #v4 gti.var 1",
        "scoreboard players set #state gti.var 0",
        "scoreboard players set #result gti.var 2",
        "scoreboard players set #round gti.var 0",
        "scoreboard players set #revealed gti.var 0",
        "scoreboard players set #used gti.var 0",
        "scoreboard players set #time gti.var 0",
        "scoreboard players set #clock gti.var 0",
        "scoreboard players set #anim gti.var 0",
        "scoreboard players set #free gti.var 0",
        "scoreboard players set #guesses gti.var 0",
        "scoreboard players set #hint_stage gti.var 0",
        "scoreboard players set #same gti.var 0",
        "scoreboard players set #auto gti.var 0",
        "scoreboard players set #team_best gti.var 2147483000",
        f"execute unless score #data_count gti.var matches {count} run function gti:data/init",
        "function gti:strip/refresh",
        "function gti:hud/refresh",
    ]
    f["init"] = mc(init)
    f["init/defaults"] = mc(_defaults())
    f["init/fast"] = mc(_constants() + ["function gti:strip/refresh", "function gti:hud/refresh"])

    # ---------------------------------------------------------------- tick
    tick: list[str] = [
        "scoreboard players add #clock gti.var 1",
        "execute if score #clock gti.var matches 20.. run scoreboard players set #clock gti.var 0",
    ]
    for objective, function in TRIGGERS:
        tick += [
            f"execute as @a[scores={{{objective}=1..}}] at @s run function {function}",
            f"scoreboard players set @a[scores={{{objective}=1..}}] {objective} 0",
            f"scoreboard players enable @a {objective}",
        ]
    tick += [
        "execute as @e[tag=gti.click] at @s if data entity @s interaction run function gti:click",
        "execute as @e[tag=gti.click] at @s if data entity @s attack run function gti:click/attack",
        "execute as @e[tag=gti.control] at @s if data entity @s interaction run function gti:control",
        "scoreboard players add @e[tag=gti.fx] gti.age 1",
        "kill @e[tag=gti.fx,scores={gti.age=10..}]",
        "execute in minecraft:overworld at @e[tag=gti.anchor,limit=1] run function gti:tick/world",
    ]
    f["tick"] = mc(tick)

    f["tick/world"] = mc([
        "execute if score #state gti.var matches 1 run function gti:intro/tick",
        "execute if score #state gti.var matches 2 run function gti:round/tick",
        "execute if score #state gti.var matches 3 run function gti:finale/tick",
        "execute if score #clock gti.var matches 0 run function gti:hud/refresh",
        "execute if score #clock gti.var matches 0 if score #state gti.var matches 2 run function gti:timer/refresh",
        "execute if score #clock gti.var matches 10 if score #state gti.var matches 0 run function gti:fx/idle",
    ])

    # --------------------------------------------------------------- setup
    f["setup"] = mc([
        'execute unless entity @s[type=player] run return run tellraw @a {"text":"Run setup as a player.","color":"red"}',
        'execute unless dimension minecraft:overworld run return run tellraw @s {"text":"Build the board in the Overworld.","color":"red"}',
        "function gti:remove",
        "execute align xyz positioned ~ ~ ~-30 run function gti:world/build",
        "tp @s ~ ~ ~ facing entity @e[tag=gti.look,limit=1]",
        "tag @a remove gti.host",
        "tag @s add gti.host",
        "tag @s add gti.player",
        "scoreboard players set #state gti.var 0",
        "scoreboard players set #result gti.var 2",
        "scoreboard players set #round gti.var 0",
        "scoreboard players set #used gti.var 0",
        "scoreboard players set #revealed gti.var 0",
        "scoreboard players set #hint_stage gti.var 0",
        'data modify storage gti:cfg status set value "PRESS START"',
        'data modify storage gti:cfg hint set value "NO HINT YET"',
        "function gti:strip/refresh",
        "function gti:hud/refresh",
        "function gti:fx/curtain_open",
        'tellraw @s [{"text":"Board ready. ","color":"#8BE28B"},{"text":"/function gti:start","color":"#61EDE5","click_event":{"action":"run_command","command":"function gti:start"}},{"text":" or open the menu.","color":"gray"}]',
        "dialog show @s gti:menu",
    ])

    f["remove"] = mc([
        "execute in minecraft:overworld run kill @e[tag=gti.entity]",
        "scoreboard players set #state gti.var 0",
        "scoreboard players set #result gti.var 2",
        "scoreboard players set #used gti.var 0",
        "scoreboard players set #revealed gti.var 0",
        "bossbar set gti:timer visible false",
        "tag @a remove gti.player",
        "tag @a remove gti.host",
        "dialog clear @a",
        'tellraw @s {"text":"Board removed.","color":"gray"}',
    ])

    f["view"] = mc([
        "execute unless entity @e[tag=gti.anchor,limit=1] run return run tellraw @s {\"text\":\"Build the board first: /function gti:setup\",\"color\":\"red\"}",
        "execute at @e[tag=gti.anchor,limit=1] run tp @s ~0.5 ~ ~30 180 -17",
    ])

    f["menu"] = mc(["dialog show @s gti:menu"])
    f["dialog"] = mc(["dialog show @s gti:menu"])
    f["help"] = mc(["dialog show @s gti:rules"])
    f["host"] = mc(["dialog show @s gti:host"])
    f["settings"] = mc(["dialog show @s gti:settings"])
    f["stats"] = mc(["dialog show @s gti:stats"])
    f["random"] = mc(["function gti:data/random_lock"])
    f["play"] = mc(["function gti:reveal/request"])
    f["start"] = mc([
        "execute if score #state gti.var matches 2..3 run return run tellraw @s {\"text\":\"A round is already running.\",\"color\":\"yellow\"}",
        "execute unless entity @e[tag=gti.anchor,limit=1] run return run tellraw @s {\"text\":\"Build the board first: /function gti:setup\",\"color\":\"red\"}",
        "function gti:round/reset",
        "scoreboard players set #state gti.var 1",
        "scoreboard players set #anim gti.var 0",
        "scoreboard players add #round gti.var 1",
        "scoreboard players set #guesses gti.var 0",
        "scoreboard players set @a[tag=gti.player] gti.tries 0",
        'data modify storage gti:cfg status set value "SEALING THE BOARD"',
        'data modify storage gti:cfg hint set value "NO HINT YET"',
        "function gti:strip/refresh",
        "function gti:hud/refresh",
        "title @a[tag=gti.player] times 4 40 8",
        'title @a[tag=gti.player] subtitle {"text":"Bedrock shield is closing","color":"gray"}',
        'title @a[tag=gti.player] title {"text":"GET READY","color":"#45E9E0","bold":true}',
        "execute as @a[tag=gti.player] at @s run playsound minecraft:block.stone.place master @s ~ ~ ~ 0.7 0.6",
    ])

    f["next"] = mc(["function gti:start"])
    f["stop"] = mc([
        "execute unless score #state gti.var matches 1..3 run return run tellraw @s {\"text\":\"Nothing is running.\",\"color\":\"gray\"}",
        "function gti:round/abort",
        'tellraw @s {"text":"Round stopped.","color":"gray"}',
    ])

    f["round/reset"] = mc([
        "scoreboard players set #used gti.var 0",
        "scoreboard players set #revealed gti.var 0",
        "scoreboard players set #time gti.var 0",
        "scoreboard players set #auto gti.var 0",
        "scoreboard players set #hint_stage gti.var 0",
        "scoreboard players set #same gti.var 0",
        "scoreboard players set #free gti.var 0",
        "scoreboard players set #result gti.var 2",
        "data modify storage gti:cfg hint set value \"NO HINT YET\"",
        "execute as @e[tag=gti.cell] run tag @s remove gti.open",
        "function gti:strip/refresh",
    ])

    f["round/abort"] = mc([
        "scoreboard players set #state gti.var 0",
        "scoreboard players set #result gti.var 2",
        "function gti:round/reset",
        "function gti:fx/curtain_open",
        "function gti:fx/restore",
        'data modify storage gti:cfg status set value "STOPPED"',
        "function gti:hud/refresh",
        "bossbar set gti:timer visible false",
    ])

    # -------------------------------------------------------------- intro
    f["intro/tick"] = mc([
        "scoreboard players add #anim gti.var 1",
        "execute if score #anim gti.var matches 1 run function gti:intro/seal",
        "execute if score #anim gti.var matches 10 run function gti:fx/restore",
        "execute if score #anim gti.var matches 18 run function gti:intro/pick",
        "execute if score #anim gti.var matches 26 run function gti:intro/open",
        "execute if score #anim gti.var matches 54 run function gti:intro/go",
    ])
    f["intro/seal"] = mc(
        [
            f"execute as @e[tag=gti.shutter,tag=gti.col{col}] run data merge entity @s "
            f"{{start_interpolation:{col},interpolation_duration:8,transformation:"
            f"{{scale:[1f,16f,0.3f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}}}"
            for col in range(COLS)
        ]
        + [
            "execute at @e[tag=gti.anchor,limit=1] run playsound minecraft:block.deepslate_bricks.place master @a[tag=gti.player] ~ ~ ~ 0.8 0.7",
            'data modify storage gti:cfg status set value "BEDROCK SEALED"',
            "function gti:hud/refresh",
        ]
    )
    f["intro/pick"] = mc([
        "execute if score #source gti.var matches 1 run function gti:data/use_fixed",
        "execute unless score #source gti.var matches 1 run function gti:data/random_answer",
        'data modify storage gti:cfg status set value "ANSWER LOCKED"',
        "function gti:hud/refresh",
    ])
    f["intro/open"] = mc(
        [
            f"execute as @e[tag=gti.shutter,tag=gti.col{col}] run data merge entity @s "
            f"{{start_interpolation:{abs(col - 8) + 2},interpolation_duration:10,transformation:"
            f"{{scale:[1f,16f,0.3f],translation:[0f,18.2f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}}}"
            for col in range(COLS)
        ]
        + [
            "execute at @e[tag=gti.anchor,limit=1] run playsound minecraft:block.deepslate_bricks.break master @a[tag=gti.player] ~ ~ ~ 0.8 1.2",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:block minecraft:bedrock ~ ~10.5 ~1.2 9 9 0.2 0.05 200 force @a[tag=gti.player]",
        ]
    )
    f["intro/go"] = mc([
        "scoreboard players set #state gti.var 2",
        "scoreboard players set #time gti.var 0",
        "scoreboard players set #auto gti.var 0",
        'data modify storage gti:cfg status set value "GO"',
        "scoreboard players set #free gti.var 1",
        "execute if score #initial gti.var matches 1.. run function gti:reveal/initial",
        "scoreboard players set #free gti.var 0",
        "function gti:strip/refresh",
        "function gti:hud/refresh",
        "function gti:timer/begin",
        'title @a[tag=gti.player] times 3 30 8',
        'title @a[tag=gti.player] subtitle {"text":"Click cells to crack the bedrock","color":"gray"}',
        'title @a[tag=gti.player] title {"text":"GUESS IT!","color":"#8BE28B","bold":true}',
        "execute as @a[tag=gti.player] at @s run playsound minecraft:entity.experience_orb.pickup master @s ~ ~ ~ 0.7 1.5",
    ])

    f["reveal/initial"] = mc([
        "execute store result storage gti:tmp batch int 1 run scoreboard players get #initial gti.var",
        "execute at @e[tag=gti.anchor,limit=1] run function gti:reveal/batch with storage gti:tmp",
    ])

    # ------------------------------------------------------------- reveal
    f["reveal/request"] = mc([
        'execute unless score #state gti.var matches 2 run return run tellraw @s {"text":"No round is running. Open the menu: /trigger gti_menu","color":"gray"}',
        "execute unless entity @e[tag=gti.cell,tag=!gti.open,limit=1] run return run tellraw @s {\"text\":\"Every cell is revealed - hold the item and guess!\",\"color\":\"yellow\"}",
        "tag @s add gti.player",
        "execute store result storage gti:tmp batch int 1 run scoreboard players get #batch gti.var",
        "execute at @e[tag=gti.anchor,limit=1] run function gti:reveal/batch with storage gti:tmp",
        "function gti:hud/refresh",
    ])
    f["reveal/batch"] = mc([
        "$execute as @e[tag=gti.cell,tag=!gti.open,sort=random,limit=$(batch)] at @s run function gti:reveal/cell",
        "execute at @e[tag=gti.anchor,limit=1] run playsound minecraft:block.amethyst_block.chime master @a[tag=gti.player] ~ ~ ~ 0.45 1.4",
        "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:block minecraft:bedrock ~ ~10.5 ~1 9 9 0.1 0.05 40 force @a[tag=gti.player]",
    ])
    f["reveal/cell"] = mc([
        "execute unless score #state gti.var matches 2 run return 0",
        "tag @s add gti.open",
        "scoreboard players add #revealed gti.var 1",
        "execute if score #free gti.var matches 0 run scoreboard players add #used gti.var 1",
        "data modify storage gti:tmp id set value 0",
        "execute store result storage gti:tmp id int 1 run scoreboard players get @s gti.id",
        "data modify storage gti:tmp key set from storage gti:cfg art_key",
        "function gti:art/place with storage gti:tmp",
        "execute if score #free gti.var matches 0 run function gti:strip/refresh",
        "execute if score #free gti.var matches 0 if score #limit gti.var matches 1.. if score #left gti.var matches ..0 run function gti:round/lose",
        "execute if score #revealed gti.var matches 256 run function gti:round/complete",
    ])
    f["reveal/final"] = mc([
        "execute if entity @s[tag=gti.open] run return 0",
        "tag @s add gti.open",
        "data modify storage gti:tmp id set value 0",
        "execute store result storage gti:tmp id int 1 run scoreboard players get @s gti.id",
        "data modify storage gti:tmp key set from storage gti:cfg art_key",
        "function gti:art/place with storage gti:tmp",
        "execute at @s run particle minecraft:block minecraft:bedrock ~ ~ ~ 0.35 0.35 0.2 0.02 5 force @a[tag=gti.player]",
    ])
    f["round/complete"] = mc([
        'data modify storage gti:cfg status set value "ALL CELLS REVEALED - GUESS NOW"',
        "function gti:hud/refresh",
        'title @a[tag=gti.player] actionbar [{"text":"ALL CELLS REVEALED","color":"#8BE28B","bold":true},{"text":"  hold the item and press GUESS","color":"gray"}]',
    ])

    # ---------------------------------------------------------------- art
    f["art/place"] = mc([
        "$execute store result storage gti:tmp n int 1 run data get storage gti:art $(key)[$(id)]",
        "function gti:art/lookup with storage gti:tmp",
        '$data merge entity @e[tag=gti.cell,scores={gti.id=$(id)},limit=1] {block_state:{Name:"$(block)"}}',
        '$execute as @e[tag=gti.cell,scores={gti.id=$(id)},limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{scale:[0.9f,0.9f,0.9f],translation:[0f,0f,0.14f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}',
        '$execute at @e[tag=gti.cell,scores={gti.id=$(id)},limit=1] run summon block_display ~ ~ ~ {Tags:["gti.entity","gti.fx","gti.flash"],block_state:{Name:"minecraft:white_concrete"},brightness:{sky:15,block:15},view_range:4f,transformation:{scale:[1.3f,1.3f,0.2f],translation:[0f,0f,0.2f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}',
        '$execute at @e[tag=gti.cell,scores={gti.id=$(id)},limit=1] run data merge entity @e[tag=gti.flash,sort=nearest,limit=1] {start_interpolation:0,interpolation_duration:6,transformation:{scale:[0.02f,0.02f,0.02f],translation:[0f,0f,0.2f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}',
    ])
    f["art/lookup"] = mc([
        '$data modify storage gti:tmp block set from storage gti:art palette[$(n)]',
    ])

    # --------------------------------------------------------------- data
    f["data/random_index"] = mc([
        f"execute store result score #random gti.var run random value 0..{count - 1}",
        "scoreboard players operation #random gti.var %= #data_count gti.var",
        "execute store result storage gti:tmp index int 1 run scoreboard players get #random gti.var",
    ])
    f["data/pick_rand"] = mc([
        "$data modify storage gti:ctx id set from storage gti:items ids[$(index)]",
    ])
    f["data/random_answer"] = mc([
        "function gti:data/random_index",
        "function gti:data/pick_rand with storage gti:tmp",
        "data modify storage gti:cfg answer set from storage gti:ctx id",
        "function gti:data/lookup with storage gti:ctx",
        "scoreboard players set #source gti.var 0",
    ])
    f["data/use_fixed"] = mc([
        "data modify storage gti:ctx id set from storage gti:cfg answer",
        "function gti:data/lookup with storage gti:ctx",
    ])
    f["data/lookup"] = mc([
        '$data modify storage gti:cfg meta set from storage gti:items by_id."$(id)"',
        "data modify storage gti:cfg art_key set from storage gti:cfg meta.ak",
        "data modify storage gti:cfg answer_key set from storage gti:cfg meta.key",
        "execute store result score #eq_answer gti.var run data get storage gti:cfg meta.eq",
        "execute store result score #hint_cat gti.var run data get storage gti:cfg meta.cat",
    ])
    f["data/set_fixed"] = mc([
        '$execute store success score #found gti.var run data get storage gti:items by_id."$(id)"',
        '$execute if score #found gti.var matches 0 run return run tellraw @s [{"text":"Unknown item id: ","color":"red"},{"text":"$(id)","color":"#FF8996"}]',
        'execute if score #state gti.var matches 1..3 run return run tellraw @s {"text":"Finish the running round first.","color":"yellow"}',
        '$data modify storage gti:cfg answer set value "$(id)"',
        "scoreboard players set #source gti.var 1",
        "function gti:data/use_fixed",
        "function gti:round/reset",
        'data modify storage gti:cfg status set value "ANSWER LOCKED"',
        "function gti:hud/refresh",
        '$tellraw @s [{"text":"Answer locked: ","color":"gray"},{"text":"$(id)","color":"#61EDE5"}]',
        "dialog show @s gti:host",
    ])
    f["data/set_id"] = mc([
        '$data modify storage gti:tmp id set value "$(id)"',
        '$execute unless data storage gti:items by_id."$(id)" run data modify storage gti:tmp id set value "minecraft:$(id)"',
        "function gti:data/set_fixed with storage gti:tmp",
    ])
    f["data/hand"] = mc([
        "execute unless items entity @s weapon.mainhand #gti:answers run return run tellraw @s {\"text\":\"Hold an item from the catalogue in your main hand.\",\"color\":\"yellow\"}",
        "data modify storage gti:tmp id set from entity @s SelectedItem.id",
        "function gti:data/set_fixed with storage gti:tmp",
    ])
    f["data/random_lock"] = mc([
        "function gti:data/random_index",
        "function gti:data/pick_rand with storage gti:tmp",
        "data modify storage gti:tmp id set from storage gti:ctx id",
        "function gti:data/set_fixed with storage gti:tmp",
    ])
    f["data/pick"] = mc([
        "scoreboard players operation #pick gti.var = @s gti_pick",
        "scoreboard players remove #pick gti.var 1",
        "scoreboard players operation #cat gti.var = #pick gti.var",
        "scoreboard players operation #cat gti.var /= #tenk gti.var",
        "scoreboard players operation #idx gti.var = #pick gti.var",
        "scoreboard players operation #idx gti.var %= #tenk gti.var",
        "execute store result storage gti:tmp index int 1 run scoreboard players get #idx gti.var",
        'data modify storage gti:tmp cat set value "all"',
        "execute if score #cat gti.var matches 1 run data modify storage gti:tmp cat set value \"blocks\"",
        "execute if score #cat gti.var matches 2 run data modify storage gti:tmp cat set value \"equipment\"",
        "execute if score #cat gti.var matches 3 run data modify storage gti:tmp cat set value \"food\"",
        "execute if score #cat gti.var matches 4 run data modify storage gti:tmp cat set value \"mobs\"",
        "execute if score #cat gti.var matches 5 run data modify storage gti:tmp cat set value \"materials\"",
        "execute if score #cat gti.var matches 6 run data modify storage gti:tmp cat set value \"other\"",
        "function gti:data/pick_cat with storage gti:tmp",
        "function gti:data/set_fixed with storage gti:tmp",
    ])
    f["data/pick_cat"] = mc([
        '$data modify storage gti:tmp id set from storage gti:cat $(cat)[$(index)]',
    ])

    # --------------------------------------------------------------- guess
    f["guess/request"] = mc([
        'execute unless score #state gti.var matches 2 run return run tellraw @s {"text":"No round is running.","color":"gray"}',
        'execute unless items entity @s weapon.mainhand #gti:answers run return run tellraw @s {"text":"Hold the item you want to guess in your main hand.","color":"yellow"}',
        "tag @s add gti.player",
        "scoreboard players add @s gti.tries 1",
        "scoreboard players add #guesses gti.var 1",
        "data modify storage gti:ctx answer set from storage gti:cfg answer",
        "data modify storage gti:ctx guess set from entity @s SelectedItem.id",
        "scoreboard players set #same gti.var 0",
        "function gti:guess/check with storage gti:ctx",
        "execute if score #same gti.var matches 0 run function gti:guess/equiv with storage gti:ctx",
        "execute if score #same gti.var matches 1 run function gti:guess/win",
        "execute if score #same gti.var matches 0 run function gti:guess/wrong",
    ])
    f["guess/check"] = mc([
        '$execute if data storage gti:ctx {answer:"$(guess)"} run scoreboard players set #same gti.var 1',
    ])
    f["guess/equiv"] = mc([
        "$execute store result score #eq_guess gti.var run data get storage gti:items by_id.\"$(guess)\".eq",
        "execute if score #eq_answer gti.var matches 1.. if score #eq_guess gti.var = #eq_answer gti.var run scoreboard players set #same gti.var 1",
    ])
    f["guess/win"] = mc([
        "execute unless score #state gti.var matches 2 run return 0",
        "scoreboard players add @s gti.wins 1",
        "scoreboard players add @s gti.rounds 1",
        "scoreboard players add @s gti.streak 1",
        "execute if score @s gti.streak > @s gti.best_streak run scoreboard players operation @s gti.best_streak = @s gti.streak",
        "scoreboard players operation #best_now gti.var = #used gti.var",
        "scoreboard players add #best_now gti.var 1",
        "scoreboard players set #new_best gti.var 0",
        "execute unless score @s gti.best matches 1.. run scoreboard players set #new_best gti.var 1",
        "execute if score #new_best gti.var matches 0 if score #best_now gti.var < @s gti.best run scoreboard players set #new_best gti.var 1",
        "execute if score #new_best gti.var matches 1 run scoreboard players operation @s gti.best = #best_now gti.var",
        "execute if score #new_best gti.var matches 1 run tellraw @s {\"text\":\"★ NEW PERSONAL BEST ★\",\"color\":\"gold\",\"bold\":true}",
        "scoreboard players set #result gti.var 1",
        "scoreboard players set #state gti.var 3",
        "scoreboard players set #anim gti.var 0",
        "scoreboard players set #shown gti.var 0",
        "function gti:strip/refresh",
        "function gti:hud/refresh",
        "function gti:finale/win",
        "function gti:timer/hide",
    ])
    f["guess/wrong"] = mc([
        "execute unless score #state gti.var matches 2 run return 0",
        "scoreboard players add #wrong gti.var 1",
        "scoreboard players set @s gti.streak 0",
        "scoreboard players add #used gti.var 3",
        'title @s times 2 24 8',
        'title @s subtitle {"text":"-3 attempts • try again","color":"gray"}',
        'title @s title {"text":"NOT THIS ITEM","color":"#FF8996","bold":true}',
        "execute at @s run playsound minecraft:block.note_block.bass master @s ~ ~ ~ 0.8 0.55",
        "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:smoke ~ ~10.5 ~1.2 8 8 0.2 0.02 40 force @a[tag=gti.player]",
        "function gti:strip/refresh",
        "function gti:hud/refresh",
        "execute if score #mode gti.var matches 1 run function gti:reveal/peek",
        "execute if score #limit gti.var matches 1.. if score #left gti.var matches ..0 run function gti:round/lose",
    ])
    f["reveal/peek"] = mc([
        "scoreboard players set #free gti.var 1",
        "execute store result storage gti:tmp batch int 1 run scoreboard players get #two gti.var",
        "execute at @e[tag=gti.anchor,limit=1] run function gti:reveal/batch with storage gti:tmp",
        "scoreboard players set #free gti.var 0",
        "function gti:strip/refresh",
    ])

    # -------------------------------------------------------------- hints
    f["hint/request"] = mc([
        'execute unless score #state gti.var matches 2 run return run tellraw @s {"text":"No round is running.","color":"gray"}',
        'execute if score #hints_on gti.var matches 0 run return run tellraw @s {"text":"Hints are disabled in the settings.","color":"yellow"}',
        'execute if score #hint_stage gti.var matches 3 run return run tellraw @s {"text":"All three hints are already used.","color":"yellow"}',
        "scoreboard players add #hint_stage gti.var 1",
        "scoreboard players add #used gti.var 2",
        "execute if score #hint_stage gti.var matches 1 run function gti:hint/cat",
        "execute if score #hint_stage gti.var matches 2 run function gti:hint/len",
        "execute if score #hint_stage gti.var matches 3 run function gti:hint/mask",
        "function gti:strip/refresh",
        "function gti:hud/refresh",
        "execute at @e[tag=gti.anchor,limit=1] run playsound minecraft:block.amethyst_block.resonate master @a[tag=gti.player] ~ ~ ~ 0.6 1.6",
        "execute if score #limit gti.var matches 1.. if score #left gti.var matches ..0 run function gti:round/lose",
    ])
    f["hint/cat"] = mc([
        "execute store result storage gti:ui cat int 1 run scoreboard players get #hint_cat gti.var",
        "function gti:hint/fmt_cat with storage gti:ui",
    ])
    f["hint/fmt_cat"] = mc([
        "$data modify storage gti:ui cat_name set from storage gti:cfg cat_names[$(cat)]",
        "function gti:hint/fmt_cat2 with storage gti:ui",
    ])
    f["hint/fmt_cat2"] = mc([
        "$data modify storage gti:cfg hint set value \"CATEGORY  ·  $(cat_name)\"",
    ])
    f["hint/len"] = mc([
        "data modify storage gti:ui len set from storage gti:cfg meta.len",
        "data modify storage gti:ui first set from storage gti:cfg meta.first",
        "function gti:hint/fmt_len with storage gti:ui",
    ])
    f["hint/fmt_len"] = mc([
        '$data modify storage gti:cfg hint set value "LENGTH $(len)  •  FIRST LETTER $(first)"',
    ])
    f["hint/mask"] = mc([
        "data modify storage gti:ui mask set from storage gti:cfg meta.mask",
        "function gti:hint/fmt_mask with storage gti:ui",
    ])
    f["hint/fmt_mask"] = mc([
        '$data modify storage gti:cfg hint set value "PATTERN $(mask)"',
    ])

    # -------------------------------------------------------------- round
    f["round/tick"] = mc([
        "scoreboard players add #time gti.var 1",
        "scoreboard players add #auto gti.var 1",
        "execute if score #timer_sec gti.var matches 1.. if score #time gti.var >= #timer_end gti.var run function gti:round/lose",
        "execute if score #mode gti.var matches 2 if score #auto gti.var matches 140.. run function gti:round/auto",
    ])
    f["round/auto"] = mc([
        "scoreboard players set #auto gti.var 0",
        "execute store result storage gti:tmp batch int 1 run scoreboard players get #batch gti.var",
        "execute at @e[tag=gti.anchor,limit=1] run function gti:reveal/batch with storage gti:tmp",
        "function gti:hud/refresh",
    ])
    f["round/lose"] = mc([
        "execute unless score #state gti.var matches 2 run return 0",
        "scoreboard players set #result gti.var 0",
        "scoreboard players set #state gti.var 3",
        "scoreboard players set #anim gti.var 0",
        "scoreboard players set #shown gti.var 0",
        "scoreboard players set @a[tag=gti.player] gti.streak 0",
        "scoreboard players add @a[tag=gti.player] gti.rounds 1",
        'title @a[tag=gti.player] times 4 60 12',
        'title @a[tag=gti.player] subtitle {"text":"The bedrock hides nothing anymore","color":"gray"}',
        'title @a[tag=gti.player] title {"text":"OUT OF ATTEMPTS","color":"#FF8996","bold":true}',
        "execute as @a[tag=gti.player] at @s run playsound minecraft:block.beacon.deactivate master @s ~ ~ ~ 0.7 0.7",
        "function gti:strip/refresh",
        "function gti:hud/refresh",
        "function gti:finale/lose",
        "function gti:timer/hide",
    ])

    # ------------------------------------------------------------ timers
    f["timer/begin"] = mc([
        "scoreboard players operation #timer_end gti.var = #timer_sec gti.var",
        "scoreboard players operation #timer_end gti.var *= #twenty gti.var",
        "execute if score #timer_sec gti.var matches 1.. run bossbar set gti:timer visible true",
        "execute if score #timer_sec gti.var matches 1.. run bossbar set gti:timer players @a[tag=gti.player]",
        "execute if score #timer_sec gti.var matches 0 run function gti:timer/hide",
    ])
    f["timer/hide"] = mc([
        "bossbar set gti:timer visible false",
    ])
    f["timer/refresh"] = mc([
        "execute unless score #timer_sec gti.var matches 1.. run bossbar set gti:timer visible false",
        "execute if score #timer_sec gti.var matches 1.. run bossbar set gti:timer max 100",
        "execute if score #timer_sec gti.var matches 1.. store result bossbar gti:timer value run function gti:timer/value",
    ])
    f["timer/value"] = mc([
        "scoreboard players operation #timer_left gti.var = #timer_end gti.var",
        "scoreboard players operation #timer_left gti.var -= #time gti.var",
        "scoreboard players operation #timer_left gti.var *= #hundred gti.var",
        "scoreboard players operation #timer_left gti.var /= #timer_end gti.var",
        "execute if score #timer_left gti.var matches ..-1 run scoreboard players set #timer_left gti.var 0",
        "return run scoreboard players get #timer_left gti.var",
    ])

    # --------------------------------------------------------------- HUD
    f["hud/refresh"] = mc([
        "execute store result storage gti:ui round int 1 run scoreboard players get #round gti.var",
        "execute store result storage gti:ui used int 1 run scoreboard players get #used gti.var",
        "execute store result storage gti:ui found int 1 run scoreboard players get #revealed gti.var",
        "execute if score #limit gti.var matches 1.. run scoreboard players operation #left gti.var = #limit gti.var",
        "execute if score #limit gti.var matches 1.. run scoreboard players operation #left gti.var -= #used gti.var",
        "execute if score #limit gti.var matches 1.. if score #left gti.var matches ..0 run scoreboard players set #left gti.var 0",
        "execute if score #limit gti.var matches 0 run data modify storage gti:ui left set value \"∞\"",
        "execute if score #limit gti.var matches 1.. store result storage gti:ui left int 1 run scoreboard players get #left gti.var",
        "scoreboard players operation #sec gti.var = #time gti.var",
        "scoreboard players operation #sec gti.var /= #twenty gti.var",
        "scoreboard players operation #mm gti.var = #sec gti.var",
        "scoreboard players operation #mm gti.var /= #sixty gti.var",
        "scoreboard players operation #ss gti.var = #sec gti.var",
        "scoreboard players operation #ss gti.var %= #sixty gti.var",
        'data modify storage gti:ui mm0 set value ""',
        'data modify storage gti:ui ss0 set value ""',
        "execute if score #mm gti.var matches ..9 run data modify storage gti:ui mm0 set value \"0\"",
        "execute if score #ss gti.var matches ..9 run data modify storage gti:ui ss0 set value \"0\"",
        "execute store result storage gti:ui mm int 1 run scoreboard players get #mm gti.var",
        "execute store result storage gti:ui ss int 1 run scoreboard players get #ss gti.var",
        "data modify storage gti:ui hint set from storage gti:cfg hint",
        "data modify storage gti:ui status set from storage gti:cfg status",
        "function gti:hud/apply with storage gti:ui",
    ])
    f["hud/apply"] = mc([
        '$data modify entity @e[tag=gti.hud.round,limit=1] text set value [{"text":"$(round)","color":"#F6CF84","bold":true}]',
        '$data modify entity @e[tag=gti.hud.used,limit=1] text set value [{"text":"$(used)","color":"#FF8996","bold":true}]',
        '$data modify entity @e[tag=gti.hud.left,limit=1] text set value [{"text":"$(left)","color":"#8BE28B","bold":true}]',
        '$data modify entity @e[tag=gti.hud.found,limit=1] text set value [{"text":"$(found)","color":"#45E9E0","bold":true},{"text":" / 256","color":"#5F7899"}]',
        '$data modify entity @e[tag=gti.hud.time,limit=1] text set value [{"text":"$(mm0)$(mm):$(ss0)$(ss)","color":"#79C4F8","bold":true}]',
        '$data modify entity @e[tag=gti.hud.hint,limit=1] text set value [{"text":"$(hint)","color":"#F6CF84","bold":true}]',
        '$data modify entity @e[tag=gti.hud.status,limit=1] text set value [{"text":"$(status)","color":"#8BE28B","bold":true}]',
    ])

    # -------------------------------------------------------------- FINALE
    f["finale/win"] = mc([
        "function gti:fx/confetti",
        "execute as @a[tag=gti.player] at @s run playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 0.8 1.05",
        "execute as @a[tag=gti.player] at @s run playsound minecraft:entity.firework_rocket.twinkle master @s ~ ~ ~ 0.8 1.1",
        'data modify storage gti:cfg status set value "SOLVED"',
    ])
    f["finale/lose"] = mc([
        "execute as @a[tag=gti.player] at @s run playsound minecraft:entity.villager.no master @s ~ ~ ~ 0.6 0.8",
        'data modify storage gti:cfg status set value "ANSWER REVEALED"',
    ])
    f["finale/tick"] = mc(
        [
            "scoreboard players add #anim gti.var 1",
        ]
        + [
            f"execute if score #anim gti.var matches {2 + 2 * col} as @e[tag=gti.cell,tag=gti.col{col}] run function gti:reveal/final"
            for col in range(COLS)
        ]
        + [
            "execute if score #anim gti.var matches 40 run function gti:fx/confetti",
            "execute if score #anim gti.var matches 46 if score #result gti.var matches 1 run function gti:fx/fireworks",
            "execute if score #anim gti.var matches 64 if score #result gti.var matches 1 run function gti:finale/summary",
            "execute if score #anim gti.var matches 64 if score #result gti.var matches 0 run function gti:finale/summary",
            "execute if score #anim gti.var matches 120 run function gti:finale/end",
            "execute if score #anim gti.var matches 128 run function gti:finale/end2",
            "execute if score #anim gti.var matches 138 run function gti:finale/end3",
        ]
    )
    f["finale/curtain"] = mc(
        [
            f"execute as @e[tag=gti.shutter,tag=gti.col{col}] run data merge entity @s "
            f"{{start_interpolation:{abs(col - 8)},interpolation_duration:8,transformation:"
            f"{{scale:[1f,16f,0.3f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}}}"
            for col in range(COLS)
        ]
    )
    f["finale/answer"] = mc([
        "data modify storage gti:tmp key set from storage gti:cfg answer_key",
        "function gti:fx/show_answer with storage gti:tmp",
    ])
    f["fx/show_answer"] = mc([
        '$data modify entity @e[tag=gti.hud.hint,limit=1] text set value [{"text":"ANSWER  ","color":"#8FA8C8","bold":true},{"translate":"$(key)","color":"#F6CF84","bold":true}]',
    ])
    f["finale/summary"] = mc([
        "execute if score #shown gti.var matches 1 run return 0",
        "scoreboard players set #shown gti.var 1",
        "function gti:finale/answer",
        "execute as @a[tag=gti.host] run dialog show @s gti:summary",
        'tellraw @a[tag=gti.player] [{"text":"Round over ","color":"#8FA8C8"},{"text":"• ","color":"dark_gray"},{"text":"attempts used: ","color":"gray"},{"score":{"name":"#used","objective":"gti.var"},"color":"#FF8996"},{"text":"  •  guesses: ","color":"gray"},{"score":{"name":"#guesses","objective":"gti.var"},"color":"#F6CF84"}]',
    ])
    f["finale/end"] = mc([
        "function gti:finale/curtain",
        "execute as @a[tag=gti.player] at @s run playsound minecraft:block.deepslate_bricks.place master @s ~ ~ ~ 0.7 0.8",
    ])
    f["finale/end2"] = mc([
        "function gti:fx/restore",
        'data modify storage gti:cfg status set value "PRESS START"',
        "function gti:hud/refresh",
    ])
    f["finale/end3"] = mc([
        "scoreboard players set #state gti.var 0",
        "function gti:round/reset",
        "function gti:fx/curtain_open",
        "function gti:strip/refresh",
        "function gti:hud/refresh",
    ])

    # ----------------------------------------------------------------- FX
    f["fx/idle"] = mc([
        "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:end_rod ~ ~10.5 ~1.4 9 9 0.1 0.02 12 force @a[tag=gti.player]",
        "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:glow ~ ~10.5 ~1.6 9 9 0.1 0.01 6 force @a[tag=gti.player]",
    ])
    f["fx/confetti"] = mc([
        "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:totem_of_undying ~ ~10 ~1.6 8 8 0.5 0.4 60 force @a[tag=gti.player]",
        "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:firework ~ ~10 ~1.6 9 9 0.5 0.15 30 force @a[tag=gti.player]",
    ])
    f["fx/fireworks"] = mc(
        [
            f"execute at @e[tag=gti.anchor,limit=1] run summon firework_rocket ~{x} ~12 ~2 "
            f'{{LifeTime:20,FireworksItem:{{id:"minecraft:firework_rocket",count:1,components:{{"minecraft:fireworks":{{flight_duration:1,explosions:[{{shape:"star",colors:[I;{c1}],fade_colors:[I;{c2}],has_trail:1b,has_twinkle:1b}}]}}}}}}}}'
            for x, c1, c2 in (
                (-8, 2077344, 4512159),
                (0, 14826495, 6488063),
                (8, 4843599, 16711935),
            )
        ]
    )
    f["fx/restore"] = mc([
        "execute as @e[tag=gti.cell] run tag @s remove gti.open",
        'execute as @e[tag=gti.cell] run data merge entity @s {block_state:{Name:"minecraft:bedrock"},start_interpolation:0,interpolation_duration:0,transformation:{scale:[1f,1f,1f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}',
        "kill @e[tag=gti.fx]",
    ])
    f["fx/curtain_open"] = mc(
        [
            f"execute as @e[tag=gti.shutter,tag=gti.col{col}] run data merge entity @s "
            f"{{start_interpolation:0,interpolation_duration:0,transformation:"
            f"{{scale:[1f,16f,0.3f],translation:[0f,18.2f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}}}"
            for col in range(COLS)
        ]
    )

    f["control"] = mc([
        "execute if entity @s[tag=gti.control.reveal] on target run function gti:reveal/request",
        "execute if entity @s[tag=gti.control.guess] on target run function gti:guess/request",
        "execute if entity @s[tag=gti.control.hint] on target run function gti:hint/request",
        "execute if entity @s[tag=gti.control.menu] on target run function gti:ui/menu",
        "execute if entity @s[tag=gti.control.menu] on target run playsound minecraft:ui.button.click master @s ~ ~ ~ 0.6 1.2",
        "data remove entity @s interaction",
        "data remove entity @s attack",
    ])
    f["click"] = mc([
        "execute unless score #state gti.var matches 2 run return run data remove entity @s interaction",
        "execute on target run tag @s add gti.player",
        "execute on target run scoreboard players add @s gti.tries 1",
        "execute store result storage gti:tmp batch int 1 run scoreboard players get #batch gti.var",
        "execute at @s run function gti:reveal/batch with storage gti:tmp",
        "data remove entity @s interaction",
        "function gti:hud/refresh",
    ])
    f["click/attack"] = mc([
        "execute unless score #state gti.var matches 2 run return run data remove entity @s attack",
        "execute on attacker run tag @s add gti.player",
        "execute on attacker run scoreboard players add @s gti.tries 1",
        "execute store result storage gti:tmp batch int 1 run scoreboard players get #batch gti.var",
        "execute at @s run function gti:reveal/batch with storage gti:tmp",
        "data remove entity @s attack",
        "function gti:hud/refresh",
    ])

    # settings are written by the dialog macro
    f["cfg/store"] = mc([
        '$data modify storage gti:cfg mode_str set value "$(mode)"',
        "$scoreboard players set #limit gti.var $(limit)",
        "$scoreboard players set #batch gti.var $(batch)",
        "$scoreboard players set #initial gti.var $(initial)",
        "$scoreboard players set #timer_sec gti.var $(timer)",
        "$scoreboard players set #hints_on gti.var $(hints)",
        "scoreboard players set #mode gti.var 0",
        'execute if data storage gti:cfg {mode_str:"peek"} run scoreboard players set #mode gti.var 1',
        'execute if data storage gti:cfg {mode_str:"auto"} run scoreboard players set #mode gti.var 2',
        "$data modify storage gti:cfg settings.limit set value $(limit)",
        "$data modify storage gti:cfg settings.batch set value $(batch)",
        "$data modify storage gti:cfg settings.initial set value $(initial)",
        "$data modify storage gti:cfg settings.timer set value $(timer)",
        "$data modify storage gti:cfg settings.hints set value $(hints)",
        "$data modify storage gti:cfg settings.mode set value \"$(mode)\"",
        "function gti:strip/refresh",
        "function gti:hud/refresh",
    ])
    f["cfg/apply"] = mc([
        '$data modify storage gti:tmp limit set value $(limit)',
        '$data modify storage gti:tmp batch set value $(batch)',
        '$data modify storage gti:tmp initial set value $(initial)',
        '$data modify storage gti:tmp timer set value $(timer)',
        '$data modify storage gti:tmp hints set value $(hints)',
        '$data modify storage gti:tmp mode set value "$(mode)"',
        "function gti:cfg/store with storage gti:tmp",
        '$tellraw @s [{"text":"Settings saved. ","color":"#8BE28B"},{"text":"max attempts: ","color":"gray"},{"text":"$(limit)","color":"#F6CF84"},{"text":"  cells/click: ","color":"gray"},{"text":"$(batch)","color":"#61EDE5"},{"text":"  mode: ","color":"gray"},{"text":"$(mode)","color":"#B295FF"}]',
        "dialog show @s gti:settings",
    ])
    for name, values in {
        "chill": (0, 4, 8, "manual", 0, 1),
        "normal": (16, 3, 4, "peek", 0, 1),
        "hard": (8, 1, 0, "manual", 0, 0),
    }.items():
        limit, batch, initial, mode, timer, hints = values
        f[f"preset/{name}"] = mc([
            f"data modify storage gti:tmp limit set value {limit}",
            f"data modify storage gti:tmp batch set value {batch}",
            f"data modify storage gti:tmp initial set value {initial}",
            f"data modify storage gti:tmp timer set value {timer}",
            f"data modify storage gti:tmp hints set value {hints}",
            f'data modify storage gti:tmp mode set value "{mode}"',
            "function gti:cfg/store with storage gti:tmp",
            f'tellraw @s {{"text":"Preset {name.upper()} applied.","color":"#8BE28B"}}',
            "dialog show @s gti:settings",
        ])
    f["preset/default"] = mc([
        "function gti:init/defaults",
        "function gti:strip/refresh",
        "function gti:hud/refresh",
        'tellraw @s {"text":"Defaults restored.","color":"#8BE28B"}',
    ])

    # ------------------------------------------------------------ world
    world = build_world(vd) + world_text(vd)
    out_world: list[str] = ["summon marker ~ ~ ~ {Tags:[\"gti.entity\",\"gti.anchor\"]}"]
    out_world.append("summon marker ~ ~10.5 ~ {Tags:[\"gti.entity\",\"gti.look\"]}")
    out_world += world
    chunks = [out_world[i : i + 260] for i in range(0, len(out_world), 260)]
    for index, chunk in enumerate(chunks):
        f[f"world/{index}"] = mc(chunk)
    f["world/build"] = mc([f"function gti:world/{i}" for i in range(len(chunks))])

    # --------------------------------------------------------------- stats
    f["ui/stats"] = mc(["dialog show @s gti:stats"])
    f["ui/menu"] = mc(["dialog show @s gti:menu"])
    f["ui/host"] = mc(["dialog show @s gti:host"])
    f["ui/settings"] = mc(["dialog show @s gti:settings"])
    f["ui/rules"] = mc(["dialog show @s gti:rules"])
    f["ui/browse"] = mc(["dialog show @s gti:catalogue/index"])
    f["ui/summary"] = mc(["dialog show @s gti:summary"])
    f["ui/stats_reset"] = mc([
        "scoreboard players set @s gti.wins 0",
        "scoreboard players set @s gti.best 0",
        "scoreboard players set @s gti.streak 0",
        "scoreboard players set @s gti.best_streak 0",
        "scoreboard players set @s gti.rounds 0",
        "scoreboard players set @s gti.tries 0",
        'tellraw @s {"text":"Your stats were reset.","color":"#8BE28B"}',
        "dialog show @s gti:stats",
    ])
    return f
