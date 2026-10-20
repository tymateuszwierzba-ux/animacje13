# GUESS THE ITEM 4.0 — block wall, bedrock shield, max-attempt strip (Minecraft Java)

A datapack minigame: a hidden item icon is buried in a **wall of bedrock blocks**. Carve
cells out of the wall, one coloured block at a time, until you can recognise the icon — then
hold the item and guess.

- **The board is made of blocks.** Every one of the 256 cells is real `bedrock`; revealing a
  cell swaps it for the concrete block matching that pixel of the item texture. No fake grid,
  no floating pictures — a wall you can look at from any angle.
- **The answer is hidden behind bedrock.** The icon sits on the wall, the bedrock curtain
  seals the front, and it opens only for the cells you have earned.
- **A hotbar-style strip above the wall is the max-attempt counter.** It appears only when a
  limit is set, and drains pip by pip as the round is played.
- **All text is English**, and dialog ids use the namespace form: `gti:menu`, not `gti.menu`.

No mods, no resource pack, no plugins — commands and display entities only.

## Three packs in this repository

| ZIP | Minecraft | `pack_format` | Items | Blocks | Gear | Food | Mobs | Materials | Other |
|---|---|---|---|---|---|---|---|---|---|
| `Guess_the_item_1.21.11_v4.zip` | 1.21.11 | 94.1 | **1504** | 1002 | 95 | 52 | 93 | 79 | 183 |
| `Guess_the_item_26.2_v4.zip` | 26.2 | 107.1 | **1536** | 1031 | 95 | 52 | 94 | 79 | 185 |
| `Guess_the_item_26.3_v4.zip` | 26.3 | 121.0 | **1657** | 1134 | 95 | 52 | 94 | 79 | 203 |

Each ZIP is standalone — install exactly one, matching your game version.
The 3.0 packs (`*_v3.zip`) and the 2.0 pack stay in the repository for comparison.

## Install

1. Drop the ZIP **without unpacking** into:
   - single player: `.minecraft/saves/WORLD_NAME/datapacks/`
   - server: `WORLD_NAME/datapacks/`
2. In game, as an operator: `/reload`
3. Stand on flat open ground in the **Overworld** and run `/function gti:setup`.
   The wall is built 30 blocks north of you and the camera turns to face it.
4. Open the host panel (**MENU → HOST PANEL** or `/function gti:host`), pick an item or leave
   it random, adjust the settings, then **START ROUND**.

`/function gti:remove` removes the board and every effect, `/function gti:view` re-centres the
camera, `/function gti:start` starts a round without clicking through the menu.

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

Dialog ids use the namespace form (`gti:menu`, `gti:host`, …); trigger objectives use
underscores (`gti_menu`, `gti_next`, …), so there is no dot/colon mix-up.

## The LIMIT strip

Above the wall sits a strip of 32 sockets. It is the **maximum attempt counter**:

- it appears only when a limit is configured (`Max attempts` in the settings, `0` = unlimited),
- each revealed cell costs 1 attempt, a wrong guess 3, a hint 2,
- the pips stay lime, then turn yellow, orange and red as the budget drains,
- when the last pip is spent the round ends and the answer is revealed.

## GUI

| Dialog | Contents |
|---|---|
| `gti:menu` | start, reveal, guess, hint, stats, host panel, catalogue, rules |
| `gti:host` | start/stop, settings, catalogue, held item, random answer, typed id, presets, stats |
| `gti:settings` | max attempts, cells per click, free cells, time limit, reveal mode, hints |
| `gti:rules` | short rules and scoring |
| `gti:stats` | personal stats and reset |
| `gti:item_id` | type any item id as the answer |
| `gti:catalogue/index` + `gti:catalogue/<category>/<page>` | every item id, 24 per page |
| `gti:summary` | end-of-round summary |

Settings and the item id field are real dialog inputs: the values are interpolated into
`/function gti:cfg/apply` and `/function gti:data/set_id` macros.

## Scoring

- revealed cell **1 attempt**, wrong guess **3 attempts**, hint **2 attempts**,
- the answer may also be a variant of the item (copper vs waxed copper, stone bricks vs
  infested stone bricks) — 67 equivalence groups are included,
- unlimited mode (limit `0`) still tracks attempts for the personal best,
- personal best = fewest attempts in a solved round, stored as attempts + 1 so a flawless
  round (`0` attempts) is still recorded.

## What is in the pack

```
pack.mcmeta                   pack metadata (min/max format)
pack.png                      generated 128×128 icon
README_EN.md                  this readme, embedded in every pack
ITEM_LIST.txt                 every id with its English name
data/gti/function/            logic, animations, art data, world build
data/gti/dialog/              dialogs (menu, host, settings, catalogue, …)
data/gti/tags/item/           answer tags + 67 equivalence tags
data/minecraft/tags/function  load + tick
```

## Building from source

The generators live in `src4/` (4.0) and `src/` (3.0). All textures are baked into command
data — no downloads at runtime.

```bash
cd src4
python3 build.py       # writes Guess_the_item_<version>_v4.zip and build4/<version>/
python3 validate.py    # static checks: JSON, macros, function/dialog references
python3 smoke.py       # headless play-through against build4/26.2
```

`mecha` can verify the generated functions against a vanilla command tree:

```bash
cd build4/26.2 && mecha . -m 1.21
```

## Notes

- Build the board in the **Overworld**; the pack refuses other dimensions.
- `/function gti:setup` needs operator rights. Players without OP can use the wall console and
  the `/trigger gti_*` objectives.
- The board wants a flat area with roughly 30 blocks of free space in front of the wall.
- A partial reveal is intentional: the uncracked cells stay bedrock even after the answer is
  shown, so the picture tears itself out of the rock.
