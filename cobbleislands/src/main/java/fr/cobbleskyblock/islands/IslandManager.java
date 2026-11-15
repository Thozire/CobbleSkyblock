package fr.cobbleskyblock.islands;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Random;
import java.util.UUID;

/** Logique des royaumes : grille des domaines, création, bâtiments, production, équipe. */
public class IslandManager {
    public static final ResourceKey<Level> ISLANDS = ResourceKey.create(Registries.DIMENSION,
            ResourceLocation.fromNamespaceAndPath("cobbleislands", "royaumes"));
    private static final int COLUMNS = 50;

    public record Invite(int islandId, String from, long expires) {}
    public record Pending(BuildingType type, BlockPos origin, long expires) {}

    private final MinecraftServer server;
    private final IslandConfig cfg;
    private final Random rnd = new Random();
    public final Map<UUID, Invite> invites = new HashMap<>();
    public final Map<UUID, Long> pendingDelete = new HashMap<>();
    public final Map<UUID, Pending> placing = new HashMap<>();

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

    public boolean inBounds(Island is, BlockPos pos) {
        BlockPos c = center(is.id);
        int r = cfg.radiusFor(is.sizeLevel);
        return Math.abs(pos.getX() - c.getX()) <= r && Math.abs(pos.getZ() - c.getZ()) <= r;
    }

    public int maxMembers(Island is) { return cfg.membersFor(is.memberLevel); }

    public int radius(Island is) { return cfg.radiusFor(is.sizeLevel); }

    // ---------- création ----------

    private boolean placeTemplate(ServerLevel level, String name, BlockPos origin) {
        Optional<StructureTemplate> tpl = server.getStructureManager().get(ResourceLocation.parse(name));
        if (tpl.isEmpty()) {
            CobbleIslands.LOG.warn("Structure {} introuvable", name);
            return false;
        }
        tpl.get().placeInWorld(level, origin, origin, new StructurePlaceSettings(), level.getRandom(), Block.UPDATE_CLIENTS);
        return true;
    }

    public String create(ServerPlayer player) {
        IslandData d = data();
        if (d.byPlayer.containsKey(player.getUUID())) return "Tu as déjà un royaume : /royaume go";
        ServerLevel level = islandsLevel();
        if (level == null) return "La dimension des royaumes n'est pas chargée (redémarre le serveur).";
        int id = d.nextId++;
        BlockPos c = center(id);
        // le campement (9x9) est centré sur le domaine, posé à la place de l'herbe
        placeTemplate(level, cfg.modele, c.offset(-4, -1, -4));
        Island is = new Island(id, player.getUUID(), player.getGameProfile().getName());
        is.home = c.offset(0, 0, 6);
        is.open = cfg.visitesOuvertesParDefaut;
        is.money = cfg.ecusDepart;
        d.islands.put(id, is);
        d.byPlayer.put(player.getUUID(), is);
        d.setDirty();
        markCorners(is, true);
        teleportHome(player, is);
        return null;
    }

    /** Bornes (muret + lanterne) aux quatre coins du domaine. */
    public void markCorners(Island is, boolean place) {
        ServerLevel level = islandsLevel();
        BlockPos c = center(is.id);
        int r = radius(is);
        BlockState wall = place ? Blocks.MOSSY_COBBLESTONE_WALL.defaultBlockState() : Blocks.AIR.defaultBlockState();
        BlockState lantern = place ? Blocks.LANTERN.defaultBlockState() : Blocks.AIR.defaultBlockState();
        for (int sx : new int[]{-1, 1})
            for (int sz : new int[]{-1, 1}) {
                BlockPos p = c.offset(sx * r, 0, sz * r);
                level.setBlockAndUpdate(p, wall);
                level.setBlockAndUpdate(p.above(), wall);
                level.setBlockAndUpdate(p.above(2), lantern);
            }
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
        markCorners(is, false);
        is.money -= cost;
        is.sizeLevel = next;
        markCorners(is, true);
        data().setDirty();
        return null;
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

    // ---------- bâtiments ----------

    private String validate(Island is, BlockPos origin) {
        BlockPos[] corners = {origin, origin.offset(Building.SIZE_X - 1, 0, 0), origin.offset(0, 0, Building.SIZE_Z - 1),
                origin.offset(Building.SIZE_X - 1, 0, Building.SIZE_Z - 1)};
        for (BlockPos c : corners) if (islandAt(c) != is || !inBounds(is, c)) return "Le bâtiment dépasse de ton domaine.";
        BlockPos camp = center(is.id).offset(-4, 0, -4);
        if (Math.abs(origin.getX() - camp.getX()) < Building.SIZE_X + 2 && Math.abs(origin.getZ() - camp.getZ()) < Building.SIZE_Z + 2)
            return "Trop près du campement : éloigne-toi un peu.";
        for (Building b : is.buildings) if (b.overlaps(origin)) return "Trop près d'un autre bâtiment (" + b.type.label + ").";
        if (Math.abs(origin.getY() - cfg.hauteur) > 6) return "Place-toi au niveau du sol.";
        return null;
    }

    /** Prépare la construction devant le joueur (aperçu en particules). Renvoie un problème éventuel. */
    public String startPlacement(ServerPlayer p, BuildingType t) {
        Island is = islandOf(p.getUUID());
        if (is == null) return "Tu n'as pas de royaume.";
        if (p.level().dimension() != ISLANDS || islandAt(p.blockPosition()) != is) return "Va sur ton domaine pour construire (/royaume go).";
        if (is.money < t.price) return "Il te manque " + Market.fmt(t.price - is.money) + " écus.";
        Direction f = p.getDirection();
        BlockPos center = p.blockPosition().relative(f, 7);
        BlockPos origin = center.offset(-Building.SIZE_X / 2, 0, -Building.SIZE_Z / 2);
        placing.put(p.getUUID(), new Pending(t, origin, System.currentTimeMillis() + 60_000));
        return validate(is, origin);
    }

    public String confirmPlacement(ServerPlayer p) {
        Pending pd = placing.remove(p.getUUID());
        if (pd == null || pd.expires() < System.currentTimeMillis()) return "Aucune construction en attente.";
        Island is = islandOf(p.getUUID());
        if (is == null) return "Tu n'as pas de royaume.";
        String err = validate(is, pd.origin());
        if (err != null) return err;
        if (is.money < pd.type().price) return "Il te manque " + Market.fmt(pd.type().price - is.money) + " écus.";
        is.money -= pd.type().price;
        placeTemplate(islandsLevel(), "cobbleislands:" + pd.type().structure, pd.origin().below());
        is.buildings.add(new Building(is.nextBuildingId++, pd.type(), pd.origin()));
        data().setDirty();
        return null;
    }

    /** Aperçu en particules du terrain occupé par les constructions en attente. */
    public void showPreviews() {
        long now = System.currentTimeMillis();
        placing.entrySet().removeIf(e -> e.getValue().expires() < now);
        ServerLevel level = islandsLevel();
        if (level == null) return;
        for (Map.Entry<UUID, Pending> e : placing.entrySet()) {
            ServerPlayer p = server.getPlayerList().getPlayer(e.getKey());
            if (p == null || p.level() != level) continue;
            Island is = islandOf(p.getUUID());
            boolean ok = is != null && validate(is, e.getValue().origin()) == null;
            DustParticleOptions dust = new DustParticleOptions(ok ? new Vector3f(0.35f, 1f, 0.45f) : new Vector3f(1f, 0.3f, 0.3f), 1.3f);
            BlockPos o = e.getValue().origin();
            double y = o.getY() + 0.15;
            for (int i = 0; i <= Building.SIZE_X; i++) {
                level.sendParticles(p, dust, true, o.getX() + i, y, o.getZ(), 1, 0, 0, 0, 0);
                level.sendParticles(p, dust, true, o.getX() + i, y, o.getZ() + Building.SIZE_Z, 1, 0, 0, 0, 0);
            }
            for (int k = 0; k <= Building.SIZE_Z; k++) {
                level.sendParticles(p, dust, true, o.getX(), y, o.getZ() + k, 1, 0, 0, 0, 0);
                level.sendParticles(p, dust, true, o.getX() + Building.SIZE_X, y, o.getZ() + k, 1, 0, 0, 0, 0);
            }
            for (int h = 1; h < 6; h++)
                for (int[] c : new int[][]{{0, 0}, {Building.SIZE_X, 0}, {0, Building.SIZE_Z}, {Building.SIZE_X, Building.SIZE_Z}})
                    level.sendParticles(p, dust, true, o.getX() + c[0], y + h * 0.8, o.getZ() + c[1], 1, 0, 0, 0, 0);
        }
    }

    public String upgradeBuilding(Island is, Building b) {
        int cost = b.type.nextCost(b.level);
        if (cost < 0) return "Ce bâtiment est déjà au niveau maximum.";
        if (is.money < cost) return "Il te manque " + Market.fmt(cost - is.money) + " écus.";
        is.money -= cost;
        b.level++;
        data().setDirty();
        return null;
    }

    /** Démolit un bâtiment (rembourse la moitié de son prix d'achat). */
    public void demolish(Island is, Building b) {
        ServerLevel level = islandsLevel();
        BlockPos o = b.origin;
        BlockState air = Blocks.AIR.defaultBlockState(), grass = Blocks.GRASS_BLOCK.defaultBlockState();
        for (int x = 0; x < Building.SIZE_X; x++)
            for (int z = 0; z < Building.SIZE_Z; z++) {
                level.setBlock(o.offset(x, -1, z), grass, Block.UPDATE_CLIENTS);
                for (int y = 0; y < Building.SIZE_Y + 2; y++) level.setBlock(o.offset(x, y, z), air, Block.UPDATE_CLIENTS);
            }
        is.buildings.remove(b);
        is.money += b.type.price / 2;
        data().setDirty();
    }

    public Building buildingAtLectern(Island is, BlockPos pos) {
        for (Building b : is.buildings) if (b.lectern().equals(pos)) return b;
        return null;
    }

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
