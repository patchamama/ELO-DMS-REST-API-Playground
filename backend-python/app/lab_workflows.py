"""Testing lab - which workflow templates are actually used.

Read-only, **live only**. ELO keeps no usage counter on a template, but
every started workflow (active or finished) records the template it came
from, so :func:`top_workflows` lists the templates, lists the instances and
counts them per template:

* ``findFirstWorkflows`` with ``findInfo.type.bset`` = ``2`` returns the
  **templates**, ``1`` the **active** instances, ``4`` the **finished** ones
  (``WFTypeC.TEMPLATE / ACTIVE / FINISHED``). ``findNextWorkflows`` /
  ``findClose`` page like every other find.
* ``wfDiagramZ.bset`` picks the ``WFDiagram`` members. Bits verified on IX
  23+: 0 id/name/version, 4 completionDateIso, 5 nodes, 9 startDateIso,
  11 ownerName, 15 templateName, 23 objName.

Finished workflows only exist until an administrator (or the ELO
"workflow cleanup" job) removes them, so ``finished`` counts what is still
on the server - the panel says so when it is zero.
"""
from __future__ import annotations

from typing import Any

from .config import get_settings

try:
    from elo_playground import EloError
except Exception:  # pragma: no cover
    class EloError(Exception):
        ...

# WFTypeC
TYPE_ACTIVE, TYPE_TEMPLATE, TYPE_FINISHED = "1", "2", "4"
# WFDiagramC member bits (see module docstring)
_MB_BASE, _MB_COMPLETION, _MB_NODES, _MB_START, _MB_OWNER, _MB_TEMPLATE_NAME, _MB_OBJ_NAME = 0, 4, 5, 9, 11, 15, 23
TEMPLATE_Z = str((1 << _MB_BASE) | (1 << _MB_NODES) | (1 << _MB_OWNER))
INSTANCE_Z = str((1 << _MB_BASE) | (1 << _MB_COMPLETION) | (1 << _MB_START) | (1 << _MB_OWNER) | (1 << _MB_TEMPLATE_NAME) | (1 << _MB_OBJ_NAME))
_PAGE = 500


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _pretty_date(iso: str) -> str:
    s = str(iso or "")
    if len(s) >= 12 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}"
    return s


def _find_workflows(client: Any, wf_type: str, bset: str, *, max_rows: int = 20000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    res = client.call("findFirstWorkflows", {"findInfo": {"type": {"bset": wf_type}}, "max": _PAGE, "wfDiagramZ": {"bset": bset}})
    if not isinstance(res, dict):
        return rows
    search_id = res.get("searchId")
    rows.extend(w for w in (res.get("workflows") or []) if isinstance(w, dict))
    more = bool(res.get("moreResults"))
    while more and len(rows) < max_rows:
        nxt = client.call("findNextWorkflows", {"searchId": search_id, "idx": len(rows), "max": _PAGE, "wfDiagramZ": {"bset": bset}})
        page = [w for w in ((nxt.get("workflows") or []) if isinstance(nxt, dict) else []) if isinstance(w, dict)]
        if not page:
            break
        rows.extend(page)
        more = bool(nxt.get("moreResults"))
    if search_id:
        try:
            client.call("findClose", {"searchId": search_id})
        except EloError:
            pass
    return rows


def _description(template: dict[str, Any]) -> str:
    """Templates carry no description field; the start node's comment (what
    the designer typed into the first node) or the version comment is the
    closest thing."""
    nodes = template.get("nodes") or []
    first = nodes[0] if nodes and isinstance(nodes[0], dict) else {}
    for candidate in (first.get("comment"), (template.get("version") or {}).get("comment"), template.get("nameTranslationKey")):
        if candidate and str(candidate).strip():
            return str(candidate).strip()
    return ""


def top_workflows(client: Any, *, limit: int = 25) -> dict[str, Any]:
    """Templates ranked by how many workflows were started from them
    (active + finished still on the server), with last use, first use,
    description, owner, node count and version."""
    templates = _find_workflows(client, TYPE_TEMPLATE, TEMPLATE_Z)
    active = _find_workflows(client, TYPE_ACTIVE, INSTANCE_Z)
    finished = _find_workflows(client, TYPE_FINISHED, INSTANCE_Z)

    stats: dict[str, dict[str, Any]] = {}

    def bucket(key: str, name: str) -> dict[str, Any]:
        return stats.setdefault(key, {"template_id": key, "name": name, "count": 0, "active": 0, "finished": 0,
                                      "last_used_iso": "", "first_used_iso": "", "last_object": ""})

    for t in templates:
        b = bucket(str(t.get("id")), str(t.get("name") or t.get("id")))
        b.update({
            "description": _description(t), "owner": str(t.get("ownerName") or ""),
            "nodes": len(t.get("nodes") or []), "version": str((t.get("version") or {}).get("version") or ""),
            "template_exists": True,
        })
    for kind, rows in (("active", active), ("finished", finished)):
        for w in rows:
            tid = str(w.get("templateId") or "")
            # an instance whose template was deleted still tells us it ran
            key = tid if tid and tid != "0" and tid in stats else f"name:{w.get('templateName') or w.get('name')}"
            b = bucket(key, str(w.get("templateName") or w.get("name") or key))
            b.setdefault("template_exists", False)
            b["count"] += 1
            b[kind] += 1
            started = str(w.get("startDateIso") or "")
            if started and started > b["last_used_iso"]:
                b["last_used_iso"] = started
                b["last_object"] = str(w.get("objName") or "")
            if started and (not b["first_used_iso"] or started < b["first_used_iso"]):
                b["first_used_iso"] = started

    rows = sorted(stats.values(), key=lambda b: (-b["count"], b["name"].lower()))
    for b in rows:
        b["last_used"] = _pretty_date(b["last_used_iso"])
        b["first_used"] = _pretty_date(b["first_used_iso"])
        b.setdefault("description", "")
        b.setdefault("owner", "")
        b.setdefault("nodes", 0)
        b.setdefault("version", "")
    return {
        "rows": rows[:limit],
        "totals": {"templates": len(templates), "active": len(active), "finished": len(finished),
                   "used_templates": sum(1 for b in rows if b["count"])},
    }


# --------------------------------------------------------------------------- #
#  "show me the code"
# --------------------------------------------------------------------------- #
_SLICE_START = "// >>> lab-workflows slice"
_SLICE_END = "// <<< lab-workflows slice"


def _slice(text: str) -> str:
    a, b = text.find(_SLICE_START), text.find(_SLICE_END)
    return text[a:b + len(_SLICE_END)] if a >= 0 and b > a else text


def lab_workflows_source() -> dict[str, list[dict[str, str]]]:
    root = get_settings().project_root
    files = [
        ("backend-python/app/lab_workflows.py", root / "backend-python" / "app" / "lab_workflows.py"),
        ("catalog/90-lab/10-workflow-usage.yaml", root / "catalog" / "90-lab" / "10-workflow-usage.yaml"),
    ]
    backend = [{"title": t, "code": p.read_text(encoding="utf-8")} for t, p in files if p.exists()]
    js = root / "frontend" / "static" / "app.js"
    frontend = [{"title": "frontend/static/app.js (lab-workflows slice)", "code": _slice(js.read_text(encoding="utf-8"))}] if js.exists() else []
    return {"backend": backend, "frontend": frontend}
