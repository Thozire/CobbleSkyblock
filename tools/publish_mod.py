"""Ajoute le jar compilé de CobbleIslands au modpack (côté serveur) et régénère index.toml / pack.toml.
Lancé automatiquement par GitHub Actions après chaque compilation."""
import glob, hashlib, os, re, shutil, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = "https://raw.githubusercontent.com/Thozire/CobbleSkyblock/main/"
EXCLUDE_DIRS = {".git", ".github", "cobbleislands", "tools", "builds", "launcher", "launcher-src"}
EXCLUDE_FILES = {"pack.toml", "index.toml", ".packwizignore", ".gitignore", "README.md", "launcher.json"}

def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def publish_jar():
    jars = [j for j in glob.glob(os.path.join(ROOT, "cobbleislands/build/libs/cobbleislands-*.jar")) if not j.endswith("-sources.jar")]
    if not jars:
        sys.exit("aucun jar compilé trouvé")
    jar = max(jars, key=os.path.getmtime)
    name = os.path.basename(jar)
    os.makedirs(os.path.join(ROOT, "builds"), exist_ok=True)
    for old in glob.glob(os.path.join(ROOT, "builds", "cobbleislands-*.jar")):
        os.remove(old)
    dst = os.path.join(ROOT, "builds", name)
    shutil.copy(jar, dst)
    with open(os.path.join(ROOT, "mods", "cobbleislands.pw.toml"), "w", newline="\n") as f:
        f.write(f'''name = "CobbleIslands"
filename = "{name}"
side = "server"

[download]
url = "{RAW}builds/{name}"
hash-format = "sha256"
hash = "{sha256(dst)}"
''')
    print("publié :", name)

def reindex():
    files = []
    for root, dirs, fs in os.walk(ROOT):
        rel_root = os.path.relpath(root, ROOT)
        top = rel_root.split(os.sep)[0]
        if top in EXCLUDE_DIRS:
            dirs[:] = []
            continue
        for f in fs:
            rel = os.path.normpath(os.path.join(rel_root, f)).replace(os.sep, "/")
            if rel in EXCLUDE_FILES:
                continue
            files.append(rel)
    idx = 'hash-format = "sha256"\n'
    for rel in sorted(files):
        idx += f'\n[[files]]\nfile = "{rel}"\nhash = "{sha256(os.path.join(ROOT, rel))}"\n'
        if rel.endswith(".pw.toml"):
            idx += "metafile = true\n"
    open(os.path.join(ROOT, "index.toml"), "w", newline="\n").write(idx)
    pack = open(os.path.join(ROOT, "pack.toml")).read()
    h = hashlib.sha256(idx.encode()).hexdigest()
    pack = re.sub(r'(\[index\][\s\S]*?hash = ")[0-9a-f]+', lambda m: m.group(1) + h, pack)
    open(os.path.join(ROOT, "pack.toml"), "w", newline="\n").write(pack)
    print(len(files), "fichiers indexés")

if __name__ == "__main__":
    if "--index-only" not in sys.argv:
        publish_jar()
    reindex()
