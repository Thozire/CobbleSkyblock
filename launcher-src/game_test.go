package main

import (
	"encoding/json"
	"os"
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

func TestLaunchCommandNeoForge(t *testing.T) {
	currentOS = "windows"
	var van, neo VersionJSON
	if err := json.Unmarshal([]byte(vanFix), &van); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile("testdata/neoforge-21.1.267.json") // profil réel extrait de l'installeur
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(b, &neo); err != nil {
		t.Fatal(err)
	}
	g := &Game{Dir: "/D", Instance: "/D/instance"}
	tasks, cp := g.libraries(&van, &neo)
	all := strings.Join(cp, "\n")
	for _, want := range []string{"l-win.jar", "lwjgl-3.3.3.jar", "bootstraplauncher-2.0.2.jar", "securejarhandler-3.0.8.jar", "asm-9.10.1.jar", "fancymodloader"} {
		if !strings.Contains(all, want) {
			t.Errorf("classpath sans %s", want)
		}
	}
	for _, bad := range []string{"l-linux.jar", "ca/x.jar", "asm-9.6.jar"} {
		if strings.Contains(all, bad) {
			t.Errorf("classpath contient %s", bad)
		}
	}
	for _, tk := range tasks {
		if tk.URL == "" {
			t.Errorf("tâche sans URL : %s", tk.Path)
		}
	}
	verJar := "/D/versions/" + neo.ID + "/" + neo.ID + ".jar"
	c := g.command(&van, &neo, "/J", append(cp, verJar), "/D/log.xml",
		LaunchOptions{Acc: &Account{Name: "Steve", UUID: "uuid", XUID: "x", MCToken: "tok"}, RAM: 6144, Server: "localhost"})
	line := strings.Join(c.Args, " ")
	t.Log(line)
	for _, want := range []string{"-Xmx6144M", "-DignoreList=client-extra,neoforge-21.1.267.jar", "-DlibraryDirectory=/D/libraries",
		"-p /D/libraries/cpw/mods/bootstraplauncher/2.0.2/bootstraplauncher-2.0.2.jar", "--add-modules ALL-MODULE-PATH",
		"cpw.mods.bootstraplauncher.BootstrapLauncher --username Steve", "--launchTarget forgeclient", "--fml.neoForgeVersion 21.1.267",
		"--version neoforge-21.1.267", "--quickPlayMultiplayer localhost", verJar} {
		if !strings.Contains(line, want) {
			t.Errorf("commande sans %q", want)
		}
	}
	if strings.Contains(line, "/D/versions/1.21.1/1.21.1.jar") {
		t.Error("le jar vanilla ne doit pas être dans le classpath (FML le prendrait pour un mod)")
	}
	for _, bad := range []string{"--demo", "-XstartOnFirstThread", "-Xss1M", "${"} {
		if strings.Contains(line, bad) {
			t.Errorf("commande contient %q", bad)
		}
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
