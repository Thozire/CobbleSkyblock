"""Renders HD des personnages des niches (vrais skins + objets extrudés)."""
import os, sys
from PIL import Image
import skin_render as R

HERE = os.path.dirname(os.path.abspath(__file__))

def sprite(rows, pal):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in pal: im.putpixel((i, j), pal[ch] + (255,))
    return im

# objets originaux, manche vertical (grip ~ colonne 7)
AXE = sprite([
    "................",
    ".....bbb........",
    "....bSSsb.......",
    "...bSSSssb......",
    "...bSWSsHb......",
    "...bSSSsHHw.....",
    "....bSSsHHw.....",
    ".....bbbHHw.....",
    ".......dHw......",
    ".......dHw......",
    ".......dHw......",
    ".......dHw......",
    ".......dHw......",
    ".......dHw......",
    ".......dGw......",
    "........d.......",
], {"b": (40, 42, 50), "S": (196, 204, 216), "s": (130, 138, 152), "W": (240, 246, 252),
    "H": (128, 84, 48), "w": (160, 110, 64), "d": (84, 54, 32), "G": (60, 40, 26)})

SCEPTER = sprite([
    "......g.g.......",
    ".....gYgYg......",
    "....gYRRRYg.....",
    "....YRrWRRY.....",
    "....gYRRRYg.....",
    ".....gYYYg......",
    "......gYg.......",
    "......dYg.......",
    "......dYg.......",
    ".....gYYYg......",
    "......dYg.......",
    "......dYg.......",
    "......dYg.......",
    "......dYg.......",
    ".....gYYYg......",
    "......gYg.......",
], {"g": (150, 100, 30), "Y": (240, 196, 70), "d": (190, 140, 40), "R": (200, 30, 60), "r": (150, 10, 40), "W": (255, 190, 200)})

def king():
    sk = Image.open(os.path.join(HERE, "renders", "skin_roi.png"))
    pose = {"head": (-4, 0, 12), "body": (0, 0, 4), "rarm": (34, -6, 0), "larm": (-4, 10, 0),
            "rleg": (4, -3, 0), "lleg": (-6, 3, 0)}
    f, h = R.player(sk, pose)
    f += R.held(SCEPTER, h, "r", grip=(7, 11), angle=-34, px=0.95, glow=((200, 30, 60), (255, 190, 200), (150, 10, 40)))
    return f

def lumberjack():
    sk = Image.open(os.path.join(HERE, "renders", "skin_bucheron.png"))
    pose = {"head": (-6, 0, -10), "body": (0, 0, -6), "rarm": (70, -10, 0), "larm": (-8, 12, 0),
            "rleg": (8, -3, 0), "lleg": (-10, 4, 0)}
    f, h = R.player(sk, pose)
    f += R.held(AXE, h, "r", grip=(8, 13), angle=-40, roll=28, px=1.05)
    return f

CHARS = {"roi": king, "bucheron": lumberjack}

def make(who, height=240):
    return R.render(CHARS[who](), height_px=height)

if __name__ == "__main__":
    ims = [make(n, 300) for n in (sys.argv[1:] or CHARS)]
    o = Image.new("RGBA", (sum(i.width for i in ims) + 30 * len(ims) + 10, 330), (70, 70, 80, 255)); x = 10
    for i in ims: o.alpha_composite(i, (x, 10)); x += i.width + 30
    o.save("/home/claude/rp/t.png")
    for n in CHARS: make(n).save(os.path.join(HERE, "renders", n + ".png"))
