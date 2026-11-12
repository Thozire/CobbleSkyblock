package main

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Account est ce qu'on garde entre deux lancements (le refresh token est
// chiffré sur le disque avec la protection de données de Windows).
type Account struct {
	Name         string    `json:"name"`
	UUID         string    `json:"uuid"`
	XUID         string    `json:"xuid"`
	RefreshToken string    `json:"refresh_token"`
	MCToken      string    `json:"-"`
	MCTokenExp   time.Time `json:"-"`
}

var ErrNotApproved = errors.New("not_approved")
var ErrNoGame = errors.New("no_game")

const msAuthBase = "https://login.microsoftonline.com/consumers/oauth2/v2.0"
const msScope = "XboxLive.signin offline_access"

type pkce struct{ verifier, challenge, state string }

func newPKCE() pkce {
	b := make([]byte, 32)
	rand.Read(b)
	v := base64.RawURLEncoding.EncodeToString(b)
	h := sha256.Sum256([]byte(v))
	s := make([]byte, 16)
	rand.Read(s)
	return pkce{v, base64.RawURLEncoding.EncodeToString(h[:]), base64.RawURLEncoding.EncodeToString(s)}
}

func authorizeURL(p pkce, redirect string) string {
	q := url.Values{
		"client_id":             {MSClientID},
		"response_type":         {"code"},
		"redirect_uri":          {redirect},
		"scope":                 {msScope},
		"code_challenge":        {p.challenge},
		"code_challenge_method": {"S256"},
		"state":                 {p.state},
		"prompt":                {"select_account"},
	}
	return msAuthBase + "/authorize?" + q.Encode()
}

type msToken struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	Error        string `json:"error"`
	ErrorDesc    string `json:"error_description"`
}

func msTokenRequest(form url.Values) (*msToken, error) {
	form.Set("client_id", MSClientID)
	form.Set("scope", msScope)
	resp, err := httpClient.PostForm(msAuthBase+"/token", form)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var t msToken
	if err := json.NewDecoder(resp.Body).Decode(&t); err != nil {
		return nil, err
	}
	if t.Error != "" {
		return nil, fmt.Errorf("Microsoft : %s", t.Error)
	}
	return &t, nil
}

func postJSON(u string, body any, out any, bearer string) (int, error) {
	b, _ := json.Marshal(body)
	req, _ := http.NewRequest("POST", u, strings.NewReader(string(b)))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	if bearer != "" {
		req.Header.Set("Authorization", "Bearer "+bearer)
	}
	resp, err := httpClient.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	data, _ := io.ReadAll(resp.Body)
	if out != nil && len(data) > 0 {
		json.Unmarshal(data, out)
	}
	return resp.StatusCode, nil
}

func getJSON(u string, out any, bearer string) (int, error) {
	req, _ := http.NewRequest("GET", u, nil)
	req.Header.Set("Accept", "application/json")
	if bearer != "" {
		req.Header.Set("Authorization", "Bearer "+bearer)
	}
	resp, err := httpClient.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode == 200 && out != nil {
		return 200, json.NewDecoder(resp.Body).Decode(out)
	}
	return resp.StatusCode, nil
}

// minecraftLogin enchaîne Microsoft -> Xbox Live -> XSTS -> Minecraft, puis
// vérifie que le compte possède bien le jeu.
func minecraftLogin(msAccess string) (*Account, error) {
	var xbl struct {
		Token         string
		DisplayClaims struct {
			Xui []struct {
				Uhs string `json:"uhs"`
			} `json:"xui"`
		}
	}
	code, err := postJSON("https://user.auth.xboxlive.com/user/authenticate", map[string]any{
		"Properties":   map[string]any{"AuthMethod": "RPS", "SiteName": "user.auth.xboxlive.com", "RpsTicket": "d=" + msAccess},
		"RelyingParty": "http://auth.xboxlive.com", "TokenType": "JWT",
	}, &xbl, "")
	if err != nil {
		return nil, err
	}
	if code != 200 || xbl.Token == "" {
		return nil, fmt.Errorf("connexion Xbox Live refusée (%d)", code)
	}
	var xsts struct {
		Token         string
		XErr          int64
		DisplayClaims struct {
			Xui []struct {
				Uhs string `json:"uhs"`
				Xid string `json:"xid"`
			} `json:"xui"`
		}
	}
	code, err = postJSON("https://xsts.auth.xboxlive.com/xsts/authorize", map[string]any{
		"Properties":   map[string]any{"SandboxId": "RETAIL", "UserTokens": []string{xbl.Token}},
		"RelyingParty": "rp://api.minecraftservices.com/", "TokenType": "JWT",
	}, &xsts, "")
	if err != nil {
		return nil, err
	}
	if code == 401 {
		switch xsts.XErr {
		case 2148916233:
			return nil, errors.New("ce compte Microsoft n'a pas de profil Xbox : connecte-toi une fois sur minecraft.net pour le créer")
		case 2148916238:
			return nil, errors.New("compte mineur : il doit être ajouté à une famille Microsoft par un adulte")
		default:
			return nil, fmt.Errorf("Xbox Live a refusé la connexion (%d)", xsts.XErr)
		}
	}
	if code != 200 || len(xsts.DisplayClaims.Xui) == 0 {
		return nil, fmt.Errorf("autorisation Xbox refusée (%d)", code)
	}
	uhs := xsts.DisplayClaims.Xui[0].Uhs
	var mc struct {
		AccessToken string `json:"access_token"`
		ExpiresIn   int    `json:"expires_in"`
	}
	code, err = postJSON("https://api.minecraftservices.com/authentication/login_with_xbox",
		map[string]string{"identityToken": "XBL3.0 x=" + uhs + ";" + xsts.Token}, &mc, "")
	if err != nil {
		return nil, err
	}
	if code == 403 {
		return nil, ErrNotApproved
	}
	if code != 200 || mc.AccessToken == "" {
		return nil, fmt.Errorf("connexion Minecraft refusée (%d)", code)
	}
	var ent struct {
		Items []struct{ Name string } `json:"items"`
	}
	if _, err := getJSON("https://api.minecraftservices.com/entitlements/mcstore", &ent, mc.AccessToken); err != nil {
		return nil, err
	}
	var prof struct{ ID, Name string }
	code, err = getJSON("https://api.minecraftservices.com/minecraft/profile", &prof, mc.AccessToken)
	if err != nil {
		return nil, err
	}
	if len(ent.Items) == 0 || code == 404 || prof.ID == "" {
		return nil, ErrNoGame
	}
	xid := ""
	if len(xsts.DisplayClaims.Xui) > 0 {
		xid = xsts.DisplayClaims.Xui[0].Xid
	}
	return &Account{Name: prof.Name, UUID: prof.ID, XUID: xid, MCToken: mc.AccessToken,
		MCTokenExp: time.Now().Add(time.Duration(mc.ExpiresIn-300) * time.Second)}, nil
}

func loginWithCode(code, redirect string, p pkce) (*Account, error) {
	t, err := msTokenRequest(url.Values{"grant_type": {"authorization_code"}, "code": {code},
		"redirect_uri": {redirect}, "code_verifier": {p.verifier}})
	if err != nil {
		return nil, err
	}
	acc, err := minecraftLogin(t.AccessToken)
	if err != nil {
		return nil, err
	}
	acc.RefreshToken = t.RefreshToken
	return acc, saveAccount(acc)
}

// ensureFresh renouvelle le jeton Minecraft si besoin, avec le refresh token.
func ensureFresh(acc *Account) (*Account, error) {
	if acc.MCToken != "" && time.Now().Before(acc.MCTokenExp) {
		return acc, nil
	}
	t, err := msTokenRequest(url.Values{"grant_type": {"refresh_token"}, "refresh_token": {acc.RefreshToken}})
	if err != nil {
		return nil, fmt.Errorf("session expirée, reconnecte-toi (%v)", err)
	}
	n, err := minecraftLogin(t.AccessToken)
	if err != nil {
		return nil, err
	}
	n.RefreshToken = t.RefreshToken
	if n.RefreshToken == "" {
		n.RefreshToken = acc.RefreshToken
	}
	return n, saveAccount(n)
}

func accountPath() string { return filepath.Join(dataDir(), "account.dat") }

func saveAccount(a *Account) error {
	b, _ := json.Marshal(a)
	enc, err := protect(b)
	if err != nil {
		return err
	}
	return os.WriteFile(accountPath(), enc, 0600)
}

func loadAccount() *Account {
	b, err := os.ReadFile(accountPath())
	if err != nil {
		return nil
	}
	dec, err := unprotect(b)
	if err != nil {
		return nil
	}
	var a Account
	if json.Unmarshal(dec, &a) != nil || a.RefreshToken == "" {
		return nil
	}
	return &a
}

func logout() { os.Remove(accountPath()) }
