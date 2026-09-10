// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"createSord","params":{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"refSord","params":{"objId":{"$expression":"obj_id"},"oldParentId":"1","newParentId":{"$expression":"new_parent"}}},{"method":"findFirstSords","params":{"findInfo":{"findChildren":{"parentId":{"$expression":"new_parent"},"mainParent":false,"endLevel":1}},"max":20,"sordZ":{"bset":{"$expression":"ALL"}}}},{"method":"deleteSord","params":{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":false}}},{"method":"deleteSord","params":{"objId":{"$expression":"oid"},"parentId":"1","deleteOptions":{"deleteFinally":true}}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    client := elo.Connect() // ELOPG_* overrides the local teaching defaults.
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
