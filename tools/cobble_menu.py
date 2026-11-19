"""Maquette du menu /is « Cobblemon tycoon » : panneau gris arrondi, boutons icône + étiquette colorée.

Tout est dessiné en pixel art 1:1 (une unité = un pixel d'interface Minecraft), puis agrandi pour l'aperçu.
"""
import random
from PIL import Image
from royal_ui import FONT
from royal_kingdom import Pix, outline, layer, sprite
from royal_art import pick, vgrad, ellipse, fancy_text_c

K = (34, 30, 44)

# palettes des étiquettes (sombre -> clair)
ORANGE = [(150, 70, 10), (214, 112, 18), (244, 154, 32), (252, 188, 56), (255, 214, 110), (255, 236, 170)]
GREEN = [(40, 100, 30), (70, 150, 40), (110, 196, 60), (146, 222, 84), (186, 240, 124), (220, 252, 180)]
BLUE = [(20, 70, 130), (34, 108, 182), (54, 150, 222), (92, 186, 240), (146, 214, 250), (200, 238, 255)]
RED = [(110, 22, 30), (170, 40, 48), (214, 66, 70), (236, 104, 100), (250, 150, 140), (255, 200, 190)]
GREY = [(66, 70, 86), (98, 104, 122), (132, 138, 156), (166, 172, 188), (198, 204, 216), (228, 232, 240)]
FRAME = [(150, 72, 10), (214, 120, 20), (246, 166, 40), (255, 206, 90)]

# ---------------------------------------------------------------- icônes 14x14 (dessinées à la main)
P = {"K": K, "W": (250, 250, 252), "w": (196, 200, 214), "y": (252, 210, 64), "Y": (255, 240, 150), "o": (226, 140, 30),
     "r": (214, 60, 60), "R": (246, 120, 110), "d": (130, 30, 40), "b": (60, 130, 220), "B": (140, 196, 250), "n": (30, 60, 130),
     "g": (80, 170, 60), "G": (150, 220, 100), "h": (40, 100, 40), "t": (150, 98, 54), "T": (196, 140, 84), "e": (96, 60, 34),
     "s": (240, 196, 160), "S": (210, 150, 116), "p": (170, 90, 200), "P": (220, 160, 240), "i": (150, 156, 170), "I": (210, 214, 226),
     "c": (80, 210, 200), "C": (180, 250, 240)}
ICONS = {
 "gift": ["....KK..KK....", "...KrRKKrRK...", "....KrKKrK....", "KKKKKKKKKKKKKK", "KyyyyYKKyyyyyK", "KooooyKKoooooK",
          "KKKKKKKKKKKKKK", ".KrrrrKKrrrrK.", ".KrRrrKKrrrrK.", ".KrrrrKKrrrrK.", ".KrrrrKKrrrrK.", ".KdddrKKrdddK.", ".KKKKKKKKKKKK."],
 "scroll": [".KKKKKKKKKK...", "KTTTTTTTTTTK..", "KtKWWWWWWWWK..", ".KWwWWWWWwWK..", ".KWWwwwwWWWK..", ".KWWWWWWWWWK..",
            ".KWwwwwwwWWK..", ".KWWWWWWWWWK..", ".KWwwwwWWWWKK.", ".KWWWWWWWWWKrK", "KTTTTTTTTTKrdK", "KtttttttttKKK.", ".KKKKKKKKKK..."],
 "bag": ["....KKKKK.....", "...KtK.KtK....", "...Kt...tK....", ".KKKKKKKKKK...", "KTTTTTTTTTTK..", "KTttttttttTK..",
         "KTtTTyyTTtTK..", "KTtTyYYyTtTK..", "KTtTTyyTTtTK..", "KTttttttttTK..", "KTTTTTTTTTTK..", ".KKKKKKKKKK..."],
 "book": [".KKKKKKKKKKK..", ".KbbbbbbbbbWK.", ".KbBBBBBBbbWK.", ".KbBKKKKBbbWK.", ".KbBKyyKBbbWK.", ".KbBKKKKBbbWK.",
          ".KbBBBBBBbbWK.", ".KbbbbbbbbbWK.", ".KnnnnnnnnnWK.", ".KnWWWWWWWWWK.", ".KKKKKKKKKKKK."],
 "house": ["......KK......", ".....KrrK.....", "....KrRrrK....", "...KrRrrrrK...", "..KrRrrrrrrK..", ".KKKKKKKKKKKK.",
           "..KWWWWWWWWK..", "..KWbBWWtTWK..", "..KWbbWWttWK..", "..KWWWWWttWK..", "..KWWWWWttWK..", "..KKKKKKKKKK.."],
 "arrow": ["......KK......", ".....KGGK.....", "....KGGGgK....", "...KGGGGggK...", "..KGGGGGgggK..", ".KKKKGGggKKKK.",
           "....KGGggK....", "....KGGggK....", "....KGGggK....", "....KGggggK...", "....KKKKKK...."],
 "gear": ["....KK..KK....", "...KiIKKIiK...", ".KKKiIIIIiKKK.", "KiIIIIiiIIIIiK", "KKIIiKKKKiIIKK", ".KIIK....KIIK.",
          ".KIIK....KiIK.", "KKIIiKKKKiiIKK", "KiIIIiiiiiiiiK", ".KKKiiiiiiKKK.", "...KiiKKiiK...", "....KK..KK...."],
 "coins": [".....KKKK.....", "....KyYYyK....", "...KyYyyYyK...", "...KyyyyyyK...", "KKKKKyyyyKKKK.", "KyYYyKKKKyYYyK",
           "KyyyyyyKyyyyyK", "KKKKKKKKKKKKKK", "KyYYyyyKyYYyyK", "KoooooooKooooK", ".KKKKKKK.KKKK."],
 "people": ["..KKK...KKK...", ".KeeeK.KtttK..", ".KsssK.KsssK..", ".KsKsK.KsKsK..", "..KsK...KsK...", "KKKKKKKKKKKK..",
            "KbBbbKKrRrrK..", "KbBbbKKrRrrK..", "KbbbbKKrrrrK..", "KKKKKKKKKKKK.."],
 "map": ["KKKKKKKKKKKKK.", "KWWWKWWWWKWWK.", "KWgWKWWrWKWWK.", "KWggKWrrrKWbK.", "KWWgKWWrWKbbK.", "KWWWKWWWWKbWK.",
         "KWgWKWWWWKWWK.", "KwwwKwwwwKwwK.", "KKKKKKKKKKKKK."],
 "egg": [".....KKK......", "....KWWWK.....", "...KWWWWWK....", "..KWcWWWWWK...", "..KWccWWWWK...", ".KWWWWWWcWWK..",
         ".KWWWWWcccWK..", ".KWWcWWWcWWK..", ".KwWcccWWWwK..", "..KwWcWWWwK...", "...KwwwwwK....", "....KKKKK....."],
 "wrench": [".........KKK..", "........KIIK..", ".........KIIK.", "....K...KIIiK.", "...KIK.KIIiK..", "...KIIKIIiK...",
            "....KIIIiK....", "...KIIIiK.....", "..KIIiK.......", ".KIIiK........", "KIIiK.........", "KiiK..........", ".KK..........."],
 "trophy": ["KKKKKKKKKKKK..", "KyYYYYyyyyoK..", "KyYYYYyyyyoK..", ".KyYYYyyyoK...", "KKyYYYyyyoKK..", "..KyYyyyoK....",
            "...KyyyoK.....", "....KyoK......", "...KyyyoK.....", "..KtttttttK...", "..KKKKKKKKK..."],
 "portal": ["...KKKKKKK....", "..KpppppppK...", ".KpPPPPPPPpK..", ".KpPCCCCCPpK..", "KpPCcccccCPpK.", "KpPCcWWWcCPpK.",
            "KpPCcWWWcCPpK.", "KpPCcccccCPpK.", ".KpPCCCCCPpK..", ".KpPPPPPPPpK..", "..KpppppppK...", "...KKKKKKK...."],
 "sword": [".........KKK..", "........KIWK..", ".......KIWK...", "......KIWK....", ".....KIWK.....", "..K.KIWK......",
           "..KKIWK.......", "...KyK........", "..KtKyK.......", ".KtK.KK.......", "KtK...........", "KK............"],
 "star": ["......KK......", ".....KYYK.....", ".....KYyK.....", "KKKKKKYyKKKKKK", "KYYYYYyyyyyyoK", ".KyyyyyyyyyoK.",
          "..KyyyyyyyoK..", "..KyyyKKyyoK..", ".KyyoK..KyyoK.", ".KyoK....KyoK.", ".KKK......KKK."],
 "head": ["...KKKKKKK....", "..KeeeeeeeK...", ".KeeeeeeeeeK..", ".KesssssssK...", ".KsKKsssKKsK..", ".KsWKsssWKsK..",
          ".KsssssSsssK..", ".KssSSSSSssK..", "..KsssssssK...", "...KKKKKKK...."],
}

def icon_img(name):
    return outline(sprite(ICONS[name], P), K) if False else sprite(ICONS[name], P)

# ---------------------------------------------------------------- mascotte originale (pas un Pokémon existant)
MASCOT = [
    "..........KK.........",
    ".........KGGK........",
    "....KK..KGhGK..KK....",
    "...KGGK.KGhK..KGGK...",
    "...KGhGKKhK..KGhGK...",
    "....KGhGKK..KGhGK....",
    ".....KKKcccccKKK.....",
    "....KcccCCCCCcccK....",
    "...KcCCCCCCCCCCccK...",
    "..KcCCKKCCCCKKCCccK..",
    "..KcCCKWKCCCKWKCccK..",
    "..KcCCKKCCCCKKCCccK..",
    "..KcRRCCCCKCCCCRRcK..",
    "..KccCCCCKCKCCCCccK..",
    "...KccCCCCCCCCCccK...",
    "...KKcccCCCCCcccKK...",
    "..KcK.KcccccccK.KcK..",
    "..KK..KccKKKccK..KK..",
    "......KKK...KKK......",
]

# ---------------------------------------------------------------- éléments
def panel(p, x0, y0, x1, y1, tab=None):
    """Panneau gris arrondi, cadre orange. tab = (x0, x1, haut) : onglet qui dépasse au-dessus à droite."""
    def shape(x, y):
        inside = x0 <= x <= x1 and y0 <= y <= y1
        if tab: inside = inside or (tab[0] <= x <= tab[1] and tab[2] <= y <= y0 + 4)
        return inside
    L = Pix(x1 - x0 + 12, y1 - min(y0, tab[2] if tab else y0) + 12, -x0 + 6, -min(y0, tab[2] if tab else y0) + 6)
    top = min(y0, tab[2] if tab else y0)
    for y in range(top - 3, y1 + 4):
        for x in range(x0 - 3, x1 + 4):
            d = min([abs(x - xx) + abs(y - yy) for xx in range(x0, x1 + 1, max(1, x1 - x0)) for yy in range(y0, y1 + 1, max(1, y1 - y0))])
            # distance au rectangle (union) -> bandes : noir, orange (2), clair, gris
            def dist(xx, yy):
                dd = 9
                for (a0, b0, a1, b1) in ([(x0, y0, x1, y1)] + ([(tab[0], tab[2], tab[1], y0 + 4)] if tab else [])):
                    dx = max(a0 - xx, 0, xx - a1); dy = max(b0 - yy, 0, yy - b1)
                    dd = min(dd, max(dx, dy) if (dx and dy) is False else (dx + dy if dx and dy else max(dx, dy)))
                return dd
            dd = dist(x, y)
            corner = 0
            if dd == 0:
                p.px(x, y, pick([GREY[3], GREY[4]], 0.6 - (y - top) / 600, x, y))
            elif dd == 1: p.px(x, y, FRAME[3])
            elif dd == 2: p.px(x, y, FRAME[2])
            elif dd == 3: p.px(x, y, K)
    # coins arrondis (on coupe les angles extérieurs)
    for (cx, cy, sx, sy) in ((x0 - 3, top - 3, 1, 1), (x1 + 3, top - 3, -1, 1), (x0 - 3, y1 + 3, 1, -1), (x1 + 3, y1 + 3, -1, -1)):
        for (a, b) in ((0, 0), (1, 0), (0, 1)): p.px(cx + sx * a, cy + sy * b, (0, 0, 0, 0)) if False else None

def rounded_panel(p, rects, fill, frame=True):
    """Union de rectangles, bordée : contour sombre, liseré orange épais, liseré clair, fond gris. Coins arrondis."""
    xs = [r[0] for r in rects] + [r[2] for r in rects]; ys = [r[1] for r in rects] + [r[3] for r in rects]
    X0, Y0, X1, Y1 = min(xs) - 5, min(ys) - 5, max(xs) + 5, max(ys) + 5
    def inside(x, y, grow=0):
        for (a0, b0, a1, b1) in rects:
            if a0 - grow <= x <= a1 + grow and b0 - grow <= y <= b1 + grow:
                # arrondi : on retire les coins du rectangle grossi
                cx = min(abs(x - (a0 - grow)), abs(x - (a1 + grow))); cy = min(abs(y - (b0 - grow)), abs(y - (b1 + grow)))
                if cx + cy < (2 if grow >= 2 else 1) and (x < a0 or x > a1 or y < b0 or y > b1 or grow == 0):
                    if not any(c0 - grow <= x <= c1 + grow and d0 - grow <= y <= d1 + grow and (c0, d0, c1, d1) != (a0, b0, a1, b1)
                               for (c0, d0, c1, d1) in rects):
                        continue
                return True
        return False
    for y in range(Y0, Y1 + 1):
        for x in range(X0, X1 + 1):
            if inside(x, y, 0):
                p.px(x, y, fill(x, y))
            elif inside(x, y, 1): p.px(x, y, (255, 250, 230))
            elif inside(x, y, 3): p.px(x, y, FRAME[2] if inside(x, y, 2) else FRAME[1])
            elif inside(x, y, 4): p.px(x, y, K)

def chip(p, x, y, w, h, pal):
    """Petit bloc arrondi en relief (fond d'icône ou étiquette)."""
    p.rect(x + 1, y, x + w - 2, y + h - 1, K); p.rect(x, y + 1, x + w - 1, y + h - 2, K)
    for yy in range(y + 1, y + h - 1):
        for xx in range(x + 1, x + w - 1):
            p.px(xx, yy, pick(pal[1:5], 0.82 - (yy - y) / (h * 1.6), xx, yy))
    p.hline(x + 2, x + w - 3, y + 1, pal[5]); p.vline(x + 1, y + 2, y + h - 4, pal[4])
    p.hline(x + 2, x + w - 3, y + h - 2, pal[1]); p.vline(x + w - 2, y + 2, y + h - 3, pal[2])
    p.hline(x + 1, x + w - 2, y + h, (0, 0, 0, 70))       # ombre portée

def label(p, cx, cy, text, pal):
    words = text.split(" ")
    lines = [text] if FONT.width(text) <= 72 or len(words) == 1 else [" ".join(words[:2]), " ".join(words[2:])]
    lh = 9
    y = cy - (len(lines) * lh - 1) // 2
    for i, ln in enumerate(lines):
        w = FONT.width(ln)
        x = cx - w // 2
        FONT.draw(p.img, x + p.ox + 1, y + i * lh + p.oy + 1, ln, pal[0], False)
        FONT.draw(p.img, x + p.ox, y + i * lh + p.oy, ln, (255, 255, 255), False)

def button(p, x, y, icon, text, pal, w=102, h=22):
    chip(p, x, y, 24, h, GREY)
    im = sprite(ICONS[icon], P)
    p.paste(im, x + 12 - im.width // 2, y + h // 2 - im.height // 2)
    chip(p, x + 23, y, w - 23, h, pal)
    label(p, x + 23 + (w - 23) // 2, y + h // 2, text, pal)

# ---------------------------------------------------------------- menu
TITLE_GRAD = [(255, 252, 200), (255, 238, 120), (252, 214, 60), (244, 188, 40), (230, 160, 30), (214, 136, 24), (196, 116, 20)]

def build():
    W, H = 360, 212
    p = Pix(W, H)
    # panneau principal + onglet des raccourcis en haut à droite
    gx0, gy0, gx1, gy1 = 12, 50, 344, 200
    tab = (238, 24, 344, 50)
    def fill(x, y): return pick([GREY[3], GREY[4]], 0.7 - (y - 24) / 500 + (0.06 if (x + y) % 23 == 0 else 0), x, y)
    rounded_panel(p, [(gx0, gy0, gx1, gy1), tab], fill)
    # raccourcis de l'onglet
    for i, ic in enumerate(("head", "star", "gear")):
        chip(p, 244 + i * 33, 28, 30, 20, GREY)
        im = sprite(ICONS[ic], P); p.paste(im, 244 + i * 33 + 15 - im.width // 2, 38 - im.height // 2)
    # titre
    fancy_text_c(p, 150, 26, "MON ÎLE", scale=2, bold=True, grad=TITLE_GRAD, out=(90, 40, 10), extrude=2,
                 ext_cols=((170, 90, 20), (120, 56, 14)))
    # mascotte assise sur le coin du cadre
    m = sprite(MASCOT, P).resize((42, 38), Image.NEAREST)
    p.paste(m, 16, 18)
    # boutons
    cols = [
        (ORANGE, [("gift", "RÉCOMPENSES"), ("scroll", "QUÊTES"), ("bag", "BOUTIQUE"), ("book", "SUCCÈS")]),
        (GREEN, [("house", "ALLER SUR MON ÎLE"), ("arrow", "AMÉLIORER"), ("gear", "MACHINES"), ("coins", "BANQUE")]),
        (BLUE, [("people", "MEMBRES"), ("map", "VISITER"), ("egg", "PENSION"), ("wrench", "RÉGLAGES")]),
    ]
    x0s = (22, 128, 234)
    for c, (pal, items) in enumerate(cols):
        for r, (ic, txt) in enumerate(items):
            button(p, x0s[c], 58 + r * 26, ic, txt, pal)
    for c, (ic, txt) in enumerate((("trophy", "CLASSEMENT"), ("portal", "WARPS"), ("sword", "DÉFIS"))):
        button(p, x0s[c], 170, ic, txt, RED)
    for x in range(24, 334, 3): p.px(x, 164, GREY[1]); p.px(x, 165, GREY[5])
    return p.img

if __name__ == "__main__":
    img = build()
    bg = Image.new("RGBA", img.size, (232, 232, 236, 255)); bg.alpha_composite(img)
    bg.resize((img.width * 3, img.height * 3), Image.NEAREST).save("/home/claude/rp/menu_is_cobble.png")
    print("ok")
