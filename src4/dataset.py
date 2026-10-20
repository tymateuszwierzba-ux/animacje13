"""Loads the generated per-version item catalogue."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data" / "versions.json").read_text(encoding="utf-8"))

CATEGORY_ORDER = ["blocks", "equipment", "food", "mobs", "materials", "other"]
CATEGORY_LABELS = {
    "blocks": "BLOCKS AND BUILDING",
    "equipment": "WEAPONS, TOOLS, ARMOR",
    "food": "FOOD AND PLANTS",
    "mobs": "MOBS AND SPAWN EGGS",
    "materials": "MATERIALS AND INGREDIENTS",
    "other": "OTHER ITEMS",
}
CATEGORY_SHORT = {
    "blocks": "BLOCKS",
    "equipment": "EQUIPMENT",
    "food": "FOOD",
    "mobs": "MOBS",
    "materials": "MATERIALS",
    "other": "OTHER",
}


@lru_cache(maxsize=None)
def version_data(version: str) -> dict:
    return DATA[version]


def items(version: str) -> list[dict]:
    return version_data(version)["items"]


def grouped(version: str) -> dict[str, list[dict]]:
    out = {key: [] for key in CATEGORY_ORDER}
    for item in items(version):
        out[item["cat"]].append(item)
    return out
