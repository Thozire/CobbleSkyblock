"""Render 3D haute définition d'un vrai skin Minecraft (64x64), posé, avec objet tenu (sprite extrudé).

Rasterisation par pixel avec z-buffer, suréchantillonnage puis réduction (bords lisses, texels nets),
éclairage clé chaud + contre-jour froid + occlusion ambiante en espace écran.
Repère : y vers le haut, le personnage regarde vers +z, son côté droit est en −x.
"""
import math
import numpy as np
from PIL import Image, ImageFilter

# ---------------------------------------------------------------- géométrie
def rot_x(a):
    c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def rot_y(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def rot_z(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

class Xf:
    """Transformation rigide p -> R p + t."""
    def __init__(self, R=None, t=None):
        self.R = np.eye(3) if R is None else R; self.t = np.zeros(3) if t is None else np.asarray(t, float)
    def __matmul__(self, o): return Xf(self.R @ o.R, self.R @ o.t + self.t)
    def ap(self, p): return self.R @ np.asarray(p, float) + self.t

def pivot(px, R):
    px = np.asarray(px, float); return Xf(R, px - R @ px)

def bone(pv, fwd=0, side=0, twist=0):
    """fwd : vers l'avant (°) ; side : z (°, + = vers +x) ; twist : autour de y."""
    R = rot_z(math.radians(side)) @ rot_x(math.radians(-fwd)) @ rot_y(math.radians(twist))
    return pivot(pv, R)

# Une face : origine, axe u, axe v (monde, avant transformation), source texture (image, u0, v0, tw, th, flipu, flipv)
def box_faces(f, t, img, U, V, w, h, d, inflate=0.0, mirror=False):
    x0, y0, z0 = (f[i] - inflate for i in range(3)); x1, y1, z1 = (t[i] + inflate for i in range(3))
    reg = {"top": (U + d, V, w, d), "bottom": (U + d + w, V, w, d), "right": (U, V + d, d, h),
           "front": (U + d, V + d, w, h), "left": (U + d + w, V + d, d, h), "back": (U + 2 * d + w, V + d, w, h)}
    F = []
    # (nom, origine (coin u=0,v=0), vec u, vec v, normale)
    F.append(("front", (x0, y1, z1), (x1 - x0, 0, 0), (0, y0 - y1, 0), (0, 0, 1)))
    F.append(("back", (x1, y1, z0), (x0 - x1, 0, 0), (0, y0 - y1, 0), (0, 0, -1)))
    F.append(("right", (x0, y1, z0), (0, 0, z1 - z0), (0, y0 - y1, 0), (-1, 0, 0)))
    F.append(("left", (x1, y1, z1), (0, 0, z0 - z1), (0, y0 - y1, 0), (1, 0, 0)))
    F.append(("top", (x0, y1, z0), (x1 - x0, 0, 0), (0, 0, z1 - z0), (0, 1, 0)))
    F.append(("bottom", (x0, y0, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), (0, -1, 0)))
    out = []
    for name, o, u, v, n in F:
        out.append(dict(o=np.array(o, float), u=np.array(u, float), v=np.array(v, float), n=np.array(n, float),
                        tex=(img, *reg[name]), overlay=inflate > 0))
    return out

def solid_faces(f, t, color):
    """Boîte unie (accessoires)."""
    (x0, y0, z0), (x1, y1, z1) = f, t
    F = [((x0, y1, z1), (x1 - x0, 0, 0), (0, y0 - y1, 0), (0, 0, 1)), ((x1, y1, z0), (x0 - x1, 0, 0), (0, y0 - y1, 0), (0, 0, -1)),
         ((x0, y1, z0), (0, 0, z1 - z0), (0, y0 - y1, 0), (-1, 0, 0)), ((x1, y1, z1), (0, 0, z0 - z1), (0, y0 - y1, 0), (1, 0, 0)),
         ((x0, y1, z0), (x1 - x0, 0, 0), (0, 0, z1 - z0), (0, 1, 0)), ((x0, y0, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), (0, -1, 0))]
    return [dict(o=np.array(o, float), u=np.array(u, float), v=np.array(v, float), n=np.array(n, float), color=color) for o, u, v, n in F]

def sprite_faces(sprite, px=0.62, thick=0.62, glow=()):
    """Sprite 16x16 extrudé (comme les objets tenus en jeu). Coin bas-gauche du sprite en (0,0,0), plan xy,
    centré en z. Renvoie des faces colorées ; seules les faces extérieures sont émises."""
    a = np.array(sprite.convert("RGBA")); H, W = a.shape[:2]
    op = a[:, :, 3] > 0
    F = []
    z0, z1 = -thick / 2, thick / 2
    for j in range(H):
        for i in range(W):
            if not op[j, i]: continue
            c = tuple(int(v) for v in a[j, i, :3]); g = c in glow
            x0, x1 = i * px, (i + 1) * px; y1, y0 = (H - j) * px, (H - j - 1) * px
            def add(o, u, v, n): F.append(dict(o=np.array(o, float), u=np.array(u, float), v=np.array(v, float), n=np.array(n, float), color=c, glow=g))
            add((x0, y1, z1), (px, 0, 0), (0, -px, 0), (0, 0, 1))
            add((x1, y1, z0), (-px, 0, 0), (0, -px, 0), (0, 0, -1))
            if i == 0 or not op[j, i - 1]: add((x0, y1, z0), (0, 0, thick), (0, -px, 0), (-1, 0, 0))
            if i == W - 1 or not op[j, i + 1]: add((x1, y1, z1), (0, 0, -thick), (0, -px, 0), (1, 0, 0))
            if j == 0 or not op[j - 1, i]: add((x0, y1, z0), (px, 0, 0), (0, 0, thick), (0, 1, 0))
            if j == H - 1 or not op[j + 1, i]: add((x0, y0, z1), (px, 0, 0), (0, 0, -thick), (0, -1, 0))
    return F

def xform(faces, X):
    out = []
    for f in faces:
        g = dict(f); g["o"] = X.ap(f["o"]); g["u"] = X.R @ f["u"]; g["v"] = X.R @ f["v"]; g["n"] = X.R @ f["n"]; out.append(g)
    return out

# ---------------------------------------------------------------- modèle joueur
def player(skin, pose, slim=None):
    img = np.array(skin.convert("RGBA"))
    if slim is None: slim = img[20, 54, 3] == 0
    aw = 3 if slim else 4
    P = pose
    body_x = bone((0, 12, 0), P.get("body", (0, 0, 0))[0], P.get("body", (0, 0, 0))[1], P.get("body", (0, 0, 0))[2])
    parts = {}
    def part(name, f, t, U, V, OU, OV, w, h, d, X, infl):
        fs = box_faces(f, t, img, U, V, w, h, d) + box_faces(f, t, img, OU, OV, w, h, d, inflate=infl)
        parts[name] = (fs, X)
    hd = P.get("head", (0, 0, 0))
    Xh = body_x @ bone((0, 24, 0), hd[0], hd[1], hd[2])
    part("head", (-4, 24, -4), (4, 32, 4), 0, 0, 32, 0, 8, 8, 8, Xh, 0.5)
    part("body", (-4, 12, -2), (4, 24, 2), 16, 16, 16, 32, 8, 12, 4, body_x, 0.25)
    ra, la = P.get("rarm", (0, 0, 0)), P.get("larm", (0, 0, 0))
    Xra = body_x @ bone((-5, 22, 0), *ra); Xla = body_x @ bone((5, 22, 0), *la)
    part("rarm", (-4 - aw, 12, -2), (-4, 24, 2), 40, 16, 40, 32, aw, 12, 4, Xra, 0.25)
    part("larm", (4, 12, -2), (4 + aw, 24, 2), 32, 48, 48, 48, aw, 12, 4, Xla, 0.25)
    rl, ll = P.get("rleg", (0, 0, 0)), P.get("lleg", (0, 0, 0))
    part("rleg", (-4, 0, -2), (0, 12, 2), 0, 16, 0, 32, 4, 12, 4, bone((-2, 12, 0), *rl), 0.25)
    part("lleg", (0, 0, -2), (4, 12, 2), 16, 48, 0, 48, 4, 12, 4, bone((2, 12, 0), *ll), 0.25)
    faces = []
    for fs, X in parts.values(): faces += xform(fs, X)
    hands = {"r": Xra, "l": Xla, "rpos": np.array([-4 - aw / 2, 13, 0]), "lpos": np.array([4 + aw / 2, 13, 0])}
    return faces, hands

def held(sprite, hands, side="r", grip=(3, 3), angle=0, roll=0, yaw=0, px=0.62, glow=()):
    """Objet tenu : le pixel grip (i, j du sprite) est placé dans la main ; angle (°) incline l'objet
    vers l'avant autour de x, roll autour de z, yaw autour de y."""
    H = sprite.height
    F = sprite_faces(sprite, px, glow=glow)
    gx, gy = (grip[0] + 0.5) * px, (H - grip[1] - 0.5) * px
    R = rot_y(math.radians(yaw)) @ rot_x(math.radians(-angle)) @ rot_z(math.radians(roll))
    hp = hands[side + "pos"]
    X = Xf(R, hp - R @ np.array([gx, gy, 0.0]))
    return xform(F, hands[side] @ X)

# ---------------------------------------------------------------- rendu
def boxblur(a, r):
    for ax in (0, 1):
        p = np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in (0, 1)], mode="edge")
        c = np.cumsum(p, axis=ax)
        a = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return a

def render(faces, height_px=240, ss=4, yaw=-28, pitch=10, key=(-0.55, 0.75, 0.75), rim=(0.45, 0.12, -0.88),
           key_col=(1.0, 0.95, 0.86), rim_col=(0.55, 0.7, 1.0), rim_k=0.45, amb=0.5, ao=0.5):
    Ry = rot_y(math.radians(yaw)); Rx = rot_x(math.radians(pitch)); C = Rx @ Ry
    key = np.array(key) / np.linalg.norm(key); rim = np.array(rim) / np.linalg.norm(rim)
    # bornes
    pts = []
    for f in faces:
        for a in (0, 1):
            for b in (0, 1): pts.append(C @ (f["o"] + a * f["u"] + b * f["v"]))
    pts = np.array(pts); y0, y1 = pts[:, 1].min(), pts[:, 1].max(); x0, x1 = pts[:, 0].min(), pts[:, 0].max()
    S = height_px * ss / (y1 - y0) * 0.94
    W = int((x1 - x0) * S) + 8 * ss; H = int((y1 - y0) * S) + 8 * ss
    offx, offy = -x0 * S + 4 * ss, y1 * S + 4 * ss
    zbuf = np.full((H, W), -1e9); col = np.zeros((H, W, 3)); alpha = np.zeros((H, W)); nrm = np.zeros((H, W, 3))
    glowm = np.zeros((H, W), bool)
    for f in faces:
        n = C @ f["n"]
        if n[2] <= 1e-6: continue                                   # face dos à la caméra (caméra en +z)
        o = C @ f["o"]; u = C @ f["u"]; v = C @ f["v"]
        P0 = np.array([o[0] * S + offx, -o[1] * S + offy]); Pu = np.array([u[0] * S, -u[1] * S]); Pv = np.array([v[0] * S, -v[1] * S])
        cs = np.array([P0, P0 + Pu, P0 + Pv, P0 + Pu + Pv])
        bx0, by0 = np.floor(cs.min(0)).astype(int); bx1, by1 = np.ceil(cs.max(0)).astype(int)
        bx0, by0 = max(bx0, 0), max(by0, 0); bx1, by1 = min(bx1, W - 1), min(by1, H - 1)
        if bx1 < bx0 or by1 < by0: continue
        M = np.array([[Pu[0], Pv[0]], [Pu[1], Pv[1]]]); det = np.linalg.det(M)
        if abs(det) < 1e-9: continue
        Mi = np.linalg.inv(M)
        yy, xx = np.mgrid[by0:by1 + 1, bx0:bx1 + 1]
        dx = xx + 0.5 - P0[0]; dy = yy + 0.5 - P0[1]
        a = Mi[0, 0] * dx + Mi[0, 1] * dy; b = Mi[1, 0] * dx + Mi[1, 1] * dy
        inside = (a >= 0) & (a < 1) & (b >= 0) & (b < 1)
        if not inside.any(): continue
        z = o[2] + a * u[2] + b * v[2]
        if "tex" in f:
            img, U, V, tw, th = f["tex"]
            ti = np.clip((a * tw).astype(int), 0, tw - 1) + U; tj = np.clip((b * th).astype(int), 0, th - 1) + V
            rgba = img[tj, ti]
            inside &= rgba[:, :, 3] > 0
            c = rgba[:, :, :3].astype(float)
            if f.get("overlay"): z = z + 0.01
        else:
            c = np.broadcast_to(np.array(f["color"], float), inside.shape + (3,))
        sub = zbuf[by0:by1 + 1, bx0:bx1 + 1]
        m = inside & (z > sub)
        if not m.any(): continue
        sub[m] = z[m]
        col[by0:by1 + 1, bx0:bx1 + 1][m] = c[m]
        alpha[by0:by1 + 1, bx0:bx1 + 1][m] = 1
        nrm[by0:by1 + 1, bx0:bx1 + 1][m] = n
        glowm[by0:by1 + 1, bx0:bx1 + 1][m] = f.get("glow", False)
    # éclairage
    keyc = C @ key; rimc = C @ rim
    dk = np.clip((nrm * keyc).sum(2), 0, 1); dr = np.clip((nrm * rimc).sum(2), 0, 1)
    up = np.clip(nrm[:, :, 1] * 0.5 + 0.5, 0, 1)                    # ciel / sol (hémisphérique)
    # occlusion ambiante : ce qui est derrière ses voisins est assombri
    zf = np.where(alpha > 0, zbuf, np.nan)
    zb = np.nan_to_num(zf, nan=float(np.nanmin(zf)))
    occ = np.zeros_like(alpha)
    for r in (ss * 3, ss * 8):
        bl = boxblur(zb, r)
        occ += np.clip((bl - np.nan_to_num(zf, nan=0)) / (S * 2.2), 0, 1)
    occ = np.clip(occ / 2, 0, 1)
    shade = amb * (0.75 + 0.35 * up)[:, :, None] + dk[:, :, None] * np.array(key_col) * 0.82
    shade = shade * (1 - ao * occ)[:, :, None]
    out = col / 255 * shade + dr[:, :, None] ** 1.5 * np.array(rim_col) * rim_k
    out = np.where(glowm[:, :, None], col / 255 * 1.15, out)
    # contre-jour accentué sur la silhouette (bord de l'alpha)
    a_img = Image.fromarray((alpha * 255).astype(np.uint8))
    er = np.array(a_img.filter(ImageFilter.MinFilter(2 * ss + 1))) / 255
    edge = np.clip(alpha - er, 0, 1) * np.clip(dr * 2 + 0.25, 0, 1)
    out = out + edge[:, :, None] * np.array(rim_col) * 0.35
    out = np.clip(out, 0, 1)
    rgba = np.dstack([out * 255, alpha * 255]).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA")
    # réduction : prémultiplier pour éviter les franges
    pm = np.array(im).astype(float); pm[:, :, :3] *= pm[:, :, 3:4] / 255
    pmi = Image.fromarray(pm.astype(np.uint8), "RGBA").resize((W // ss, H // ss), Image.LANCZOS)
    r = np.array(pmi).astype(float); A = r[:, :, 3:4]
    r[:, :, :3] = np.where(A > 0, r[:, :, :3] * 255 / np.maximum(A, 1), 0)
    im = Image.fromarray(np.clip(r, 0, 255).astype(np.uint8), "RGBA")
    return im.crop(im.getbbox())
