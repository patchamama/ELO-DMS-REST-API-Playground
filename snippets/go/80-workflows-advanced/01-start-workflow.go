// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: [{"method":"createSord","params":{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}},{"method":"checkinSord","params":{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}},{"method":"startWorkFlow","params":{"templFlowId":{"$expression":"tmpl['id']"},"flowName":"playground test workflow","objId":{"$expression":"obj_id"}}},{"method":"checkoutWorkFlow","params":{"flowId":{"$expression":"flow_id"},"typeZ":{"bset":"0"},"lockZ":{"bset":"0"},"workFlowDiagramZ":{"bset":"1073741823"}}},{"method":"deleteSord","params":{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}},{"method":"findFirstWorkflows","params":{"findInfo":{"type":{"bset":"2"},"inclHidden":true},"max":5,"wfDiagramZ":{"bset":"0"}}}]
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
    result, err := client.Call("createSord", json.RawMessage(`{"parentId":"1","maskId":0,"editInfoZ":{"bset":"1","sordZ":{"bset":{"$expression":"ALL"}}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkinSord", json.RawMessage(`{"sord":{"$expression":"tpl"},"sordZ":{"bset":{"$expression":"ALL"}},"unlockZ":{"bset":"1"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("startWorkFlow", json.RawMessage(`{"templFlowId":{"$expression":"tmpl['id']"},"flowName":"playground test workflow","objId":{"$expression":"obj_id"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("checkoutWorkFlow", json.RawMessage(`{"flowId":{"$expression":"flow_id"},"typeZ":{"bset":"0"},"lockZ":{"bset":"0"},"workFlowDiagramZ":{"bset":"1073741823"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("deleteSord", json.RawMessage(`{"objId":{"$expression":"obj_id"},"parentId":"1","deleteOptions":{"deleteFinally":{"$expression":"step"}}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
    result, err := client.Call("findFirstWorkflows", json.RawMessage(`{"findInfo":{"type":{"bset":"2"},"inclHidden":true},"max":5,"wfDiagramZ":{"bset":"0"}}`))
    if err != nil { panic(err) }
    fmt.Println(string(result))
}
