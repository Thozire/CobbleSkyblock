package fr.cobbleskyblock.islands;

import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.FloatTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.StringTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

import java.util.Random;
import java.util.UUID;

/**
 * Entités d'affichage des machines : création, animation (rotation, balancier, flamme), suppression.
 * Tout passe par les données NBT publiques des entités (comme /summon et /data), sans mixin.
 */
final class MachineEntities {
    private MachineEntities() {}

    static final String TAG = "royaumes_machine";
    private static final Random RND = new Random();

    // ---------- création ----------

    static void spawn(ServerLevel level, Building b) {
        b.entities.clear();
        level.setBlock(b.pos, Blocks.BARRIER.defaultBlockState(), Block.UPDATE_ALL);
        UUID base = display(level, b, MachineModels.base(b.type.id), 0, 0, 0, false);
        if (base != null) b.entities.add(base);
        for (MachineModels.Part part : MachineModels.parts(b.type.id)) {
            UUID u = display(level, b, part.cmd(), part.ox(), part.oy(), part.oz(), part.bright());
            if (u != null) b.entities.add(u);
        }
    }

    private static UUID display(ServerLevel level, Building b, int cmd, float ox, float oy, float oz, boolean bright) {
        CompoundTag t = new CompoundTag();
        t.putString("id", "minecraft:item_display");
        ItemStack s = new ItemStack(Items.PAPER);
        s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(cmd));
        t.put("item", s.save(level.registryAccess()));
        t.putString("item_display", "none");
        t.put("transformation", transform(0, 0, 0, 1, ox / 16f, oy / 16f, oz / 16f, 1, 1, 1));
        if (bright) {
            CompoundTag br = new CompoundTag();
            br.putInt("sky", 15);
            br.putInt("block", 15);
            t.put("brightness", br);
        }
        ListTag tags = new ListTag();
        tags.add(StringTag.valueOf(TAG));
        t.put("Tags", tags);
        double x = b.pos.getX() + 0.5, y = b.pos.getY() + 0.5, z = b.pos.getZ() + 0.5;
        Entity e = EntityType.loadEntityRecursive(t, level, en -> {
            en.moveTo(x, y, z, b.yaw, 0f);
            return en;
        });
        if (e == null || !level.addFreshEntity(e)) {
            CobbleIslands.LOG.warn("Impossible de créer l'affichage de la machine {}", b.type.id);
            return null;
        }
        return e.getUUID();
    }

    private static ListTag floats(float... v) {
        ListTag l = new ListTag();
        for (float f : v) l.add(FloatTag.valueOf(f));
        return l;
    }

    private static CompoundTag transform(float qx, float qy, float qz, float qw, float tx, float ty, float tz, float sx, float sy, float sz) {
        CompoundTag t = new CompoundTag();
        t.put("left_rotation", floats(qx, qy, qz, qw));
        t.put("right_rotation", floats(0, 0, 0, 1));
        t.put("translation", floats(tx, ty, tz));
        t.put("scale", floats(sx, sy, sz));
        return t;
    }

    // ---------- suppression ----------

    static void remove(ServerLevel level, Building b) {
        for (UUID u : b.entities) {
            Entity e = level.getEntity(u);
            if (e != null) e.discard();
        }
        // sécurité : toute entité de machine restée sur ce bloc
        for (Entity e : level.getEntities((Entity) null, new net.minecraft.world.phys.AABB(b.pos).inflate(0.1), en -> en.getTags().contains(TAG)))
            e.discard();
        b.entities.clear();
        if (level.getBlockState(b.pos).is(Blocks.BARRIER)) level.setBlock(b.pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
    }

    // ---------- animation ----------

    /** Appelé toutes les 10 ticks ; step augmente de 1 à chaque appel. */
    static void animate(ServerLevel level, Building b, int step) {
        if (b.full()) return;
        double cx = b.pos.getX() + 0.5, cy = b.pos.getY() + 0.5, cz = b.pos.getZ() + 0.5;
        if (!level.hasNearbyAlivePlayer(cx, cy, cz, 48)) return;
        MachineModels.Part[] parts = MachineModels.parts(b.type.id);
        for (int i = 0; i < parts.length && i + 1 < b.entities.size(); i++) {
            Entity e = level.getEntity(b.entities.get(i + 1));
            if (e == null) continue;
            MachineModels.Part p = parts[i];
            float qx = 0, qy = 0, qz = 0, qw = 1, sx = 1, sy = 1, sz = 1;
            switch (p.anim()) {
                case "spin_z" -> { double a = Math.toRadians(step * 90.0) / 2; qz = (float) Math.sin(a); qw = (float) Math.cos(a); }
                case "spin_y" -> { double a = Math.toRadians(step * 45.0) / 2; qy = (float) Math.sin(a); qw = (float) Math.cos(a); }
                case "swing" -> { double a = Math.toRadians(step % 2 == 0 ? 0 : -38) / 2; qz = (float) Math.sin(a); qw = (float) Math.cos(a); }
                case "flicker" -> { sy = 0.8f + RND.nextFloat() * 0.4f; sx = sz = 0.92f + RND.nextFloat() * 0.16f; }
                default -> { }
            }
            CompoundTag t = new CompoundTag();
            e.saveWithoutId(t);
            t.put("transformation", transform(qx, qy, qz, qw, p.ox() / 16f, p.oy() / 16f, p.oz() / 16f, sx, sy, sz));
            t.putInt("interpolation_duration", 10);
            t.putInt("start_interpolation", 0);
            e.load(t);
        }
        if (step % 2 == 0) particles(level, b);
    }

    /** Point du modèle (en 1/16, repère du modèle) converti en coordonnées du monde. */
    private static double[] world(Building b, double mx, double my, double mz) {
        double lx = (mx - 8) / 16.0, lz = (mz - 8) / 16.0;
        double phi = Math.toRadians(-b.yaw);
        double wx = lx * Math.cos(phi) + lz * Math.sin(phi);
        double wz = -lx * Math.sin(phi) + lz * Math.cos(phi);
        return new double[]{b.pos.getX() + 0.5 + wx, b.pos.getY() + my / 16.0, b.pos.getZ() + 0.5 + wz};
    }

    private static void particles(ServerLevel level, Building b) {
        switch (b.type) {
            case SCIERIE -> {
                double[] w = world(b, 8, 12, 8);
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.OAK_PLANKS.defaultBlockState()), w[0], w[1], w[2], 3, 0.12, 0.05, 0.12, 0.02);
            }
            case MOULIN -> {
                double[] w = world(b, 8, 13, 8);
                level.sendParticles(ParticleTypes.WHITE_ASH, w[0], w[1], w[2], 4, 0.25, 0.1, 0.25, 0.0);
            }
            case MINE -> {
                double[] w = world(b, 8, 4, 8);
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.STONE.defaultBlockState()), w[0], w[1], w[2], 3, 0.15, 0.05, 0.15, 0.02);
            }
            case FORGE -> {
                double[] chim = world(b, 4.5, 21.5, 2.5);
                level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, chim[0], chim[1], chim[2], 1, 0.05, 0.05, 0.05, 0.01);
                double[] fire = world(b, 4.5, 9.5, 10);
                ParticleOptions o = RND.nextInt(3) == 0 ? ParticleTypes.LAVA : ParticleTypes.FLAME;
                level.sendParticles(o, fire[0], fire[1], fire[2], 1, 0.15, 0.05, 0.15, 0.0);
            }
        }
    }

    static BlockPos posOf(Building b) { return b.pos; }
}
