package fr.cobbleskyblock.islands;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.LinkedHashMap;
import java.util.Map;

/** Le marché de la capitale : prix de rachat des ressources et ventes. */
public final class Market {
    private Market() {}

    /** Prix de vente unitaire (écus). */
    public static final Map<String, Integer> PRICES = new LinkedHashMap<>();
    static {
        PRICES.put("minecraft:oak_log", 2);
        PRICES.put("minecraft:spruce_log", 3);
        PRICES.put("minecraft:dark_oak_log", 4);
        PRICES.put("minecraft:wheat", 2);
        PRICES.put("minecraft:carrot", 3);
        PRICES.put("minecraft:potato", 3);
        PRICES.put("minecraft:pumpkin", 6);
        PRICES.put("minecraft:cobblestone", 1);
        PRICES.put("minecraft:coal", 4);
        PRICES.put("minecraft:raw_copper", 5);
        PRICES.put("minecraft:raw_iron", 9);
        PRICES.put("minecraft:raw_gold", 16);
    }

    public static int price(String item) { return PRICES.getOrDefault(item, 0); }

    public static Item item(String id) { return BuiltInRegistries.ITEM.get(ResourceLocation.parse(id)); }

    public static String id(Item item) { return BuiltInRegistries.ITEM.getKey(item).toString(); }

    /** Vend tout le contenu des entrepôts du royaume. Renvoie le gain. */
    public static long sellStorages(Island is) {
        long gain = 0;
        for (Building b : is.buildings) gain += sellBuilding(is, b);
        return gain;
    }

    public static long sellBuilding(Island is, Building b) {
        long gain = 0;
        for (Map.Entry<String, Long> e : b.storage.entrySet()) gain += e.getValue() * price(e.getKey());
        b.storage.clear();
        is.earn(gain);
        return gain;
    }

    /** Vend les ressources reconnues présentes dans l'inventaire du joueur. */
    public static long sellInventory(ServerPlayer p, Island is) {
        long gain = 0;
        var inv = p.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack s = inv.getItem(i);
            if (s.isEmpty() || s.has(net.minecraft.core.component.DataComponents.CUSTOM_NAME)) continue;
            int pr = price(id(s.getItem()));
            if (pr <= 0) continue;
            gain += (long) pr * s.getCount();
            inv.setItem(i, ItemStack.EMPTY);
        }
        is.earn(gain);
        return gain;
    }

    /** Total stocké, par ressource, dans tous les entrepôts du royaume. */
    public static Map<String, Long> totals(Island is) {
        Map<String, Long> m = new LinkedHashMap<>();
        for (String k : PRICES.keySet()) m.put(k, 0L);
        for (Building b : is.buildings) b.storage.forEach((k, v) -> m.merge(k, v, Long::sum));
        return m;
    }

    public static String fmt(long v) {
        String s = Long.toString(Math.abs(v));
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            if (i > 0 && (s.length() - i) % 3 == 0) out.append(' ');
            out.append(s.charAt(i));
        }
        return (v < 0 ? "-" : "") + out;
    }
}
