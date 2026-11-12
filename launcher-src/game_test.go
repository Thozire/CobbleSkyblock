package main

import (
	"encoding/json"
	"strings"
	"testing"
)

const vanFix = `{"id":"1.21.1","mainClass":"net.minecraft.client.main.Main","arguments":{"game":["--username","${auth_player_name}","--version","${version_name}","--gameDir","${game_directory}","--assetsDir","${assets_root}","--assetIndex","${assets_index_name}","--uuid","${auth_uuid}","--accessToken","${auth_access_token}","--clientId","${clientid}","--xuid","${auth_xuid}","--userType","${user_type}","--versionType","${version_type}",{"rules":[{"action":"allow","features":{"is_demo_user":true}}],"value":"--demo"},{"rules":[{"action":"allow","features":{"has_custom_resolution":true}}],"value":["--width","${resolution_width}"]}],
"jvm":[{"rules":[{"action":"allow","os":{"name":"osx"}}],"value":["-XstartOnFirstThread"]},{"rules":[{"action":"allow","os":{"name":"windows"}}],"value":"-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump"},{"rules":[{"action":"allow","os":{"arch":"x86"}}],"value":"-Xss1M"},"-Djava.library.path=${natives_directory}","-Dminecraft.launcher.brand=${launcher_name}","-cp","${classpath}"]},
"assetIndex":{"id":"17"},"javaVersion":{"component":"java-runtime-delta"},"logging":{"client":{"argument":"-Dlog4j.configurationFile=${path}","file":{"id":"client-1.12.xml"}}},
"libraries":[
{"name":"ca.weblite:java-objc-bridge:1.1","rules":[{"action":"allow","os":{"name":"osx"}}],"downloads":{"artifact":{"path":"ca/x.jar","url":"u"}}},
{"name":"org.ow2.asm:asm:9.6","downloads":{"artifact":{"path":"org/ow2/asm/asm/9.6/asm-9.6.jar","url":"u"}}},
{"name":"org.lwjgl:lwjgl:3.3.3","downloads":{"artifact":{"path":"org/lwjgl/lwjgl/3.3.3/lwjgl-3.3.3.jar","url":"u"}}},
{"name":"org.lwjgl:lwjgl:3.3.3:natives-linux","rules":[{"action":"allow","os":{"name":"linux"}}],"downloads":{"artifact":{"path":"l-linux.jar","url":"u"}}},
{"name":"org.lwjgl:lwjgl:3.3.3:natives-windows","rules":[{"action":"allow","os":{"name":"windows"}}],"downloads":{"artifact":{"path":"l-win.jar","url":"u"}}}]}`

const fabFix = `{"id":"fabric-loader-0.20.1-1.21.1","mainClass":"net.fabricmc.loader.impl.launch.knot.KnotClient","arguments":{"game":[],"jvm":["-DFabricMcEmu= net.minecraft.client.main.Main "]},
"libraries":[{"name":"org.ow2.asm:asm:9.10.1","url":"https://maven.fabricmc.net/","sha1":"a"},{"name":"net.fabricmc:fabric-loader:0.20.1","url":"https://maven.fabricmc.net/"}]}`

func TestLaunchCommand(t *testing.T) {
	currentOS = "windows"
	var van, fab VersionJSON
	if err := json.Unmarshal([]byte(vanFix), &van); err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal([]byte(fabFix), &fab); err != nil {
		t.Fatal(err)
	}
	g := &Game{Dir: "/D", Instance: "/D/instance"}
	tasks, cp := g.libraries(&van, &fab)
	all := strings.Join(cp, "\n")
	for _, want := range []string{"l-win.jar", "asm-9.10.1.jar", "fabric-loader-0.20.1.jar", "lwjgl-3.3.3.jar"} {
		if !strings.Contains(all, want) {
			t.Errorf("classpath sans %s", want)
		}
	}
	for _, bad := range []string{"l-linux.jar", "ca/x.jar", "asm-9.6.jar"} {
		if strings.Contains(all, bad) {
			t.Errorf("classpath contient %s", bad)
		}
	}
	if tasks[0].URL != "https://maven.fabricmc.net/org/ow2/asm/asm/9.10.1/asm-9.10.1.jar" {
		t.Errorf("url fabric: %s", tasks[0].URL)
	}
	c := g.command(&van, &fab, "/J", append(cp, "/D/client.jar"), "/D/log.xml",
		LaunchOptions{Acc: &Account{Name: "Steve", UUID: "uuid", XUID: "x", MCToken: "tok"}, RAM: 4096, Server: "localhost"})
	line := strings.Join(c.Args, " ")
	t.Log(line)
	for _, want := range []string{"-Xmx4096M", "HeapDumpPath", "-DFabricMcEmu= net.minecraft.client.main.Main ", "KnotClient --username Steve",
		"--accessToken tok", "--userType msa", "--quickPlayMultiplayer localhost", "-Dlog4j.configurationFile=/D/log.xml", "--version fabric-loader-0.20.1-1.21.1"} {
		if !strings.Contains(line, want) {
			t.Errorf("commande sans %q", want)
		}
	}
	for _, bad := range []string{"--demo", "-XstartOnFirstThread", "-Xss1M", "${"} {
		if strings.Contains(line, bad) {
			t.Errorf("commande contient %q", bad)
		}
	}
	if !strings.HasSuffix(c.Args[0], "javaw.exe") && currentOS == "windows" && osName() == "windows" {
		t.Error("javaw attendu")
	}
}

func TestPKCE(t *testing.T) {
	p := newPKCE()
	u := authorizeURL(p, "http://localhost:1234")
	for _, w := range []string{"consumers", "client_id=" + MSClientID, "code_challenge_method=S256", "XboxLive.signin", "redirect_uri=http%3A%2F%2Flocalhost%3A1234"} {
		if !strings.Contains(u, w) {
			t.Errorf("url sans %s", w)
		}
	}
}
