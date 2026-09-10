// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"checkoutSord","params":{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"1","sordZ":{"bset":"449304431574384639"}}}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    ELOBaseURL := elo.Env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") // ELOPG_DEFAULT:base_url
    ELOUser := elo.Env("ELOPG_ELO_USER", "Administrator") // ELOPG_DEFAULT:user
    ELOPass := elo.Env("ELOPG_ELO_PASSWORD", "elo") // ELOPG_DEFAULT:password
    client := elo.New(ELOBaseURL, ELOUser, ELOPass)
    result, err := client.Call("checkoutSord", json.RawMessage(`{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"1","sordZ":{"bset":"449304431574384639"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
