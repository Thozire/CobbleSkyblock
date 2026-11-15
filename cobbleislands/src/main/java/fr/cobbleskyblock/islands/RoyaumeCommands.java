package fr.cobbleskyblock.islands;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.LongArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.tree.LiteralCommandNode;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

import java.util.Arrays;
import java.util.Map;
import java.util.UUID;
import java.util.function.Supplier;

import static net.minecraft.commands.Commands.argument;
import static net.minecraft.commands.Commands.literal;

/** Commandes /royaume (alias /r), /capitale, /spawn, /marche. */
public final class RoyaumeCommands {
    private RoyaumeCommands() {}

    private static IslandManager mgr() { return CobbleIslands.manager(); }

    private static int fail(CommandContext<CommandSourceStack> c, String msg) {
        c.getSource().sendFailure(Msg.err(msg));
        return 0;
    }

    private static int ok(CommandContext<CommandSourceStack> c, Supplier<Component> msg) {
        c.getSource().sendSuccess(msg, false);
        return 1;
    }

    private static Island mine(CommandContext<CommandSourceStack> c, ServerPlayer p) {
        Island is = mgr().islandOf(p.getUUID());
        if (is == null) c.getSource().sendFailure(Msg.err("Tu n'as pas de royaume. ").append(Msg.button("Fonder mon royaume", "/royaume creer", ChatFormatting.GREEN)));
        return is;
    }

    private static boolean lord(CommandContext<CommandSourceStack> c, Island is, ServerPlayer p) {
        if (is.isOwner(p.getUUID())) return true;
        c.getSource().sendFailure(Msg.err("Seul le seigneur du royaume peut faire ça."));
        return false;
    }

    public static void register(CommandDispatcher<CommandSourceStack> d) {
        LiteralCommandNode<CommandSourceStack> root = d.register(literal("royaume")
                .executes(c -> { KingdomMenus.main(c.getSource().getPlayerOrException()); return 1; })
                .then(literal("menu").executes(c -> { KingdomMenus.main(c.getSource().getPlayerOrException()); return 1; }))
                .then(literal("creer").executes(RoyaumeCommands::create))
                .then(literal("go").executes(RoyaumeCommands::home))
                .then(literal("home").executes(RoyaumeCommands::home))
                .then(literal("nom").then(argument("nom", StringArgumentType.greedyString()).executes(RoyaumeCommands::rename)))
                .then(literal("inviter").then(argument("joueur", EntityArgument.player()).executes(RoyaumeCommands::invite)))
                .then(literal("accepter").executes(RoyaumeCommands::accept))
                .then(literal("refuser").executes(RoyaumeCommands::decline))
                .then(literal("exclure").then(argument("pseudo", StringArgumentType.word())
                        .suggests((c, b) -> {
                            Island is = mgr().islandOf(c.getSource().getPlayerOrException().getUUID());
                            return is == null ? b.buildFuture() : SharedSuggestionProvider.suggest(is.members.values(), b);
                        }).executes(RoyaumeCommands::kick)))
                .then(literal("quitter").executes(RoyaumeCommands::leave))
                .then(literal("visiter").then(argument("joueur", EntityArgument.player()).executes(RoyaumeCommands::visit)))
                .then(literal("ouvrir").executes(c -> setOpen(c, true)))
                .then(literal("fermer").executes(c -> setOpen(c, false)))
                .then(literal("supprimer").executes(RoyaumeCommands::deleteAsk)
                        .then(literal("confirmer").executes(RoyaumeCommands::deleteConfirm)))
                .then(literal("acheter")
                        .then(argument("machine", StringArgumentType.word())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(Arrays.stream(BuildingType.values()).map(t -> t.id), b))
                                .executes(RoyaumeCommands::buy)))
                .then(literal("vendre").executes(RoyaumeCommands::sellAll))
                .then(literal("ecus").executes(RoyaumeCommands::balance))
                .then(literal("classement").executes(c -> { KingdomMenus.ranking(c.getSource().getPlayerOrException(), 0); return 1; }))
                .then(literal("admin").requires(s -> s.hasPermission(2))
                        .then(literal("ecus").then(argument("joueur", EntityArgument.player())
                                .then(argument("montant", LongArgumentType.longArg()).executes(RoyaumeCommands::adminMoney))))
                        .then(literal("taille").then(argument("joueur", EntityArgument.player())
                                .then(argument("niveau", IntegerArgumentType.integer(1, 10)).executes(c -> adminLevel(c, 0)))))
                        .then(literal("membres").then(argument("joueur", EntityArgument.player())
                                .then(argument("niveau", IntegerArgumentType.integer(1, 10)).executes(c -> adminLevel(c, 1)))))
                        .then(literal("batiments").then(argument("joueur", EntityArgument.player())
                                .then(argument("niveau", IntegerArgumentType.integer(1, 10)).executes(c -> adminLevel(c, 2)))))
                        .then(literal("tp").then(argument("joueur", EntityArgument.player()).executes(c -> {
                            ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
                            Island is = mgr().islandOf(t.getUUID());
                            if (is == null) return fail(c, "Ce joueur n'a pas de royaume.");
                            mgr().visit(c.getSource().getPlayerOrException(), is);
                            return 1;
                        })))
                        .then(literal("supprimer").then(argument("joueur", EntityArgument.player()).executes(c -> {
                            ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
                            Island is = mgr().islandOf(t.getUUID());
                            if (is == null) return fail(c, "Ce joueur n'a pas de royaume.");
                            mgr().delete(is);
                            return ok(c, () -> Msg.ok("Royaume supprimé."));
                        })))
                        .then(literal("capitale")
                                .then(literal("reconstruire").executes(c -> {
                                    SpawnBuilder.build(mgr(), true);
                                    return ok(c, () -> Msg.ok("Capitale reconstruite."));
                                }))
                                .then(literal("ici").executes(c -> {
                                    ServerPlayer p = c.getSource().getPlayerOrException();
                                    if (p.level() != mgr().server().overworld()) return fail(c, "La capitale doit être dans l'Overworld.");
                                    SpawnBuilder.setSpawn(mgr(), p.blockPosition());
                                    return ok(c, () -> Msg.ok("Point d'apparition déplacé ici."));
                                })))));
        d.register(literal("r").executes(c -> { KingdomMenus.main(c.getSource().getPlayerOrException()); return 1; }).redirect(root));
        for (String name : new String[]{"capitale", "spawn"}) {
            d.register(literal(name).executes(c -> {
                mgr().teleportSpawn(c.getSource().getPlayerOrException());
                return ok(c, () -> Msg.info("Bienvenue à la capitale !"));
            }));
        }
        d.register(literal("sell").executes(RoyaumeCommands::sellHand));
        d.register(literal("sellall").executes(RoyaumeCommands::sellAll));
        d.register(literal("ecus").executes(RoyaumeCommands::balance)
                .then(literal("give").requires(src -> src.hasPermission(2))
                        .then(argument("joueur", EntityArgument.player())
                                .then(argument("montant", LongArgumentType.longArg(1)).executes(RoyaumeCommands::giveMoney)))));
        d.register(literal("marche").executes(c -> { KingdomMenus.market(c.getSource().getPlayerOrException()); return 1; }));
    }

    private static int create(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        String err = mgr().create(p);
        if (err != null) return fail(c, err);
        return ok(c, () -> Msg.ok("Ton île est née ! Une §6Scierie §ats'attend dans ton inventaire : pose-la sur ton île. ")
                .append(Msg.button("Menu", "/royaume", ChatFormatting.AQUA)));
    }

    private static int home(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mine(c, p);
        if (is == null) return 0;
        mgr().teleportHome(p, is);
        return ok(c, () -> Msg.ok("Bienvenue chez toi, seigneur."));
    }

    private static int rename(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mine(c, p);
        if (is == null || !lord(c, is, p)) return 0;
        String name = StringArgumentType.getString(c, "nom").replace("§", "").trim();
        if (name.length() < 3 || name.length() > 32) return fail(c, "Le nom doit faire entre 3 et 32 caractères.");
        is.name = name;
        mgr().data().setDirty();
        return ok(c, () -> Msg.ok("Ton royaume s'appelle désormais « " + name + " »."));
    }

    private static int invite(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mine(c, p);
        if (is == null || !lord(c, is, p)) return 0;
        ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
        if (t == p) return fail(c, "Tu ne peux pas t'inviter toi-même.");
        if (is.isMember(t.getUUID())) return fail(c, t.getGameProfile().getName() + " fait déjà partie de ta cour.");
        if (is.members.size() >= mgr().maxMembers(is)) return fail(c, "Ta cour est pleine (" + mgr().maxMembers(is) + " membres max) : agrandis-la !");
        mgr().invites.put(t.getUUID(), new IslandManager.Invite(is.id, p.getGameProfile().getName(),
                System.currentTimeMillis() + mgr().config().dureeInvitation * 1000L));
        t.sendSystemMessage(Msg.info(p.getGameProfile().getName() + " t'invite à rejoindre le " + is.name + " ! ")
                .append(Msg.button("Accepter", "/royaume accepter", ChatFormatting.GREEN)).append(Component.literal(" "))
                .append(Msg.button("Refuser", "/royaume refuser", ChatFormatting.RED)));
        return ok(c, () -> Msg.ok("Invitation envoyée à " + t.getGameProfile().getName() + "."));
    }

    private static int accept(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        IslandManager.Invite inv = mgr().invites.remove(p.getUUID());
        if (inv == null || inv.expires() < System.currentTimeMillis()) return fail(c, "Tu n'as pas d'invitation en cours.");
        Island target = mgr().data().islands.get(inv.islandId());
        if (target == null) return fail(c, "Ce royaume n'existe plus.");
        Island current = mgr().islandOf(p.getUUID());
        if (current != null) {
            if (current.isOwner(p.getUUID()) && current.members.size() > 1)
                return fail(c, "Tu es seigneur d'un royaume avec des vassaux : bannis-les ou abandonne ton royaume d'abord.");
            if (current.isOwner(p.getUUID())) mgr().delete(current);
            else mgr().removeMember(current, p.getUUID());
        }
        if (target.members.size() >= mgr().maxMembers(target)) return fail(c, "Cette cour est pleine.");
        mgr().join(p, target);
        mgr().teleportHome(p, target);
        mgr().broadcast(target, Msg.ok(p.getGameProfile().getName() + " a rejoint le royaume !"));
        return 1;
    }

    private static int decline(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        if (mgr().invites.remove(c.getSource().getPlayerOrException().getUUID()) == null) return fail(c, "Tu n'as pas d'invitation en cours.");
        return ok(c, () -> Msg.info("Invitation refusée."));
    }

    private static int kick(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mine(c, p);
        if (is == null || !lord(c, is, p)) return 0;
        String name = StringArgumentType.getString(c, "pseudo");
        UUID target = null;
        for (Map.Entry<UUID, String> e : is.members.entrySet()) if (e.getValue().equalsIgnoreCase(name)) target = e.getKey();
        if (target == null) return fail(c, name + " ne fait pas partie de ta cour.");
        if (target.equals(p.getUUID())) return fail(c, "Tu ne peux pas te bannir toi-même.");
        mgr().removeMember(is, target);
        ServerPlayer t = mgr().server().getPlayerList().getPlayer(target);
        if (t != null) t.sendSystemMessage(Msg.err("Tu as été banni du " + is.name + "."));
        return ok(c, () -> Msg.ok(name + " a été banni du royaume."));
    }

    private static int leave(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mine(c, p);
        if (is == null) return 0;
        if (is.isOwner(p.getUUID())) return fail(c, "Tu es le seigneur : abandonne le royaume depuis le menu Améliorer.");
        mgr().removeMember(is, p.getUUID());
        mgr().teleportSpawn(p);
        return ok(c, () -> Msg.info("Tu as quitté le " + is.name + "."));
    }

    private static int visit(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
        Island is = mgr().islandOf(t.getUUID());
        if (is == null) return fail(c, t.getGameProfile().getName() + " n'a pas de royaume.");
        if (!is.open && !is.isMember(p.getUUID()) && !p.hasPermissions(2)) return fail(c, "Ce royaume a fermé ses portes.");
        mgr().visit(p, is);
        return 1;
    }

    private static int setOpen(CommandContext<CommandSourceStack> c, boolean open) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mine(c, p);
        if (is == null || !lord(c, is, p)) return 0;
        is.open = open;
        mgr().data().setDirty();
        return ok(c, () -> Msg.ok(open ? "Les portes de ton royaume sont ouvertes." : "Les portes de ton royaume sont fermées."));
    }

    private static int deleteAsk(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mine(c, p);
        if (is == null || !lord(c, is, p)) return 0;
        mgr().pendingDelete.put(p.getUUID(), System.currentTimeMillis() + 30_000);
        c.getSource().sendSystemMessage(Msg.err("Abandonner ton royaume est définitif. ")
                .append(Msg.button("Je confirme", "/royaume supprimer confirmer", ChatFormatting.DARK_RED)));
        return 1;
    }

    private static int deleteConfirm(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Long until = mgr().pendingDelete.remove(p.getUUID());
        if (until == null || until < System.currentTimeMillis()) return fail(c, "Tape d'abord /royaume supprimer.");
        Island is = mgr().islandOf(p.getUUID());
        if (is == null || !is.isOwner(p.getUUID())) return fail(c, "Tu n'es seigneur d'aucun royaume.");
        mgr().delete(is);
        mgr().teleportSpawn(p);
        return ok(c, () -> Msg.info("Ton royaume a été abandonné. Tu peux en fonder un autre avec /royaume creer."));
    }

    private static int buy(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        BuildingType t = BuildingType.byName(StringArgumentType.getString(c, "machine"));
        if (t == null) return fail(c, "Machine inconnue.");
        String err = mgr().buyMachine(p, t);
        if (err != null) return fail(c, err);
        return ok(c, () -> Msg.ok(t.label + " achetée ! Fais un clic droit sur ton île pour la poser."));
    }

    private static int sellAll(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mine(c, p);
        if (is == null) return 0;
        long g = Market.sellInventory(p, is);
        mgr().data().setDirty();
        if (g == 0) return fail(c, "Rien à vendre dans ton inventaire.");
        return ok(c, () -> Msg.ok("Vente réussie : +" + Market.fmt(g) + " écus (trésor : " + Market.fmt(is.money) + ")."));
    }

    private static int sellHand(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mine(c, p);
        if (is == null) return 0;
        if (p.getMainHandItem().isEmpty()) return fail(c, "Tiens dans ta main l'objet à vendre.");
        long g = Market.sellHand(p, is);
        if (g == 0) return fail(c, "Cet objet ne se vend pas.");
        mgr().data().setDirty();
        return ok(c, () -> Msg.ok("Vendu : +" + Market.fmt(g) + " écus (trésor : " + Market.fmt(is.money) + ")."));
    }

    private static int giveMoney(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
        Island is = mgr().islandOf(t.getUUID());
        if (is == null) return fail(c, t.getGameProfile().getName() + " n'a pas de royaume : les écus vont dans le trésor d'un royaume.");
        long amount = LongArgumentType.getLong(c, "montant");
        is.money += amount;
        mgr().data().setDirty();
        t.sendSystemMessage(Msg.ok("Tu as reçu " + Market.fmt(amount) + " écus !"));
        return ok(c, () -> Msg.ok(Market.fmt(amount) + " écus donnés à " + t.getGameProfile().getName() + " (trésor : " + Market.fmt(is.money) + ")."));
    }

    private static int balance(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Island is = mine(c, p);
        if (is == null) return 0;
        return ok(c, () -> Msg.info("Trésor du " + is.name + " : §6" + Market.fmt(is.money) + " écus"));
    }

    private static int adminMoney(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
        Island is = mgr().islandOf(t.getUUID());
        if (is == null) return fail(c, "Ce joueur n'a pas de royaume.");
        long amount = LongArgumentType.getLong(c, "montant");
        is.money = Math.max(0, is.money + amount);
        mgr().data().setDirty();
        return ok(c, () -> Msg.ok("Trésor du " + is.name + " : " + Market.fmt(is.money) + " écus."));
    }

    /** what : 0 = terrain, 1 = membres, 2 = bâtiments. */
    private static int adminLevel(CommandContext<CommandSourceStack> c, int what) throws CommandSyntaxException {
        ServerPlayer t = EntityArgument.getPlayer(c, "joueur");
        Island is = mgr().islandOf(t.getUUID());
        if (is == null) return fail(c, "Ce joueur n'a pas de royaume.");
        int lvl = IntegerArgumentType.getInteger(c, "niveau");
        IslandConfig cfg = mgr().config();
        int max = what == 0 ? cfg.taillesParNiveau.length : what == 1 ? cfg.membresParNiveau.length : cfg.machinesParNiveau.length;
        if (lvl > max) return fail(c, "Niveau maximum : " + max + ".");
        if (what == 0) is.sizeLevel = lvl;
        else if (what == 1) is.memberLevel = lvl;
        else is.machineLevel = lvl;
        mgr().data().setDirty();
        return ok(c, () -> Msg.ok("Niveau mis à jour."));
    }

}
