// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"findInfo":{"findByIndex":{"name":"Administration*"}},"max":10,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res.get('searchId')"}}},{"method":"checkoutSord","params":{"objId":2,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutSord","params":{"objId":{"$expression":"by_id['guid']"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}}]
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
    result, err := client.Call("findFirstSords", json.RawMessage(`{"findInfo":{"findByIndex":{"name":"Administration*"}},"max":10,"sordZ":{"bset":{"$expression":"ALL"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findClose", json.RawMessage(`{"searchId":{"$expression":"res.get('searchId')"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutSord", json.RawMessage(`{"objId":2,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutSord", json.RawMessage(`{"objId":{"$expression":"by_id['guid']"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
