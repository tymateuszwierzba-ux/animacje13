"""Render a 2D front-view mock of the built wall for a visual check."""
import json, struct, zlib, random
import textures as t

arts = json.load(open('data/art.json'))
PAL = t.PALETTE_COLORS

S = 24
X0, X1 = -13.6, 13.6
Y0, Y1 = -0.6, 27.2
W = int((X1 - X0) * S)
H = int((Y1 - Y0) * S)
img = [[(118, 170, 212, 255) for _ in range(W)] for _ in range(H)]

def px(x, y):
    return (x - X0) * S, (Y1 - y) * S

def rect(x, y, w, h, colour):
    ax, ay = px(x, y + h)
    bx_, by = px(x + w, y)
    for yy in range(max(0, int(ay)), min(H, int(by))):
        for xx in range(max(0, int(ax)), min(W, int(bx_))):
            img[yy][xx] = colour + (255,)

SAND = (222, 208, 163)
SAND2 = (211, 196, 149)
SAND3 = (196, 179, 130)
CUT = (183, 165, 115)
CHIS = (168, 150, 100)
STONE = (126, 126, 130)
DARK = (22, 24, 30)
BED1 = (92, 92, 96)
BED2 = (64, 64, 68)

# sandstone panels
rect(-12.7, 0.6, 25.4, 26.9, SAND)
for y in range(1, 27, 2):
    rect(-12.7, y, 25.4, 0.9, SAND2)
for x in (-10.6, -6.4, -2.2, 2.0, 6.2, 10.4):
    rect(x, 17.6, 0.35, 9.9, SAND3)

# plinth
rect(-12.6, -0.1, 25.2, 1.05, STONE)
rect(-12.6, 0.85, 25.2, 0.16, (46, 48, 54))

# frame ring
for i in range(18):
    x = -8.5 + i
    rect(x - 0.5, 1.5, 1.0, 1.0, CUT)
    rect(x - 0.5, 18.5, 1.0, 1.0, CUT)
for y in range(3, 19):
    rect(-9.0, y - 0.5, 1.0, 1.0, CUT)
    rect(8.0, y - 0.5, 1.0, 1.0, CUT)
for cx in (-8.5, 8.5):
    for cy in (2, 19):
        rect(cx - 0.5, cy - 0.5, 1.0, 1.0, CHIS)

# board 16 x 16
item = 'minecraft:diamond_sword'
art = arts[item]
random.seed(11)
revealed = {i for i in range(256) if random.random() < 0.42}
for idx in range(256):
    row, col = divmod(idx, 16)
    x = -7.5 + col
    y = 18 - row
    if idx in revealed:
        v = art[idx]
        colour = (16, 16, 20) if v == 0 else PAL[v - 1]
        rect(x - 0.5, y - 0.5, 1.0, 1.0, colour)
    else:
        rect(x - 0.5, y - 0.5, 1.0, 1.0, BED1)
        rect(x - 0.34, y - 0.34, 0.36, 0.36, BED2)
        rect(x + 0.06, y - 0.04, 0.3, 0.34, BED2)

# attempt strip: limit 16, 11 left -> centred 16 sockets, 11 lit
LIMIT, LEFT = 16, 11
pad = (32 - LIMIT) // 2
rect(-8.7, 20.77, 17.4, 1.66, (26, 26, 30))
for i in range(32):
    x = -8 + (i + 0.5) * 0.5
    if not (pad <= i < pad + LIMIT):
        continue
    rect(x - 0.19, 20.95, 0.38, 1.3, (12, 12, 16))
    if i - pad < LEFT:
        tone = min(3, (LEFT * 3) // LIMIT)
        colour = {0: (176, 42, 48), 1: (225, 97, 0), 2: (241, 175, 21), 3: (94, 169, 24)}[tone]
    else:
        colour = (86, 86, 92)
    rect(x - 0.14, 21.02, 0.28, 1.16, colour)
# LIMIT label
rect(-10.1, 20.95, 1.4, 1.3, (26, 26, 30))
rect(-9.85, 21.2, 0.9, 0.24, (140, 158, 180))
rect(-9.85, 21.55, 0.9, 0.24, (140, 158, 180))

# left HUD
rect(-12.8, 3.4, 3.3, 13.0, (24, 30, 40))
for i in range(5):
    rect(-12.55, 4.3 + i * 2.55, 2.8, 0.9, (52, 68, 92))
    rect(-12.55, 3.45 + i * 2.55, 2.8, 0.7, (150, 168, 190))

# right console
buttons = [("GUESS", (94, 169, 24)), ("REVEAL", (21, 119, 136)),
           ("HINT", (241, 175, 21)), ("MENU", (169, 48, 159))]
for i, (label, colour) in enumerate(buttons):
    y = 14.8 - i * 3.0
    rect(8.9, y - 0.85, 3.0, 1.7, (28, 28, 34))
    rect(9.05, y - 0.67, 2.7, 1.34, colour)
    rect(9.35, y - 0.12, 2.1, 0.24, (250, 250, 250))

# status caption on the plinth
rect(-3.4, 0.42, 6.8, 0.42, (150, 176, 205))
rect(-2.6, 0.52, 5.2, 0.2, (40, 44, 52))

raw = b''.join(b'\x00' + bytes(v for p in row for v in p) for row in img)
def chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
png = (b'\x89PNG\r\n\x1a\n'
       + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 6, 0, 0, 0))
       + chunk(b'IDAT', zlib.compress(raw, 9))
       + chunk(b'IEND', b''))
open('/home/user/animacje13/preview.png', 'wb').write(png)
print(W, H)
