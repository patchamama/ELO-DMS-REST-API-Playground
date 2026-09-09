// Offline mock example. The runner supplies ELOPG_MOCK_DATA from canonical fixtures.
package main

import ("encoding/json"; "fmt"; "os")

func main() {
  const method = "checkoutSord" // IXServicePortIF/checkoutSord
  raw, err := os.ReadFile(os.Getenv("ELOPG_MOCK_DATA"))
  if err != nil { panic("ELOPG_MOCK_DATA is required for offline mock runs: " + err.Error()) }
  var fixture map[string]json.RawMessage
  if err := json.Unmarshal(raw, &fixture); err != nil { panic(err) }
  result, ok := fixture[method]
  if !ok { result = json.RawMessage(`{}`) }
  fmt.Println(string(result))
}
