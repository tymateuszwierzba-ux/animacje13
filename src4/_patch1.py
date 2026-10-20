import re

p = 'game.py'
s = open(p).read()

# ---------------------------------------------------------------- intro/tick
old = '''    f["intro/tick"] = mc([
        "scoreboard players add #anim gti.var 1",
        "execute if score #anim gti.var matches 1 run function gti:intro/seal",
        "execute if score #anim gti.var matches 10 run function gti:fx/restore",
        "execute if score #anim gti.var matches 18 run function gti:intro/pick",
        "execute if score #anim gti.var matches 26 run function gti:intro/open",
        "execute if score #anim gti.var matches 54 run function gti:intro/go",
    ])'''
new = '''    # Every step is threshold based and latched with its own flag, so a skipped
    # tick (reload, lag, a second start) can never strand the intro half way.
    f["intro/tick"] = mc([
        "scoreboard players add #anim gti.var 1",
        "execute if score #anim gti.var matches 1.. if score #did_seal gti.var matches 0 run function gti:intro/seal",
        "execute if score #anim gti.var matches 10.. if score #did_restore gti.var matches 0 run function gti:intro/restore",
        "execute if score #anim gti.var matches 18.. if score #did_pick gti.var matches 0 run function gti:intro/pick",
        "execute if score #anim gti.var matches 26.. if score #did_open gti.var matches 0 run function gti:intro/open",
        "execute if score #anim gti.var matches 54.. if score #did_go gti.var matches 0 run function gti:intro/go",
    ])
    f["intro/restore"] = mc([
        "function gti:fx/restore",
        "scoreboard players set #did_restore gti.var 1",
    ])'''
assert old in s
s = s.replace(old, new)

# seal latch
old = '''            "execute at @e[tag=gti.anchor,limit=1] run playsound minecraft:block.deepslate_bricks.place master @a[tag=gti.player] ~ ~ ~ 0.8 0.7",
            'data modify storage gti:cfg status set value "BEDROCK SEALED"',
            "function gti:hud/refresh",
        ]
    )'''
new = '''            "execute at @e[tag=gti.anchor,limit=1] run playsound minecraft:block.deepslate_bricks.place master @a[tag=gti.player] ~ ~ ~ 0.8 0.7",
            'data modify storage gti:cfg status set value "BEDROCK SEALED"',
            "function gti:hud/refresh",
            "scoreboard players set #did_seal gti.var 1",
        ]
    )'''
assert old in s
s = s.replace(old, new)

# pick latch
old = '''        'data modify storage gti:cfg status set value "ANSWER LOCKED"',
        "function gti:hud/refresh",
    ])'''
new = '''        'data modify storage gti:cfg status set value "ANSWER LOCKED"',
        "scoreboard players set #picked gti.var 1",
        "scoreboard players set #did_pick gti.var 1",
        "function gti:hud/refresh",
    ])'''
assert old in s
s = s.replace(old, new)

# open latch
old = '''            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:block minecraft:bedrock ~ ~10.5 ~1.2 9 9 0.2 0.05 200 force @a[tag=gti.player]",
        ]
    )'''
new = '''            "execute at @e[tag=gti.anchor,limit=1] run particle minecraft:block minecraft:bedrock ~ ~10.5 ~1.2 9 9 0.2 0.05 200 force @a[tag=gti.player]",
            "scoreboard players set #did_open gti.var 1",
        ]
    )'''
assert old in s
s = s.replace(old, new)

# go guard + latch
old = '''    f["intro/go"] = mc([
        "scoreboard players set #state gti.var 2",'''
new = '''    f["intro/go"] = mc([
        "execute if score #state gti.var matches 2.. run return 0",
        "execute if score #picked gti.var matches 0 run function gti:intro/pick",
        "scoreboard players set #did_go gti.var 1",
        "scoreboard players set #state gti.var 2",'''
assert old in s
s = s.replace(old, new)

# ---------------------------------------------------------------- finale/tick
old_fin = '''    f["finale/tick"] = mc(
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
    )'''
new_fin = '''    f["finale/tick"] = mc(
        [
            "scoreboard players add #anim gti.var 1",
        ]
        + [
            f"execute if score #anim gti.var matches {2 + 2 * col}.. as @e[tag=gti.cell,tag=gti.col{col}] run function gti:reveal/final"
            for col in range(COLS)
        ]
        + [
            "execute if score #anim gti.var matches 40.. if score #did_confetti gti.var matches 0 run function gti:finale/confetti",
            "execute if score #anim gti.var matches 46.. if score #did_fire gti.var matches 0 if score #result gti.var matches 1 run function gti:finale/fireworks",
            "execute if score #anim gti.var matches 64.. if score #shown gti.var matches 0 run function gti:finale/summary",
            "execute if score #anim gti.var matches 120.. if score #did_end gti.var matches 0 run function gti:finale/end",
            "execute if score #anim gti.var matches 128.. if score #did_end2 gti.var matches 0 run function gti:finale/end2",
            "execute if score #anim gti.var matches 138.. if score #did_end3 gti.var matches 0 run function gti:finale/end3",
        ]
    )
    f["finale/confetti"] = mc([
        "function gti:fx/confetti",
        "scoreboard players set #did_confetti gti.var 1",
    ])
    f["finale/fireworks"] = mc([
        "function gti:fx/fireworks",
        "scoreboard players set #did_fire gti.var 1",
    ])'''
assert old_fin in s
s = s.replace(old_fin, new_fin)

s = s.replace('''    f["finale/end"] = mc([
        "function gti:finale/curtain",''', '''    f["finale/end"] = mc([
        "scoreboard players set #did_end gti.var 1",
        "function gti:finale/curtain",''')
s = s.replace('''    f["finale/end2"] = mc([
        "function gti:fx/restore",''', '''    f["finale/end2"] = mc([
        "scoreboard players set #did_end2 gti.var 1",
        "function gti:fx/restore",''')

open(p, 'w').write(s)
print('intro/finale patched')
