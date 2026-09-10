// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"linkSords","params":{"fromId":{"$expression":"a"},"toIds":[{"$expression":"b"}],"linkZ":{"bset":"1"}}},{"method":"unlinkSords","params":{"fromId":{"$expression":"a"},"toIds":[{"$expression":"b"}],"linkZ":{"bset":"1"}}},{"method":"createSord","params":{"parentId":{"$expression":"str(PARENT)"},"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"checkoutSord","params":{"objId":{"$expression":"a"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"deleteSord","params":{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"oid"},"deleteOptions":{"deleteFinally":false}}},{"method":"deleteSord","params":{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"oid"},"deleteOptions":{"deleteFinally":true}}}]
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
    result, err := client.Call("linkSords", json.RawMessage(`{"fromId":{"$expression":"a"},"toIds":[{"$expression":"b"}],"linkZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("unlinkSords", json.RawMessage(`{"fromId":{"$expression":"a"},"toIds":[{"$expression":"b"}],"linkZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("createSord", json.RawMessage(`{"parentId":{"$expression":"str(PARENT)"},"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkinSord", json.RawMessage(`{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutSord", json.RawMessage(`{"objId":{"$expression":"a"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("deleteSord", json.RawMessage(`{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"oid"},"deleteOptions":{"deleteFinally":false}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("deleteSord", json.RawMessage(`{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"oid"},"deleteOptions":{"deleteFinally":true}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
