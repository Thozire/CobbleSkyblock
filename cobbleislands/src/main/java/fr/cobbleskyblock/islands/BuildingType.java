package fr.cobbleskyblock.islands;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;

import java.util.List;
import java.util.Random;

/**
 * Les bâtiments producteurs. Chaque niveau augmente la production par minute
 * et la capacité de l'entrepôt ; certains débloquent de nouvelles ressources.
 */
public enum BuildingType {
    SCIERIE("Scierie", "scierie", 7221, 150,
            new int[]{12, 20, 32, 48, 70}, new int[]{0, 400, 1200, 3500, 9000},
            List.of(new Output("minecraft:oak_log", 1, 6), new Output("minecraft:spruce_log", 3, 3), new Output("minecraft:dark_oak_log", 5, 2))),
    FERME("Ferme", "ferme", 7223, 300,
            new int[]{10, 18, 28, 42, 60}, new int[]{0, 600, 1800, 5000, 12000},
            List.of(new Output("minecraft:wheat", 1, 6), new Output("minecraft:carrot", 2, 3), new Output("minecraft:potato", 3, 3), new Output("minecraft:pumpkin", 5, 1))),
    MINE("Mine", "mine", 7222, 600,
            new int[]{10, 16, 26, 38, 55}, new int[]{0, 1000, 3000, 8000, 20000},
            List.of(new Output("minecraft:cobblestone", 1, 8), new Output("minecraft:coal", 2, 3), new Output("minecraft:raw_copper", 3, 2),
                    new Output("minecraft:raw_iron", 4, 2), new Output("minecraft:raw_gold", 5, 1)));

    /** Une ressource produite à partir d'un certain niveau, avec un poids de tirage. */
    public record Output(String item, int fromLevel, int weight) {
        public Item asItem() {
            Item it = BuiltInRegistries.ITEM.get(ResourceLocation.parse(item));
            return it == null ? Items.AIR : it;
        }
    }

    public static final int MAX_LEVEL = 5;

    public final String label, structure;
    public final int icon, price;
    /** Objets produits par minute, par niveau. */
    public final int[] perMinute;
    /** Prix pour passer au niveau i+1 (index 0 inutilisé). */
    public final int[] upgradeCost;
    public final List<Output> outputs;

    BuildingType(String label, String structure, int icon, int price, int[] perMinute, int[] upgradeCost, List<Output> outputs) {
        this.label = label;
        this.structure = structure;
        this.icon = icon;
        this.price = price;
        this.perMinute = perMinute;
        this.upgradeCost = upgradeCost;
        this.outputs = outputs;
    }

    public int rate(int level) { return perMinute[Math.min(level, MAX_LEVEL) - 1]; }

    /** Capacité de l'entrepôt : 30 minutes de production. */
    public int capacity(int level) { return rate(level) * 30; }

    public int nextCost(int level) { return level >= MAX_LEVEL ? -1 : upgradeCost[level]; }

    /** Tire au sort une ressource parmi celles débloquées à ce niveau. */
    public Output roll(int level, Random rnd) {
        int total = 0;
        for (Output o : outputs) if (o.fromLevel <= level) total += o.weight;
        int r = rnd.nextInt(Math.max(1, total));
        for (Output o : outputs) {
            if (o.fromLevel > level) continue;
            r -= o.weight;
            if (r < 0) return o;
        }
        return outputs.get(0);
    }

    public static BuildingType byName(String s) {
        for (BuildingType t : values()) if (t.name().equalsIgnoreCase(s) || t.structure.equalsIgnoreCase(s)) return t;
        return null;
    }
}
