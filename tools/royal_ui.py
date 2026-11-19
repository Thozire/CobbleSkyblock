"""Interface « Royaumes » en pixel art (1 pixel de texture = 1 pixel d'interface).

- Le fond de chaque page est un grand dessin découpé en tuiles (< 256 px) affichées comme
  glyphes de police dans le titre du coffre.
- Les textes dynamiques (trésor, classement…) utilisent la police Minecraft d'origine décalée
  verticalement (polices cobbleislands:t<dy>) et positionnée avec des espaces de largeur connue.
Coordonnées : repère du coffre vanilla (0,0 = coin haut-gauche du coffre 176x222).
"""
import json, math, os, random, sys
from PIL import Image, ImageDraw

MC = "/home/claude/mcassets/assets/minecraft"
OX, OY = 132, 80           # position du coin du coffre dans le dessin (64 px au-dessus pour les flèches des tours)
W, H = 440, 326            # taille du dessin
TILE_W, TILE_H = 220, 163  # tuiles < 256 px

# ---------- palette ----------
OUT = (34, 20, 14)
WOOD = [(70, 42, 24), (96, 60, 34), (122, 78, 44), (150, 100, 58), (178, 128, 78)]
PARCH = [(118, 74, 44), (196, 150, 104), (222, 184, 136), (238, 208, 160), (248, 228, 190), (255, 242, 214)]
RED = [(84, 14, 20), (132, 26, 32), (176, 40, 44), (214, 64, 58), (240, 110, 90)]
GOLD = [(96, 56, 12), (166, 104, 24), (216, 156, 44), (246, 200, 76), (255, 240, 160)]
IRON = [(30, 30, 38), (58, 58, 70), (96, 96, 110), (140, 140, 156), (196, 196, 210)]
GREEN = [(24, 58, 24), (44, 104, 40), (72, 150, 56), (112, 196, 80), (176, 236, 130)]
BLUE = [(18, 34, 74), (34, 66, 130), (58, 104, 180), (98, 150, 224), (160, 200, 255)]
PURPLE = [(48, 22, 70), (82, 40, 120), (122, 64, 170), (164, 106, 210), (210, 170, 245)]
LABEL_GREY = (64, 64, 64)

# ---------- police Minecraft ----------
class MCFont:
    def __init__(self):
        d = json.load(open(f"{MC}/font/include/default.json"))
        self.glyphs = {}
        for p in d["providers"]:
            img = Image.open(f"{MC}/textures/" + p["file"].split(":")[1]).convert("RGBA")
            rows = p["chars"]
            cw, ch = img.width // len(rows[0]), img.height // len(rows)
            h = p.get("height", 8)
            scale = h / ch
            for r, line in enumerate(rows):
                for c, char in enumerate(line):
                    if char in ("\u0000", " ") or char in self.glyphs: continue
                    cell = img.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
                    px = cell.load(); w = 0
                    for x in range(cw - 1, -1, -1):
                        if any(px[x, y][3] for y in range(ch)): w = x + 1; break
                    self.glyphs[char] = (cell, int(0.5 + w * scale) + 1, p.get("ascent", 7), ch)
    def width(self, s, bold=False):
        n = 0
        for ch in s:
            if ch == " ": n += 4
            elif ch in self.glyphs: n += self.glyphs[ch][1]
            else: n += 6
            if bold and ch != " ": n += 1
        return n
    def draw(self, img, x, y, s, color, shadow=True, bold=False, scale=1):
        """Dessine le texte comme en jeu (y = haut des lettres ascii)."""
        if shadow:
            sc = tuple(int(c * 0.25) for c in color[:3])
            self.draw(img, x + scale, y + scale, s, sc, False, bold, scale)
        for ch in s:
            if ch == " ":
                x += 4 * scale; continue
            g = self.glyphs.get(ch)
            if not g: x += 6 * scale; continue
            cell, adv, asc, chh = g
            top = y + (7 - asc) * scale
            mask = cell.split()[3]
            if scale != 1:
                mask = mask.resize((cell.width * scale, cell.height * scale), Image.NEAREST)
            col = Image.new("RGBA", mask.size, color + (255,) if len(color) == 3 else color)
            img.paste(col, (x, top), mask)
            if bold: img.paste(col, (x + scale, top), mask)
            x += (adv + (1 if bold else 0)) * scale
        return x

FONT = MCFont()

# ---------- toile ----------
class Canvas:
    def __init__(self):
        self.img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
    def P(self, x, y): return (x + OX, y + OY)
    def px(self, x, y, c):
        X, Y = self.P(x, y)
        if 0 <= X < W and 0 <= Y < H: self.img.putpixel((X, Y), c + (255,) if len(c) == 3 else c)
    def rect(self, x0, y0, x1, y1, c):
        if x1 < x0 or y1 < y0: return
        self.d.rectangle([*self.P(x0, y0), *self.P(x1, y1)], fill=c + (255,) if len(c) == 3 else c)
    def hline(self, x0, x1, y, c): self.rect(x0, y, x1, y, c)
    def vline(self, x, y0, y1, c): self.rect(x, y0, x, y1, c)
    def outline(self, x0, y0, x1, y1, c, round_=True):
        self.hline(x0 + (1 if round_ else 0), x1 - (1 if round_ else 0), y0, c)
        self.hline(x0 + (1 if round_ else 0), x1 - (1 if round_ else 0), y1, c)
        self.vline(x0, y0 + (1 if round_ else 0), y1 - (1 if round_ else 0), c)
        self.vline(x1, y0 + (1 if round_ else 0), y1 - (1 if round_ else 0), c)
    def text(self, x, y, s, color, shadow=True, bold=False, scale=1):
        X, Y = self.P(x, y)
        return FONT.draw(self.img, X, Y, s, color, shadow, bold, scale) - OX
    def text_c(self, cx, y, s, color, shadow=True, bold=False, scale=1):
        return self.text(cx - FONT.width(s, bold) * scale // 2, y, s, color, shadow, bold, scale)

# ---------- matériaux ----------
def wood_panel(cv, x0, y0, x1, y1, seed=1, vertical=False):
    rnd = random.Random(seed)
    cv.rect(x0, y0, x1, y1, WOOD[2])
    if not vertical:
        y = y0 + 1
        while y < y1:
            h = rnd.choice((5, 6, 7))
            base = rnd.choice((1, 2, 2, 3))
            cv.rect(x0 + 1, y, x1 - 1, min(y1 - 1, y + h - 1), WOOD[base])
            cv.hline(x0 + 1, x1 - 1, y, WOOD[min(4, base + 1)])
            for _ in range((x1 - x0) // 9):
                gx = rnd.randint(x0 + 2, x1 - 6); gy = rnd.randint(y + 1, min(y1 - 1, y + h - 2))
                cv.hline(gx, gx + rnd.randint(2, 6), gy, WOOD[max(0, base - 1)])
            if y + h < y1: cv.hline(x0 + 1, x1 - 1, y + h, WOOD[0])
            # joints verticaux décalés
            jx = rnd.randint(x0 + 10, x1 - 10)
            cv.vline(jx, y + 1, min(y1 - 1, y + h - 1), WOOD[0])
            y += h + 1
    cv.outline(x0, y0, x1, y1, OUT)

def nail(cv, x, y):
    cv.px(x, y, IRON[3]); cv.px(x + 1, y, IRON[2]); cv.px(x, y + 1, IRON[2]); cv.px(x + 1, y + 1, IRON[1])

def parchment(cv, x0, y0, x1, y1, seed=2, torn=True):
    rnd = random.Random(seed)
    for y in range(y0, y1 + 1):
        inset_l = rnd.choice((0, 0, 0, 1)) if torn else 0
        inset_r = rnd.choice((0, 0, 0, 1)) if torn else 0
        cv.hline(x0 + inset_l, x1 - inset_r, y, PARCH[4])
        cv.px(x0 + inset_l, y, PARCH[1]); cv.px(x1 - inset_r, y, PARCH[1])
    for x in range(x0, x1 + 1):
        if rnd.random() < 0.85 or not torn:
            cv.px(x, y0, PARCH[1]); cv.px(x, y1, PARCH[1])
    # ombrage des bords et taches
    for y in range(y0 + 1, y1):
        cv.px(x0 + 1, y, PARCH[3]); cv.px(x1 - 1, y, PARCH[3])
    for x in range(x0 + 1, x1):
        cv.px(x, y1 - 1, PARCH[3]); cv.px(x, y0 + 1, PARCH[5])
    for _ in range((x1 - x0) * (y1 - y0) // 60):
        x = rnd.randint(x0 + 3, x1 - 3); y = rnd.randint(y0 + 3, y1 - 3)
        cv.px(x, y, PARCH[3] if rnd.random() < 0.8 else PARCH[2])

def ribbon(cv, x0, x1, y0, h=20, colors=RED):
    """Grand ruban horizontal avec bouts repliés et galons dorés."""
    # bouts repliés
    for side in (-1, 1):
        ex = x0 - 14 if side < 0 else x1 + 1
        for i in range(14):
            xx = ex + (13 - i if side < 0 else i)
            top = y0 + 5
            cut = abs(i - 0) if False else 0
            for y in range(top, top + h):
                notch = (side < 0 and xx < x0 - 9 and abs(y - (top + h // 2)) < (x0 - 9 - xx)) or \
                        (side > 0 and xx > x1 + 9 and abs(y - (top + h // 2)) < (xx - x1 - 9))
                if not notch: cv.px(xx, y, colors[1])
        cv.rect(x0 - 4 if side < 0 else x1 + 1, y0 + h, x0 - 1 if side < 0 else x1 + 4, y0 + h + 4, colors[0])
    cv.rect(x0, y0, x1, y0 + h - 1, colors[2])
    cv.hline(x0, x1, y0 + 1, colors[3]); cv.hline(x0, x1, y0 + h - 3, colors[1])
    cv.hline(x0, x1, y0 + 3, GOLD[3]); cv.hline(x0, x1, y0 + h - 5, GOLD[2])
    for x in range(x0 + 2, x1, 4): cv.px(x, y0 + 3, GOLD[4])
    cv.hline(x0, x1, y0, OUT); cv.hline(x0, x1, y0 + h, OUT)
    cv.vline(x0, y0, y0 + h, OUT); cv.vline(x1, y0, y0 + h, OUT)

def crown(cv, cx, y):
    pts = [(-12, 10), (-12, 2), (-7, 6), (-3, -2), (0, -4), (3, -2), (7, 6), (12, 2), (12, 10)]
    poly = [cv.P(cx + a, y + b) for a, b in pts]
    cv.d.polygon(poly, fill=GOLD[3] + (255,), outline=OUT + (255,))
    cv.rect(cx - 12, y + 8, cx + 12, y + 11, GOLD[2]); cv.outline(cx - 12, y + 8, cx + 12, y + 11, OUT, False)
    for gx, col in ((-7, RED[3]), (0, BLUE[3]), (7, GREEN[3])):
        cv.rect(cx + gx - 1, y + 9, cx + gx + 1, y + 10, col)
    cv.rect(cx - 1, y - 1, cx + 1, y + 1, BLUE[3]); cv.px(cx - 1, y - 1, BLUE[4])
    for a in (-12, 12, -3, 3): cv.px(cx + a, y + 1, GOLD[4])
    cv.hline(cx - 10, cx + 10, y + 7, GOLD[4])

def flag(cv, x, y, colors, emblem_col=GOLD[3], mirror=False):
    cv.vline(x, y, y + 26, WOOD[0]); cv.vline(x + 1, y, y + 26, WOOD[3]); cv.px(x, y - 1, GOLD[3]); cv.px(x + 1, y - 1, GOLD[3])
    d = -1 if mirror else 1
    for i in range(16):
        wave = int(1.5 * math.sin(i / 3))
        for j in range(10):
            xx = x + 2 + i if not mirror else x - 1 - i
            col = colors[2] if j > 1 else colors[3]
            if j == 9: col = colors[1]
            cv.px(xx, y + 1 + j + wave, col)
        cv.px(x + 2 + i if not mirror else x - 1 - i, y + wave, OUT); cv.px(x + 2 + i if not mirror else x - 1 - i, y + 11 + wave, OUT)
    cx = x + 9 if not mirror else x - 8
    cv.rect(cx - 1, y + 4, cx + 1, y + 7, emblem_col)

def arrow_deco(cv, x, y, mirror=False):
    s = -1 if mirror else 1
    for i in range(18):
        cv.px(x + s * i, y + i // 2, WOOD[3]); cv.px(x + s * i, y + i // 2 + 1, WOOD[1])
    # pointe
    tx, ty = x + s * 18, y + 9
    for k in range(4):
        cv.vline(tx + s * k, ty - 3 + k, ty + 3 - k, IRON[3] if k < 2 else IRON[2])
    # empennage
    for k in range(4):
        cv.px(x - s * k, y - 2 + k // 2, RED[3]); cv.px(x - s * k, y + 2 + k // 2, RED[2])

def iron_corner(cv, x, y, fx=1, fy=1):
    for i in range(9):
        cv.px(x + fx * i, y, IRON[2]); cv.px(x + fx * i, y + fy, IRON[1])
        cv.px(x, y + fy * i, IRON[2]); cv.px(x + fx, y + fy * i, IRON[1])
    for i in range(10): cv.px(x + fx * i, y - fy, OUT); cv.px(x - fx, y + fy * i, OUT)
    nail(cv, x + fx * 3 - (1 if fx < 0 else 0), y + fy * 3 - (1 if fy < 0 else 0))

# ---------- éléments d'interface ----------
def slot_xy(slot):
    if slot < 54:
        r, c = divmod(slot, 9)
        return 8 + 18 * c, 18 + 18 * r
    i = slot - 54
    if i < 27:
        r, c = divmod(i, 9)
        return 8 + 18 * c, 140 + 18 * r
    return 8 + 18 * (i - 27), 198

def icon_box(cv, slot, colors=PARCH):
    x, y = slot_xy(slot)
    cv.rect(x - 1, y - 1, x + 16, y + 16, OUT)
    cv.rect(x, y, x + 15, y + 15, PARCH[3])
    cv.hline(x, x + 15, y, PARCH[2]); cv.vline(x, y, y + 15, PARCH[2])
    cv.hline(x + 1, x + 15, y + 15, PARCH[5]); cv.vline(x + 15, y + 1, y + 15, PARCH[5])

def wide_button(cv, slot_first, n, colors, label, sub=None, x0=None, x1=None):
    """Bouton peint ; l'icône va dans la première case, le reste du bouton couvre n cases."""
    x, y = slot_xy(slot_first)
    x0 = x - 2 if x0 is None else x0
    x1 = x + 18 * n - 3 if x1 is None else x1
    y0, y1 = y - 1, y + 16
    cv.rect(x0 + 1, y0 + 1, x1 + 1, y1 + 2, (0, 0, 0, 90))  # ombre portée
    cv.rect(x0, y0, x1, y1, colors[2])
    cv.hline(x0 + 1, x1 - 1, y0 + 1, colors[4]); cv.hline(x0 + 1, x1 - 1, y0 + 2, colors[3])
    cv.hline(x0 + 1, x1 - 1, y1 - 1, colors[1]); cv.hline(x0 + 1, x1 - 1, y1 - 2, colors[1])
    # grain de planche
    rnd = random.Random(slot_first)
    for _ in range(n * 3):
        gx = rnd.randint(x0 + 20, x1 - 6); gy = rnd.randint(y0 + 4, y1 - 4)
        cv.hline(gx, gx + rnd.randint(2, 5), gy, colors[1])
    cv.outline(x0, y0, x1, y1, OUT)
    nail(cv, x1 - 4, y0 + 3); nail(cv, x1 - 4, y1 - 4)
    icon_box(cv, slot_first)
    tx = x + 21
    if sub:
        cv.text(tx, y + 1, label, (255, 250, 230), True)
        cv.text(tx, y + 9, sub, colors[4], False)
    else:
        cv.text(tx, y + 4, label, (255, 250, 230), True)

def round_button(cv, slot, colors, glyph=None):
    x, y = slot_xy(slot)
    cv.rect(x - 1, y - 1, x + 16, y + 16, OUT)
    cv.rect(x, y, x + 15, y + 15, colors[2])
    cv.hline(x, x + 15, y, colors[4]); cv.hline(x, x + 15, y + 1, colors[3])
    cv.hline(x, x + 15, y + 15, colors[1]); cv.hline(x, x + 15, y + 14, colors[1])

def hanging_scroll(cv, x0, y0, x1, y1, seed=5):
    # cordes
    for x in (x0 + 8, x1 - 8):
        cv.vline(x, y0 - 10, y0, WOOD[3]); cv.px(x, y0 - 11, IRON[3])
    # rouleaux haut/bas
    for yy in (y0, y1):
        cv.rect(x0 - 3, yy - 2, x1 + 3, yy + 2, PARCH[2]); cv.hline(x0 - 3, x1 + 3, yy - 2, PARCH[4])
        cv.outline(x0 - 3, yy - 3, x1 + 3, yy + 3, OUT)
        for xx in (x0 - 5, x1 + 4):
            cv.rect(xx, yy - 2, xx + 1, yy + 2, WOOD[2]); cv.outline(xx - 1, yy - 3, xx + 2, yy + 3, OUT, False)
    parchment(cv, x0, y0 + 3, x1, y1 - 3, seed, torn=False)

def shield(cv, cx, y, colors=BLUE):
    w = 10
    for i in range(22):
        half = w if i < 12 else max(0, w - (i - 11))
        cv.hline(cx - half, cx + half, y + i, colors[2] if i % 6 else colors[3])
        cv.px(cx - half, y + i, OUT); cv.px(cx + half, y + i, OUT)
        cv.hline(cx - half + 1, cx - 1, y + i, colors[2])
        cv.hline(cx, cx + half - 1, y + i, colors[1])
    cv.hline(cx - w, cx + w, y, OUT)
    # croix dorée
    cv.rect(cx - 1, y + 3, cx + 1, y + 17, GOLD[3]); cv.rect(cx - 6, y + 7, cx + 6, y + 9, GOLD[3])
    cv.px(cx, y + 8, GOLD[4])

def notice_board(cv, x0, y0, x1, y1):
    # poteaux + planche
    wood_panel(cv, x0, y0, x1, y1, seed=9)
    parchment(cv, x0 + 4, y0 + 14, x1 - 4, y1 - 4, seed=11)
    # punaises
    for x, y in ((x0 + 8, y0 + 17), (x1 - 9, y0 + 17)):
        cv.rect(x, y, x + 1, y + 1, RED[3]); cv.px(x, y, RED[4])

def castle_strip(cv, x0, y0, x1, y1):
    """Bandeau illustré : ciel au crépuscule, château et collines (pixel art)."""
    sky = [(52, 46, 96), (78, 60, 120), (120, 76, 136), (176, 98, 120), (226, 140, 110), (248, 186, 120)]
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        cv.hline(x0, x1, y, sky[min(5, int(t * 6))])
    rnd = random.Random(3)
    for _ in range(26):
        cv.px(rnd.randint(x0 + 2, x1 - 2), rnd.randint(y0 + 2, y0 + (y1 - y0) // 2), (255, 240, 220))
    # soleil
    sx, sy = x1 - 40, y1 - 18
    for r in range(9, 0, -1):
        col = (255, 214, 140) if r < 7 else (250, 180, 120)
        cv.d.ellipse([*cv.P(sx - r, sy - r), *cv.P(sx + r, sy + r)], fill=col + (255,))
    # collines
    for x in range(x0, x1 + 1):
        h1 = int(8 + 5 * math.sin((x - x0) / 14))
        h2 = int(4 + 3 * math.sin((x - x0) / 9 + 2))
        cv.vline(x, y1 - h1, y1, (66, 92, 86)); cv.vline(x, y1 - h2, y1, (58, 112, 64))
        cv.px(x, y1 - h2, (90, 150, 80))
    # château
    cx, base = x0 + 46, y1 - 9
    stone, shade, roof = (120, 112, 140), (88, 80, 110), RED[2]
    def tower(tx, w, h, cone=True):
        cv.rect(tx - w // 2, base - h, tx + w // 2, base, stone)
        cv.vline(tx - w // 2, base - h, base, shade)
        cv.outline(tx - w // 2 - 1, base - h - 1, tx + w // 2 + 1, base + 1, OUT, False)
        if cone:
            for i in range(w // 2 + 3):
                cv.hline(tx - w // 2 - 1 + i, tx + w // 2 + 1 - i, base - h - 2 - i, roof)
            cv.vline(tx, base - h - w // 2 - 7, base - h - w // 2 - 4, WOOD[0]); cv.px(tx + 1, base - h - w // 2 - 7, GOLD[3])
        cv.px(tx, base - h + 4, (255, 210, 120)); cv.px(tx, base - h + 5, (255, 210, 120))
    cv.rect(cx - 20, base - 10, cx + 20, base, stone); cv.outline(cx - 21, base - 11, cx + 21, base + 1, OUT, False)
    for k in range(-20, 21, 3): cv.rect(cx + k, base - 12, cx + k + 1, base - 11, stone)
    tower(cx - 20, 7, 18); tower(cx + 20, 7, 18); tower(cx, 9, 26); tower(cx - 10, 5, 14, False); tower(cx + 10, 5, 14, False)
    cv.rect(cx - 2, base - 6, cx + 2, base, (40, 28, 30))

# ---------- page principale ----------
def frame(cv):
    """Cadre commun : planches, coins en fer, ruban du titre, couronne, drapeaux, flèches."""
    wood_panel(cv, -128, -8, 304, 244, seed=1)
    cv.rect(-127, 241, 303, 243, WOOD[0])
    for (x, y, fx, fy) in ((-126, -6, 1, 1), (302, -6, -1, 1), (-126, 242, 1, -1), (302, 242, -1, -1)):
        iron_corner(cv, x, y, fx, fy)
    flag(cv, -116, -24, BLUE); flag(cv, 292, -24, RED, mirror=True)
    arrow_deco(cv, -90, -17); arrow_deco(cv, 266, -17, mirror=True)
    ribbon(cv, -56, 232, -16, 17)
    crown(cv, 88, -21)

def side_left(cv):
    hanging_scroll(cv, -120, 8, -14, 236, seed=31)
    shield(cv, -67, 18)
    cv.text_c(-67, 44, "~ Ton royaume ~", PARCH[0], False)
    cv.hline(-112, -22, 54, PARCH[2])

def side_right(cv, title="Classement"):
    notice_board(cv, 186, 2, 298, 238)
    cv.text_c(242, 6, title, (255, 236, 190), True)

def iron_bar(cv):
    """Barre de fer : gris #404040 exact sous le mot « Inventaire » du jeu (il devient invisible)."""
    cv.rect(-4, 124, 180, 138, OUT)
    cv.rect(-3, 125, 179, 137, LABEL_GREY)
    cv.hline(-3, 179, 125, (84, 84, 84)); cv.hline(-3, 179, 137, (44, 44, 44))
    for x in (0, 174): nail(cv, x, 130)

def page_main(cv, demo=False):
    frame(cv)
    side_left(cv)
    side_right(cv)
    parchment(cv, -4, 2, 180, 122, seed=21)
    cv.text_c(88, 6, "Que veux-tu faire, seigneur ?", PARCH[0], False)
    L, R = (2, 85), (91, 174)
    wide_button(cv, 9, 4, GREEN, "Domaine", x0=L[0], x1=L[1])
    wide_button(cv, 14, 4, WOOD, "Bâtiments", x0=R[0], x1=R[1])
    wide_button(cv, 18, 4, GOLD, "Marché", x0=L[0], x1=L[1])
    wide_button(cv, 23, 4, BLUE, "Ma cour", x0=R[0], x1=R[1])
    wide_button(cv, 27, 4, PURPLE, "Améliorer", x0=L[0], x1=L[1])
    wide_button(cv, 32, 4, GOLD, "Palmarès", x0=R[0], x1=R[1])
    wide_button(cv, 36, 4, RED, "Capitale", x0=L[0], x1=L[1])
    wide_button(cv, 41, 4, BLUE, "Visiter", x0=R[0], x1=R[1])
    round_button(cv, 45, WOOD); round_button(cv, 53, RED)
    iron_bar(cv)
    wide_button(cv, 55, 7, GOLD, "", x0=-2, x1=178)
    parchment(cv, -4, 158, 180, 172, seed=41)
    castle_strip(cv, -4, 176, 180, 238)
    cv.text_c(120, 184, "ROYAUMES", GOLD[3], True, True, 2)
    if demo:
        demo_text(cv)

def demo_text(cv):
    """Textes dynamiques d'exemple (en jeu, envoyés par le serveur)."""
    cv.text_c(88, -8, "Royaume de Thozire", (255, 244, 214), True, True)
    lines = [("Seigneur", "Thozire", (60, 40, 30)), ("Trésor", "12 480 écus", GOLD[2]), ("Revenu", "+356 écus/min", GREEN[2]),
             ("Rang", "#2 sur 14", BLUE[2]), ("Bâtiments", "5", (60, 40, 30)), ("Cour", "2 / 3 membres", (60, 40, 30)),
             ("Domaine", "81 x 81", (60, 40, 30))]
    y = 62
    for k, v, c in lines:
        cv.text(-110, y, k, PARCH[1], False); cv.text(-110, y + 10, v, c, False); y += 24
    top = [("Valoria", "48 210"), ("Thozire", "12 480"), ("Brumeval", "9 950"), ("Kaelor", "4 300"), ("Aubépine", "1 120"),
           ("Corbeval", "860"), ("Montfroid", "540"), ("Lisière", "310"), ("Hautbois", "120")]
    y = 22
    for i, (n, v) in enumerate(top):
        col = [GOLD[2], IRON[3], (200, 110, 60)][i] if i < 3 else PARCH[1]
        cv.text(194, y, f"{i + 1}.", col, False); cv.text(206, y, n, (60, 40, 30), False)
        cv.text(206, y + 10, v + " écus", GOLD[1], False); y += 23
    cv.text(48, 145, "Vendre : ", (255, 250, 230), True)
    cv.text(48 + 53, 145, "1 842 écus", (255, 236, 150), True)
    cv.text_c(88, 161, "Astuce : améliore ta mine !", PARCH[0], False)

def preview(page_fn, path, icons):
    cv = Canvas()
    page_fn(cv, demo=True)
    img = cv.img.copy()
    for slot, ic in icons.items():
        x, y = slot_xy(slot)
        img.alpha_composite(Image.open(ic).convert("RGBA").resize((16, 16), Image.NEAREST), (x + OX, y + OY))
    # simulation de l'écran de jeu (échelle x3)
    bg = Image.new("RGBA", (W + 40, H + 30), (36, 48, 34, 255))
    bg.alpha_composite(Image.new("RGBA", bg.size, (0, 0, 0, 110)))
    bg.alpha_composite(img, (20, 15))
    bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST).save(path)

if __name__ == "__main__":
    I = "/home/claude/rp/royaumes/assets/cobbleislands/textures/item/ui/"
    icons = {45: I + "7209.png", 53: I + "7210.png", 9: I + "7201.png", 14: I + "7202.png", 18: I + "7203.png", 23: I + "7204.png",
             27: I + "7205.png", 32: I + "7206.png", 36: I + "7207.png", 41: I + "7208.png", 55: I + "7231.png"}
    preview(page_main, "/home/claude/rp/royal_main.png", icons)
    print("ok")
