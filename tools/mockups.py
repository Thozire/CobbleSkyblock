"""Maquettes de styles pour le menu /ile (aperçus seulement)."""
import math, random, sys
sys.path.insert(0, "/home/claude/cobbleskyblock/tools")
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import make_gui as G

S = 2
W, H = 256, 272
OX, OY = 40, 24
u = G.u
POP = G.POPPINS
ICON_DIR = "/home/claude/rp/pack/assets/cobbleislands/textures/item/ui/"
MAIN = {4: None, 20: 7101, 22: 7102, 24: 7103, 29: 7104, 31: 7106, 33: 7107, 39: 7108, 41: 7109, 45: 7111, 49: 7112}

def slot_xy(slot):
    r, c = divmod(slot, 9)
    return OX + 8 + 18 * c, OY + 18 + 18 * r

def put_icons(img):
    for slot, cmd in MAIN.items():
        x, y = slot_xy(slot)
        if cmd:
            img.alpha_composite(Image.open(f"{ICON_DIR}{cmd}.png"), (u(x), u(y)))
        else:  # tête du joueur
            d = ImageDraw.Draw(img)
            d.rectangle([u(x + 2), u(y + 2), u(x + 14), u(y + 14)], fill=(196, 150, 110, 255))
            d.rectangle([u(x + 2), u(y + 2), u(x + 14), u(y + 6)], fill=(70, 48, 30, 255))
            d.rectangle([u(x + 4), u(y + 8), u(x + 6), u(y + 10)], fill=(40, 60, 160, 255))
            d.rectangle([u(x + 10), u(y + 8), u(x + 12), u(y + 10)], fill=(40, 60, 160, 255))

def title(img, text, col=(255, 255, 255), x=OX + 14, y=OY + 5):
    f = ImageFont.truetype(POP, u(7))
    d = ImageDraw.Draw(img)
    d.text((u(x) + S, u(y) + S), text, font=f, fill=(0, 0, 0, 120))
    d.text((u(x), u(y)), text, font=f, fill=col + (255,))

def on_world(img, path):
    bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
    d = ImageDraw.Draw(bg)
    rnd = random.Random(2)
    for y in range(0, img.size[1], 16):
        for x in range(0, img.size[0], 16):
            g = rnd.randint(40, 70)
            d.rectangle([x, y, x + 15, y + 15], fill=(g - 15, g + 20, g - 20, 255))
    bg = bg.filter(ImageFilter.GaussianBlur(3))
    bg.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 90)))
    bg.alpha_composite(img)
    bg = bg.resize((bg.width * 3 // 2, bg.height * 3 // 2), Image.LANCZOS)
    bg.save(path)

# ================= Style A : « Arène » (jeu Pokémon récent) =================
def style_arena():
    img = Image.new("RGBA", (u(W), u(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = OX - 8, OY - 8, OX + 184, OY + 238
    # ombre
    sh = G.rmask(img.size, [u(x0 + 3), u(y0 + 4), u(x1 + 3), u(y1 + 4)], u(12))
    G.glow(img, sh, (0, 0, 0), u(4), 1.2)
    # coque blanche épaisse
    d.rounded_rectangle([u(x0), u(y0), u(x1), u(y1)], radius=u(12), fill=(250, 250, 252, 255))
    # intérieur sombre à rayures diagonales
    inner = [u(x0 + 5), u(OY + 14), u(x1 - 5), u(y1 - 5)]
    im = G.rmask(img.size, inner, u(8))
    stripes = Image.new("RGBA", img.size, (34, 36, 48, 255)); sd = ImageDraw.Draw(stripes)
    for k in range(-60, 140, 9):
        sd.polygon([(u(OX + k), u(y0)), (u(OX + k + 4), u(y0)), (u(OX + k - 120), u(y1)), (u(OX + k - 124), u(y1))], fill=(42, 44, 58, 255))
    G.paste_masked(img, stripes, im)
    # en-tête rouge en biais
    head = Image.new("RGBA", img.size, (0, 0, 0, 0)); hd = ImageDraw.Draw(head)
    hd.polygon([(u(x0), u(y0)), (u(x1), u(y0)), (u(x1), u(OY + 9)), (u(OX + 120), u(OY + 9)), (u(OX + 110), u(OY + 15)), (u(x0), u(OY + 15))], fill=(228, 40, 52, 255))
    hd.polygon([(u(OX + 124), u(y0)), (u(OX + 160), u(y0)), (u(OX + 150), u(OY + 9)), (u(OX + 114), u(OY + 9))], fill=(250, 210, 40, 255))
    hm = G.rmask(img.size, [u(x0), u(y0), u(x1), u(y1)], u(12))
    G.paste_masked(img, head, hm)
    d.line([u(x0 + 4), u(OY + 15), u(OX + 110), u(OY + 15)], fill=(255, 255, 255, 255), width=S)
    # cartes : boutons blancs arrondis avec base colorée
    cols = {4: (250, 210, 40), 20: (94, 210, 120), 22: (70, 160, 250), 24: (250, 170, 50), 29: (94, 210, 120), 31: (190, 90, 230),
            33: (70, 200, 230), 39: (150, 150, 170), 41: (228, 40, 52), 45: (150, 150, 170), 49: (228, 40, 52)}
    for slot, c in cols.items():
        x, y = slot_xy(slot)
        d.rounded_rectangle([u(x - 1), u(y - 1), u(x + 17), u(y + 17)], radius=u(4), fill=c + (255,))
        d.rounded_rectangle([u(x - 1), u(y - 1), u(x + 17), u(y + 15)], radius=u(4), fill=(252, 252, 255, 255))
        d.rounded_rectangle([u(x - 1), u(y - 1), u(x + 17), u(y + 17)], radius=u(4), outline=(20, 20, 30, 255), width=S)
    # barre « Inventaire » (#404040)
    d.rounded_rectangle([u(OX + 4), u(OY + 127), u(OX + 172), u(OY + 137)], radius=u(5), fill=(64, 64, 64, 255))
    d.polygon([(u(OX + 150), u(OY + 127)), (u(OX + 172), u(OY + 127)), (u(OX + 172), u(OY + 137)), (u(OX + 144), u(OY + 137))], fill=(228, 40, 52, 255))
    # terrain de combat (bas)
    sx0, sy0, sx1, sy1 = OX - 2, OY + 141, OX + 178, OY + 231
    scene = Image.new("RGBA", img.size, (0, 0, 0, 0)); scd = ImageDraw.Draw(scene)
    sky = G.grad(img.size, (120, 200, 255), (210, 240, 255)); scene.alpha_composite(sky)
    scd.rectangle([0, u(sy1 - 30), u(W), u(H)], fill=(120, 200, 110, 255))
    for k in range(0, 12):
        scd.line([(0, u(sy1 - 30 + k * 3)), (u(W), u(sy1 - 30 + k * 3))], fill=(110, 190, 100, 255), width=1)
    for cx, cy, rx in ((OX + 52, sy1 - 14, 34), (OX + 130, sy1 - 34, 26)):
        scd.ellipse([u(cx - rx), u(cy - rx * 0.28), u(cx + rx), u(cy + rx * 0.28)], fill=(196, 170, 110, 255))
        scd.ellipse([u(cx - rx + 3), u(cy - rx * 0.28 + 2), u(cx + rx - 3), u(cy + rx * 0.28 - 2)], fill=(150, 210, 110, 255))
    for cx, cy, r in ((OX + 20, sy0 + 16, 9), (OX + 34, sy0 + 13, 11), (OX + 150, sy0 + 22, 10)):
        scd.ellipse([u(cx - r * 1.7), u(cy - r * 0.6), u(cx + r * 1.7), u(cy + r * 0.6)], fill=(255, 255, 255, 230))
    f = ImageFont.truetype(POP, u(13))
    t = "CobbleSkyblock"
    tw = scd.textlength(t, font=f); tx = u(OX + 88) - tw / 2
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)):
        scd.text((tx + dx * S, u(sy0 + 6) + dy * S), t, font=f, fill=(20, 30, 90, 255))
    scd.text((tx, u(sy0 + 6)), t, font=f, fill=(255, 214, 40, 255))
    sm = G.rmask(img.size, [u(sx0), u(sy0), u(sx1), u(sy1)], u(7))
    G.paste_masked(img, scene, sm)
    d.rounded_rectangle([u(sx0), u(sy0), u(sx1), u(sy1)], radius=u(7), outline=(20, 20, 30, 255), width=S)
    title(img, "Mon île")
    put_icons(img)
    return img

# ================= Style B : « Nature Cobblemon » =================
def leaf(d, x, y, r, col):
    d.ellipse([u(x - r), u(y - r * 0.6), u(x + r), u(y + r * 0.6)], fill=col + (255,))

def berry(d, x, y, col):
    d.ellipse([u(x - 2.2), u(y - 2.2), u(x + 2.2), u(y + 2.2)], fill=col + (255,))
    d.ellipse([u(x - 1.2), u(y - 1.5), u(x - 0.2), u(y - 0.5)], fill=(255, 255, 255, 200))
    d.line([u(x), u(y - 2.2), u(x + 0.8), u(y - 4)], fill=(80, 120, 50, 255), width=S)

def tall_grass(d, x, base, h, rnd):
    for k in range(5):
        bx = x + k * 1.6 - 3.2
        tip = (bx + rnd.uniform(-2, 2), base - h * rnd.uniform(0.7, 1.0))
        d.polygon([(u(bx - 1), u(base)), (u(bx + 1), u(base)), (u(tip[0]), u(tip[1]))], fill=(70 + k * 6, 170 + k * 8, 80, 255))

def style_nature():
    img = Image.new("RGBA", (u(W), u(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rnd = random.Random(4)
    x0, y0, x1, y1 = OX - 9, OY - 4, OX + 185, OY + 236
    sh = G.rmask(img.size, [u(x0 + 2), u(y0 + 4), u(x1 + 2), u(y1 + 5)], u(10))
    G.glow(img, sh, (0, 0, 0), u(4), 1.1)
    # cadre bois
    d.rounded_rectangle([u(x0), u(y0), u(x1), u(y1)], radius=u(10), fill=(122, 80, 48, 255))
    for k in range(0, 60):
        yy = y0 + 2 + k * 4
        if yy > y1 - 2: break
        d.line([u(x0 + 2), u(yy), u(x0 + 6), u(yy + 1)], fill=(100, 64, 38, 255), width=S)
        d.line([u(x1 - 6), u(yy), u(x1 - 2), u(yy + 1)], fill=(100, 64, 38, 255), width=S)
    # papier crème
    paper = [u(x0 + 6), u(OY + 14), u(x1 - 6), u(y1 - 6)]
    pm = G.rmask(img.size, paper, u(6))
    G.paste_masked(img, G.grad(img.size, (252, 246, 228), (238, 226, 196)), pm)
    dots = Image.new("RGBA", img.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(dots)
    for yy in range(OY + 16, y1 - 6, 7):
        for xx in range(x0 + 9 + (yy // 7 % 2) * 3, x1 - 6, 7):
            dd.point((u(xx), u(yy)), fill=(220, 200, 160, 255))
    G.paste_masked(img, dots, pm)
    # en-tête vert feuillage + toit d'herbe
    hb = [u(x0 + 2), u(y0 - 2), u(x1 - 2), u(OY + 15)]
    G.paste_masked(img, G.grad(img.size, (88, 186, 96), (52, 140, 70)), G.rmask(img.size, hb, u(8)))
    for xx in range(x0 - 4, x1 + 6, 5):
        leaf(d, xx + rnd.uniform(-1, 1), y0 - 3 + rnd.uniform(-1.5, 1.5), 4.2, (72, 168, 82) if xx % 2 else (96, 196, 96))
    d.line([u(x0 + 6), u(OY + 15), u(x1 - 6), u(OY + 15)], fill=(40, 110, 56, 255), width=S)
    # arbres apricorn qui débordent
    for tx, ty, s in ((x0 + 2, y0 - 6, 1.0), (x1 - 2, y0 + 2, 0.85)):
        d.rectangle([u(tx - 1.5), u(ty - 2), u(tx + 1.5), u(ty + 16 * s)], fill=(112, 76, 50, 255))
        for k in range(14):
            a = k / 14 * math.tau
            leaf(d, tx + math.cos(a) * 9 * s, ty - 8 * s + math.sin(a) * 6 * s, 5 * s, (66, 156, 80) if k % 2 else (88, 184, 92))
        leaf(d, tx, ty - 9 * s, 7 * s, (100, 196, 100))
        for k, col in enumerate(((232, 64, 72), (60, 130, 240), (250, 200, 50), (240, 240, 240))):
            a = k / 4 * math.tau + 0.4
            berry(d, tx + math.cos(a) * 7 * s, ty - 6 * s + math.sin(a) * 5 * s, col)
    # lianes et baies sur les côtés
    for side in (x0 + 1, x1 - 1):
        for yy in range(OY + 22, OY + 120, 9):
            leaf(d, side + rnd.uniform(-1, 1), yy, 3, (78, 170, 86))
        for yy, col in ((OY + 40, (232, 64, 72)), (OY + 78, (240, 140, 200)), (OY + 104, (250, 200, 50))):
            berry(d, side, yy, col)
    # cartes : boutons « galets » verts
    cols = {4: (250, 200, 50), 20: (70, 170, 90), 22: (60, 140, 220), 24: (230, 150, 50), 29: (70, 170, 90), 31: (180, 90, 200),
            33: (60, 170, 200), 39: (150, 120, 90), 41: (220, 70, 70), 45: (150, 120, 90), 49: (220, 70, 70)}
    for slot, c in cols.items():
        x, y = slot_xy(slot)
        d.rounded_rectangle([u(x - 1.5), u(y - 0.5), u(x + 17.5), u(y + 18)], radius=u(5), fill=tuple(int(v * 0.65) for v in c) + (255,))
        d.rounded_rectangle([u(x - 1.5), u(y - 1.5), u(x + 17.5), u(y + 16.5)], radius=u(5), fill=c + (255,))
        d.rounded_rectangle([u(x), u(y), u(x + 16), u(y + 15)], radius=u(4), fill=(255, 250, 236, 255))
    # barre « Inventaire » (#404040) façon panneau en bois sombre
    d.rounded_rectangle([u(OX + 3), u(OY + 126), u(OX + 173), u(OY + 138)], radius=u(5), fill=(64, 64, 64, 255))
    # prairie avec hautes herbes
    sx0, sy0, sx1, sy1 = OX - 3, OY + 141, OX + 179, OY + 231
    scene = Image.new("RGBA", img.size, (0, 0, 0, 0)); scd = ImageDraw.Draw(scene)
    scene.alpha_composite(G.grad(img.size, (150, 215, 255), (255, 236, 200)))
    for cx, cy, r in ((OX + 30, sy0 + 26, 8), (OX + 140, sy0 + 18, 9)):
        scd.ellipse([u(cx - r * 1.8), u(cy - r * 0.6), u(cx + r * 1.8), u(cy + r * 0.6)], fill=(255, 255, 255, 235))
    scd.ellipse([u(OX - 30), u(sy1 - 40), u(OX + 110), u(sy1 + 30)], fill=(110, 196, 100, 255))
    scd.ellipse([u(OX + 60), u(sy1 - 32), u(OX + 210), u(sy1 + 40)], fill=(88, 176, 88, 255))
    for k in range(26):
        tall_grass(scd, OX + rnd.uniform(-2, 178), sy1 - rnd.uniform(0, 14), rnd.uniform(7, 13), rnd)
    for bx, by, col in ((OX + 150, sy1 - 22, (232, 64, 72)), (OX + 160, sy1 - 18, (250, 200, 50)), (OX + 22, sy1 - 20, (60, 130, 240))):
        leaf(scd, bx, by + 3, 7, (60, 140, 70))
        berry(scd, bx - 2, by, col); berry(scd, bx + 3, by + 1, col)
    f = ImageFont.truetype(POP, u(13))
    t = "CobbleSkyblock"
    tw = scd.textlength(t, font=f); tx = u(OX + 88) - tw / 2
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 3), (0, 3)):
        scd.text((tx + dx * S, u(sy0 + 5) + dy * S), t, font=f, fill=(40, 90, 50, 255))
    scd.text((tx, u(sy0 + 5)), t, font=f, fill=(255, 250, 236, 255))
    sm = G.rmask(img.size, [u(sx0), u(sy0), u(sx1), u(sy1)], u(7))
    G.paste_masked(img, scene, sm)
    d.rounded_rectangle([u(sx0), u(sy0), u(sx1), u(sy1)], radius=u(7), outline=(90, 60, 36, 255), width=S)
    title(img, "Mon île", (255, 255, 240))
    put_icons(img)
    return img

if __name__ == "__main__":
    on_world(style_arena(), "/home/claude/rp/maquette_A_arene.png")
    on_world(style_nature(), "/home/claude/rp/maquette_B_nature.png")
    print("ok")
