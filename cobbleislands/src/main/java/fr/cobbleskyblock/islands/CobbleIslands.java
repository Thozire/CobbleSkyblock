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

/** Point d'entrée du mod Royaumes (tycoon médiéval). */
public class CobbleIslands implements ModInitializer {
    public static final Logger LOG = LoggerFactory.getLogger("Royaumes");
    private static IslandManager manager;

    public static IslandManager manager() { return manager; }

    @Override
    public void onInitialize() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registries, env) -> RoyaumeCommands.register(dispatcher));
        Protection.register();

        ServerLifecycleEvents.SERVER_STARTED.register(server -> {
            manager = new IslandManager(server, IslandConfig.load());
            if (!manager.data().spawnBuilt) SpawnBuilder.build(manager, false);
            ResourcePackSender.init(manager.config());
            LOG.info("Royaumes prêt : {} royaume(s), dimension {}", manager.data().islands.size(),
                    manager.islandsLevel() != null ? "chargée" : "ABSENTE");
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> manager = null);

        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            if (manager == null) return;
            ServerPlayer p = handler.getPlayer();
            ResourcePackSender.send(p, manager.config());
            Hud.forget(p.getUUID());
            manager.forgetBorder(p.getUUID());
            Island is = manager.islandOf(p.getUUID());
            if (is == null) {
                p.sendSystemMessage(Msg.info("Bienvenue à la capitale, voyageur ! ")
                        .append(Msg.button("Fonder mon royaume", "/royaume", ChatFormatting.GOLD)));
            } else {
                is.members.put(p.getUUID(), p.getGameProfile().getName());
                manager.data().setDirty();
                p.sendSystemMessage(Msg.info("Bon retour, seigneur. Ton trésor : §6" + Market.fmt(is.money) + " écus §7— ")
                        .append(Msg.button("Menu", "/royaume", ChatFormatting.AQUA)));
            }
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            Hud.forget(handler.getPlayer().getUUID());
            if (manager != null) manager.forgetBorder(handler.getPlayer().getUUID());
        });

        ServerTickEvents.END_SERVER_TICK.register(CobbleIslands::tick);
    }

    private static int ticks;

    private static void tick(MinecraftServer server) {
        if (manager == null) return;
        ticks++;
        if (ticks % 20 == 0) manager.produce();
        if (ticks % 20 == 10) IslandMenu.refreshLive(server);
        if (ticks % MachineEntities.STEP_TICKS == 0) manager.animate();
        if (ticks % 10 == 0) manager.watchPlayers();
        if (ticks % 40 == 0) for (ServerPlayer p : server.getPlayerList().getPlayers()) Hud.update(p, manager);
        if (ticks % 1200 == 0) SpawnBuilder.refreshLeaderboard(manager);
    }
}
