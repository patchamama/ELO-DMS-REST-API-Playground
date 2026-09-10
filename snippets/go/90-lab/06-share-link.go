// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"checkinDocBegin","params":{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":"txt"}]}}},{"method":"createDoc","params":{"parentId":1,"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"insertPublicDownload","params":{"opts":{"objId":{"$expression":"obj_id"},"remaining":5,"fileNameFromSordName":true}}},{"method":"getPublicDownloads","params":{"opts":{"objId":{"$expression":"obj_id"}}}},{"method":"terminatePublicDownloadUrls","params":{"opts":{"objId":{"$expression":"obj_id"}}}},{"method":"checkinDocEnd","params":{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"getPublicDownloads","params":{"opts":{"objId":{"$expression":"obj_id"}}}},{"method":"deleteSord","params":{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    client := elo.Connect() // ELOPG_* overrides the local teaching defaults.
    result, err := client.Call("checkinDocBegin", json.RawMessage(`{"sord":{"$expression":"sord"},"document":{"docs":[{"ext":"txt"}]}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("createDoc", json.RawMessage(`{"parentId":1,"maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("insertPublicDownload", json.RawMessage(`{"opts":{"objId":{"$expression":"obj_id"},"remaining":5,"fileNameFromSordName":true}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("getPublicDownloads", json.RawMessage(`{"opts":{"objId":{"$expression":"obj_id"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("terminatePublicDownloadUrls", json.RawMessage(`{"opts":{"objId":{"$expression":"obj_id"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkinDocEnd", json.RawMessage(`{"sord":{"$expression":"sord"},"document":{"$expression":"doc"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("getPublicDownloads", json.RawMessage(`{"opts":{"objId":{"$expression":"obj_id"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("deleteSord", json.RawMessage(`{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
