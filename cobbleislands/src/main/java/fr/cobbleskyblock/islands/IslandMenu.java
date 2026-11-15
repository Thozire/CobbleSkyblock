package fr.cobbleskyblock.islands;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

import java.util.HashMap;
import java.util.Map;
import java.util.function.Consumer;

/**
 * Menu « coffre » 6 rangées dont les objets sont des boutons.
 * <ul>
 * <li>Le fond (pages dessinées) est fait de glyphes de la police du resource pack, placés dans le titre.</li>
 * <li>Les 36 cases du bas (l'inventaire du joueur) pointent vers un inventaire vide :
 * le joueur ne voit pas ses objets dans le menu, et ses vrais objets ne sont jamais touchés.
 * À la fermeture, on renvoie son vrai inventaire à son client.</li>
 * </ul>
 */
public class IslandMenu extends AbstractContainerMenu {
    /** Pages du menu. Seule la page principale a déjà son fond dessiné (voir RoyalGui). */
    public enum Page { MAIN, LIST, BUILDING, DOMAIN, CONFIRM, START }

    private final SimpleContainer buttons = new SimpleContainer(54);
    private final Map<Integer, Consumer<ServerPlayer>> actions = new HashMap<>();

    public IslandMenu(int id) {
        super(MenuType.GENERIC_9x6, id);
        for (int r = 0; r < 6; r++)
            for (int c = 0; c < 9; c++) addSlot(new Slot(buttons, c + r * 9, 8 + c * 18, 18 + r * 18));
        SimpleContainer hidden = new SimpleContainer(36);
        for (int r = 0; r < 3; r++)
            for (int c = 0; c < 9; c++) addSlot(new Slot(hidden, 9 + c + r * 9, 8 + c * 18, 140 + r * 18));
        for (int c = 0; c < 9; c++) addSlot(new Slot(hidden, c, 8 + c * 18, 198));
    }

    public void set(int slot, ItemStack stack, Consumer<ServerPlayer> action) {
        buttons.setItem(slot, stack);
        if (action != null) actions.put(slot, action);
        else actions.remove(slot);
    }

    public void set(int slot, ItemStack stack) { set(slot, stack, null); }

    @Override
    public void clicked(int slotId, int button, ClickType type, Player player) {
        if (player instanceof ServerPlayer sp && slotId >= 0 && slotId < 54 && type != ClickType.QUICK_CRAFT) {
            Consumer<ServerPlayer> a = actions.get(slotId);
            if (a != null) {
                sp.playNotifySound(SoundEvents.UI_BUTTON_CLICK.value(), SoundSource.MASTER, 0.5f, 1.0f);
                a.accept(sp);
            }
        }
        setCarried(ItemStack.EMPTY);
        sendAllDataToRemote();
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) { return ItemStack.EMPTY; }

    @Override
    public boolean stillValid(Player player) { return true; }

    @Override
    public void removed(Player player) {
        super.removed(player);
        // le client a affiché un inventaire vide : on lui renvoie le vrai
        if (player instanceof ServerPlayer sp) sp.inventoryMenu.sendAllDataToRemote();
    }

    /** Titre simple (pages sans fond dessiné) : texte vanilla sur le coffre gris. */
    public static Component title(Page page, String text) {
        return Component.literal(text);
    }

    public static void open(ServerPlayer p, Page page, String title, Consumer<IslandMenu> fill) {
        open(p, title(page, title), fill);
    }

    public static void open(ServerPlayer p, Component title, Consumer<IslandMenu> fill) {
        p.openMenu(new SimpleMenuProvider((id, inv, pl) -> {
            IslandMenu m = new IslandMenu(id);
            fill.accept(m);
            return m;
        }, title));
    }
}
