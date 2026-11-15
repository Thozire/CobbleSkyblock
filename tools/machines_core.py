"""Bâtiments médiévaux « Royaumes » (v2) : scierie à roue à aubes, moulin-ferme, mine, forge.

Chaque bâtiment occupe 3x3 blocs au sol et jusqu'à 3 blocs de haut. Il est dessiné dans un
« repère de dessin » : X, Y, Z de 0 à 48 (1 = 1/16 de bloc), façade en Z = 0, sol en Y = 0,
bloc central = X et Z de 16 à 32.

Un bâtiment = un socle immobile + des pièces animées + une pièce lumineuse (fenêtres, braises…).
Chaque pièce est une entité item_display posée au centre du bloc central ; le serveur lui applique
les images-clés (translation, rotation autour d'un axe, échelle) générées ici, et le client
interpole entre deux clés : les animations sont fluides.

Ce fichier sait aussi dessiner des aperçus (PNG / GIF animés) avec un petit moteur de rendu logiciel.
"""
import json, math, os, random
from PIL import Image, ImageDraw

MC = os.environ.get("MC_ASSETS", "/home/claude/mcassets/assets/minecraft") + "/textures/"
PACK = os.environ.get("ROYAUMES_PACK", "/home/claude/rp/royaumes")
NS = PACK + "/assets/cobbleislands"
VERSION = 5            # version des modèles : les machines déjà posées sont reconstruites si elle change
TICKS_PER_STEP = 5     # le serveur anime toutes les 5 ticks

# ================================================================ textures peintes (16x16)
def _img(h=16): return Image.new("RGBA", (16, h), (0, 0, 0, 0))

def _mul(c, v): return tuple(max(0, min(255, int(k * v))) for k in c)

def tex_sack():
    im = _img(); d = im.load(); rnd = random.Random(5)
    for y in range(16):
        for x in range(16):
            v = 0.85 + 0.15 * ((x + y) % 2) + rnd.uniform(-0.06, 0.06)
            d[x, y] = _mul((204, 170, 118), v) + (255,)
    return im

def tex_sawdust():
    im = _img(); d = im.load(); rnd = random.Random(6)
    for y in range(16):
        for x in range(16):
            v = rnd.choice((0.8, 0.9, 1.0, 1.08))
            d[x, y] = _mul((226, 190, 128), v) + (255,)
    return im

def tex_leather():
    im = _img(); d = im.load(); rnd = random.Random(10)
    for y in range(16):
        for x in range(16):
            v = 0.86 + (0.16 if x % 4 == 0 else 0) + rnd.uniform(-0.05, 0.05) - (0.12 if x % 4 == 1 else 0)
            d[x, y] = _mul((132, 80, 48), v) + (255,)
    return im

def tex_hole():
    im = Image.new("RGBA", (16, 16), (14, 11, 13, 255)); d = im.load(); rnd = random.Random(2)
    for _ in range(14):
        d[rnd.randrange(16), rnd.randrange(16)] = (24, 20, 22, 255)
    return im

def tex_rope():
    im = _img(); d = im.load()
    for y in range(16):
        for x in range(16):
            d[x, y] = ((182, 144, 92) if (x + y) % 4 < 2 else (134, 100, 62)) + (255,)
    return im

def tex_iron_dark():
    im = _img(); d = im.load(); rnd = random.Random(11)
    for y in range(16):
        for x in range(16):
            v = 74 + rnd.randint(-6, 6)
            d[x, y] = (v, v + 1, v + 10, 255)
    for i in range(16): d[i, 0] = (104, 106, 120, 255); d[0, i] = (96, 98, 112, 255); d[i, 15] = (52, 52, 62, 255)
    return im

def tex_steel():
    im = _img(); d = im.load(); rnd = random.Random(12)
    for y in range(16):
        for x in range(16):
            v = 176 + rnd.randint(-8, 8) + (22 if (x + y) % 7 == 0 else 0)
            d[x, y] = (v, v + 4, v + 14, 255)
    return im

def tex_blade():
    """Lame de scie verticale : dents à gauche (u = 0), dos à droite. Se répète en hauteur."""
    im = _img(); d = im.load()
    for y in range(16):
        tooth = (y % 4)                     # dents en biseau de 3 px
        for x in range(16):
            if x < 3 and x < 3 - tooth: continue
            v = 168 + (26 if x in (3, 4) else 0) - (30 if x >= 14 else 0) + (10 if y % 4 == 0 else 0)
            d[x, y] = (v, v + 4, v + 16, 255)
        if tooth == 0: d[0, y] = (240, 244, 252, 255)
    return im

def tex_thatch():
    im = _img(); d = im.load(); rnd = random.Random(21)
    for x in range(16):
        base = rnd.choice((0.86, 0.94, 1.0, 1.06))
        for y in range(16):
            v = base + rnd.uniform(-0.05, 0.05)
            if y % 8 == 7: v *= 0.68                      # ombre sous chaque rang de chaume
            elif y % 8 == 0: v *= 1.12
            d[x, y] = _mul((196, 160, 84), v) + (255,)
    return im

def tex_shingle():
    """Bardeaux de bois : rangs de 4 px décalés en quinconce."""
    im = _img(); d = im.load(); rnd = random.Random(22)
    for row in range(4):
        off = 0 if row % 2 == 0 else 2
        for x in range(16):
            col = ((x + off) // 4)
            tone = random.Random(row * 31 + col % 4).choice((0.84, 0.94, 1.0, 1.1))
            for yy in range(4):
                y = row * 4 + yy
                v = tone + rnd.uniform(-0.04, 0.04)
                if yy == 3: v *= 0.62
                if (x + off) % 4 == 3: v *= 0.78
                d[x, y] = _mul((122, 74, 44), v) + (255,)
    return im

def tex_sail():
    """Toile de voile écrue tendue sur un treillis de bois."""
    im = _img(); d = im.load(); rnd = random.Random(23)
    for y in range(16):
        for x in range(16):
            v = 0.94 + rnd.uniform(-0.03, 0.03) + (0.05 if (x + y) % 2 == 0 else 0)
            c = _mul((232, 220, 192), v)
            if x % 8 == 7 or y % 8 == 7: c = (112, 78, 46)
            elif x % 8 == 6 or y % 8 == 6: c = _mul(c, 0.86)
            d[x, y] = c + (255,)
    return im

def tex_water():
    """Eau courante animée (8 images) : reflets qui glissent vers le bas de la texture."""
    frames = 8
    im = Image.new("RGBA", (16, 16 * frames)); d = im.load(); rnd = random.Random(24)
    streaks = [(rnd.randrange(16), rnd.randrange(16), rnd.randint(2, 4)) for _ in range(9)]
    noise = [[rnd.uniform(-0.04, 0.04) for _ in range(16)] for _ in range(16)]
    for f in range(frames):
        for y in range(16):
            for x in range(16):
                c = _mul((52, 112, 196), 1.0 + noise[(y - 2 * f) % 16][x])
                d[x, f * 16 + y] = c + (255,)
        for (sx, sy, ln) in streaks:
            for k in range(ln):
                y = (sy + k + 2 * f) % 16
                d[sx, f * 16 + y] = ((150, 200, 246) if k < ln - 1 else (214, 236, 255)) + (255,)
    return im, {"animation": {"frametime": 2}}

def tex_glow():
    """Lumière chaude (vitre de lanterne, fenêtre éclairée) qui palpite doucement."""
    frames = 4
    im = Image.new("RGBA", (16, 16 * frames)); d = im.load()
    for f in range(frames):
        k = (1.0, 0.95, 1.03, 0.92)[f]
        for y in range(16):
            for x in range(16):
                r = math.hypot(x - 7.5, y - 7.5) / 10.6
                c = _mul((255, 232 - 70 * r, 150 - 110 * r), k)
                d[x, f * 16 + y] = c + (255,)
    return im, {"animation": {"frametime": 5, "interpolate": True}}

def tex_window():
    """Fenêtre à croisillons éclairée de l'intérieur."""
    im = _img(); d = im.load()
    for y in range(16):
        for x in range(16):
            r = math.hypot(x - 7.5, y - 7.5) / 10.6
            c = (255, int(214 - 60 * r), int(120 - 70 * r))
            if x % 4 == 3 or y % 4 == 3: c = (74, 48, 30)
            d[x, y] = c + (255,)
    return im

def tex_hot():
    """Métal chauffé à blanc (lingot sur l'enclume), 4 images."""
    frames = 4
    im = Image.new("RGBA", (16, 16 * frames)); d = im.load(); rnd = random.Random(25)
    for f in range(frames):
        k = (1.0, 0.93, 1.05, 0.9)[f]
        for y in range(16):
            for x in range(16):
                c = _mul((255, 150 + rnd.randint(-10, 30), 50 + rnd.randint(0, 40)), k)
                d[x, f * 16 + y] = c + (255,)
    return im, {"animation": {"frametime": 4, "interpolate": True}}

def _banner(main, trim):
    def paint():
        im = _img(); d = im.load()
        for y in range(16):
            for x in range(16):
                c = _mul(main, 1.0 - 0.10 * ((x // 2) % 2))
                if y < 2 or x == 0: c = trim
                if 6 <= x <= 9 and 5 <= y <= 12 and (x in (7, 8) or y in (8, 9)): c = trim
                d[x, y] = c + (255,)
        return im
    return paint

def tex_ore(seed, nug):
    def paint():
        base = Image.open(MC + "block/stone.png").convert("RGBA").crop((0, 0, 16, 16))
        d = base.load(); rnd = random.Random(seed)
        for _ in range(11):
            x, y = rnd.randint(0, 14), rnd.randint(0, 14)
            d[x, y] = nug + (255,); d[x + 1, y] = _mul(nug, 0.78) + (255,)
            if rnd.random() < 0.5: d[x, y + 1] = _mul(nug, 1.15) + (255,)
        return base
    return paint

def tex_plaster():
    """Torchis clair, légèrement sali vers le bas."""
    im = _img(); d = im.load(); rnd = random.Random(27)
    for y in range(16):
        for x in range(16):
            v = 1.0 + rnd.uniform(-0.035, 0.035)
            if rnd.random() < 0.06: v -= 0.08
            d[x, y] = _mul((226, 212, 184), v) + (255,)
    return im

CUSTOM = {
    "sack": tex_sack, "sawdust": tex_sawdust, "leather": tex_leather, "hole": tex_hole, "rope": tex_rope,
    "iron_dark": tex_iron_dark, "steel": tex_steel, "blade": tex_blade, "thatch": tex_thatch, "shingle": tex_shingle,
    "sail": tex_sail, "water": tex_water, "glow": tex_glow, "window": tex_window, "hot": tex_hot, "plaster": tex_plaster,
    "banner_green": _banner((58, 128, 62), (232, 196, 84)), "banner_red": _banner((170, 44, 40), (232, 196, 84)),
    "banner_blue": _banner((50, 84, 168), (232, 196, 84)), "banner_gold": _banner((214, 160, 40), (120, 40, 36)),
    "ore_gold": tex_ore(31, (250, 214, 74)), "ore_iron": tex_ore(32, (216, 175, 147)),
    "ore_copper": tex_ore(33, (226, 128, 84)), "ore_coal": tex_ore(34, (38, 38, 42)),
}

def tex_ref(name):
    if name.startswith("mc:"): return "minecraft:block/" + name[3:]
    return "cobbleislands:block/machine/" + name

_tex_cache = {}
def tex_image(name):
    """Première image (16x16) d'une texture, pour les aperçus."""
    if name not in _tex_cache:
        if name.startswith("mc:"):
            im = Image.open(MC + "block/" + name[3:] + ".png").convert("RGBA")
        else:
            im = CUSTOM[name]()
            if isinstance(im, tuple): im = im[0]
        _tex_cache[name] = im.crop((0, 0, 16, 16)).load()
    return _tex_cache[name]

# ================================================================ modèle
FACES = ("north", "south", "east", "west", "up", "down")

def _rot(p, rot):
    """Rotation (règle de la main droite, comme les modèles Minecraft) : rot = (axe, angle°, origine)."""
    if not rot: return p
    ax, ang, o = rot
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    x, y, z = p[0] - o[0], p[1] - o[1], p[2] - o[2]
    if ax == "y": x, z = x * c + z * s, -x * s + z * c
    elif ax == "x": y, z = y * c - z * s, y * s + z * c
    else: x, y = x * c - y * s, x * s + y * c
    return (x + o[0], y + o[1], z + o[2])

class Model:
    """Liste de boîtes dans le repère de dessin."""
    def __init__(self): self.els = []

    def box(self, f, t, tex, faces=None, rot=None, tile=True, uvrot=None, uvo=None, uv=None, skip=()):
        """tex : nom ou dict face -> nom ('*' = défaut). rot = (axe, angle, origine) parmi ±22.5 / ±45.
        tile : découpe sur la grille de 16 pour que les textures se répètent comme sur de vrais blocs.
        uvrot : dict face -> 90/180/270. uvo : décalage (u, v) du coin de texture quand tile=False.
        uv : dict face -> [u0, v0, u1, v1] imposé."""
        if isinstance(tex, str): tex = {k: tex for k in FACES}
        else: tex = {k: tex.get(k, tex.get("*")) for k in FACES}
        fs = [k for k in (faces or FACES) if tex.get(k) and k not in skip]
        self.els.append({"from": tuple(map(float, f)), "to": tuple(map(float, t)), "tex": tex, "faces": fs, "rot": rot,
                         "tile": tile and not rot, "uvrot": uvrot or {}, "uvo": uvo or (0, 0), "uv": uv or {}})
        return self

    def add(self, other):
        self.els += other.els
        return self

    def bounds(self):
        lo = [1e9] * 3; hi = [-1e9] * 3
        for e in self.els:
            (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
            for cx in (x0, x1):
                for cy in (y0, y1):
                    for cz in (z0, z1):
                        p = _rot((cx, cy, cz), e["rot"])
                        for k in range(3): lo[k] = min(lo[k], p[k]); hi[k] = max(hi[k], p[k])
        return lo, hi

def _split(e):
    """Découpe une boîte aux multiples de 16 (repère de dessin) ; ne garde que les faces extérieures."""
    cuts = []
    for k in range(3):
        a, b = e["from"][k], e["to"][k]
        pts = [a]
        if e["tile"]:
            g = math.floor(a / 16) * 16 + 16
            while g < b - 1e-6:
                pts.append(g); g += 16
        elif b - a > 16 + 1e-6 and not e["uv"]:      # boîte libre trop longue : tronçons égaux de 16 au plus
            n = math.ceil((b - a) / 16 - 1e-6)
            pts += [a + (b - a) * i / n for i in range(1, n)]
        pts.append(b)
        cuts.append(pts)
    if all(len(c) == 2 for c in cuts): return [e]
    out = []
    for i in range(len(cuts[0]) - 1):
        for j in range(len(cuts[1]) - 1):
            for k in range(len(cuts[2]) - 1):
                faces = []
                for fc in e["faces"]:
                    if fc == "west" and i != 0: continue
                    if fc == "east" and i != len(cuts[0]) - 2: continue
                    if fc == "down" and j != 0: continue
                    if fc == "up" and j != len(cuts[1]) - 2: continue
                    if fc == "north" and k != 0: continue
                    if fc == "south" and k != len(cuts[2]) - 2: continue
                    faces.append(fc)
                if not faces: continue
                e2 = dict(e)
                e2["from"] = (cuts[0][i], cuts[1][j], cuts[2][k]); e2["to"] = (cuts[0][i + 1], cuts[1][j + 1], cuts[2][k + 1])
                e2["faces"] = faces
                out.append(e2)
    return out

def _face_uv(e, face):
    """UV [u0, v0, u1, v1] d'une face (boîte déjà découpée)."""
    if face in e["uv"]: return list(e["uv"][face])
    (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
    if e["tile"]:
        ox, oy, oz = (math.floor(x0 / 16 + 1e-9) * 16, math.floor(y0 / 16 + 1e-9) * 16, math.floor(z0 / 16 + 1e-9) * 16)
        lx0, lx1, ly0, ly1, lz0, lz1 = x0 - ox, x1 - ox, y0 - oy, y1 - oy, z0 - oz, z1 - oz
        if face == "north": h = (16 - lx1, 16 - lx0); v = (16 - ly1, 16 - ly0)
        elif face == "south": h = (lx0, lx1); v = (16 - ly1, 16 - ly0)
        elif face == "east": h = (16 - lz1, 16 - lz0); v = (16 - ly1, 16 - ly0)
        elif face == "west": h = (lz0, lz1); v = (16 - ly1, 16 - ly0)
        elif face == "up": h = (lx0, lx1); v = (lz0, lz1)
        else: h = (lx0, lx1); v = (16 - lz1, 16 - lz0)
    elif e["tex"][face].endswith("_log_top"):
        h = (0, 16); v = (0, 16)                 # bout de rondin : les cernes entiers, jamais un coin de la texture
    else:
        w = {"north": x1 - x0, "south": x1 - x0, "east": z1 - z0, "west": z1 - z0, "up": x1 - x0, "down": x1 - x0}[face]
        hgt = (z1 - z0) if face in ("up", "down") else (y1 - y0)
        ou, ov = e["uvo"]
        w, hgt = min(w, 16 - ou), min(hgt, 16 - ov)
        h = (ou, ou + w); v = (ov, ov + hgt)
    r = e["uvrot"].get(face, 0)
    if r in (90, 270):      # la zone de texture est tournée : on échange largeur et hauteur
        wv, hv = h[1] - h[0], v[1] - v[0]
        h = (h[0], h[0] + hv) if h[0] + hv <= 16 else (16 - hv, 16)
        v = (v[0], v[0] + wv) if v[0] + wv <= 16 else (16 - wv, 16)
    return [round(h[0], 3), round(v[0], 3), round(h[1], 3), round(v[1], 3)]

def to_json(model, pivot, display=None, shrink=1.0):
    """Modèle JSON : le point `pivot` du repère de dessin devient le centre (8, 8, 8) du modèle.
    shrink : réduit la géométrie autour du point (24, 0, 24) — pour faire tenir l'icône dans le cube permis."""
    texmap = {}
    def key(t):
        if t not in texmap: texmap[t] = "t%d" % len(texmap)
        return texmap[t]
    sh = [8 - pivot[k] for k in range(3)]
    els = []
    for e0 in model.els:
        for e in _split(e0):
            faces = {}
            for fc in e["faces"]:
                fd = {"uv": _face_uv(e, fc), "texture": "#" + key(e["tex"][fc])}
                if e["uvrot"].get(fc): fd["rotation"] = e["uvrot"][fc]
                faces[fc] = fd
            def pt(q): return [round((24, 0, 24)[k] + (q[k] - (24, 0, 24)[k]) * shrink + sh[k], 3) for k in range(3)]
            el = {"from": pt(e["from"]), "to": pt(e["to"]), "faces": faces}
            if e["rot"]:
                ax, ang, org = e["rot"]
                el["rotation"] = {"angle": ang, "axis": ax, "origin": pt(org)}
            for k in range(3):
                assert -16 <= el["from"][k] <= 32 and -16 <= el["to"][k] <= 32, ("hors limites", e["from"], e["to"], pivot)
            els.append(el)
    out = {"textures": {v: tex_ref(k) for k, v in texmap.items()}, "elements": els}
    out["textures"]["particle"] = out["textures"]["t0"]
    if display: out["display"] = display
    return out

ICON_DISPLAY = {
    "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.24, 0.24, 0.24]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.12, 0.12, 0.12]},
    "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [0.3, 0.3, 0.3]},
    "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.14, 0.14, 0.14]},
    "thirdperson_lefthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.14, 0.14, 0.14]},
    "firstperson_righthand": {"rotation": [0, 225, 0], "translation": [0, 2, 0], "scale": [0.16, 0.16, 0.16]},
    "firstperson_lefthand": {"rotation": [0, 225, 0], "translation": [0, 2, 0], "scale": [0.16, 0.16, 0.16]},
}

# ================================================================ images-clés
def key(dur, t=(0, 0, 0), axis="y", angle=0.0, s=(1, 1, 1)):
    """Cible atteinte au bout de `dur` pas (1 pas = 5 ticks = 0,25 s)."""
    return (int(dur), tuple(map(float, t)), axis, float(angle), tuple(map(float, s)))

def spin(axis, seconds, direction=1):
    """Tour complet en `seconds` secondes : 4 clés de 90°."""
    d = max(1, round(seconds * 20 / TICKS_PER_STEP / 4))
    return [key(d, axis=axis, angle=direction * a) for a in (90, 180, 270, 360)]

def pose_at(keys, step):
    """Pose interpolée (t, axe, angle, s) au pas `step` (flottant) — pour les aperçus."""
    if not keys: return ((0, 0, 0), "y", 0.0, (1, 1, 1))
    total = sum(k[0] for k in keys)
    tt = step % total
    prev = keys[-1]
    for k in keys:
        if tt < k[0]:
            f = tt / k[0]
            pa = prev[3]
            if abs(k[3] - pa) > 180: pa -= 360 * round((pa - k[3]) / 360)
            return (tuple(prev[1][i] + (k[1][i] - prev[1][i]) * f for i in range(3)), k[2], pa + (k[3] - pa) * f,
                    tuple(prev[4][i] + (k[4][i] - prev[4][i]) * f for i in range(3)))
        tt -= k[0]; prev = k
    return (prev[1], prev[2], prev[3], prev[4])

class Part:
    def __init__(self, name, model, pivot, keys=None, bright=False, jitter=0.0):
        self.name, self.model, self.pivot, self.keys = name, model, tuple(map(float, pivot)), keys or []
        self.bright, self.jitter = bright, jitter

class Emitter:
    """Particules : type, position (repère de dessin), nombre, dispersion, vitesse, période et instant (en pas)."""
    def __init__(self, kind, pos, count=1, spread=(0.1, 0.1, 0.1), speed=0.0, period=2, at=0):
        self.kind, self.pos, self.count, self.spread, self.speed, self.period, self.at = kind, pos, count, spread, speed, period, at

class Building:
    def __init__(self, name, base, parts, emitters): self.name, self.base, self.parts, self.emitters = name, base, parts, emitters

# ================================================================ briques de construction
SP, DO, OAK = "mc:spruce_planks", "mc:dark_oak_planks", "mc:oak_planks"
def log(kind="dark_oak", axis="y", stripped=False):
    """Texture de rondin orientée selon son axe."""
    n = ("mc:stripped_" if stripped else "mc:") + kind + "_log"
    if axis == "y": return {"*": n, "up": n + "_top", "down": n + "_top"}
    if axis == "z": return {"*": n, "north": n + "_top", "south": n + "_top"}
    return {"*": n, "east": n + "_top", "west": n + "_top"}
def log_uvrot(axis):
    if axis == "z": return {"east": 90, "west": 90}
    if axis == "x": return {"north": 90, "south": 90, "up": 90, "down": 90}
    return {}

def beam(m, f, t, kind="dark_oak", stripped=False):
    """Poutre en rondin : l'axe est la plus grande dimension."""
    d = [t[k] - f[k] for k in range(3)]
    ax = "xyz"[d.index(max(d))]
    m.box(f, t, log(kind, ax, stripped), uvrot=log_uvrot(ax), tile=(ax == "y"))

def gable_roof(m, x0, x1, z0, z1, y0, y1, tex, ridge="z", thick=2.6, cap=None):
    """Toit à deux pans en gradins. ridge = axe du faîtage."""
    steps = max(1, round((y1 - y0) / 2))
    if ridge == "z":
        half = (x1 - x0) / 2; run = half / steps
        for i in range(steps):
            y = y0 + 2 * i
            m.box((x0 + run * i, y, z0), (x0 + run * (i + 1) + 0.7, y + thick, z1), tex)
            m.box((x1 - run * (i + 1) - 0.7, y, z0), (x1 - run * i, y + thick, z1), tex)
        mid = (x0 + x1) / 2
        m.box((mid - 1.6, y1 - 0.4, z0 - 0.5), (mid + 1.6, y1 + 1.8, z1 + 0.5), cap or tex)
    else:
        half = (z1 - z0) / 2; run = half / steps
        for i in range(steps):
            y = y0 + 2 * i
            m.box((x0, y, z0 + run * i), (x1, y + thick, z0 + run * (i + 1) + 0.7), tex)
            m.box((x0, y, z1 - run * (i + 1) - 0.7), (x1, y + thick, z1 - run * i), tex)
        mid = (z0 + z1) / 2
        m.box((x0 - 0.5, y1 - 0.4, mid - 1.6), (x1 + 0.5, y1 + 1.8, mid + 1.6), cap or tex)

def gable_fill(m, a0, a1, c0, c1, y0, y1, tex, ridge="z"):
    """Pignon plein (triangle en gradins). ridge='z' : le pignon est dans un plan Z (c0..c1 = épaisseur en Z)."""
    steps = max(1, round((y1 - y0) / 2))
    half = (a1 - a0) / 2; run = half / steps
    for i in range(steps):
        y = y0 + 2 * i
        if ridge == "z": m.box((a0 + run * (i + 0.6), y, c0), (a1 - run * (i + 0.6), y + 2, c1), tex)
        else: m.box((c0, y, a0 + run * (i + 0.6)), (c1, y + 2, a1 - run * (i + 0.6)), tex)

def ring(m, c, r_in, r_out, a0, a1, tex, axis="x", n=16):
    """Couronne à n côtés (8 ou 16) autour de l'axe `axis`, entre a0 et a1 le long de cet axe."""
    seg = math.tan(math.pi / n) * r_out
    angles = (0, 45) if n == 8 else (0, 22.5, 45, -22.5)
    for gi, ang in enumerate(angles):
        a0, a1 = a0 + 0.02, a1 - 0.02
        for sgn in (1, -1):
            for flip in (0, 1):
                # segment « haut/bas » (flip=0) ou « avant/arrière » (flip=1)
                lo, hi = (r_in, r_out) if sgn > 0 else (-r_out, -r_in)
                if axis == "x":
                    f = (a0, c[1] + lo, c[2] - seg) if not flip else (a0, c[1] - seg, c[2] + lo)
                    t = (a1, c[1] + hi, c[2] + seg) if not flip else (a1, c[1] + seg, c[2] + hi)
                elif axis == "z":
                    f = (c[0] - seg, c[1] + lo, a0) if not flip else (c[0] + lo, c[1] - seg, a0)
                    t = (c[0] + seg, c[1] + hi, a1) if not flip else (c[0] + hi, c[1] + seg, a1)
                else:
                    f = (c[0] - seg, a0, c[2] + lo) if not flip else (c[0] + lo, a0, c[2] - seg)
                    t = (c[0] + seg, a1, c[2] + hi) if not flip else (c[0] + hi, a1, c[2] + seg)
                m.box(f, t, tex, rot=(axis, ang, c) if ang else None, tile=False)

def disc(m, c, r, a0, a1, tex, axis="x", face_tex=None):
    """Disque plein octogonal (3 boîtes + les mêmes tournées de 45°)."""
    k = r * math.tan(math.pi / 8)
    tx = tex if face_tex is None else None
    for ang in (0, 45):
        a0, a1 = a0 + 0.03, a1 - 0.03
        b0, b1 = a0 + 0.015, a1 - 0.015
        if axis == "x":
            f, t = (a0, c[1] - r, c[2] - k), (a1, c[1] + r, c[2] + k)
            f2, t2 = (b0, c[1] - k, c[2] - r), (b1, c[1] + k, c[2] + r)
        elif axis == "z":
            f, t = (c[0] - r, c[1] - k, a0), (c[0] + r, c[1] + k, a1)
            f2, t2 = (c[0] - k, c[1] - r, b0), (c[0] + k, c[1] + r, b1)
        else:
            f, t = (c[0] - r, a0, c[2] - k), (c[0] + r, a1, c[2] + k)
            f2, t2 = (c[0] - k, b0, c[2] - r), (c[0] + k, b1, c[2] + r)
        m.box(f, t, tex, rot=(axis, ang, c) if ang else None, tile=False)
        m.box(f2, t2, tex, rot=(axis, ang, c) if ang else None, tile=False)

def lantern(base, glow, x, y, z, hang=3):
    """Lanterne suspendue : chaîne et armature (socle), vitre lumineuse (pièce lumineuse). (x, y, z) = centre haut."""
    base.box((x - 0.4, y, z - 0.4), (x + 0.4, y + hang, z + 0.4), "iron_dark", tile=False)
    base.box((x - 1.5, y - 1, z - 1.5), (x + 1.5, y, z + 1.5), "iron_dark", tile=False)
    base.box((x - 1.5, y - 5, z - 1.5), (x + 1.5, y - 4.2, z + 1.5), "iron_dark", tile=False)
    glow.box((x - 1.1, y - 4.2, z - 1.1), (x + 1.1, y - 1, z + 1.1), "glow", tile=False, uvo=(6, 6))

def banner(tex, x, y, z, height=9, sway=10):
    """Mât et fanion qui ondule (pièce animée). (x, y, z) = pied du mât."""
    m = Model()
    m.box((x - 0.6, y, z - 0.6), (x + 0.6, y + height, z + 0.6), DO, tile=False)
    m.box((x - 0.9, y + height, z - 0.9), (x + 0.9, y + height + 1.2, z + 0.9), "mc:gold_block", tile=False, uvo=(4, 4))
    m.box((x - 7, y + height - 5.5, z - 0.2), (x - 0.6, y + height - 0.5, z + 0.2), tex, tile=False)
    m.box((x - 9.5, y + height - 4.5, z - 0.2), (x - 7, y + height - 1.5, z + 0.2), tex, tile=False, uvo=(8, 2))
    keys = [key(4, angle=sway), key(3, angle=-sway * 0.4), key(4, angle=sway * 0.7), key(5, angle=-sway)]
    return Part("fanion", m, (x, y + height / 2, z), keys)

# ================================================================ aperçus (rendu logiciel)
def _quads(model, xform, cam, out):
    """Ajoute à `out` les texels visibles de `model` : (profondeur, polygone, couleur)."""
    right, up, fwd, scale, cx, cy = cam
    for e0 in model.els:
        for e in _split(e0):
            (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
            for fc in e["faces"]:
                if fc == "north": o, du, dv, n = (x1, y1, z0), (x0 - x1, 0, 0), (0, y0 - y1, 0), (0, 0, -1)
                elif fc == "south": o, du, dv, n = (x0, y1, z1), (x1 - x0, 0, 0), (0, y0 - y1, 0), (0, 0, 1)
                elif fc == "east": o, du, dv, n = (x1, y1, z1), (0, 0, z0 - z1), (0, y0 - y1, 0), (1, 0, 0)
                elif fc == "west": o, du, dv, n = (x0, y1, z0), (0, 0, z1 - z0), (0, y0 - y1, 0), (-1, 0, 0)
                elif fc == "up": o, du, dv, n = (x0, y1, z0), (x1 - x0, 0, 0), (0, 0, z1 - z0), (0, 1, 0)
                else: o, du, dv, n = (x0, y0, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), (0, -1, 0)
                wlen = math.sqrt(sum(k * k for k in du)); hlen = math.sqrt(sum(k * k for k in dv))
                if wlen < 1e-6 or hlen < 1e-6: continue
                # transforme les 3 coins (affine)
                def tr(p): return xform(_rot(p, e["rot"]))
                P0 = tr(o); Pu = tr((o[0] + du[0], o[1] + du[1], o[2] + du[2])); Pv = tr((o[0] + dv[0], o[1] + dv[1], o[2] + dv[2]))
                eu = [Pu[k] - P0[k] for k in range(3)]; ev = [Pv[k] - P0[k] for k in range(3)]
                nn = (eu[1] * ev[2] - eu[2] * ev[1], eu[2] * ev[0] - eu[0] * ev[2], eu[0] * ev[1] - eu[1] * ev[0])
                # la normale sortante est ev x eu pour notre ordre de coins ; on la recalcule via n transformée
                N0 = tr((o[0] + n[0], o[1] + n[1], o[2] + n[2])); nrm = [N0[k] - P0[k] for k in range(3)]
                ln = math.sqrt(sum(k * k for k in nrm)) or 1; nrm = [k / ln for k in nrm]
                if sum(nrm[k] * fwd[k] for k in range(3)) > 0.02: continue      # face arrière
                shade = 0.62 * nrm[0] ** 2 + 0.82 * nrm[2] ** 2 + (1.0 if nrm[1] > 0 else 0.5) * nrm[1] ** 2
                uv = _face_uv(e, fc); r = e["uvrot"].get(fc, 0)
                tex = tex_image(e["tex"][fc])
                ns, nt = max(1, math.ceil(wlen - 1e-6)), max(1, math.ceil(hlen - 1e-6))
                for j in range(nt):
                    t0, t1 = j * hlen / nt, min(hlen, (j + 1) * hlen / nt)
                    for i in range(ns):
                        s0, s1 = i * wlen / ns, min(wlen, (i + 1) * wlen / ns)
                        s, t = (s0 + s1) / 2 / wlen, (t0 + t1) / 2 / hlen
                        if r == 90: s, t = t, 1 - s
                        elif r == 180: s, t = 1 - s, 1 - t
                        elif r == 270: s, t = 1 - t, s
                        tx = int(min(15, max(0, uv[0] + s * (uv[2] - uv[0])))); ty = int(min(15, max(0, uv[1] + t * (uv[3] - uv[1]))))
                        c = tex[tx, ty]
                        if c[3] < 128: continue
                        pts = []; depth = 0
                        for (a, b_) in ((s0, t0), (s1, t0), (s1, t1), (s0, t1)):
                            p = [P0[k] + eu[k] * a / wlen + ev[k] * b_ / hlen for k in range(3)]
                            q = (p[0] - 24, p[1] - 22, p[2] - 24)
                            pts.append((cx + scale * sum(q[k] * right[k] for k in range(3)), cy - scale * sum(q[k] * up[k] for k in range(3))))
                            depth += sum(q[k] * fwd[k] for k in range(3))
                        out.append((depth / 4, pts, (int(c[0] * shade), int(c[1] * shade), int(c[2] * shade), 255)))

def camera(azimuth, pitch, scale, size):
    a, p = math.radians(azimuth), math.radians(pitch)
    c = (math.sin(a) * math.cos(p), math.sin(p), -math.cos(a) * math.cos(p))      # position de la caméra (azimut 0 = face)
    f = (-c[0], -c[1], -c[2])
    r = (f[1] * 0 - f[2] * 1, f[2] * 0 - f[0] * 0, f[0] * 1 - f[1] * 0)           # f x haut
    ln = math.sqrt(sum(k * k for k in r)); r = tuple(k / ln for k in r)
    u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    return (r, u, f, scale, size[0] / 2, size[1] * 0.56)

def part_xform(p, step):
    t, ax, ang, s = pose_at(p.keys, step)
    pv = p.pivot
    def xf(q):
        v = [(q[k] - pv[k]) * s[k] + pv[k] for k in range(3)]
        v = _rot(v, (ax, ang, pv))
        return (v[0] + t[0], v[1] + t[1], v[2] + t[2])
    return xf

def render(b, step=0.0, azimuth=-32, pitch=22, scale=9.0, size=(620, 620), bg=(34, 30, 40, 255), base_cache=None):
    cam = camera(azimuth, pitch, scale, size)
    if base_cache is not None and "q" in base_cache: quads = list(base_cache["q"])
    else:
        quads = []
        _quads(b.base, lambda q: q, cam, quads)
        if base_cache is not None: base_cache["q"] = list(quads)
    for p in b.parts: _quads(p.model, part_xform(p, step), cam, quads)
    quads.sort(key=lambda q: -q[0])
    img = Image.new("RGBA", size, bg)
    d = ImageDraw.Draw(img)
    for _, pts, col in quads: d.polygon(pts, fill=col)
    return img

def loop_steps(b, cap=96):
    n = 1
    for p in b.parts:
        if p.keys:
            t = sum(k[0] for k in p.keys)
            n = n * t // math.gcd(n, t)
    return min(n, cap)

def gif(b, path, azimuth=-32, pitch=22, scale=9.0, size=(620, 620), sub=2):
    """GIF animé d'une boucle complète, `sub` images par pas (le jeu, lui, interpole à chaque image)."""
    cache = {}
    n = loop_steps(b)
    frames = [render(b, i / sub, azimuth, pitch, scale, size, base_cache=cache).convert("P", palette=Image.ADAPTIVE, colors=255) for i in range(n * sub)]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=TICKS_PER_STEP * 50 // sub, loop=0, disposal=1)

