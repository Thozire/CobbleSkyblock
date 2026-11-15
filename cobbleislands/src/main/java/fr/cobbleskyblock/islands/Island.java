package fr.cobbleskyblock.islands;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Un royaume : son île sur la grille, son équipe, son trésor et ses machines. */
public class Island {
    public final int id;
    public UUID owner;
    /** Membres (seigneur compris) : UUID -> dernier pseudo connu. */
    public final Map<UUID, String> members = new LinkedHashMap<>();
    public String name;
    public BlockPos home;
    public int sizeLevel = 1;
    public int memberLevel = 1;
    public boolean open = true;
    public long created = System.currentTimeMillis();
    /** Trésor (écus) partagé par toute l'équipe. */
    public long money;
    /** Total gagné depuis la création (sert au classement). */
    public long totalEarned;
    public final List<Building> buildings = new ArrayList<>();
    public int nextBuildingId = 1;

    public Island(int id, UUID owner, String ownerName) {
        this.id = id;
        this.owner = owner;
        this.members.put(owner, ownerName);
        this.name = "Royaume de " + ownerName;
    }

    public boolean isMember(UUID u) { return members.containsKey(u); }

    public boolean isOwner(UUID u) { return owner.equals(u); }

    public String ownerName() { return members.getOrDefault(owner, "?"); }

    public Building building(int bid) {
        for (Building b : buildings) if (b.id == bid) return b;
        return null;
    }

    public Building machineAt(net.minecraft.core.BlockPos pos) {
        for (Building b : buildings) if (b.pos.equals(pos)) return b;
        return null;
    }

    public void earn(long amount) {
        money += amount;
        totalEarned += amount;
    }

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
        t.putString("name", name);
        t.putInt("hx", home.getX());
        t.putInt("hy", home.getY());
        t.putInt("hz", home.getZ());
        t.putInt("sizeLevel", sizeLevel);
        t.putInt("memberLevel", memberLevel);
        t.putBoolean("open", open);
        t.putLong("created", created);
        t.putLong("money", money);
        t.putLong("totalEarned", totalEarned);
        t.putInt("nextBuildingId", nextBuildingId);
        ListTag bl = new ListTag();
        for (Building b : buildings) bl.add(b.save());
        t.put("buildings", bl);
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
        is.name = t.contains("name") ? t.getString("name") : "Royaume de " + is.ownerName();
        is.home = new BlockPos(t.getInt("hx"), t.getInt("hy"), t.getInt("hz"));
        is.sizeLevel = Math.max(1, t.getInt("sizeLevel"));
        is.memberLevel = Math.max(1, t.getInt("memberLevel"));
        is.open = t.getBoolean("open");
        is.created = t.getLong("created");
        is.money = t.getLong("money");
        is.totalEarned = t.getLong("totalEarned");
        is.nextBuildingId = Math.max(1, t.getInt("nextBuildingId"));
        ListTag bl = t.getList("buildings", Tag.TAG_COMPOUND);
        for (int i = 0; i < bl.size(); i++) {
            Building b = Building.load(bl.getCompound(i));
            if (b != null) is.buildings.add(b);
        }
        return is;
    }
}
