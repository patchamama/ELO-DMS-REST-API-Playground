// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"checkoutUsers","params":{"ids":{"$expression":"[u['id'] for u in users]"},"checkoutUsersZ":{"bset":"513"}}},{"method":"findFirstSords","params":{"findInfo":{"findChildren":{"parentId":{"$expression":"str(parent_id)"},"mainParent":true,"endLevel":1}},"max":1000,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res['searchId']"}}},{"method":"checkoutSord","params":{"objId":{"$expression":"str(folder_id)"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}}]
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
    result, err := client.Call("checkoutUsers", json.RawMessage(`{"ids":{"$expression":"[u['id'] for u in users]"},"checkoutUsersZ":{"bset":"513"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findFirstSords", json.RawMessage(`{"findInfo":{"findChildren":{"parentId":{"$expression":"str(parent_id)"},"mainParent":true,"endLevel":1}},"max":1000,"sordZ":{"bset":{"$expression":"ALL"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findClose", json.RawMessage(`{"searchId":{"$expression":"res['searchId']"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutSord", json.RawMessage(`{"objId":{"$expression":"str(folder_id)"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
