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
    /** Distance entre deux îles (en blocs). Ne pas changer une fois des îles créées. */
    public int espacement = 1024;
    /** Hauteur du haut de l'île de départ. */
    public int hauteur = 100;
    /** Modèle de l'île de départ (structure). Sauvegarde ta propre île avec un bloc de structure sous ce nom pour la remplacer. */
    public String modele = "cobbleislands:ile_depart";
    /** Demi-largeur de la zone constructible pour chaque niveau d'île (niveau 1 = premier chiffre). */
    public int[] taillesParNiveau = {20, 35, 50, 75, 100};
    /** Nombre maximum de membres (chef compris) pour chaque niveau d'équipe. */
    public int[] membresParNiveau = {3, 4, 5, 6};
    /** Ramène sur son île un joueur qui tombe dans le vide (au lieu de mourir). */
    public boolean sauvetageVide = true;
    /** Les îles sont ouvertes aux visites par défaut. */
    public boolean visitesOuvertesParDefaut = true;
    /** Modèle du spawn (île hub commune), construit au premier démarrage dans l'Overworld. */
    public String modeleSpawn = "cobbleislands:spawn";
    /** Hauteur du sol du spawn. */
    public int hauteurSpawn = 100;
    /** Rayon protégé autour du spawn (seuls les opérateurs peuvent y construire). */
    public int protectionSpawn = 48;
    /** Durée de validité d'une invitation (secondes). */
    public int dureeInvitation = 300;

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();

    public static IslandConfig load() {
        Path p = FabricLoader.getInstance().getConfigDir().resolve("cobbleislands.json");
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

    public int membersFor(int level) {
        return membresParNiveau[Math.max(0, Math.min(level, membresParNiveau.length) - 1)];
    }
}
