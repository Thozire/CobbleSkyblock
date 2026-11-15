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
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.UUID;

/**
 * Entités d'affichage des bâtiments : création, animation par images-clés, particules, suppression.
 * Un bâtiment occupe 3x3 blocs au sol (barrières invisibles) autour de son bloc central ; toutes ses
 * entités d'affichage sont posées au centre de ce bloc et décalées par leur transformation.
 * Tout passe par les données NBT publiques des entités (comme /summon et /data), sans mixin.
 */
final class MachineEntities {
    private MachineEntities() {}

    static final String TAG = "royaumes_machine";
    /** Emprise : RADIUS blocs autour du centre, HEIGHT blocs de haut. */
    static final int RADIUS = 1, HEIGHT = 2;
    /** Durée d'un pas d'animation, en ticks. */
    static final int STEP_TICKS = 5;
    private static final Random RND = new Random();

    // ---------- emprise ----------

    static List<BlockPos> footprint(BlockPos center) {
        List<BlockPos> l = new ArrayList<>();
        for (int dy = 0; dy < HEIGHT; dy++)
            for (int dx = -RADIUS; dx <= RADIUS; dx++)
                for (int dz = -RADIUS; dz <= RADIUS; dz++) l.add(center.offset(dx, dy, dz));
        return l;
    }

    static boolean covers(Building b, BlockPos pos) {
        int dy = pos.getY() - b.pos.getY();
        return dy >= 0 && dy < HEIGHT && Math.abs(pos.getX() - b.pos.getX()) <= RADIUS && Math.abs(pos.getZ() - b.pos.getZ()) <= RADIUS;
    }

    // ---------- création ----------

    static void spawn(ServerLevel level, Building b) {
        b.entities.clear();
        for (BlockPos p : footprint(b.pos)) {
            BlockState s = level.getBlockState(p);
            if (p.equals(b.pos) || s.isAir() || s.canBeReplaced()) level.setBlock(p, Blocks.BARRIER.defaultBlockState(), Block.UPDATE_ALL);
        }
        UUID base = display(level, b, MachineModels.base(b.type.id), transform(0, 0, 0, 1, 0, 1, 0, 1, 1, 1), false);
        if (base != null) b.entities.add(base);
        for (MachineModels.Part part : MachineModels.parts(b.type.id)) {
            float[] k = part.keys();
            int last = k.length - 9;
            CompoundTag rest = last >= 0
                    ? pose(part, k[last + 1], k[last + 2], k[last + 3], (int) k[last + 4], k[last + 5], k[last + 6], k[last + 7], k[last + 8])
                    : pose(part, 0, 0, 0, 1, 0, 1, 1, 1);
            UUID u = display(level, b, part.cmd(), rest, part.bright());
            if (u != null) b.entities.add(u);
        }
        clickZone(level, b);
        b.model = MachineModels.VERSION;
    }

    /**
     * Zone de clic invisible qui enveloppe les barrières : le viseur la touche avant elles, donc le
     * contour de sélection des blocs ne s'affiche plus par-dessus le modèle. Retrouvée par son étiquette.
     */
    private static void clickZone(ServerLevel level, Building b) {
        CompoundTag t = new CompoundTag();
        t.putString("id", "minecraft:interaction");
        t.putFloat("width", 2 * RADIUS + 1.08f);
        t.putFloat("height", HEIGHT + 0.06f);
        t.putBoolean("response", true);
        ListTag tags = new ListTag();
        tags.add(StringTag.valueOf(TAG));
        t.put("Tags", tags);
        double x = b.pos.getX() + 0.5, y = b.pos.getY() - 0.02, z = b.pos.getZ() + 0.5;
        Entity e = EntityType.loadEntityRecursive(t, level, en -> {
            en.moveTo(x, y, z, 0f, 0f);
            return en;
        });
        if (e == null || !level.addFreshEntity(e)) CobbleIslands.LOG.warn("Impossible de créer la zone de clic du bâtiment {}", b.type.id);
    }

    private static UUID display(ServerLevel level, Building b, int cmd, CompoundTag transformation, boolean bright) {
        CompoundTag t = new CompoundTag();
        t.putString("id", "minecraft:item_display");
        ItemStack s = new ItemStack(Items.PAPER);
        s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(cmd));
        t.put("item", s.save(level.registryAccess()));
        t.putString("item_display", "none");
        t.put("transformation", transformation);
        t.putFloat("view_range", 1.5f);
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
            CobbleIslands.LOG.warn("Impossible de créer l'affichage du bâtiment {}", b.type.id);
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

    /**
     * Transformation d'une pièce : son pivot plus un décalage (repère de dessin, 1/16 de bloc), une rotation
     * de {@code deg} degrés autour de l'axe (0 = X, 1 = Y, 2 = Z) et une échelle, le tout autour du pivot.
     * Un item_display affiche son objet tourné de 180° autour de Y : X et Z sont inversés, donc le sens
     * des rotations autour de X et Z aussi.
     */
    private static CompoundTag pose(MachineModels.Part p, float tx, float ty, float tz, int axis, float deg, float sx, float sy, float sz) {
        double a = Math.toRadians(axis == 1 ? deg : -deg) / 2;
        float s = (float) Math.sin(a), c = (float) Math.cos(a);
        return transform(axis == 0 ? s : 0, axis == 1 ? s : 0, axis == 2 ? s : 0, c,
                -(p.px() - 24 + tx) / 16f, (p.py() - 8 + ty) / 16f, -(p.pz() - 24 + tz) / 16f, sx, sy, sz);
    }

    // ---------- suppression ----------

    static void remove(ServerLevel level, Building b) {
        for (UUID u : b.entities) {
            Entity e = level.getEntity(u);
            if (e != null) e.discard();
        }
        // sécurité : toute entité de bâtiment restée sur le bloc central
        for (Entity e : level.getEntities((Entity) null, new AABB(b.pos).inflate(0.1), en -> en.getTags().contains(TAG)))
            e.discard();
        b.entities.clear();
        for (BlockPos p : footprint(b.pos))
            if (level.getBlockState(p).is(Blocks.BARRIER)) level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
    }

    /**
     * Retire les entités orphelines d'un bâtiment : d'anciens affichages chargés après une reconstruction
     * (ils resteraient immobiles, en double sous les pièces animées) et les zones de clic en trop.
     */
    static void purge(ServerLevel level, Building b) {
        boolean zone = false;
        for (Entity e : level.getEntities((Entity) null, new AABB(b.pos).inflate(0.4), en -> en.getTags().contains(TAG))) {
            if (e instanceof net.minecraft.world.entity.Interaction) {
                if (zone) e.discard();
                zone = true;
            } else if (!b.entities.contains(e.getUUID())) {
                e.discard();
            }
        }
    }

    // ---------- animation ----------

    /**
     * Appelé toutes les {@link #STEP_TICKS} ticks ; step augmente de 1 à chaque appel.
     * Renvoie true si le bâtiment a été reconstruit (ancien modèle) et doit être sauvegardé.
     */
    static boolean animate(ServerLevel level, Building b, int step) {
        double cx = b.pos.getX() + 0.5, cy = b.pos.getY() + 0.5, cz = b.pos.getZ() + 0.5;
        if (!level.hasNearbyAlivePlayer(cx, cy, cz, 48)) return false;
        MachineModels.Part[] parts = MachineModels.parts(b.type.id);
        if (b.model != MachineModels.VERSION || b.entities.size() != parts.length + 1) {
            // bâtiment posé avec d'anciens modèles : on le reconstruit dès que sa zone est chargée
            if (!level.isLoaded(b.pos) || !level.isPositionEntityTicking(b.pos)) return false;
            remove(level, b);
            spawn(level, b);
            return true;
        }
        if ((step + b.id) % 8 == 0) purge(level, b);
        if (b.full()) return false;
        int t = step + b.id * 7;          // décalage : deux bâtiments voisins ne bougent pas à l'unisson
        for (int i = 0; i < parts.length; i++) {
            MachineModels.Part p = parts[i];
            float[] k = p.keys();
            CompoundTag tr;
            int dur;
            if (p.jitter() > 0) {         // flamme : échelle aléatoire à chaque pas
                float j = p.jitter();
                float w = 1 + (RND.nextFloat() - 0.5f) * j;
                tr = pose(p, 0, 0, 0, 1, 0, w, 1 + (RND.nextFloat() - 0.4f) * 2 * j, w);
                dur = 1;
            } else if (k.length >= 9) {   // image-clé qui commence à ce pas
                int total = 0;
                for (int n = 0; n < k.length; n += 9) total += (int) k[n];
                int lt = Math.floorMod(t, total), start = 0, at = -1;
                for (int n = 0; n < k.length && start <= lt; n += 9) {
                    if (start == lt) { at = n; break; }
                    start += (int) k[n];
                }
                if (at < 0) continue;
                tr = pose(p, k[at + 1], k[at + 2], k[at + 3], (int) k[at + 4], k[at + 5], k[at + 6], k[at + 7], k[at + 8]);
                dur = (int) k[at];
            } else continue;
            Entity e = level.getEntity(b.entities.get(i + 1));
            if (e == null) continue;
            CompoundTag nbt = new CompoundTag();
            e.saveWithoutId(nbt);
            nbt.put("transformation", tr);
            nbt.putInt("interpolation_duration", dur * STEP_TICKS);
            nbt.putInt("start_interpolation", 0);
            e.load(nbt);
        }
        for (MachineModels.Emitter em : MachineModels.emitters(b.type.id)) {
            if (Math.floorMod(t, em.period()) != em.at()) continue;
            ParticleOptions o = particle(em.kind());
            if (o == null) continue;
            double[] w = world(b, em.x(), em.y(), em.z());
            level.sendParticles(o, w[0], w[1], w[2], em.count(), em.dx(), em.dy(), em.dz(), em.speed());
        }
        return false;
    }

    private static ParticleOptions particle(String kind) {
        return switch (kind) {
            case "wood" -> new BlockParticleOption(ParticleTypes.BLOCK, Blocks.OAK_PLANKS.defaultBlockState());
            case "stone" -> new BlockParticleOption(ParticleTypes.BLOCK, Blocks.STONE.defaultBlockState());
            case "splash" -> ParticleTypes.SPLASH;
            case "ash" -> ParticleTypes.WHITE_ASH;
            case "grow" -> ParticleTypes.HAPPY_VILLAGER;
            case "smoke" -> ParticleTypes.CAMPFIRE_COSY_SMOKE;
            case "spark" -> ParticleTypes.ELECTRIC_SPARK;
            case "lava" -> ParticleTypes.LAVA;
            case "flame" -> ParticleTypes.FLAME;
            case "small_flame" -> ParticleTypes.SMALL_FLAME;
            default -> null;
        };
    }

    /** Point du repère de dessin (1/16 de bloc, centre du bâtiment en X = Z = 24) converti en coordonnées du monde. */
    private static double[] world(Building b, double mx, double my, double mz) {
        double lx = -(mx - 24) / 16.0, lz = -(mz - 24) / 16.0;
        double phi = Math.toRadians(-b.yaw);
        double wx = lx * Math.cos(phi) + lz * Math.sin(phi);
        double wz = -lx * Math.sin(phi) + lz * Math.cos(phi);
        return new double[]{b.pos.getX() + 0.5 + wx, b.pos.getY() + my / 16.0, b.pos.getZ() + 0.5 + wz};
    }

    static BlockPos posOf(Building b) { return b.pos; }
}
