package fr.cobbleskyblock.islands;

import com.mojang.authlib.GameProfile;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Unit;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.item.component.ResolvableProfile;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

import fr.cobbleskyblock.islands.IslandMenu.Page;

/** Toutes les pages du menu /royaume. Les positions des boutons suivent les fonds dessinés. */
public final class KingdomMenus {
    private KingdomMenus() {}

    private static IslandManager mgr() { return CobbleIslands.manager(); }

    // icônes du resource pack (papier + custom_model_data)
    static final int I_DOMAIN = 7201, I_BUILD = 7202, I_MARKET = 7203, I_TEAM = 7204, I_UPGRADE = 7205, I_RANK = 7206,
            I_CAPITAL = 7207, I_VISIT = 7208, I_HELP = 7209, I_CLOSE = 7210, I_SETTINGS = 7211, I_BANNER = 7212,
            I_BACK = 7213, I_PREV = 7214, I_NEXT = 7215, I_YES = 7216, I_NO = 7217, I_HARVEST = 7218, I_SELL = 7219,
            I_DEMOLISH = 7220, I_INVITE = 7224, I_LOCKED = 7225, I_EMPTY = 7226, I_FOUND = 7227, I_EXPAND = 7228,
            I_OPEN = 7229, I_CLOSED = 7230, I_SELL_ALL = 7231, I_CROWN = 7232, I_LETTER = 7233;

    static final int GOLD = 0xFFC94D, GREEN = 0x8BE37A, RED = 0xFF7A6B, BLUE = 0x8CC8FF, CREAM = 0xFFF1D0, GRAY = 0xA89C88;

    // ---------- fabrication des boutons ----------

    static ItemStack button(int icon, String name, int color, String... lore) {
        ItemStack s = new ItemStack(Items.PAPER);
        s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(icon));
        return decorate(s, name, color, lore);
    }

    static ItemStack item(Item item, String name, int color, String... lore) {
        return decorate(new ItemStack(item), name, color, lore);
    }

    static ItemStack decorate(ItemStack s, String name, int color, String... lore) {
        s.set(DataComponents.CUSTOM_NAME, Component.literal(name).withStyle(st -> st.withColor(color).withBold(true).withItalic(false)));
        List<Component> lines = new ArrayList<>();
        for (String l : lore) lines.add(Component.literal(l).withStyle(st -> st.withColor(0xC8BBA0).withItalic(false)));
        s.set(DataComponents.LORE, new ItemLore(lines));
        s.set(DataComponents.HIDE_ADDITIONAL_TOOLTIP, Unit.INSTANCE);
        return s;
    }

    static ItemStack glow(ItemStack s) {
        s.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        return s;
    }

    static ItemStack head(GameProfile profile, String name, int color, String... lore) {
        ItemStack s = decorate(new ItemStack(Items.PLAYER_HEAD), name, color, lore);
        s.set(DataComponents.PROFILE, new ResolvableProfile(profile));
        return s;
    }

    static GameProfile profileOf(UUID uuid, String name) {
        ServerPlayer online = mgr().server().getPlayerList().getPlayer(uuid);
        return online != null ? online.getGameProfile() : new GameProfile(uuid, name);
    }

    static void cmd(ServerPlayer p, String command) {
        p.server.getCommands().performPrefixedCommand(p.createCommandSourceStack(), command);
    }

    static String ecus(long v) { return "§6" + Market.fmt(v) + " écus"; }

    private static void closeBtn(IslandMenu m, int slot) {
        m.set(slot, button(I_CLOSE, "Fermer", RED), ServerPlayer::closeContainer);
    }

    private static void backBtn(IslandMenu m, Consumer<ServerPlayer> to) {
        m.set(45, button(I_BACK, "Retour", CREAM, "§7Revenir au menu précédent"), to);
    }

    private static ItemStack infoCard(Island is) {
        int r = mgr().radius(is);
        return glow(button(I_BANNER, is.name, GOLD,
                "§7Seigneur : §f" + is.ownerName(),
                "§7Trésor : " + ecus(is.money),
                "§7Revenu : §a+" + Market.fmt(mgr().incomePerMinute(is)) + " /min",
                "§7Terrain : §f" + (2 * r + 1) + " × " + (2 * r + 1) + " §8(niv. " + is.sizeLevel + ")",
                "§7Bâtiments : §f" + is.buildings.size() + " / " + mgr().maxMachines(is),
                "§7Équipe : §f" + is.members.size() + "/" + mgr().maxMembers(is),
                "§7Rang : §b#" + mgr().rankOf(is)));
    }

    /** Grille des pages « liste » : 4 rangées de 7 cases. */
    static final int[] LIST = new int[28];
    static {
        for (int r = 0, k = 0; r < 4; r++) for (int c = 1; c <= 7; c++) LIST[k++] = 9 + r * 9 + c;
    }

    // ---------- page principale ----------

    static final int I_BLANK = 7299;   // objet transparent : seulement une infobulle sur le dessin

    /** Remplit une zone de cases avec un bouton invisible (le bouton est dessiné dans le fond). */
    private static void zone(IslandMenu m, int row0, int row1, int col0, int col1, ItemStack tip, Consumer<ServerPlayer> action) {
        for (int r = row0; r <= row1; r++)
            for (int c = col0; c <= col1; c++) m.set(r * 9 + c, tip.copy(), action);
    }

    public static void main(ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) { start(p); return; }
        int total = mgr().ranking().size();
        Component title = RoyalGui.mainTitle(
                is.ownerName(),
                Market.fmt(is.money) + " écus",
                "+" + Market.fmt(mgr().incomePerMinute(is)) + " / min",
                "#" + mgr().rankOf(is) + " sur " + total,
                is.members.size() + " / " + mgr().maxMembers(is),
                "Niveau " + is.sizeLevel);
        IslandMenu.open(p, title, m -> {
            zone(m, 0, 1, 0, 8, button(I_BLANK, "Aller à mon royaume", GREEN, "§7Te téléporte sur ton île.", "", "§8Raccourci : §e/royaume go"),
                    pl -> { pl.closeContainer(); cmd(pl, "royaume go"); });
            zone(m, 2, 3, 0, 3, button(I_BLANK, "Bâtiments", CREAM, "§7Achète et gère tes machines :", "§7scierie, ferme, mine, forge.", "",
                    "§f" + is.buildings.size() + "/" + mgr().maxMachines(is) + " §7machines"), KingdomMenus::buildings);
            zone(m, 2, 3, 5, 8, button(I_BLANK, "Améliorer", GREEN, "§7Terrain, nombre de bâtiments", "§7et taille de la cour."), KingdomMenus::domain);
            zone(m, 4, 5, 0, 3, button(I_BLANK, "Membres", BLUE, "§7Ta cour : membres", "§7et invitations.", "",
                    "§f" + is.members.size() + "/" + mgr().maxMembers(is) + " §7membres"), KingdomMenus::team);
            zone(m, 4, 5, 5, 8, button(I_BLANK, "Aller à la capitale", RED, "§7Marché, classement et", "§7autres royaumes.", "",
                    "§8Raccourci : §e/capitale"), pl -> { pl.closeContainer(); cmd(pl, "capitale"); });
        });
    }

    private static void start(ServerPlayer p) {
        IslandManager.Invite inv = mgr().invites.get(p.getUUID());
        boolean invited = inv != null && inv.expires() > System.currentTimeMillis();
        IslandMenu.open(p, Page.START, "Bienvenue, voyageur !", m -> {
            m.set(4, head(p.getGameProfile(), p.getGameProfile().getName(), GOLD, "§7Tu n'as pas encore de royaume."));
            closeBtn(m, 8);
            m.set(21, glow(button(I_FOUND, "Fonder mon royaume", GREEN, "§7Reçois un domaine avec ton", "§7campement et " + ecus(mgr().config().ecusDepart) + "§7.", "", "§aClique pour commencer !")),
                    pl -> { pl.closeContainer(); cmd(pl, "royaume creer"); });
            if (invited) {
                m.set(23, glow(button(I_LETTER, "Invitation de " + inv.from(), GOLD, "§7Rejoindre son royaume.", "", "§aClic : accepter", "§8/royaume refuser pour refuser")),
                        pl -> { pl.closeContainer(); cmd(pl, "royaume accepter"); });
            } else {
                m.set(23, button(I_EMPTY, "Aucune invitation", GRAY, "§7Un ami peut t'inviter avec", "§e/royaume inviter <pseudo>"));
            }
            m.set(39, button(I_CAPITAL, "Capitale", RED, "§7Retourner à la capitale."), pl -> { pl.closeContainer(); cmd(pl, "capitale"); });
            m.set(41, button(I_VISIT, "Visiter", BLUE, "§7Va voir les royaumes existants."), pl -> visit(pl, 0));
        });
    }

    // ---------- bâtiments ----------

    public static void buildings(ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) { start(p); return; }
        int max = mgr().maxMachines(is);
        long stock = 0;
        for (Building b : is.buildings) stock += b.stored();
        int next = mgr().config().machinesCost(is.machineLevel + 1);
        Component title = RoyalGui.listTitle(
                is.buildings.size() + " / " + max,
                "+" + Market.fmt(mgr().incomePerMinute(is)) + " / min",
                Market.fmt(stock),
                Market.fmt(is.money) + " écus",
                next < 0 ? "Maximum" : Market.fmt(next) + " écus",
                is.buildings.size() + " / " + max + " posés");
        IslandMenu.open(p, title, m -> {
            // bâtiments posés : les trois rangées de cases du haut ; un clic ouvre la page du bâtiment
            int k = 0;
            for (Building b : is.buildings) {
                if (k >= 27) break;
                int cap = b.type.capacity(b.level);
                m.set(k++, button(b.type.icon(), b.type.label + " (niv. " + b.level + ")", CREAM,
                        "§7Production : §a" + b.type.rate(b.level) + " /min",
                        "§7Stock : §f" + Market.fmt(b.stored()) + " / " + Market.fmt(cap) + (b.full() ? " §c(plein !)" : ""),
                        "§8Position : " + b.pos.getX() + " " + b.pos.getY() + " " + b.pos.getZ(), "", "§eClic : ouvrir"),
                        pl -> building(pl, b.id));
            }
            // boutique : quatre cases dorées
            int i = 0;
            for (BuildingType t : BuildingType.values()) {
                m.set(37 + 2 * i++, button(t.icon(), "Acheter : " + t.label, GREEN,
                        "§7Prix : " + ecus(t.price), "§7Production : §a" + t.rate(1) + " /min §8(niv. 1)",
                        "§7Stock max : §f" + Market.fmt(t.capacity(1)),
                        "§7Produit : §f" + outputs(t), "", "§7Bâtiments posés : §f" + is.buildings.size() + " / " + max,
                        is.money >= t.price ? "§aClic : acheter (il va dans ton inventaire)" : "§cIl te manque " + Market.fmt(t.price - is.money) + " écus"),
                        pl -> { cmd(pl, "royaume acheter " + t.id); buildings(pl); });
            }
            m.set(45, button(I_BLANK, "Retour", CREAM, "§7Revenir au menu du royaume"), KingdomMenus::main);
            m.set(53, button(I_BLANK, "Fermer", RED), ServerPlayer::closeContainer);
        });
    }

    private static String outputs(BuildingType t) {
        StringBuilder sb = new StringBuilder();
        for (BuildingType.Output o : t.outputs) {
            if (sb.length() > 0) sb.append(", ");
            sb.append(o.asItem().getDescription().getString());
        }
        return sb.toString();
    }

    public static void building(ServerPlayer p, int bid) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) { start(p); return; }
        Building b = is.building(bid);
        if (b == null) { buildings(p); return; }
        BuildingType t = b.type;
        int cap = t.capacity(b.level);
        long value = 0;
        for (Map.Entry<String, Long> e : b.storage.entrySet()) value += e.getValue() * Market.price(e.getKey());
        int cost = t.nextCost(b.level);
        Component title = RoyalGui.buildingTitle(t.id,
                b.level + " / " + BuildingType.MAX_LEVEL,
                "+" + t.rate(b.level) + " / min",
                Market.fmt(b.stored()) + " / " + Market.fmt(cap),
                Market.fmt(value) + " écus",
                cost < 0 ? "Maximum" : Market.fmt(cost) + " écus",
                "Niveau " + b.level);
        IslandMenu.open(p, title, m -> {
            zone(m, 0, 1, 0, 8, button(I_BLANK, "Récupérer le stock", GREEN, "§7Met tout le stock du bâtiment", "§7dans ton inventaire.", "",
                    "§7Stock : §f" + Market.fmt(b.stored()) + " / " + Market.fmt(cap) + (b.full() ? " §c(plein !)" : ""),
                    "§7Vends ensuite avec §e/sell §7ou §e/sellall§7."),
                    pl -> { harvest(pl, is, b); building(pl, bid); });
            if (cost < 0) {
                zone(m, 2, 3, 0, 3, button(I_BLANK, "Niveau maximum", GOLD, "§7Ce bâtiment est au sommet !",
                        "§7Production : §a" + t.rate(b.level) + " /min", "§7Stock max : §f" + Market.fmt(cap)), null);
            } else {
                int nl = b.level + 1;
                List<String> lore = new ArrayList<>();
                lore.add("§7Niveau : §f" + b.level + " §7→ §a" + nl);
                lore.add("§7Production : §f" + t.rate(b.level) + " §7→ §a" + t.rate(nl) + " /min");
                lore.add("§7Stock max : §f" + Market.fmt(cap) + " §7→ §a" + Market.fmt(t.capacity(nl)));
                for (BuildingType.Output o : t.unlocks(nl))
                    lore.add("§7Nouvelle ressource : §b" + o.asItem().getDescription().getString() + " §8(" + Market.price(o.item()) + " écus)");
                lore.add("");
                lore.add("§7Prix : " + ecus(cost));
                lore.add(is.money >= cost ? "§aClic : améliorer" : "§cIl te manque " + Market.fmt(cost - is.money) + " écus");
                zone(m, 2, 3, 0, 3, button(I_BLANK, "Améliorer au niveau " + nl, GREEN, lore.toArray(new String[0])),
                        pl -> {
                            String err = mgr().upgradeBuilding(is, b);
                            pl.sendSystemMessage(err == null ? Msg.ok(t.label + " améliorée au niveau " + b.level + " !") : Msg.err(err));
                            building(pl, bid);
                        });
            }
            zone(m, 2, 3, 5, 8, button(I_BLANK, "Ramasser le bâtiment", RED, "§7Le bâtiment revient dans ton", "§7inventaire et garde son niveau.", "§7Son stock t'est rendu aussi."),
                    pl -> {
                        mgr().pickUp(pl, is, b);
                        pl.sendSystemMessage(Msg.info(t.label + " ramassée : elle est dans ton inventaire."));
                        pl.closeContainer();
                    });
            // contenu du stock : la rangée de cases dessinée (ligne 4)
            int k = 0;
            for (Map.Entry<String, Long> e : b.storage.entrySet()) {
                if (k >= 9 || e.getValue() <= 0) continue;
                Item it = Market.item(e.getKey());
                ItemStack s = item(it, it.getDescription().getString(), CREAM, "§7En stock : §f" + Market.fmt(e.getValue()),
                        "§7Valeur : " + ecus(Market.price(e.getKey())) + " §7l'unité");
                s.setCount((int) Math.max(1, Math.min(64, e.getValue())));
                m.set(36 + k++, s);
            }
            m.set(45, button(I_BLANK, "Retour", CREAM, "§7Revenir à la liste des bâtiments"), KingdomMenus::buildings);
            m.set(53, button(I_BLANK, "Fermer", RED), ServerPlayer::closeContainer);
        });
    }

    /** Ressources produites à ce niveau. */
    private static String outputs(BuildingType t, int level) {
        StringBuilder sb = new StringBuilder();
        for (BuildingType.Output o : t.outputs) {
            if (o.fromLevel() > level) continue;
            if (sb.length() > 0) sb.append(", ");
            sb.append(o.asItem().getDescription().getString());
        }
        return sb.toString();
    }

    private static void harvest(ServerPlayer p, Island is, Building b) {
        int given = 0;
        for (Map.Entry<String, Long> e : b.storage.entrySet()) {
            int max = Market.item(e.getKey()).getDefaultMaxStackSize();
            long left = e.getValue();
            while (left > 0) {
                int n = (int) Math.min(left, max);
                ItemStack s = Market.stack(e.getKey(), n);
                boolean all = p.getInventory().add(s);
                int took = n - s.getCount();
                left -= took; given += took;
                if (!all) break;
            }
            e.setValue(left);
        }
        b.storage.values().removeIf(v -> v <= 0);
        mgr().data().setDirty();
        p.sendSystemMessage(given > 0 ? Msg.ok(given + " ressources récupérées. Vends-les avec /sell ou /sellall.") : Msg.err("Rien à récupérer (ou inventaire plein)."));
    }

    // ---------- marché ----------

    public static void market(ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) { start(p); return; }
        Map<String, Long> totals = Market.inventoryTotals(p);
        IslandMenu.open(p, Page.LIST, "Marché de la capitale", m -> {
            int k = 0;
            long all = 0;
            for (Map.Entry<String, Integer> e : Market.PRICES.entrySet()) {
                if (k >= 28) break;
                long qty = totals.getOrDefault(e.getKey(), 0L);
                all += qty * e.getValue();
                Item it = Market.item(e.getKey());
                String id = e.getKey();
                ItemStack s = item(it, it.getDescription().getString(), qty > 0 ? CREAM : GRAY,
                        "§7Valeur : " + ecus(e.getValue()) + " §7l'unité", "§7Dans ton inventaire : §f" + qty,
                        qty > 0 ? "§aClic : vendre (" + Market.fmt(qty * e.getValue()) + " écus)" : "§8Tu n'en as pas");
                s.setCount((int) Math.max(1, Math.min(64, qty)));
                m.set(LIST[k++], s, qty > 0 ? pl -> {
                    long g = Market.sellInventory(pl, is, id);
                    mgr().data().setDirty();
                    pl.sendSystemMessage(Msg.ok("Vendu pour " + Market.fmt(g) + " écus."));
                    market(pl);
                } : null);
            }
            backBtn(m, KingdomMenus::main);
            m.set(49, glow(button(I_SELL_ALL, "Tout vendre", GOLD, "§7Ton inventaire vaut " + ecus(all) + "§7.", "", "§aClic : tout vendre §8(/sellall)")),
                    pl -> { cmd(pl, "sellall"); market(pl); });
            closeBtn(m, 53);
        });
    }

    // ---------- équipe ----------

    public static void team(ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) { start(p); return; }
        boolean owner = is.isOwner(p.getUUID());
        IslandMenu.open(p, Page.LIST, "Ta cour", m -> {
            int k = 0;
            for (Map.Entry<UUID, String> e : is.members.entrySet()) {
                UUID u = e.getKey();
                String name = e.getValue();
                boolean lord = is.isOwner(u);
                boolean online = mgr().server().getPlayerList().getPlayer(u) != null;
                List<String> lore = new ArrayList<>(List.of(lord ? "§6Seigneur" : "§fVassal", online ? "§aEn ligne" : "§8Hors ligne"));
                if (owner && !lord) { lore.add(""); lore.add("§cClic : bannir du royaume"); }
                ItemStack h = head(profileOf(u, name), name, lord ? GOLD : CREAM, lore.toArray(new String[0]));
                m.set(LIST[k++], lord ? glow(h) : h, owner && !lord ? pl -> confirm(pl, "Bannir " + name + " ?",
                        head(profileOf(u, name), name, CREAM), ok -> { cmd(ok, "royaume exclure " + name); team(ok); }, KingdomMenus::team) : null);
            }
            int free = mgr().maxMembers(is) - is.members.size();
            for (int i = 0; i < free && k < 28; i++)
                m.set(LIST[k++], button(I_INVITE, "Place libre", GREEN, owner ? "§7Invite quelqu'un !" : "§7En attente d'un vassal"),
                        owner ? KingdomMenus::invite : null);
            backBtn(m, KingdomMenus::main);
            if (owner) m.set(49, glow(button(I_INVITE, "Inviter", GREEN, "§7Choisis un joueur en ligne.")), KingdomMenus::invite);
            closeBtn(m, 53);
        });
    }

    private static void invite(ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null || !is.isOwner(p.getUUID())) { main(p); return; }
        IslandMenu.open(p, Page.LIST, "Inviter un joueur", m -> {
            int k = 0;
            for (ServerPlayer t : mgr().server().getPlayerList().getPlayers()) {
                if (k >= 28) break;
                if (t == p || is.isMember(t.getUUID())) continue;
                String name = t.getGameProfile().getName();
                Island other = mgr().islandOf(t.getUUID());
                m.set(LIST[k++], head(t.getGameProfile(), name, CREAM, other == null ? "§7Sans royaume" : "§7A déjà un royaume", "", "§aClic : inviter"),
                        pl -> { cmd(pl, "royaume inviter " + name); team(pl); });
            }
            if (k == 0) m.set(LIST[10], button(I_EMPTY, "Personne à inviter", GRAY, "§7Aucun autre joueur en ligne."));
            backBtn(m, KingdomMenus::team);
            closeBtn(m, 53);
        });
    }

    // ---------- améliorations du domaine ----------

    public static void domain(ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) { start(p); return; }
        boolean owner = is.isOwner(p.getUUID());
        IslandConfig cfg = mgr().config();
        IslandMenu.open(p, Page.DOMAIN, "Améliorer le royaume", m -> {
            m.set(4, infoCard(is));
            closeBtn(m, 8);
            String who = "§8Réservé au seigneur";
            // terrain : seule la bordure s'écarte
            int sc = cfg.sizeCost(is.sizeLevel + 1);
            int r = mgr().radius(is), nr = sc < 0 ? r : cfg.radiusFor(is.sizeLevel + 1);
            m.set(20, sc < 0 ? glow(button(I_EXPAND, "Terrain au maximum", GOLD, "§7" + (2 * r + 1) + " × " + (2 * r + 1) + " blocs"))
                    : button(I_EXPAND, "Agrandir le terrain", GREEN, "§7Niveau : §f" + is.sizeLevel + " §7→ §a" + (is.sizeLevel + 1),
                    "§7Terrain : §f" + (2 * r + 1) + " × " + (2 * r + 1) + " §7→ §a" + (2 * nr + 1) + " × " + (2 * nr + 1) + " blocs",
                    "§8La bordure s'écarte : à toi de bâtir !", "",
                    "§7Prix : " + ecus(sc), owner ? (is.money >= sc ? "§aClic : agrandir" : "§cIl te manque " + Market.fmt(sc - is.money) + " écus") : who),
                    sc < 0 || !owner ? null : pl -> {
                        String err = mgr().upgradeSize(is);
                        pl.sendSystemMessage(err == null ? Msg.ok("Ton terrain s'agrandit : la bordure s'est écartée !") : Msg.err(err));
                        domain(pl);
                    });
            // nombre de bâtiments
            int bc = cfg.machinesCost(is.machineLevel + 1);
            int bm = mgr().maxMachines(is);
            m.set(22, bc < 0 ? glow(button(I_BUILD, "Bâtiments au maximum", GOLD, "§7" + bm + " bâtiments"))
                    : button(I_BUILD, "Plus de bâtiments", GOLD, "§7Niveau : §f" + is.machineLevel + " §7→ §a" + (is.machineLevel + 1),
                    "§7Bâtiments posés : §f" + is.buildings.size() + " / " + bm,
                    "§7Limite : §f" + bm + " §7→ §a" + cfg.machinesFor(is.machineLevel + 1) + " bâtiments", "",
                    "§7Prix : " + ecus(bc), owner ? (is.money >= bc ? "§aClic : améliorer" : "§cIl te manque " + Market.fmt(bc - is.money) + " écus") : who),
                    bc < 0 || !owner ? null : pl -> {
                        String err = mgr().upgradeMachines(is);
                        pl.sendSystemMessage(err == null ? Msg.ok("Tu peux poser plus de bâtiments !") : Msg.err(err));
                        domain(pl);
                    });
            // membres
            int mc = cfg.membersCost(is.memberLevel + 1);
            m.set(24, mc < 0 ? glow(button(I_TEAM, "Cour au maximum", GOLD, "§7" + mgr().maxMembers(is) + " membres"))
                    : button(I_TEAM, "Agrandir la cour", BLUE, "§7Niveau : §f" + is.memberLevel + " §7→ §a" + (is.memberLevel + 1),
                    "§7Membres : §f" + is.members.size() + " / " + mgr().maxMembers(is),
                    "§7Limite : §f" + mgr().maxMembers(is) + " §7→ §a" + cfg.membersFor(is.memberLevel + 1) + " membres", "",
                    "§7Prix : " + ecus(mc), owner ? (is.money >= mc ? "§aClic : améliorer" : "§cIl te manque " + Market.fmt(mc - is.money) + " écus") : who),
                    mc < 0 || !owner ? null : pl -> {
                        String err = mgr().upgradeMembers(is);
                        pl.sendSystemMessage(err == null ? Msg.ok("Ta cour peut accueillir plus de monde !") : Msg.err(err));
                        domain(pl);
                    });
            m.set(39, button(is.open ? I_OPEN : I_CLOSED, is.open ? "Portes ouvertes" : "Portes fermées", is.open ? GREEN : RED,
                    "§7Les autres joueurs " + (is.open ? "§apeuvent" : "§cne peuvent pas"), "§7visiter ton domaine.", "",
                    owner ? "§eClic : changer" : who),
                    owner ? pl -> { cmd(pl, is.open ? "royaume fermer" : "royaume ouvrir"); domain(pl); } : null);
            if (owner) {
                m.set(41, button(I_DEMOLISH, "Abandonner le royaume", RED, "§7Supprime définitivement", "§7ton royaume."),
                        pl -> confirm(pl, "Abandonner le royaume ?", button(I_DEMOLISH, "Attention !", RED, "§7Domaine, bâtiments et trésor", "§7seront perdus §cdéfinitivement§7."),
                                ok -> { ok.closeContainer(); cmd(ok, "royaume supprimer"); cmd(ok, "royaume supprimer confirmer"); }, KingdomMenus::domain));
            } else {
                m.set(41, button(I_BACK, "Quitter le royaume", RED, "§7Quitter le royaume de " + is.ownerName() + "."),
                        pl -> confirm(pl, "Quitter le royaume ?", button(I_BACK, "Quitter", RED),
                                ok -> { ok.closeContainer(); cmd(ok, "royaume quitter"); }, KingdomMenus::domain));
            }
            backBtn(m, KingdomMenus::main);
        });
    }

    // ---------- classement et visites ----------

    public static void ranking(ServerPlayer p, int page) {
        List<Island> all = mgr().ranking();
        int pages = Math.max(1, (all.size() + 27) / 28);
        int pg = Math.max(0, Math.min(page, pages - 1));
        IslandMenu.open(p, Page.LIST, "Classement des royaumes", m -> {
            for (int i = 0; i < 28 && pg * 28 + i < all.size(); i++) {
                Island is = all.get(pg * 28 + i);
                int rank = pg * 28 + i + 1;
                String medal = rank == 1 ? "§6♛ " : rank == 2 ? "§7♛ " : rank == 3 ? "§c♛ " : "§8#" + rank + " ";
                ItemStack h = head(profileOf(is.owner, is.ownerName()), is.name, rank <= 3 ? GOLD : CREAM,
                        medal + "§7Rang " + rank, "§7Fortune gagnée : " + ecus(is.totalEarned), "§7Machines : §f" + is.buildings.size(),
                        "", is.open || is.isMember(p.getUUID()) ? "§eClic : visiter" : "§8Fermé aux visites");
                m.set(LIST[i], rank == 1 ? glow(h) : h, is.open || is.isMember(p.getUUID()) ? pl -> { pl.closeContainer(); mgr().visit(pl, is); } : null);
            }
            if (all.isEmpty()) m.set(LIST[10], button(I_EMPTY, "Aucun royaume", GRAY, "§7Sois le premier !"));
            pager(m, pg, pages, n -> pl -> ranking(pl, n));
            backBtn(m, KingdomMenus::main);
            closeBtn(m, 53);
        });
    }

    public static void visit(ServerPlayer p, int page) {
        List<Island> open = new ArrayList<>();
        for (Island is : mgr().ranking()) if (is.open || is.isMember(p.getUUID())) open.add(is);
        int pages = Math.max(1, (open.size() + 27) / 28);
        int pg = Math.max(0, Math.min(page, pages - 1));
        IslandMenu.open(p, Page.LIST, "Visiter un royaume", m -> {
            for (int i = 0; i < 28 && pg * 28 + i < open.size(); i++) {
                Island is = open.get(pg * 28 + i);
                boolean mine = is.isMember(p.getUUID());
                m.set(LIST[i], head(profileOf(is.owner, is.ownerName()), is.name, mine ? GREEN : CREAM,
                        "§7Seigneur : §f" + is.ownerName(), "§7Machines : §f" + is.buildings.size(), "", mine ? "§aC'est ton royaume !" : "§eClic : visiter"),
                        pl -> { pl.closeContainer(); mgr().visit(pl, is); });
            }
            if (open.isEmpty()) m.set(LIST[10], button(I_EMPTY, "Aucun royaume ouvert", GRAY, "§7Reviens plus tard !"));
            pager(m, pg, pages, n -> pl -> visit(pl, n));
            backBtn(m, pl -> main(pl));
            closeBtn(m, 53);
        });
    }

    private static void pager(IslandMenu m, int pg, int pages, java.util.function.IntFunction<Consumer<ServerPlayer>> go) {
        if (pg > 0) m.set(48, button(I_PREV, "Page précédente", CREAM), go.apply(pg - 1));
        m.set(49, button(I_RANK, "Page " + (pg + 1) + "/" + pages, GOLD));
        if (pg < pages - 1) m.set(50, button(I_NEXT, "Page suivante", CREAM), go.apply(pg + 1));
    }

    // ---------- confirmation ----------

    static void confirm(ServerPlayer p, String title, ItemStack info, Consumer<ServerPlayer> yes, Consumer<ServerPlayer> no) {
        IslandMenu.open(p, Page.CONFIRM, title, m -> {
            m.set(13, glow(info));
            m.set(29, glow(button(I_YES, "Confirmer", GREEN)), yes);
            m.set(33, button(I_NO, "Annuler", RED), no);
        });
    }

    static ChatFormatting unused() { return ChatFormatting.RESET; }
}
