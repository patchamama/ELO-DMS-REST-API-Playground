// Package elo is the standard-library teaching client used by generated Go examples.
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

const defaultBaseURL = "http://localhost:9090/ix-Repository1"

type Client struct {
	BaseURL, User, Password string
	HTTP                    *http.Client
}

func Connect() *Client {
	return New(env("ELOPG_ELO_BASE_URL", defaultBaseURL), env("ELOPG_ELO_USER", "Administrator"), os.Getenv("ELOPG_ELO_PASSWORD"))
}
func New(baseURL, user, password string) *Client {
	return &Client{BaseURL: baseURL, User: user, Password: password, HTTP: http.DefaultClient}
}
func env(name, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
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
	req, err := http.NewRequest(http.MethodPost, strings.TrimRight(c.BaseURL, "/")+"/rest/IXServicePortIF/"+method, bytes.NewReader(payload))
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
		Result json.RawMessage `json:"result"`
	}
	if err := json.Unmarshal(raw, &envelope); err != nil {
		return nil, err
	}
	if envelope.Result == nil {
		return json.RawMessage(`{}`), nil
	}
	return envelope.Result, nil
}
