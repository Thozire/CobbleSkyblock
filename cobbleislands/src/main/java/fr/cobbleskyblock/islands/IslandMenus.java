package fr.cobbleskyblock.islands;

import com.mojang.authlib.GameProfile;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.Unit;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.item.component.ResolvableProfile;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Les pages du menu /ile. */
public final class IslandMenus {
    private IslandMenus() {}

    private static IslandManager mgr() { return CobbleIslands.manager(); }

    // ---------- fabrication des icônes ----------

    private static Item item(String id, Item fallback) {
        Item it = BuiltInRegistries.ITEM.get(ResourceLocation.parse(id));
        return it == Items.AIR ? fallback : it;
    }

    /** Icône avec un nom coloré et une description. Les lignes acceptent les codes §. */
    static ItemStack icon(Item item, String name, int color, String... lore) {
        ItemStack s = new ItemStack(item);
        s.set(DataComponents.CUSTOM_NAME, Component.literal(name).withStyle(st -> st.withColor(color).withBold(true).withItalic(false)));
        List<Component> lines = new ArrayList<>();
        for (String l : lore) lines.add(Component.literal(l).withStyle(st -> st.withColor(0xA9A1BF).withItalic(false)));
        s.set(DataComponents.LORE, new ItemLore(lines));
        s.set(DataComponents.HIDE_ADDITIONAL_TOOLTIP, Unit.INSTANCE);
        return s;
    }

    static ItemStack glow(ItemStack s) {
        s.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        return s;
    }

    static ItemStack head(GameProfile profile, String name, int color, String... lore) {
        ItemStack s = icon(Items.PLAYER_HEAD, name, color, lore);
        s.set(DataComponents.PROFILE, new ResolvableProfile(profile));
        return s;
    }

    static GameProfile profileOf(UUID uuid, String name) {
        ServerPlayer online = mgr().server().getPlayerList().getPlayer(uuid);
        return online != null ? online.getGameProfile() : new GameProfile(uuid, name);
    }

    private static void cmd(ServerPlayer p, String command) {
        p.server.getCommands().performPrefixedCommand(p.createCommandSourceStack(), command);
    }

    private static final int PURPLE = 0xD65CF0, GREEN = 0x5EE0A0, AQUA = 0x5AD7FF, GOLD = 0xFFC857, RED = 0xFF6B7A, WHITE = 0xF3E8FF;

    private static void back(IslandMenu m, Runnable r) {
        m.set(45, icon(Items.ARROW, "◀ Retour", WHITE, "§7Revenir au menu précédent"), p -> r.run());
    }

    private static void close(IslandMenu m) {
        m.set(49, icon(Items.BARRIER, "Fermer", RED), ServerPlayer::closeContainer);
    }

    // ---------- page principale ----------

    public static void main(ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) { noIsland(p); return; }
        boolean owner = is.isOwner(p.getUUID());
        int r = mgr().radius(is);
        IslandMenu.open(p, "Mon île", m -> {
            m.set(4, glow(head(p.getGameProfile(), "Île de " + is.ownerName(), PURPLE,
                    "§7Taille : §f" + (2 * r + 1) + "×" + (2 * r + 1) + " §8(niveau " + is.sizeLevel + ")",
                    "§7Équipe : §f" + is.members.size() + "/" + mgr().maxMembers(is),
                    "§7Visites : " + (is.open ? "§aouvertes" : "§cfermées"),
                    "§7Ton rôle : " + (owner ? "§6Chef" : "§fMembre"))));

            m.set(20, glow(icon(Items.GRASS_BLOCK, "Aller sur mon île", GREEN, "§7Te téléporte sur ton île.", "", "§8Raccourci : §b/ile go")),
                    pl -> { pl.closeContainer(); cmd(pl, "ile go"); });
            m.set(22, icon(item("cobblemon:poke_ball", Items.ENDER_PEARL), "Mon équipe", AQUA,
                    "§7Membres, invitations", "§7et gestion de l'équipe.", "", "§f" + is.members.size() + "/" + mgr().maxMembers(is) + " §7membres"),
                    IslandMenus::team);
            m.set(24, icon(Items.COMPASS, "Visiter des îles", GOLD, "§7Découvre les îles", "§7des autres joueurs."),
                    pl -> visit(pl, 0));

            m.set(29, icon(is.open ? Items.LIME_DYE : Items.GRAY_DYE, "Visites : " + (is.open ? "ouvertes" : "fermées"), is.open ? GREEN : RED,
                    owner ? "§7Clique pour " + (is.open ? "§cfermer" : "§aouvrir") + " §7ton île" : "§7Seul le chef peut changer ça.", "§7aux visiteurs."),
                    owner ? pl -> { cmd(pl, is.open ? "ile fermer" : "ile ouvrir"); main(pl); } : null);
            m.set(31, icon(Items.EXPERIENCE_BOTTLE, "Améliorations", PURPLE, "§7Agrandir l'île et l'équipe."), IslandMenus::upgrades);
            m.set(33, icon(item("cobblemon:healing_machine", Items.BEACON), "Spawn", WHITE, "§7Retourner au spawn :", "§7centre Pokémon et machine à fusion."),
                    pl -> { pl.closeContainer(); cmd(pl, "spawn"); });

            if (owner) {
                m.set(39, icon(Items.RED_BED, "Point d'arrivée", WHITE, "§7Place le point d'arrivée", "§7de l'île là où tu te trouves."),
                        pl -> { pl.closeContainer(); cmd(pl, "ile sethome"); });
                m.set(41, icon(Items.TNT, "Supprimer l'île", RED, "§7Supprime définitivement", "§7ton île et tout son contenu."), IslandMenus::confirmDelete);
            } else {
                m.set(41, icon(Items.OAK_DOOR, "Quitter l'île", RED, "§7Quitter l'île de " + is.ownerName() + "."), IslandMenus::confirmLeave);
            }
            m.set(45, icon(Items.BOOK, "Aide", WHITE, "§b/ile §7: ce menu", "§b/ile go §7: aller sur ton île", "§b/ile inviter <joueur>", "§b/ile visiter <joueur>", "§b/spawn §7: le spawn"));
            close(m);
        });
    }

    private static void noIsland(ServerPlayer p) {
        IslandManager.Invite inv = mgr().invites.get(p.getUUID());
        boolean invited = inv != null && inv.expires() > System.currentTimeMillis();
        IslandMenu.open(p, "Bienvenue !", m -> {
            m.set(4, head(p.getGameProfile(), p.getGameProfile().getName(), PURPLE, "§7Tu n'as pas encore d'île."));
            m.set(22, glow(icon(Items.GRASS_BLOCK, "Créer mon île", GREEN, "§7Une île de départ Cobblemon", "§7rien que pour toi (et tes potes).", "", "§aClique pour commencer !")),
                    pl -> { pl.closeContainer(); cmd(pl, "ile creer"); });
            if (invited) {
                m.set(30, glow(icon(Items.LIME_CONCRETE, "Accepter l'invitation", GREEN, "§7Rejoindre l'île de §f" + inv.from())),
                        pl -> { pl.closeContainer(); cmd(pl, "ile accepter"); });
                m.set(32, icon(Items.RED_CONCRETE, "Refuser l'invitation", RED, "§7de §f" + inv.from()),
                        pl -> { cmd(pl, "ile refuser"); main(pl); });
            }
            m.set(40, icon(Items.COMPASS, "Visiter des îles", GOLD, "§7Va voir ce que font les autres."), pl -> visit(pl, 0));
            m.set(38, icon(item("cobblemon:healing_machine", Items.BEACON), "Spawn", WHITE, "§7Retourner au spawn."),
                    pl -> { pl.closeContainer(); cmd(pl, "spawn"); });
            close(m);
        });
    }

    // ---------- équipe ----------

    public static void team(ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) { main(p); return; }
        boolean owner = is.isOwner(p.getUUID());
        IslandMenu.open(p, "Mon équipe", m -> {
            int[] slots = {10, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25};
            int i = 0;
            for (Map.Entry<UUID, String> e : is.members.entrySet()) {
                if (i >= slots.length) break;
                UUID u = e.getKey();
                String name = e.getValue();
                boolean isOwner = is.isOwner(u);
                boolean online = mgr().server().getPlayerList().getPlayer(u) != null;
                List<String> lore = new ArrayList<>(List.of(isOwner ? "§6Chef de l'île" : "§fMembre", online ? "§aEn ligne" : "§8Hors ligne"));
                if (owner && !isOwner) { lore.add(""); lore.add("§cClique pour exclure"); }
                ItemStack h = head(profileOf(u, name), name, isOwner ? GOLD : WHITE, lore.toArray(new String[0]));
                m.set(slots[i++], isOwner ? glow(h) : h, owner && !isOwner ? pl -> confirmKick(pl, u, name) : null);
            }
            int free = mgr().maxMembers(is) - is.members.size();
            for (int k = 0; k < free && i < slots.length; k++, i++) {
                m.set(slots[i], icon(Items.LIGHT_GRAY_STAINED_GLASS_PANE, "Place libre", 0x8A8399, owner ? "§7Invite quelqu'un !" : "§7En attente d'un joueur"),
                        owner ? IslandMenus::invite : null);
            }
            if (owner) {
                m.set(40, glow(icon(Items.WRITABLE_BOOK, "Inviter un joueur", GREEN, "§7Choisis un joueur en ligne", "§7à inviter sur ton île.",
                        "", "§f" + is.members.size() + "/" + mgr().maxMembers(is) + " §7membres")), IslandMenus::invite);
            }
            back(m, () -> main(p));
            close(m);
        });
    }

    private static void invite(ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null || !is.isOwner(p.getUUID())) { main(p); return; }
        IslandMenu.open(p, "Inviter un joueur", m -> {
            int slot = 10;
            for (ServerPlayer t : mgr().server().getPlayerList().getPlayers()) {
                if (slot > 43) break;
                if (t == p || is.isMember(t.getUUID())) continue;
                Island other = mgr().islandOf(t.getUUID());
                String name = t.getGameProfile().getName();
                m.set(slot, head(t.getGameProfile(), name, WHITE, other == null ? "§7Sans île" : "§7A déjà une île", "", "§aClique pour l'inviter"),
                        pl -> { cmd(pl, "ile inviter " + name); team(pl); });
                slot = (slot % 9 == 7) ? slot + 3 : slot + 1;
            }
            if (slot == 10) m.set(22, icon(Items.STRUCTURE_VOID, "Personne à inviter", 0x8A8399, "§7Aucun autre joueur en ligne."));
            back(m, () -> team(p));
            close(m);
        });
    }

    private static void confirmKick(ServerPlayer p, UUID uuid, String name) {
        IslandMenu.open(p, "Exclure " + name + " ?", m -> {
            m.set(4, head(profileOf(uuid, name), name, WHITE));
            m.set(29, glow(icon(Items.RED_CONCRETE, "Oui, exclure " + name, RED, "§7Il sera renvoyé au spawn.")),
                    pl -> { cmd(pl, "ile exclure " + name); team(pl); });
            m.set(33, icon(Items.LIME_CONCRETE, "Non, annuler", GREEN), IslandMenus::team);
        });
    }

    // ---------- visites ----------

    public static void visit(ServerPlayer p, int page) {
        List<Island> open = new ArrayList<>();
        for (Island is : mgr().data().islands.values()) if (is.open || is.isMember(p.getUUID())) open.add(is);
        open.sort((a, b) -> Integer.compare(b.members.size(), a.members.size()));
        int perPage = 28, pages = Math.max(1, (open.size() + perPage - 1) / perPage);
        int pg = Math.max(0, Math.min(page, pages - 1));
        IslandMenu.open(p, "Visiter des îles", m -> {
            int[] slots = new int[perPage];
            for (int r = 0, k = 0; r < 4; r++) for (int c = 1; c <= 7; c++) slots[k++] = 9 + r * 9 + c;
            for (int i = 0; i < perPage && pg * perPage + i < open.size(); i++) {
                Island is = open.get(pg * perPage + i);
                int r = mgr().radius(is);
                boolean mine = is.isMember(p.getUUID());
                m.set(slots[i], head(profileOf(is.owner, is.ownerName()), "Île de " + is.ownerName(), mine ? GREEN : GOLD,
                        "§7Équipe : §f" + is.members.size() + " joueur" + (is.members.size() > 1 ? "s" : ""),
                        "§7Taille : §f" + (2 * r + 1) + "×" + (2 * r + 1), "", mine ? "§aC'est ton île !" : "§eClique pour visiter"),
                        pl -> { pl.closeContainer(); mgr().visit(pl, is); });
            }
            if (open.isEmpty()) m.set(22, icon(Items.STRUCTURE_VOID, "Aucune île ouverte", 0x8A8399, "§7Reviens plus tard !"));
            if (pg > 0) m.set(48, icon(Items.SPECTRAL_ARROW, "Page précédente", WHITE), pl -> visit(pl, pg - 1));
            if (pg < pages - 1) m.set(50, icon(Items.SPECTRAL_ARROW, "Page suivante", WHITE), pl -> visit(pl, pg + 1));
            back(m, () -> main(p));
            close(m);
        });
    }

    // ---------- améliorations ----------

    private static void upgrades(ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) { main(p); return; }
        IslandConfig cfg = mgr().config();
        IslandMenu.open(p, "Améliorations", m -> {
            m.set(10, icon(Items.GRASS_BLOCK, "Taille de l'île", GREEN, "§7Agrandit la zone où tu peux construire."));
            for (int lvl = 1; lvl <= cfg.taillesParNiveau.length && lvl <= 7; lvl++) {
                int w = 2 * cfg.taillesParNiveau[lvl - 1] + 1;
                boolean have = lvl <= is.sizeLevel;
                ItemStack s = icon(have ? Items.LIME_STAINED_GLASS_PANE : Items.GRAY_STAINED_GLASS_PANE,
                        "Niveau " + lvl, have ? GREEN : 0x8A8399, "§7" + w + "×" + w + " blocs", have ? "§aDébloqué" : "§8Verrouillé");
                m.set(10 + lvl, lvl == is.sizeLevel ? glow(s) : s);
            }
            m.set(28, icon(item("cobblemon:poke_ball", Items.ENDER_PEARL), "Taille de l'équipe", AQUA, "§7Plus de joueurs sur ton île."));
            for (int lvl = 1; lvl <= cfg.membresParNiveau.length && lvl <= 7; lvl++) {
                boolean have = lvl <= is.memberLevel;
                ItemStack s = icon(have ? Items.LIGHT_BLUE_STAINED_GLASS_PANE : Items.GRAY_STAINED_GLASS_PANE,
                        "Niveau " + lvl, have ? AQUA : 0x8A8399, "§7" + cfg.membresParNiveau[lvl - 1] + " membres", have ? "§aDébloqué" : "§8Verrouillé");
                m.set(28 + lvl, lvl == is.memberLevel ? glow(s) : s);
            }
            m.set(40, icon(Items.CLOCK, "Bientôt", GOLD, "§7Les améliorations s'achèteront", "§7bientôt en jeu. Pour l'instant,", "§7demande à un admin !"));
            back(m, () -> main(p));
            close(m);
        });
    }

    // ---------- confirmations ----------

    private static void confirmDelete(ServerPlayer p) {
        IslandMenu.open(p, "Supprimer l'île ?", m -> {
            m.set(13, glow(icon(Items.TNT, "Attention !", RED, "§7Ton île et tout ce qu'elle contient", "§7seront perdus §cdéfinitivement§7.")));
            m.set(29, icon(Items.RED_CONCRETE, "Oui, supprimer", RED, "§7Action définitive."),
                    pl -> { pl.closeContainer(); cmd(pl, "ile supprimer"); cmd(pl, "ile supprimer confirmer"); });
            m.set(33, glow(icon(Items.LIME_CONCRETE, "Non, garder mon île", GREEN)), IslandMenus::main);
        });
    }

    private static void confirmLeave(ServerPlayer p) {
        IslandMenu.open(p, "Quitter l'île ?", m -> {
            m.set(29, icon(Items.RED_CONCRETE, "Oui, quitter", RED, "§7Tu seras renvoyé au spawn."),
                    pl -> { pl.closeContainer(); cmd(pl, "ile quitter"); });
            m.set(33, glow(icon(Items.LIME_CONCRETE, "Non, rester", GREEN)), IslandMenus::main);
        });
    }
}
