package fr.cobbleskyblock.islands;

/** Généré par tools/build_royal_pack.py (bâtiments de tools/machines_designs.py) — ne pas modifier à la main. */
final class MachineModels {
    private MachineModels() {}

    /** Version des modèles : un bâtiment posé avec une autre version est reconstruit. */
    static final int VERSION = 8;

    /**
     * Pièce d'un bâtiment : modèle, pivot (repère de dessin, 1/16 de bloc), pleine lumière, vacillement
     * aléatoire (flammes) et images-clés. Chaque clé tient en 9 valeurs : durée (en pas de 5 ticks),
     * décalage x y z, axe de rotation (0 = X, 1 = Y, 2 = Z), angle en degrés, échelle x y z.
     */
    record Part(int cmd, float px, float py, float pz, boolean bright, float jitter, float[] keys) {}

    /**
     * Particules : type, position (repère de dessin), nombre, dispersion, vitesse, période et instant (en pas).
     * Nombre 0 : une seule particule lancée dans la direction (dx, dy, dz) à la vitesse donnée.
     */
    record Emitter(String kind, float x, float y, float z, int count, float dx, float dy, float dz, float speed, int period, int at) {}

    private static final Part[] SCIERIE = {
            new Part(7320, 42f, 18f, 24f, false, 0f, new float[]{4f, 0f, 0f, 0f, 0f, -90f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, -180f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, -270f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, -360f, 1f, 1f, 1f}),   // roue
            new Part(7321, 18f, 14f, 24f, false, 0f, new float[]{1f, 0f, 3.4f, 0f, 1f, 0f, 1f, 1f, 1f, 1f, 0f, 0f, 0f, 1f, 0f, 1f, 1f, 1f}),   // scie
            new Part(7322, 18f, 13.5f, 20f, false, 0f, new float[]{22f, 0f, 0f, 8f, 1f, 0f, 1f, 1f, 1f, 2f, 0f, 0f, 8f, 1f, 0f, 1f, 1f, 1f, 6f, 0f, 0f, 0f, 1f, 0f, 1f, 1f, 1f, 2f, 0f, 0f, 0f, 1f, 0f, 1f, 1f, 1f}),   // grume
            new Part(7323, 18f, 47.9f, 24f, false, 0f, new float[]{4f, 0f, 0f, 0f, 1f, 10f, 1f, 1f, 1f, 3f, 0f, 0f, 0f, 1f, -4f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 1f, 7f, 1f, 1f, 1f, 5f, 0f, 0f, 0f, 1f, -10f, 1f, 1f, 1f}),   // fanion
    };

    private static final Emitter[] SCIERIE_FX = {
            new Emitter("wood", 18f, 18.5f, 22.5f, 3, 0.06f, 0.04f, 0.06f, 0.03f, 2, 0),
            new Emitter("splash", 42f, 5.5f, 33f, 2, 0.2f, 0.05f, 0.12f, 0f, 2, 1),
    };

    private static final Part[] FERME = {
            new Part(7330, 24f, 30f, 14.4f, false, 0f, new float[]{8f, 0f, 0f, 0f, 2f, 90f, 1f, 1f, 1f, 8f, 0f, 0f, 0f, 2f, 180f, 1f, 1f, 1f, 8f, 0f, 0f, 0f, 2f, 270f, 1f, 1f, 1f, 8f, 0f, 0f, 0f, 2f, 360f, 1f, 1f, 1f}),   // ailes
            new Part(7331, 37f, 1f, 5.6f, false, 0f, new float[]{4f, 0f, 0f, 0f, 0f, 5f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, -2f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, 4f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, -5f, 1f, 1f, 1f}),   // ble
            new Part(7332, 13f, 1f, 7.2f, false, 0f, new float[]{8f, 0f, 0f, 0f, 2f, 4f, 1f, 1f, 1f, 8f, 0f, 0f, 0f, 2f, -4f, 1f, 1f, 1f}),   // epouvantail
            new Part(7333, 24f, 48.2f, 30f, false, 0f, new float[]{6f, 0f, 0f, 0f, 1f, 25f, 1f, 1f, 1f, 3f, 0f, 0f, 0f, 1f, 14f, 1f, 1f, 1f, 5f, 0f, 0f, 0f, 1f, 42f, 1f, 1f, 1f, 6f, 0f, 0f, 0f, 1f, -8f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 1f, 6f, 1f, 1f, 1f, 8f, 0f, 0f, 0f, 1f, 0f, 1f, 1f, 1f}),   // girouette
            new Part(7334, 24f, 24f, 24f, true, 0f, new float[]{}),   // lumiere
    };

    private static final Emitter[] FERME_FX = {
            new Emitter("ash", 24f, 9f, 16f, 2, 0.25f, 0.3f, 0.15f, 0f, 4, 0),
            new Emitter("grow", 37f, 12f, 6f, 1, 0.5f, 0.2f, 0.3f, 0f, 10, 3),
    };

    private static final Part[] MINE = {
            new Part(7340, 24f, 6f, 9f, false, 0f, new float[]{6f, 0f, 0f, 0f, 1f, 0f, 1f, 1f, 1f, 10f, 0f, 0f, 27f, 1f, 0f, 1f, 1f, 1f, 6f, 0f, 0f, 27f, 1f, 0f, 1f, 1f, 1f, 10f, 0f, 0f, 0f, 1f, 0f, 1f, 1f, 1f}),   // wagonnet
            new Part(7341, 41f, 18f, 7.5f, false, 0f, new float[]{4f, 0f, 0f, 0f, 0f, 120f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, 240f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, 360f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, 360f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, 240f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, 120f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, 0f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 0f, 0f, 1f, 1f, 1f}),   // treuil
            new Part(7342, 41f, 17.4f, 7.5f, false, 0f, new float[]{12f, 0f, 0f, 0f, 1f, 0f, 1f, 0.26f, 1f, 4f, 0f, 0f, 0f, 1f, 0f, 1f, 0.26f, 1f, 12f, 0f, 0f, 0f, 1f, 0f, 1f, 0.86f, 1f, 4f, 0f, 0f, 0f, 1f, 0f, 1f, 0.86f, 1f}),   // corde
            new Part(7343, 41f, 3f, 7.5f, false, 0f, new float[]{12f, 0f, 6f, 0f, 1f, 0f, 1f, 1f, 1f, 4f, 0f, 6f, 0f, 1f, 0f, 1f, 1f, 1f, 12f, 0f, 0f, 0f, 1f, 0f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 1f, 0f, 1f, 1f, 1f}),   // seau
            new Part(7344, 23f, 45.25f, 37f, false, 0f, new float[]{4f, 0f, 0f, 0f, 1f, 10f, 1f, 1f, 1f, 3f, 0f, 0f, 0f, 1f, -4f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 1f, 7f, 1f, 1f, 1f, 5f, 0f, 0f, 0f, 1f, -10f, 1f, 1f, 1f}),   // fanion
    };

    private static final Emitter[] MINE_FX = {
            new Emitter("stone", 24f, 3f, 19f, 2, 0.3f, 0.1f, 0.2f, 0.02f, 6, 0),
    };

    private static final Part[] FORGE = {
            new Part(7350, 10f, 17.6f, 17.5f, false, 0f, new float[]{4f, 0f, 0f, 0f, 2f, 24f, 1f, 1f, 1f, 1f, 0f, 0f, 0f, 2f, 24f, 1f, 1f, 1f, 1f, 0f, 0f, 0f, 2f, 0f, 1f, 1f, 1f, 2f, 0f, 0f, 0f, 2f, 0f, 1f, 1f, 1f}),   // marteau
            new Part(7351, 15.5f, 9f, 38f, false, 0f, new float[]{3f, 0f, 0f, 0f, 1f, 0f, 1f, 0.5f, 1f, 5f, 0f, 0f, 0f, 1f, 0f, 1f, 1f, 1f}),   // soufflet
            new Part(7352, 9f, 9.6f, 8f, false, 0f, new float[]{1f, 0f, 0f, 0f, 2f, 90f, 1f, 1f, 1f, 1f, 0f, 0f, 0f, 2f, 180f, 1f, 1f, 1f, 1f, 0f, 0f, 0f, 2f, 270f, 1f, 1f, 1f, 1f, 0f, 0f, 0f, 2f, 360f, 1f, 1f, 1f}),   // meule
            new Part(7353, 35f, 8f, 37f, true, 0.22f, new float[]{}),   // feu
            new Part(7354, 8f, 43.65f, 24f, false, 0f, new float[]{4f, 0f, 0f, 0f, 1f, 10f, 1f, 1f, 1f, 3f, 0f, 0f, 0f, 1f, -4f, 1f, 1f, 1f, 4f, 0f, 0f, 0f, 1f, 7f, 1f, 1f, 1f, 5f, 0f, 0f, 0f, 1f, -10f, 1f, 1f, 1f}),   // fanion
            new Part(7355, 24f, 24f, 24f, true, 0f, new float[]{}),   // lumiere
    };

    private static final Emitter[] FORGE_FX = {
            new Emitter("smoke", 35f, 47f, 40f, 0, 0f, 1f, 0f, 0.05f, 2, 0),
            new Emitter("spark", 23.6f, 14.8f, 17.5f, 7, 0.12f, 0.05f, 0.12f, 0.12f, 8, 6),
            new Emitter("lava", 23.6f, 14.8f, 17.5f, 1, 0.05f, 0.02f, 0.05f, 0f, 8, 6),
            new Emitter("flame", 35f, 11f, 31.5f, 3, 0.3f, 0.12f, 0.1f, 0.01f, 8, 3),
            new Emitter("spark", 9f, 14.6f, 8f, 2, 0.06f, 0.03f, 0.04f, 0.06f, 2, 0),
    };

    /** Objet complet (icône, objet à poser). */
    static int item(String id) {
        return switch (id) {
            case "scierie" -> 7301;
            case "ferme" -> 7302;
            case "mine" -> 7303;
            case "forge" -> 7304;
            default -> 0;
        };
    }

    /** Socle immobile. */
    static int base(String id) {
        return switch (id) {
            case "scierie" -> 7311;
            case "ferme" -> 7312;
            case "mine" -> 7313;
            case "forge" -> 7314;
            default -> 0;
        };
    }

    static Part[] parts(String id) {
        return switch (id) {
            case "scierie" -> SCIERIE;
            case "ferme" -> FERME;
            case "mine" -> MINE;
            case "forge" -> FORGE;
            default -> new Part[0];
        };
    }

    static Emitter[] emitters(String id) {
        return switch (id) {
            case "scierie" -> SCIERIE_FX;
            case "ferme" -> FERME_FX;
            case "mine" -> MINE_FX;
            case "forge" -> FORGE_FX;
            default -> new Emitter[0];
        };
    }
}
