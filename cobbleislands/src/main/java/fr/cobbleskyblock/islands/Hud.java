package fr.cobbleskyblock.islands;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.numbers.BlankFormat;
import net.minecraft.network.protocol.game.ClientboundResetScorePacket;
import net.minecraft.network.protocol.game.ClientboundSetDisplayObjectivePacket;
import net.minecraft.network.protocol.game.ClientboundSetObjectivePacket;
import net.minecraft.network.protocol.game.ClientboundSetScorePacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.scores.DisplaySlot;
import net.minecraft.world.scores.Objective;
import net.minecraft.world.scores.Scoreboard;
import net.minecraft.world.scores.criteria.ObjectiveCriteria;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/** Tableau personnel à droite de l'écran (trésor, revenu, rang), envoyé à chaque joueur séparément. */
public final class Hud {
    private Hud() {}

    private static final String OBJ = "royaumes_hud";
    private static final Scoreboard DUMMY = new Scoreboard();
    private static final Map<UUID, List<String>> sent = new HashMap<>();

    public static void forget(UUID u) { sent.remove(u); }

    private static MutableComponent line(String label, String value, ChatFormatting valueColor) {
        return Component.literal(" " + label).withStyle(ChatFormatting.GRAY)
                .append(Component.literal(value).withStyle(valueColor));
    }

    public static void update(ServerPlayer p, IslandManager m) {
        Island is = m.islandOf(p.getUUID());
        List<Component> lines = new ArrayList<>();
        lines.add(Component.literal(" "));
        if (is == null) {
            lines.add(Component.literal(" Aucun royaume").withStyle(ChatFormatting.WHITE));
            lines.add(Component.literal("  "));
            lines.add(Component.literal(" Tape ").withStyle(ChatFormatting.GRAY).append(Component.literal("/royaume").withStyle(ChatFormatting.GOLD)));
            lines.add(Component.literal(" pour en fonder un !").withStyle(ChatFormatting.GRAY));
        } else {
            String name = is.name.length() > 22 ? is.name.substring(0, 21) + "…" : is.name;
            lines.add(Component.literal(" " + name).withStyle(ChatFormatting.WHITE, ChatFormatting.BOLD));
            lines.add(Component.literal("  "));
            lines.add(line("Trésor : ", Market.fmt(is.money) + " écus", ChatFormatting.GOLD));
            lines.add(line("Revenu : ", "+" + Market.fmt(m.incomePerMinute(is)) + "/min", ChatFormatting.GREEN));
            lines.add(line("Machines : ", is.buildings.size() + "/" + m.maxMachines(is), ChatFormatting.WHITE));
            lines.add(line("Rang : ", "#" + m.rankOf(is), ChatFormatting.AQUA));
            lines.add(Component.literal("   "));
            lines.add(Component.literal(" /royaume").withStyle(ChatFormatting.DARK_AQUA));
        }
        List<String> key = new ArrayList<>();
        for (Component c : lines) key.add(c.getString());
        List<String> before = sent.get(p.getUUID());
        if (key.equals(before)) return;

        Objective o = new Objective(DUMMY, OBJ, ObjectiveCriteria.DUMMY,
                Component.literal("⚜ ROYAUMES ⚜").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD),
                ObjectiveCriteria.RenderType.INTEGER, false, BlankFormat.INSTANCE);
        if (before == null) {
            p.connection.send(new ClientboundSetObjectivePacket(o, ClientboundSetObjectivePacket.METHOD_ADD));
            p.connection.send(new ClientboundSetDisplayObjectivePacket(DisplaySlot.SIDEBAR, o));
        }
        int n = lines.size();
        for (int i = 0; i < n; i++) {
            p.connection.send(new ClientboundSetScorePacket("l" + i, OBJ, n - i, Optional.of(lines.get(i)), Optional.of(BlankFormat.INSTANCE)));
        }
        if (before != null)
            for (int i = n; i < before.size(); i++) p.connection.send(new ClientboundResetScorePacket("l" + i, OBJ));
        sent.put(p.getUUID(), key);
    }
}
