package fr.cobbleskyblock.islands;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.state.BlockState;

import java.util.Random;

/**
 * L'île de départ d'un royaume : un îlot flottant médiéval (placette pavée, vieille arche en ruine,
 * grand chêne, mare, coin du feu). Elle ne grandit jamais : agrandir son terrain écarte seulement
 * la bordure, au joueur de bâtir autour.
 */
final class IslandGen {
    private IslandGen() {}

    private static final int FLAGS = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE;
    /** Rayon moyen de l'îlot. */
    static final int RADIUS = 13;

    private static double edge(double r, double angle, long seed) {
        Random rnd = new Random(seed);
        double p1 = rnd.nextDouble() * Math.PI * 2, p2 = rnd.nextDouble() * Math.PI * 2, p3 = rnd.nextDouble() * Math.PI * 2;
        return r * (1 + 0.09 * Math.sin(3 * angle + p1) + 0.05 * Math.sin(5 * angle + p2) + 0.03 * Math.sin(8 * angle + p3));
    }

    private static double hash(long seed, int x, int z) {
        long h = seed ^ (x * 341873128712L) ^ (z * 132897987541L);
        h = (h ^ (h >>> 13)) * 0x5DEECE66DL;
        return ((h >>> 16) & 0xFFFF) / 65535.0;
    }

    private static void set(ServerLevel level, BlockPos c, int dx, int dy, int dz, BlockState s) {
        level.setBlock(c.offset(dx, dy, dz), s, FLAGS);
    }

    private static BlockState pick(Random rnd, Block... blocks) { return blocks[rnd.nextInt(blocks.length)].defaultBlockState(); }

    /** Construit l'île autour de c (c.y = hauteur où l'on marche ; le joueur apparaît en c, tourné vers le nord). */
    static void build(ServerLevel level, BlockPos c, long seed) {
        Random rnd = new Random(seed);
        int lim = RADIUS + 4;
        // ---- terrain : herbe, terre, roche, pointe d'ardoise des profondeurs
        for (int dx = -lim; dx <= lim; dx++) {
            for (int dz = -lim; dz <= lim; dz++) {
                double d = Math.sqrt(dx * dx + dz * dz), e = edge(RADIUS, Math.atan2(dz, dx), seed);
                if (d > e) continue;
                double j = hash(seed, dx, dz) - 0.5, t = d / e;
                int depth = Math.max(1, (int) Math.round(17 * (1 - Math.pow(t, 1.7)) + 1 + j * 3));
                boolean rim = d > e - 1.6;
                for (int k = 0; k <= depth; k++) {
                    BlockState s;
                    if (k == 0) s = rim && rnd.nextInt(3) == 0 ? pick(rnd, Blocks.MOSS_BLOCK, Blocks.MOSSY_COBBLESTONE, Blocks.COARSE_DIRT) : Blocks.GRASS_BLOCK.defaultBlockState();
                    else if (k <= 2 + (j > 0.2 ? 1 : 0)) s = Blocks.DIRT.defaultBlockState();
                    else if (k > depth * 0.62) s = rnd.nextInt(4) == 0 ? Blocks.COBBLED_DEEPSLATE.defaultBlockState() : Blocks.DEEPSLATE.defaultBlockState();
                    else {
                        double r = rnd.nextDouble();
                        s = r < 0.02 ? Blocks.COAL_ORE.defaultBlockState() : r < 0.03 ? Blocks.IRON_ORE.defaultBlockState()
                                : r < 0.09 ? Blocks.ANDESITE.defaultBlockState() : r < 0.14 ? Blocks.COBBLESTONE.defaultBlockState()
                                : r < 0.17 ? Blocks.MOSSY_COBBLESTONE.defaultBlockState() : Blocks.STONE.defaultBlockState();
                    }
                    set(level, c, dx, -1 - k, dz, s);
                }
            }
        }
        // ---- placette pavée au centre, allée vers le nord
        for (int dx = -3; dx <= 3; dx++)
            for (int dz = -3; dz <= 3; dz++)
                if (dx * dx + dz * dz <= 11)
                    set(level, c, dx, -1, dz, pick(rnd, Blocks.STONE_BRICKS, Blocks.STONE_BRICKS, Blocks.MOSSY_STONE_BRICKS, Blocks.CRACKED_STONE_BRICKS, Blocks.COBBLESTONE));
        set(level, c, 0, -1, 0, Blocks.CHISELED_STONE_BRICKS.defaultBlockState());
        for (int dz = -8; dz <= -4; dz++)
            for (int dx = -1; dx <= 0; dx++)
                set(level, c, dx, -1, dz, rnd.nextInt(5) == 0 ? pick(rnd, Blocks.GRAVEL, Blocks.COARSE_DIRT) : Blocks.DIRT_PATH.defaultBlockState());
        // lanternes sur poteaux, de part et d'autre de l'allée
        for (int dx : new int[]{-3, 2}) {
            for (int y = 0; y < 2; y++) set(level, c, dx, y, -3, Blocks.DARK_OAK_FENCE.defaultBlockState());
            set(level, c, dx, 2, -3, Blocks.LANTERN.defaultBlockState());
        }
        // ---- vieille arche en ruine au bout de l'allée
        int az = -9;
        int[] px = {-3, 2}, ph = {5, 3};
        for (int i = 0; i < 2; i++) {
            for (int y = 0; y < ph[i]; y++)
                set(level, c, px[i], y, az, pick(rnd, Blocks.STONE_BRICKS, Blocks.STONE_BRICKS, Blocks.MOSSY_STONE_BRICKS, Blocks.CRACKED_STONE_BRICKS));
            set(level, c, px[i], -1, az, Blocks.STONE_BRICKS.defaultBlockState());
        }
        for (int dx = -3; dx <= 0; dx++) set(level, c, dx, 5, az, pick(rnd, Blocks.STONE_BRICKS, Blocks.MOSSY_STONE_BRICKS));
        set(level, c, -2, 4, az, Blocks.MOSSY_STONE_BRICKS.defaultBlockState());
        set(level, c, 1, 5, az, Blocks.STONE_BRICK_SLAB.defaultBlockState());
        set(level, c, -3, 6, az, Blocks.STONE_BRICK_SLAB.defaultBlockState());
        set(level, c, -1, 6, az, Blocks.RED_BANNER.defaultBlockState());
        set(level, c, 2, 3, az, Blocks.MOSSY_STONE_BRICK_SLAB.defaultBlockState());
        set(level, c, 3, 0, az, Blocks.MOSSY_COBBLESTONE.defaultBlockState());          // éboulis
        set(level, c, 3, 0, az + 1, Blocks.COBBLESTONE_SLAB.defaultBlockState());
        set(level, c, -4, 0, az, Blocks.MOSSY_COBBLESTONE_WALL.defaultBlockState());
        set(level, c, -4, 0, az + 1, Blocks.MOSS_CARPET.defaultBlockState());
        // ---- grand chêne à l'ouest, lanterne pendue à une branche
        int tx = -7, tz = -2;
        BlockState log = Blocks.OAK_LOG.defaultBlockState();
        BlockState leaves = Blocks.OAK_LEAVES.defaultBlockState().setValue(LeavesBlock.PERSISTENT, true);
        for (int dy = 2; dy <= 9; dy++) {
            double rad = dy <= 3 ? 2.4 : dy <= 6 ? 3.7 : dy == 7 ? 3.0 : dy == 8 ? 2.2 : 1.2;
            for (int dx = -4; dx <= 4; dx++)
                for (int dz = -4; dz <= 4; dz++) {
                    double dd = Math.sqrt(dx * dx + dz * dz) + (rnd.nextDouble() - 0.5) * 0.9;
                    if (dd <= rad) set(level, c, tx + dx, dy, tz + dz, leaves);
                }
        }
        for (int dy = 0; dy <= 6; dy++) set(level, c, tx, dy, tz, log);
        set(level, c, tx, -1, tz, Blocks.DIRT.defaultBlockState());
        set(level, c, tx + 1, 0, tz, Blocks.OAK_LOG.defaultBlockState().setValue(RotatedPillarBlock.AXIS, Direction.Axis.X));     // racine
        set(level, c, tx, 0, tz + 1, Blocks.OAK_LOG.defaultBlockState().setValue(RotatedPillarBlock.AXIS, Direction.Axis.Z));
        BlockState branch = Blocks.OAK_LOG.defaultBlockState().setValue(RotatedPillarBlock.AXIS, Direction.Axis.X);
        set(level, c, tx + 1, 4, tz, branch); set(level, c, tx + 2, 4, tz, branch);
        set(level, c, tx + 2, 3, tz, Blocks.CHAIN.defaultBlockState());
        set(level, c, tx + 2, 2, tz, Blocks.LANTERN.defaultBlockState().setValue(LanternBlock.HANGING, true));
        set(level, c, tx - 1, 5, tz, branch);
        // ---- mare à l'est
        int mx = 6, mz = 4;
        for (int dx = -3; dx <= 3; dx++)
            for (int dz = -3; dz <= 3; dz++) {
                double dd = Math.sqrt(dx * dx + dz * dz * 1.3);
                if (dd <= 2.3) {
                    set(level, c, mx + dx, -1, mz + dz, Blocks.WATER.defaultBlockState());
                    set(level, c, mx + dx, -2, mz + dz, pick(rnd, Blocks.GRAVEL, Blocks.CLAY, Blocks.SAND));
                } else if (dd <= 3.3 && rnd.nextInt(3) != 0) {
                    set(level, c, mx + dx, -1, mz + dz, pick(rnd, Blocks.MOSS_BLOCK, Blocks.MOSSY_COBBLESTONE, Blocks.STONE, Blocks.GRASS_BLOCK));
                }
            }
        set(level, c, mx - 1, 0, mz, Blocks.LILY_PAD.defaultBlockState());
        set(level, c, mx + 1, 0, mz + 1, Blocks.LILY_PAD.defaultBlockState());
        set(level, c, mx + 3, 0, mz - 1, Blocks.FLOWERING_AZALEA.defaultBlockState());
        // ---- coin du feu au sud-ouest : feu de camp, bancs de rondins, foin, tonneau, établi
        set(level, c, -4, 0, 6, Blocks.CAMPFIRE.defaultBlockState());
        set(level, c, -4, -1, 6, Blocks.COARSE_DIRT.defaultBlockState());
        set(level, c, -6, 0, 6, Blocks.SPRUCE_LOG.defaultBlockState().setValue(RotatedPillarBlock.AXIS, Direction.Axis.Z));
        set(level, c, -4, 0, 8, Blocks.SPRUCE_LOG.defaultBlockState().setValue(RotatedPillarBlock.AXIS, Direction.Axis.X));
        set(level, c, -7, 0, 8, Blocks.HAY_BLOCK.defaultBlockState());
        set(level, c, -7, 1, 8, Blocks.HAY_BLOCK.defaultBlockState());
        set(level, c, -8, 0, 7, Blocks.HAY_BLOCK.defaultBlockState().setValue(RotatedPillarBlock.AXIS, Direction.Axis.X));
        set(level, c, -6, 0, 9, Blocks.BARREL.defaultBlockState().setValue(net.minecraft.world.level.block.BarrelBlock.FACING, Direction.UP));
        set(level, c, -2, 0, 9, Blocks.CRAFTING_TABLE.defaultBlockState());
        // ---- herbes, fleurs, buissons (jamais sur la placette, l'allée ni le décor)
        Block[] flowers = {Blocks.POPPY, Blocks.DANDELION, Blocks.CORNFLOWER, Blocks.OXEYE_DAISY, Blocks.AZURE_BLUET, Blocks.ALLIUM};
        for (int dx = -lim; dx <= lim; dx++)
            for (int dz = -lim; dz <= lim; dz++) {
                BlockPos p = c.offset(dx, 0, dz);
                if (dx * dx + dz * dz <= 16 || !level.getBlockState(p).isAir() || !level.getBlockState(p.below()).is(Blocks.GRASS_BLOCK)) continue;
                double r = rnd.nextDouble();
                if (r < 0.16) level.setBlock(p, Blocks.SHORT_GRASS.defaultBlockState(), FLAGS);
                else if (r < 0.20) level.setBlock(p, flowers[rnd.nextInt(flowers.length)].defaultBlockState(), FLAGS);
                else if (r < 0.208) level.setBlock(p, Blocks.AZALEA.defaultBlockState(), FLAGS);
            }
        // l'endroit où l'on apparaît reste dégagé
        for (int y = 0; y < 3; y++) set(level, c, 0, y, 0, Blocks.AIR.defaultBlockState());
    }
}
