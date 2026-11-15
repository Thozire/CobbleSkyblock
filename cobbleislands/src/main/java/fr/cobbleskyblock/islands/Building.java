package fr.cobbleskyblock.islands;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;

import java.util.LinkedHashMap;
import java.util.Map;

/** Un bâtiment posé sur un domaine, avec son entrepôt virtuel. */
public class Building {
    /** Taille commune des bâtiments (en blocs). */
    public static final int SIZE_X = 9, SIZE_Y = 9, SIZE_Z = 9;
    /** Position du pupitre (bloc d'accès au menu du bâtiment) dans la structure. */
    public static final int LECTERN_X = 4, LECTERN_Y = 0, LECTERN_Z = 8;

    public final int id;
    public final BuildingType type;
    public int level = 1;
    /** Coin nord-ouest au niveau du sol. */
    public final BlockPos origin;
    public final Map<String, Long> storage = new LinkedHashMap<>();
    public double progress;

    public Building(int id, BuildingType type, BlockPos origin) {
        this.id = id;
        this.type = type;
        this.origin = origin;
    }

    public BlockPos lectern() { return origin.offset(LECTERN_X, LECTERN_Y, LECTERN_Z); }

    public boolean contains(BlockPos p, int margin) {
        return p.getX() >= origin.getX() - margin && p.getX() < origin.getX() + SIZE_X + margin
                && p.getZ() >= origin.getZ() - margin && p.getZ() < origin.getZ() + SIZE_Z + margin
                && p.getY() >= origin.getY() - 2 && p.getY() < origin.getY() + SIZE_Y + 2;
    }

    public boolean overlaps(BlockPos otherOrigin) {
        return Math.abs(otherOrigin.getX() - origin.getX()) < SIZE_X + 1 && Math.abs(otherOrigin.getZ() - origin.getZ()) < SIZE_Z + 1;
    }

    public long stored() {
        long n = 0;
        for (long v : storage.values()) n += v;
        return n;
    }

    public CompoundTag save() {
        CompoundTag t = new CompoundTag();
        t.putInt("id", id);
        t.putString("type", type.name());
        t.putInt("level", level);
        t.putInt("x", origin.getX());
        t.putInt("y", origin.getY());
        t.putInt("z", origin.getZ());
        t.putDouble("progress", progress);
        CompoundTag st = new CompoundTag();
        storage.forEach(st::putLong);
        t.put("storage", st);
        return t;
    }

    public static Building load(CompoundTag t) {
        BuildingType type = BuildingType.byName(t.getString("type"));
        if (type == null) return null;
        Building b = new Building(t.getInt("id"), type, new BlockPos(t.getInt("x"), t.getInt("y"), t.getInt("z")));
        b.level = Math.max(1, t.getInt("level"));
        b.progress = t.getDouble("progress");
        CompoundTag st = t.getCompound("storage");
        for (String k : st.getAllKeys()) b.storage.put(k, st.getLong(k));
        return b;
    }
}
