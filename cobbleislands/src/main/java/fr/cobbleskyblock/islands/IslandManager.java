package fr.cobbleskyblock.islands;

import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundInitializeBorderPacket;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.level.border.WorldBorder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;

/** Logique des royaumes : grille des domaines, création, bâtiments, production, équipe. */
public class IslandManager {
    public static final ResourceKey<Level> ISLANDS = ResourceKey.create(Registries.DIMENSION,
            ResourceLocation.fromNamespaceAndPath("cobbleislands", "iles"));
    private static final int COLUMNS = 50;

    public record Invite(int islandId, String from, long expires) {}

    private final MinecraftServer server;
    private final IslandConfig cfg;
    private final Random rnd = new Random();
    public final Map<UUID, Invite> invites = new HashMap<>();
    public final Map<UUID, Long> pendingDelete = new HashMap<>();

    public IslandManager(MinecraftServer server, IslandConfig cfg) {
        this.server = server;
        this.cfg = cfg;
    }

    public IslandData data() { return IslandData.get(server); }

    public ServerLevel islandsLevel() { return server.getLevel(ISLANDS); }

    public Island islandOf(UUID player) { return data().byPlayer.get(player); }

    public MinecraftServer server() { return server; }

    public IslandConfig config() { return cfg; }

    // ---------- grille ----------

    public BlockPos center(int id) {
        int col = (id - 1) % COLUMNS, row = (id - 1) / COLUMNS;
        return new BlockPos(col * cfg.espacement, cfg.hauteur, row * cfg.espacement);
    }

    public Island islandAt(BlockPos pos) {
        int col = Math.round((float) pos.getX() / cfg.espacement);
        int row = Math.round((float) pos.getZ() / cfg.espacement);
        if (col < 0 || col >= COLUMNS || row < 0) return null;
        return data().islands.get(row * COLUMNS + col + 1);
    }

    /** Zone constructible : le rayon de l'île plus une marge (pour les ponts et balcons). */
    public int buildRadius(Island is) { return cfg.radiusFor(is.sizeLevel) + cfg.marge; }

    public boolean inBounds(Island is, BlockPos pos) {
        BlockPos c = center(is.id);
        int r = buildRadius(is);
        return Math.abs(pos.getX() - c.getX()) <= r && Math.abs(pos.getZ() - c.getZ()) <= r;
    }

    public int maxMachines(Island is) { return cfg.machinesFor(is.sizeLevel); }

    public int maxMembers(Island is) { return cfg.membersFor(is.memberLevel); }

    public int radius(Island is) { return cfg.radiusFor(is.sizeLevel); }

    // ---------- création ----------

    private static long seedOf(Island is) { return is.id * 0x9E3779B97F4A7C15L + 12345L; }

    public String create(ServerPlayer player) {
        IslandData d = data();
        if (d.byPlayer.containsKey(player.getUUID())) return "Tu as déjà un royaume : /royaume go";
        ServerLevel level = islandsLevel();
        if (level == null) return "La dimension des îles n'est pas chargée (redémarre le serveur).";
        int id = d.nextId++;
        BlockPos c = center(id);
        Island is = new Island(id, player.getUUID(), player.getGameProfile().getName());
        IslandGen.generate(level, c, 0, cfg.radiusFor(1), seedOf(is));
        level.setBlock(c.below(), Blocks.GRASS_BLOCK.defaultBlockState(), Block.UPDATE_CLIENTS);
        for (int y = 0; y < 3; y++) level.setBlock(c.above(y), Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
        is.home = c;
        is.open = cfg.visitesOuvertesParDefaut;
        is.money = cfg.ecusDepart;
        d.islands.put(id, is);
        d.byPlayer.put(player.getUUID(), is);
        d.setDirty();
        teleportHome(player, is);
        give(player, machineItem(BuildingType.SCIERIE, 1));
        return null;
    }

    // ---------- téléportations ----------

    public void teleportHome(ServerPlayer p, Island is) {
        BlockPos h = is.home;
        p.teleportTo(islandsLevel(), h.getX() + 0.5, h.getY(), h.getZ() + 0.5, 180f, 0f);
        p.setRespawnPosition(ISLANDS, h, 180f, true, false);
    }

    public void visit(ServerPlayer p, Island is) {
        BlockPos h = is.home;
        p.teleportTo(islandsLevel(), h.getX() + 0.5, h.getY(), h.getZ() + 0.5, 180f, 0f);
        p.sendSystemMessage(Msg.ok(is.isMember(p.getUUID()) ? "Bienvenue chez toi, seigneur." : "Bienvenue dans le " + is.name + " !"));
    }

    public void teleportSpawn(ServerPlayer p) {
        ServerLevel ow = server.overworld();
        IslandData d = data();
        BlockPos s = d.spawnBuilt ? new BlockPos(d.spawnX, d.spawnY, d.spawnZ) : ow.getSharedSpawnPos();
        p.teleportTo(ow, s.getX() + 0.5, s.getY(), s.getZ() + 0.5, 180f, 0f);
    }

    // ---------- équipe ----------

    public void join(ServerPlayer p, Island is) {
        is.members.put(p.getUUID(), p.getGameProfile().getName());
        data().byPlayer.put(p.getUUID(), is);
        data().setDirty();
    }

    public void removeMember(Island is, UUID u) {
        is.members.remove(u);
        data().byPlayer.remove(u);
        data().setDirty();
        ServerPlayer p = server.getPlayerList().getPlayer(u);
        if (p != null) {
            p.setRespawnPosition(Level.OVERWORLD, null, 0f, false, false);
            if (p.level().dimension() == ISLANDS && islandAt(p.blockPosition()) == is) teleportSpawn(p);
        }
    }

    public void delete(Island is) {
        ServerLevel level = islandsLevel();
        if (level != null) for (Building b : is.buildings) MachineEntities.remove(level, b);
        for (UUID u : is.members.keySet().toArray(new UUID[0])) removeMember(is, u);
        data().islands.remove(is.id);
        data().setDirty();
    }

    public void broadcast(Island is, net.minecraft.network.chat.Component msg) {
        for (UUID u : is.members.keySet()) {
            ServerPlayer m = server.getPlayerList().getPlayer(u);
            if (m != null) m.sendSystemMessage(msg);
        }
    }

    public boolean anyOnline(Island is) {
        for (UUID u : is.members.keySet()) if (server.getPlayerList().getPlayer(u) != null) return true;
        return false;
    }

    // ---------- améliorations du domaine ----------

    public String upgradeSize(Island is) {
        int next = is.sizeLevel + 1;
        int cost = cfg.sizeCost(next);
        if (cost < 0) return "Ton domaine est déjà au niveau maximum.";
        if (is.money < cost) return "Il te manque " + Market.fmt(cost - is.money) + " écus.";
        int from = cfg.radiusFor(is.sizeLevel);
        is.money -= cost;
        is.sizeLevel = next;
        IslandGen.generate(islandsLevel(), center(is.id), from, cfg.radiusFor(next), seedOf(is));
        data().setDirty();
        return null;
    }

    /** Agrandit l'île jusqu'au rayon de son niveau actuel (commande admin). */
    public void growIsland(Island is, int fromRadius) {
        IslandGen.generate(islandsLevel(), center(is.id), fromRadius, cfg.radiusFor(is.sizeLevel), seedOf(is));
    }

    public String upgradeMembers(Island is) {
        int next = is.memberLevel + 1;
        int cost = cfg.membersCost(next);
        if (cost < 0) return "Ton équipe est déjà au niveau maximum.";
        if (is.money < cost) return "Il te manque " + Market.fmt(cost - is.money) + " écus.";
        is.money -= cost;
        is.memberLevel = next;
        data().setDirty();
        return null;
    }

    // ---------- machines ----------

    public static final String MACHINE_KEY = "royaumes_machine";

    /** Objet « machine » à poser (papier + modèle 3D), avec son type et son niveau. */
    public static ItemStack machineItem(BuildingType t, int level) {
        ItemStack s = new ItemStack(Items.PAPER);
        s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(t.icon()));
        s.set(DataComponents.CUSTOM_NAME, Component.literal(t.label + (level > 1 ? " (niv. " + level + ")" : ""))
                .withStyle(st -> st.withColor(0xFFC94D).withBold(true).withItalic(false)));
        List<Component> lore = new ArrayList<>();
        lore.add(Component.literal("Machine de ton royaume").withStyle(st -> st.withColor(0xC8BBA0).withItalic(false)));
        lore.add(Component.literal("Production : " + t.rate(level) + " /min").withStyle(st -> st.withColor(0x8BE37A).withItalic(false)));
        lore.add(Component.literal(""));
        lore.add(Component.literal("Clic droit sur ton île pour la poser").withStyle(st -> st.withColor(0xFFF1D0).withItalic(false)));
        s.set(DataComponents.LORE, new ItemLore(lore));
        CompoundTag tag = new CompoundTag();
        tag.putString(MACHINE_KEY, t.id);
        tag.putInt("level", level);
        s.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        s.set(DataComponents.MAX_STACK_SIZE, 1);
        return s;
    }

    /** Type de machine porté par un objet, ou null. */
    public static BuildingType machineOf(ItemStack s) {
        CustomData cd = s.get(DataComponents.CUSTOM_DATA);
        if (cd == null) return null;
        CompoundTag t = cd.copyTag();
        return t.contains(MACHINE_KEY) ? BuildingType.byName(t.getString(MACHINE_KEY)) : null;
    }

    public static int machineLevel(ItemStack s) {
        CustomData cd = s.get(DataComponents.CUSTOM_DATA);
        return cd == null ? 1 : Math.max(1, Math.min(BuildingType.MAX_LEVEL, cd.copyTag().getInt("level")));
    }

    public static void give(ServerPlayer p, ItemStack s) {
        if (!p.getInventory().add(s)) p.drop(s, false);
    }

    public String buyMachine(ServerPlayer p, BuildingType t) {
        Island is = islandOf(p.getUUID());
        if (is == null) return "Tu n'as pas de royaume.";
        if (is.money < t.price) return "Il te manque " + Market.fmt(t.price - is.money) + " écus.";
        is.money -= t.price;
        data().setDirty();
        give(p, machineItem(t, 1));
        return null;
    }

    /** Pose une machine (objet en main) au bloc pos, façade vers le joueur. */
    public String placeMachine(ServerPlayer p, ItemStack stack, BlockPos pos) {
        BuildingType t = machineOf(stack);
        if (t == null) return "Objet invalide.";
        ServerLevel level = islandsLevel();
        if (p.level() != level) return "Les machines se posent sur ton île (/royaume go).";
        Island is = islandOf(p.getUUID());
        if (is == null) return "Tu n'as pas de royaume.";
        if (islandAt(pos) != is || !inBounds(is, pos)) return "Pose-la sur ton île.";
        if (!level.getBlockState(pos).canBeReplaced()) return "Il n'y a pas la place ici.";
        if (level.getBlockState(pos.below()).isAir()) return "Une machine doit être posée sur le sol.";
        if (is.machineAt(pos) != null) return "Il y a déjà une machine ici.";
        if (is.buildings.size() >= maxMachines(is))
            return "Limite atteinte (" + maxMachines(is) + " machines) : agrandis ton île pour en poser plus.";
        float yaw = p.getDirection().getOpposite().toYRot();
        Building b = new Building(is.nextBuildingId++, t, pos.immutable(), yaw);
        b.level = machineLevel(stack);
        MachineEntities.spawn(level, b);
        is.buildings.add(b);
        if (!p.isCreative()) stack.shrink(1);
        level.playSound(null, pos, SoundEvents.WOOD_PLACE, SoundSource.BLOCKS, 1f, 0.8f);
        data().setDirty();
        return null;
    }

    /** Ramasse une machine : son stock est vendu, l'objet (avec son niveau) revient au joueur. */
    public long pickUp(ServerPlayer p, Island is, Building b) {
        long gain = Market.sellBuilding(is, b);
        MachineEntities.remove(islandsLevel(), b);
        is.buildings.remove(b);
        data().setDirty();
        give(p, machineItem(b.type, b.level));
        return gain;
    }

    /** Une machine a perdu son bloc (opérateur en créatif) : on la retire proprement. */
    public void machineBroken(ServerLevel level, BlockPos pos) {
        Island is = islandAt(pos);
        Building b = is == null ? null : is.machineAt(pos);
        if (b == null) return;
        MachineEntities.remove(level, b);
        is.buildings.remove(b);
        data().setDirty();
    }

    public String upgradeBuilding(Island is, Building b) {
        int cost = b.type.nextCost(b.level);
        if (cost < 0) return "Cette machine est déjà au niveau maximum.";
        if (is.money < cost) return "Il te manque " + Market.fmt(cost - is.money) + " écus.";
        is.money -= cost;
        b.level++;
        data().setDirty();
        return null;
    }

    private int animStep;

    /** Animation des machines (toutes les 10 ticks). */
    public void animate() {
        ServerLevel level = islandsLevel();
        if (level == null) return;
        animStep++;
        for (Island is : data().islands.values())
            for (Building b : is.buildings) MachineEntities.animate(level, b, animStep);
    }

    // ---------- bordure et chute dans le vide ----------

    private final Map<UUID, String> borderSent = new HashMap<>();

    /** Chaque joueur voit la bordure de l'île où il se trouve ; s'il tombe, il revient sur l'île. */
    public void watchPlayers() {
        ServerLevel level = islandsLevel();
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            if (p.level() != level) { borderSent.remove(p.getUUID()); continue; }
            Island is = islandAt(p.blockPosition());
            if (p.getY() < cfg.hauteur - 48) {
                Island to = is != null && (is.open || is.isMember(p.getUUID())) ? is : islandOf(p.getUUID());
                p.fallDistance = 0;
                if (to != null) visit(p, to); else teleportSpawn(p);
                p.displayClientMessage(Msg.info("Attention au vide !"), true);
                continue;
            }
            if (is == null) continue;
            BlockPos c = center(is.id);
            int r = buildRadius(is);
            String key = is.id + ":" + r;
            if (key.equals(borderSent.get(p.getUUID()))) continue;
            borderSent.put(p.getUUID(), key);
            WorldBorder wb = new WorldBorder();
            wb.setCenter(c.getX() + 0.5, c.getZ() + 0.5);
            wb.setSize(2 * r + 1);
            wb.setWarningBlocks(2);
            wb.setWarningTime(0);
            p.connection.send(new ClientboundInitializeBorderPacket(wb));
        }
    }

    public void forgetBorder(UUID u) { borderSent.remove(u); }

    // ---------- production ----------

    /** Appelé chaque seconde : les bâtiments remplissent leur entrepôt. */
    public void produce() {
        boolean any = false;
        for (Island is : data().islands.values()) {
            double factor = anyOnline(is) ? 1.0 : cfg.productionHorsLigne;
            for (Building b : is.buildings) {
                int cap = b.type.capacity(b.level);
                if (b.stored() >= cap) continue;
                b.progress += b.type.rate(b.level) / 60.0 * factor;
                while (b.progress >= 1 && b.stored() < cap) {
                    b.progress -= 1;
                    b.storage.merge(b.type.roll(b.level, rnd).item(), 1L, Long::sum);
                    any = true;
                }
            }
        }
        if (any) data().setDirty();
    }

    /** Valeur moyenne d'un objet produit par ce bâtiment à son niveau. */
    public static double avgValue(Building b) {
        double tw = 0, tv = 0;
        for (BuildingType.Output o : b.type.outputs) {
            if (o.fromLevel() > b.level) continue;
            tw += o.weight();
            tv += o.weight() * Market.price(o.item());
        }
        return tw == 0 ? 0 : tv / tw;
    }

    /** Revenu estimé (écus/minute) si on vend toute la production. */
    public long incomePerMinute(Island is) {
        double factor = anyOnline(is) ? 1.0 : cfg.productionHorsLigne;
        double v = 0;
        for (Building b : is.buildings) v += b.type.rate(b.level) * avgValue(b) * factor;
        return Math.round(v);
    }

    public List<Island> ranking() {
        List<Island> l = new ArrayList<>(data().islands.values());
        l.sort((a, b) -> Long.compare(b.totalEarned, a.totalEarned));
        return l;
    }

    public int rankOf(Island is) { return ranking().indexOf(is) + 1; }
}
