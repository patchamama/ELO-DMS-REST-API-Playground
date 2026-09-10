// Package elo is the standard-library teaching client used by generated Go examples.
package elo

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

const defaultBaseURL = "http://localhost:9090/ix-Repository1"
const defaultRequestTimeout = 15 * time.Second

type Client struct {
	BaseURL, User, Password string
	HTTP                    *http.Client
}

func Connect() *Client {
	return New(Env("ELOPG_ELO_BASE_URL", defaultBaseURL), Env("ELOPG_ELO_USER", "Administrator"), Env("ELOPG_ELO_PASSWORD", "elo"))
}
func New(baseURL, user, password string) *Client {
	return &Client{BaseURL: baseURL, User: user, Password: password, HTTP: &http.Client{Timeout: defaultRequestTimeout}}
}
// Env reads a non-empty environment variable or returns its teaching default.
// Generated examples use it explicitly so the connection values stay visible.
func Env(name, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
}

// Login opens an IX session with the same request shape as elo_playground.
func (c *Client) Login() (json.RawMessage, error) {
	return c.Call("login", map[string]interface{}{
		"userName": c.User, "userPwd": c.Password, "clientComputer": "elo-api-playground", "runAsUser": "", "ci": map[string]interface{}{"language": "en", "country": "US", "timezone": "Europe/Berlin"},
	})
}

// Call returns the IX result payload, unwrapping the REST {"result": ...} envelope.
func (c *Client) Call(method string, body interface{}) (json.RawMessage, error) {
	if os.Getenv("ELOPG_MOCK") == "1" {
		raw, err := os.ReadFile(os.Getenv("ELOPG_MOCK_DATA"))
		if err != nil {
			return nil, err
		}
		var fixture map[string]json.RawMessage
		if err = json.Unmarshal(raw, &fixture); err != nil {
			return nil, err
		}
		if result, ok := fixture[method]; ok {
			return result, nil
		}
		return json.RawMessage(`{}`), nil
	}
	payload, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), defaultRequestTimeout)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, strings.TrimRight(c.BaseURL, "/")+"/rest/IXServicePortIF/"+method, bytes.NewReader(payload))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.SetBasicAuth(c.User, c.Password)
	response, err := c.HTTP.Do(req)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	raw, err := io.ReadAll(response.Body)
	if err != nil {
		return nil, err
	}
	if response.StatusCode >= http.StatusMultipleChoices {
		return nil, fmt.Errorf("IX HTTP %s: %s", response.Status, string(raw))
	}
	var envelope struct {
		Result    json.RawMessage `json:"result"`
		Exception json.RawMessage `json:"exception"`
	}
	if err := json.Unmarshal(raw, &envelope); err != nil {
		return nil, err
	}
	if envelope.Result == nil {
		if envelope.Exception != nil {
			return nil, fmt.Errorf("IX exception: %s", string(envelope.Exception))
		}
		return json.RawMessage(`{}`), nil
	}
	return envelope.Result, nil
}
