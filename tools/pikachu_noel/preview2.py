import json, sys
import numpy as np
from PIL import Image, ImageDraw
from render import render, posed

A = '/home/claude/jar/x/assets/cobblemon/bedrock/pokemon/animations/0025_pikachu/pikachu.animation.json'
anims = json.load(open(A))['animations']
sway = json.load(open('/home/claude/work/out2/pikachu_christmas.animation.json'))['animations']['animation.pikachu_christmas.sway']

geo_file, tex_file, out = sys.argv[1], sys.argv[2], sys.argv[3]
geo = json.load(open(geo_file))['minecraft:geometry'][0]
tex = np.array(Image.open(tex_file).convert('RGBA'))
H, W = tex.shape[:2]
# le rendu travaille en unités de texture 128x64 : on ré-échantillonne l'accès texel
scale = W // 128


class Tex:
    shape = (64, 128)
    def __getitem__(self, idx):
        y, x = idx
        return tex[y * scale + scale // 2, x * scale + scale // 2]


rows = []
specs = [('ground_idle', 0.4), ('ground_walk', 0.3), ('battle_idle', 0.5), ('sleep', 0.5)]
views = [(20, 10), (-35, 12), (160, 15)]
for an, t in specs:
    g = posed(geo, [anims['animation.pikachu.' + an], sway], t)
    ims = [render(g, tex, y, p, size=420, scale=9.5) for y, p in views]
    row = Image.new('RGB', (420 * len(ims), 420))
    for i, im in enumerate(ims):
        row.paste(im, (420 * i, 0))
    ImageDraw.Draw(row).text((8, 8), an, fill=(255, 255, 255))
    rows.append(row)
sheet = Image.new('RGB', (rows[0].width, 420 * len(rows)))
for i, r in enumerate(rows):
    sheet.paste(r, (0, 420 * i))
sheet.save(out)
