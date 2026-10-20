"""Minimal dependency-free PNG reader and item-icon -> block palette mapper.

Used at authoring time to bake 16x16 block-art for every item into
``data/art.json`` (committed), so building the datapack never needs the
vanilla texture assets.
"""

from __future__ import annotations

import json
import struct
import zlib
from functools import lru_cache
from pathlib import Path

ASSET_ROOT = Path("/tmp/mcmeta/assets/minecraft")
TEX_ROOT = ASSET_ROOT / "textures"
MODEL_ROOT = ASSET_ROOT / "models"

# (block id, label) - the palette the board is built from
PALETTE: list[str] = [
    "white_concrete",
    "light_gray_concrete",
    "gray_concrete",
    "black_concrete",
    "brown_concrete",
    "red_concrete",
    "orange_concrete",
    "yellow_concrete",
    "lime_concrete",
    "green_concrete",
    "cyan_concrete",
    "light_blue_concrete",
    "blue_concrete",
    "purple_concrete",
    "magenta_concrete",
    "pink_concrete",
    "terracotta",
    "brown_terracotta",
    "red_terracotta",
    "orange_terracotta",
    "yellow_terracotta",
    "white_terracotta",
    "light_gray_terracotta",
    "gray_terracotta",
    "black_terracotta",
    "gold_block",
    "iron_block",
    "copper_block",
    "emerald_block",
    "lapis_block",
    "amethyst_block",
    "calcite",
    "oak_planks",
    "dark_oak_planks",
    "deepslate",
    "sandstone",
]


# ---------------------------------------------------------------------------
# PNG decoding
# ---------------------------------------------------------------------------

def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png(path: Path) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    """Decode a PNG into (width, height, RGBA pixel rows)."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    pos = 8
    width = height = bit_depth = color_type = 0
    palette: list[tuple[int, int, int]] = []
    trns = b""
    idat = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        ctype = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
            interlace = chunk[12]
            if interlace:
                raise ValueError("interlaced PNG not supported")
        elif ctype == b"PLTE":
            palette = [tuple(chunk[i : i + 3]) for i in range(0, len(chunk), 3)]
        elif ctype == b"tRNS":
            trns = bytes(chunk)
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break

    raw = zlib.decompress(bytes(idat))
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    bpp = max(1, (channels * bit_depth) // 8)
    stride = (width * channels * bit_depth + 7) // 8
    out: list[tuple[int, int, int, int]] = []
    prev = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        line = bytearray(raw[offset : offset + stride])
        offset += stride
        if filter_type == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif filter_type == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filter_type == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filter_type == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upleft = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev[i], upleft)) & 0xFF
        prev = line

        row: list[tuple[int, int, int, int]] = []
        if bit_depth == 8:
            step = channels
            for x in range(width):
                px = line[x * step : x * step + step]
                if color_type == 0:
                    gray = px[0]
                    alpha = 0 if (len(trns) >= 2 and gray == trns[1]) else 255
                    row.append((gray, gray, gray, alpha))
                elif color_type == 2:
                    alpha = 255
                    if len(trns) >= 6 and bytes(px[:3]) == trns[:3]:
                        alpha = 0
                    row.append((px[0], px[1], px[2], alpha))
                elif color_type == 3:
                    index = px[0]
                    r, g, b = palette[index]
                    alpha = trns[index] if index < len(trns) else 255
                    row.append((r, g, b, alpha))
                elif color_type == 4:
                    row.append((px[0], px[0], px[0], px[1]))
                else:
                    row.append((px[0], px[1], px[2], px[3]))
        elif bit_depth in (1, 2, 4):
            bits_per = bit_depth
            mask = (1 << bit_depth) - 1
            per_byte = 8 // bits_per
            for x in range(width):
                byte = line[x // per_byte]
                shift = 8 - bits_per * ((x % per_byte) + 1)
                value = (byte >> shift) & mask
                if color_type == 3:
                    r, g, b = palette[value]
                    alpha = trns[value] if value < len(trns) else 255
                    row.append((r, g, b, alpha))
                else:
                    scale = 255 // mask
                    v = value * scale
                    row.append((v, v, v, 255))
        else:
            raise ValueError(f"unsupported bit depth {bit_depth} in {path}")
        out.append(row)  # type: ignore[arg-type]
    return width, height, out


def _texture(name: str, kind: str) -> Path | None:
    path = TEX_ROOT / kind / f"{name}.png"
    return path if path.exists() else None


def _strip_ns(value: str) -> str:
    return value.split(":", 1)[-1]


_TEXTURE_KEYS = ("all", "side", "top", "end", "texture", "particle", "bottom",
                 "front", "side_alt", "content")


@lru_cache(maxsize=None)
def _model_texture(model: str, kind: str, _depth: int = 0) -> str | None:
    if _depth > 6:
        return None
    path = MODEL_ROOT / kind / f"{model}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    textures = data.get("textures", {})
    for key in _TEXTURE_KEYS:
        value = textures.get(key)
        if isinstance(value, str) and value and not value.startswith("#"):
            return _strip_ns(value).rsplit("/", 1)[-1]
    # resolve "#ref" entries against the same file
    for key in _TEXTURE_KEYS:
        value = textures.get(key)
        if isinstance(value, str) and value.startswith("#"):
            target = textures.get(value[1:])
            if isinstance(target, str) and target and not target.startswith("#"):
                return _strip_ns(target).rsplit("/", 1)[-1]
    parent = data.get("parent")
    if parent:
        parent = _strip_ns(parent)
        pkind = "block" if parent.startswith("block/") else kind
        return _model_texture(parent.split("/", 1)[-1], pkind, _depth + 1)
    return None


_SUFFIXES = (
    "_slab", "_stairs", "_fence_gate", "_fence", "_wall", "_button",
    "_pressure_plate", "_trapdoor", "_door", "_shelf",
    "_hanging_sign", "_sign", "_chest_boat", "_pane",
)

# suffix -> how the fallback texture name is derived from the base name
_SUFFIX_TARGETS = {
    "_banner": "{base}_wool",
    "_bed": "{base}_wool",
    "_carpet": "{base}_wool",
    "_head": "{base}_spawn_egg",
    "_skull": "{base}_spawn_egg",
}

_COLORS = ("white", "light_gray", "gray", "black", "brown", "red", "orange",
           "yellow", "lime", "green", "cyan", "light_blue", "blue", "purple",
           "magenta", "pink")


def _texture_candidates(item_id: str) -> list[str]:
    name = item_id.split(":", 1)[1]
    seen: list[str] = []

    def push(value: str | None) -> None:
        if not value:
            return
        value = _strip_ns(value)
        for kind in ("item", "block"):
            if _texture(value, kind) is not None and value not in seen:
                seen.append(value)

    push(name)
    push(_model_texture(name, "item"))
    push(_model_texture(name, "block"))
    for prefix in ("waxed_", "infested_"):
        if name.startswith(prefix):
            stripped = name[len(prefix):]
            push(stripped)
            push(_model_texture(stripped, "block"))
            push(_model_texture(stripped, "item"))
    base = name
    for suffix in _SUFFIXES:
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    if base != name:
        stem = base[len("waxed_"):] if base.startswith("waxed_") else base
        for candidate in (base, stem, base + "s", stem + "s", base + "_block",
                          stem + "_block", base + "_planks", base + "_wool"):
            push(candidate)
            push(_model_texture(candidate, "block"))
    for suffix, target in _SUFFIX_TARGETS.items():
        if name.endswith(suffix):
            stem = name[: -len(suffix)]
            push(target.format(base=stem))
            push(target.format(base=stem) + "_planks")
    # generic: clock -> clock_00, compass -> compass_00, bee_nest -> bee_nest_side
    for kind in ("item", "block"):
        folder = TEX_ROOT / kind
        if folder.exists():
            matches = sorted(p.stem for p in folder.glob(name + "_*.png"))
            if matches:
                push(matches[0])
    for prefix in ("waxed_", "infested_", "stripped_", "cracked_", "mossy_",
                   "chiseled_", "polished_", "smooth_", "cut_", "aged_",
                   "exposed_", "weathered_", "oxidized_"):
        if name.startswith(prefix):
            push(name[len(prefix):])
    for alias in ("enchanted_golden_apple", "debug_stick", "player_head",
                  "moss_carpet"):
        if name == alias:
            fallback = {
                "enchanted_golden_apple": "golden_apple",
                "debug_stick": "stick",
                "player_head": "zombie_spawn_egg",
                "moss_carpet": "moss_block",
            }[alias]
            push(fallback)
    return seen


@lru_cache(maxsize=None)
def icon_pixels(item_id: str) -> tuple[tuple[int, int, int, int], ...]:
    """Return 256 RGBA pixels for an item id, top-left to bottom-right."""
    for name in _texture_candidates(item_id):
        for kind in ("item", "block"):
            path = _texture(name, kind)
            if path is None:
                continue
            try:
                width, height, rows = read_png(path)
            except Exception:
                continue
            if width >= 16 and height >= 16:
                # animated textures are vertical strips: first frame is the top 16 rows
                step_x = max(1, width // 16)
                step_y = max(1, height // 16) if height > 16 else 1
                pixels = []
                for y in range(16):
                    for x in range(16):
                        pixels.append(rows[y * step_y][x * step_x])
                return tuple(pixels)
    return ()


# ---------------------------------------------------------------------------
# palette
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def block_color(block: str) -> tuple[int, int, int]:
    path = _texture(block, "block")
    if path is None:
        return (127, 127, 127)
    width, height, rows = read_png(path)
    samples: list[tuple[int, int, int]] = []
    for y in range(min(16, height)):
        for x in range(min(16, width)):
            r, g, b, a = rows[y][x]
            if a >= 128:
                samples.append((r, g, b))
    if not samples:
        return (127, 127, 127)
    # median keeps outlines/shadows from dragging the colour away
    return tuple(sorted(c[i] for c in samples)[len(samples) // 2] for i in range(3))  # type: ignore[return-value]


PALETTE_COLORS: list[tuple[int, int, int]] = [block_color(b) for b in PALETTE]


def nearest_slot(r: int, g: int, b: int) -> int:
    """Palette index + 1 for a colour (0 means transparent/air)."""
    best = 1
    best_dist = 1 << 30
    for i, (pr, pg, pb) in enumerate(PALETTE_COLORS):
        # slightly favour luminance agreement so shading survives
        lum = (r * 3 + g * 6 + b) / 10
        plum = (pr * 3 + pg * 6 + pb) / 10
        dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2 + int((lum - plum) ** 2 * 1.6)
        if dist < best_dist:
            best_dist = dist
            best = i + 1
    return best


def item_art(item_id: str) -> list[int]:
    """256 palette indices (0 = transparent) for an item."""
    pixels = icon_pixels(item_id)
    if not pixels:
        return [0] * 256
    out = []
    for r, g, b, a in pixels:
        if a < 90:
            out.append(0)
        else:
            out.append(nearest_slot(r, g, b))
    return out
