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

        /** Dessine les quatre tuiles d'un fond 440x270 dont le coin haut-gauche est à CANVAS_X. */
        Builder background(String tiles) {
            Style st = Style.EMPTY.withFont(GUI).withColor(0xFFFFFF);
            int x0 = GuiFont.CANVAS_X, tw = GuiFont.TILE_W;
            for (int row = 0; row < 2; row++) {
                for (int col = 0; col < 2; col++) {
                    moveTo(x0 + col * tw);
                    root.append(Component.literal(String.valueOf(tiles.charAt(row * 2 + col))).withStyle(st));
                    pen += tw + 1;     // avance d'un glyphe bitmap = largeur + 1
                }
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
        while (!s.isEmpty() && GuiFont.width(s + "..") > maxW) s = s.substring(0, s.length() - 1);
        return s + "..";
    }

    // ---------- page principale ----------
    private static final int STATS_X = -85;
    private static final int[] STATS_DY = {69, 89, 109, 129, 149};
    private static final int LEVEL_CX = 241, LEVEL_DY = 156;

    /** Page d'un bâtiment : même parchemin (niveau, production, stock, valeur, amélioration) et nom sur la plaque. */
    /** Liste des bâtiments : posés, production, stock total, trésor, prix de la prochaine place ; plaque libre. */
    static Component listTitle(String placed, String rate, String stock, String treasury, String upgrade, String plate) {
        Builder b = new Builder().background(GuiFont.LIST_TILES);
        String[] v = {placed, rate, stock, treasury, upgrade};
        int[] c = {0x3E261A, 0x226C26, 0x3E261A, 0x9C5C10, 0x284CA6};
        for (int i = 0; i < 5; i++) b.text(STATS_X, STATS_DY[i], fit(v[i], 68), c[i]);
        b.textCentered(LEVEL_CX, LEVEL_DY, fit(plate, 52), 0xFFECBE);
        return b.build();
    }

    static Component buildingTitle(String id, String level, String rate, String stock, String value, String upgrade, String name) {
        Builder b = new Builder().background(GuiFont.buildingTiles(id));
        String[] v = {level, rate, stock, value, upgrade};
        int[] c = {0x3E261A, 0x226C26, 0x3E261A, 0x9C5C10, 0x284CA6};
        for (int i = 0; i < 5; i++) b.text(STATS_X, STATS_DY[i], fit(v[i], 68), c[i]);
        b.textCentered(LEVEL_CX, LEVEL_DY, fit(name, 52), 0xFFECBE);
        return b.build();
    }

    static Component mainTitle(String lord, String treasury, String income, String rank, String members, String level) {
        Builder b = new Builder().background(GuiFont.MAIN_TILES);
        String[] v = {lord, treasury, income, rank, members};
        int[] c = {0x3E261A, 0x9C5C10, 0x226C26, 0x284CA6, 0x3E261A};
        for (int i = 0; i < 5; i++) b.text(STATS_X, STATS_DY[i], fit(v[i], 68), c[i]);
        b.textCentered(LEVEL_CX, LEVEL_DY, level, 0xFFECBE);
        return b.build();
    }
}
