import json, sys
import numpy as np
from PIL import Image
import render
render.BASE = 1.05
from render import render as R, posed
A = '/home/claude/jar/x/assets/cobblemon/bedrock/pokemon/animations/0025_pikachu/pikachu.animation.json'
anims = json.load(open(A))['animations']
sway = json.load(open('/home/claude/work/out2/pikachu_christmas.animation.json'))['animations']['animation.pikachu_christmas.sway']
geo = json.load(open(sys.argv[1]))['minecraft:geometry'][0]
tex = np.array(Image.open(sys.argv[2]).convert('RGBA'))
g = posed(geo, [anims['animation.pikachu.' + sys.argv[4]], sway], 0.4)
views = [(25, 15), (-40, 25), (200, 20)]
ims = []
for y, p in views:
    ims.append(R(g, tex, y, p, size=600, scale=17))
sheet = Image.new('RGB', (1800, 600))
for i, im in enumerate(ims): sheet.paste(im, (600 * i, 0))
sheet.save(sys.argv[3])
