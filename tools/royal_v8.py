"""Interface « Royaumes » v8 — château unique, bannière-titre « Royaume », boutons peints.

Repère : coordonnées du coffre vanilla (0,0 = coin haut-gauche du coffre 176x222).
Cases cliquables : x 8..169, y 18..125 (+ inventaire caché y 140..213).
"""
import math, random
import numpy as np
from PIL import Image
from royal_ui import FONT, OX, OY, W, H
from royal_kingdom import Pix, outline, layer, sprite
from royal_art import *
from royal_scenes import SCENES, cloud
from royal_titlefont import title_glyph

MORTAR = (40, 34, 52)
BRIGHT_GRAD = [(255, 255, 250), (255, 252, 232), (255, 244, 206), (252, 232, 178), (246, 218, 150), (250, 226, 166), (236, 204, 136),
               (222, 186, 116), (206, 166, 96)]

# ---------------------------------------------------------------- maçonnerie
def blocks(p, x0, y0, x1, y1, seed, bw=10, bh=6, pal=STONE, base=4, mortar=MORTAR, var=1, moss=0.0):
    rnd = random.Random(seed)
    p.rect(x0, y0, x1, y1, mortar)
    row = 0; y = y0
    while y <= y1:
        x = x0 - (bw // 2 if row % 2 else 0) - rnd.randint(0, 2)
        while x <= x1:
            w = bw + rnd.choice((-2, -1, 0, 0, 1, 2))
            b = max(1, min(len(pal) - 3, base + rnd.randint(-var, var)))
            sx0, sx1 = max(x0, x + 1), min(x1, x + w - 1)
            sy0, sy1 = y + 1, min(y1, y + bh - 1)
            if sx1 >= sx0 and sy1 >= sy0:
                warm = rnd.random() < 0.18
                base_c = pal[b]
                if warm: base_c = tuple(min(255, int(c * f)) for c, f in zip(base_c, (1.08, 1.02, 0.94)))
                p.rect(sx0, sy0, sx1, sy1, base_c)
                p.hline(sx0, sx1, sy0, pal[b + 1]); p.vline(sx0, sy0, sy1, pal[b + 1])
                p.hline(sx0 + 1, sx1, sy1, pal[b - 1]); p.vline(sx1, sy0 + 1, sy1, pal[b - 1])
                p.px(sx0, sy0, pal[b + 2])
                if rnd.random() < .35:
                    cx, cy = rnd.randint(sx0 + 1, max(sx0 + 1, sx1 - 1)), rnd.randint(sy0 + 1, max(sy0 + 1, sy1 - 1))
                    p.px(cx, cy, pal[b - 1]); p.px(cx + 1, cy, pal[b + 1])
                if rnd.random() < .08 and sx1 - sx0 > 4:      # fissure
                    cx = rnd.randint(sx0 + 1, sx1 - 2)
                    for k in range(sy1 - sy0): p.px(cx + (k % 2), sy0 + k, pal[b - 2])
                if moss and rnd.random() < moss:
                    for k in range(rnd.randint(2, 5)):
                        p.px(rnd.randint(sx0, sx1), sy1 - rnd.randint(0, 1), LEAF[rnd.choice((1, 2, 3))])
            x += w
        y += bh; row += 1

def shade_columns(p, x0, x1, y0, y1, light=0.30, lo=0.60, hi=1.12):
    a = np.array(p.img).astype(np.float32)
    X0, X1, Y0, Y1 = x0 + p.ox, x1 + p.ox, max(0, y0 + p.oy), y1 + p.oy
    for X in range(max(0, X0), min(a.shape[1], X1 + 1)):
        t = (X - X0) / max(1, X1 - X0)
        f = lo + (hi - lo) * max(0.0, math.cos((t - light) * math.pi / 1.45))
        a[Y0:Y1 + 1, X, :3] *= f
    p.img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def arch_mask(x0, y0, x1, y1, rise):
    cx, half = (x0 + x1) / 2, (x1 - x0) / 2
    def inside(x, y):
        if x < x0 or x > x1 or y > y1: return False
        if y >= y0 + rise: return True
        t = (x - cx) / max(1, half)
        return y >= y0 + rise - rise * math.sqrt(max(0, 1 - t * t))
    return inside

def arch_opening(p, x0, y0, x1, y1, rise, fill_fn, frame=DRESS, voussoir=5, key=True):
    """Ouverture en arc : claveaux en pierre de taille, clé de voûte dorée, intérieur fill_fn(Pix, w, h)."""
    outer = arch_mask(x0 - voussoir, y0 - voussoir, x1 + voussoir, y1, rise + voussoir // 2)
    inner = arch_mask(x0, y0, x1, y1, rise)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    inside = Pix(w, h); fill_fn(inside, w, h)
    cxm = (x0 + x1) / 2; cym = y0 + rise
    nseg = 11
    def seg_of(x, y):
        if y < cym:
            return int((math.atan2(y - cym, x - cxm) + math.pi) / (math.pi / nseg))
        return 100 + (y - y0) // 8
    for y in range(y0 - voussoir - 1, y1 + 1):
        for x in range(x0 - voussoir - 1, x1 + voussoir + 2):
            o, i = outer(x, y), inner(x, y)
            if i:
                c = inside.img.getpixel((x - x0, y - y0))
                if c[3]: p.px(x, y, c)
            elif o:
                near_in = inner(x + 1, y) or inner(x - 1, y) or inner(x, y + 1) or inner(x, y - 1)
                near_out = not (outer(x + 1, y) and outer(x - 1, y) and outer(x, y - 1))
                if near_in or near_out:
                    p.px(x, y, K); continue
                s = seg_of(x, y)
                b = 4 if s % 2 else 3
                # biseau : bord intérieur éclairé en bas-droite (creux), bord extérieur éclairé en haut-gauche
                if inner(x + 1, y + 1) and not inner(x, y): b += 1
                p.px(x, y, frame[b])
                if seg_of(x + 1, y) != s or seg_of(x, y + 1) != s:
                    p.px(x, y, frame[1])
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if inner(x, y):
                d = 0
                if not inner(x, y - 1) or not inner(x - 1, y): d = 120
                elif not inner(x, y - 2) or not inner(x - 2, y): d = 80
                elif not inner(x, y - 3) or not inner(x - 3, y): d = 40
                if d: p.px(x, y, (10, 4, 14, d))
    if key:
        kx = int(cxm)
        rows = ["KKKKKKKKK", "K6555554K", ".K55443K.", ".K54433K.", "..K433K..", "..K322K..", "...KKK..."]
        pal = {"K": K, "6": GOLD[6], "5": GOLD[5], "4": GOLD[4], "3": GOLD[3], "2": GOLD[2]}
        p.paste(sprite(rows, pal), kx - 4, y0 - voussoir - 2)

def cone_roof(p, cx, base_y, half, height, seed=1):
    for i in range(height):
        y = base_y - i
        hw = int(half * (1 - i / height) ** 0.92) + (1 if i < 2 else 0)
        if hw < 0: break
        for x in range(cx - hw, cx + hw + 1):
            t = (x - (cx - hw)) / max(1, 2 * hw)
            v = max(0.0, math.cos((t - 0.3) * math.pi * 0.9))
            c = pick(ROOF[1:], v, x, y)
            if i % 4 == 3: c = ROOF[max(0, ROOF.index(c) - 1)] if c in ROOF else c
            elif (x + (i // 4) * 3) % 6 == 0: c = ROOF[max(0, ROOF.index(c) - 1)] if c in ROOF else c
            p.px(x, y, c)
    p.hline(cx - half - 2, cx + half + 2, base_y + 1, ROOF[0]); p.hline(cx - half - 1, cx + half + 1, base_y, ROOF[4])
    tip = base_y - height
    # épi doré + petite boule
    p.vline(cx, tip - 5, tip + 2, GOLD[3]); p.px(cx, tip - 6, GOLD[6]); p.rect(cx - 1, tip - 3, cx + 1, tip - 3, GOLD[4])
    # lucarne
    lx, ly = cx - 2, base_y - height // 3
    p.rect(lx - 1, ly - 1, lx + 5, ly + 5, K); p.rect(lx, ly, lx + 4, ly + 4, STONE[5])
    p.rect(lx + 1, ly + 1, lx + 3, ly + 4, (40, 26, 40)); p.rect(lx + 1, ly + 2, lx + 3, ly + 4, GOLD[4]); p.vline(lx + 2, ly + 1, ly + 4, K)
    for k in range(4): p.hline(lx - 1 + k, lx + 5 - k, ly - 1 - k, ROOF[2] if k else ROOF[0])

def merlons(p, x0, x1, y, h=7, w=8, gap=5, seed=3):
    x = x0; i = 0
    while x + w - 1 <= x1:
        blocks(p, x, y, x + w - 1, y + h - 1, seed + i, bw=w + 1, bh=4, base=5, var=0)
        p.hline(x, x + w - 1, y, STONE[7]); p.vline(x, y, y + h - 1, STONE[6])
        p.rect(x + w, y + 2, x + w + gap - 1, y + h - 1, (24, 16, 30))
        x += w + gap; i += 1

def corbels(p, x0, x1, y):
    p.rect(x0, y, x1, y + 3, STONE[5]); p.hline(x0, x1, y, STONE[7]); p.hline(x0, x1, y + 3, STONE[3])
    for x in range(x0 + 2, x1 - 2, 6):
        p.rect(x, y + 4, x + 3, y + 7, STONE[4]); p.hline(x, x + 3, y + 4, STONE[6]); p.vline(x + 3, y + 4, y + 7, STONE[2])
        p.rect(x + 4, y + 4, x + 5, y + 6, (20, 12, 24))

def quoins(p, x, y0, y1, left=True):
    k = 0
    for y in range(y0, y1, 9):
        w = 8 if k % 2 else 6
        xx = x if left else x - w + 1
        p.rect(xx, y, xx + w - 1, y + 7, DRESS[3]); p.hline(xx, xx + w - 1, y, DRESS[5]); p.vline(xx, y, y + 7, DRESS[4])
        p.hline(xx, xx + w - 1, y + 7, DRESS[1]); p.vline(xx + w - 1, y, y + 7, DRESS[2]); p.px(xx, y, DRESS[6])
        k += 1

# ---------------------------------------------------------------- décor
def torch(p, x, y):
    glow(p, x + 1, y - 1, 14, (255, 170, 70), 40)
    p.rect(x - 1, y + 6, x + 3, y + 7, IRON[2]); p.vline(x - 1, y + 7, y + 11, IRON[1]); p.px(x - 2, y + 11, IRON[2])
    p.rect(x, y + 1, x + 2, y + 8, WOOD[3]); p.vline(x, y + 1, y + 8, WOOD[4]); p.vline(x + 2, y + 1, y + 8, WOOD[1])
    p.rect(x - 1, y, x + 3, y + 1, IRON[3])
    for yy, hw, c in ((-1, 1, FIRE[2]), (-2, 1, FIRE[2]), (-3, 1, FIRE[1]), (-4, 0, FIRE[2]), (-5, 0, FIRE[1])):
        p.hline(x + 1 - hw, x + 1 + hw, y + yy, c)
    p.vline(x + 1, y - 3, y, FIRE[4]); p.px(x + 1, y - 1, (255, 255, 255))

def lantern(p, x, y):
    glow(p, x + 1, y + 6, 12, (255, 190, 90), 36)
    p.hline(x - 5, x + 1, y, IRON[2]); p.px(x - 5, y + 1, IRON[2]); p.px(x - 4, y + 1, IRON[1]); p.px(x, y + 1, IRON[3])
    p.rect(x - 1, y + 2, x + 3, y + 3, IRON[2]); p.px(x + 1, y + 1, IRON[3])
    p.rect(x - 1, y + 4, x + 3, y + 10, K); p.rect(x, y + 5, x + 2, y + 9, GOLD[5]); p.px(x + 1, y + 6, (255, 255, 240))
    p.vline(x + 1, y + 5, y + 9, GOLD[4]) if False else None
    p.hline(x - 1, x + 3, y + 11, IRON[2]); p.px(x + 1, y + 12, IRON[1])

def ivy(p, x, y, n, seed, hang=True):
    rnd = random.Random(seed)
    for i in range(n):
        y += 1; x += rnd.choice((-1, 0, 0, 0, 1))
        p.px(x, y, LEAF[1])
        if rnd.random() < .6:
            s = rnd.choice((-1, 1))
            p.px(x + s, y, LEAF[3]); p.px(x + 2 * s, y, LEAF[2]); p.px(x + s, y - 1, LEAF[4])
            if rnd.random() < .25: p.px(x + 2 * s, y + 1, LEAF[1])

def bush(p, x, y, r=4, seed=0, flowers=True):
    rnd = random.Random(seed)
    lay = layer(2 * r + 6, r + 5)
    for k in range(3):
        ellipse(lay, r + 1 + k * r // 2, r + 2 - (k == 1), r * 0.7 + (k == 1), r * 0.75, LEAF[1:5])
    if flowers:
        for _ in range(r):
            fx, fy = rnd.randint(2, 2 * r + 2), rnd.randint(1, r)
            c = rnd.choice((RED[5], (250, 246, 250), GOLD[5], (220, 140, 230)))
            lay.px(fx, fy, c)
    stamp(p, lay, x - r - 1, y - r - 3, LEAF[0], drop=None)

def grass_tufts(p, x0, x1, y, seed):
    rnd = random.Random(seed)
    for x in range(x0, x1, 2):
        if rnd.random() < .5:
            h = rnd.randint(1, 3)
            p.vline(x, y - h, y, LEAF[rnd.choice((2, 3))]); p.px(x, y - h, LEAF[4])

def fleur(p, x, y, col=GOLD):
    rows = ["...4...", "..454..", ".24542.", "3.454.3", "4444444", "3.222.3", "..2.2.."]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != ".": p.px(x + i, y + j, col[int(ch)])

def mini_tower(p, x, y, col=GOLD):
    rows = ["4.4.4", "44444", "43334", "43K34", "42K24"]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == "K": p.px(x + i, y + j, RED[1])
            elif ch != ".": p.px(x + i, y + j, col[int(ch)])

def heraldic_shield(p, x, y, w=26, h=30):
    """Écu parti azur (fleur de lys d'or) / gueules (tour d'or), bordure dorée."""
    lay = layer(w, h)
    def inside(xx, yy):
        if yy < 0 or yy >= h or xx < 0 or xx >= w: return False
        if yy < h * 0.55: return True
        t = (yy - h * 0.55) / (h * 0.45)
        half = (w / 2) * math.sqrt(max(0, 1 - t ** 1.6))
        return abs(xx - (w - 1) / 2) <= half
    for yy in range(h):
        for xx in range(w):
            if not inside(xx, yy): continue
            edge = not (inside(xx - 2, yy) and inside(xx + 2, yy) and inside(xx, yy + 2) and inside(xx, yy - 2))
            if edge:
                c = GOLD[5] if (xx < w / 2 and yy < h * 0.6) else GOLD[3] if yy < h * 0.8 else GOLD[2]
                if not (inside(xx - 1, yy) and inside(xx + 1, yy) and inside(xx, yy + 1) and inside(xx, yy - 1)): c = GOLD[1]
            else:
                left = xx < w // 2
                cols = BLUE if left else RED
                c = pick(cols[2:5] if left else cols[2:5], 1 - yy / h * 0.9 - (0.15 if xx > w * 0.75 else 0), xx, yy)
            lay.px(xx, yy, c)
    lay.vline(w // 2, 2, h - 3, GOLD[3]); lay.vline(w // 2 - 1, 2, h - 4, GOLD[5])
    fleur(lay, 3, 7)
    mini_tower(lay, 17, 8) if False else None
    for j, r in enumerate(["4.4.4", "44444", "43334", "4K3K4", "43334", "44444", "4KKK4", "4KKK4"]):
        for i, ch in enumerate(r):
            if ch == "K": lay.px(16 + i, 7 + j, RED[1])
            elif ch != ".": lay.px(16 + i, 7 + j, GOLD[int(ch)])
    lay.px(4, 2, (255, 255, 255)); lay.px(3, 3, GOLD[6])
    stamp(p, lay, x, y, K, drop=(10, 4, 14, 110))

# ---------------------------------------------------------------- bannière-titre
def _cloth_col(lay, x, top, h, pal, trim=True, embroid=True):
    for y in range(h):
        t = y / (h - 1)
        c = pal[5] if t < .07 else pal[4] if t < .2 else pal[3] if t < .62 else pal[2] if t < .9 else pal[1]
        lay.px(x, top + y, c)
    if trim:
        for gy, gc in ((1, GOLD[4]), (2, GOLD[2]), (h - 3, GOLD[4]), (h - 2, GOLD[2])):
            lay.px(x, top + gy, gc)
        if x % 3 == 0: lay.px(x, top + 1, GOLD[6]); lay.px(x, top + h - 3, GOLD[5])
    if embroid and x % 6 == 3:
        lay.px(x, top + 4, GOLD[3]); lay.px(x, top + h - 5, GOLD[3])

def title_banner(p, x0, x1, yc, h, A, text):
    cx, half = (x0 + x1) / 2, (x1 - x0) / 2
    def top_at(x): return yc + int(round(A * ((x - cx) / half) ** 2))
    TAIL = [(40, 6, 22), (66, 12, 30), (96, 20, 38), (128, 30, 44), (156, 44, 52), (180, 60, 60)]
    th, tw = h - 6, 34
    for side in (-1, 1):
        lay = Pix(tw + 8, th + 8, 4, 4)
        for x in range(tw):
            _cloth_col(lay, x, 0, th, TAIL, embroid=False)
        for y in range(th):
            d = th // 2 - abs(y - th // 2)
            for k in range(d // 2 + 2):
                lay.px(k if side < 0 else tw - 1 - k, y, (0, 0, 0, 0))
        tx = (x0 - tw + 10) if side < 0 else (x1 - 10)
        ty = top_at(x0) + 8
        im = outline(lay.img, K)
        a = np.array(im)[:, :, 3] > 0
        sh = np.zeros((*a.shape, 4), np.uint8); sh[a] = (10, 4, 14, 110)
        p.paste(Image.fromarray(sh), tx - 4 + 2, ty - 4 + 3); p.paste(im, tx - 4, ty - 4)
        # pli
        fx = x0 if side < 0 else x1
        for i in range(8):
            for k in range(8 - i):
                p.px(fx + (k if side < 0 else -k), ty + th - 1 - i + 1, (34, 4, 18))
    lay = Pix(int(2 * half) + 8, h + A + 12, 4, 6)
    for x in range(0, int(2 * half) + 1):
        _cloth_col(lay, x, top_at(x0 + x) - yc, h, RED)
        if x % 26 in (0, 1):
            for y in range(6, h - 6): lay.px(x, top_at(x0 + x) - yc + y, RED[2] if x % 26 == 0 else RED[4])
    for fx in (7, int(2 * half) - 7):
        ty = top_at(x0 + fx) - yc + h // 2 - 3
        fleur(lay, fx - 3, ty)
    im = outline(lay.img, K)
    a = np.array(im)[:, :, 3] > 0
    sh = np.zeros((*a.shape, 4), np.uint8); sh[a] = (10, 4, 14, 120)
    p.paste(Image.fromarray(sh), x0 - 4 + 2, yc - 6 + 3); p.paste(im, x0 - 4, yc - 6)
    # texte qui suit la courbe
    tw_ = sum(title_glyph(c)[1] for c in text) - 2
    tx0 = int(cx - tw_ / 2)
    fancy_text(p, tx0, yc + 4, text, font=title_glyph, grad=TITLE_GRAD, extrude=3,
               offs=lambda i, c: int(round(A * ((c - cx) / half) ** 2)))

# ---------------------------------------------------------------- boutons
def painting(p, x, y, w, h, scene, arch=0):
    """Tableau à cadre doré mouluré, sommet éventuellement en arc."""
    m = arch_mask(x, y, x + w - 1, y + h - 1, arch) if arch else (lambda xx, yy: x <= xx < x + w and y <= yy < y + h)
    mo = arch_mask(x - 3, y - 3, x + w + 2, y + h + 2, arch + 2) if arch else (lambda xx, yy: x - 3 <= xx < x + w + 3 and y - 3 <= yy < y + h + 3)
    img = scene(w, h)
    for yy in range(y - 4, y + h + 4):
        for xx in range(x - 4, x + w + 4):
            if m(xx, yy):
                c = img.getpixel((xx - x, yy - y))
                p.px(xx, yy, c)
            elif mo(xx, yy):
                edge_out = not (mo(xx - 1, yy) and mo(xx + 1, yy) and mo(xx, yy - 1) and mo(xx, yy + 1))
                edge_in = m(xx - 1, yy) or m(xx + 1, yy) or m(xx, yy - 1) or m(xx, yy + 1)
                if edge_out: p.px(xx, yy, K)
                elif edge_in: p.px(xx, yy, GOLD[1])
                else:
                    tl = (xx - x) + (yy - y) < (w + h) / 2
                    p.px(xx, yy, GOLD[5] if (not mo(xx - 2, yy) or not mo(xx, yy - 2)) else GOLD[3] if tl else GOLD[2])
    # reflets du verre
    for k in range(3): p.px(x + 1 + k, y + 3 - k + (arch // 2 if arch else 0), (255, 255, 255, 70))
    # ombre portée sur le fond
    for yy in range(y + 2, y + h + 4): p.px(x + w + 3, yy, (8, 2, 10, 90))
    for xx in range(x - 1, x + w + 4): p.px(xx, y + h + 3, (8, 2, 10, 90))

def bay(p, x0, y0, x1, y1, scene, lines, vw, vh, arch=0, sub=None):
    # fond : panneau de chêne sombre, vignetté
    for x in range(x0, x1 + 1):
        stripe = ((x - x0) // 6) % 2
        for y in range(y0, y1 + 1):
            v = 1 - abs((x - (x0 + x1) / 2) / ((x1 - x0) / 2)) * 0.5 - abs((y - (y0 + y1) / 2) / ((y1 - y0) / 2)) * 0.3
            p.px(x, y, pick([WOOD[0], WOOD[1], WOOD[2]], v * 0.9 + 0.05 * stripe, x, y))
        if (x - x0) % 6 == 0: p.vline(x, y0, y1, WOOD[0])
    rnd = random.Random(x0 + y0)
    for _ in range((x1 - x0) // 2):
        gx, gy = rnd.randint(x0 + 1, x1 - 1), rnd.randint(y0 + 1, y1 - 3)
        p.vline(gx, gy, gy + rnd.randint(1, 3), WOOD[1])
    # ombre intérieure (baie creusée)
    for i, a in enumerate((150, 100, 55, 25)):
        p.hline(x0, x1, y0 + i, (8, 2, 10, a)); p.vline(x0 + i, y0, y1, (8, 2, 10, a))
    p.hline(x0, x1, y1, (255, 220, 170, 35)); p.vline(x1, y0, y1, (255, 220, 170, 25))
    if scene is None: return
    px_, py_ = x0 + 4, y0 + (y1 - y0 + 1 - vh) // 2 + 1
    painting(p, px_, py_, vw, vh, scene, arch)
    # libellé
    tx0 = px_ + vw + 4
    cx = (tx0 + x1 - 1) // 2
    n = len(lines) + (1 if sub else 0)
    lh = 11
    ty = (y0 + y1) // 2 - (n * lh - 3) // 2
    for i, ln in enumerate(lines):
        fancy_text_c(p, cx, ty + i * lh, ln, grad=BRIGHT_GRAD, extrude=1, out=(16, 6, 10),
                     ext_cols=((60, 22, 18),), shine=False)
    if sub:
        fancy_text_c(p, cx, ty + len(lines) * lh + 1, sub, grad=CREAM_GRAD, extrude=1, shine=False)
    # clous en laiton aux coins
    for cx_, cy_ in ((x0 + 2, y0 + 2), (x1 - 2, y0 + 2), (x0 + 2, y1 - 2), (x1 - 2, y1 - 2)):
        p.px(cx_, cy_, GOLD[5]); p.px(cx_ + 1, cy_ + 1, GOLD[1])

# ---------------------------------------------------------------- château
def build(p, demo=False, page="main"):
    S = Pix(W, H, OX, OY)

    # toit central (derrière la bannière)
    for i in range(22):
        y = -4 - i
        hw = int(86 * (1 - i / 22))
        for x in range(88 - hw, 88 + hw + 1):
            t = (x - (88 - hw)) / max(1, 2 * hw)
            v = max(0.0, math.cos((t - 0.3) * math.pi * 0.9))
            c = pick(ROOF[1:], v, x, y)
            if i % 4 == 3: c = ROOF[1]
            S.px(x, y, c)

    # corps central
    blocks(S, -4, -4, 180, 186, 7, moss=0.04)
    corbels(S, -6, 182, -6)
    quoins(S, -4, 2, 184, True); quoins(S, 180, 2, 184, False)

    # tours
    TOW = ((-124, -6), (182, 300))
    for i, (tx0, tx1) in enumerate(TOW):
        cx = (tx0 + tx1) // 2
        cone_roof(S, cx, 4, (tx1 - tx0) // 2 - 2, 28, seed=i)
        blocks(S, tx0, 18, tx1, 186, 100 + i, bw=11, bh=7, moss=0.05)
        corbels(S, tx0 - 3, tx1 + 3, 13)
        S.rect(tx0 - 3, 9, tx1 + 3, 12, STONE[5]); S.hline(tx0 - 3, tx1 + 3, 9, STONE[7]); S.hline(tx0 - 3, tx1 + 3, 12, STONE[3])
        merlons(S, tx0 - 3, tx1 + 3, 2, h=7, w=8, gap=5, seed=20 + i)
        shade_columns(S, tx0 - 3, tx1 + 3, 2, 186, lo=0.6, hi=1.14)
        if i == 0: S.rect(tx1 + 1, 2, tx1 + 6, 186, (10, 4, 14, 80))
        else: S.rect(tx0 - 3, 2, tx0 - 1, 186, (10, 4, 14, 40))

    # encadrement des baies : pierre de taille claire + moulure
    blocks(S, 0, 12, 176, 129, 61, bw=14, bh=8, pal=DRESS, base=3, mortar=DRESS[1], var=0)
    S.rect(-1, 11, 177, 11, K); S.rect(-1, 130, 177, 130, K); S.vline(-1, 11, 130, K); S.vline(177, 11, 130, K)
    S.hline(0, 176, 12, DRESS[6]); S.vline(0, 12, 129, DRESS[5])

    # corniche à denticules
    S.rect(-6, 130, 182, 141, K)
    S.rect(-5, 131, 181, 133, DRESS[5]); S.hline(-5, 181, 131, DRESS[6]); S.hline(-5, 181, 133, DRESS[3])
    S.rect(-5, 134, 181, 140, DRESS[1])
    for x in range(-4, 181, 5):
        S.rect(x, 134, x + 2, 138, DRESS[4]); S.hline(x, x + 2, 134, DRESS[5]); S.px(x + 2, 138, DRESS[2])
    S.hline(-5, 181, 140, DRESS[0])

    # niche gauche (statistiques)
    def parch_fill(L, w, h):
        for x in range(w):
            for y in range(h):
                L.px(x, y, pick([WOOD[0], WOOD[1], WOOD[2]], 0.6 - abs(x - w / 2) / w + (0.1 if (x // 7) % 2 else 0), x, y))
            if x % 7 == 0: L.vline(x, 0, h - 1, WOOD[0])
    arch_opening(S, -116, 28, -14, 174, 16, parch_fill)
    # niche droite (bannière)
    arch_opening(S, 190, 28, 292, 174, 16, parch_fill)
    # porte
    def gate_fill(L, w, h):
        L.rect(0, 0, w - 1, h - 1, (20, 12, 18))
        for x in range(2, w - 2):
            for y in range(7, h):
                L.px(x, y, pick([WOOD[1], WOOD[2], WOOD[3], WOOD[4]], 0.75 - abs(x - w / 2) / w - (0.25 if (x - 2) % 6 == 0 else 0), x, y))
        L.vline(w // 2, 7, h - 1, WOOD[0]); L.vline(w // 2 - 1, 7, h - 1, WOOD[0])
        for yy in (14, 29):
            L.rect(2, yy, w - 3, yy + 1, IRON[2]); L.hline(2, w - 3, yy, IRON[4])
            for xx in range(4, w - 3, 5): L.px(xx, yy, IRON[5]); L.px(xx, yy + 1, IRON[1])
        for (rx, ry) in ((w // 2 - 4, 21), (w // 2 + 3, 21)):
            L.rect(rx - 1, ry - 1, rx + 1, ry + 1, GOLD[2]); L.px(rx, ry, (20, 12, 18)); L.px(rx - 1, ry - 1, GOLD[5])
        for xx in range(3, w - 3, 4):
            L.vline(xx, 0, 5, IRON[3]); L.px(xx, 6, IRON[4]); L.vline(xx + 1, 0, 4, IRON[1])
        L.hline(1, w - 2, 2, IRON[2])
    arch_opening(S, 64, 147, 112, 186, 12, gate_fill)

    # socle
    blocks(S, -128, 180, 304, 193, 77, bw=16, bh=7, base=3)
    S.hline(-128, 304, 180, STONE[6]); S.hline(-128, 304, 181, STONE[5])
    # lumière d'ensemble (haut plus clair, pied plus sombre) + contour unique
    a = np.array(S.img).astype(np.float32)
    for Y in range(a.shape[0]):
        a[Y, :, :3] *= 1.08 - 0.30 * (Y / a.shape[0])
    S.img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    S.img = outline(S.img, K)
    p.paste(S.img, -OX, -OY)

    # ---- boutons ----
    if page == "main":
        bay(p, 5, 16, 171, 54, SCENES["kingdom"], ["Aller à mon", "royaume"], 92, 31)
        bay(p, 5, 58, 85, 90, SCENES["build"], ["Bâtiments"], 24, 26, arch=5)
        bay(p, 91, 58, 171, 90, SCENES["forge"], ["Améliorer"], 24, 26, arch=5)
        bay(p, 5, 94, 85, 126, SCENES["court"], ["Membres"], 24, 26, arch=5)
        bay(p, 91, 94, 171, 126, SCENES["capital"], ["Capitale"], 24, 26, arch=5)
        bays, knobs = ((5, 16, 171, 54), (5, 58, 85, 90), (91, 58, 171, 90), (5, 94, 85, 126), (91, 94, 171, 126)), ((88, 56), (88, 92))
    else:
        bay(p, 5, 16, 171, 52, SCENES["stock"], ["Récupérer", "le stock"], 92, 29)
        bay(p, 5, 56, 85, 86, SCENES["forge"], ["Améliorer"], 24, 24, arch=5)
        bay(p, 91, 56, 171, 86, SCENES["cart"], ["Ramasser"], 24, 24, arch=5)
        bay(p, 5, 89, 171, 126, None, [], 0, 0)
        # cases du stock (ligne 4 du coffre) : les objets du jeu s'affichent dedans
        for c in range(9):
            x, y = 8 + 18 * c, 90
            p.rect(x - 1, y - 1, x + 16, y + 16, (20, 10, 14))
            p.rect(x, y, x + 16, y + 16, WOOD[1]); p.rect(x, y, x + 15, y + 15, (44, 24, 26))
            p.hline(x, x + 15, y, (16, 8, 12)); p.vline(x, y, y + 15, (16, 8, 12))
            p.hline(x, x + 16, y + 16, WOOD[3]); p.vline(x + 16, y, y + 16, WOOD[3])
        fancy_text_c(p, 88, 113, "Stock du bâtiment", grad=CREAM_GRAD, extrude=1, shine=False)
        # retour (case 45) et fermer (case 53)
        for (bx, pal, rows) in ((8, GOLD, ["........", "...#....", "..##....", ".#######", ".#######", "..##....", "...#....", "........"]),
                                (152, RED, ["........", ".##..##.", ".###.##.", "..####..", "..####..", ".##.###.", ".##..##.", "........"])):
            by = 108
            p.rect(bx - 1, by - 1, bx + 16, by + 16, K)
            for yy in range(16):
                for xx in range(16):
                    p.px(bx + xx, by + yy, pick(pal[2:6], 0.9 - yy / 20 - (0.2 if xx > 12 else 0), bx + xx, by + yy))
            p.hline(bx, bx + 15, by, pal[6] if len(pal) > 6 else pal[5]); p.hline(bx, bx + 15, by + 15, pal[1]); p.vline(bx + 15, by, by + 15, pal[1])
            for yy, r in enumerate(rows):
                for xx, ch in enumerate(r):
                    if ch == "#":
                        p.rect(bx + xx * 2, by + yy * 2 + 1, bx + xx * 2 + 1, by + yy * 2 + 2, pal[0])
            for yy, r in enumerate(rows):
                for xx, ch in enumerate(r):
                    if ch == "#": p.rect(bx + xx * 2, by + yy * 2, bx + xx * 2 + 1, by + yy * 2 + 1, (255, 248, 226))
        bays, knobs = ((5, 16, 171, 52), (5, 56, 85, 86), (91, 56, 171, 86), (5, 89, 171, 126)), ((88, 54), (88, 87.5))
    for (bx0, by0, bx1, by1) in bays:
        p.rect(bx0 - 1, by0 - 1, bx1 + 1, by0 - 1, K); p.rect(bx0 - 1, by1 + 1, bx1 + 1, by1 + 1, K)
        p.vline(bx0 - 1, by0 - 1, by1 + 1, K); p.vline(bx1 + 1, by0 - 1, by1 + 1, K)
    for cx_, cy_ in knobs:
        cy_ = int(cy_)
        p.rect(cx_ - 3, cy_ - 2, cx_ + 3, cy_ + 2, K)
        ellipse(p, cx_, cy_, 2.2, 1.6, [GOLD[1], GOLD[3], GOLD[5], GOLD[6]])

    # ---- niche gauche : parchemin ----
    PX0, PY0, PW, PH = -112, 36, 94, 138
    lay = layer(PW, PH)
    for x in range(PW):
        for y in range(5, PH - 5):
            lay.px(x, y, pick([PARCH[2], PARCH[3], PARCH[4], PARCH[5]], 0.95 - abs(x - PW / 2) / PW * 1.2 - (y - 5) / 500, x, y))
    rnd = random.Random(8)
    for _ in range(170): lay.px(rnd.randint(1, PW - 2), rnd.randint(8, PH - 8), PARCH[2] if rnd.random() < .7 else PARCH[5])
    for y in range(5, PH - 5):                         # bords légèrement brûlés
        lay.px(0, y, PARCH[1]); lay.px(PW - 1, y, PARCH[1])
        if rnd.random() < .3: lay.px(1, y, PARCH[2])
        if rnd.random() < .3: lay.px(PW - 2, y, PARCH[2])
    for (yy, flip) in ((0, False), (PH - 6, True)):   # rouleaux
        for x in range(-3, PW + 3):
            for k in range(6):
                lay.px(x, yy + k, pick([PARCH[0], PARCH[1], PARCH[3], PARCH[5]], (1 - k / 5) * 0.9 + 0.1 if not flip else k / 5 * 0.85 + 0.1, x, yy + k))
        for ex, cols in ((-6, WOOD[3:6]), (PW + 3, WOOD[1:4])):
            for k in range(6): lay.hline(ex, ex + 2, yy + k, cols[0] if k > 3 else cols[1] if k > 1 else cols[2])
    stamp(p, lay, PX0, PY0, K)
    # corde + crochet
    for x in range(PX0 + 4, PX0 + PW - 4):
        yy = PY0 - 2 - int((1 - abs(x - (PX0 + PW / 2)) / (PW / 2 - 4)) * 4)
        p.px(x, yy, (206, 166, 112)); p.px(x, yy + 1, (128, 90, 56))
    p.rect(-67, PY0 - 9, -61, PY0 - 5, K); ellipse(p, -64, PY0 - 7, 2.2, 1.6, [IRON[2], IRON[4], IRON[5]])
    # en-tête : ruban « Ton royaume »
    hw_, hh_ = 104, 16
    hdr = Pix(hw_ + 8, hh_ + 8, 4, 4)
    for x in range(hw_):
        _cloth_col(hdr, x, 0, hh_, RED, embroid=False)
    for y in range(hh_):                               # entailles en V aux bouts
        d = hh_ // 2 - abs(y - hh_ // 2)
        for k in range(d // 2 + 1):
            hdr.px(k, y, (0, 0, 0, 0)); hdr.px(hw_ - 1 - k, y, (0, 0, 0, 0))
    stamp(p, hdr, PX0 - 5, PY0 + 10, K)
    fancy_text_c(p, PX0 + PW // 2, PY0 + 14, "Ton royaume" if page == "main" else "Ce bâtiment", grad=BRIGHT_GRAD, extrude=1, out=(30, 6, 12),
                 ext_cols=((70, 14, 24),), shine=False)
    # catégories
    ROW0, STEP = PY0 + 30, 20
    rows_ = ((("crown", "Seigneur"), ("coins", "Trésor"), ("hourglass", "Revenu"), ("trophy", "Rang"), ("people", "Membres")) if page == "main"
             else (("trophy", "Niveau"), ("hourglass", "Production"), ("chest", "Stock"), ("coins", "Valeur"), ("arrow", "Amélioration")))
    for i, (ic, lab) in enumerate(rows_):
        y = ROW0 + i * STEP
        L = icon(ic)
        iw = L.img.width - 2 * L.ox
        # médaillon derrière l'icône
        ellipse(p, PX0 + 13, y + 8, 9, 8.5, [PARCH[1], PARCH[2], PARCH[3]], light=(0.4, 0.5))
        stamp(p, L, PX0 + 13 - iw // 2, y + 2, K, drop=(60, 30, 10, 70), dx=1, dy=1)
        p.text(PX0 + 27, y, lab, (124, 82, 50), False)
        if i < 4:
            sy = y + 18
            for x in range(PX0 + 8, PX0 + PW - 8, 2): p.px(x, sy, PARCH[2])
    # sceau de cire
    sx, sy = PX0 + PW - 10, PY0 + PH - 6
    for k in range(5): p.px(sx - 2 - k // 2, sy + 4 + k, RED[2]); p.px(sx + 2 + k // 2, sy + 4 + k, RED[3])
    ellipse(p, sx, sy, 5, 5, [RED[1], RED[2], RED[3], RED[4], RED[5]])
    ellipse(p, sx, sy, 3, 3, [RED[3], RED[2], RED[4]])
    p.px(sx - 1, sy - 1, RED[5]); p.px(sx + 1, sy - 1, RED[5]); p.px(sx, sy - 2, RED[5]); p.hline(sx - 1, sx + 1, sy, RED[5])

    # ---- niche droite : bannière du royaume ----
    rod_y = 42
    p.rect(200, rod_y, 282, rod_y + 2, K); p.hline(201, 281, rod_y + 1, GOLD[3]); p.hline(201, 281, rod_y, GOLD[5])
    for fx in (199, 283):
        ellipse(p, fx, rod_y + 1, 2.4, 2.4, [GOLD[1], GOLD[3], GOLD[5], GOLD[6]])
    for x0_, x1_ in ((210, 241), (272, 241)):
        for k in range(0, 12):
            xx = x0_ + (x1_ - x0_) * k // 12; yy = rod_y - 1 - k * 9 // 12
            p.px(xx, yy, IRON[3] if k % 2 else IRON[1])
    p.rect(239, 30, 243, 33, K); ellipse(p, 241, 31, 1.6, 1.2, [GOLD[2], GOLD[4], GOLD[6]])
    ban = Pix(66, 110, 4, 4)
    for x in range(58):
        depth = 92 + min(12, min(x, 57 - x) // 2)
        for y in range(depth):
            t = x / 57
            v = 0.85 - abs(t - 0.35) * 0.9 - (0.12 if x % 14 in (0, 1) else 0)
            ban.px(x, y, pick(RED[1:6], v, x, y))
        ban.px(x, depth - 1, RED[0])
        if 3 <= x <= 54:
            ban.px(x, 3, GOLD[4]); ban.px(x, 4, GOLD[2])
            ban.px(x, depth - 4, GOLD[4]); ban.px(x, depth - 5, GOLD[2])
    for x, c in ((3, GOLD[4]), (4, GOLD[2]), (53, GOLD[3]), (54, GOLD[1])):
        depth = 92 + min(12, min(x, 57 - x) // 2)
        for y in range(3, depth - 4): ban.px(x, y, c)
    stamp(p, ban, 212, rod_y + 2, K)
    for tx in (214, 241, 268):                         # glands
        p.vline(tx, rod_y + 100, rod_y + 104, GOLD[3]) if False else None
    heraldic_shield(p, 228, 70, 26, 30)
    lay = icon_crown(); stamp(p, lay, 234, 58, K, drop=(10, 4, 14, 100))
    fleur(p, 220, 112, GOLD); fleur(p, 255, 112, GOLD); fleur(p, 237, 124, GOLD)
    # plaque « Niveau »
    pl = layer(60, 15)
    vgrad(pl, 0, 0, 59, 14, [GOLD[5], GOLD[4], GOLD[3], GOLD[2]])
    pl.rect(2, 2, 57, 12, K); vgrad(pl, 3, 3, 56, 11, [RED[2], RED[1], RED[0]])
    stamp(p, pl, 211, 158, K)
    for side in (-1, 1):                               # lauriers
        bx = 209 if side < 0 else 273
        for k in range(5):
            yy = 170 - k * 3
            xx = bx + side * (2 - abs(k - 2))
            p.px(xx, yy, LEAF[3]); p.px(xx + side, yy - 1, LEAF[4]); p.px(xx - side, yy - 1, LEAF[2])

    # ---- décor ----
    torch(p, 52, 152); torch(p, 122, 152)
    lantern(p, -1, 143); lantern(p, 178, 143)
    def wall_banner(x, col, emb):
        p.rect(x - 2, 142, x + 19, 143, K); p.hline(x - 1, x + 18, 142, GOLD[4]); p.hline(x - 1, x + 18, 143, GOLD[2])
        L = Pix(26, 36, 4, 2)
        for xx in range(18):
            depth = 24 + min(5, min(xx, 17 - xx))
            for yy in range(depth):
                L.px(xx, yy, pick(col[1:6], 0.85 - abs(xx / 17 - 0.35) * 1.0, xx, yy))
            L.px(xx, depth - 1, col[0])
        for yy in range(26):
            L.px(1, yy, GOLD[4]); L.px(16, yy, GOLD[2])
        stamp(p, L, x, 144, K)
        if emb == "fleur": fleur(p, x + 6, 152)
        else:
            rows = ["3...4...3", "43.454.34", "444444444", "4r44b44r4", "222222222"]
            for j, r in enumerate(rows):
                for i, ch in enumerate(r):
                    if ch == "r": p.px(x + 5 + i, 153 + j, RED[4])
                    elif ch == "b": p.px(x + 5 + i, 153 + j, (130, 200, 255))
                    elif ch != ".": p.px(x + 5 + i, 153 + j, GOLD[int(ch) + 1])
    wall_banner(15, RED, "fleur"); wall_banner(143, BLUE, "crown")
    ivy(p, -122, 18, 60, 3); ivy(p, 298, 18, 50, 4); ivy(p, 1, 132, 34, 5); ivy(p, 175, 132, 30, 6)
    ivy(p, -10, 0, 22, 9); ivy(p, 186, 0, 26, 10)
    # sol herbeux devant le château
    G = Pix(W, H, OX, OY)
    rnd = random.Random(31)
    for x in range(-130, 307):
        edge = min(x + 130, 306 - x)
        top = 192 + (0 if edge > 10 else (10 - edge) // 2) + (1 if rnd.random() < .25 else 0)
        bot = 202 - (0 if edge > 18 else (18 - edge) // 3)
        for y in range(top, bot + 1):
            t = (y - top) / max(1, bot - top)
            G.px(x, y, pick([LEAF[4], LEAF[3], LEAF[2], DIRT[2], DIRT[1]], t * 1.1, x, y))
        # dessous de l'île : terre et roche (couvre le bas du coffre vanilla jusqu'à y = 222)
        u = abs(x - 88) / 220
        under = 202 + int(32 * max(0.0, 1 - u ** 1.6)) + (rnd.randint(-1, 1) if u < .95 else 0)
        for y in range(bot + 1, under + 1):
            t = (y - bot) / max(1, under - bot)
            G.px(x, y, pick([DIRT[2], DIRT[1], DIRT[0], (34, 20, 26)], t, x, y))
        if 46 <= x <= 130:                            # chemin de terre au pied des marches
            for y in range(top + 2, bot + 1):
                G.px(x, y, pick([DIRT[4], DIRT[3], DIRT[2]], (y - top) / 10 + abs(x - 88) / 120, x, y))
    rr = random.Random(77)
    for _ in range(70):                               # pierres et racines dans la terre
        x = rr.randint(-110, 286); u = abs(x - 88) / 220
        y = rr.randint(204, 200 + int(30 * max(0.0, 1 - u ** 1.6)))
        if G.img.getpixel((x + OX, y + OY))[3] == 0: continue
        if rr.random() < .7:
            G.px(x, y, STONE[3]); G.px(x + 1, y, STONE[2]); G.px(x, y - 1, STONE[4])
        else:
            for k in range(rr.randint(2, 4)): G.px(x + (k % 2), y + k, (90, 60, 40))
    G.img = outline(G.img, K)
    p.paste(G.img, -OX, -OY)
    for _ in range(18):                               # cailloux du chemin
        x, y = rnd.randint(50, 126), rnd.randint(196, 200)
        p.px(x, y, STONE[5]); p.px(x + 1, y, STONE[3])
    # touffes d'herbe le long du socle
    for x in range(-126, 304, 2):
        if 40 <= x <= 136 or rnd.random() < .35: continue
        h = rnd.randint(2, 4)
        p.vline(x, 193 - h, 193, LEAF[rnd.choice((2, 3))]); p.px(x, 193 - h, LEAF[4])
    # massifs fleuris
    def shrub(cx, gy, r, seed):
        rr = random.Random(seed)
        lay = layer(2 * r + 8, r + 8)
        for k, (ox, oy, s_) in enumerate(((-r * .55, 1, .75), (r * .55, 1, .75), (0, -1, .95))):
            ellipse(lay, r + 4 + ox, r + 3 + oy, r * s_ + 1, r * s_, [LEAF[1], LEAF[2], LEAF[3], LEAF[4], LEAF[5]], light=(-0.5, -0.7))
        for _ in range(r * 3):                         # feuilles
            fx, fy = rr.randint(2, 2 * r + 5), rr.randint(1, r + 3)
            if lay.img.getpixel((fx + lay.ox, fy + lay.oy))[3]: lay.px(fx, fy, LEAF[rr.choice((2, 4))])
        fc = rr.choice((RED[5], (250, 244, 252), GOLD[5], (226, 150, 236)))
        for _ in range(max(2, r - 1)):
            fx, fy = rr.randint(3, 2 * r + 4), rr.randint(1, r + 1)
            if lay.img.getpixel((fx + lay.ox, fy + lay.oy))[3]:
                lay.px(fx, fy, fc); lay.px(fx, fy + 1, tuple(int(c * .7) for c in fc))
        lay.hline(0, 2 * r + 8, r + 6, (0, 0, 0, 0)); lay.hline(0, 2 * r + 8, r + 7, (0, 0, 0, 0))
        stamp(p, lay, cx - r - 4, gy - r - 5, LEAF[0], drop=(0, 0, 0, 60), dx=1, dy=1)
    # perron : trois marches en pierre de taille, en saillie devant la porte
    St = Pix(W, H, OX, OY)
    for i in range(3):
        y = 185 + i * 5
        a_, b_ = 62 - i * 6, 114 + i * 6
        St.rect(a_, y, b_, y + 1, DRESS[5]); St.hline(a_ + 1, b_, y, DRESS[6])
        St.rect(a_, y + 2, b_, y + 4, DRESS[3]); St.hline(a_, b_, y + 4, DRESS[1])
        for x in range(a_ + 6 + i * 3, b_ - 2, 10): St.vline(x, y + 2, y + 4, DRESS[1]); St.vline(x + 1, y + 2, y + 4, DRESS[4])
        St.vline(a_, y, y + 4, DRESS[4]); St.vline(b_, y, y + 4, DRESS[1])
    for i in range(1, 3):                              # ombre de chaque marche sur la suivante
        y = 185 + i * 5
        St.hline(62 - i * 6, 114 + i * 6, y, (60, 40, 40, 90)) if False else None
    St.img = outline(St.img, K)
    a2 = np.array(St.img)[:, :, 3] > 0
    sh = np.zeros((*a2.shape, 4), np.uint8); sh[a2] = (10, 4, 14, 90)
    p.paste(Image.fromarray(sh), -OX + 1, -OY + 2)
    p.paste(St.img, -OX, -OY)
    # massifs : gros buissons aux pieds des tours, petits près des marches
    for x, r, gy in ((-124, 6, 197), (-108, 4, 198), (-20, 5, 197), (-6, 3, 198), (24, 3, 198), (38, 4, 198),
                     (138, 4, 198), (152, 3, 198), (182, 3, 198), (196, 5, 197), (284, 4, 198), (300, 6, 197)):
        shrub(x, gy, r, x * 7 + 3)
    # quelques pierres dans l'herbe
    for x in (-90, -46, 12, 160, 214, 262):
        ellipse(p, x, 199, 2.4, 1.4, [STONE[2], STONE[4], STONE[6]])
    for x in range(-126, 304, 3):                     # fleurs dans l'herbe
        if 44 <= x <= 132: continue
        if rnd.random() < .18:
            y = rnd.randint(195, 199)
            p.px(x, y, rnd.choice((RED[5], (250, 244, 252), GOLD[5]))); p.px(x, y + 1, LEAF[2])

    # ---- bannière-titre ----
    title_banner(p, -28, 204, -23, 27, 9, "ROYAUME")

    if demo:
        vals = ((("Thozire", (62, 38, 26)), ("12 480 écus", (156, 92, 16)), ("+356 / min", (34, 108, 38)),
                 ("#2 sur 14", (40, 76, 166)), ("2 / 3", (62, 38, 26))) if page == "main" else
                (("3 / 5", (62, 38, 26)), ("+32 / min", (34, 108, 38)), ("412 / 960", (62, 38, 26)),
                 ("1 240 écus", (156, 92, 16)), ("3 500 écus", (40, 76, 166))))
        for i, (v, c) in enumerate(vals): p.text(-112 + 27, 36 + 30 + i * 20 + 9, v, c, False)
        p.text_c(241, 162, "Niveau 2" if page == "main" else "Scierie", (255, 236, 190), True)

def render(page="main"):
    """Fond définitif (sans textes dynamiques) : image 440x270."""
    p = Pix(W, H, OX, OY)
    build(p, demo=False, page=page)
    return p.img

def preview(path, page="main"):
    p = Pix(W, H, OX, OY)
    build(p, demo=True, page=page)
    bg = Image.new("RGBA", (W + 40, H + 20), (0, 0, 0, 255))
    d = bg.load()
    for y in range(bg.height):
        for x in range(bg.width):
            v = 24 + ((x // 3 + y // 3) % 2) * 2
            d[x, y] = (v + 8, v, v + 8, 255)
    bg.alpha_composite(p.img, (20, 10))
    bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST).save(path)

if __name__ == "__main__":
    preview("/home/claude/rp/v8.png")
    print("ok")
