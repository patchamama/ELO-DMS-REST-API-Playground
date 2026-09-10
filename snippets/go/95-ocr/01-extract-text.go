// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"processOcr","params":{"ocrInfo":{"recognizeFile":{"imageData":{"data":{"$expression":"base64.b64encode(data).decode('ascii')"},"contentType":{"$expression":"ext"}},"outputFormat":0,"pageNo":{"$expression":"-1"}}}}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    client := elo.Connect() // ELOPG_* overrides the local teaching defaults.
    result, err := client.Call("processOcr", json.RawMessage(`{"ocrInfo":{"recognizeFile":{"imageData":{"data":{"$expression":"base64.b64encode(data).decode('ascii')"},"contentType":{"$expression":"ext"}},"outputFormat":0,"pageNo":{"$expression":"-1"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
