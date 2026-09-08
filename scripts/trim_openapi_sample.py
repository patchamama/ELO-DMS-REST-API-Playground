"""Dev tool: build the committed ``fixtures/openapi.sample.json`` from a full
ELO ``openapi.json``.

    # first, save the real spec (no auth needed):
    curl http://localhost:9090/ix-Repository1/rest/openapi.json -o runtime/openapi.real.json
    python scripts/trim_openapi_sample.py runtime/openapi.real.json

Keeps a hand-picked set of operations plus every component schema they reach
(transitively, capped), so the file stays small enough to commit while the
"API reference" tab still has something real to render offline.

Live mode fetches the full spec from the server; this sample is only the
mock / CI fallback.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fixtures" / "openapi.sample.json"

# Operations to keep (path last segment). Covers every method the catalogue
# uses, plus a few more so the reference tab is not tiny.
KEEP = {
    "login", "logout", "getServerInfo", "getSessionOptions", "getUserData",
    "findFirstSords", "findNextSords", "findClose", "checkoutSord", "createSord",
    "checkinSord", "deleteSord", "checkoutDoc", "checkinDocEnd",
    "findFirstDocMasks", "findNextDocMasks", "checkoutDocMask",
    "findFirstUsers", "findNextUsers", "checkoutUsers", "checkinUsers",
    "checkoutKeywordList", "findFirstWorkflows", "startWorkflow",
    "getWorkFlowStatus", "checkoutSordTypes", "getServerInfoDM",
}
MAX_DEPTH = 4


def _refs(node, acc: set[str]) -> None:
    if isinstance(node, dict):
        r = node.get("$ref")
        if isinstance(r, str) and r.startswith("#/components/schemas/"):
            acc.add(r.rsplit("/", 1)[-1])
        for v in node.values():
            _refs(v, acc)
    elif isinstance(node, list):
        for v in node:
            _refs(v, acc)


def main(src: str) -> int:
    full = json.loads(Path(src).read_text(encoding="utf-8"))
    all_schemas = full.get("components", {}).get("schemas", {})

    kept_paths: dict = {}
    seed: set[str] = set()
    for path, item in full.get("paths", {}).items():
        if not isinstance(item, dict):
            continue
        seg = [s for s in path.split("/") if s]
        if seg and seg[-1] in KEEP:
            kept_paths[path] = item
            _refs(item, seed)

    # transitive schema closure (capped)
    keep_schemas: set[str] = set()
    frontier = set(seed)
    for _ in range(MAX_DEPTH):
        nxt: set[str] = set()
        for name in frontier:
            if name in keep_schemas or name not in all_schemas:
                continue
            keep_schemas.add(name)
            _refs(all_schemas[name], nxt)
        frontier = nxt - keep_schemas
    keep_schemas |= {n for n in frontier if n in all_schemas}

    sample = {
        "openapi": full.get("openapi", "3.0.1"),
        "info": full.get("info", {}),
        "_note": "Trimmed sample for offline / CI use - see scripts/trim_openapi_sample.py. Live mode fetches the full spec.",
        "paths": dict(sorted(kept_paths.items())),
        "components": {"schemas": {n: all_schemas[n] for n in sorted(keep_schemas) if n in all_schemas}},
    }
    OUT.write_text(json.dumps(sample, indent=1, ensure_ascii=False), encoding="utf-8")
    print(
        f"wrote {OUT.relative_to(ROOT)}  "
        f"({len(kept_paths)} paths, {len(sample['components']['schemas'])} schemas, "
        f"{OUT.stat().st_size // 1024} KiB)"
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
