"""Boîte à outils pixel art « Royaumes » v8 : palettes à teintes décalées, tramage, texte doré, icônes.

Toutes les fonctions dessinent dans un Pix (voir royal_kingdom.Pix).
"""
import math, random
import numpy as np
from PIL import Image
from royal_ui import FONT
from royal_kingdom import Pix, outline, layer, put, disc

# ---------------------------------------------------------------- palettes (sombre -> clair)
K = (30, 16, 26)
STONE = [(34, 30, 48), (52, 48, 70), (74, 70, 94), (100, 96, 118), (128, 122, 142), (158, 150, 164), (190, 180, 186), (220, 210, 206)]
DRESS = [(70, 52, 56), (106, 84, 80), (142, 116, 102), (176, 150, 126), (204, 180, 150), (228, 208, 176), (246, 232, 204)]
WOOD = [(40, 20, 24), (66, 36, 32), (96, 56, 40), (130, 82, 50), (164, 110, 64), (198, 144, 86), (226, 182, 120)]
RED = [(58, 10, 30), (96, 18, 38), (138, 28, 44), (180, 44, 50), (216, 74, 62), (240, 120, 90), (252, 170, 130)]
GOLD = [(84, 40, 20), (140, 78, 22), (196, 124, 30), (230, 172, 50), (250, 214, 96), (255, 240, 170), (255, 252, 226)]
BLUE = [(20, 22, 56), (30, 40, 92), (44, 66, 138), (66, 100, 184), (104, 146, 222), (156, 196, 246)]
ROOF = [(22, 24, 52), (34, 42, 84), (48, 64, 120), (68, 92, 158), (98, 128, 196), (146, 174, 228)]
LEAF = [(18, 40, 42), (28, 66, 50), (44, 98, 54), (74, 134, 58), (118, 170, 70), (172, 206, 102)]
DIRT = [(48, 30, 30), (74, 48, 40), (104, 72, 52), (136, 100, 70), (166, 128, 90)]
IRON = [(30, 30, 42), (52, 54, 70), (82, 86, 106), (122, 126, 146), (170, 174, 192), (220, 224, 236)]
PARCH = [(122, 82, 54), (170, 124, 82), (206, 166, 116), (228, 198, 148), (242, 222, 178), (252, 240, 208)]
SKIN = [(110, 56, 50), (170, 98, 76), (218, 148, 112), (244, 194, 154), (252, 222, 190)]
HAIR = [(40, 22, 24), (72, 40, 32), (110, 66, 40), (150, 98, 54)]
WHITE = [(130, 128, 150), (184, 182, 200), (226, 224, 236), (250, 250, 255)]
FIRE = [(150, 40, 20), (220, 90, 30), (250, 150, 40), (255, 210, 90), (255, 246, 200)]
SKY = [(70, 110, 200), (96, 144, 226), (132, 178, 240), (176, 210, 248), (218, 236, 252)]
DUSK = [(52, 36, 96), (106, 50, 116), (170, 70, 112), (226, 112, 98), (250, 164, 96), (255, 214, 140)]

BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))

def pick(cols, t, x, y):
    """Couleur tramée (Bayer 4x4) le long d'une rampe, t dans [0,1]."""
    t = min(1.0, max(0.0, t))
    f = t * (len(cols) - 1); i = int(f)
    if i >= len(cols) - 1: return cols[-1]
    fr = f - i
    fr = 0.0 if fr < 0.3 else 1.0 if fr > 0.7 else (fr - 0.3) / 0.4      # bandes nettes, tramage aux jonctions
    return cols[i + 1] if fr > (BAYER[y & 3][x & 3] + 0.5) / 16 else cols[i]

def vgrad(p, x0, y0, x1, y1, cols):
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        for x in range(x0, x1 + 1):
            p.px(x, y, pick(cols, t, x, y))

def lathe(p, cx, y0, prof, cols, light=0.28, gamma=1.0):
    """Volume de révolution : prof = demi-largeurs par ligne ; ombrage cylindrique (lumière à gauche)."""
    for i, hw in enumerate(prof):
        if hw is None or hw < 0: continue
        y = y0 + i
        for x in range(int(cx - hw), int(cx + hw) + 1):
            t = (x - (cx - hw)) / max(1, 2 * hw)
            v = max(0.0, math.cos((t - light) * math.pi * 0.95)) ** gamma
            p.px(x, y, pick(cols, v, x, y))

def ellipse(p, cx, cy, rx, ry, cols, light=(-0.45, -0.55)):
    """Disque ombré façon sphère (lumière haut-gauche)."""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            dx, dy = (x - cx) / max(.5, rx), (y - cy) / max(.5, ry)
            d = dx * dx + dy * dy
            if d <= 1.0:
                nz = math.sqrt(max(0, 1 - d))
                v = max(0, -dx * light[0] - dy * light[1] + nz * 0.75) / 1.45
                p.px(x, y, pick(cols, v, x, y))

def glow(p, cx, cy, r, col, a=60):
    for rr in range(r, 0, -max(1, r // 4)):
        disc(p, cx, cy, rr, col + (int(a * (1 - rr / r) + a * 0.25),))

def finish(lay, col=K, shadow=None):
    """Contour + ombre portée éventuelle d'un calque, renvoie l'image."""
    im = outline(lay.img, col)
    if shadow:
        a = np.array(im)[:, :, 3] > 0
        sh = np.zeros((*a.shape, 4), np.uint8); sh[a] = shadow
        base = Image.new("RGBA", im.size, (0, 0, 0, 0))
        s = Image.fromarray(sh)
        base.alpha_composite(s, (1, 2)) if False else None
    return im

def stamp(p, lay, x, y, col=K, drop=(14, 6, 16, 90), dx=1, dy=2):
    """Colle un calque (avec contour) à (x,y) = coin de la zone utile, et ombre portée."""
    im = outline(lay.img, col)
    if drop:
        a = np.array(im)[:, :, 3] > 0
        sh = np.zeros((*a.shape, 4), np.uint8); sh[a] = drop
        p.paste(Image.fromarray(sh), x - lay.ox + dx, y - lay.oy + dy)
    p.paste(im, x - lay.ox, y - lay.oy)

# ---------------------------------------------------------------- texte doré stylisé
TITLE_GRAD = [(255, 252, 232), (255, 246, 190), (255, 234, 146), (253, 220, 106), (249, 204, 80), (243, 188, 62), (233, 170, 50),
              (206, 130, 34), (222, 150, 42), (236, 172, 54), (246, 192, 70), (241, 180, 60), (226, 156, 46), (202, 128, 36)]
LABEL_GRAD = [(255, 248, 200), (255, 230, 130), (248, 202, 74), (232, 170, 50), (196, 120, 30), (216, 150, 44), (178, 104, 28),
              (150, 84, 24), (130, 70, 22)]
CREAM_GRAD = [(255, 252, 236), (252, 240, 208), (244, 226, 186), (232, 210, 166), (214, 188, 144), (226, 204, 160), (200, 172, 130),
              (180, 152, 112), (160, 134, 98)]

def glyph_mask(ch, scale=1, bold=False):
    """Masque bool d'un caractère, avec la ligne des majuscules à y = 3*scale ; renvoie (mask, avance)."""
    if ch == " ": return None, 4 * scale
    g = FONT.glyphs.get(ch)
    if not g: return None, 6 * scale
    cell, adv, asc, chh = g
    m = Image.new("L", (cell.width + 2, 14), 0)
    m.paste(255, (0, 3 + 7 - asc), cell.split()[3])
    if scale != 1: m = m.resize((m.width * scale, m.height * scale), Image.NEAREST)
    a = np.array(m) > 0
    if bold:
        b = a.copy(); b[:, scale:] |= a[:, :-scale]; a = b
    return a, (adv + (1 if bold else 0)) * scale

def text_width(s, scale=1, bold=False):
    return sum(glyph_mask(c, scale, bold)[1] for c in s)

def _dil(b):
    n = b.copy()
    n[1:, :] |= b[:-1, :]; n[:-1, :] |= b[1:, :]; n[:, 1:] |= b[:, :-1]; n[:, :-1] |= b[:, 1:]
    n[1:, 1:] |= b[:-1, :-1]; n[:-1, :-1] |= b[1:, 1:]; n[1:, :-1] |= b[:-1, 1:]; n[:-1, 1:] |= b[1:, :-1]
    return n

def mc_glyph(scale, bold):
    def g(ch):
        a, adv = glyph_mask(ch, scale, bold)
        return a, adv, 3 * scale, 10 * scale - 1
    return g

def fancy_text(p, x, y, s, scale=1, bold=False, grad=LABEL_GRAD, out=(40, 16, 14), extrude=1,
               ext_cols=((96, 34, 22), (70, 22, 20), (52, 16, 18)), offs=None, shine=True, font=None):
    """Texte en relief : dégradé métallique, contour, extrusion vers le bas.
    (x, y) = coin haut-gauche de la ligne des majuscules. offs(i, cx) -> décalage vertical par lettre."""
    pad = 2 + extrude
    cur = x
    font = font or mc_glyph(scale, bold)
    for i, ch in enumerate(s):
        a, adv, cap, basel = font(ch)
        if a is None:
            cur += adv; continue
        h, w = a.shape
        A_ = np.zeros((h + 2 * pad, w + 2 * pad), bool); A_[pad:pad + h, pad:pad + w] = a
        ext = np.zeros_like(A_)
        for k in range(1, extrude + 1):
            sh = np.zeros_like(A_); sh[k:, :] = A_[:-k, :]; ext |= sh
        body = A_ | ext
        ol = _dil(body) & ~body
        img = np.zeros((*A_.shape, 4), np.uint8)
        img[ol] = out + (255,)
        for k in range(extrude, 0, -1):
            sh = np.zeros_like(A_); sh[k:, :] = A_[:-k, :]
            img[sh & ~A_] = ext_cols[min(len(ext_cols) - 1, k - 1)] + (255,)
        rows_on = np.where(A_.any(axis=1))[0]
        top = rows_on[0] if len(rows_on) else pad
        base = pad + basel                              # ligne de base
        rows = max(1, base - top + 1)
        for yy in range(img.shape[0]):
            t = (yy - top) / rows
            c = grad[max(0, min(len(grad) - 1, int(t * (len(grad) - 1) * 1.0 + 0.5)))]
            img[yy][A_[yy]] = c + (255,)
        if shine:
            edge = A_ & ~np.vstack([np.zeros((1, A_.shape[1]), bool), A_[:-1]])
            img[edge] = (255, 255, 240, 255)
        dy = offs(i, cur + w // 2) if offs else 0
        p.paste(Image.fromarray(img), cur - pad, y - pad - cap + dy)
        cur += adv
    return cur

def fancy_text_c(p, cx, y, s, **kw):
    f = kw.get("font")
    w = sum(f(c)[1] for c in s) if f else text_width(s, kw.get("scale", 1), kw.get("bold", False))
    return fancy_text(p, cx - w // 2, y, s, **kw)

# ---------------------------------------------------------------- icônes (≈ 14 px)
def icon_crown():
    L = layer(15, 12)
    # bandeau
    vgrad(L, 0, 7, 14, 11, [GOLD[5], GOLD[4], GOLD[3], GOLD[2], GOLD[1]])
    # pointes
    for px_, ph in ((1, 5), (7, 7), (13, 5)):
        for yy in range(7 - ph, 7):
            hw = (yy - (7 - ph)) * 2 // ph
            for xx in range(px_ - hw, px_ + hw + 1):
                L.px(xx, yy, GOLD[4] if xx <= px_ else GOLD[2])
        ellipse(L, px_, 7 - ph - 1, 1.2, 1.2, [GOLD[2], GOLD[4], GOLD[6]])
    for yy in (4, 5, 6):
        L.hline(3, 5, yy, GOLD[3] if yy > 4 else (0, 0, 0, 0)); L.hline(9, 11, yy, GOLD[2] if yy > 4 else (0, 0, 0, 0))
    L.hline(0, 14, 7, GOLD[5])
    for gx, gc in ((3, RED), (7, BLUE), (11, RED)):
        L.rect(gx - 1, 8, gx + 1, 10, gc[3]); L.px(gx - 1, 8, gc[5]); L.px(gx + 1, 10, gc[1])
    L.hline(0, 14, 11, GOLD[1])
    return L

def icon_coins():
    L = layer(15, 13)
    def coin(cx, cy):
        ellipse(L, cx, cy + 1, 4, 1.6, [GOLD[0], GOLD[1], GOLD[2]])
        ellipse(L, cx, cy, 4, 1.6, [GOLD[2], GOLD[4], GOLD[5], GOLD[6]])
    for i in range(4): coin(4, 11 - i * 2)
    for i in range(2): coin(10, 11 - i * 2)
    # pièce debout
    ellipse(L, 10, 4, 3.6, 3.8, [GOLD[1], GOLD[3], GOLD[4], GOLD[6]])
    L.vline(10, 2, 6, GOLD[1]); L.px(9, 3, GOLD[2]); L.px(11, 5, GOLD[2])
    return L

def icon_hourglass():
    L = layer(11, 14)
    L.rect(0, 0, 10, 1, WOOD[4]); L.hline(0, 10, 0, WOOD[6]); L.rect(0, 12, 10, 13, WOOD[3]); L.hline(0, 10, 13, WOOD[1])
    prof = [3.6, 3.4, 3.0, 2.2, 1.2, 0.6, 0.6, 1.2, 2.2, 3.0, 3.4, 3.6]
    lathe(L, 5, 1, [None] + prof[1:-1] + [None], [(120, 170, 200), (170, 214, 236), (226, 244, 252)])
    # sable
    for yy, hw in ((3, 2.2), (4, 1.0), (8, 1.2), (9, 2.2), (10, 3.0)):
        for xx in range(int(5 - hw), int(5 + hw) + 1): L.px(xx, yy, GOLD[4] if xx < 5 else GOLD[3])
    L.vline(5, 5, 8, GOLD[4])
    L.vline(1, 2, 11, WOOD[3]); L.vline(9, 2, 11, WOOD[2])
    return L

def icon_trophy():
    L = layer(15, 14)
    prof = [6, 6, 5.6, 5.2, 4.6, 3.8, 2.6, 1.4, 1, 1, 2.4, 3.4, 3.6]
    lathe(L, 7, 0, prof, [GOLD[1], GOLD[2], GOLD[3], GOLD[4], GOLD[5], GOLD[6]])
    # anses
    for side in (-1, 1):
        for yy, dx in ((1, 7), (2, 8), (3, 8), (4, 7), (5, 6)):
            L.px(7 + side * dx, yy, GOLD[3] if side < 0 else GOLD[2])
    L.hline(2, 12, 0, GOLD[1]); L.hline(3, 11, 1, GOLD[0])
    L.rect(3, 12, 11, 13, WOOD[3]); L.hline(3, 11, 12, WOOD[5]); L.hline(3, 11, 13, WOOD[1])
    L.px(7, 4, (255, 255, 255)); L.px(6, 3, GOLD[6])
    return L

def icon_people():
    L = layer(16, 14)
    def bust(cx, top, body, hair):
        lathe(L, cx, top + 7, [2, 3, 4, 4.5, 4.8, 5], body)
        ellipse(L, cx, top + 3, 2.8, 3.2, SKIN[1:])
        for xx in range(cx - 3, cx + 4):
            L.px(xx, top, hair[2]); L.px(xx, top + 1, hair[1 if xx > cx else 3])
        L.px(cx - 3, top + 2, hair[2]); L.px(cx + 3, top + 2, hair[1])
        L.px(cx - 1, top + 3, K); L.px(cx + 1, top + 3, K)
    bust(11, 1, BLUE[1:], HAIR)
    bust(5, 2, RED[1:], [HAIR[0], (150, 90, 40), (200, 140, 60), (230, 180, 90)])
    return L

def icon_scroll_seal():
    L = layer(10, 10)
    ellipse(L, 5, 5, 4.4, 4.4, RED[1:])
    L.rect(4, 3, 6, 6, RED[2]); L.px(5, 2, RED[5])
    return L

def icon_chest():
    L = layer(14, 12)
    vgrad(L, 0, 4, 13, 11, [WOOD[5], WOOD[4], WOOD[3], WOOD[2]])
    vgrad(L, 0, 0, 13, 4, [WOOD[6], WOOD[5], WOOD[4]])
    L.hline(0, 13, 4, WOOD[1]); L.hline(0, 13, 11, WOOD[1])
    for x in (0, 13): L.vline(x, 0, 11, IRON[2])
    for x in (3, 10): L.vline(x, 0, 11, IRON[3])
    L.rect(6, 3, 7, 6, GOLD[4]); L.px(6, 3, GOLD[6]); L.px(7, 6, GOLD[2])
    return L

def icon_arrow():
    L = layer(13, 13)
    rows = ["......#......", ".....###.....", "....#####....", "...#######...", "..#########..", ".###########.", "....#####....",
            "....#####....", "....#####....", "....#####....", "....#####....", "....#####...."]
    G = [(30, 96, 40), (60, 150, 60), (110, 200, 90), (180, 240, 150)]
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "#": L.px(x, y, G[3] if x < 5 and y > 5 else G[2] if x < 7 else G[1])
    return L

ICON_FUNCS = {"chest": icon_chest, "arrow": icon_arrow, "crown": icon_crown, "coins": icon_coins, "hourglass": icon_hourglass, "trophy": icon_trophy, "people": icon_people}

def icon(name):
    return ICON_FUNCS[name]()

def draw_icon(p, name, x, y, out=K):
    stamp(p, icon(name), x, y, out, drop=(30, 14, 10, 70), dx=1, dy=1)
