// Package elo provides a small standard-library IX REST client for Go examples.
package elo

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

type Client struct {
	BaseURL, User, Password string
	HTTP                    *http.Client
}

func (c *Client) Call(method string, body interface{}, out interface{}) error {
	if os.Getenv("ELOPG_MOCK") == "1" {
		raw, e := os.ReadFile(os.Getenv("ELOPG_MOCK_DATA"))
		if e != nil {
			return e
		}
		var m map[string]json.RawMessage
		if e = json.Unmarshal(raw, &m); e != nil {
			return e
		}
		return json.Unmarshal(m[method], out)
	}
	raw, e := json.Marshal(body)
	if e != nil {
		return e
	}
	req, e := http.NewRequest(http.MethodPost, strings.TrimRight(c.BaseURL, "/")+"/rest/IXServicePortIF/"+method, bytes.NewReader(raw))
	if e != nil {
		return e
	}
	req.Header.Set("Content-Type", "application/json")
	req.SetBasicAuth(c.User, c.Password)
	h := c.HTTP
	if h == nil {
		h = http.DefaultClient
	}
	resp, e := h.Do(req)
	if e != nil {
		return e
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("IX HTTP %s", resp.Status)
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

var _ = io.EOF
