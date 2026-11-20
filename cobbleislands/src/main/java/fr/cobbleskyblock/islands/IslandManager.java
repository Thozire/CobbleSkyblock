package fr.cobbleskyblock.islands;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/** Logique des îles : grille, création à partir du modèle, téléportations, invitations. */
public class IslandManager {
    public static final ResourceKey<Level> ISLANDS = ResourceKey.create(Registries.DIMENSION,
            ResourceLocation.fromNamespaceAndPath("cobbleislands", "islands"));
    private static final int COLUMNS = 50;

    public record Invite(int islandId, String from, long expires) {}

    private final MinecraftServer server;
    private final IslandConfig cfg;
    public final Map<UUID, Invite> invites = new HashMap<>();
    public final Map<UUID, Long> pendingDelete = new HashMap<>();

    public IslandManager(MinecraftServer server, IslandConfig cfg) {
        this.server = server;
        this.cfg = cfg;
    }

    public IslandData data() { return IslandData.get(server); }

    public ServerLevel islandsLevel() { return server.getLevel(ISLANDS); }

    public Island islandOf(UUID player) { return data().byPlayer.get(player); }

    /** Centre (x, z) de l'île n° id sur la grille. */
    public BlockPos center(int id) {
        int col = (id - 1) % COLUMNS, row = (id - 1) / COLUMNS;
        return new BlockPos(col * cfg.espacement, cfg.hauteur, row * cfg.espacement);
    }

    /** Île dont la case contient cette position (dans la dimension des îles), ou null. */
    public Island islandAt(BlockPos pos) {
        int col = Math.round((float) pos.getX() / cfg.espacement);
        int row = Math.round((float) pos.getZ() / cfg.espacement);
        if (col < 0 || col >= COLUMNS || row < 0) return null;
        return data().islands.get(row * COLUMNS + col + 1);
    }

    /** La position est-elle dans la zone constructible de cette île ? */
    public boolean inBounds(Island is, BlockPos pos) {
        BlockPos c = center(is.id);
        int r = cfg.radiusFor(is.sizeLevel);
        return Math.abs(pos.getX() - c.getX()) <= r && Math.abs(pos.getZ() - c.getZ()) <= r;
    }

    public int maxMembers(Island is) { return cfg.membersFor(is.memberLevel); }

    public int radius(Island is) { return cfg.radiusFor(is.sizeLevel); }

    /** Crée une île pour ce joueur et l'y téléporte. Renvoie un message d'erreur, ou null si tout va bien. */
    public String create(ServerPlayer player) {
        IslandData d = data();
        if (d.byPlayer.containsKey(player.getUUID())) return "Tu as déjà une île : /ile home";
        ServerLevel level = islandsLevel();
        if (level == null) return "La dimension des îles n'est pas chargée (redémarre le serveur).";
        Optional<StructureTemplate> tpl = server.getStructureManager().get(ResourceLocation.parse(cfg.modele));
        int id = d.nextId++;
        BlockPos c = center(id);
        if (tpl.isPresent()) {
            Vec3i size = tpl.get().getSize();
            BlockPos origin = c.offset(-size.getX() / 2, -size.getY() + 1, -size.getZ() / 2);
            StructurePlaceSettings settings = new StructurePlaceSettings().setIgnoreEntities(false);
            tpl.get().placeInWorld(level, origin, origin, settings, level.getRandom(), Block.UPDATE_CLIENTS);
        } else {
            CobbleIslands.LOG.warn("Modèle {} introuvable, île de secours", cfg.modele);
            for (int x = -2; x <= 2; x++)
                for (int z = -2; z <= 2; z++)
                    level.setBlockAndUpdate(c.offset(x, 0, z), Blocks.GRASS_BLOCK.defaultBlockState());
        }
        int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c.getX(), c.getZ());
        Island is = new Island(id, player.getUUID(), player.getGameProfile().getName());
        is.home = new BlockPos(c.getX(), Math.max(top, c.getY() + 1), c.getZ());
        is.open = cfg.visitesOuvertesParDefaut;
        d.islands.put(id, is);
        d.byPlayer.put(player.getUUID(), is);
        d.setDirty();
        teleportHome(player, is);
        return null;
    }

    public void teleportHome(ServerPlayer p, Island is) {
        ServerLevel level = islandsLevel();
        BlockPos h = is.home;
        p.teleportTo(level, h.getX() + 0.5, h.getY(), h.getZ() + 0.5, p.getYRot(), p.getXRot());
        p.setRespawnPosition(ISLANDS, h, 0f, true, false);
    }

    public void teleportSpawn(ServerPlayer p) {
        ServerLevel ow = server.overworld();
        IslandData d = data();
        BlockPos s = d.spawnBuilt ? new BlockPos(d.spawnX, d.spawnY, d.spawnZ) : ow.getSharedSpawnPos();
        p.teleportTo(ow, s.getX() + 0.5, s.getY(), s.getZ() + 0.5, p.getYRot(), p.getXRot());
    }

    /** Téléporte un visiteur sur une île. */
    public void visit(ServerPlayer p, Island is) {
        BlockPos h = is.home;
        p.teleportTo(islandsLevel(), h.getX() + 0.5, h.getY(), h.getZ() + 0.5, p.getYRot(), p.getXRot());
        p.sendSystemMessage(Msg.ok(is.isMember(p.getUUID()) ? "Retour sur ton île." : "Bienvenue sur l'île de " + is.ownerName() + " !"));
    }

    public void join(ServerPlayer p, Island is) {
        is.members.put(p.getUUID(), p.getGameProfile().getName());
        data().byPlayer.put(p.getUUID(), is);
        data().setDirty();
    }

    /** Retire un membre (exclusion ou départ). Le renvoie au spawn s'il est connecté. */
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

    /** Supprime l'île (les blocs restent, mais la case n'est jamais réutilisée). */
    public void delete(Island is) {
        for (UUID u : is.members.keySet().toArray(new UUID[0])) removeMember(is, u);
        data().islands.remove(is.id);
        data().setDirty();
    }

    public MinecraftServer server() { return server; }

    public IslandConfig config() { return cfg; }
}
