package main

import (
	"crypto/sha1"
	"encoding/hex"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"sync/atomic"
	"time"
)

var httpClient = &http.Client{Timeout: 5 * time.Minute}

type dlTask struct {
	URL, Path, SHA1 string
	Size            int64
	Exec            bool
}

func fileSHA1(p string) string {
	f, err := os.Open(p)
	if err != nil {
		return ""
	}
	defer f.Close()
	h := sha1.New()
	io.Copy(h, f)
	return hex.EncodeToString(h.Sum(nil))
}

// needs indique si le fichier doit être (re)téléchargé.
func (t dlTask) needs(deep bool) bool {
	st, err := os.Stat(t.Path)
	if err != nil {
		return true
	}
	if t.Size > 0 && st.Size() != t.Size {
		return true
	}
	if deep && t.SHA1 != "" {
		return fileSHA1(t.Path) != t.SHA1
	}
	return false
}

func downloadOne(t dlTask) error {
	var last error
	for i := 0; i < 4; i++ {
		if i > 0 {
			time.Sleep(time.Duration(i) * time.Second)
		}
		last = func() error {
			resp, err := httpClient.Get(t.URL)
			if err != nil {
				return err
			}
			defer resp.Body.Close()
			if resp.StatusCode != 200 {
				return fmt.Errorf("HTTP %d pour %s", resp.StatusCode, t.URL)
			}
			os.MkdirAll(filepath.Dir(t.Path), 0755)
			tmp := t.Path + ".part"
			f, err := os.Create(tmp)
			if err != nil {
				return err
			}
			h := sha1.New()
			_, err = io.Copy(io.MultiWriter(f, h), resp.Body)
			f.Close()
			if err != nil {
				os.Remove(tmp)
				return err
			}
			if t.SHA1 != "" && hex.EncodeToString(h.Sum(nil)) != t.SHA1 {
				os.Remove(tmp)
				return fmt.Errorf("fichier corrompu : %s", filepath.Base(t.Path))
			}
			mode := os.FileMode(0644)
			if t.Exec {
				mode = 0755
			}
			os.Chmod(tmp, mode)
			os.Remove(t.Path)
			return os.Rename(tmp, t.Path)
		}()
		if last == nil {
			return nil
		}
	}
	return last
}

// downloadAll télécharge en parallèle ce qui manque, en signalant la progression.
func downloadAll(label string, tasks []dlTask, deep bool, progress func(string, float64)) error {
	var todo []dlTask
	seen := map[string]bool{}
	for _, t := range tasks {
		if seen[t.Path] {
			continue
		}
		seen[t.Path] = true
		if t.needs(deep) {
			todo = append(todo, t)
		}
	}
	if len(todo) == 0 {
		return nil
	}
	var done int64
	var firstErr error
	var mu sync.Mutex
	ch := make(chan dlTask)
	var wg sync.WaitGroup
	for w := 0; w < 12; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for t := range ch {
				if err := downloadOne(t); err != nil {
					mu.Lock()
					if firstErr == nil {
						firstErr = err
					}
					mu.Unlock()
				}
				n := atomic.AddInt64(&done, 1)
				progress(fmt.Sprintf("%s (%d/%d)", label, n, len(todo)), float64(n)/float64(len(todo)))
			}
		}()
	}
	for _, t := range todo {
		ch <- t
	}
	close(ch)
	wg.Wait()
	return firstErr
}
