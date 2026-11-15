"""Machines médiévales « Royaumes » : textures pixel art, modèles JSON d'objets et aperçus 3D.

Chaque machine = un modèle de base (immobile) + des pièces animées (entités d'affichage séparées).
Les modèles sont des modèles d'objet (papier + custom_model_data) affichés par des item_display,
centrés sur le bloc (0..16 = un bloc). Les pièces animées sont modélisées centrées sur (8, 8, 8) :
le serveur les tourne autour de ce point puis les déplace avec `offset` (en 1/16 de bloc).
"""
import json, math, os, random
import numpy as np
from PIL import Image, ImageDraw

MC = "/home/claude/mcassets/assets/minecraft/textures/"
PACK = "/home/claude/rp/royaumes"
NS = PACK + "/assets/cobbleislands"

# ---------------------------------------------------------------- textures peintes (16x16)
def _img(): return Image.new("RGBA", (16, 16), (0, 0, 0, 0))

def tex_saw():
    im = _img(); d = im.load()
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            tooth = 6.6 + 0.9 * ((a / (2 * math.pi) * 14) % 1.0)
            if r <= tooth:
                if r < 1.4: c = (60, 50, 50)
                elif r < 2.4: c = (120, 70, 40)
                elif r > 6.4: c = (236, 238, 246)
                else:
                    shade = 0.5 + 0.5 * (-dx - dy) / (r + 0.01) * 0.5
                    v = int(150 + 60 * shade)
                    c = (v, v + 4, v + 14)
                    if abs(r - 4.2) < 0.5 and int(a * 3) % 2 == 0: c = (110, 112, 126)
                d[x, y] = c + (255,)
    return im

def tex_wheel():
    im = _img(); d = im.load()
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            r = math.hypot(dx, dy)
            a = (math.degrees(math.atan2(dy, dx)) + 360) % 90
            c = None
            if 5.6 <= r <= 7.6: c = (130, 86, 48) if r > 6.6 else (96, 60, 34)
            elif r < 1.6: c = (70, 70, 84)
            elif r < 5.6 and (a < 12 or a > 78): c = (150, 104, 60)
            if c: d[x, y] = c + (255,)
    for x, y in ((7, 0), (8, 0), (0, 7), (0, 8), (15, 7), (15, 8), (7, 15), (8, 15)):
        d[x, y] = (70, 70, 84, 255)
    return im

def tex_millstone_top():
    im = _img(); d = im.load(); rnd = random.Random(3)
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            r = math.hypot(dx, dy)
            v = 150 + rnd.randint(-10, 10)
            ang = math.degrees(math.atan2(dy, dx)) % 45
            if r < 1.8: v = 60
            elif ang < 6 and r > 2.5: v -= 38
            if r > 7: v -= 25
            d[x, y] = (v, v - 4, v - 12, 255)
    return im

def tex_millstone_side():
    im = _img(); d = im.load(); rnd = random.Random(4)
    for y in range(16):
        for x in range(16):
            v = 140 + rnd.randint(-12, 12) - (20 if y in (0, 15) else 0) + (14 if y == 1 else 0)
            d[x, y] = (v, v - 4, v - 12, 255)
    return im

def tex_sack():
    im = _img(); d = im.load(); rnd = random.Random(5)
    for y in range(16):
        for x in range(16):
            v = 0.85 + 0.15 * ((x + y) % 2) + rnd.uniform(-0.06, 0.06) - 0.18 * abs(x - 7.5) / 8
            d[x, y] = (int(196 * v), int(160 * v), int(110 * v), 255)
    for x in range(16): d[x, 3] = (120, 84, 50, 255); d[x, 4] = (150, 108, 64, 255)
    return im

def tex_sawdust():
    im = _img(); d = im.load(); rnd = random.Random(6)
    for y in range(16):
        for x in range(16):
            v = rnd.choice((0.8, 0.9, 1.0, 1.1))
            d[x, y] = (int(222 * v) if v < 1.1 else 246, int(186 * v), int(124 * v), 255)
    return im

def tex_ore():
    base = Image.open(MC + "block/cobblestone.png").convert("RGBA")
    d = base.load(); rnd = random.Random(7)
    for _ in range(9):
        x, y = rnd.randint(1, 14), rnd.randint(1, 14)
        c = rnd.choice(((216, 175, 147), (252, 222, 80), (40, 40, 44), (226, 128, 84)))
        d[x, y] = c + (255,); d[x + 1, y] = tuple(int(v * .8) for v in c) + (255,)
    return base

def tex_coals():
    im = _img(); d = im.load(); rnd = random.Random(8)
    for y in range(16):
        for x in range(16):
            t = rnd.random()
            c = (40, 26, 26) if t < .3 else (120, 30, 20) if t < .55 else (230, 90, 30) if t < .85 else (255, 200, 90)
            d[x, y] = c + (255,)
    return im

def tex_fire():
    im = _img(); d = im.load(); rnd = random.Random(9)
    for x in range(16):
        h = 8 + int(5 * abs(math.sin(x * 0.9))) + rnd.randint(-1, 2)
        for y in range(16 - h, 16):
            t = (y - (16 - h)) / h
            c = (255, 240, 170) if t > .75 and 5 < x < 11 else (255, 190, 60) if t > .4 else (240, 110, 30)
            if y == 16 - h: c = (200, 60, 20)
            d[x, y] = c + (255,)
    return im

def tex_leather():
    im = _img(); d = im.load(); rnd = random.Random(10)
    for y in range(16):
        for x in range(16):
            v = 0.85 + 0.15 * (1 if y % 4 == 0 else 0) + rnd.uniform(-0.05, 0.05)
            d[x, y] = (int(126 * v), int(76 * v), int(46 * v), 255)
    return im

def tex_hole():
    im = Image.new("RGBA", (16, 16), (16, 12, 14, 255))
    d = im.load()
    for i in range(16): d[i, 0] = (40, 30, 30, 255); d[0, i] = (40, 30, 30, 255)
    return im

def tex_rope():
    im = _img(); d = im.load()
    for y in range(16):
        for x in range(16):
            d[x, y] = ((176, 138, 88) if (x + y) % 4 < 2 else (132, 98, 60)) + (255,)
    return im

def tex_iron_dark():
    im = _img(); d = im.load(); rnd = random.Random(11)
    for y in range(16):
        for x in range(16):
            v = 70 + rnd.randint(-6, 6) + (24 if y == 0 or x == 0 else 0)
            d[x, y] = (v, v, v + 10, 255)
    return im

def tex_ingot_gold():
    return Image.open(MC + "block/gold_block.png").convert("RGBA")

CUSTOM = {"saw": tex_saw, "wheel": tex_wheel, "millstone_top": tex_millstone_top, "millstone_side": tex_millstone_side,
          "sack": tex_sack, "sawdust": tex_sawdust, "ore": tex_ore, "coals": tex_coals, "fire": tex_fire,
          "leather": tex_leather, "hole": tex_hole, "rope": tex_rope, "iron_dark": tex_iron_dark}

def tex_ref(name):
    """'mc:oak_planks' -> minecraft:block/oak_planks ; 'saw' -> cobbleislands:block/machine/saw."""
    if name.startswith("mc:"): return "minecraft:block/" + name[3:]
    return "cobbleislands:block/machine/" + name

def tex_image(name):
    if name.startswith("mc:"):
        im = Image.open(MC + "block/" + name[3:] + ".png").convert("RGBA")
        return im.crop((0, 0, 16, 16))
    return CUSTOM[name]()

# ---------------------------------------------------------------- modèle
FACES = ("north", "south", "east", "west", "up", "down")

class Model:
    def __init__(self, name):
        self.name = name
        self.els = []
    def box(self, f, t, tex, faces=FACES, rot=None, uv=None):
        """tex : nom de texture ou dict face -> texture. rot = (axe, angle, origine)."""
        if isinstance(tex, str): tex = {k: tex for k in FACES}
        else:
            default = tex.get("*")
            tex = {k: tex.get(k, default) for k in FACES}
        self.els.append({"from": list(f), "to": list(t), "tex": tex, "faces": [x for x in faces if tex.get(x)], "rot": rot, "uv": uv or {}})
        return self
    def merged(self, *others):
        m = Model(self.name); m.els = list(self.els)
        for o in others: m.els += o.els
        return m
    def to_json(self, display=True):
        texmap = {}
        def key(t):
            if t not in texmap: texmap[t] = "t%d" % len(texmap)
            return texmap[t]
        els = []
        for e in self.els:
            (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
            def auto(face):
                if face in e["uv"]: return e["uv"][face]
                def c(a, b): return [max(0, min(16, a)), max(0, min(16, b))]
                if face in ("north", "south"):
                    u = c(16 - x1, 16 - x0) if face == "north" else c(x0, x1)
                    v = c(16 - y1, 16 - y0)
                elif face in ("east", "west"):
                    u = c(16 - z1, 16 - z0) if face == "east" else c(z0, z1)
                    v = c(16 - y1, 16 - y0)
                else:
                    u = c(x0, x1); v = c(z0, z1)
                return [u[0], v[0], u[1], v[1]]
            faces = {f: {"uv": auto(f), "texture": "#" + key(e["tex"][f])} for f in e["faces"]}
            el = {"from": [round(v, 3) for v in e["from"]], "to": [round(v, 3) for v in e["to"]], "faces": faces}
            if e["rot"]:
                ax, ang, org = e["rot"]
                el["rotation"] = {"angle": ang, "axis": ax, "origin": list(org)}
            els.append(el)
        out = {"textures": {v: tex_ref(k) for k, v in texmap.items()}, "elements": els}
        out["textures"]["particle"] = out["textures"]["t0"]
        if display:
            out["display"] = {
                "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.625, 0.625, 0.625]},
                "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.25, 0.25, 0.25]},
                "fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]},
                "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.375, 0.375, 0.375]},
                "firstperson_righthand": {"rotation": [0, 45, 0], "translation": [0, 0, 0], "scale": [0.4, 0.4, 0.4]},
                "firstperson_lefthand": {"rotation": [0, 225, 0], "translation": [0, 0, 0], "scale": [0.4, 0.4, 0.4]},
            }
        return out

# ---------------------------------------------------------------- les machines
PL, SP, DO, DOL, SPL = "mc:oak_planks", "mc:spruce_planks", "mc:dark_oak_planks", "mc:dark_oak_log", "mc:spruce_log"
LOG = {"*": "mc:oak_log", "up": "mc:oak_log_top", "down": "mc:oak_log_top"}

def legs(m, h, tex=DOL, inset=1, w=2):
    for x in (inset, 16 - inset - w):
        for z in (inset, 16 - inset - w):
            m.box((x, 0, z), (x + w, h, z + w), {"*": tex, "up": tex + "_top" if tex.endswith("log") else tex, "down": tex + "_top" if tex.endswith("log") else tex})

def sawmill():
    b = Model("scierie_base")
    legs(b, 9)
    for z in (1.5, 13.5):                       # traverses basses
        b.box((3, 3, z), (13, 4.5, z + 1), SP)
    for x in (1.5, 13.5):
        b.box((x, 3, 3), (x + 1, 4.5, 13), SP)
    b.box((2, 4.5, 2), (14, 5, 14), SP)         # étagère
    b.box((3, 5, 3), (7, 6.5, 6), "sawdust")      # tas de sciure en dessous
    # plateau fendu pour la lame
    b.box((0, 9, 0), (16, 11, 7.5), SP)
    b.box((0, 9, 8.5), (16, 11, 16), SP)
    b.box((0, 9, 7.5), (1.5, 11, 8.5), SP); b.box((14.5, 9, 7.5), (16, 11, 8.5), SP)
    # rebords en chêne sombre
    b.box((0, 11, 0), (16, 11.5, 1), DO); b.box((0, 11, 15), (16, 11.5, 16), DO)
    # tronc en cours de découpe
    b.box((9, 11, 5.5), (16, 16, 10.5), LOG)
    b.box((1, 11, 5.5), (6.5, 13, 10.5), {"*": "mc:stripped_oak_log", "up": PL, "down": PL})
    b.box((2, 11, 11.5), (7, 12, 14), "sawdust")
    # manivelle sur le côté
    b.box((16, 8.5, 7), (17, 10.5, 9), "iron_dark")
    b.box((17, 9, 7.5), (17.5, 14, 8.5), SP); b.box((17, 13, 7.5), (19, 14, 8.5), SP)
    blade = Model("scierie_lame").box((2, 2, 7.6), (14, 14, 8.4), {"north": "saw", "south": "saw"})
    return b, [("lame", blade, (0, 2, 0), "spin_z", 0)]

def mill():
    b = Model("moulin_base")
    b.box((1, 0, 1), (15, 7, 15), SP)
    for x in (0, 13):
        for z in (0, 13):
            b.box((x, 0, z), (x + 3, 8, z + 3), {"*": DOL, "up": "mc:dark_oak_log_top", "down": "mc:dark_oak_log_top"})
    b.box((3, 2, 15), (13, 3, 15.5), DO); b.box((3, 5, 15), (13, 6, 15.5), DO)
    b.box((2, 7, 2), (14, 8, 14), "mc:smooth_stone")
    b.box((6.5, 3, 15), (9.5, 5.5, 18), SP)                  # goulotte
    b.box((5.5, 0, 17), (10.5, 4, 21), "sack")               # sac de farine devant
    b.box((6.5, 4, 18), (9.5, 4.8, 20), "rope")
    b.box((0.5, 8, 12.5), (3.5, 12, 15.5), "sack")
    b.box((12.5, 8, 0.5), (15.5, 11, 3.5), {"*": "mc:hay_block_side", "up": "mc:hay_block_top", "down": "mc:hay_block_top"})
    stone = Model("moulin_meule")
    st = {"*": "millstone_side", "up": "millstone_top", "down": "millstone_top"}
    stone.box((3, 6.5, 3), (13, 9.5, 13), st)
    stone.box((3, 6.5, 3), (13, 9.5, 13), st, rot=("y", 45, (8, 8, 8)))
    stone.box((7, 9.5, 7), (9, 15, 9), {"*": SPL, "up": "mc:spruce_log_top"})
    stone.box((1, 13, 7.5), (15, 14, 8.5), DO)
    return b, [("meule", stone, (0, 1.5, 0), "spin_y", 0)]

def mine():
    b = Model("mine_base")
    b.box((0, 0, 0), (16, 3, 16), "mc:cobblestone")
    b.box((5, 2.95, 5), (11, 3.05, 11), {"up": "hole"})
    for (f, t) in (((4, 3, 4), (12, 4, 5)), ((4, 3, 11), (12, 4, 12)), ((4, 3, 5), (5, 4, 11)), ((11, 3, 5), (12, 4, 11))):
        b.box(f, t, SP)
    for x in (2, 12):
        b.box((x, 3, 7), (x + 2, 16, 9), {"*": DOL, "up": "mc:dark_oak_log_top", "down": "mc:dark_oak_log_top"})
        b.box((x + (2 if x == 2 else -3), 3, 7.5), (x + (5 if x == 2 else 0), 4, 8.5), SP)    # jambes de force
    b.box((1, 15, 6.5), (15, 16.5, 9.5), DO)
    b.box((7.8, 3.5, 7.9), (8.2, 6.5, 8.1), "rope")
    # wagonnet de minerai
    b.box((10, 4, 12), (15.5, 7.5, 15.5), "iron_dark")
    b.box((10, 7.5, 12), (15.5, 8, 15.5), SP)
    b.box((10.5, 7.5, 12.5), (15, 8.6, 15), {"*": "ore"})
    for x in (10.5, 13.5):
        for z in (11.5, 15.5):
            b.box((x, 3, z), (x + 1.5, 4.5, z + 0.5), "mc:coal_block")
    b.box((0.5, 3, 12), (4.5, 6, 15.5), {"*": SP, "up": "ore"})
    wheel = Model("mine_roue").box((4, 4, 7.4), (12, 12, 8.6), {"north": "wheel", "south": "wheel"})
    return b, [("roue", wheel, (0, 2.5, 0), "spin_z", 0)]

def forge():
    b = Model("forge_base")
    brick = "mc:stone_bricks"
    b.box((0, 0, 0), (9, 8, 16), brick)                      # foyer en pierre
    b.box((1, 7.5, 5.5), (8, 8.2, 14.5), "coals")
    b.box((0, 8, 14.5), (9, 9, 16), brick); b.box((0, 8, 5), (1, 9, 16), brick); b.box((8, 8, 5), (9, 9, 16), brick)
    b.box((0, 8, 0), (9, 12, 5), "mc:bricks")                # hotte à l'arrière
    b.box((1.5, 12, 0.5), (7.5, 20, 4.5), "mc:bricks")       # cheminée
    b.box((1, 20, 1), (8, 21, 5), "mc:bricks")
    b.box((9, 2, 1), (12, 6, 5), "leather"); b.box((12, 3, 1.5), (15, 5, 4.5), "leather")      # soufflet
    b.box((15, 3.5, 2.5), (16.5, 4.5, 3.5), SP)
    b.box((10, 0, 7), (15, 5, 12), LOG)                       # billot
    b.box((10.5, 5, 8), (14.5, 6, 11), "iron_dark")          # enclume
    b.box((11.5, 6, 8.75), (13.5, 7, 10.25), "iron_dark")
    b.box((9.5, 7, 8), (15.5, 9, 11), {"*": "iron_dark", "up": "mc:anvil_top"})
    b.box((10.5, 0, 13), (15.5, 1, 16), "mc:iron_block")     # lingots
    b.box((11, 1, 13.5), (15, 2, 15.5), "mc:gold_block")
    fire = Model("forge_feu")
    fire.box((4, 6, 8), (12, 14, 8), {"north": "fire", "south": "fire"})
    fire.box((8, 6, 4), (8, 14, 12), {"east": "fire", "west": "fire"})
    hammer = Model("forge_marteau")
    hammer.box((8, 7.5, 7.5), (14.5, 8.5, 8.5), SP)
    hammer.box((14, 6, 7), (17, 10, 9), "iron_dark")
    return b, [("feu", fire, (-3.5, 2, 2), "flicker", 1), ("marteau", hammer, (-3.5, 4.5, 1.5), "swing", 0)]

MACHINES = {"scierie": sawmill, "moulin": mill, "mine": mine, "forge": forge}

# custom_model_data : objet complet 7301+, base 7311+, pièces 7321+ (2 par machine)
def cmd_table():
    t = {}
    for i, name in enumerate(MACHINES):
        t[name] = {"item": 7301 + i, "base": 7311 + i, "parts": [7321 + i * 2, 7322 + i * 2]}
    return t

# ---------------------------------------------------------------- aperçu 3D (rendu logiciel simple)
def _rot(p, rot):
    if not rot: return p
    ax, ang, o = rot
    a = math.radians(ang)
    x, y, z = p[0] - o[0], p[1] - o[1], p[2] - o[2]
    if ax == "y": x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
    elif ax == "x": y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    else: x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return (x + o[0], y + o[1], z + o[2])

def render_preview(models, size=420, yaw=35, pitch=28, scale=13, extra_rot=None):
    """models : liste de (Model, offset (en 1/16), rot_z_deg pour pièces)."""
    quads = []
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    def proj(p):
        x, y, z = p[0] - 8, p[1] - 8, p[2] - 8
        x, z = x * cy - z * sy, x * sy + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        return (size / 2 + x * scale, size * 0.58 - y * scale, z)
    cache = {}
    for (m, off, prot) in models:
        for e in m.els:
            (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
            for f in e["faces"]:
                tn = e["tex"][f]
                if tn not in cache: cache[tn] = tex_image(tn)
                im = cache[tn]
                # coins (u, v) de la face dans l'espace
                if f == "up": P = lambda u, v: (x0 + (x1 - x0) * u, y1, z0 + (z1 - z0) * v); shade = 1.0
                elif f == "down": P = lambda u, v: (x0 + (x1 - x0) * u, y0, z1 - (z1 - z0) * v); shade = 0.5
                elif f == "south": P = lambda u, v: (x0 + (x1 - x0) * u, y1 - (y1 - y0) * v, z1); shade = 0.8
                elif f == "north": P = lambda u, v: (x1 - (x1 - x0) * u, y1 - (y1 - y0) * v, z0); shade = 0.8
                elif f == "east": P = lambda u, v: (x1, y1 - (y1 - y0) * v, z1 - (z1 - z0) * u); shade = 0.6
                else: P = lambda u, v: (x0, y1 - (y1 - y0) * v, z0 + (z1 - z0) * u); shade = 0.6
                # UV automatiques identiques à to_json
                m2 = Model("t"); m2.els = [e]
                face_uv = m2.to_json(False)["elements"][0]["faces"][f]["uv"]
                u0, v0, u1, v1 = face_uv
                nu, nv = max(1, int(round(abs(u1 - u0)))), max(1, int(round(abs(v1 - v0))))
                for j in range(nv):
                    for i in range(nu):
                        tx = int(min(15, (u0 + (u1 - u0) * (i + .5) / nu)))
                        ty = int(min(15, (v0 + (v1 - v0) * (j + .5) / nv)))
                        c = im.getpixel((tx, ty))
                        if c[3] < 128: continue
                        pts3 = [P(i / nu, j / nv), P((i + 1) / nu, j / nv), P((i + 1) / nu, (j + 1) / nv), P(i / nu, (j + 1) / nv)]
                        pts3 = [_rot(q, e["rot"]) for q in pts3]
                        if prot: pts3 = [_rot(q, ("z", prot, (8, 8, 8))) for q in pts3]
                        pts3 = [(q[0] + off[0], q[1] + off[1], q[2] + off[2]) for q in pts3]
                        pts = [proj(q) for q in pts3]
                        # culling
                        ax_, ay_ = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
                        bx_, by_ = pts[3][0] - pts[0][0], pts[3][1] - pts[0][1]
                        if ax_ * by_ - ay_ * bx_ < 0 and f not in ("north", "south", "east", "west") and False: continue
                        depth = sum(q[2] for q in pts) / 4
                        col = tuple(int(c[k] * shade) for k in range(3)) + (255,)
                        quads.append((depth, [(q[0], q[1]) for q in pts], col))
    quads.sort(key=lambda q: q[0])
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for _, pts, col in quads:
        d.polygon(pts, fill=col)
    return img

# ---------------------------------------------------------------- export
def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=1)

def export():
    """Écrit textures et modèles dans le pack ; renvoie la table des custom_model_data."""
    os.makedirs(NS + "/textures/block/machine", exist_ok=True)
    for k, fn in CUSTOM.items(): fn().save(f"{NS}/textures/block/machine/{k}.png")
    table = cmd_table()
    out = {}
    for name, fn in MACHINES.items():
        base, parts = fn()
        ids = table[name]
        full = base
        for (_, pm, off, _, _) in parts:
            moved = Model("x")
            for e in pm.els:
                e2 = dict(e); e2["from"] = [e["from"][k] + off[k] for k in range(3)]; e2["to"] = [e["to"][k] + off[k] for k in range(3)]
                if e["rot"]:
                    ax, ang, o = e["rot"]; e2["rot"] = (ax, ang, [o[k] + off[k] for k in range(3)])
                moved.els.append(e2)
            full = full.merged(moved)
        write(f"{NS}/models/item/machine/{name}.json", full.to_json(True))
        write(f"{NS}/models/item/machine/{name}_base.json", base.to_json(False))
        for i, (pn, pm, off, anim, bright) in enumerate(parts):
            write(f"{NS}/models/item/machine/{name}_{pn}.json", pm.to_json(False))
        out[name] = {"cmd": ids, "parts": [{"name": pn, "offset": off, "anim": anim, "bright": bright} for (pn, _, off, anim, bright) in parts]}
    return out

def model_overrides(table):
    """Paires (custom_model_data, modèle) à ajouter au papier."""
    res = []
    for name, info in table.items():
        res.append((info["cmd"]["item"], f"cobbleislands:item/machine/{name}"))
        res.append((info["cmd"]["base"], f"cobbleislands:item/machine/{name}_base"))
        for i, p in enumerate(info["parts"]):
            res.append((info["cmd"]["parts"][i], f"cobbleislands:item/machine/{name}_{p['name']}"))
    return res

def previews(path):
    tiles = []
    for name, fn in MACHINES.items():
        base, parts = fn()
        models = [(base, (0, 0, 0), 0)] + [(pm, off, 20 if anim.startswith("spin_z") else 0) for (_, pm, off, anim, _) in parts]
        tiles.append(render_preview(models))
    sheet = Image.new("RGBA", (420 * len(tiles), 420), (44, 36, 46, 255))
    for i, t in enumerate(tiles): sheet.alpha_composite(t, (i * 420, 0))
    sheet.save(path)

if __name__ == "__main__":
    previews("/home/claude/rp/machines_preview.png")
    print("ok")
