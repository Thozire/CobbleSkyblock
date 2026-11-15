"""Génère les fonds de menus et les icônes du resource pack (style Cobblemon moderne, double résolution).

Les fonds sont des glyphes de police affichés dans le titre du menu (voir IslandMenu.java).
Repère : 1 unité = 1 pixel d'interface ; les textures sont dessinées en x2.
Le cadre vanilla du coffre (176x222) commence en (OX, OY) dans le glyphe.
"""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

S = 2                      # résolution
W, H = 256, 272            # taille du glyphe en unités GUI
OX, OY = 40, 24            # position du coin du coffre vanilla dans le glyphe
POPPINS = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
OUT = sys.argv[1] if len(sys.argv) > 1 else "pack"

CYAN = (90, 215, 255); PINK = (214, 92, 240); GOLD = (255, 200, 87); GREEN = (94, 224, 160)
RED = (255, 107, 122); WHITE = (243, 232, 255); GRAY = (138, 131, 153)

def u(v): return int(round(v * S))

def grad(size, c1, c2, vertical=True):
    w, h = size
    g = Image.new("RGBA", (w, h))
    px = g.load()
    for i in range(h if vertical else w):
        t = i / max(1, (h if vertical else w) - 1)
        c = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(len(c1)))
        if len(c) == 3: c = c + (255,)
        if vertical:
            for x in range(w): px[x, i] = c
        else:
            for y in range(h): px[i, y] = c
    return g

def diag_grad(size, c1, c2):
    w, h = size
    g = Image.new("RGBA", (w, h)); px = g.load()
    for y in range(h):
        for x in range(w):
            t = (x / w + y / h) / 2
            px[x, y] = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3)) + (255,)
    return g

def rmask(size, box, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=r, fill=255)
    return m

def paste_masked(base, layer, mask):
    tmp = Image.new("RGBA", base.size, (0, 0, 0, 0))
    tmp.paste(layer, (0, 0), mask)
    base.alpha_composite(tmp)

def glow(base, mask, color, radius, strength=1.0):
    g = Image.new("RGBA", base.size, color + (0,))
    a = mask.filter(ImageFilter.GaussianBlur(radius))
    a = a.point(lambda v: int(min(255, v * strength)))
    g.putalpha(a)
    base.alpha_composite(g)

# ---------- éléments décoratifs ----------

def floating_island(d_img, cx, cy, w, tree=None, seed=1):
    """Petite île flottante (coordonnées GUI)."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(d_img)
    top = cy
    # dessous rocheux (triangle irrégulier)
    pts = [(cx - w / 2, top)]
    steps = 7
    for i in range(1, steps):
        x = cx - w / 2 + w * i / steps
        depth = (1 - abs(i / steps - 0.5) * 2) * w * 0.55 + rnd.uniform(-2, 2)
        pts.append((x, top + 3 + depth))
    pts.append((cx + w / 2, top))
    d.polygon([(u(x), u(y)) for x, y in pts], fill=(92, 70, 88, 255))
    d.polygon([(u(x), u(y)) for x, y in pts[:len(pts) // 2 + 1]] + [(u(cx), u(top))], fill=(112, 86, 104, 255))
    # terre + herbe
    d.rounded_rectangle([u(cx - w / 2), u(top - 1), u(cx + w / 2), u(top + 3)], radius=u(1.5), fill=(126, 84, 60, 255))
    d.rounded_rectangle([u(cx - w / 2 - 1), u(top - 3), u(cx + w / 2 + 1), u(top + 0.5)], radius=u(1.5), fill=(108, 201, 98, 255))
    d.line([u(cx - w / 2), u(top - 3), u(cx + w / 2), u(top - 3)], fill=(160, 236, 140, 255), width=S)
    if tree:
        tx, kind = tree
        trunk = (120, 82, 58, 255)
        d.rectangle([u(tx - 0.8), u(top - 10), u(tx + 0.8), u(top - 3)], fill=trunk)
        leaf = (70, 170, 90, 255) if kind == "oak" else (88, 158, 120, 255)
        d.ellipse([u(tx - 6), u(top - 17), u(tx + 6), u(top - 7)], fill=leaf)
        d.ellipse([u(tx - 4), u(top - 16), u(tx + 3), u(top - 10)], fill=tuple(min(255, c + 30) for c in leaf[:3]) + (255,))
        if kind == "apricorn":
            for ax, ay, col in ((tx - 3.5, top - 8.5, (232, 72, 80)), (tx + 3, top - 9.5, (90, 150, 240)), (tx + 0.5, top - 7.5, (250, 210, 70))):
                d.ellipse([u(ax - 1.4), u(ay - 1.4), u(ax + 1.4), u(ay + 1.4)], fill=col + (255,))
                d.point((u(ax - 0.6), u(ay - 0.6)), fill=(255, 255, 255, 220))

def waterfall(img, x, y1, y2):
    d = ImageDraw.Draw(img)
    for i in range(int((y2 - y1) * S)):
        a = int(220 * (1 - i / ((y2 - y1) * S)))
        d.line([u(x - 1), u(y1) + i, u(x + 1), u(y1) + i], fill=(150, 220, 255, a))

def sparkle(d, x, y, r, col=(255, 255, 255)):
    d.line([u(x - r), u(y), u(x + r), u(y)], fill=col + (230,), width=1)
    d.line([u(x), u(y - r), u(x), u(y + r)], fill=col + (230,), width=1)
    d.ellipse([u(x) - 1, u(y) - 1, u(x) + 1, u(y) + 1], fill=col + (255,))

def apricorn_emblem(img, cx, cy, r):
    """Emblème : un apricorn stylisé (fruit Cobblemon), pas une Poké Ball."""
    d = ImageDraw.Draw(img)
    d.ellipse([u(cx - r), u(cy - r + 1), u(cx + r), u(cy + r + 1)], fill=(232, 72, 96, 255))
    d.ellipse([u(cx - r * 0.55), u(cy - r * 0.5), u(cx + r * 0.1), u(cy + r * 0.1)], fill=(255, 140, 150, 200))
    d.rectangle([u(cx - 0.4), u(cy - r - 1.5), u(cx + 0.4), u(cy - r + 1)], fill=(110, 76, 50, 255))
    d.polygon([(u(cx + 0.4), u(cy - r - 0.5)), (u(cx + r * 0.9), u(cy - r - 2.5)), (u(cx + r * 0.5), u(cy - r + 0.8))], fill=(94, 200, 120, 255))

# ---------- fond commun ----------

def base_background():
    img = Image.new("RGBA", (u(W), u(H)), (0, 0, 0, 0))
    px0, py0, px1, py1 = OX - 10, OY - 10, OX + 176 + 10, OY + 222 + 16
    box = [u(px0), u(py0), u(px1), u(py1)]
    panel_mask = rmask(img.size, box, u(9))
    # halo néon autour du panneau
    glow(img, panel_mask, PINK, u(6), 0.55)
    glow(img, panel_mask, CYAN, u(3), 0.35)
    # verre sombre
    body = diag_grad(img.size, (16, 18, 40), (42, 20, 62))
    paste_masked(img, body, panel_mask)
    # reflets diagonaux
    rays = Image.new("RGBA", img.size, (0, 0, 0, 0)); rd = ImageDraw.Draw(rays)
    for k, a in ((0, 26), (1, 16), (2, 10)):
        x = u(px0 + 30 + k * 26)
        rd.polygon([(x, u(py0)), (x + u(14), u(py0)), (x - u(90), u(py1)), (x - u(104), u(py1))], fill=(255, 255, 255, a))
    m2 = ImageChops.multiply(panel_mask, Image.new("L", img.size, 255))
    paste_masked(img, rays, m2)
    # étoiles de fond
    rnd = random.Random(7); d = ImageDraw.Draw(img)
    for _ in range(70):
        x = rnd.uniform(px0 + 4, px1 - 4); y = rnd.uniform(py0 + 4, py1 - 4)
        a = rnd.randint(40, 120)
        d.point((u(x), u(y)), fill=(220, 210, 255, a))
    # bordure dégradée cyan -> rose
    border = diag_grad(img.size, CYAN, PINK)
    ring = ImageChops.subtract(panel_mask, rmask(img.size, [box[0] + 3, box[1] + 3, box[2] - 3, box[3] - 3], u(8)))
    paste_masked(img, border, ring)
    # en-tête
    hb = [u(px0 + 4), u(py0 + 4), u(px1 - 4), u(OY + 15)]
    hm = rmask(img.size, hb, u(6))
    paste_masked(img, grad(img.size, (70, 36, 110), (34, 22, 64)), hm)
    shine = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shine).rounded_rectangle([hb[0] + 2, hb[1] + 2, hb[2] - 2, hb[1] + u(5)], radius=u(3), fill=(255, 255, 255, 34))
    img.alpha_composite(shine)
    underline = grad((hb[2] - hb[0], S * 1), CYAN, PINK, vertical=False)
    img.alpha_composite(underline, (hb[0], hb[3] - S))
    apricorn_emblem(img, OX + 6, OY + 5, 4.2)
    for sx, sy, r in ((OX + 150, OY + 2, 2), (OX + 160, OY + 7, 1.5), (OX + 168, OY + 1, 1)):
        sparkle(d, sx, sy, r)
    return img, (px0, py0, px1, py1)

def decorations(img):
    """Éléments qui débordent du cadre (îles flottantes, nuage, étoiles)."""
    floating_island(img, 18, 26, 26, tree=(15, "apricorn"), seed=3)
    floating_island(img, 240, 46, 16, tree=(242, "oak"), seed=5)
    d = ImageDraw.Draw(img)
    for x, y, r in ((228, 10, 2.5), (250, 22, 1.5), (8, 52, 1.5), (30, 6, 1.2)):
        sparkle(d, x, y, r, (255, 240, 200))
    # petit nuage
    for cx, cy, r in ((214, 18, 4), (219, 15, 5), (225, 18, 4)):
        d.ellipse([u(cx - r), u(cy - r), u(cx + r), u(cy + r)], fill=(240, 240, 255, 210))

def scene(img):
    """Illustration du bas (remplace l'inventaire) : îles dans le ciel + logo."""
    x0, y0, x1, y1 = OX - 2, OY + 140, OX + 178, OY + 230
    box = [u(x0), u(y0), u(x1), u(y1)]
    m = rmask(img.size, box, u(7))
    sky = grad(img.size, (36, 40, 96), (112, 64, 150))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layer.alpha_composite(sky)
    ld = ImageDraw.Draw(layer)
    # soleil couchant (halo flou)
    sun = Image.new("L", img.size, 0)
    ImageDraw.Draw(sun).ellipse([u(OX + 132 - 11), u(y1 - 31), u(OX + 132 + 11), u(y1 - 9)], fill=255)
    glow(layer, sun, (255, 150, 120), u(9), 1.0)
    layer.alpha_composite(Image.composite(Image.new("RGBA", img.size, (255, 196, 140, 255)), Image.new("RGBA", img.size, (0, 0, 0, 0)), sun))
    # nuages bas
    for cx, cy, r in ((OX + 20, y1 - 6, 10), (OX + 40, y1 - 3, 12), (OX + 120, y1 - 4, 11), (OX + 150, y1 - 2, 13), (OX + 175, y1 - 6, 9)):
        ld.ellipse([u(cx - r * 1.6), u(cy - r * 0.7), u(cx + r * 1.6), u(cy + r * 0.7)], fill=(210, 190, 240, 230))
    rnd = random.Random(11)
    for _ in range(40):
        ld.point((u(rnd.uniform(x0, x1)), u(rnd.uniform(y0, y0 + 45))), fill=(255, 255, 255, rnd.randint(80, 200)))
    floating_island(layer, OX + 34, y1 - 34, 30, tree=(OX + 30, "apricorn"), seed=21)
    waterfall(layer, OX + 46, y1 - 33, y1 - 10)
    floating_island(layer, OX + 150, y1 - 46, 22, tree=(OX + 154, "oak"), seed=22)
    floating_island(layer, OX + 100, y1 - 24, 12, seed=23)
    # logo
    font = ImageFont.truetype(POPPINS, u(15))
    text = "CobbleSkyblock"
    tw = ld.textlength(text, font=font)
    tx, ty = (u(OX + 88) - tw / 2), u(y0 + 14)
    tmask = Image.new("L", img.size, 0)
    ImageDraw.Draw(tmask).text((tx, ty), text, font=font, fill=255)
    glow(layer, tmask, (0, 0, 0), 4, 1.3)
    fill = grad(img.size, (255, 255, 255), (255, 214, 250))
    shadow = Image.new("L", img.size, 0); ImageDraw.Draw(shadow).text((tx + S, ty + S), text, font=font, fill=255)
    paste_masked(layer, Image.new("RGBA", img.size, (120, 40, 140, 255)), shadow)
    paste_masked(layer, fill, tmask)
    small = ImageFont.truetype(POPPINS, u(5.5))
    sub = "ÎLES  •  POKÉMON  •  FUSION"
    sw = ld.textlength(sub, font=small)
    ld.text((u(OX + 88) - sw / 2, u(y0 + 33)), sub, font=small, fill=(200, 236, 255, 230))
    paste_masked(img, layer, m)
    # cadre fin
    ImageDraw.Draw(img).rounded_rectangle(box, radius=u(7), outline=(255, 255, 255, 60), width=S)
    # barre de séparation : gris #404040 exact là où le jeu écrit « Inventaire » (le texte devient invisible)
    bar = [u(OX + 4), u(OY + 127), u(OX + 172), u(OY + 137)]
    bm = rmask(img.size, bar, u(5))
    glow(img, bm, PINK, u(2), 0.5)
    paste_masked(img, Image.new("RGBA", img.size, (64, 64, 64, 255)), bm)
    caps = grad((u(12), bar[3] - bar[1]), CYAN, PINK, vertical=False)
    cm = Image.new("L", img.size, 0)
    ImageDraw.Draw(cm).rounded_rectangle([u(OX + 160), bar[1], bar[2], bar[3]], radius=u(5), fill=255)
    paste_masked(img, diag_grad(img.size, CYAN, PINK), cm)
    for i, x in enumerate(range(OX + 92, OX + 156, 8)):
        ImageDraw.Draw(img).ellipse([u(x), u(OY + 131), u(x + 2), u(OY + 133)], fill=(150, 120, 200, 255 - i * 25))

def card(img, slot, color, hero=False):
    r, c = divmod(slot, 9)
    x, y = OX + 8 + 18 * c, OY + 18 + 18 * r
    box = [u(x - 0.5), u(y - 0.5), u(x + 16.5), u(y + 16.5)]
    m = rmask(img.size, box, u(3.5))
    if hero:
        glow(img, m, color, u(3), 0.9)
    fill = grad(img.size, (58, 50, 92, 215), (30, 26, 52, 225))
    paste_masked(img, fill, m)
    inner = rmask(img.size, [box[0] + S, box[1] + S, box[2] - S, box[3] - S], u(3))
    ring = ImageChops.subtract(m, inner)
    paste_masked(img, Image.new("RGBA", img.size, color + (235,)), ring)
    ImageDraw.Draw(img).line([box[0] + u(3), box[1] + S + 1, box[2] - u(3), box[1] + S + 1], fill=(255, 255, 255, 50), width=1)

# ---------- pages ----------
P = {"gold": GOLD, "green": GREEN, "aqua": CYAN, "pink": PINK, "red": RED, "white": (200, 190, 230), "gray": (110, 104, 130)}
LIST_SLOTS = [9 + r * 9 + c for r in range(4) for c in range(1, 8)]
PAGES = {
    "main": ("\ue010", {4: "gold!", 20: "green!", 22: "aqua", 24: "gold", 29: "white", 31: "pink", 33: "aqua", 39: "white", 41: "red", 45: "white", 49: "red"}),
    "start": ("\ue011", {4: "gold", 22: "green!", 30: "green", 32: "red", 38: "aqua", 40: "gold", 49: "red"}),
    "team": ("\ue012", {**{s: "aqua" for s in list(range(10, 17)) + list(range(19, 26))}, 40: "green!", 45: "white", 49: "red"}),
    "list": ("\ue013", {**{s: "gold" for s in LIST_SLOTS}, 45: "white", 48: "white", 49: "red", 50: "white"}),
    "upgrades": ("\ue014", {10: "green!", 11: "green", 12: "green", 13: "green", 14: "green", 15: "green",
                             28: "aqua!", 29: "aqua", 30: "aqua", 31: "aqua", 32: "aqua", 40: "gold", 45: "white", 49: "red"}),
    "confirm": ("\ue015", {13: "gold!", 29: "red!", 33: "green!"}),
}

def build_page(name):
    img, _ = base_background()
    decorations(img)
    scene(img)
    for slot, col in PAGES[name][1].items():
        card(img, slot, P[col.rstrip("!")], col.endswith("!"))
    return img

# ---------- icônes (32x32) ----------
ICONS = {}
def icon(cmd):
    def deco(f):
        ICONS[cmd] = f
        return f
    return deco

def canvas():
    return Image.new("RGBA", (128, 128), (0, 0, 0, 0))

def finish(img):
    sh = img.split()[3].filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * 0.5))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow = Image.new("RGBA", img.size, (10, 6, 24, 0)); shadow.putalpha(sh)
    out.alpha_composite(shadow, (0, 4)); out.alpha_composite(img)
    return out.resize((32, 32), Image.LANCZOS)

def outline_circle(d, box, fill, out=(20, 14, 34, 255), w=6):
    d.ellipse(box, fill=out)
    d.ellipse([box[0] + w, box[1] + w, box[2] - w, box[3] - w], fill=fill)

@icon(7101)  # aller sur mon île
def i_home():
    im = canvas(); d = ImageDraw.Draw(im)
    floating_isl(d, 64, 88, 112)
    d.polygon([(28, 52), (64, 16), (100, 52)], fill=(232, 72, 96, 255))
    d.polygon([(28, 52), (64, 16), (64, 52)], fill=(255, 120, 140, 255))
    d.rectangle([36, 50, 92, 80], fill=(250, 244, 255, 255))
    d.rounded_rectangle([56, 58, 72, 80], radius=3, fill=(126, 84, 60, 255))
    d.rectangle([40, 56, 50, 66], fill=(90, 215, 255, 255)); d.rectangle([78, 56, 88, 66], fill=(90, 215, 255, 255))
    return finish(im)

def floating_isl(d, cx, top, w):
    d.polygon([(cx - w / 2, top), (cx + w / 2, top), (cx + w * 0.15, top + w * 0.42), (cx - w * 0.1, top + w * 0.5)], fill=(112, 86, 104, 255))
    d.rounded_rectangle([cx - w / 2, top - 6, cx + w / 2, top + 6], radius=6, fill=(126, 84, 60, 255))
    d.rounded_rectangle([cx - w / 2 - 2, top - 10, cx + w / 2 + 2, top], radius=5, fill=(108, 201, 98, 255))

@icon(7102)  # équipe
def i_team():
    im = canvas(); d = ImageDraw.Draw(im)
    for cx, col in ((42, (90, 215, 255)), (86, (214, 92, 240)), (64, (255, 200, 87))):
        d.ellipse([cx - 14, 24, cx + 14, 52], fill=col + (255,))
        d.rounded_rectangle([cx - 22, 56, cx + 22, 104], radius=18, fill=col + (255,))
    return finish(im)

@icon(7103)  # visiter
def i_visit():
    im = canvas(); d = ImageDraw.Draw(im)
    outline_circle(d, [14, 14, 114, 114], (36, 40, 96, 255), (255, 200, 87, 255), 8)
    d.polygon([(64, 26), (76, 64), (64, 102), (52, 64)], fill=(250, 244, 255, 255))
    d.polygon([(64, 26), (76, 64), (52, 64)], fill=(255, 107, 122, 255))
    d.ellipse([58, 58, 70, 70], fill=(20, 14, 34, 255))
    return finish(im)

@icon(7104)  # visites ouvertes
def i_open():
    im = canvas(); d = ImageDraw.Draw(im)
    d.ellipse([10, 34, 118, 94], fill=(94, 224, 160, 255))
    d.ellipse([22, 42, 106, 86], fill=(250, 244, 255, 255))
    d.ellipse([46, 46, 82, 82], fill=(30, 110, 80, 255))
    d.ellipse([54, 52, 66, 64], fill=(255, 255, 255, 255))
    return finish(im)

@icon(7105)  # visites fermées
def i_closed():
    im = canvas(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([38, 18, 90, 74], radius=26, outline=(200, 190, 230, 255), width=12)
    d.rounded_rectangle([24, 56, 104, 112], radius=14, fill=(255, 107, 122, 255))
    d.ellipse([56, 70, 72, 86], fill=(60, 20, 34, 255)); d.rectangle([61, 80, 67, 98], fill=(60, 20, 34, 255))
    return finish(im)

@icon(7106)  # améliorations
def i_up():
    im = canvas(); d = ImageDraw.Draw(im)
    d.polygon([(64, 10), (108, 58), (82, 58), (82, 112), (46, 112), (46, 58), (20, 58)], fill=(214, 92, 240, 255))
    d.polygon([(64, 10), (108, 58), (82, 58), (82, 70), (46, 70), (46, 58), (20, 58)], fill=(240, 150, 255, 255))
    for x, y in ((20, 92), (104, 88)):
        d.polygon([(x, y - 12), (x + 4, y - 4), (x + 12, y), (x + 4, y + 4), (x, y + 12), (x - 4, y + 4), (x - 12, y), (x - 4, y - 4)], fill=(255, 200, 87, 255))
    return finish(im)

@icon(7107)  # spawn
def i_spawn():
    im = canvas(); d = ImageDraw.Draw(im)
    d.ellipse([10, 82, 118, 114], fill=(90, 215, 255, 120))
    d.ellipse([28, 88, 100, 108], fill=(90, 215, 255, 255))
    d.polygon([(44, 96), (52, 24), (76, 24), (84, 96)], fill=(250, 244, 255, 255))
    d.polygon([(40, 28), (64, 8), (88, 28)], fill=(232, 72, 96, 255))
    d.rectangle([58, 70, 70, 96], fill=(90, 70, 130, 255))
    d.ellipse([56, 36, 72, 52], fill=(255, 200, 87, 255))
    return finish(im)

@icon(7108)  # point d'arrivée
def i_flag():
    im = canvas(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, 12, 40, 116], radius=4, fill=(200, 190, 230, 255))
    d.polygon([(40, 16), (108, 32), (40, 64)], fill=(94, 224, 160, 255))
    d.polygon([(40, 16), (108, 32), (40, 34)], fill=(150, 245, 200, 255))
    d.ellipse([18, 104, 52, 120], fill=(110, 104, 130, 255))
    return finish(im)

@icon(7109)  # supprimer
def i_trash():
    im = canvas(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([24, 22, 104, 36], radius=6, fill=(255, 140, 150, 255))
    d.rounded_rectangle([50, 10, 78, 26], radius=6, fill=(255, 140, 150, 255))
    d.polygon([(30, 40), (98, 40), (90, 116), (38, 116)], fill=(255, 107, 122, 255))
    for x in (48, 64, 80):
        d.rounded_rectangle([x - 4, 52, x + 4, 104], radius=4, fill=(150, 40, 60, 255))
    return finish(im)

@icon(7110)  # quitter
def i_leave():
    im = canvas(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([18, 12, 74, 116], radius=8, fill=(126, 84, 60, 255))
    d.rounded_rectangle([26, 20, 66, 108], radius=6, fill=(160, 110, 76, 255))
    d.ellipse([54, 60, 62, 68], fill=(255, 200, 87, 255))
    d.polygon([(70, 52), (96, 52), (96, 38), (122, 64), (96, 90), (96, 76), (70, 76)], fill=(255, 107, 122, 255))
    return finish(im)

@icon(7111)  # aide
def i_help():
    im = canvas(); d = ImageDraw.Draw(im)
    outline_circle(d, [12, 12, 116, 116], (90, 215, 255, 255), (20, 14, 34, 255), 6)
    f = ImageFont.truetype(POPPINS, 84)
    d.text((64, 66), "?", font=f, fill=(20, 14, 34, 255), anchor="mm")
    return finish(im)

def cross(d, col, w=22):
    d.line([(30, 30), (98, 98)], fill=col, width=w); d.line([(98, 30), (30, 98)], fill=col, width=w)

@icon(7112)  # fermer
def i_close():
    im = canvas(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 118, 118], radius=28, fill=(255, 107, 122, 255))
    cross(d, (255, 255, 255, 255), 16)
    return finish(im)

def arrow(d, left, col):
    pts = [(98, 52), (54, 52), (54, 30), (14, 64), (54, 98), (54, 76), (98, 76)]
    if not left: pts = [(128 - x, y) for x, y in pts]
    d.polygon(pts, fill=col)

@icon(7113)  # retour / précédent
def i_back():
    im = canvas(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 14, 122, 114], radius=28, fill=(70, 60, 110, 255))
    arrow(d, True, (243, 232, 255, 255))
    return finish(im)

@icon(7114)  # suivant
def i_next():
    im = canvas(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 14, 122, 114], radius=28, fill=(70, 60, 110, 255))
    arrow(d, False, (243, 232, 255, 255))
    return finish(im)

@icon(7116)  # confirmer
def i_yes():
    im = canvas(); d = ImageDraw.Draw(im)
    d.ellipse([8, 8, 120, 120], fill=(94, 224, 160, 255))
    d.line([(34, 66), (56, 88), (96, 42)], fill=(255, 255, 255, 255), width=18, joint="curve")
    return finish(im)

@icon(7117)  # annuler
def i_no():
    im = canvas(); d = ImageDraw.Draw(im)
    d.ellipse([8, 8, 120, 120], fill=(255, 107, 122, 255))
    d.line([(42, 42), (86, 86)], fill=(255, 255, 255, 255), width=18); d.line([(86, 42), (42, 86)], fill=(255, 255, 255, 255), width=18)
    return finish(im)

@icon(7118)  # créer une île
def i_create():
    im = canvas(); d = ImageDraw.Draw(im)
    floating_isl(d, 56, 82, 88)
    d.ellipse([70, 10, 122, 62], fill=(94, 224, 160, 255))
    d.rounded_rectangle([92, 20, 100, 52], radius=3, fill=(255, 255, 255, 255))
    d.rounded_rectangle([80, 32, 112, 40], radius=3, fill=(255, 255, 255, 255))
    return finish(im)

@icon(7119)  # inviter
def i_invite():
    im = canvas(); d = ImageDraw.Draw(im)
    d.ellipse([28, 18, 64, 54], fill=(90, 215, 255, 255))
    d.rounded_rectangle([16, 60, 76, 112], radius=22, fill=(90, 215, 255, 255))
    d.ellipse([70, 42, 122, 94], fill=(94, 224, 160, 255))
    d.rounded_rectangle([92, 52, 100, 84], radius=3, fill=(255, 255, 255, 255))
    d.rounded_rectangle([80, 64, 112, 72], radius=3, fill=(255, 255, 255, 255))
    return finish(im)

def gem(d, fill, light):
    d.polygon([(64, 10), (108, 46), (64, 118), (20, 46)], fill=fill)
    d.polygon([(64, 10), (108, 46), (64, 46), (20, 46)], fill=light)

@icon(7120)  # niveau débloqué
def i_lvl_on():
    im = canvas(); d = ImageDraw.Draw(im)
    gem(d, (94, 224, 160, 255), (170, 250, 210, 255))
    return finish(im)

@icon(7121)  # niveau verrouillé
def i_lvl_off():
    im = canvas(); d = ImageDraw.Draw(im)
    gem(d, (70, 64, 90, 255), (100, 94, 120, 255))
    return finish(im)

@icon(7122)  # place libre
def i_free():
    im = canvas(); d = ImageDraw.Draw(im)
    for a in range(0, 360, 30):
        x = 64 + 46 * math.cos(math.radians(a)); y = 64 + 46 * math.sin(math.radians(a))
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(160, 150, 190, 255))
    d.rounded_rectangle([58, 38, 70, 90], radius=4, fill=(200, 190, 230, 255))
    d.rounded_rectangle([38, 58, 90, 70], radius=4, fill=(200, 190, 230, 255))
    return finish(im)

@icon(7123)  # place verrouillée
def i_locked_slot():
    im = canvas(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([44, 30, 84, 70], radius=18, outline=(110, 104, 130, 255), width=10)
    d.rounded_rectangle([32, 58, 96, 110], radius=12, fill=(90, 84, 110, 255))
    return finish(im)

@icon(7124)  # info / bientôt
def i_soon():
    im = canvas(); d = ImageDraw.Draw(im)
    outline_circle(d, [10, 10, 118, 118], (255, 200, 87, 255), (20, 14, 34, 255), 6)
    d.line([(64, 64), (64, 32)], fill=(20, 14, 34, 255), width=10)
    d.line([(64, 64), (88, 76)], fill=(20, 14, 34, 255), width=10)
    return finish(im)

@icon(7125)  # aucune invitation / vide
def i_none():
    im = canvas(); d = ImageDraw.Draw(im)
    d.ellipse([16, 16, 112, 112], outline=(110, 104, 130, 255), width=10)
    d.line([(36, 92), (92, 36)], fill=(110, 104, 130, 255), width=10)
    return finish(im)

@icon(7126)  # niveau taille (titre)
def i_size():
    im = canvas(); d = ImageDraw.Draw(im)
    floating_isl(d, 64, 70, 100)
    for (x1, y1, x2, y2) in (((10, 30), (40, 30), (10, 30), (10, 50))[0:0]):
        pass
    d.polygon([(8, 20), (36, 20), (8, 48)], fill=(255, 255, 255, 255))
    d.polygon([(120, 20), (92, 20), (120, 48)], fill=(255, 255, 255, 255))
    return finish(im)

if __name__ == "__main__":
    tex = os.path.join(OUT, "assets/cobbleislands/textures/gui")
    os.makedirs(tex, exist_ok=True)
    providers = [{"type": "space", "advances": {"\ue001": -(8 + OX), "\ue002": -(W + 1 - OX - 14)}}]
    for name, (ch, _) in PAGES.items():
        img = build_page(name)
        img.save(os.path.join(tex, name + ".png"))
        providers.append({"type": "bitmap", "file": f"cobbleislands:gui/{name}.png", "height": H, "ascent": 13 + OY, "chars": [ch]})
    fdir = os.path.join(OUT, "assets/cobbleislands/font"); os.makedirs(fdir, exist_ok=True)
    json.dump({"providers": providers}, open(os.path.join(fdir, "gui.json"), "w"), ensure_ascii=False, indent=2)
    idir = os.path.join(OUT, "assets/cobbleislands/textures/item/ui"); os.makedirs(idir, exist_ok=True)
    mdir = os.path.join(OUT, "assets/cobbleislands/models/item/ui"); os.makedirs(mdir, exist_ok=True)
    for cmd, f in sorted(ICONS.items()):
        f().save(os.path.join(idir, f"{cmd}.png"))
        json.dump({"parent": "minecraft:item/generated", "textures": {"layer0": f"cobbleislands:item/ui/{cmd}"}},
                  open(os.path.join(mdir, f"{cmd}.json"), "w"))
    print("pages", list(PAGES), "icônes", sorted(ICONS))
