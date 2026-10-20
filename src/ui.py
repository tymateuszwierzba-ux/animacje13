"""Dialog screens and trigger-driven UI functions."""

from __future__ import annotations

import json

from dataset import CATEGORY_LABELS, CATEGORY_ORDER, CATEGORY_SHORT, grouped
from model import CYAN, MAGENTA, mc

PAGE = 24
PER_CHUNK = 200


def _comp(text: str, color: str = "gray", bold: bool = False) -> dict:
    out = {"text": text, "color": color}
    if bold:
        out["bold"] = True
    return out


def _dialog(title: str, body: list[dict], actions: list[dict], *, columns: int = 2,
            exit_label: str = "Zamknij", exit_action: dict | None = None,
            inputs: list[dict] | None = None, subtitle: str | None = None) -> dict:
    out: dict = {
        "type": "minecraft:multi_action",
        "title": {"text": title, "color": "aqua", "bold": True},
        "external_title": {"text": "Guess the item", "color": "aqua"},
        "pause": False,
        "after_action": "close",
        "body": body,
        "inputs": inputs or [],
        "columns": columns,
        "actions": actions,
        "exit_action": {"label": exit_label and {"text": exit_label, "color": "gray"}, "width": 200},
    }
    if subtitle:
        out["external_title"] = {"text": subtitle, "color": "aqua"}
    if exit_action:
        out["exit_action"] = exit_action
    if not exit_label:
        out.pop("exit_action")
    return out


def _msg(text: str, color: str = "gray", width: int = 340) -> dict:
    return {"type": "minecraft:plain_message", "contents": {"text": text, "color": color}, "width": width}


def _rich(parts: list[dict], width: int = 340) -> dict:
    return {"type": "minecraft:plain_message", "contents": parts, "width": width}


def _action(label: str, color: str, command: str | None = None, dialog: str | None = None,
            width: int = 170, tooltip: str | None = None) -> dict:
    if dialog:
        act: dict = {"type": "minecraft:show_dialog", "dialog": dialog}
    else:
        act = {"type": "minecraft:run_command", "command": command}
    out = {"label": {"text": label, "color": color}, "width": width, "action": act}
    if tooltip:
        out["tooltip"] = {"text": tooltip, "color": "dark_gray"}
    return out


def dialogs(vd: dict) -> dict[str, dict]:
    version = vd["label"]
    count = vd["count"]
    groups = grouped(version)
    out: dict[str, dict] = {}

    # ---------------------------------------------------------------- menu
    out["menu"] = _dialog(
        "GUESS THE ITEM",
        [
            _rich([_comp("PIXEL REVEAL  ", "aqua", True), _comp(f"{count} PRZEDMIOTÓW  ", "dark_aqua"),
                   _comp(f"JAVA {version}", "dark_aqua")]),
            _msg("Rozpoznaj przedmiot po fragmentach ikony. Odsłaniaj piksele, "
                 "a gdy będziesz pewien — weź przedmiot do głównej ręki i naciśnij ZGADUJ."),
            _msg("Mniej prób = lepiej. Przy remisie decyduje mniej odkrytych pikseli. "
                 "Menu otworzysz też komendą /trigger gti.menu.", "dark_aqua"),
        ],
        [
            _action("▶  Nowa runda", "green", "trigger gti.next set 1", width=205),
            _action("◆  Odkryj paczkę", "aqua", "trigger gti.pixel set 1", width=205),
            _action("✓  Zgaduj z ręki", "gold", "trigger gti.guess set 1", width=205),
            _action("💡  Podpowiedź", "light_purple", "trigger gti.hint set 1", width=205),
            _action("★  Moje statystyki", "yellow", "trigger gti.stats set 1", width=205),
            _action("⚙  Panel gospodarza", "light_purple", "trigger gti.hostmenu set 1", width=205),
            _action("▦  Katalog przedmiotów", "aqua", "trigger gti.browser set 1", width=205),
            _action("?  Jak grać", "gray", dialog="gti:rules", width=205),
        ],
        exit_label="Wróć do planszy",
    )

    # ---------------------------------------------------------------- host
    out["host"] = _dialog(
        "PANEL GOSPODARZA",
        [
            _msg("Ustawienia i wybór hasła zmieniaj między rundami. "
                 "Formularze i wpisywanie ID wymagają uprawnień operatora.", "gold"),
            _msg("Nowa runda losuje hasło. Aby ustawić własne, użyj katalogu, "
                 "przedmiotu z ręki albo wpisz identyfikator.", "dark_aqua"),
        ],
        [
            _action("▶  Rozpocznij rundę", "green", "trigger gti.next set 1"),
            _action("■  Przerwij rundę", "red", "trigger gti.stop set 1"),
            _action("⚙  Ustawienia rundy", "aqua", "trigger gti.settings set 1"),
            _action("▦  Katalog", "aqua", "trigger gti.browser set 1"),
            _action("↗  Przedmiot z ręki", "yellow", "trigger gti.hand set 1"),
            _action("⟳  Losowy przedmiot", "light_purple", "trigger gti.random set 1"),
            _action("ID  Wpisz identyfikator", "gray", dialog="gti:item_id"),
            _action("☰  Menu gry", "gray", dialog="gti:menu"),
            _action("◈  Preset CHILL", "green", "function gti:preset/chill"),
            _action("◈  Preset NORMAL", "gold", "function gti:preset/normal"),
            _action("◈  Preset HARD", "red", "function gti:preset/hard"),
            _action("↺  Statystyki", "yellow", "trigger gti.stats set 1"),
        ],
        exit_label="Wróć",
        exit_action={"label": {"text": "Menu gry", "color": "gray"}, "width": 200,
                     "action": {"type": "minecraft:show_dialog", "dialog": "gti:menu"}},
    )

    # ------------------------------------------------------------ settings
    out["settings"] = _dialog(
        "USTAWIENIA RUNDY",
        [
            _msg("Suwaki ustawiają paczkę pikseli, budżet punktów i liczbę pól "
                 "odkrywanych na starcie. Zapisz, aby zastosować.", "gray"),
            _msg("Tryb AUTO odkrywa paczkę co kilka sekund. PO BŁĘDZIE — po nietrafionym "
                 "guessie. RĘCZNIE — tylko na kliknięcie.", "dark_aqua"),
        ],
        [
            {
                "label": {"text": "✔  Zapisz ustawienia", "color": "green"},
                "width": 205,
                "action": {
                    "type": "minecraft:dynamic/run_command",
                    "template": "function gti:ui/settings_apply {batch:$(batch),limit:$(limit),mode:\"$(mode)\",initial:$(initial),hints:$(hints)}",
                },
                "tooltip": {"text": "Zastosuje wszystkie suwaki naraz.", "color": "dark_gray"},
            },
            _action("↺  Domyślne", "gray", "function gti:ui/settings_reset", width=205),
            _action("◆  Paczka 1", "aqua", "function gti:ui/batch_set {value:1}", width=205),
            _action("◆  Paczka 5", "aqua", "function gti:ui/batch_set {value:5}", width=205),
            _action("☰  Menu", "gray", dialog="gti:menu", width=205),
            _action("⚙  Panel gospodarza", "light_purple", dialog="gti:host", width=205),
        ],
        columns=2,
        inputs=[
            {
                "type": "minecraft:number_range",
                "key": "batch",
                "label": {"text": "Paczka pikseli", "color": "aqua"},
                "start": 1.0,
                "end": 16.0,
                "step": 1.0,
                "initial": 5.0,
                "width": 220,
            },
            {
                "type": "minecraft:number_range",
                "key": "limit",
                "label": {"text": "Budżet punktów (0 = ∞)", "color": "gold"},
                "start": 0.0,
                "end": 256.0,
                "step": 8.0,
                "initial": 96.0,
                "width": 220,
            },
            {
                "type": "minecraft:single_option",
                "key": "mode",
                "label": {"text": "Tryb odkrywania", "color": "light_purple"},
                "width": 220,
                "options": [
                    {"id": "manual", "display": {"text": "RĘCZNIE", "color": "aqua"}, "initial": True},
                    {"id": "error", "display": {"text": "PO BŁĘDZIE", "color": "gold"}},
                    {"id": "auto", "display": {"text": "AUTO", "color": "green"}},
                ],
            },
            {
                "type": "minecraft:number_range",
                "key": "initial",
                "label": {"text": "Piksele na start", "color": "aqua"},
                "start": 0.0,
                "end": 32.0,
                "step": 1.0,
                "initial": 1.0,
                "width": 220,
            },
            {
                "type": "minecraft:boolean",
                "key": "hints",
                "label": {"text": "Podpowiedzi", "color": "light_purple"},
                "initial": True,
            },
        ],
        exit_label="Wróć",
        exit_action={"label": {"text": "Panel gospodarza", "color": "gray"}, "width": 200,
                     "action": {"type": "minecraft:show_dialog", "dialog": "gti:host"}},
    )

    # --------------------------------------------------------------- rules
    out["rules"] = _dialog(
        "JAK GRAĆ",
        [
            _rich([_comp("CEL  ", "aqua", True),
                   _comp("Odgadnij ukryty przedmiot, zanim wyczerpiesz budżet.", "white")]),
            _msg("Kliknij kafelek, aby odsłonić paczkę pikseli wokół niego. "
                 "Przycisk ODKRYJ wybiera pola losowo. Każdy piksel kosztuje 1 punkt.", "gray"),
            _msg("Aby zgadnąć, weź przedmiot do GŁÓWNEJ ręki i naciśnij ZGADUJ "
                 "(lub /trigger gti.guess set 1). Zła odpowiedź kosztuje 4 punkty.", "gray"),
            _msg("PODPOWIEDŹ odsłania kategorię, potem długość i pierwszą literę, "
                 "a na końcu wzór nazwy. Każda kosztuje 8 punktów.", "gray"),
            _msg("Budżet 0 oznacza brak limitu. Wygrywa mniej prób; przy remisie mniej pikseli. "
                 "Hasła z tej samej grupy (np. miedź i wosk) są uznawane za poprawne.", "dark_aqua"),
        ],
        [
            _action("▶  Gramy", "green", "trigger gti.next set 1", width=205),
            _action("☰  Menu", "gray", dialog="gti:menu", width=205),
        ],
        exit_label="Wróć",
        exit_action={"label": {"text": "Menu", "color": "gray"}, "width": 200,
                     "action": {"type": "minecraft:show_dialog", "dialog": "gti:menu"}},
    )

    # --------------------------------------------------------------- stats
    out["stats"] = _dialog(
        "MOJE STATYSTYKI",
        [
            _msg("Wygrane, rekord, seria i liczba prób są zapisywane w scoreboardach "
                 "tego świata. Rekord to próby × 1000 + piksele — mniej znaczy lepiej.", "gray"),
            _msg("Podsumowanie ostatniej rundy otworzysz z panelu lub komendą "
                 "/trigger gti.summary set 1.", "dark_aqua"),
        ],
        [
            _action("↺  Reset moich statystyk", "red", dialog="gti:stats_confirm"),
            _action("☰  Menu", "gray", dialog="gti:menu"),
        ],
        exit_label="Wróć",
        exit_action={"label": {"text": "Menu", "color": "gray"}, "width": 200,
                     "action": {"type": "minecraft:show_dialog", "dialog": "gti:menu"}},
    )
    out["stats_confirm"] = {
        "type": "minecraft:confirmation",
        "title": {"text": "Zresetować statystyki?", "color": "red", "bold": True},
        "external_title": {"text": "Guess the item", "color": "aqua"},
        "pause": False,
        "body": [_msg("Usunie to Twoje wygrane, rekord, serię i licznik prób w tym świecie.", "gray")],
        "yes": {
            "label": {"text": "Tak, resetuj", "color": "red"},
            "action": {"type": "minecraft:run_command", "command": "function gti:ui/stats_reset"},
        },
        "no": {"label": {"text": "Nie", "color": "gray"}},
    }

    # ----------------------------------------------------------- item ID
    out["item_id"] = _dialog(
        "WPISZ IDENTYFIKATOR",
        [
            _msg("Przykłady: diamond, minecraft:stone, copper_chest, waxed_copper_block. "
                 "Można pominąć minecraft:. Wymaga uprawnień operatora.", "gray"),
        ],
        [
            {
                "label": {"text": "✔  Zapisz hasło", "color": "green"},
                "width": 300,
                "action": {
                    "type": "minecraft:dynamic/run_command",
                    "template": "function gti:ui/set_id {id:\"$(item)\"}",
                },
            },
        ],
        columns=1,
        inputs=[
            {
                "type": "minecraft:text",
                "key": "item",
                "label": {"text": "Identyfikator", "color": "gold"},
                "initial": "diamond",
                "max_length": 100,
                "width": 300,
            }
        ],
        exit_label="Anuluj",
        exit_action={"label": {"text": "Panel gospodarza", "color": "gray"}, "width": 200,
                     "action": {"type": "minecraft:show_dialog", "dialog": "gti:host"}},
    )

    # ----------------------------------------------------------- catalogue
    cat_colors = {"blocks": "aqua", "equipment": "gold", "food": "green",
                  "mobs": "light_purple", "materials": "yellow", "other": "red"}
    index_actions = [
        _action(f"Wszystkie ({count})", "white", dialog="gti:catalogue/all/0", width=205)
    ]
    for cat in CATEGORY_ORDER:
        index_actions.append(
            _action(f"{CATEGORY_LABELS[cat]} ({len(groups[cat])})", cat_colors[cat],
                    dialog=f"gti:catalogue/{cat}/0", width=205)
        )
    index_actions += [
        _action("ID  Wpisz identyfikator", "gray", dialog="gti:item_id", width=205),
        _action("⚙  Panel gospodarza", "light_purple", dialog="gti:host", width=205),
    ]
    out["catalogue/index"] = _dialog(
        f"KATALOG  /  {count} PRZEDMIOTÓW",
        [
            _msg("Kliknięcie nazwy ustawia stałe hasło dla następnej rundy. "
                 "Nazwy są tłumaczone przez klienta, identyfikator znajdziesz w podpowiedzi.", "gray"),
            _msg("Kategorie są rozłączne — każdy przedmiot występuje dokładnie raz.", "dark_aqua"),
        ],
        index_actions,
        exit_label="Wróć",
        exit_action={"label": {"text": "Panel gospodarza", "color": "gray"}, "width": 200,
                     "action": {"type": "minecraft:show_dialog", "dialog": "gti:host"}},
    )

    def add_pages(cat: str, items: list[dict], start_index: int) -> None:
        pages = max(1, (len(items) + PAGE - 1) // PAGE)
        label = "WSZYSTKIE" if cat == "all" else CATEGORY_LABELS[cat]
        for page in range(pages):
            actions = []
            for offset, item in enumerate(items[page * PAGE : (page + 1) * PAGE]):
                idx = page * PAGE + offset
                value = idx + 1 if cat == "all" else 1 + start_index * 10000 + idx
                actions.append({
                    "label": {"translate": item["key"], "color": "white"},
                    "width": 165,
                    "action": {"type": "minecraft:run_command",
                               "command": f"trigger gti.pick set {value}"},
                    "tooltip": {"text": f"{item['id']}  •  {CATEGORY_SHORT[item['cat']]}", "color": "dark_gray"},
                })
            nav = []
            if page > 0:
                nav.append(_action("◀ Poprzednia", "gray", dialog=f"gti:catalogue/{cat}/{page-1}", width=165))
            nav.append(_action("▦ Kategorie", "aqua", dialog="gti:catalogue/index", width=165))
            if page + 1 < pages:
                nav.append(_action("Następna ▶", "gray", dialog=f"gti:catalogue/{cat}/{page+1}", width=165))
            out[f"catalogue/{cat}/{page}"] = _dialog(
                f"{label}  /  {page + 1} z {pages}",
                [_rich([_comp(f"{len(items)} przedmiotów", "aqua", True),
                        _comp("  •  wybierz hasło", "gray")])],
                actions + nav,
                exit_label="Wróć",
                exit_action={"label": {"text": "Kategorie", "color": "gray"}, "width": 200,
                             "action": {"type": "minecraft:show_dialog", "dialog": "gti:catalogue/index"}},
            )

    # all-items list must follow the same order as the storage array
    all_items = []
    for cat in CATEGORY_ORDER:
        all_items.extend(groups[cat])
    # cat == 'all' uses start_index 0
    add_pages("all", all_items, 0)
    for cat_index, cat in enumerate(CATEGORY_ORDER, start=1):
        add_pages(cat, groups[cat], cat_index)

    # ------------------------------------------------------------ summary
    out["summary"] = _dialog(
        "PODSUMOWANIE RUNDY",
        [
            _msg("Szczegółowe podsumowanie pojawia się automatycznie po zakończeniu rundy.", "gray"),
        ],
        [
            _action("▶  Nowa runda", "green", "trigger gti.next set 1", width=205),
            _action("☰  Menu", "gray", dialog="gti:menu", width=205),
        ],
        exit_label="Zamknij",
    )

    return out


def catalogue_functions(vd: dict) -> dict[str, str]:
    groups = grouped(vd["label"])
    f: dict[str, str] = {}
    names = ["all"] + CATEGORY_ORDER
    for cat in names:
        items = (
            [item for c in CATEGORY_ORDER for item in groups[c]]
            if cat == "all" else groups[cat]
        )
        f[f"ui/cat/{cat}"] = mc(["data modify storage gti:cat " + cat + " set value []"])
        chunks = [items[i : i + PER_CHUNK] for i in range(0, len(items), PER_CHUNK)]
        for ci, chunk in enumerate(chunks):
            f[f"ui/cat/{cat}/{ci}"] = mc(
                [f'data modify storage gti:cat {cat} append value "{item["id"]}"' for item in chunk]
            )
        f[f"ui/cat/{cat}/init"] = mc(
            [f"function gti:ui/cat/{cat}"] + [f"function gti:ui/cat/{cat}/{ci}" for ci in range(len(chunks))]
        )
    return f


def ui_functions(vd: dict) -> dict[str, str]:
    f: dict[str, str] = {}
    f.update(catalogue_functions(vd))

    f["ui/cat_init"] = mc([f"function gti:ui/cat/{cat}/init" for cat in ["all", "blocks", "equipment", "food", "mobs", "materials", "other"]])
    f["ui/menu"] = mc(["dialog show @s gti:menu"])
    f["ui/host"] = mc(["dialog show @s gti:host"])
    f["ui/settings"] = mc(["dialog show @s gti:settings"])
    f["ui/browser"] = mc(["dialog show @s gti:catalogue/index"])
    f["ui/stats"] = mc(["dialog show @s gti:stats"])
    f["ui/summary"] = mc(
        [
            "execute if score #summary_ready gti.var matches 1 run function gti:internal/summary",
            "execute unless score #summary_ready gti.var matches 1 run dialog show @s gti:summary",
        ]
    )
    f["ui/rules"] = mc(["dialog show @s gti:rules"])

    f["ui/play"] = mc(
        [
            "execute unless score #state gti.var matches 0 run return run tellraw @s {\"text\":\"Runda trwa.\",\"color\":\"gray\"}",
            "execute in minecraft:overworld unless entity @e[tag=gti.anchor] run return run tellraw @s {\"text\":\"Brak planszy — /function gti:setup\",\"color\":\"red\"}",
            "tag @s add gti.player",
            "function gti:internal/start",
        ]
    )

    f["ui/random"] = mc(
        [
            "execute unless entity @s[tag=gti.host] run return run tellraw @s {\"text\":\"Tylko gospodarz wybiera hasło.\",\"color\":\"red\"}",
            "execute unless score #state gti.var matches 0 run return run tellraw @s {\"text\":\"Hasło zmienisz między rundami.\",\"color\":\"yellow\"}",
            "scoreboard players set #source gti.var 0",
            'data modify storage gti:tmp msg set value "Hasło: losowane z pełnej puli."',
            "function gti:visual/event with storage gti:tmp",
            "tellraw @s {\"text\":\"✔ Hasło będzie losowane.\",\"color\":\"green\"}",
        ]
    )

    f["ui/hand"] = mc(
        [
            "execute unless entity @s[tag=gti.host] run return run tellraw @s {\"text\":\"Tylko gospodarz wybiera hasło.\",\"color\":\"red\"}",
            "execute unless score #state gti.var matches 0 run return run tellraw @s {\"text\":\"Hasło zmienisz między rundami.\",\"color\":\"yellow\"}",
            "execute unless items entity @s weapon.mainhand #gti:answers run return run tellraw @s {\"text\":\"Trzymaj obsługiwany przedmiot w głównej ręce.\",\"color\":\"yellow\"}",
            "data modify storage gti:tmp id set from entity @s SelectedItem.id",
            "data modify storage gti:tmp manual set value 1b",
            "function gti:data/set_fixed",
        ]
    )

    f["ui/pick"] = mc(
        [
            "execute unless score #state gti.var matches 0 run return run tellraw @s {\"text\":\"Hasło zmienisz między rundami.\",\"color\":\"yellow\"}",
            "scoreboard players operation #pick gti.var = @s gti.pick",
            "scoreboard players remove #pick gti.var 1",
            "scoreboard players operation #cat gti.var = #pick gti.var",
            "scoreboard players operation #cat gti.var /= #tenk gti.var",
            "scoreboard players operation #idx gti.var = #pick gti.var",
            "scoreboard players operation #idx gti.var %= #tenk gti.var",
            "execute store result storage gti:tmp index int 1 run scoreboard players get #idx gti.var",
            'data modify storage gti:tmp cat set value "all"',
            'execute if score #cat gti.var matches 1 run data modify storage gti:tmp cat set value "blocks"',
            'execute if score #cat gti.var matches 2 run data modify storage gti:tmp cat set value "equipment"',
            'execute if score #cat gti.var matches 3 run data modify storage gti:tmp cat set value "food"',
            'execute if score #cat gti.var matches 4 run data modify storage gti:tmp cat set value "mobs"',
            'execute if score #cat gti.var matches 5 run data modify storage gti:tmp cat set value "materials"',
            'execute if score #cat gti.var matches 6 run data modify storage gti:tmp cat set value "other"',
            "execute unless data storage gti:cat all run function gti:ui/cat/all/init",
            "function gti:ui/pick_lookup with storage gti:tmp",
            "data modify storage gti:tmp manual set value 0b",
            "function gti:data/set_fixed",
            "dialog clear @s",
        ]
    )
    f["ui/pick_lookup"] = mc(
        ['$data modify storage gti:tmp id set from storage gti:cat.$(cat)[$(index)]']
    )

    f["ui/set_id"] = mc(
        [
            "execute unless entity @s[tag=gti.host] run return run tellraw @s {\"text\":\"Tylko gospodarz wybiera hasło.\",\"color\":\"red\"}",
            "execute unless score #state gti.var matches 0 run return run tellraw @s {\"text\":\"Hasło zmienisz między rundami.\",\"color\":\"yellow\"}",
            "data remove storage gti:tmp id",
            '$execute if data storage gti:items by_id."$(id)" run data modify storage gti:tmp id set value "$(id)"',
            '$execute if data storage gti:items by_id."minecraft:$(id)" run data modify storage gti:tmp id set value "minecraft:$(id)"',
            "execute unless data storage gti:tmp id run return run tellraw @s {\"text\":\"Nieznany identyfikator. Użyj np. diamond lub minecraft:stone.\",\"color\":\"red\"}",
            'data modify storage gti:tmp manual set value 0b',
            "function gti:data/set_fixed",
            "dialog clear @s",
        ]
    )

    f["ui/stats_reset"] = mc(
        [
            "scoreboard players set @s gti.wins 0",
            "scoreboard players set @s gti.best 0",
            "scoreboard players set @s gti.streak 0",
            "scoreboard players set @s gti.best_streak 0",
            "scoreboard players set @s gti.rounds 0",
            "scoreboard players set @s gti.tries 0",
            "scoreboard players set @s gti.clicks 0",
            "tellraw @s {\"text\":\"✔ Statystyki wyzerowane.\",\"color\":\"green\"}",
        ]
    )

    f["ui/batch_set"] = mc(
        ['$scoreboard players set #batch gti.var $(value)', "function gti:internal/hud"]
    )

    f["ui/settings_apply"] = mc(
        [
            '$data modify storage gti:tmp args set value {batch:$(batch),limit:$(limit),mode:"$(mode)",initial:$(initial),hints:$(hints)}',
            "execute store result score #batch gti.var run data get storage gti:tmp args.batch",
            "execute store result score #limit gti.var run data get storage gti:tmp args.limit",
            "execute store result score #initial gti.var run data get storage gti:tmp args.initial",
            "execute if score #batch gti.var matches ..0 run scoreboard players set #batch gti.var 1",
            "execute if score #batch gti.var matches 17.. run scoreboard players set #batch gti.var 16",
            "execute if score #initial gti.var matches ..-1 run scoreboard players set #initial gti.var 0",
            "execute if score #initial gti.var matches 33.. run scoreboard players set #initial gti.var 32",
            "execute if score #limit gti.var matches ..-1 run scoreboard players set #limit gti.var 0",
            "scoreboard players set #reveal_mode gti.var 0",
            'execute if data storage gti:tmp args {mode:"error"} run scoreboard players set #reveal_mode gti.var 1',
            'execute if data storage gti:tmp args {mode:"auto"} run scoreboard players set #reveal_mode gti.var 2',
            "scoreboard players set #hints_enabled gti.var 0",
            "execute if data storage gti:tmp args {hints:1b} run scoreboard players set #hints_enabled gti.var 1",
            "scoreboard players operation #interval gti.var = #seconds_cfg gti.var",
            "scoreboard players operation #interval gti.var *= #twenty gti.var",
            "tellraw @s {\"text\":\"✔ Ustawienia zapisane.\",\"color\":\"green\"}",
            "function gti:internal/hud",
        ]
    )
    f["ui/settings_reset"] = mc(
        [
            "function gti:internal/defaults",
            "scoreboard players operation #interval gti.var = #seconds_cfg gti.var",
            "scoreboard players operation #interval gti.var *= #twenty gti.var",
            "tellraw @s {\"text\":\"✔ Przywrócono ustawienia domyślne.\",\"color\":\"green\"}",
            "function gti:internal/hud",
        ]
    )

    f["ui/actionbar"] = mc(
        [
            "execute unless score #state gti.var matches 2..3 run return 0",
            'title @a[tag=gti.player] actionbar [{"text":"PRÓBY ","color":"gray"},{"score":{"name":"#guesses","objective":"gti.var"},"color":"gold","bold":true},{"text":"   ◆ ","color":"dark_gray"},{"text":"PIKSELE ","color":"gray"},{"score":{"name":"#pixels","objective":"gti.var"},"color":"aqua","bold":true},{"text":"/256","color":"dark_aqua"},{"text":"   ◆ ","color":"dark_gray"},{"text":"CZAS ","color":"gray"},{"score":{"name":"#mins","objective":"gti.var"},"color":"white"},{"text":":"},{"score":{"name":"#secs","objective":"gti.var"},"color":"white"}]',
            "execute if score #paused gti.var matches 1 run title @a[tag=gti.player] actionbar [{\"text\":\"⏸ PAUZA\",\"color\":\"yellow\",\"bold\":true}]",
        ]
    )
    return f
