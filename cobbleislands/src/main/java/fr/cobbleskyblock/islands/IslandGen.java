package fr.cobbleskyblock.islands;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.state.BlockState;

import java.util.Random;

/**
 * Génération des îles flottantes. La forme dépend d'un rayon et d'un bruit angulaire propre
 * à chaque île : en agrandissant, on ne remplit que l'anneau nouveau (les constructions
 * du joueur ne sont pas touchées) et on prolonge le dessous de l'île.
 */
final class IslandGen {
    private IslandGen() {}

    private static final int FLAGS = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE;

    /** Rayon du bord de l'île dans une direction donnée. */
    private static double edge(double r, double angle, long seed) {
        Random rnd = new Random(seed);
        double p1 = rnd.nextDouble() * Math.PI * 2, p2 = rnd.nextDouble() * Math.PI * 2, p3 = rnd.nextDouble() * Math.PI * 2;
        return r * (1 + 0.10 * Math.sin(3 * angle + p1) + 0.06 * Math.sin(5 * angle + p2) + 0.04 * Math.sin(8 * angle + p3));
    }

    private static double hash(long seed, int x, int z) {
        long h = seed ^ (x * 341873128712L) ^ (z * 132897987541L);
        h = (h ^ (h >>> 13)) * 0x5DEECE66DL;
        return ((h >>> 16) & 0xFFFF) / 65535.0;
    }

    /** Profondeur de la colonne (nombre de blocs sous la surface) pour un rayon donné. */
    private static int depth(double d, double e, double r, double jitter) {
        if (d > e) return -1;
        double t = d / Math.max(1, e);
        double max = 5 + r * 0.85;
        return Math.max(1, (int) Math.round(max * (1 - Math.pow(t, 1.6)) + 1 + jitter * 2));
    }

    /**
     * Génère (ou agrandit) l'île de centre c (c.y = hauteur du sol où l'on marche).
     * fromR = 0 pour une nouvelle île.
     */
    static void generate(ServerLevel level, BlockPos c, int fromR, int toR, long seed) {
        int top = c.getY() - 1;
        Random rnd = new Random(seed * 31 + toR);
        int lim = (int) Math.ceil(toR * 1.25) + 2;
        BlockState grass = Blocks.GRASS_BLOCK.defaultBlockState(), dirt = Blocks.DIRT.defaultBlockState(),
                stone = Blocks.STONE.defaultBlockState();
        for (int dx = -lim; dx <= lim; dx++) {
            for (int dz = -lim; dz <= lim; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz), a = Math.atan2(dz, dx);
                double eNew = edge(toR, a, seed);
                if (d > eNew) continue;
                double j = hash(seed, dx, dz) - 0.5;
                int depNew = depth(d, eNew, toR, j);
                int depOld = -1;
                boolean fresh = true;
                if (fromR > 0) {
                    double eOld = edge(fromR, a, seed);
                    if (d <= eOld) { fresh = false; depOld = depth(d, eOld, fromR, j); }
                }
                int x = c.getX() + dx, z = c.getZ() + dz;
                for (int k = 0; k <= depNew; k++) {
                    if (!fresh && k <= depOld) continue;       // déjà généré (et peut-être modifié par le joueur)
                    BlockPos p = new BlockPos(x, top - k, z);
                    if (!level.getBlockState(p).isAir()) continue;
                    BlockState s;
                    if (k == 0) s = grass;
                    else if (k <= 2 + (j > 0.2 ? 1 : 0)) s = dirt;
                    else {
                        double r = rnd.nextDouble();
                        s = r < 0.015 ? Blocks.COAL_ORE.defaultBlockState() : r < 0.022 ? Blocks.IRON_ORE.defaultBlockState()
                                : r < 0.06 ? Blocks.ANDESITE.defaultBlockState() : r < 0.08 ? Blocks.GRAVEL.defaultBlockState() : stone;
                        if (k == depNew && depNew > 3) s = Blocks.DIRT.defaultBlockState();
                    }
                    level.setBlock(p, s, FLAGS);
                }
                if (fresh) decorate(level, new BlockPos(x, top + 1, z), d, rnd);
            }
        }
    }

    private static void decorate(ServerLevel level, BlockPos above, double d, Random rnd) {
        if (d < 4 || !level.getBlockState(above).isAir() || !level.getBlockState(above.below()).is(Blocks.GRASS_BLOCK)) return;
        double r = rnd.nextDouble();
        if (r < 0.018 && d > 5) tree(level, above, rnd);
        else if (r < 0.20) level.setBlock(above, Blocks.SHORT_GRASS.defaultBlockState(), FLAGS);
        else if (r < 0.235) {
            Block[] flowers = {Blocks.POPPY, Blocks.DANDELION, Blocks.CORNFLOWER, Blocks.OXEYE_DAISY, Blocks.AZURE_BLUET};
            level.setBlock(above, flowers[rnd.nextInt(flowers.length)].defaultBlockState(), FLAGS);
        }
    }

    private static void tree(ServerLevel level, BlockPos base, Random rnd) {
        int h = 4 + rnd.nextInt(2);
        BlockState log = Blocks.OAK_LOG.defaultBlockState();
        BlockState leaves = Blocks.OAK_LEAVES.defaultBlockState().setValue(LeavesBlock.PERSISTENT, true);
        for (int dy = h - 2; dy <= h + 1; dy++) {
            int rad = dy >= h ? 1 : 2;
            for (int dx = -rad; dx <= rad; dx++)
                for (int dz = -rad; dz <= rad; dz++) {
                    if (Math.abs(dx) == rad && Math.abs(dz) == rad && (dy == h + 1 || rnd.nextBoolean())) continue;
                    BlockPos p = base.offset(dx, dy, dz);
                    if (level.getBlockState(p).isAir()) level.setBlock(p, leaves, FLAGS);
                }
        }
        for (int dy = 0; dy < h; dy++) level.setBlock(base.above(dy), log, FLAGS);
        level.setBlock(base.below(), Blocks.DIRT.defaultBlockState(), FLAGS);
    }
}
