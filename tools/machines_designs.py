"""Les quatre bâtiments du royaume, dessinés boîte par boîte (repère de dessin : voir machines_core.py)."""
from machines_core import *          # noqa: F401,F403

C = (24.0, 24.0, 24.0)               # pivot des pièces immobiles (socle, lumière)
STONE, MOSSY, COBBLE, MCOBBLE = "mc:stone_bricks", "mc:mossy_stone_bricks", "mc:cobblestone", "mc:mossy_cobblestone"


# ====================================================================== SCIERIE
def scierie():
    """Scierie à eau : halle ouverte sur quatre poteaux, roue à aubes, scie à cadre qui monte et descend, grume qui avance."""
    b, glow = Model(), Model()
    # --- aire de sciage dallée, canal du moulin
    b.box((1, 0, 2), (35, 2, 47), {"*": STONE, "up": "mc:stone_bricks"})
    b.box((11, 0, 0), (25, 1, 2), STONE)                                  # marche d'entrée en pierre
    b.box((36, 0, 0), (48, 1, 48), COBBLE)
    b.box((36, 1, 0), (37.5, 5, 48), MCOBBLE)
    b.box((46.5, 1, 0), (48, 5, 48), MCOBBLE)
    b.box((37.5, 1, 0), (46.5, 5, 1.5), MCOBBLE); b.box((37.5, 1, 46.5), (46.5, 5, 48), MCOBBLE)     # rebords des deux bouts
    b.box((37.5, 1, 1.5), (46.5, 4, 46.5), "water")
    # --- halle ouverte : quatre grands poteaux, rien d'autre que la scie dessous
    PX, PZ = (3, 30.5), (13, 32)
    for x in PX:
        for z in PZ: b.box((x, 1.6, z), (x + 3, 30, z + 3), log("dark_oak"))
    for z in PZ: beam(b, (1.5, 30, z), (35, 32.6, z + 3))                  # entraits
    for x in PX: beam(b, (x, 30, 11), (x + 3, 32.6, 37))                   # sablières
    for z in PZ:
        brace(b, 5, 22, z + 1.5, 9, 1); brace(b, 31.5, 22, z + 1.5, 9, -1)
    for x in PX:
        brace(b, x + 1.5, 22, 15, 9, 1, axis="x"); brace(b, x + 1.5, 22, 33, 9, -1, axis="x")
    # palier de l'arbre de roue : un poteau court, percé à la taille de l'arbre (huit pans, rayon 1,41)
    b.box((31, 1.6, 22.5), (34, 15.2, 25.5), log("dark_oak"))
    b.box((31, 15.2, 22.5), (34, 16.5, 25.5), log("dark_oak"), tile=False)
    b.box((31, 19.5, 22.5), (34, 20.8, 25.5), log("dark_oak"), tile=False)
    for (za, zb) in ((22.5, 22.55), (25.45, 25.5)): b.box((31, 16.5, za), (34, 19.5, zb), log("dark_oak"), tile=False)
    b.box((30.6, 20.8, 22.1), (34.4, 22, 25.9), DO, tile=False)
    # --- toit en bardeaux, haut perché : on voit tout ce qui se passe dessous
    gable_fill(b, 11.5, 36.5, 3.4, 4.6, 32.6, 43.6, SP, ridge="x")
    gable_fill(b, 11.5, 36.5, 31.9, 33.1, 32.6, 43.6, SP, ridge="x")
    gable_roof(b, 0.6, 36, 9.6, 38.4, 30.8, 42.8, "shingle", ridge="x", cap=DO)
    # --- banc de sciage : rails et tréteaux
    for x in (13, 21.5):
        b.box((x, 7, 4), (x + 1.5, 8.5, 45), DO)
    for z in (6, 16, 32, 42):
        for x in (13, 21.5): b.box((x, 2, z), (x + 1.5, 7, z + 1.5), SP)
        b.box((12.5, 4.5, z + 0.2), (23.5, 5.7, z + 1.3), SP)
    for x in (10.5, 23.5):                                               # guides du cadre de scie : le montant
        b.box((x - 0.6, 2, 22.2), (x + 2.6, 3, 25.8), SP)                  # coulisse entre deux planches
        for (za, zb) in ((22.2, 22.95), (25.05, 25.8)): b.box((x - 0.6, 3, za), (x + 2.6, 12, zb), SP, tile=False)
    b.box((14.5, 2, 20.5), (21.5, 3, 27.5), "sawdust"); b.box((16, 3, 22), (20, 3.9, 26), "sawdust")
    b.box((26.6, 1.6, 22.8), (29, 15.6, 25.2), DO)                       # pied du carter

    b.box((25.8, 15.6, 22.3), (29.6, 20.6, 25.7), DO)                    # carter de l'excentrique, fixe
    b.box((25.6, 20.6, 22.1), (29.8, 21, 25.9), SP, tile=False)

    # --- scie à cadre (monte et descend)
    saw = Model()
    for x in (10.5, 23.5): saw.box((x, 3, 23.05), (x + 2, 23, 24.95), DO)
    saw.box((9.5, 21, 22.7), (29, 23.6, 25.3), DO)                       # la traverse va jusqu'au-dessus de la came
    saw.box((27, 16.6, 23.3), (28.4, 21.05, 24.7), DO, tile=False)       # tige de bielle : toujours dans le carter
    saw.box((17.8, 4, 22.5), (18.2, 21, 25.5), {"east": "blade", "west": "blade"}, tile=False,
            uv={"west": [0, 0, 3, 16], "east": [3, 0, 0, 16]})
    saw_keys = [key(1, t=(0, 3.4, 0)), key(1)]

    # --- grume sur son chariot (avance lentement, revient vite)
    lg = Model()
    lg.box((14, 9.5, 5), (22, 17.5, 37), log("oak", "z"), uvrot=log_uvrot("z"), tile=False)
    for z in (9, 31): lg.box((12.3, 8.5, z), (23.7, 9.5, z + 2.2), DO)
    for z in (9, 31):
        for x in (12.6, 22): lg.box((x, 9.5, z + 0.3), (x + 1.4, 12, z + 1.9), "iron_dark", tile=False)
    log_keys = [key(22, t=(0, 0, 8)), key(2, t=(0, 0, 8)), key(6), key(2)]

    # --- roue à aubes, arbre et manivelle
    w = Model(); ctr = (42.0, 18.0, 24.0)
    w.box((26, 17, 23), (47.6, 19, 25), DO, tile=False)
    w.box((26.05, 17.05, 23.05), (47.55, 18.95, 24.95), DO, rot=("x", 45, ctr), tile=False)        # arbre à huit pans
    disc(w, ctr, 3.4, 37.8, 46.2, DO)
    for (xa, xb) in ((38.5, 40), (44, 45.5)):
        for i, ang in enumerate((0, 45)):
            r = ("x", ang, ctr) if ang else None
            d = 0.25 + 0.05 * i
            w.box((xa + d, 4.6, 23.3), (xb - d, 31.4, 24.7), SP, rot=r, tile=False)
            w.box((xa + d + 0.02, 17.3, 10.6), (xb - d - 0.02, 18.7, 37.4), SP, rot=r, tile=False)
        ring(w, ctr, 12.4, 14.4, xa, xb, DO)
    for ang in (0, 22.5, 45, -22.5):
        r = ("x", ang, ctr) if ang else None
        for (f, t) in (((38.1, 29.4, 23.5), (45.9, 34.2, 24.5)), ((38.1, 1.8, 23.5), (45.9, 6.6, 24.5)),
                       ((38.1, 17.5, 35.4), (45.9, 18.5, 40.2)), ((38.1, 17.5, 7.8), (45.9, 18.5, 12.6))):
            w.box(f, t, SP, rot=r, tile=False)

    parts = [Part("roue", w, ctr, spin("x", 4, -1)),
             Part("scie", saw, (18, 14, 24), saw_keys),
             Part("grume", lg, (18, 13.5, 20), log_keys),
             banner("banner_green", 18, 44.4, 24, height=7)]
    em = [Emitter("wood", (18, 18.5, 22.5), 3, (0.06, 0.04, 0.06), 0.03, period=2),
          Emitter("splash", (42, 5.5, 33), 2, (0.2, 0.05, 0.12), 0.0, period=2, at=1)]
    return Building("scierie", b, parts, em)


# ====================================================================== FERME (moulin à vent)
def octa(m, cx, cz, r, y0, y1, tex):
    """Tour octogonale « en blocs » : trois boîtes croisées."""
    k, d = r * 0.44, r * 0.78
    m.box((cx - r, y0, cz - k), (cx + r, y1, cz + k), tex)
    m.box((cx - k, y0, cz - r), (cx + k, y1, cz + r), tex)
    m.box((cx - d, y0, cz - d), (cx + d, y1, cz + d), tex)

def moulin():
    """Ferme : moulin à vent en pierre et torchis, ailes qui tournent, champ de blé qui ondule, épouvantail."""
    b, glow = Model(), Model()
    cx, cz = 24, 30
    # --- tour
    octa(b, cx, cz, 12.3, 0, 3, MCOBBLE)
    octa(b, cx, cz, 11.5, 3, 15, COBBLE)
    octa(b, cx, cz, 11.0, 14.4, 16.6, DO)
    octa(b, cx, cz, 10.2, 16.6, 30.4, "plaster")
    octa(b, cx, cz, 10.9, 30.4, 32, DO)
    # --- toit de chaume conique
    octa(b, cx, cz, 12.6, 31.6, 33.6, "thatch")
    for i, rr in enumerate((11.2, 9.6, 8.0, 6.4, 4.8, 3.2, 1.8)):
        octa(b, cx, cz, rr, 33.6 + 1.8 * i, 35.6 + 1.8 * i, "thatch")
    # --- porte : seuil au-dessus du soubassement, deux marches, encadrement, vantail ferré
    fz = cz - 11.5
    b.box((19, 0, fz - 5.4), (29, 1.5, fz - 2.6), STONE)
    b.box((19.4, 0, fz - 2.6), (28.6, 3, fz - 0.6), STONE)
    for x in (19.6, 26.8):
        b.box((x, 3, fz - 1.4), (x + 1.6, 13.6, fz + 0.4), log("dark_oak"), tile=False)
    b.box((19, 13.6, fz - 1.7), (29, 15.4, fz + 0.4), DO)
    b.box((21.2, 3, fz - 0.6), (26.8, 13.6, fz + 0.2), SP)
    for y in (5.2, 10.6): b.box((21.1, y, fz - 0.9), (26.9, y + 1, fz - 0.55), "iron_dark", tile=False)
    b.box((25.3, 7.6, fz - 1.1), (26.1, 8.8, fz - 0.55), "mc:gold_block", tile=False, uvo=(4, 4))
    # --- fenêtres : appui en pierre, linteau, volets, petits carreaux éclairés
    def win(axis, wall, n, mid):
        y0, half, hgt = 18.8, 2.2, 5.6
        def bx(a0, a1, y_0, y_1, d0, d1, tex, mdl=b, **kw):
            lo, hi = sorted((wall + n * d0, wall + n * d1))
            if axis == "z": mdl.box((mid + a0, y_0, lo), (mid + a1, y_1, hi), tex, **kw)
            else: mdl.box((lo, y_0, mid + a0), (hi, y_1, mid + a1), tex, **kw)
        bx(-half - 2.2, half + 2.2, y0 - 1.4, y0, -0.3, 1.5, STONE, tile=False)                 # appui
        bx(-half - 1.6, half + 1.6, y0 + hgt, y0 + hgt + 1.4, -0.3, 1.1, DO, tile=False)         # linteau
        bx(-half - 0.7, -half, y0, y0 + hgt, -0.3, 0.7, DO, tile=False); bx(half, half + 0.7, y0, y0 + hgt, -0.3, 0.7, DO, tile=False)
        for sgn in (-1, 1):                                                                       # volets ouverts
            a0, a1 = sorted((sgn * (half + 0.7), sgn * (half + 2.9)))
            bx(a0, a1, y0 + 0.2, y0 + hgt - 0.2, 0.05, 0.6, SP, tile=False)
            bx(a0 - 0.05, a1 + 0.05, y0 + 1.2, y0 + 1.9, 0.6, 0.8, "iron_dark", tile=False); bx(a0 - 0.05, a1 + 0.05, y0 + hgt - 1.9, y0 + hgt - 1.2, 0.6, 0.8, "iron_dark", tile=False)
        face = {("z", -1): "north", ("z", 1): "south", ("x", -1): "west", ("x", 1): "east"}[(axis, n)]
        bx(-half, half, y0, y0 + hgt, 0.12, 0.2, {face: "window"}, mdl=glow, tile=False, uv={face: [0, 0, 8, 12]})
    win("z", cz - 10.2, -1, cx)
    win("x", cx - 10.2, -1, cz); win("x", cx + 10.2, 1, cz)
    # --- chemin, champs, clôture
    b.box((21, 0, 0), (27, 0.6, fz - 5.4), "mc:dirt_path_top")
    b.box((28.5, 0, 1.5), (46.5, 1, 10.5), {"*": "mc:dirt", "up": "mc:farmland_moist"})
    b.box((1.5, 0, 1.5), (19.5, 1, 10.5), {"*": "mc:dirt", "up": "mc:farmland_moist"})
    def fence(x0, x1, z):
        n = max(1, round((x1 - x0) / 9))
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            b.box((x - 0.8, 0, z - 0.8), (x + 0.8, 7.5, z + 0.8), log("oak"), tile=False)
        b.box((x0, 3, z - 0.4), (x1, 4.2, z + 0.4), OAK); b.box((x0, 5.6, z - 0.4), (x1, 6.8, z + 0.4), OAK)
    fence(28.5, 47, 0.9); fence(1, 19.5, 0.9)
    def fence_z(x, z0, z1):
        b.box((x - 0.8, 0, z1 - 0.8), (x + 0.8, 7.5, z1 + 0.8), log("oak"), tile=False)
        b.box((x - 0.4, 3, z0), (x + 0.4, 4.2, z1), OAK); b.box((x - 0.4, 5.6, z0), (x + 0.4, 6.8, z1), OAK)
    fence_z(47, 0.9, 10.6); fence_z(1, 0.9, 10.6)
    # une citrouille devant l'épouvantail
    pk = {"*": "mc:pumpkin_side", "up": "mc:pumpkin_top", "down": "mc:pumpkin_top"}
    b.box((3.5, 1, 3), (10, 6.6, 9.5), pk, tile=False, uvo=(5, 5))
    b.box((6.3, 6.6, 5.8), (7.3, 8.2, 6.8), "mc:moss_block", tile=False)
    # sacs de farine, botte de foin, tonneau
    b.box((31, 0, 17.5), (36, 5.5, 22), "sack", tile=False); b.box((32, 5.5, 18), (35.5, 6.3, 21.5), "rope", tile=False)
    b.box((36.3, 0, 18.5), (40.6, 4.5, 22.5), "sack", tile=False)
    hay = {"*": "mc:hay_block_side", "up": "mc:hay_block_top", "down": "mc:hay_block_top"}
    b.box((6, 0.02, 17.5), (13, 6, 23.5), hay, tile=False, uvo=(4, 5)); b.box((7, 6, 18.2), (12.6, 11, 23), hay, tile=False, uvo=(5, 5))

    # --- ailes
    sails = Model(); hub = (24.0, 30.0, 14.4)
    def r90(p, n):
        x, y = p[0] - hub[0], p[1] - hub[1]
        for _ in range(n): x, y = -y, x
        return (x + hub[0], y + hub[1], p[2])
    def rbox(f, t, tex, n, **kw):
        a, c = r90(f, n), r90(t, n)
        sails.box(tuple(min(a[k], c[k]) for k in range(3)), tuple(max(a[k], c[k]) for k in range(3)), tex, tile=False, **kw)
    sails.box((23, 29, 14.6), (25, 31, 20.2), DO, tile=False)                                 # arbre
    sails.box((21.6, 27.6, 12.2), (26.4, 32.4, 15.2), DO, tile=False)                          # moyeu
    sails.box((23.2, 29.2, 11.4), (24.8, 30.8, 12.2), "iron_dark", tile=False)
    for n in range(4):
        rbox((23.3, 32.4, 13.0), (24.7, 53.4, 14.4), SP, n)                                    # bras
        rbox((25.5, 36.6, 13.5), (31.0, 52.0, 13.9), "sail", n)                                # toile
        rbox((24.7, 52.0, 13.2), (32.0, 53.0, 14.2), SP, n); rbox((24.7, 35.6, 13.2), (32.0, 36.6, 14.2), SP, n)
        rbox((31.0, 36.6, 13.2), (32.0, 52.0, 14.2), SP, n); rbox((24.7, 43.8, 13.3), (31.0, 44.6, 14.1), SP, n)

    # --- blé qui ondule
    wheat = Model()
    for z in (2.8, 5.6, 8.4):
        for (x0, x1) in ((29, 45), ):
            wheat.box((x0, 1, z), (x1, 15, z), {"north": "mc:wheat_stage7", "south": "mc:wheat_stage7"}, tile=False,
                      uv={"north": [0, 2, 16, 16], "south": [0, 2, 16, 16]})
    for x in (31, 35, 39, 43):
        wheat.box((x, 1, 2), (x, 15, 9.5), {"east": "mc:wheat_stage7", "west": "mc:wheat_stage7"}, tile=False,
                  uv={"east": [4, 2, 12, 16], "west": [4, 2, 12, 16]})
    wheat_keys = [key(4, axis="x", angle=5), key(4, axis="x", angle=-2), key(4, axis="x", angle=4), key(4, axis="x", angle=-5)]

    # --- épouvantail
    sc = Model(); sx, sz = 13.0, 7.2
    sc.box((sx - 0.7, 1, sz - 0.7), (sx + 0.7, 15, sz + 0.7), SP, tile=False)
    sc.box((sx - 6, 10.6, sz - 0.6), (sx + 6, 11.8, sz + 0.6), SP, tile=False)
    sc.box((sx - 2.6, 6.5, sz - 1.3), (sx + 2.6, 12.4, sz + 1.3), "sack", tile=False)
    sc.box((sx - 6.4, 9.2, sz - 0.9), (sx - 4.4, 12.2, sz + 0.9), "mc:hay_block_top", tile=False); sc.box((sx + 4.4, 9.2, sz - 0.9), (sx + 6.4, 12.2, sz + 0.9), "mc:hay_block_top", tile=False)
    sc.box((sx - 2, 12.4, sz - 2), (sx + 2, 16.4, sz + 2), {"*": "mc:pumpkin_side", "north": "mc:carved_pumpkin", "up": "mc:pumpkin_top"}, tile=False, uvo=(6, 6),
           uv={"north": [0, 0, 16, 16]})
    sc.box((sx - 3.2, 16.4, sz - 3.2), (sx + 3.2, 17.2, sz + 3.2), "mc:hay_block_top", tile=False)
    sc.box((sx - 1.8, 17.2, sz - 1.8), (sx + 1.8, 19.4, sz + 1.8), "mc:hay_block_top", tile=False, uvo=(3, 3))
    sc_keys = [key(8, axis="z", angle=4), key(8, axis="z", angle=-4)]

    # --- girouette
    v = Model(); vy = 46.2
    v.box((23.6, vy, 29.6), (24.4, vy + 5, 30.4), "iron_dark", tile=False)
    v.box((19.5, vy + 3.2, 29.75), (28.5, vy + 4, 30.25), "iron_dark", tile=False)
    v.box((19.5, vy + 2.2, 29.8), (22.5, vy + 5, 30.2), "mc:gold_block", tile=False, uvo=(3, 3))
    v.box((27.5, vy + 2.9, 29.8), (29.5, vy + 4.3, 30.2), "mc:gold_block", tile=False, uvo=(8, 8))
    v_keys = [key(6, angle=25), key(3, angle=14), key(5, angle=42), key(6, angle=-8), key(4, angle=6), key(8, angle=0)]

    parts = [Part("ailes", sails, hub, spin("z", 8)),
             Part("ble", wheat, (37, 1, 5.6), wheat_keys),
             Part("epouvantail", sc, (sx, 1, sz), sc_keys),
             Part("girouette", v, (24, vy + 2, 30), v_keys),
             Part("lumiere", glow, C, bright=True)]
    em = [Emitter("ash", (24, 9, 16), 2, (0.25, 0.3, 0.15), 0.0, period=4),
          Emitter("grow", (37, 12, 6), 1, (0.5, 0.2, 0.3), 0.0, period=10, at=3)]
    return Building("ferme", b, parts, em)


# ====================================================================== MINE
def mine():
    """Mine : colline rocheuse veinée de minerai, galerie étayée, wagonnet sur rails, puits à treuil."""
    b, glow = Model(), Model()
    ST, AND, TUFF, DEEP = "mc:stone", "mc:andesite", "mc:tuff", "mc:deepslate"
    # --- colline (construite autour de la galerie X 17..31, Y 1..15)
    b.box((2, 0, 18), (17, 20, 46), ST); b.box((31, 0, 18), (46, 20, 46), ST)
    b.box((17, 15, 18), (31, 20, 46), ST)
    b.box((17, 0, 44), (31, 15, 46), ST)
    b.box((5, 20, 21), (43, 29, 46.5), AND)
    b.box((9, 29, 25), (38, 36, 45), ST)
    b.box((15, 36, 30), (32, 41, 44), AND)
    b.box((0.8, 0, 24), (4, 13, 41), COBBLE); b.box((44, 0, 27), (47.2, 15, 44), TUFF)    # épaulements
    b.box((1, 13, 27), (5, 17, 38), MCOBBLE); b.box((40, 20, 23), (45, 24, 34), COBBLE)
    b.box((3, 20, 19.5), (12, 23, 24), COBBLE); b.box((33, 29, 23.5), (40, 32, 30), TUFF)
    b.box((7, 29, 23.5), (14, 31.5, 28), MCOBBLE)
    b.box((2.7, 0, 14), (9, 5, 19), COBBLE); b.box((8, 0, 15.5), (13, 3, 18.5), TUFF)       # rochers au pied
    b.box((33.5, 0, 15.5), (38, 4, 18.5), COBBLE)
    # mousse sur les replats
    for (f, t) in (((15, 41, 30), (32, 42, 44)), ((9, 36, 25), (15, 36.8, 45)), ((32, 36, 31), (38, 36.8, 45)), ((5, 29, 21), (9, 29.8, 40)),
                   ((38, 29, 30), (43, 29.8, 46)), ((2, 20, 24), (5, 20.8, 46)), ((43, 20, 34), (46, 20.8, 46)), ((14, 29, 21), (33, 29.8, 23.5))):
        b.box(f, t, "mc:moss_block")
    # blocs en saillie : casse la silhouette
    for (f, t, tx) in (((6, 6, 16.6), (12, 11, 18), ST), ((34, 10, 16.8), (40, 16, 18), AND), ((36, 0, 44), (44, 9, 47.5), COBBLE),
                       ((6, 0, 44), (14, 12, 47.5), TUFF), ((18, 20, 19.4), (30, 24, 21), ST), ((45, 6, 22), (46.6, 14, 27.6), ST), ((20, 29, 44), (30, 34, 46.6), COBBLE), ((30, 36, 28.6), (35, 39, 32), MCOBBLE),
                       ((12, 36, 27.5), (17, 38.5, 33), TUFF), ((40.5, 24, 24), (44, 26.5, 29), MCOBBLE), ((4, 23, 20.2), (8, 25.5, 23), MCOBBLE)):
        b.box(f, t, tx)
    # buisson et touffes
    b.box((33.5, 36.8, 36), (38.5, 40.6, 41), "mc:azalea_leaves", tile=False); b.box((34.5, 40.6, 37), (37.5, 42.4, 40), "mc:flowering_azalea_leaves", tile=False, uvo=(4, 4))
    b.box((5.4, 29.8, 30), (8.6, 32.4, 33.6), "mc:azalea_leaves", tile=False, uvo=(6, 3))
    # veines de minerai : chaque veine est un petit pavé en relief sur une paroi (jamais dans le même plan qu'elle)
    def vein(face, a0, a1, y0, y1, wall, tx, out=0.5):
        """face : paroi qui porte la veine ; wall = position de cette paroi ; a0..a1 = étendue le long de la paroi."""
        n = -1 if face in ("north", "west") else 1
        lo, hi = sorted((wall - n * 0.3, wall + n * out))
        if face in ("north", "south"): f, t = (a0, y0, lo), (a1, y1, hi)
        else: f, t = (lo, y0, a0), (hi, y1, a1)
        b.box(f, t, tx, tile=False, uvo=(4, 4))
    vein("north", 6.5, 11.5, 6.4, 10.6, 16.6, "mc:gold_ore"); vein("north", 8.6, 12.4, 0.6, 2.6, 15.5, "mc:coal_ore")
    vein("north", 35, 39.5, 10.6, 15.4, 16.8, "mc:iron_ore"); vein("north", 40, 45, 3, 8, 18, "mc:iron_ore")
    vein("north", 20, 25, 20.6, 23.4, 19.4, "mc:copper_ore"); vein("north", 31, 36, 22, 27, 21, "mc:coal_ore")
    vein("north", 15, 19.5, 30.6, 34.6, 25, "mc:coal_ore"); vein("north", 24, 30, 30, 35, 25, "mc:gold_ore")
    vein("east", 30, 37, 4, 10, 47.2, "mc:copper_ore"); vein("west", 30, 36, 5, 10, 0.8, "mc:iron_ore")
    vein("east", 35, 40, 21.4, 26, 43, "mc:gold_ore"); vein("south", 10, 18, 21, 27, 46.5, "mc:iron_ore")
    vein("south", 24, 31, 5, 12, 46, "mc:copper_ore"); vein("west", 40, 45, 14, 19, 2, "mc:coal_ore")
    # --- galerie : parois sombres, fond noir, ballast, rails
    b.box((17, 1, 18), (17.4, 15, 44), DEEP); b.box((30.6, 1, 18), (31, 15, 44), DEEP)
    b.box((17.4, 14.6, 18), (30.6, 15, 44), DEEP)
    b.box((17.4, 1, 43.4), (30.6, 14.6, 44), {"north": "hole"})
    b.box((17, 0, 0), (31, 1, 44), "mc:gravel")
    b.box((16, 1.06, 2), (32, 1.06, 43.4), {"up": "mc:rail"})
    for x in (18.6, 27.8):                                                               # butoir en bout de voie
        b.box((x, 1, 0.5), (x + 1.6, 5.4, 2.1), log("dark_oak"), tile=False)
    b.box((17.8, 3.2, 0.2), (30.2, 4.8, 1.2), SP, tile=False); b.box((17.6, 3.5, 0.0), (18.4, 4.5, 1.4), "iron_dark", tile=False); b.box((29.6, 3.5, 0.0), (30.4, 4.5, 1.4), "iron_dark", tile=False)
    # --- devanture : piédroits en pierre de taille, portique de rondins, contrefiches, enseigne
    for i, y in enumerate((0, 4.25, 8.5, 12.75)):
        d = 1.2 if i % 2 == 0 else 0
        b.box((11.6 - d, y, 16.2), (14.6, y + 4.25, 18.2), STONE); b.box((33.4, y, 16.2), (36.4 + d, y + 4.25, 18.2), STONE)
    for x in (14.5, 30.5): b.box((x, 0, 14), (x + 3, 17, 17.6), log("dark_oak"))
    beam(b, (11.5, 17, 13.5), (36.5, 20.8, 18))
    for x in (13.6, 32.4):                                                               # ferrures du linteau
        b.box((x, 16.8, 13.3), (x + 2, 21, 18.2), "iron_dark", tile=False, skip=("down",))
    brace(b, 16.8, 10.6, 15.8, 6.6, 1); brace(b, 31.2, 10.6, 15.8, 6.6, -1)
    b.box((18.4, 21, 14.4), (29.6, 26.4, 15.6), DO)                                      # enseigne posée sur le linteau
    b.box((19.2, 21.8, 14.1), (28.8, 25.6, 14.5), SP, tile=False)
    b.box((21, 24.2, 13.8), (27, 25, 14.2), "steel", tile=False); b.box((20.4, 23.6, 13.8), (21.2, 24.6, 14.2), "steel", tile=False); b.box((26.8, 23.6, 13.8), (27.6, 24.6, 14.2), "steel", tile=False)
    b.box((23.6, 22.2, 13.8), (24.4, 24.2, 14.2), DO, tile=False)                        # pioche de l'enseigne
    for z in (27, 37):
        b.box((17.4, 1, z), (18.9, 13.4, z + 1.8), SP); b.box((29.1, 1, z), (30.6, 13.4, z + 1.8), SP)
        b.box((17.4, 13.2, z - 0.2), (30.6, 14.6, z + 2), SP)
    # --- puits à treuil
    for (f, t) in (((34.5, 0, 1.5), (47.5, 5, 4)), ((34.5, 0, 11), (47.5, 5, 13.5)), ((34.5, 0, 4), (37, 5, 11)), ((45, 0, 4), (47.5, 5, 11))):
        b.box(f, t, MCOBBLE)
    b.box((37, 0.3, 4), (45, 0.3, 11), {"up": "hole"})
    for x in (35, 45.4): b.box((x, 5, 6.7), (x + 1.6, 26.4, 8.3), log("spruce"))
    b.box((34.4, 21.4, 6.9), (47.6, 22.8, 8.1), SP, tile=False)                          # entrait sous le toit
    gable_roof(b, 33.6, 47.4, 2.5, 12.5, 22.6, 26.6, "shingle", ridge="x", thick=2.2, cap=DO)
    # --- bac à minerai cerclé de fer, pioche appuyée contre, tas de charbon
    for z in (3.6, 9.2): b.box((2.4, 0, z), (11.6, 1.2, z + 1.4), DO, tile=False)        # patins
    b.box((2.6, 1.2, 3), (11.4, 7, 11), SP)
    b.box((2.2, 6.4, 2.6), (11.8, 7.6, 3.6), DO, tile=False); b.box((2.2, 6.4, 10.4), (11.8, 7.6, 11.4), DO, tile=False)   # rebord
    b.box((2.2, 6.4, 3.6), (3.2, 7.6, 10.4), DO, tile=False); b.box((10.8, 6.4, 3.6), (11.8, 7.6, 10.4), DO, tile=False)
    for x in (4.2, 8.6): b.box((x, 1.2, 2.8), (x + 1.2, 6.4, 11.2), "iron_dark", tile=False, skip=("up", "down"))
    b.box((3.2, 6.6, 3.6), (10.8, 8.2, 10.4), "mc:raw_iron_block", tile=False, uvo=(2, 3))
    b.box((4.4, 8.2, 4.6), (9.4, 9.4, 9.2), "mc:raw_iron_block", tile=False, uvo=(6, 5))
    b.box((5.2, 9.4, 5.6), (8, 10.4, 8), "mc:raw_copper_block", tile=False, uvo=(5, 5))
    b.box((8.4, 8.2, 8), (10.2, 9.2, 9.8), "mc:raw_gold_block", tile=False, uvo=(4, 4))
    b.box((0.6, 0, 11.8), (2.8, 1.6, 13.8), "mc:raw_iron_block", tile=False, uvo=(8, 2)); b.box((3.4, 0, 12.2), (4.8, 1, 13.4), "mc:raw_copper_block", tile=False, uvo=(3, 9))
    pr = ("z", 22.5, (15.2, 0, 6.6))                                                     # la pioche penche vers le bac
    b.box((14.6, 0, 6), (15.8, 14.4, 7.2), SP, rot=pr, tile=False)                       # manche
    b.box((14.3, 12.2, 5.7), (16.1, 14.6, 7.5), "iron_dark", rot=pr, tile=False)        # douille
    b.box((14.5, 12.6, 3.6), (15.9, 14.2, 9.6), "steel", rot=pr, tile=False)             # fer : centre
    b.box((14.6, 11.9, 1.8), (15.8, 13.3, 3.6), "steel", rot=pr, tile=False); b.box((14.6, 11.9, 9.6), (15.8, 13.3, 11.4), "steel", rot=pr, tile=False)
    b.box((14.7, 11.0, 0.6), (15.7, 12.2, 1.8), "steel", rot=pr, tile=False); b.box((14.7, 11.0, 11.4), (15.7, 12.2, 12.6), "steel", rot=pr, tile=False)
    b.box((12.4, 0, 14.2), (15.6, 2.4, 17.2), "mc:coal_block", tile=False); b.box((11, 0, 15.6), (12.8, 1.4, 17.6), "mc:coal_block", tile=False, uvo=(6, 3))

    # --- wagonnet
    cart = Model(); zc = 9.0
    cart.box((19, 3.4, zc - 5.5), (29, 9, zc + 5.5), "iron_dark", tile=False)
    cart.box((18.6, 8.4, zc - 5.9), (29.4, 9.6, zc - 5), "steel", tile=False); cart.box((18.6, 8.4, zc + 5), (29.4, 9.6, zc + 5.9), "steel", tile=False)
    cart.box((18.6, 8.4, zc - 5), (19.5, 9.6, zc + 5), "steel", tile=False); cart.box((28.5, 8.4, zc - 5), (29.4, 9.6, zc + 5), "steel", tile=False)
    cart.box((19.5, 9, zc - 5), (28.5, 10.6, zc + 5), "mc:raw_iron_block", tile=False, uvo=(3, 2))
    cart.box((21, 10.6, zc - 3.4), (26.6, 11.8, zc + 2.6), "mc:raw_gold_block", tile=False, uvo=(4, 5))
    cart.box((23, 11.8, zc - 1.5), (25.4, 12.6, zc + 1), "mc:raw_copper_block", tile=False, uvo=(6, 6))
    for z in (zc - 3.4, zc + 3.4):
        for (xa, xb) in ((18, 19), (29, 30)): disc(cart, ((xa + xb) / 2, 2.8, z), 1.8, xa, xb, "iron_dark")
        cart.box((19, 2.3, z - 0.5), (29, 3.4, z + 0.5), "iron_dark", tile=False)
    cart_keys = [key(6), key(10, t=(0, 0, 27)), key(6, t=(0, 0, 27)), key(10)]

    # --- treuil, corde, seau
    wl = Model(); wc = (41.0, 18.0, 7.5)
    wl.box((36.6, 17, 6.5), (45.4, 19, 8.5), log("oak", "x"), uvrot=log_uvrot("x"), tile=False)
    wl.box((38.4, 16.6, 6.1), (43.6, 19.4, 8.9), "rope", tile=False)
    wl.box((45.4, 17.5, 7.0), (47.3, 18.5, 8.0), "iron_dark", tile=False)                # axe qui traverse le poteau
    wl.box((47.05, 17.4, 6.9), (47.85, 21.2, 8.1), "iron_dark", tile=False)              # bras de manivelle, hors du poteau
    wl.box((47.85, 20.2, 7.0), (48.9, 21.2, 8.0), SP, tile=False)                        # poignée
    wl_keys = [key(4, axis="x", angle=120), key(4, axis="x", angle=240), key(4, axis="x", angle=360), key(4, axis="x", angle=360),
               key(4, axis="x", angle=240), key(4, axis="x", angle=120), key(4, axis="x", angle=0), key(4, axis="x", angle=0)]
    top, low, high = 17.4, 8.8, 14.8                                                     # la corde va du tambour à l'anse du seau
    rope = Model().box((40.7, top - 10, 7.2), (41.3, top, 7.8), "rope", tile=False, skip=("down",))
    s_low, s_high = (top - low) / 10, (top - high) / 10
    rope_keys = [key(12, s=(1, s_high, 1)), key(4, s=(1, s_high, 1)), key(12, s=(1, s_low, 1)), key(4, s=(1, s_low, 1))]
    bk = Model()
    bk.box((38.6, 0.6, 5.3), (43.4, 5.2, 9.7), SP, tile=False)
    bk.box((38.4, 3.8, 5.1), (43.6, 4.6, 9.9), "iron_dark", tile=False, skip=("up", "down"))
    bk.box((39.2, 5.2, 5.9), (42.8, 6, 9.1), "mc:raw_gold_block", tile=False, uvo=(5, 5))
    for x in (38.2, 43.2): bk.box((x, 4.4, 7.1), (x + 0.6, 8.2, 7.9), "iron_dark", tile=False)      # anse
    bk.box((38.2, 8.2, 7.1), (43.8, 8.8, 7.9), "iron_dark", tile=False)
    lift = high - low
    bk_keys = [key(12, t=(0, lift, 0)), key(4, t=(0, lift, 0)), key(12), key(4)]

    parts = [Part("wagonnet", cart, (24, 6, zc), cart_keys),
             Part("treuil", wl, wc, wl_keys),
             Part("corde", rope, (41, top, 7.5), rope_keys),
             Part("seau", bk, (41, 3, 7.5), bk_keys),
             banner("banner_blue", 23, 42, 37, height=6.5)]
    em = [Emitter("stone", (24, 3, 19), 2, (0.3, 0.1, 0.2), 0.02, period=6)]
    return Building("mine", b, parts, em)


# ====================================================================== FORGE
def forge():
    """Forge : âtre et cheminée de brique, soufflet, martinet qui frappe l'enclume, meule, toit d'ardoise."""
    b, glow = Model(), Model()
    b.box((1, 0, 3), (47, 2, 47), STONE)
    b.box((14, 0, 0.5), (34, 1, 3), COBBLE)
    # --- âtre et cheminée
    b.box((24, 2, 30), (46, 7, 46), STONE)
    b.box((24, 7, 30), (28, 16, 46), STONE); b.box((42, 7, 30), (46, 16, 46), STONE)
    b.box((28, 7, 43), (42, 16, 46), STONE)
    b.box((28, 7.6, 42.5), (42, 16, 43), "mc:deepslate_bricks")
    b.box((23.4, 16, 29.4), (46.6, 19.5, 46), STONE)
    b.box((26, 19.5, 32), (44, 23, 44), "mc:bricks")
    b.box((24, 19.5, 44), (46, 24, 46), "mc:bricks")                                    # dos de la hotte, dans le plan du mur
    b.box((29, 23, 35), (41, 44, 46.4), "mc:bricks")
    b.box((27.8, 44, 33.8), (42.2, 46, 47.2), STONE)
    b.box((30.5, 46.05, 36.5), (39.5, 46.05, 43.5), {"up": "hole"})
    glow.box((28, 7, 30.6), (42, 8, 42.5), "mc:magma")
    # --- charpente et murs
    for (x, z) in ((2, 4), (43, 4), (2, 43)):
        b.box((x, 2, z), (x + 3, 24, z + 3), log("dark_oak"))
    for z in (4, 43): beam(b, (1, 24, z), (47, 26.5, z + 3))
    for x in (2, 43): beam(b, (x, 24, 1.5), (x + 3, 26.5, 47))
    brace(b, 4, 15.4, 5.5, 9.4, 1); brace(b, 44, 15.4, 5.5, 9.4, -1)                     # noyées dans le poteau et la sablière
    brace(b, 3.5, 15.4, 6, 9.4, 1, axis="x"); brace(b, 44.5, 15.4, 6, 9.4, 1, axis="x")
    brace(b, 3.5, 15.4, 44, 9.4, -1, axis="x")
    # mur du fond : soubassement de pierre sur toute la largeur, torchis à pans de bois au-dessus
    b.box((5, 2, 44), (24, 11, 46), STONE); b.box((5, 12.4, 44.4), (24, 24, 45.6), "plaster")
    b.box((4.6, 11, 43.8), (24.2, 12.4, 46.2), DO); b.box((13.6, 12.4, 44.1), (15, 24, 45.9), DO)
    b.box((23, 12.4, 44.1), (24.2, 24, 45.9), DO)
    b.box((2.6, 2, 7), (4.2, 10, 43), STONE); b.box((2.4, 10, 7), (4.4, 11.2, 43), DO)
    gable_fill(b, 2, 46, 2.5, 3.7, 26.5, 38.5, "plaster", ridge="x")
    gable_fill(b, 2, 46, 44.3, 45.5, 26.5, 38.5, "plaster", ridge="x")
    for x in (2.2, 44.2):
        b.box((x - 0.1, 26.5, 23), (x + 1.7, 38.3, 25), DO)                              # poinçon
        b.box((x - 0.1, 30.4, 13.6), (x + 1.7, 31.8, 34.4), DO)                          # entrait retroussé, à l'abri sous le toit
    gable_roof(b, 0.6, 47.4, 0.4, 47.6, 24.6, 38.6, "mc:deepslate_tiles", ridge="x", cap="mc:deepslate_bricks")
    # --- enclume sur son billot : pied, col, table, bigorne à deux ressauts, talon
    b.box((20, 2, 14), (27, 8, 21), log("oak"), tile=False)
    b.box((20.6, 8, 15.4), (26.4, 9.4, 19.6), "iron_dark", tile=False)
    b.box((22, 9.4, 16.2), (25, 11.4, 18.8), "iron_dark", tile=False)
    b.box((19.6, 11.4, 15.6), (27.4, 13.5, 19.4), "iron_dark", tile=False)
    b.box((27.4, 12.1, 16.2), (29.4, 13.5, 18.8), "iron_dark", tile=False)
    b.box((29.4, 12.7, 16.8), (30.9, 13.5, 18.2), "iron_dark", tile=False)
    b.box((18.4, 12.5, 16), (19.6, 13.5, 19), "iron_dark", tile=False)
    glow.box((21.6, 13.5, 16.7), (25.6, 14.3, 18.3), "hot", tile=False)
    # --- bâti du martinet
    for z in (13.6, 19.8):
        b.box((8.8, 2, z), (11.2, 19.4, z + 1.6), DO)
    b.box((8.4, 2, 13.4), (11.6, 3.4, 21.6), DO)
    # --- pieds du soufflet
    for x in (10, 19.5):
        for z in (35, 39.5): b.box((x, 2, z), (x + 1.5, 9, z + 1.5), SP)
    b.box((21.5, 9.6, 37), (25, 11.4, 39), "iron_dark", tile=False)
    # --- poste d'affûtage : auge pleine d'eau, deux fourches qui portent l'axe, repose-lame
    b.box((4.4, 2, 5.4), (13.6, 5, 10.6), SP)
    b.box((5.2, 5.02, 6.2), (12.8, 5.02, 9.8), {"up": "water_still"}, tile=False, uv={"up": [0, 0, 7.6, 3.6]})
    for z in (3.8, 10.8):
        b.box((8.1, 2, z), (9.9, 8.6, z + 1.4), DO, tile=False)
        b.box((7.5, 8.6, z), (8.5, 10.6, z + 1.4), DO, tile=False); b.box((9.5, 8.6, z), (10.5, 10.6, z + 1.4), DO, tile=False)
    b.box((14.6, 2, 7.2), (16, 13.8, 8.8), DO, tile=False)                               # repose-lame
    b.box((6.2, 13.8, 7.6), (16.4, 14.4, 8.4), "steel", tile=False)                      # épée en cours d'affûtage
    b.box((16.4, 13.1, 7.0), (17.2, 15.1, 9.0), "mc:gold_block", tile=False, uvo=(4, 4))
    b.box((17.2, 13.7, 7.6), (20, 14.5, 8.4), DO, tile=False); b.box((20, 13.5, 7.4), (20.8, 14.7, 8.6), "mc:gold_block", tile=False, uvo=(8, 8))
    # --- baquet de trempe
    bs = {"*": "mc:barrel_side", "up": "mc:barrel_top", "down": "mc:barrel_bottom"}
    b.box((33, 2, 7), (41, 11, 15), bs, tile=False, uvo=(4, 0))
    b.box((34, 11.05, 8), (40, 11.05, 14), {"up": "water_still"}, tile=False, uv={"up": [0, 0, 6, 6]})
    # --- établi, râtelier d'outils, lingots, charbon
    b.box((5, 8, 23), (10, 9.2, 37), SP)
    for z in (23.4, 35.4): b.box((5.4, 2, z), (6.6, 8, z + 1.2), DO); b.box((8.4, 2, z), (9.6, 8, z + 1.2), DO)
    b.box((5.6, 9.2, 25), (9, 11.6, 28), "steel", tile=False); b.box((6.4, 11.6, 25.8), (8.2, 12.4, 27.2), "steel", tile=False)      # heaume
    b.box((6, 9.2, 30.5), (9.4, 10, 35.5), "mc:iron_block", tile=False, uvo=(2, 2))
    # --- mur du fond : râtelier d'outils sous la sablière
    wz = 44.4                                                                            # face du torchis
    b.box((6, 22, wz - 1.2), (22.6, 23.2, wz), DO, tile=False)
    for x in (7.2, 11.4, 16.6, 20.3): b.box((x, 21.4, wz - 1.6), (x + 0.8, 22, wz - 1.2), "iron_dark", tile=False)
    b.box((7.2, 15, wz - 0.9), (8, 22, wz - 0.3), SP, tile=False)                        # marteau
    b.box((5.9, 14.6, wz - 1.2), (9.3, 16.8, wz - 0.1), "iron_dark", tile=False)
    b.box((10.9, 16.6, wz - 0.8), (11.5, 22, wz - 0.3), "iron_dark", tile=False); b.box((12.1, 16.6, wz - 0.8), (12.7, 22, wz - 0.3), "iron_dark", tile=False)   # pinces
    b.box((10.7, 17.8, wz - 1.0), (12.9, 18.6, wz - 0.2), "steel", tile=False)
    b.box((11.2, 14.6, wz - 0.8), (12.4, 16.6, wz - 0.3), "iron_dark", tile=False)
    b.box((16.5, 13.4, wz - 0.7), (17.5, 19.6, wz - 0.3), "steel", tile=False)                                                                # épée
    b.box((15.6, 19.6, wz - 0.9), (18.4, 20.4, wz - 0.1), "mc:gold_block", tile=False, uvo=(4, 6)); b.box((16.6, 20.4, wz - 0.7), (17.4, 22, wz - 0.3), DO, tile=False)
    disc(b, (20.7, 17.4, wz - 0.6), 3.0, wz - 1.1, wz - 0.1, SP, axis="z")                                                                     # rondache
    disc(b, (20.7, 17.4, wz - 0.9), 1.0, wz - 1.7, wz - 1.0, "iron_dark", axis="z")
    for (dx, dy) in ((-2.1, 0), (2.1, 0), (0, -2.1), (0, 2.1)):
        b.box((20.7 + dx - 0.3, 17.4 + dy - 0.3, wz - 1.35), (20.7 + dx + 0.3, 17.4 + dy + 0.3, wz - 1.1), "mc:gold_block", tile=False, uvo=(6, 6))
    b.box((6.2, 9.2, 31), (9.2, 9.8, 31.6), "iron_dark", tile=False); b.box((6.2, 9.2, 32.6), (9.2, 9.8, 33.2), "iron_dark", tile=False)      # pinces sur l'établi
    b.box((13, 2, 24), (19, 3.5, 29), "mc:iron_block", tile=False, uvo=(1, 1)); b.box((14, 3.5, 24.6), (18, 5, 28.4), "mc:iron_block", tile=False, uvo=(5, 5))
    b.box((14.6, 5, 25.4), (17.4, 6.3, 27.6), "mc:gold_block", tile=False, uvo=(3, 3))
    # --- bac à charbon au pied de l'âtre
    b.box((35, 2, 21), (43, 6.4, 28), SP)
    for (x, z) in ((34.7, 20.7), (42.1, 20.7), (34.7, 27.1), (42.1, 27.1)): b.box((x, 2, z), (x + 1.2, 7, z + 1.2), DO, tile=False)
    b.box((35.8, 6.4, 21.8), (42.2, 7.6, 27.2), "mc:coal_block", tile=False); b.box((37, 7.6, 23), (40.6, 8.6, 26), "mc:coal_block", tile=False, uvo=(6, 4))
    # --- flammes de l'âtre (texture animée + vacillement)
    fire = Model(); ff = "mc:campfire_fire"
    for z in (33.5, 37.5, 41):
        fire.box((28.6, 8, z), (41.4, 15.6, z), {"north": ff, "south": ff}, tile=False, uv={"north": [1, 6, 15, 16], "south": [1, 6, 15, 16]})
    for x in (31.5, 35, 38.5):
        fire.box((x, 8, 31), (x, 15.6, 42.4), {"east": ff, "west": ff}, tile=False, uv={"east": [2, 6, 14, 16], "west": [2, 6, 14, 16]})

    # --- martinet
    hm = Model(); hp = (10.0, 17.6, 17.5)
    hm.box((4, 16.8, 16.6), (24.6, 18.6, 18.4), SP, tile=False)
    hm.box((21.6, 14.5, 15.9), (25.6, 20.4, 19.1), "iron_dark", tile=False)
    hm.box((21.2, 18.9, 15.6), (26, 19.8, 19.4), "steel", tile=False)
    hm.box((8.6, 16.6, 15.2), (11.4, 18.8, 19.8), "iron_dark", tile=False)
    hm.box((3.4, 16.4, 16.2), (5, 19, 18.8), "iron_dark", tile=False)
    hm_keys = [key(4, axis="z", angle=24), key(1, axis="z", angle=24), key(1, axis="z", angle=0), key(2, axis="z", angle=0)]

    # --- soufflet
    bl = Model()
    bl.box((9, 9, 34), (22, 10, 42), SP, tile=False)
    bl.box((10, 10, 35), (21.4, 15, 41), "leather", tile=False)
    bl.box((9, 15, 34), (22, 16, 42), SP, tile=False)
    bl.box((4.6, 15.1, 37.3), (9, 15.9, 38.7), DO, tile=False)
    for x in (11, 15, 19): bl.box((x, 9.6, 34.7), (x + 0.8, 15.4, 41.3), "iron_dark", tile=False)
    bl_keys = [key(3, s=(1, 0.5, 1)), key(5)]

    # --- meule à aiguiser : roue de grès sur son axe, manivelle en façade
    gr = Model(); gc = (9.0, 9.6, 8.0)
    disc(gr, gc, 4.4, 6.9, 9.1, "whetstone", axis="z")
    disc(gr, gc, 1.1, 6.5, 9.5, "iron_dark", axis="z")
    gr.box((8.5, 9.1, 3.2), (9.5, 10.1, 12.4), "iron_dark", tile=False)                  # axe
    gr.box((8.5, 9.1, 2.6), (9.5, 12.6, 3.3), "iron_dark", tile=False)                   # manivelle
    gr.box((8.4, 11.6, 1.2), (9.6, 12.8, 2.6), SP, tile=False)

    parts = [Part("marteau", hm, hp, hm_keys),
             Part("soufflet", bl, (15.5, 9, 38), bl_keys),
             Part("meule", gr, gc, spin("z", 1)),
             Part("feu", fire, (35, 8, 37), bright=True, jitter=0.22),
             banner("banner_red", 8, 40.4, 24, height=6.5),
             Part("lumiere", glow, C, bright=True)]
    em = [Emitter("smoke", (35, 47, 40), 0, (0.0, 1.0, 0.0), 0.05, period=2),
          Emitter("spark", (23.6, 14.8, 17.5), 7, (0.12, 0.05, 0.12), 0.12, period=8, at=6),
          Emitter("lava", (23.6, 14.8, 17.5), 1, (0.05, 0.02, 0.05), 0.0, period=8, at=6),
          Emitter("flame", (35, 11, 31.5), 3, (0.3, 0.12, 0.1), 0.01, period=8, at=3),
          Emitter("spark", (9, 14.6, 8), 2, (0.06, 0.03, 0.04), 0.06, period=2)]
    return Building("forge", b, parts, em)


MACHINES = {"scierie": scierie, "ferme": moulin, "mine": mine, "forge": forge}
