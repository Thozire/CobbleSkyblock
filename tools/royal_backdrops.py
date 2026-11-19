"""Décors peints des niches de personnages (salle du trône, forêt, forge, champs, mine)."""
import math, random
from royal_kingdom import Pix
from royal_art import *
from royal_chars import mul

def _rocks(p, w, h, base, seed, dark=0.0):
    rnd = random.Random(seed)
    for y in range(h):
        for x in range(w):
            n = math.sin(x * 0.35 + y * 0.2 + seed) + math.sin(x * 0.12 - y * 0.31) + rnd.uniform(-0.4, 0.4)
            p.px(x, y, pick(base, 0.5 + n * 0.22 - dark, x, y))

def throne(w, h, gy):
    p = Pix(w, h)
    _rocks(p, w, h, [(34, 30, 46), (52, 48, 66), (70, 66, 86), (90, 86, 104)], 3)
    for y in range(0, gy, 7):                                     # appareil de pierre
        off = 6 if (y // 7) % 2 else 0
        p.hline(0, w - 1, y, (28, 24, 38))
        for x in range(off, w, 12): p.vline(x, y, y + 6, (28, 24, 38))
    cx = w // 2
    # grand vitrail
    win = lambda x, y: abs(x - cx) <= 15 and y >= 14 and (y >= 30 or (x - cx) ** 2 + (y - 30) ** 2 <= 15 ** 2)
    cols = [(220, 60, 70), (60, 120, 220), (250, 200, 80), (80, 180, 110), (180, 90, 200)]
    for y in range(10, 80):
        for x in range(cx - 18, cx + 19):
            if win(x, y):
                c = cols[((x - cx + 30) // 5 + (y // 6)) % len(cols)]
                if (x - cx) % 5 == 0 or y % 6 == 0: c = (40, 30, 40)
                p.px(x, y, mul(c, 0.8 + 0.4 * (1 - (y - 14) / 70)))
            elif win(x + 2, y) or win(x - 2, y) or win(x, y + 2) or win(x, y - 2):
                p.px(x, y, (150, 140, 156))
    ellipse(p, cx, 30, 6, 6, [(250, 200, 80), (255, 230, 140), (255, 250, 210)])
    glow(p, cx, 46, 52, (255, 220, 160), 50)
    # rayons de lumière
    for k in range(-2, 3):
        for y in range(80, gy + 20):
            x = int(cx + k * 6 + (y - 80) * k * 0.35)
            if 0 <= x < w: p.px(x, y, (255, 236, 190, 40)); p.px(x + 1, y, (255, 236, 190, 28))
    # piliers
    for px_ in (6, w - 12):
        for y in range(0, gy + 2):
            for x in range(px_, px_ + 7):
                p.px(x, y, pick([(70, 66, 86), (110, 106, 124), (150, 146, 160), (190, 186, 196)], 0.85 - abs(x - px_ - 2) / 7, x, y))
        p.rect(px_ - 1, gy - 2, px_ + 7, gy + 2, (110, 106, 124))
    # bannières suspendues aux piliers
    for bx in (13, w - 21):
        p.rect(bx - 1, 12, bx + 9, 13, GOLD[1])
        for y in range(14, 60):
            for x in range(bx, bx + 9):
                if y > 52 + abs(x - bx - 4): continue
                p.px(x, y, pick([(36, 50, 120), (54, 80, 170), (80, 116, 210)], 0.8 - abs(x - bx - 3) / 9, x, y))
        p.vline(bx, 14, 52, GOLD[2]); p.vline(bx + 8, 14, 52, GOLD[1])
        for (dx, dy) in ((4, 26), (3, 27), (5, 27), (4, 28), (4, 29)): p.px(bx + dx, dy, GOLD[3])
        for (dx, dy) in ((2, 33), (6, 33), (4, 31), (4, 35)): p.px(bx + dx, dy, GOLD[2])
    # torchères murales
    for tx in (24, w - 26):
        glow(p, tx, 70, 16, (255, 180, 90), 60)
        p.rect(tx - 1, 72, tx + 1, 80, (90, 70, 50)); p.rect(tx - 2, 71, tx + 2, 72, GOLD[1])
        p.rect(tx - 1, 66, tx + 1, 70, (255, 150, 40)); p.vline(tx, 64, 69, (255, 230, 140))
    # trône (dossier très haut, dépasse autour du roi)
    tx0, tx1 = cx - 30, cx + 30
    for y in range(42, gy + 4):
        for x in range(tx0, tx1 + 1):
            top = 42 + int(14 * (abs(x - cx) / 30) ** 2)
            if y < top: continue
            edge = x - tx0 < 4 or tx1 - x < 4 or y - top < 4
            p.px(x, y, pick(GOLD[1:5], 0.8 - (y - 60) / 120, x, y) if edge else pick(RED[1:5], 0.75 - abs(x - cx) / 50, x, y))
    for (x, y) in ((cx, 44), (tx0 + 2, 56), (tx1 - 2, 56)):
        ellipse(p, x, y, 3, 3, [GOLD[1], GOLD[3], GOLD[5], GOLD[6]])
    ellipse(p, cx, 44, 1.5, 1.5, [(160, 20, 40), (230, 60, 80)])
    for y in range(52, gy, 6):                                     # capitonnage du dossier
        for x in range(cx - 22, cx + 23, 8): p.px(x + (3 if (y // 6) % 2 else 0), y, GOLD[2])
    # sol et tapis
    for y in range(gy, h):
        t = (y - gy) / max(1, h - gy)
        for x in range(w):
            sq = ((x + int((x - cx) * t * 0.6)) // 9 + (y - gy) // 5) % 2
            p.px(x, y, pick([(40, 34, 50), (70, 64, 86), (120, 114, 132), (170, 164, 178)], 0.62 - t * 0.3 + (0.22 if sq else 0), x, y))
        half = 16 + int(t * 26)
        for x in range(cx - half, cx + half + 1):
            edge = abs(x - cx) >= half - 1
            p.px(x, y, GOLD[3] if edge else pick(RED[1:5], 0.7 - t * 0.3, x, y))
    return p.img

def forest(w, h, gy):
    p = Pix(w, h)
    vgrad(p, 0, 0, w - 1, gy, [(66, 100, 170), (120, 160, 210), (230, 190, 140), (250, 210, 150)])
    glow(p, w // 2 + 12, gy - 18, 40, (255, 220, 160), 70)
    rnd = random.Random(5)
    for layer_i, (col, base, size) in enumerate((((110, 140, 150), gy - 8, 9), ((60, 96, 80), gy - 2, 13), ((32, 62, 46), gy + 4, 18))):
        x = -rnd.randint(0, 10)
        while x < w + 10:
            hgt = size * 3 + rnd.randint(-4, 6)
            for i in range(hgt):
                hw = int(i * size / hgt) + (1 if i % 4 == 3 else 0)
                y = base - hgt + i
                for xx in range(x - hw, x + hw + 1):
                    if 0 <= xx < w and 0 <= y < h: p.px(xx, y, mul(col, 1.08 if xx < x else 0.92))
            p.vline(x, base, base + 3, mul((80, 54, 36), 0.6 + layer_i * 0.2))
            x += size + rnd.randint(2, 8)
    for y in range(gy, h):
        t = (y - gy) / max(1, h - gy)
        for x in range(w): p.px(x, y, pick([(40, 82, 40), (62, 116, 52), (96, 150, 64)], 0.75 - t * 0.5 + 0.12 * math.sin(x * 0.7 + y), x, y))
    # brume au pied des arbres et rayons de soleil
    for y in range(gy - 14, gy + 3):
        for x in range(w): p.px(x, y, (240, 220, 200, 40 + (y - gy + 14) * 3))
    for k in range(4):
        x0 = 20 + k * 20
        for y in range(0, gy):
            x = int(x0 + y * 0.4)
            if x < w: p.px(x, y, (255, 240, 200, 26)); p.px(x + 1, y, (255, 240, 200, 18))
    # souche et rondins
    sx, sy = 16, gy + 8
    for y in range(sy - 7, sy + 1):
        for x in range(sx - 7, sx + 8): p.px(x, y, pick([(70, 46, 30), (110, 74, 44), (140, 96, 58)], 0.8 - abs(x - sx) / 10, x, y))
    ellipse(p, sx, sy - 7, 7, 2.2, [(160, 116, 70), (200, 156, 100), (230, 196, 140)])
    for i, (x, y) in enumerate(((w - 26, gy + 10), (w - 16, gy + 10), (w - 21, gy + 4))):
        ellipse(p, x, y, 5, 5, [(90, 60, 36), (150, 104, 60), (200, 150, 96), (230, 190, 130)])
        ellipse(p, x, y, 2, 2, [(150, 104, 60), (190, 140, 86)])
    p.vline(sx + 3, sy - 15, sy - 7, (120, 80, 46)); p.rect(sx + 1, sy - 15, sx + 3, sy - 12, (190, 196, 210))   # hache plantée
    for _ in range(30):                                            # copeaux
        x, y = rnd.randint(4, w - 4), rnd.randint(gy + 6, h - 2)
        p.px(x, y, (220, 180, 110)); p.px(x + 1, y, (190, 150, 90))
    for (x, y) in ((8, gy + 22), (w - 12, gy + 26), (30, gy + 30)):   # champignons
        p.rect(x - 2, y - 2, x + 2, y - 1, (200, 50, 50)); p.px(x - 1, y - 2, (250, 240, 240)); p.px(x + 1, y - 1, (250, 240, 240)); p.vline(x, y, y + 2, (230, 220, 200))
    for _ in range(26):                                            # fleurs et herbes hautes
        x, y = rnd.randint(2, w - 3), rnd.randint(gy + 4, h - 2)
        if rnd.random() < 0.4: p.px(x, y, rnd.choice(((250, 230, 90), (240, 240, 250), (190, 120, 220))))
        else: p.vline(x, y - 2, y, (110, 170, 70))
    return p.img

def forge_room(w, h, gy):
    p = Pix(w, h)
    rnd = random.Random(7)
    p.rect(0, 0, w - 1, h - 1, (34, 18, 20))
    for y in range(0, gy, 5):
        off = 4 if (y // 5) % 2 else 0
        for x in range(-off, w, 9):
            c = (86 + rnd.randint(-10, 10), 42, 36)
            p.rect(x + 1, y + 1, x + 8, y + 4, c); p.hline(x + 1, x + 8, y + 1, mul(c, 1.25))
    cx = w // 2
    # foyer derrière le personnage
    fx0, fx1, fy0 = cx - 26, cx + 26, 50
    p.rect(fx0 - 4, fy0 - 26, fx1 + 4, gy, (70, 66, 80))
    for y in range(fy0 - 26, fy0 - 4):                             # hotte
        hw = 18 + (y - fy0 + 26)
        p.hline(cx - hw, cx + hw, y, (60, 56, 70) if y % 4 else (44, 40, 52))
    for y in range(fy0, gy):
        for x in range(fx0, fx1 + 1):
            top = fy0 + int(12 * (1 - math.sqrt(max(0, 1 - ((x - cx) / 26) ** 2))))
            if y >= top: p.px(x, y, (30, 10, 10))
    for x in range(fx0 + 3, fx1 - 2):
        hh = 14 + int(10 * abs(math.sin(x * 0.45))) + rnd.randint(0, 6)
        for y in range(gy - hh, gy):
            p.px(x, y, pick([(150, 40, 20), (230, 100, 30), (255, 170, 50), (255, 230, 140)], (y - (gy - hh)) / hh, x, y))
    glow(p, cx, gy - 8, 70, (255, 160, 70), 110)
    # outils accrochés
    for i, x in enumerate((8, 15, w - 16, w - 9)):
        p.vline(x, 20, 46, (110, 74, 44)); p.rect(x - 2, 44 + (i % 2) * 2, x + 2, 50, (130, 136, 150))
    # chaînes pendantes
    for x in (cx - 30, cx + 30):
        for y in range(0, 24): p.px(x, y, (110, 110, 124) if y % 2 else (70, 70, 82))
        p.rect(x - 2, 24, x + 2, 26, (90, 90, 104))
    # sol
    for y in range(gy, h):
        t = (y - gy) / max(1, h - gy)
        for x in range(w): p.px(x, y, pick([(40, 34, 40), (70, 60, 64), (100, 84, 80)], 0.6 - t * 0.4 + 0.1 * ((x // 9 + y // 5) % 2), x, y))
    # tonneau d'eau à gauche
    for y in range(gy - 10, gy + 8):
        for x in range(2, 16): p.px(x, y, pick([(70, 44, 26), (120, 80, 46), (160, 110, 64)], 0.85 - abs(x - 7) / 9, x, y))
    for yy in (gy - 6, gy + 4): p.hline(2, 15, yy, (80, 80, 92))
    p.hline(3, 14, gy - 10, (60, 110, 180)); p.hline(4, 12, gy - 11, (110, 160, 220))
    # râtelier d'épées à droite
    p.rect(w - 18, gy - 4, w - 3, gy - 2, (110, 74, 44)); p.rect(w - 18, gy + 6, w - 3, gy + 8, (110, 74, 44))
    for k, x in enumerate(range(w - 16, w - 4, 4)):
        p.vline(x, gy - 22 - k, gy + 6, (200, 206, 220)); p.vline(x + 1, gy - 22 - k, gy + 6, (140, 146, 160))
        p.rect(x - 1, gy - 6, x + 2, gy - 5, GOLD[2]); p.vline(x, gy - 9, gy - 6, (90, 60, 40))
    # braises au sol
    for _ in range(18):
        x, y = rnd.randint(cx - 30, cx + 30), rnd.randint(gy + 1, gy + 10)
        p.px(x, y, (255, 120, 40) if rnd.random() < .5 else (200, 60, 30))
    for _ in range(40):
        x, y = rnd.randint(4, w - 4), rnd.randint(30, gy)
        p.px(x, y, (255, 220, 120) if rnd.random() < .6 else (255, 150, 60))
    return p.img

def field(w, h, gy):
    p = Pix(w, h)
    vgrad(p, 0, 0, w - 1, gy, [(80, 70, 140), (200, 110, 120), (250, 170, 100), (255, 214, 140)])
    ellipse(p, w // 2 - 20, gy - 16, 9, 9, [(255, 200, 120), (255, 230, 170), (255, 250, 220)])
    glow(p, w // 2 - 20, gy - 16, 40, (255, 210, 150), 70)
    for x in range(w):                                             # collines
        top = int(gy - 10 + 4 * math.sin(x / 13) + 2 * math.sin(x / 5))
        p.vline(x, top, gy, (110, 120, 80))
    mx, my = w - 26, gy - 12                                       # moulin lointain
    p.rect(mx - 3, my - 12, mx + 3, my, (70, 56, 60)); 
    for i in range(4): p.hline(mx - 3 + i, mx + 3 - i, my - 13 - i, (60, 46, 52))
    for t in range(-10, 11):
        p.px(mx + t, my - 15 + t, (60, 46, 52)); p.px(mx + t, my - 15 - t, (60, 46, 52))
    fx = 18                                                         # ferme au loin
    p.rect(fx - 6, gy - 13, fx + 6, gy - 5, (150, 120, 100)); p.rect(fx - 1, gy - 9, fx + 1, gy - 5, (70, 50, 40))
    for i in range(7): p.hline(fx - 7 + i, fx + 7 - i, gy - 14 - i, (150, 60, 50) if i % 2 else (120, 44, 40))
    p.px(fx - 4, gy - 10, (255, 210, 120)); p.px(fx + 4, gy - 10, (255, 210, 120))
    for (x, y) in ((30, 20), (36, 16), (44, 22)):
        p.px(x, y, (60, 40, 50)); p.px(x - 1, y - 1, (60, 40, 50)); p.px(x + 1, y - 1, (60, 40, 50))
    rnd = random.Random(9)
    for y in range(gy, h):
        t = (y - gy) / max(1, h - gy)
        for x in range(w):
            base = [(150, 110, 40), (210, 160, 60), (240, 200, 90), (255, 230, 140)]
            p.px(x, y, pick(base, 0.85 - t * 0.5 + 0.15 * math.sin(x * 1.3 + y * 0.4), x, y))
        if y % 3 == 0:
            for x in range(0, w, 3): p.px(x + (y // 3) % 3, y, (170, 120, 40))
    for (bx, by, r) in ((14, gy + 14, 7), (w - 16, gy + 18, 8)):   # meules de foin
        for y in range(by - r, by + 2):
            for x in range(bx - r, bx + r + 1):
                if (x - bx) ** 2 / (r * r) + ((y - by) ** 2) / (r * r * 0.8) <= 1:
                    p.px(x, y, pick([(150, 100, 30), (210, 160, 60), (240, 200, 100)], 0.85 - (x - bx + r) / (3 * r) - (y - by + r) / (4 * r) * 0.3, x, y))
        for k in range(-r + 2, r - 1, 3): p.vline(bx + k, by - r + 2 + abs(k) // 2, by, (180, 130, 40))
    for x in range(0, w, 2):                                       # épis au premier plan
        hgt = rnd.randint(6, 14)
        p.vline(x, h - hgt, h - 1, (200, 150, 50)); p.px(x, h - hgt - 1, (250, 220, 120))
    for x in (6, 30, w - 30, w - 8):                               # clôture
        p.rect(x, gy - 2, x + 1, gy + 8, (110, 74, 44))
    p.hline(0, w - 1, gy + 1, (130, 90, 54)); p.hline(0, w - 1, gy + 5, (110, 74, 44))
    return p.img

def cave(w, h, gy):
    p = Pix(w, h)
    _rocks(p, w, h, [(24, 22, 30), (40, 38, 48), (60, 58, 70), (84, 80, 92)], 11)
    rnd = random.Random(11)
    for _ in range(14):                                            # veines de minerai qui brillent
        x, y = rnd.randint(4, w - 6), rnd.randint(8, gy - 4)
        c = rnd.choice(((250, 210, 90), (220, 160, 120), (120, 220, 230), (220, 220, 230)))
        for k in range(rnd.randint(3, 6)):
            xx, yy = x + rnd.randint(-2, 2), y + rnd.randint(-2, 2)
            p.px(xx, yy, c); p.px(xx + 1, yy, mul(c, 0.7))
        glow(p, x, y, 5, c, 30)
    cx = w // 2
    # galerie qui s'enfonce derrière le personnage
    for y in range(30, gy + 1):
        hw = 14 + int((y - 30) * 0.25)
        for x in range(cx - hw, cx + hw + 1):
            if (x - cx) ** 2 + (y - 46) ** 2 * 0.6 <= hw * hw or y >= 46:
                p.px(x, y, pick([(6, 4, 10), (16, 12, 20), (30, 26, 36)], (y - 30) / 90 + abs(x - cx) / 60, x, y))
    # boisage
    for x in (cx - 24, cx + 20):
        for y in range(30, gy + 4):
            for xx in range(x, x + 5): p.px(xx, y, pick([(70, 44, 26), (110, 72, 42), (140, 96, 56)], 0.8 - (xx - x) / 6, xx, y))
    for y in range(26, 32):
        for x in range(cx - 28, cx + 29): p.px(x, y, pick([(70, 44, 26), (110, 72, 42), (150, 104, 60)], 0.9 - (y - 26) / 7, x, y))
    for (x, y) in ((cx - 22, 40), (cx + 22, 40)):
        glow(p, x, y, 14, (255, 190, 90), 60); p.rect(x - 1, y - 2, x + 1, y + 1, (255, 210, 110))
    # cristaux qui sortent de la roche
    for (x, y, c) in ((10, 36, (120, 220, 240)), (w - 12, 52, (180, 120, 240)), (14, 82, (120, 220, 240))):
        glow(p, x, y, 10, c, 50)
        for k in range(3):
            for i in range(6 - k):
                p.px(x + k * 2 - 2, y - i, mul(c, 1.1 - i * 0.08)); p.px(x + k * 2 - 1, y - i, mul(c, 0.8))
    # sol, rails
    for y in range(gy, h):
        t = (y - gy) / max(1, h - gy)
        for x in range(w): p.px(x, y, pick([(30, 28, 34), (56, 50, 56), (84, 74, 74)], 0.7 - t * 0.4 + rnd.uniform(-0.1, 0.1), x, y))
        hw = 10 + int(t * 34)
        for k in (-1, 1): p.px(cx + k * hw, y, (150, 156, 170)); p.px(cx + k * hw + k, y, (90, 94, 108))
        if (y - gy) % 4 == 0: p.hline(cx - hw - 2, cx + hw + 2, y, (100, 66, 40))
    # wagonnet chargé à gauche
    wx, wy = 4, gy + 8
    p.rect(wx, wy - 8, wx + 18, wy, (80, 84, 96)); p.hline(wx, wx + 18, wy - 8, (130, 136, 150)); p.hline(wx, wx + 18, wy, (50, 52, 60))
    for x in range(wx + 1, wx + 18):
        hh = 2 + int(2 * abs(math.sin(x)))
        for y in range(wy - 8 - hh, wy - 8):
            p.px(x, y, rnd.choice(((80, 76, 84), (110, 104, 112), (250, 210, 90), (220, 150, 110))))
    for x in (wx + 3, wx + 14): ellipse(p, x, wy + 1, 2, 2, [(30, 30, 36), (70, 70, 80)])
    # caisses à droite
    for (x, y, s_) in ((w - 20, gy + 6, 12), (w - 14, gy - 4, 9)):
        p.rect(x, y, x + s_, y + s_, (110, 74, 44)); p.rect(x + 1, y + 1, x + s_ - 1, y + s_ - 1, (150, 104, 60))
        for k in range(s_ - 1): p.px(x + 1 + k, y + 1 + k, (110, 74, 44))
    return p.img

BACKDROPS = {"roi": throne, "bucheron": forest, "forgeron": forge_room, "fermier": field, "mineur": cave}
