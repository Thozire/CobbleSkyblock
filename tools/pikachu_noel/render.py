"""Aperçu logiciel d'un modèle Bedrock (box UV) : sert à vérifier le placement des accessoires."""
import json, sys, math
import numpy as np
from PIL import Image, ImageDraw


def rot(rx, ry, rz):
    # convention Blockbench/Cobblemon : rx positif penche le haut vers l'avant (-Z)
    # Cobblemon : Y inversé à la conversion => X et Z s'inversent, Y reste
    a, b, c = math.radians(-rx), math.radians(ry), math.radians(-rz)
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
        if '_offset' in b:
            O = np.eye(4); O[:3, 3] = b['_offset']; T = O @ T
        if b.get('parent'):
            T = M(b['parent']) @ T
        cache[name] = T
        return T
    return M


def quads(geo, tex, hide=()):
    bones = geo['bones']
    M = bone_mats(bones)
    k = max(1, tex.shape[1] // int(geo['description'].get('texture_width', 128)))
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
            X1, Y1, Z1 = X0 + w + 2 * inf, Y0 + h + 2 * inf, Z0 + d + 2 * inf

            def P(x, y, z):
                q = T @ np.array([x, y, z, 1.0]); return q[:3]

            def face(tu, tv, tw, th, corner, ax_i, ax_j):
                """tw x th unités de texture ; corner + i*ax_i + j*ax_j parcourt la face."""
                n_i, n_j = tw * k, th * k
                for j in range(n_j):
                    for i in range(n_i):
                        py, px = tv * k + j, tu * k + i
                        if px >= tex.shape[1] or py >= tex.shape[0]:
                            continue
                        col = tex[py, px]
                        a0 = corner + ax_i * (i / n_i) + ax_j * (j / n_j)
                        a1 = corner + ax_i * ((i + 1) / n_i) + ax_j * (j / n_j)
                        a2 = corner + ax_i * ((i + 1) / n_i) + ax_j * ((j + 1) / n_j)
                        a3 = corner + ax_i * (i / n_i) + ax_j * ((j + 1) / n_j)
                        out.append(([P(*a0), P(*a1), P(*a2), P(*a3)], col))
            V = np.array
            if W and H:
                face(u + D, v + D, W, H, V([X0, Y1, Z0]), V([X1 - X0, 0, 0]), V([0, Y0 - Y1, 0]))          # avant
                face(u + 2 * D + W, v + D, W, H, V([X1, Y1, Z1]), V([X0 - X1, 0, 0]), V([0, Y0 - Y1, 0]))  # arrière
            if D and H:
                face(u, v + D, D, H, V([X0, Y1, Z1]), V([0, 0, Z0 - Z1]), V([0, Y0 - Y1, 0]))              # côté x0
                face(u + D + W, v + D, D, H, V([X1, Y1, Z0]), V([0, 0, Z1 - Z0]), V([0, Y0 - Y1, 0]))      # côté x1
            if W and D:
                face(u + D, v, W, D, V([X0, Y1, Z1]), V([X1 - X0, 0, 0]), V([0, 0, Z0 - Z1]))              # dessus
                face(u + D + W, v, W, D, V([X0, Y0, Z0]), V([X1 - X0, 0, 0]), V([0, 0, Z1 - Z0]))          # dessous
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
        sx = S / 2 + p[:, 0] * scale * 2; sy = S * getattr(sys.modules[__name__], "BASE", 0.86) - p[:, 1] * scale * 2
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


# ---------------------------------------------------------------- poses animées
def molang(v, t):
    if isinstance(v, (int, float)):
        return float(v)
    e = str(v).lower().replace('math.sin', 'msin').replace('math.cos', 'mcos').replace('q.anim_time', 'T') \
        .replace('query.anim_time', 'T').replace('math.abs', 'abs').replace('math.clamp', 'clamp')
    env = {'msin': lambda d: math.sin(math.radians(d)), 'mcos': lambda d: math.cos(math.radians(d)),
           'T': t, 'abs': abs, 'clamp': lambda x, a, b: max(a, min(b, x)), 'math': math}
    try:
        return float(eval(e, {'__builtins__': {}}, env))
    except Exception:
        return 0.0


def channel(ch, t):
    if isinstance(ch, (int, float, str)):
        return [molang(ch, t)] * 3
    if isinstance(ch, list):
        return [molang(x, t) for x in ch]
    # images clés : on prend la plus proche avant t (approximation suffisante pour l'aperçu)
    keys = sorted(ch.items(), key=lambda kv: float(kv[0]))
    best = keys[0][1]
    for k, val in keys:
        if float(k) <= t:
            best = val
    if isinstance(best, dict):
        best = best.get('post', best.get('pre'))
    return [molang(x, t) for x in best]


def posed(geo, anims, t=0.0):
    """Renvoie une copie du modèle avec les rotations/positions des animations ajoutées."""
    g = json.loads(json.dumps(geo))
    by = {b['name']: b for b in g['bones']}
    for an in anims:
        for bone, ch in an.get('bones', {}).items():
            if bone not in by:
                continue
            b = by[bone]
            if 'rotation' in ch:
                r = channel(ch['rotation'], t)
                base = b.get('rotation', [0, 0, 0])
                b['rotation'] = [base[i] + r[i] for i in range(3)]
            if 'position' in ch:
                p = channel(ch['position'], t)
                b['_offset'] = p
    return g
