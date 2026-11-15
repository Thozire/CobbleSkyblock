"""Vignettes peintes des boutons (v8)."""
import math, random
from PIL import Image
from royal_kingdom import Pix, layer, sprite
from royal_art import *

# ---------------------------------------------------------------- petits motifs
def cloud(p, x, y, w=12):
    lay = layer(w + 2, 8)
    for cx, cy, r in ((w * .3, 4, 3), (w * .55, 3, 3.6), (w * .8, 4.5, 2.6), (w * .15, 5.5, 2.2)):
        ellipse(lay, cx, cy, r * 1.2, r, [WHITE[1], WHITE[2], WHITE[3], WHITE[3]], light=(-0.2, -0.9))
    lay.hline(1, w, 7, (0, 0, 0, 0))
    p.paste(lay.img, x - lay.ox, y - lay.oy)

def round_tree(p, x, gy, r=3.5, cols=LEAF):
    p.vline(x, gy - 2, gy, WOOD[1])
    ellipse(p, x, gy - r - 1, r, r * 0.95, [cols[0], cols[1], cols[2], cols[3], cols[4]], light=(-0.5, -0.6))

def pine(p, x, gy, h=8, cols=LEAF):
    for i in range(h):
        hw = (i * 3) // 4 // 1 if i < h else 0
        hw = int(i * 0.45) + (1 if i % 3 == 2 else 0)
        for xx in range(x - hw, x + hw + 1):
            p.px(xx, gy - h + i, cols[2] if xx < x else cols[1])
        p.px(x - hw, gy - h + i, cols[3])
    p.vline(x, gy - 1, gy, WOOD[1])

def house(p, x, gy, w=9, roof=RED, lit=True):
    """Maison à colombages ; x = gauche, gy = sol."""
    hgt = 5
    p.rect(x, gy - hgt, x + w - 1, gy - 1, (236, 226, 204))
    p.vline(x, gy - hgt, gy - 1, WOOD[2]); p.vline(x + w - 1, gy - hgt, gy - 1, WOOD[1])
    p.hline(x, x + w - 1, gy - hgt, WOOD[2])
    p.px(x + 2, gy - hgt + 1, WOOD[2]); p.px(x + 3, gy - hgt + 2, WOOD[2])
    p.rect(x + w // 2, gy - 3, x + w // 2 + 1, gy - 1, WOOD[1])
    if lit: p.px(x + w - 3, gy - 3, GOLD[5]); p.px(x + 2, gy - 3, GOLD[4])
    rh = (w + 1) // 2 + 1
    for i in range(rh):
        x0, x1 = x - 1 + i, x + w - i
        for xx in range(x0, x1 + 1):
            p.px(xx, gy - hgt - 1 - i, roof[4] if xx < (x0 + x1) / 2 else roof[2])
        p.px(x0, gy - hgt - 1 - i, roof[1]); p.px(x1, gy - hgt - 1 - i, roof[1])
    p.hline(x - 1, x + w, gy - hgt - 1, roof[1])

def flag(p, x, y, col=RED, w=4):
    p.vline(x, y, y + 5, WOOD[1])
    for i in range(w):
        p.px(x + 1 + i, y + (1 if i in (1, 2) else 0), col[4]); p.px(x + 1 + i, y + 1 + (1 if i in (1, 2) else 0), col[2])

def birds(p, pts):
    for x, y in pts:
        p.px(x, y, K); p.px(x - 1, y - 1, K); p.px(x + 1, y - 1, K)

# ---------------------------------------------------------------- 1. Mon royaume (paysage)
def scene_kingdom(w, h):
    p = Pix(w, h)
    vgrad(p, 0, 0, w - 1, h - 1, [SKY[1], SKY[2], SKY[3], SKY[4], SKY[4]])
    glow(p, w - 12, 7, 9, (255, 240, 190), 70)
    ellipse(p, w - 12, 7, 3.2, 3.2, [GOLD[5], GOLD[6], (255, 255, 255)])
    cloud(p, 3, 2, 13); cloud(p, 40, 5, 10); cloud(p, 58, 1, 12)
    birds(p, ((30, 4), (34, 6)))
    # montagnes lointaines (versant gauche éclairé)
    peaks = [(8, 10), (24, 6), (40, 9), (55, 5), (72, 9), (88, 7)]
    for x in range(w):
        best = min(peaks, key=lambda pk: pk[1] + abs(x - pk[0]) * 0.8)
        top = int(best[1] + abs(x - best[0]) * 0.8)
        for y in range(top, h):
            lit = x < best[0]
            c = (172, 180, 222) if lit else (132, 140, 192)
            if y < best[1] + 3 and abs(x - best[0]) < 4:
                c = (248, 250, 255) if lit else (196, 206, 236)
            p.px(x, y, c)
    # collines
    for x in range(w):
        top = int(17 + 2.2 * math.sin(x / 7.0 + 0.6) + 1.2 * math.sin(x / 2.6))
        for y in range(top, h):
            p.px(x, y, pick([LEAF[3], LEAF[2], LEAF[2]], (y - top) / 8, x, y))
        p.px(x, top, LEAF[4])
    # champs en damier
    rnd = random.Random(4)
    for (fx, fy, fw, fh, c) in ((0, 23, 18, 4, GOLD[4]), (18, 25, 14, 3, LEAF[4]), (60, 23, 16, 4, GOLD[3]), (76, 25, 14, 4, LEAF[4]),
                                (4, 28, 20, 4, LEAF[3]), (66, 28, 24, 4, GOLD[4])):
        for y in range(fy, min(h, fy + fh)):
            for x in range(fx, min(w, fx + fw)):
                p.px(x, y, c if (y % 2 == 0) else tuple(int(v * 0.86) for v in c))
        p.hline(fx, min(w - 1, fx + fw - 1), fy, LEAF[1])
    # rivière + pont
    for y in range(18, h):
        cx = 46 + int(3 * math.sin(y / 2.5)) - (y - 18) // 3
        hw = 1 + (y - 18) // 4
        for x in range(cx - hw, cx + hw + 1): p.px(x, y, pick([(56, 104, 190), (90, 150, 220), (160, 210, 250)], 0.3 + 0.4 * ((x + y) % 3 == 0), x, y))
        p.px(cx - hw - 1, y, LEAF[1])
    p.rect(40, 25, 50, 25, DRESS[4]); p.rect(41, 26, 49, 26, DRESS[2]); p.px(45, 26, (40, 70, 140))
    # château du joueur sur la colline
    cx = 24
    p.rect(cx - 7, 12, cx + 7, 19, STONE[4]); p.vline(cx + 7, 12, 19, STONE[2])
    for i in range(cx - 7, cx + 8, 3): p.px(i, 11, STONE[5])
    for tx in (cx - 8, cx + 6):
        p.rect(tx, 9, tx + 2, 19, STONE[5]); p.px(tx + 2, 10, STONE[3])
        p.px(tx + 1, 7, RED[4]); p.hline(tx, tx + 2, 8, RED[3])
    p.rect(cx - 2, 6, cx + 2, 19, STONE[5]); p.vline(cx + 2, 6, 19, STONE[3])
    for i in range(4): p.hline(cx - 3 + i, cx + 3 - i, 5 - i, RED[4] if i < 2 else RED[3])
    flag(p, cx, -1, RED)
    p.rect(cx - 1, 16, cx + 1, 19, WOOD[1]); p.px(cx, 9, GOLD[5]); p.px(cx - 5, 15, GOLD[5]); p.px(cx + 5, 15, GOLD[5])
    # village
    house(p, 6, 22, 7, RED); house(p, 33, 22, 7, BLUE); house(p, 52, 21, 8, RED); house(p, 62, 23, 6, ROOF)
    # moulin
    mx = 80
    p.rect(mx - 2, 13, mx + 2, 21, (236, 226, 204)); p.vline(mx + 2, 13, 21, (190, 176, 150))
    for i in range(3): p.hline(mx - 2 + i, mx + 2 - i, 12 - i, WOOD[3])
    p.px(mx, 18, WOOD[1]); p.px(mx, 19, WOOD[1])
    for t in range(-6, 7):
        p.px(mx + t, 12 + t, WOOD[4] if t < 0 else WOOD[3]); p.px(mx + t, 12 - t, WOOD[4] if t > 0 else WOOD[3])
    p.px(mx, 12, GOLD[4])
    for x, gy, r in ((14, 22, 2.6), (2, 24, 3), (55, 27, 2.4), (88, 24, 3)): round_tree(p, x, gy, r)
    for x, gy in ((36, 18), (39, 19), (70, 19), (73, 20)): pine(p, x, gy, 6)
    return p.img

# ---------------------------------------------------------------- 2. Bâtiments (chantier)
def scene_build(w, h):
    p = Pix(w, h)
    vgrad(p, 0, 0, w - 1, h - 1, [SKY[2], SKY[3], SKY[4]])
    cloud(p, 12, 2, 9)
    gy = h - 4
    for x in range(w):
        p.vline(x, gy, h - 1, DIRT[2]); p.px(x, gy, LEAF[3]); p.px(x, gy + 1, LEAF[2])
    # fondations en pierre
    for i, x in enumerate(range(2, 17, 4)):
        p.rect(x, gy - 3, x + 3, gy - 1, STONE[5] if i % 2 else STONE[4]); p.hline(x, x + 3, gy - 3, STONE[6]); p.vline(x + 3, gy - 3, gy - 1, STONE[2])
    # ossature en bois (colombages)
    beam = WOOD[3]; dark = WOOD[1]
    for x in (2, 9, 16):
        p.vline(x, gy - 12, gy - 4, beam); p.vline(x + 1, gy - 12, gy - 4, dark)
    p.hline(2, 17, gy - 12, beam); p.hline(2, 17, gy - 11, dark); p.hline(2, 17, gy - 8, beam)
    for i in range(7): p.px(3 + i, gy - 11 + i, WOOD[4])
    # charpente du toit
    for i in range(9):
        p.px(1 + i, gy - 13 - i, WOOD[4]); p.px(2 + i, gy - 13 - i, dark)
        p.px(18 - i, gy - 13 - i, beam); p.px(17 - i, gy - 13 - i, dark)
    p.vline(9, gy - 21, gy - 13, WOOD[4])
    # quelques tuiles posées
    for i in range(4):
        p.hline(1 + i, 5 + i, gy - 13 - i, RED[4] if i % 2 else RED[3])
    # échelle
    for y in range(gy - 14, gy):
        p.px(19 + (gy - y) // 6, y, WOOD[4]); p.px(22 + (gy - y) // 6, y, WOOD[2])
        if y % 3 == 0: p.hline(19 + (gy - y) // 6, 22 + (gy - y) // 6, y, WOOD[3])
    # marteau au premier plan
    lay = layer(10, 10)
    for i in range(8): lay.px(1 + i, 8 - i, WOOD[4]); lay.px(2 + i, 8 - i, WOOD[2])
    lay.rect(6, 0, 9, 2, IRON[4]); lay.rect(7, 0, 10, 4, IRON[3]); lay.px(6, 0, IRON[5]); lay.hline(7, 10, 4, IRON[1])
    p.paste(outline(lay.img), 11 - lay.ox, gy - 8 - lay.oy)
    # planches empilées
    for i in range(3):
        p.hline(0 + i, 7 - i, gy - 1 - i, WOOD[5] if i % 2 else WOOD[4]); p.px(7 - i, gy - 1 - i, WOOD[2])
    return p.img

# ---------------------------------------------------------------- 3. Améliorer (forge)
def scene_forge(w, h):
    p = Pix(w, h)
    rnd = random.Random(11)
    p.rect(0, 0, w - 1, h - 1, (34, 18, 24))
    for y in range(0, h, 4):
        off = 3 if (y // 4) % 2 else 0
        for x in range(-off, w, 6):
            c = (70 + rnd.randint(-8, 6), 38, 40)
            p.rect(x + 1, y + 1, x + 5, y + 3, c); p.hline(x + 1, x + 5, y + 1, (96, 54, 50))
    glow(p, w // 2, h - 5, 18, (255, 150, 50), 70)
    # flammes du foyer en fond
    for x in range(1, w - 1):
        hh = 3 + int(2.5 * abs(math.sin(x * 1.7))) + rnd.randint(0, 2)
        for y in range(h - 6 - hh, h - 6):
            p.px(x, y, pick(FIRE, (y - (h - 6 - hh)) / hh, x, y))
    # enclume
    an = [".KKKKKKKKKKKKKKKKK....", "K66666666666666666KK..", "K5555555555555555555K.", ".K33333333333333333K..",
          "..KK333333333333KK....", "....K3333333333K......", "....K2222222222K......", "...K333333333333K.....", "..K22222222222222K....", "..KKKKKKKKKKKKKKKK...."]
    pal = {"K": K, "6": IRON[5], "5": IRON[4], "3": IRON[2], "2": IRON[1]}
    p.paste(sprite(an, pal), 1, h - 10)
    # épée incandescente
    for i in range(14):
        p.px(3 + i, h - 12, pick(FIRE, 0.95 - i * 0.03, 3 + i, h - 12)); p.px(3 + i, h - 11, FIRE[2])
    p.px(2, h - 12, FIRE[4]); p.rect(17, h - 14, 18, h - 9, GOLD[3]); p.px(17, h - 14, GOLD[5]); p.rect(19, h - 12, 21, h - 11, WOOD[3])
    glow(p, 9, h - 12, 7, (255, 200, 90), 60)
    # étincelles
    for _ in range(16):
        x, y = rnd.randint(2, w - 3), rnd.randint(3, h - 15)
        p.px(x, y, FIRE[4] if rnd.random() < .5 else FIRE[3])
        if rnd.random() < .3: p.px(x - 1, y + 1, FIRE[2])
    # flèche verte lumineuse
    arr = ["....KK....", "...KhhK...", "..KhggfK..", ".KhgggffK.", "KhggggfffK", "KKKKgfKKKK", "...Kgf K...".replace(" ", "f"), "...KgfK...", "...KKKK..."]
    pal = {"K": (20, 50, 30), "h": (200, 255, 170), "g": (110, 220, 90), "f": (60, 160, 60)}
    glow(p, w - 7, 5, 7, (140, 255, 120), 60)
    p.paste(sprite(arr, pal), w - 12, 1)
    return p.img

# ---------------------------------------------------------------- 4. Membres (la cour)
KING = [
    "...K...K...K....",
    "..K5K.K5K.K5K...",
    "..K45KK545KK54K.",
    "..K4444444444K..",
    "..K3r33b33r33K..",
    ".KHHHHHHHHHHHHK.",
    ".KHSSSSSSSSSSHK.",
    ".KHSeSSSSSSeSHK.",
    ".KHSSSSSsSSSSHK.",
    ".KHsSSSSSSSSsHK.",
    ".KHHHSSSSSSHHHK.",
    "..KHHHsxxsHHHK..",
    "..KHHHHHHHHHHK..",
    ".KWKKHHHHHHKKWK.",
    "KWkWWKKHHKKWWkWK",
    "KrrWWkWWWWkWWrrK",
    "KRrrWWWWWWWWrrrK",
    "KRrrrrWW5WWrrrdK",
]
LADY = [
    "....KKKKKK....",
    "...KggggggK...",
    "..KgGGGGGggK..",
    ".KgGHHHHHHggK.",
    ".KgHSSSSSSHgK.",
    ".KgSeSSSSeSgK.",
    ".KgSSSSSSSSgK.",
    ".KgSSSxxSSSgK.",
    ".KggSSSSSSggK.",
    "KgggKSSSSKgggK",
    "KggKGGGGGGKggK",
    "KgKGGG5GGGGKgK",
    "KgGGGGGGGGGGfK",
    "KGGGGGGGGGGGfK",
]
KNIGHT = [
    "......KK......",
    ".....KRrK.....",
    "....KRrrK.....",
    "..KKKKKKKKK...",
    ".K55555554iK..",
    ".K5444444ijK..",
    ".K4KKKKKKKjK..",
    ".K4KeKKKeKjK..",
    ".K444444ijjK..",
    ".K4444K4ijjK..",
    "..Kj44K4ijK...",
    "KbbKKKKKKKbbK.",
    "KBbbbb5bbbbnK.",
    "KBbbb555bbbnK.",
]
def scene_court(w, h):
    p = Pix(w, h)
    vgrad(p, 0, 0, w - 1, h - 1, [RED[2], RED[1], RED[1]])
    for y in range(2, h, 6):
        for x in range(((y // 6) % 2) * 3, w, 6):
            p.px(x, y, GOLD[3]); p.px(x - 1, y + 1, GOLD[2]); p.px(x + 1, y + 1, GOLD[2]); p.px(x, y + 2, GOLD[3])
    for x in range(w):
        p.px(x, 0, GOLD[4]); p.px(x, 1, GOLD[2] if x % 3 else GOLD[4])
    glow(p, w // 2, 9, 12, (255, 220, 140), 50)
    pal = {"K": K, "5": GOLD[5], "4": GOLD[4], "3": GOLD[3], "r": RED[3], "R": RED[5], "d": RED[1], "b": BLUE[3], "B": BLUE[4],
           "n": BLUE[1], "H": HAIR[2], "S": SKIN[3], "s": SKIN[2], "x": RED[3], "e": (40, 24, 30), "W": WHITE[3], "k": K,
           "g": LEAF[2], "G": LEAF[3], "f": LEAF[1], "i": IRON[3], "j": IRON[2]}
    lady = sprite(LADY, pal); knight = sprite(KNIGHT, pal); king = sprite(KING, pal)
    p.paste(lady, -5, h - lady.height); p.paste(knight, w - knight.width + 5, h - knight.height)
    p.paste(king, (w - king.width) // 2, h - king.height)
    return p.img

# ---------------------------------------------------------------- 5. Capitale (crépuscule)
def scene_capital(w, h):
    p = Pix(w, h)
    vgrad(p, 0, 0, w - 1, h - 1, DUSK)
    glow(p, 4, h - 8, 10, (255, 220, 150), 80)
    ellipse(p, 4, h - 8, 4, 4, [GOLD[5], GOLD[6], (255, 255, 240)])
    birds(p, ((5, 5), (9, 3)))
    gy = h - 3
    for x in range(w):
        top = int(gy - 2.5 * math.exp(-((x - w / 2) / 8.0) ** 2))
        for y in range(top, h): p.px(x, y, pick([LEAF[0], LEAF[1], LEAF[2]], 1 - (y - top) / 4, x, y))
    base = gy - 2
    sil = STONE[2]; sil2 = STONE[1]
    # remparts
    p.rect(2, base - 6, w - 3, base, STONE[3]); p.vline(w - 3, base - 6, base, STONE[1])
    for x in range(2, w - 2, 2): p.px(x, base - 7, STONE[4])
    # tours latérales + toits
    for tx, th in ((2, 12), (w - 6, 12)):
        p.rect(tx, base - th, tx + 3, base, STONE[4]); p.vline(tx + 3, base - th, base, STONE[2])
        for i in range(4): p.hline(tx - 1 + i // 2, tx + 4 - i // 2, base - th - 1 - i, ROOF[3] if i < 2 else ROOF[2])
        p.px(tx + 1, base - th - 5, GOLD[4])
        p.px(tx + 1, base - th + 3, GOLD[5])
    # donjon central
    cx = w // 2
    p.rect(cx - 4, base - 17, cx + 4, base, STONE[4]); p.vline(cx + 4, base - 17, base, STONE[2]); p.vline(cx - 4, base - 17, base, STONE[5])
    for i in range(8):
        hw = 5 - (i * 5) // 8
        for xx in range(cx - hw, cx + hw + 1): p.px(xx, base - 18 - i, ROOF[4] if xx < cx else ROOF[2])
    flag(p, cx, base - 30, RED, 5)
    for yy in (base - 13, base - 8):
        p.px(cx - 2, yy, GOLD[5]); p.px(cx + 2, yy, GOLD[5])
    p.rect(cx - 1, base - 3, cx + 1, base, WOOD[1]); p.px(cx, base - 4, WOOD[1])
    for x in (6, w - 9): p.px(x, base - 3, GOLD[5])
    # chemin
    for y in range(base + 1, h):
        p.hline(cx - 1 - (y - base) // 2, cx + 1 + (y - base) // 2, y, DIRT[3])
    return p.img

# ---------------------------------------------------------------- 6. Récupérer le stock (entrepôt)
def scene_stock(w, h):
    p = Pix(w, h)
    for x in range(w):                                    # mur de planches, lumière chaude au centre
        for y in range(h):
            v = 0.75 - abs(x - w * 0.5) / w * 0.9 + (0.08 if (x // 7) % 2 else 0)
            p.px(x, y, pick([WOOD[1], WOOD[2], WOOD[3], WOOD[4]], v, x, y))
        if x % 7 == 0: p.vline(x, 0, h - 1, WOOD[1])
    glow(p, w // 2, 6, 14, (255, 210, 120), 60)
    gy = h - 4
    p.rect(0, gy, w - 1, h - 1, WOOD[2]); p.hline(0, w - 1, gy, WOOD[5]); p.hline(0, w - 1, h - 1, WOOD[0])
    # pile de rondins
    for row, n in enumerate((4, 3, 2)):
        for i in range(n):
            cx, cy = 6 + row * 3.5 + i * 7, gy - 4 - row * 6
            ellipse(p, cx, cy, 3.4, 3.4, [WOOD[1], WOOD[3], WOOD[5], WOOD[6]]); ellipse(p, cx, cy, 1.4, 1.4, [WOOD[3], WOOD[4]])
    # sacs de grain
    for sx, sh in ((36, 11), (44, 9)):
        ellipse(p, sx, gy - sh / 2, 4.2, sh / 2 + 1, [PARCH[0], PARCH[1], PARCH[3], PARCH[5]])
        p.hline(int(sx - 2), int(sx + 2), int(gy - sh), PARCH[1])
    # grand coffre ouvert, débordant d'or
    cx = 58
    p.rect(cx, gy - 9, cx + 20, gy - 1, WOOD[3]); p.hline(cx, cx + 20, gy - 9, WOOD[5]); p.hline(cx, cx + 20, gy - 1, WOOD[1])
    for x in (cx, cx + 20): p.vline(x, gy - 9, gy - 1, IRON[2])
    for x in (cx + 6, cx + 14): p.vline(x, gy - 9, gy - 1, IRON[3])
    p.rect(cx + 1, gy - 17, cx + 19, gy - 14, WOOD[2]); p.hline(cx + 1, cx + 19, gy - 17, WOOD[5])       # couvercle relevé
    for x in range(cx + 2, cx + 19):
        hh = 2 + int(2 * abs(math.sin(x * 0.9)))
        for y in range(gy - 9 - hh, gy - 9): p.px(x, y, pick([GOLD[2], GOLD[4], GOLD[5]], 1 - (y - (gy - 9 - hh)) / hh, x, y))
    for (x, y) in ((cx + 5, gy - 13), (cx + 12, gy - 14), (cx + 16, gy - 12)): p.px(x, y, (255, 255, 240))
    p.rect(cx + 9, gy - 7, cx + 11, gy - 4, GOLD[4]); p.px(cx + 9, gy - 7, GOLD[6])
    # lingots et tonneau
    for i, (x, y) in enumerate(((82, gy - 2), (86, gy - 2), (84, gy - 4))):
        p.rect(x, y, x + 3, y + 1, IRON[4] if i != 2 else GOLD[4]); p.hline(x, x + 3, y, IRON[5] if i != 2 else GOLD[6])
    return p.img

# ---------------------------------------------------------------- 7. Ramasser (charrette)
def scene_cart(w, h):
    p = Pix(w, h)
    vgrad(p, 0, 0, w - 1, h - 1, [SKY[2], SKY[3], SKY[4]])
    cloud(p, 2, 2, 9)
    gy = h - 4
    for x in range(w):
        p.vline(x, gy, h - 1, LEAF[2]); p.px(x, gy, LEAF[4]); p.px(x, h - 1, DIRT[2])
    # plateau et ridelles
    p.rect(3, gy - 7, 20, gy - 5, WOOD[3]); p.hline(3, 20, gy - 7, WOOD[5]); p.hline(3, 20, gy - 5, WOOD[1])
    p.vline(3, gy - 11, gy - 7, WOOD[2]); p.vline(20, gy - 11, gy - 7, WOOD[2])
    for i in range(5): p.px(20 + i, gy - 6 - i // 2, WOOD[2])                 # timon
    # caisse du bâtiment démonté
    p.rect(6, gy - 15, 17, gy - 8, WOOD[4]); p.hline(6, 17, gy - 15, WOOD[6]); p.hline(6, 17, gy - 8, WOOD[2])
    p.vline(6, gy - 15, gy - 8, WOOD[2]); p.vline(17, gy - 15, gy - 8, WOOD[1])
    for k in range(6): p.px(8 + k, gy - 14 + k, WOOD[2])
    for i in range(4): p.hline(8 + i, 15 - i, gy - 16 - i, RED[4] if i < 2 else RED[3])   # petit toit
    # roues
    for cx in (7, 17):
        ellipse(p, cx, gy - 2, 3.3, 3.3, [WOOD[0], WOOD[1], WOOD[3], WOOD[5]]); p.px(cx, gy - 2, IRON[5])
    return p.img

SCENES = {"stock": scene_stock, "cart": scene_cart, "kingdom": scene_kingdom, "build": scene_build, "forge": scene_forge, "court": scene_court, "capital": scene_capital}
