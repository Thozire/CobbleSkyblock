package fr.cobbleskyblock.islands;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

/** Une île : sa case sur la grille, son équipe et ses niveaux. */
public class Island {
    public final int id;
    public UUID owner;
    /** Membres (chef compris) : UUID -> dernier pseudo connu. */
    public final Map<UUID, String> members = new LinkedHashMap<>();
    public BlockPos home;
    public int sizeLevel = 1;
    public int memberLevel = 1;
    public boolean open = true;
    public long created = System.currentTimeMillis();

    public Island(int id, UUID owner, String ownerName) {
        this.id = id;
        this.owner = owner;
        this.members.put(owner, ownerName);
    }

    public boolean isMember(UUID u) { return members.containsKey(u); }

    public boolean isOwner(UUID u) { return owner.equals(u); }

    public String ownerName() { return members.getOrDefault(owner, "?"); }

    public CompoundTag save() {
        CompoundTag t = new CompoundTag();
        t.putInt("id", id);
        t.putUUID("owner", owner);
        ListTag list = new ListTag();
        members.forEach((u, n) -> {
            CompoundTag m = new CompoundTag();
            m.putUUID("uuid", u);
            m.putString("name", n);
            list.add(m);
        });
        t.put("members", list);
        t.putInt("hx", home.getX());
        t.putInt("hy", home.getY());
        t.putInt("hz", home.getZ());
        t.putInt("sizeLevel", sizeLevel);
        t.putInt("memberLevel", memberLevel);
        t.putBoolean("open", open);
        t.putLong("created", created);
        return t;
    }

    public static Island load(CompoundTag t) {
        UUID owner = t.getUUID("owner");
        Island is = new Island(t.getInt("id"), owner, "?");
        is.members.clear();
        ListTag list = t.getList("members", Tag.TAG_COMPOUND);
        for (int i = 0; i < list.size(); i++) {
            CompoundTag m = list.getCompound(i);
            is.members.put(m.getUUID("uuid"), m.getString("name"));
        }
        is.members.putIfAbsent(owner, "?");
        is.home = new BlockPos(t.getInt("hx"), t.getInt("hy"), t.getInt("hz"));
        is.sizeLevel = Math.max(1, t.getInt("sizeLevel"));
        is.memberLevel = Math.max(1, t.getInt("memberLevel"));
        is.open = t.getBoolean("open");
        is.created = t.getLong("created");
        return is;
    }
}
