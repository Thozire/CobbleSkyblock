//go:build !windows

package main

// Version non-Windows : uniquement pour les tests de développement.

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

func protect(d []byte) ([]byte, error)   { return d, nil }
func unprotect(d []byte) ([]byte, error) { return d, nil }

func dataDir() string {
	if d := os.Getenv("CSL_DATA"); d != "" {
		return d
	}
	h, _ := os.UserHomeDir()
	return filepath.Join(h, DataDirName)
}

func osName() string {
	return "linux"
}

func javaExe(runtimeDir string) string            { return filepath.Join(runtimeDir, "bin", "java") }
func hideWindow(c *exec.Cmd)                      {}
func detach(c *exec.Cmd)                          {}
func messageBox(title, text string, info ...bool) { fmt.Fprintln(os.Stderr, title+": "+text) }
func openAppWindow(u string) (*exec.Cmd, error) {
	fmt.Println("Interface :", u)
	return nil, nil
}
func openFolder(p string) {}
