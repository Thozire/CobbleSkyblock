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
import machines

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

def add_paper_models(pairs):
    """Ajoute (custom_model_data, modèle) au papier, pour les anciens et nouveaux formats de modèles d'objets."""
    mp = f"{PACK}/assets/minecraft/models/item/paper.json"
    m = json.load(open(mp))
    have = {o["predicate"]["custom_model_data"] for o in m["overrides"]}
    for cmd, model in pairs:
        if cmd not in have: m["overrides"].append({"predicate": {"custom_model_data": cmd}, "model": model})
        else:
            for o in m["overrides"]:
                if o["predicate"]["custom_model_data"] == cmd: o["model"] = model
    m["overrides"].sort(key=lambda o: o["predicate"]["custom_model_data"])
    write_json(mp, m)
    ip = f"{PACK}/assets/minecraft/items/paper.json"
    it = json.load(open(ip))
    ent = {e["threshold"]: e for e in it["model"]["entries"]}
    for cmd, model in pairs:
        ent[cmd] = {"threshold": cmd, "model": {"type": "minecraft:model", "model": model}}
    it["model"]["entries"] = [ent[k] for k in sorted(ent)]
    write_json(ip, it)

def drop_machine_models():
    """Retire du papier les anciens modèles de machines (custom_model_data 7300 à 7399)."""
    mp = f"{PACK}/assets/minecraft/models/item/paper.json"
    m = json.load(open(mp))
    m["overrides"] = [o for o in m["overrides"] if not 7300 <= o["predicate"]["custom_model_data"] <= 7399]
    write_json(mp, m)
    ip = f"{PACK}/assets/minecraft/items/paper.json"
    it = json.load(open(ip))
    it["model"]["entries"] = [e for e in it["model"]["entries"] if not 7300 <= e["threshold"] <= 7399]
    write_json(ip, it)

def jf(v):
    """Nombre flottant Java compact."""
    v = round(float(v), 3)
    return ("%d" % v if v == int(v) else repr(v)) + "f"

def build_machines():
    drop_machine_models()
    table = machines.export()
    add_paper_models(machines.model_overrides(table))
    axis = {"x": 0, "y": 1, "z": 2}
    consts, items, bases, parts_sw, em_sw = [], [], [], [], []
    for name, (ids, b) in table.items():
        up = name.upper()
        rows = []
        for j, p in enumerate(b.parts):
            keys = ", ".join(", ".join([jf(k[0]), jf(k[1][0]), jf(k[1][1]), jf(k[1][2]), jf(axis[k[2]]), jf(k[3]), jf(k[4][0]), jf(k[4][1]), jf(k[4][2])])
                             for k in p.keys)
            rows.append("            new Part(%d, %s, %s, %s, %s, %s, new float[]{%s}),   // %s" % (
                ids["parts"] + j, jf(p.pivot[0]), jf(p.pivot[1]), jf(p.pivot[2]), "true" if p.bright else "false", jf(p.jitter), keys, p.name))
        consts.append("    private static final Part[] %s = {\n%s\n    };" % (up, "\n".join(rows)))
        ems = ["            new Emitter(\"%s\", %s, %s, %s, %d, %s, %s, %s, %s, %d, %d)," % (
            e.kind, jf(e.pos[0]), jf(e.pos[1]), jf(e.pos[2]), e.count, jf(e.spread[0]), jf(e.spread[1]), jf(e.spread[2]), jf(e.speed), e.period, e.at)
               for e in b.emitters]
        consts.append("    private static final Emitter[] %s_FX = {\n%s\n    };" % (up, "\n".join(ems)))
        items.append('            case "%s" -> %d;' % (name, ids["item"]))
        bases.append('            case "%s" -> %d;' % (name, ids["base"]))
        parts_sw.append('            case "%s" -> %s;' % (name, up))
        em_sw.append('            case "%s" -> %s_FX;' % (name, up))
    nl = "\n"
    src = f'''package fr.cobbleskyblock.islands;

/** Généré par tools/build_royal_pack.py (bâtiments de tools/machines_designs.py) — ne pas modifier à la main. */
final class MachineModels {{
    private MachineModels() {{}}

    /** Version des modèles : un bâtiment posé avec une autre version est reconstruit. */
    static final int VERSION = {machines.VERSION};

    /**
     * Pièce d'un bâtiment : modèle, pivot (repère de dessin, 1/16 de bloc), pleine lumière, vacillement
     * aléatoire (flammes) et images-clés. Chaque clé tient en 9 valeurs : durée (en pas de 5 ticks),
     * décalage x y z, axe de rotation (0 = X, 1 = Y, 2 = Z), angle en degrés, échelle x y z.
     */
    record Part(int cmd, float px, float py, float pz, boolean bright, float jitter, float[] keys) {{}}

    /**
     * Particules : type, position (repère de dessin), nombre, dispersion, vitesse, période et instant (en pas).
     * Nombre 0 : une seule particule lancée dans la direction (dx, dy, dz) à la vitesse donnée.
     */
    record Emitter(String kind, float x, float y, float z, int count, float dx, float dy, float dz, float speed, int period, int at) {{}}

{(nl + nl).join(consts)}

    /** Objet complet (icône, objet à poser). */
    static int item(String id) {{
        return switch (id) {{
{nl.join(items)}
            default -> 0;
        }};
    }}

    /** Socle immobile. */
    static int base(String id) {{
        return switch (id) {{
{nl.join(bases)}
            default -> 0;
        }};
    }}

    static Part[] parts(String id) {{
        return switch (id) {{
{nl.join(parts_sw)}
            default -> new Part[0];
        }};
    }}

    static Emitter[] emitters(String id) {{
        return switch (id) {{
{nl.join(em_sw)}
            default -> new Emitter[0];
        }};
    }}
}}
'''
    with open(f"{REPO}/cobbleislands/src/main/java/fr/cobbleskyblock/islands/MachineModels.java", "w", encoding="utf-8") as f:
        f.write(src)

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
    if "--machines-only" in sys.argv:        # ne régénère que les bâtiments (le reste du pack est gardé tel quel)
        build_machines()
        print("pack :", zip_pack())
        sys.exit(0)
    clean_old()
    tiles = build_tiles()
    build_fonts(tiles)
    build_lang()
    build_blank_item()
    build_machines()
    build_java()
    print("pack :", zip_pack())
