// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"checkinDocBegin","params":{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":{"$expression":"ext"}}]}}},{"method":"createDoc","params":{"parentId":1,"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkoutDoc","params":{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}},{"method":"checkinDocEnd","params":{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"processOcr","params":{"ocrInfo":{"recognizeFile":{"objId":{"$expression":"obj_id"},"outputFormat":0,"pageNo":{"$expression":"-1"}}}}},{"method":"deleteSord","params":{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}}]
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
    result, err := client.Call("checkinDocBegin", json.RawMessage(`{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":{"$expression":"ext"}}]}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("createDoc", json.RawMessage(`{"parentId":1,"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutDoc", json.RawMessage(`{"objId":{"$expression":"obj_id"},"editInfoZ":{"bset":"320","sordZ":{"bset":"0"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkinDocEnd", json.RawMessage(`{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("processOcr", json.RawMessage(`{"ocrInfo":{"recognizeFile":{"objId":{"$expression":"obj_id"},"outputFormat":0,"pageNo":{"$expression":"-1"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("deleteSord", json.RawMessage(`{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
