"""Les quatre bâtiments du royaume, dessinés boîte par boîte (repère de dessin : voir machines_core.py)."""
from machines_core import *          # noqa: F401,F403

C = (24.0, 24.0, 24.0)               # pivot des pièces immobiles (socle, lumière)
STONE, MOSSY, COBBLE, MCOBBLE = "mc:stone_bricks", "mc:mossy_stone_bricks", "mc:cobblestone", "mc:mossy_cobblestone"


# ====================================================================== SCIERIE
def scierie():
    """Scierie à eau : hangar à pans de bois, roue à aubes, scie à cadre qui monte et descend, grume qui avance."""
    b, glow = Model(), Model()
    # --- dallage et canal
    b.box((1, 0, 3), (35, 2, 47), {"*": STONE, "up": "mc:stone_bricks"})
    b.box((11, 0, 0.5), (25, 1, 3), SP)                                   # marche d'entrée
    b.box((36, 0, 0), (48, 1, 48), COBBLE)
    b.box((36, 1, 0), (37.5, 5, 48), MCOBBLE)
    b.box((46.5, 1, 0), (48, 5, 48), MCOBBLE)
    b.box((37.5, 1, 0), (46.5, 4, 48), "water")
    # --- ossature
    for (x, z) in ((2, 4), (31, 4), (2, 43), (31, 43)):
        b.box((x, 2, z), (x + 3, 24, z + 3), log("dark_oak"))
    for x in (2, 31):
        b.box((x, 2, 23), (x + 3, 24, 26), log("dark_oak"))             # poteaux intermédiaires
    for z in (4, 43):
        beam(b, (1, 24, z), (35, 26.5, z + 3))                           # entraits
    for x in (2, 31):
        beam(b, (x, 24, 1.5), (x + 3, 26.5, 47))                         # sablières
    beam(b, (16.5, 24, 23), (19.5, 26.5, 26), "dark_oak")
    # jambes de force des poteaux de façade
    b.box((5, 16, 4.6), (6.4, 28, 6.4), DO, rot=("z", -45, (5, 18, 5.5)))
    b.box((29.6, 16, 4.6), (31, 28, 6.4), DO, rot=("z", 45, (31, 18, 5.5)))
    # pignon de façade ouvert : poinçon et contrefiches
    b.box((17, 26.5, 4.5), (19, 40, 6.5), DO)
    b.box((9.3, 25, 4.8), (10.7, 38, 6.2), DO, rot=("z", -45, (10, 27, 5.5)))
    b.box((25.3, 25, 4.8), (26.7, 38, 6.2), DO, rot=("z", 45, (26, 27, 5.5)))
    # --- murs : fond plein, côté roue à mi-hauteur, côté opposé ajouré
    b.box((5, 2, 44), (31, 24, 45.2), SP)
    b.box((4.5, 12, 43.5), (31.5, 13.6, 45.6), DO)
    gable_fill(b, 2, 34, 44, 45.2, 26.5, 40.5, SP)
    b.box((32, 2, 7), (33.2, 13, 23), SP); b.box((32, 2, 26), (33.2, 13, 43), SP)
    b.box((31.6, 13, 7), (33.6, 14.2, 43), DO)
    b.box((2.8, 9, 7), (4.2, 10.4, 23), DO); b.box((2.8, 9, 26), (4.2, 10.4, 43), DO)      # lisse basse côté ouvert
    # --- toit en bardeaux
    gable_roof(b, 0, 36, 1, 47.4, 24.6, 40.6, "shingle", ridge="z", cap=DO)
    # --- banc de sciage : rails et tréteaux
    for x in (13, 21.5):
        b.box((x, 7, 5), (x + 1.5, 8.5, 43), DO)
    for z in (7, 16, 32, 40.5):
        for x in (13, 21.5): b.box((x, 2, z), (x + 1.5, 7, z + 1.5), SP)
        b.box((12.5, 4.5, z + 0.2), (23.5, 5.7, z + 1.3), SP)
    for x in (9.5, 22.5):                                                # glissières du cadre de scie
        b.box((x, 2, 22), (x + 4, 7.5, 26), {"*": SP, "up": "hole"})
    # --- décor (allégé : Thozire a retiré la pile de planches, le billot et les grumes en attente)
    b.box((14.5, 2, 20.5), (21.5, 3, 27.5), "sawdust"); b.box((16, 3, 22), (20, 3.9, 26), "sawdust")
    b.box((7.2, 24.2 - 2.4, 4.2), (8.8, 24.2, 4.9), "iron_dark", tile=False)                   # potence de lanterne
    lantern(b, glow, 8, 21.6, 2.8, hang=0.6)
    b.box((7.6, 21.6, 2.2), (8.4, 22.4, 4.4), "iron_dark", tile=False)

    # --- scie à cadre (monte et descend)
    saw = Model()
    for x in (10.5, 23.5): saw.box((x, 4, 23), (x + 2, 23, 25), DO)
    saw.box((9.5, 21, 22.7), (26.5, 23.6, 25.3), DO)
    saw.box((17, 20, 22.9), (19, 21, 25.1), "iron_dark", tile=False)
    saw.box((17.8, 4, 22.5), (18.2, 21, 25.5), {"east": "blade", "west": "blade"}, tile=False,
            uv={"west": [0, 0, 3, 16], "east": [3, 0, 0, 16]})
    saw_keys = [key(1, t=(0, 2.4, 0)), key(1, t=(0, -1.4, 0))]

    # --- grume sur son chariot (avance lentement, revient vite)
    lg = Model()
    lg.box((14, 9.5, 6), (22, 17.5, 34), log("oak", "z"), uvrot=log_uvrot("z"), tile=False)
    for z in (9, 29): lg.box((12.3, 8.5, z), (23.7, 9.5, z + 2.2), DO)
    for z in (9, 29):
        for x in (12.6, 22): lg.box((x, 9.5, z + 0.3), (x + 1.4, 12, z + 1.9), "iron_dark", tile=False)
    log_keys = [key(22, t=(0, 0, 8)), key(2, t=(0, 0, 8)), key(6), key(2)]

    # --- roue à aubes, arbre et manivelle
    w = Model(); ctr = (42.0, 18.0, 24.0)
    w.box((26, 17, 23), (47.6, 19, 25), DO, tile=False)
    disc(w, (26.75, 18, 24), 3.2, 26, 27.5, SP)
    w.box((24.6, 20, 23.3), (26, 21.4, 24.7), "iron_dark", tile=False)
    disc(w, ctr, 3.4, 38, 46, DO)
    for (xa, xb) in ((38.5, 40), (44, 45.5)):
        for ang in (0, 45):
            r = ("x", ang, ctr) if ang else None
            w.box((xa, 4.6, 23.3), (xb, 31.4, 24.7), SP, rot=r, tile=False)
            w.box((xa, 17.3, 10.6), (xb, 18.7, 37.4), SP, rot=r, tile=False)
        ring(w, ctr, 12.4, 14.4, xa, xb, DO)
    for ang in (0, 22.5, 45, -22.5):
        r = ("x", ang, ctr) if ang else None
        for (f, t) in (((38.5, 29.4, 23.5), (45.5, 34.2, 24.5)), ((38.5, 1.8, 23.5), (45.5, 6.6, 24.5)),
                       ((38.5, 17.5, 35.4), (45.5, 18.5, 40.2)), ((38.5, 17.5, 7.8), (45.5, 18.5, 12.6))):
            w.box(f, t, SP, rot=r, tile=False)

    parts = [Part("roue", w, ctr, spin("x", 4, -1)),
             Part("scie", saw, (18, 14, 24), saw_keys),
             Part("grume", lg, (18, 13.5, 20), log_keys),
             banner("banner_green", 18, 42, 3.5, height=7),
             Part("lumiere", glow, C, bright=True)]
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
    r = 10.2; k, d = r * 0.44, r * 0.78
    for (px, pz) in ((-r, -k), (-r, k), (r, -k), (r, k), (-k, -r), (k, -r), (-k, r), (k, r), (-d, -d), (d, -d), (-d, d), (d, d)):
        b.box((cx + px - 0.8, 16.6, cz + pz - 0.8), (cx + px + 0.8, 30.4, cz + pz + 0.8), DO)       # colombages d'angle
    b.box((cx - r - 0.3, 22.6, cz - k), (cx + r + 0.3, 23.8, cz + k), DO)
    b.box((cx - k, 22.6, cz - r - 0.3), (cx + k, 23.8, cz + r + 0.3), DO)
    # --- toit de chaume conique
    octa(b, cx, cz, 12.6, 31.6, 33.6, "thatch")
    for i, rr in enumerate((11.2, 9.6, 8.0, 6.4, 4.8, 3.2, 1.8)):
        octa(b, cx, cz, rr, 33.6 + 1.8 * i, 35.6 + 1.8 * i, "thatch")
    # --- porte, perron, fenêtres
    fz = cz - 11.5
    b.box((20, 0, fz - 3.5), (28, 1, fz + 0.2), STONE)
    b.box((20, 1, fz - 0.9), (21.4, 13, fz + 0.3), log("dark_oak")); b.box((26.6, 1, fz - 0.9), (28, 13, fz + 0.3), log("dark_oak"))
    b.box((19.4, 12.6, fz - 1.1), (28.6, 14.4, fz + 0.3), DO)
    b.box((21.4, 1, fz - 0.5), (26.6, 12.6, fz + 0.1), SP)
    b.box((21.4, 4, fz - 0.7), (26.6, 5, fz - 0.4), "iron_dark", tile=False); b.box((21.4, 9, fz - 0.7), (26.6, 10, fz - 0.4), "iron_dark", tile=False)
    b.box((25.2, 6.4, fz - 0.9), (26, 7.4, fz - 0.4), "mc:gold_block", tile=False, uvo=(4, 4))
    uz = cz - 10.2
    b.box((21, 18.4, uz - 0.5), (27, 25.2, uz + 0.1), DO)
    glow.box((22, 19.4, uz - 0.7), (26, 24.2, uz - 0.4), {"north": "window"}, tile=False)
    for sx, face in ((-1, "west"), (1, "east")):
        x = cx + sx * 10.2
        b.box((x - 0.4, 18.4, cz - 3), (x + 0.4, 25.2, cz + 3), DO)
        glow.box((x + sx * 0.45 - 0.05, 19.4, cz - 2), (x + sx * 0.45 + 0.05, 24.2, cz + 2), {face: "window"}, tile=False)
    b.box((17.4, 9, fz - 1.2), (18.6, 10.2, fz + 0.4), "iron_dark", tile=False)
    lantern(b, glow, 18, 9, fz - 1.9, hang=0.6)
    b.box((17.6, 9, fz - 2.4), (18.4, 9.8, fz - 0.6), "iron_dark", tile=False)
    # --- chemin, champs, clôture
    b.box((21, 0, 0), (27, 0.6, fz - 3.5), "mc:dirt_path_top")
    b.box((28.5, 0, 1.5), (46.5, 1, 12.5), {"*": "mc:dirt", "up": "mc:farmland_moist"})
    b.box((1.5, 0, 1.5), (19.5, 1, 12.5), {"*": "mc:dirt", "up": "mc:farmland_moist"})
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
    fence_z(47, 0.9, 13); fence_z(1, 0.9, 13)
    # carottes, citrouilles
    for z in (3.2, 6.4):
        b.box((2, 1, z), (18, 12, z), {"north": "mc:carrots_stage3", "south": "mc:carrots_stage3"}, tile=False, uv={"north": [0, 5, 16, 16], "south": [0, 5, 16, 16]})
    pk = {"*": "mc:pumpkin_side", "up": "mc:pumpkin_top", "down": "mc:pumpkin_top"}
    b.box((3, 1, 8), (9, 6, 12.4), pk, tile=False, uvo=(5, 5)); b.box((15, 1, 8.6), (19, 4.6, 12.2), pk, tile=False, uvo=(6, 6))
    b.box((5.5, 6, 9.6), (6.5, 7.4, 10.6), "mc:moss_block", tile=False); b.box((16.6, 4.6, 10), (17.4, 5.6, 10.8), "mc:moss_block", tile=False)
    # sacs de farine, botte de foin, tonneau
    b.box((31, 0, 15.5), (36, 5.5, 20), "sack", tile=False); b.box((32, 5.5, 16), (35.5, 6.3, 19.5), "rope", tile=False)
    b.box((36.3, 0, 17.5), (40.6, 4.5, 21.5), "sack", tile=False)
    hay = {"*": "mc:hay_block_side", "up": "mc:hay_block_top", "down": "mc:hay_block_top"}
    b.box((9, 0, 15), (16, 6, 21), hay, tile=False, uvo=(4, 5)); b.box((10.5, 6, 15.8), (16.5, 11, 20.6), hay, tile=False, uvo=(5, 5))

    # --- ailes
    sails = Model(); hub = (24.0, 30.0, 14.4)
    def r90(p, n):
        x, y = p[0] - hub[0], p[1] - hub[1]
        for _ in range(n): x, y = -y, x
        return (x + hub[0], y + hub[1], p[2])
    def rbox(f, t, tex, n, **kw):
        a, c = r90(f, n), r90(t, n)
        sails.box(tuple(min(a[k], c[k]) for k in range(3)), tuple(max(a[k], c[k]) for k in range(3)), tex, tile=False, **kw)
    sails.box((23, 29, 13), (25, 31, 20.2), DO, tile=False)
    sails.box((21.8, 27.8, 12.6), (26.2, 32.2, 15.2), DO, tile=False)
    sails.box((23.3, 29.3, 11.8), (24.7, 30.7, 12.6), "iron_dark", tile=False)
    for n in range(4):
        rbox((23.3, 32.2, 13.5), (24.7, 53, 14.9), SP, n)
        rbox((24.7, 36, 13.9), (31.4, 52.6, 14.4), "sail", n)
        rbox((24.7, 52, 13.7), (31.6, 53, 14.7), SP, n); rbox((24.7, 35.4, 13.7), (31.6, 36.4, 14.7), SP, n)
        rbox((30.8, 35.4, 13.7), (31.8, 53, 14.7), SP, n)

    # --- blé qui ondule
    wheat = Model()
    for z in (3.2, 6.4, 9.6):
        for (x0, x1) in ((29, 45), ):
            wheat.box((x0, 1, z), (x1, 15, z), {"north": "mc:wheat_stage7", "south": "mc:wheat_stage7"}, tile=False,
                      uv={"north": [0, 2, 16, 16], "south": [0, 2, 16, 16]})
    for x in (31, 35, 39, 43):
        wheat.box((x, 1, 2), (x, 15, 12), {"east": "mc:wheat_stage7", "west": "mc:wheat_stage7"}, tile=False,
                  uv={"east": [3, 2, 13, 16], "west": [3, 2, 13, 16]})
    wheat_keys = [key(4, axis="x", angle=5), key(4, axis="x", angle=-2), key(4, axis="x", angle=4), key(4, axis="x", angle=-5)]

    # --- épouvantail
    sc = Model(); sx, sz = 11.5, 10.2
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
             Part("ble", wheat, (37, 1, 6.4), wheat_keys),
             Part("epouvantail", sc, (sx, 1, sz), sc_keys),
             Part("girouette", v, (24, vy + 2, 30), v_keys),
             Part("lumiere", glow, C, bright=True)]
    em = [Emitter("ash", (24, 9, 16), 2, (0.25, 0.3, 0.15), 0.0, period=4),
          Emitter("grow", (37, 12, 6), 1, (0.5, 0.2, 0.3), 0.0, period=10, at=3)]
    return Building("moulin", b, parts, em)


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
    b.box((0, 0, 24), (4, 13, 41), COBBLE); b.box((44, 0, 27), (48, 15, 44), TUFF)        # épaulements
    b.box((1, 13, 27), (5, 17, 38), MCOBBLE); b.box((40, 20, 23), (45, 24, 34), COBBLE)
    b.box((3, 20, 19.5), (12, 23, 24), COBBLE); b.box((33, 29, 23.5), (40, 32, 30), TUFF)
    b.box((7, 29, 23.5), (14, 31.5, 28), MCOBBLE)
    b.box((2, 0, 14), (9, 5, 19), COBBLE); b.box((8, 0, 15.5), (13, 3, 18.5), TUFF)       # rochers au pied
    b.box((33.5, 0, 15.5), (38, 4, 18.5), COBBLE)
    # mousse sur les replats
    for (f, t) in (((15, 41, 30), (32, 42, 44)), ((9, 36, 25), (15, 36.8, 45)), ((32, 36, 31), (38, 36.8, 45)), ((5, 29, 21), (9, 29.8, 40)),
                   ((38, 29, 30), (43, 29.8, 46)), ((2, 20, 24), (5, 20.8, 46)), ((43, 20, 34), (46, 20.8, 46)), ((14, 29, 21), (33, 29.8, 23.5))):
        b.box(f, t, "mc:moss_block")
    # blocs en saillie : casse la silhouette
    for (f, t, tx) in (((6, 6, 16.6), (12, 11, 18), ST), ((34, 10, 16.8), (40, 16, 18), AND), ((36, 0, 44), (44, 9, 47.5), COBBLE),
                       ((6, 0, 44), (14, 12, 47.5), TUFF), ((18, 20, 19.4), (30, 24, 21), ST), ((0.6, 4, 28), (2, 11, 36), AND),
                       ((46, 6, 22), (47.4, 14, 30), ST), ((20, 29, 44), (30, 34, 46.6), COBBLE), ((30, 36, 28.6), (35, 39, 32), MCOBBLE),
                       ((12, 36, 27.5), (17, 38.5, 33), TUFF), ((40.5, 24, 24), (44, 26.5, 29), MCOBBLE), ((4, 23, 20.2), (8, 25.5, 23), MCOBBLE)):
        b.box(f, t, tx)
    # buisson et touffes
    b.box((33.5, 36.8, 36), (38.5, 40.6, 41), "mc:azalea_leaves", tile=False); b.box((34.5, 40.6, 37), (37.5, 42.4, 40), "mc:flowering_azalea_leaves", tile=False, uvo=(4, 4))
    b.box((5.4, 29.8, 30), (8.6, 32.4, 33.6), "mc:azalea_leaves", tile=False, uvo=(6, 3))
    # veines de minerai (légèrement en relief)
    for (f, t, tx) in (((6.5, 6.6, 16.2), (11.5, 10.4, 16.6), "mc:gold_ore"), ((8, 1, 15.1), (12, 3, 15.5), "mc:coal_ore"),
                       ((35, 10.6, 16.4), (39.4, 15.4, 16.8), "mc:iron_ore"), ((40, 3, 17.6), (45, 8, 18), "mc:iron_ore"),
                       ((20, 20.6, 19), (25, 23.4, 19.4), "mc:copper_ore"), ((31, 22, 20.6), (36, 27, 21), "mc:coal_ore"),
                       ((11, 30.6, 24.6), (16, 34.6, 25), "mc:coal_ore"), ((24, 30, 24.6), (30, 35, 25), "mc:gold_ore"),
                       ((47.6, 4, 30), (48, 10, 37), "mc:copper_ore"), ((-0.4 + 0.4, 5, 30), (0.4, 10, 36), "mc:iron_ore"),
                       ((43, 21, 34.6), (46.4, 26, 40), "mc:gold_ore"), ((10, 20.4, 46.5), (18, 27, 46.9), "mc:iron_ore"),
                       ((28, 6, 46), (35, 13, 46.4), "mc:copper_ore"), ((1.6, 14, 40), (2, 19, 45), "mc:coal_ore")):
        b.box(f, t, tx, tile=False, uvo=(4, 4))
    # --- galerie : parois sombres, fond noir, ballast, rails
    b.box((17, 1, 18), (17.4, 15, 44), DEEP); b.box((30.6, 1, 18), (31, 15, 44), DEEP)
    b.box((17.4, 14.6, 18), (30.6, 15, 44), DEEP)
    b.box((17.4, 1, 43.4), (30.6, 14.6, 44), {"north": "hole"})
    b.box((17, 0, 0), (31, 1, 44), "mc:gravel")
    b.box((16, 1.06, 2), (32, 1.06, 43.4), {"up": "mc:rail"})
    b.box((18, 1, 0.4), (30, 4.5, 2), DO)                                                # butoir
    # étais
    for x in (14.5, 30.5): b.box((x, 0, 14), (x + 3, 17, 17.6), log("dark_oak"))
    beam(b, (12.5, 17, 13.5), (35.5, 20.6, 18))
    b.box((17.5, 11.5, 15), (18.9, 18.5, 16.6), DO, rot=("z", -45, (17.5, 11.5, 15.8)))
    b.box((29.1, 11.5, 15), (30.5, 18.5, 16.6), DO, rot=("z", 45, (30.5, 11.5, 15.8)))
    for z in (27, 37):
        b.box((17.4, 1, z), (18.9, 13.4, z + 1.8), SP); b.box((29.1, 1, z), (30.6, 13.4, z + 1.8), SP)
        b.box((17.4, 13.2, z - 0.2), (30.6, 14.6, z + 2), SP)
    # torches de l'entrée
    for x in (16, 32):
        b.box((x - 0.6, 8, 12.6), (x + 0.6, 13.5, 14), SP, tile=False)
        glow.box((x - 0.9, 13.5, 12.4), (x + 0.9, 15.3, 14.2), "glow", tile=False, uvo=(5, 5))
        glow.box((x - 1.6, 14.6, 13.3), (x + 1.6, 18.6, 13.3), {"north": "mc:campfire_fire", "south": "mc:campfire_fire"}, tile=False,
                 uv={"north": [5, 5, 11, 16], "south": [5, 5, 11, 16]})
    # --- puits à treuil
    for (f, t) in (((34.5, 0, 1.5), (47.5, 5, 4)), ((34.5, 0, 11), (47.5, 5, 13.5)), ((34.5, 0, 4), (37, 5, 11)), ((45, 0, 4), (47.5, 5, 11))):
        b.box(f, t, MCOBBLE)
    b.box((37, 0.3, 4), (45, 0.3, 11), {"up": "hole"})
    for x in (35, 45.4): b.box((x, 5, 6.7), (x + 1.6, 23, 8.3), log("spruce"))
    gable_roof(b, 33.6, 47.4, 2.5, 12.5, 22.6, 26.6, "shingle", ridge="x", thick=2.2, cap=DO)
    # --- caisse de minerai, pioche, charbon
    b.box((2, 0, 3), (11, 6, 11), SP)
    for (f, t) in (((1.7, 0, 2.7), (3, 6.4, 4)), ((10, 0, 2.7), (11.3, 6.4, 4)), ((1.7, 0, 10), (3, 6.4, 11.3)), ((10, 0, 10), (11.3, 6.4, 11.3))):
        b.box(f, t, DO)
    b.box((3, 6, 4), (10, 7.4, 10), "mc:raw_iron_block", tile=False, uvo=(2, 3)); b.box((4.5, 7.4, 5.2), (8.5, 8.6, 8.6), "mc:raw_copper_block", tile=False, uvo=(5, 5))
    b.box((11.6, 0, 6.2), (12.6, 13, 7.2), SP, rot=("z", 22.5, (12.1, 0, 6.7)), tile=False)
    b.box((4.4, 11, 6.1), (10.6, 12.4, 7.3), "steel", rot=("z", 22.5, (12.1, 0, 6.7)), tile=False)
    b.box((12.5, 0, 9), (16, 2.6, 12.5), "mc:coal_block", tile=False); b.box((11.5, 0, 11.5), (13.5, 1.6, 13.8), "mc:coal_block", tile=False, uvo=(6, 3))

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
    wl.box((45.4, 17.4, 6.9), (47.6, 18.6, 8.1), "iron_dark", tile=False)
    wl.box((46.8, 17.4, 6.9), (47.8, 22.6, 8.1), "iron_dark", tile=False)
    wl_keys = [key(4, axis="x", angle=120), key(4, axis="x", angle=240), key(4, axis="x", angle=360), key(4, axis="x", angle=360),
               key(4, axis="x", angle=240), key(4, axis="x", angle=120), key(4, axis="x", angle=0), key(4, axis="x", angle=0)]
    rope = Model().box((40.6, 8, 7.1), (41.4, 17.4, 7.9), "rope", tile=False)
    rope_keys = [key(12, s=(1, 0.36, 1)), key(4, s=(1, 0.36, 1)), key(12, s=(1, 1.3, 1)), key(4, s=(1, 1.3, 1))]
    bk = Model()
    bk.box((38.6, 0.6, 5.3), (43.4, 5.2, 9.7), SP, tile=False)
    bk.box((38.4, 3.8, 5.1), (43.6, 4.6, 9.9), "iron_dark", tile=False)
    bk.box((39.2, 5.2, 5.9), (42.8, 6, 9.1), "mc:raw_gold_block", tile=False, uvo=(5, 5))
    lift = (17.4 - 9.4 * 0.36) - (17.4 - 9.4 * 1.3)
    bk_keys = [key(12, t=(0, lift, 0)), key(4, t=(0, lift, 0)), key(12), key(4)]

    parts = [Part("wagonnet", cart, (24, 6, zc), cart_keys),
             Part("treuil", wl, wc, wl_keys),
             Part("corde", rope, (41, 17.4, 7.5), rope_keys),
             Part("seau", bk, (41, 3, 7.5), bk_keys),
             banner("banner_blue", 23, 42, 37, height=6.5),
             Part("lumiere", glow, C, bright=True)]
    em = [Emitter("stone", (24, 3, 19), 2, (0.3, 0.1, 0.2), 0.02, period=6),
          Emitter("small_flame", (16, 16.5, 13.3), 1, (0.03, 0.05, 0.03), 0.0, period=5),
          Emitter("small_flame", (32, 16.5, 13.3), 1, (0.03, 0.05, 0.03), 0.0, period=5, at=2)]
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
    b.box((23.4, 16, 29.4), (46.6, 19.5, 46.6), MOSSY)
    b.box((26, 19.5, 32), (44, 23, 46), "mc:bricks")
    b.box((29, 23, 35), (41, 44, 45), "mc:bricks")
    b.box((27.6, 44, 33.6), (42.4, 46, 46.4), STONE)
    b.box((30.5, 46.05, 36.5), (39.5, 46.05, 43.5), {"up": "hole"})
    glow.box((28, 7, 30.6), (42, 8, 42.5), "mc:magma")
    # --- charpente et murs
    for (x, z) in ((2, 4), (43, 4), (2, 43)):
        b.box((x, 2, z), (x + 3, 24, z + 3), log("dark_oak"))
    for z in (4, 43): beam(b, (1, 24, z), (47, 26.5, z + 3))
    for x in (2, 43): beam(b, (x, 24, 1.5), (x + 3, 26.5, 47))
    b.box((5, 18, 4.6), (6.4, 26, 6.4), DO, rot=("z", -45, (5, 18, 5.5)))
    b.box((41.6, 18, 4.6), (43, 26, 6.4), DO, rot=("z", 45, (43, 18, 5.5)))
    b.box((5, 2, 44), (24, 11, 45.6), STONE); b.box((5, 11, 44.2), (24, 24, 45.4), "plaster")
    b.box((4.6, 11, 43.8), (24, 12.4, 45.8), DO); b.box((13.6, 12.4, 43.9), (15, 24, 45.7), DO)
    b.box((2.6, 2, 7), (4.2, 10, 43), STONE); b.box((2.4, 10, 7), (4.4, 11.2, 43), DO)
    gable_fill(b, 2, 46, 2.5, 3.7, 26.5, 38.5, "plaster", ridge="x")
    gable_fill(b, 2, 46, 44.3, 45.5, 26.5, 38.5, "plaster", ridge="x")
    for x in (2.2, 44.2):
        b.box((x, 26.5, 23), (x + 1.6, 38.5, 25), DO)
        b.box((x, 30.4, 10), (x + 1.6, 31.8, 38), DO)
    gable_roof(b, 0.6, 47.4, 0.4, 47.6, 24.6, 38.6, "mc:deepslate_tiles", ridge="x", cap="mc:deepslate_bricks")
    # --- enclume sur son billot
    b.box((20, 2, 14), (27, 8, 21), log("oak"))
    b.box((20.5, 8, 15.5), (26.5, 9.5, 19.5), "iron_dark", tile=False)
    b.box((22, 9.5, 16.2), (25, 11.5, 18.8), "iron_dark", tile=False)
    b.box((19.4, 11.5, 15.5), (27.6, 13.5, 19.5), {"*": "iron_dark", "up": "mc:anvil_top"}, tile=False)
    b.box((27.6, 12, 16.5), (30, 13.2, 18.5), "iron_dark", tile=False)
    glow.box((21.6, 13.5, 16.7), (25.6, 14.3, 18.3), "hot", tile=False)
    # --- bâti du martinet
    for z in (13.6, 19.8):
        b.box((8.8, 2, z), (11.2, 19.4, z + 1.6), DO)
    b.box((8.4, 2, 13.4), (11.6, 3.4, 21.6), DO)
    # --- pieds du soufflet
    for x in (10, 19.5):
        for z in (35, 39.5): b.box((x, 2, z), (x + 1.5, 9, z + 1.5), SP)
    b.box((21.5, 9.6, 37), (25, 11.4, 39), "iron_dark", tile=False)
    # --- bâti de la meule
    for z in (4.8, 9.6):
        b.box((3.4, 2, z), (4.8, 10.6, z + 1.4), SP); b.box((11.2, 2, z), (12.6, 10.6, z + 1.4), SP)
    b.box((3.4, 2, 6.2), (12.6, 3.4, 9.6), {"*": SP, "up": "water"})
    # --- baquet de trempe
    bs = {"*": "mc:barrel_side", "up": "mc:barrel_top", "down": "mc:barrel_bottom"}
    b.box((33, 2, 7), (41, 11, 15), bs, tile=False, uvo=(4, 0))
    b.box((34, 11.05, 8), (40, 11.05, 14), {"up": "water"}, tile=False)
    # --- établi, râtelier d'outils, lingots, charbon
    b.box((5, 8, 23), (10, 9.2, 37), SP)
    for z in (23.4, 35.4): b.box((5.4, 2, z), (6.6, 8, z + 1.2), DO); b.box((8.4, 2, z), (9.6, 8, z + 1.2), DO)
    b.box((5.6, 9.2, 25), (9, 11.6, 28), "steel", tile=False); b.box((6.4, 11.6, 25.8), (8.2, 12.4, 27.2), "steel", tile=False)      # heaume
    b.box((6, 9.2, 30.5), (9.4, 10, 35.5), "mc:iron_block", tile=False, uvo=(2, 2))
    b.box((7, 15, 43.2), (23, 16.2, 44), DO)
    b.box((8.6, 9.5, 43.3), (9.4, 15, 43.9), SP, tile=False); b.box((7.6, 8.4, 43.1), (10.4, 10.4, 44), "iron_dark", tile=False)     # marteau
    b.box((12, 7.5, 43.4), (12.8, 15, 43.8), "steel", tile=False); b.box((10.8, 13.4, 43.3), (14, 14.2, 44), "mc:gold_block", tile=False, uvo=(4, 6))  # épée
    b.box((17, 9, 43.3), (17.7, 15, 43.9), "iron_dark", tile=False); b.box((18.4, 9, 43.3), (19.1, 15, 43.9), "iron_dark", tile=False)  # pinces
    b.box((21, 10, 43.3), (21.8, 15, 43.9), SP, tile=False); b.box((20.4, 8.6, 43.2), (22.4, 10, 44), "steel", tile=False)
    b.box((13, 2, 24), (19, 3.5, 29), "mc:iron_block", tile=False, uvo=(1, 1)); b.box((14, 3.5, 24.6), (18, 5, 28.4), "mc:iron_block", tile=False, uvo=(5, 5))
    b.box((14.6, 5, 25.4), (17.4, 6.3, 27.6), "mc:gold_block", tile=False, uvo=(3, 3))
    b.box((36, 2, 22), (42, 3.6, 27), "mc:copper_block", tile=False, uvo=(2, 2)); b.box((37, 3.6, 22.8), (41, 5, 26.2), "mc:copper_block", tile=False, uvo=(6, 5))
    b.box((16.5, 2, 30.5), (23, 5.4, 36), "mc:coal_block", tile=False); b.box((14, 2, 31.6), (16.5, 3.8, 35), "mc:coal_block", tile=False, uvo=(5, 4))
    b.box((18, 5.4, 31.6), (21.6, 6.8, 34.6), "mc:coal_block", tile=False, uvo=(8, 2))
    # --- écu sur le poteau, lanterne
    b.box((1.6, 13.4, 3.2), (5.4, 19.4, 4), "banner_red", tile=False, uvo=(6, 4)); b.box((2.5, 12, 3.2), (4.5, 13.4, 4), "banner_red", tile=False, uvo=(7, 12))
    b.box((1.2, 19.4, 3), (5.8, 20.2, 4.1), "mc:gold_block", tile=False, uvo=(2, 2))
    b.box((43.7, 21.8, 4.2), (45.3, 24.2, 4.9), "iron_dark", tile=False); b.box((44.1, 21.6, 2.2), (44.9, 22.4, 4.4), "iron_dark", tile=False)
    lantern(b, glow, 44.5, 21.6, 2.8, hang=0.6)

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

    # --- meule à aiguiser
    gr = Model(); gc = (8.0, 9.6, 7.9)
    disc(gr, gc, 4.6, 6.9, 8.9, "mc:polished_andesite", axis="z")
    gr.box((7.2, 8.8, 4.6), (8.8, 10.4, 11.2), "iron_dark", tile=False)
    gr.box((7.4, 9, 3.6), (8.6, 12.6, 4.6), "iron_dark", tile=False)

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
          Emitter("spark", (8, 14, 7.4), 1, (0.05, 0.03, 0.05), 0.05, period=3)]
    return Building("forge", b, parts, em)


MACHINES = {"scierie": scierie, "moulin": moulin, "mine": mine, "forge": forge}
