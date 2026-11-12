package fr.cobbleskyblock.islands;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

import java.util.Optional;

/**
 * Construit le spawn (île hub commune) dans l'Overworld au premier démarrage :
 * structure cobbleislands:spawn + textes flottants + machine à fusion.
 */
public final class SpawnBuilder {
    private SpawnBuilder() {}

    /** Position du centre (fontaine) dans la structure du spawn, et hauteur du sol. */
    private static final int TPL_CENTER = 15, TPL_GROUND = 7;
    private static final String TAG = "cobbleislands_spawn";

    public static void build(IslandManager m, boolean rebuild) {
        MinecraftServer server = m.server();
        ServerLevel ow = server.overworld();
        IslandData d = m.data();
        // le point d'apparition est 4 blocs au sud de la fontaine
        int sx = rebuild && d.spawnBuilt ? d.spawnX : 0;
        int sz = rebuild && d.spawnBuilt ? d.spawnZ - 4 : 0;
        int sy = m.config().hauteurSpawn;
        Optional<StructureTemplate> tpl = server.getStructureManager().get(ResourceLocation.parse(m.config().modeleSpawn));
        if (tpl.isEmpty()) {
            CobbleIslands.LOG.error("Structure {} introuvable : spawn non construit", m.config().modeleSpawn);
            return;
        }
        BlockPos origin = new BlockPos(sx - TPL_CENTER, sy - TPL_GROUND, sz - TPL_CENTER);
        tpl.get().placeInWorld(ow, origin, origin, new StructurePlaceSettings(), ow.getRandom(), Block.UPDATE_CLIENTS);

        run(server, "kill @e[type=minecraft:text_display,tag=" + TAG + "]");
        run(server, "kill @e[type=minecraft:item_display,tag=" + TAG + "]");
        text(server, sx + 0.5, sy + 5.2, sz + 0.5, "{\"text\":\"CobbleSkyblock\",\"color\":\"light_purple\",\"bold\":true}", 2.5f);
        text(server, sx + 0.5, sy + 4.5, sz + 0.5, "{\"text\":\"Pokémon, îles et machine à fusion\",\"color\":\"gray\"}", 1.2f);
        text(server, sx + 0.5, sy + 3.0, sz + 2.5,
                "[{\"text\":\"Tape \",\"color\":\"white\"},{\"text\":\"/ile\",\"color\":\"aqua\",\"bold\":true},{\"text\":\" pour aller sur ton île\",\"color\":\"white\"}]", 1.0f);
        text(server, sx + 0.5, sy + 5.6, sz - 8.4, "{\"text\":\"Centre Pokémon\",\"color\":\"red\",\"bold\":true}", 1.5f);
        text(server, sx + 11.0, sy + 4.2, sz + 0.5, "{\"text\":\"Machine à fusion\",\"color\":\"light_purple\",\"bold\":true}", 1.3f);
        text(server, sx + 11.0, sy + 3.7, sz + 0.5, "{\"text\":\"Bientôt disponible\",\"color\":\"gray\",\"italic\":true}", 1.0f);
        run(server, String.format(java.util.Locale.ROOT,
                "summon minecraft:item_display %.2f %.2f %.2f {Tags:[\"%s\"],item_display:\"none\",brightness:{sky:15,block:15},"
                        + "item:{id:\"minecraft:paper\",count:1,components:{\"minecraft:custom_model_data\":7001}}}",
                sx + 11.0, sy + 1.5, sz + 0.5, TAG));

        setSpawn(m, new BlockPos(sx, sy + 1, sz + 4));
        CobbleIslands.LOG.info("Spawn construit en {} {} {}", sx, sy, sz);
    }

    /** Fixe le point d'apparition du serveur (et celui de /spawn). */
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
        run(server, String.format(java.util.Locale.ROOT,
                "summon minecraft:text_display %.2f %.2f %.2f {Tags:[\"%s\"],billboard:\"center\",background:0,shadow:1b,"
                        + "transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[%.2ff,%.2ff,%.2ff]},text:'%s'}",
                x, y, z, TAG, scale, scale, scale, json.replace("'", "\\'")));
    }

    private static void run(MinecraftServer server, String cmd) {
        CommandSourceStack src = server.createCommandSourceStack().withSuppressedOutput().withPermission(4);
        server.getCommands().performPrefixedCommand(src, cmd);
    }
}
