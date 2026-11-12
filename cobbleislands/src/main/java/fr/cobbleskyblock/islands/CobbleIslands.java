package fr.cobbleskyblock.islands;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CobbleIslands implements ModInitializer {
    public static final Logger LOG = LoggerFactory.getLogger("CobbleIslands");
    private static IslandManager manager;

    public static IslandManager manager() { return manager; }

    @Override
    public void onInitialize() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registries, env) -> IslandCommands.register(dispatcher));
        Protection.register();

        ServerLifecycleEvents.SERVER_STARTED.register(server -> {
            manager = new IslandManager(server, IslandConfig.load());
            if (!manager.data().spawnBuilt) SpawnBuilder.build(manager, false);
            int n = manager.data().islands.size();
            LOG.info("CobbleIslands prêt : {} île(s), dimension {}", n,
                    manager.islandsLevel() != null ? "chargée" : "ABSENTE");
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> manager = null);

        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            ServerPlayer p = handler.getPlayer();
            if (manager == null) return;
            Island is = manager.islandOf(p.getUUID());
            if (is == null) {
                p.sendSystemMessage(Msg.info("Bienvenue sur CobbleSkyblock ! Tu n'as pas encore d'île. ")
                        .append(Msg.button("Créer mon île", "/ile creer", ChatFormatting.GREEN)));
            } else {
                // garde le pseudo à jour si le joueur en a changé
                is.members.put(p.getUUID(), p.getGameProfile().getName());
                manager.data().setDirty();
            }
        });

        ServerTickEvents.END_SERVER_TICK.register(CobbleIslands::tick);
    }

    private static int ticks;

    /** Toutes les demi-secondes : sauvetage des joueurs tombés dans le vide. */
    private static void tick(MinecraftServer server) {
        if (manager == null || ++ticks % 10 != 0) return;
        if (!manager.config().sauvetageVide) return;
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            if (p.level().dimension() != IslandManager.ISLANDS || p.isSpectator()) continue;
            if (p.getY() > p.level().getMinBuildHeight() + 8) continue;
            Island is = manager.islandAt(p.blockPosition());
            if (is == null) is = manager.islandOf(p.getUUID());
            p.fallDistance = 0;
            if (is != null) {
                net.minecraft.core.BlockPos h = is.home;
                p.teleportTo(manager.islandsLevel(), h.getX() + 0.5, h.getY(), h.getZ() + 0.5, p.getYRot(), p.getXRot());
            } else {
                manager.teleportSpawn(p);
            }
            p.displayClientMessage(Msg.info("Rattrapé de justesse !"), true);
        }
    }
}
