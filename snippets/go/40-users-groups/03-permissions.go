// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"checkoutUsers","params":{"ids":[0,1],"checkoutUsersZ":{"bset":"513"}}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    client := elo.Connect() // ELOPG_* overrides the local teaching defaults.
    result, err := client.Call("checkoutUsers", json.RawMessage(`{"ids":[0,1],"checkoutUsersZ":{"bset":"513"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
