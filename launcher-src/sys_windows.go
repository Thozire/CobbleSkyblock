//go:build windows

package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"unsafe"
)

var (
	crypt32        = syscall.NewLazyDLL("crypt32.dll")
	kernel32       = syscall.NewLazyDLL("kernel32.dll")
	user32         = syscall.NewLazyDLL("user32.dll")
	procProtect    = crypt32.NewProc("CryptProtectData")
	procUnprotect  = crypt32.NewProc("CryptUnprotectData")
	procLocalFree  = kernel32.NewProc("LocalFree")
	procMessageBox = user32.NewProc("MessageBoxW")
)

type dataBlob struct {
	cbData uint32
	pbData *byte
}

func blobOf(d []byte) *dataBlob {
	if len(d) == 0 {
		return &dataBlob{}
	}
	return &dataBlob{cbData: uint32(len(d)), pbData: &d[0]}
}

func (b *dataBlob) bytes() []byte {
	out := make([]byte, b.cbData)
	copy(out, unsafe.Slice(b.pbData, b.cbData))
	return out
}

// protect/unprotect : chiffrement DPAPI lié à la session Windows de l'utilisateur.
func protect(d []byte) ([]byte, error) {
	var out dataBlob
	r, _, err := procProtect.Call(uintptr(unsafe.Pointer(blobOf(d))), 0, 0, 0, 0, 0x1, uintptr(unsafe.Pointer(&out)))
	if r == 0 {
		return nil, err
	}
	defer procLocalFree.Call(uintptr(unsafe.Pointer(out.pbData)))
	return out.bytes(), nil
}

func unprotect(d []byte) ([]byte, error) {
	var out dataBlob
	r, _, err := procUnprotect.Call(uintptr(unsafe.Pointer(blobOf(d))), 0, 0, 0, 0, 0x1, uintptr(unsafe.Pointer(&out)))
	if r == 0 {
		return nil, err
	}
	defer procLocalFree.Call(uintptr(unsafe.Pointer(out.pbData)))
	return out.bytes(), nil
}

func dataDir() string {
	base := os.Getenv("APPDATA")
	if base == "" {
		base, _ = os.UserHomeDir()
	}
	return filepath.Join(base, DataDirName)
}

func osName() string { return "windows" }

func javaExe(runtimeDir string) string { return filepath.Join(runtimeDir, "bin", "javaw.exe") }

func hideWindow(c *exec.Cmd) {
	c.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000} // CREATE_NO_WINDOW
}

func detach(c *exec.Cmd) {
	c.SysProcAttr = &syscall.SysProcAttr{CreationFlags: 0x00000008 | 0x00000200} // DETACHED_PROCESS | NEW_PROCESS_GROUP
}

func messageBox(title, text string, info ...bool) {
	t, _ := syscall.UTF16PtrFromString(title)
	m, _ := syscall.UTF16PtrFromString(text)
	flags := uintptr(0x10)
	if len(info) > 0 && info[0] {
		flags = 0x40
	}
	procMessageBox.Call(0, uintptr(unsafe.Pointer(m)), uintptr(unsafe.Pointer(t)), flags)
}

// openAppWindow ouvre l'interface dans une fenêtre Edge "application" (sans
// barre d'adresse). Edge est présent sur tous les Windows 10/11.
func openAppWindow(u string) (*exec.Cmd, error) {
	candidates := []string{
		filepath.Join(os.Getenv("ProgramFiles(x86)"), `Microsoft\Edge\Application\msedge.exe`),
		filepath.Join(os.Getenv("ProgramFiles"), `Microsoft\Edge\Application\msedge.exe`),
		filepath.Join(os.Getenv("LOCALAPPDATA"), `Microsoft\Edge\Application\msedge.exe`),
		filepath.Join(os.Getenv("ProgramFiles"), `Google\Chrome\Application\chrome.exe`),
		filepath.Join(os.Getenv("ProgramFiles(x86)"), `Google\Chrome\Application\chrome.exe`),
		filepath.Join(os.Getenv("LOCALAPPDATA"), `Google\Chrome\Application\chrome.exe`),
	}
	for _, exe := range candidates {
		if _, err := os.Stat(exe); err == nil {
			c := exec.Command(exe, "--app="+u, "--window-size=1000,640",
				"--user-data-dir="+filepath.Join(dataDir(), "ui-profile"),
				"--no-first-run", "--no-default-browser-check", "--disable-features=Translate")
			return c, c.Start()
		}
	}
	c := exec.Command("rundll32", "url.dll,FileProtocolHandler", u)
	return nil, c.Start()
}

func openFolder(p string) { exec.Command("explorer", p).Start() }
