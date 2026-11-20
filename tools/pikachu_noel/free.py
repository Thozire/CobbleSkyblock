import json,math
from PIL import Image
import numpy as np
B='/home/claude/jar/x/assets/cobblemon/'
used=np.zeros((64,128),bool)
for n in ['pikachu_male','pikachu_female']:
  g=json.load(open(B+f'bedrock/pokemon/models/0025_pikachu/{n}.geo.json'))
  for b in g['minecraft:geometry'][0]['bones']:
    for c in b.get('cubes',[]):
      w,h,d=[abs(math.floor(x)) if x>=0 else abs(math.ceil(x)) for x in c['size']]
      w,h,d=[int(abs(x)) for x in c['size']]
      u,v=c['uv']; W=2*(d+w); H=d+h
      used[v:v+H, u:u+W]=True
for f in ['pikachu','pikachu_shiny','pikachu_emissive']:
  a=np.array(Image.open(B+f'textures/pokemon/0025_pikachu/{f}.png').convert('RGBA'))[:,:,3]>0
  used|=a
# print map
for y in range(64):
  print(''.join('#' if used[y,x] else '.' for x in range(128)))
np.save('used.npy',used)
