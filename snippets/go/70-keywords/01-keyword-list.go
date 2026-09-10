// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"checkoutKeywordList","params":{"kwid":"ELOSTDSWL","max":500,"keywordZ":{"bset":"7"}}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    client := elo.Connect() // ELOPG_* overrides the local teaching defaults.
    result, err := client.Call("checkoutKeywordList", json.RawMessage(`{"kwid":"ELOSTDSWL","max":500,"keywordZ":{"bset":"7"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
