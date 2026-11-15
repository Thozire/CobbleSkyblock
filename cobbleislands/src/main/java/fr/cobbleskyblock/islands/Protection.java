package fr.cobbleskyblock.islands;

import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.BucketItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.level.Level;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Protection : dans la dimension des royaumes, seuls les membres agissent sur leur domaine ;
 * la capitale est protégée (on peut utiliser, pas construire). Les opérateurs passent partout.
 * Gère aussi les pupitres des bâtiments et le marchand de la capitale.
 */
public final class Protection {
    private Protection() {}

    public static final String MERCHANT_TAG = "royaumes_marchand";
    private static final Map<UUID, Long> lastWarn = new HashMap<>();

    public static boolean allowed(Player player, Level level, BlockPos pos) {
        if (level.isClientSide() || player.hasPermissions(2)) return true;
        IslandManager m = CobbleIslands.manager();
        if (m == null) return true;
        if (level.dimension() == Level.OVERWORLD) {
            IslandData d = m.data();
            int r = m.config().protectionSpawn;
            if (d.spawnBuilt && Math.abs(pos.getX() - d.spawnX) <= r && Math.abs(pos.getZ() - d.spawnZ) <= r) {
                warn(player, "La capitale est protégée.");
                return false;
            }
            return true;
        }
        if (level.dimension() != IslandManager.ISLANDS) return true;
        Island is = m.islandAt(pos);
        if (is != null && is.isMember(player.getUUID()) && m.inBounds(is, pos)) return true;
        warn(player, is == null || !is.isMember(player.getUUID())
                ? "Ce domaine ne t'appartient pas."
                : "Limite de ton domaine : agrandis-le pour aller plus loin.");
        return false;
    }

    /** À la capitale on peut utiliser les blocs (portes, boutons) mais pas poser. */
    private static boolean allowedUse(Player player, Level level, BlockPos pos, ItemStack held) {
        if (!level.isClientSide() && level.dimension() == Level.OVERWORLD
                && !(held.getItem() instanceof BlockItem) && !(held.getItem() instanceof BucketItem)) return true;
        return allowed(player, level, pos);
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
        UseBlockCallback.EVENT.register((player, level, hand, hit) -> {
            // pupitre d'un bâtiment : ouvre son menu
            if (!level.isClientSide() && player instanceof ServerPlayer sp && level.dimension() == IslandManager.ISLANDS) {
                IslandManager m = CobbleIslands.manager();
                Island is = m == null ? null : m.islandAt(hit.getBlockPos());
                Building b = is == null ? null : m.buildingAtLectern(is, hit.getBlockPos());
                if (b != null) {
                    if (hand == InteractionHand.MAIN_HAND) {
                        if (is.isMember(sp.getUUID())) KingdomMenus.building(sp, b.id);
                        else sp.displayClientMessage(Msg.info(b.type.label + " (niv. " + b.level + ") du " + is.name), true);
                    }
                    return InteractionResult.SUCCESS;
                }
            }
            return allowedUse(player, level, hit.getBlockPos(), player.getItemInHand(hand)) ? InteractionResult.PASS : InteractionResult.FAIL;
        });
        UseEntityCallback.EVENT.register((player, level, hand, entity, hit) -> {
            if (entity.getTags().contains(MERCHANT_TAG)) {
                if (!level.isClientSide() && hand == InteractionHand.MAIN_HAND && player instanceof ServerPlayer sp) KingdomMenus.market(sp);
                return InteractionResult.SUCCESS;
            }
            return entity instanceof Player || level.dimension() == Level.OVERWORLD || allowed(player, level, entity.blockPosition())
                    ? InteractionResult.PASS : InteractionResult.FAIL;
        });
        AttackEntityCallback.EVENT.register((player, level, hand, entity, hit) -> {
            if (entity.getTags().contains(MERCHANT_TAG)) return InteractionResult.FAIL;
            return entity instanceof Player || allowed(player, level, entity.blockPosition()) ? InteractionResult.PASS : InteractionResult.FAIL;
        });
        UseItemCallback.EVENT.register((player, level, hand) -> {
            ItemStack stack = player.getItemInHand(hand);
            boolean risky = stack.getItem() instanceof BucketItem || stack.getItem() instanceof SpawnEggItem;
            if (risky && !allowed(player, level, player.blockPosition())) return InteractionResultHolder.fail(stack);
            return InteractionResultHolder.pass(stack);
        });
    }
}
