"""Generate standalone offline ELO examples for Go, PHP, Java and Rhino.

The generated programs deliberately use only each runtime's standard library.  They
read the canonical merged fixture written by the playground runner through
ELOPG_MOCK_DATA, so examples remain reproducible without an ELO installation.
Rhino is documented as an IndexServer script artifact and is never browser-run.
"""
from __future__ import annotations

from pathlib import Path

EXTENSIONS = {"python": "py", "node": "mjs", "browser": "js", "go": "go", "php": "php", "java": "java", "rhino": "js"}
LANGUAGES = tuple(EXTENSIONS)


def method_for(topic: dict) -> str:
    refs = topic.get("elo_api") or []
    return str(refs[0].get("method", "login")) if refs else "login"


def generate(topic: dict, language: str) -> str:
    method = method_for(topic)
    if language == "go":
        return f'''// Offline mock example. The runner supplies ELOPG_MOCK_DATA from canonical fixtures.
package main

import ("encoding/json"; "fmt"; "os")

func main() {{
  const method = "{method}" // IXServicePortIF/{method}
  raw, err := os.ReadFile(os.Getenv("ELOPG_MOCK_DATA"))
  if err != nil {{ panic("ELOPG_MOCK_DATA is required for offline mock runs: " + err.Error()) }}
  var fixture map[string]json.RawMessage
  if err := json.Unmarshal(raw, &fixture); err != nil {{ panic(err) }}
  result, ok := fixture[method]
  if !ok {{ result = json.RawMessage(`{{}}`) }}
  fmt.Println(string(result))
}}
'''
    if language == "php":
        return f'''<?php
// Offline mock example. The runner supplies ELOPG_MOCK_DATA from canonical fixtures.
$method = '{method}'; // IXServicePortIF/{method}
$path = getenv('ELOPG_MOCK_DATA');
if (!$path || !is_file($path)) {{ throw new RuntimeException('ELOPG_MOCK_DATA is required for offline mock runs'); }}
$fixture = json_decode(file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
echo json_encode($fixture[$method] ?? new stdClass(), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;
'''
    if language == "java":
        return f'''// Offline mock example. The runner supplies ELOPG_MOCK_DATA from canonical fixtures.
// Uses only the JDK; add the ELO IX client JAR for typed live calls in a real application.
import java.nio.file.Files;
import java.nio.file.Path;

public final class Main {{
  public static void main(String[] args) throws Exception {{
    String method = "{method}"; // IXServicePortIF/{method}
    String mockPath = System.getenv("ELOPG_MOCK_DATA");
    if (mockPath == null || mockPath.isBlank()) throw new IllegalStateException("ELOPG_MOCK_DATA is required for offline mock runs");
    // Print canonical fixture JSON. A production client should deserialize the method result.
    System.out.println(Files.readString(Path.of(mockPath)));
  }}
}}
'''
    if language == "rhino":
        return f'''/**
 * IndexServer Rhino script example, NOT Web Client injection.
 * Register this script through ELO administration/deployment, review it, then invoke
 * it using IXServicePortIF.executeScript. Incoming args are data, never code.
 */
function RF_playground_readMetadata(ec, args) {{
  var objId = String((args && args.objId) || "");
  if (!objId) throw "objId is required";
  var sord = ixConnect.ix().checkoutSord(objId, SordC.mbAllIndex, LockC.NO);
  return {{ id: String(sord.id), name: String(sord.name), mask: String(sord.maskName || "") }};
}}
'''
    return ""
