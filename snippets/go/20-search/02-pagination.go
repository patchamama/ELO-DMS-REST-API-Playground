// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"findFirstSords","params":{"$expression":"body"}},{"method":"findClose","params":{"searchId":{"$expression":"search_id"}}},{"method":"findNextSords","params":{"searchId":{"$expression":"search_id"},"idx":{"$expression":"len(rows)"},"max":2,"sordZ":{"$expression":"body['sordZ']"}}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    client := elo.Connect() // ELOPG_* overrides the local teaching defaults.
    result, err := client.Call("findFirstSords", json.RawMessage(`{"$expression":"body"}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findClose", json.RawMessage(`{"searchId":{"$expression":"search_id"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findNextSords", json.RawMessage(`{"searchId":{"$expression":"search_id"},"idx":{"$expression":"len(rows)"},"max":2,"sordZ":{"$expression":"body['sordZ']"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
