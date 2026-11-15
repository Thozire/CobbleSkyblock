"""Interface « Royaumes » — style Minecraft vanilla, pixel art 1:1.

Fenêtre centrale = le coffre (176 px), deux panneaux latéraux pour les infos.
Toutes les coordonnées sont dans le repère du coffre (0,0 = coin haut-gauche).
"""
import random
from PIL import Image, ImageEnhance
from royal_ui import Canvas, FONT, slot_xy, OX, OY, W, H

T = "/home/claude/mcassets/assets/minecraft/textures/"

# ---------- couleurs vanilla ----------
BG, HI, SH, BLK = (198, 198, 198), (255, 255, 255), (85, 85, 85), (0, 0, 0)
SLOT_BG, SLOT_D = (139, 139, 139), (55, 55, 55)
TXT = (64, 64, 64)
GOLD_T, GREEN_T, BLUE_T, RED_T, AQUA_T = (255, 170, 0), (85, 255, 85), (85, 170, 255), (255, 85, 85), (85, 255, 255)

_cache = {}
def tex(name, size=None):
    key = (name, size)
    if key not in _cache:
        im = Image.open(T + name + ".png").convert("RGBA")
        if im.height > im.width: im = im.crop((0, 0, im.width, im.width))  # textures animées
        if size: im = im.resize((size, size), Image.BOX)
        _cache[key] = im
    return _cache[key]

def tint(im, rgb):
    r, g, b = rgb
    px = im.copy(); d = px.load()
    for y in range(px.height):
        for x in range(px.width):
            p = d[x, y]
            d[x, y] = (p[0] * r // 255, p[1] * g // 255, p[2] * b // 255, p[3])
    return px

def paste(cv, im, x, y, shadow=False):
    if shadow:
        a = im.split()[3]
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.paste((20, 20, 20, 110), (0, 0), a)
        cv.img.alpha_composite(sh, (x + OX + 1, y + OY + 1))
    cv.img.alpha_composite(im, (x + OX, y + OY))

def fill_tex(cv, x0, y0, x1, y1, im, dark=1.0):
    if dark != 1.0: im = ImageEnhance.Brightness(im).enhance(dark)
    for y in range(y0, y1 + 1, im.height):
        for x in range(x0, x1 + 1, im.width):
            c = im.crop((0, 0, min(im.width, x1 - x + 1), min(im.height, y1 - y + 1)))
            cv.img.alpha_composite(c, (x + OX, y + OY))

def face(skin, scale=2):
    s = Image.open(T + "entity/player/wide/" + skin + ".png").convert("RGBA")
    f = s.crop((8, 8, 16, 16)); hat = s.crop((40, 8, 48, 16))
    f.alpha_composite(hat)
    return f.resize((8 * scale, 8 * scale), Image.NEAREST)

# ---------- éléments vanilla ----------
def window(cv, x0, y0, x1, y1):
    """Panneau gris vanilla (comme generic_54) avec coins arrondis."""
    cv.rect(x0 + 2, y0, x1 - 3, y0, BLK); cv.rect(x0 + 3, y1, x1 - 2, y1, BLK)
    cv.rect(x0, y0 + 2, x0, y1 - 3, BLK); cv.rect(x1, y0 + 3, x1, y1 - 2, BLK)
    cv.px(x0 + 1, y0 + 1, BLK); cv.px(x1 - 2, y0 + 1, BLK); cv.px(x1 - 1, y0 + 2, BLK)
    cv.px(x1 - 1, y1 - 1, BLK); cv.px(x0 + 1, y1 - 2, BLK); cv.px(x0 + 2, y1 - 1, BLK)
    cv.rect(x0 + 1, y0 + 2, x1 - 1, y1 - 2, BG); cv.rect(x0 + 2, y0 + 1, x1 - 2, y1 - 1, BG)
    cv.rect(x0 + 2, y0 + 1, x1 - 3, y0 + 2, HI); cv.rect(x0 + 1, y0 + 2, x0 + 2, y1 - 3, HI)
    cv.px(x0 + 3, y0 + 3, HI)
    cv.rect(x0 + 3, y1 - 2, x1 - 2, y1 - 1, SH); cv.rect(x1 - 2, y0 + 3, x1 - 1, y1 - 2, SH)
    cv.px(x1 - 3, y1 - 3, SH)

def inset(cv, x0, y0, x1, y1, fill=SLOT_BG):
    cv.rect(x0, y0, x1, y1, fill)
    cv.hline(x0, x1 - 1, y0, SLOT_D); cv.vline(x0, y0, y1 - 1, SLOT_D)
    cv.hline(x0 + 1, x1, y1, HI); cv.vline(x1, y0 + 1, y1, HI)
    cv.px(x1, y0, SLOT_BG); cv.px(x0, y1, SLOT_BG)

def slot(cv, x, y, item=None):
    inset(cv, x, y, x + 17, y + 17)
    if item is not None: paste(cv, item, x + 1, y + 1)

_btn = Image.open(T + "gui/sprites/widget/button.png").convert("RGBA")
def button(cv, x0, y0, x1, y1, tint_rgb=None):
    """Bouton vanilla étiré en nine-slice (bordure 3), éventuellement teinté."""
    src = _btn if tint_rgb is None else tint(_btn, tint_rgb)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    out = Image.new("RGBA", (w, h))
    b = 3
    mid_w, mid_h = 200 - 2 * b, 20 - 2 * b
    def blit(sx0, sy0, sx1, sy1, dx0, dy0, dx1, dy1):
        piece = src.crop((sx0, sy0, sx1, sy1))
        for yy in range(dy0, dy1, piece.height):
            for xx in range(dx0, dx1, piece.width):
                out.alpha_composite(piece.crop((0, 0, min(piece.width, dx1 - xx), min(piece.height, dy1 - yy))), (xx, yy))
    blit(0, 0, b, b, 0, 0, b, b); blit(200 - b, 0, 200, b, w - b, 0, w, b)
    blit(0, 20 - b, b, 20, 0, h - b, b, h); blit(200 - b, 20 - b, 200, 20, w - b, h - b, w, h)
    blit(b, 0, 200 - b, b, b, 0, w - b, b); blit(b, 20 - b, 200 - b, 20, b, h - b, w - b, h)
    blit(0, b, b, 20 - b, 0, b, b, h - b); blit(200 - b, b, 200, 20 - b, w - b, b, w, h - b)
    blit(b, b, 200 - b, 20 - b, b, b, w - b, h - b)
    cv.img.alpha_composite(out, (x0 + OX, y0 + OY))

def frame_box(cv, x0, y0, x1, y1, bg_tex, dark=0.55):
    """Petit cadre façon cadre d'objet : bordure noire + bois de bouleau + fond texturé."""
    cv.rect(x0, y0, x1, y1, BLK)
    fill_tex(cv, x0 + 1, y0 + 1, x1 - 1, y1 - 1, tex("block/stripped_birch_log", 16), 0.95)
    cv.hline(x0 + 1, x1 - 1, y0 + 1, (232, 220, 176)); cv.vline(x0 + 1, y0 + 1, y1 - 1, (232, 220, 176))
    cv.hline(x0 + 1, x1 - 1, y1 - 1, (120, 100, 70)); cv.vline(x1 - 1, y0 + 1, y1 - 1, (120, 100, 70))
    cv.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, BLK)
    fill_tex(cv, x0 + 3, y0 + 3, x1 - 3, y1 - 3, bg_tex, dark)

def divider(cv, x0, x1, y):
    cv.hline(x0, x1, y, SH); cv.hline(x0 + 1, x1 + 1, y + 1, HI)
    cx = (x0 + x1) // 2
    for dx, c in ((0, GOLD_T),):
        cv.rect(cx - 1, y - 1, cx + 1, y + 2, (120, 80, 20)); cv.px(cx, y, GOLD_T); cv.px(cx, y + 1, (255, 220, 120))

# ---------- petites scènes pixel art ----------
GRASS = (124, 189, 107)
def sky(cv, x0, y0, x1, y1, top=(120, 167, 255), bot=(196, 222, 255)):
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        cv.hline(x0, x1, y, tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))

def cloud(cv, x, y):
    for dx, dy, w in ((2, 0, 6), (0, 1, 11), (1, 2, 9)):
        cv.hline(x + dx, x + dx + w - 1, y + dy, (255, 255, 255))
    cv.hline(x + 1, x + 9, y + 3, (226, 234, 250))

def block8(name, t=None):
    im = tex(name, 8)
    return tint(im, t) if t else im

def diorama_home(cv, x0, y0, w=62, h=30):
    """Mini-paysage : maison en bois, arbre, chemin — le royaume du joueur."""
    x1, y1 = x0 + w - 1, y0 + h - 1
    sky(cv, x0, y0, x1, y1)
    cloud(cv, x0 + 4, y0 + 3); cloud(cv, x0 + 40, y0 + 6)
    cv.rect(x0 + 52, y0 + 2, x0 + 57, y0 + 7, (255, 250, 200)); cv.rect(x0 + 53, y0 + 3, x0 + 56, y0 + 6, (255, 255, 235))
    # collines lointaines
    for i, x in enumerate(range(x0, x1 + 1)):
        hh = int(4 + 2.5 * __import__("math").sin(i / 6.0) + 1.5 * __import__("math").sin(i / 2.3))
        cv.vline(x, y1 - 7 - hh, y1 - 8, (110, 160, 120))
    gy = y1 - 7
    side = tint(tex("block/grass_block_side", 8), (255, 255, 255))
    over = tint(tex("block/grass_block_side_overlay", 8), GRASS)
    for x in range(x0, x1 + 1, 8):
        c = side.copy(); c.alpha_composite(over)
        c = c.crop((0, 0, min(8, x1 - x + 1), 8))
        cv.img.alpha_composite(c, (x + OX, gy + OY))
    # maison
    hx = x0 + 18
    fill_tex(cv, hx, gy - 14, hx + 21, gy - 1, block8("block/oak_planks"))
    for lx in (hx, hx + 19):
        fill_tex(cv, lx, gy - 14, lx + 2, gy - 1, tex("block/oak_log", 8).crop((0, 0, 3, 8)))
    # toit en escalier (briques sombres)
    roof = [(105, 52, 36), (138, 70, 46), (164, 88, 58)]
    for i in range(7):
        cv.hline(hx - 2 + i, hx + 23 - i, gy - 15 - i, roof[i % 3] if i else (70, 34, 24))
        cv.hline(hx - 1 + i, hx + 22 - i, gy - 15 - i, roof[(i + 1) % 3])
    cv.hline(hx - 2, hx + 23, gy - 15, (70, 34, 24))
    # cheminée + fumée
    cv.rect(hx + 16, gy - 22, hx + 18, gy - 17, (120, 120, 120)); cv.hline(hx + 16, hx + 18, gy - 22, (90, 90, 90))
    for i, (dx, dy) in enumerate(((17, -25), (18, -27), (20, -28))):
        cv.px(hx + dx, gy + dy, (230, 230, 230)); cv.px(hx + dx + 1, gy + dy, (200, 200, 200))
    # porte + fenêtres
    door = tex("block/oak_door_bottom", 8).crop((1, 0, 7, 8)); doort = tex("block/oak_door_top", 8).crop((1, 2, 7, 8))
    paste(cv, doort, hx + 8, gy - 14 + 0); paste(cv, door, hx + 8, gy - 8)
    for wx in (hx + 3, hx + 16):
        cv.rect(wx, gy - 11, wx + 3, gy - 8, (60, 40, 20)); cv.rect(wx + 1, gy - 10, wx + 2, gy - 9, (255, 214, 120))
    # arbre
    tx = x0 + 49
    cv.rect(tx + 3, gy - 9, tx + 4, gy - 1, (102, 78, 46)); cv.vline(tx + 3, gy - 9, gy - 1, (78, 58, 34))
    leaves = tint(tex("block/oak_leaves", 8), (72, 181, 24))
    for (lx, ly) in ((0, -16), (5, -16), (-2, -12), (3, -12), (8, -13), (2, -19)):
        paste(cv, leaves.crop((0, 0, 6, 5)), tx + lx, gy + ly)
    # bannière rouge
    bx = x0 + 9
    cv.vline(bx, gy - 16, gy - 1, (90, 66, 40))
    cv.rect(bx + 1, gy - 15, bx + 5, gy - 7, (176, 46, 38)); cv.hline(bx + 1, bx + 5, gy - 15, (210, 70, 60))
    cv.px(bx + 3, gy - 12, GOLD_T); cv.px(bx + 2, gy - 11, GOLD_T); cv.px(bx + 4, gy - 11, GOLD_T); cv.px(bx + 3, gy - 10, GOLD_T)
    cv.px(bx + 1, gy - 6, (176, 46, 38)); cv.px(bx + 5, gy - 6, (176, 46, 38))
    # chemin
    for i in range(7):
        cv.hline(hx + 8 - i // 2, hx + 13 + i // 3, gy + i, (172, 140, 96) if i % 2 else (150, 120, 80))
    # cadre
    cv.outline(x0 - 1, y0 - 1, x1 + 1, y1 + 1, BLK, round_=False)

def castle_icon(cv, x0, y0, s=26):
    """Petite capitale : murailles en pierre, tours, toits dorés, drapeau."""
    x1, y1 = x0 + s - 1, y0 + s - 1
    sky(cv, x0, y0, x1, y1, (255, 170, 100), (255, 222, 160))
    cv.rect(x0 + 18, y0 + 3, x0 + 21, y0 + 6, (255, 246, 200))
    st = tex("block/stone_bricks", 8)
    gy = y1 - 2
    cv.rect(x0, gy, x1, y1, (94, 157, 52)); cv.hline(x0, x1, gy, (124, 189, 107))
    # mur
    fill_tex(cv, x0 + 3, gy - 8, x1 - 3, gy - 1, st)
    for x in range(x0 + 3, x1 - 2, 3): cv.rect(x, gy - 10, x + 1, gy - 9, (130, 130, 130))
    # tours
    for tx in (x0 + 1, x1 - 6):
        fill_tex(cv, tx, gy - 13, tx + 5, gy - 1, st)
        for i in range(4):
            cv.hline(tx + i // 1 - 1 + (1 if i else 0), tx + 6 - i, gy - 14 - i, (240, 184, 40) if i % 2 else (200, 140, 20))
        cv.vline(tx, gy - 13, gy - 1, (80, 80, 80))
    # donjon
    kx = x0 + 9
    fill_tex(cv, kx, gy - 13, kx + 7, gy - 1, st)
    for i in range(4): cv.hline(kx - 1 + i, kx + 8 - i, gy - 14 - i, (240, 184, 40) if i % 2 == 0 else (200, 140, 20))
    cv.vline(kx + 3, gy - 20, gy - 18, (60, 40, 20))
    cv.rect(kx + 4, gy - 20, kx + 7, gy - 19, (200, 40, 40)); cv.px(kx + 7, gy - 18, (200, 40, 40))
    cv.rect(kx + 2, gy - 5, kx + 5, gy - 1, (50, 34, 20)); cv.hline(kx + 3, kx + 4, gy - 6, (50, 34, 20))
    cv.px(kx + 3, gy - 9, (255, 214, 120)); cv.px(kx + 4, gy - 9, (255, 214, 120))

def arrow_up(cv, x, y, col=(85, 255, 85), dark=(20, 110, 20)):
    rows = ["...X...", "..XXX..", ".XXXXX.", "XXXXXXX", "..XXX..", "..XXX..", "..XXX.."]
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c == "X":
                cv.px(x + i + 1, y + j + 1, dark)
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c == "X": cv.px(x + i, y + j, col)

def sparkle(cv, x, y, c=(255, 255, 200)):
    cv.px(x, y, c); cv.px(x - 1, y, c[:3] + (150,)); cv.px(x + 1, y, c[:3] + (150,)); cv.px(x, y - 1, c[:3] + (150,)); cv.px(x, y + 1, c[:3] + (150,))

def icon_tile(cv, kind, x, y):
    s = 24
    if kind == "batiments":
        frame_box(cv, x - 3, y - 3, x + s + 2, y + s + 2, tex("block/bricks"), 0.45)
        paste(cv, tex("item/oak_door"), x + 1, y + 4, True)
        paste(cv, tex("item/iron_axe"), x + 10, y + 7, True)
    elif kind == "ameliorer":
        frame_box(cv, x - 3, y - 3, x + s + 2, y + s + 2, tex("block/emerald_block"), 0.40)
        paste(cv, tex("item/experience_bottle"), x + 1, y + 6, True)
        paste(cv, tex("item/emerald"), x + 10, y + 9, True)
        arrow_up(cv, x + 16, y + 1)
        sparkle(cv, x + 4, y + 3); sparkle(cv, x + 23, y + 20)
    elif kind == "membres":
        frame_box(cv, x - 3, y - 3, x + s + 2, y + s + 2, tex("block/blue_wool"), 0.45)
        for i, sk in enumerate(("alex", "efe", "steve")):
            f = face(sk, 2 if i == 2 else 1)
        paste(cv, face("alex", 1).resize((12, 12), Image.NEAREST) if False else face("alex", 1), x + 1, y + 4, True)
        paste(cv, face("efe", 1), x + 17, y + 4, True)
        paste(cv, face("steve", 2), x + 5, y + 9, True)
        # petite couronne sur le chef
        for i, px_ in enumerate((0, 2, 4)): cv.px(x + 9 + px_ * 2, y + 6, GOLD_T)
        cv.hline(x + 9, x + 17, y + 7, (255, 200, 40)); cv.hline(x + 9, x + 17, y + 8, (200, 140, 20))
    elif kind == "capitale":
        cv.rect(x - 3, y - 3, x + s + 2, y + s + 2, BLK)
        fill_tex(cv, x - 2, y - 2, x + s + 1, y + s + 1, tex("block/stripped_birch_log", 16), 0.95)
        cv.rect(x - 1, y - 1, x + s, y + s, BLK)
        castle_icon(cv, x, y, s)

# ---------- page principale ----------
def stat_row(cv, x, y, item, label, value=None, vcol=(255, 255, 255)):
    slot(cv, x, y, item)
    cv.text(x + 22, y + 1, label, TXT, False)
    if value: cv.text(x + 22, y + 10, value, vcol, True)

def side_panel(cv, x0, y0, x1, y1, title, emblem):
    window(cv, x0, y0, x1, y1)
    inset(cv, x0 + 5, y0 + 5, x1 - 5, y0 + 20, (110, 110, 110))
    paste(cv, emblem, x0 + 7, y0 + 5, True)
    cv.text(x0 + 26, y0 + 9, title, (255, 255, 255), True)

def big_button(cv, x0, y0, x1, y1, tint_rgb=None):
    button(cv, x0, y0, x1, y1, tint_rgb)

def page_main(cv, demo=False):
    # ---- fenêtre centrale (le coffre) ----
    window(cv, -6, 0, 181, 163)
    # bandeau titre : bannière de part et d'autre
    for bx, col in ((2, (176, 46, 38)), (167, (46, 86, 176))):
        cv.vline(bx + 3, 3, 4, (90, 66, 40)); cv.hline(bx, bx + 6, 3, (90, 66, 40))
        cv.rect(bx + 1, 4, bx + 5, 12, col); cv.hline(bx + 1, bx + 5, 4, tuple(min(255, c + 40) for c in col))
        cv.px(bx + 3, 8, GOLD_T); cv.px(bx + 2, 7, GOLD_T); cv.px(bx + 4, 7, GOLD_T)
        cv.px(bx + 1, 13, col); cv.px(bx + 5, 13, col); cv.px(bx + 3, 13, col)
    # Héros : Aller à mon royaume (slots 0..17)
    big_button(cv, 0, 16, 175, 53)
    diorama_home(cv, 4, 19, 58, 32)
    # Bâtiments / Améliorer (slots 18..35)
    big_button(cv, 0, 55, 86, 89); icon_tile(cv, "batiments", 5, 60)
    big_button(cv, 89, 55, 175, 89); icon_tile(cv, "ameliorer", 94, 60)
    # Membres / Capitale (slots 36..53)
    big_button(cv, 0, 91, 86, 125); icon_tile(cv, "membres", 5, 96)
    big_button(cv, 89, 91, 175, 125); icon_tile(cv, "capitale", 94, 96)
    # sillon « Inventaire » (le texte vanilla #404040 s'y fond)
    inset(cv, 0, 127, 175, 137, TXT)
    # pied : aide + fermer (slots 54 et 62)
    for sx, c in ((7, None), (151, (255, 150, 150))):
        button(cv, sx, 139, sx + 17, 156, c)
    q = [".XXX.", "X...X", "...X.", "..X..", ".....", "..X.."]
    for j, r in enumerate(q):
        for i, ch in enumerate(r):
            if ch == "X": cv.px(9 + 5 + i, 142 + 2 + j + 1, (63, 63, 63)); cv.px(9 + 4 + i, 142 + 2 + j, (255, 255, 255))
    for i in range(7):
        for (a, b) in ((i, i), (i, 6 - i)):
            cv.px(157 + a, 144 + b + 1, (63, 20, 20)); cv.px(156 + a, 144 + b, (255, 255, 255))
    inset(cv, 28, 140, 147, 155, (110, 110, 110))

    # ---- panneau gauche : Ton royaume ----
    side_panel(cv, -130, 0, -10, 163, "Ton royaume", tex("item/golden_helmet"))
    ys = 28
    stat_row(cv, -124, ys, face("steve", 2), "Seigneur")
    stat_row(cv, -124, ys + 25, tex("item/gold_ingot"), "Trésor")
    stat_row(cv, -124, ys + 50, tex("item/clock_00"), "Revenu")
    stat_row(cv, -124, ys + 75, tex("item/nether_star"), "Rang")
    stat_row(cv, -124, ys + 100, tex("item/name_tag"), "Membres")

    # ---- panneau droit : Domaine ----
    side_panel(cv, 186, 0, 306, 163, "Ton domaine", tex("item/filled_map"))
    stat_row(cv, 192, ys, tex("item/map"), "Taille")
    stat_row(cv, 192, ys + 25, tex("item/brick"), "Bâtiments")
    stat_row(cv, 192, ys + 50, tex("item/wheat"), "Production")
    stat_row(cv, 192, ys + 75, tex("item/chest_minecart"), "Entrepôts")
    stat_row(cv, 192, ys + 100, tex("item/emerald"), "Amélioration")

    if demo: demo_text(cv)

def demo_text(cv):
    W_, Y_ = (255, 255, 255), (255, 255, 160)
    cv.text_c(88, 5, "Royaume de Thozire", TXT, False)
    cv.text(68, 23, "Aller à mon royaume", W_, True)
    cv.text(68, 34, "Niv. 2 · 5 bâtiments", (190, 190, 190), True)
    cv.text(68, 43, "» Téléportation", Y_, True)
    for x, y, a, b in ((33, 63, "Bâtiments", "» Gérer"), (122, 63, "Améliorer", "» Niv. 3"),
                       (33, 99, "Membres", "» 2 / 3"), (122, 99, "Capitale", "» Y aller")):
        cv.text(x, y, a, W_, True); cv.text(x, y + 11, b, Y_, True)
    cv.text_c(88, 144, "Niveau 2 · 81×81", (220, 220, 220), True)
    for i, (v, c) in enumerate((("Thozire", W_), ("12 480 écus", GOLD_T), ("+356 écus/min", GREEN_T),
                                 ("#2 sur 14", AQUA_T), ("2 / 3", W_))):
        cv.text(-124 + 22, 38 + 25 * i, v, c, True)
    for i, (v, c) in enumerate((("81 × 81", W_), ("5 / 12", W_), ("98 objets/min", GREEN_T),
                                 ("1 842 écus", GOLD_T), ("8 000 écus", BLUE_T))):
        cv.text(192 + 22, 38 + 25 * i, v, c, True)

def preview(page_fn, path):
    cv = Canvas()
    page_fn(cv, demo=True)
    # fond = monde assombri
    bg = Image.new("RGBA", (W + 40, H + 20), (0, 0, 0, 255))
    fill = tex("block/dirt", 16)
    for y in range(0, bg.height, 16):
        for x in range(0, bg.width, 16):
            bg.alpha_composite(ImageEnhance.Brightness(fill).enhance(0.25), (x, y))
    bg.alpha_composite(cv.img, (20, 10))
    bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST).save(path)

if __name__ == "__main__":
    preview(page_main, "/home/claude/rp/mc_main.png")
    print("ok")
