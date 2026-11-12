package fr.cobbleskyblock.islands;

import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.common.ClientboundResourcePackPushPacket;
import net.minecraft.server.level.ServerPlayer;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.HexFormat;
import java.util.Optional;
import java.util.UUID;

/**
 * Envoie le resource pack du serveur (menus, machine à fusion) à chaque joueur qui se connecte.
 * L'empreinte SHA-1 est calculée au démarrage en téléchargeant le pack.
 */
public final class ResourcePackSender {
    private ResourcePackSender() {}

    private static volatile String url, sha1;

    public static void init(IslandConfig cfg) {
        if (cfg.resourcePack == null || cfg.resourcePack.isBlank()) return;
        Thread t = new Thread(() -> {
            try {
                HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(15)).followRedirects(HttpClient.Redirect.NORMAL).build();
                HttpResponse<byte[]> r = http.send(HttpRequest.newBuilder(URI.create(cfg.resourcePack)).timeout(Duration.ofSeconds(60)).build(),
                        HttpResponse.BodyHandlers.ofByteArray());
                if (r.statusCode() != 200) throw new IllegalStateException("HTTP " + r.statusCode());
                sha1 = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-1").digest(r.body()));
                url = cfg.resourcePack;
                CobbleIslands.LOG.info("Resource pack prêt ({} octets, sha1 {})", r.body().length, sha1);
            } catch (Exception e) {
                CobbleIslands.LOG.warn("Resource pack indisponible : {}", e.toString());
            }
        }, "CobbleIslands-pack");
        t.setDaemon(true);
        t.start();
    }

    public static void send(ServerPlayer p, IslandConfig cfg) {
        if (url == null) return;
        p.connection.send(new ClientboundResourcePackPushPacket(UUID.nameUUIDFromBytes(url.getBytes()), url, sha1, cfg.resourcePackObligatoire,
                Optional.of(Component.literal("Le pack CobbleSkyblock ajoute les menus et la machine à fusion."))));
    }
}
