package fr.cobbleskyblock.islands;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

import java.util.List;
import java.util.Locale;
import java.util.Optional;

/**
 * La capitale (spawn commun) : île céleste avec château, marché, puits et tableau du classement.
 * Construite dans l'Overworld au premier démarrage.
 */
public final class SpawnBuilder {
    private SpawnBuilder() {}

    /** Centre (puits) et hauteur du sol dans la structure cobbleislands:capitale. */
    private static final int TPL_CENTER = 22, TPL_GROUND = 8;
    private static final String TAG = "royaumes_capitale", TOP_TAG = "royaumes_top";

    /** Centre de la capitale (le point d'apparition est 9 blocs au sud). */
    private static int[] center(IslandManager m) {
        IslandData d = m.data();
        return d.spawnBuilt ? new int[]{d.spawnX, d.spawnY - 1, d.spawnZ - 9} : new int[]{0, m.config().hauteurSpawn, 0};
    }

    public static void build(IslandManager m, boolean rebuild) {
        MinecraftServer server = m.server();
        ServerLevel ow = server.overworld();
        int[] c = rebuild ? center(m) : new int[]{0, m.config().hauteurSpawn, 0};
        int sx = c[0], sy = c[1], sz = c[2];
        Optional<StructureTemplate> tpl = server.getStructureManager().get(ResourceLocation.parse(m.config().modeleSpawn));
        if (tpl.isEmpty()) {
            CobbleIslands.LOG.error("Structure {} introuvable : capitale non construite", m.config().modeleSpawn);
            return;
        }
        BlockPos origin = new BlockPos(sx - TPL_CENTER, sy - TPL_GROUND, sz - TPL_CENTER);
        tpl.get().placeInWorld(ow, origin, origin, new StructurePlaceSettings(), ow.getRandom(), Block.UPDATE_CLIENTS);

        run(server, "kill @e[tag=" + TAG + "]");
        text(server, sx + 0.5, sy + 6.4, sz + 0.5, "{\"text\":\"Capitale\",\"color\":\"gold\",\"bold\":true}", 2.4f);
        text(server, sx + 0.5, sy + 5.7, sz + 0.5, "{\"text\":\"Bienvenue dans les Royaumes\",\"color\":\"#F3E3B5\"}", 1.1f);
        text(server, sx + 0.5, sy + 2.9, sz + 6.5,
                "[{\"text\":\"Tape \",\"color\":\"white\"},{\"text\":\"/royaume\",\"color\":\"gold\",\"bold\":true},{\"text\":\" pour fonder ton royaume\",\"color\":\"white\"}]", 1.0f);
        text(server, sx + 7.5, sy + 4.9, sz + 7.5, "{\"text\":\"Marchand\",\"color\":\"gold\",\"bold\":true}", 1.3f);
        text(server, sx + 7.5, sy + 4.45, sz + 7.5, "{\"text\":\"Clic droit pour vendre\",\"color\":\"gray\",\"italic\":true}", 0.9f);
        run(server, String.format(Locale.ROOT, "summon minecraft:villager %.2f %.2f %.2f {Tags:[\"%s\",\"%s\"],NoAI:1b,Invulnerable:1b,Silent:1b,"
                        + "PersistenceRequired:1b,Rotation:[0f,0f],CustomName:'{\"text\":\"Marchand\",\"color\":\"gold\"}',"
                        + "VillagerData:{type:\"minecraft:plains\",profession:\"minecraft:farmer\",level:5}}",
                sx + 7.5, sy + 1.0, sz + 7.5, TAG, Protection.MERCHANT_TAG));

        setSpawn(m, new BlockPos(sx, sy + 1, sz + 9));
        refreshLeaderboard(m);
        CobbleIslands.LOG.info("Capitale construite en {} {} {}", sx, sy, sz);
    }

    /** Met à jour le tableau des 5 royaumes les plus riches, à côté du puits. */
    public static void refreshLeaderboard(IslandManager m) {
        if (!m.data().spawnBuilt) return;
        int[] c = center(m);
        MinecraftServer server = m.server();
        run(server, "kill @e[type=minecraft:text_display,tag=" + TOP_TAG + "]");
        List<Island> top = m.ranking();
        StringBuilder sb = new StringBuilder("[{\"text\":\"♛ Royaumes les plus riches ♛\\n\",\"color\":\"gold\",\"bold\":true}");
        if (top.isEmpty()) sb.append(",{\"text\":\"Aucun royaume pour l'instant\",\"color\":\"gray\",\"italic\":true}");
        for (int i = 0; i < Math.min(5, top.size()); i++) {
            Island is = top.get(i);
            String col = i == 0 ? "gold" : i == 1 ? "#D9D9D9" : i == 2 ? "#E0915A" : "white";
            sb.append(",{\"text\":\"").append(i + 1).append(". \",\"color\":\"").append(col).append("\",\"bold\":false}")
                    .append(",{\"text\":\"").append(esc(is.name)).append("  \",\"color\":\"white\",\"bold\":false}")
                    .append(",{\"text\":\"").append(Market.fmt(is.totalEarned)).append(" écus").append(i < 4 ? "\\n" : "").append("\",\"color\":\"gold\",\"bold\":false}");
        }
        sb.append("]");
        run(server, String.format(Locale.ROOT,
                "summon minecraft:text_display %.2f %.2f %.2f {Tags:[\"%s\",\"%s\"],billboard:\"center\",background:-1442840576,line_width:260,text:'%s'}",
                c[0] - 6.9, c[1] + 2.0, c[2] + 0.5, TAG, TOP_TAG, sb.toString().replace("'", "\\'")));
    }

    private static String esc(String s) { return s.replace("\\", "").replace("\"", "'"); }

    public static void setSpawn(IslandManager m, BlockPos pos) {
        IslandData d = m.data();
        d.spawnBuilt = true;
        d.spawnX = pos.getX();
        d.spawnY = pos.getY();
        d.spawnZ = pos.getZ();
        d.setDirty();
        m.server().overworld().setDefaultSpawnPos(pos, 180f);
        run(m.server(), "gamerule spawnRadius 0");
    }

    private static void text(MinecraftServer server, double x, double y, double z, String json, float scale) {
        run(server, String.format(Locale.ROOT,
                "summon minecraft:text_display %.2f %.2f %.2f {Tags:[\"%s\"],billboard:\"center\",background:0,shadow:1b,"
                        + "transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[%.2ff,%.2ff,%.2ff]},text:'%s'}",
                x, y, z, TAG, scale, scale, scale, json.replace("'", "\\'")));
    }

    private static void run(MinecraftServer server, String cmd) {
        CommandSourceStack src = server.createCommandSourceStack().withSuppressedOutput().withPermission(4);
        server.getCommands().performPrefixedCommand(src, cmd);
    }
}
