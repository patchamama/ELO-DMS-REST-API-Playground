// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"processOcr","params":{"ocrInfo":{"recognizeFile":{"imageData":{"data":{"$expression":"base64.b64encode(data).decode('ascii')"},"contentType":{"$expression":"ext"}},"outputFormat":0,"pageNo":{"$expression":"-1"}}}}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    ELO_BASE_URL := elo.Env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") // ELOPG_DEFAULT:base_url
    ELO_USER := elo.Env("ELOPG_ELO_USER", "Administrator") // ELOPG_DEFAULT:user
    ELO_PASS := elo.Env("ELOPG_ELO_PASSWORD", "elo") // ELOPG_DEFAULT:password

    client := elo.New(ELO_BASE_URL, ELO_USER, ELO_PASS)
    result, err := client.Call("processOcr", json.RawMessage(`{"ocrInfo":{"recognizeFile":{"imageData":{"data":{"$expression":"base64.b64encode(data).decode('ascii')"},"contentType":{"$expression":"ext"}},"outputFormat":0,"pageNo":{"$expression":"-1"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
