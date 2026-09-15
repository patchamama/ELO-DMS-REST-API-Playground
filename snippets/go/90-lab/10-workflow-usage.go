// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"findFirstWorkflows","params":{"findInfo":{"type":{"bset":{"$expression":"wf_type"}}},"max":500,"wfDiagramZ":{"bset":{"$expression":"bset"}}}},{"method":"findNextWorkflows","params":{"searchId":{"$expression":"res['searchId']"},"idx":{"$expression":"len(rows)"},"max":500,"wfDiagramZ":{"bset":{"$expression":"bset"}}}},{"method":"findClose","params":{"searchId":{"$expression":"res['searchId']"}}}]
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
    result, err := client.Call("findFirstWorkflows", json.RawMessage(`{"findInfo":{"type":{"bset":{"$expression":"wf_type"}}},"max":500,"wfDiagramZ":{"bset":{"$expression":"bset"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findNextWorkflows", json.RawMessage(`{"searchId":{"$expression":"res['searchId']"},"idx":{"$expression":"len(rows)"},"max":500,"wfDiagramZ":{"bset":{"$expression":"bset"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findClose", json.RawMessage(`{"searchId":{"$expression":"res['searchId']"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
