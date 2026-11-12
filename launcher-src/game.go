package main

import (
	"bufio"
	_ "embed"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
)

//go:embed packwiz-installer-bootstrap.jar
var bootstrapJar []byte

var currentOS = osName()

const javaRuntimeIndex = "https://launchermeta.mojang.com/v1/products/java-runtime/2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json"
const versionManifest = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

type Rule struct {
	Action   string            `json:"action"`
	OS       map[string]string `json:"os"`
	Features map[string]bool   `json:"features"`
}

func rulesAllow(rules []Rule) bool {
	if len(rules) == 0 {
		return true
	}
	allowed := false
	for _, r := range rules {
		match := true
		if n, ok := r.OS["name"]; ok && n != currentOS {
			match = false
		}
		if a, ok := r.OS["arch"]; ok && !(a == "x86" && runtime.GOARCH == "386") {
			match = false
		}
		if len(r.Features) > 0 {
			match = false // aucune option spéciale (démo, résolution forcée...) n'est activée
		}
		if match {
			allowed = r.Action == "allow"
		}
	}
	return allowed
}

type Artifact struct {
	Path, URL, SHA1 string
	Size            int64
}

type Library struct {
	Name      string `json:"name"`
	URL       string `json:"url"`
	SHA1      string `json:"sha1"`
	Size      int64  `json:"size"`
	Downloads struct {
		Artifact *Artifact `json:"artifact"`
	} `json:"downloads"`
	Rules []Rule `json:"rules"`
}

// Arg est soit une chaîne, soit {rules, value}.
type Arg struct {
	Values []string
	Rules  []Rule
}

func (a *Arg) UnmarshalJSON(b []byte) error {
	var s string
	if json.Unmarshal(b, &s) == nil {
		a.Values = []string{s}
		return nil
	}
	var o struct {
		Rules []Rule          `json:"rules"`
		Value json.RawMessage `json:"value"`
	}
	if err := json.Unmarshal(b, &o); err != nil {
		return err
	}
	a.Rules = o.Rules
	if json.Unmarshal(o.Value, &s) == nil {
		a.Values = []string{s}
		return nil
	}
	return json.Unmarshal(o.Value, &a.Values)
}

type VersionJSON struct {
	ID        string `json:"id"`
	MainClass string `json:"mainClass"`
	Type      string `json:"type"`
	Arguments struct {
		Game []Arg `json:"game"`
		JVM  []Arg `json:"jvm"`
	} `json:"arguments"`
	AssetIndex struct {
		ID, URL, SHA1 string
		Size          int64
	} `json:"assetIndex"`
	Assets    string `json:"assets"`
	Downloads struct {
		Client Artifact `json:"client"`
	} `json:"downloads"`
	JavaVersion struct {
		Component string `json:"component"`
	} `json:"javaVersion"`
	Libraries []Library `json:"libraries"`
	Logging   struct {
		Client struct {
			Argument string `json:"argument"`
			File     struct {
				ID, URL, SHA1 string
				Size          int64
			} `json:"file"`
		} `json:"client"`
	} `json:"logging"`
}

func fetchJSON(u string, out any) error {
	resp, err := httpClient.Get(u)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("HTTP %d : %s", resp.StatusCode, u)
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

// cachedJSON télécharge un JSON et le garde sur le disque, pour pouvoir
// relancer même si un serveur de Mojang ne répond pas.
func cachedJSON(u, path string, out any) error {
	var raw json.RawMessage
	if err := fetchJSON(u, &raw); err == nil {
		os.MkdirAll(filepath.Dir(path), 0755)
		os.WriteFile(path, raw, 0644)
		return json.Unmarshal(raw, out)
	}
	b, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("impossible de joindre les serveurs de Minecraft")
	}
	return json.Unmarshal(b, out)
}

func mavenPath(name string) string {
	p := strings.Split(name, ":")
	if len(p) < 3 {
		return ""
	}
	file := p[1] + "-" + p[2]
	if len(p) > 3 {
		file += "-" + p[3]
	}
	return filepath.Join(append(strings.Split(p[0], "."), p[1], p[2], file+".jar")...)
}

func libKey(name string) string {
	p := strings.Split(name, ":")
	if len(p) > 3 {
		return p[0] + ":" + p[1] + ":" + p[3]
	}
	if len(p) >= 2 {
		return p[0] + ":" + p[1]
	}
	return name
}

type Game struct {
	Dir      string // dossier commun (libraries, assets, versions, runtime)
	Instance string // dossier de jeu (mods, saves, options)
	Progress func(string, float64)
	Log      func(string)
	Deep     bool
}

func (g *Game) p(s string, f float64) {
	if g.Progress != nil {
		g.Progress(s, f)
	}
}

// ensureJava installe le Java fourni par Mojang (le même que le launcher officiel).
func (g *Game) ensureJava(component string) (string, error) {
	g.p("Préparation de Java…", 0)
	var idx map[string]map[string][]struct {
		Manifest struct{ URL, SHA1 string } `json:"manifest"`
	}
	if err := cachedJSON(javaRuntimeIndex, filepath.Join(g.Dir, "runtime", "all.json"), &idx); err != nil {
		return "", err
	}
	plat := "windows-x64"
	if osName() != "windows" {
		plat = "linux"
	}
	list := idx[plat][component]
	if len(list) == 0 {
		return "", fmt.Errorf("Java %s introuvable pour %s", component, plat)
	}
	var man struct {
		Files map[string]struct {
			Type       string `json:"type"`
			Executable bool   `json:"executable"`
			Downloads  struct {
				Raw struct {
					URL, SHA1 string
					Size      int64
				} `json:"raw"`
			} `json:"downloads"`
		} `json:"files"`
	}
	rt := filepath.Join(g.Dir, "runtime", component)
	if err := cachedJSON(list[0].Manifest.URL, filepath.Join(g.Dir, "runtime", component+".json"), &man); err != nil {
		return "", err
	}
	var tasks []dlTask
	for p, f := range man.Files {
		dst := filepath.Join(rt, filepath.FromSlash(p))
		switch f.Type {
		case "directory":
			os.MkdirAll(dst, 0755)
		case "file":
			tasks = append(tasks, dlTask{URL: f.Downloads.Raw.URL, Path: dst, SHA1: f.Downloads.Raw.SHA1, Size: f.Downloads.Raw.Size, Exec: f.Executable})
		}
	}
	return rt, downloadAll("Installation de Java", tasks, g.Deep, g.Progress)
}

func (g *Game) loadVersions() (*VersionJSON, *VersionJSON, error) {
	g.p("Lecture des versions…", 0)
	var man struct {
		Versions []struct{ ID, URL string } `json:"versions"`
	}
	vdir := filepath.Join(g.Dir, "versions")
	if err := cachedJSON(versionManifest, filepath.Join(vdir, "version_manifest_v2.json"), &man); err != nil {
		return nil, nil, err
	}
	var vurl string
	for _, v := range man.Versions {
		if v.ID == MCVersion {
			vurl = v.URL
		}
	}
	var van VersionJSON
	if err := cachedJSON(vurl, filepath.Join(vdir, MCVersion, MCVersion+".json"), &van); err != nil {
		return nil, nil, err
	}
	var fab VersionJSON
	fid := "fabric-loader-" + FabricLoader + "-" + MCVersion
	if err := cachedJSON(fmt.Sprintf("https://meta.fabricmc.net/v2/versions/loader/%s/%s/profile/json", MCVersion, FabricLoader),
		filepath.Join(vdir, fid, fid+".json"), &fab); err != nil {
		return nil, nil, err
	}
	return &van, &fab, nil
}

// classpath fusionne les bibliothèques vanilla et Fabric (Fabric gagne en cas de doublon).
func (g *Game) libraries(van, fab *VersionJSON) ([]dlTask, []string) {
	libDir := filepath.Join(g.Dir, "libraries")
	type entry struct {
		key  string
		task dlTask
	}
	var order []entry
	add := func(l Library, isFabric bool) {
		if !rulesAllow(l.Rules) {
			return
		}
		var t dlTask
		if a := l.Downloads.Artifact; a != nil && a.URL != "" {
			t = dlTask{URL: a.URL, Path: filepath.Join(libDir, filepath.FromSlash(a.Path)), SHA1: a.SHA1, Size: a.Size}
		} else if l.URL != "" {
			mp := mavenPath(l.Name)
			base := strings.TrimRight(l.URL, "/") + "/"
			t = dlTask{URL: base + filepath.ToSlash(mp), Path: filepath.Join(libDir, mp), SHA1: l.SHA1, Size: l.Size}
		} else {
			return
		}
		k := libKey(l.Name)
		for i, e := range order {
			if e.key == k {
				if isFabric {
					order[i].task = t
				}
				return
			}
		}
		order = append(order, entry{k, t})
	}
	for _, l := range van.Libraries {
		add(l, false)
	}
	for _, l := range fab.Libraries {
		add(l, true)
	}
	var tasks []dlTask
	var cp []string
	for _, e := range order {
		tasks = append(tasks, e.task)
		cp = append(cp, e.task.Path)
	}
	return tasks, cp
}

func (g *Game) assets(van *VersionJSON) error {
	adir := filepath.Join(g.Dir, "assets")
	idxPath := filepath.Join(adir, "indexes", van.AssetIndex.ID+".json")
	if err := downloadAll("Index des ressources", []dlTask{{URL: van.AssetIndex.URL, Path: idxPath, SHA1: van.AssetIndex.SHA1}}, true, g.Progress); err != nil {
		return err
	}
	b, err := os.ReadFile(idxPath)
	if err != nil {
		return err
	}
	var idx struct {
		Objects map[string]struct {
			Hash string
			Size int64
		} `json:"objects"`
	}
	json.Unmarshal(b, &idx)
	var tasks []dlTask
	for _, o := range idx.Objects {
		tasks = append(tasks, dlTask{URL: "https://resources.download.minecraft.net/" + o.Hash[:2] + "/" + o.Hash,
			Path: filepath.Join(adir, "objects", o.Hash[:2], o.Hash), SHA1: o.Hash, Size: o.Size})
	}
	return downloadAll("Sons et textures", tasks, g.Deep, g.Progress)
}

var pwProgress = regexp.MustCompile(`\((\d+)/(\d+)\)`)

// syncModpack lance packwiz pour aligner mods, configs et resource packs sur GitHub.
func (g *Game) syncModpack(javaDir string) error {
	g.p("Synchronisation du modpack…", 0)
	os.MkdirAll(g.Instance, 0755)
	bs := filepath.Join(g.Instance, "packwiz-installer-bootstrap.jar")
	if cur, _ := os.ReadFile(bs); len(cur) != len(bootstrapJar) {
		os.WriteFile(bs, bootstrapJar, 0644)
	}
	java := filepath.Join(javaDir, "bin", "java")
	if osName() == "windows" {
		java += ".exe"
	}
	c := exec.Command(java, "-jar", bs, "-g", "-s", "client", PackURL)
	c.Dir = g.Instance
	hideWindow(c)
	out, _ := c.StdoutPipe()
	c.Stderr = c.Stdout
	if err := c.Start(); err != nil {
		return err
	}
	sc := bufio.NewScanner(out)
	var tail []string
	for sc.Scan() {
		line := sc.Text()
		if g.Log != nil {
			g.Log("[modpack] " + line)
		}
		tail = append(tail, line)
		if len(tail) > 5 {
			tail = tail[1:]
		}
		if m := pwProgress.FindStringSubmatch(line); m != nil {
			var a, b float64
			fmt.Sscan(m[1], &a)
			fmt.Sscan(m[2], &b)
			if b > 0 {
				g.p(fmt.Sprintf("Mods du serveur (%s/%s)", m[1], m[2]), a/b)
			}
		}
	}
	if err := c.Wait(); err != nil {
		return fmt.Errorf("la mise à jour des mods a échoué : %s", strings.Join(tail, " | "))
	}
	return nil
}

type LaunchOptions struct {
	Acc    *Account
	RAM    int
	Server string
}

type installed struct {
	van, fab *VersionJSON
	javaDir  string
	cp       []string
	logCfg   string
}

// install télécharge / met à jour Java, Minecraft, Fabric, les ressources et le modpack.
func (g *Game) install() (*installed, error) {
	van, fab, err := g.loadVersions()
	if err != nil {
		return nil, err
	}
	javaDir, err := g.ensureJava(van.JavaVersion.Component)
	if err != nil {
		return nil, err
	}
	libTasks, cp := g.libraries(van, fab)
	clientJar := filepath.Join(g.Dir, "versions", MCVersion, MCVersion+".jar")
	libTasks = append(libTasks, dlTask{URL: van.Downloads.Client.URL, Path: clientJar, SHA1: van.Downloads.Client.SHA1, Size: van.Downloads.Client.Size})
	logCfg := filepath.Join(g.Dir, "assets", "log_configs", van.Logging.Client.File.ID)
	if van.Logging.Client.File.URL != "" {
		libTasks = append(libTasks, dlTask{URL: van.Logging.Client.File.URL, Path: logCfg, SHA1: van.Logging.Client.File.SHA1})
	}
	if err := downloadAll("Fichiers de Minecraft", libTasks, g.Deep, g.Progress); err != nil {
		return nil, err
	}
	if err := g.assets(van); err != nil {
		return nil, err
	}
	if err := g.syncModpack(javaDir); err != nil {
		return nil, err
	}
	return &installed{van, fab, javaDir, append(cp, clientJar), logCfg}, nil
}

// Prepare installe tout, puis renvoie la commande de lancement.
func (g *Game) Prepare(o LaunchOptions) (*exec.Cmd, error) {
	in, err := g.install()
	if err != nil {
		return nil, err
	}
	g.p("Lancement de Minecraft…", 1)
	return g.command(in.van, in.fab, in.javaDir, in.cp, in.logCfg, o), nil
}

func (g *Game) command(van, fab *VersionJSON, javaDir string, cp []string, logCfg string, o LaunchOptions) *exec.Cmd {
	natives := filepath.Join(g.Dir, "versions", MCVersion, "natives")
	os.MkdirAll(natives, 0755)
	sep := string(os.PathListSeparator)
	vars := map[string]string{
		"auth_player_name":    o.Acc.Name,
		"version_name":        fab.ID,
		"game_directory":      g.Instance,
		"assets_root":         filepath.Join(g.Dir, "assets"),
		"assets_index_name":   van.AssetIndex.ID,
		"auth_uuid":           o.Acc.UUID,
		"auth_access_token":   o.Acc.MCToken,
		"clientid":            MSClientID,
		"auth_xuid":           o.Acc.XUID,
		"user_type":           "msa",
		"version_type":        "release",
		"natives_directory":   natives,
		"launcher_name":       "CobbleSkyblock",
		"launcher_version":    LauncherVersion,
		"classpath":           strings.Join(cp, sep),
		"classpath_separator": sep,
		"library_directory":   filepath.Join(g.Dir, "libraries"),
		"user_properties":     "{}",
	}
	re := regexp.MustCompile(`\$\{([a-zA-Z_]+)\}`)
	expand := func(s string) string {
		return re.ReplaceAllStringFunc(s, func(m string) string {
			if v, ok := vars[m[2:len(m)-1]]; ok {
				return v
			}
			return m
		})
	}
	collect := func(args []Arg) []string {
		var out []string
		for _, a := range args {
			if rulesAllow(a.Rules) {
				for _, v := range a.Values {
					out = append(out, expand(v))
				}
			}
		}
		return out
	}
	args := []string{fmt.Sprintf("-Xmx%dM", o.RAM), "-Xms1024M", "-XX:+UseG1GC", "-XX:+UnlockExperimentalVMOptions",
		"-XX:G1NewSizePercent=20", "-XX:G1ReservePercent=20", "-XX:MaxGCPauseMillis=50", "-XX:G1HeapRegionSize=32M"}
	args = append(args, collect(van.Arguments.JVM)...)
	args = append(args, collect(fab.Arguments.JVM)...)
	if van.Logging.Client.Argument != "" {
		args = append(args, strings.ReplaceAll(van.Logging.Client.Argument, "${path}", logCfg))
	}
	args = append(args, fab.MainClass)
	args = append(args, collect(van.Arguments.Game)...)
	args = append(args, collect(fab.Arguments.Game)...)
	if o.Server != "" {
		args = append(args, "--quickPlayMultiplayer", o.Server)
	}
	c := exec.Command(javaExe(javaDir), args...)
	c.Dir = g.Instance
	return c
}
