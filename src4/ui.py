"""Dialog screens (English) for Guess the Item 4.0."""

from __future__ import annotations

from dataset import CATEGORY_LABELS, CATEGORY_ORDER, CATEGORY_SHORT, grouped
from model import CYAN, MAGENTA, mc

PAGE = 24


def _comp(text: str, color: str = "gray", bold: bool = False) -> dict:
    out = {"text": text, "color": color}
    if bold:
        out["bold"] = True
    return out


def _msg(text: str, color: str = "gray", width: int = 340) -> dict:
    return {"type": "minecraft:plain_message", "contents": {"text": text, "color": color},
            "width": width}


def _rich(parts: list[dict], width: int = 340) -> dict:
    return {"type": "minecraft:plain_message", "contents": parts, "width": width}


def _dialog(title: str, body: list[dict], actions: list[dict], *,
            columns: int = 2, inputs: list[dict] | None = None,
            exit_label: str | None = "Back", exit_dialog: str | None = None) -> dict:
    out: dict = {
        "type": "minecraft:multi_action",
        "title": {"text": title, "color": "aqua", "bold": True},
        "external_title": {"text": "Guess the Item", "color": "aqua"},
        "pause": False,
        "after_action": "close",
        "body": body,
        "inputs": inputs or [],
        "columns": columns,
        "actions": actions,
    }
    if exit_label:
        if exit_dialog:
            out["exit_action"] = {
                "label": {"text": exit_label, "color": "gray"},
                "width": 200,
                "action": {"type": "minecraft:show_dialog", "dialog": exit_dialog},
            }
        else:
            out["exit_action"] = {"label": {"text": exit_label, "color": "gray"}, "width": 200}
    return out


def _action(label: str, color: str, command: str | None = None, dialog: str | None = None,
            width: int = 170, tooltip: str | None = None) -> dict:
    if dialog:
        act: dict = {"type": "minecraft:show_dialog", "dialog": dialog}
    else:
        act = {"type": "minecraft:run_command", "command": command}
    out: dict = {"label": {"text": label, "color": color}, "width": width, "action": act}
    if tooltip:
        out["tooltip"] = {"text": tooltip, "color": "dark_gray"}
    return out


def dialogs(vd: dict) -> dict[str, dict]:
    version = vd["label"]
    count = vd["count"]
    groups = grouped(version)
    out: dict[str, dict] = {}

    # ------------------------------------------------------------------ menu
    out["menu"] = _dialog(
        "GUESS THE ITEM",
        [
            _rich([_comp("BLOCK EDITION  ", "aqua", True),
                   _comp(f"{count} ITEMS  ", "dark_aqua"),
                   _comp(f"MINECRAFT {version}", "dark_aqua")]),
            _msg("Crack the bedrock wall cell by cell to reveal a hidden item icon. "
                 "When you recognise it, hold the item in your main hand and press GUESS."),
            _msg("Fewer attempts is better. Without operator permissions use "
                 "/trigger gti_menu, gti_reveal, gti_guess or gti_hint.", "dark_aqua"),
        ],
        [
            _action("START ROUND", "green", "trigger gti_next set 1", width=205),
            _action("REVEAL CELLS", "aqua", "trigger gti_reveal set 1", width=205),
            _action("GUESS HELD ITEM", "yellow", "trigger gti_guess set 1", width=205),
            _action("HINT", "light_purple", "trigger gti_hint set 1", width=205),
            _action("MY STATS", "gold", "trigger gti_stats set 1", width=205),
            _action("HOST PANEL", "light_purple", dialog="gti:host", width=205),
            _action("ITEM CATALOGUE", "aqua", dialog="gti:catalogue/index", width=205),
            _action("HOW TO PLAY", "gray", dialog="gti:rules", width=205),
        ],
        exit_label="Close",
    )

    # ------------------------------------------------------------------ host
    out["host"] = _dialog(
        "HOST PANEL",
        [
            _msg("Pick the answer and the rules between rounds. Everything here works "
                 "for the host only.", "gold"),
            _msg("The round answers are drawn from the full item pool unless you lock one "
                 "with the held item, the catalogue or a typed id.", "dark_aqua"),
        ],
        [
            _action("START ROUND", "green", "trigger gti_next set 1"),
            _action("STOP ROUND", "red", "trigger gti_stop set 1"),
            _action("ROUND SETTINGS", "aqua", dialog="gti:settings"),
            _action("CATALOGUE", "aqua", dialog="gti:catalogue/index"),
            _action("USE HELD ITEM", "yellow", "trigger gti_hand set 1"),
            _action("RANDOM ANSWER", "light_purple", "trigger gti_random set 1"),
            _action("TYPE AN ITEM ID", "gray", dialog="gti:item_id"),
            _action("GAME MENU", "gray", dialog="gti:menu"),
            _action("PRESET CHILL", "green", "trigger gti_easy set 1"),
            _action("PRESET NORMAL", "gold", "trigger gti_normal set 1"),
            _action("PRESET HARD", "red", "trigger gti_hard set 1"),
            _action("STATS", "yellow", dialog="gti:stats"),
        ],
        exit_label="Back",
        exit_dialog="gti:menu",
    )

    # -------------------------------------------------------------- settings
    out["settings"] = _dialog(
        "ROUND SETTINGS",
        [
            _msg("The limit slider is the maximum number of attempts; the pips above the "
                 "board show it. 0 means unlimited.", "gray"),
            _msg("Mode: MANUAL reveals only on clicks, PEEK uncovers two cells after a "
                 "wrong guess, AUTO reveals a batch every seven seconds.", "dark_aqua"),
        ],
        [
            {
                "label": {"text": "SAVE SETTINGS", "color": "green"},
                "width": 205,
                "action": {
                    "type": "minecraft:dynamic/run_command",
                    "template": "function gti:cfg/apply {limit:$(limit),batch:$(batch),"
                                "initial:$(initial),mode:\"$(mode)\",timer:$(timer),hints:$(hints)}",
                },
                "tooltip": {"text": "Applies every slider at once.", "color": "dark_gray"},
            },
            _action("RESET TO DEFAULTS", "gray", "trigger gti_default set 1", width=205),
            _action("PRESET CHILL", "green", "trigger gti_easy set 1", width=205),
            _action("PRESET NORMAL", "gold", "trigger gti_normal set 1", width=205),
            _action("PRESET HARD", "red", "trigger gti_hard set 1", width=205),
            _action("HOST PANEL", "light_purple", dialog="gti:host", width=205),
        ],
        inputs=[
            {
                "type": "minecraft:number_range",
                "key": "limit",
                "label": {"text": "Max attempts (0 = unlimited)", "color": "gold"},
                "start": 0.0,
                "end": 32.0,
                "step": 1.0,
                "initial": 16.0,
                "width": 220,
            },
            {
                "type": "minecraft:number_range",
                "key": "batch",
                "label": {"text": "Cells per click", "color": "aqua"},
                "start": 1.0,
                "end": 8.0,
                "step": 1.0,
                "initial": 3.0,
                "width": 220,
            },
            {
                "type": "minecraft:number_range",
                "key": "initial",
                "label": {"text": "Free cells at start", "color": "aqua"},
                "start": 0.0,
                "end": 16.0,
                "step": 1.0,
                "initial": 4.0,
                "width": 220,
            },
            {
                "type": "minecraft:number_range",
                "key": "timer",
                "label": {"text": "Time limit in seconds (0 = off)", "color": "red"},
                "start": 0.0,
                "end": 300.0,
                "step": 30.0,
                "initial": 0.0,
                "width": 220,
            },
            {
                "type": "minecraft:single_option",
                "key": "mode",
                "label": {"text": "Reveal mode", "color": "light_purple"},
                "width": 220,
                "options": [
                    {"id": "manual", "display": {"text": "MANUAL", "color": "aqua"}},
                    {"id": "peek", "display": {"text": "PEEK", "color": "gold"}, "initial": True},
                    {"id": "auto", "display": {"text": "AUTO", "color": "green"}},
                ],
            },
            {
                "type": "minecraft:boolean",
                "key": "hints",
                "label": {"text": "Hints enabled", "color": "light_purple"},
                "initial": True,
            },
        ],
        exit_label="Back",
        exit_dialog="gti:host",
    )

    # ----------------------------------------------------------------- rules
    out["rules"] = _dialog(
        "HOW TO PLAY",
        [
            _rich([_comp("GOAL  ", "aqua", True),
                   _comp("Guess the hidden item before your attempts run out.", "white")]),
            _msg("Click or hit a cell to crack that bedrock block and reveal the icon pixels "
                 "under it. Every revealed cell costs one attempt, and the LIMIT strip above "
                 "the wall shows how many are left."),
            _msg("Hold the item you want to name in your MAIN HAND and press GUESS. A wrong "
                 "item costs three attempts."),
            _msg("HINT unlocks three facts: category, then name length and first letter, then "
                 "the name pattern. Each costs two attempts."),
            _msg("Unlimited attempts when the limit is 0. Fewer attempts wins, then fewer "
                 "revealed cells. Variants of the same item (copper and waxed copper, "
                 "stone bricks and infested stone bricks) count as correct.", "dark_aqua"),
        ],
        [
            _action("START ROUND", "green", "trigger gti_next set 1", width=205),
            _action("MENU", "gray", dialog="gti:menu", width=205),
        ],
        exit_label="Back",
        exit_dialog="gti:menu",
    )

    # ----------------------------------------------------------------- stats
    out["stats"] = _dialog(
        "MY STATS",
        [
            _msg("Wins, personal best, streak and rounds are stored in this world's "
                 "scoreboard. Personal best is the fewest attempts used in a solved round."),
            _msg("Round details appear in chat at the end of every round; the host can also "
                 "open the summary dialog.", "dark_aqua"),
        ],
        [
            _action("RESET MY STATS", "red", dialog="gti:stats_confirm"),
            _action("MENU", "gray", dialog="gti:menu"),
        ],
        exit_label="Back",
        exit_dialog="gti:menu",
    )
    out["stats_confirm"] = {
        "type": "minecraft:confirmation",
        "title": {"text": "Reset your stats?", "color": "red", "bold": True},
        "external_title": {"text": "Guess the Item", "color": "aqua"},
        "pause": False,
        "body": [_msg("This clears your wins, personal best, streak and round counter in "
                      "this world.", "gray")],
        "yes": {
            "label": {"text": "Yes, reset", "color": "red"},
            "action": {"type": "minecraft:run_command", "command": "function gti:ui/stats_reset"},
        },
        "no": {"label": {"text": "Keep my stats", "color": "gray"}},
    }

    # --------------------------------------------------------------- item id
    out["item_id"] = _dialog(
        "TYPE AN ITEM ID",
        [
            _msg("Examples: diamond, minecraft:stone, copper_chest, waxed_copper_block. "
                 "You may drop the minecraft: prefix."),
        ],
        [
            {
                "label": {"text": "LOCK THIS ANSWER", "color": "green"},
                "width": 300,
                "action": {
                    "type": "minecraft:dynamic/run_command",
                    "template": "function gti:data/set_id {id:\"$(item)\"}",
                },
            },
        ],
        columns=1,
        inputs=[
            {
                "type": "minecraft:text",
                "key": "item",
                "label": {"text": "Item id", "color": "gold"},
                "initial": "minecraft:diamond",
                "max_length": 100,
                "width": 300,
            }
        ],
        exit_label="Cancel",
        exit_dialog="gti:host",
    )

    # ------------------------------------------------------------- catalogue
    cat_colors = {"blocks": "aqua", "equipment": "gold", "food": "green",
                  "mobs": "light_purple", "materials": "yellow", "other": "red"}
    index_actions = [
        _action(f"ALL ITEMS ({count})", "white", dialog="gti:catalogue/all/0", width=205)
    ]
    for cat in CATEGORY_ORDER:
        index_actions.append(
            _action(f"{CATEGORY_LABELS[cat]} ({len(groups[cat])})", cat_colors[cat],
                    dialog=f"gti:catalogue/{cat}/0", width=205)
        )
    index_actions += [
        _action("TYPE AN ITEM ID", "gray", dialog="gti:item_id", width=205),
        _action("HOST PANEL", "light_purple", dialog="gti:host", width=205),
    ]
    out["catalogue/index"] = _dialog(
        f"CATALOGUE  /  {count} ITEMS",
        [
            _msg("Clicking a name locks it as the answer for the next round. Item ids are "
                 "shown in the tooltip."),
            _msg("Each item belongs to exactly one category.", "dark_aqua"),
        ],
        index_actions,
        exit_label="Back",
        exit_dialog="gti:host",
    )

    def add_pages(cat: str, items: list[dict], start_index: int) -> None:
        pages = max(1, (len(items) + PAGE - 1) // PAGE)
        label = "ALL ITEMS" if cat == "all" else CATEGORY_LABELS[cat]
        for page in range(pages):
            actions = []
            for offset, item in enumerate(items[page * PAGE : (page + 1) * PAGE]):
                idx = page * PAGE + offset
                value = idx + 1 if cat == "all" else 1 + start_index * 10000 + idx
                actions.append({
                    "label": {"translate": item["key"], "color": "white"},
                    "width": 165,
                    "action": {"type": "minecraft:run_command",
                               "command": f"trigger gti_pick set {value}"},
                    "tooltip": {"text": f"{item['id']}  •  {CATEGORY_SHORT[item['cat']]}",
                                "color": "dark_gray"},
                })
            nav = []
            if page > 0:
                nav.append(_action("◀ PREVIOUS", "gray",
                                   dialog=f"gti:catalogue/{cat}/{page-1}", width=165))
            nav.append(_action("CATEGORIES", "aqua", dialog="gti:catalogue/index", width=165))
            if page + 1 < pages:
                nav.append(_action("NEXT ▶", "gray",
                                   dialog=f"gti:catalogue/{cat}/{page+1}", width=165))
            out[f"catalogue/{cat}/{page}"] = _dialog(
                f"{label}  /  {page + 1} of {pages}",
                [_rich([_comp(f"{len(items)} items", "aqua", True),
                        _comp("  •  click to lock the answer", "gray")])],
                actions + nav,
                exit_label="Back",
                exit_dialog="gti:catalogue/index",
            )

    all_items = [item for cat in CATEGORY_ORDER for item in groups[cat]]
    add_pages("all", all_items, 0)
    for cat_index, cat in enumerate(CATEGORY_ORDER, start=1):
        add_pages(cat, groups[cat], cat_index)

    # --------------------------------------------------------------- summary
    out["summary"] = _dialog(
        "ROUND SUMMARY",
        [
            _msg("The answer is on the board and in chat. Start another round whenever "
                 "you are ready.", "gray"),
            _msg("Board cards: attempts used, guesses, hints and time. Personal best is the "
                 "lowest number of attempts in a solved round.", "dark_aqua"),
        ],
        [
            _action("NEW ROUND", "green", "trigger gti_next set 1", width=205),
            _action("HOST PANEL", "light_purple", dialog="gti:host", width=205),
        ],
        exit_label="Close",
    )
    return out


def ui_functions(vd: dict) -> dict[str, str]:
    f: dict[str, str] = {}
    f["ui/menu"] = mc(["dialog show @s gti:menu"])
    f["ui/host"] = mc(["dialog show @s gti:host"])
    f["ui/settings"] = mc(["dialog show @s gti:settings"])
    f["ui/rules"] = mc(["dialog show @s gti:rules"])
    f["ui/stats"] = mc(["dialog show @s gti:stats"])
    f["ui/browse"] = mc(["dialog show @s gti:catalogue/index"])
    f["ui/summary"] = mc(["dialog show @s gti:summary"])
    f["menu"] = mc(["dialog show @s gti:menu"])
    f["help"] = mc(["dialog show @s gti:rules"])
    f["host"] = mc(["dialog show @s gti:host"])
    f["settings"] = mc(["dialog show @s gti:settings"])
    f["stats"] = mc(["dialog show @s gti:stats"])
    return f
