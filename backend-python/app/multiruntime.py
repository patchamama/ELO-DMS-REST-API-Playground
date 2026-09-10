"""Generate shared-client examples for every supported runtime.

Go, PHP and Java snippets all follow the teaching-client convention: connect from
ELOPG_* configuration, call one IX method, and print its result payload. Mock mode
is implemented by each shared client over the runner-provided canonical fixture.
Rhino output is a reviewed IndexServer script contract, never Web Client code.
"""
from __future__ import annotations
import ast
import json
import re

EXTENSIONS = {"python": "py", "node": "mjs", "browser": "js", "go": "go", "php": "php", "java": "java", "rhino": "js"}
LANGUAGES = tuple(EXTENSIONS)


def method_for(topic: dict) -> str:
    refs = topic.get("elo_api") or []
    return str(refs[0].get("method", "login")) if refs else "login"


def _function_name(topic: dict) -> str:
    return "RF_playground_" + re.sub(r"[^A-Za-z0-9_]", "_", str(topic.get("id", "operation")))


def _expression(value: ast.AST) -> object:
    """A stable cross-runtime representation of Python snippet call arguments."""
    if isinstance(value, ast.Constant):
        return value.value
    if isinstance(value, ast.Dict):
        return {str(_expression(k)): _expression(v) for k, v in zip(value.keys, value.values) if k is not None}
    if isinstance(value, (ast.List, ast.Tuple)):
        return [_expression(v) for v in value.elts]
    # Variables (sord, ids, selectors) are deliberately represented rather
    # than guessed. All generated runtimes receive the same semantic marker.
    return {"$expression": ast.unparse(value)}


def operation_plan(topic: dict) -> list[dict[str, object]]:
    source = str((topic.get("snippets") or {}).get("python") or "")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [{"method": method_for(topic), "params": {}}]
    plan: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "call":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
            continue
        plan.append({"method": node.args[0].value, "params": _expression(node.args[1]) if len(node.args) > 1 else {}})
    return plan or [{"method": method_for(topic), "params": {}}]


def _rhino_body(method: str) -> str:
    if method in {"createSord", "checkinSord"}:
        return '''  var parentId = String(args.parentId || "");
  var name = String(args.name || "");
  if (!parentId || !name) throw "parentId and name are required";
  // Deployment policy must validate the parent against an approved scratch root.
  var sord = ixConnect.ix().createSord(parentId, "", EditInfoC.mbSord).sord;
  sord.name = name;
  sord = ixConnect.ix().checkinSord(sord, SordC.mbAll, LockC.NO);
  return { id: String(sord.id), name: String(sord.name) };'''
    if method in {"deleteSord", "deleteSordPath"}:
        return '''  var objId = String(args.objId || "");
  if (!objId || args.confirm !== true) throw "objId and confirm=true are required";
  // Only a dedicated test-root policy may permit destructive operations.
  ixConnect.ix().deleteSord(null, objId, LockC.NO, null);
  return { deletedId: objId };'''
    if method.startswith("find"):
        return '''  var query = String(args.query || "");
  if (!query) throw "query is required";
  var findInfo = new FindInfo();
  findInfo.findByIndex = new FindByIndex();
  findInfo.findByIndex.name = query;
  var page = ixConnect.ix().findFirstSords(findInfo, 20, SordC.mbLean);
  try { return { count: page.sords.length, ids: page.sords.map(function (s) { return String(s.id); }) }; }
  finally { ixConnect.ix().findClose(page.searchId); }'''
    if "Doc" in method or method in {"processOcr"}:
        return '''  var objId = String(args.objId || "");
  if (!objId) throw "objId is required";
  // Document byte transfer and OCR must be configured server-side, not received as code.
  var sord = ixConnect.ix().checkoutSord(objId, SordC.mbAllIndex, LockC.NO);
  return { id: String(sord.id), name: String(sord.name), mask: String(sord.maskName || "") };'''
    return '''  var objId = String(args.objId || "");
  if (!objId) throw "objId is required";
  var sord = ixConnect.ix().checkoutSord(objId, SordC.mbAllIndex, LockC.NO);
  return { id: String(sord.id), name: String(sord.name), mask: String(sord.maskName || "") };'''


def generate(topic: dict, language: str) -> str:
    method = method_for(topic)
    plan = operation_plan(topic)
    plan_json = json.dumps(plan, ensure_ascii=False, separators=(",", ":"))
    if language == "go":
        needs_json = any(step["method"] != "login" for step in plan)
        calls = "\n".join(
            ("    result, err := client.Login()\n" if step["method"] == "login" else f'    result, err := client.Call("{step["method"]}", json.RawMessage(`{json.dumps(step["params"], ensure_ascii=False, separators=(",", ":"))}`))\n') +
            "    if err != nil { panic(err) }\n    fmt.Println(string(result))"
            for step in plan
        )
        json_import = '    "encoding/json"\n' if needs_json else ""
        return f'''// Uses shared/go/elo.go. The runner copies it and creates a temporary module.
// ELOPG_PLAN: {plan_json}
package main

import (
{json_import}    "fmt"
    "example.com/elopg/elo"
)

func main() {{
    ELOBaseURL := elo.Env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") // ELOPG_DEFAULT:base_url
    ELOUser := elo.Env("ELOPG_ELO_USER", "Administrator") // ELOPG_DEFAULT:user
    ELOPass := elo.Env("ELOPG_ELO_PASSWORD", "elo") // ELOPG_DEFAULT:password
    client := elo.New(ELOBaseURL, ELOUser, ELOPass)
{calls}
}}
'''
    if language == "php":
        calls = "\n".join(
            f"$result = $elo->call('{step['method']}', json_decode('{json.dumps(step['params'], ensure_ascii=False, separators=(',', ':')).replace(chr(39), chr(92)+chr(39))}', true, 512, JSON_THROW_ON_ERROR));\necho json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), PHP_EOL;"
            for step in plan
        )
        return f'''<?php
// The runner places the shared teaching client beside this example.
// ELOPG_PLAN: {plan_json}
require_once __DIR__ . '/EloClient.php';

$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url
$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user
$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password
$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);
{calls}
'''
    if language == "java":
        calls = "\n".join(
            f'    System.out.println(elo.call("{step["method"]}", "{json.dumps(step["params"], ensure_ascii=False, separators=(",", ":")).replace("\\", "\\\\").replace(chr(34), "\\\"")}"));'
            for step in plan
        )
        return f'''// The runner compiles this file with shared/java/EloClient.java.
// ELOPG_PLAN: {plan_json}
public final class Main {{
  public static void main(String[] args) throws Exception {{
    String eloBaseUrl = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url
    String eloUser = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user
    String eloPass = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password
    var elo = EloClient.connect(eloBaseUrl, eloUser, eloPass);
{calls}
  }}
}}
'''
    if language == "rhino":
        name = _function_name(topic)
        return f'''/**
 * Reviewed IndexServer Rhino function for IXServicePortIF.{method}.
 * Contract: args is structured data; script name, target hosts and permitted roots
 * are deployment configuration. Never inject this source into ELO Web Client.
 */
var ELO_BASE_URL = java.lang.System.getenv("ELOPG_ELO_BASE_URL") || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url
var ELO_USER = java.lang.System.getenv("ELOPG_ELO_USER") || "Administrator"; // ELOPG_DEFAULT:user
var ELO_PASS = java.lang.System.getenv("ELOPG_ELO_PASSWORD") || "elo"; // ELOPG_DEFAULT:password

function {name}(ec, args) {{
  args = args || {{}};
{_rhino_body(method)}
}}
'''
    return ""
