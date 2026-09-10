"""Read the ELO IX ``openapi.json`` and drive the "API reference" tab.

Live mode fetches ``{base_url}/rest/openapi.json`` from the server (no auth
needed) and caches it briefly. Mock / offline mode uses the trimmed, committed
``fixtures/openapi.sample.json``.

The spec has no per-operation prose (ELO leaves ``summary`` / ``description``
empty on operations), so the reference view is built from the request / response
*schemas*: for each operation we resolve its ``BRequest_*`` component and list
its top-level properties, drilling one level into nested ``$ref`` schemas, then
generate a minimal ``elo.call(...)`` skeleton. Schema *properties* do carry
descriptions (javadoc-style, with a copyright boilerplate we strip).
"""
from __future__ import annotations

import json
import re
import time
from functools import lru_cache
from typing import Any

import httpx

from .config import get_settings

_HTTP_METHODS = {"get", "post", "put", "delete", "patch"}
_SPEC_TTL = 600.0
_cache: dict[str, tuple[float, dict]] = {}

# request properties every snippet can ignore - the shared client fills them in
_SKIP_PROPS = {"ci"}

# copyright / org boilerplate that pads almost every ELO schema description
_DESC_NOISE = re.compile(
    r"<[^>]+>|Copyright:.*?(?=(\s|$))|Organisation:.*?(?=(\s|$))|ELO Digital Office GmbH|\(c\)\s*\d{4}",
    re.IGNORECASE | re.DOTALL,
)


@lru_cache
def _sample_spec() -> dict:
    path = get_settings().project_root / "fixtures" / "openapi.sample.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_spec(base_url: str | None, *, mock: bool) -> dict:
    if mock or not base_url:
        return _sample_spec()
    key = base_url.rstrip("/")
    hit = _cache.get(key)
    now = time.time()
    if hit and now - hit[0] < _SPEC_TTL:
        return hit[1]
    url = f"{key}/rest/openapi.json"
    try:
        resp = httpx.get(url, timeout=15.0, verify=False, follow_redirects=True)
        resp.raise_for_status()
        spec = resp.json()
    except (httpx.HTTPError, ValueError) as exc:  # noqa: BLE001 - degrade to the sample
        spec = {**_sample_spec(), "_fetch_error": f"{type(exc).__name__}: {exc}"}
    _cache[key] = (now, spec)
    return spec


# ---- iteration helpers ------------------------------------------------- #
def _iter_ops(spec: dict):
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        seg = [s for s in path.split("/") if s]
        service = seg[0] if seg else "?"
        method = seg[-1] if seg else path
        for http_method, op in item.items():
            if http_method in _HTTP_METHODS and isinstance(op, dict):
                yield service, method, http_method, path, op


def spec_info(spec: dict) -> dict:
    info = spec.get("info") or {}
    return {
        "title": info.get("title", "Indexserver"),
        "version": info.get("version", ""),
        "operations": sum(1 for _ in _iter_ops(spec)),
        "sample": "_note" in spec,
        "fetch_error": spec.get("_fetch_error", ""),
    }


def services(spec: dict) -> list[dict]:
    counts: dict[str, int] = {}
    for service, *_ in _iter_ops(spec):
        counts[service] = counts.get(service, 0) + 1
    return [{"service": s, "count": n} for s, n in sorted(counts.items())]


def operations(spec: dict, service: str | None = None) -> list[dict]:
    out: list[dict] = []
    for svc, method, http_method, path, op in _iter_ops(spec):
        if service and svc != service:
            continue
        out.append(
            {
                "operation_id": op.get("operationId") or f"{svc}_{method}",
                "service": svc,
                "method": method,
                "http_method": http_method.upper(),
                "path": path,
            }
        )
    out.sort(key=lambda o: o["method"].lower())
    return out


# ---- schema helpers --------------------------------------------------- #
def _resolve_ref(spec: dict, ref: str) -> dict:
    if not ref.startswith("#/"):
        return {}
    node: Any = spec
    for part in ref[2:].split("/"):
        if not isinstance(node, dict):
            return {}
        node = node.get(part, {})
    return node if isinstance(node, dict) else {}


def _ref_name(schema: dict) -> str:
    return schema.get("$ref", "").rsplit("/", 1)[-1] if "$ref" in schema else ""


def _type_of(schema: dict) -> str:
    if "$ref" in schema:
        return _ref_name(schema)
    t = schema.get("type")
    if t == "array":
        return f"{_type_of(schema.get('items') or {})}[]"
    if t == "integer":
        return schema.get("format") or "integer"
    return t or "object"


def _trim_desc(text: object, limit: int = 220) -> str:
    if not text:
        return ""
    clean = _DESC_NOISE.sub(" ", str(text))
    clean = re.sub(r"\s+", " ", clean).strip(" .;:")
    return (clean[: limit - 1] + "…") if len(clean) > limit else clean


def _props(spec: dict, schema: dict, *, deep: bool) -> list[dict]:
    """Top-level properties of ``schema``; when ``deep`` and a property is a
    ``$ref`` to an object, include that object's own top-level props (one level)."""
    out: list[dict] = []
    for name, sub in (schema.get("properties") or {}).items():
        sub = sub if isinstance(sub, dict) else {}
        entry = {
            "name": name,
            "type": _type_of(sub),
            "ref": _ref_name(sub),
            "description": _trim_desc(sub.get("description")),
            "fields": [],
        }
        if deep and entry["ref"]:
            nested = _resolve_ref(spec, sub["$ref"])
            if nested.get("type") == "object" and nested.get("properties"):
                entry["fields"] = _props(spec, nested, deep=False)
        out.append(entry)
    out.sort(key=lambda p: p["name"])
    return out


# ---- one operation's detail ---------------------------------------- #
def operation_detail(spec: dict, operation_id: str) -> dict | None:
    for svc, method, http_method, path, op in _iter_ops(spec):
        if (op.get("operationId") or f"{svc}_{method}") != operation_id:
            continue

        req_schema = (((op.get("requestBody") or {}).get("content") or {}).get("application/json") or {}).get(
            "schema"
        ) or {}
        if "$ref" in req_schema:
            req_schema = _resolve_ref(spec, req_schema["$ref"])
        request_props = _props(spec, req_schema, deep=True)

        resp = (op.get("responses") or {}).get("200") or (op.get("responses") or {}).get("default") or {}
        resp_schema_ref = ((resp.get("content") or {}).get("application/json") or {}).get("schema") or {}
        resp_schema = _resolve_ref(spec, resp_schema_ref["$ref"]) if "$ref" in resp_schema_ref else {}
        # BResult_* wraps the payload in a "result" property
        result_ref = ""
        response_props: list[dict] = []
        result_prop = (resp_schema.get("properties") or {}).get("result")
        if isinstance(result_prop, dict) and "$ref" in result_prop:
            result_ref = _ref_name(result_prop)
            payload = _resolve_ref(spec, result_prop["$ref"])
            if payload.get("properties"):
                response_props = _props(spec, payload, deep=False)

        return {
            "operation_id": operation_id,
            "service": svc,
            "method": method,
            "http_method": http_method.upper(),
            "path": path,
            "request_props": request_props,
            "response_ref": _ref_name(resp_schema_ref),
            "result_ref": result_ref,
            "response_props": response_props,
            "used_by": _catalog_uses(method),
            # deep link into the server's own Swagger UI ({base} filled in client-side)
            "elo_doc_url": f"{{base}}/rest/#/{svc}/{operation_id}",
        }
    return None


def _catalog_uses(method: str) -> list[dict]:
    """Curated topics whose 'ELO API used' list references this method."""
    from . import catalog as catalog_mod

    hits: list[dict] = []
    for topic in catalog_mod.load_topics("en"):
        if any(ref.method == method for ref in topic.elo_api):
            hits.append({"id": topic.id, "title": topic.title})
    return hits


# ---- code generation --------------------------------------------- #
def _placeholder(prop: dict) -> str:
    t = prop["type"]
    if t.endswith("[]"):
        return "[]"
    if t in ("int32", "int64", "integer", "number"):
        return "0"
    if t == "boolean":
        return "false"
    if t == "string":
        return '""'
    # a nested Z-selector like SordZ / EditInfoZ is just { "bset": "..." }
    if len(prop.get("fields") or []) == 1 and prop["fields"][0]["name"] == "bset":
        return '{ "bset": "0" }'
    return "{}"


def generate(detail: dict, language: str) -> str:
    method = detail["method"]
    service = detail["service"]
    body_lines = [
        (p["name"], _placeholder(p), p["type"])
        for p in detail["request_props"]
        if p["name"] not in _SKIP_PROPS
    ]

    if language == "go":
        return (
            "// Requires shared/go/elo.go.\npackage main\n\n"
            'import (\n  "encoding/json"\n  "fmt"\n  "example.com/elopg/elo"\n)\n\n'
            "func main() {\n"
            '  ELO_BASE_URL := elo.Env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") // ELOPG_DEFAULT:base_url\n'
            '  ELO_USER := elo.Env("ELOPG_ELO_USER", "Administrator") // ELOPG_DEFAULT:user\n'
            '  ELO_PASS := elo.Env("ELOPG_ELO_PASSWORD", "elo") // ELOPG_DEFAULT:password\n'
            "\n"
            "  client := elo.New(ELO_BASE_URL, ELO_USER, ELO_PASS)\n"
            f'  result, err := client.Call("{method}", json.RawMessage(`{{}}`))\n'
            "  if err != nil { panic(err) }\n  fmt.Println(string(result))\n}\n"
        )
    if language == "php":
        return (
            "<?php\nrequire_once __DIR__ . '/EloClient.php';\n"
            "$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url\n"
            "$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user\n"
            "$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password\n"
            "\n"
            "$elo = EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS);\n"
            f'print_r($elo->call("{method}", []));\n'
        )
    if language == "java":
        return (
            "// Requires shared/java/EloClient.java on the classpath.\n"
            "public final class Main {\n  public static void main(String[] args) throws Exception {\n"
            '    String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url\n'
            '    String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user\n'
            '    String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password\n'
            '\n'
            '    var elo = EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS);\n'
            f'    System.out.println(elo.call("{method}", "{{}}"));\n'
            "  }\n}\n"
        )
    if language == "rhino":
        return (
            "// Deploy a reviewed server-side Rhino function, then call it through IXServicePortIF.executeScript.\n"
            "// Never inject this code into Web Client and never accept arbitrary script names or code.\n"
            'var ELO_BASE_URL = java.lang.System.getenv("ELOPG_ELO_BASE_URL") || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url\n'
            'var ELO_USER = java.lang.System.getenv("ELOPG_ELO_USER") || "Administrator"; // ELOPG_DEFAULT:user\n'
            'var ELO_PASS = java.lang.System.getenv("ELOPG_ELO_PASSWORD") || "elo"; // ELOPG_DEFAULT:password\n'
            '\n'
            'function playgroundIx(baseUrl, user, password) {\n'
            '  if (!baseUrl || !user || !password) throw "ELO connection settings are required";\n'
            '  return ixConnect.ix(); // IndexServer owns the authenticated Rhino session.\n'
            '}\n\n'
            'var ix = playgroundIx(ELO_BASE_URL, ELO_USER, ELO_PASS);\n'
            'var result = ix.executeScript("RF_playground_readMetadata", { objId: "<object-id>" });\n'
        )
    if language == "python":
        svc_arg = "" if service == "IXServicePortIF" else f', service="{service}"'
        if not body_lines:
            body = "{}"
        else:
            inner = "\n".join(f'        "{n}": {v},  # {t}' for n, v, t in body_lines)
            body = "{\n" + inner + "\n    }"
        return (
            "import os\nfrom elo_playground import connect\n\n"
            "# --- local ELO test box (override with ELOPG_* env vars or a .env) ---\n"
            'ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url\n'
            'ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user\n'
            'ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password\n\n'
            "elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)\n\n"
            f'# {detail["http_method"]} {detail["path"]}\n'
            f'result = elo.call("{method}", {body}{svc_arg})\n'
            "print(result)\n"
        )

    svc_arg = "" if service == "IXServicePortIF" else f', {{ service: "{service}" }}'
    if not body_lines:
        body = "{}"
    else:
        inner = "\n".join(f"  {n}: {v}, // {t}" for n, v, t in body_lines)
        body = "{\n" + inner + "\n}"
    head = 'import { connect } from "elo-playground";\n\n' if language == "node" else ""
    return (
        f"{head}"
        "// --- local ELO test box (override with ELOPG_* env vars or a .env) ---\n"
        f'const ELO_BASE_URL = {"process.env.ELOPG_ELO_BASE_URL" if language == "node" else "globalThis.ELOPG_ELO_BASE_URL"} || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url\n'
        f'const ELO_USER = {"process.env.ELOPG_ELO_USER" if language == "node" else "globalThis.ELOPG_ELO_USER"} || "Administrator"; // ELOPG_DEFAULT:user\n'
        f'const ELO_PASS = {"process.env.ELOPG_ELO_PASSWORD" if language == "node" else "globalThis.ELOPG_ELO_PASSWORD"} || "elo"; // ELOPG_DEFAULT:password\n\n'
        "const elo = await connect({ baseUrl: ELO_BASE_URL, user: ELO_USER, password: ELO_PASS });\n\n"
        f'// {detail["http_method"]} {detail["path"]}\n'
        f'const result = await elo.call("{method}", {body}{svc_arg});\n'
        "console.log(result);\n"
    )
