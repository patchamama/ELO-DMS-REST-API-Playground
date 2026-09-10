// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"findFirstWorkflows","params":{"findInfo":{"type":{"bset":"2"},"inclHidden":true},"max":100,"wfDiagramZ":{"bset":"1073741823"}}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    client := elo.Connect() // ELOPG_* overrides the local teaching defaults.
    result, err := client.Call("findFirstWorkflows", json.RawMessage(`{"findInfo":{"type":{"bset":"2"},"inclHidden":true},"max":100,"wfDiagramZ":{"bset":"1073741823"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
