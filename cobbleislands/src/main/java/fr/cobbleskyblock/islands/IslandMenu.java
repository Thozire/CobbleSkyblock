package fr.cobbleskyblock.islands;

import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.ItemStack;

import java.util.HashMap;
import java.util.Map;
import java.util.function.Consumer;

/**
 * Menu "coffre" 6 rangées dont les objets sont des boutons. Rien ne peut être
 * pris ni déposé. Le titre utilise la police du resource pack pour afficher le
 * fond personnalisé (glyphe  décalé par des espaces négatifs).
 */
public class IslandMenu extends ChestMenu {
    private static final ResourceLocation GUI_FONT = ResourceLocation.fromNamespaceAndPath("cobbleislands", "gui");
    private final Map<Integer, Consumer<ServerPlayer>> actions = new HashMap<>();

    public IslandMenu(int id, Inventory inv) {
        super(MenuType.GENERIC_9x6, id, inv, new SimpleContainer(54), 6);
    }

    public void set(int slot, ItemStack stack, Consumer<ServerPlayer> action) {
        getContainer().setItem(slot, stack);
        if (action != null) actions.put(slot, action);
        else actions.remove(slot);
    }

    public void set(int slot, ItemStack stack) { set(slot, stack, null); }

    @Override
    public void clicked(int slotId, int button, ClickType type, Player player) {
        if (player instanceof ServerPlayer sp && slotId >= 0 && slotId < 54 && type != ClickType.QUICK_CRAFT) {
            Consumer<ServerPlayer> a = actions.get(slotId);
            if (a != null) {
                sp.playNotifySound(SoundEvents.UI_BUTTON_CLICK.value(), SoundSource.MASTER, 0.5f, 1.2f);
                a.accept(sp);
            }
        }
        // on annule tout déplacement d'objet et on resynchronise l'écran du joueur
        setCarried(ItemStack.EMPTY);
        sendAllDataToRemote();
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) { return ItemStack.EMPTY; }

    @Override
    public boolean stillValid(Player player) { return true; }

    /** Titre : fond personnalisé + texte. */
    public static Component title(String text) {
        MutableComponent bg = Component.literal("").withStyle(Style.EMPTY.withFont(GUI_FONT).withColor(0xFFFFFF));
        return bg.append(Component.literal(text).withStyle(s -> s.withColor(0xF3E8FF).withBold(true)));
    }

    /** Ouvre un menu rempli par {@code fill}. */
    public static void open(ServerPlayer p, String title, Consumer<IslandMenu> fill) {
        p.openMenu(new SimpleMenuProvider((id, inv, pl) -> {
            IslandMenu m = new IslandMenu(id, inv);
            fill.accept(m);
            return m;
        }, title(title)));
    }
}
