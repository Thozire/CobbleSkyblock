"""Construit le resource pack « Royaumes » (menu v9) et le code Java qui en dépend.

- Fond du menu principal découpé en 4 tuiles 220x135 (glyphes de la police cobbleislands:gui).
- Caractères d'espacement (±1 … ±512 px) pour placer le stylo.
- Polices décalées cobbleislands:t<dy> pour écrire les textes dynamiques à la bonne hauteur.
- Langue : « Inventaire » vidé (le libellé vanilla passerait par-dessus le dessin).
- Objet transparent (papier, custom_model_data 7299) pour les infobulles des boutons.
- Génère cobbleislands/.../GuiFont.java (largeurs des caractères vanilla, codes des glyphes).
"""
import json, os, shutil, sys, zipfile
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from royal_ui import FONT, OX, OY, W, H, TILE_W, TILE_H
import royal_v8

PACK = "/home/claude/rp/royaumes"
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MC = "/home/claude/mcassets/assets/minecraft"
NS = f"{PACK}/assets/cobbleislands"

# Polices décalées utilisées par le menu principal (haut du texte = 6 + dy, repère du coffre)
TEXT_DY = [69, 89, 109, 129, 149, 156]

NEG = [chr(0xF801 + i) for i in range(10)]   # -1, -2, -4 … -512
POS = [chr(0xF821 + i) for i in range(10)]   # +1, +2, +4 … +512
TILE_CHARS = [chr(0xE100 + i) for i in range(4)]

def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)

def build_tiles():
    img = royal_v8.render()
    assert img.size == (W, H)
    out = []
    os.makedirs(f"{NS}/textures/font", exist_ok=True)
    for r in range(2):
        for c in range(2):
            t = img.crop((c * TILE_W, r * TILE_H, (c + 1) * TILE_W, (r + 1) * TILE_H)).copy()
            # Minecraft calcule l'avance d'un glyphe d'après sa dernière colonne non transparente :
            # un pixel quasi invisible dans le coin droit garantit une largeur de 220.
            if t.getpixel((TILE_W - 1, 0))[3] == 0: t.putpixel((TILE_W - 1, 0), (0, 0, 0, 1))
            name = f"main_{r}{c}.png"
            t.save(f"{NS}/textures/font/{name}")
            top = -OY + r * TILE_H                 # haut de la tuile dans le repère du coffre
            out.append({"type": "bitmap", "file": f"cobbleislands:font/{name}", "height": TILE_H,
                        "ascent": 13 - top, "chars": [TILE_CHARS[r * 2 + c]]})
    return out

def build_fonts(tile_providers):
    adv = {}
    for i in range(10):
        adv[NEG[i]] = -(1 << i); adv[POS[i]] = 1 << i
    write_json(f"{NS}/font/gui.json", {"providers": [{"type": "space", "advances": adv}] + tile_providers})
    vanilla = json.load(open(f"{MC}/font/include/default.json"))["providers"]
    for dy in TEXT_DY:
        provs = [{"type": "space", "advances": {" ": 4, "‌": 0}}]
        for p in vanilla:
            q = dict(p)
            q["ascent"] = p.get("ascent", 7) - dy
            provs.append(q)
        write_json(f"{NS}/font/t{dy}.json", {"providers": provs})

def build_lang():
    for lang in ("fr_fr", "fr_ca", "en_us", "en_gb"):
        write_json(f"{PACK}/assets/minecraft/lang/{lang}.json", {"container.inventory": ""})

def build_blank_item():
    Image.new("RGBA", (16, 16), (0, 0, 0, 0)).save(f"{NS}/textures/item/ui/blank.png")
    write_json(f"{NS}/models/item/ui/7299.json", {"parent": "minecraft:item/generated", "textures": {"layer0": "cobbleislands:item/ui/blank"}})
    mp = f"{PACK}/assets/minecraft/models/item/paper.json"
    m = json.load(open(mp))
    if not any(o["predicate"]["custom_model_data"] == 7299 for o in m["overrides"]):
        m["overrides"].append({"predicate": {"custom_model_data": 7299}, "model": "cobbleislands:item/ui/7299"})
        m["overrides"].sort(key=lambda o: o["predicate"]["custom_model_data"])
        write_json(mp, m)
    ip = f"{PACK}/assets/minecraft/items/paper.json"
    it = json.load(open(ip))
    ent = it["model"]["entries"]
    if not any(e["threshold"] == 7299 for e in ent):
        ent.append({"threshold": 7299, "model": {"type": "minecraft:model", "model": "cobbleislands:item/ui/7299"}})
        ent.sort(key=lambda e: e["threshold"])
        # 7299 ne doit pas « déborder » sur 7300+ : rien au-delà, c'est la dernière entrée
        write_json(ip, it)

def clean_old():
    d = f"{NS}/textures/gui"
    if os.path.isdir(d): shutil.rmtree(d)

def java_escape(s):
    return "".join(c if 32 <= ord(c) < 127 and c not in '\\"' else "\\u%04x" % ord(c) for c in s)

def build_java():
    chars = sorted(FONT.glyphs.keys())
    hexs = "".join("%04x%02x" % (ord(c), FONT.glyphs[c][1]) for c in chars if ord(c) < 0x10000)
    parts = [hexs[i:i + 120] for i in range(0, len(hexs), 120)]
    table = "\n            + ".join('"%s"' % x for x in parts)
    src = f'''package fr.cobbleskyblock.islands;

/** Généré par tools/build_royal_pack.py — ne pas modifier à la main. */
final class GuiFont {{
    private GuiFont() {{}}

    /** Glyphes des tuiles du fond du menu principal (haut-gauche, haut-droit, bas-gauche, bas-droit). */
    static final String MAIN_TILES = "{java_escape(''.join(TILE_CHARS))}";
    static final int TILE_W = {TILE_W}, CANVAS_X = {-OX};
    /** Espacements : NEG[i] recule de 2^i pixels, POS[i] avance de 2^i pixels. */
    static final String NEG = "{java_escape(''.join(NEG))}";
    static final String POS = "{java_escape(''.join(POS))}";

    /** Paires « code (4 hex) + largeur (2 hex) » concaténées. */
    private static final String TABLE = {table};
    private static final java.util.Map<Character, Integer> W = new java.util.HashMap<>();
    static {{
        for (int i = 0; i + 6 <= TABLE.length(); i += 6)
            W.put((char) Integer.parseInt(TABLE.substring(i, i + 4), 16), Integer.parseInt(TABLE.substring(i + 4, i + 6), 16));
    }}

    /** Largeur en pixels d'un texte dans la police vanilla (sans gras). */
    static int width(String s) {{
        int w = 0;
        for (int i = 0; i < s.length(); i++) {{
            char c = s.charAt(i);
            w += c == ' ' ? 4 : W.getOrDefault(c, 6);
        }}
        return w;
    }}
}}
'''
    path = f"{REPO}/cobbleislands/src/main/java/fr/cobbleskyblock/islands/GuiFont.java"
    with open(path, "w", encoding="utf-8") as f: f.write(src)

def zip_pack():
    dst = f"{REPO}/resourcepacks/RoyaumesPack.zip"
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(PACK):
            for fn in sorted(files):
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, PACK))
    return dst

if __name__ == "__main__":
    clean_old()
    tiles = build_tiles()
    build_fonts(tiles)
    build_lang()
    build_blank_item()
    build_java()
    print("pack :", zip_pack())
