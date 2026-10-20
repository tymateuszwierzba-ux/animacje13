"""Assemble the three datapack zips."""

from __future__ import annotations

import json
import struct
import zipfile
import zlib
from pathlib import Path

import game
import ui
from dataset import CATEGORY_LABELS, CATEGORY_ORDER, version_data
from model import VERSIONS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT
BUILD = ROOT / "build"

DESCRIPTION = {
    "1.21.11": "Guess the Item 3.0 • 1504 przedmioty • holo-plansza • dialog GUI • Java 1.21.11",
    "26.2": "Guess the Item 3.0 • 1536 przedmiotów • holo-plansza • dialog GUI • Java 26.2",
    "26.3": "Guess the Item 3.0 • 1657 przedmiotów • holo-plansza • dialog GUI • Java 26.3",
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
    """128x128 pack icon: dark card, gradient frame and a question mark."""
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
    # outer gradient frame
    for i in range(10):
        c = lerp(cyan, magenta, i / 9) + (255,)
        rect(4 + i, 4 + i, w - 4 - i, 5 + i, c)
        rect(4 + i, h - 5 - i, w - 4 - i, h - 4 - i, c)
        rect(4 + i, 4 + i, 5 + i, h - 4 - i, c)
        rect(w - 5 - i, 4 + i, w - 4 - i, h - 4 - i, c)
    # inner panel
    rect(14, 14, w - 14, h - 14, (13, 20, 34, 255))
    # pixel mosaic hint in the middle
    mosaic = [
        "........",
        "..####..",
        ".##..##.",
        ".....###",
        "....##..",
        "...##...",
        "...##...",
        "........",
        "...##...",
    ]
    cell = 8
    ox, oy = 32, 30
    for row, line in enumerate(mosaic):
        for col, ch in enumerate(line):
            if ch == "#":
                c = lerp(cyan, magenta, (row * 8 + col) / 63) + (255,)
                rect(ox + col * cell, oy + row * cell, ox + (col + 1) * cell, oy + (row + 1) * cell, c)
    raw = b"".join(b"\x00" + b"".join(struct.pack("4B", *(int(v) for v in p)) for p in row) for row in px)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def readme(vd: dict) -> str:
    version = vd["label"]
    count = vd["count"]
    cats = vd["categories"]
    cat_lines = "\n".join(
        f"- **{CATEGORY_LABELS[cat]}** — {cats[cat]}" for cat in CATEGORY_ORDER
    )
    return f"""# GUESS THE ITEM 3.0
### HOLO-PLANSZA • DIALOG GUI • Minecraft Java {version}

Zgadnij ukryty przedmiot po fragmentach jego ikony. **{count} przedmiotów**, animowana
holograficzna plansza 16×16, osiem ekranów GUI, katalog wszystkich ID, podpowiedzi,
budżet punktów i trzy tryby odkrywania. Bez modów, pluginów i resource packa.

## Co nowego względem 2.0

- **Holograficzna plansza 3D** — rama z neonów, narożne klejnoty, animowany skaner,
  dwa świetliki krążące po obwodzie, unoszące się litery tytułu.
- **Prawdziwe animacje** — migawka (shutter), fala kolorów na kafelkach, wielkie
  odliczanie 3–2–1, fajerwerki i konfetti na koniec, pierścień gwiazd w finale.
- **Nowy panel gry** — sześć liczników, pasek budżetu, pasek postępu, cztery przyciski
  z ikonami i podpowiedzią pod ręką.
- **Więcej GUI** — menu, panel gospodarza, formularz ustawień z suwakami, zasady,
  statystyki, katalog (kategorie + strony), wpisywanie ID, dynamiczne podsumowanie rundy.
- **Podpowiedzi** — kategoria, długość i pierwsza litera, wzór nazwy.
- **Budżet punktów** z paskiem i bossbarem, tryb AUTO z bossbarem odliczania.
- **Statystyki i rekordy** — wygrane, rekord, seria, liczba prób, celność.

## Instalacja

1. Włóż ZIP (bez rozpakowywania) do:
   - singleplayer: `.minecraft/saves/NAZWA_ŚWIATA/datapacks/`
   - serwer: `NAZWA_ŚWIATA/datapacks/`
2. W Overworldzie znajdź duże otwarte miejsce i wpisz jako operator:
   ```mcfunction
   /reload
   /function gti:setup
   ```
3. Plansza pojawi się 30 klocków przed Tobą, 11 klocków nad ziemią. Kamera obróci się w jej stronę.
4. Wybierz hasło i ustawienia, potem **Rozpocznij rundę** w panelu gospodarza.

`/function gti:remove` usuwa planszę i wszystkie efekty. `/function gti:view` ustawia kamerę.

## Sterowanie

| Akcja | Jak |
|---|---|
| Odsłoń paczkę wokół klikniętego pola | LPM / PPM na kafelku |
| Odsłoń paczkę losowo | przycisk **ODKRYJ** lub `/trigger gti.pixel set 1` |
| Zgadnij | przedmiot w głównej ręce + **ZGADUJ** lub `/trigger gti.guess set 1` |
| Podpowiedź | **PODPOWIEDŹ** lub `/trigger gti.hint set 1` |
| Menu | **MENU**, `/trigger gti.menu` lub `/dialog show @s gti:menu` |
| Nowa runda | `/trigger gti.next set 1` lub `/function gti:start` |
| Stop | `/function gti:stop` |
| Pauza | przycisk **II** w panelu (gospodarz) |

Każdy gracz w promieniu 64 klocków od planszy jest widzem i może zgadywać.

## Punktacja

- Odkryty piksel: **1 punkt**.
- Błędna odpowiedź: **4 punkty** oraz licznik prób.
- Podpowiedź: **8 punktów**.
- Budżet ustawiasz suwakiem; 0 = brak limitu.
- Wygrywa mniej prób; przy remisie mniej odkrytych pikseli. Rekord gracza to
  `próby × 1000 + piksele` — mniejszy jest lepszy.
- Przedmioty z tej samej grupy (np. `copper_block` i `waxed_copper_block`,
  `stone_bricks` i `infested_stone_bricks`) są równoważne.

## Katalog

Katalog zawiera wszystkie {count} ID w kategoriach:

{cat_lines}

Strony mają po 24 pozycje. Kliknięcie nazwy ustawia stałe hasło na następną rundę.
Nazwy są tłumaczone przez klienta; identyfikator jest w podpowiedzi.

## Komendy

```mcfunction
/function gti:setup            # zbuduj planszę
/function gti:remove           # usuń wszystko
/function gti:view             # popraw kamerę
/function gti:start | gti:stop
/function gti:mode/chill | easy | normal | hard
/function gti:preset/chill | normal | hard
/function gti:ui/menu | host | settings | stats | browser
/dialog show @s gti:menu
```

## Kompatybilność

- **Java {version}**, data pack format `{vd['pack_format']}.{vd['pack_format_minor']}`.
- Wymaga cheats/uprawnień operatora do budowy planszy i formularzy.
- Pakiety dla 1.21.11, 26.2 i 26.3 mają identyczną mechanikę i różnią się listą przedmiotów
  oraz formatem packa.

## Uwagi

- Plansza jest w pełni świetlista, więc działa też nocą i pod ziemią.
- Dialogi nie zatrzymują świata (`pause:false`), dzięki czemu runda działa w tle.
- Pierwsze `/reload` ładuje {count} przedmiotów do pamięci gry (jednorazowo).
- Nie instaluj jednocześnie kilku wersji tego packa — używają tej samej przestrzeni nazw `gti`.

Miłej gry!
"""


def item_list(vd: dict) -> str:
    lines = [f"GUESS THE ITEM 3.0 — Java {vd['label']} — {vd['count']} przedmiotów", ""]
    for cat in CATEGORY_ORDER:
        items = [i for i in vd["items"] if i["cat"] == cat]
        lines.append(f"== {CATEGORY_LABELS[cat]} ({len(items)}) ==")
        lines += [f"{i['id']}  [{i['name']}]" for i in items]
        lines.append("")
    return "\n".join(lines) + "\n"


def build_version(vd: dict) -> Path:
    label = vd["label"]
    files: dict[str, bytes] = {}

    def put(path: str, data: str | bytes) -> None:
        files[path] = data.encode("utf-8") if isinstance(data, str) else data

    put("pack.mcmeta", json.dumps(pack_meta(vd), ensure_ascii=False, indent=2) + "\n")
    put("pack.png", png_icon())
    put("README_PL.md", readme(vd))
    put("LISTA_PRZEDMIOTOW.txt", item_list(vd))

    put("data/minecraft/tags/function/load.json", json.dumps({"values": ["gti:load"]}, indent=2) + "\n")
    put("data/minecraft/tags/function/tick.json", json.dumps({"values": ["gti:tick"]}, indent=2) + "\n")
    put("data/minecraft/tags/dialog/quick_actions.json", json.dumps({"values": ["gti:menu"]}, indent=2) + "\n")

    put("data/gti/tags/item/answers.json", json.dumps({"values": [i["id"] for i in vd["items"]]}, indent=2) + "\n")
    for idx, group in enumerate(vd["equivalents"]):
        put(f"data/gti/tags/item/equivalent/g{idx}.json", json.dumps({"values": group}, indent=2) + "\n")

    funcs = {}
    funcs.update(game.game_functions(vd))
    funcs.update(ui.ui_functions(vd))
    for name, body in funcs.items():
        put(f"data/gti/function/{name}.mcfunction", body)

    for name, dialog in ui.dialogs(vd).items():
        put(f"data/gti/dialog/{name}.json", json.dumps(dialog, ensure_ascii=False, indent=2) + "\n")

    target = BUILD / label
    if target.exists():
        import shutil
        shutil.rmtree(target)
    for path, data in files.items():
        full = target / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)

    zip_path = OUT / vd["file"]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(files):
            info = zipfile.ZipInfo(path, date_time=(2026, 10, 20, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, files[path])
    return zip_path


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    for vd in VERSIONS:
        data = version_data(vd["label"])
        merged = {**vd, **{k: data[k] for k in ("count", "items", "categories", "equivalents")}}
        path = build_version(merged)
        print(f"{path.name}: {path.stat().st_size / 1024:.0f} KiB, {merged['count']} items")


if __name__ == "__main__":
    main()
