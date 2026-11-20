"""Aperçu logiciel d'un modèle Bedrock (box UV) : sert à vérifier le placement des accessoires."""
import json, sys, math
import numpy as np
from PIL import Image, ImageDraw


def rot(rx, ry, rz):
    # convention Blockbench/Cobblemon : rx positif penche le haut vers l'avant (-Z)
    a, b, c = math.radians(-rx), math.radians(ry), math.radians(rz)
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def bone_mats(bones):
    by = {b['name']: b for b in bones}
    cache = {}

    def M(name):
        if name in cache:
            return cache[name]
        b = by[name]
        p = np.array(b.get('pivot', [0, 0, 0]), float)
        R = rot(*b.get('rotation', [0, 0, 0]))
        T = np.eye(4); T[:3, :3] = R; T[:3, 3] = p - R @ p
        if b.get('parent'):
            T = M(b['parent']) @ T
        cache[name] = T
        return T
    return M


def quads(geo, tex, hide=()):
    bones = geo['bones']
    M = bone_mats(bones)
    out = []
    for b in bones:
        if b['name'] in hide:
            continue
        Tb = M(b['name'])
        for c in b.get('cubes', []):
            T = Tb
            if 'rotation' in c:
                p = np.array(c['pivot'], float); R = rot(*c['rotation'])
                Tc = np.eye(4); Tc[:3, :3] = R; Tc[:3, 3] = p - R @ p
                T = Tb @ Tc
            inf = c.get('inflate', 0)
            x0, y0, z0 = c['origin']; w, h, d = c['size']
            u, v = c['uv']
            W, H, D = int(round(abs(w))), int(round(abs(h))), int(round(abs(d)))
            X0, Y0, Z0 = x0 - inf, y0 - inf, z0 - inf
            sx = (w + 2 * inf) / max(W, 1e-9) if W else 0
            sy = (h + 2 * inf) / max(H, 1e-9) if H else 0
            sz = (d + 2 * inf) / max(D, 1e-9) if D else 0
            X1, Y1, Z1 = X0 + w + 2 * inf, Y0 + h + 2 * inf, Z0 + d + 2 * inf

            def P(x, y, z):
                q = T @ np.array([x, y, z, 1.0]); return q[:3]

            def texel(px, py):
                if px >= tex.shape[1] or py >= tex.shape[0]:
                    print('UV hors texture', b['name'], c['uv'], file=sys.stderr)
                    return (255, 0, 255, 255)
                return tex[py, px]
            # front (z=Z0)
            for j in range(H):
                for i in range(W):
                    col = texel(u + D + i, v + D + j)
                    xa, xb = X0 + i * sx, X0 + (i + 1) * sx
                    ya, yb = Y1 - j * sy, Y1 - (j + 1) * sy
                    out.append(([P(xa, ya, Z0), P(xb, ya, Z0), P(xb, yb, Z0), P(xa, yb, Z0)], col))
                    col = texel(u + 2 * D + W + i, v + D + j)  # back
                    xa, xb = X1 - i * sx, X1 - (i + 1) * sx
                    out.append(([P(xa, ya, Z1), P(xb, ya, Z1), P(xb, yb, Z1), P(xa, yb, Z1)], col))
            for j in range(H):
                for i in range(D):
                    ya, yb = Y1 - j * sy, Y1 - (j + 1) * sy
                    col = texel(u + i, v + D + j)  # right side x=X0, col D-1 = front
                    za, zb = Z1 - i * sz, Z1 - (i + 1) * sz
                    out.append(([P(X0, ya, za), P(X0, ya, zb), P(X0, yb, zb), P(X0, yb, za)], col))
                    col = texel(u + D + W + i, v + D + j)  # left side x=X1, col 0 = front
                    za, zb = Z0 + i * sz, Z0 + (i + 1) * sz
                    out.append(([P(X1, ya, za), P(X1, ya, zb), P(X1, yb, zb), P(X1, yb, za)], col))
            for j in range(D):
                for i in range(W):
                    xa, xb = X0 + i * sx, X0 + (i + 1) * sx
                    col = texel(u + D + i, v + j)  # top, row D-1 = front
                    za, zb = Z1 - j * sz, Z1 - (j + 1) * sz
                    out.append(([P(xa, Y1, za), P(xb, Y1, za), P(xb, Y1, zb), P(xa, Y1, zb)], col))
                    col = texel(u + D + W + i, v + j)  # bottom, row 0 = front
                    za, zb = Z0 + j * sz, Z0 + (j + 1) * sz
                    out.append(([P(xa, Y0, za), P(xb, Y0, za), P(xb, Y0, zb), P(xa, Y0, zb)], col))
    return out


HIDE_DEFAULT = ('eye_emote', 'eyelid', 'mouth_open', 'tongue', 'acting_teeth', 'eyeshine_right2', 'eyeshine_left2')


def render(geo, tex, yaw, pitch, size=560, scale=15, hide=HIDE_DEFAULT):
    bones = [b for b in geo['bones'] if not any(h in b['name'] for h in hide)]
    qs = quads(dict(geo, bones=bones), tex)
    R = rot(-pitch, 0, 0) @ rot(0, yaw, 0)
    S = size * 2  # suréchantillonnage
    col = np.zeros((S, S, 3)); col[:] = (34, 40, 58)
    zb = np.full((S, S), np.inf)
    L = np.array([0.35, 0.8, -0.5]); L /= np.linalg.norm(L)
    for pts, c in qs:
        if c[3] == 0:
            continue
        p = np.array([R @ q for q in pts])
        n = np.cross(p[1] - p[0], p[3] - p[0]); nn = np.linalg.norm(n)
        shade = 0.72 + 0.28 * abs(np.dot(n / nn, L)) if nn > 1e-9 else 1
        sx = S / 2 + p[:, 0] * scale * 2; sy = S * 0.8 - p[:, 1] * scale * 2
        for tri in ((0, 1, 2), (0, 2, 3)):
            ax, ay, az = sx[tri[0]], sy[tri[0]], p[tri[0], 2]
            bx, by, bz = sx[tri[1]], sy[tri[1]], p[tri[1], 2]
            cx, cy, cz = sx[tri[2]], sy[tri[2]], p[tri[2], 2]
            x0, x1 = int(max(0, np.floor(min(ax, bx, cx)))), int(min(S - 1, np.ceil(max(ax, bx, cx))))
            y0, y1 = int(max(0, np.floor(min(ay, by, cy)))), int(min(S - 1, np.ceil(max(ay, by, cy))))
            if x1 < x0 or y1 < y0:
                continue
            det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(det) < 1e-9:
                continue
            X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            l1 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / det
            l2 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / det
            l3 = 1 - l1 - l2
            m = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
            z = l1 * az + l2 * bz + l3 * cz
            sub = zb[y0:y1 + 1, x0:x1 + 1]
            m &= z < sub - 1e-4
            sub[m] = z[m]
            col[y0:y1 + 1, x0:x1 + 1][m] = np.array(c[:3]) * shade
    img = Image.fromarray(np.clip(col, 0, 255).astype('uint8')).resize((size, size), Image.LANCZOS)
    return img


if __name__ == '__main__':
    geo = json.load(open(sys.argv[1]))['minecraft:geometry'][0]
    tex = np.array(Image.open(sys.argv[2]).convert('RGBA'))
    views = [(0, 8), (35, 12), (-60, 10), (150, 15), (0, -60)]
    ims = [render(geo, tex, y, p) for y, p in views]
    sheet = Image.new('RGBA', (560 * len(ims), 560))
    for i, im in enumerate(ims):
        sheet.paste(im, (560 * i, 0))
    sheet.save(sys.argv[3])
