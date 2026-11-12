# CobbleSkyblock Launcher — compilation

Go 1.24+, aucune dépendance externe.

    GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-H windowsgui -s -w" -o CobbleSkyblock-Launcher.exe .

- `config.go` : ID de l'application Azure, adresse du modpack, versions.
- `launcher.json` (à la racine du dépôt) : adresse du serveur, actus, message, dernière version du launcher.
- `CobbleSkyblock-Launcher.exe --verifier` : télécharge et vérifie tout sans lancer le jeu.
