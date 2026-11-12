package main

// Réglages fixes du launcher. Le reste (adresse du serveur, actus, version
// minimale du launcher) est lu en ligne dans launcher.json sur GitHub, pour
// pouvoir changer sans redistribuer l'exe.
const (
	LauncherName    = "CobbleSkyblock Launcher"
	LauncherVersion = "1.0.0"
	DataDirName     = ".cobbleskyblock"

	// Application Azure "CobbleSkyblock Launcher" (comptes Microsoft personnels).
	MSClientID = "85f2af90-a0fa-415c-ae22-4226c78a7048"

	RepoRaw       = "https://raw.githubusercontent.com/Thozire/CobbleSkyblock/main"
	PackURL       = RepoRaw + "/pack.toml"
	RemoteConfURL = RepoRaw + "/launcher.json"
	ReleasesURL   = "https://github.com/Thozire/CobbleSkyblock/raw/main/launcher/CobbleSkyblock-Launcher.exe"

	MCVersion     = "1.21.1"
	FabricLoader  = "0.20.1"
	DefaultServer = "localhost"
)
