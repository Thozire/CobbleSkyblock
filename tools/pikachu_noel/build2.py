"""Pikachu de Noël v2 : bonnet ajusté avec trous d'oreilles, écharpe tricotée nouée dans le dos,
textures 4x plus détaillées, animation de balancement (pompon, pans d'écharpe, clochette)."""
import json, math, random, copy, os
import numpy as np
from PIL import Image

B = '/home/claude/jar/x/assets/cobblemon/'
OUT = '/home/claude/work/out2/'
TEX = B + 'textures/pokemon/0025_pikachu/'
MOD = B + 'bedrock/pokemon/models/0025_pikachu/'
S = 4  # densité de la texture des accessoires (pixels par unité de modèle)

# ------------------------------------------------------------------ géométrie (2 passes : tailles puis UV)
SPECS = {}   # clé UV -> taille (w,h,d)


MATERIALS = {'fur', 'knit', 'knit_dark', 'rib'}
REGION = {}  # matériau -> (W, H) en unités


def box_wh(w, h, d):
    return 2 * (d + w), d + h


def spec(key, size):
    dims = [int(round(abs(v))) for v in size]
    if key in MATERIALS:
        W, H = box_wh(*dims)
        w0, h0 = REGION.get(key, (0, 0))
        REGION[key] = (max(w0, W), max(h0, H))
    else:
        SPECS.setdefault(key, dims)
    return key


def allocate():
    used = np.load('/home/claude/work/used.npy').copy()
    alloc = {}
    sizes = {k: box_wh(*SPECS[k]) for k in SPECS}
    sizes.update(REGION)
    order = sorted(sizes, key=lambda k: -(sizes[k][0] * sizes[k][1]))
    for k in order:
        W, H = sizes[k]
        done = False
        for v in range(0, 64 - H + 1):
            for u in range(0, 128 - W + 1):
                if not used[v:v + H, u:u + W].any():
                    used[v:v + H, u:u + W] = True
                    alloc[k] = (u, v); done = True
                    break
            if done:
                break
        if not done:
            raise SystemExit(f'pas de place pour {k} {W}x{H}')
    return alloc


ALLOC = {}


def C(key, origin, size, inflate=None, pivot=None, rotation=None):
    spec(key, size)
    c = {'origin': [round(x, 3) for x in origin], 'size': size, 'uv': list(ALLOC.get(key, (0, 0)))}
    if inflate:
        c['inflate'] = inflate
    if pivot is not None:
        c['pivot'] = pivot
        c['rotation'] = rotation
    return c


def bone(name, parent, pivot, cubes=(), rotation=None):
    b = {'name': name, 'parent': parent, 'pivot': pivot}
    if rotation:
        b['rotation'] = rotation
    if cubes:
        b['cubes'] = list(cubes)
    return b


def christmas_bones():
    bs = []
    # ---------- BONNET : posé sur le crâne, ajusté, avec deux trous pour les oreilles
    # trous : x de ±1 à ±5 (côté ouvert), z de -1 à +1.5 ; les oreilles y passent quelle que soit l'animation
    bs.append(bone('santa_hat', 'head_angle', [0, 19.5, 0], [
        # bordure de fourrure (bourrelet blanc) en 3 morceaux autour des trous
        C('fur', [-5, 18.25, -5], [10, 2, 4], inflate=0.15),
        C('fur', [-5, 18.25, 1.5], [10, 2, 3], inflate=0.15),
        C('fur', [-1, 18.25, -1], [2, 2, 2], inflate=0.1),
        # calotte rouge, ajustée au crâne
        C('knit', [-4.5, 20.25, -4.25], [9, 3, 3]),
        C('knit', [-4.5, 20.25, 1.5], [9, 3, 3]),
        C('knit', [-1, 20.25, -1.25], [2, 3, 3]),
        # doublure sombre au fond des trous (on ne voit plus le crâne jaune)
        C('lining', [1, 20.35, -1.25], [4, 0, 3]),
        C('lining', [-5, 20.35, -1.25], [4, 0, 3]),
        # écusson flocon doré sur le devant
        C('badge', [-1.5, 20.6, -4.32], [3, 3, 0]),
    ]))
    # cône qui retombe en arrière en 6 segments + pompon (articulés => courbe douce)
    cone = [  # (taille, décalage z de l'origine, rotation de repos)
        (7, -3.5, [-14, 0, 2]), (6, -2.75, [-26, 0, 4]), (5, -2.0, [-30, 0, 4]),
        (4, -1.25, [-32, 0, 4]), (3, -0.5, [-28, 0, 3]), (2, 0.25, [-22, 0, 2]),
    ]
    parent, y = 'santa_hat', 23.25
    for i, (w, z0, r) in enumerate(cone, 1):
        name = f'santa_hat_cone{i}'
        pz = z0 + w / 2
        bs.append(bone(name, parent, [0, y, pz], [C('knit' if i <= 3 else 'knit_dark', [-w / 2, y, z0], [w, 1.5, w])], rotation=r))
        parent, y = name, y + 1.5
    bs.append(bone('santa_hat_pompom', parent, [0, y, 1.25]))  # os animé (balancement), sans rotation de repos
    bs.append(bone('santa_hat_pompom_ball', 'santa_hat_pompom', [0, y + 1.5, 1.25], [
        C('fur', [-2, y - 0.25, -0.75], [4, 4, 4]),
        C('fur', [-1.5, y + 0.25, -0.25], [3, 3, 3], inflate=0.35,
          pivot=[0, y + 1.75, 1.25], rotation=[45, 45, 0]),
    ]))
    # houx (3 feuilles + 3 baies) sur le bord avant gauche
    bs.append(bone('santa_hat_holly', 'santa_hat', [3.5, 19.4, -5.2], [
        C('holly_leaf', [1.6, 18.9, -5.25], [3, 2, 0], pivot=[3.1, 19.9, -5.25], rotation=[0, -10, 28]),
        C('holly_leaf', [3.6, 19.3, -5.2], [3, 2, 0], pivot=[5.1, 20.3, -5.2], rotation=[0, 15, -24]),
        C('holly_leaf', [2.4, 20.2, -5.3], [3, 2, 0], pivot=[3.9, 21.2, -5.3], rotation=[0, 0, 82]),
        C('berry', [2.75, 19.55, -5.85], [1, 1, 1], inflate=-0.05),
        C('berry', [3.55, 19.0, -5.8], [1, 1, 1], inflate=-0.12),
        C('berry', [3.45, 19.95, -5.75], [1, 1, 1], inflate=-0.14),
    ]))
    # guirlande : ampoules qui brillent la nuit (couche émissive), enroulées sur le cône
    bulbs = [  # (segment, x, z) sur la surface du segment
        (1, -3.75, -2.0, 'bulb_r'), (2, 2.85, -1.0, 'bulb_g'), (3, -1.0, 2.85, 'bulb_b'),
        (4, -2.25, 0.5, 'bulb_y'), (5, 1.6, 0.6, 'bulb_r'),
    ]
    ys = {i: 23.25 + 1.5 * (i - 1) for i in range(1, 7)}
    for seg, x, z, col in bulbs:
        y0 = ys[seg] + 0.25
        bs.append(bone(f'santa_hat_bulb{seg}', f'santa_hat_cone{seg}', [x, y0, z],
                       [C(col, [x - 0.5, y0, z - 0.5], [1, 1, 1], inflate=-0.12)]))
    for i, (x, col) in enumerate([(-3.4, 'bulb_y'), (-0.4, 'bulb_b')]):
        bs.append(bone(f'santa_hat_bulb_brim{i}', 'santa_hat', [x, 18.9, -5.2],
                       [C(col, [x - 0.5, 18.75, -5.75], [1, 1, 1], inflate=-0.12)]))

    # ---------- MANCHONS DE FOURRURE autour de la base de chaque oreille (attachés à l'oreille => la suivent)
    bs.append(bone('ear_cuff_right', 'ear_right', [-3, 20.25, -0.25],
                   [C('fur', [-5.5, 19.25, -0.75], [5, 2, 1], inflate=0.22)]))
    bs.append(bone('ear_cuff_left', 'ear_left', [3, 20.25, -0.25],
                   [C('fur', [0.5, 19.25, -0.75], [5, 2, 1], inflate=0.22)]))

    # ---------- ÉCHARPE : deux tours autour du cou, nœud dans le dos, pans qui flottent
    bs.append(bone('scarf', 'neck', [0, 11, 0.5], [
        C('scarf_wrap', [-5, 10.0, -4.5], [10, 2, 9], inflate=0.15),
        C('rib', [-4.5, 9.0, -4.0], [9, 1, 8], inflate=0.25, pivot=[0, 9.5, 0.5], rotation=[0, 0, -5]),
    ]))
    bs.append(bone('scarf_knot', 'scarf', [3.25, 10.5, 5.0], [
        C('rib', [1.75, 9.25, 4.25], [3, 3, 2], inflate=0.1),
    ], rotation=[0, -12, 0]))
    bs.append(bone('scarf_tail_a', 'scarf_knot', [2.75, 9.6, 5.4]))  # os animés : pas de rotation de repos
    bs.append(bone('scarf_tail_a_rest', 'scarf_tail_a', [2.75, 9.6, 5.4], [
        C('rib', [1.25, 5.6, 5.0], [3, 4, 1]),
    ], rotation=[22, 0, 6]))
    bs.append(bone('scarf_tail_a_end', 'scarf_tail_a_rest', [2.75, 5.6, 5.5], [
        C('tail_a2', [1.25, 2.6, 5.0], [3, 3, 1]),
    ], rotation=[10, 0, -4]))
    bs.append(bone('scarf_tail_b', 'scarf_knot', [4.0, 9.4, 5.4]))
    bs.append(bone('scarf_tail_b_rest', 'scarf_tail_b', [4.0, 9.4, 5.4], [
        C('rib', [3.0, 5.9, 5.0], [2, 4, 1]),
    ], rotation=[30, 0, 24]))
    bs.append(bone('scarf_tail_b_end', 'scarf_tail_b_rest', [4.0, 5.9, 5.5], [
        C('tail_a2', [3.0, 3.4, 5.0], [2, 3, 1]),  # réutilise la même UV que tail_a2 (franges)
    ], rotation=[8, 0, 6]))
    # clochette dorée accrochée devant, sous le menton
    bs.append(bone('scarf_bell', 'scarf', [0, 9.4, -4.7]))  # animée
    bs.append(bone('scarf_bell_rest', 'scarf_bell', [0, 9.4, -4.7], [
        C('bell_loop', [-0.5, 8.9, -5.2], [1, 1, 1], inflate=-0.2),
        C('bell', [-1, 7.0, -5.75], [2, 2, 2], inflate=0.05),
        C('bell_rim', [-1.5, 6.7, -6.25], [3, 1, 3], inflate=-0.15),
    ]))
    return bs


# ------------------------------------------------------------------ peinture
def faces(key):
    u, v = ALLOC[key]
    w, h, d = SPECS[key]
    f = {'up': (u + d, v, w, d), 'down': (u + d + w, v, w, d), 'right': (u, v + d, d, h),
         'front': (u + d, v + d, w, h), 'left': (u + d + w, v + d, d, h), 'back': (u + 2 * d + w, v + d, w, h)}
    return {k: (x * S, y * S, w_ * S, h_ * S) for k, (x, y, w_, h_) in f.items() if w_ and h_}


def paint_region(img, key, fn):
    u, v = ALLOC[key]; W, H = REGION[key]
    x0, y0, w, h = u * S, v * S, W * S, H * S
    for j in range(h):
        for i in range(w):
            c = fn('front', i, j, w, h)
            img[y0 + j, x0 + i] = c if len(c) == 4 else (*c, 255)


def paint(img, key, fn):
    for name, (x, y, w, h) in faces(key).items():
        for j in range(h):
            for i in range(w):
                c = fn(name, i, j, w, h)
                img[y + j, x + i] = c if len(c) == 4 else (*c, 255)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3))


def hsh(*a):
    return (hash(a) & 0xffff) / 65535.0


def fur_fn(pal, seed, region=False):
    """fourrure bouclée : touffes rondes, ombre en bas, reflets."""
    W, Ws, Wd = pal['fur'], pal['fur_shade'], pal['fur_dark']

    def f(name, i, j, w, h):
        cx, cy = (i // 3) * 3 + 1, (j // 3) * 3 + 1 + ((i // 3) % 2)
        d = math.hypot(i - cx, j - cy)
        n = hsh(seed, name, i // 3, (j + (i // 3) % 2) // 3)
        c = W if n > 0.18 else mix(W, Ws, 0.6)
        if d > 1.45:
            c = mix(c, Ws, 0.45)
        if d > 1.9 and n < 0.35:
            c = mix(c, Wd, 0.35)
        if name in ('front', 'back', 'left', 'right') and not region:
            c = mix(c, Wd, (j / max(h - 1, 1)) ** 2 * 0.45)
        if name == 'down':
            c = mix(c, Wd, 0.55)
        if name == 'up' and n > 0.8:
            c = (255, 255, 255)
        return c
    return f


def knit_fn(pal, shade_top=0.0, shade_bottom=0.0, seed=0, region=False):
    """tricot jersey : colonnes de mailles en V, ombre progressive (plis)."""
    R, Rd, Rl = pal['hat'], pal['hat_dark'], pal['hat_light']

    def f(name, i, j, w, h):
        col, row = i % 4, j % 4
        # une maille = un V sur 4x4 px
        v_shape = (col in (0, 3) and row in (0, 1)) or (col in (1, 2) and row in (1, 2))
        c = mix(R, Rl, 0.55) if v_shape and row < 2 else R
        if col in (1, 2) and row == 3:
            c = mix(R, Rd, 0.32)
        if (col == 0 and row == 3):
            c = mix(R, Rd, 0.18)
        t = (j % 6) / 5 if region else j / max(h - 1, 1)  # en région : pli tous les 2 unités
        c = mix(c, Rd, shade_top * (1 - t) + shade_bottom * t + (0.18 * t * t if region else 0))
        if name == 'down':
            c = mix(c, Rd, 0.6)
        if name == 'up':
            c = mix(c, Rl, 0.12)
        if hsh(seed, name, i, j) > 0.97:
            c = mix(c, Rd, 0.4)
        return c
    return f


def fair_isle_fn(pal, seed=0):
    """écharpe jacquard : bandes, zigzag et petits flocons tricotés."""
    S1, S2, S3, Sd = pal['scarf'], pal['scarf2'], pal['scarf3'], pal['scarf_dark']
    flake = ['..#..', '#.#.#', '.###.', '#.#.#', '..#..']

    def f(name, i, j, w, h):
        if name in ('front', 'back', 'left', 'right'):
            # j : 0..h (8 px de haut pour 2 unités)
            y = j * 8 // max(h, 1)
            if y in (0, 7):
                c = S3
            elif y in (1, 6):
                c = S2 if (i // 2) % 2 == 0 else S1
            else:
                fx, fy = (i % 7) - 1, y - 2  # flocons tous les 7 px
                if 0 <= fx < 5 and 0 <= fy < 4 and flake[fy + (1 if fy >= 2 else 0)][fx] == '#':
                    c = S2
                else:
                    c = S1
        else:
            stripe = (j // 4) % 3
            c = (S1, S2, S3)[stripe] if name == 'up' else mix(S1, Sd, 0.5)
        if (i + j) % 2 and c == S1:
            c = mix(c, Sd, 0.15)
        return c
    return f


def ribbed_fn(pal, fringe=False):
    S1, S2, S3, Sd = pal['scarf'], pal['scarf2'], pal['scarf3'], pal['scarf_dark']
    W, Ws = pal['fur'], pal['fur_shade']

    def f(name, i, j, w, h):
        band = (j // 3) % 4
        c = (S1, S1, S2, S3)[band]
        if i % 2:
            c = mix(c, Sd, 0.2)
        if fringe and j >= h - 4:
            if (i % 3) == 2:
                return (0, 0, 0, 0)
            return W if (i % 3) == 0 else Ws
        return c
    return f


def gold_fn(pal, kind):
    Au, Ad, Al = pal['gold'], pal['gold_dark'], pal['gold_light']

    def f(name, i, j, w, h):
        if kind == 'bell':
            t = j / max(h - 1, 1)
            c = mix(Al, Ad, t * 0.9)
            if name == 'front' and abs(i - w * 0.32) < 1.2 and j < h * 0.6:
                c = (255, 255, 240)  # reflet
            if name == 'front' and abs(i - w / 2) < 1 and j > h * 0.65:
                c = mix(Ad, (60, 40, 10), 0.5)  # fente
            if name == 'down':
                c = (70, 46, 12)
            return c
        if kind == 'rim':
            return mix(Au, Ad, 0.3) if name != 'up' else Al
        return Ad
    return f


def badge_fn(pal):
    """flocon doré à 6 branches sur fond transparent (12x12 px)."""
    Au, Ad, Al = pal['gold'], pal['gold_dark'], pal['gold_light']

    def f(name, i, j, w, h):
        cx, cy = (w - 1) / 2, (h - 1) / 2
        x, y = i - cx, j - cy
        r = math.hypot(x, y)
        a = math.degrees(math.atan2(y, x)) % 60
        on_arm = r <= 5.6 and (min(a, 60 - a) * math.pi / 180 * r < 0.75)
        twig = 2.2 < r < 4.2 and abs(min(a, 60 - a) * math.pi / 180 * r - (r - 2.2) * 0.8) < 0.6
        if r < 1.2 or on_arm or twig:
            return Al if (x + y) < 0 else Au
        return (0, 0, 0, 0)
    return f


def leaf_fn(pal):
    G, Gd, Gl = pal['leaf'], pal['leaf_dark'], pal['leaf_light']

    def f(name, i, j, w, h):  # feuille de houx 12x8 : dents, nervure, reflet
        x = i / (w - 1); y = (j - (h - 1) / 2) / ((h - 1) / 2)
        half = 0.85 * math.sin(math.pi * x) ** 0.7
        teeth = 0.18 * abs(math.sin(x * math.pi * 3))
        if abs(y) > half - teeth or x < 0.03:
            return (0, 0, 0, 0)
        if abs(y) < 0.12:
            return Gl
        c = G if y < 0 else Gd
        if abs(y) > half - teeth - 0.18:
            c = mix(c, Gd, 0.5)
        return c
    return f


def berry_fn(pal):
    def f(name, i, j, w, h):
        if name == 'up' or (i < 2 and j < 2):
            return pal['berry_light']
        return pal['berry'] if j < h - 1 else mix(pal['berry'], (60, 0, 0), 0.4)
    return f


def bulb_fn(col, glow=False):
    def f(name, i, j, w, h):
        if name == 'up':
            return (40, 60, 40)  # culot
        if glow:
            return col
        return mix(col, (255, 255, 255), 0.5) if (i == 1 and j == 1) else col
    return f


def make_texture(base_png, pal, seed=7):
    base = Image.open(TEX + base_png).convert('RGBA')
    img = np.array(base.resize((128 * S, 64 * S), Image.NEAREST))
    paint_region(img, 'fur', fur_fn(pal, seed, region=True))
    paint_region(img, 'knit', knit_fn(pal, 0.0, 0.0, 1, region=True))
    paint_region(img, 'knit_dark', knit_fn(pal, 0.25, 0.25, 2, region=True))
    paint_region(img, 'rib', ribbed_fn(pal))
    paint(img, 'lining', lambda n, i, j, w, h: mix(pal['hat_dark'], (30, 0, 6), 0.55))
    paint(img, 'badge', badge_fn(pal))
    paint(img, 'holly_leaf', leaf_fn(pal))
    paint(img, 'berry', berry_fn(pal))
    for k in ('bulb_r', 'bulb_g', 'bulb_b', 'bulb_y'):
        paint(img, k, bulb_fn(pal[k]))
    paint(img, 'scarf_wrap', fair_isle_fn(pal))
    paint(img, 'tail_a2', ribbed_fn(pal, fringe=True))
    paint(img, 'bell', gold_fn(pal, 'bell'))
    paint(img, 'bell_rim', gold_fn(pal, 'rim'))
    paint(img, 'bell_loop', gold_fn(pal, 'loop'))
    return img


def make_emissive(base_png, pal):
    base = Image.open(TEX + base_png).convert('RGBA')
    img = np.array(base.resize((128 * S, 64 * S), Image.NEAREST))
    for k in ('bulb_r', 'bulb_g', 'bulb_b', 'bulb_y'):
        paint(img, k, bulb_fn(pal[k], glow=True))
        # le culot ne brille pas
        x, y, w, h = faces(k)['up']; img[y:y + h, x:x + w] = 0
    return img


NORMAL = dict(
    hat=(200, 26, 42), hat_dark=(112, 10, 24), hat_light=(236, 70, 76),
    fur=(250, 250, 246), fur_shade=(222, 226, 234), fur_dark=(170, 180, 198),
    leaf=(34, 126, 58), leaf_dark=(16, 78, 36), leaf_light=(120, 196, 112),
    berry=(220, 20, 34), berry_light=(255, 150, 150),
    bulb_r=(255, 72, 72), bulb_g=(96, 255, 128), bulb_b=(100, 170, 255), bulb_y=(255, 216, 80),
    scarf=(196, 26, 44), scarf2=(246, 246, 240), scarf3=(30, 120, 62), scarf_dark=(100, 10, 22),
    gold=(236, 184, 44), gold_dark=(150, 98, 16), gold_light=(255, 240, 160),
)
SHINY = dict(NORMAL,  # Noël givré : bleu glacier et argent
             hat=(52, 108, 204), hat_dark=(20, 50, 124), hat_light=(126, 182, 244),
             scarf=(70, 130, 210), scarf2=(250, 252, 255), scarf3=(170, 210, 245), scarf_dark=(24, 60, 130),
             gold=(214, 222, 236), gold_dark=(128, 140, 166), gold_light=(255, 255, 255))


def build_model(src, ident):
    g = json.load(open(MOD + src))
    geo = g['minecraft:geometry'][0]
    geo['description']['identifier'] = ident
    geo['description']['visible_bounds_height'] = 5
    geo['bones'].extend(christmas_bones())
    return g


ANIM = {
    'format_version': '1.8.0',
    'animations': {
        'animation.pikachu_christmas.sway': {
            'loop': True, 'animation_length': 4,
            'bones': {
                'santa_hat_cone3': {'rotation': ['math.sin(q.anim_time*90*2)*2.5', 0, 'math.sin(q.anim_time*90-30)*2']},
                'santa_hat_cone5': {'rotation': ['math.sin(q.anim_time*90*2-40)*4', 0, 'math.sin(q.anim_time*90-60)*3']},
                'santa_hat_pompom': {'rotation': ['math.sin(q.anim_time*90*2-80)*9', 0, 'math.sin(q.anim_time*90-90)*7']},
                'scarf_tail_a': {'rotation': ['math.sin(q.anim_time*90*2)*5', 0, 'math.sin(q.anim_time*90*2-45)*3']},
                'scarf_tail_b': {'rotation': ['math.sin(q.anim_time*90*2-60)*6', 0, 'math.sin(q.anim_time*90*2-100)*4']},
                'scarf_bell': {'rotation': ['math.sin(q.anim_time*90*2-20)*4', 0, 'math.sin(q.anim_time*90*4)*10']},
            },
        }
    },
}


def build_poser():
    p = json.load(open(B + 'bedrock/pokemon/posers/0025_pikachu/pikachu.json'))
    for pose in p['poses'].values():
        pose.setdefault('animations', []).append("q.bedrock('pikachu_christmas', 'sway')")
    return p


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    christmas_bones()          # passe 1 : collecte des tailles
    ALLOC.update(allocate())   # placement des UV (les plus grandes d'abord)
    male = build_model('pikachu_male.geo.json', 'geometry.pikachu_christmas_male')
    female = build_model('pikachu_female.geo.json', 'geometry.pikachu_christmas_female')
    json.dump(male, open(OUT + 'pikachu_christmas_male.geo.json', 'w'), indent=1)
    json.dump(female, open(OUT + 'pikachu_christmas_female.geo.json', 'w'), indent=1)
    Image.fromarray(make_texture('pikachu.png', NORMAL)).save(OUT + 'pikachu_christmas.png')
    Image.fromarray(make_texture('pikachu_shiny.png', SHINY)).save(OUT + 'pikachu_christmas_shiny.png')
    Image.fromarray(make_emissive('pikachu_emissive.png', NORMAL)).save(OUT + 'pikachu_christmas_emissive.png')
    Image.fromarray(make_emissive('pikachu_emissive_shiny.png', NORMAL)).save(OUT + 'pikachu_christmas_emissive_shiny.png')
    json.dump(ANIM, open(OUT + 'pikachu_christmas.animation.json', 'w'), indent=1)
    json.dump(build_poser(), open(OUT + 'pikachu_christmas.json', 'w'), indent=1)
    print(ALLOC); print(REGION)
