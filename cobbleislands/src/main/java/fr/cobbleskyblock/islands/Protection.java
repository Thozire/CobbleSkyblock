package fr.cobbleskyblock.islands;

import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BucketItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.level.Level;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Protection des îles : dans la dimension des îles, seuls les membres d'une île
 * peuvent casser, poser ou utiliser quoi que ce soit, et seulement dans la zone
 * constructible de leur île. Les opérateurs ne sont pas bloqués.
 */
public final class Protection {
    private Protection() {}

    private static final Map<UUID, Long> lastWarn = new HashMap<>();

    /** Au spawn, on peut utiliser les blocs (machine de soin, PC, portes) mais pas poser de blocs. */
    public static boolean allowedUse(Player player, Level level, BlockPos pos, ItemStack held) {
        if (!level.isClientSide() && level.dimension() == Level.OVERWORLD && !(held.getItem() instanceof net.minecraft.world.item.BlockItem)
                && !(held.getItem() instanceof BucketItem)) return true;
        return allowed(player, level, pos);
    }

    /** Le joueur peut-il agir à cette position ? (et prévient le joueur sinon) */
    public static boolean allowed(Player player, Level level, BlockPos pos) {
        if (level.isClientSide() || player.hasPermissions(2)) return true;
        IslandManager m = CobbleIslands.manager();
        if (m == null) return true;
        if (level.dimension() == Level.OVERWORLD) {
            IslandData d = m.data();
            int r = m.config().protectionSpawn;
            if (d.spawnBuilt && Math.abs(pos.getX() - d.spawnX) <= r && Math.abs(pos.getZ() - d.spawnZ) <= r) {
                warn(player, "Le spawn est protégé.");
                return false;
            }
            return true;
        }
        if (level.dimension() != IslandManager.ISLANDS) return true;
        Island is = m.islandAt(pos);
        if (is != null && is.isMember(player.getUUID()) && m.inBounds(is, pos)) return true;
        warn(player, is == null || !is.isMember(player.getUUID())
                ? "Tu ne peux rien modifier ici : ce n'est pas ton île."
                : "Limite de ton île atteinte : agrandis-la pour construire plus loin.");
        return false;
    }

    private static void warn(Player p, String msg) {
        long now = System.currentTimeMillis();
        Long last = lastWarn.get(p.getUUID());
        if (last == null || now - last > 2000) {
            lastWarn.put(p.getUUID(), now);
            if (p instanceof ServerPlayer sp) sp.displayClientMessage(Msg.err(msg), true);
        }
    }

    public static void register() {
        PlayerBlockBreakEvents.BEFORE.register((level, player, pos, state, be) -> allowed(player, level, pos));
        AttackBlockCallback.EVENT.register((player, level, hand, pos, dir) ->
                allowed(player, level, pos) ? InteractionResult.PASS : InteractionResult.FAIL);
        UseBlockCallback.EVENT.register((player, level, hand, hit) ->
                allowedUse(player, level, hit.getBlockPos(), player.getItemInHand(hand)) ? InteractionResult.PASS : InteractionResult.FAIL);
        UseEntityCallback.EVENT.register((player, level, hand, entity, hit) ->
                entity instanceof Player || level.dimension() == Level.OVERWORLD || allowed(player, level, entity.blockPosition())
                        ? InteractionResult.PASS : InteractionResult.FAIL);
        AttackEntityCallback.EVENT.register((player, level, hand, entity, hit) ->
                entity instanceof Player || allowed(player, level, entity.blockPosition()) ? InteractionResult.PASS : InteractionResult.FAIL);
        UseItemCallback.EVENT.register((player, level, hand) -> {
            ItemStack stack = player.getItemInHand(hand);
            boolean risky = stack.getItem() instanceof BucketItem || stack.getItem() instanceof SpawnEggItem;
            if (risky && !allowed(player, level, player.blockPosition())) return InteractionResultHolder.fail(stack);
            return InteractionResultHolder.pass(stack);
        });
    }
}
