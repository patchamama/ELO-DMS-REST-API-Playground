// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"findInfo":{"findByIndex":{"iDateIso":{"$expression":"f'{since}...{until}'"}},"findByType":{"typeDocuments":true}},"max":500,"sordZ":{"bset":{"$expression":"LEAN"}}}},{"method":"findNextSords","params":{"searchId":{"$expression":"res['searchId']"},"idx":{"$expression":"len(rows)"},"max":500,"sordZ":{"bset":{"$expression":"LEAN"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res['searchId']"}}},{"method":"checkoutDoc","params":{"objId":{"$expression":"str(doc['id'])"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}}]
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
    result, err := client.Call("findFirstSords", json.RawMessage(`{"findInfo":{"findByIndex":{"iDateIso":{"$expression":"f'{since}...{until}'"}},"findByType":{"typeDocuments":true}},"max":500,"sordZ":{"bset":{"$expression":"LEAN"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findNextSords", json.RawMessage(`{"searchId":{"$expression":"res['searchId']"},"idx":{"$expression":"len(rows)"},"max":500,"sordZ":{"bset":{"$expression":"LEAN"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findClose", json.RawMessage(`{"searchId":{"$expression":"res['searchId']"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutDoc", json.RawMessage(`{"objId":{"$expression":"str(doc['id'])"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
