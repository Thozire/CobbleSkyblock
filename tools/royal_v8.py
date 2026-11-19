import os
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


SLATE = [(16, 18, 40), (26, 32, 66), (38, 50, 98), (54, 72, 136), (76, 102, 172), (108, 138, 206), (156, 184, 232)]

def flag(p, cx, ytop, ybase, d, seed=0):
    """Grand mât doré et oriflamme à queue d'aronde : plis ombrés, liserés et franges d'or."""
    L, Hf = 28, 13
    lay = layer(L + 3, Hf + 8)
    R0, R1 = np.array((96, 14, 28)), np.array((240, 84, 70))
    for i in range(L):
        off = round(2.0 * math.sin(i * 0.27 + 0.3 + seed))
        br = 0.5 + 0.45 * math.cos(i * 0.27 + 1.3 + seed)
        hh = Hf - (1 if i > L * 0.6 else 0)
        for j in range(hh):
            if i >= L - 6 and abs(j - (hh - 1) / 2) < (i - (L - 7)) * 0.95: continue        # queue d'aronde
            t = br - j / hh * 0.22 + (0.08 if j == 2 else 0)
            c = tuple(int(v) for v in R0 + (R1 - R0) * max(0.0, min(1.0, t)))
            if j == 0: c = GOLD[5] if br > 0.45 else GOLD[3]
            elif j == 1: c = GOLD[3] if br > 0.45 else GOLD[1]
            elif j == hh - 1: c = GOLD[3] if br > 0.45 else GOLD[1]
            lay.px(i, 2 + off + j, c)
        if i < L - 6 and i % 2 == 0:                                   # franges
            lay.px(i, 2 + off + hh, GOLD[2] if br > 0.45 else GOLD[1])
    if d < 0: lay.img = lay.img.transpose(Image.FLIP_LEFT_RIGHT)
    stamp(p, lay, cx + 1 if d > 0 else cx - L - 2, ytop + 1, K, drop=(8, 2, 12, 90), dx=1, dy=2)
    p.rect(cx - 1, ytop + 2, cx + 1, ybase, K)                          # mât fin (1 px), dans l'axe de la pointe
    p.vline(cx, ytop + 3, ybase, GOLD[4]); p.px(cx, ytop + 4, GOLD[6])
    p.rect(cx - 1, ytop, cx + 1, ytop + 2, K); p.px(cx, ytop + 1, GOLD[5]); p.px(cx, ytop, GOLD[6])

def cone_roof(p, cx, base_y, half, height, seed=1):
    """Toit en poivrière : ardoises en écailles, galbe concave, égout doré, lucarne, épi et oriflamme."""
    tip = base_y - height
    prof = lambda i: half * (1 - i / height) ** 1.55 + (2.0 if i < 2 else 0)
    ring = int(height * 0.62)
    for i in range(height):
        y = base_y - i
        hw = prof(i)
        row = i // 5; inrow = i % 5
        for x in range(int(round(cx - hw)), int(round(cx + hw)) + 1):
            t = (x - (cx - hw)) / max(1.0, 2 * hw)
            light = max(0.0, math.cos((t - 0.3) * math.pi * 0.95))
            sw = 7
            lx = (x - cx + (3 if row % 2 else 0)) % sw
            v = light * 0.8 + 0.14
            if inrow == 0: v += (-0.4 if lx in (0, 6) else -0.22 if lx in (1, 5) else -0.06)      # bas arrondi de l'écaille
            elif inrow == 1: v += (-0.24 if lx == 0 else 0.02)
            elif inrow in (3, 4) and 2 <= lx <= 4: v += 0.1                                    # reflet du haut
            if ring <= i <= ring + 1:
                c = (GOLD[4] if i == ring + 1 else GOLD[2]) if light > 0.3 else (GOLD[2] if i == ring + 1 else GOLD[1])
            else:
                c = pick(SLATE[1:7], v, x, y)
            p.px(x, y, c)
        p.px(int(round(cx - hw)) - 1, y, K); p.px(int(round(cx + hw)) + 1, y, K)
    # égout : bandeau doré et ombre portée sur la tour
    p.rect(cx - half - 3, base_y + 1, cx + half + 3, base_y + 3, K)
    p.hline(cx - half - 2, cx + half + 2, base_y + 1, GOLD[4]); p.hline(cx - half - 2, cx + half + 2, base_y + 2, GOLD[2])
    for x in range(cx - half, cx + half + 1, 5): p.px(x, base_y + 2, GOLD[5])
    dormer(p, cx, base_y - int(height * 0.36))
    # épi : collier doré, boule, pointe
    p.rect(cx - 2, tip, cx + 2, tip + 2, K); p.hline(cx - 1, cx + 1, tip + 1, GOLD[4]); p.px(cx - 1, tip + 1, GOLD[6])
    flag(p, cx, tip - 18, tip - 1, 1 if cx > 88 else -1, seed)

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

def bay(p, x0, y0, x1, y1, scene, lines, vw, vh, arch=0, sub=None, hd=None):
    walnut_fill(p, x0, y0, x1, y1)
    for i, al in enumerate((150, 90, 40)):                    # ombre intérieure
        p.hline(x0, x1, y0 + i, (6, 0, 4, al)); p.vline(x0 + i, y0, y1, (6, 0, 4, al))
    p.hline(x0 + 3, x1 - 1, y1, (255, 200, 140, 30))
    corner_brackets(p, x0 + 1, y0 + 1, x1 - 1, y1 - 1)
    if scene is None: return
    px_, py_ = (x0 + 7 if vw > 40 else x0 + 6), y0 + (y1 - y0 + 1 - vh) // 2
    painting(p, px_, py_, vw, vh, scene, arch)
    if hd and os.path.exists(hd):
        if not hasattr(p, "overlays"): p.overlays = []
        p.overlays.append((hd, px_, py_, vw, vh))
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



# ---------------------------------------------------------------- île flottante, perron, jardins
MOSS = [(20, 44, 40), (30, 70, 46), (46, 102, 50), (72, 136, 54), (112, 170, 64), (164, 204, 92), (210, 232, 140)]
ROCK = [(26, 22, 34), (40, 36, 50), (58, 54, 70), (82, 78, 94), (110, 106, 122), (142, 138, 152)]
EARTH = [(36, 20, 22), (56, 34, 30), (82, 52, 40), (110, 74, 52), (140, 100, 66)]

def shrub2(p, cx, gy, r, seed, flower=None):
    """Buisson rond fait de touffes de feuilles, ombré, contour net, quelques fleurs."""
    rr = random.Random(seed)
    w, h = 2 * r + 10, int(r * 1.6) + 8
    lay = layer(w, h)
    blobs = [(-r * .55, -r * .25, .72), (r * .55, -r * .25, .72), (0, -r * .7, .82), (-r * .2, -r * 1.05, .55), (r * .35, -r * .95, .5)]
    for (ox, oy, k) in blobs:
        ellipse(lay, w / 2 + ox, h - 4 + oy, r * k + 1, r * k * 0.9, [MOSS[1], MOSS[2], MOSS[3], MOSS[4], MOSS[5]], light=(-0.55, -0.75))
    for _ in range(r * 7):                                      # petites feuilles en relief
        fx, fy = rr.randint(1, w - 2), rr.randint(1, h - 3)
        if lay.img.getpixel((fx + lay.ox, fy + lay.oy))[3]:
            hi = fy < h * 0.55 and fx < w * 0.6
            lay.px(fx, fy, MOSS[5] if hi and rr.random() < .5 else MOSS[2]); lay.px(fx + 1, fy + 1, MOSS[1])
    if flower:
        for _ in range(max(3, r)):
            fx, fy = rr.randint(3, w - 4), rr.randint(2, h - 5)
            if lay.img.getpixel((fx + lay.ox, fy + lay.oy))[3]:
                lay.px(fx, fy, flower[1]); lay.px(fx + 1, fy, flower[0]); lay.px(fx, fy - 1, flower[1]); lay.px(fx, fy + 1, flower[2])
    stamp(p, lay, cx - w // 2, gy - h + 3, K, drop=(8, 2, 10, 90), dx=1, dy=1)

def pot(lay, cx, y, w=5, col=None):
    """Pot (pierre ou terre cuite) dont le haut est en y."""
    col = col or ROCK
    lay.rect(cx - w, y, cx + w, y + 1, col[4]); lay.hline(cx - w, cx + w, y, col[5])
    for j in range(2, 7):
        hw = w - 1 - (j > 4)
        for i in range(-hw, hw + 1): lay.px(cx + i, y + j, pick(col[1:5], 0.8 - (i + hw) / (2 * hw + 1) * 0.6, i, j))
    lay.hline(cx - w + 1, cx + w - 1, y + 4, col[2])

def topiary(p, cx, gy, h, seed):
    """Quatre plantes en pot différentes selon seed : if en cône, boule taillée, rosier, lavande."""
    kind = seed % 4
    top_pad = 8
    lay = layer(20, h + 12 + top_pad)
    lay.oy += top_pad                                                  # marge au-dessus : rien n'est coupé
    mx = 10
    TERRA = [(70, 30, 22), (110, 50, 34), (150, 74, 46), (186, 104, 62), (214, 138, 86), (236, 170, 116)]
    if kind == 0:                                                     # if en cône à étages
        for j in range(h):
            hw = 1 + j * 6 // h
            for i in range(-hw, hw + 1):
                t = 0.75 - (i + hw) / (2 * hw + 1) * 0.6 + (0.15 if (j + i) % 3 == 0 else 0) - (0.25 if j % 5 == 4 else 0)
                lay.px(mx + i, j, pick(MOSS[1:6], t, i, j))
        pot(lay, mx, h, 5)
    elif kind == 1:                                                   # boule taillée sur tige
        lay.vline(mx, h - 6, h, EARTH[3]); lay.vline(mx + 1, h - 6, h, EARTH[2])
        ellipse(lay, mx, h - 10, 5.5, 5.5, [MOSS[1], MOSS[2], MOSS[3], MOSS[4], MOSS[5]], light=(-0.5, -0.6))
        for (dx, dy) in ((-2, -13), (1, -12), (3, -9), (-3, -8)): lay.px(mx + dx, h + dy, MOSS[5])
        pot(lay, mx, h, 5, TERRA)
    elif kind == 2:                                                   # rosier rouge
        for (ox, oy, r) in ((-3, -5, 3.6), (3, -5, 3.6), (0, -9, 3.8)):
            ellipse(lay, mx + ox, h + oy, r, r * 0.9, [MOSS[1], MOSS[2], MOSS[3], MOSS[4]], light=(-0.5, -0.6))
        for (dx, dy) in ((-4, -6), (2, -9), (4, -4), (-1, -11), (0, -5), (-3, -9)):
            lay.px(mx + dx, h + dy, RED[4]); lay.px(mx + dx + 1, h + dy, RED[3]); lay.px(mx + dx, h + dy - 1, RED[5])
        pot(lay, mx, h, 6, TERRA)
    else:                                                             # lavande
        rr = random.Random(seed)
        for k in range(-4, 5, 2):
            hh = 7 + rr.randint(0, 4) - abs(k) // 2
            for j in range(hh):
                lay.px(mx + k + (j % 3 == 0), h - j, MOSS[3] if j < hh - 4 else (150, 110, 210) if j % 2 else (190, 150, 240))
        pot(lay, mx, h, 5)
    stamp(p, lay, cx - 10, gy - h - 5, K, drop=(8, 2, 10, 90), dx=1, dy=1)

def post_lantern(p, x, gy):
    """Borne de pierre surmontée d'une lanterne."""
    glow(p, x, gy - 22, 18, (255, 180, 90), 46)
    p.rect(x - 4, gy - 14, x + 3, gy, K)
    for y in range(gy - 13, gy):
        for xx in range(x - 3, x + 3): p.px(xx, y, pick(ROCK[2:6], 0.85 - (xx - x + 3) / 7, xx, y))
    p.hline(x - 4, x + 3, gy - 14, ROCK[5]); p.rect(x - 5, gy - 16, x + 4, gy - 15, ROCK[4]); p.hline(x - 5, x + 4, gy - 16, ROCK[5])
    p.rect(x - 3, gy - 25, x + 2, gy - 17, K)
    p.rect(x - 2, gy - 24, x + 1, gy - 18, (255, 196, 90)); p.vline(x - 1, gy - 23, gy - 19, (255, 244, 190))
    p.rect(x - 4, gy - 27, x + 3, gy - 26, IRON[2]); p.hline(x - 3, x + 2, gy - 28, IRON[3]); p.px(x - 1, gy - 29, IRON[4])
    p.hline(x - 3, x + 2, gy - 17, IRON[2])

def ground(p):
    """Île : épaisse bande d'herbe (le perron repose dessus), puis terre en dégradé continu, pierres et racines."""
    CX = 88
    x0g, x1g = -130, 306
    Wg = x1g - x0g + 1
    noise = value_noise(Wg, 60, (40, 8), 11) * 0.7 + value_noise(Wg, 60, (110, 20), 12) * 0.3
    rnd = random.Random(31)
    arr = np.zeros((H, W, 4), np.uint8)
    GRASS_T, GRASS_B = np.array((126, 184, 72)), np.array((52, 110, 50))
    DIRT_T, DIRT_B = np.array((122, 84, 56)), np.array((34, 20, 24))
    for x in range(x0g, x1g + 1):
        edge = min(x - x0g, x1g - x)
        r_ = 9                                                          # bout arrondi de la couche d'herbe
        top = 192 + (0 if edge >= r_ else round(r_ - math.sqrt(max(0.0, r_ * r_ - (r_ - edge) ** 2))))
        gb = top + 4 + 8 * math.sqrt(min(1.0, edge / 20))               # épaisseur d'herbe
        u = abs(x - CX) / 218
        under_f = gb + 1 + 34 * max(0.0, 1 - u * u) ** 0.6              # dessous en bol arrondi
        under = int(under_f)
        for y in range(top, under + 1):
            nz = noise[min(59, max(0, y - 190)), x - x0g] - 0.5
            if y <= int(gb):
                t = (y - top) / max(1.0, gb - top)
                c = GRASS_T * (1 - t) + GRASS_B * t + nz * 26
                if y == top: c = c * 1.12 + 10
            else:
                t = (y - gb) / max(1.0, under_f - gb)
                c = DIRT_T * (1 - t) ** 1.2 + DIRT_B * (1 - (1 - t) ** 1.2) + nz * 30
                if y == int(gb) + 1: c = c * 0.72                       # ombre sous l'herbe
            arr[y + OY, x + OX] = (*np.clip(c, 0, 255).astype(int), 255)
        if rnd.random() < .45:                                          # mèches d'herbe qui retombent
            for k in range(rnd.randint(1, 3)):
                yy = int(gb) + 1 + k
                if yy <= under: arr[yy + OY, x + OX] = (58, 112, 52, 255) if k < 2 else (44, 88, 46, 255)
    G = Image.fromarray(arr, "RGBA")
    Gp = Pix(W, H, OX, OY); Gp.img = G
    rr = random.Random(77)
    for _ in range(260):                                                # mottes : texture pixel de la terre
        x = rr.randint(-124, 300); u = abs(x - CX) / 220
        y = rr.randint(208, max(209, 205 + int(29 * max(0.0, 1 - u ** 1.6))))
        c = Gp.img.getpixel((x + OX, y + OY))
        if c[3] == 0: continue
        k = 1.18 if rr.random() < .5 else 0.8
        Gp.px(x, y, tuple(min(255, int(v * k)) for v in c[:3]))
        if rr.random() < .5: Gp.px(x + 1, y, tuple(min(255, int(v * (k + 1) / 2)) for v in c[:3]))
    for _ in range(60):                                                 # pierres et racines
        x = rr.randint(-110, 286); u = abs(x - CX) / 220
        y = rr.randint(210, max(211, 204 + int(28 * max(0.0, 1 - u ** 1.6))))
        if G.getpixel((x + OX, y + OY))[3] == 0: continue
        if rr.random() < .65:
            Gp.px(x, y, (128, 122, 138)); Gp.px(x + 1, y, (92, 86, 102)); Gp.px(x, y - 1, (160, 154, 168)); Gp.px(x + 1, y + 1, (60, 52, 64))
        else:
            for k in range(rr.randint(2, 4)): Gp.px(x + (k % 2), y + k, (96, 64, 42))
    G = outline(Gp.img, K)
    p.paste(G, -OX, -OY)
    rnd2 = random.Random(5)
    for x in range(-114, 292, 2):                                       # brins d'herbe sur le bord
        if 36 <= x <= 140 or rnd2.random() < .35: continue
        h = rnd2.randint(2, 4)
        p.vline(x, 193 - h, 193, LEAF[rnd2.choice((2, 3))]); p.px(x, 193 - h, LEAF[4])

    # ---- perron d'honneur : 4 marches, tapis rouge bordé d'or, bornes-lanternes
    St = Pix(W, H, OX, OY)
    for i in range(4):
        y = 186 + i * 3
        a_, b_ = 58 - i * 5, 118 + i * 5
        St.rect(a_, y, b_, y, ROCK[5]); St.hline(a_, b_, y + 1, ROCK[4])                     # nez de marche
        for yy in range(y + 2, y + 3):
            for x in range(a_, b_ + 1): St.px(x, yy, pick(ROCK[1:5], 0.7 - (yy - y - 2) * 0.3 - abs(x - CX) / 260, x, yy))
        for x in range(a_ + 4 + (i * 5) % 9, b_ - 2, 9): St.vline(x, y + 2, y + 2, ROCK[1])
        St.vline(a_, y, y + 2, ROCK[5]); St.vline(b_, y, y + 2, ROCK[2])
    St.img = outline(St.img, K)
    a2 = np.array(St.img)[:, :, 3] > 0
    sh = np.zeros((*a2.shape, 4), np.uint8); sh[a2] = (10, 4, 14, 110)
    p.paste(Image.fromarray(sh), -OX + 1, -OY + 2)
    p.paste(St.img, -OX, -OY)
    for i in range(4):                                                  # tapis qui descend les marches
        y = 186 + i * 3
        hw = 10 + i
        for yy in range(y, y + 3):
            for x in range(CX - hw, CX + hw + 1):
                t = 0.75 - (yy - y) * 0.18 - abs(x - CX) / 40
                p.px(x, yy, pick(RED[1:5], t, x, yy))
            p.px(CX - hw, yy, GOLD[3]); p.px(CX + hw, yy, GOLD[2])
        p.hline(CX - hw, CX + hw, y, RED[5])

    # ---- jardins
    topiary(p, -100, 192, 15, 0); topiary(p, 278, 192, 10, 3)
    topiary(p, -4, 192, 12, 2); topiary(p, 180, 192, 13, 1)
    for (x, r, fl) in ((-82, 6, (RED[5], RED[4], RED[2])), (-66, 4, None), (-26, 5, ((250, 246, 252), (220, 220, 240), (170, 170, 200))),
                       (16, 4, None), (32, 5, (GOLD[5], GOLD[4], GOLD[2])), (144, 5, (GOLD[5], GOLD[4], GOLD[2])), (160, 4, None),
                       (198, 5, ((226, 150, 236), (190, 110, 210), (130, 60, 150))), (244, 4, None), (260, 6, (RED[5], RED[4], RED[2]))):
        shrub2(p, x, 195, r, x * 13 + 5, fl)
    for x in range(-120, 300, 2):                                       # fleurs des prés
        if 36 <= x <= 140: continue
        if rnd.random() < .16:
            y = rnd.randint(192, 197); c = rnd.choice(((RED[5], RED[3]), ((252, 248, 255), (200, 200, 220)), (GOLD[5], GOLD[3]), ((180, 200, 255), (110, 130, 220))))
            p.vline(x, y + 1, y + 2, MOSS[2]); p.px(x, y, c[0]); p.px(x + 1, y, c[1]); p.px(x - 1, y, c[1])


INK_GRAD = [(150, 34, 34), (140, 30, 32), (128, 26, 30), (118, 22, 28), (108, 18, 26), (100, 16, 24), (92, 14, 22), (86, 12, 20), (80, 10, 18), (74, 8, 16)]

def drop_shadow(im, dx, dy, a):
    m = np.array(im)[:, :, 3] > 0
    sh = np.zeros((im.height + dy, im.width + dx, 4), np.uint8)
    sh[dy:, dx:][m] = (8, 2, 12, a)
    return Image.fromarray(sh).crop((0, 0, im.width, im.height)) if False else Image.fromarray(sh[:im.height, :im.width]) if False else _shift(sh, im, dx, dy)

def _shift(sh, im, dx, dy):
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(Image.fromarray(sh[:im.height, :im.width]))
    return out

def value_noise(w, h, cells, seed):
    rnd = np.random.RandomState(seed)
    g = rnd.rand(cells[1] + 2, cells[0] + 2)
    im = Image.fromarray((g * 255).astype(np.uint8), "L").resize((w, h), Image.BICUBIC)
    return np.array(im).astype(float) / 255

def parchment_paper(w, h):
    """Papier ancien : teinte chaude, marbrures douces, bords brunis, quelques fibres. Couleurs continues (pas de bandes)."""
    n = value_noise(w, h, (6, 9), 3) * 0.6 + value_noise(w, h, (14, 20), 4) * 0.3 + value_noise(w, h, (30, 44), 5) * 0.1
    yy, xx = np.mgrid[0:h, 0:w]
    ex = np.minimum(xx, w - 1 - xx) / 7.0; ey = np.minimum(yy, h - 1 - yy) / 7.0
    edge = np.clip(np.minimum(ex, ey * 1.4), 0, 1)
    light = 0.18 * (1 - np.abs(xx - w * 0.45) / w) - 0.06 * yy / h
    v = 0.62 + (n - 0.5) * 0.35 + light - (1 - edge) ** 2 * 0.55
    lo, mid, hi = np.array((150, 104, 62)), np.array((224, 192, 140)), np.array((250, 236, 200))
    v3 = v[..., None]
    col = np.where(v3 < 0.6, lo + (mid - lo) * np.clip(v3 / 0.6, 0, 1), mid + (hi - mid) * np.clip((v3 - 0.6) / 0.4, 0, 1))
    rnd = np.random.RandomState(9)
    col += rnd.randn(h, w, 1) * 3.5                                     # grain
    for _ in range(90):                                                 # fibres
        x, y = rnd.randint(3, w - 4), rnd.randint(3, h - 4)
        col[y, x:x + 2] *= 0.94
    col[:, 0] *= 0.7; col[:, -1] *= 0.7
    a = np.full((h, w, 1), 255.0)
    return Image.fromarray(np.dstack([np.clip(col, 0, 255), a]).astype(np.uint8), "RGBA")

def roller(p, x0, x1, y):
    """Rouleau de bois tourné (6 px) avec embouts dorés arrondis."""
    shades = (WOOD[1], WOOD[3], WOOD[5], WOOD[4], WOOD[3], WOOD[1])
    p.rect(x0 + 2, y - 1, x1 - 2, y + 6, K)
    for k, c in enumerate(shades): p.hline(x0 + 3, x1 - 3, y + k, c)
    for x in range(x0 + 6, x1 - 5, 7): p.px(x, y + 2, WOOD[6]); p.px(x + 1, y + 3, WOOD[2])
    for ex in (x0, x1 - 4):
        p.rect(ex - 1, y - 2, ex + 5, y + 7, K)
        for k in range(-1, 7):
            c = (GOLD[3], GOLD[5], GOLD[6], GOLD[5], GOLD[4], GOLD[3], GOLD[2], GOLD[1])[k + 1]
            p.hline(ex, ex + 4, y + k, c)
        p.vline(ex + 4, y - 1, y + 6, GOLD[1]); p.vline(ex, y - 1, y + 6, GOLD[4])
        p.px(ex + 1, y, (255, 255, 240))

def flourish(p, cx, y, half):
    """Filet d'or calligraphique avec losange central et volutes."""
    for x in range(cx - half, cx + half + 1):
        d = abs(x - cx)
        if d < 4: continue
        a = 1 - d / (half + 1)
        p.px(x, y, (196, 124, 30, int(140 + 115 * a)))
    for sgn in (-1, 1):                                                 # volutes
        bx = cx + sgn * (half - 3)
        for (dx, dy) in ((0, -1), (1 * sgn, -2), (2 * sgn, -2), (3 * sgn, -1), (3 * sgn, 0)):
            p.px(bx + dx, y + dy, GOLD[2])
    for (dx, dy, c) in ((0, -2, GOLD[5]), (-1, -1, GOLD[4]), (0, -1, RED[3]), (1, -1, GOLD[3]), (-2, 0, GOLD[4]), (-1, 0, RED[3]),
                        (0, 0, RED[4]), (1, 0, RED[2]), (2, 0, GOLD[2]), (-1, 1, GOLD[3]), (0, 1, RED[2]), (1, 1, GOLD[2]), (0, 2, GOLD[2])):
        p.px(cx + dx, y + dy, c)

# ---------------------------------------------------------------- ornements du panneau central
WALNUT = [(22, 10, 14), (34, 16, 18), (48, 24, 22), (64, 34, 28), (82, 46, 34)]
VELVET = [(34, 6, 16), (52, 10, 22), (74, 16, 30), (98, 24, 38)]

def gold_bevel(p, x0, y0, x1, y1, w=2):
    """Moulure dorée en relief, visible sur les 4 côtés (lumière douce en haut à gauche)."""
    p.rect(x0 - w - 1, y0 - w - 1, x1 + w + 1, y0 - w - 1, K); p.rect(x0 - w - 1, y1 + w + 1, x1 + w + 1, y1 + w + 1, K)
    p.vline(x0 - w - 1, y0 - w - 1, y1 + w + 1, K); p.vline(x1 + w + 1, y0 - w - 1, y1 + w + 1, K)
    prof = [GOLD[5], GOLD[4], GOLD[3], GOLD[2]] if w >= 3 else [GOLD[5], GOLD[3]]
    for k in range(w):
        a, b = x0 - w + k, x1 + w - k; c, d = y0 - w + k, y1 + w - k
        col = prof[min(k, len(prof) - 1)] if w >= 3 else prof[k]
        sh = GOLD[max(1, GOLD.index(col) - 1)]
        for x in range(a, b + 1):
            p.px(x, c, GOLD[6] if (k == 0 and (x - a) % 9 == 4) else col); p.px(x, d, sh)
        for y in range(c, d + 1):
            p.px(a, y, col); p.px(b, y, sh)
    p.hline(x0, x1, y0, (10, 4, 8, 150)); p.vline(x0, y0, y1, (10, 4, 8, 150))

def corner_brackets(p, x0, y0, x1, y1, gem=RED):
    """Équerres de filigrane doré dans les coins, petite gemme."""
    pat = ["GGGG.", "Gg...", "G.o..", "G....", "....."]
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        for j, row in enumerate(pat):
            for i, ch in enumerate(row):
                if ch == ".": continue
                col = GOLD[4] if ch == "G" else GOLD[2] if ch == "g" else gem[4]
                p.px(cx + sx * i, cy + sy * j, col)
        p.px(cx + sx * 3, cy + sy * 1, GOLD[5]); p.px(cx + sx * 1, cy + sy * 3, GOLD[3])

def medallion(p, cx, cy, r=4, gem=RED):
    ellipse(p, cx, cy, r + 1.4, r + 1.4, [K, K])
    ellipse(p, cx, cy, r + 0.6, r + 0.6, [GOLD[1], GOLD[2], GOLD[4], GOLD[5]])
    ellipse(p, cx, cy, r - 1.4, r - 1.4, [gem[0], gem[2], gem[3], gem[5]])
    p.px(cx - 1, cy - 1, (255, 240, 240))

def velvet_bg(p, x0, y0, x1, y1):
    """Velours pourpre damassé."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u, v = (x - x0) % 12, (y - y0) % 12
            d = abs(u - 6) + abs(v - 6)
            motif = d in (5, 6) or (d <= 1)
            t = 0.55 - abs(x - (x0 + x1) / 2) / (x1 - x0) * 0.6 - abs(y - (y0 + y1) / 2) / (y1 - y0) * 0.3
            p.px(x, y, pick(VELVET, t + (0.28 if motif else 0), x, y))

def walnut_fill(p, x0, y0, x1, y1):
    """Panneau de noyer verni, reflet doux en haut."""
    rnd = random.Random(x0 * 7 + y0)
    for x in range(x0, x1 + 1):
        g = rnd.random() * 0.12
        for y in range(y0, y1 + 1):
            ty = (y - y0) / max(1, y1 - y0); tx = abs(x - (x0 + x1) / 2) / max(1, (x1 - x0) / 2)
            t = 0.7 - tx * 0.35 - ty * 0.45 + g + (0.18 if ty < 0.12 else 0)
            p.px(x, y, pick(WALNUT, t, x, y))
    for _ in range((x1 - x0) // 3):
        gx, gy = rnd.randint(x0 + 2, x1 - 2), rnd.randint(y0 + 2, y1 - 4)
        p.vline(gx, gy, gy + rnd.randint(2, 5), WALNUT[0])


def dormer(p, cx, by):
    """Lucarne à fronton intégrée au toit : petit toit d'ardoises, jouées en pierre, fenêtre en plein cintre éclairée,
    ombre portée sur les ardoises. by = bas de la lucarne."""
    w = 11; x0 = cx - w // 2; x1 = x0 + w - 1
    fy0 = by - 8                                                        # haut de la façade
    # ombre portée sur le toit (à droite, en bas)
    for k in range(3):
        p.hline(x1 + 1, x1 + 3, fy0 + 2 + k, (8, 6, 22, 110 - k * 25))
    p.hline(x0 + 1, x1 + 2, by + 1, (8, 6, 22, 120))
    # façade
    p.rect(x0, fy0, x1, by, K)
    for y in range(fy0 + 1, by):
        for x in range(x0 + 1, x1):
            p.px(x, y, pick(DRESS[2:6], 0.85 - (x - x0) / w * 0.6, x, y))
    # fenêtre en plein cintre
    wx0, wx1, wy0 = cx - 2, cx + 2, fy0 + 2
    p.rect(wx0 - 1, wy0, wx1 + 1, by - 1, K)
    for y in range(wy0 + 1, by - 1):
        for x in range(wx0, wx1 + 1):
            if y == wy0 + 1 and x in (wx0, wx1): continue
            t = (y - wy0) / (by - wy0)
            p.px(x, y, (255, int(236 - 60 * t), int(170 - 90 * t)))
    p.vline(cx, wy0 + 1, by - 2, (90, 50, 30)); p.hline(wx0, wx1, wy0 + 4, (90, 50, 30))
    p.hline(wx0 - 1, wx1 + 1, by - 1, DRESS[6])                        # appui
    glow(p, cx, by - 3, 8, (255, 190, 90), 30)
    # petit toit à deux pans en ardoise, débord d'1 px
    for k in range(6):
        y = fy0 - k
        a, b = x0 - 1 + k, x1 + 1 - k
        if a > b: break
        for x in range(a, b + 1):
            left = x < cx
            p.px(x, y, SLATE[5] if left and (x + k) % 3 else SLATE[4] if left else SLATE[3] if (x + k) % 3 else SLATE[2])
        p.px(a - 1, y, K); p.px(b + 1, y, K)
    p.hline(x0 - 2, x1 + 2, fy0 + 1, K); p.hline(x0 - 1, x1 + 1, fy0, SLATE[6])
    p.px(cx, fy0 - 6, K); p.px(cx, fy0 - 7, GOLD[5]); p.px(cx, fy0 - 8, K)   # épi doré

def tower_crown(S, tx0, tx1, seed=0):
    """Couronnement de tour : parapet en encorbellement sur consoles arrondies, merlons à chaperon,
    créneaux profonds, écus armoriés. Même pierre que la tour pour un ensemble homogène."""
    X0, X1 = tx0 - 4, tx1 + 4
    # --- consoles (y 13..22) et arcs entre elles
    S.rect(X0, 13, X1, 22, (18, 12, 24))
    for x in range(X0 + 3, X1 - 3, 10):
        for (yy, w_) in ((13, 6), (14, 6), (15, 6), (16, 6), (17, 6), (18, 5), (19, 5), (20, 4), (21, 2)):
            cx0 = x
            for xx in range(cx0, cx0 + w_):
                t = 0.85 - (xx - cx0) / max(1, w_) * 0.55 - (yy - 13) * 0.03
                S.px(xx, yy, pick(STONE[2:7], t, xx, yy))
        S.px(x, 13, STONE[7]); S.px(x + 1, 13, STONE[7])
    for x in range(X0 + 9, X1 - 3, 10):                                   # petits arcs trilobés sombres
        S.hline(x, x + 3, 14, (38, 28, 46)); S.px(x + 1, 13, (38, 28, 46)); S.px(x + 2, 13, (38, 28, 46))
    for k in range(5): S.hline(tx0, tx1, 23 + k, (10, 4, 14, 100 - k * 20))  # ombre portée sur le fût
    # --- cordon mouluré (y 10..12)
    S.rect(X0 - 1, 10, X1 + 1, 12, STONE[4])
    S.hline(X0 - 1, X1 + 1, 10, STONE[7]); S.hline(X0 - 1, X1 + 1, 11, STONE[5]); S.hline(X0 - 1, X1 + 1, 12, STONE[2])
    # --- corps du parapet (y 0..9), mêmes pierres que la tour
    blocks(S, X0, 0, X1, 9, 300 + seed, bw=11, bh=5, base=4, var=1)
    # écus armoriés suspendus au parapet
    for k, (ex, col) in enumerate(((X0 + (X1 - X0) // 4, RED), (X0 + 3 * (X1 - X0) // 4, BLUE))):
        sh = ["KKKKKKK", "KcccccK", "KcGcGcK", "KccGccK", "KcGcGcK", ".KcccK.", "..KcK..", "...K..."]
        for j, row in enumerate(sh):
            for i, ch in enumerate(row):
                if ch == ".": continue
                c = K if ch == "K" else (col[4] if i < 3 else col[3]) if ch == "c" else GOLD[5]
                S.px(ex - 3 + i, 1 + j, c)
        S.px(ex - 2, 2, col[5])
    # --- merlons (y -12..-1) et créneaux
    mw, gap = 11, 6
    n = max(1, (X1 - X0 + 1 + gap) // (mw + gap))
    span = n * mw + (n - 1) * gap
    x = X0 + (X1 - X0 + 1 - span) // 2
    for y in range(-12, 0):                                                # fond des créneaux : ombre du chemin de ronde
        S.hline(X0, X1, y, (18 + (y + 12) * 2, 12 + (y + 12), 26 + (y + 12) * 2))
    S.hline(X0, X1, -1, (58, 50, 70))
    for i in range(n):
        blocks(S, x, -12, x + mw - 1, -1, 400 + seed * 10 + i, bw=mw + 1, bh=5, base=4, var=1)
        S.rect(x - 1, -14, x + mw, -13, K); S.hline(x - 1, x + mw, -13, STONE[7]); S.px(x - 1, -13, STONE[6]); S.px(x + mw, -13, STONE[3])   # chaperon
        S.hline(x, x + mw - 1, -12, STONE[6])
        S.vline(x, -12, -1, STONE[6]); S.vline(x + mw - 1, -12, -1, STONE[2])
        S.vline(x - 1, -13, -1, K); S.vline(x + mw, -13, -1, K)
        if i % 2 == 0:                                                     # archère
            ax = x + mw // 2
            S.vline(ax, -10, -4, (12, 6, 18)); S.px(ax, -11, STONE[3]); S.px(ax - 1, -4, (12, 6, 18)); S.px(ax + 1, -4, (12, 6, 18))
            S.vline(ax + 1, -10, -5, STONE[3])
        x += mw + gap
    S.vline(X0 - 1, -1, 22, K); S.vline(X1 + 1, -1, 22, K)

def turret_gallery(S, tx0, tx1, seed=0):
    """Sous l'avant-toit, dans la pierre même de la tour : fenêtres en plein cintre éclairées, encadrées de pierre."""
    y0, y1 = 13, 27
    n = 4
    step = (tx1 - tx0) / n
    for k in range(n):
        wx = int(tx0 + step * (k + 0.5))
        S.rect(wx - 4, y0 + 2, wx + 4, y1, K)
        for y in range(y0 + 3, y1):                                       # encadrement : pierre de la tour, un ton plus clair
            for x in range(wx - 3, wx + 4):
                S.px(x, y, STONE[5] if x < wx + 3 else STONE[3])
        S.px(wx - 3, y0 + 3, K); S.px(wx + 3, y0 + 3, K)
        for y in range(y0 + 4, y1 - 1):                                   # vitre éclairée, haut arrondi
            for x in range(wx - 2, wx + 3):
                if y == y0 + 4 and x in (wx - 2, wx + 2): continue
                t = (y - y0 - 4) / (y1 - y0 - 5)
                S.px(x, y, (255, int(232 - 70 * t), int(150 - 80 * t)))
        S.vline(wx, y0 + 5, y1 - 2, (96, 54, 30)); S.hline(wx - 2, wx + 2, y0 + 8, (96, 54, 30))
        S.hline(wx - 4, wx + 4, y1, STONE[6]); S.hline(wx - 4, wx + 4, y1 + 1, STONE[2])   # appui
    for k in range(4): S.hline(tx0, tx1, y0 - 3 + k, (10, 4, 14, 130 - k * 32))           # ombre de l'avant-toit

def mini_icon(p, x, y, kind):
    """Petites icônes 12x12 : porte en bois cintrée, étendard rouge déchiré."""
    if kind == "door":
        rows = ["...KKKKKK...", "..KwWWWWwK..", ".KwWwWWwWwK.", ".KwWwWWwWwK.", ".KiiiiiiiiK.", ".KwWwWWwWwK.", ".KwWwWWgWwK.",
                ".KwWwWWwWwK.", ".KiiiiiiiiK.", ".KwWwWWwWwK.", ".KwWwWWwWwK.", "KKKKKKKKKKKK"]
        pal = {"K": K, "W": WOOD[4], "w": WOOD[2], "i": IRON[3], "g": GOLD[5]}
    else:
        rows = ["KKKKKKKKKKKK", "KgggggggggK.", ".KrrRRRRrrK.", ".KrRRgRRRrK.", ".KrRgggRRrK.", ".KrRRgRRRrK.", ".KrRRRRRRrK.",
                ".KrRRRRRRrK.", ".KrRRK.KRrK.", ".KrRK...KrK.", ".KrK.....KK.", ".KK........."]
        pal = {"K": K, "g": GOLD[5], "r": RED[2], "R": RED[4]}
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in pal: p.px(x + i, y + j, pal[ch])

# ---------------------------------------------------------------- château
def slot_recess(p, x, y, gold=False):
    """Case creusée sertie d'or : l'objet du jeu (16x16) s'affiche dedans, à (x, y)."""
    p.rect(x - 1, y - 1, x + 16, y + 16, K)
    for yy in range(y, y + 16):
        for xx in range(x, x + 16):
            t = 0.25 + (xx - x) / 60 + (yy - y) / 40
            p.px(xx, yy, pick(VELVET[:3], t, xx, yy))
    p.hline(x, x + 15, y, (8, 2, 6)); p.vline(x, y, y + 15, (8, 2, 6)); p.hline(x + 1, x + 15, y + 1, (16, 4, 10))
    p.hline(x, x + 15, y + 15, GOLD[2] if gold else WALNUT[4]); p.vline(x + 15, y, y + 15, GOLD[1] if gold else WALNUT[3])
    for (cx, cy) in ((x, y), (x + 15, y), (x, y + 15), (x + 15, y + 15)): p.px(cx, cy, GOLD[3])
    if gold:
        p.rect(x - 2, y - 2, x + 17, y - 2, GOLD[4]); p.rect(x - 2, y + 17, x + 17, y + 17, GOLD[2])
        p.vline(x - 2, y - 2, y + 17, GOLD[4]); p.vline(x + 17, y - 2, y + 17, GOLD[2])
        p.px(x - 2, y - 2, GOLD[6])

def plaque(p, x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p.px(x, y, pick(VELVET, 0.75 - (y - y0) / (y1 - y0) * 0.5, x, y))
    gold_bevel(p, x0, y0, x1, y1, w=1)

def nav_buttons(p, by=108):
    """Retour (case 45) et fermer (case 53)."""
    for (bx, pal, rows) in ((8, GOLD, ["........", "...#....", "..##....", ".#######", ".#######", "..##....", "...#....", "........"]),
                            (152, RED, ["........", ".##..##.", ".###.##.", "..####..", "..####..", ".##.###.", ".##..##.", "........"])):
        p.rect(bx - 1, by - 1, bx + 16, by + 16, K)
        for yy in range(16):
            for xx in range(16):
                p.px(bx + xx, by + yy, pick(pal[2:6], 0.9 - yy / 20 - (0.2 if xx > 12 else 0), bx + xx, by + yy))
        p.hline(bx, bx + 15, by, pal[6]); p.hline(bx, bx + 15, by + 15, pal[1]); p.vline(bx + 15, by, by + 15, pal[1])
        for (oy, col) in ((1, pal[0]), (0, (255, 248, 226))):
            if pal is GOLD:                                        # flèche centrée (pixel par pixel)
                for dy in range(-4, 5):
                    for xx in range(3 + abs(dy), 8): p.px(bx + xx, by + 7 + dy + oy, col)
                    if abs(dy) <= 1:
                        for xx in range(8, 13): p.px(bx + xx, by + 7 + dy + oy, col)
                continue
            for yy, r in enumerate(rows):
                for xx, ch in enumerate(r):
                    if ch == "#": p.rect(bx + xx * 2, by + yy * 2 + oy, bx + xx * 2 + 1, by + yy * 2 + 1 + oy, col)

RIM = {"roi": (255, 226, 170), "bucheron": (255, 214, 160), "forgeron": (255, 170, 90), "fermier": (255, 210, 150), "mineur": (255, 200, 120)}

def niche_character(p, who, plate=None):
    """Personnage en 3D dans la niche de droite, devant un décor peint propre à son métier."""
    import royal_chars, royal_backdrops
    NX0, NX1, NTOP, NBOT = 198, 284, 40, 170
    hd0 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders", "niche_" + who + ".png")
    if os.path.exists(hd0):
        p.hires = ("niche", hd0, NX0, NTOP, NX1, NBOT)
        return
    w, h, gy = NX1 - NX0 + 1, NBOT - NTOP + 1, 104
    bg = royal_backdrops.BACKDROPS[who](w, h, gy)
    inner = arch_mask(NX0, NTOP, NX1, NBOT, 16)
    for y in range(h):
        for x in range(w):
            if inner(NX0 + x, NTOP + y): p.px(NX0 + x, NTOP + y, bg.getpixel((x, y)))
    # ombre intérieure de l'arcade (profondeur)
    for y in range(NTOP, NBOT + 1):
        for x in range(NX0, NX1 + 1):
            if not inner(x, y): continue
            d = 0
            for k, a in ((1, 130), (2, 90), (3, 55), (4, 25)):
                if not inner(x - k, y) or not inner(x, y - k): d = a; break
            if d: p.px(x, y, (8, 2, 10, d))
    cx = (NX0 + NX1) // 2
    foot = NTOP + h - 9
    hd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders", "niche_" + who + ".png")
    if os.path.exists(hd):                                         # niche HD (scène 3D + skin) : glyphe à part
        p.hires = ("niche", hd, NX0, NTOP, NX1, NBOT)
        return
    rp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders", who + ".png")
    if os.path.exists(rp):                                         # vrai render : glyphe haute définition à part
        for k in range(3):
            ellipse(p, cx + 2, foot - 1, 19 - k * 4, 3.4 - k * 0.7, [(0, 0, 0, 60)] * 3)
        p.hires = (rp, cx, foot, 120)
        return
    im = royal_chars.render(royal_chars.CHARS[who]())
    # liseré de lumière sur les bords haut-gauche (détache le personnage du décor)
    arr = np.array(im).astype(np.int32)
    solid = arr[:, :, 3] > 0
    dark = (arr[:, :, :3].sum(axis=2) < 110)                      # contour
    body = solid & ~dark
    edge = np.zeros_like(body)
    edge[:, 1:] |= body[:, 1:] & ~body[:, :-1]
    edge[1:, :] |= body[1:, :] & ~body[:-1, :]
    rim = RIM.get(who, (255, 230, 180))
    for k in range(3): arr[:, :, k] = np.where(edge, np.minimum(255, arr[:, :, k] * 0.55 + rim[k] * 0.5), arr[:, :, k])
    im = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    # ombre au sol
    for k in range(3):
        ellipse(p, cx + 3, foot - 1, 15 - k * 3, 3 - k * 0.6, [(0, 0, 0, 50)] * 3)
    fx, fy = cx - im.width // 2, foot - im.height
    p.paste(im, fx, fy)

def build(p, demo=False, page="main", title="ROYAUME", who=None, plate=None):
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
        blocks(S, tx0, 8, tx1, 186, 100 + i, bw=11, bh=7, moss=0.05)
        turret_gallery(S, tx0, tx1, i)
        shade_columns(S, tx0, tx1, 8, 186, lo=0.62, hi=1.1)
        cone_roof(S, cx, 10, (tx1 - tx0) // 2 + 5, 64, seed=i)
        if i == 0: S.rect(tx1 + 1, 2, tx1 + 6, 186, (10, 4, 14, 80))
        else: S.rect(tx0 - 3, 2, tx0 - 1, 186, (10, 4, 14, 40))

    # encadrement des baies : pierre de taille claire + moulure
    velvet_bg(S, 0, 12, 176, 129)
    gold_bevel(S, 0, 12, 176, 129, w=4)

    # niche gauche (statistiques)
    def parch_fill(L, w, h):
        for x in range(w):
            for y in range(h):
                L.px(x, y, pick([WOOD[0], WOOD[1], WOOD[2]], 0.6 - abs(x - w / 2) / w + (0.1 if (x // 7) % 2 else 0), x, y))
            if x % 7 == 0: L.vline(x, 0, h - 1, WOOD[0])
    # niche droite (bannière)
    arch_opening(S, 198, 40, 284, 170, 14, parch_fill, voussoir=3)
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
    blocks(S, -124, 180, 300, 193, 77, bw=16, bh=7, base=3)
    S.hline(-124, 300, 180, STONE[6]); S.hline(-124, 300, 181, STONE[5])
    # lumière d'ensemble (haut plus clair, pied plus sombre) + contour unique
    a = np.array(S.img).astype(np.float32)
    for Y in range(a.shape[0]):
        a[Y, :, :3] *= 1.08 - 0.30 * (Y / a.shape[0])
    S.img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    S.img = outline(S.img, K)
    p.paste(S.img, -OX, -OY)

    # ---- boutons ----
    if page == "main":
        bay(p, 5, 16, 171, 54, SCENES["kingdom"], ["Aller à mon", "royaume"], 88, 27)
        bay(p, 5, 58, 85, 90, SCENES["build"], ["Bâtiments"], 20, 24, arch=5)
        bay(p, 91, 58, 171, 90, SCENES["forge"], ["Améliorer"], 20, 24, arch=5)
        bay(p, 5, 94, 85, 126, SCENES["court"], ["Membres"], 20, 24, arch=5)
        bay(p, 91, 94, 171, 126, SCENES["capital"], ["Capitale"], 20, 24, arch=5)
        bays, knobs = ((5, 16, 171, 54), (5, 58, 85, 90), (91, 58, 171, 90), (5, 94, 85, 126), (91, 94, 171, 126)), ((88, 56), (88, 92))
    elif page == "building":
        bid = {"bucheron": "scierie", "fermier": "ferme", "forgeron": "forge", "mineur": "mine"}.get(who)
        bay(p, 5, 16, 171, 52, SCENES["stock"], ["Récupérer", "le stock"], 88, 25,
            hd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders", f"stock_{bid}.png") if bid else None)
        bay(p, 5, 56, 85, 86, SCENES["forge"], ["Améliorer"], 20, 22, arch=5)
        bay(p, 91, 56, 171, 86, SCENES["cart"], ["Ramasser"], 20, 22, arch=5)
        bay(p, 5, 89, 171, 126, None, [], 0, 0)
        for c in range(9): slot_recess(p, 8 + 18 * c, 90)          # stock (ligne 4 du coffre)
        plaque(p, 34, 110, 142, 122)
        fancy_text_c(p, 88, 113, "Stock du bâtiment", grad=BRIGHT_GRAD, extrude=1, out=(16, 6, 10), ext_cols=((60, 22, 18),), shine=False)
        nav_buttons(p)
        bays, knobs = ((5, 16, 171, 52), (5, 56, 85, 86), (91, 56, 171, 86), (5, 89, 171, 126)), ((88, 54), (88, 87.5))
    elif page == "domain":                                         # améliorer le royaume : 3 cartes + 2 réglages
        for k, (scene, label) in enumerate(((SCENES["kingdom"], "Terrain"), (SCENES["build"], "Bâtiments"), (SCENES["court"], "Membres"))):
            x0, x1 = 8 + 54 * k, 58 + 54 * k
            bay(p, x0, 17, x1, 87, None, [], 0, 0)
            painting(p, x0 + 6, 22, x1 - x0 - 11, 24, scene, 4)
            fancy_text_c(p, (x0 + x1) // 2, 51, label, grad=BRIGHT_GRAD, extrude=1, out=(16, 6, 10), ext_cols=((60, 22, 18),), shine=False)
            for xx in range(x0 + 6, x1 - 5):
                if abs(xx - (x0 + x1) // 2) > 2: p.px(xx, 62, (196, 124, 30, 200))
            p.px((x0 + x1) // 2, 61, GOLD[5]); p.px((x0 + x1) // 2, 62, RED[3]); p.px((x0 + x1) // 2, 63, GOLD[2])
        for (x0, x1, spr) in ((8, 85, "door"), (91, 168, "banner")):
            bay(p, x0, 90, x1, 105, None, [], 0, 0)
            mini_icon(p, x0 + 5, 92, spr)
        nav_buttons(p)
        bays, knobs = ((8, 17, 58, 87), (62, 17, 112, 87), (116, 17, 166, 87), (8, 90, 85, 105), (91, 90, 168, 105)), ()
    elif page == "team":                                           # la cour : membres + inviter
        bay(p, 5, 16, 171, 71, None, [], 0, 0)
        for r in range(3):
            for c in range(9): slot_recess(p, 8 + 18 * c, 18 + 18 * r)
        bay(p, 5, 75, 171, 104, SCENES["court"], ["Inviter un", "joueur"], 60, 24)
        nav_buttons(p)
        bays, knobs = ((5, 16, 171, 71), (5, 75, 171, 104)), ()
    elif page == "invite":                                         # inviter : joueurs en ligne
        bay(p, 5, 16, 171, 89, None, [], 0, 0)
        for r in range(4):
            for c in range(9): slot_recess(p, 8 + 18 * c, 18 + 18 * r)
        plaque(p, 34, 110, 142, 122)
        fancy_text_c(p, 88, 113, "Clique pour inviter", grad=BRIGHT_GRAD, extrude=1, out=(16, 6, 10), ext_cols=((60, 22, 18),), shine=False)
        nav_buttons(p)
        bays, knobs = ((5, 16, 171, 89),), ()
    else:                                                          # liste des bâtiments + boutique
        bay(p, 5, 16, 171, 71, None, [], 0, 0)
        for r in range(3):
            for c in range(9): slot_recess(p, 8 + 18 * c, 18 + 18 * r)
        bay(p, 5, 75, 171, 126, None, [], 0, 0)
        fancy_text_c(p, 88, 78, "Acheter un bâtiment", grad=BRIGHT_GRAD, extrude=1, out=(16, 6, 10), ext_cols=((60, 22, 18),), shine=False)
        for c in (1, 3, 5, 7): slot_recess(p, 8 + 18 * c, 90, gold=True)
        plaque(p, 34, 110, 142, 122)
        fancy_text_c(p, 88, 113, "Clique pour acheter", grad=BRIGHT_GRAD, extrude=1, out=(16, 6, 10), ext_cols=((60, 22, 18),), shine=False)
        nav_buttons(p)
        bays, knobs = ((5, 16, 171, 71), (5, 75, 171, 126)), ((88, 73),)
    for (bx0, by0, bx1, by1) in bays:
        gold_bevel(p, bx0, by0, bx1, by1, w=1)
    for (mx, my) in ((-1, 11), (177, 11), (-1, 130), (177, 130)):
        medallion(p, mx, my, 4)

    # ---- niche gauche : parchemin (décret royal) ----
    PX0, PY0, PW, PH = -112, 36, 94, 138
    paper = parchment_paper(PW, PH - 10)                             # papier vieilli, dégradés continus
    p.img.alpha_composite(drop_shadow(paper, 2, 3, 120), (PX0 + OX, PY0 + 5 + OY))
    p.img.alpha_composite(paper, (PX0 + OX, PY0 + 5 + OY))
    for yy in (PY0, PY0 + PH - 7):                                    # rouleaux de bois, embouts dorés
        roller(p, PX0 - 5, PX0 + PW + 4, yy)
    p.hline(PX0 + 1, PX0 + PW - 2, PY0 + 7, (90, 56, 30, 120))       # ombre du rouleau sur le papier
    p.hline(PX0 + 1, PX0 + PW - 2, PY0 + 8, (90, 56, 30, 50))
    p.hline(PX0 + 1, PX0 + PW - 2, PY0 + PH - 8, (90, 56, 30, 90))
    # deux pattes de fer scellées dans le mur tiennent le rouleau du haut
    for hx_ in (PX0 + 6, PX0 + PW - 8):
        p.rect(hx_ - 1, PY0 - 6, hx_ + 3, PY0 + 1, K)
        p.rect(hx_, PY0 - 5, hx_ + 2, PY0 - 3, IRON[3]); p.hline(hx_, hx_ + 2, PY0 - 5, IRON[4])
        p.vline(hx_ + 1, PY0 - 2, PY0 + 0, IRON[2]); p.px(hx_ + 1, PY0 - 4, IRON[1])
    # titre calligraphié à l'encre rouge, souligné d'un filet d'or orné
    title_txt = {"main": "Ton royaume", "building": "Ce bâtiment", "domain": "Ton domaine", "team": "Ta cour", "invite": "Invitations"}.get(page, "Tes bâtiments")
    fancy_text_c(p, PX0 + PW // 2, PY0 + 12, title_txt, grad=INK_GRAD, extrude=0, out=(238, 218, 176), shine=False, bold=True)
    flourish(p, PX0 + PW // 2, PY0 + 25, 34)
    # catégories
    ROW0, STEP = PY0 + 30, 20
    rows_ = ((("crown", "Seigneur"), ("coins", "Trésor"), ("hourglass", "Revenu"), ("trophy", "Rang"), ("people", "Membres")) if page == "main"
             else (("trophy", "Niveau"), ("hourglass", "Production"), ("chest", "Stock"), ("coins", "Valeur"), ("arrow", "Amélioration")) if page == "building"
             else (("trophy", "Terrain"), ("chest", "Bâtiments"), ("people", "Membres"), ("coins", "Trésor"), ("arrow", "Visites")) if page == "domain"
             else (("crown", "Seigneur"), ("people", "Membres"), ("hourglass", "En ligne"), ("trophy", "Places libres"), ("coins", "Trésor")) if page == "team"
             else (("people", "En ligne"), ("trophy", "Places libres"), ("crown", "Seigneur"), ("hourglass", "Membres"), ("coins", "Trésor")) if page == "invite"
             else (("trophy", "Posés"), ("hourglass", "Production"), ("chest", "Stock total"), ("coins", "Trésor"), ("arrow", "Agrandir")))
    for i in range(len(rows_)):                                        # cartouches : une bande douce par catégorie
        y = ROW0 + i * STEP
        bx0, bx1, by0, by1 = PX0 + 3, PX0 + PW - 4, y - 2, y + 18
        for yy in range(by0, by1 + 1):
            for xx in range(bx0, bx1 + 1):
                cnr = min(xx - bx0, bx1 - xx, yy - by0, by1 - yy)
                if cnr == 0 and (xx in (bx0, bx1) and yy in (by0, by1)): continue
                if i % 2 == 0: a_ = 46 if cnr > 0 else 70
                else: a_ = 0 if cnr > 0 else 0
                if a_: p.px(xx, yy, (150, 104, 62, a_))
        if i % 2 == 0:
            p.hline(bx0 + 1, bx1 - 1, by0, (120, 80, 44, 90)); p.hline(bx0 + 1, bx1 - 1, by1, (255, 244, 214, 90))
    for i, (ic, lab) in enumerate(rows_):
        y = ROW0 + i * STEP
        L = icon(ic)
        iw = L.img.width - 2 * L.ox
        # médaillon derrière l'icône
        ellipse(p, PX0 + 13, y + 8, 9, 8.5, [PARCH[1], PARCH[2], PARCH[3]], light=(0.4, 0.5))
        stamp(p, L, PX0 + 13 - iw // 2, y + 2, K, drop=(60, 30, 10, 70), dx=1, dy=1)
        p.text(PX0 + 27, y, lab, (124, 82, 50), False)
        pass

    # ---- niche droite ----
    if who:
        niche_character(p, who, plate)
    else:
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
    ground(p)
    # ---- bannière-titre ----
    title_banner(p, -28, 204, -23, 27, 9, title)

    if demo:
        DEMO = {"domain": (("31 × 31 blocs", (62, 38, 26)), ("5 / 7", (62, 38, 26)), ("2 / 3", (62, 38, 26)), ("12 480 écus", (156, 92, 16)), ("Ouvertes", (34, 108, 38))),
                "team": (("Thozire", (62, 38, 26)), ("2 / 3", (62, 38, 26)), ("1", (34, 108, 38)), ("1", (40, 76, 166)), ("12 480 écus", (156, 92, 16))),
                "invite": (("6", (34, 108, 38)), ("1", (40, 76, 166)), ("Thozire", (62, 38, 26)), ("2 / 3", (62, 38, 26)), ("12 480 écus", (156, 92, 16)))}
        vals = DEMO[page] if page in DEMO else ((("Thozire", (62, 38, 26)), ("12 480 écus", (156, 92, 16)), ("+356 / min", (34, 108, 38)),
                 ("#2 sur 14", (40, 76, 166)), ("2 / 3", (62, 38, 26))) if page == "main" else
                (("3 / 5", (62, 38, 26)), ("+32 / min", (34, 108, 38)), ("412 / 960", (62, 38, 26)),
                 ("1 240 écus", (156, 92, 16)), ("3 500 écus", (40, 76, 166))))
        for i, (v, c) in enumerate(vals): p.text(-112 + 27, 36 + 30 + i * 20 + 9, v, c, False)
        if page == "domain":
            for k, (a_, b_) in enumerate((("Niv. 3→4", "8 000"), ("Niv. 2→3", "5 000"), ("Niv. 1→2", "4 000"))):
                cx_ = 33 + 54 * k
                p.text_c(cx_, 66, a_, (255, 236, 190), True); p.text_c(cx_, 77, b_, (255, 214, 110), True)
            p.text(27, 94, "Ouvertes", (140, 230, 120), True); p.text(107, 94, "Abandonner", (255, 140, 120), True)

def hd_layers(p):
    """Calques haute définition (2x) à poser par-dessus le fond : niche (masquée en arcade, ombre intérieure)
    et tableaux. Renvoie [(image 2x, x, y, w, h)] en coordonnées du coffre."""
    out = []
    for (hp, x0, y0, w_, h_) in getattr(p, "overlays", []):
        out.append((Image.open(hp).convert("RGBA").resize((w_ * 2, h_ * 2), Image.LANCZOS), x0, y0, w_, h_))
    hr = getattr(p, "hires", None)
    if hr and hr[0] == "niche":
        _, hp, x0, y0, x1, y1 = hr
        w_, h_ = x1 - x0 + 1, y1 - y0 + 1
        n = Image.open(hp).convert("RGBA").resize((w_ * 2, h_ * 2), Image.LANCZOS); arr = np.array(n).astype(float)
        inside = arch_mask(x0, y0, x1 + 0.99, y1 + 0.99, 14)
        Hh, Ww = arr.shape[:2]
        m = np.zeros((Hh, Ww))
        for y in range(Hh):
            for x in range(Ww):
                m[y, x] = 1.0 if inside(x0 + (x + 0.5) / 2, y0 + (y + 0.5) / 2) else 0.0
        sh = m.copy()
        for k in range(1, 9):
            e = np.ones_like(m); e[:, k:] = np.minimum(e[:, k:], m[:, :-k]); e[k:, :] = np.minimum(e[k:, :], m[:-k, :])
            e[:, :-k] = np.minimum(e[:, :-k], m[:, k:])
            sh = sh * (1 - (1 - e) * 0.09)
        arr[:, :, :3] *= sh[..., None]; arr[:, :, 3] = m * 255
        out.append((Image.fromarray(arr.clip(0, 255).astype(np.uint8)), x0, y0, w_, h_))
    return out

def render(page="main", title="ROYAUME", who=None):
    """Fond définitif (sans textes dynamiques) + calques HD."""
    p = Pix(W, H, OX, OY)
    build(p, demo=False, page=page, title=title, who=who)
    return p.img, hd_layers(p)

def preview(path, page="main", title="ROYAUME", who=None, plate=None):
    p = Pix(W, H, OX, OY)
    build(p, demo=True, page=page, title=title, who=who, plate=plate)
    bg = Image.new("RGBA", (W + 40, H + 20), (0, 0, 0, 255))
    d = bg.load()
    for y in range(bg.height):
        for x in range(bg.width):
            v = 24 + ((x // 3 + y // 3) % 2) * 2
            d[x, y] = (v + 8, v, v + 8, 255)
    bg.alpha_composite(p.img, (20, 10))
    big = bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST)
    for (im, x0, y0, w_, h_) in hd_layers(p):
        big.alpha_composite(im, ((x0 + OX + 20) * 2, (y0 + OY + 10) * 2))
    big.save(path)

if __name__ == "__main__":
    preview("/home/claude/rp/v8.png")
    print("ok")
