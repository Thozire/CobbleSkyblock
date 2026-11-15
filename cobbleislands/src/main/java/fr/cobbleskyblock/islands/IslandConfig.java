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
    /** Distance entre deux domaines (en blocs). Ne pas changer une fois des royaumes créés. */
    public int espacement = 512;
    /** Hauteur du sol des domaines (la dimension est plate : herbe à y=-1). */
    public int hauteur = 0;
    /** Structure du campement de départ. */
    public String modele = "cobbleislands:campement";
    /** Demi-largeur du domaine pour chaque niveau. */
    public int[] taillesParNiveau = {24, 40, 60, 80, 100};
    /** Prix (écus) pour atteindre chaque niveau de domaine (le premier est gratuit). */
    public int[] coutTaille = {0, 2000, 8000, 25000, 60000};
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
                    IslandConfig read = GSON.fromJson(r, IslandConfig.class);
                    if (read != null) cfg = read;
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

    public int membersCost(int level) { return level >= 1 && level <= coutMembres.length ? coutMembres[level - 1] : -1; }

    public int membersFor(int level) {
        return membresParNiveau[Math.max(0, Math.min(level, membresParNiveau.length) - 1)];
    }
}
