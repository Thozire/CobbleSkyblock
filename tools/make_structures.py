"""Génère les structures .nbt de CobbleIslands : l'île de départ et le spawn.

Usage : python3 tools/make_structures.py   (écrit dans cobbleislands/src/main/resources/data/cobbleislands/structure/)
Pour modifier une île à la main : construis-la en jeu et sauvegarde-la avec un bloc de structure
sous le nom cobbleislands:ile_depart (ou cobbleislands:spawn) — la version du monde remplace celle du mod.
"""
import gzip, io, math, os, struct

DATA_VERSION = 3955  # Minecraft 1.21.1
OUT = os.path.join(os.path.dirname(__file__), "..", "cobbleislands", "src", "main", "resources", "data", "cobbleislands", "structure")

# ---------- écriture NBT minimale ----------
END, BYTE, INT, STRING, LIST, COMPOUND = 0, 1, 3, 8, 9, 10

class Byte(int): pass

def _str(s):
    b = s.encode("utf-8")
    return struct.pack(">H", len(b)) + b

def _tag_type(v):
    if isinstance(v, Byte): return BYTE
    if isinstance(v, int): return INT
    if isinstance(v, str): return STRING
    if isinstance(v, list): return LIST
    if isinstance(v, dict): return COMPOUND
    raise TypeError(v)

def _payload(v):
    t = _tag_type(v)
    if t == BYTE: return struct.pack(">b", v)
    if t == INT: return struct.pack(">i", v)
    if t == STRING: return _str(v)
    if t == LIST:
        et = _tag_type(v[0]) if v else END
        return struct.pack(">bi", et, len(v)) + b"".join(_payload(x) for x in v)
    out = b""
    for k, x in v.items():
        out += struct.pack(">b", _tag_type(x)) + _str(k) + _payload(x)
    return out + b"\x00"

def write_nbt(path, root):
    raw = struct.pack(">b", COMPOUND) + _str("") + _payload(root)
    with gzip.open(path, "wb") as f:
        f.write(raw)

# ---------- construction ----------
class Build:
    def __init__(self):
        self.blocks = {}   # (x,y,z) -> (name, props, nbt)

    def set(self, x, y, z, name, props=None, nbt=None):
        self.blocks[(x, y, z)] = (name, props or {}, nbt)

    def get(self, x, y, z):
        return self.blocks.get((x, y, z), (None,))[0]

    def save(self, path):
        xs = [p[0] for p in self.blocks]; ys = [p[1] for p in self.blocks]; zs = [p[2] for p in self.blocks]
        mx, my, mz = min(xs), min(ys), min(zs)
        palette, pidx, blocks = [], {}, []
        for (x, y, z), (name, props, nbt) in sorted(self.blocks.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0])):
            key = (name, tuple(sorted(props.items())))
            if key not in pidx:
                pidx[key] = len(palette)
                entry = {"Name": name}
                if props: entry["Properties"] = {k: str(v) for k, v in props.items()}
                palette.append(entry)
            b = {"pos": [x - mx, y - my, z - mz], "state": pidx[key]}
            if nbt: b["nbt"] = nbt
            blocks.append(b)
        size = [max(xs) - mx + 1, max(ys) - my + 1, max(zs) - mz + 1]
        write_nbt(path, {"DataVersion": DATA_VERSION, "size": size, "palette": palette, "blocks": blocks, "entities": []})
        return size, (mx, my, mz)

def items(lst):
    return {"id": "minecraft:chest", "Items": [{"Slot": Byte(i), "id": iid, "count": n} for i, (iid, n) in enumerate(lst)]}

def leaves(b, cx, cy, cz, r, name, hmin, hmax):
    for y in range(hmin, hmax + 1):
        rr = r if y < hmax else max(1, r - 1)
        for x in range(cx - rr, cx + rr + 1):
            for z in range(cz - rr, cz + rr + 1):
                if abs(x - cx) == rr and abs(z - cz) == rr and rr > 1: continue
                if b.get(x, y + cy, z) is None:
                    b.set(x, y + cy, z, name, {"persistent": "true", "distance": "1", "waterlogged": "false"})

def tree(b, x, g, z, log, leaf, height=4):
    for y in range(1, height + 1):
        b.set(x, g + y, z, log, {"axis": "y"})
    leaves(b, x, g, z, 2, leaf, height - 1, height)
    for y in (height + 1, height + 2):
        for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if y == height + 2 and (dx or dz): continue
            b.set(x + dx, g + y, z + dz, leaf, {"persistent": "true", "distance": "1", "waterlogged": "false"})

def underside(b, cx, cz, g, r0, depth, step, mat):
    for k in range(1, depth + 1):
        r = r0 - step * k
        if r < 0.8: break
        for x in range(cx - int(r) - 1, cx + int(r) + 2):
            for z in range(cz - int(r) - 1, cz + int(r) + 2):
                if math.hypot(x - cx, z - cz) <= r:
                    b.set(x, g - k, z, mat(k, x, z))

# ---------- île de départ ----------
def starter():
    b, c, g = Build(), 6, 5
    R = 6.3
    for x in range(0, 13):
        for z in range(0, 13):
            if math.hypot(x - c, z - c) <= R:
                b.set(x, g, z, "minecraft:grass_block", {"snowy": "false"})
    underside(b, c, c, g, R, 5, 1.25, lambda k, x, z: "minecraft:dirt" if k <= 2 else ("minecraft:stone" if (x + z + k) % 5 else "minecraft:andesite"))
    # mare (eau infinie : 2 sources)
    for x in (3, 4):
        b.set(x, g, 8, "minecraft:water", {"level": "0"})
    # coin sable + cactus
    for x, z in ((9, 9), (10, 9), (9, 10)):
        b.set(x, g, z, "minecraft:sand")
    b.set(10, g + 1, 9, "minecraft:cactus", {"age": "0"})
    # arbres : chêne et apricorn (Cobblemon)
    tree(b, 9, g, 3, "minecraft:oak_log", "minecraft:oak_leaves")
    tree(b, 3, g, 3, "cobblemon:apricorn_log", "cobblemon:apricorn_leaves", 3)
    # coin Pokémon : machine de soin + PC
    b.set(5, g + 1, 10, "cobblemon:healing_machine", {"facing": "north", "charge": "0", "natural": "false"})
    b.set(7, g + 1, 10, "cobblemon:pc", {"facing": "north", "part": "bottom", "on": "false"})
    b.set(7, g + 2, 10, "cobblemon:pc", {"facing": "north", "part": "top", "on": "false"})
    b.set(6, g + 1, 10, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})
    # coffre de départ
    b.set(6, g + 1, 2, "minecraft:chest", {"facing": "south", "type": "single", "waterlogged": "false"}, items([
        ("minecraft:lava_bucket", 1), ("minecraft:ice", 2), ("minecraft:bone_meal", 8), ("minecraft:oak_sapling", 2),
        ("minecraft:sugar_cane", 1), ("minecraft:melon_seeds", 1), ("minecraft:pumpkin_seeds", 1), ("minecraft:bread", 8),
        ("cobblemon:poke_ball", 10), ("cobblemon:potion", 3), ("cobblemon:oran_berry", 4),
        ("cobblemon:red_apricorn_seed", 1), ("cobblemon:blue_apricorn_seed", 1), ("minecraft:torch", 8)]))
    # quelques fleurs
    for x, z, f in ((8, 7, "minecraft:poppy"), (4, 6, "minecraft:dandelion"), (8, 11, "minecraft:cornflower")):
        if b.get(x, g, z) == "minecraft:grass_block" and b.get(x, g + 1, z) is None:
            b.set(x, g + 1, z, f)
    return b

# ---------- spawn ----------
SPAWN_G = 7  # sol du spawn dans la structure (index Y)

def spawn():
    b, c, g = Build(), 16, SPAWN_G
    R = 15.5
    for x in range(0, 33):
        for z in range(0, 33):
            d = math.hypot(x - c, z - c)
            if d > R: continue
            dx, dz = x - c, z - c
            if d <= 5.5:
                m = "minecraft:polished_andesite"
            elif d <= 6.5:
                m = "minecraft:stone_bricks"
            elif (abs(dx) <= 1 and d < 15) or (abs(dz) <= 1 and d < 15):
                m = "minecraft:dirt_path"
            else:
                m = "minecraft:grass_block"
            b.set(x, g, z, m, {"snowy": "false"} if m == "minecraft:grass_block" else None)
    underside(b, c, c, g, R, 7, 2.0, lambda k, x, z: "minecraft:dirt" if k <= 2 else ("minecraft:stone" if (x * 3 + z + k) % 6 else "minecraft:mossy_cobblestone"))
    # fontaine
    for x in range(c - 3, c + 4):
        for z in range(c - 3, c + 4):
            d = math.hypot(x - c, z - c)
            if 1.6 < d <= 2.6:
                b.set(x, g + 1, z, "minecraft:stone_brick_wall", {"up": "true", "north": "none", "south": "none", "east": "none", "west": "none", "waterlogged": "false"})
            elif d <= 1.6 and (x, z) != (c, c):
                b.set(x, g, z, "minecraft:water", {"level": "0"})
    for y in (g, g + 1, g + 2):
        b.set(c, y, c, "minecraft:chiseled_stone_bricks")
    b.set(c, g + 3, c, "minecraft:water", {"level": "0"})
    # centre Pokémon (nord)
    x0, x1, z0, z1 = c - 4, c + 4, c - 14, c - 9
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            b.set(x, g, z, "minecraft:white_concrete")
            b.set(x, g + 4, z, "minecraft:red_concrete")
            wall = x in (x0, x1) or z in (z0, z1)
            for y in (g + 1, g + 2, g + 3):
                if wall:
                    b.set(x, y, z, "minecraft:white_concrete")
    for y in (g + 1, g + 2):
        b.set(c, y, z1, "minecraft:air")  # porte
    for x in (c - 2, c + 2):
        b.set(x, g + 2, z1, "minecraft:glass")
    b.set(c, g + 3, z1, "minecraft:red_concrete")
    b.set(c, g + 4, c - 11, "minecraft:sea_lantern")
    b.set(c - 2, g + 1, z0 + 1, "cobblemon:healing_machine", {"facing": "south", "charge": "0", "natural": "false"})
    b.set(c + 2, g + 1, z0 + 1, "cobblemon:healing_machine", {"facing": "south", "charge": "0", "natural": "false"})
    b.set(c, g + 1, z0 + 1, "cobblemon:pc", {"facing": "south", "part": "bottom", "on": "false"})
    b.set(c, g + 2, z0 + 1, "cobblemon:pc", {"facing": "south", "part": "top", "on": "false"})
    # socle de la machine à fusion (est)
    for x in range(c + 9, c + 14):
        for z in range(c - 2, c + 3):
            b.set(x, g, z, "minecraft:purpur_block")
    for x, z in ((c + 9, c - 2), (c + 13, c - 2), (c + 9, c + 2), (c + 13, c + 2)):
        b.set(x, g + 1, z, "minecraft:purpur_pillar", {"axis": "y"})
        b.set(x, g + 2, z, "minecraft:end_rod", {"facing": "up"})
    for x in (c + 10, c + 11):
        for y in (g + 1, g + 2):
            b.set(x, y, c, "minecraft:barrier")
    # jardin (ouest) : arbres apricorn et fleurs
    tree(b, c - 11, g, c - 4, "cobblemon:apricorn_log", "cobblemon:apricorn_leaves", 3)
    tree(b, c - 11, g, c + 4, "cobblemon:apricorn_log", "cobblemon:apricorn_leaves", 3)
    tree(b, c + 8, g, c + 10, "minecraft:oak_log", "minecraft:oak_leaves")
    tree(b, c - 7, g, c + 11, "minecraft:birch_log", "minecraft:birch_leaves")
    flowers = ["minecraft:poppy", "minecraft:dandelion", "minecraft:cornflower", "minecraft:allium", "minecraft:oxeye_daisy", "minecraft:azure_bluet"]
    i = 0
    for x in range(1, 32):
        for z in range(1, 32):
            if b.get(x, g, z) == "minecraft:grass_block" and b.get(x, g + 1, z) is None and (x * 7 + z * 13) % 11 == 0:
                b.set(x, g + 1, z, flowers[i % len(flowers)]); i += 1
    # lampadaires le long des chemins
    for dx, dz in ((2, 7), (-2, 7), (2, -7), (-2, -7), (7, 2), (7, -2), (-7, 2), (-7, -2)):
        x, z = c + dx, c + dz
        if b.get(x, g + 1, z) not in (None, "minecraft:poppy", "minecraft:dandelion", "minecraft:cornflower", "minecraft:allium", "minecraft:oxeye_daisy", "minecraft:azure_bluet"):
            continue
        b.set(x, g + 1, z, "minecraft:oak_fence", {"north": "false", "south": "false", "east": "false", "west": "false", "waterlogged": "false"})
        b.set(x, g + 2, z, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})
    return b

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    s1 = starter().save(os.path.join(OUT, "ile_depart.nbt"))
    s2 = spawn().save(os.path.join(OUT, "spawn.nbt"))
    print("ile_depart", s1, "spawn", s2)
