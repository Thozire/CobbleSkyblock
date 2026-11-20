"""Génère Pikachu de Noël (modèles mâle/femelle, textures normale/shiny, couche émissive)."""
import json, copy, random
import numpy as np
from PIL import Image

B = '/home/claude/jar/x/assets/cobblemon/'
OUT = '/home/claude/work/out/'
TEX = B + 'textures/pokemon/0025_pikachu/'
MOD = B + 'bedrock/pokemon/models/0025_pikachu/'

used = np.load('/home/claude/work/used.npy')
ALLOC = {}


def alloc(key, W, H):
    """Place un bloc W x H libre dans l'atlas 128x64 (en évitant les pixels existants)."""
    if key in ALLOC:
        return ALLOC[key]
    for v in range(0, 64 - H + 1):
        for u in range(0, 128 - W + 1):
            if not used[v:v + H, u:u + W].any():
                used[v:v + H, u:u + W] = True
                ALLOC[key] = (u, v)
                return u, v
    raise SystemExit(f'pas de place pour {key} {W}x{H}')


def box_wh(size):
    w, h, d = [int(round(abs(s))) for s in size]
    return 2 * (d + w), d + h


def cube(key, origin, size, inflate=None, pivot=None, rotation=None):
    W, H = box_wh(size)
    u, v = alloc(key, W, H)
    c = {'origin': origin, 'size': size, 'uv': [u, v]}
    if inflate:
        c['inflate'] = inflate
    if pivot is not None:
        c['pivot'] = pivot
        c['rotation'] = rotation
    return c


# ------------------------------------------------------------------ géométrie
def christmas_bones():
    bones = []
    # Bonnet du Père Noël, posé sur la tête (suit le regard et toutes les animations de tête)
    bones.append({'name': 'santa_hat', 'parent': 'head_angle', 'pivot': [0, 19.5, 0], 'cubes': [
        cube('hat_brim', [-4.5, 18.5, -4.5], [9, 2, 9], inflate=0.6),
        cube('hat_base', [-4, 20.5, -4], [8, 3, 8]),
    ]})
    bones.append({'name': 'santa_hat_mid', 'parent': 'santa_hat', 'pivot': [0, 23.5, 0.5],
                  'rotation': [-28, 0, 8], 'cubes': [cube('hat_mid', [-3, 23.25, -2.5], [6, 3, 6])]})
    bones.append({'name': 'santa_hat_upper', 'parent': 'santa_hat_mid', 'pivot': [0, 26.25, 1],
                  'rotation': [-42, 0, 12], 'cubes': [cube('hat_upper', [-2, 26, -1], [4, 3, 4])]})
    bones.append({'name': 'santa_hat_tip', 'parent': 'santa_hat_upper', 'pivot': [0, 29, 1],
                  'rotation': [-48, 0, 10], 'cubes': [cube('hat_tip', [-1, 28.75, 0], [2, 2, 2])]})
    bones.append({'name': 'santa_hat_pompom', 'parent': 'santa_hat_tip', 'pivot': [0, 30.75, 1],
                  'cubes': [cube('pompom', [-1.5, 30.5, -0.5], [3, 3, 3], inflate=0.3)]})
    # Houx sur le côté gauche du bord
    bones.append({'name': 'santa_hat_holly', 'parent': 'santa_hat', 'pivot': [3, 19.5, -5.1], 'cubes': [
        cube('holly_leaf', [1.2, 19.0, -5.2], [3, 2, 0], pivot=[2.7, 20, -5.2], rotation=[0, 0, 25]),
        cube('holly_leaf', [3.0, 19.4, -5.15], [3, 2, 0], pivot=[4.5, 20.4, -5.15], rotation=[0, 0, -30]),
        cube('holly_berry', [2.3, 19.9, -5.75], [1, 1, 1], inflate=-0.05),
        cube('holly_berry', [3.2, 19.4, -5.7], [1, 1, 1], inflate=-0.1),
        cube('holly_berry', [2.6, 18.9, -5.65], [1, 1, 1], inflate=-0.1),
    ]})
    # Guirlande lumineuse autour du bord (couche émissive => brille la nuit)
    bulbs = []
    cols = ['bulb_r', 'bulb_g', 'bulb_b', 'bulb_y']
    spots = [  # (x, z) centre de l'ampoule, posée sur la face du bord
        (-3.6, -5.45), (-1.0, -5.45),
        (-5.45, -2.8), (-5.45, 0.2), (-5.45, 3.2),
        (-2.6, 5.45), (0.4, 5.45), (3.4, 5.45),
        (5.45, 3.0), (5.45, 0.0), (5.45, -2.9),
    ]
    for i, (x, z) in enumerate(spots):
        bulbs.append(cube(cols[i % 4], [x - 0.5, 18.35, z - 0.5], [1, 1, 1], inflate=-0.15))
    bones.append({'name': 'santa_hat_lights', 'parent': 'santa_hat', 'pivot': [0, 19, 0], 'cubes': bulbs})

    # Écharpe tricotée autour du cou (suit le torse et la respiration)
    bones.append({'name': 'scarf', 'parent': 'neck', 'pivot': [0, 11.25, 0.5], 'cubes': [
        cube('scarf_wrap', [-4.5, 10.5, -3.75], [9, 2, 8], inflate=0.5),
        cube('scarf_knot', [-2.75, 9.6, -5.1], [3, 2, 1], inflate=0.1),
    ]})
    bones.append({'name': 'scarf_tail', 'parent': 'scarf', 'pivot': [-1.25, 9.9, -4.6],
                  'rotation': [-10, 0, 7], 'cubes': [cube('scarf_tail1', [-2.75, 5.9, -5.1], [3, 4, 1])]})
    bones.append({'name': 'scarf_tail_end', 'parent': 'scarf_tail', 'pivot': [-1.25, 5.9, -4.6],
                  'rotation': [-6, 0, -5], 'cubes': [cube('scarf_tail2', [-2.75, 3.9, -5.1], [3, 2, 1])]})
    bones.append({'name': 'scarf_tail_b', 'parent': 'scarf', 'pivot': [0.25, 9.9, -4.6],
                  'rotation': [-14, 0, -9], 'cubes': [cube('scarf_tail3', [-0.75, 6.9, -5.0], [2, 3, 1])]})
    bones.append({'name': 'scarf_bell', 'parent': 'scarf', 'pivot': [-1.25, 9.6, -5.6], 'cubes': [
        cube('bell', [-2.25, 8.1, -6.4], [2, 2, 2], inflate=-0.05),
        cube('bell_loop', [-1.75, 9.9, -5.95], [1, 1, 1], inflate=-0.25),
    ]})
    return bones


def build_model(src, ident):
    g = json.load(open(MOD + src))
    geo = g['minecraft:geometry'][0]
    geo['description']['identifier'] = ident
    geo['description']['visible_bounds_height'] = 4.5
    geo['bones'].extend(christmas_bones())
    return g


# ------------------------------------------------------------------ texture
def faces(key, size):
    u, v = ALLOC[key]
    w, h, d = [int(round(abs(s))) for s in size]
    return {
        'up': (u + d, v, w, d), 'down': (u + d + w, v, w, d),
        'right': (u, v + d, d, h), 'front': (u + d, v + d, w, h),
        'left': (u + d + w, v + d, d, h), 'back': (u + 2 * d + w, v + d, w, h),
    }


def paint(img, key, size, fn):
    for name, (x, y, w, h) in faces(key, size).items():
        for j in range(h):
            for i in range(w):
                img[y + j, x + i] = (*fn(name, i, j, w, h), 255)


def lerp(a, b, t):
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


def make_texture(base_png, pal, seed):
    rnd = random.Random(seed)
    img = np.array(Image.open(TEX + base_png).convert('RGBA'))
    R, Rd, Rl = pal['hat'], pal['hat_dark'], pal['hat_light']
    W_, Ws, Wd = pal['fur'], pal['fur_shade'], pal['fur_dark']

    def fur(name, i, j, w, h):
        r = rnd.random()
        c = W_ if r < 0.62 else Ws if r < 0.9 else Wd
        if name == 'down':
            c = lerp(c, Wd, 0.35)
        return c

    def knit(name, i, j, w, h):  # tricot : côtes verticales + bruit léger
        c = R if i % 2 == 0 else lerp(R, Rd, 0.35)
        if (j + i // 2) % 3 == 0:
            c = lerp(c, Rl, 0.3)
        if rnd.random() < 0.08:
            c = Rd
        if name == 'down':
            c = lerp(c, Rd, 0.5)
        if name in ('front', 'back', 'left', 'right') and j == h - 1:
            c = lerp(c, Rd, 0.45)  # ombre du bord de fourrure
        return c

    paint(img, 'hat_brim', [9, 2, 9], fur)
    paint(img, 'hat_base', [8, 3, 8], knit)
    paint(img, 'hat_mid', [6, 3, 6], knit)
    paint(img, 'hat_upper', [4, 3, 4], knit)
    paint(img, 'hat_tip', [2, 2, 2], lambda n, i, j, w, h: lerp(R, Rd, 0.15) if (i + j) % 2 else R)
    paint(img, 'pompom', [3, 3, 3], fur)

    G, Gd, Gl = pal['leaf'], pal['leaf_dark'], pal['leaf_light']

    def leaf(name, i, j, w, h):  # feuille de houx dentelée : nervure centrale + pointes
        if j == 0 and i == 1:
            return Gl
        if j == 1 and i in (0, 2):
            return Gd
        return G
    paint(img, 'holly_leaf', [3, 2, 0], leaf)
    # pointes transparentes pour la silhouette dentelée
    for (x, y, w, h) in faces('holly_leaf', [3, 2, 0]).values():
        if w and h:
            img[y, x] = (0, 0, 0, 0)
            img[y, x + w - 1] = (0, 0, 0, 0)
    paint(img, 'holly_berry', [1, 1, 1],
          lambda n, i, j, w, h: pal['berry_light'] if n == 'up' else pal['berry'])

    for k, col in (('bulb_r', 'bulb_r'), ('bulb_g', 'bulb_g'), ('bulb_b', 'bulb_b'), ('bulb_y', 'bulb_y')):
        paint(img, k, [1, 1, 1], lambda n, i, j, w, h, c=pal[col]: c)

    S1, S2, Sd = pal['scarf'], pal['scarf2'], pal['scarf_dark']

    def stripes(name, i, j, w, h, axis='x'):
        t = i if name in ('front', 'back', 'up', 'down') else j
        band = (t // 2) % 2
        c = S1 if band == 0 else S2
        if (i + j) % 2 and band == 0:
            c = lerp(c, Sd, 0.2)
        if name == 'down':
            c = lerp(c, Sd, 0.4)
        return c

    def wrap(name, i, j, w, h):  # bande enroulée : rayures horizontales le long du cou
        band = j % 2 if name in ('front', 'back', 'left', 'right') else (i // 2) % 2
        c = S1 if band == 0 else S2
        if band == 0 and (i % 2):
            c = lerp(c, Sd, 0.18)
        if name == 'down':
            c = lerp(c, Sd, 0.45)
        return c

    def tail(name, i, j, w, h):  # pan d'écharpe : rayures horizontales
        c = S1 if (j // 1) % 3 != 1 else S2
        if i % 2 and c == S1:
            c = lerp(c, Sd, 0.18)
        return c

    def tail_end(name, i, j, w, h):  # bout avec franges blanches
        if j == h - 1:
            return W_ if i % 2 == 0 else Ws
        return S2 if j == 0 else S1

    paint(img, 'scarf_wrap', [9, 2, 8], wrap)
    paint(img, 'scarf_knot', [3, 2, 1], lambda n, i, j, w, h: lerp(S1, Sd, 0.25) if (i + j) % 2 else S1)
    paint(img, 'scarf_tail1', [3, 4, 1], tail)
    paint(img, 'scarf_tail2', [3, 2, 1], tail_end)
    paint(img, 'scarf_tail3', [2, 3, 1], tail_end)
    for (x, y, w, h) in [faces('scarf_tail2', [3, 2, 1])['front'], faces('scarf_tail2', [3, 2, 1])['back'],
                         faces('scarf_tail3', [2, 3, 1])['front'], faces('scarf_tail3', [2, 3, 1])['back']]:
        for i in range(1, w, 2):
            img[y + h - 1, x + i] = (0, 0, 0, 0)  # franges découpées

    Au, Ad, Al = pal['gold'], pal['gold_dark'], pal['gold_light']

    def bell(name, i, j, w, h):
        if name == 'front':
            return [[Al, Au], [Ad, Ad]][j][i]
        if name == 'down':
            return Ad
        if name == 'up':
            return Al
        return Au if j == 0 else Ad
    paint(img, 'bell', [2, 2, 2], bell)
    paint(img, 'bell_loop', [1, 1, 1], lambda n, i, j, w, h: Ad)
    return img


def make_emissive(base_png, pal):
    img = np.array(Image.open(TEX + base_png).convert('RGBA'))
    for k in ('bulb_r', 'bulb_g', 'bulb_b', 'bulb_y'):
        paint(img, k, [1, 1, 1], lambda n, i, j, w, h, c=pal[k]: c)
    return img


NORMAL = dict(
    hat=(196, 28, 44), hat_dark=(128, 14, 28), hat_light=(232, 72, 78),
    fur=(248, 248, 244), fur_shade=(222, 226, 232), fur_dark=(186, 194, 208),
    leaf=(36, 122, 58), leaf_dark=(20, 80, 38), leaf_light=(92, 170, 96),
    berry=(214, 22, 36), berry_light=(255, 128, 128),
    bulb_r=(255, 70, 70), bulb_g=(90, 255, 120), bulb_b=(90, 160, 255), bulb_y=(255, 214, 70),
    scarf=(32, 128, 66), scarf2=(240, 240, 236), scarf_dark=(14, 74, 36),
    gold=(234, 182, 42), gold_dark=(160, 108, 18), gold_light=(255, 238, 150),
)
SHINY = dict(NORMAL,  # Noël « givré » : bonnet bleu glacier et écharpe argentée
             hat=(48, 104, 200), hat_dark=(24, 58, 136), hat_light=(116, 172, 240),
             scarf=(150, 196, 236), scarf2=(250, 252, 255), scarf_dark=(82, 128, 182),
             gold=(214, 220, 232), gold_dark=(140, 150, 170), gold_light=(255, 255, 255))

if __name__ == '__main__':
    import os
    os.makedirs(OUT, exist_ok=True)
    male = build_model('pikachu_male.geo.json', 'geometry.pikachu_christmas_male')
    female = build_model('pikachu_female.geo.json', 'geometry.pikachu_christmas_female')
    json.dump(male, open(OUT + 'pikachu_christmas_male.geo.json', 'w'), indent=1)
    json.dump(female, open(OUT + 'pikachu_christmas_female.geo.json', 'w'), indent=1)
    Image.fromarray(make_texture('pikachu.png', NORMAL, 25)).save(OUT + 'pikachu_christmas.png')
    Image.fromarray(make_texture('pikachu_shiny.png', SHINY, 25)).save(OUT + 'pikachu_christmas_shiny.png')
    Image.fromarray(make_emissive('pikachu_emissive.png', NORMAL)).save(OUT + 'pikachu_christmas_emissive.png')
    Image.fromarray(make_emissive('pikachu_emissive_shiny.png', NORMAL)).save(OUT + 'pikachu_christmas_emissive_shiny.png')
    print(json.dumps(ALLOC))
