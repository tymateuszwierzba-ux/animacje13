"""Load/tick, setup, round state machine and all gameplay functions."""

from __future__ import annotations

from logic import CAT_LABELS, PIXELS, data_functions, hud_functions, visual_functions
from model import mc
from world import build_world, mask_lines, pixel_lines, ripple_lines

TRIGGERS = [
    ("menu", "gti/ui/menu"),
    ("play", "gti/ui/play"),
    ("pixel", "gti/internal/pixel_request"),
    ("guess", "gti/internal/guess_request"),
    ("hint", "gti/internal/hint_request"),
    ("next", "gti/internal/next"),
    ("stats", "gti/ui/stats"),
    ("settings", "gti/ui/settings"),
    ("browser", "gti/ui/browser"),
    ("hand", "gti/ui/hand"),
    ("random", "gti/ui/random"),
    ("stop", "gti/internal/stop"),
    ("hostmenu", "gti/ui/host"),
    ("pick", "gti/ui/pick"),
    ("pause", "gti/ui/pause_click"),
    ("summary", "gti/ui/summary"),
]


def _constants() -> list[str]:
    return [
        "scoreboard players set #ten gti.var 10",
        "scoreboard players set #twenty gti.var 20",
        "scoreboard players set #sixty gti.var 60",
        "scoreboard players set #eighty gti.var 80",
        "scoreboard players set #hundred gti.var 100",
        "scoreboard players set #thousand gti.var 1000",
        "scoreboard players set #tenk gti.var 10000",
        "scoreboard players set #two gti.var 2",
        "scoreboard players set #three gti.var 3",
        "scoreboard players set #twelve gti.var 12",
        "scoreboard players set #eight gti.var 8",
        "scoreboard players set #halo_max gti.var 36",
        "scoreboard players set #maxpix gti.var 256",
    ]


def _defaults() -> list[str]:
    return [
        "scoreboard players set #source gti.var 0",
        "scoreboard players set #reveal_mode gti.var 0",
        "scoreboard players set #batch gti.var 1",
        "scoreboard players set #seconds_cfg gti.var 6",
        "scoreboard players set #initial gti.var 1",
        "scoreboard players set #limit gti.var 0",
        "scoreboard players set #aliases gti.var 1",
        "scoreboard players set #hints_enabled gti.var 1",
    ]


def _reset_round() -> list[str]:
    return [
        "scoreboard players set #state gti.var 1",
        "scoreboard players set #anim gti.var 0",
        "scoreboard players set #clock gti.var 0",
        "scoreboard players set #result gti.var 2",
        "scoreboard players set #paused gti.var 0",
        "scoreboard players set #hint_stage gti.var 0",
        "scoreboard players set #hints_used gti.var 0",
        "scoreboard players set #cost gti.var 0",
        "scoreboard players set #pixels gti.var 0",
        "scoreboard players set #guesses gti.var 0",
        "scoreboard players set #wrong gti.var 0",
        "scoreboard players set #time gti.var 0",
        "scoreboard players set #timer gti.var 0",
        "scoreboard players set #shown_summary gti.var 0",
        "scoreboard players set #new_record gti.var 0",
        "scoreboard players set #free gti.var 0",
        "scoreboard players set #warned gti.var 0",
        "scoreboard players add #round gti.var 1",
        "scoreboard players operation #interval gti.var = #seconds_cfg gti.var",
        "scoreboard players operation #interval gti.var *= #twenty gti.var",
        "scoreboard players set @a[tag=gti.player] gti.tries 0",
        "scoreboard players set @a[tag=gti.player] gti.clicks 0",
    ]


def game_functions(vd: dict) -> dict[str, str]:
    f: dict[str, str] = {}
    f.update(data_functions(vd))
    f.update(visual_functions(vd))
    f.update(hud_functions(vd))
    f.update(ripple_lines())

    for col in range(16):
        f[f"internal/columns/{col}"] = mc(mask_lines(col))
        f[f"internal/pixels/{col}"] = mc(pixel_lines(col))

    # -- load -----------------------------------------------------------
    objectives = [
        "gti.menu", "gti.play", "gti.pixel", "gti.guess", "gti.hint", "gti.next",
        "gti.stats", "gti.settings", "gti.browser", "gti.hand", "gti.random",
        "gti.stop", "gti.hostmenu", "gti.pick", "gti.pause", "gti.summary",
    ]
    load = [f"scoreboard objectives add {name} trigger" for name in objectives]
    load += [
        "scoreboard objectives add gti.var dummy",
        "scoreboard objectives add gti.id dummy",
        "scoreboard objectives add gti.age dummy",
        "scoreboard objectives add gti.wins dummy",
        "scoreboard objectives add gti.best dummy",
        "scoreboard objectives add gti.tries dummy",
        "scoreboard objectives add gti.clicks dummy",
        "scoreboard objectives add gti.rounds dummy",
        "scoreboard objectives add gti.streak dummy",
        "scoreboard objectives add gti.best_streak dummy",
        'bossbar add gti:budget {"text":"BUDŻET RUNDY","color":"green"}',
        'bossbar add gti:timer {"text":"NASTĘPNE ODKRYCIE","color":"purple"}',
        "execute unless score #init gti.var matches 1 run function gti:internal/init",
        "scoreboard players set #init gti.var 1",
        f"execute unless score #data_count gti.var matches {vd['count']} run function gti:data/init",
        "execute unless score #fx_ready gti.var matches 1 run function gti:visual/setup",
        "scoreboard players set #fx_ready gti.var 1",
        "execute unless score #cat_ready gti.var matches 1 run function gti:ui/cat_init",
        "scoreboard players set #cat_ready gti.var 1",
        f'tellraw @a [{{"text":"[Guess the Item] ","color":"#45E9E0","bold":true}},{{"text":"v3 • {vd["label"]} • {vd["count"]} przedmiotów","color":"gray"}}]',
        'tellraw @a [{"text":"/function gti:setup","color":"#61EDE5","click_event":{"action":"suggest_command","command":"/function gti:setup"}},{"text":"   •   ","color":"dark_gray"},{"text":"/trigger gti.menu","color":"#F47BC6","click_event":{"action":"run_command","command":"trigger gti.menu set 1"}},{"text":"  (menu bez OP)","color":"gray"}]',
    ]
    f["load"] = mc(load)

    f["internal/init"] = mc(
        _constants()
        + [
            "execute unless score #v3 gti.var matches 1 run function gti:internal/defaults",
            "scoreboard players set #v3 gti.var 1",
            "scoreboard players set #state gti.var 0",
            "scoreboard players set #result gti.var 2",
            "scoreboard players set #round gti.var 0",
            "scoreboard players set #last_index gti.var -1",
            "scoreboard players set #pixels gti.var 0",
            "scoreboard players set #guesses gti.var 0",
            "scoreboard players set #wrong gti.var 0",
            "scoreboard players set #cost gti.var 0",
            "scoreboard players set #time gti.var 0",
            "scoreboard players set #timer gti.var 0",
            "scoreboard players set #clock gti.var 0",
            "scoreboard players set #anim gti.var 0",
            "scoreboard players set #paused gti.var 0",
            "scoreboard players set #hint_stage gti.var 0",
            "scoreboard players set #hints_used gti.var 0",
            "scoreboard players set #free gti.var 0",
            "scoreboard players set #warned gti.var 0",
            "scoreboard players set #summary_ready gti.var 0",
            "scoreboard players set #pulse gti.var 0",
            "scoreboard players set #bob gti.var 0",
            "scoreboard players set #sway gti.var 0",
            "scoreboard players set #scan gti.var 0",
            "scoreboard players set #run0 gti.var 0",
            "scoreboard players set #run1 gti.var 40",
            "scoreboard players set #halo gti.var 0",
            "scoreboard players set #shutter gti.var 0",
            "scoreboard players set #idle_fx gti.var 0",
            "scoreboard players set #team_best gti.var 2147483000",
            "scoreboard players set #team_best_tries gti.var 0",
            "scoreboard players set #team_best_pixels gti.var 0",
            "scoreboard players set #ab_clock gti.var 0",
            'data modify storage gti:config fixed set value {id:"minecraft:diamond",count:1}',
            'data modify storage gti:cfg answer set value "minecraft:diamond"',
            'data modify storage gti:cfg answer_key set value "item.minecraft.diamond"',
            'data modify storage gti:cfg hint set value "BRAK PODPOWIEDZI"',
            'data modify storage gti:ui guesses set value 0',
            'data modify storage gti:ui pixels set value 0',
            'data modify storage gti:ui wrong set value 0',
            'data modify storage gti:ui batch set value 1',
            'data modify storage gti:ui limit set value 0',
            'data modify storage gti:ui cost set value 0',
            'data modify storage gti:ui mins set value 0',
            'data modify storage gti:ui secs set value 0',
            'data modify storage gti:ui round set value 0',
            'data modify storage gti:ui hint_stage set value 0',
            'data modify storage gti:ui timer_seconds set value 0',
            'data modify storage gti:ui mm0 set value ""',
            'data modify storage gti:ui ss0 set value ""',
            'data modify storage gti:ui limit_label set value "∞"',
            'data modify storage gti:ui mode set value "RĘCZNIE"',
            'data modify storage gti:ui status set value "GOTOWA"',
            'data modify storage gti:ui time set value "0:00"',
            'data modify storage gti:ui hint set value "BRAK PODPOWIEDZI"',
            'data modify storage gti:ui answer set value "???"',
            'data modify storage gti:ui answer_line set value "ODPOWIEDŹ: ???"',
            'data modify storage gti:ui reveal_label set value "ODKRYJ ×1"',
            'data modify storage gti:ui hint_label set value "PODPOWIEDŹ 0/3"',
            'data modify storage gti:ui budget_label set value "0 / ∞"',
            'data modify storage gti:ui progress_label set value "0 / 256"',
            'data modify storage gti:ui round_label set value "RUNDA 0 • GOTOWA"',
            'data modify storage gti:ui timer_label set value "RĘCZNIE"',
        ]
    )
    f["internal/defaults"] = mc(_defaults())

    # -- tick -----------------------------------------------------------
    tick = [
        "scoreboard players add #clock gti.var 1",
        "execute if score #clock gti.var matches 4.. run scoreboard players set #clock gti.var 0",
        "scoreboard players add #ab_clock gti.var 1",
        "execute if score #ab_clock gti.var matches 10.. run scoreboard players set #ab_clock gti.var 0",
    ]
    for obj, fn in TRIGGERS:
        tick += [
            f"execute as @a[scores={{gti.{obj}=1..}}] at @s run function {fn}",
            f"scoreboard players set @a[scores={{gti.{obj}=1..}}] gti.{obj} 0",
            f"scoreboard players enable @a gti.{obj}",
        ]
    tick += [
        "execute as @e[tag=gti.control] at @s if data entity @s interaction run function gti:internal/control_event",
        "execute as @e[tag=gti.pixel,tag=!gti.open] at @s if data entity @s interaction run function gti:internal/pixel_event",
        "execute as @e[tag=gti.pixel,tag=!gti.open] at @s if data entity @s attack run function gti:internal/pixel_attack",
        "scoreboard players add @e[tag=gti.fx] gti.age 1",
        "kill @e[tag=gti.fx,scores={gti.age=8..}]",
        "execute in minecraft:overworld at @e[tag=gti.anchor,limit=1] run function gti:internal/tick",
    ]
    f["tick"] = mc(tick)

    f["internal/tick"] = mc(
        [
            "execute if score #state gti.var matches 1 run function gti:internal/intro",
            "execute if score #state gti.var matches 2 run function gti:internal/active",
            "execute if score #state gti.var matches 3 run function gti:internal/finale",
            "function gti:visual/tick",
            "execute if score #clock gti.var matches 0 run function gti:internal/periodic",
            "execute if score #ab_clock gti.var matches 0 run function gti:ui/actionbar",
        ]
    )

    f["internal/periodic"] = mc(
        [
            "function gti:internal/hud",
            "function gti:visual/bob",
            "function gti:visual/pulse",
            "execute if score #state gti.var matches 0..1 run function gti:visual/particles_idle",
            "execute if score #idle_fx gti.var matches 1.. run function gti:internal/idle_fx",
            "execute if score #idle_fx gti.var matches 1.. run scoreboard players remove #idle_fx gti.var 1",
        ]
    )
    f["internal/idle_fx"] = mc(
        [
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:end_rod ~ ~11.6 ~0.5 8.5 0.2 0.2 0.01 2 force @a[tag=gti.player]",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:glow ~ ~ ~0.9 9.5 9.5 0.1 0.01 3 force @a[tag=gti.player]",
        ]
    )

    # -- setup / remove / view -----------------------------------------
    f["setup"] = mc(
        [
            "execute unless entity @s[type=player] run return run tellraw @a {\"text\":\"Setup uruchom jako gracz.\",\"color\":\"red\"}",
            "execute unless dimension minecraft:overworld run return run tellraw @s {\"text\":\"Planszę zbuduj w Overworldzie.\",\"color\":\"red\"}",
            "function gti:remove",
            "execute align xyz positioned ~ ~11 ~-30 run function gti:internal/build",
            "tp @s ~ ~ ~ 180 -17",
            "tag @a remove gti.host",
            "tag @s add gti.host",
            "tag @s add gti.player",
            "scoreboard players set #state gti.var 0",
            "scoreboard players set #result gti.var 2",
            "scoreboard players set #round gti.var 0",
            "execute at @e[tag=gti.anchor,limit=1] run function gti:internal/hud",
            "execute at @e[tag=gti.anchor,limit=1] run function gti:visual/particles_idle",
            "tellraw @s [{\"text\":\"Plansza gotowa. \",\"color\":\"#8BE28B\"},{\"text\":\"/function gti:start\",\"color\":\"#61EDE5\",\"click_event\":{\"action\":\"run_command\",\"command\":\"function gti:start\"}},{\"text\":\" lub wybierz ruch w panelu.\",\"color\":\"gray\"}]",
            "dialog show @s gti:menu",
        ]
    )
    f["internal/build"] = mc(build_world(vd))

    f["remove"] = mc(
        [
            "execute in minecraft:overworld run kill @e[tag=gti.entity]",
            "scoreboard players set #state gti.var 0",
            "scoreboard players set #result gti.var 2",
            "scoreboard players set #paused gti.var 0",
            "scoreboard players set #halo gti.var 0",
            "bossbar set gti:budget visible false",
            "bossbar set gti:timer visible false",
            "tag @a remove gti.player",
            "tag @a remove gti.host",
            "dialog clear @a",
            "tellraw @s {\"text\":\"Plansza i efekty usunięte.\",\"color\":\"gray\"}",
        ]
    )

    f["view"] = mc(
        [
            "execute unless entity @s[type=player] run return 0",
            "execute in minecraft:overworld unless entity @e[tag=gti.anchor] run return run tellraw @s {\"text\":\"Brak planszy — /function gti:setup\",\"color\":\"red\"}",
            "tp @s ~ ~ ~ 180 -17",
            "tag @s add gti.player",
        ]
    )

    # -- start / stop ---------------------------------------------------
    f["start"] = mc(
        [
            "execute unless entity @s[type=player] run return 0",
            "execute in minecraft:overworld unless entity @e[tag=gti.anchor] run return run tellraw @s {\"text\":\"Najpierw /function gti:setup.\",\"color\":\"red\"}",
            "execute unless score #state gti.var matches 0 run return run tellraw @s {\"text\":\"Runda trwa. /function gti:stop ją przerwie.\",\"color\":\"red\"}",
            "tag @s add gti.player",
            "execute at @e[tag=gti.anchor,limit=1] run tag @a[distance=..64] add gti.player",
            "execute at @e[tag=gti.anchor,limit=1] run function gti:internal/start",
        ]
    )

    f["internal/start"] = mc(
        _reset_round()
        + [
            "execute as @e[tag=gti.mask] run data merge entity @s {block_state:{Name:\"minecraft:black_concrete\"},start_interpolation:0,interpolation_duration:0,transformation:{scale:[1.26f,1.26f,0.055f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}",
            "execute as @e[tag=gti.mask] run tag @s remove gti.fx",
            "kill @e[tag=gti.pixel]",
            *[f"function gti:internal/pixels/{i}" for i in range(16)],
            "kill @e[tag=gti.fx]",
            "function gti:visual/halo_reset",
            "function gti:visual/shutter_open_all",
            "function gti:data/set_answer",
            "function gti:visual/answer_hidden",
            'execute as @e[tag=gti.overlay.title,limit=1] run data modify entity @s text set value {"text":"INICJALIZACJA","color":"#45E9E0","bold":true}',
            'execute as @e[tag=gti.overlay.title,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:8,transformation:{scale:[1.9f,1.9f,1.9f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.overlay.sub,limit=1] run data modify entity @s text set value {"text":"Losowanie przedmiotu z pełnej puli","color":"#8FA8C8"}',
            'execute as @e[tag=gti.overlay.sub,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:8,transformation:{scale:[0.85f,0.85f,0.85f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.overlay.count,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:0,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.overlay.bad,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:0,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.item,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:0,transformation:{scale:[20f,20f,0.001f],translation:[0f,0f,0f],left_rotation:[0f,1f,0f,0f],right_rotation:[0f,0f,0f,1f]}}',
            'execute as @e[tag=gti.hud.answer,limit=1] run data modify entity @s text set value [{"text":"ODPOWIEDŹ UKRYTA","color":"#8FA8C8"}]',
            'data modify storage gti:tmp msg set value "Runda startuje — losowanie hasła."',
            "function gti:visual/event with storage gti:tmp",
            "title @a[tag=gti.player] times 5 35 10",
            'title @a[tag=gti.player] subtitle {"text":"Przygotuj się…","color":"gray"}',
            'title @a[tag=gti.player] title {"text":"GUESS THE ITEM","color":"#45E9E0","bold":true}',
            "execute as @a[tag=gti.player] at @s run playsound minecraft:block.beacon.activate master @s ~ ~ ~ 0.65 1.2",
            "execute as @a[tag=gti.player] at @s run playsound minecraft:block.conduit.activate master @s ~ ~ ~ 0.5 1.4",
            "function gti:internal/hud",
        ]
    )

    intro = [
        "scoreboard players add #anim gti.var 1",
    ]
    for k in range(8):
        intro.append(f"execute if score #anim gti.var matches {1 + 2 * k} run function gti:visual/shutter_close_{k}")
    for k in range(8):
        intro.append(f"execute if score #anim gti.var matches {24 + 3 * k} run function gti:visual/shutter_open_{k}")
    for k in range(8):
        intro.append(f"execute if score #anim gti.var matches {34 + 5 * k} run function gti:visual/ripple_{k}")
        intro.append(f"execute if score #anim gti.var matches {78 + 2 * k} run function gti:visual/ripple_clear_{k}")
    intro += [
        "execute if score #anim gti.var matches 34 as @a[tag=gti.player] at @s run playsound minecraft:block.amethyst_block.chime master @s ~ ~ ~ 0.55 1.6",
        "execute if score #anim gti.var matches 70 as @a[tag=gti.player] at @s run playsound minecraft:block.beacon.deactivate master @s ~ ~ ~ 0.5 1.1",
        "execute if score #anim gti.var matches 84 run function gti:internal/pick_announce",
        "execute if score #anim gti.var matches 92 run function gti:internal/count3",
        "execute if score #anim gti.var matches 104 run function gti:internal/count2",
        "execute if score #anim gti.var matches 116 run function gti:internal/count1",
        "execute if score #anim gti.var matches 128 run function gti:internal/begin",
    ]
    f["internal/intro"] = mc(intro)

    f["internal/pick_announce"] = mc(
        [
            'execute as @e[tag=gti.overlay.title,limit=1] run data modify entity @s text set value {"text":"HASŁO WYLOSOWANE","color":"#F6CF84","bold":true}',
            'execute as @e[tag=gti.overlay.sub,limit=1] run data modify entity @s text set value {"text":"Kliknij kafelek albo użyj panelu","color":"#8FA8C8"}',
        ]
    )

    def countdown(fn: str, n: int, color: str) -> str:
        return mc(
            [
                f'execute as @e[tag=gti.overlay.title,limit=1] run data merge entity @s {{start_interpolation:0,interpolation_duration:5,transformation:{{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}}}',
                f'execute as @e[tag=gti.overlay.sub,limit=1] run data merge entity @s {{start_interpolation:0,interpolation_duration:5,transformation:{{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}}}',
                f'execute as @e[tag=gti.overlay.count,limit=1] run data modify entity @s text set value {{"text":"{n}","color":"{color}","bold":true}}',
                'execute as @e[tag=gti.overlay.count,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:0,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}',
                'execute as @e[tag=gti.overlay.count,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:7,transformation:{scale:[5.6f,5.6f,5.6f],translation:[0f,0f,0f]}}',
                "execute as @a[tag=gti.player] at @s run playsound minecraft:block.note_block.pling master @s ~ ~ ~ 0.8 1.0",
                "execute as @a[tag=gti.player] at @s run playsound minecraft:block.note_block.bass master @s ~ ~ ~ 0.5 0.8",
            ]
        )

    f["internal/count3"] = countdown("count3", 3, "#F6CF84")
    f["internal/count2"] = countdown("count2", 2, "#FFC46B")
    f["internal/count1"] = countdown("count1", 1, "#8BE28B")

    f["internal/begin"] = mc(
        [
            "scoreboard players set #state gti.var 2",
            "scoreboard players set #time gti.var 0",
            "scoreboard players set #timer gti.var 0",
            "function gti:visual/shutter_open_all",
            'execute as @e[tag=gti.overlay.count,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:4,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.overlay.title,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:4,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.overlay.sub,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:4,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}',
            'title @a[tag=gti.player] times 4 30 10',
            'title @a[tag=gti.player] subtitle {"text":"Odkrywaj piksele • zgaduj przedmiot z ręki","color":"gray"}',
            'title @a[tag=gti.player] title {"text":"ZGADUJ!","color":"#8BE28B","bold":true}',
            "execute as @a[tag=gti.player] at @s run playsound minecraft:entity.experience_orb.pickup master @s ~ ~ ~ 0.7 1.5",
            "execute if score #initial gti.var matches 1.. run function gti:internal/initial_reveal",
            'data modify storage gti:tmp msg set value "Kliknij kafelek lub przycisk ODKRYJ."',
            "function gti:visual/event with storage gti:tmp",
            "tellraw @a[tag=gti.player] [{\"text\":\"▶ Otwórz panel gry\",\"color\":\"#45E9E0\",\"bold\":true,\"click_event\":{\"action\":\"run_command\",\"command\":\"trigger gti.play set 1\"}},{\"text\":\"   •   LPM/PPM na kafelku odsłania pobliskie pola\",\"color\":\"gray\"}]",
            "function gti:internal/hud",
        ]
    )

    f["internal/initial_reveal"] = mc(
        [
            "scoreboard players set #free gti.var 1",
            "execute store result storage gti:ctx batch int 1 run scoreboard players get #initial gti.var",
            "execute at @e[tag=gti.anchor,limit=1] run function gti:internal/batch_random with storage gti:ctx",
            "scoreboard players set #free gti.var 0",
        ]
    )

    f["internal/active"] = mc(
        [
            "execute if score #paused gti.var matches 1 run return 0",
            "scoreboard players add #time gti.var 1",
            "execute if score #reveal_mode gti.var matches 2 run scoreboard players add #timer gti.var 1",
            "execute if score #reveal_mode gti.var matches 2 if score #timer gti.var >= #interval gti.var run function gti:internal/auto_batch",
            "execute if score #limit gti.var matches 1.. if score #remaining gti.var matches 1..8 if score #warned gti.var matches 0 run function gti:internal/warn",
            "execute if score #limit gti.var matches 1.. if score #cost gti.var >= #limit gti.var run function gti:internal/lose",
        ]
    )

    f["internal/warn"] = mc(
        [
            "scoreboard players set #warned gti.var 1",
            'title @a[tag=gti.player] actionbar [{"text":"⚠ NISKI BUDŻET","color":"red","bold":true}]',
            "execute as @a[tag=gti.player] at @s run playsound minecraft:block.note_block.bass master @s ~ ~ ~ 0.5 1.4",
        ]
    )

    f["internal/auto_batch"] = mc(
        [
            "scoreboard players set #timer gti.var 0",
            "execute store result storage gti:ctx batch int 1 run scoreboard players get #batch gti.var",
            "execute at @e[tag=gti.anchor,limit=1] run function gti:internal/batch_random with storage gti:ctx",
            "function gti:internal/hud",
        ]
    )

    f["internal/batch_random"] = mc(
        [
            "$execute as @e[tag=gti.pixel,tag=!gti.open,sort=random,limit=$(batch)] at @s run function gti:internal/reveal",
            "execute at @e[tag=gti.anchor,limit=1] run playsound minecraft:block.amethyst_block.chime master @a[tag=gti.player] ~ ~ ~ 0.5 1.35",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:electric_spark ~ ~ ~0.6 9 9 0.2 0.02 30 force @a[tag=gti.player]",
        ]
    )
    f["internal/batch_near"] = mc(
        [
            "$execute as @e[tag=gti.pixel,tag=!gti.open,sort=nearest,limit=$(batch)] at @s run function gti:internal/reveal",
            "execute at @e[tag=gti.anchor,limit=1] run playsound minecraft:block.amethyst_block.chime master @a[tag=gti.player] ~ ~ ~ 0.45 1.5",
        ]
    )

    f["internal/reveal"] = mc(
        [
            "execute unless score #state gti.var matches 2 run return 0",
            "execute if score #paused gti.var matches 1 run return 0",
            "tag @s add gti.open",
            "data remove entity @s interaction",
            "data remove entity @s attack",
            "scoreboard players add #pixels gti.var 1",
            "execute if score #free gti.var matches 0 run scoreboard players add #cost gti.var 1",
            "execute store result storage gti:ctx id int 1 run scoreboard players get @s gti.id",
            "function gti:internal/shrink with storage gti:ctx",
            "execute at @s run particle minecraft:glow ~ ~ ~0.2 0.5 0.5 0.15 0 8 force @a[tag=gti.player]",
            "execute if score #limit gti.var matches 1.. if score #cost gti.var >= #limit gti.var run function gti:internal/lose",
        ]
    )

    f["internal/shrink"] = mc(
        [
            '$data merge entity @e[tag=gti.mask,scores={gti.id=$(id)},limit=1] {start_interpolation:0,interpolation_duration:5,transformation:{scale:[0.02f,0.02f,0.06f],translation:[0f,0f,1.45f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}',
            '$execute at @e[tag=gti.mask,scores={gti.id=$(id)},limit=1] run particle minecraft:electric_spark ~0.63 ~0.63 ~0.2 0.45 0.45 0.1 0.12 8 force @a[tag=gti.player]',
            '$execute at @e[tag=gti.mask,scores={gti.id=$(id)},limit=1] run summon block_display ~0.63 ~0.63 ~0.2 {Tags:["gti.entity","gti.fx","gti.flash"],block_state:{Name:"minecraft:white_concrete"},brightness:{sky:15,block:15},view_range:4f,transformation:{scale:[1.28f,1.28f,0.05f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}',
        ]
    )

    # -- input ----------------------------------------------------------
    f["internal/pixel_request"] = mc(
        [
            "execute unless score #state gti.var matches 2 run return run tellraw @s {\"text\":\"Poczekaj na start rundy. Menu: /trigger gti.menu\",\"color\":\"gray\"}",
            "execute if score #paused gti.var matches 1 run return run tellraw @s {\"text\":\"Runda jest wstrzymana.\",\"color\":\"yellow\"}",
            "execute unless entity @e[tag=gti.pixel,tag=!gti.open,limit=1] run return run tellraw @s {\"text\":\"Wszystkie pola odkryte — zgaduj! Trzymaj przedmiot w ręce.\",\"color\":\"yellow\"}",
            "tag @s add gti.player",
            "scoreboard players add @s gti.clicks 1",
            "execute store result storage gti:ctx batch int 1 run scoreboard players get #batch gti.var",
            "execute at @e[tag=gti.anchor,limit=1] run function gti:internal/batch_random with storage gti:ctx",
            'data modify storage gti:tmp msg set value "Odkryto paczkę pikseli."',
            "function gti:visual/event with storage gti:tmp",
            "function gti:internal/hud",
        ]
    )

    f["internal/pixel_event"] = mc(
        [
            "execute unless score #state gti.var matches 2 run return run data remove entity @s interaction",
            "execute if score #paused gti.var matches 1 run return run data remove entity @s interaction",
            "execute on target run tag @s add gti.player",
            "execute on target run scoreboard players add @s gti.clicks 1",
            "execute store result storage gti:ctx batch int 1 run scoreboard players get #batch gti.var",
            "function gti:internal/batch_near with storage gti:ctx",
            "data remove entity @s interaction",
            "data remove entity @s attack",
            "function gti:internal/hud",
        ]
    )
    f["internal/pixel_attack"] = mc(
        [
            "execute unless score #state gti.var matches 2 run return run data remove entity @s attack",
            "execute if score #paused gti.var matches 1 run return run data remove entity @s attack",
            "execute on attacker run tag @s add gti.player",
            "execute on attacker run scoreboard players add @s gti.clicks 1",
            "execute store result storage gti:ctx batch int 1 run scoreboard players get #batch gti.var",
            "function gti:internal/batch_near with storage gti:ctx",
            "function gti:internal/hud",
        ]
    )

    f["internal/control_event"] = mc(
        [
            "execute if entity @s[tag=gti.control.reveal] on target run function gti:internal/pixel_request",
            "execute if entity @s[tag=gti.control.guess] on target run function gti:internal/guess_request",
            "execute if entity @s[tag=gti.control.hint] on target run function gti:internal/hint_request",
            "execute if entity @s[tag=gti.control.pause] on target run function gti:ui/pause_click",
            "execute if entity @s[tag=gti.control.menu] on target run function gti:ui/menu",
            "execute if entity @s[tag=gti.control.menu] on target run playsound minecraft:ui.button.click master @s ~ ~ ~ 0.6 1.2",
            "data remove entity @s interaction",
            "data remove entity @s attack",
        ]
    )

    # -- guesses --------------------------------------------------------
    f["internal/guess_request"] = mc(
        [
            "execute unless score #state gti.var matches 2 run return run tellraw @s {\"text\":\"Poczekaj na start rundy.\",\"color\":\"gray\"}",
            "execute if score #paused gti.var matches 1 run return run tellraw @s {\"text\":\"Runda jest wstrzymana.\",\"color\":\"yellow\"}",
            "execute unless items entity @s weapon.mainhand #gti:answers run return run tellraw @s {\"text\":\"Trzymaj obsługiwany przedmiot w głównej ręce — pusta ręka nie nalicza próby.\",\"color\":\"yellow\"}",
            "tag @s add gti.player",
            "scoreboard players add @s gti.tries 1",
            "scoreboard players add #guesses gti.var 1",
            "data modify storage gti:ctx answer set from storage gti:cfg answer",
            'data modify storage gti:ctx guess set from entity @s SelectedItem.id',
            "scoreboard players set #same gti.var 0",
            "function gti:internal/check_guess with storage gti:ctx",
            "execute if score #same gti.var matches 0 if score #aliases gti.var matches 1 run function gti:internal/equiv with storage gti:ctx",
            "execute if score #same gti.var matches 1 run function gti:internal/win",
            "execute if score #same gti.var matches 0 run function gti:internal/wrong",
            "function gti:internal/hud",
        ]
    )
    f["internal/check_guess"] = mc(
        ['$execute if data storage gti:ctx {answer:"$(guess)"} run scoreboard players set #same gti.var 1']
    )
    f["internal/equiv"] = mc(
        [
            '$execute store result score #eq_guess gti.var run data get storage gti:items by_id."$(guess)" eq',
            "execute if score #eq_answer gti.var matches 0.. if score #eq_guess gti.var = #eq_answer gti.var run scoreboard players set #same gti.var 1",
        ]
    )

    f["internal/win"] = mc(
        [
            "execute unless score #state gti.var matches 2 run return 0",
            "scoreboard players add @s gti.wins 1",
            "scoreboard players add @s gti.rounds 1",
            "scoreboard players add @s gti.streak 1",
            "execute if score @s gti.streak > @s gti.best_streak run scoreboard players operation @s gti.best_streak = @s gti.streak",
            "scoreboard players operation #rank gti.var = #guesses gti.var",
            "scoreboard players operation #rank gti.var *= #thousand gti.var",
            "scoreboard players operation #rank gti.var += #pixels gti.var",
            "scoreboard players set #new_record gti.var 0",
            "execute unless score @s gti.best matches 1.. run scoreboard players set #new_record gti.var 1",
            "execute if score #new_record gti.var matches 0 if score #rank gti.var < @s gti.best run scoreboard players set #new_record gti.var 1",
            "execute if score #new_record gti.var matches 1 run scoreboard players operation @s gti.best = #rank gti.var",
            "execute if score #new_record gti.var matches 1 if score #rank gti.var < #team_best gti.var run scoreboard players operation #team_best gti.var = #rank gti.var",
            "execute if score #new_record gti.var matches 1 if score #rank gti.var < #team_best gti.var run scoreboard players operation #team_best_tries gti.var = #guesses gti.var",
            "execute if score #new_record gti.var matches 1 if score #rank gti.var < #team_best gti.var run scoreboard players operation #team_best_pixels gti.var = #pixels gti.var",
            "execute if score #new_record gti.var matches 1 run tellraw @s {\"text\":\"★ NOWY REKORD! ★\",\"color\":\"gold\",\"bold\":true}",
            "scoreboard players set #result gti.var 1",
            "title @a[tag=gti.player] times 5 55 12",
            'title @a[tag=gti.player] subtitle [{"selector":"@s","color":"#F6CF84"},{"text":" odgaduje przedmiot!","color":"white"}]',
            'title @a[tag=gti.player] title {"text":"TRAFIONE!","color":"#8BE28B","bold":true}',
            "execute as @a[tag=gti.player] at @s run playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 0.75 1.05",
            "execute as @a[tag=gti.player] at @s run playsound minecraft:entity.player.levelup master @s ~ ~ ~ 0.5 1.4",
            "function gti:internal/finish",
        ]
    )

    f["internal/wrong"] = mc(
        [
            "execute unless score #state gti.var matches 2 run return 0",
            "scoreboard players add #wrong gti.var 1",
            "scoreboard players add #cost gti.var 4",
            "scoreboard players set @s gti.streak 0",
            "title @s times 2 22 8",
            'title @s subtitle {"text":"−4 punkty • spróbuj ponownie","color":"gray"}',
            'title @s title {"text":"NIE TEN ITEM","color":"#FF8996","bold":true}',
            "execute at @s run playsound minecraft:block.note_block.bass master @s ~ ~ ~ 0.8 0.55",
            'execute as @e[tag=gti.overlay.bad,limit=1] run data modify entity @s text set value {"text":"−4 PUNKTY","color":"#FF8996","bold":true}',
            'execute as @e[tag=gti.overlay.bad,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:0,transformation:{scale:[0.4f,0.4f,0.4f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.overlay.bad,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:4,transformation:{scale:[1.5f,1.5f,1.5f],translation:[0f,0f,0f]}}',
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:glow ~ ~ ~0.7 8 8 0.2 0.01 60 force @a[tag=gti.player]",
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:smoke ~ ~ ~0.7 6 6 0.2 0.02 25 force @a[tag=gti.player]",
            "function gti:internal/hud",
            "execute if score #limit gti.var matches 1.. if score #cost gti.var >= #limit gti.var run function gti:internal/lose",
            "execute if score #state gti.var matches 2 if score #reveal_mode gti.var matches 1 run function gti:internal/auto_batch",
        ]
    )

    f["internal/lose"] = mc(
        [
            "execute unless score #state gti.var matches 2 run return 0",
            "scoreboard players set #result gti.var 0",
            "title @a[tag=gti.player] times 5 60 15",
            'title @a[tag=gti.player] subtitle {"text":"Budżet wyczerpany — odpowiedź na planszy","color":"gray"}',
            'title @a[tag=gti.player] title {"text":"KONIEC RUNDY","color":"#FF8996","bold":true}',
            "execute as @a[tag=gti.player] at @s run playsound minecraft:block.beacon.deactivate master @s ~ ~ ~ 0.7 0.7",
            "execute as @a[tag=gti.player] at @s run playsound minecraft:entity.villager.no master @s ~ ~ ~ 0.6 0.8",
            "function gti:internal/finish",
        ]
    )

    f["internal/finish"] = mc(
        [
            "scoreboard players set #state gti.var 3",
            "scoreboard players set #anim gti.var 0",
            "scoreboard players operation #last_tries gti.var = #guesses gti.var",
            "scoreboard players operation #last_pixels gti.var = #pixels gti.var",
            "scoreboard players operation #last_wrong gti.var = #wrong gti.var",
            "scoreboard players operation #last_time gti.var = #time gti.var",
            "scoreboard players operation #last_time gti.var /= #twenty gti.var",
            "scoreboard players operation #last_hints gti.var = #hints_used gti.var",
            "scoreboard players operation #last_cost gti.var = #cost gti.var",
            "scoreboard players operation #last_result gti.var = #result gti.var",
            "scoreboard players set #shown_summary gti.var 0",
            "scoreboard players set #summary_ready gti.var 1",
            "kill @e[tag=gti.pixel]",
            "kill @e[tag=gti.fx]",
            "bossbar set gti:timer visible false",
            "data modify storage gti:tmp key set from storage gti:cfg answer_key",
            "function gti:visual/answer_caption with storage gti:tmp",
            'data modify storage gti:tmp msg set value "Koniec rundy — podsumowanie za chwilę."',
            "function gti:visual/event with storage gti:tmp",
            "execute if score #result gti.var matches 1 run function gti:internal/finale_win_start",
            "execute if score #result gti.var matches 0 run function gti:internal/finale_lose_start",
            "function gti:internal/hud",
        ]
    )

    f["internal/finale_win_start"] = mc(
        [
            'execute as @e[tag=gti.overlay.title,limit=1] run data modify entity @s text set value {"text":"TRAFIONE!","color":"#8BE28B","bold":true}',
            'execute as @e[tag=gti.overlay.title,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:8,transformation:{scale:[2.7f,2.7f,2.7f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.overlay.sub,limit=1] run data modify entity @s text set value {"text":"Świetna robota — zobacz podsumowanie","color":"#8FA8C8"}',
            'execute as @e[tag=gti.overlay.sub,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:8,transformation:{scale:[0.9f,0.9f,0.9f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.item,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:14,transformation:{scale:[21.6f,21.6f,0.001f],translation:[0f,0.4f,0f],left_rotation:[0f,1f,0f,0f],right_rotation:[0f,0f,0f,1f]}}',
            "function gti:visual/halo",
            "function gti:visual/confetti",
            "execute as @a[tag=gti.player] at @s run playsound minecraft:entity.firework_rocket.twinkle master @s ~ ~ ~ 0.8 1.1",
            "execute as @a[tag=gti.player] at @s run playsound minecraft:block.conduit.activate master @s ~ ~ ~ 0.6 1.5",
        ]
    )
    f["internal/finale_lose_start"] = mc(
        [
            'execute as @e[tag=gti.overlay.title,limit=1] run data modify entity @s text set value {"text":"KONIEC RUNDY","color":"#FF8996","bold":true}',
            'execute as @e[tag=gti.overlay.title,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:8,transformation:{scale:[2.4f,2.4f,2.4f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.overlay.sub,limit=1] run data modify entity @s text set value {"text":"Odpowiedź odsłonięta na planszy","color":"#8FA8C8"}',
            'execute as @e[tag=gti.overlay.sub,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:8,transformation:{scale:[0.9f,0.9f,0.9f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.item,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:16,transformation:{scale:[21.6f,21.6f,0.001f],translation:[0f,0.4f,0f],left_rotation:[0f,1f,0f,0f],right_rotation:[0f,0f,0f,1f]}}',
            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:glow ~ ~ ~0.6 8 8 0.2 0.01 60 force @a[tag=gti.player]",
            "execute as @a[tag=gti.player] at @s run playsound minecraft:block.beacon.activate master @s ~ ~ ~ 0.6 0.6",
        ]
    )

    f["internal/finale"] = mc(
        [
            "scoreboard players add #anim gti.var 1",
            "execute if score #result gti.var matches 1 run function gti:internal/finale_win",
            "execute if score #result gti.var matches 0 run function gti:internal/finale_lose",
            "execute if score #anim gti.var matches 70 if score #shown_summary gti.var matches 0 run function gti:internal/summary",
            "execute if score #anim gti.var matches 70 run scoreboard players set #shown_summary gti.var 1",
        ]
    )

    win_steps = [7, 8, 6, 9, 5, 10, 4, 11, 3, 12, 2, 13, 1, 14, 0, 15]
    f["internal/finale_win"] = mc(
        [
            f"execute if score #anim gti.var matches {2 + 2 * i} as @e[tag=gti.mask,tag=gti.col{col}] run function gti:internal/final_shrink"
            for i, col in enumerate(win_steps)
        ]
        + [
            "execute if score #anim gti.var matches 74 run function gti:internal/finale_wave_2",
            "execute if score #anim gti.var matches 120 run function gti:internal/end_finale",
        ]
    )
    f["internal/finale_wave_2"] = mc(
        [
            "function gti:visual/confetti",
            "execute as @a[tag=gti.player] at @s run playsound minecraft:entity.firework_rocket.launch master @s ~ ~ ~ 0.7 1.6",
        ]
    )
    f["internal/finale_lose"] = mc(
        [
            f"execute if score #anim gti.var matches {1 + 2 * row} as @e[tag=gti.mask,tag=gti.row{row}] run function gti:internal/final_shrink_lose"
            for row in range(16)
        ]
        + [
            "execute if score #anim gti.var matches 100 run function gti:internal/end_finale",
        ]
    )

    f["internal/final_shrink"] = mc(
        [
            "data merge entity @s {start_interpolation:0,interpolation_duration:9,transformation:{scale:[0.02f,0.02f,0.06f],translation:[0f,0f,0.9f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}",
            "execute at @s run particle minecraft:firework ~0.63 ~0.63 ~0.25 0.35 0.35 0.05 0.12 6 force @a[tag=gti.player]",
        ]
    )
    f["internal/final_shrink_lose"] = mc(
        [
            "data merge entity @s {start_interpolation:0,interpolation_duration:12,transformation:{scale:[0.02f,0.02f,0.06f],translation:[0f,-1.8f,0.6f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}",
            "execute at @s run particle minecraft:crit ~0.63 ~0.63 ~0.25 0.3 0.3 0.05 0 3 force @a[tag=gti.player]",
        ]
    )

    f["internal/end_finale"] = mc(
        [
            "scoreboard players set #state gti.var 0",
            "function gti:internal/restore_board",
            "function gti:internal/hud",
            "execute as @e[tag=gti.overlay.title,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:6,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}",
            "execute as @e[tag=gti.overlay.sub,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:6,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}",
            'data modify storage gti:tmp msg set value "Gotowe. Naciśnij START, aby zagrać ponownie."',
            "function gti:visual/event with storage gti:tmp",
            "scoreboard players set #idle_fx gti.var 5",
        ]
    )

    f["internal/restore_board"] = mc(
        [
            "kill @e[tag=gti.pixel]",
            "kill @e[tag=gti.fx]",
            "execute as @e[tag=gti.mask] run data merge entity @s {block_state:{Name:\"minecraft:black_concrete\"},start_interpolation:0,interpolation_duration:0,transformation:{scale:[1.26f,1.26f,0.055f],translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f]}}",
            "execute as @e[tag=gti.mask] run tag @s remove gti.fx",
            "function gti:visual/halo_reset",
            "function gti:visual/shutter_open_all",
            "function gti:visual/answer_hidden",
            "execute as @e[tag=gti.item,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:0,transformation:{scale:[20f,20f,0.001f],translation:[0f,0f,0f],left_rotation:[0f,1f,0f,0f],right_rotation:[0f,0f,0f,1f]}}",
            "execute as @e[tag=gti.overlay.bad,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:3,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}",
            "bossbar set gti:budget visible false",
            "bossbar set gti:timer visible false",
        ]
    )

    f["internal/stop"] = mc(
        [
            "execute unless score #state gti.var matches 1..3 run return run tellraw @s {\"text\":\"Runda już stoi.\",\"color\":\"gray\"}",
            "scoreboard players set #state gti.var 0",
            "scoreboard players set #paused gti.var 0",
            "scoreboard players set #result gti.var 2",
            "function gti:internal/restore_board",
            'execute as @e[tag=gti.overlay.count,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:0,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.overlay.title,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:3,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}',
            'execute as @e[tag=gti.overlay.sub,limit=1] run data merge entity @s {start_interpolation:0,interpolation_duration:3,transformation:{scale:[0.01f,0.01f,0.01f],translation:[0f,0f,0f]}}',
            'data modify storage gti:tmp msg set value "Runda przerwana."',
            "function gti:visual/event with storage gti:tmp",
            "function gti:internal/hud",
        ]
    )
    f["stop"] = mc(["function gti:internal/stop"])
    f["internal/next"] = mc(
        [
            "execute unless score #state gti.var matches 0 run return run tellraw @s {\"text\":\"Runda trwa. Przerwij ją: /function gti:stop\",\"color\":\"red\"}",
            "tag @s add gti.player",
            "execute at @e[tag=gti.anchor,limit=1] run function gti:internal/start",
        ]
    )

    # -- hints ----------------------------------------------------------
    f["internal/hint_request"] = mc(
        [
            "execute unless score #state gti.var matches 2 run return run tellraw @s {\"text\":\"Podpowiedzi są dostępne w trakcie rundy.\",\"color\":\"gray\"}",
            "execute if score #paused gti.var matches 1 run return run tellraw @s {\"text\":\"Runda jest wstrzymana.\",\"color\":\"yellow\"}",
            "execute if score #hints_enabled gti.var matches 0 run return run tellraw @s {\"text\":\"Podpowiedzi są wyłączone w ustawieniach.\",\"color\":\"yellow\"}",
            "execute if score #hint_stage gti.var matches 3.. run return run tellraw @s {\"text\":\"Wykorzystano wszystkie 3 podpowiedzi w tej rundzie.\",\"color\":\"yellow\"}",
            "scoreboard players add #hint_stage gti.var 1",
            "scoreboard players add #hints_used gti.var 1",
            "scoreboard players add #cost gti.var 8",
            "function gti:internal/hint_text",
            "title @s times 2 30 10",
            'title @s subtitle {"text":"−8 punktów • podpowiedź","color":"gray"}',
            'title @s title {"text":"PODPOWIEDŹ","color":"#F47BC6","bold":true}',
            "execute at @s run playsound minecraft:block.amethyst_block.chime master @s ~ ~ ~ 0.7 1.2",
            "tellraw @s [{\"text\":\"💡 \",\"color\":\"#F47BC6\"},{\"nbt\":\"hint\",\"storage\":\"gti:cfg\",\"color\":\"#F6CF84\"}]",
            "function gti:internal/hud",
            "execute if score #limit gti.var matches 1.. if score #cost gti.var >= #limit gti.var run function gti:internal/lose",
        ]
    )
    f["internal/hint_text"] = mc(
        [
            "execute if score #hint_stage gti.var matches 1 run function gti:internal/hint_cat",
            "execute if score #hint_stage gti.var matches 2 run function gti:internal/hint_len with storage gti:cfg meta",
            "execute if score #hint_stage gti.var matches 3 run function gti:internal/hint_mask with storage gti:cfg meta",
        ]
    )
    f["internal/hint_cat"] = mc(
        [
            f'execute if score #hint_cat gti.var matches {i} run data modify storage gti:cfg hint set value "KATEGORIA: {name}"'
            for i, name in enumerate(CAT_LABELS)
        ]
    )
    f["internal/hint_len"] = mc(
        ['$data modify storage gti:cfg hint set value "DŁUGOŚĆ: $(len) • PIERWSZA LITERA: $(first)"']
    )
    f["internal/hint_mask"] = mc(['$data modify storage gti:cfg hint set value "WZÓR: $(mask)"'])

    # -- summary --------------------------------------------------------
    f["internal/summary"] = mc(
        [
            "execute store result storage gti:tmp round int 1 run scoreboard players get #round gti.var",
            "execute store result storage gti:tmp tries int 1 run scoreboard players get #last_tries gti.var",
            "execute store result storage gti:tmp pixels int 1 run scoreboard players get #last_pixels gti.var",
            "execute store result storage gti:tmp wrong int 1 run scoreboard players get #last_wrong gti.var",
            "execute store result storage gti:tmp secs int 1 run scoreboard players get #last_time gti.var",
            "execute store result storage gti:tmp hints int 1 run scoreboard players get #last_hints gti.var",
            "execute store result storage gti:tmp cost int 1 run scoreboard players get #last_cost gti.var",
            "data modify storage gti:tmp key set from storage gti:cfg answer_key",
            "execute if score #result gti.var matches 1 run function gti:internal/summary_win with storage gti:tmp",
            "execute if score #result gti.var matches 0 run function gti:internal/summary_lose with storage gti:tmp",
        ]
    )
    body = (
        '{type:"minecraft:plain_message",contents:[{text:"Hasło: ",color:"gray"},{translate:"$(key)",color:"gold",bold:true}],width:340},'
        '{type:"minecraft:plain_message",contents:{text:"Próby: $(tries)   •   Błędy: $(wrong)   •   Piksele: $(pixels)/256",color:"white"},width:340},'
        '{type:"minecraft:plain_message",contents:{text:"Czas: $(secs) s   •   Podpowiedzi: $(hints)   •   Koszt: $(cost)",color:"gray"},width:340}'
    )
    actions = (
        '[{label:{text:"▶ Nowa runda",color:"green"},width:170,action:{type:"minecraft:run_command",command:"trigger gti.next set 1"}},'
        '{label:{text:"☰ Menu",color:"aqua"},width:170,action:{type:"minecraft:show_dialog",dialog:"gti:menu"}}]'
    )
    f["internal/summary_win"] = mc(
        [
            f'$dialog show @a[tag=gti.player] {{type:"minecraft:multi_action",title:{{text:"RUNDA $(round) • TRAFIONE",color:"#8BE28B",bold:true}},external_title:{{text:"Guess the item"}},pause:0b,after_action:"close",body:[{body}],inputs:[],columns:2,actions:{actions},exit_action:{{label:{{text:"Zamknij",color:"gray"}},width:200}}}}'
        ]
    )
    f["internal/summary_lose"] = mc(
        [
            f'$dialog show @a[tag=gti.player] {{type:"minecraft:multi_action",title:{{text:"RUNDA $(round) • NIETRAFIONE",color:"#FF8996",bold:true}},external_title:{{text:"Guess the item"}},pause:0b,after_action:"close",body:[{body}],inputs:[],columns:2,actions:{actions},exit_action:{{label:{{text:"Zamknij",color:"gray"}},width:200}}}}'
        ]
    )

    # -- pause ----------------------------------------------------------
    f["ui/pause_click"] = mc(
        [
            "execute unless entity @s[type=player] run return 0",
            "execute unless entity @s[tag=gti.host] run return run tellraw @s {\"text\":\"Pauzę może włączyć gospodarz.\",\"color\":\"red\"}",
            "execute unless score #state gti.var matches 2 run return run tellraw @s {\"text\":\"Pauza działa tylko w trakcie rundy.\",\"color\":\"gray\"}",
            "execute if score #paused gti.var matches 0 run scoreboard players set #paused gti.var 1",
            "execute if score #paused gti.var matches 1 run scoreboard players set #paused gti.var 0",
            "execute if score #paused gti.var matches 1 run tellraw @a[tag=gti.player] {\"text\":\"⏸ Runda wstrzymana.\",\"color\":\"yellow\"}",
            "execute if score #paused gti.var matches 0 run tellraw @a[tag=gti.player] {\"text\":\"▶ Runda wznowiona.\",\"color\":\"green\"}",
            "execute if score #paused gti.var matches 1 run title @a[tag=gti.player] actionbar [{\"text\":\"⏸ PAUZA\",\"color\":\"yellow\",\"bold\":true}]",
            "execute if score #paused gti.var matches 0 run title @a[tag=gti.player] actionbar [{\"text\":\"▶ WZNOWIONO\",\"color\":\"green\",\"bold\":true}]",
            "function gti:internal/hud",
        ]
    )

    # -- modes and presets ---------------------------------------------
    for name, limit in [("chill", 0), ("easy", 160), ("normal", 96), ("hard", 48)]:
        f[f"mode/{name}"] = mc(
            [
                "execute unless score #state gti.var matches 0 run return run tellraw @s {\"text\":\"Zmień tryb między rundami.\",\"color\":\"red\"}",
                f"scoreboard players set #limit gti.var {limit}",
                f'tellraw @a[tag=gti.player] {{"text":"Tryb: {name.upper()} • {limit if limit else "bez limitu"}",color:"#61EDE5"}}',
                "function gti:internal/hud",
            ]
        )
    for name, values in [
        ("chill", {"limit": 0, "mode": 0, "batch": 4, "seconds": 8, "initial": 2, "aliases": 1, "hints": 1}),
        ("normal", {"limit": 96, "mode": 1, "batch": 5, "seconds": 7, "initial": 1, "aliases": 1, "hints": 1}),
        ("hard", {"limit": 48, "mode": 1, "batch": 8, "seconds": 6, "initial": 0, "aliases": 0, "hints": 0}),
    ]:
        f[f"preset/{name}"] = mc(
            [
                "execute unless entity @s[tag=gti.host] run return run tellraw @s {\"text\":\"Tylko gospodarz może zmieniać presety.\",\"color\":\"red\"}",
                "execute unless score #state gti.var matches 0 run return run tellraw @s {\"text\":\"Presety ustawisz między rundami.\",\"color\":\"yellow\"}",
                f"scoreboard players set #limit gti.var {values['limit']}",
                f"scoreboard players set #reveal_mode gti.var {values['mode']}",
                f"scoreboard players set #batch gti.var {values['batch']}",
                f"scoreboard players set #seconds_cfg gti.var {values['seconds']}",
                f"scoreboard players set #initial gti.var {values['initial']}",
                f"scoreboard players set #aliases gti.var {values['aliases']}",
                f"scoreboard players set #hints_enabled gti.var {values['hints']}",
                "scoreboard players operation #interval gti.var = #seconds_cfg gti.var",
                "scoreboard players operation #interval gti.var *= #twenty gti.var",
                f'tellraw @s {{"text":"Preset {name.upper()} zapisany.","color":"#8BE28B"}}',
                "function gti:internal/hud",
            ]
        )

    # -- misc aliases ---------------------------------------------------
    f["help"] = mc(["function gti:ui/menu"])
    f["menu"] = mc(["function gti:ui/menu"])
    f["dialog"] = mc(["function gti:ui/menu"])
    f["dialogue"] = mc(["function gti:ui/menu"])
    f["play"] = mc(["function gti:ui/play"])
    f["stats"] = mc(["function gti:ui/stats"])
    f["settings"] = mc(["function gti:ui/settings"])
    f["host"] = mc(["tag @a remove gti.host", "tag @s add gti.host", "function gti:ui/host"])
    f["random"] = mc(["function gti:ui/random"])
    return f
