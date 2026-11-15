package fr.cobbleskyblock.islands;

/** Généré par tools/build_royal_pack.py (modèles de tools/machines.py) — ne pas modifier à la main. */
final class MachineModels {
    private MachineModels() {}

    /** Pièce animée : modèle, décalage (1/16 de bloc), animation, pleine lumière. */
    record Part(int cmd, float ox, float oy, float oz, String anim, boolean bright) {}

    /** Objet complet (icône, objet à poser). */
    static int item(String id) {
        return switch (id) {
            case "scierie" -> 7301;
            case "moulin" -> 7302;
            case "mine" -> 7303;
            case "forge" -> 7304;
            default -> 0;
        };
    }

    /** Socle immobile. */
    static int base(String id) {
        return switch (id) {
            case "scierie" -> 7311;
            case "moulin" -> 7312;
            case "mine" -> 7313;
            case "forge" -> 7314;
            default -> 0;
        };
    }

    static Part[] parts(String id) {
        return switch (id) {
            case "scierie" -> new Part[]{new Part(7321, 0f, 2f, 0f, "spin_z", false)};
            case "moulin" -> new Part[]{new Part(7323, 0f, 1.5f, 0f, "spin_y", false)};
            case "mine" -> new Part[]{new Part(7325, 0f, 2.5f, 0f, "spin_z", false)};
            case "forge" -> new Part[]{new Part(7327, -3.5f, 2f, 2f, "flicker", true), new Part(7328, -3.5f, 4.5f, 1.5f, "swing", false)};
            default -> new Part[0];
        };
    }
}
