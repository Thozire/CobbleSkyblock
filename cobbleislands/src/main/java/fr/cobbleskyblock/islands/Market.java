package fr.cobbleskyblock.islands;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.component.ItemLore;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
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
        PRICES.put("minecraft:copper_ingot", 10);
        PRICES.put("minecraft:iron_ingot", 18);
        PRICES.put("minecraft:gold_ingot", 32);
    }

    public static int price(String item) { return PRICES.getOrDefault(item, 0); }

    public static Item item(String id) { return BuiltInRegistries.ITEM.get(ResourceLocation.parse(id)); }

    public static String id(Item item) { return BuiltInRegistries.ITEM.getKey(item).toString(); }

    /** Prix d'une pile : 0 si l'objet n'est pas vendable (objets renommés, bâtiments, objets sans prix). */
    public static int priceOf(ItemStack s) {
        if (s.isEmpty() || s.has(DataComponents.CUSTOM_NAME) || s.has(DataComponents.CUSTOM_DATA)) return 0;
        return price(id(s.getItem()));
    }

    /** Ressource sortie d'un bâtiment : sa description indique son prix et comment la vendre. */
    public static ItemStack stack(String itemId, int count) {
        ItemStack s = new ItemStack(item(itemId), count);
        int pr = price(itemId);
        if (pr <= 0) return s;
        List<Component> lore = new ArrayList<>();
        lore.add(Component.literal("Ressource du royaume").withStyle(st -> st.withColor(0x9A9080).withItalic(false)));
        lore.add(Component.literal(""));
        lore.add(Component.literal("Valeur : ").withStyle(st -> st.withColor(0xFFF1D0).withItalic(false))
                .append(Component.literal(fmt(pr) + " écu" + (pr > 1 ? "s" : "")).withStyle(st -> st.withColor(0xFFAA00).withItalic(false)))
                .append(Component.literal(" l'unité").withStyle(st -> st.withColor(0x9A9080).withItalic(false))));
        lore.add(Component.literal(""));
        lore.add(Component.literal("Vends l'objet en main avec ").withStyle(st -> st.withColor(0xFFF1D0).withItalic(false))
                .append(Component.literal("/sell").withStyle(st -> st.withColor(0xFFE14D).withItalic(false))));
        lore.add(Component.literal("ou tout ton inventaire avec ").withStyle(st -> st.withColor(0xFFF1D0).withItalic(false))
                .append(Component.literal("/sellall").withStyle(st -> st.withColor(0xFFE14D).withItalic(false))));
        s.set(DataComponents.LORE, new ItemLore(lore));
        return s;
    }

    /** Vend la pile tenue en main. Renvoie le gain (0 si elle n'est pas vendable). */
    public static long sellHand(ServerPlayer p, Island is) {
        ItemStack s = p.getMainHandItem();
        long gain = (long) priceOf(s) * s.getCount();
        if (gain <= 0) return 0;
        p.getInventory().setItem(p.getInventory().selected, ItemStack.EMPTY);
        is.earn(gain);
        return gain;
    }

    /** Vend tout ce qui est vendable dans l'inventaire (ou seulement la ressource `only`). Renvoie le gain. */
    public static long sellInventory(ServerPlayer p, Island is, String only) {
        long gain = 0;
        var inv = p.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack s = inv.getItem(i);
            int pr = priceOf(s);
            if (pr <= 0 || (only != null && !only.equals(id(s.getItem())))) continue;
            gain += (long) pr * s.getCount();
            inv.setItem(i, ItemStack.EMPTY);
        }
        is.earn(gain);
        return gain;
    }

    public static long sellInventory(ServerPlayer p, Island is) { return sellInventory(p, is, null); }

    /** Quantité vendable de chaque ressource dans l'inventaire du joueur. */
    public static Map<String, Long> inventoryTotals(ServerPlayer p) {
        Map<String, Long> m = new LinkedHashMap<>();
        for (String k : PRICES.keySet()) m.put(k, 0L);
        var inv = p.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack s = inv.getItem(i);
            if (priceOf(s) > 0) m.merge(id(s.getItem()), (long) s.getCount(), Long::sum);
        }
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
