"""Mini moteur de rendu 3D (perspective, z-buffer, ombres portées, lumières ponctuelles, brouillard, flou de profondeur)
pour composer des dioramas Minecraft (vrais blocs vanilla) avec un vrai skin posé au centre.
Unités : 1 pixel de texture (1 bloc = 16). y vers le haut, le personnage regarde vers +z.
"""
import math, os
import numpy as np
from PIL import Image

MC = "/home/claude/mc/assets/minecraft/textures"
_TEX = {}

def T(name, kind="block"):
    k = (kind, name)
    if k not in _TEX:
        im = Image.open(f"{MC}/{kind}/{name}.png").convert("RGBA")
        if im.height > im.width: im = im.crop((0, 0, im.width, im.width))       # textures animées : 1re image
        _TEX[k] = np.array(im)
    return _TEX[k]

def tinted(name, rgb, kind="block"):
    k = (kind, name, rgb)
    if k not in _TEX:
        a = T(name, kind).astype(float).copy(); a[:, :, :3] *= np.array(rgb) / 255; _TEX[k] = a.clip(0, 255).astype(np.uint8)
    return _TEX[k]

GRASS = (124, 189, 90); FOLIAGE = (96, 160, 46)

def face(o, u, v, n, tex=None, uv=(0, 0, 16, 16), color=None, glow=0.0, cast=True, char=False, two=False):
    return dict(o=np.asarray(o, float), u=np.asarray(u, float), v=np.asarray(v, float), n=np.asarray(n, float),
                tex=tex, uv=uv, color=color, glow=glow, cast=cast, char=char, two=two)

def box(f, t, tex, glow=0.0, skip=(), cast=True, uvo=None):
    """Boîte texturée façon modèle de bloc : tex = image (toutes faces) ou dict {top, bottom, side, north, south, east, west}.
    UV automatiques d'après la position dans le bloc (comme les modèles vanilla) ; uvo force l'origine du bloc."""
    x0, y0, z0 = f; x1, y1, z1 = t
    if uvo is None and abs(t[0] - f[0] - 16) < 1e-6 and abs(t[1] - f[1] - 16) < 1e-6 and abs(t[2] - f[2] - 16) < 1e-6:
        uvo = f                                                    # bloc entier : texture entière, jamais décalée
    bx, by, bz = uvo if uvo is not None else (16 * math.floor(x0 / 16 + 1e-6), 16 * math.floor(y0 / 16 + 1e-6), 16 * math.floor(z0 / 16 + 1e-6))
    lx0, lx1, ly0, ly1, lz0, lz1 = x0 - bx, x1 - bx, y0 - by, y1 - by, z0 - bz, z1 - bz
    def tx(k):
        if isinstance(tex, dict): return tex.get(k, tex.get("side"))
        return tex
    w, h, d = x1 - x0, y1 - y0, z1 - z0
    F = []
    if "front" not in skip: F.append(face((x0, y1, z1), (w, 0, 0), (0, -h, 0), (0, 0, 1), tx("south"), (lx0, 16 - ly1, w, h), glow=glow, cast=cast))
    if "back" not in skip: F.append(face((x1, y1, z0), (-w, 0, 0), (0, -h, 0), (0, 0, -1), tx("north"), (16 - lx1, 16 - ly1, w, h), glow=glow, cast=cast))
    if "right" not in skip: F.append(face((x0, y1, z0), (0, 0, d), (0, -h, 0), (-1, 0, 0), tx("west"), (lz0, 16 - ly1, d, h), glow=glow, cast=cast))
    if "left" not in skip: F.append(face((x1, y1, z1), (0, 0, -d), (0, -h, 0), (1, 0, 0), tx("east"), (16 - lz1, 16 - ly1, d, h), glow=glow, cast=cast))
    if "top" not in skip: F.append(face((x0, y1, z0), (w, 0, 0), (0, 0, d), (0, 1, 0), tx("top"), (lx0, lz0, w, d), glow=glow, cast=cast))
    if "bottom" not in skip: F.append(face((x0, y0, z1), (w, 0, 0), (0, 0, -d), (0, -1, 0), tx("bottom"), (lx0, 16 - lz1, w, d), glow=glow, cast=cast))
    return F

class World:
    """Grille de blocs pleins avec élimination des faces cachées + éléments libres."""
    def __init__(self): self.blocks = {}; self.extra = []
    def set(self, x, y, z, tex, glow=0.0, opaque=True): self.blocks[(x, y, z)] = (tex, glow, opaque)
    def fill(self, a, b, tex, **k):
        for x in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
            for y in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
                for z in range(min(a[2], b[2]), max(a[2], b[2]) + 1): self.set(x, y, z, tex, **k)
    def add(self, faces): self.extra += faces
    def faces(self):
        out = []
        nb = {"front": (0, 0, 1), "back": (0, 0, -1), "right": (-1, 0, 0), "left": (1, 0, 0), "top": (0, 1, 0), "bottom": (0, -1, 0)}
        for (x, y, z), (tex, glow, opq) in self.blocks.items():
            skip = []
            for k, d in nb.items():
                o = self.blocks.get((x + d[0], y + d[1], z + d[2]))
                if o and o[2] and opq: skip.append(k)
            if len(skip) == 6: continue
            out += box((x * 16, y * 16, z * 16), (x * 16 + 16, y * 16 + 16, z * 16 + 16), tex, glow=glow, skip=skip)
        return out + self.extra

# ---------------------------------------------------------------- caméra
class Cam:
    def __init__(self, pos, target, fov=40, W=200, H=300, ortho=None, up=(0, 1, 0)):
        self.pos = np.asarray(pos, float); f = np.asarray(target, float) - self.pos; self.f = f / np.linalg.norm(f)
        r = np.cross(self.f, up); self.r = r / np.linalg.norm(r); self.u = np.cross(self.r, self.f)
        self.W, self.H, self.ortho = W, H, ortho
        self.k = math.tan(math.radians(fov) / 2)
    def project(self, P):
        d = P - self.pos; z = d @ self.f; x = d @ self.r; y = d @ self.u
        if self.ortho:
            s = self.H / self.ortho; return x * s + self.W / 2, -y * s + self.H / 2, z
        s = self.H / 2 / self.k
        return x / z * s + self.W / 2, -y / z * s + self.H / 2, z
    def rays(self, xs, ys):
        if self.ortho:
            s = self.ortho / self.H
            O = self.pos + ((xs - self.W / 2) * s)[..., None] * self.r - ((ys - self.H / 2) * s)[..., None] * self.u
            D = np.broadcast_to(self.f, O.shape)
            return O, D
        s = 2 * self.k / self.H
        D = self.f + ((xs - self.W / 2) * s)[..., None] * self.r - ((ys - self.H / 2) * s)[..., None] * self.u
        return np.broadcast_to(self.pos, D.shape), D

def raster(faces, cam, need_attr=True):
    W, H = cam.W, cam.H
    T_ = np.full((H, W), np.inf); C = np.zeros((H, W, 3)); N = np.zeros((H, W, 3)); G = np.zeros((H, W)); CH = np.zeros((H, W), bool)
    for f in faces:
        o, u, v, n = f["o"], f["u"], f["v"], f["n"]
        cs = [o, o + u, o + v, o + u + v]
        if not cam.ortho:
            if (cam.pos - o) @ n <= 0 and not f["two"]: continue
        elif cam.f @ n >= 0 and not f["two"]: continue
        pr = [cam.project(c) for c in cs]
        if min(p[2] for p in pr) <= 0.5: continue
        xs = [p[0] for p in pr]; ys = [p[1] for p in pr]
        x0, x1 = max(int(math.floor(min(xs))), 0), min(int(math.ceil(max(xs))), W - 1)
        y0, y1 = max(int(math.floor(min(ys))), 0), min(int(math.ceil(max(ys))), H - 1)
        if x1 < x0 or y1 < y0: continue
        yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1].astype(float)
        O, D = cam.rays(xx + 0.5, yy + 0.5)
        w = O - o; nd = -D
        vxd = np.cross(v, nd); det = vxd @ u
        if np.all(np.abs(det) < 1e-12): continue
        det = np.where(np.abs(det) < 1e-12, 1e-12, det)
        a = (w * vxd).sum(-1) / det
        b = (np.cross(w, nd) * u).sum(-1) / det
        t = (np.cross(v, w) * u).sum(-1) / det
        m = (a >= 0) & (a < 1) & (b >= 0) & (b < 1) & (t > 0)
        if not m.any(): continue
        if f["tex"] is not None:
            img = f["tex"]; U, V, tw, th = f["uv"]
            ti = np.floor(U + np.clip(a, 0, 0.9999) * tw).astype(int) % img.shape[1]
            tj = np.floor(V + np.clip(b, 0, 0.9999) * th).astype(int) % img.shape[0]
            px = img[tj, ti]; m &= px[..., 3] > 100; col = px[..., :3].astype(float)
        else:
            col = np.broadcast_to(np.array(f["color"], float), m.shape + (3,))
        if f["char"]: t = t - 0.02
        sub = T_[y0:y1 + 1, x0:x1 + 1]; m &= t < sub
        if not m.any(): continue
        sub[m] = t[m]
        if need_attr:
            C[y0:y1 + 1, x0:x1 + 1][m] = col[m]
            nn = n if (cam.ortho or (cam.pos - o) @ n > 0) else -n
            N[y0:y1 + 1, x0:x1 + 1][m] = nn
            G[y0:y1 + 1, x0:x1 + 1][m] = f["glow"]
            CH[y0:y1 + 1, x0:x1 + 1][m] = f["char"]
    return T_, C, N, G, CH

def boxblur(a, r):
    if r < 1: return a
    for ax in (0, 1):
        pad = [(0, 0)] * a.ndim; pad[ax] = (r + 1, r)
        p = np.pad(a, pad, mode="edge"); c = np.cumsum(p, axis=ax)
        n = c.shape[ax]
        a = (np.take(c, range(2 * r + 1, n), axis=ax) - np.take(c, range(0, n - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return a

def blur(a, r, it=3):
    for _ in range(it): a = boxblur(a, r)
    return a

def shade(faces, cam, sun_dir=(-0.4, 1, 0.5), sun_col=(1, .95, .85), sun_k=0.9, amb_sky=(0.42, 0.46, 0.55), amb_gnd=(0.22, 0.18, 0.16),
          lights=(), fog_col=(0.1, 0.1, 0.12), fog=(200, 600), dof=(0, 0), sky=None, rim_col=(0.5, 0.6, 0.9), rim_k=0.35,
          shadow_res=900, ao_k=0.55, char_light=1.0, bloom=0.5, vignette=0.35, grade=None, rays=None):
    """Renvoie une image RGBA (W x H) suréchantillonnée au rendu de la caméra."""
    T_, C, N, G, CH = raster(faces, cam)
    hit = np.isfinite(T_)
    O, D = cam.rays(*np.meshgrid(np.arange(cam.W) + 0.5, np.arange(cam.H) + 0.5))
    P = O + D * np.where(hit, T_, 0)[..., None]
    alb = C / 255
    # ombre du soleil (carte d'ombre orthographique)
    sd = np.asarray(sun_dir, float); sd /= np.linalg.norm(sd)
    casters = [f for f in faces if f["cast"]]
    pts = np.array([f["o"] for f in casters]); ctr = pts.mean(0); ext = np.ptp(pts, 0).max() + 64
    lc = Cam(ctr + sd * 600, ctr, W=shadow_res, H=shadow_res, ortho=ext)
    lc.f = -sd; r = np.cross(lc.f, (0, 1, 0) if abs(sd[1]) < 0.99 else (1, 0, 0)); lc.r = r / np.linalg.norm(r); lc.u = np.cross(lc.r, lc.f)
    for f in casters: f["two"] = True
    LT = raster(casters, lc, need_attr=False)[0]
    for f in casters: f["two"] = False
    s = shadow_res / ext
    d = P - lc.pos; lx = (d @ lc.r) * s + shadow_res / 2; ly = -(d @ lc.u) * s + shadow_res / 2; lz = d @ lc.f
    lit = np.zeros(hit.shape)
    ndl0 = np.clip((N * sd).sum(-1), 0.05, 1)
    bias = 1.5 + 4.0 * np.sqrt(1 - ndl0 ** 2) / ndl0 * 0.35
    for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):              # PCF
        ix = np.clip((lx + ox).astype(int), 0, shadow_res - 1); iy = np.clip((ly + oy).astype(int), 0, shadow_res - 1)
        lit += (lz <= LT[iy, ix] + bias)
    lit /= 5
    ndl = np.clip((N * sd).sum(-1), 0, 1)
    hemi = np.clip(N[..., 1] * 0.5 + 0.5, 0, 1)[..., None]
    amb = np.array(amb_gnd) * (1 - hemi) + np.array(amb_sky) * hemi
    # occlusion ambiante (espace écran)
    tz = np.where(hit, T_, np.nan); fill = np.nanmax(tz) if np.isfinite(np.nanmax(tz)) else 0
    tz = np.nan_to_num(tz, nan=fill)
    occ = 0
    for rr in (2, 5, 11):
        rr = max(1, int(rr * cam.H / 300))
        occ = occ + np.clip((tz - blur(tz, rr, 2)) / (6 + rr * 1.5), 0, 1)
    occ = np.clip(occ / 2.2, 0, 1)
    light = amb * (1 - ao_k * occ)[..., None] + (ndl * lit * sun_k)[..., None] * np.array(sun_col)
    for (lp, lcol, rad) in lights:
        L = np.asarray(lp, float) - P; dist = np.linalg.norm(L, axis=-1) + 1e-6
        att = 1 / (1 + (dist / rad) ** 2)
        light = light + (np.clip((N * L).sum(-1) / dist, 0, 1) * 0.75 + 0.25)[..., None] * att[..., None] * np.array(lcol)
    light = np.where(CH[..., None], light * char_light, light)
    out = alb * light
    # contre-jour sur le personnage
    vd = -D / np.linalg.norm(D, axis=-1, keepdims=True)
    fres = (1 - np.clip((N * vd).sum(-1), 0, 1)) ** 2.5
    out = out + np.where(CH, fres, 0)[..., None] * np.array(rim_col) * rim_k
    out = np.where(G[..., None] > 0, alb * (0.6 + G[..., None]), out)
    # brouillard
    fz = np.clip((T_ - fog[0]) / (fog[1] - fog[0]), 0, 1) if True else 0
    fz = np.where(hit, fz, 1)
    skyimg = sky(cam.W, cam.H) if sky else np.broadcast_to(np.array(fog_col), out.shape)
    out = np.where(hit[..., None], out * (1 - fz[..., None]) + np.array(fog_col) * fz[..., None], skyimg)
    # flou de profondeur sur le décor
    if dof[1] > 0:
        bl = np.stack([blur(out[..., k], max(1, int(dof[1] * cam.H / 300)), 2) for k in range(3)], -1)
        k = np.clip((np.where(hit, T_, 1e4) - dof[0]) / 60, 0, 1)[..., None]
        k = np.where(CH[..., None], 0, k)
        out = out * (1 - k) + bl * k
    # bloom des zones lumineuses
    if bloom:
        br = np.clip(out - 0.8, 0, None)
        out = out + np.stack([blur(br[..., k], max(2, cam.H // 40), 3) for k in range(3)], -1) * bloom * 2.2
    if rays:                                                     # rayons de lumière (flou radial des zones lumineuses)
        k_, (sx, sy), thr = rays
        lum = out.mean(-1)
        src = np.clip(out - thr, 0, None) * (lum > thr)[..., None]
        if not CH.any(): pass
        src = np.where(CH[..., None], 0, src)
        acc = np.zeros_like(out); Lx, Ly = sx * cam.W, sy * cam.H
        im_ = [Image.fromarray(np.clip(src[..., c] * 255, 0, 255).astype(np.uint8)) for c in range(3)]
        n = 40
        for i in range(n):
            sc = 1 - i * 0.012
            M = (sc, 0, Lx * (1 - sc), 0, sc, Ly * (1 - sc))
            Minv = (1 / sc, 0, -Lx * (1 - sc) / sc, 0, 1 / sc, -Ly * (1 - sc) / sc)
            acc += np.stack([np.array(c.transform(c.size, Image.AFFINE, Minv, resample=Image.BILINEAR)) for c in im_], -1) / 255 * (0.96 ** i)
        out = out + acc / n * k_ * 6
    if grade: out = grade(out)
    if vignette:
        yy, xx = np.mgrid[0:cam.H, 0:cam.W]
        r2 = ((xx / cam.W - 0.5) ** 2 * 1.4 + (yy / cam.H - 0.45) ** 2)
        out = out * (1 - vignette * np.clip(r2 * 2.2, 0, 1))[..., None]
    out = np.clip(out, 0, 1)
    # tonemapping doux
    out = 1 - np.exp(-out * 1.9); out = out / (1 - math.exp(-1.9))
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), "RGB")

def sky_gradient(top, bottom, sun=None):
    def f(W, H):
        t = np.linspace(0, 1, H)[:, None, None]
        img = np.array(top) * (1 - t) + np.array(bottom) * t
        img = np.broadcast_to(img, (H, W, 3)).copy()
        if sun:
            sx, sy, r, c = sun
            yy, xx = np.mgrid[0:H, 0:W]
            d = np.sqrt((xx - sx * W) ** 2 + (yy - sy * H) ** 2) / (r * H)
            img += np.clip(1 - d, 0, 1)[..., None] ** 2 * np.array(c)
        return img
    return f
