p = 'game.py'
s = open(p).read()

# ---------------------------------------------------------- watchdog in tick
old = '''    f["tick/world"] = mc([
        "execute if score #state gti.var matches 1 run function gti:intro/tick",
        "execute if score #state gti.var matches 2 run function gti:round/tick",
        "execute if score #state gti.var matches 3 run function gti:finale/tick",'''
new = '''    f["tick/world"] = mc([
        "execute if score #state gti.var matches 1 run function gti:intro/tick",
        "execute if score #state gti.var matches 2 run function gti:round/tick",
        "execute if score #state gti.var matches 3 run function gti:finale/tick",
        # watchdogs: if an intro or finale ever stops making progress, finish it
        "execute if score #state gti.var matches 1 run scoreboard players add #g_intro gti.var 1",
        "execute unless score #state gti.var matches 1 run scoreboard players set #g_intro gti.var 0",
        "execute if score #state gti.var matches 1 if score #g_intro gti.var matches 110.. run function gti:intro/go",
        "execute if score #state gti.var matches 3 run scoreboard players add #g_fin gti.var 1",
        "execute unless score #state gti.var matches 3 run scoreboard players set #g_fin gti.var 0",
        "execute if score #state gti.var matches 3 if score #g_fin gti.var matches 240.. run function gti:finale/end3",'''
assert old in s
s = s.replace(old, new)

# --------------------------------------------------------------- round/abort
old = '''    f["round/abort"] = mc([
        "scoreboard players set #state gti.var 0",
        "scoreboard players set #result gti.var 2",
        "function gti:round/reset",'''
new = '''    f["round/abort"] = mc([
        "scoreboard players set #state gti.var 0",
        "scoreboard players set #result gti.var 2",
        "scoreboard players set #anim gti.var 0",
        "scoreboard players set #picked gti.var 0",
        "scoreboard players set #shown gti.var 0",
        "scoreboard players set #g_intro gti.var 0",
        "scoreboard players set #g_fin gti.var 0",
        "scoreboard players set #did_seal gti.var 0",
        "scoreboard players set #did_restore gti.var 0",
        "scoreboard players set #did_pick gti.var 0",
        "scoreboard players set #did_open gti.var 0",
        "scoreboard players set #did_go gti.var 0",
        "scoreboard players set #did_confetti gti.var 0",
        "scoreboard players set #did_fire gti.var 0",
        "scoreboard players set #did_end gti.var 0",
        "scoreboard players set #did_end2 gti.var 0",
        "scoreboard players set #did_end3 gti.var 0",
        "function gti:round/reset",'''
assert old in s
s = s.replace(old, new)

# ------------------------------------------------------------------- start
old = '''    f["start"] = mc([
        "execute if score #state gti.var matches 2..3 run return run tellraw @s {\\"text\\":\\"A round is already running.\\",\\"color\\":\\"yellow\\"}",
        "execute unless entity @e[tag=gti.anchor,limit=1] run return run tellraw @s {\\"text\\":\\"Build the board first: /function gti:setup\\",\\"color\\":\\"red\\"}",
        "function gti:round/reset",
        "scoreboard players set #state gti.var 1",
        "scoreboard players set #anim gti.var 0",'''
new = '''    f["start"] = mc([
        "execute unless entity @e[tag=gti.anchor,limit=1] run return run tellraw @s {\\"text\\":\\"Build the board first: /function gti:setup\\",\\"color\\":\\"red\\"}",
        # pressing START while a round is stuck simply restarts it
        "execute if score #state gti.var matches 1.. run function gti:round/abort",
        "function gti:round/reset",
        "scoreboard players set #state gti.var 1",
        "scoreboard players set #anim gti.var 0",
        "scoreboard players set #picked gti.var 0",
        "scoreboard players set #shown gti.var 0",
        "scoreboard players set #g_intro gti.var 0",
        "scoreboard players set #g_fin gti.var 0",
        "scoreboard players set #did_seal gti.var 0",
        "scoreboard players set #did_restore gti.var 0",
        "scoreboard players set #did_pick gti.var 0",
        "scoreboard players set #did_open gti.var 0",
        "scoreboard players set #did_go gti.var 0",
        "scoreboard players set #did_confetti gti.var 0",
        "scoreboard players set #did_fire gti.var 0",
        "scoreboard players set #did_end gti.var 0",
        "scoreboard players set #did_end2 gti.var 0",
        "scoreboard players set #did_end3 gti.var 0",'''
assert old in s
s = s.replace(old, new)

# ------------------------------------------------------------------- setup
old = '''        "scoreboard players set #hint_stage gti.var 0",
        'data modify storage gti:cfg status set value "PRESS START"',
        'data modify storage gti:cfg hint set value "NO HINT YET"',
        "function gti:strip/refresh",'''
new = '''        "scoreboard players set #hint_stage gti.var 0",
        "scoreboard players set #anim gti.var 0",
        "scoreboard players set #picked gti.var 0",
        "scoreboard players set #shown gti.var 0",
        "scoreboard players set #g_intro gti.var 0",
        "scoreboard players set #g_fin gti.var 0",
        "scoreboard players set #did_seal gti.var 0",
        "scoreboard players set #did_restore gti.var 0",
        "scoreboard players set #did_pick gti.var 0",
        "scoreboard players set #did_open gti.var 0",
        "scoreboard players set #did_go gti.var 0",
        "scoreboard players set #did_confetti gti.var 0",
        "scoreboard players set #did_fire gti.var 0",
        "scoreboard players set #did_end gti.var 0",
        "scoreboard players set #did_end2 gti.var 0",
        "scoreboard players set #did_end3 gti.var 0",
        'data modify storage gti:cfg status set value "PRESS START"',
        'data modify storage gti:cfg hint set value "NO HINT YET"',
        "function gti:strip/refresh",'''
assert old in s
s = s.replace(old, new)

# ---------------------------------------------------------------- fix/repair
old = '''    f["menu"] = mc(["dialog show @s gti:menu"])'''
new = '''    # /function gti:fix - rebuild the wall in place and clear any leftover state
    f["fix"] = mc([
        'execute unless entity @e[tag=gti.anchor,limit=1] run return run tellraw @s {"text":"No board here - run /function gti:setup first.","color":"red"}',
        "execute at @e[tag=gti.anchor,limit=1] run function gti:fix/at",
    ])
    f["fix/at"] = mc([
        "function gti:remove",
        "execute align xyz positioned ~ ~ ~ run function gti:world/build",
        "scoreboard players set #state gti.var 0",
        "scoreboard players set #result gti.var 2",
        "scoreboard players set #anim gti.var 0",
        "scoreboard players set #picked gti.var 0",
        "scoreboard players set #shown gti.var 0",
        "scoreboard players set #g_intro gti.var 0",
        "scoreboard players set #g_fin gti.var 0",
        "scoreboard players set #did_seal gti.var 0",
        "scoreboard players set #did_restore gti.var 0",
        "scoreboard players set #did_pick gti.var 0",
        "scoreboard players set #did_open gti.var 0",
        "scoreboard players set #did_go gti.var 0",
        "scoreboard players set #did_confetti gti.var 0",
        "scoreboard players set #did_fire gti.var 0",
        "scoreboard players set #did_end gti.var 0",
        "scoreboard players set #did_end2 gti.var 0",
        "scoreboard players set #did_end3 gti.var 0",
        "scoreboard players set #used gti.var 0",
        "scoreboard players set #revealed gti.var 0",
        "scoreboard players set #hint_stage gti.var 0",
        "tag @a remove gti.player",
        "tag @a remove gti.host",
        "tag @s add gti.player",
        "tag @s add gti.host",
        "function gti:round/reset",
        "function gti:fx/restore",
        "function gti:fx/curtain_open",
        "function gti:strip/refresh",
        "function gti:hud/refresh",
        'data modify storage gti:cfg status set value "PRESS START"',
        'data modify storage gti:cfg hint set value "NO HINT YET"',
        'tellraw @s [{"text":"Board repaired. ","color":"#8BE28B"},{"text":"Press START ROUND in the menu.","color":"gray"}]',
        "dialog show @s gti:menu",
    ])

    f["menu"] = mc(["dialog show @s gti:menu"])'''
assert old in s
s = s.replace(old, new)

open(p, 'w').write(s)
print('watchdog + start/stop/setup + fix patched')
