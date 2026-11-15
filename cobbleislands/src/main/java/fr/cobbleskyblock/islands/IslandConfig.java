package fr.cobbleskyblock.islands;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.fabricmc.loader.api.FabricLoader;

import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Réglages modifiables dans config/cobbleislands.json (rechargés au redémarrage). */
public class IslandConfig {
    /** Version du fichier (migration automatique des anciennes valeurs). */
    public int version = 3;
    /** Distance entre deux domaines (en blocs). Ne pas changer une fois des royaumes créés. */
    public int espacement = 512;
    /** Hauteur où l'on marche sur les îles (la dimension est vide). */
    public int hauteur = 100;
    /** Demi-largeur du terrain constructible (distance du centre à la bordure) pour chaque niveau. L'îlot de départ fait 13 de rayon. */
    public int[] taillesParNiveau = {16, 22, 30, 40, 52, 64};
    /** Marge ajoutée à la bordure. */
    public int marge = 0;
    /** Prix (écus) pour atteindre chaque niveau de terrain (le premier est gratuit). */
    public int[] coutTaille = {0, 1500, 5000, 15000, 40000, 90000};
    /** Nombre maximum de bâtiments par niveau (amélioration indépendante du terrain). */
    public int[] machinesParNiveau = {3, 5, 7, 10, 13, 16, 20};
    /** Prix (écus) pour chaque niveau de limite de bâtiments. */
    public int[] coutMachines = {0, 1000, 3000, 8000, 20000, 45000, 90000};
    /** Nombre maximum de membres (seigneur compris) par niveau d'équipe. */
    public int[] membresParNiveau = {3, 4, 5, 6};
    /** Prix (écus) pour chaque niveau d'équipe. */
    public int[] coutMembres = {0, 1500, 5000, 15000};
    /** Écus donnés à la création d'un royaume. */
    public int ecusDepart = 250;
    /** Production quand aucun membre n'est connecté (1.0 = 100 %). */
    public double productionHorsLigne = 0.5;
    /** Les domaines sont ouverts aux visites par défaut. */
    public boolean visitesOuvertesParDefaut = true;
    /** Structure de la capitale (spawn), construite au premier démarrage. */
    public String modeleSpawn = "cobbleislands:capitale";
    /** Hauteur du sol de la capitale. */
    public int hauteurSpawn = 100;
    /** Rayon protégé autour de la capitale. */
    public int protectionSpawn = 64;
    /** Resource pack envoyé aux joueurs à la connexion (menus, icônes). Vide = désactivé. */
    public String resourcePack = "https://raw.githubusercontent.com/Thozire/CobbleSkyblock/main/resourcepacks/RoyaumesPack.zip";
    /** Le pack est-il obligatoire pour jouer ? */
    public boolean resourcePackObligatoire = true;
    /** Durée de validité d'une invitation (secondes). */
    public int dureeInvitation = 300;

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();

    public static IslandConfig load() {
        Path p = FabricLoader.getInstance().getConfigDir().resolve("royaumes.json");
        IslandConfig cfg = new IslandConfig();
        try {
            if (Files.exists(p)) {
                try (Reader r = Files.newBufferedReader(p, StandardCharsets.UTF_8)) {
                    com.google.gson.JsonObject raw = com.google.gson.JsonParser.parseReader(r).getAsJsonObject();
                    IslandConfig read = GSON.fromJson(raw, IslandConfig.class);
                    if (read != null) cfg = read;
                    if (!raw.has("version") || cfg.version < 2) {             // passage aux îles flottantes
                        IslandConfig def = new IslandConfig();
                        cfg.hauteur = def.hauteur;
                        cfg.taillesParNiveau = def.taillesParNiveau;
                        cfg.marge = def.marge;
                        cfg.machinesParNiveau = def.machinesParNiveau;
                        cfg.version = 2;
                    }
                    if (cfg.version < 3) {                                    // améliorations indépendantes, îlot fixe
                        IslandConfig def = new IslandConfig();
                        cfg.taillesParNiveau = def.taillesParNiveau;
                        cfg.coutTaille = def.coutTaille;
                        cfg.marge = def.marge;
                        cfg.machinesParNiveau = def.machinesParNiveau;
                        cfg.coutMachines = def.coutMachines;
                        cfg.version = 3;
                    }
                    if (cfg.machinesParNiveau == null) cfg.machinesParNiveau = new IslandConfig().machinesParNiveau;
                    if (cfg.coutMachines == null) cfg.coutMachines = new IslandConfig().coutMachines;
                }
            }
            try (Writer w = Files.newBufferedWriter(p, StandardCharsets.UTF_8)) {
                GSON.toJson(cfg, w);
            }
        } catch (Exception e) {
            CobbleIslands.LOG.error("Config illisible, valeurs par défaut utilisées", e);
        }
        return cfg;
    }

    public int radiusFor(int level) {
        return taillesParNiveau[Math.max(0, Math.min(level, taillesParNiveau.length) - 1)];
    }

    public int sizeCost(int level) { return level >= 1 && level <= coutTaille.length ? coutTaille[level - 1] : -1; }

    public int machinesCost(int level) { return level >= 1 && level <= coutMachines.length ? coutMachines[level - 1] : -1; }

    public int membersCost(int level) { return level >= 1 && level <= coutMembres.length ? coutMembres[level - 1] : -1; }

    public int machinesFor(int level) {
        return machinesParNiveau[Math.max(0, Math.min(level, machinesParNiveau.length) - 1)];
    }

    public int membersFor(int level) {
        return membresParNiveau[Math.max(0, Math.min(level, membresParNiveau.length) - 1)];
    }
}
