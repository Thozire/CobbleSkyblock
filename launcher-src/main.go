package main

import (
	"embed"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

//go:embed ui
var uiFiles embed.FS

type Settings struct {
	RAM int `json:"ram"`
}

type News struct {
	Title string `json:"title"`
	Text  string `json:"text"`
	Date  string `json:"date"`
}

type RemoteConf struct {
	Server         string `json:"server"`
	ServerName     string `json:"serverName"`
	LatestLauncher string `json:"latestLauncher"`
	Message        string `json:"message"`
	News           []News `json:"news"`
}

type App struct {
	mu       sync.Mutex
	acc      *Account
	busy     bool
	status   string
	frac     float64
	errMsg   string
	gameOn   bool
	logs     []string
	settings Settings
	remote   RemoteConf
	lastPing time.Time
	pending  *pkce
	redirect string
	logFile  *os.File
}

var app = &App{}

func (a *App) log(s string) {
	line := time.Now().Format("15:04:05") + " " + s
	a.mu.Lock()
	a.logs = append(a.logs, line)
	if len(a.logs) > 400 {
		a.logs = a.logs[len(a.logs)-400:]
	}
	if a.logFile != nil {
		fmt.Fprintln(a.logFile, line)
	}
	a.mu.Unlock()
}

func (a *App) setProgress(s string, f float64) {
	a.mu.Lock()
	a.status, a.frac = s, f
	a.mu.Unlock()
}

func (a *App) fail(err error) {
	msg := err.Error()
	switch {
	case errors.Is(err, ErrNotApproved):
		msg = "Microsoft n'a pas encore autorisé ce launcher à se connecter à Minecraft. Réessaie dans quelques jours (en attendant, utilise l'instance Prism)."
	case errors.Is(err, ErrNoGame):
		msg = "Ce compte Microsoft ne possède pas Minecraft Java Edition. Il faut l'acheter sur minecraft.net pour jouer."
	}
	a.log("ERREUR : " + msg)
	a.mu.Lock()
	a.errMsg, a.busy, a.status = msg, false, ""
	a.mu.Unlock()
}

func settingsPath() string { return filepath.Join(dataDir(), "settings.json") }

func (a *App) loadSettings() {
	a.settings = Settings{RAM: 4096}
	if b, err := os.ReadFile(settingsPath()); err == nil {
		json.Unmarshal(b, &a.settings)
	}
	if a.settings.RAM < 2048 {
		a.settings.RAM = 2048
	}
}

func (a *App) saveSettings() {
	b, _ := json.MarshalIndent(a.settings, "", "  ")
	os.WriteFile(settingsPath(), b, 0644)
}

func (a *App) fetchRemote() {
	var rc RemoteConf
	if err := fetchJSON(RemoteConfURL, &rc); err != nil {
		a.log("launcher.json indisponible : " + err.Error())
		rc.Server = DefaultServer
	}
	if rc.Server == "" {
		rc.Server = DefaultServer
	}
	a.mu.Lock()
	a.remote = rc
	a.mu.Unlock()
}

func (a *App) state() map[string]any {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.lastPing = time.Now()
	var acc any
	if a.acc != nil {
		acc = map[string]string{"name": a.acc.Name, "uuid": a.acc.UUID}
	}
	tail := a.logs
	if len(tail) > 120 {
		tail = tail[len(tail)-120:]
	}
	return map[string]any{
		"account": acc, "busy": a.busy, "status": a.status, "progress": a.frac, "error": a.errMsg,
		"gameRunning": a.gameOn, "ram": a.settings.RAM, "remote": a.remote, "logs": tail,
		"version": LauncherVersion, "update": a.remote.LatestLauncher != "" && a.remote.LatestLauncher != LauncherVersion,
		"releases": ReleasesURL,
	}
}

func (a *App) begin(status string) bool {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.busy {
		return false
	}
	a.busy, a.errMsg, a.status, a.frac = true, "", status, 0
	return true
}

func (a *App) play(deep bool) {
	defer func() {
		if r := recover(); r != nil {
			a.fail(fmt.Errorf("erreur inattendue : %v", r))
		}
	}()
	a.mu.Lock()
	acc, ram, server := a.acc, a.settings.RAM, a.remote.Server
	a.mu.Unlock()
	if acc == nil {
		a.fail(errors.New("connecte-toi d'abord avec ton compte Microsoft"))
		return
	}
	a.setProgress("Vérification du compte…", 0)
	acc, err := ensureFresh(acc)
	if err != nil {
		a.fail(err)
		return
	}
	a.mu.Lock()
	a.acc = acc
	a.mu.Unlock()
	g := &Game{Dir: dataDir(), Instance: filepath.Join(dataDir(), "instance"), Progress: a.setProgress, Log: a.log, Deep: deep}
	cmd, err := g.Prepare(LaunchOptions{Acc: acc, RAM: ram, Server: server})
	if err != nil {
		a.fail(err)
		return
	}
	logPath := filepath.Join(dataDir(), "derniere-partie.log")
	lf, _ := os.Create(logPath)
	cmd.Stdout, cmd.Stderr = lf, lf
	detach(cmd)
	a.log("Lancement : " + acc.Name + " -> " + server)
	if err := cmd.Start(); err != nil {
		a.fail(fmt.Errorf("impossible de démarrer Minecraft : %v", err))
		return
	}
	start := time.Now()
	a.mu.Lock()
	a.busy, a.gameOn, a.status = false, true, "Minecraft est lancé, bon jeu !"
	a.mu.Unlock()
	go func() {
		err := cmd.Wait()
		lf.Close()
		a.mu.Lock()
		a.gameOn, a.status = false, ""
		a.mu.Unlock()
		if err != nil && time.Since(start) < 60*time.Second {
			a.fail(fmt.Errorf("Minecraft s'est fermé au démarrage. Le détail est dans %s", logPath))
		} else {
			a.log("Minecraft s'est fermé.")
		}
	}()
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	json.NewEncoder(w).Encode(v)
}

func (a *App) routes() http.Handler {
	mux := http.NewServeMux()
	sub, _ := fs.Sub(uiFiles, "ui")
	static := http.FileServer(http.FS(sub))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		q := r.URL.Query()
		if r.URL.Path == "/" && (q.Get("code") != "" || q.Get("error") != "") {
			a.oauthCallback(q.Get("code"), q.Get("state"), q.Get("error"), q.Get("error_description"))
			http.Redirect(w, r, "/", http.StatusFound)
			return
		}
		static.ServeHTTP(w, r)
	})
	mux.HandleFunc("/api/state", func(w http.ResponseWriter, r *http.Request) { writeJSON(w, a.state()) })
	mux.HandleFunc("/api/login", func(w http.ResponseWriter, r *http.Request) {
		p := newPKCE()
		a.mu.Lock()
		a.pending = &p
		a.errMsg = ""
		a.lastPing = time.Now().Add(15 * time.Minute) // la fenêtre est sur la page Microsoft pendant la connexion
		a.mu.Unlock()
		writeJSON(w, map[string]string{"url": authorizeURL(p, a.redirect)})
	})
	mux.HandleFunc("/api/logout", func(w http.ResponseWriter, r *http.Request) {
		logout()
		a.mu.Lock()
		a.acc = nil
		a.mu.Unlock()
		writeJSON(w, a.state())
	})
	mux.HandleFunc("/api/play", func(w http.ResponseWriter, r *http.Request) {
		deep := r.URL.Query().Get("repair") == "1"
		if a.begin("Préparation…") {
			go a.play(deep)
		}
		writeJSON(w, a.state())
	})
	mux.HandleFunc("/api/settings", func(w http.ResponseWriter, r *http.Request) {
		var s Settings
		if json.NewDecoder(r.Body).Decode(&s) == nil && s.RAM >= 2048 && s.RAM <= 32768 {
			a.mu.Lock()
			a.settings.RAM = s.RAM
			a.mu.Unlock()
			a.saveSettings()
		}
		writeJSON(w, a.state())
	})
	mux.HandleFunc("/api/folder", func(w http.ResponseWriter, r *http.Request) {
		d := filepath.Join(dataDir(), "instance")
		os.MkdirAll(d, 0755)
		openFolder(d)
		writeJSON(w, map[string]bool{"ok": true})
	})
	mux.HandleFunc("/api/dismiss", func(w http.ResponseWriter, r *http.Request) {
		a.mu.Lock()
		a.errMsg = ""
		a.mu.Unlock()
		writeJSON(w, a.state())
	})
	return mux
}

func (a *App) oauthCallback(code, state, errCode, errDesc string) {
	a.mu.Lock()
	p := a.pending
	a.pending = nil
	a.mu.Unlock()
	if errCode != "" {
		if errCode == "access_denied" {
			a.log("Connexion annulée.")
			return
		}
		a.fail(fmt.Errorf("Microsoft : %s %s", errCode, errDesc))
		return
	}
	if p == nil || state != p.state {
		a.fail(errors.New("connexion invalide, réessaie"))
		return
	}
	if !a.begin("Connexion à Minecraft…") {
		return
	}
	go func() {
		acc, err := loginWithCode(code, a.redirect, *p)
		if err != nil {
			a.fail(err)
			return
		}
		a.log("Connecté : " + acc.Name)
		a.mu.Lock()
		a.acc, a.busy, a.status = acc, false, ""
		a.mu.Unlock()
	}()
}

func main() {
	os.MkdirAll(dataDir(), 0755)
	portFile := filepath.Join(dataDir(), "launcher.port")
	// Une seule fenêtre : si le launcher tourne déjà, on rouvre simplement son interface.
	if b, err := os.ReadFile(portFile); err == nil {
		port := strings.TrimSpace(string(b))
		c := http.Client{Timeout: time.Second}
		if resp, err := c.Get("http://127.0.0.1:" + port + "/api/state"); err == nil {
			resp.Body.Close()
			openAppWindow("http://localhost:" + port + "/")
			return
		}
	}
	if len(os.Args) > 1 && os.Args[1] == "--verifier" {
		checkInstall()
		return
	}
	app.logFile, _ = os.Create(filepath.Join(dataDir(), "launcher.log"))
	app.loadSettings()
	app.acc = loadAccount()
	app.lastPing = time.Now()

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		messageBox(LauncherName, "Impossible de démarrer le launcher : "+err.Error())
		return
	}
	port := ln.Addr().(*net.TCPAddr).Port
	if ln6, err := net.Listen("tcp", fmt.Sprintf("[::1]:%d", port)); err == nil {
		go http.Serve(ln6, app.routes())
	}
	app.redirect = fmt.Sprintf("http://localhost:%d", port)
	os.WriteFile(portFile, []byte(fmt.Sprint(port)), 0644)
	app.log(LauncherName + " " + LauncherVersion)
	go app.fetchRemote()

	go func() {
		// Le launcher se ferme quand sa fenêtre est fermée (le jeu, lui, continue).
		for range time.Tick(3 * time.Second) {
			app.mu.Lock()
			idle := time.Since(app.lastPing) > 20*time.Second && !app.busy
			app.mu.Unlock()
			if idle && os.Getenv("CSL_NOEXIT") == "" {
				os.Remove(portFile)
				os.Exit(0)
			}
		}
	}()
	if _, err := openAppWindow(app.redirect + "/"); err != nil {
		messageBox(LauncherName, "Impossible d'ouvrir la fenêtre : "+err.Error())
	}
	http.Serve(ln, app.routes())
}

// checkInstall (--verifier) : télécharge et vérifie tous les fichiers du jeu
// sans se connecter ni lancer Minecraft. Sert à tester une installation.
func checkInstall() {
	lf, _ := os.Create(filepath.Join(dataDir(), "verification.log"))
	defer lf.Close()
	last := ""
	g := &Game{Dir: dataDir(), Instance: filepath.Join(dataDir(), "instance"), Deep: true,
		Log: func(s string) { fmt.Fprintln(lf, s) },
		Progress: func(s string, f float64) {
			if s != last {
				last = s
				fmt.Fprintf(lf, "%s %s\n", time.Now().Format("15:04:05"), s)
			}
		}}
	start := time.Now()
	in, err := g.install()
	if err != nil {
		fmt.Fprintln(lf, "ECHEC :", err)
		messageBox(LauncherName, "Échec de la vérification :\n"+err.Error()+"\n\nDétail : "+filepath.Join(dataDir(), "verification.log"))
		return
	}
	mods, _ := filepath.Glob(filepath.Join(g.Instance, "mods", "*.jar"))
	msg := fmt.Sprintf("Tout est installé en %s.\n\nJava : %s\nBibliothèques : %d\nMods : %d\nDossier : %s",
		time.Since(start).Round(time.Second), filepath.Base(in.javaDir), len(in.cp), len(mods), dataDir())
	fmt.Fprintln(lf, "OK", msg)
	messageBox(LauncherName, msg, true)
}
