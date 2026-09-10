// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"findFirstDocMasks","params":{}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    client := elo.Connect() // ELOPG_* overrides the local teaching defaults.
    result, err := client.Call("findFirstDocMasks", json.RawMessage(`{}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
