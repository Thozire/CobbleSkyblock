package fr.cobbleskyblock.islands;

import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.resources.ResourceLocation;

/**
 * Titres « dessinés » : le fond de la page est fait de tuiles (glyphes de la police
 * cobbleislands:gui) et les textes dynamiques sont écrits avec des polices décalées
 * verticalement (cobbleislands:t&lt;dy&gt;, haut du texte à y = 6 + dy dans le repère du coffre).
 * Le stylo est déplacé horizontalement avec des caractères d'espacement.
 */
final class RoyalGui {
    private RoyalGui() {}

    private static final ResourceLocation GUI = ResourceLocation.fromNamespaceAndPath("cobbleislands", "gui");

    /** Le titre vanilla d'un coffre commence à x = 8. */
    private static final int TITLE_X = 8;

    /** Construit un titre en suivant la position du stylo. */
    static final class Builder {
        private final MutableComponent root = Component.empty();
        private int pen = TITLE_X;

        /** Déplace le stylo jusqu'à x (repère du coffre). */
        Builder moveTo(int x) {
            int d = x - pen;
            if (d != 0) {
                StringBuilder sb = new StringBuilder();
                String set = d < 0 ? GuiFont.NEG : GuiFont.POS;
                int a = Math.abs(d);
                for (int i = 9; i >= 0; i--) {
                    while (a >= (1 << i)) { sb.append(set.charAt(i)); a -= 1 << i; }
                }
                root.append(Component.literal(sb.toString()).withStyle(Style.EMPTY.withFont(GUI)));
                pen = x;
            }
            return this;
        }

        /** Dessine le fond d'une page : ses quatre tuiles puis ses calques haute définition (niche, tableau). */
        Builder page(String page) {
            Style st = Style.EMPTY.withFont(GUI).withColor(0xFFFFFF);
            String tiles = GuiFont.tiles(page);
            int x0 = GuiFont.CANVAS_X, tw = GuiFont.TILE_W;
            for (int row = 0; row < 2; row++) {
                for (int col = 0; col < 2; col++) {
                    moveTo(x0 + col * tw);
                    root.append(Component.literal(String.valueOf(tiles.charAt(row * 2 + col))).withStyle(st));
                    pen += tw + 1;     // avance d'un glyphe bitmap = largeur + 1
                }
            }
            int[] ov = GuiFont.overlays(page);
            for (int i = 0; i + 2 < ov.length; i += 3) {
                moveTo(ov[i + 1]);
                root.append(Component.literal(String.valueOf((char) ov[i])).withStyle(st));
                pen += ov[i + 2];
            }
            return this;
        }

        /** Écrit un texte à (x, haut = 6 + dy). */
        Builder text(int x, int dy, String s, int color) {
            moveTo(x);
            ResourceLocation font = ResourceLocation.fromNamespaceAndPath("cobbleislands", "t" + dy);
            root.append(Component.literal(s).withStyle(Style.EMPTY.withFont(font).withColor(color)
                    .withBold(false).withItalic(false)));
            pen += GuiFont.width(s);
            return this;
        }

        Builder textCentered(int cx, int dy, String s, int color) {
            return text(cx - GuiFont.width(s) / 2, dy, s, color);
        }

        Component build() { return root; }
    }

    /** Coupe un texte pour qu'il tienne dans maxW pixels. */
    static String fit(String s, int maxW) {
        if (GuiFont.width(s) <= maxW) return s;
        // 1) nombres longs en version courte (12 480 -> 12,5k), 2) sans l'unité, 3) coupe
        java.util.regex.Matcher mt = java.util.regex.Pattern.compile("\\d{1,3}(?:[ \u202F]\\d{3})+").matcher(s);
        StringBuilder sb = new StringBuilder();
        while (mt.find()) mt.appendReplacement(sb, compact(Long.parseLong(mt.group().replace(" ", "").replace("\u202F", ""))));
        mt.appendTail(sb);
        s = sb.toString();
        if (GuiFont.width(s) <= maxW) return s;
        String noUnit = s.replace(" écus", "").replace(" / min", "/min");
        if (GuiFont.width(noUnit) <= maxW) return noUnit;
        s = noUnit;
        while (!s.isEmpty() && GuiFont.width(s + "..") > maxW) s = s.substring(0, s.length() - 1);
        return s + "..";
    }

    /** 1 234 -> 1,2k ; 48 300 -> 48,3k ; 412 000 -> 412k ; 2 500 000 -> 2,5M. */
    static String compact(long v) {
        String[] u = {"", "k", "M", "G", "T"};
        double d = v; int i = 0;
        while (Math.abs(d) >= 1000 && i < u.length - 1) { d /= 1000; i++; }
        if (i == 0) return Long.toString(v);
        String r = Math.abs(d) >= 100 ? Long.toString(Math.round(d)) : String.format(java.util.Locale.FRANCE, "%.1f", d);
        if (r.endsWith(",0")) r = r.substring(0, r.length() - 2);
        return r + u[i];
    }

    // ---------- pages ----------
    private static final int STATS_X = -85, STATS_W = 62;
    private static final int[] STATS_DY = {69, 89, 109, 129, 149};
    static final int INK = 0x3E261A, GREEN = 0x226C26, GOLD = 0x9C5C10, BLUE = 0x284CA6, RED = 0xA02C24;

    /** Parchemin de gauche : cinq valeurs sous les cinq libellés dessinés. */
    private static Builder stats(Builder b, String[] v, int[] c) {
        for (int i = 0; i < 5 && i < v.length; i++) b.text(STATS_X, STATS_DY[i], fit(v[i], STATS_W), c[i]);
        return b;
    }

    static Component mainTitle(String lord, String treasury, String income, String rank, String members, String unused) {
        return stats(new Builder().page("main"), new String[]{lord, treasury, income, rank, members},
                new int[]{INK, GOLD, GREEN, BLUE, INK}).build();
    }

    static Component listTitle(String placed, String rate, String stock, String treasury, String upgrade, String unused) {
        return stats(new Builder().page("list"), new String[]{placed, rate, stock, treasury, upgrade},
                new int[]{INK, GREEN, INK, GOLD, BLUE}).build();
    }

    static Component buildingTitle(String id, String level, String rate, String stock, String value, String upgrade, String unused) {
        return stats(new Builder().page(id), new String[]{level, rate, stock, value, upgrade},
                new int[]{INK, GREEN, INK, GOLD, BLUE}).build();
    }

    /** Améliorer le royaume : trois cartes (niveau, prix) et deux réglages (visites, quitter / abandonner). */
    static Component domainTitle(String[] st, String[] levels, String[] prices, String doors, boolean open, String quit) {
        Builder b = stats(new Builder().page("domain"), st, new int[]{INK, INK, INK, GOLD, open ? GREEN : RED});
        for (int k = 0; k < 3; k++) {
            int cx = 33 + 54 * k;
            b.textCentered(cx, 60, fit(levels[k], 48), 0xFFECBE);
            b.textCentered(cx, 71, fit(prices[k], 48), 0xFFD66E);
        }
        b.text(27, 88, fit(doors, 56), open ? 0x8CE678 : 0xFF8C78);
        b.text(107, 88, fit(quit, 59), 0xFF8C78);
        return b.build();
    }

    static Component teamTitle(String[] st) {
        return stats(new Builder().page("team"), st, new int[]{INK, INK, GREEN, BLUE, GOLD}).build();
    }

    static Component inviteTitle(String[] st) {
        return stats(new Builder().page("invite"), st, new int[]{GREEN, BLUE, INK, INK, GOLD}).build();
    }
}
