package main

// Réglages fixes du launcher. Le reste (adresse du serveur, actus, version
// minimale du launcher) est lu en ligne dans launcher.json sur GitHub, pour
// pouvoir changer sans redistribuer l'exe.
const (
	LauncherName    = "CobbleSkyblock Launcher"
	LauncherVersion = "2.0.0"
	DataDirName     = ".cobbleskyblock"

	// Application Azure "CobbleSkyblock Launcher" (comptes Microsoft personnels).
	MSClientID = "85f2af90-a0fa-415c-ae22-4226c78a7048"

	RepoRaw       = "https://raw.githubusercontent.com/Thozire/CobbleSkyblock/main"
	PackURL       = RepoRaw + "/pack.toml"
	RemoteConfURL = RepoRaw + "/launcher.json"
	ReleasesURL   = "https://github.com/Thozire/CobbleSkyblock/raw/main/launcher/CobbleSkyblock-Launcher.exe"

	MCVersion     = "1.21.1"
	DefaultServer = "localhost"

	// NeoForge (MineColonies). L'installeur officiel est lancé en mode client
	// la première fois ; son empreinte est vérifiée avant de l'exécuter.
	NeoForgeVersion       = "21.1.267"
	NeoForgeInstallerSHA1 = "4565232f0bf231d0edfe512b949664dc5ff88fd8"
)
