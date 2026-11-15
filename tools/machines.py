"""Bâtiments médiévaux « Royaumes » : export vers le resource pack et aperçus.

- machines_core.py : moteur (textures peintes, boîtes, images-clés, rendu des aperçus) ;
- machines_designs.py : les quatre bâtiments ;
- ce fichier : table des custom_model_data, export des modèles, aperçus PNG / GIF.
"""
import json, os
from machines_core import *          # noqa: F401,F403
from machines_core import _split
from machines_designs import MACHINES

# ================================================================ table des custom_model_data
def cmd_table():
    """Objet complet 7301+, socle 7311+, pièces 7320 + 10 * i + j."""
    return {name: {"item": 7301 + i, "base": 7311 + i, "parts": 7320 + 10 * i} for i, name in enumerate(MACHINES)}

BASE_PIVOT = (24.0, 24.0, 24.0)

def icon_model(b):
    """Modèle complet (socle + pièces au repos) pour l'icône et l'objet en main, et le facteur de réduction
    qui le fait tenir dans le cube de 48 autorisé par Minecraft (ailes, fanions et girouette dépassent)."""
    m = Model().add(b.base)
    for p in b.parts: m.add(p.model)
    lo, hi = [1e9] * 3, [-1e9] * 3
    for e in m.els:          # bornes avant rotation : c'est ce que Minecraft limite
        for k in range(3):
            lo[k] = min(lo[k], e["from"][k]); hi[k] = max(hi[k], e["to"][k])
    shrink = min(1.0, 48 / hi[1], 24 / max(24 - lo[0], hi[0] - 24), 24 / max(24 - lo[2], hi[2] - 24))
    return m, math.floor(shrink * 1000) / 1000

# ================================================================ export
def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

def export():
    """Écrit textures et modèles dans le pack ; renvoie {nom: (ids, Building)}."""
    import shutil
    for d in (NS + "/textures/block/machine", NS + "/models/item/machine"):
        if os.path.isdir(d): shutil.rmtree(d)
        os.makedirs(d)
    used = set()
    out = {}
    table = cmd_table()
    for name, fn in MACHINES.items():
        b = fn()
        ids = table[name]
        im, shrink = icon_model(b)
        write(f"{NS}/models/item/machine/{name}.json", to_json(im, BASE_PIVOT, ICON_DISPLAY, shrink))
        write(f"{NS}/models/item/machine/{name}_base.json", to_json(b.base, BASE_PIVOT))
        for p in b.parts:
            write(f"{NS}/models/item/machine/{name}_{p.name}.json", to_json(p.model, p.pivot))
        for mdl in [b.base] + [p.model for p in b.parts]:
            for e in mdl.els:
                for fc in e["faces"]: used.add(e["tex"][fc])
        out[name] = (ids, b)
    for k in sorted(used):
        if k.startswith("mc:"):
            assert os.path.exists(MC + "block/" + k[3:] + ".png"), k
            continue
        im = CUSTOM[k]()
        meta = None
        if isinstance(im, tuple): im, meta = im
        im.save(f"{NS}/textures/block/machine/{k}.png")
        if meta: write(f"{NS}/textures/block/machine/{k}.png.mcmeta", meta)
    return out

def model_overrides(table):
    """Paires (custom_model_data, modèle) à déclarer sur le papier."""
    res = []
    for name, (ids, b) in table.items():
        res.append((ids["item"], f"cobbleislands:item/machine/{name}"))
        res.append((ids["base"], f"cobbleislands:item/machine/{name}_base"))
        for j, p in enumerate(b.parts):
            res.append((ids["parts"] + j, f"cobbleislands:item/machine/{name}_{p.name}"))
    return res

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(MACHINES)
    os.makedirs("/home/claude/previews", exist_ok=True)
    for n in names:
        b = MACHINES[n]()
        render(b, 3).save(f"/home/claude/previews/{n}.png")
        print(n, "ok", sum(len(_split(e)) for e in b.base.els), "éléments (socle)", [(p.name, sum(len(_split(e)) for e in p.model.els)) for p in b.parts])
