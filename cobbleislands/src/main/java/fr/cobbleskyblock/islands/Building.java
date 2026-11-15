package fr.cobbleskyblock.islands;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.StringTag;
import net.minecraft.nbt.Tag;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Une machine posée sur une île : un bloc de barrière (collision, clic) et des entités
 * d'affichage (le modèle 3D et ses pièces animées). Son stock est virtuel.
 */
public class Building {
    public final int id;
    public final BuildingType type;
    public int level = 1;
    public final BlockPos pos;
    /** Orientation (degrés, 0 = façade vers le sud). */
    public final float yaw;
    public final Map<String, Long> storage = new LinkedHashMap<>();
    public double progress;
    /** Entités d'affichage : [0] = socle, puis les pièces animées. */
    public final List<UUID> entities = new ArrayList<>();

    public Building(int id, BuildingType type, BlockPos pos, float yaw) {
        this.id = id;
        this.type = type;
        this.pos = pos;
        this.yaw = yaw;
    }

    public long stored() {
        long n = 0;
        for (long v : storage.values()) n += v;
        return n;
    }

    public boolean full() { return stored() >= type.capacity(level); }

    public CompoundTag save() {
        CompoundTag t = new CompoundTag();
        t.putInt("id", id);
        t.putString("type", type.name());
        t.putInt("level", level);
        t.putInt("x", pos.getX());
        t.putInt("y", pos.getY());
        t.putInt("z", pos.getZ());
        t.putFloat("yaw", yaw);
        t.putDouble("progress", progress);
        CompoundTag st = new CompoundTag();
        storage.forEach(st::putLong);
        t.put("storage", st);
        ListTag ents = new ListTag();
        for (UUID u : entities) ents.add(StringTag.valueOf(u.toString()));
        t.put("entities", ents);
        return t;
    }

    public static Building load(CompoundTag t) {
        BuildingType type = BuildingType.byName(t.getString("type"));
        if (type == null) return null;
        Building b = new Building(t.getInt("id"), type, new BlockPos(t.getInt("x"), t.getInt("y"), t.getInt("z")), t.getFloat("yaw"));
        b.level = Math.max(1, t.getInt("level"));
        b.progress = t.getDouble("progress");
        CompoundTag st = t.getCompound("storage");
        for (String k : st.getAllKeys()) b.storage.put(k, st.getLong(k));
        ListTag ents = t.getList("entities", Tag.TAG_STRING);
        for (int i = 0; i < ents.size(); i++) {
            try { b.entities.add(UUID.fromString(ents.getString(i))); } catch (IllegalArgumentException ignored) {}
        }
        return b;
    }
}
