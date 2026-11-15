"""Interface « Royaumes » — façade de château en pixel art (1 px de dessin = 1 px d'interface).

Repère : coordonnées du coffre vanilla (0,0 = coin haut-gauche du coffre 176x222).
Les boutons cliquables tombent sur les cases du coffre (x 8..169, y 18..125).
"""
import math, random
import numpy as np
from PIL import Image
from royal_ui import FONT, OX, OY, W, H

# ---------------------------------------------------------------- palettes
K = (36, 22, 30)                      # contour
STONE = [(52, 50, 66), (78, 76, 94), (106, 104, 122), (136, 134, 150), (168, 166, 180), (204, 202, 212)]
WOOD = [(58, 34, 24), (88, 54, 32), (120, 76, 42), (154, 102, 58), (190, 136, 80), (222, 176, 118)]
PARCH = [(150, 104, 62), (196, 152, 100), (224, 188, 136), (240, 214, 166), (250, 234, 196)]
SLATE = [(30, 34, 64), (44, 56, 100), (62, 84, 138), (92, 120, 176), (136, 166, 214)]
ROOFR = [(84, 22, 28), (128, 36, 38), (172, 56, 48), (210, 88, 64), (238, 132, 96)]
GOLD = [(110, 62, 16), (176, 112, 26), (226, 166, 44), (250, 210, 80), (255, 242, 170)]
RED = [(92, 16, 26), (140, 26, 36), (186, 40, 46), (222, 70, 64), (246, 120, 100)]
BLUE = [(24, 36, 84), (38, 62, 130), (60, 98, 180), (100, 146, 222), (160, 200, 250)]
GRASS = [(30, 70, 40), (46, 104, 48), (70, 140, 56), (108, 178, 70), (156, 212, 96)]
DIRT = [(64, 40, 30), (92, 60, 40), (122, 84, 54), (150, 108, 70)]
IRON = [(40, 42, 54), (70, 74, 90), (110, 114, 132), (156, 160, 178), (210, 214, 228)]
LABEL_GREY = (64, 64, 64)

def A(c, a=255): return tuple(c[:3]) + (a,)

# ---------------------------------------------------------------- toile
class Pix:
    def __init__(self, w, h, ox=0, oy=0):
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); self.ox, self.oy = ox, oy
        self.a = None
    def px(self, x, y, c):
        X, Y = x + self.ox, y + self.oy
        if 0 <= X < self.img.width and 0 <= Y < self.img.height:
            if len(c) == 4 and c[3] < 255:
                self.img.alpha_composite(Image.new("RGBA", (1, 1), c), (X, Y))
            else:
                self.img.putpixel((X, Y), A(c))
    def rect(self, x0, y0, x1, y1, c):
        if x1 < x0 or y1 < y0: return
        X0, Y0 = max(0, x0 + self.ox), max(0, y0 + self.oy)
        X1, Y1 = min(self.img.width - 1, x1 + self.ox), min(self.img.height - 1, y1 + self.oy)
        if X1 < X0 or Y1 < Y0: return
        if len(c) == 4 and c[3] < 255:
            self.img.alpha_composite(Image.new("RGBA", (X1 - X0 + 1, Y1 - Y0 + 1), c), (X0, Y0))
        else:
            self.img.paste(A(c), (X0, Y0, X1 + 1, Y1 + 1))
    def hline(self, x0, x1, y, c): self.rect(min(x0, x1), y, max(x0, x1), y, c)
    def vline(self, x, y0, y1, c): self.rect(x, min(y0, y1), x, max(y0, y1), c)
    def paste(self, im, x, y): self.img.alpha_composite(im, (x + self.ox, y + self.oy)) if (x + self.ox >= 0 and y + self.oy >= 0) else self._paste_clip(im, x, y)
    def _paste_clip(self, im, x, y):
        X, Y = x + self.ox, y + self.oy
        cx, cy = max(0, -X), max(0, -Y)
        if cx >= im.width or cy >= im.height: return
        self.img.alpha_composite(im.crop((cx, cy, im.width, im.height)), (X + cx, Y + cy))
    def text(self, x, y, s, col, shadow=True, bold=False):
        return FONT.draw(self.img, x + self.ox, y + self.oy, s, col, shadow, bold) - self.ox
    def text_outline(self, x, y, s, col, out=K, bold=False):
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            FONT.draw(self.img, x + dx + self.ox, y + dy + self.oy, s, out, False, bold)
        FONT.draw(self.img, x + self.ox, y + 1 + self.oy, s, tuple(int(c * 0.55) for c in col[:3]), False, bold)
        return FONT.draw(self.img, x + self.ox, y + self.oy, s, col, False, bold) - self.ox
    def text_c(self, cx, y, s, col, shadow=True, bold=False):
        return self.text(cx - FONT.width(s, bold) // 2, y, s, col, shadow, bold)
    def text_outline_c(self, cx, y, s, col, out=K, bold=False):
        return self.text_outline(cx - FONT.width(s, bold) // 2, y, s, col, out, bold)

def outline(im, col=K, diag=False):
    a = np.array(im)[:, :, 3] > 0
    n = np.zeros_like(a)
    n[1:, :] |= a[:-1, :]; n[:-1, :] |= a[1:, :]; n[:, 1:] |= a[:, :-1]; n[:, :-1] |= a[:, 1:]
    if diag:
        n[1:, 1:] |= a[:-1, :-1]; n[:-1, :-1] |= a[1:, 1:]; n[1:, :-1] |= a[:-1, 1:]; n[:-1, 1:] |= a[1:, :-1]
    edge = n & ~a
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    arr = np.array(out); arr[edge] = A(col); out = Image.fromarray(arr)
    out.alpha_composite(im)
    return out

def layer(w, h, pad=2):
    return Pix(w + 2 * pad, h + 2 * pad, pad, pad)

def put(dst, lay, x, y, pad=2, ol=True, shadow=True):
    im = outline(lay.img) if ol else lay.img
    if shadow:
        a = np.array(im)[:, :, 3] > 0
        sh = np.zeros((*a.shape, 4), np.uint8); sh[a] = (20, 10, 20, 70)
        dst.paste(Image.fromarray(sh), x - pad + 2, y - pad + 2)
    dst.paste(im, x - pad, y - pad)

def sprite(rows, pal):
    h, w = len(rows), max(len(r) for r in rows)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in pal: im.putpixel((x, y), A(pal[ch]))
    return im

PAL = {"K": K, "Y": GOLD[3], "y": GOLD[1], "L": GOLD[4], "o": GOLD[2], "R": RED[2], "r": RED[1], "q": RED[3],
       "W": (250, 246, 236), "w": (196, 190, 182), "B": BLUE[2], "b": BLUE[1], "c": BLUE[4],
       "G": GRASS[3], "g": GRASS[1], "h": GRASS[4], "N": WOOD[2], "n": WOOD[1], "O": WOOD[4],
       "S": (240, 192, 150), "s": (204, 142, 110), "I": IRON[3], "i": IRON[1], "J": IRON[4], "j": IRON[2],
       "P": PARCH[3], "p": PARCH[1], "E": (44, 30, 36), "H": (120, 76, 44), "e": (80, 52, 34),
       "F": (255, 150, 40), "f": (255, 226, 120), "M": (180, 60, 140), "m": (120, 30, 96)}

# ---------------------------------------------------------------- matériaux
def stone_wall(p, x0, y0, x1, y1, seed=1, bw=10, bh=6, moss=True):
    rnd = random.Random(seed)
    p.rect(x0, y0, x1, y1, STONE[1])
    row = 0
    for y in range(y0, y1 + 1, bh):
        off = (bw // 2) if row % 2 else 0
        x = x0 - off
        while x <= x1:
            w = bw + rnd.choice((-2, 0, 0, 2))
            sh = rnd.choice((2, 2, 3, 3, 3, 4))
            bx0, bx1 = max(x0, x + 1), min(x1, x + w - 1)
            by0, by1 = y + 1, min(y1, y + bh - 1)
            p.rect(bx0, by0, bx1, by1, STONE[sh])
            p.hline(bx0, bx1, by0, STONE[min(5, sh + 1)])
            p.vline(bx0, by0, by1, STONE[min(5, sh + 1)])
            p.hline(bx0, bx1, by1, STONE[sh - 1])
            if rnd.random() < 0.25:
                p.px(rnd.randint(bx0, max(bx0, bx1)), rnd.randint(by0, max(by0, by1)), STONE[sh - 1])
            x += w
        row += 1
    if moss:
        for _ in range((x1 - x0) * (y1 - y0) // 160):
            mx, my = rnd.randint(x0, x1), rnd.randint(y0, y1)
            for k in range(rnd.randint(2, 6)):
                p.px(mx + rnd.randint(-2, 2), my + rnd.randint(-1, 1), GRASS[rnd.choice((1, 2, 2))])

def planks(p, x0, y0, x1, y1, seed=2, vertical=False, pal=WOOD, base=2):
    rnd = random.Random(seed)
    p.rect(x0, y0, x1, y1, pal[base])
    if vertical:
        x = x0
        while x <= x1:
            w = rnd.choice((5, 6, 6, 7)); c = pal[base + rnd.choice((-1, 0, 0, 1))]
            p.rect(x, y0, min(x1, x + w - 1), y1, c)
            p.vline(x, y0, y1, pal[max(0, base - 2)])
            p.vline(x + 1, y0, y1, pal[min(5, base + 1)])
            for _ in range((y1 - y0) // 6):
                gx = rnd.randint(x + 2, max(x + 2, min(x1, x + w - 2))); gy = rnd.randint(y0, y1)
                p.vline(gx, gy, min(y1, gy + rnd.randint(2, 4)), pal[max(0, base - 1)])
            x += w
    else:
        y = y0
        while y <= y1:
            h = rnd.choice((4, 5, 5)); c = pal[base + rnd.choice((-1, 0, 0, 1))]
            p.rect(x0, y, x1, min(y1, y + h - 1), c)
            p.hline(x0, x1, y, pal[min(5, base + 1)])
            p.hline(x0, x1, min(y1, y + h - 1), pal[max(0, base - 1)])
            for _ in range((x1 - x0) // 8):
                gx = rnd.randint(x0, x1); gy = rnd.randint(y + 1, max(y + 1, min(y1, y + h - 2)))
                p.hline(gx, min(x1, gx + rnd.randint(2, 5)), gy, pal[max(0, base - 1)])
            y += h

def gradient(p, x0, y0, x1, y1, stops):
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0) * (len(stops) - 1)
        i = min(len(stops) - 2, int(t)); f = t - i
        c = tuple(int(stops[i][k] + (stops[i + 1][k] - stops[i][k]) * f) for k in range(3))
        # tramage léger entre deux bandes
        p.hline(x0, x1, y, c)

def disc(p, cx, cy, r, c):
    for y in range(-r, r + 1):
        w = int(math.sqrt(max(0, r * r - y * y)) + 0.3)
        p.hline(cx - w, cx + w, cy + y, c)

def tree(p, cx, by, r=5, pal=GRASS, trunk=True):
    lay = layer(2 * r + 6, 2 * r + 10)
    c = r + 3
    if trunk:
        lay.rect(c - 1, 2 * r, c, 2 * r + 6, WOOD[1]); lay.vline(c, 2 * r, 2 * r + 6, WOOD[2])
    disc(lay, c, r + 1, r, pal[1])
    disc(lay, c - 1, r, r - 1, pal[2])
    disc(lay, c - 2, r - 1, max(1, r - 3), pal[3])
    lay.px(c - 3, r - 2, pal[4]); lay.px(c - 2, r - 3, pal[4])
    put(p, lay, cx - c, by - 2 * r - 6, ol=True, shadow=False)

def cloud(p, x, y, w=14, c=(255, 255, 255), sh=(214, 226, 246)):
    lay = layer(w + 2, 7)
    lay.rect(3, 2, w - 2, 5, c); lay.rect(1, 4, w, 5, c); lay.rect(5, 0, w // 2 + 2, 2, c)
    lay.hline(1, w, 5, sh)
    put(p, lay, x, y, ol=False, shadow=False)

def flag(p, x, y, col=RED, h=10, w=9, left=False):
    p.vline(x, y, y + h, WOOD[1]); p.px(x, y - 1, GOLD[3])
    for i in range(5):
        wave = int(1.2 * math.sin(i / 1.6))
        for j in range(w):
            xx = x - 1 - j if left else x + 1 + j
            yy = y + i + int(1.0 * math.sin(j / 2.0))
            p.px(xx, yy, col[2] if i < 4 else col[1])
            if i == 0: p.px(xx, yy, col[3])

def torch(p, x, y):
    p.rect(x, y + 3, x + 2, y + 9, WOOD[2]); p.vline(x, y + 3, y + 9, WOOD[1])
    p.rect(x - 1, y + 3, x + 3, y + 4, IRON[1])
    p.rect(x, y - 2, x + 2, y + 2, (255, 150, 40)); p.px(x + 1, y - 3, (255, 150, 40))
    p.rect(x + 1, y - 1, x + 1, y + 2, (255, 230, 130)); p.px(x + 1, y - 4, (255, 210, 90))
    for r, a in ((6, 40), (4, 50)):
        disc(p, x + 1, y, r, (255, 190, 80, a))

# ---------------------------------------------------------------- petites icônes (12 px)
ICONS = {
 "crown": ["...K..K..K...", "..KYK.KYKKYK.", ".KYYK.KYKYYK.", ".KYYYKYYKYYYK", ".KYRYYYBYYRYK", ".KLLLLLLLLLLK", ".KyyyyyyyyyyK", "..KKKKKKKKKK."],
 "coins": ["....KKKK....", "...KYYYYK...", "...KyyyyK...", "..KKYYYYKK..", ".KYYKyyKYYK.", ".KyyKYYKyyK.", "KKYYKyyKYYKK", "KYYYKYYKyyYK", "KyyyKyyKYYyK", "KYYYKYYKyyYK", ".KKKKKKKKKK."],
 "hourglass": ["KKKKKKKKKK", "KNNNNNNNNK", ".KcccccccK.", ".KcYYYYYcK", "..KcYYYcK.", "...KcYcK..", "...KcYcK..", "..KccYccK.", ".KccYYYccK", ".KcYYYYYcK", "KNNNNNNNNK", "KKKKKKKKKK"],
 "trophy": ["KKKKKKKKKKK", "KYLYYYYYyYK", "KYLYYYYYyYK", ".KYLYYYyYK.", "KKYYYYYyYKK", "..KYYYyyK..", "...KYyyK...", "....KyK....", "...KYYyK...", "..KNNNNNK..", "..KKKKKKK.."],
 "people": ["...KKK..KKK.", "..KHHHKKHHHK", "..KSSSKKSSSK", "..KSESKKSESK", "...KSK..KSK.", "KKKKKKKKKKKK", "KRRRRKKBBBBK", "KRqRRKKBcBBK", "KRRRRKKBBBBK", "KKKKKKKKKKKK"],
 "map": ["KKKKKKKKKKKK", "KPPPKPPPPKPK", "KPgPKPPRPKPK", "KPggKPRRPKPK", "KPPgKPPPPKPK", "KPPPKPPBBKPK", "KPPPKPBBPKPK", "KpppKppppKpK", "KKKKKKKKKKKK"],
 "house": [".....KK.....", "....KRRK....", "...KRRRRK...", "..KRRqqRRK..", ".KRRqqqqRRK.", "KKKKKKKKKKKK", ".KWWWWWWWWK.", ".KWfWKNKWWK.", ".KWWWKNKWfK.", ".KWWWKNKWWK.", ".KKKKKKKKKK."],
 "wheat": ["..K..K..K...", ".KYKKYKKYK..", ".KYKKYKKYK..", "..KYKYKYK...", "..KYYYYYK...", "...KYYYK....", "...KyYyK....", "..KKNNNKK...", "...KyYyK....", "...KYyYK....", "...KyYyK....", "....KKK....."],
 "chest": [".KKKKKKKKKK.", "KNOOOOOOOONK", "KNNNNNNNNNNK", "KKKKKYKKKKKK", "KNOOKYKOOONK", "KNNNKyKNNNNK", "KNNNNNNNNNNK", "KnnnnnnnnnnK", "KKKKKKKKKKKK"],
 "hammer": ["..KKKKKK....", ".KJIIIIIK...", ".KIIIIIiK...", "..KKKKKiK...", "....KNK.K...", "....KNK.....", "....KOK.....", "....KNK.....", "....KNK.....", "....KnK.....", ".....K......"],
 "shield": ["KKKKKKKKKKK", "KRRRRYBBBBK", "KRqRRYBcBBK", "KRRRRYBBBBK", "KYYYYYYYYYK", "KBBBBYRRRRK", ".KBBBYRRRK.", "..KBBYRRK..", "...KKYKK...", "....KKK...."],
}
def icon(name):
    return sprite(ICONS[name], PAL)

# ---------------------------------------------------------------- scènes des boutons
def scene_kingdom(w, h):
    """Paysage du royaume du joueur : vallée, village, moulin, rivière (≈ 92x32)."""
    p = Pix(w, h)
    gradient(p, 0, 0, w - 1, h - 1, [(108, 156, 236), (160, 200, 246), (218, 236, 252)])
    disc(p, w - 12, 7, 4, (255, 246, 200)); disc(p, w - 12, 7, 3, (255, 255, 236))
    cloud(p, 4, 2, 14); cloud(p, 48, 5, 11)
    for x in range(w):
        m = int(13 + 5 * math.sin(x / 8.0) + 3 * math.sin(x / 3.4 + 1))
        p.vline(x, m, h, (118, 134, 176))
        if m < 12: p.vline(x, m, m + 1, (236, 240, 252))
    for x in range(w):
        m = int(19 + 2 * math.sin(x / 6.0 + 2) + 1.5 * math.sin(x / 2.7))
        p.vline(x, m, h, GRASS[2]); p.px(x, m, GRASS[3])
    for fx, fw, col in ((2, 20, GOLD[3]), (64, 22, GRASS[3])):
        for yy in range(24, h):
            p.hline(fx + (yy - 24), fx + fw + (yy - 24) // 2, yy, col if yy % 2 else tuple(max(0, c - 34) for c in col))
    for yy in range(21, h):
        cx = int(40 + 6 * math.sin(yy / 2.6) + (yy - 21) * 1.2)
        p.hline(cx - 1 - (yy - 21) // 3, cx + 1 + (yy - 21) // 3, yy, (70, 130, 210)); p.px(cx, yy, (170, 214, 255))
    def house(x, y, rc):
        lay = layer(11, 11)
        for i in range(5): lay.hline(5 - i, 5 + i, i, rc[2] if i < 3 else rc[3])
        lay.hline(0, 10, 4, rc[1])
        lay.rect(1, 5, 9, 10, (240, 230, 210)); lay.vline(1, 5, 10, WOOD[2]); lay.vline(9, 5, 10, WOOD[2]); lay.hline(1, 9, 5, WOOD[2])
        lay.rect(4, 7, 5, 10, WOOD[1]); lay.px(7, 7, (255, 220, 120))
        put(p, lay, x, y, shadow=False)
    lay = layer(14, 24)
    stone_wall(lay, 2, 8, 11, 23, seed=5, bw=5, bh=3, moss=False)
    for i in range(4): lay.rect(2 + 3 * i, 6, 2 + 3 * i + 1, 7, STONE[3])
    lay.rect(5, 17, 8, 23, WOOD[1]); lay.px(6, 12, (255, 220, 120)); lay.px(7, 12, (255, 220, 120))
    lay.vline(7, 0, 5, WOOD[1]); lay.rect(8, 0, 11, 2, RED[2])
    put(p, lay, 22, 6, shadow=False)
    for x, y, rc in ((10, 18, ROOFR), (40, 19, SLATE), (52, 21, ROOFR)):
        house(x, y, rc)
    lay = layer(16, 22)
    lay.rect(5, 8, 10, 21, (232, 220, 196)); lay.vline(5, 8, 21, (190, 176, 150))
    for i in range(4): lay.hline(7 - i, 8 + i, 4 + i, WOOD[2])
    lay.rect(7, 16, 8, 21, WOOD[1])
    for t in range(-7, 8): lay.px(8 + t, 7 + t, WOOD[3]); lay.px(8 + t, 7 - t, WOOD[3])
    put(p, lay, 64, 8, shadow=False)
    for x, y, r in ((4, 30, 4), (84, 31, 5), (60, 33, 3), (32, 33, 3)):
        tree(p, x, y, r)
    return p.img

def scene_build(w, h):
    """Chantier : tour en construction, échafaudage, grue (≈ 28x28)."""
    p = Pix(w, h)
    gradient(p, 0, 0, w - 1, h - 1, [(124, 176, 240), (206, 230, 252)])
    cloud(p, 14, 2, 10)
    p.rect(0, h - 4, w - 1, h - 1, GRASS[2]); p.hline(0, w - 1, h - 4, GRASS[3]); p.hline(0, w - 1, h - 1, DIRT[2])
    lay = layer(16, 18)
    stone_wall(lay, 0, 4, 15, 17, seed=7, bw=5, bh=3, moss=False)
    for x in range(16):
        top = 4 + int(4 * abs(math.sin(x / 2.6)))
        lay.vline(x, 0, top - 1, (0, 0, 0, 0))
    lay.img = Image.fromarray(np.where((np.array(lay.img)[:, :, 1:2] == 0) & (np.array(lay.img)[:, :, 3:4] == 255) & False, 0, np.array(lay.img)))
    lay.rect(6, 12, 9, 17, (40, 26, 22))
    put(p, lay, 3, h - 21)
    for x in (1, 21):
        p.vline(x, 6, h - 4, WOOD[2])
    p.rect(0, 8, 22, 8, WOOD[3]); p.rect(0, 15, 22, 15, WOOD[3])
    for i in range(7): p.px(2 + i, 9 + i, WOOD[1])
    # grue
    for t in range(20): p.px(23 + (t // 7), h - 4 - t, WOOD[2]); p.px(26 - (t // 7), h - 4 - t, WOOD[1])
    p.rect(8, 2, 27, 3, WOOD[3]); p.hline(8, 27, 3, WOOD[1])
    p.vline(11, 4, 9, (220, 210, 180))
    p.rect(9, 10, 13, 13, STONE[3]); p.hline(9, 13, 10, STONE[5]); p.vline(13, 10, 13, STONE[1])
    p.paste(outline(icon("hammer")).crop((0, 0, 14, 13)), 15, h - 15)
    return p.img

def scene_forge(w, h):
    """Forge : enclume, épée incandescente, étincelles, flèche d'amélioration."""
    p = Pix(w, h)
    rnd = random.Random(11)
    p.rect(0, 0, w - 1, h - 1, (40, 22, 24))
    for y in range(0, h, 4):
        off = 3 if (y // 4) % 2 else 0
        for x in range(-off, w, 7):
            c = (66 + rnd.randint(-6, 6), 36, 34)
            p.rect(x + 1, y + 1, x + 6, y + 3, c); p.hline(x + 1, x + 6, y + 1, (88, 50, 44))
    for r, a in ((20, 50), (13, 60), (8, 70)):
        disc(p, w // 2, h - 6, r, (255, 140, 40, a))
    an = sprite(["KKKKKKKKKKKKKKKKKKKK....", "KJJJJJJJJJJJJJJJJJJJKK..", "KIIIIIIIIIIIIIIIIIIIIIK.", ".KiiiiiiiiiiiiiiiiiiiK..",
                 "...KKiiiiiiiiiiiiKK.....", ".....KiiiiiiiiiiK.......", ".....KjjjjjjjjjjK.......", "....KIIIIIIIIIIIIK......", "...KiiiiiiiiiiiiiiK.....", "...KKKKKKKKKKKKKKKK....."], PAL)
    p.paste(an, 2, h - 10)
    for i in range(16):
        p.px(4 + i, h - 12, (255, 210, 100)); p.px(4 + i, h - 11, (255, 130, 40))
    p.px(3, h - 12, (255, 244, 200)); p.rect(20, h - 14, 21, h - 9, GOLD[2]); p.rect(22, h - 12, 25, h - 11, WOOD[2])
    for _ in range(14):
        x, y = rnd.randint(2, w - 3), rnd.randint(6, h - 14)
        p.px(x, y, (255, 230, 120) if rnd.random() < .6 else (255, 160, 60))
    arr = ["....KK....", "...KhhK...", "..KhGGhK..", ".KhGGGGhK.", "KKKGGGGKKK", "...KGGK...", "...KGgK...", "...KKKK..."]
    p.paste(sprite(arr, PAL), w - 11, 1)
    return p.img

FACES = {
 "king": [".K..K..K..K..", ".KYKKYKKYKKY.", "KYYYYYYYYYYYK", "KYRYYBYYRYYYK", "KKKKKKKKKKKKK", "KHSSSSSSSSSHK", "KHSESSSSESSHK",
          "KHSSSSsSSSSHK", "KHWWSSSSSWWHK", ".KWWWsssWWWK.", ".KWWWWWWWWWK.", "..KKWWWWWKK..", "KRRKKWWWKKRRK", "KRqRRKKKRRRrK", "KRRRYRRRYRRrK", "KRRRRYRYRRRrK"],
 "knight": ["......KK.....", ".....KRqK....", "....KKRKK....", "..KKIIIIIKK..", ".KJIIIIIIIiK.", ".KJIIIIIIIiK.", ".KIKKKKKKKiK.", ".KIKEKKKEKiK.",
            ".KJIIIIIIIiK.", ".KJIIIKIIIiK.", ".KJIIIKIIIiK.", "..KiiIIIiiK..", "KBBKKKKKKKBBK", "KBcBBBBBBBBbK", "KBBBYYYYYBBbK", "KBBBBYYYBBBbK"],
 "lady": ["....KKKKK....", "...KHHHHHK...", "..KHHHHHHHK..", ".KHHSSSSSHHK.", ".KHSSSSSSSHK.", ".KHSESSSESHK.", ".KHSSSSSSSHK.",
          ".KHSSSqSSSHK.", ".KHHSSSSSHHK.", "KHHHKSSSKHHHK", "KHHKGGGGGKHHK", "KHKGGGGGGGKHK", ".KGGGhGhGGGK.", "KGGGGGhGGGGgK", "KGGGGGGGGGGgK", "KGGGGGGGGGGgK"],
}
def scene_court(w, h):
    """La cour : reine, chevalier et roi devant une tapisserie."""
    p = Pix(w, h)
    p.rect(0, 0, w - 1, h - 1, RED[1])
    for y in range(3, h, 7):
        for x in ((y // 7) % 2 * 4, ) and range((y // 7) % 2 * 4, w, 8):
            p.px(x, y, GOLD[2]); p.px(x - 1, y + 1, GOLD[1]); p.px(x + 1, y + 1, GOLD[1]); p.px(x, y + 2, GOLD[2])
    p.hline(0, w - 1, 0, GOLD[3]); p.hline(0, w - 1, 1, GOLD[1])
    for nm, fx, fy in (("lady", -1, h - 15), ("knight", w - 12, h - 15), ("king", (w - 13) // 2, h - 17)):
        im = sprite(FACES[nm], PAL)
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.split()[3].point(lambda a: 100 if a else 0))
        p.paste(sh, fx + 1, fy + 1); p.paste(im, fx, fy)
    return p.img

def scene_capital(w, h):
    """La capitale au coucher du soleil."""
    p = Pix(w, h)
    gradient(p, 0, 0, w - 1, h - 1, [(66, 46, 120), (190, 86, 120), (250, 160, 100), (255, 214, 140)])
    disc(p, 5, h - 9, 5, (255, 220, 140)); disc(p, 5, h - 9, 3, (255, 244, 200))
    for x, y in ((4, 4), (9, 6)):
        p.px(x, y, K); p.px(x - 1, y - 1, K); p.px(x + 1, y - 1, K)
    for x in range(w):
        m = int(h - 4 - 3 * math.exp(-((x - w / 2) / 9.0) ** 2))
        p.vline(x, m, h, GRASS[1]); p.px(x, m, GRASS[2])
    lay = layer(22, 20)
    stone_wall(lay, 2, 12, 19, 19, seed=9, bw=4, bh=3, moss=False)
    for i in range(0, 18, 3): lay.rect(2 + i, 10, 3 + i, 11, STONE[3])
    def tower(x, y0, wdt, roof=SLATE):
        stone_wall(lay, x, y0, x + wdt - 1, 19, seed=x, bw=3, bh=3, moss=False)
        n = wdt // 2 + 1
        for i in range(n):
            lay.hline(x - 1 + i, x + wdt - i, y0 - 1 - i * 2, roof[2]); lay.hline(x - 1 + i, x + wdt - i, y0 - i * 2, roof[1])
            lay.px(x - 1 + i, y0 - 1 - i * 2, roof[3])
        lay.px(x + wdt // 2, y0 + 3, (255, 214, 120))
    tower(0, 9, 4); tower(18, 9, 4); tower(7, 6, 8, ROOFR)
    lay.rect(9, 15, 12, 19, (40, 26, 20))
    put(p, lay, (w - 22) // 2 + 2, h - 22)
    p.vline(w // 2 + 2, 0, 3, WOOD[1]); p.rect(w // 2 + 3, 0, w // 2 + 6, 1, RED[2])
    return p.img

def vignette(p, x, y, w, h, scene):
    """Petit tableau encadré d'or."""
    p.rect(x - 2, y - 2, x + w + 1, y + h + 1, K)
    p.rect(x - 1, y - 1, x + w, y + h, GOLD[2]); p.hline(x - 1, x + w, y - 1, GOLD[4]); p.vline(x - 1, y - 1, y + h, GOLD[3])
    p.hline(x - 1, x + w, y + h, GOLD[1]); p.vline(x + w, y - 1, y + h, GOLD[1])
    p.paste(scene(w, h), x, y)
    p.rect(x, y, x + w - 1, y, (255, 255, 255, 40))

def framed_tile(p, x0, y0, x1, y1, scene, lines, vw=None, sub=None):
    """Bouton : cadre en bois + vignette peinte à gauche + libellé gravé à droite."""
    p.rect(x0, y0, x1, y1, K)
    planks(p, x0 + 1, y0 + 1, x1 - 1, y1 - 1, seed=x0 * 3 + y0, base=1)
    p.hline(x0 + 1, x1 - 1, y0 + 1, WOOD[3]); p.vline(x0 + 1, y0 + 1, y1 - 1, WOOD[2])
    p.hline(x0 + 1, x1 - 1, y1 - 1, WOOD[0]); p.vline(x1 - 1, y0 + 1, y1 - 1, WOOD[0])
    for cx, cy in ((x0 + 2, y0 + 2), (x1 - 3, y0 + 2), (x0 + 2, y1 - 3), (x1 - 3, y1 - 3)):
        p.px(cx, cy, IRON[4]); p.px(cx + 1, cy + 1, IRON[1])
    vh = y1 - y0 - 9
    vw = vw or vh
    vignette(p, x0 + 5, y0 + 5, vw, vh, scene)
    tx0 = x0 + vw + 8
    cx = (tx0 + x1 - 1) // 2
    n = len(lines) + (1 if sub else 0)
    ty = (y0 + y1) // 2 - (n * 10 - 2) // 2
    for i, ln in enumerate(lines):
        p.text_c(cx, ty + i * 10, ln, (255, 236, 190), True)
    if sub:
        p.text_c(cx, ty + len(lines) * 10, sub, GOLD[3], True)

# ---------------------------------------------------------------- page principale
def castle(p):
    # ---- sol / socle de l'île ----
    lay = layer(420, 30)
    for x in range(0, 420):
        bot = 12 + int(6 * math.sin(x / 23.0) + 4 * math.sin(x / 7.0)) + (10 if 30 < x < 390 else 0)
        edge = min(x, 419 - x)
        top = 4 if edge > 12 else 4 + (12 - edge) // 2
        lay.vline(x, top, min(28, bot), DIRT[1 + (x // 5 % 2)])
        lay.vline(x, top, top + 3, GRASS[2]); lay.px(x, top, GRASS[3])
        if x % 3 == 0: lay.px(x, top + 4, GRASS[1])
    rnd = random.Random(21)
    for _ in range(60):
        x, y = rnd.randint(4, 415), rnd.randint(10, 24)
        lay.px(x, y, STONE[2]); lay.px(x + 1, y, STONE[3])
    put(p, lay, -126, 170)

    # ---- tours latérales ----
    for tx, roof, fc in ((-70, SLATE, RED), (178, SLATE, BLUE)):
        lay = layer(68, 200)
        stone_wall(lay, 4, 36, 63, 199, seed=tx + 100)
        for i in range(6):
            stone_wall(lay, 2 + i * 11, 28, 9 + i * 11, 36, seed=i + tx, bw=4, bh=4, moss=False)
        lay.rect(2, 35, 65, 37, STONE[0])
        for i in range(30):
            half = 34 - int(i * 1.45)
            if half < 1: break
            y = 28 - i
            lay.hline(34 - half, 33 + half, y, roof[1] if (i % 3 == 0) else roof[2])
            lay.hline(34 - half, 34 - half + max(1, half // 3), y, roof[3])
            lay.hline(33 + half - max(1, half // 4), 33 + half, y, roof[0])
        top = 28 - 23
        lay.vline(34, top - 5, top, WOOD[1])
        for i in range(4):
            for j in range(8): lay.px(35 + j, top - 5 + i + int(math.sin(j / 2.0)), fc[2] if i < 3 else fc[1])
        for wy in (52, 172):
            lay.rect(30, wy, 37, wy + 10, K); lay.rect(31, wy + 1, 36, wy + 10, (40, 30, 50))
            lay.rect(31, wy + 4, 36, wy + 10, (255, 196, 90)); lay.vline(33, wy + 1, wy + 10, K); lay.hline(31, 36, wy + 6, K)
        put(p, lay, tx - 2, -24)

    # ---- mur central ----
    lay = layer(184, 180)
    stone_wall(lay, 0, 8, 183, 179, seed=3)
    for i in range(12):
        stone_wall(lay, i * 16 - 2, 0, i * 16 + 7, 8, seed=50 + i, bw=5, bh=4, moss=False)
    lay.rect(0, 7, 183, 9, STONE[0])
    put(p, lay, -4, -4)

    # ---- enseigne du titre ----
    lay = layer(130, 14)
    planks(lay, 0, 0, 129, 13, seed=8, pal=WOOD, base=2)
    lay.rect(2, 2, 127, 11, WOOD[1]); planks(lay, 3, 3, 126, 10, seed=9, base=3)
    for x in (4, 125):
        lay.px(x, 5, IRON[4]); lay.px(x, 8, IRON[4])
    put(p, lay, 23, 0)
    for x in (30, 145):   # chaînes
        for y in range(-5, 0, 2): p.px(x, y, IRON[2]); p.px(x, y + 1, IRON[0])
    # couronne au-dessus
    cr = outline(sprite(["K...K...K...K", "KYK.KYK.KYK.K", "KYYKYYYKYYYKY", "KYRYYBYYRYYYK", "KLLLLLLLLLLLK", "KyyyyyyyyyyyK"], PAL))
    p.paste(cr, 81, -10)

    # ---- boutons-tableaux ----
    framed_tile(p, 2, 16, 174, 55, scene_kingdom, ["Aller à mon", "royaume"], vw=92, sub="» Y aller")
    framed_tile(p, 2, 57, 87, 91, scene_build, ["Bâtiments"])
    framed_tile(p, 89, 57, 174, 91, scene_forge, ["Améliorer"])
    framed_tile(p, 2, 93, 87, 127, scene_court, ["Membres"])
    framed_tile(p, 89, 93, 174, 127, scene_capital, ["Capitale"])

    # ---- linteau de fer (cache le mot « Inventaire » vanilla) ----
    lay = layer(178, 10)
    lay.rect(0, 0, 177, 9, IRON[1]); lay.hline(0, 177, 0, IRON[3]); lay.hline(0, 177, 9, IRON[0])
    lay.rect(10, 2, 120, 8, LABEL_GREY)
    for x in range(4, 178, 12):
        if not (8 <= x <= 122): lay.px(x, 4, IRON[4]); lay.px(x, 5, IRON[2])
    put(p, lay, -1, 128, shadow=False)
    # ---- porte du château ----
    lay = layer(52, 36)
    for y in range(36):
        half = 26 if y > 12 else int(math.sqrt(max(0, 26 ** 2 - (13 - y) ** 2 * 4)))
        lay.hline(26 - half, 25 + half, y, STONE[0])
    for y in range(3, 36):
        half = 22 if y > 14 else int(math.sqrt(max(0, 22 ** 2 - (15 - y) ** 2 * 3)))
        if half > 0: planks(lay, 26 - half, y, 25 + half, y, seed=y, vertical=True, base=2)
    lay.vline(25, 4, 35, WOOD[0]); lay.vline(26, 4, 35, WOOD[0])
    for y in (14, 28):
        lay.rect(5, y, 46, y + 1, IRON[1]); lay.hline(5, 46, y, IRON[3])
    lay.px(21, 22, GOLD[3]); lay.px(30, 22, GOLD[3])
    put(p, lay, 62, 138)
    # bannières et torches
    for bx, col, em in ((22, RED, "Y"), (136, BLUE, "Y")):
        lay = layer(18, 30)
        lay.rect(0, 0, 17, 1, WOOD[1])
        lay.rect(1, 2, 16, 24, col[2]); lay.vline(1, 2, 24, col[3]); lay.vline(16, 2, 24, col[1])
        lay.rect(3, 2, 4, 24, GOLD[2]); lay.rect(13, 2, 14, 24, GOLD[2])
        for i in range(5): lay.hline(1 + i, 16 - i, 25 + i, col[2] if i < 4 else col[1])
        lay.paste(icon("shield") if col is RED else icon("crown"), 3 if col is RED else 2, 8)
        put(p, lay, bx, 139)
    torch(p, 50, 146); torch(p, 124, 146)

    # ---- accessoires au sol ----
    def barrel(x, y):
        l = layer(12, 14)
        planks(l, 0, 0, 11, 13, seed=x, vertical=True, base=2)
        for yy in (2, 10): l.hline(0, 11, yy, IRON[1])
        l.rect(1, 0, 10, 1, WOOD[1])
        put(p, l, x, y)
    def crate(x, y, s=12):
        l = layer(s, s)
        planks(l, 0, 0, s - 1, s - 1, seed=x + 7, base=3)
        l.rect(0, 0, s - 1, s - 1, WOOD[1]); l.rect(1, 1, s - 2, s - 2, WOOD[3])
        for i in range(s - 2): l.px(1 + i, 1 + i, WOOD[1])
        put(p, l, x, y)
    def coins_pile(x, y):
        l = layer(18, 9)
        for i in range(9):
            l.hline(i, 17 - i, 8 - i // 1 if False else 8 - i, GOLD[2] if i % 2 else GOLD[3])
        for k in range(6): l.px(2 + 2 * k + k % 2, 7 - k % 3, GOLD[4])
        put(p, l, x, y)
    barrel(-114, 162); barrel(-101, 165); crate(-126, 166)
    crate(276, 164, 14); barrel(263, 164); coins_pile(244, 170)
    p.paste(outline(icon("chest")), 228, 168)
    
    # buissons / fleurs le long du mur
    rnd = random.Random(30)
    for x in list(range(-60, 56, 7)) + list(range(122, 236, 7)):
        if 56 < x < 122: continue
        l = layer(8, 5)
        disc(l, 4, 3, 3, GRASS[1]); disc(l, 3, 2, 2, GRASS[2]); l.px(2, 1, GRASS[3])
        put(p, l, x, 171, shadow=False)
        if rnd.random() < .5: p.px(x + 3, 173, rnd.choice((RED[3], GOLD[3], (240, 240, 255))))
    # lierre
    for sx, sy, n in ((0, 20, 22), (174, 40, 30), (-60, 60, 20), (232, 20, 26)):
        x = sx
        for i in range(n):
            x += rnd.choice((-1, 0, 0, 1)); y = sy + i * 2
            p.px(x, y, GRASS[1]); p.px(x + rnd.choice((-1, 1)), y + 1, GRASS[2])
            if i % 3 == 0: p.px(x + 1, y, GRASS[3])

def panel_left(p):
    """Parchemin cloué sur la tour gauche : infos du royaume."""
    lay = layer(112, 142)
    lay.rect(0, 6, 111, 135, PARCH[3])
    rnd = random.Random(2)
    for _ in range(140):
        lay.px(rnd.randint(2, 109), rnd.randint(8, 133), PARCH[2 if rnd.random() < .7 else 4])
    lay.vline(0, 6, 135, PARCH[1]); lay.vline(111, 6, 135, PARCH[1])
    for yy in (0, 136):   # rouleaux
        lay.rect(-3, yy, 114, yy + 5, PARCH[2]); lay.hline(-3, 114, yy, PARCH[4]); lay.hline(-3, 114, yy + 5, PARCH[0])
        lay.rect(-6, yy + 1, -4, yy + 4, WOOD[2]); lay.rect(115, yy + 1, 117, yy + 4, WOOD[2])
    lay.rect(6, 13, 105, 25, RED[2]); lay.hline(6, 105, 13, RED[3]); lay.hline(6, 105, 25, RED[1])
    for x in (6, 105):
        lay.px(x, 13, PARCH[3]); lay.px(x, 25, PARCH[3])
    put(p, lay, -124, 16)
    p.text_outline_c(-68, 33, "Ton royaume", (255, 240, 200), RED[0])
    for i, ic in enumerate(("crown", "coins", "hourglass", "trophy", "people")):
        y = 48 + i * 21
        p.paste(outline(icon(ic)), -118, y + 2)
        if i < 4:
            for x in range(-116, -14, 2): p.px(x, y + 18, PARCH[1])
    for i, lab in enumerate(("Seigneur", "Trésor", "Revenu", "Rang", "Membres")):
        p.text(-100, 48 + i * 21, lab, (120, 78, 44), False)

def panel_right(p):
    """Panneau en bois sur la tour droite : infos du domaine."""
    lay = layer(112, 142)
    planks(lay, 0, 0, 111, 141, seed=12, base=3)
    lay.rect(4, 4, 107, 137, WOOD[1]); lay.rect(5, 5, 106, 136, PARCH[3])
    rnd = random.Random(5)
    for _ in range(120): lay.px(rnd.randint(6, 105), rnd.randint(6, 135), PARCH[2])
    for x, y in ((2, 2), (108, 2), (2, 138), (108, 138)):
        lay.rect(x - 1, y - 1, x + 1, y + 1, IRON[1]); lay.px(x, y, IRON[4])
    lay.rect(10, 9, 101, 21, BLUE[2]); lay.hline(10, 101, 9, BLUE[3]); lay.hline(10, 101, 21, BLUE[1])
    put(p, lay, 188, 16)
    p.text_outline_c(244, 29, "Ton domaine", (230, 240, 255), BLUE[0])
    for i, ic in enumerate(("map", "house", "wheat", "chest", "hammer")):
        y = 44 + i * 21
        p.paste(outline(icon(ic)), 196, y + 2)
        if i < 4:
            for x in range(198, 290, 2): p.px(x, y + 18, PARCH[1])
    for i, lab in enumerate(("Taille", "Bâtiments", "Production", "Entrepôts", "Amélioration")):
        p.text(214, 44 + i * 21, lab, (120, 78, 44), False)

def page_main(p, demo=False):
    castle(p)
    panel_left(p)
    panel_right(p)
    if demo:
        p.text_c(88, 3, "Royaume de Thozire", (255, 240, 200), True)
        vals = (("Thozire", (60, 40, 30)), ("12 480 écus", (176, 112, 26)), ("+356 écus/min", (40, 120, 40)),
                ("#2 sur 14", (40, 80, 170)), ("2 / 3", (60, 40, 30)))
        for i, (v, c) in enumerate(vals): p.text(-100, 57 + i * 21, v, c, False)
        vals = (("81 × 81", (60, 40, 30)), ("5 / 12", (60, 40, 30)), ("98 objets/min", (40, 120, 40)),
                ("1 842 écus", (176, 112, 26)), ("8 000 écus", (40, 80, 170)))
        for i, (v, c) in enumerate(vals): p.text(214, 53 + i * 21, v, c, False)

def preview(path):
    p = Pix(W, H, OX, OY)
    page_main(p, demo=True)
    bg = Image.new("RGBA", (W + 40, H + 20), (0, 0, 0, 255))
    rnd = random.Random(1)
    d = bg.load()
    for y in range(bg.height):
        for x in range(bg.width):
            v = 24 + ((x // 2 + y // 2) % 2) * 2
            d[x, y] = (v + 10, v, v + 6, 255)
    bg.alpha_composite(p.img, (20, 10))
    bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST).save(path)
    return p

if __name__ == "__main__":
    preview("/home/claude/rp/kingdom_main.png")
    print("ok")
