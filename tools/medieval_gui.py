"""Style médiéval des menus « Royaumes » : fonds de pages (glyphes de police) et icônes.

Repère : 1 unité = 1 pixel d'interface ; textures en x2. Le coffre vanilla (176x222)
commence en (OX, OY) dans le glyphe. Les boutons sont disposés en grille avec leur nom
écrit sous chaque case.
"""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

S = 2
W, H = 256, 272
OX, OY = 40, 24
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"

def u(v): return int(round(v * S))

def font(size, black=True):
    return ImageFont.truetype(SERIF if black else SERIF_B, u(size), index=0)

def grad(size, c1, c2, vertical=True):
    w, h = size
    g = Image.new("RGBA", (w, h)); px = g.load()
    n = h if vertical else w
    for i in range(n):
        t = i / max(1, n - 1)
        c = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3)) + (255,)
        if vertical:
            for x in range(w): px[x, i] = c
        else:
            for y in range(h): px[i, y] = c
    return g

def rmask(size, box, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=r, fill=255)
    return m

def paste_masked(base, layer, mask):
    tmp = Image.new("RGBA", base.size, (0, 0, 0, 0))
    tmp.paste(layer, (0, 0), mask)
    base.alpha_composite(tmp)

def glow(base, mask, color, radius, strength=1.0, offset=(0, 0)):
    a = mask.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(min(255, v * strength)))
    g = Image.new("RGBA", base.size, color + (0,)); g.putalpha(a)
    base.alpha_composite(g, offset)

def noise(size, base, amp, seed):
    rnd = random.Random(seed)
    img = Image.new("RGBA", size, base + (255,)); px = img.load()
    for y in range(size[1]):
        for x in range(size[0]):
            n = rnd.randint(-amp, amp)
            px[x, y] = tuple(max(0, min(255, base[k] + n)) for k in range(3)) + (255,)
    return img

# ---------- matériaux ----------

def wood(size, seed=1):
    """Planches de bois horizontales avec veinage."""
    w, h = size
    img = Image.new("RGBA", size, (92, 58, 34, 255)); d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    plank = u(9)
    for i, y in enumerate(range(0, h, plank)):
        base = (96 + rnd.randint(-8, 8), 61 + rnd.randint(-6, 6), 35 + rnd.randint(-4, 4))
        d.rectangle([0, y, w, y + plank - 1], fill=base + (255,))
        for _ in range(int(w / 6)):
            gx = rnd.randint(0, w); gy = y + rnd.randint(1, plank - 2); gl = rnd.randint(u(4), u(18))
            d.line([gx, gy, gx + gl, gy], fill=tuple(c - 14 for c in base) + (255,), width=1)
        d.line([0, y, w, y], fill=(54, 32, 18, 255), width=S)
        d.line([0, y + S, w, y + S], fill=(130, 88, 54, 255), width=1)
    return img

def parchment(size, seed=3):
    w, h = size
    img = grad(size, (246, 232, 196), (228, 205, 156))
    n = noise((w // 4 + 1, h // 4 + 1), (0, 0, 0), 18, seed).resize(size, Image.BILINEAR)
    lum = n.convert("L").point(lambda v: 128 + (v - 9) * 2)
    tint = Image.new("RGBA", size, (120, 80, 30, 0)); tint.putalpha(lum.point(lambda v: max(0, min(40, v - 110))))
    img.alpha_composite(tint)
    return img

def iron_bracket(d, x, y, flip_x=False, flip_y=False):
    sx = -1 if flip_x else 1; sy = -1 if flip_y else 1
    pts = [(0, 0), (16, 0), (16, 4), (4, 4), (4, 16), (0, 16)]
    P = [(u(x + sx * px), u(y + sy * py)) for px, py in pts]
    d.polygon(P, fill=(58, 58, 64, 255))
    d.line([P[0], P[1]], fill=(120, 120, 130, 255), width=S)
    d.line([P[0], P[5]], fill=(120, 120, 130, 255), width=S)
    for rx, ry in ((2, 2), (12, 2), (2, 12)):
        cx, cy = x + sx * rx, y + sy * ry
        d.ellipse([u(cx - 1.1), u(cy - 1.1), u(cx + 1.1), u(cy + 1.1)], fill=(170, 170, 180, 255))
        d.point((u(cx - 0.4), u(cy - 0.4)), fill=(240, 240, 250, 255))

def rivet(d, x, y, r=1.2):
    d.ellipse([u(x - r), u(y - r), u(x + r), u(y + r)], fill=(36, 36, 40, 255))
    d.ellipse([u(x - r * 0.6), u(y - r * 0.7), u(x + r * 0.3), u(y)], fill=(180, 180, 190, 255))

def pennant(img, x, y, color, length=26, emblem=None):
    d = ImageDraw.Draw(img)
    d.rectangle([u(x - 6), u(y - 1.2), u(x + 6), u(y + 0.6)], fill=(110, 76, 44, 255))
    pts = [(x - 5, y), (x + 5, y), (x + 5, y + length), (x, y + length - 5), (x - 5, y + length)]
    d.polygon([(u(a), u(b)) for a, b in pts], fill=color + (255,))
    d.polygon([(u(a), u(b)) for a, b in [(x - 5, y), (x - 2.5, y), (x - 2.5, y + length - 2.4), (x - 5, y + length)]],
              fill=tuple(max(0, c - 30) for c in color) + (255,))
    d.line([u(x - 5), u(y + 3), u(x + 5), u(y + 3)], fill=(232, 190, 80, 255), width=S)
    if emblem == "crown":
        crown(d, x, y + 11, 3.2, (240, 200, 80))
    elif emblem == "tower":
        d.rectangle([u(x - 2), u(y + 9), u(x + 2), u(y + 16)], fill=(240, 200, 80, 255))
        for k in (-2, 0, 2):
            d.rectangle([u(x + k - 0.6), u(y + 7.6), u(x + k + 0.6), u(y + 9)], fill=(240, 200, 80, 255))

def crown(d, cx, cy, r, col):
    pts = [(cx - r, cy + r * 0.6), (cx - r, cy - r * 0.4), (cx - r * 0.5, cy + r * 0.05), (cx, cy - r * 0.8),
           (cx + r * 0.5, cy + r * 0.05), (cx + r, cy - r * 0.4), (cx + r, cy + r * 0.6)]
    d.polygon([(u(a), u(b)) for a, b in pts], fill=col + (255,))
    for px in (cx - r, cx, cx + r):
        py = cy - r * 0.4 if px != cx else cy - r * 0.8
        d.ellipse([u(px - 0.55), u(py - 0.55), u(px + 0.55), u(py + 0.55)], fill=(255, 240, 180, 255))

def torch(img, x, y):
    d = ImageDraw.Draw(img)
    d.rectangle([u(x - 1), u(y), u(x + 1), u(y + 10)], fill=(100, 66, 38, 255))
    d.rectangle([u(x - 2), u(y + 2), u(x + 2), u(y + 3.5)], fill=(70, 70, 76, 255))
    fl = Image.new("L", img.size, 0); fd = ImageDraw.Draw(fl)
    fd.ellipse([u(x - 2.4), u(y - 5), u(x + 2.4), u(y + 1)], fill=255)
    glow(img, fl, (255, 160, 60), u(5), 0.9)
    d.ellipse([u(x - 2.2), u(y - 4.5), u(x + 2.2), u(y + 0.8)], fill=(255, 150, 40, 255))
    d.ellipse([u(x - 1.2), u(y - 3), u(x + 1.2), u(y + 0.5)], fill=(255, 230, 120, 255))

def wax_seal(img, cx, cy, r):
    d = ImageDraw.Draw(img)
    pts = []
    for k in range(18):
        a = k / 18 * math.tau
        rr = r * (1 + 0.08 * math.sin(k * 2.7))
        pts.append((u(cx + math.cos(a) * rr), u(cy + math.sin(a) * rr)))
    d.polygon(pts, fill=(150, 28, 34, 255))
    d.ellipse([u(cx - r * 0.72), u(cy - r * 0.72), u(cx + r * 0.72), u(cy + r * 0.72)], fill=(176, 40, 44, 255))
    crown(d, cx, cy + 0.3, r * 0.5, (110, 16, 22))
    d.arc([u(cx - r * 0.8), u(cy - r * 0.8), u(cx + r * 0.8), u(cy + r * 0.8)], 200, 290, fill=(220, 110, 110, 255), width=S)

# ---------- scène du bas : château au crépuscule ----------

def castle_scene(img, box):
    x0, y0, x1, y1 = box
    sc = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sc.alpha_composite(grad(img.size, (60, 70, 130), (240, 160, 110)))
    d = ImageDraw.Draw(sc)
    # soleil
    sun = Image.new("L", img.size, 0); ImageDraw.Draw(sun).ellipse([u(x0 + 120), u(y1 - 52), u(x0 + 146), u(y1 - 26)], fill=255)
    glow(sc, sun, (255, 200, 120), u(10), 1.0)
    d.ellipse([u(x0 + 122), u(y1 - 50), u(x0 + 144), u(y1 - 28)], fill=(255, 214, 140, 255))
    rnd = random.Random(5)
    for _ in range(30):
        d.point((u(rnd.uniform(x0, x1)), u(rnd.uniform(y0, y0 + 30))), fill=(255, 255, 255, rnd.randint(60, 180)))
    # collines lointaines
    d.ellipse([u(x0 - 40), u(y1 - 36), u(x0 + 90), u(y1 + 40)], fill=(70, 96, 92, 255))
    d.ellipse([u(x0 + 90), u(y1 - 30), u(x1 + 40), u(y1 + 40)], fill=(64, 88, 86, 255))
    # château (silhouette détaillée)
    cx, base = x0 + 70, y1 - 22
    stone, dark = (88, 80, 98, 255), (60, 54, 70, 255)
    def tower(tx, w, h, roof=True):
        d.rectangle([u(tx - w / 2), u(base - h), u(tx + w / 2), u(base)], fill=stone)
        d.rectangle([u(tx - w / 2), u(base - h), u(tx - w / 2 + 1.2), u(base)], fill=dark)
        if roof:
            d.polygon([(u(tx - w / 2 - 1.5), u(base - h)), (u(tx), u(base - h - w * 1.1)), (u(tx + w / 2 + 1.5), u(base - h))], fill=(150, 44, 50, 255))
            d.line([u(tx), u(base - h - w * 1.1), u(tx), u(base - h - w * 1.1 - 5)], fill=(60, 50, 40, 255), width=S)
            d.polygon([(u(tx), u(base - h - w * 1.1 - 5)), (u(tx + 4), u(base - h - w * 1.1 - 4)), (u(tx), u(base - h - w * 1.1 - 3))], fill=(240, 200, 80, 255))
        for wy in range(int(h // 7)):
            d.rectangle([u(tx - 0.7), u(base - h + 4 + wy * 7), u(tx + 0.7), u(base - h + 6.5 + wy * 7)], fill=(255, 210, 120, 255))
    d.rectangle([u(cx - 26), u(base - 14), u(cx + 26), u(base)], fill=stone)
    for k in range(-26, 26, 4):
        d.rectangle([u(cx + k), u(base - 16), u(cx + k + 2), u(base - 14)], fill=stone)
    tower(cx - 26, 9, 26); tower(cx + 26, 9, 26); tower(cx, 12, 36); tower(cx - 12, 7, 20, False); tower(cx + 12, 7, 20, False)
    d.pieslice([u(cx - 5), u(base - 10), u(cx + 5), u(base)], 180, 360, fill=(40, 30, 30, 255))
    d.rectangle([u(cx - 5), u(base - 5), u(cx + 5), u(base)], fill=(40, 30, 30, 255))
    # colline du château + chemin
    d.ellipse([u(cx - 56), u(base - 4), u(cx + 56), u(base + 30)], fill=(86, 130, 70, 255))
    d.polygon([(u(cx - 4), u(base)), (u(cx + 4), u(base)), (u(cx + 18), u(y1)), (u(cx + 4), u(y1))], fill=(190, 160, 110, 255))
    # oiseaux
    for bx, by in ((x0 + 150, y0 + 22), (x0 + 158, y0 + 18), (x0 + 30, y0 + 26)):
        d.line([u(bx - 2), u(by), u(bx), u(by + 1), u(bx + 2), u(by)], fill=(40, 30, 50, 255), width=S)
    # premier plan : arbres sombres
    for tx in (x0 + 8, x0 + 156, x0 + 170):
        d.polygon([(u(tx - 7), u(y1)), (u(tx), u(y1 - 26)), (u(tx + 7), u(y1))], fill=(36, 60, 50, 255))
    # logo
    f = font(14)
    t = "ROYAUMES"
    tw = d.textlength(t, font=f); tx, ty = u(x0 + 90) - tw / 2, u(y0 + 2)
    tm = Image.new("L", img.size, 0); ImageDraw.Draw(tm).text((tx, ty), t, font=f, fill=255)
    glow(sc, tm, (20, 10, 10), 5, 1.4)
    om = tm.filter(ImageFilter.MaxFilter(5))
    paste_masked(sc, Image.new("RGBA", img.size, (70, 30, 16, 255)), om)
    paste_masked(sc, grad(img.size, (255, 236, 150), (214, 150, 40)), tm)
    m = rmask(img.size, [u(x0), u(y0), u(x1), u(y1)], u(4))
    paste_masked(img, sc, m)
    ImageDraw.Draw(img).rounded_rectangle([u(x0), u(y0), u(x1), u(y1)], radius=u(4), outline=(54, 32, 18, 255), width=S)

# ---------- cadre et pages ----------

LABEL_COL = (74, 44, 20)

def slot_xy(slot):
    r, c = divmod(slot, 9)
    return OX + 8 + 18 * c, OY + 18 + 18 * r

def small_card(img, slot, accent="wood"):
    d = ImageDraw.Draw(img)
    x, y = slot_xy(slot)
    rim = {"wood": (110, 72, 40), "gold": (214, 160, 50), "red": (160, 40, 44), "green": (70, 120, 60), "blue": (50, 80, 140)}[accent]
    d.rounded_rectangle([u(x - 1), u(y - 1), u(x + 17), u(y + 17)], radius=u(2), fill=rim + (255,), outline=(50, 28, 14, 255), width=S)
    d.rounded_rectangle([u(x), u(y), u(x + 16), u(y + 16)], radius=u(1.5), fill=(214, 190, 140, 235))

def card(img, slot, accent="wood", label=None):
    d = ImageDraw.Draw(img)
    x, y = slot_xy(slot)
    rim = {"wood": (110, 72, 40), "gold": (214, 160, 50), "red": (160, 40, 44), "green": (70, 120, 60), "blue": (50, 80, 140)}[accent]
    sh = rmask(img.size, [u(x - 2), u(y - 1), u(x + 18), u(y + 19)], u(3))
    glow(img, sh, (60, 30, 10), u(1.5), 0.7, (0, S))
    d.rounded_rectangle([u(x - 2), u(y - 2), u(x + 18), u(y + 18)], radius=u(3), fill=rim + (255,))
    d.rounded_rectangle([u(x - 2), u(y - 2), u(x + 18), u(y + 18)], radius=u(3), outline=(50, 28, 14, 255), width=S)
    d.rounded_rectangle([u(x - 0.5), u(y - 0.5), u(x + 16.5), u(y + 16.5)], radius=u(2), fill=(214, 190, 140, 235))
    d.line([u(x), u(y + 16), u(x + 16), u(y + 16)], fill=(255, 240, 200, 160), width=S)
    if accent == "gold":
        for rx, ry in ((x - 1, y - 1), (x + 17, y - 1), (x - 1, y + 17), (x + 17, y + 17)):
            d.ellipse([u(rx - 0.8), u(ry - 0.8), u(rx + 0.8), u(ry + 0.8)], fill=(255, 236, 160, 255))
    if label:
        f = font(4.6, black=False)
        tw = d.textlength(label, font=f)
        lx = u(x + 8) - tw / 2; ly = u(y + 19.5)
        d.text((lx + 1, ly + 1), label, font=f, fill=(255, 240, 200, 180))
        d.text((lx, ly), label, font=f, fill=LABEL_COL + (255,))

def page(cards):
    img = Image.new("RGBA", (u(W), u(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fx0, fy0, fx1, fy1 = OX - 10, OY - 9, OX + 186, OY + 240
    # ombre + cadre bois
    glow(img, rmask(img.size, [u(fx0), u(fy0), u(fx1), u(fy1)], u(6)), (0, 0, 0), u(5), 1.0, (0, u(3)))
    paste_masked(img, wood(img.size, 2), rmask(img.size, [u(fx0), u(fy0), u(fx1), u(fy1)], u(6)))
    d.rounded_rectangle([u(fx0), u(fy0), u(fx1), u(fy1)], radius=u(6), outline=(40, 22, 10, 255), width=S)
    # parchemin
    px0, py0, px1, py1 = OX - 4, OY + 14, OX + 180, OY + 234
    pm = rmask(img.size, [u(px0), u(py0), u(px1), u(py1)], u(3))
    paste_masked(img, parchment(img.size), pm)
    edge = ImageChops.subtract(pm, rmask(img.size, [u(px0 + 3), u(py0 + 3), u(px1 - 3), u(py1 - 3)], u(3)).filter(ImageFilter.GaussianBlur(u(2))))
    burnt = Image.new("RGBA", img.size, (120, 70, 30, 0)); burnt.putalpha(edge.point(lambda v: int(v * 0.55)))
    img.alpha_composite(burnt)
    d.rounded_rectangle([u(px0), u(py0), u(px1), u(py1)], radius=u(3), outline=(70, 42, 20, 255), width=S)
    # bannière rouge du titre
    bx0, by0, bx1, by1 = OX - 6, OY - 5, OX + 182, OY + 15
    ban = Image.new("RGBA", img.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(ban)
    bd.polygon([(u(bx0 - 6), u(by0 + 2)), (u(bx0), u(by0)), (u(bx0), u(by1)), (u(bx0 - 6), u(by1 + 2)), (u(bx0 - 3), u((by0 + by1) / 2 + 1))], fill=(120, 26, 30, 255))
    bd.polygon([(u(bx1 + 6), u(by0 + 2)), (u(bx1), u(by0)), (u(bx1), u(by1)), (u(bx1 + 6), u(by1 + 2)), (u(bx1 + 3), u((by0 + by1) / 2 + 1))], fill=(120, 26, 30, 255))
    ban.alpha_composite(grad(img.size, (176, 40, 44), (130, 28, 32)), (0, 0)) if False else None
    bm = Image.new("L", img.size, 0); ImageDraw.Draw(bm).rectangle([u(bx0), u(by0), u(bx1), u(by1)], fill=255)
    paste_masked(ban, grad(img.size, (178, 42, 46), (128, 26, 30)), bm)
    bd.line([u(bx0), u(by0 + 1.5), u(bx1), u(by0 + 1.5)], fill=(236, 190, 80, 255), width=S)
    bd.line([u(bx0), u(by1 - 1.5), u(bx1), u(by1 - 1.5)], fill=(236, 190, 80, 255), width=S)
    for k in range(int(bx0) + 4, int(bx1), 6):
        bd.point((u(k), u(by0 + 3.2)), fill=(255, 220, 140, 120))
    img.alpha_composite(ban)
    wax_seal(img, OX + 6, OY + 5, 6.5)
    # coins en fer forgé
    iron_bracket(d, fx0 + 1, fy0 + 1); iron_bracket(d, fx1 - 1, fy0 + 1, flip_x=True)
    iron_bracket(d, fx0 + 1, fy1 - 1, flip_y=True); iron_bracket(d, fx1 - 1, fy1 - 1, True, True)
    # décorations qui débordent : fanions et torches
    pennant(img, OX - 20, OY - 18, (40, 70, 150), 30, "tower")
    pennant(img, OX + 196, OY - 18, (150, 34, 40), 30, "crown")
    torch(img, OX - 19, OY + 100); torch(img, OX + 195, OY + 100)
    # cartes (accent suivi de « - » = petite carte de grille)
    for slot, (accent, label) in cards.items():
        if accent.endswith("-"):
            small_card(img, slot, accent[:-1])
        else:
            card(img, slot, accent, label)
    # barre en fer #404040 (cache le mot « Inventaire » du jeu)
    bar = [u(OX + 2), u(OY + 127), u(OX + 174), u(OY + 137)]
    d.rounded_rectangle([bar[0], bar[1] - S, bar[2], bar[3] + S], radius=u(2), fill=(30, 30, 34, 255))
    d.rectangle(bar, fill=(64, 64, 64, 255))
    for x in (OX + 4.5, OX + 171.5, OX + 88):
        rivet(d, x, OY + 132)
    # scène du château
    castle_scene(img, (OX + 1, OY + 140, OX + 175, OY + 229))
    return img

# ---------- icônes 32x32 (dessinées en 128) ----------
ICONS = {}
def icon(cmd):
    def deco(f):
        ICONS[cmd] = f
        return f
    return deco

def cv(): return Image.new("RGBA", (128, 128), (0, 0, 0, 0))

def fin(im):
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    a = im.split()[3]
    ol = a.filter(ImageFilter.MaxFilter(9))
    o = Image.new("RGBA", im.size, (40, 22, 10, 255)); o.putalpha(ol)
    out.alpha_composite(o); out.alpha_composite(im)
    return out.resize((32, 32), Image.LANCZOS)

GOLD = (236, 188, 64, 255); GOLD_L = (255, 228, 140, 255); STONE = (150, 146, 160, 255); STONE_D = (110, 106, 122, 255)
RED = (176, 40, 44, 255); WOOD = (150, 98, 54, 255); WOOD_D = (110, 70, 38, 255); GREEN = (90, 160, 70, 255); BLUE = (60, 100, 180, 255)

@icon(7201)  # mon domaine : maison médiévale
def i_domain():
    im = cv(); d = ImageDraw.Draw(im)
    d.rectangle([24, 58, 104, 112], fill=(236, 220, 186, 255))
    for x in (24, 62, 100): d.rectangle([x, 58, x + 6, 112], fill=WOOD_D)
    d.rectangle([24, 80, 104, 86], fill=WOOD_D)
    d.polygon([(12, 62), (64, 14), (116, 62)], fill=RED)
    d.polygon([(12, 62), (64, 14), (64, 62)], fill=(206, 70, 70, 255))
    d.rounded_rectangle([54, 84, 74, 112], radius=8, fill=WOOD)
    d.rectangle([34, 66, 48, 78], fill=(120, 170, 220, 255)); d.rectangle([80, 66, 94, 78], fill=(120, 170, 220, 255))
    return fin(im)

@icon(7202)  # bâtiments : marteau + planche
def i_build():
    im = cv(); d = ImageDraw.Draw(im)
    d.polygon([(30, 104), (44, 118), (98, 64), (84, 50)], fill=WOOD)
    d.polygon([(64, 18), (110, 40), (96, 70), (50, 48)], fill=STONE)
    d.polygon([(64, 18), (110, 40), (104, 52), (58, 30)], fill=(190, 186, 200, 255))
    return fin(im)

@icon(7203)  # marché : sac d'écus
def i_market():
    im = cv(); d = ImageDraw.Draw(im)
    d.ellipse([22, 44, 106, 120], fill=(170, 120, 70, 255))
    d.polygon([(44, 50), (84, 50), (96, 26), (32, 26)], fill=(170, 120, 70, 255))
    d.rectangle([40, 44, 88, 52], fill=RED)
    f = ImageFont.truetype(SERIF, 52, index=0)
    d.text((64, 86), "€" if False else "$", font=f, fill=GOLD, anchor="mm") if False else None
    d.ellipse([46, 66, 82, 102], fill=GOLD); d.ellipse([54, 74, 74, 94], fill=GOLD_L)
    for cx in (98, 108):
        d.ellipse([cx - 14, 96, cx + 14, 110], fill=GOLD); d.ellipse([cx - 14, 92, cx + 14, 106], fill=GOLD_L)
    return fin(im)

@icon(7204)  # équipe : deux boucliers
def i_team():
    im = cv(); d = ImageDraw.Draw(im)
    def shield(x, col, col2):
        d.polygon([(x - 30, 22), (x + 30, 22), (x + 30, 64), (x, 112), (x - 30, 64)], fill=col)
        d.polygon([(x, 22), (x + 30, 22), (x + 30, 64), (x, 112)], fill=col2)
        d.rectangle([x - 4, 30, x + 4, 96], fill=GOLD)
    shield(44, BLUE, (40, 70, 140, 255)); shield(84, RED, (140, 30, 34, 255))
    return fin(im)

@icon(7205)  # améliorer : parchemin + flèche
def i_upgrade():
    im = cv(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([26, 20, 102, 112], radius=10, fill=(240, 222, 180, 255))
    d.ellipse([18, 12, 46, 30], fill=(220, 196, 150, 255)); d.ellipse([82, 102, 110, 120], fill=(220, 196, 150, 255))
    d.polygon([(64, 32), (92, 64), (76, 64), (76, 98), (52, 98), (52, 64), (36, 64)], fill=GREEN)
    return fin(im)

@icon(7206)  # classement : coupe
def i_rank():
    im = cv(); d = ImageDraw.Draw(im)
    d.pieslice([30, 2, 98, 82], 0, 180, fill=GOLD)
    d.rectangle([30, 20, 98, 42], fill=GOLD)
    d.arc([12, 26, 44, 62], 90, 270, fill=GOLD, width=8); d.arc([84, 26, 116, 62], 270, 90, fill=GOLD, width=8)
    d.rectangle([56, 80, 72, 96], fill=GOLD); d.rounded_rectangle([36, 96, 92, 114], radius=4, fill=WOOD)
    d.polygon([(64, 30), (69, 42), (82, 42), (72, 50), (76, 62), (64, 55), (52, 62), (56, 50), (46, 42), (59, 42)], fill=GOLD_L)
    return fin(im)

@icon(7207)  # capitale : château
def i_capital():
    im = cv(); d = ImageDraw.Draw(im)
    d.rectangle([20, 56, 108, 114], fill=STONE)
    for x in range(20, 108, 16): d.rectangle([x, 46, x + 8, 56], fill=STONE)
    d.rectangle([44, 30, 84, 114], fill=(170, 166, 180, 255))
    for x in (44, 60, 76): d.rectangle([x, 20, x + 8, 30], fill=(170, 166, 180, 255))
    d.pieslice([52, 84, 76, 108], 180, 360, fill=WOOD_D); d.rectangle([52, 96, 76, 114], fill=WOOD_D)
    d.line([64, 20, 64, 2], fill=WOOD_D, width=4); d.polygon([(64, 2), (88, 8), (64, 14)], fill=RED)
    return fin(im)

@icon(7208)  # visiter : carte
def i_visit():
    im = cv(); d = ImageDraw.Draw(im)
    d.polygon([(14, 30), (46, 20), (82, 30), (114, 20), (114, 100), (82, 110), (46, 100), (14, 110)], fill=(236, 216, 170, 255))
    d.polygon([(46, 20), (82, 30), (82, 110), (46, 100)], fill=(214, 190, 140, 255))
    d.line([(26, 88), (44, 70), (64, 78), (88, 54)], fill=RED, width=5)
    d.line([(92, 44), (104, 56)], fill=RED, width=6); d.line([(104, 44), (92, 56)], fill=RED, width=6)
    return fin(im)

@icon(7209)  # aide : livre
def i_help():
    im = cv(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([22, 16, 106, 112], radius=8, fill=(120, 40, 40, 255))
    d.rectangle([30, 16, 40, 112], fill=(90, 26, 28, 255))
    d.rounded_rectangle([50, 34, 94, 58], radius=4, fill=GOLD)
    d.rectangle([22, 100, 106, 112], fill=(240, 226, 196, 255))
    return fin(im)

@icon(7210)  # fermer : croix en fer
def i_close():
    im = cv(); d = ImageDraw.Draw(im)
    d.line([(26, 26), (102, 102)], fill=RED, width=22); d.line([(102, 26), (26, 102)], fill=RED, width=22)
    d.line([(30, 26), (102, 98)], fill=(220, 90, 90, 255), width=6)
    return fin(im)

@icon(7211)  # paramètres : roue dentée
def i_settings():
    im = cv(); d = ImageDraw.Draw(im)
    for k in range(8):
        a = k / 8 * math.tau
        x, y = 64 + math.cos(a) * 44, 64 + math.sin(a) * 44
        d.rounded_rectangle([x - 11, y - 11, x + 11, y + 11], radius=3, fill=STONE_D)
    d.ellipse([22, 22, 106, 106], fill=STONE); d.ellipse([46, 46, 82, 82], fill=(70, 66, 80, 255))
    return fin(im)

@icon(7212)  # bannière / blason (info royaume)
def i_banner():
    im = cv(); d = ImageDraw.Draw(im)
    d.rectangle([20, 8, 108, 16], fill=WOOD_D)
    d.polygon([(28, 16), (100, 16), (100, 104), (64, 120), (28, 104)], fill=BLUE)
    d.polygon([(64, 16), (100, 16), (100, 104), (64, 120)], fill=(46, 80, 156, 255))
    crown(d, 0, 0, 0, (0, 0, 0)) if False else None
    pts = [(40, 70), (40, 44), (52, 58), (64, 36), (76, 58), (88, 44), (88, 70)]
    d.polygon(pts, fill=GOLD)
    return fin(im)


# ---------- icônes supplémentaires ----------
def arrow(d, left, col):
    pts = [(100, 52), (56, 52), (56, 28), (14, 64), (56, 100), (56, 76), (100, 76)]
    if not left: pts = [(128 - x, y) for x, y in pts]
    d.polygon(pts, fill=col)

@icon(7213)
def i_back():
    im = cv(); d = ImageDraw.Draw(im); arrow(d, True, (236, 220, 186, 255)); return fin(im)

@icon(7214)
def i_prev():
    im = cv(); d = ImageDraw.Draw(im); arrow(d, True, GOLD); return fin(im)

@icon(7215)
def i_next():
    im = cv(); d = ImageDraw.Draw(im); arrow(d, False, GOLD); return fin(im)

@icon(7216)
def i_yes():
    im = cv(); d = ImageDraw.Draw(im)
    d.line([(24, 66), (52, 96), (106, 32)], fill=GREEN, width=24, joint="curve"); return fin(im)

@icon(7217)
def i_no():
    im = cv(); d = ImageDraw.Draw(im)
    d.line([(30, 30), (98, 98)], fill=RED, width=22); d.line([(98, 30), (30, 98)], fill=RED, width=22); return fin(im)

@icon(7218)  # récolter : panier
def i_harvest():
    im = cv(); d = ImageDraw.Draw(im)
    d.arc([30, 14, 98, 86], 180, 360, fill=WOOD_D, width=10)
    for x, col in ((40, (230, 200, 60, 255)), (60, (232, 120, 40, 255)), (80, (200, 60, 60, 255))):
        d.ellipse([x - 14, 40, x + 14, 66], fill=col)
    d.polygon([(18, 56), (110, 56), (96, 112), (32, 112)], fill=WOOD)
    for y in (68, 84, 100): d.line([(26, y), (102, y)], fill=WOOD_D, width=5)
    return fin(im)

@icon(7219)  # vendre : pile d'écus
def i_sell():
    im = cv(); d = ImageDraw.Draw(im)
    for k, y in enumerate((96, 80, 64, 48)):
        d.ellipse([30, y, 98, y + 24], fill=GOLD); d.ellipse([30, y - 6, 98, y + 18], fill=GOLD_L)
    d.ellipse([44, 36, 84, 54], fill=GOLD)
    return fin(im)

@icon(7220)  # démolir : pioche cassante
def i_demolish():
    im = cv(); d = ImageDraw.Draw(im)
    d.line([(36, 108), (92, 36)], fill=WOOD, width=14)
    d.arc([22, 8, 110, 76], 200, 340, fill=STONE, width=16)
    for x, y in ((18, 96), (104, 100), (60, 116)): d.polygon([(x, y), (x + 10, y - 8), (x + 14, y + 4)], fill=RED)
    return fin(im)

@icon(7221)  # scierie : bûches + scie
def i_sawmill():
    im = cv(); d = ImageDraw.Draw(im)
    for k, (x, y) in enumerate(((24, 70), (64, 70), (44, 40))):
        d.rounded_rectangle([x, y, x + 40, y + 30], radius=12, fill=WOOD)
        d.ellipse([x + 26, y + 2, x + 44, y + 28], fill=(214, 170, 110, 255)); d.ellipse([x + 31, y + 9, x + 39, y + 21], fill=WOOD_D)
    d.polygon([(70, 12), (118, 12), (118, 26), (70, 26)], fill=STONE)
    for x in range(72, 118, 8): d.polygon([(x, 26), (x + 4, 34), (x + 8, 26)], fill=STONE)
    return fin(im)

@icon(7222)  # mine : pioche + minerai
def i_mine():
    im = cv(); d = ImageDraw.Draw(im)
    d.polygon([(12, 110), (40, 50), (88, 40), (118, 96), (100, 116)], fill=STONE_D)
    for x, y, c in ((44, 72, (40, 40, 44, 255)), (70, 86, (220, 180, 140, 255)), (90, 66, (240, 210, 80, 255))):
        d.rectangle([x, y, x + 12, y + 12], fill=c)
    d.line([(30, 100), (96, 22)], fill=WOOD, width=12)
    d.arc([46, 0, 126, 60], 200, 330, fill=(200, 200, 210, 255), width=14)
    return fin(im)

@icon(7223)  # ferme : gerbe de blé
def i_farm():
    im = cv(); d = ImageDraw.Draw(im)
    for k in range(-3, 4):
        x = 64 + k * 9
        d.line([(64, 108), (x, 30)], fill=(214, 180, 70, 255), width=6)
        d.ellipse([x - 7, 14, x + 7, 40], fill=(240, 206, 90, 255))
    d.rectangle([48, 70, 80, 82], fill=RED)
    return fin(im)

@icon(7224)  # inviter : parchemin + plume
def i_invite():
    im = cv(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 26, 92, 110], radius=8, fill=(240, 222, 180, 255))
    for y in (46, 62, 78): d.line([(32, y), (80, y)], fill=(170, 140, 100, 255), width=5)
    d.polygon([(70, 96), (118, 12), (124, 20), (82, 100)], fill=(250, 250, 255, 255))
    d.line([(74, 98), (60, 112)], fill=(40, 30, 30, 255), width=5)
    return fin(im)

@icon(7225)  # verrouillé : cadenas en fer
def i_locked():
    im = cv(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([40, 18, 88, 72], radius=22, outline=STONE, width=12)
    d.rounded_rectangle([26, 56, 102, 116], radius=10, fill=STONE_D)
    d.ellipse([56, 74, 72, 90], fill=(40, 36, 46, 255)); d.rectangle([61, 84, 67, 102], fill=(40, 36, 46, 255))
    return fin(im)

@icon(7226)  # vide
def i_empty():
    im = cv(); d = ImageDraw.Draw(im)
    d.ellipse([20, 20, 108, 108], outline=(150, 130, 100, 255), width=12)
    d.line([(38, 90), (90, 38)], fill=(150, 130, 100, 255), width=12); return fin(im)

@icon(7227)  # fonder : drapeau planté
def i_found():
    im = cv(); d = ImageDraw.Draw(im)
    d.ellipse([16, 96, 112, 122], fill=GREEN)
    d.rectangle([34, 8, 44, 108], fill=WOOD_D)
    d.polygon([(44, 12), (112, 30), (44, 62)], fill=RED)
    crown(d, 0, 0, 0, (0, 0, 0)) if False else None
    d.polygon([(56, 34), (60, 24), (66, 32), (72, 22), (76, 36)], fill=GOLD)
    return fin(im)

@icon(7228)  # agrandir : carte + flèches
def i_expand():
    im = cv(); d = ImageDraw.Draw(im)
    d.rectangle([34, 34, 94, 94], fill=GREEN); d.rectangle([34, 34, 94, 94], outline=(60, 110, 50, 255), width=6)
    for (x, y, dx, dy) in ((10, 10, 1, 1), (118, 10, -1, 1), (10, 118, 1, -1), (118, 118, -1, -1)):
        d.polygon([(x, y), (x + dx * 28, y), (x, y + dy * 28)], fill=GOLD)
    return fin(im)

@icon(7229)  # portes ouvertes
def i_open():
    im = cv(); d = ImageDraw.Draw(im)
    d.pieslice([24, 14, 104, 94], 180, 360, fill=STONE); d.rectangle([24, 54, 104, 116], fill=STONE)
    d.pieslice([40, 30, 88, 78], 180, 360, fill=(120, 200, 110, 255)); d.rectangle([40, 54, 88, 116], fill=(120, 200, 110, 255))
    d.polygon([(40, 54), (26, 62), (26, 116), (40, 116)], fill=WOOD); d.polygon([(88, 54), (102, 62), (102, 116), (88, 116)], fill=WOOD)
    return fin(im)

@icon(7230)  # portes fermées
def i_closed():
    im = cv(); d = ImageDraw.Draw(im)
    d.pieslice([24, 14, 104, 94], 180, 360, fill=STONE); d.rectangle([24, 54, 104, 116], fill=STONE)
    d.pieslice([40, 30, 88, 78], 180, 360, fill=WOOD); d.rectangle([40, 54, 88, 116], fill=WOOD)
    d.line([(64, 30), (64, 116)], fill=WOOD_D, width=4)
    for y in (64, 90): d.rectangle([40, y, 88, y + 6], fill=(60, 60, 66, 255))
    return fin(im)

@icon(7231)  # tout vendre : charrette
def i_cart():
    im = cv(); d = ImageDraw.Draw(im)
    d.polygon([(14, 46), (114, 46), (102, 88), (26, 88)], fill=WOOD)
    for x, col in ((34, GOLD), (56, (214, 120, 60, 255)), (78, (120, 180, 80, 255)), (96, GOLD_L)):
        d.ellipse([x - 12, 26, x + 12, 50], fill=col)
    for cx in (38, 92):
        d.ellipse([cx - 16, 80, cx + 16, 112], fill=WOOD_D); d.ellipse([cx - 6, 90, cx + 6, 102], fill=STONE)
    return fin(im)

@icon(7232)  # couronne
def i_crown():
    im = cv(); d = ImageDraw.Draw(im)
    d.polygon([(14, 100), (14, 36), (40, 68), (64, 24), (88, 68), (114, 36), (114, 100)], fill=GOLD)
    d.rectangle([14, 92, 114, 108], fill=(214, 160, 40, 255))
    for x, c in ((40, RED), (64, BLUE), (88, GREEN)): d.ellipse([x - 7, 92, x + 7, 106], fill=c)
    return fin(im)

@icon(7233)  # invitation : lettre scellée
def i_letter():
    im = cv(); d = ImageDraw.Draw(im)
    d.rectangle([14, 32, 114, 100], fill=(240, 222, 180, 255))
    d.polygon([(14, 32), (64, 72), (114, 32)], fill=(222, 198, 150, 255))
    d.ellipse([50, 58, 78, 86], fill=RED); crown(d, 0, 0, 0, (0, 0, 0)) if False else None
    return fin(im)

# ---------- pages ----------
LIST_SLOTS = [9 + r * 9 + c for r in range(4) for c in range(1, 8)]
PAGES = {
    "main": ("\ue020", {0: ("wood", None), 4: ("gold", None), 8: ("red", None),
        19: ("green", "Mon domaine"), 21: ("wood", "Bâtiments"), 23: ("gold", "Marché"), 25: ("blue", "Équipe"),
        37: ("green", "Améliorer"), 39: ("gold", "Classement"), 41: ("red", "Capitale"), 43: ("blue", "Visiter")}),
    "list": ("\ue021", {**{s: ("wood-", None) for s in LIST_SLOTS}, 45: ("wood-", None), 48: ("wood-", None),
        49: ("gold-", None), 50: ("wood-", None), 53: ("red-", None)}),
    "building": ("\ue022", {4: ("gold", None), 8: ("red", None),
        19: ("green", "Récolter"), 21: ("gold", "Vendre"), 23: ("green", "Améliorer"), 25: ("red", "Démolir"),
        **{s: ("wood-", None) for s in range(37, 44)}, 45: ("wood-", None)}),
    "domain": ("\ue023", {4: ("gold", None), 8: ("red", None),
        20: ("green", "Agrandir"), 22: ("blue", "Visites"), 24: ("blue", "Équipe"), 40: ("red", None), 45: ("wood-", None)}),
    "confirm": ("\ue024", {13: ("gold", None), 29: ("green", "Confirmer"), 33: ("red", "Annuler")}),
    "start": ("\ue025", {4: ("gold", None), 8: ("red", None),
        21: ("green", "Fonder"), 23: ("gold", "Invitation"), 39: ("red", "Capitale"), 41: ("blue", "Visiter")}),
}

def build_pack(out):
    tex = os.path.join(out, "assets/cobbleislands/textures/gui"); os.makedirs(tex, exist_ok=True)
    providers = [{"type": "space", "advances": {"\ue001": -(8 + OX), "\ue002": -(W + 1 - OX - 16)}}]
    for name, (ch, cards) in PAGES.items():
        page(cards).save(os.path.join(tex, name + ".png"))
        providers.append({"type": "bitmap", "file": f"cobbleislands:gui/{name}.png", "height": H, "ascent": 13 + OY, "chars": [ch]})
    fdir = os.path.join(out, "assets/cobbleislands/font"); os.makedirs(fdir, exist_ok=True)
    json.dump({"providers": providers}, open(os.path.join(fdir, "gui.json"), "w"), ensure_ascii=False, indent=1)
    idir = os.path.join(out, "assets/cobbleislands/textures/item/ui"); os.makedirs(idir, exist_ok=True)
    mdir = os.path.join(out, "assets/cobbleislands/models/item/ui"); os.makedirs(mdir, exist_ok=True)
    entries = []
    for cmd, f in sorted(ICONS.items()):
        f().save(os.path.join(idir, f"{cmd}.png"))
        json.dump({"parent": "minecraft:item/generated", "textures": {"layer0": f"cobbleislands:item/ui/{cmd}"}}, open(os.path.join(mdir, f"{cmd}.json"), "w"))
        entries.append((cmd, f"cobbleislands:item/ui/{cmd}"))
    os.makedirs(os.path.join(out, "assets/minecraft/models/item"), exist_ok=True)
    os.makedirs(os.path.join(out, "assets/minecraft/items"), exist_ok=True)
    json.dump({"parent": "minecraft:item/generated", "textures": {"layer0": "minecraft:item/paper"},
               "overrides": [{"predicate": {"custom_model_data": c}, "model": m} for c, m in entries]},
              open(os.path.join(out, "assets/minecraft/models/item/paper.json"), "w"), indent=1)
    json.dump({"model": {"type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data", "index": 0,
               "fallback": {"type": "minecraft:model", "model": "minecraft:item/paper"},
               "entries": [{"threshold": c, "model": {"type": "minecraft:model", "model": m}} for c, m in entries]}},
              open(os.path.join(out, "assets/minecraft/items/paper.json"), "w"), indent=1)
    json.dump({"pack": {"pack_format": 34, "supported_formats": {"min_inclusive": 34, "max_inclusive": 99},
               "description": "§6Royaumes §7- menus et icônes"}}, open(os.path.join(out, "pack.mcmeta"), "w"), ensure_ascii=False, indent=1)
    # icône du pack : bannière
    ICONS[7212]().resize((128, 128), Image.NEAREST).save(os.path.join(out, "pack.png"))
    return len(entries)

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--pack":
    print("icônes :", build_pack(sys.argv[2]))
    sys.exit(0)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/rp/med"
    os.makedirs(out, exist_ok=True)
    for cmd, f in ICONS.items():
        f().save(os.path.join(out, f"{cmd}.png"))
    main = {0: ("wood", None), 4: ("gold", None), 8: ("red", None),
            19: ("green", "Mon domaine"), 21: ("wood", "Bâtiments"), 23: ("gold", "Marché"), 25: ("blue", "Équipe"),
            37: ("green", "Améliorer"), 39: ("gold", "Classement"), 41: ("red", "Capitale"), 43: ("blue", "Visiter")}
    img = page(main)
    img.save(os.path.join(out, "main_bg.png"))
    # aperçu « en jeu » : icônes posées + titre
    icons = {0: 7211, 4: 7212, 8: 7210, 19: 7201, 21: 7202, 23: 7203, 25: 7204, 37: 7205, 39: 7206, 41: 7207, 43: 7208}
    prev = img.copy()
    for slot, cmd in icons.items():
        x, y = slot_xy(slot)
        prev.alpha_composite(Image.open(os.path.join(out, f"{cmd}.png")), (u(x), u(y)))
    pd = ImageDraw.Draw(prev)
    tf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", u(7))
    pd.text((u(OX + 15) + S, u(OY + 6) + S), "Royaume de Thozire", font=tf, fill=(60, 10, 10, 255))
    pd.text((u(OX + 15), u(OY + 6)), "Royaume de Thozire", font=tf, fill=(255, 236, 190, 255))
    bg = Image.new("RGBA", prev.size, (0, 0, 0, 255)); bd = ImageDraw.Draw(bg); rnd = random.Random(1)
    for yy in range(0, prev.size[1], 16):
        for xx in range(0, prev.size[0], 16):
            g = rnd.randint(50, 80); bd.rectangle([xx, yy, xx + 15, yy + 15], fill=(g - 10, g + 15, g - 25, 255))
    bg = bg.filter(ImageFilter.GaussianBlur(3)); bg.alpha_composite(Image.new("RGBA", bg.size, (0, 0, 0, 100)))
    bg.alpha_composite(prev)
    bg.resize((bg.width * 3 // 2, bg.height * 3 // 2), Image.LANCZOS).save("/home/claude/rp/maquette_royaumes.png")
    print("ok")
