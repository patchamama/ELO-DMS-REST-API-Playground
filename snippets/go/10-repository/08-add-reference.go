// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"createSord","params":{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"refSord","params":{"objId":{"$expression":"obj_id"},"oldParentId":"1","newParentId":{"$expression":"new_parent"}}},{"method":"findFirstSords","params":{"findInfo":{"findChildren":{"parentId":{"$expression":"new_parent"},"mainParent":false,"endLevel":1}},"max":20,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"deleteSord","params":{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":false}}},{"method":"deleteSord","params":{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":true}}}]
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
    result, err := client.Call("createSord", json.RawMessage(`{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkinSord", json.RawMessage(`{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("refSord", json.RawMessage(`{"objId":{"$expression":"obj_id"},"oldParentId":"1","newParentId":{"$expression":"new_parent"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findFirstSords", json.RawMessage(`{"findInfo":{"findChildren":{"parentId":{"$expression":"new_parent"},"mainParent":false,"endLevel":1}},"max":20,"sordZ":{"bset":{"$expression":"ALL"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("deleteSord", json.RawMessage(`{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":false}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("deleteSord", json.RawMessage(`{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":true}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
