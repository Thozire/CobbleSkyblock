"""Structures .nbt du mod Royaumes : capitale, campement de départ, scierie, ferme, mine.

Usage : python3 tools/medieval_structures.py
Les bâtiments font 9x9 au sol ; la couche y=0 remplace l'herbe, le pupitre (accès au menu)
est en (4, 1, 8) — voir Building.java. La capitale fait 45x45, centre (22, 22), sol à y=8.
"""
import math, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from make_structures import Build, items, write_nbt  # écrivain NBT existant

OUT = os.path.join(os.path.dirname(__file__), "..", "cobbleislands", "src", "main", "resources", "data", "cobbleislands", "structure")

AIR = "minecraft:air"

def stairs(facing, half="bottom"):
    return {"facing": facing, "half": half, "shape": "straight", "waterlogged": "false"}

def fence():
    return {"north": "false", "south": "false", "east": "false", "west": "false", "waterlogged": "false"}

def log(axis="y"):
    return {"axis": axis}

def clear(b, x0, x1, y0, y1, z0, z1):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if (x, y, z) not in b.blocks:
                    b.set(x, y, z, AIR)

def floor(b, block, x0, x1, z0, z1, y=0, props=None):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            b.set(x, y, z, block, props)

def gable_roof(b, x0, x1, z0, z1, y, mat="minecraft:spruce_stairs", ridge="minecraft:spruce_planks"):
    """Toit à deux pans (pentes vers le nord et le sud)."""
    depth = (z1 - z0 + 2) // 2
    for i in range(depth):
        zn, zs = z0 - 1 + i, z1 + 1 - i
        for x in range(x0 - 1, x1 + 2):
            if zn < zs:
                b.set(x, y + i, zn, mat, stairs("south"))
                b.set(x, y + i, zs, mat, stairs("north"))
            else:
                b.set(x, y + i, zn, ridge)
    return y + depth

def lectern(b, x=4, y=1, z=8, facing="south"):
    b.set(x, y, z, "minecraft:lectern", {"facing": facing, "has_book": "false", "powered": "false"})

def lantern_post(b, x, y, z, h=2):
    for k in range(h):
        b.set(x, y + k, z, "minecraft:spruce_fence", fence())
    b.set(x, y + h, z, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})

def base_9(b, ground="minecraft:dirt_path"):
    clear(b, 0, 8, 1, 8, 0, 8)
    floor(b, "minecraft:grass_block", 0, 8, 0, 8, props={"snowy": "false"})
    for x in range(0, 9):
        b.set(x, 0, 8, ground)
    b.set(4, 0, 7, ground)

# ---------- campement de départ ----------
def campement():
    b = Build()
    base_9(b)
    floor(b, "minecraft:coarse_dirt", 2, 6, 2, 6)
    # tente (laine) au nord
    for z, w in ((1, 3), (2, 3), (3, 3)):
        for y, half in ((1, 3), (2, 2), (3, 1)):
            for x in range(4 - half + 1, 4 + half):
                b.set(x, y, z, "minecraft:white_wool" if (x + y) % 2 else "minecraft:red_wool")
    for y in (1, 2):
        b.set(4, y, 3, AIR)
    b.set(4, 1, 1, "minecraft:red_bed", {"facing": "south", "part": "head", "occupied": "false"}) if False else None
    # feu de camp + bûches
    b.set(4, 1, 5, "minecraft:campfire", {"facing": "north", "lit": "true", "signal_fire": "false", "waterlogged": "false"})
    b.set(3, 1, 5, "minecraft:spruce_log", log("z")); b.set(5, 1, 5, "minecraft:spruce_log", log("z"))
    # charrette de stockage (tonneaux) et caisse de départ
    b.set(7, 1, 3, "minecraft:barrel", {"facing": "up", "open": "false"})
    b.set(7, 1, 4, "minecraft:chest", {"facing": "west", "type": "single", "waterlogged": "false"}, items([
        ("minecraft:bread", 8), ("minecraft:oak_sapling", 4), ("minecraft:wheat_seeds", 8), ("minecraft:torch", 16),
        ("minecraft:stone_axe", 1), ("minecraft:stone_pickaxe", 1), ("minecraft:stone_hoe", 1), ("minecraft:oak_planks", 32)]))
    b.set(7, 1, 2, "minecraft:hay_block", log())
    b.set(1, 1, 3, "minecraft:crafting_table"); b.set(1, 1, 4, "minecraft:furnace", {"facing": "east", "lit": "false"})
    lantern_post(b, 1, 1, 7); lantern_post(b, 7, 1, 7)
    # bannière du royaume
    b.set(4, 1, 0, "minecraft:spruce_fence", fence()); b.set(4, 2, 0, "minecraft:spruce_fence", fence())
    b.set(4, 3, 0, "minecraft:blue_banner", {"rotation": "0"})
    return b

# ---------- scierie ----------
def scierie():
    b = Build()
    base_9(b)
    floor(b, "minecraft:spruce_planks", 1, 7, 1, 6)
    # poteaux + toit
    for x, z in ((1, 1), (7, 1), (1, 6), (7, 6)):
        for y in range(1, 4):
            b.set(x, y, z, "minecraft:stripped_spruce_log", log())
    for x in range(1, 8):
        b.set(x, 4, 1, "minecraft:spruce_log", log("x")); b.set(x, 4, 6, "minecraft:spruce_log", log("x"))
    gable_roof(b, 1, 7, 1, 6, 5)
    # scie et établi
    b.set(4, 1, 3, "minecraft:stonecutter", {"facing": "south"})
    b.set(3, 1, 3, "minecraft:spruce_slab", {"type": "top", "waterlogged": "false"})
    b.set(5, 1, 3, "minecraft:spruce_slab", {"type": "top", "waterlogged": "false"})
    # tas de bûches
    for x in (2, 3):
        for y in (1, 2):
            for z in (5,):
                b.set(x, y, z, "minecraft:oak_log", log("x"))
    for x in (5, 6):
        b.set(x, 1, 5, "minecraft:spruce_log", log("x"))
    b.set(6, 1, 2, "minecraft:barrel", {"facing": "up", "open": "false"})
    b.set(2, 1, 2, "minecraft:oak_log", log())
    b.set(2, 2, 2, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})
    # enseigne : bannière marron
    b.set(0, 1, 7, "minecraft:spruce_fence", fence()); b.set(0, 2, 7, "minecraft:spruce_fence", fence())
    b.set(0, 3, 7, "minecraft:brown_banner", {"rotation": "0"})
    lectern(b)
    return b

# ---------- ferme ----------
def ferme():
    b = Build()
    base_9(b)
    # champs
    for x in range(1, 8):
        for z in range(1, 6):
            if (x, z) == (4, 3):
                b.set(x, 0, z, "minecraft:water", {"level": "0"})
                continue
            b.set(x, 0, z, "minecraft:farmland", {"moisture": "7"})
            crop = "minecraft:wheat" if x < 3 else ("minecraft:carrots" if x < 6 else "minecraft:potatoes")
            b.set(x, 1, z, crop, {"age": "7"})
    # clôture
    for x in range(0, 9):
        b.set(x, 1, 0, "minecraft:oak_fence", fence())
    for z in range(0, 7):
        b.set(0, 1, z, "minecraft:oak_fence", fence()); b.set(8, 1, z, "minecraft:oak_fence", fence())
    # cabane et bottes de foin
    floor(b, "minecraft:oak_planks", 1, 3, 6, 7)
    b.set(1, 1, 6, "minecraft:composter", {"level": "4"}); b.set(2, 1, 6, "minecraft:hay_block", log()); b.set(3, 1, 6, "minecraft:hay_block", log())
    b.set(2, 2, 6, "minecraft:hay_block", log())
    b.set(6, 1, 6, "minecraft:barrel", {"facing": "up", "open": "false"}); b.set(7, 1, 6, "minecraft:pumpkin")
    b.set(7, 1, 7, "minecraft:carved_pumpkin", {"facing": "south"})
    lantern_post(b, 8, 1, 7)
    b.set(0, 1, 7, "minecraft:spruce_fence", fence()); b.set(0, 2, 7, "minecraft:spruce_fence", fence())
    b.set(0, 3, 7, "minecraft:yellow_banner", {"rotation": "0"})
    lectern(b)
    return b

# ---------- mine ----------
def mine():
    b = Build()
    base_9(b, "minecraft:gravel")
    # colline de pierre
    for x in range(0, 9):
        for z in range(0, 6):
            h = 4 - max(abs(x - 4) - 1, 0) // 1 - (0 if z < 4 else z - 3)
            for y in range(1, max(1, h) + 1):
                b.set(x, y, z, "minecraft:stone" if (x + y + z) % 4 else ("minecraft:coal_ore" if (x * y) % 3 else "minecraft:iron_ore"))
            if h >= 1:
                b.set(x, max(1, h), z, "minecraft:mossy_cobblestone" if (x + z) % 3 else "minecraft:cobblestone")
    # entrée boisée
    for y in (1, 2):
        b.set(3, y, 5, "minecraft:spruce_log", log()); b.set(5, y, 5, "minecraft:spruce_log", log())
        b.set(4, y, 5, AIR); b.set(4, y, 4, AIR); b.set(4, y, 3, AIR)
    for x in (3, 4, 5):
        b.set(x, 3, 5, "minecraft:spruce_log", log("x"))
    b.set(4, 2, 2, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})
    b.set(4, 1, 2, "minecraft:spruce_fence", fence())
    # rails et wagonnet de minerai (tonneaux)
    for z in (3, 4, 5, 6, 7):
        b.set(4, 1, z, "minecraft:rail", {"shape": "north_south", "waterlogged": "false"}) if z != 7 else None
    b.set(6, 1, 6, "minecraft:barrel", {"facing": "up", "open": "false"}); b.set(7, 1, 6, "minecraft:coal_block")
    b.set(2, 1, 6, "minecraft:cobblestone"); b.set(1, 1, 6, "minecraft:cobblestone"); b.set(1, 2, 6, "minecraft:cobblestone_slab", {"type": "bottom", "waterlogged": "false"})
    lantern_post(b, 8, 1, 7)
    b.set(0, 1, 7, "minecraft:spruce_fence", fence()); b.set(0, 2, 7, "minecraft:spruce_fence", fence())
    b.set(0, 3, 7, "minecraft:gray_banner", {"rotation": "0"})
    lectern(b)
    return b

# ---------- capitale ----------
CAP_C, CAP_G = 22, 8

def house(b, x0, z0, w, d, g, door_side="south", seed=0):
    rnd = random.Random(seed)
    x1, z1 = x0 + w - 1, z0 + d - 1
    floor(b, "minecraft:spruce_planks", x0, x1, z0, z1, g)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            if not edge:
                for y in range(g + 1, g + 5): b.set(x, y, z, AIR)
                continue
            corner = x in (x0, x1) and z in (z0, z1)
            for y in range(g + 1, g + 5):
                if corner or y == g + 4:
                    b.set(x, y, z, "minecraft:dark_oak_log", log() if corner else log("x" if z in (z0, z1) else "z"))
                else:
                    b.set(x, y, z, "minecraft:white_terracotta")
    # fenêtres et porte
    dz = z1 if door_side == "south" else z0
    mx = (x0 + x1) // 2
    b.set(mx, g + 1, dz, "minecraft:spruce_door", {"facing": door_side, "half": "lower", "hinge": "left", "open": "false", "powered": "false"})
    b.set(mx, g + 2, dz, "minecraft:spruce_door", {"facing": door_side, "half": "upper", "hinge": "left", "open": "false", "powered": "false"})
    for x in (x0 + 1, x1 - 1):
        if x != mx:
            b.set(x, g + 2, z0, "minecraft:glass_pane", {"north": "false", "south": "false", "east": "true", "west": "true", "waterlogged": "false"})
            b.set(x, g + 2, z1, "minecraft:glass_pane", {"north": "false", "south": "false", "east": "true", "west": "true", "waterlogged": "false"})
    gable_roof(b, x0, x1, z0, z1, g + 5, "minecraft:dark_oak_stairs", "minecraft:dark_oak_planks")
    b.set(mx + 1 if mx + 1 < x1 else mx - 1, g + 1, dz + (1 if door_side == "south" else -1), "minecraft:flower_pot") if False else None

def stall(b, x0, z0, g, wool_a, wool_b, goods):
    for dx in range(4):
        for dz in range(3):
            b.set(x0 + dx, g, z0 + dz, "minecraft:spruce_planks")
    for dx, dz in ((0, 0), (3, 0), (0, 2), (3, 2)):
        for y in (1, 2):
            b.set(x0 + dx, g + y, z0 + dz, "minecraft:spruce_fence", fence())
    for dx in range(-1, 5):
        for dz in range(-1, 4):
            b.set(x0 + dx, g + 3, z0 + dz, wool_a if (dx + 10) % 2 else wool_b)
    for dx in (1, 2):
        b.set(x0 + dx, g + 1, z0 + 2, "minecraft:spruce_slab", {"type": "top", "waterlogged": "false"})
    for k, block in enumerate(goods):
        b.set(x0 + 1 + k % 2, g + 1, z0, block)

def capitale():
    b = Build()
    C, G = CAP_C, CAP_G
    R = 22.4
    rnd = random.Random(42)
    for x in range(0, 45):
        for z in range(0, 45):
            d = math.hypot(x - C, z - C)
            if d > R: continue
            dx, dz = x - C, z - C
            if abs(dx) <= 12 and abs(dz) <= 12:
                m = "minecraft:polished_andesite" if abs(dx) in (12,) or abs(dz) in (12,) else ("minecraft:stone_bricks" if (x + z) % 7 else "minecraft:cracked_stone_bricks")
                if (abs(dx) + abs(dz)) % 9 == 0 and abs(dx) < 11 and abs(dz) < 11: m = "minecraft:mossy_stone_bricks"
            elif abs(dx) <= 1 or abs(dz) <= 1:
                m = "minecraft:cobblestone" if rnd.random() < 0.7 else "minecraft:gravel"
            else:
                m = "minecraft:grass_block"
            b.set(x, G, z, m, {"snowy": "false"} if m == "minecraft:grass_block" else None)
            for k in range(1, 4):
                b.set(x, G - k, z, "minecraft:dirt")
    # dessous de l'île céleste
    for k in range(4, 9):
        r = R - (k - 3) * 3.8
        for x in range(0, 45):
            for z in range(0, 45):
                if math.hypot(x - C, z - C) <= r:
                    b.set(x, G - k, z, "minecraft:stone" if (x + z + k) % 5 else "minecraft:andesite")
    # puits central
    for x in range(C - 2, C + 3):
        for z in range(C - 2, C + 3):
            ring = max(abs(x - C), abs(z - C)) == 2
            if ring:
                b.set(x, G + 1, z, "minecraft:stone_brick_wall", {"up": "true", "north": "none", "south": "none", "east": "none", "west": "none", "waterlogged": "false"})
            else:
                b.set(x, G, z, "minecraft:water", {"level": "0"})
    for x, z in ((C - 2, C - 2), (C + 2, C - 2), (C - 2, C + 2), (C + 2, C + 2)):
        b.set(x, G + 2, z, "minecraft:spruce_fence", fence()); b.set(x, G + 3, z, "minecraft:spruce_fence", fence())
    for x in range(C - 2, C + 3):
        for z in range(C - 2, C + 3):
            if max(abs(x - C), abs(z - C)) <= 2:
                b.set(x, G + 4, z, "minecraft:spruce_slab", {"type": "bottom", "waterlogged": "false"})
    b.set(C, G + 3, C, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
    b.set(C, G + 4, C, "minecraft:spruce_planks")
    # château au nord
    zf, zb = C - 17, C - 21
    for x in range(C - 12, C + 13):
        for z in range(zb, zf + 1):
            for y in range(G + 1, G + 8):
                b.set(x, y, z, "minecraft:stone_bricks" if (x + y) % 6 else "minecraft:mossy_stone_bricks")
        if x % 2 == 0:
            b.set(x, G + 8, zf, "minecraft:stone_bricks")
    for tx in (C - 12, C + 12):
        for x in range(tx - 2, tx + 3):
            for z in range(zf - 3, zf + 2):
                for y in range(G + 1, G + 12):
                    b.set(x, y, z, "minecraft:stone_bricks" if (y % 5) else "minecraft:chiseled_stone_bricks")
        for x in range(tx - 2, tx + 3):
            for z in range(zf - 3, zf + 2):
                if (x + z) % 2 == 0:
                    b.set(x, G + 12, z, "minecraft:stone_bricks")
        b.set(tx, G + 9, zf + 1, "minecraft:glass")
    # porte du château
    for x in range(C - 1, C + 2):
        for y in range(G + 1, G + 5):
            b.set(x, y, zf, "minecraft:iron_bars", {"north": "false", "south": "false", "east": "true", "west": "true", "waterlogged": "false"})
    for x in range(C - 2, C + 3):
        b.set(x, G + 5, zf, "minecraft:chiseled_stone_bricks")
    for x in (C - 6, C + 6):
        b.set(x, G + 6, zf + 1, "minecraft:red_wall_banner", {"facing": "south"})
        b.set(x, G + 3, zf + 1, "minecraft:wall_torch", {"facing": "south"})
    # étals du marché (le marchand se tient dans l'étal sud-est)
    stall(b, C + 6, C + 6, G, "minecraft:red_wool", "minecraft:white_wool", ["minecraft:pumpkin", "minecraft:hay_block"])
    stall(b, C - 9, C + 6, G, "minecraft:yellow_wool", "minecraft:white_wool", ["minecraft:barrel", "minecraft:melon"])
    stall(b, C + 6, C - 9, G, "minecraft:blue_wool", "minecraft:white_wool", ["minecraft:barrel", "minecraft:oak_log"])
    stall(b, C - 9, C - 9, G, "minecraft:green_wool", "minecraft:white_wool", ["minecraft:coal_block", "minecraft:iron_block"])
    # tableau du classement (ouest du puits)
    for z in range(C - 2, C + 3):
        for y in range(G + 1, G + 4):
            b.set(C - 8, y, z, "minecraft:dark_oak_planks")
        b.set(C - 8, G + 4, z, "minecraft:dark_oak_slab", {"type": "bottom", "waterlogged": "false"})
    # maisons à l'est et à l'ouest
    house(b, C + 14, C - 4, 7, 6, G, "south", 1)
    house(b, C - 20, C - 4, 7, 6, G, "south", 2)
    house(b, C + 14, C + 6, 6, 5, G, "north", 3)
    house(b, C - 19, C + 6, 6, 5, G, "north", 4)
    # lampadaires
    for dx, dz in ((3, 11), (-3, 11), (11, 3), (11, -3), (-11, 3), (-11, -3), (5, -14), (-5, -14), (3, 18), (-3, 18)):
        x, z = C + dx, C + dz
        if (x, G + 1, z) not in b.blocks:
            lantern_post(b, x, G + 1, z, 2)
    # arbres et fleurs dans l'herbe
    def tree(x, z):
        for y in range(1, 5): b.set(x, G + y, z, "minecraft:oak_log", log())
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                for y in (4, 5):
                    if abs(dx) + abs(dz) < 4 and (x + dx, G + y, z + dz) not in b.blocks:
                        b.set(x + dx, G + y, z + dz, "minecraft:oak_leaves", {"persistent": "true", "distance": "1", "waterlogged": "false"})
        b.set(x, G + 6, z, "minecraft:oak_leaves", {"persistent": "true", "distance": "1", "waterlogged": "false"})
    for x, z in ((C - 16, C + 15), (C + 16, C + 15), (C + 17, C - 12), (C - 17, C - 12)):
        if math.hypot(x - C, z - C) < R - 2: tree(x, z)
    flowers = ["minecraft:poppy", "minecraft:dandelion", "minecraft:cornflower", "minecraft:oxeye_daisy"]
    for x in range(0, 45):
        for z in range(0, 45):
            if b.get(x, G, z) == "minecraft:grass_block" and (x, G + 1, z) not in b.blocks and (x * 5 + z * 11) % 13 == 0:
                b.set(x, G + 1, z, flowers[(x + z) % 4])
    return b

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, f in (("campement", campement), ("scierie", scierie), ("ferme", ferme), ("mine", mine), ("capitale", capitale)):
        size, mins = f().save(os.path.join(OUT, name + ".nbt"))
        print(name, size, "min", mins)
