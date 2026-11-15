# Royaumes

Serveur Minecraft **tycoon médiéval** (Java 1.21.1, Fabric) : fonde ton royaume, construis des bâtiments
producteurs, vends au marché de la capitale et grimpe au classement. Seul ou en équipe.

## Jouer

- Minecraft Java **1.21.1** suffit : le serveur envoie lui-même le resource pack (menus, icônes).
- Launcher dédié : **[CobbleSkyblock-Launcher.exe](https://github.com/Thozire/CobbleSkyblock/raw/main/launcher/CobbleSkyblock-Launcher.exe)** (comptes premium).

## Commandes

| Commande | Effet |
|---|---|
| `/royaume` (ou `/r`) | menu du royaume |
| `/royaume go` | aller sur ton domaine |
| `/royaume construire <scierie\|ferme\|mine>` | poser un bâtiment |
| `/royaume vendre` | vendre toute la production |
| `/royaume inviter <joueur>` | inviter dans ta cour |
| `/capitale` | retourner à la capitale |

## Contenu du dépôt

- `cobbleislands/` : le mod serveur (Royaumes), compilé par GitHub Actions et publié dans `builds/`.
- `tools/` : générateurs du resource pack (`medieval_gui.py`) et des structures (`medieval_structures.py`).
- `pack.toml`, `index.toml`, `mods/`, `resourcepacks/` : le modpack (packwiz) synchronisé par le serveur et le launcher.
- `launcher/`, `launcher-src/`, `launcher.json` : le launcher Windows et sa configuration en ligne.
