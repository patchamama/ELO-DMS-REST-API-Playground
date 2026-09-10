// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"checkinUsers","params":{"userInfos":[{"$expression":"ui"}],"checkinUsersZ":{"bset":"513"},"unlockZ":{"bset":"1"}}},{"method":"checkinUsers","params":{"userInfos":[{"id":{"$expression":"-1"},"name":{"$expression":"USER"},"type":1,"pwd":"PlaygroundDemoUser2026!"}],"checkinUsersZ":{"bset":"1"},"unlockZ":{"bset":"1"}}},{"method":"checkinUsers","params":{"userInfos":[{"id":{"$expression":"-1"},"name":{"$expression":"GROUP"},"type":0}],"checkinUsersZ":{"bset":"1"},"unlockZ":{"bset":"1"}}},{"method":"checkoutUsers","params":{"ids":[{"$expression":"uid"}],"checkoutUsersZ":{"bset":"513"}}},{"method":"checkoutUsers","params":{"ids":[{"$expression":"uid"}],"checkoutUsersZ":{"bset":"513"}}},{"method":"deleteUsers","params":{"ids":{"$expression":"ids"}}},{"method":"checkoutUsers","params":{"ids":[{"$expression":"name"}],"checkoutUsersZ":{"bset":"1"}}}]
package main

import (
    "encoding/json"
    "fmt"
    "example.com/elopg/elo"
)

func main() {
    client := elo.Connect() // ELOPG_* overrides the local teaching defaults.
    result, err := client.Call("checkinUsers", json.RawMessage(`{"userInfos":[{"$expression":"ui"}],"checkinUsersZ":{"bset":"513"},"unlockZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkinUsers", json.RawMessage(`{"userInfos":[{"id":{"$expression":"-1"},"name":{"$expression":"USER"},"type":1,"pwd":"PlaygroundDemoUser2026!"}],"checkinUsersZ":{"bset":"1"},"unlockZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkinUsers", json.RawMessage(`{"userInfos":[{"id":{"$expression":"-1"},"name":{"$expression":"GROUP"},"type":0}],"checkinUsersZ":{"bset":"1"},"unlockZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutUsers", json.RawMessage(`{"ids":[{"$expression":"uid"}],"checkoutUsersZ":{"bset":"513"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutUsers", json.RawMessage(`{"ids":[{"$expression":"uid"}],"checkoutUsersZ":{"bset":"513"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("deleteUsers", json.RawMessage(`{"ids":{"$expression":"ids"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutUsers", json.RawMessage(`{"ids":[{"$expression":"name"}],"checkoutUsersZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
