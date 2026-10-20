# GUESS THE ITEM 3.0 — animowana plansza + pełne GUI (Minecraft Java)

Datapack, w którym zgadujesz ukryty przedmiot po fragmentach jego ikony. Zamiast
zwykłej siatki z kolorowych bloków dostajesz **holograficzną planszę 3D** z animacjami,
**osiem ekranów dialogowego GUI**, katalog wszystkich przedmiotów z podziałem na
kategorie, podpowiedzi, budżet punktów i statystyki.

Bez modów, bez resource packa, bez pluginów — wszystko na komendach i encjach display.

## Trzy wersje w tym repozytorium

| Plik ZIP | Minecraft | `pack_format` | Przedmioty | Kategorie (bloki / sprzęt / jedzenie / moby / materiały / inne) |
|---|---|---|---|---|
| `Guess_the_item_1.21.11_v3.zip` | 1.21.11 | 94.1 | **1504** | 1002 / 95 / 52 / 93 / 79 / 183 |
| `Guess_the_item_26.2_v3.zip` | 26.2 | 107.1 | **1536** | 1031 / 95 / 52 / 94 / 79 / 185 |
| `Guess_the_item_26.3_v3.zip` | 26.3 | 121.0 | **1657** | 1134 / 95 / 52 / 94 / 79 / 203 |

Każdy ZIP jest samodzielny — wrzucasz dokładnie jeden, pasujący do wersji gry.
Wersja 2.0 (`Guess_the_item_Java_26.2_v2.zip`) została w repo dla porównania.

## Instalacja

1. Wrzuć ZIP **bez rozpakowywania** do:
   - singleplayer: `.minecraft/saves/NAZWA_ŚWIATA/datapacks/`
   - serwer: `NAZWA_ŚWIATA/datapacks/`
2. W grze (jako operator): `/reload`
3. Znajdź dużą otwartą przestrzeń w **Overworldzie** i wpisz `/function gti:setup`.
   Plansza stanie 30 klocków przed Tobą i 11 nad ziemią, kamera sama obróci się w jej stronę.
4. Otwórz panel gospodarza (**MENU → Panel gospodarza** albo `/dialog show @s gti:host`),
   wybierz hasło i ustawienia, potem **Rozpocznij rundę**.

`/function gti:remove` usuwa planszę i wszystkie efekty, `/function gti:view` ustawia kamerę,
`/function gti:start` startuje rundę bez klikania.

## Sterowanie

| Akcja | Jak |
|---|---|
| Odsłoń paczkę wokół klikniętego pola | LPM / PPM na kafelku planszy |
| Odsłoń paczkę losowo | **ODKRYJ** w panelu lub `/trigger gti.pixel set 1` |
| Zgadnij | przedmiot w głównej ręce + **ZGADUJ** lub `/trigger gti.guess set 1` |
| Podpowiedź (3 poziomy) | **PODPOWIEDŹ** lub `/trigger gti.hint set 1` |
| Menu | **MENU**, `/trigger gti.menu` lub `/dialog show @s gti:menu` |
| Nowa runda | **Nowa runda** lub `/trigger gti.next set 1` |
| Stop / sprzątanie | `/function gti:stop`, `/function gti:remove` |
| Pauza | przycisk **II** w panelu (gospodarz) |

Każdy gracz w promieniu 64 klocków jest widzem i może zgadywać — nie trzeba nic
konfigurować. Rundy, statystyki i rekordy są per gracz.

## Punktacja

- odkryty piksel: **+1 punkt** budżetu,
- błędna odpowiedź: **+4 punkty** i licznik prób,
- podpowiedź: **+8 punktów** (maks. 3 stopnie),
- budżet ustawiasz suwakiem (0 = brak limitu); po jego wyczerpaniu runda przegrywa się
  z animacją i podsumowaniem,
- wygrywa **mniej prób**, przy remisie **mniej odkrytych pikseli**,
- rekord gracza to `próby × 1000 + piksele` — mniejsza wartość jest lepsza,
- przedmioty z tej samej grupy (np. `copper_block` i `waxed_copper_block`) są
  akceptowane jako poprawna odpowiedź — w sumie **67 grup**.

## Co jest w GUI

| Dialog | Co robi |
|---|---|
| `gti:menu` | główne menu: nowa runda, odkrywanie, zgadywanie, podpowiedź, statystyki, panel gospodarza, katalog, zasady |
| `gti:host` | panel gospodarza: start/stop, ustawienia, katalog, hasło z ręki, losowy przedmiot, wpisanie ID, presety CHILL/NORMAL/HARD |
| `gti:settings` | suwaki: paczka pikseli 1–16, budżet 0–256, tryb odkrywania (RĘCZNIE / PO BŁĘDZIE / AUTO), piksele na start, podpowiedzi |
| `gti:rules` | skrót zasad i punktacji |
| `gti:stats` | wygrane, rekord, seria, próby, celność + reset własnych statystyk |
| `gti:item_id` | wpisanie dowolnego identyfikatora jako hasła |
| `gti:catalogue/index` i `gti:catalogue/<kategoria>/<strona>` | katalog wszystkich ID: „wszystkie” + 6 kategorii, po 24 pozycje na stronę |
| `gti:summary` | dynamiczne podsumowanie rundy (wynik, rekord, statystyki) |

Dodatkowo: **bossbary** budżetu i odliczania, panel boczny z 6 licznikami, paskiem
budżetu, paskiem postępu i 4 przyciskami, dolne karty z podpowiedziami oraz
unoszący się tytuł nad planszą.

## Animacje

- intro: **migawka (shutter)** zamyka i otwiera planszę, po kafelkach rozchodzą się
  kolorowe fale, potem wielkie odliczanie **3–2–1**,
- plansza: skaner, dwa świetliki krążące po obwodzie, pulsujące narożne klejenty,
  unoszące się litery tytułu, drgające kafelki po trafieniu,
- wygrana: fala kolorów po kolumnach, dwa pierścienie cząstek, konfetti i fajerwerki,
- przegrana: fala po wierszach i przygaszenie planszy,
- finał: podsumowanie w GUI + sprzątanie scenografii.

## Struktura paczki

```
pack.mcmeta                  # min_format/max_format = wersja gry
pack.png                     # wygenerowana ikona 128×128
README_PL.md                 # instrukcja w paczce
LISTA_PRZEDMIOTOW.txt        # wszystkie ID i nazwy dla tej wersji
data/gti/function/           # logika, animacje, UI, dane
data/gti/dialog/             # 137–151 dialogów (menu, panel, katalog, ...)
data/gti/tags/item/          # answers + 67 grup equivalent/*
data/minecraft/tags/function # load + tick
```

## Rozwój

Generator i walidator są w `src/` (czysty Python 3, bez zależności):

```bash
cd src
python3 build.py       # buduje build/<wersja>/ i trzy ZIP-y w katalogu głównym
python3 validate.py    # JSON, SNBT, referencje funkcji/dialogów, składnia scoreboardów
```

Dodatkowo każdą paczkę można sprawdzić parserem `mecha`:

```bash
cd build/26.2 && mecha . -m 1.21
```

Katalogi `build/` są artefaktem — można je regenerować w każdej chwili.

## Uwagi

- Planszę buduj w **Overworldzie** (datapack sam tego pilnuje i wypisze komunikat).
- `/function gti:setup` wymaga uprawnień operatora; gracze bez OP mogą używać
  `/trigger gti.menu` i przycisków w GUI.
- Dialogi wymagają Minecrafta 1.21.9+ — wszystkie trzy wersje w tym repo je mają.
- Po `/reload` wystarczy ponownie wpisać `/function gti:setup`, żeby odświeżyć planszę.
