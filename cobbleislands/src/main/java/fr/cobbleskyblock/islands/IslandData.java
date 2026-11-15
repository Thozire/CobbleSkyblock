package fr.cobbleskyblock.islands;

import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Sauvegarde des îles dans world/data/cobbleislands.dat. */
public class IslandData extends SavedData {
    public final Map<Integer, Island> islands = new HashMap<>();
    /** Index joueur -> île (reconstruit au chargement). */
    public final Map<UUID, Island> byPlayer = new HashMap<>();
    public int nextId = 1;
    public boolean spawnBuilt = false;
    public int spawnX, spawnY, spawnZ;
    /** 2 = îles flottantes (les royaumes plats de la version 1 sont abandonnés). */
    public int version = 3;

    public static IslandData get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(
                new SavedData.Factory<>(IslandData::new, IslandData::load, null), "royaumes");
    }

    public static IslandData load(CompoundTag tag, HolderLookup.Provider registries) {
        IslandData d = new IslandData();
        d.nextId = Math.max(1, tag.getInt("nextId"));
        d.spawnBuilt = tag.getBoolean("spawnBuilt");
        d.spawnX = tag.getInt("spawnX");
        d.spawnY = tag.getInt("spawnY");
        d.spawnZ = tag.getInt("spawnZ");
        int v = tag.getInt("version");
        ListTag list = tag.getList("islands", Tag.TAG_COMPOUND);
        if (v < 3) {
            // nouvel îlot de départ : les anciens royaumes sont abandonnés ; les nouveaux prennent des
            // emplacements neufs (le compteur continue), loin des anciennes îles
            if (!list.isEmpty()) CobbleIslands.LOG.warn("Nouvelles îles de départ : {} ancien(s) royaume(s) remis à zéro.", list.size());
            list = new ListTag();
            if (v < 2) d.nextId = 1;
            d.setDirty();
        }
        for (int i = 0; i < list.size(); i++) {
            Island is = Island.load(list.getCompound(i));
            d.islands.put(is.id, is);
        }
        d.reindex();
        return d;
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        tag.putInt("version", version);
        tag.putInt("nextId", nextId);
        tag.putBoolean("spawnBuilt", spawnBuilt);
        tag.putInt("spawnX", spawnX);
        tag.putInt("spawnY", spawnY);
        tag.putInt("spawnZ", spawnZ);
        ListTag list = new ListTag();
        for (Island is : islands.values()) list.add(is.save());
        tag.put("islands", list);
        return tag;
    }

    public void reindex() {
        byPlayer.clear();
        for (Island is : islands.values()) {
            for (UUID u : is.members.keySet()) byPlayer.put(u, is);
        }
    }
}
