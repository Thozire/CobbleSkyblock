package fr.cobbleskyblock.islands;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.tree.LiteralCommandNode;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerPlayer;

import java.util.Map;
import java.util.UUID;
import java.util.function.Supplier;

import static net.minecraft.commands.Commands.argument;
import static net.minecraft.commands.Commands.literal;

/** Toutes les commandes /ile (alias /is) et /spawn. */
public final class IslandCommands {
    private IslandCommands() {}

    private static IslandManager mgr() { return CobbleIslands.manager(); }

    private static int fail(CommandContext<CommandSourceStack> c, String msg) {
        c.getSource().sendFailure(Msg.err(msg));
        return 0;
    }

    private static int ok(CommandContext<CommandSourceStack> c, Supplier<Component> msg) {
        c.getSource().sendSuccess(msg, false);
        return 1;
    }

    public static void register(CommandDispatcher<CommandSourceStack> d) {
        LiteralCommandNode<CommandSourceStack> root = d.register(literal("ile")
                .executes(IslandCommands::quick)
                .then(literal("aide").executes(IslandCommands::help))
                .then(literal("creer").executes(IslandCommands::create))
                .then(literal("home").executes(IslandCommands::home))
                .then(literal("sethome").executes(IslandCommands::setHome))
                .then(literal("info").executes(IslandCommands::info))
                .then(literal("inviter").then(argument("joueur", EntityArgument.player()).executes(IslandCommands::invite)))
                .then(literal("accepter").executes(IslandCommands::accept))
                .then(literal("refuser").executes(IslandCommands::decline))
                .then(literal("exclure").then(argument("pseudo", StringArgumentType.word())
                        .suggests((c, b) -> {
                            Island is = mgr().islandOf(c.getSource().getPlayerOrException().getUUID());
                            return is == null ? b.buildFuture() : SharedSuggestionProvider.suggest(is.members.values(), b);
                        })
                        .executes(IslandCommands::kick)))
                .then(literal("quitter").executes(IslandCommands::leave))
                .then(literal("visiter").then(argument("joueur", EntityArgument.player()).executes(IslandCommands::visit)))
                .then(literal("ouvrir").executes(c -> setOpen(c, true)))
                .then(literal("fermer").executes(c -> setOpen(c, false)))
                .then(literal("supprimer").executes(IslandCommands::deleteAsk)
                        .then(literal("confirmer").executes(IslandCommands::deleteConfirm)))
                .then(literal("admin").requires(s -> s.hasPermission(2))
                        .then(literal("taille").then(argument("joueur", EntityArgument.player())
                                .then(argument("niveau", IntegerArgumentType.integer(1, 10)).executes(c -> adminLevel(c, true)))))
                        .then(literal("membres").then(argument("joueur", EntityArgument.player())
                                .then(argument("niveau", IntegerArgumentType.integer(1, 10)).executes(c -> adminLevel(c, false)))))
                        .then(literal("tp").then(argument("joueur", EntityArgument.player()).executes(IslandCommands::adminTp)))
                        .then(literal("supprimer").then(argument("joueur", EntityArgument.player()).executes(IslandCommands::adminDelete)))
                        .then(literal("spawn")
                                .then(literal("reconstruire").executes(c -> {
                                    SpawnBuilder.build(mgr(), true);
                                    return ok(c, () -> Msg.ok("Spawn reconstruit."));
                                }))
                                .then(literal("ici").executes(c -> {
                                    ServerPlayer p = c.getSource().getPlayerOrException();
                                    if (p.level() != mgr().server().overworld()) return fail(c, "Le spawn doit être dans l'Overworld.");
                                    SpawnBuilder.setSpawn(mgr(), p.blockPosition());
                                    return ok(c, () -> Msg.ok("Point d'apparition du serveur déplacé ici."));
                                })))));
        d.register(literal("is").executes(IslandCommands::quick).redirect(root));
        d.register(literal("spawn").executes(c -> {
            mgr().teleportSpawn(c.getSource().getPlayerOrException());
            return ok(c, () -> Msg.info("Bienvenue au spawn !"));
        }));
    }

    /** /ile ou /is sans argument : va sur son île, ou propose d'en créer une. */
    private static int quick(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) {
            help(c);
            c.getSource().sendSystemMessage(Msg.info("Tu n'as pas encore d'île. ").append(Msg.button("Créer mon île", "/ile creer", ChatFormatting.GREEN)));
            return 1;
        }
        mgr().teleportHome(p, is);
        return ok(c, () -> Msg.ok("Retour sur ton île. ").append(Msg.button("Aide", "/ile aide", ChatFormatting.AQUA)));
    }

    private static int help(CommandContext<CommandSourceStack> c) {
        MutableComponent m = Component.literal("━━━━━━ ").withStyle(ChatFormatting.DARK_PURPLE)
                .append(Component.literal("Îles CobbleSkyblock").withStyle(ChatFormatting.LIGHT_PURPLE, ChatFormatting.BOLD))
                .append(Component.literal(" ━━━━━━").withStyle(ChatFormatting.DARK_PURPLE));
        String[][] lines = {
                {"/ile", "aller sur ton île (ou /is)"}, {"/ile creer", "créer ton île"},
                {"/ile info", "infos sur ton île et ton équipe"}, {"/ile inviter <joueur>", "inviter un joueur"},
                {"/ile accepter", "rejoindre l'île qui t'a invité"}, {"/ile exclure <pseudo>", "retirer un membre (chef)"},
                {"/ile quitter", "quitter l'île d'un autre"}, {"/ile visiter <joueur>", "visiter une île"},
                {"/ile ouvrir|fermer", "autoriser ou non les visites"}, {"/ile sethome", "changer le point d'arrivée (chef)"},
                {"/ile supprimer", "supprimer ton île (chef)"}, {"/spawn", "aller au spawn"}};
        for (String[] l : lines) {
            m.append(Component.literal("\n" + l[0]).withStyle(s -> s.withColor(ChatFormatting.AQUA)
                    .withClickEvent(new net.minecraft.network.chat.ClickEvent(net.minecraft.network.chat.ClickEvent.Action.SUGGEST_COMMAND, l[0].split(" <")[0].split("\\|")[0]))))
                    .append(Component.literal(" — " + l[1]).withStyle(ChatFormatting.GRAY));
        }
        c.getSource().sendSystemMessage(m);
        return 1;
    }

    private static int create(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        String err = mgr().create(p);
        if (err != null) return fail(c, err);
        return ok(c, () -> Msg.ok("Bienvenue sur ton île ! ").append(Msg.button("Aide", "/ile aide", ChatFormatting.AQUA)));
    }

    private static Island requireIsland(CommandContext<CommandSourceStack> c, ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) {
            c.getSource().sendFailure(Msg.err("Tu n'as pas encore d'île. ").append(Msg.button("Créer mon île", "/ile creer", ChatFormatting.GREEN)));
        }
        return is;
    }

    private static int home(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = requireIsland(c, p);
        if (is == null) return 0;
        mgr().teleportHome(p, is);
        return ok(c, () -> Msg.ok("Retour sur ton île."));
    }

    private static int setHome(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = requireIsland(c, p);
        if (is == null) return 0;
        if (!is.isOwner(p.getUUID())) return fail(c, "Seul le chef de l'île peut faire ça.");
        if (p.level().dimension() != IslandManager.ISLANDS || mgr().islandAt(p.blockPosition()) != is || !mgr().inBounds(is, p.blockPosition()))
            return fail(c, "Tu dois être sur ton île.");
        is.home = p.blockPosition();
        mgr().data().setDirty();
        for (UUID u : is.members.keySet()) {
            ServerPlayer m = mgr().server().getPlayerList().getPlayer(u);
            if (m != null) m.setRespawnPosition(IslandManager.ISLANDS, is.home, 0f, true, false);
        }
        return ok(c, () -> Msg.ok("Point d'arrivée de l'île déplacé ici."));
    }

    private static int info(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = requireIsland(c, p);
        if (is == null) return 0;
        int r = mgr().radius(is);
        MutableComponent m = Msg.info("Île de ").append(Component.literal(is.ownerName()).withStyle(ChatFormatting.WHITE))
                .append(Component.literal(String.format("\n  Taille : niveau %d (%d×%d blocs)", is.sizeLevel, 2 * r + 1, 2 * r + 1)).withStyle(ChatFormatting.GRAY))
                .append(Component.literal(String.format("\n  Équipe : %d/%d (niveau %d)", is.members.size(), mgr().maxMembers(is), is.memberLevel)).withStyle(ChatFormatting.GRAY))
                .append(Component.literal("\n  Visites : " + (is.open ? "ouvertes" : "fermées")).withStyle(ChatFormatting.GRAY))
                .append(Component.literal("\n  Membres : ").withStyle(ChatFormatting.GRAY));
        boolean first = true;
        for (Map.Entry<UUID, String> e : is.members.entrySet()) {
            if (!first) m.append(Component.literal(", ").withStyle(ChatFormatting.GRAY));
            first = false;
            m.append(Component.literal(e.getValue() + (is.isOwner(e.getKey()) ? " (chef)" : ""))
                    .withStyle(is.isOwner(e.getKey()) ? ChatFormatting.GOLD : ChatFormatting.WHITE));
        }
        c.getSource().sendSystemMessage(m);
        return 1;
    }

    private static int invite(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = requireIsland(c, p);
        if (is == null) return 0;
        if (!is.isOwner(p.getUUID())) return fail(c, "Seul le chef de l'île peut inviter.");
        ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
        if (t == p) return fail(c, "Tu ne peux pas t'inviter toi-même.");
        if (is.isMember(t.getUUID())) return fail(c, t.getGameProfile().getName() + " fait déjà partie de ton île.");
        if (is.members.size() >= mgr().maxMembers(is)) return fail(c, "Ton île est pleine (" + mgr().maxMembers(is) + " membres max).");
        long exp = System.currentTimeMillis() + mgr().config().dureeInvitation * 1000L;
        mgr().invites.put(t.getUUID(), new IslandManager.Invite(is.id, p.getGameProfile().getName(), exp));
        t.sendSystemMessage(Msg.info(p.getGameProfile().getName() + " t'invite sur son île ! ")
                .append(Msg.button("Accepter", "/ile accepter", ChatFormatting.GREEN)).append(Component.literal(" "))
                .append(Msg.button("Refuser", "/ile refuser", ChatFormatting.RED)));
        return ok(c, () -> Msg.ok("Invitation envoyée à " + t.getGameProfile().getName() + "."));
    }

    private static int accept(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        IslandManager.Invite inv = mgr().invites.remove(p.getUUID());
        if (inv == null || inv.expires() < System.currentTimeMillis()) return fail(c, "Tu n'as pas d'invitation en cours.");
        Island target = mgr().data().islands.get(inv.islandId());
        if (target == null) return fail(c, "Cette île n'existe plus.");
        Island current = mgr().islandOf(p.getUUID());
        if (current != null) {
            if (current.isOwner(p.getUUID()) && current.members.size() > 1)
                return fail(c, "Tu es chef d'une île avec des membres : exclus-les ou supprime ton île d'abord.");
            if (current.isOwner(p.getUUID())) mgr().delete(current);
            else mgr().removeMember(current, p.getUUID());
        }
        if (target.members.size() >= mgr().maxMembers(target)) return fail(c, "Cette île est pleine.");
        mgr().join(p, target);
        mgr().teleportHome(p, target);
        for (UUID u : target.members.keySet()) {
            ServerPlayer m = mgr().server().getPlayerList().getPlayer(u);
            if (m != null && m != p) m.sendSystemMessage(Msg.ok(p.getGameProfile().getName() + " a rejoint l'île !"));
        }
        return ok(c, () -> Msg.ok("Tu as rejoint l'île de " + target.ownerName() + " !"));
    }

    private static int decline(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        if (mgr().invites.remove(p.getUUID()) == null) return fail(c, "Tu n'as pas d'invitation en cours.");
        return ok(c, () -> Msg.info("Invitation refusée."));
    }

    private static int kick(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = requireIsland(c, p);
        if (is == null) return 0;
        if (!is.isOwner(p.getUUID())) return fail(c, "Seul le chef de l'île peut exclure.");
        String name = StringArgumentType.getString(c, "pseudo");
        UUID target = null;
        for (Map.Entry<UUID, String> e : is.members.entrySet())
            if (e.getValue().equalsIgnoreCase(name)) target = e.getKey();
        if (target == null) return fail(c, name + " ne fait pas partie de ton île.");
        if (target.equals(p.getUUID())) return fail(c, "Tu ne peux pas t'exclure toi-même (utilise /ile supprimer).");
        mgr().removeMember(is, target);
        ServerPlayer t = mgr().server().getPlayerList().getPlayer(target);
        if (t != null) t.sendSystemMessage(Msg.err("Tu as été exclu de l'île de " + is.ownerName() + "."));
        return ok(c, () -> Msg.ok(name + " a été exclu de l'île."));
    }

    private static int leave(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = requireIsland(c, p);
        if (is == null) return 0;
        if (is.isOwner(p.getUUID())) return fail(c, "Tu es le chef : utilise /ile supprimer.");
        mgr().removeMember(is, p.getUUID());
        mgr().teleportSpawn(p);
        return ok(c, () -> Msg.info("Tu as quitté l'île de " + is.ownerName() + "."));
    }

    private static int visit(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
        Island is = mgr().islandOf(t.getUUID());
        if (is == null) return fail(c, t.getGameProfile().getName() + " n'a pas d'île.");
        if (!is.open && !is.isMember(p.getUUID()) && !p.hasPermissions(2)) return fail(c, "Cette île est fermée aux visites.");
        net.minecraft.core.BlockPos h = is.home;
        p.teleportTo(mgr().islandsLevel(), h.getX() + 0.5, h.getY(), h.getZ() + 0.5, p.getYRot(), p.getXRot());
        return ok(c, () -> Msg.ok("Bienvenue sur l'île de " + is.ownerName() + " !"));
    }

    private static int setOpen(CommandContext<CommandSourceStack> c, boolean open) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = requireIsland(c, p);
        if (is == null) return 0;
        if (!is.isOwner(p.getUUID())) return fail(c, "Seul le chef de l'île peut faire ça.");
        is.open = open;
        mgr().data().setDirty();
        return ok(c, () -> Msg.ok(open ? "Ton île est ouverte aux visites." : "Ton île est fermée aux visites."));
    }

    private static int deleteAsk(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = requireIsland(c, p);
        if (is == null) return 0;
        if (!is.isOwner(p.getUUID())) return fail(c, "Seul le chef peut supprimer l'île (utilise /ile quitter).");
        mgr().pendingDelete.put(p.getUUID(), System.currentTimeMillis() + 30_000);
        c.getSource().sendSystemMessage(Msg.err("Supprimer ton île est définitif : tout ce qui s'y trouve sera perdu. ")
                .append(Msg.button("Je confirme", "/ile supprimer confirmer", ChatFormatting.DARK_RED)));
        return 1;
    }

    private static int deleteConfirm(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Long until = mgr().pendingDelete.remove(p.getUUID());
        if (until == null || until < System.currentTimeMillis()) return fail(c, "Tape d'abord /ile supprimer.");
        Island is = mgr().islandOf(p.getUUID());
        if (is == null || !is.isOwner(p.getUUID())) return fail(c, "Tu n'es chef d'aucune île.");
        mgr().delete(is);
        mgr().teleportSpawn(p);
        return ok(c, () -> Msg.info("Ton île a été supprimée. Tu peux en recréer une avec /ile creer."));
    }

    private static int adminLevel(CommandContext<CommandSourceStack> c, boolean size) throws CommandSyntaxException {
        ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
        Island is = mgr().islandOf(t.getUUID());
        if (is == null) return fail(c, t.getGameProfile().getName() + " n'a pas d'île.");
        int lvl = IntegerArgumentType.getInteger(c, "niveau");
        int max = size ? mgr().config().taillesParNiveau.length : mgr().config().membresParNiveau.length;
        if (lvl > max) return fail(c, "Niveau maximum : " + max + " (modifiable dans config/cobbleislands.json).");
        if (size) is.sizeLevel = lvl; else is.memberLevel = lvl;
        mgr().data().setDirty();
        String what = size ? "Taille de l'île : niveau " + lvl + " (" + (2 * mgr().radius(is) + 1) + " blocs de large)"
                : "Équipe : niveau " + lvl + " (" + mgr().maxMembers(is) + " membres max)";
        for (UUID u : is.members.keySet()) {
            ServerPlayer m = mgr().server().getPlayerList().getPlayer(u);
            if (m != null) m.sendSystemMessage(Msg.ok("Amélioration ! " + what));
        }
        return ok(c, () -> Msg.ok("Île de " + is.ownerName() + " → " + what));
    }

    private static int adminTp(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
        Island is = mgr().islandOf(t.getUUID());
        if (is == null) return fail(c, t.getGameProfile().getName() + " n'a pas d'île.");
        net.minecraft.core.BlockPos h = is.home;
        p.teleportTo(mgr().islandsLevel(), h.getX() + 0.5, h.getY(), h.getZ() + 0.5, p.getYRot(), p.getXRot());
        return ok(c, () -> Msg.ok("Téléporté sur l'île de " + is.ownerName() + "."));
    }

    private static int adminDelete(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
        Island is = mgr().islandOf(t.getUUID());
        if (is == null) return fail(c, t.getGameProfile().getName() + " n'a pas d'île.");
        mgr().delete(is);
        return ok(c, () -> Msg.ok("Île de " + t.getGameProfile().getName() + " supprimée."));
    }
}
