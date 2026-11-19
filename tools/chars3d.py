"""Niches HD : vrais skins posés dans des dioramas Minecraft (blocs vanilla), objets vanilla tenus comme en jeu."""
import math, os, sys
import numpy as np
from PIL import Image
import skin_render as SR
import scene3d as S
from scene3d import T, box, face, World

HERE = os.path.dirname(os.path.abspath(__file__))
NW, NH = 174, 262            # niche HD (2x la niche du GUI)

# ---------------------------------------------------------------- personnage
def to_scene(faces, color_glow=()):
    out = []
    for f in faces:
        if "tex" in f and f["tex"] is not None and not isinstance(f["tex"], np.ndarray):
            img, U, V, tw, th = f["tex"]
            out.append(face(f["o"], f["u"], f["v"], f["n"], tex=img, uv=(U, V, tw, th), char=True))
        else:
            g = 0.5 if f.get("glow") else 0.0
            out.append(face(f["o"], f["u"], f["v"], f["n"], color=f["color"], char=True, glow=g))
    return out

def held_mc(spr, hands, side="r", grip=(4, 11), tilt=0.0, roll=0.0, px=0.72, glow=(), spin=0.0):
    """Objet tenu comme en jeu (3e personne) : sprite dans le plan avant/haut du bras, manche dans le poing."""
    H = spr.height
    F = SR.sprite_faces(spr, px, thick=px, glow=glow)
    gx, gy = (grip[0] + 0.5) * px, (H - grip[1] - 0.5) * px
    R = SR.rot_x(math.radians(-tilt)) @ SR.rot_z(math.radians(roll)) @ SR.rot_y(math.radians(-90 + spin))
    hp = hands[side + "pos"] + np.array([0, -0.5, 0.6])
    X = SR.Xf(R, hp - R @ np.array([gx, gy, 0.0]))
    return SR.xform(F, hands[side] @ X)

def item(name, flip=False):
    im = Image.open(f"{S.MC}/item/{name}.png").convert("RGBA")
    if flip:                                                     # symétrie selon la diagonale du manche : tranchant vers l'avant
        a = np.array(im); im = Image.fromarray(a[::-1, ::-1].transpose(1, 0, 2).copy())
    return im

def scepter():
    """Sceptre d'or (objet original, dessiné en diagonale comme les outils vanilla)."""
    im = Image.new("RGBA", (16, 16)); P = im.load()
    Y, y, g, R, r, W = (250, 206, 80), (200, 150, 40), (120, 80, 20), (210, 30, 60), (140, 10, 40), (255, 200, 210)
    for k in range(10):
        i, j = 2 + k, 13 - k
        P[i, j] = Y + (255,); P[i + 1, j] = y + (255,); P[i, j + 1] = g + (255,)
    for (i, j, c) in ((11, 3, R), (12, 3, R), (13, 3, R), (11, 4, R), (12, 4, r), (13, 4, R), (12, 2, R), (11, 2, R), (13, 2, Y),
                      (12, 1, Y), (10, 3, Y), (14, 3, Y), (12, 5, Y), (11, 1, Y), (13, 1, Y), (12, 0, Y), (12, 3, W), (10, 2, Y), (14, 4, Y)):
        P[i, j] = c + (255,)
    for (i, j) in ((5, 10), (4, 11), (6, 10), (5, 11)): P[i, j] = Y + (255,)
    P[1, 14] = Y + (255,); P[2, 14] = y + (255,)
    return im

GLOW_RED = ((210, 30, 60), (140, 10, 40), (255, 200, 210))

CHARS = {
    "fermier": dict(skin="skin_fermier.png", pose={"head": (-6, 0, -10), "body": (0, 0, -6), "rarm": (30, -32, -70), "larm": (-6, 10, 0),
                                                   "rleg": (6, -3, 0), "lleg": (-8, 3, 0)},
                    tool=lambda: (item("iron_hoe", flip=True), dict(grip=(3, 12), tilt=-30))),
    "roi": dict(skin="skin_roi.png", pose={"head": (-4, 0, 14), "body": (0, 0, 6), "rarm": (12, -18, 0), "larm": (-4, 7, 0),
                                            "rleg": (4, -3, 0), "lleg": (-6, 3, 0)},
                tool=lambda: (scepter(), dict(grip=(3, 12), tilt=-6, spin=75, roll=40, glow=GLOW_RED)), turn=6),
    "bucheron": dict(skin="skin_bucheron.png", pose={"head": (-6, 0, -12), "body": (0, 0, -8), "rarm": (30, -35, -70), "larm": (-10, 10, 0),
                                                     "rleg": (9, -3, 0), "lleg": (-10, 4, 0)},
                     tool=lambda: (item("iron_axe", flip=True), dict(grip=(3, 12), tilt=-30))),
    "mineur": dict(skin="skin_mineur.png", pose={"head": (6, 0, 10), "body": (0, 0, 6), "rarm": (34, -32, -70), "larm": (-4, 10, 0),
                                                 "rleg": (6, -2, 0), "lleg": (-7, 3, 0)},
                   tool=lambda: (item("iron_pickaxe"), dict(grip=(3, 12), tilt=-30))),
    "forgeron": dict(skin="skin_forgeron.png", pose={"head": (8, 0, -8), "body": (0, 0, -6), "rarm": (40, -30, -70), "larm": (-6, 10, 0),
                                                     "rleg": (5, -3, 0), "lleg": (-6, 3, 0)},
                     tool=lambda: (item("mace"), dict(grip=(3, 12), tilt=-30))),
}

def character(who):
    c = CHARS[who]
    sk = Image.open(os.path.join(HERE, "renders", c["skin"]))
    f, h = SR.player(sk, c["pose"])
    spr, kw = c["tool"]()
    f += held_mc(spr, h, "r", **kw)
    return to_scene(f)

# ---------------------------------------------------------------- éléments de décor
def cross(x, y, z, tex, s=16):
    """Plante en croix (herbe, fleurs) ; x,y,z en unités."""
    h = s / 2 * 1.41
    a = face((x - s / 2 * .7, y + s, z - s / 2 * .7), (s * .7 * 2 / 1.41 * 1.0, 0, s * .7 * 2 / 1.41), (0, -s, 0), (-.7, 0, .7), tex=tex, uv=(0, 0, 16, 16), two=True, cast=False)
    b = face((x - s / 2 * .7, y + s, z + s / 2 * .7), (s * .7 * 2 / 1.41, 0, -s * .7 * 2 / 1.41), (0, -s, 0), (.7, 0, .7), tex=tex, uv=(0, 0, 16, 16), two=True, cast=False)
    return [a, b]

def lantern(x, y, z, hanging=True):
    tx = T("lantern")
    F = box((x - 3, y, z - 3), (x + 3, y + 7, z + 3), {"side": tx, "top": tx, "bottom": tx}, glow=0.9, uvo=(x - 8, y - (0 if not hanging else 1), z - 8))
    for f in F:                                    # UV du modèle vanilla de lanterne
        if f["n"][1] == 0: f["uv"] = (0, 2, 6, 7)
        else: f["uv"] = (0, 9, 6, 6)
    F += box((x - 2, y + 7, z - 2), (x + 2, y + 9, z + 2), tx, glow=0.5)
    for f in F[-6:]:
        f["uv"] = (1, 10, 4, 2) if f["n"][1] == 0 else (1, 10, 4, 4)
    return F

def chain(x, y0, y1, z):
    tx = T("chain")
    a = face((x - 1.5, y1, z - 1.5), (3, 0, 3), (0, -(y1 - y0), 0), (-.7, 0, .7), tex=tx, uv=(0, 0, 3, 16), two=True)
    b = face((x - 1.5, y1, z + 1.5), (3, 0, -3), (0, -(y1 - y0), 0), (.7, 0, .7), tex=tx, uv=(3, 0, 3, 16), two=True)
    return [a, b]

def torch_wall(x, y, z, facing=1):
    """Torche murale simplifiée : bâton + flamme lumineuse."""
    t = T("torch")
    F = box((x - 1, y, z - 1), (x + 1, y + 10, z + 1), t, uvo=(x - 7, y, z - 7))
    for f in F: f["uv"] = (7, 6, 2, 10) if f["n"][1] == 0 else (7, 6, 2, 2)
    F += box((x - 1.2, y + 8, z - 1.2), (x + 1.2, y + 10.5, z + 1.2), t, glow=1.0, uvo=(x - 7, y, z - 7))
    for f in F[-6:]: f["uv"] = (7, 5, 2, 3)
    return F

def log_x(x, y, z, top="oak_log_top", side="oak_log"):
    """Bûche couchée le long de x."""
    s = T(side)
    rot = np.rot90(s).copy()
    return box((x, y, z), (x + 16, y + 16, z + 16), {"west": T(top), "east": T(top), "top": rot, "bottom": rot, "south": rot, "north": rot})

def particles(n, box_, colors, size=(0.6, 1.4), glow=0.8, seed=1):
    rnd = np.random.RandomState(seed); F = []
    for _ in range(n):
        x, y, z = (rnd.uniform(box_[0][i], box_[1][i]) for i in range(3)); sz = rnd.uniform(*size)
        c = colors[rnd.randint(len(colors))]
        F.append(face((x - sz / 2, y + sz / 2, z), (sz, 0, 0), (0, -sz, 0), (0, 0, 1), color=c, glow=glow, cast=False, two=True))
    return F

# ---------------------------------------------------------------- scènes
def leaves_ball(W, cx, cy, cz, r=2, lo=None):
    lv = S.tinted("oak_leaves", S.FOLIAGE)
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            for dy in range(-1, 2):
                if abs(dx) + abs(dz) + abs(dy) > r + 1: continue
                if lo is not None and cy + dy < lo: continue
                if (dx * 7 + dz * 3 + dy * 5) % 11 == 0: continue
                if (cx + dx, cy + dy, cz + dz) not in W.blocks: W.set(cx + dx, cy + dy, cz + dz, lv, opaque=False)

def tree(W, x, z, h, lo=None):
    for y in range(h): W.set(x, y, z, {"side": T("oak_log"), "top": T("oak_log_top")})
    leaves_ball(W, x, h - 1, z, 2, lo); leaves_ball(W, x, h + 1, z, 1, lo)

def scene_bucheron(W):
    g = {"top": S.tinted("grass_block_top", S.GRASS), "side": T("grass_block_side"), "bottom": T("dirt")}
    for x in range(-9, 10):
        for z in range(-16, 5): W.set(x, -1, z, g)
    for (tx, tz, h) in ((-3, -2, 6), (3, -4, 6), (-1, -9, 6), (4, -10, 7), (-5, -8, 7), (1, -14, 7), (-3, -15, 6), (6, -15, 7)):
        tree(W, tx, tz, h, lo=3 if tz > -6 else None)
    for (tx, tz, h) in ((-7, -20, 7), (-2, -22, 8), (3, -21, 7), (8, -23, 8), (5, -18, 6), (-9, -16, 6)):
        tree(W, tx, tz, h)
    for x in range(-12, 13):
        for z in range(-26, -16): W.set(x, -1, z, g)
    W.add(particles(60, ((-60, 4, -120), (60, 70, -10)), [(255, 240, 160), (230, 255, 170)], (0.4, 0.9), 0.6, 5))
    W.set(1, 0, -1, {"side": T("oak_log"), "top": T("oak_log_top")})                       # souche
    W.add(log_x(-56, 0, -60) + log_x(-40, 0, -60) + log_x(-48, 16, -60))                  # tas de bûches
    W.add(log_x(28, 0, -40))
    rnd = np.random.RandomState(4)
    for k in range(110):
        x, z = rnd.uniform(-120, 120), rnd.uniform(-240, 40)
        if z > -14 and abs(x) < 26: continue
        tex = S.tinted("short_grass", S.GRASS) if rnd.rand() < .65 else T(rnd.choice(["poppy", "dandelion", "oxeye_daisy", "cornflower", "allium"]))
        W.add(cross(x, 0, z, tex, 16))
    return dict(sun_dir=(-0.45, 0.85, -0.6), sun_col=(1.0, 0.85, 0.6), sun_k=1.1, amb_sky=(0.44, 0.52, 0.64), amb_gnd=(0.24, 0.26, 0.16),
                fog_col=(0.66, 0.74, 0.76), fog=(240, 800), sky=S.sky_gradient((0.34, 0.55, 0.86), (0.95, 0.85, 0.66), (0.7, 0.3, 0.2, (0.45, 0.35, 0.2))),
                rim_col=(1.0, 0.8, 0.5), rim_k=0.5, dof=(130, 2), char_light=1.15, rays=(0.55, "sun", 0.85))

def scene_roi(W):
    floor = T("polished_andesite"); wall = T("stone_bricks"); gold = T("gold_block")
    for x in range(-8, 9):
        for z in range(-12, 5):
            W.set(x, -1, z, T("polished_blackstone") if (x + z) % 2 else floor)
    for z in range(-12, 5): W.add(box((-12, 0, z * 16), (12, 1, z * 16 + 16), S.tinted("red_wool", (120, 92, 92)), cast=False))
    for x in range(-8, 9):
        for y in range(0, 10): W.set(x, y, -10, T("chiseled_stone_bricks") if y in (3, 7) and x % 2 == 0 else wall)
    for x in (-1, 0, 1):
        for y in (6, 7, 8): W.blocks.pop((x, y, -10), None)
    for x in (-2, 2):
        for y in (6, 7, 8): W.set(x, y, -10, T("chiseled_stone_bricks"))
    for x in (-1, 0, 1):
        W.set(x, 9, -10, T("chiseled_stone_bricks"))
        W.add([face((x * 16, 144, -152), (16, 0, 0), (0, -48, 0), (0, 0, 1), tex=T("iron_bars"), uv=(0, 0, 16, 16), cast=True, two=True)])
    for z in range(-12, 5):
        W.add(box((-13, 0, z * 16), (-12, 1.2, z * 16 + 16), gold, cast=False)); W.add(box((12, 0, z * 16), (13, 1.2, z * 16 + 16), gold, cast=False))
    W.add(particles(30, ((-40, 10, -140), (40, 140, -40)), [(255, 200, 120), (240, 170, 90)], (0.4, 0.8), 0.3, 3))
    for px_ in (-3, 3):
        for y in range(0, 9): W.set(px_, y, -3, {"side": T("quartz_pillar"), "top": T("quartz_pillar_top")})
        W.set(px_, 9, -3, gold)
    for px_ in (-3, 3):
        for y in range(0, 9): W.set(px_, y, -7, {"side": T("quartz_pillar"), "top": T("quartz_pillar_top")})
    # trône
    dk = T("dark_oak_planks")
    W.add(box((-26, 0, -100), (26, 14, -76), dk))
    W.add(box((-22, 14, -100), (22, 70, -92), dk))
    W.add(box((-16, 18, -92), (16, 64, -91.2), T("red_wool")))
    W.add(box((-17, 17, -92), (17, 18, -91), gold)); W.add(box((-17, 64, -92), (17, 65, -91), gold))
    W.add(box((-28, 14, -98), (-22, 30, -76), gold)); W.add(box((22, 14, -98), (28, 30, -76), gold))
    W.add(box((-26, 70, -100), (26, 76, -90), gold)); W.add(box((-6, 76, -98), (6, 88, -92), gold))
    W.add(box((-3, 80, -92.6), (3, 86, -92.2), T("redstone_block"), glow=0.6))
    for x in (-44, 44):                                            # bannières
        W.add(box((x - 7, 50, -143.4), (x + 7, 138, -142.8), T("red_wool")))
        W.add(box((x - 8, 134, -143.6), (x + 8, 140, -142), gold))
        W.add(box((x - 3, 84, -142.8), (x + 3, 96, -142.4), gold))
        W.add(torch_wall(x + (24 if x > 0 else -24), 70, -142))
    for x in (-34, 34):
        W.add(lantern(x, 50, -30)); W.add(chain(x, 59, 160, -30))
    lights = [((-68, 80, -140), (1.6, 0.9, 0.4), 60), ((68, 80, -140), (1.6, 0.9, 0.4), 60),
              ((-34, 53, -30), (0.8, 0.5, 0.25), 30), ((34, 53, -30), (0.8, 0.5, 0.25), 30), ((0, 60, -70), (0.7, 0.4, 0.2), 50)]
    return dict(sun_dir=(0.35, 0.85, 0.7), sun_col=(1.0, 0.86, 0.7), sun_k=0.45, amb_sky=(0.24, 0.21, 0.27), amb_gnd=(0.16, 0.11, 0.1),
                lights=lights, fog_col=(0.08, 0.05, 0.07), fog=(200, 520), rim_col=(1.0, 0.75, 0.4), rim_k=0.5, dof=(120, 2), char_light=1.05, bloom=0.12,
                sky=S.sky_gradient((1.3, 1.15, 0.85), (1.2, 0.95, 0.6)), rays=(0.5, (0, 120, -160), 0.8))

def scene_forgeron(W):
    for x in range(-8, 9):
        for z in range(-12, 5): W.set(x, -1, z, T("cobblestone") if (x * 3 + z) % 4 else T("mossy_cobblestone"))
    for x in range(-8, 9):
        for y in range(0, 10): W.set(x, y, -7, T("bricks") if y > 2 else T("stone_bricks"))
    # foyer à droite
    for x in (1, 2, 3, 4): W.set(x, 0, -6, T("stone_bricks")); W.set(x, 3, -6, T("stone_bricks")); W.set(x, 4, -6, T("stone_bricks"))
    for y in (1, 2): W.set(1, y, -6, T("stone_bricks")); W.set(4, y, -6, T("stone_bricks"))
    for y in range(5, 10):
        for x in (2, 3): W.set(x, y, -6, T("bricks"))
    W.add(box((32, 16, -96), (64, 17, -81), T("lava_still"), glow=1.2))
    W.add([face((32, 46, -88), (32, 0, 0), (0, -29, 0), (0, 0, 1), tex=T("fire_0"), glow=1.3, cast=False)])
    W.set(-3, 0, -6, {"south": T("blast_furnace_front_on"), "side": T("blast_furnace_side"), "top": T("blast_furnace_top")})
    W.set(-3, 1, -6, {"side": T("barrel_side"), "top": T("barrel_top")})
    W.set(-4, 0, -6, {"side": T("barrel_side"), "top": T("barrel_top")})
    W.set(-2, 0, -4, {"side": T("smithing_table_side"), "south": T("smithing_table_front"), "top": T("smithing_table_top"), "bottom": T("smithing_table_bottom")})
    an = {"side": T("anvil"), "top": T("anvil_top")}
    ax, az = 30, -14
    W.add(box((ax - 6, 0, az - 6), (ax + 6, 4, az + 6), an)); W.add(box((ax - 4, 4, az - 4), (ax + 4, 5, az + 4), an))
    W.add(box((ax - 3, 5, az - 3), (ax + 3, 10, az + 3), an)); W.add(box((ax - 8, 10, az - 5), (ax + 8, 16, az + 5), an))
    for x in (-26, 22): W.add(chain(x, 44, 160, -20)); W.add(lantern(x, 35, -20))
    W.add(particles(55, ((20, 18, -90), (70, 90, -60)), [(255, 170, 60), (255, 120, 30), (255, 220, 120)], (0.5, 1.1), 1.0, 9))
    W.add(particles(25, ((14, 8, -30), (46, 30, -6)), [(255, 170, 60), (255, 210, 110)], (0.4, 0.8), 1.0, 11))
    lights = [((48, 26, -86), (3.0, 1.2, 0.4), 80), ((-48, 10, -92), (1.6, 0.7, 0.25), 45),
              ((22, 38, -20), (0.9, 0.6, 0.3), 35), ((-26, 38, -20), (0.9, 0.6, 0.3), 35)]
    return dict(sun_dir=(0.4, 0.8, 0.6), sun_col=(0.7, 0.6, 0.55), sun_k=0.35, amb_sky=(0.2, 0.16, 0.18), amb_gnd=(0.14, 0.09, 0.07),
                lights=lights, fog_col=(0.1, 0.05, 0.04), fog=(180, 480), rim_col=(1.0, 0.55, 0.25), rim_k=0.75, dof=(120, 2), char_light=1.15, rays=(0.35, (48, 30, -88), 0.85))

def scene_mineur(W):
    rnd = np.random.RandomState(7)
    ores = ["iron_ore", "coal_ore", "gold_ore", "copper_ore", "redstone_ore", "diamond_ore", "lapis_ore"]
    def rock():
        r = rnd.rand()
        return T(rnd.choice(ores)) if r < .15 else T("stone") if r < .62 else T("andesite") if r < .76 else T("tuff") if r < .88 else T("cobblestone")
    for x in range(-8, 9):
        for z in range(-20, 5): W.set(x, -1, z, T("stone") if rnd.rand() < .7 else T("gravel"))
    for z in range(-20, 5):
        for y in range(0, 6):
            for x in (-3, 3): W.set(x + (1 if x > 0 and z % 3 == 0 else 0) - (1 if x < 0 and z % 4 == 1 else 0), y, z, rock())
        for x in range(-3, 4): W.set(x, 4 + (0 if (x + z) % 4 else 1), z, T("stone") if rnd.rand() < .6 else T("andesite") if rnd.rand() < .5 else T("tuff"))
    W.set(0, 0, -20, rock()); W.set(-1, 0, -20, rock()); W.set(1, 0, -20, rock())
    for z in range(-20, 5): W.add([face((-8, 0.3, z * 16), (16, 0, 0), (0, 0, 16), (0, 1, 0), tex=T("rail"), cast=False)])
    for z in (2, -5, -12):
        for y in range(0, 4):
            W.add(box((-38, y * 16, z * 16 + 4), (-30, y * 16 + 16, z * 16 + 12), {"side": T("oak_log"), "top": T("oak_log_top")}))
            W.add(box((30, y * 16, z * 16 + 4), (38, y * 16 + 16, z * 16 + 12), {"side": T("oak_log"), "top": T("oak_log_top")}))
        W.add(box((-38, 64, z * 16 + 4), (38, 72, z * 16 + 12), T("oak_planks")))
    W.add(lantern(-22, 44, -72)); W.add(chain(-22, 53, 64, -72))
    W.add(lantern(22, 44, 40)); W.add(chain(22, 53, 64, 40))
    W.add(lantern(14, 44, -184)); W.add(chain(14, 53, 64, -184))
    W.add(particles(60, ((-40, 6, -200), (40, 60, -20)), [(255, 220, 160), (200, 190, 255)], (0.4, 0.8), 0.45, 13))
    W.set(-2, 0, -2, {"side": T("barrel_side"), "top": T("barrel_top_open")})
    W.set(2, 0, -6, {"side": T("barrel_side"), "top": T("barrel_top")})
    for (x, y, z) in ((-3, 2, -9), (3, 1, -13), (-3, 3, -3), (3, 3, -17)): W.set(x, y, z, T("amethyst_block"), glow=0.35)
    lights = [((-22, 46, -72), (1.6, 1.0, 0.5), 60), ((22, 46, 40), (1.2, 0.8, 0.4), 50), ((14, 46, -184), (1.4, 0.9, 0.45), 60),
              ((-40, 40, -144), (0.6, 0.4, 1.2), 50), ((40, 30, -208), (0.6, 0.4, 1.2), 50)]
    return dict(sun_dir=(0.3, 0.9, 0.5), sun_col=(0.5, 0.55, 0.7), sun_k=0.25, amb_sky=(0.15, 0.16, 0.21), amb_gnd=(0.1, 0.1, 0.12),
                lights=lights, fog_col=(0.03, 0.03, 0.05), fog=(160, 420), rim_col=(0.6, 0.7, 1.0), rim_k=0.6, dof=(120, 2), char_light=1.3, rays=(0.3, (-22, 47, -72), 0.8))

def scene_fermier(W):
    g = {"top": S.tinted("grass_block_top", S.GRASS), "side": T("grass_block_side"), "bottom": T("dirt")}
    fl = {"top": T("farmland_moist"), "side": T("dirt"), "bottom": T("dirt")}
    for x in range(-12, 13):
        for z in range(-30, 5):
            if z <= -3 and abs(x) >= 1 and x % 5 != 0: W.set(x, -1, z, fl)
            elif z <= -3 and x % 5 == 0 and abs(x) >= 1: W.set(x, -1, z, {"top": S.tinted("water_still", (70, 120, 220)), "side": T("dirt")})
            else: W.set(x, -1, z, {"top": T("dirt_path_top"), "side": T("dirt_path_side"), "bottom": T("dirt")} if x == 0 else g)
    rnd = np.random.RandomState(3)
    for x in range(-12, 13):
        for z in range(-30, -2):
            if x == 0 or x % 5 == 0 or (x > 2 and z > -17 and x < 9): continue
            crop = "wheat_stage7" if (x // 5) % 2 == 0 else ("carrots_stage3" if x < 0 else "potatoes_stage3")
            W.add(cross(x * 16 + 8, -1, z * 16 + 8, T(crop), 16))
    for (x, y, z) in ((-3, 0, -4), (-3, 1, -4), (-4, 0, -4), (-4, 0, -5), (2, 0, -7)):     # bottes de foin
        W.set(x, y, z, {"side": T("hay_block_side"), "top": T("hay_block_top")})
    # grange sur le côté, au fond
    for x in range(3, 9):
        for y in range(0, 4): W.set(x, y, -12, T("stripped_spruce_log") if x in (3, 8) else T("spruce_planks"))
    for i, y in enumerate(range(4, 7)):
        for x in range(3 + i, 9 - i): W.set(x, y, -12, T("dark_oak_planks"))
    for y in (0, 1):
        for x in (5, 6): W.blocks.pop((x, y, -12), None)
    for z in range(-16, -12):
        for x in range(3, 9):
            for y in range(0, 4): W.set(x, y, z, T("spruce_planks"))
    W.add(particles(40, ((-80, 4, -200), (80, 60, -20)), [(255, 230, 150), (255, 250, 200)], (0.4, 0.8), 0.5, 21))
    return dict(sun_dir=(-0.6, 0.5, -0.6), sun_col=(1.0, 0.72, 0.45), sun_k=1.15, amb_sky=(0.42, 0.42, 0.55), amb_gnd=(0.26, 0.22, 0.14),
                fog_col=(0.95, 0.72, 0.52), fog=(260, 900), sky=S.sky_gradient((0.32, 0.42, 0.75), (1.0, 0.68, 0.42), (0.68, 0.42, 0.28, (0.9, 0.55, 0.25))),
                rim_col=(1.0, 0.7, 0.4), rim_k=0.6, dof=(130, 2), char_light=1.15, rays=(0.55, "sun", 0.85))

SCENES = {"fermier": scene_fermier, "roi": scene_roi, "bucheron": scene_bucheron, "forgeron": scene_forgeron, "mineur": scene_mineur}

def render(who, ss=3, turn=28, dist=74, fov=40):
    W = World()
    params = SCENES[who](W)
    turn = CHARS[who].get("turn", turn)
    X = SR.pivot((0, 0, 0), SR.rot_y(math.radians(turn)))
    ch = character(who)
    for f in ch: f["o"] = X.ap(f["o"]); f["u"] = X.R @ f["u"]; f["v"] = X.R @ f["v"]; f["n"] = X.R @ f["n"]
    faces = W.faces() + ch
    cam = S.Cam((0, 23, dist), (0, 17.5, 0), fov=fov, W=NW * ss, H=NH * ss)
    params.setdefault("bloom", 0.15); params["dof"] = (0, 0)
    if params.get("rays"):
        k_, src, thr = params["rays"]
        if src == "sun": sx, sy = (0.25, 0.52) if who == "fermier" else (0.7, 0.3)
        else:
            x, y, z = cam.project(np.array(src, float)); sx, sy = x / cam.W, y / cam.H
        params["rays"] = (k_, (sx, sy), thr)
    im = S.shade(faces, cam, **params)
    im = im.resize((NW, NH), Image.BOX)
    from PIL import ImageFilter
    return im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))

if __name__ == "__main__":
    for n in (sys.argv[1:] or SCENES):
        render(n).save(f"/home/claude/rp/n_{n}.png")

# ================================================================ tableaux « stock » (bandeau 88x25 → HD 176x50)
SW, SH = 176, 50

def item_at(name, x, y, z, yaw=0, lean=70, px=0.9, kind="item", glow=()):
    """Objet vanilla posé : sprite extrudé, incliné de `lean` degrés depuis le sol, tourné de `yaw`."""
    spr = Image.open(f"{S.MC}/{kind}/{name}.png").convert("RGBA").crop((0, 0, 16, 16))
    F = SR.sprite_faces(spr, px, thick=px, glow=glow)
    R = SR.rot_y(math.radians(yaw)) @ SR.rot_x(math.radians(-(90 - lean)))
    X = SR.Xf(R, np.array([x, y, z]) - R @ np.array([8 * px, 0, 0]))
    out = []
    for f in SR.xform(F, X):
        out.append(face(f["o"], f["u"], f["v"], f["n"], color=f["color"], glow=0.6 if f.get("glow") else 0.0))
    return out

def log_z(x, y, z, kind="oak"):
    """Rondin couché vers la caméra : on voit les cernes."""
    s = T(f"{kind}_log"); rot = np.rot90(s).copy()
    return box((x, y, z), (x + 16, y + 16, z + 16), {"south": T(f"{kind}_log_top"), "north": T(f"{kind}_log_top"), "top": s, "bottom": s, "east": rot, "west": rot})

def stock_scierie(W):
    for (i, n) in enumerate((3, 2)):                                        # pile de rondins (blocs entiers)
        for k in range(n):
            W.add(log_z(-72 + k * 16 + i * 8, i * 16, -28, "oak"))
    for (x, kinds) in ((-16, ("oak_planks", "spruce_planks")), (0, ("birch_planks",)), (16, ("dark_oak_planks", "oak_planks"))):
        for j, k in enumerate(kinds):
            W.add(box((x, j * 16, -28), (x + 16, j * 16 + 16, -12), T(k)))
    W.add(box((38, 0, -20), (54, 16, -4), {"side": T("oak_log"), "top": T("oak_log_top")}))
    W.add(item_at("iron_axe", 40, 15, -10, yaw=0, lean=80, px=1.1))
    W.add(box((56, 0, -32), (72, 16, -16), {"side": T("barrel_side"), "top": T("barrel_top")}))
    W.add(item_at("stick", -30, 0, 4, yaw=20, lean=8, px=0.9)); W.add(item_at("stick", 20, 0, 6, yaw=-30, lean=8, px=0.9))
    return dict(sun_dir=(-0.4, 0.8, 0.6), sun_col=(1.0, 0.85, 0.65), sun_k=0.8, amb_sky=(0.36, 0.32, 0.34), amb_gnd=(0.2, 0.15, 0.12),
                lights=[((0, 42, -40), (1.2, 0.8, 0.4), 50)], fog_col=(0.1, 0.07, 0.06), fog=(300, 600), char_light=1.0, bloom=0.12, vignette=0.45)

def stock_ferme(W):
    hay = {"side": T("hay_block_side"), "top": T("hay_block_top")}
    for (x, y, z) in ((-72, 0, -32), (-56, 0, -32), (-64, 16, -32)): W.add(box((x, y, z), (x + 16, y + 16, z + 16), hay))
    W.add(box((-36, 0, -28), (-20, 16, -12), {"side": T("pumpkin_side"), "top": T("pumpkin_top")}))
    W.add(box((-18, 0, -28), (-2, 16, -12), {"side": T("melon_side"), "top": T("melon_top")}))
    W.add(box((40, 0, -28), (56, 16, -12), {"side": T("barrel_side"), "top": T("barrel_top_open")}))
    W.add(box((58, 0, -30), (74, 16, -14), {"side": T("composter_side"), "top": T("composter_top")}))
    for (n, x, z, yw) in (("wheat", 6, -10, 10), ("carrot", 18, -4, -20), ("potato", 28, 0, 15), ("bread", -14, 2, -10), ("apple", -2, 4, 30), ("beetroot", 44, 2, -25), ("wheat", -40, 0, -15)):
        W.add(item_at(n, x, 0, z, yaw=yw, lean=60, px=0.95))
    return dict(sun_dir=(-0.5, 0.8, 0.5), sun_col=(1.0, 0.82, 0.55), sun_k=0.95, amb_sky=(0.38, 0.36, 0.36), amb_gnd=(0.22, 0.17, 0.12),
                lights=[((-10, 42, -40), (1.1, 0.75, 0.4), 50)], fog_col=(0.12, 0.08, 0.06), fog=(300, 600), bloom=0.12, vignette=0.45)

def stock_forge(W):
    an = {"side": T("anvil"), "top": T("anvil_top")}
    ax, az = -58, -16
    W.add(box((ax - 6, 0, az - 6), (ax + 6, 4, az + 6), an)); W.add(box((ax - 4, 4, az - 4), (ax + 4, 5, az + 4), an))
    W.add(box((ax - 3, 5, az - 3), (ax + 3, 10, az + 3), an)); W.add(box((ax - 10, 10, az - 5), (ax + 10, 16, az + 5), an))
    W.add(item_at("iron_ingot", -60, 16, -14, yaw=10, lean=20, px=0.8))
    for (x, y, z, b) in ((-40, 0, -30, "iron_block"), (-24, 0, -30, "iron_block"), (-32, 16, -30, "gold_block"), (-8, 0, -30, "copper_block")):
        W.add(box((x, y, z), (x + 16, y + 16, z + 16), T(b)))
    for (n, x, z, yw) in (("iron_ingot", -6, 0, 10), ("gold_ingot", 6, 2, -15), ("iron_ingot", 18, -2, 25), ("copper_ingot", 30, 2, -5), ("gold_nugget", -16, 4, 0), ("iron_nugget", 40, 4, 30)):
        W.add(item_at(n, x, 0, z, yaw=yw, lean=55, px=0.9))
    for (k, n) in enumerate(("iron_sword", "golden_sword", "iron_sword")):
        W.add(item_at(n, 22 + k * 13, 4, -31, yaw=0, lean=90, px=1.2))
    W.add(box((56, 0, -32), (72, 16, -16), {"south": T("blast_furnace_front_on"), "side": T("blast_furnace_side"), "top": T("blast_furnace_top")}))
    return dict(sun_dir=(0.4, 0.8, 0.6), sun_col=(0.8, 0.65, 0.55), sun_k=0.45, amb_sky=(0.24, 0.18, 0.18), amb_gnd=(0.16, 0.1, 0.08),
                lights=[((64, 8, -12), (2.0, 0.85, 0.3), 50), ((-60, 40, -20), (0.8, 0.55, 0.3), 50)], fog_col=(0.1, 0.05, 0.04), fog=(300, 600),
                rim_k=0, bloom=0.15, vignette=0.45)

def stock_mine(W):
    rnd = np.random.RandomState(2)
    ores = ["iron_ore", "coal_ore", "gold_ore", "copper_ore", "diamond_ore", "emerald_ore", "redstone_ore", "lapis_ore"]
    for (x, y, z) in ((-72, 0, -32), (-56, 0, -32), (-40, 0, -32), (-64, 16, -32), (-48, 16, -32)):
        W.add(box((x, y, z), (x + 16, y + 16, z + 16), T(rnd.choice(ores))))
    for (n, x, z, yw) in (("raw_iron", -24, -2, 10), ("raw_gold", -14, 2, -20), ("coal", -4, -4, 15), ("diamond", 6, 2, -10), ("emerald", 16, -2, 25),
                          ("raw_copper", 26, 3, -15), ("lapis_lazuli", 36, -3, 5), ("redstone", -34, 2, 0), ("amethyst_shard", 46, -2, -20)):
        W.add(item_at(n, x, 0, z, yaw=yw, lean=55, px=0.95, glow=() if n not in ("diamond", "emerald", "amethyst_shard") else ()))
    W.add(box((56, 0, -32), (72, 16, -16), {"side": T("barrel_side"), "top": T("barrel_top_open")}))

    return dict(sun_dir=(0.3, 0.9, 0.5), sun_col=(0.55, 0.6, 0.75), sun_k=0.45, amb_sky=(0.22, 0.22, 0.28), amb_gnd=(0.12, 0.12, 0.14),
                lights=[((-20, 42, -40), (1.4, 0.95, 0.5), 60)], fog_col=(0.03, 0.03, 0.05), fog=(300, 600), bloom=0.15, vignette=0.45)

STOCKS = {"scierie": stock_scierie, "ferme": stock_ferme, "forge": stock_forge, "mine": stock_mine}

STOCK_LOOK = {"scierie": ((64, 44, 30), (0.16, 0.11, 0.08), (0.36, 0.26, 0.18)),
              "ferme": ((84, 66, 44), (0.18, 0.13, 0.09), (0.40, 0.30, 0.20)),
              "forge": ((58, 46, 44), (0.13, 0.07, 0.06), (0.34, 0.18, 0.12)),
              "mine": ((52, 52, 60), (0.07, 0.07, 0.10), (0.20, 0.20, 0.26))}

def render_stock(name, ss=3, check=False):
    W = World(); params = STOCKS[name](W)
    params.setdefault("rim_k", 0); params["dof"] = (0, 0)
    gcol, top, bot = STOCK_LOOK[name]
    params["sky"] = S.sky_gradient(top, bot); params["fog_col"] = bot; params["fog"] = (115, 210)
    params.pop("lights", None) if name in ("scierie", "ferme") else None
    cam = S.Cam((0, 36, 92), (0, 14, -16), fov=30, W=SW * ss, H=SH * ss)
    obj = W.faces()
    if check:
        pts = [cam.project(f["o"] + a * f["u"] + b * f["v"]) for f in obj for a in (0, 1) for b in (0, 1)]
        xs = [q[0] / cam.W for q in pts]; ys = [q[1] / cam.H for q in pts]
        print(name, "x %.2f..%.2f  y %.2f..%.2f" % (min(xs), max(xs), min(ys), max(ys)))
    ground_ = [face((-600, 0, -600), (1200, 0, 0), (0, 0, 1200), (0, 1, 0), color=gcol, cast=False)]
    im = S.shade(obj + ground_, cam, **params).resize((SW, SH), Image.BOX)
    from PIL import ImageFilter
    return im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=50, threshold=2))

# ================================================================ aperçu des 4 bâtiments (page « Bâtiments »)
def model_faces(model, bright=False):
    os.environ.setdefault("MC_ASSETS", "/home/claude/mc/assets/minecraft")
    import machines_core as MCORE
    MCORE.MC = "/home/claude/mc/assets/minecraft/textures/"
    out = []
    def tex(name):
        k = ("model", name)
        if k not in S._TEX:
            if name.startswith("mc:"): S._TEX[k] = T(name[3:])
            else:
                im = MCORE.CUSTOM[name]()
                if isinstance(im, tuple): im = im[0]
                S._TEX[k] = np.array(im.convert("RGBA").crop((0, 0, 16, 16)))
        return S._TEX[k]
    for e0 in model.els:
        for e in MCORE._split(e0):
            (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
            geo = {"north": ((x1, y1, z0), (x0 - x1, 0, 0), (0, y0 - y1, 0), (0, 0, -1)),
                   "south": ((x0, y1, z1), (x1 - x0, 0, 0), (0, y0 - y1, 0), (0, 0, 1)),
                   "east": ((x1, y1, z1), (0, 0, z0 - z1), (0, y0 - y1, 0), (1, 0, 0)),
                   "west": ((x0, y1, z0), (0, 0, z1 - z0), (0, y0 - y1, 0), (-1, 0, 0)),
                   "up": ((x0, y1, z0), (x1 - x0, 0, 0), (0, 0, z1 - z0), (0, 1, 0)),
                   "down": ((x0, y0, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), (0, -1, 0))}
            for fc in e["faces"]:
                name = e["tex"].get(fc)
                if not name: continue
                try: img = tex(name)
                except Exception: continue
                r = e["uvrot"].get(fc, 0)
                if r: img = np.rot90(img, k=-(r // 90)).copy()
                u0, v0, u1, v1 = MCORE._face_uv(e, fc)
                o, u, v, n = (np.array(a, float) for a in geo[fc])
                pts = [o, o + u, o + v]
                if e["rot"]:
                    pts = [np.array(MCORE._rot(tuple(q), e["rot"])) for q in pts]
                    n = np.array(MCORE._rot(tuple(n), (e["rot"][0], e["rot"][1], (0, 0, 0))))
                out.append(face(pts[0], pts[1] - pts[0], pts[2] - pts[0], n, tex=img, uv=(u0, v0, u1 - u0, v1 - v0), glow=0.6 if bright else 0.0))
    return out

def building_faces(name, offset, turn=180):
    """Bâtiment posé à `offset`, tourné pour présenter sa devanture (côté z=0 du modèle) à la caméra."""
    import machines_designs as MD
    b = MD.MACHINES[name]()
    F = model_faces(b.base)
    for part in b.parts: F += model_faces(part.model, bright=part.bright)
    R = SR.rot_y(math.radians(turn))
    c = np.array([24.0, 0, 24.0]); off = np.asarray(offset, float) + c
    for f in F:
        f["o"] = R @ (f["o"] - c) + off; f["u"] = R @ f["u"]; f["v"] = R @ f["v"]; f["n"] = R @ f["n"]
    return F

def render_buildings(ss=3):
    W = World()
    g = {"top": S.tinted("grass_block_top", S.GRASS), "side": T("grass_block_side"), "bottom": T("dirt")}
    for x in range(-11, 11):
        for z in range(-18, 4): W.set(x, -1, z, g)
    for (tx, tz, h) in ((-9, -12, 4), (-5, -13, 5), (-1, -12, 4), (3, -13, 5), (7, -12, 4), (10, -13, 5),
                        (-7, -15, 5), (-3, -15, 4), (1, -15, 5), (5, -15, 4), (9, -15, 5), (-10, -15, 4)):
        tree(W, tx, tz, h)
    F = W.faces()
    F += [face((-6, 0.2, -200), (12, 0, 0), (0, 0, 260), (0, 1, 0), tex=T("dirt_path_top"), uv=(0, 0, 12, 260), cast=False)]
    for n, off in (("scierie", (-56, 0, -40)), ("forge", (8, 0, -40)), ("ferme", (-56, 0, -116)), ("mine", (8, 0, -116))):
        F += building_faces(n, off)
    cam = S.Cam((0, 185, 150), (0, 4, -70), fov=40, W=NW * ss, H=NH * ss)
    im = S.shade(F, cam, sun_dir=(-0.5, 0.85, 0.45), sun_col=(1.0, 0.9, 0.72), sun_k=1.0, amb_sky=(0.42, 0.48, 0.6), amb_gnd=(0.24, 0.24, 0.18),
                 fog_col=(0.66, 0.74, 0.82), fog=(300, 600), sky=S.sky_gradient((0.36, 0.56, 0.88), (0.9, 0.86, 0.74)), rim_k=0, dof=(0, 0),
                 bloom=0.12, vignette=0.4)
    from PIL import ImageFilter
    return im.resize((NW, NH), Image.BOX).filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
