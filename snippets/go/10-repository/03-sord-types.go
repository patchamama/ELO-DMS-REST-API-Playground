// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"checkoutSordTypes","params":{"id":{"$expression":"-1"},"sordTypeZ":{"bset":"31"}}}]
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
    result, err := client.Call("checkoutSordTypes", json.RawMessage(`{"id":{"$expression":"-1"},"sordTypeZ":{"bset":"31"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
