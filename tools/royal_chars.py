"""Personnages « Royaumes » rendus en 3D façon skin Minecraft (roi, bûcheron, forgeron, fermier, mineur).

Modèle : boîtes en texels (pieds en y=0, face avant vers −Z). Chaque boîte a une chaîne de rotations
(appliquées dans l'ordre : d'abord l'objet tenu autour de la main, puis le bras autour de l'épaule…).
Chaque face est peinte par f(face, u, v, w, h) -> couleur (u, v = texel de la face, v depuis le haut).
Personnages et outils originaux.
"""
import math
from PIL import Image, ImageDraw
from royal_kingdom import outline

K = (26, 14, 22)

def mul(c, f): return tuple(max(0, min(255, int(v * f))) for v in c[:3])
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def hsh(*a):
    h = 2166136261
    for v in a: h = ((h ^ (int(v * 7) & 0xFFFF)) * 16777619) & 0xFFFFFFFF
    return (h >> 8) % 1000 / 1000

class Box:
    def __init__(self, f, t, paint, rots=(), glow=False, ao=True):
        self.f, self.t, self.paint, self.rots, self.glow, self.ao = f, t, paint, list(rots), glow, ao

def _rot(p, rot):
    ax, ang, o = rot
    if ax == "x": ang = -ang
    a = math.radians(ang)
    x, y, z = p[0] - o[0], p[1] - o[1], p[2] - o[2]
    if ax == "x": y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    elif ax == "y": x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
    else: x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return (x + o[0], y + o[1], z + o[2])

LIGHT = {"north": 1.0, "up": 1.14, "west": 0.84, "east": 0.66, "south": 0.58, "down": 0.46}

def render(boxes, scale=3, yaw=206, pitch=9):
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    def proj(p):
        x, y, z = p
        x, z = x * cy - z * sy, x * sy + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        return (x * scale, -y * scale, z)
    quads = []
    for b in boxes:
        (x0, y0, z0), (x1, y1, z1) = b.f, b.t
        dims = {"north": (x1 - x0, y1 - y0), "south": (x1 - x0, y1 - y0), "east": (z1 - z0, y1 - y0),
                "west": (z1 - z0, y1 - y0), "up": (x1 - x0, z1 - z0), "down": (x1 - x0, z1 - z0)}
        for face in ("north", "south", "east", "west", "up", "down"):
            w, h = dims[face]
            nu, nv = max(1, int(round(w))), max(1, int(round(h)))
            if face == "north": P = lambda u, v: (x1 - (x1 - x0) * u, y1 - (y1 - y0) * v, z0)
            elif face == "south": P = lambda u, v: (x0 + (x1 - x0) * u, y1 - (y1 - y0) * v, z1)
            elif face == "east": P = lambda u, v: (x1, y1 - (y1 - y0) * v, z1 - (z1 - z0) * u)
            elif face == "west": P = lambda u, v: (x0, y1 - (y1 - y0) * v, z0 + (z1 - z0) * u)
            elif face == "up": P = lambda u, v: (x1 - (x1 - x0) * u, y1, z1 - (z1 - z0) * v)
            else: P = lambda u, v: (x1 - (x1 - x0) * u, y0, z0 + (z1 - z0) * v)
            for j in range(nv):
                for i in range(nu):
                    c = b.paint(face, i, j, nu, nv)
                    if c is None: continue
                    pts = [P(i / nu, j / nv), P((i + 1) / nu, j / nv), P((i + 1) / nu, (j + 1) / nv), P(i / nu, (j + 1) / nv)]
                    for r in b.rots: pts = [_rot(q, r) for q in pts]
                    pts = [proj(q) for q in pts]
                    ax_, ay_ = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
                    bx_, by_ = pts[3][0] - pts[0][0], pts[3][1] - pts[0][1]
                    if ax_ * by_ - ay_ * bx_ <= 0: continue
                    if b.glow: col = c
                    else:
                        f = LIGHT[face]
                        if b.ao and face not in ("up", "down") and nv > 2: f *= 1.04 - 0.2 * (j / (nv - 1))
                        f *= 1.0 + 0.05 * (hsh(i, j, x0, y0, z0, len(face)) - 0.5)
                        col = mul(c, f)
                    quads.append((sum(q[2] for q in pts) / 4, [(q[0], q[1]) for q in pts], col))
    quads.sort(key=lambda q: q[0])
    xs = [p[0] for q in quads for p in q[1]]; ys = [p[1] for q in quads for p in q[1]]
    ox, oy = -min(xs) + 2, -min(ys) + 2
    im = Image.new("RGBA", (int(max(xs) + ox) + 3, int(max(ys) + oy) + 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _, pts, col in quads:
        d.polygon([(x + ox, y + oy) for (x, y) in pts], fill=col + (255,))
    return outline(im, K)

# ---------------------------------------------------------------- peinture
def tex(base, var=0.07, seed=0):
    def f(face, u, v, w, h): return mul(base, 1 + var * (hsh(u, v, seed, len(face)) - 0.5) * 2)
    return f

def fabric(base, var=0.06, seed=1):
    def f(face, u, v, w, h): return mul(base, 1 + var * (hsh(u, v, seed) - 0.5) * 2)
    return f

def layered(rows, default):
    def f(face, u, v, w, h):
        if face not in ("up", "down"):
            for (a, b, p) in rows:
                if a <= v <= b: return p(face, u, v, w, h)
        return default(face, u, v, w, h)
    return f

SKIN = {"pale": [(168, 106, 80), (212, 150, 116), (236, 184, 150), (248, 210, 178)],
        "tan": [(132, 80, 56), (178, 118, 84), (208, 150, 110), (228, 178, 138)],
        "rosy": [(170, 100, 84), (214, 142, 116), (240, 178, 150), (250, 206, 182)]}

def face_paint(skin, hair, eye=(60, 90, 150), brow=None, bald=False, blush=False, scar=False):
    s = SKIN[skin]
    brow = brow or mul(hair, 0.8)
    def f(face, u, v, w, h):
        if face == "down": return s[1]
        if face == "up": return mix(s[2], s[3], 0.3) if bald else mul(hair, 1 + 0.12 * (hsh(u, v) - 0.5))
        if face == "south": return s[1] if bald and v > 2 else mul(hair, 1 + 0.12 * (hsh(u, v, 3) - 0.5))
        if face in ("east", "west"):
            if not bald and (v < 3 or (face == "east" and u > 4) or (face == "west" and u < 3)): return mul(hair, 1 + 0.1 * (hsh(u, v, 5) - .5))
            if bald and v < 1: return s[3]
            if v == 4 and ((face == "east" and u == 2) or (face == "west" and u == 5)): return s[1]
            return s[2]
        if not bald and v < 2: return mul(hair, 1 + 0.1 * (hsh(u, v, 7) - .5))
        if not bald and v == 2 and u in (0, 7): return hair
        if bald and v == 0: return s[3]
        if v == 3 and u in (1, 2, 5, 6): return brow
        if v == 4:
            if u in (1, 6): return (246, 244, 240)
            if u in (2, 5): return eye
            if u in (3, 4): return s[2]
        if v == 5 and u in (3, 4): return s[1]
        if blush and v == 5 and u in (1, 6): return mix(s[2], (230, 110, 110), 0.45)
        if scar and v in (3, 4, 5) and u == 6: return mix(s[2], (150, 70, 70), 0.6)
        if v == 6 and u in (3, 4): return (150, 70, 72)
        if v == 6 and u in (2, 5): return s[1]
        return s[2] if v < 6 else mix(s[2], s[1], 0.35)
    return f

def beard_box(color, length=3, mustache=True, braid=False):
    def f(face, u, v, w, h):
        if face == "up": return None
        c = mul(color, 1 + 0.16 * (hsh(u, v, 11) - 0.5))
        if (u + v) % 3 == 0: c = mul(c, 0.86)
        return c
    # barbe : du coin de la bouche jusque sous le menton ; moustache juste sous le nez
    boxes = [Box((-4.1, 26 - length, -4.5), (4.1, 25.6, -3.95), f),
             Box((-4.1, 25.6, -4.5), (-2.6, 27, -3.95), f), Box((2.6, 25.6, -4.5), (4.1, 27, -3.95), f)]
    if mustache: boxes.append(Box((-2.6, 25.5, -4.7), (2.6, 26.2, -4.2), tex(mul(color, 0.9), 0.1, 12)))
    if braid: boxes.append(Box((-0.8, 26 - length - 3, -4.4), (0.8, 26 - length + 0.2, -3.7), tex(mul(color, 0.85), 0.12, 13)))
    return boxes

def limb(sleeve, skin=None, cuff=None, hand=2, glove=None, stripes=None):
    def f(face, u, v, w, h):
        end = glove or (SKIN[skin][2] if skin else None)
        if face == "down": return mul(end, 0.9) if end else sleeve
        if face == "up": return sleeve
        if end and v >= h - hand: return end if face != "south" else mul(end, 0.9)
        if cuff and v == h - hand - 1: return cuff
        if stripes and stripes(u, v): return mul(sleeve, 0.78)
        return mul(sleeve, 1 + 0.07 * (hsh(u, v, 21, len(face)) - 0.5))
    return f

# ---------------------------------------------------------------- squelette et poses
def skeleton(paints, pose):
    hx, hy, hz = pose.get("head", (0, 0, 0))
    head_r = [("x", hx, (0, 24, 0)), ("y", hy, (0, 24, 0)), ("z", hz, (0, 24, 0))]
    def arm_r(sx, a): return [("x", a[0], (sx, 22, 0)), ("z", a[1], (sx, 22, 0))]
    def leg_r(sx, a): return [("x", a[0], (sx, 12, 0)), ("z", a[1], (sx, 12, 0))]
    R = {"head": head_r, "rarm": arm_r(-6, pose.get("rarm", (0, 0))), "larm": arm_r(6, pose.get("larm", (0, 0))),
         "rleg": leg_r(-2, pose.get("rleg", (0, 0))), "lleg": leg_r(2, pose.get("lleg", (0, 0)))}
    boxes = [
        Box((-4, 0, -2), (0, 12, 2), paints["rleg"], R["rleg"]), Box((0, 0, -2), (4, 12, 2), paints["lleg"], R["lleg"]),
        Box((-4, 12, -2), (4, 24, 2), paints["body"]),
        Box((-8, 12, -2), (-4, 24, 2), paints["rarm"], R["rarm"]), Box((4, 12, -2), (8, 24, 2), paints["larm"], R["larm"]),
        Box((-4, 24, -4), (4, 32, 4), paints["head"], R["head"]),
    ]
    return boxes, R

def attach(boxes, part_rots, pivot, local=()):
    for b in boxes:
        b.rots = [(a, ang, pivot) for (a, ang) in local] + list(b.rots) + list(part_rots)
    return boxes

def on(part_rots, *boxes):
    for b in boxes: b.rots = list(b.rots) + list(part_rots)
    return list(boxes)

# ---------------------------------------------------------------- outils (manche vertical centré sur la main)
WOOD_H = (132, 86, 50)
IRON = (150, 156, 172); IRON_D = (86, 90, 104); IRON_L = (220, 226, 236)
GOLD = [(140, 82, 20), (204, 140, 36), (244, 196, 70), (255, 236, 150)]

def handle(hx, hy, hz, y0, y1, w=1.1, color=WOOD_H, grip=None):
    def f(face, u, v, w_, h):
        if grip and grip[0] <= (h - 1 - v) <= grip[1]: return (60, 40, 30) if v % 2 else (96, 64, 42)
        return mul(color, 1 + 0.1 * (hsh(u, v, 31) - 0.5)) if v % 4 else mul(color, 0.86)
    return Box((hx - w / 2, hy + y0, hz - w / 2), (hx + w / 2, hy + y1, hz + w / 2), f)

def axe(hx, hy, hz):
    blade = lambda face, u, v, w, h: IRON_L if (face in ("east", "west") and u == 0) else mul(IRON, 1 + .1 * (hsh(u, v, 32) - .5))
    return [handle(hx, hy, hz, -3, 13, grip=(0, 3)),
            Box((hx - 0.45, hy + 8.4, hz - 4.8), (hx + 0.45, hy + 13.6, hz - 0.6), blade),
            Box((hx - 0.7, hy + 10, hz - 0.7), (hx + 0.7, hy + 12.6, hz + 1.8), tex(IRON_D, 0.1, 33)),
            Box((hx - 0.5, hy + 7.6, hz - 4.9), (hx + 0.5, hy + 8.4, hz - 3.4), tex(IRON, 0.05, 34)),
            Box((hx - 0.5, hy + 13.6, hz - 4.9), (hx + 0.5, hy + 14.4, hz - 3.4), tex(IRON, 0.05, 35))]

def hammer(hx, hy, hz):
    return [handle(hx, hy, hz, -3, 11, grip=(0, 3)),
            Box((hx - 1.4, hy + 9, hz - 3.0), (hx + 1.4, hy + 12.4, hz + 3.0), tex(IRON_D, 0.1, 36)),
            Box((hx - 1.7, hy + 8.7, hz - 3.6), (hx + 1.7, hy + 12.7, hz - 2.8), tex(IRON, 0.06, 37)),
            Box((hx - 1.7, hy + 8.7, hz + 2.8), (hx + 1.7, hy + 12.7, hz + 3.6), tex(IRON, 0.06, 38)),
            Box((hx - 0.9, hy + 8.2, hz - 0.9), (hx + 0.9, hy + 9.0, hz + 0.9), tex((70, 50, 40), 0.1, 39))]

def pitchfork(hx, hy, hz):
    bx = [handle(hx, hy, hz, -13, 19),
          Box((hx - 0.8, hy + 19, hz - 0.8), (hx + 0.8, hy + 20.2, hz + 0.8), tex(IRON_D, 0.1, 40)),
          Box((hx - 2.8, hy + 20.2, hz - 0.5), (hx + 2.8, hy + 21.2, hz + 0.5), tex(IRON, 0.08, 41))]
    for dx in (-2.5, 0, 2.5):
        bx.append(Box((hx + dx - 0.35, hy + 21.2, hz - 0.35), (hx + dx + 0.35, hy + 26.4, hz + 0.35), tex(IRON_L, 0.06, 42)))
    return bx

def pickaxe(hx, hy, hz):
    bx = [handle(hx, hy, hz, -2, 14, grip=(0, 2)),
          Box((hx - 0.9, hy + 12.2, hz - 1.4), (hx + 0.9, hy + 14.6, hz + 1.4), tex(IRON_D, 0.1, 43))]
    for (z0, z1, dy) in ((1.4, 4, 0.2), (4, 6.2, -0.6), (6.2, 7.8, -1.8), (-4, -1.4, 0.2), (-6.2, -4, -0.6), (-7.8, -6.2, -1.8)):
        th = 1.6 if abs(z0) < 6 else 1.1
        c = tex(IRON_L, 0.05, 44) if abs(z0) >= 6 else tex(IRON, 0.1, 45)
        bx.append(Box((hx - 0.6, hy + 12.6 + dy, hz + min(z0, z1)), (hx + 0.6, hy + 12.6 + dy + th, hz + max(z0, z1)), c))
    return bx

def scepter(hx, hy, hz):
    g = lambda s: tex(GOLD[2], 0.08, s)
    bx = [Box((hx - 0.5, hy - 6, hz - 0.5), (hx + 0.5, hy + 13, hz + 0.5), g(46))]
    for y in (-6, 2, 11): bx.append(Box((hx - 0.9, hy + y, hz - 0.9), (hx + 0.9, hy + y + 0.8, hz + 0.9), tex(GOLD[3], 0.05, 47)))
    bx.append(Box((hx - 1.4, hy + 13, hz - 1.4), (hx + 1.4, hy + 15.8, hz + 1.4), tex((200, 40, 60), 0.12, 48)))
    bx.append(Box((hx - 1.7, hy + 13.6, hz - 1.7), (hx + 1.7, hy + 14.2, hz + 1.7), g(49)))
    bx.append(Box((hx - 0.3, hy + 15.8, hz - 0.3), (hx + 0.3, hy + 18, hz + 0.3), g(50)))
    bx.append(Box((hx - 1.1, hy + 16.6, hz - 0.3), (hx + 1.1, hy + 17.2, hz + 0.3), g(51)))
    return bx

def tongs_ingot(hx, hy, hz):
    hot = lambda face, u, v, w, h: (255, 236, 160) if (u + v) % 3 else (255, 176, 66)
    return [Box((hx - 0.9, hy - 1, hz - 0.3), (hx - 0.3, hy + 9, hz + 0.3), tex(IRON_D, 0.1, 52)),
            Box((hx + 0.3, hy - 1, hz - 0.3), (hx + 0.9, hy + 9, hz + 0.3), tex(IRON_D, 0.1, 53)),
            Box((hx - 1.4, hy + 9, hz - 2.6), (hx + 1.4, hy + 10.4, hz + 2.6), hot, glow=True)]

def lantern(hx, hy, hz):
    glowp = lambda face, u, v, w, h: (255, 226, 130) if (u + v) % 2 else (255, 190, 80)
    return [Box((hx - 0.25, hy - 1.5, hz - 0.25), (hx + 0.25, hy + 0.6, hz + 0.25), tex(IRON_D, 0.1, 54)),
            Box((hx - 1.8, hy - 2.4, hz - 1.8), (hx + 1.8, hy - 1.5, hz + 1.8), tex(IRON_D, 0.1, 55)),
            Box((hx - 1.4, hy - 6.4, hz - 1.4), (hx + 1.4, hy - 2.4, hz + 1.4), glowp, glow=True),
            Box((hx - 1.8, hy - 7.2, hz - 1.8), (hx + 1.8, hy - 6.4, hz + 1.8), tex(IRON_D, 0.1, 56))]

# ---------------------------------------------------------------- personnages
RH = (-6, 12.5, 0)
LH = (6, 12.5, 0)
ERMINE_W = (246, 242, 234)

def ermine(face, u, v, w, h): return (24, 22, 28) if hsh(u, v, 61, len(face)) < 0.12 else ERMINE_W

def king():
    hair = (112, 74, 44); beardc = (150, 112, 80)
    robe, robe_d = (176, 38, 50), (124, 24, 38)
    def body(face, u, v, w, h):
        if face == "up": return robe
        if v <= 1: return ermine(face, u, v, w, h)
        if face == "north":
            if u in (3, 4): return GOLD[2] if v % 3 else GOLD[3]
            if v == 8: return GOLD[1] if u not in (3, 4) else GOLD[3]
            if (v == 3 and u in (1, 6)) or (v == 4 and u in (2, 5)): return GOLD[2]
        return mul(robe, 1 + 0.07 * (hsh(u, v, 62) - .5))
    leg = layered([(10, 11, tex((70, 44, 30), 0.1, 63)), (9, 9, tex(GOLD[1], 0.05, 64))], fabric(robe_d, seed=65))
    paints = {"head": face_paint("pale", hair, eye=(50, 80, 140)), "body": body,
              "rarm": limb(robe, "pale", cuff=ERMINE_W), "larm": limb(robe, "pale", cuff=ERMINE_W),
              "rleg": leg, "lleg": leg}
    pose = {"head": (-4, 10, 0), "rarm": (-38, -10), "larm": (-14, 22), "rleg": (5, -2), "lleg": (-7, 3)}
    boxes, R = skeleton(paints, pose)
    boxes += on(R["head"], *beard_box(beardc, 3))
    boxes += on(R["head"], Box((-4.4, 25, -1), (4.4, 31.2, 4.4), lambda face, u, v, w, h: None if face in ("north", "down") else mul(hair, 1 + .14 * (hsh(u, v, 66) - .5))))
    def band(face, u, v, w, h):
        if face in ("up", "down"): return None
        if face == "north" and v == 1 and u in (2, 6): return (200, 40, 60)
        if face == "north" and v == 1 and u == 4: return (60, 120, 220)
        return GOLD[3] if v == 0 else GOLD[2]
    crown = [Box((-4.5, 31, -4.5), (4.5, 33, 4.5), band)]
    for (x, z) in ((-4.5, -4.5), (-0.6, -4.5), (3.3, -4.5), (-4.5, 3.3), (3.3, 3.3), (-4.5, -0.6), (3.3, -0.6), (-0.6, 3.3)):
        crown.append(Box((x, 33, z), (x + 1.2, 35.2, z + 1.2), tex(GOLD[3], 0.05, 67)))
        crown.append(Box((x + 0.2, 35.2, z + 0.2), (x + 1.0, 36, z + 1.0), tex(GOLD[3], 0.03, 68)))
    boxes += on(R["head"], *crown)
    def cape(face, u, v, w, h):
        if face == "north": return None
        if v <= 1: return ermine(face, u, v, w, h)
        if face == "south" and u in (0, 1, w - 2, w - 1): return GOLD[1] if u in (1, w - 2) else robe_d
        return mul(robe_d, 1 + 0.07 * (hsh(u, v, 69) - .5)) if (u % 3) else mul(robe_d, 0.88)
    boxes.append(Box((-5.4, 1, 2), (5.4, 24.4, 3.2), cape))
    boxes.append(Box((-5.4, 23, -2.6), (5.4, 24.8, 3.2), ermine))
    boxes += attach(scepter(*RH), R["rarm"], RH, local=[("x", 38), ("z", 10)])
    return boxes

def lumberjack():
    hair = (156, 76, 34); beardc = (176, 88, 38)
    def plaid(face, u, v, w, h):
        a, b = (u // 2) % 2, (v // 2) % 2
        base = (34, 24, 28) if a and b else (190, 40, 38) if not a and not b else (128, 30, 34)
        return base
    def body(face, u, v, w, h):
        if face in ("up", "down"): return (150, 34, 34)
        if v == 9: return (84, 54, 32) if not (face == "north" and u in (3, 4)) else (196, 196, 206)
        if face == "north" and u in (1, 6) and v < 9: return (84, 54, 32)
        if face == "south" and u in (2, 5) and v < 9: return (84, 54, 32)
        return plaid(face, u, v, w, h)
    jeans = lambda face, u, v, w, h: (60, 44, 32) if v >= 10 else ((86, 60, 40) if v == 9 else mul((66, 84, 124), 1 + .08 * (hsh(u, v, 71) - .5)))
    st = lambda u, v: (v // 2) % 2 and (u // 2) % 2
    paints = {"head": face_paint("rosy", hair, eye=(60, 110, 70), blush=True), "body": body,
              "rarm": limb((190, 40, 38), "rosy", cuff=(34, 24, 28), stripes=st), "larm": limb((190, 40, 38), "rosy", cuff=(34, 24, 28), stripes=st),
              "rleg": jeans, "lleg": jeans}
    pose = {"head": (-2, -14, 0), "rarm": (-58, -8), "larm": (-10, 18), "rleg": (8, -3), "lleg": (-8, 4)}
    boxes, R = skeleton(paints, pose)
    boxes += on(R["head"], *beard_box(beardc, 4))
    beanie = lambda face, u, v, w, h: None if face == "down" else ((32, 96, 64) if v >= h - 1 and face != "up" else mul((48, 136, 88), 1 + .1 * (hsh(u, v, 72) - .5)))
    boxes += on(R["head"], Box((-4.4, 29.4, -4.4), (4.4, 33, 4.4), beanie), Box((-1, 33, -1), (1, 34.4, 1), tex((230, 226, 210), 0.1, 73)))
    boxes += attach(axe(*RH), R["rarm"], RH, local=[("x", 22), ("z", 8)])
    return boxes

def blacksmith():
    beardc = (44, 32, 30)
    leather = (128, 80, 46)
    def body(face, u, v, w, h):
        if face == "up": return (100, 100, 112)
        if face == "north":
            if v <= 1 and u not in (1, 6): return SKIN["tan"][2] if v == 0 else (100, 100, 112)
            return mul(leather, 1 + 0.12 * (hsh(u, v, 81) - .5))
        if v in (5, 6) and face in ("east", "west"): return (80, 50, 30)
        return mul((96, 96, 108), 1 + 0.06 * (hsh(u, v, 82) - .5))
    def bare(face, u, v, w, h):
        s = SKIN["tan"]
        if face == "up" or v <= 1: return (96, 96, 108)
        if v in (8, 9): return (62, 40, 30) if (u + v) % 2 else (88, 58, 40)
        if v >= 10: return (70, 48, 36)
        if face == "north" and v in (3, 4) and u in (1, 2): return s[1]
        return s[2] if hsh(u, v, 83) > 0.12 else mix(s[2], (60, 40, 40), 0.3)
    leg = lambda face, u, v, w, h: (40, 36, 40) if v >= 10 else (mul(leather, 0.9) if (face == "north" and v < 6) else mul((70, 66, 74), 1 + .07 * (hsh(u, v, 84) - .5)))
    paints = {"head": face_paint("tan", beardc, bald=True, eye=(80, 60, 40), scar=True), "body": body,
              "rarm": bare, "larm": bare, "rleg": leg, "lleg": leg}
    pose = {"head": (8, 12, 0), "rarm": (-55, -12), "larm": (-42, 10), "rleg": (4, -4), "lleg": (-5, 4)}
    boxes, R = skeleton(paints, pose)
    boxes += on(R["head"], *beard_box(beardc, 4, braid=True))
    boxes += on(R["head"], Box((-4.3, 28.6, -4.3), (4.3, 29.6, 4.3), lambda face, u, v, w, h: None if face in ("up", "down") else (96, 64, 42)))
    boxes.append(Box((-3.4, 7, -2.5), (3.4, 21, -2.05), tex(leather, 0.12, 85)))
    boxes += attach(hammer(*RH), R["rarm"], RH, local=[("x", 18), ("z", 12)])
    boxes += attach(tongs_ingot(*LH), R["larm"], LH, local=[("x", 105)])
    return boxes

def farmer():
    hair = (214, 172, 92)
    denim = (70, 112, 174)
    def body(face, u, v, w, h):
        if face == "up": return (236, 232, 220)
        if face == "north":
            if v <= 3 and 2 <= u <= 5: return (236, 232, 220) if not (v == 0 and u in (3, 4)) else SKIN["rosy"][2]
            if v <= 3 and u in (1, 6): return denim
            if v <= 3: return (236, 232, 220)
            if v == 4 and u in (2, 5): return (210, 170, 70)
            if v == 6 and u in (3, 4): return mul(denim, 0.8)
        if face == "south" and v <= 4 and u in (1, 6): return denim
        if v <= 3: return (232, 228, 214)
        return mul(denim, 1 + 0.08 * (hsh(u, v, 91) - .5))
    jean = lambda face, u, v, w, h: (92, 62, 40) if v >= 10 else mul(denim, 1 + .08 * (hsh(u, v, 92) - .5))
    paints = {"head": face_paint("rosy", hair, eye=(70, 120, 60), blush=True), "body": body,
              "rarm": limb((236, 232, 220), "rosy", cuff=(220, 214, 200)), "larm": limb((236, 232, 220), "rosy", cuff=(220, 214, 200)),
              "rleg": jean, "lleg": jean}
    pose = {"head": (-4, -10, 7), "rarm": (-24, -12), "larm": (-8, 26), "rleg": (3, -2), "lleg": (-8, 4)}
    boxes, R = skeleton(paints, pose)
    straw = lambda face, u, v, w, h: (236, 200, 104) if (u + v) % 2 else (210, 168, 78)
    boxes += on(R["head"], Box((-7.4, 30.4, -7.4), (7.4, 31.4, 7.4), straw),
                Box((-4.4, 31.4, -4.4), (4.4, 35.4, 4.4), lambda face, u, v, w, h: (196, 54, 46) if (v == h - 1 and face not in ("up", "down")) else straw(face, u, v, w, h)))
    boxes += on(R["head"], Box((1.8, 25.2, -5.6), (2.4, 25.8, -4.0), tex((232, 204, 96), 0.05, 93)),
                Box((2.4, 25.4, -6.8), (3.6, 26.2, -5.6), tex((246, 214, 100), 0.05, 94)))
    boxes += attach(pitchfork(*RH), R["rarm"], RH, local=[("x", 24), ("z", 12)])
    return boxes

def miner():
    hair = (60, 40, 30); beardc = (86, 60, 42)
    tunic = (118, 106, 94)
    def body(face, u, v, w, h):
        if face == "up": return tunic
        if v == 8: return (70, 46, 30) if not (face == "north" and u in (3, 4)) else (170, 150, 90)
        if face == "north" and v in (9, 10) and u in (5, 6): return (132, 92, 52)
        if face == "north" and u == 2 and 1 <= v <= 7: return (82, 60, 40)
        c = mul(tunic, 1 + .08 * (hsh(u, v, 101) - .5))
        return mul(c, 0.8) if hsh(u, v, 102) < 0.14 else c
    leg = lambda face, u, v, w, h: (50, 40, 36) if v >= 9 else ((68, 50, 38) if v == 8 else mul((98, 76, 58), 1 + .08 * (hsh(u, v, 103) - .5)))
    paints = {"head": face_paint("tan", hair, eye=(60, 70, 110)), "body": body,
              "rarm": limb(tunic, glove=(84, 58, 40), hand=2), "larm": limb(tunic, glove=(84, 58, 40), hand=2),
              "rleg": leg, "lleg": leg}
    pose = {"head": (-2, 12, 0), "rarm": (-48, -10), "larm": (-36, 12), "rleg": (6, -2), "lleg": (-6, 3)}
    boxes, R = skeleton(paints, pose)
    boxes += on(R["head"], *beard_box(beardc, 3))
    cap = lambda face, u, v, w, h: None if face == "down" else ((90, 60, 36) if v >= h - 1 and face != "up" else mul((126, 86, 50), 1 + .1 * (hsh(u, v, 104) - .5)))
    boxes += on(R["head"], Box((-4.4, 29.2, -4.4), (4.4, 33, 4.4), cap),
                Box((-1.6, 30.2, -5.3), (1.6, 32.8, -4.4), tex((70, 70, 82), 0.1, 105)),
                Box((-0.6, 32.8, -5.1), (0.6, 34.6, -4.5), tex((244, 238, 222), 0.03, 106)),
                Box((-0.4, 34.6, -5.0), (0.4, 35.6, -4.6), lambda *a: (255, 196, 70), glow=True))
    boxes += attach(pickaxe(*RH), R["rarm"], RH, local=[("x", 10), ("z", 14)])
    boxes += attach(lantern(*LH), R["larm"], LH, local=[("x", 36), ("z", -12)])
    return boxes

CHARS = {"roi": king, "bucheron": lumberjack, "forgeron": blacksmith, "fermier": farmer, "mineur": miner}

if __name__ == "__main__":
    ims = [render(fn()) for fn in CHARS.values()]
    W = sum(i.width for i in ims) + 20 * len(ims); H = max(i.height for i in ims) + 20
    sh = Image.new("RGBA", (W, H), (60, 50, 60, 255)); x = 10
    for i in ims: sh.alpha_composite(i, (x, H - i.height - 10)); x += i.width + 20
    sh.resize((W * 3, H * 3), Image.NEAREST).save("/home/claude/rp/chars.png")
    print("ok", [i.size for i in ims])
