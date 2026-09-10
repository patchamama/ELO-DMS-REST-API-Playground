// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"checkinMap","params":{"objId":{"$expression":"int(obj_id)"},"domainName":"objekte","data":[{"key":"grp_copy","value":{"$expression":"source_value"}}],"unlockZ":{"bset":"1"}}},{"method":"checkoutMap","params":{"objId":{"$expression":"int(obj_id)"},"id":{"$expression":"obj_id"},"domainName":"objekte","keyNames":["*"],"lockZ":{"bset":"0"}}},{"method":"createSord","params":{"parentId":{"$expression":"str(PARENT)"},"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"checkoutSord","params":{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"deleteSord","params":{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"obj_id"},"deleteOptions":{"deleteFinally":false}}},{"method":"deleteSord","params":{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"obj_id"},"deleteOptions":{"deleteFinally":true}}}]
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
    result, err := client.Call("checkinMap", json.RawMessage(`{"objId":{"$expression":"int(obj_id)"},"domainName":"objekte","data":[{"key":"grp_copy","value":{"$expression":"source_value"}}],"unlockZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutMap", json.RawMessage(`{"objId":{"$expression":"int(obj_id)"},"id":{"$expression":"obj_id"},"domainName":"objekte","keyNames":["*"],"lockZ":{"bset":"0"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("createSord", json.RawMessage(`{"parentId":{"$expression":"str(PARENT)"},"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkinSord", json.RawMessage(`{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutSord", json.RawMessage(`{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("deleteSord", json.RawMessage(`{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"obj_id"},"deleteOptions":{"deleteFinally":false}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("deleteSord", json.RawMessage(`{"parentId":{"$expression":"str(PARENT)"},"objId":{"$expression":"obj_id"},"deleteOptions":{"deleteFinally":true}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
