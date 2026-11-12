package fr.cobbleskyblock.islands;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;

/** Petits raccourcis pour des messages colorés et cliquables. */
public final class Msg {
    private Msg() {}

    public static MutableComponent prefix() {
        return Component.literal("[Île] ").withStyle(ChatFormatting.LIGHT_PURPLE);
    }

    public static MutableComponent ok(String s) {
        return prefix().append(Component.literal(s).withStyle(ChatFormatting.GREEN));
    }

    public static MutableComponent info(String s) {
        return prefix().append(Component.literal(s).withStyle(ChatFormatting.GRAY));
    }

    public static MutableComponent err(String s) {
        return prefix().append(Component.literal(s).withStyle(ChatFormatting.RED));
    }

    /** Bouton [texte] qui lance une commande au clic. */
    public static MutableComponent button(String label, String command, ChatFormatting color) {
        return Component.literal("[" + label + "]").withStyle(s -> s
                .withColor(color).withBold(true)
                .withClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, command))
                .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT, Component.literal(command))));
    }
}
