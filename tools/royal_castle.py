"""Interface « Royaumes » — un seul château construit autour des boutons.

Repère : coordonnées du coffre vanilla (0,0 = coin haut-gauche du coffre 176x222).
Cases cliquables : x 8..169, y 18..125 (+ inventaire caché y 140..213).
"""
import math, random
import numpy as np
from PIL import Image
from royal_ui import FONT, OX, OY, W, H
from royal_kingdom import (Pix, outline, layer, put, sprite, PAL, icon, gradient, disc, planks, tree,
                           scene_kingdom, scene_build, scene_forge, scene_court, scene_capital,
                           K, WOOD, PARCH, SLATE, GOLD, RED, BLUE, GRASS, DIRT, IRON, LABEL_GREY, A)

# pierre chaude (un peu beige) pour le château
ST = [(46, 42, 52), (70, 66, 78), (96, 92, 104), (124, 120, 130), (152, 148, 156), (184, 180, 186), (214, 210, 212)]
DRESS = [(70, 62, 66), (112, 102, 100), (150, 138, 128), (182, 170, 156), (210, 200, 184), (234, 226, 210)]  # pierre de taille claire
MORTAR = (58, 54, 64)
ROOF = [(26, 30, 60), (40, 50, 94), (56, 74, 128), (80, 106, 166), (120, 150, 204), (170, 196, 236)]

def blocks(p, x0, y0, x1, y1, seed, bw=10, bh=6, pal=ST, base=3, mortar=MORTAR, var=1, chips=True):
    """Appareil de pierres : chaque pierre a son reflet haut-gauche et son ombre bas-droite."""
    rnd = random.Random(seed)
    p.rect(x0, y0, x1, y1, mortar)
    row = 0
    y = y0
    while y <= y1:
        x = x0 - (bw // 2 if row % 2 else 0) - rnd.randint(0, 2)
        while x <= x1:
            w = bw + rnd.choice((-2, -1, 0, 0, 1, 2))
            b = max(1, min(len(pal) - 2, base + rnd.randint(-var, var)))
            sx0, sx1 = max(x0, x + 1), min(x1, x + w - 1)
            sy0, sy1 = y + 1, min(y1, y + bh - 1)
            if sx1 >= sx0 and sy1 >= sy0:
                p.rect(sx0, sy0, sx1, sy1, pal[b])
                p.hline(sx0, sx1, sy0, pal[b + 1]); p.vline(sx0, sy0, sy1, pal[b + 1])
                p.hline(sx0 + 1, sx1, sy1, pal[b - 1]); p.vline(sx1, sy0 + 1, sy1, pal[b - 1])
                p.px(sx0, sy0, pal[min(len(pal) - 1, b + 2)])
                if chips and rnd.random() < .35:
                    cx, cy = rnd.randint(sx0 + 1, max(sx0 + 1, sx1 - 1)), rnd.randint(sy0 + 1, max(sy0 + 1, sy1 - 1))
                    p.px(cx, cy, pal[b - 1]); p.px(cx + 1, cy, pal[b + 1] if rnd.random() < .5 else pal[b])
            x += w
        y += bh; row += 1

def shade_columns(p, x0, x1, y0, y1, light=0.30, lo=0.62, hi=1.12):
    """Ombrage cylindrique d'une tour (lumière venant de la gauche)."""
    a = np.array(p.img).astype(np.float32)
    X0, X1, Y0, Y1 = x0 + p.ox, x1 + p.ox, y0 + p.oy, y1 + p.oy
    for X in range(max(0, X0), min(a.shape[1], X1 + 1)):
        t = (X - X0) / max(1, X1 - X0)
        f = lo + (hi - lo) * max(0.0, math.cos((t - light) * math.pi / 1.45))
        a[max(0, Y0):Y1 + 1, X, :3] *= f
    p.img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def recess(p, x0, y0, x1, y1, depth=3):
    """Ombre intérieure d'une ouverture creusée dans la pierre (lumière haut-gauche)."""
    for i in range(depth):
        p.rect(x0, y0 + i, x1, y0 + i, (10, 4, 10, 120 - i * 35))
        p.rect(x0 + i, y0, x0 + i, y1, (10, 4, 10, 100 - i * 30))
    p.hline(x0, x1, y1, (255, 240, 220, 40)); p.vline(x1, y0, y1, (255, 240, 220, 30))

def moulding(p, x0, y0, x1, y1, pal=DRESS):
    """Encadrement mouluré en pierre de taille autour d'une ouverture (x0..x1 = ouverture)."""
    p.rect(x0 - 3, y0 - 3, x1 + 3, y1 + 3, K)
    p.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2, pal[3])
    p.hline(x0 - 2, x1 + 2, y0 - 2, pal[5]); p.vline(x0 - 2, y0 - 2, y1 + 2, pal[4])
    p.hline(x0 - 2, x1 + 2, y1 + 2, pal[1]); p.vline(x1 + 2, y0 - 2, y1 + 2, pal[2])
    p.rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1, K)
    # joints des pierres de l'encadrement
    for x in range(x0 + 6, x1 - 2, 12):
        p.vline(x, y0 - 2, y0 - 2, pal[1]); p.vline(x, y1 + 2, y1 + 2, pal[0])
    for y in range(y0 + 6, y1 - 2, 10):
        p.px(x0 - 2, y, pal[1]); p.px(x1 + 2, y, pal[0])

def keystone(p, cx, y, gold=True):
    pal = GOLD if gold else DRESS
    rows = ["KKKKKKK", "KLYYYyK", ".KYYyK.", "..KyK..", "...K..."] if gold else ["KKKKKKK", "K55543K", ".K443K.", "..K3K..", "...K..."]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == ".": continue
            c = K if ch == "K" else (GOLD[4] if ch == "L" else GOLD[3] if ch == "Y" else GOLD[1]) if gold else (K if ch == "K" else DRESS[int(ch)])
            p.px(cx - 3 + i, y + j, c)

def arch_mask(x0, y0, x1, y1, rise):
    """Renvoie une fonction (x, y) -> bool pour une ouverture rectangulaire à sommet en arc."""
    cx, half = (x0 + x1) / 2, (x1 - x0) / 2
    def inside(x, y):
        if x < x0 or x > x1 or y > y1: return False
        if y >= y0 + rise: return True
        t = (x - cx) / max(1, half)
        top = y0 + rise - rise * math.sqrt(max(0, 1 - t * t))
        return y >= top
    return inside

def arch_opening(p, x0, y0, x1, y1, rise, fill_fn, frame=DRESS, voussoir=4):
    """Ouverture en arc avec claveaux, intérieur dessiné par fill_fn(layer, w, h)."""
    outer = arch_mask(x0 - voussoir, y0 - voussoir, x1 + voussoir, y1, rise + voussoir // 2)
    inner = arch_mask(x0, y0, x1, y1, rise)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    inside = Pix(w, h); fill_fn(inside, w, h)
    rnd = random.Random(x0 * 7 + y0)
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
                    p.px(x, y, K)
                else:
                    # claveaux rayonnants
                    ang = math.atan2(y - (y0 + rise), x - (x0 + x1) / 2)
                    seg = int((ang + math.pi) / (math.pi / 9)) if y < y0 + rise else (y - y0) // 7 + 50
                    b = 3 + (seg % 2)
                    p.px(x, y, frame[b])
                    if (seg != int((math.atan2(y - (y0 + rise), x + 1 - (x0 + x1) / 2) + math.pi) / (math.pi / 9)) and y < y0 + rise) \
                            or (y >= y0 + rise and (y - y0) % 7 == 0):
                        p.px(x, y, frame[1])
    # ombre intérieure
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if inner(x, y) and (not inner(x, y - 2) or not inner(x - 2, y)):
                p.px(x, y, (10, 4, 10, 90))


CREST = sprite(["...K...K...K...", "..KYK.KYK.KYK..", "..KYYKYYYKYYK..", "..KYRYYBYYRYK..", "..KLLLLLLLLLK..", ".KKKKKKKKKKKKK.",
                ".KBBBBBYRRRRRK.", ".KBcBBBYRqRRRK.", ".KBBBBBYRRRRRK.", ".KYYYYYYYYYYYK.", ".KRRRRRYBBBBBK.", "..KRqRRYBcBBK..",
                "...KRRRYBBBK...", "....KRRYBBK....", ".....KKYKK.....", "......KKK......"], PAL)

# ---------------------------------------------------------------- police de titre (or, contour, relief)
TITLE_GRAD = [(255, 250, 214), (255, 240, 170), (255, 226, 120), (252, 210, 86), (246, 192, 64), (236, 172, 48),
              (222, 150, 38), (206, 130, 30), (190, 112, 26), (172, 96, 22), (154, 82, 20), (138, 70, 18)]
TITLE_OUT = (52, 18, 10)
TITLE_DROP = (24, 6, 6)

def title_mask(text, scale=2):
    """Masque 1 bit du texte (police Minecraft) agrandi ; renvoie (masque, avance totale)."""
    w = FONT.width(text) + 2
    m = Image.new("L", (w, 13), 0)
    x = 0
    for ch in text:
        if ch == " ":
            x += 4; continue
        g = FONT.glyphs.get(ch)
        if not g: x += 6; continue
        cell, adv, asc, chh = g
        m.paste(255, (x, 3 + 7 - asc), cell.split()[3])
        x += adv
    m = m.resize((w * scale, 13 * scale), Image.NEAREST)
    return m, x * scale

def title_render(text, scale=2):
    m, adv = title_mask(text, scale)
    a = np.array(m) > 0
    h, w = a.shape
    pad = 3
    A_ = np.zeros((h + 2 * pad, w + 2 * pad), bool); A_[pad:pad + h, pad:pad + w] = a
    out = np.zeros((*A_.shape, 4), np.uint8)
    def dil(b):
        n = b.copy()
        n[1:, :] |= b[:-1, :]; n[:-1, :] |= b[1:, :]; n[:, 1:] |= b[:, :-1]; n[:, :-1] |= b[:, 1:]
        n[1:, 1:] |= b[:-1, :-1]; n[:-1, :-1] |= b[1:, 1:]; n[1:, :-1] |= b[:-1, 1:]; n[:-1, 1:] |= b[1:, :-1]
        return n
    ol = dil(A_)
    drop = np.zeros_like(ol); drop[2:, 1:] = ol[:-2, :-1]
    out[drop & ~ol] = A(TITLE_DROP)
    out[ol & ~A_] = A(TITLE_OUT)
    base = pad + 3 * scale            # haut des majuscules
    for y in range(out.shape[0]):
        t = (y - base) / (7 * scale)
        c = TITLE_GRAD[max(0, min(len(TITLE_GRAD) - 1, int(t * len(TITLE_GRAD))))]
        row = A_[y]
        out[y][row] = A(c)
    # reflet : bord haut des lettres plus clair
    top = A_ & ~np.vstack([np.zeros((1, A_.shape[1]), bool), A_[:-1]])
    out[top] = A((255, 255, 236))
    # ombre interne : bord bas plus sombre
    bot = A_ & ~np.vstack([A_[1:], np.zeros((1, A_.shape[1]), bool)])
    out[bot] = A((120, 60, 16))
    return Image.fromarray(out), pad

def draw_title(p, cx, y, text, scale=2):
    """y = haut des majuscules."""
    im, pad = title_render(text, scale)
    x = cx - (im.width - 2 * pad) // 2 - pad
    p.paste(im, x, y - pad - 3 * scale)

# ---------------------------------------------------------------- grande bannière de titre
def _cloth(lay, x, dy, h, pal, trim=True):
    """Une colonne de tissu (ombrée) avec galons dorés."""
    for y in range(h):
        t = y / (h - 1)
        c = pal[3] if t < .1 else pal[2] if t < .5 else pal[1] if t < .88 else pal[0]
        lay.px(x, y + dy, c)
    if trim:
        for gy, gc in ((1, GOLD[3]), (2, GOLD[1]), (h - 3, GOLD[3]), (h - 2, GOLD[1])):
            lay.px(x, gy + dy, gc)
        if x % 4 == 0: lay.px(x, 1 + dy, GOLD[4]); lay.px(x, h - 3 + dy, GOLD[4])

def title_banner(p, x0, x1, y0, h=24):
    """Ruban rouge brodé d'or tendu entre les deux tours, avec queues repliées en V."""
    cx, half = (x0 + x1) / 2, (x1 - x0) / 2
    DARK = [(70, 10, 20), (104, 18, 28), (138, 28, 36), (170, 44, 48)]
    def lift(x): return int(round(3 * ((x - cx) / half) ** 2))
    th = h - 4                         # hauteur des queues
    tw = 30
    for side in (-1, 1):
        lay = Pix(tw + 8, th + 8, 4, 4)
        for x in range(tw):
            _cloth(lay, x, 0, th, DARK)
        # entaille en V à l'extrémité
        for y in range(th):
            d = th // 2 - abs(y - th // 2)
            for k in range(d // 2 + 1):
                xx = k if side < 0 else tw - 1 - k
                lay.px(xx, y, (0, 0, 0, 0))
        im = outline(lay.img, K)
        tx = (x0 - tw + 8) if side < 0 else (x1 - 8)
        ty = y0 + 9 - lift(x0)
        a = np.array(im)[:, :, 3] > 0
        sh = np.zeros((*a.shape, 4), np.uint8); sh[a] = (12, 4, 10, 100)
        p.paste(Image.fromarray(sh), tx - 4 + 2, ty - 4 + 3)
        p.paste(im, tx - 4, ty - 4)
        # pli : petit triangle très sombre entre queue et bande
        fx = x0 if side < 0 else x1
        for i in range(7):
            yy = ty + th - 1 - i
            for k in range(7 - i):
                p.px(fx + (k if side < 0 else -k), yy + 1, (40, 6, 14))
    lay = Pix(int(2 * half) + 8, h + 14, 4, 8)
    for x in range(0, int(2 * half) + 1):
        dy = -lift(x0 + x)
        _cloth(lay, x, dy, h, RED)
        if x % 24 in (0, 1):
            for y in range(6, h - 6): lay.px(x, y + dy, RED[1] if x % 24 == 0 else RED[3])
    # fleurons dorés aux extrémités de la bande
    for fx in (6, int(2 * half) - 6):
        dy = -lift(x0 + fx)
        for (ox, oy) in ((0, -2), (-1, -1), (1, -1), (-2, 0), (2, 0), (0, 0), (-1, 1), (1, 1), (0, 2)):
            lay.px(fx + ox, h // 2 + oy + dy, GOLD[3] if (ox, oy) != (0, 0) else RED[3])
    im = outline(lay.img, K)
    a = np.array(im)[:, :, 3] > 0
    sh = np.zeros((*a.shape, 4), np.uint8); sh[a] = (12, 4, 10, 110)
    p.paste(Image.fromarray(sh), x0 - 4 + 2, y0 - 8 + 3)
    p.paste(im, x0 - 4, y0 - 8)

def big_crown(p, cx, y):
    """Couronne royale compacte ≈ 33x15 px."""
    rows = [
        "................K................",
        "...............KLK...............",
        "......K.......KYYYK.......K......",
        ".....KLK.......KyK.......KLK.....",
        "K.....K.......KYYYK.......K.....K",
        "LK...KYK.....KYYYYYK.....KYK...KL",
        "KYK..KYYK...KYYRRRYYK...KYYK..KYK",
        "KYYK.KYYYK.KYYYRRRYYYK.KYYYK.KYYK",
        "KYYYKYYYYYKYYYYYYYYYYYKYYYYYKYYYK",
        "KLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLK",
        "KYyRRyYYWYYyyBBByyYYWYYyRRyYYyyYK",
        "KYyRRyYWWWYyyBcByyYWWWYyRRyYYyyYK",
        "KyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyK",
        ".KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK.",
    ]
    im = sprite(rows, PAL)
    p.paste(outline(im), cx - 17, y - 1)

BIG_CROWN = ["..........KK..........", ".........KLLK.........", "...KK....KYYK....KK...", "..KLLK..KYRRYK..KLLK..", "..KYYK..KYRRYK..KYYK..",
             "...KYK.KYYYYYYK.KYK...", "K..KYYKYYYYYYYYKYYK..K", "KK.KYYYYYYYYYYYYYYK.KK", "KYKKYYBYYYRRYYYBYYKKYK", "KYYYYYYYYYRRYYYYYYYYYK",
             ".KYYYYYYYYYYYYYYYYYYK.", ".KLLLLLLLLLLLLLLLLLLK.", ".KyRyyyByyyRyyyByyyRK.", ".KyyyyyyyyyyyyyyyyyyK.", "..KKKKKKKKKKKKKKKKKK.."]

# ---------------------------------------------------------------- éléments
def cone_roof(p, cx, base_y, half, height, pal=ROOF, seed=1):
    """Toit conique en ardoises, ombré, avec épi doré."""
    rnd = random.Random(seed)
    for i in range(height):
        y = base_y - i
        hw = int(half * (1 - i / height) ** 0.95) + (1 if i < 2 else 0)
        if hw < 0: break
        for x in range(cx - hw, cx + hw + 1):
            t = (x - (cx - hw)) / max(1, 2 * hw)
            b = 4 if t < .18 else 3 if t < .45 else 2 if t < .75 else 1
            row = i // 3
            if (x + row * 2) % 5 == 0 and i % 3 != 2: b = max(0, b - 1)   # rangs d'ardoises
            if i % 3 == 2: b = max(0, b - 1)
            p.px(x, y, pal[b])
    # débord
    p.hline(cx - half - 2, cx + half + 2, base_y + 1, pal[0]); p.hline(cx - half - 1, cx + half + 1, base_y, pal[3])
    # épi
    tip = base_y - height
    p.vline(cx, tip - 4, tip + 1, GOLD[2]); p.px(cx, tip - 5, GOLD[4]); p.rect(cx - 1, tip - 2, cx + 1, tip - 2, GOLD[3])

def merlons(p, x0, x1, y, h=7, w=7, gap=5, pal=ST, seed=3):
    x = x0
    i = 0
    while x + w - 1 <= x1:
        blocks(p, x, y, x + w - 1, y + h - 1, seed + i, bw=w + 1, bh=4, pal=pal, base=4, chips=False)
        p.hline(x, x + w - 1, y, pal[6]); p.vline(x, y, y + h - 1, pal[5])
        x += w + gap; i += 1

def corbels(p, x0, x1, y, pal=ST):
    """Mâchicoulis : rangée de consoles sous le chemin de ronde."""
    p.rect(x0, y, x1, y + 3, pal[4]); p.hline(x0, x1, y, pal[6]); p.hline(x0, x1, y + 3, pal[2])
    for x in range(x0 + 2, x1 - 2, 6):
        p.rect(x, y + 4, x + 3, y + 7, pal[3]); p.hline(x, x + 3, y + 4, pal[5]); p.vline(x + 3, y + 4, y + 7, pal[1])
        p.rect(x + 4, y + 4, x + 5, y + 6, (20, 12, 20))

def lantern(p, x, y):
    p.hline(x - 4, x + 1, y, IRON[1]); p.vline(x - 4, y, y + 3, IRON[1]); p.px(x, y + 1, IRON[2])
    p.rect(x - 1, y + 2, x + 3, y + 3, IRON[1])
    p.rect(x - 1, y + 4, x + 3, y + 9, K); p.rect(x, y + 5, x + 2, y + 8, (255, 210, 110)); p.px(x + 1, y + 6, (255, 250, 220))
    p.hline(x - 1, x + 3, y + 10, IRON[1])
    for r, a in ((9, 26), (6, 34), (4, 40)): disc(p, x + 1, y + 6, r, (255, 190, 90, a))

def torch(p, x, y):
    p.rect(x - 1, y + 6, x + 3, y + 7, IRON[1]); p.vline(x - 1, y + 7, y + 10, IRON[1])
    p.rect(x, y + 1, x + 2, y + 8, WOOD[2]); p.vline(x, y + 1, y + 8, WOOD[1])
    p.rect(x, y - 3, x + 2, y + 1, (255, 140, 30)); p.px(x + 1, y - 4, (255, 150, 40)); p.px(x, y - 5, (255, 190, 80))
    p.vline(x + 1, y - 2, y + 1, (255, 236, 150))
    for r, a in ((10, 22), (7, 30), (4, 40)): disc(p, x + 1, y - 1, r, (255, 170, 60, a))

def ivy(p, x, y, n, seed, dir_=1, hang=True):
    rnd = random.Random(seed)
    for i in range(n):
        if hang: y += 1; x += rnd.choice((-1, 0, 0, 1))
        else: x += dir_; y += rnd.choice((-1, 0, 0, 1))
        p.px(x, y, GRASS[1])
        if rnd.random() < .55:
            lx, ly = x + rnd.choice((-2, -1, 1, 2)), y + rnd.choice((-1, 0, 1))
            p.px(lx, ly, GRASS[2]); p.px(lx + (1 if lx > x else -1), ly, GRASS[3])
            if rnd.random() < .3: p.px(lx, ly - 1, GRASS[4])

def banner(p, x, y, w, h, col, emblem):
    p.rect(x - 2, y, x + w + 1, y + 1, WOOD[1]); p.px(x - 3, y, GOLD[3]); p.px(x + w + 2, y, GOLD[3])
    lay = layer(w, h + 5)
    lay.rect(0, 0, w - 1, h - 1, col[2]); lay.vline(0, 0, h - 1, col[3]); lay.vline(w - 1, 0, h - 1, col[1])
    lay.rect(2, 0, 2, h - 1, GOLD[2]); lay.rect(w - 3, 0, w - 3, h - 1, GOLD[2])
    for i in range(w // 2 + 1):
        lay.vline(i, h, h + min(5, i), col[2]); lay.vline(w - 1 - i, h, h + min(5, i), col[2])
    for x2 in range(w): lay.px(x2, h + min(5, x2, w - 1 - x2), col[1])
    for yy in range(3, h, 6): lay.px(1, yy, col[1])
    em = icon(emblem)
    lay.paste(em, (w - em.width) // 2, 5)
    put(p, lay, x, y + 2, shadow=True)

def bush(p, x, y, r=4, seed=0):
    rnd = random.Random(seed)
    lay = layer(2 * r + 4, r + 4)
    disc(lay, r + 2, r + 2, r + 1, GRASS[1]); disc(lay, r + 1, r + 1, r, GRASS[2]); disc(lay, r, r, max(1, r - 2), GRASS[3])
    lay.rect(0, r + 3, 2 * r + 4, r + 6, (0, 0, 0, 0))
    for _ in range(r):
        lay.px(rnd.randint(1, 2 * r + 2), rnd.randint(1, r + 1), rnd.choice((GRASS[4], RED[3], (250, 240, 250), GOLD[3])))
    put(p, lay, x - r - 2, y - r - 2, shadow=False)

# ---------------------------------------------------------------- boutons
def button_bay(p, x0, y0, x1, y1, scene, lines, vw=None, sub=None):
    """Baie creusée dans la façade : fond en bois, tableau peint, libellé."""
    planks(p, x0, y0, x1, y1, seed=x0 * 3 + y0, vertical=True, base=1)
    recess(p, x0, y0, x1, y1, 3)
    vh = y1 - y0 - 7
    vw = vw or vh
    vx, vy = x0 + 4, y0 + 4
    # tableau
    p.rect(vx - 2, vy - 2, vx + vw + 1, vy + vh + 1, K)
    p.rect(vx - 1, vy - 1, vx + vw, vy + vh, GOLD[2])
    p.hline(vx - 1, vx + vw, vy - 1, GOLD[4]); p.vline(vx - 1, vy - 1, vy + vh, GOLD[3])
    p.hline(vx - 1, vx + vw, vy + vh, GOLD[1]); p.vline(vx + vw, vy - 1, vy + vh, GOLD[1])
    p.paste(scene(vw, vh), vx, vy)
    p.hline(vx, vx + vw - 1, vy, (255, 255, 255, 50))
    # ombre du tableau sur le fond
    p.vline(vx + vw + 2, vy, vy + vh + 2, (10, 4, 10, 90)); p.hline(vx, vx + vw + 2, vy + vh + 2, (10, 4, 10, 90))
    tx0 = vx + vw + 3
    cx = (tx0 + x1) // 2 + 1
    n = len(lines) + (1 if sub else 0)
    ty = (y0 + y1) // 2 - (n * 10 - 2) // 2
    for i, ln in enumerate(lines):
        p.text_c(cx, ty + i * 10, ln, (255, 236, 190), True)
    if sub: p.text_c(cx, ty + len(lines) * 10, sub, GOLD[3], True)

# ---------------------------------------------------------------- château
def build(p, demo=False):
    S = Pix(W, H, OX, OY)          # calque de la structure (un seul contour)

    # ---- toit central (derrière la bannière) ----
    for i in range(20):
        y = -6 - i
        hw = int(84 * (1 - i / 20))
        for x in range(88 - hw, 88 + hw + 1):
            t = (x - (88 - hw)) / max(1, 2 * hw)
            bb = 4 if t < .2 else 3 if t < .5 else 2 if t < .8 else 1
            if i % 3 == 2: bb = max(0, bb - 1)
            if (x + (i // 3) * 3) % 6 == 0 and i % 3 != 2: bb = max(0, bb - 1)
            S.px(x, y, ROOF[bb])
    # ---- corps central ----
    blocks(S, -4, -6, 180, 186, 7, bw=10, bh=6, base=3)
    corbels(S, -6, 182, -6, ST)
    # chaînages d'angle (grosses pierres claires) qui relient le corps aux tours
    for x0 in (-4, 172):
        for k, y in enumerate(range(4, 182, 9)):
            w = 8 if k % 2 else 6
            xx = x0 if x0 < 0 else 180 - w + 1
            S.rect(xx, y, xx + w - 1, y + 7, DRESS[3]); S.hline(xx, xx + w - 1, y, DRESS[5]); S.vline(xx, y, y + 7, DRESS[4])
            S.hline(xx, xx + w - 1, y + 7, DRESS[1]); S.vline(xx + w - 1, y, y + 7, DRESS[2])

    # ---- tours, devant le corps central ----
    TOW = ((-124, -6), (182, 300))
    for i, (tx0, tx1) in enumerate(TOW):
        cx = (tx0 + tx1) // 2
        cone_roof(S, cx, 4, (tx1 - tx0) // 2 - 2, 28, seed=i)
        blocks(S, tx0, 18, tx1, 186, 100 + i, bw=11, bh=7, base=3)
        corbels(S, tx0 - 3, tx1 + 3, 13)
        S.rect(tx0 - 3, 9, tx1 + 3, 12, ST[3]); S.hline(tx0 - 3, tx1 + 3, 9, ST[5])
        merlons(S, tx0 - 3, tx1 + 3, 2, h=7, w=8, gap=5, seed=20 + i)
        shade_columns(S, tx0 - 3, tx1 + 3, 2, 186, lo=0.58, hi=1.15)
        if i == 0:
            S.rect(tx1 + 1, 2, tx1 + 5, 186, (10, 4, 10, 70))

    # ---- grand encadrement des baies (pierre de taille claire) ----
    blocks(S, 0, 13, 176, 128, 61, bw=14, bh=8, pal=DRESS, base=3, mortar=DRESS[1], var=0)
    S.rect(-1, 12, 177, 12, K); S.rect(-1, 129, 177, 129, K); S.vline(-1, 12, 129, K); S.vline(177, 12, 129, K)

    # ---- baies des boutons ----
    bays = [(5, 16, 171, 54), (5, 58, 85, 90), (91, 58, 171, 90), (5, 94, 85, 126), (91, 94, 171, 126)]
    for (x0, y0, x1, y1) in bays:
        S.rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1, K)
    # meneaux : petites rosaces aux croisements
    for cx, cy in ((88, 56), (88, 92)):
        S.rect(cx - 2, cy - 2, cx + 2, cy + 2, K); S.rect(cx - 1, cy - 1, cx + 1, cy + 1, GOLD[3]); S.px(cx, cy, GOLD[4])
    for cx in (45, 131):
        keystone(S, cx, 13)

    # ---- corniche à denticules ----
    S.rect(-6, 129, 182, 140, K)
    S.rect(-5, 130, 181, 132, DRESS[4]); S.hline(-5, 181, 130, DRESS[5]); S.hline(-5, 181, 132, DRESS[2])
    S.rect(-5, 133, 181, 139, DRESS[1])
    for x in range(-4, 181, 5):
        S.rect(x, 133, x + 2, 137, DRESS[3]); S.hline(x, x + 2, 133, DRESS[4]); S.px(x + 2, 137, DRESS[1])
    S.hline(-5, 181, 139, DRESS[0])
    # ---- niche des statistiques (tour gauche) ----
    def parchment_fill(L, w, h):
        planks(L, 0, 0, w - 1, h - 1, seed=4, vertical=True, base=1)
        L.rect(4, 14, w - 5, h - 4, PARCH[3])
        rnd = random.Random(8)
        for _ in range(160): L.px(rnd.randint(4, w - 5), rnd.randint(14, h - 4), PARCH[2] if rnd.random() < .75 else PARCH[4])
        L.vline(4, 14, h - 4, PARCH[1]); L.vline(w - 5, 14, h - 4, PARCH[1]); L.hline(4, w - 5, h - 4, PARCH[1])
        for yy in (12, h - 5):
            L.rect(2, yy, w - 3, yy + 2, PARCH[2]); L.hline(2, w - 3, yy, PARCH[4]); L.hline(2, w - 3, yy + 2, PARCH[0])
        L.rect(9, 18, w - 10, 29, RED[2]); L.hline(9, w - 10, 18, RED[3]); L.hline(9, w - 10, 29, RED[1])
        for x, yy in ((5, 15), (w - 6, 15)): L.px(x, yy, IRON[4])
    arch_opening(S, -116, 40, -14, 172, 14, parchment_fill)

    # ---- niche de la bannière (tour droite) ----
    def banner_fill(L, w, h):
        L.rect(0, 0, w - 1, h - 1, (34, 22, 30))
        planks(L, 0, 0, w - 1, h - 1, seed=6, vertical=True, base=1)
        for i in range(0, h, 2):
            L.hline(0, w - 1, i, (0, 0, 0, 0)) if False else None
    arch_opening(S, 190, 40, 292, 172, 14, banner_fill)

    # ---- porte du château ----
    def gate_fill(L, w, h):
        L.rect(0, 0, w - 1, h - 1, (26, 16, 20))
        planks(L, 2, 6, w - 3, h - 1, seed=3, vertical=True, base=2)
        L.vline(w // 2, 6, h - 1, WOOD[0]); L.vline(w // 2 - 1, 6, h - 1, WOOD[0])
        for yy in (14, 30):
            L.rect(2, yy, w - 3, yy + 1, IRON[1]); L.hline(2, w - 3, yy, IRON[3])
            for xx in range(5, w - 4, 6): L.px(xx, yy, IRON[4])
        L.px(w // 2 - 4, 22, GOLD[3]); L.px(w // 2 + 3, 22, GOLD[3])
        # herse relevée
        for xx in range(3, w - 3, 5): L.vline(xx, 0, 5, IRON[2]); L.px(xx, 6, IRON[3])
        L.hline(1, w - 2, 2, IRON[1])
    arch_opening(S, 66, 146, 110, 186, 10, gate_fill)

    # ---- socle et marches ----
    blocks(S, -128, 180, 304, 192, 77, bw=16, bh=6, base=2)
    S.rect(-128, 180, 304, 180, ST[5])
    for i, (a, b) in enumerate(((58, 118), (54, 122), (50, 126))):
        y = 187 + i * 3
        S.rect(a, y, b, y + 2, DRESS[3] if i % 2 == 0 else DRESS[2]); S.hline(a, b, y, DRESS[5]); S.hline(a, b, y + 2, DRESS[1])

    # ---- contour unique de toute la silhouette ----
    # on ajoute toits & toiture avant le contour
    a = np.array(S.img).astype(np.float32)
    for Y in range(a.shape[0]):
        a[Y, :, :3] *= 1.10 - 0.28 * (Y / a.shape[0])
    S.img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    S.img = outline(S.img, K)
    # ombre portée au sol
    p.rect(-130, 193, 306, 196, (0, 0, 0, 70))
    p.paste(S.img, -OX, -OY)

    # ---- contenu des baies ----
    button_bay(p, 5, 16, 171, 54, scene_kingdom, ["Aller à mon", "royaume"], vw=90, sub="» Y aller")
    button_bay(p, 5, 58, 85, 90, scene_build, ["Bâtiments"])
    button_bay(p, 91, 58, 171, 90, scene_forge, ["Améliorer"])
    button_bay(p, 5, 94, 85, 126, scene_court, ["Membres"])
    button_bay(p, 91, 94, 171, 126, scene_capital, ["Capitale"])

    # ---- contenu niche gauche (icônes + intitulés) ----
    for i, (ic, lab) in enumerate((("crown", "Seigneur"), ("coins", "Trésor"), ("hourglass", "Revenu"),
                                   ("trophy", "Rang"), ("people", "Membres"))):
        y = 73 + i * 19
        p.paste(outline(icon(ic)), -109, y + 3)
        p.text(-92, y, lab, (124, 80, 44), False)
        if i < 4:
            for x in range(-108, -22, 2): p.px(x, y + 17, PARCH[1])

    # ---- contenu niche droite : grande bannière du royaume ----
    lay = layer(56, 96)
    lay.rect(0, 0, 55, 85, RED[2]); lay.vline(0, 0, 85, RED[3]); lay.vline(55, 0, 85, RED[1])
    lay.rect(3, 0, 4, 85, GOLD[2]); lay.rect(51, 0, 52, 85, GOLD[2]); lay.hline(3, 52, 3, GOLD[2]); lay.hline(3, 52, 82, GOLD[2])
    for i in range(29):
        lay.vline(i, 86, 86 + min(9, i // 1 * 9 // 28 * 1 + i // 3), RED[2]); lay.vline(55 - i, 86, 86 + min(9, i // 3), RED[2])
    for x in range(56): lay.px(x, 86 + min(9, min(x, 55 - x) // 3), RED[1])
    big = CREST.resize((CREST.width * 2, CREST.height * 2), Image.NEAREST)
    lay.img.alpha_composite(big, (28 - big.width // 2 + 2, 22))
    for yy in range(8, 80, 9): lay.px(2, yy, RED[1])
    put(p, lay, 213, 62)
    p.rect(206, 60, 276, 61, WOOD[1]); p.hline(206, 276, 60, WOOD[3])
    for x in (205, 277): p.rect(x - 1, 59, x + 1, 62, GOLD[3])
    p.vline(241, 52, 59, IRON[2]); p.vline(226, 55, 59, IRON[2]); p.vline(256, 55, 59, IRON[2])
    # plaque « niveau »
    p.rect(213, 156, 269, 169, K); p.rect(214, 157, 268, 168, GOLD[2]); p.rect(216, 159, 266, 166, RED[1])

    # ---- décor attaché à la structure ----
    for x in (-8, 184):
        lantern(p, x if x < 0 else x, 22) if False else None
    torch(p, 54, 152); torch(p, 120, 152)
    banner(p, 16, 141, 18, 26, RED, "shield")
    banner(p, 142, 141, 18, 26, BLUE, "crown")
    lantern(p, -1, 146); lantern(p, 181, 146)
    # fenêtres éclairées des tours
    # lierre
    ivy(p, -122, 28, 50, 3); ivy(p, 298, 28, 40, 4); ivy(p, 0, 140, 30, 5); ivy(p, 176, 140, 34, 6)
    ivy(p, 62, -2, 10, 7); ivy(p, 114, -2, 12, 8)
    # végétation et accessoires au pied
    for x, r in ((-104, 5), (-92, 4), (-30, 5), (-18, 4), (22, 4), (36, 3), (140, 3), (154, 4), (196, 4), (210, 5), (268, 4), (282, 5)):
        bush(p, x, 182, r, x)
    # tonneaux et caisses contre le mur
    def barrel(x, y):
        l = layer(11, 13)
        planks(l, 0, 0, 10, 12, seed=x, vertical=True, base=2)
        for yy in (2, 9): l.hline(0, 10, yy, IRON[1]); l.hline(0, 10, yy + 1, IRON[3])
        l.rect(1, 0, 9, 0, WOOD[4])
        put(p, l, x, y)
    def crate(x, y, s=11):
        l = layer(s, s)
        planks(l, 0, 0, s - 1, s - 1, seed=x + 7, base=3)
        l.rect(0, 0, s - 1, 0, WOOD[1]); l.rect(0, s - 1, s - 1, s - 1, WOOD[1]); l.vline(0, 0, s - 1, WOOD[1]); l.vline(s - 1, 0, s - 1, WOOD[1])
        for k in range(s - 2): l.px(1 + k, 1 + k, WOOD[1])
        put(p, l, x, y)

    l = layer(16, 7)
    for i in range(7): l.hline(i, 15 - i, 6 - i, GOLD[2] if i % 2 else GOLD[3])
    for k in range(5): l.px(2 + 3 * k, 5 - k % 3, GOLD[4])
    pass

    title_banner(p, -22, 198, -10, 23)
    big_crown(p, 88, -24)
    if demo:
        draw_title(p, 88, -6, "Royaume de Thozire")
        p.text_outline_c(-65, 59, "Ton royaume", (255, 240, 210), RED[0])
        vals = (("Thozire", (70, 46, 30)), ("12 480 écus", (170, 104, 20)), ("+356 écus/min", (40, 116, 40)),
                ("#2 sur 14", (40, 80, 170)), ("2 / 3", (70, 46, 30)))
        for i, (v, c) in enumerate(vals): p.text(-92, 82 + i * 19, v, c, False)
        p.text_c(241, 159, "Niveau 2", (255, 236, 190), True)

def preview(path):
    p = Pix(W, H, OX, OY)
    build(p, demo=True)
    bg = Image.new("RGBA", (W + 40, H + 20), (0, 0, 0, 255))
    d = bg.load()
    for y in range(bg.height):
        for x in range(bg.width):
            v = 26 + ((x // 3 + y // 3) % 2) * 2
            d[x, y] = (v + 8, v, v + 8, 255)
    bg.alpha_composite(p.img, (20, 10))
    bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST).save(path)

if __name__ == "__main__":
    preview("/home/claude/rp/castle_main.png")
    print("ok")
