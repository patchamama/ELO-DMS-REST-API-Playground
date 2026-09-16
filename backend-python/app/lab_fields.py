"""Testing lab - copy values between GRP (index) fields and MAP fields, for
every object of a mask, creating the GRP field first when needed.

**Live only, and this one writes** - to the mask (a new ``DocMaskLine``) and
to the objects (``objKeys`` or the MAP). The panel therefore always runs a
dry run first (:func:`plan_copy`) and only :func:`execute_copy` commits.

The ELO model, verified against IX 23+:

* A GRP field is a **line of a mask**: ``checkoutDocMask`` returns
  ``DocMask.lines = [DocMaskLine {id, key, name, type, min, max, layout...}]``
  and ``checkinDocMask`` writes the mask back. Every object indexed with the
  mask then carries one ``objKeys`` entry per line - ``{id, name: <key>,
  data: [values]}`` - even objects created before the line was added (IX
  builds ``objKeys`` from the current mask on ``checkoutSord``).
* A MAP is free key/value storage on the object: ``checkoutMap`` /
  ``checkinMap`` with ``domainName = "objekte"``.
* The objects of a mask come from ``findFirstSords`` with
  ``findByIndex.maskId``; with ``sordZ`` bits 5 (name), 53 (objKeys) and 59
  (refPaths) one page carries everything the dry run needs.
* ``DocMaskLineC.TYPE_TEXT`` is 3000 on this server generation (3001 date,
  3002 list, ...); a new field copies the type of an existing text line
  when there is one, else 3000.
"""
from __future__ import annotations

import re
from typing import Any

from .config import get_settings

try:
    from elo_playground import EloError
except Exception:  # pragma: no cover
    class EloError(Exception):
        ...

ALL = "449304431574384639"                       # SordC.mbAllIndex
_ALL_BITS = "9223372036854775807"                # "every member" for DocMaskZ / LockZ-free reads
LEAN = str((1 << 5) | (1 << 53) | (1 << 59))     # name + objKeys + refPaths
MAP_DOMAIN = "objekte"
TYPE_TEXT = 3000
# DocMaskLineC.TYPE_* as seen on IX 23+ (best effort - the spec carries the
# names, not the values)
_TYPE_NAMES = {3000: "text", 3001: "date", 3002: "list", 3003: "thesaurus", 3004: "user", 3005: "number", 3006: "iso date"}
MAX_LINE_ID = 200                                # DocMaskLineC.MAX_ID_DOCMASK_LINE
_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,29}$")
DIRECTIONS = ("map_to_grp", "grp_to_map")
_PAGE = 500


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _path_of(row: dict[str, Any]) -> str:
    paths = row.get("refPaths") or []
    first = paths[0] if paths and isinstance(paths[0], dict) else {}
    return " / ".join(str(p.get("name") or p.get("id")) for p in (first.get("path") or []) if isinstance(p, dict))


def _obj_keys(sord: dict[str, Any]) -> dict[str, str]:
    """``{key: first value}`` of a Sord's objKeys (empty string when unset)."""
    out: dict[str, str] = {}
    for k in sord.get("objKeys") or []:
        if isinstance(k, dict) and k.get("name"):
            data = k.get("data") or []
            out[str(k["name"])] = str(data[0]) if data and data[0] is not None else ""
    return out


# --------------------------------------------------------------------------- #
#  masks and their lines
# --------------------------------------------------------------------------- #
def list_masks(client: Any) -> dict[str, Any]:
    """Every mask the session may see - ``EditInfo.maskNames`` of any
    checkout (bit 1 = ``EditInfoC.mbMaskNames``)."""
    ei = client.call("checkoutSord", {"objId": "1", "editInfoZ": {"bset": "1", "sordZ": {"bset": "1"}}})
    rows = (ei.get("maskNames") or []) if isinstance(ei, dict) else []
    masks = [
        {"id": str(m.get("id")), "name": str(m.get("name") or m.get("id")), "display_name": str(m.get("displayName") or m.get("name") or m.get("id")),
         "document_mask": bool(m.get("documentMask")), "folder_mask": bool(m.get("folderMask"))}
        for m in rows if isinstance(m, dict) and m.get("id") is not None
    ]
    masks.sort(key=lambda m: m["display_name"].lower())
    return {"masks": masks}


def _checkout_mask(client: Any, mask_id: str | int, *, lock: bool = False) -> dict[str, Any]:
    dm = client.call("checkoutDocMask", {"maskId": str(mask_id), "docMaskZ": {"bset": _ALL_BITS}, "lockZ": {"bset": "1" if lock else "0"}})
    if not isinstance(dm, dict):
        raise EloError(f"checkoutDocMask({mask_id}): unexpected reply")
    return dm


def _line_out(line: dict[str, Any]) -> dict[str, Any]:
    t = _int(line.get("type"))
    return {"id": _int(line.get("id"), -1), "key": str(line.get("key") or ""), "name": str(line.get("name") or line.get("key") or ""),
            "type": t, "type_name": _TYPE_NAMES.get(t, f"type {t}"), "hidden": bool(line.get("hidden")), "read_only": bool(line.get("readOnly"))}


def _next_line_id(lines: list[dict[str, Any]]) -> int:
    used = {_int(l.get("id"), -1) for l in lines}
    for i in range(MAX_LINE_ID):
        if i not in used:
            return i
    raise EloError(f"mask has no free line id below {MAX_LINE_ID}")


def mask_fields(client: Any, mask_id: str | int) -> dict[str, Any]:
    """The mask's GRP lines plus the id a new line would get."""
    dm = _checkout_mask(client, mask_id)
    lines = [l for l in (dm.get("lines") or []) if isinstance(l, dict)]
    return {"mask": {"id": str(dm.get("id", mask_id)), "name": str(dm.get("name") or mask_id)},
            "lines": [_line_out(l) for l in lines], "next_line_id": _next_line_id(lines)}


def add_grp_field(client: Any, mask_id: str | int, key: str, name: str, *, line_type: int | None = None) -> dict[str, Any]:
    """Append a GRP line to the mask - checked out with a lock, written back
    with ``unlockZ.bset = "1"``. The key is upper-cased and must be
    ``[A-Z][A-Z0-9_]*`` (max 30) and unique in the mask."""
    key = str(key or "").strip().upper()
    name = str(name or "").strip() or key
    if not _KEY_RE.match(key):
        raise EloError(f"invalid GRP key {key!r}: use A-Z, 0-9 and _, start with a letter, max 30 characters")
    dm = _checkout_mask(client, mask_id, lock=True)
    lines = [l for l in (dm.get("lines") or []) if isinstance(l, dict)]
    if any(str(l.get("key") or "").upper() == key for l in lines):
        client.call("checkinDocMask", {"docMask": dm, "docMaskZ": {"bset": _ALL_BITS}, "unlockZ": {"bset": "1"}})  # release the lock
        raise EloError(f"the mask already has a line with key {key}")
    text_line = next((l for l in lines if _int(l.get("type")) == TYPE_TEXT), None)
    last_row = max((_int(l.get("editRow")) for l in lines), default=-1)
    new_line = {
        "id": _next_line_id(lines), "key": key, "name": name,
        "type": line_type if line_type is not None else (_int(text_line.get("type")) if text_line else TYPE_TEXT),
        "min": 0, "max": 255,
        # a plausible spot in the client's index form: below the last line
        "labelRow": last_row + 1, "labelCol": 1, "editRow": last_row + 1, "editCol": 14, "editWidth": 40,
        "tabIndex": len(lines), "hidden": False, "readOnly": False,
    }
    dm["lines"] = lines + [new_line]
    client.call("checkinDocMask", {"docMask": dm, "docMaskZ": {"bset": _ALL_BITS}, "unlockZ": {"bset": "1"}})
    fresh = mask_fields(client, mask_id)
    return {**fresh, "created": _line_out(new_line)}


# --------------------------------------------------------------------------- #
#  objects of a mask + their MAP keys
# --------------------------------------------------------------------------- #
def mask_objects(client: Any, mask_id: str | int, *, limit: int = 500) -> list[dict[str, Any]]:
    """Objects indexed with the mask - id, name, path and ``{key: value}``
    of their GRP fields - up to *limit*."""
    rows: list[dict[str, Any]] = []
    res = client.call("findFirstSords", {"findInfo": {"findByIndex": {"maskId": str(mask_id)}}, "max": min(_PAGE, limit), "sordZ": {"bset": LEAN}})
    if not isinstance(res, dict):
        return rows
    search_id = res.get("searchId")
    sords = [s for s in (res.get("sords") or []) if isinstance(s, dict)]
    more = bool(res.get("moreResults"))
    while more and len(sords) < limit:
        nxt = client.call("findNextSords", {"searchId": search_id, "idx": len(sords), "max": min(_PAGE, limit - len(sords)), "sordZ": {"bset": LEAN}})
        page = [s for s in ((nxt.get("sords") or []) if isinstance(nxt, dict) else []) if isinstance(s, dict)]
        if not page:
            break
        sords.extend(page)
        more = bool(nxt.get("moreResults"))
    if search_id:
        try:
            client.call("findClose", {"searchId": search_id})
        except EloError:
            pass
    for s in sords[:limit]:
        rows.append({"id": str(s.get("id")), "name": str(s.get("name") or s.get("id")), "path": _path_of(s), "obj_keys": _obj_keys(s)})
    return rows


def _read_map(client: Any, obj_id: str) -> dict[str, str]:
    res = client.call("checkoutMap", {"domainName": MAP_DOMAIN, "id": str(obj_id), "keyNames": ["*"], "lockZ": {"bset": "0"}})
    items = (res.get("items") or []) if isinstance(res, dict) else []
    return {str(i.get("key")): str(i.get("value") if i.get("value") is not None else "") for i in items if isinstance(i, dict) and i.get("key")}


def map_keys_for_mask(client: Any, mask_id: str | int, *, sample: int = 50) -> dict[str, Any]:
    """MAP keys seen on the first *sample* objects of the mask, with how
    many objects carry each and one example value."""
    objects = mask_objects(client, mask_id, limit=max(1, sample))
    stats: dict[str, dict[str, Any]] = {}
    for o in objects:
        for k, v in _read_map(client, o["id"]).items():
            s = stats.setdefault(k, {"key": k, "count": 0, "example": ""})
            s["count"] += 1
            if v and not s["example"]:
                s["example"] = v[:80]
    keys = sorted(stats.values(), key=lambda s: (-s["count"], s["key"].lower()))
    return {"keys": keys, "sampled": len(objects)}


# --------------------------------------------------------------------------- #
#  the copy itself: dry run, then commit
# --------------------------------------------------------------------------- #
def plan_copy(
    client: Any, mask_id: str | int, *, direction: str, map_key: str, grp_key: str,
    limit: int = 500, overwrite: bool = False,
) -> dict[str, Any]:
    """What :func:`execute_copy` would do, object by object: ``write``,
    ``skip_empty_source``, ``skip_target_has_value`` (unless *overwrite*)
    or ``same`` (already equal)."""
    if direction not in DIRECTIONS:
        raise EloError(f"direction must be one of {DIRECTIONS}")
    map_key, grp_key = str(map_key or "").strip(), str(grp_key or "").strip()
    if not map_key or not grp_key:
        raise EloError("both a MAP key and a GRP key are required")
    fields = mask_fields(client, mask_id)
    line = next((l for l in fields["lines"] if l["key"].upper() == grp_key.upper()), None)
    if line is None:
        raise EloError(f"mask {fields['mask']['name']!r} has no GRP line {grp_key!r} - create it first")
    rows = []
    for o in mask_objects(client, mask_id, limit=limit):
        grp_value = o["obj_keys"].get(line["key"], "")
        map_value = _read_map(client, o["id"]).get(map_key, "")
        source, target = (map_value, grp_value) if direction == "map_to_grp" else (grp_value, map_value)
        if not source:
            action = "skip_empty_source"
        elif source == target:
            action = "same"
        elif target and not overwrite:
            action = "skip_target_has_value"
        else:
            action = "write"
        rows.append({"id": o["id"], "name": o["name"], "path": o["path"], "source_value": source, "target_value": target, "action": action})
    summary: dict[str, int] = {"total": len(rows)}
    for r in rows:
        summary[r["action"]] = summary.get(r["action"], 0) + 1
    return {"mask": fields["mask"], "line": line, "direction": direction, "map_key": map_key, "grp_key": line["key"],
            "overwrite": overwrite, "rows": rows, "summary": summary, "dry_run": True}


def _write_grp(client: Any, obj_id: str, line: dict[str, Any], value: str) -> None:
    sord = client.call("checkoutSord", {"objId": str(obj_id), "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}, "lockZ": {"bset": "1"}})
    sord = (sord.get("sord") or {}) if isinstance(sord, dict) else {}
    keys = [k for k in (sord.get("objKeys") or []) if isinstance(k, dict)]
    hit = next((k for k in keys if str(k.get("name") or "").upper() == line["key"].upper()), None)
    if hit is None:
        # a line added moments ago may not be materialised on this Sord yet
        hit = {"id": line["id"], "name": line["key"], "data": []}
        keys.append(hit)
    hit["data"] = [value]
    sord["objKeys"] = keys
    client.call("checkinSord", {"sord": sord, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})


def _write_map(client: Any, obj_id: str, key: str, value: str) -> None:
    client.call("checkinMap", {"objId": _int(obj_id), "id": str(obj_id), "domainName": MAP_DOMAIN,
                               "data": [{"key": key, "value": value}], "unlockZ": {"bset": "1"}})


def execute_copy(client: Any, mask_id: str | int, **kwargs: Any) -> dict[str, Any]:
    """Run the plan and commit every ``write`` row; a failing object gets an
    ``error`` and the rest continues."""
    plan = plan_copy(client, mask_id, **kwargs)
    written = failed = 0
    for r in plan["rows"]:
        if r["action"] != "write":
            r["result"] = "skipped"
            continue
        try:
            if plan["direction"] == "map_to_grp":
                _write_grp(client, r["id"], plan["line"], r["source_value"])
            else:
                _write_map(client, r["id"], plan["map_key"], r["source_value"])
            r["result"] = "written"
            written += 1
        except EloError as exc:
            r["result"] = "failed"
            r["error"] = str(exc)
            failed += 1
    plan["summary"].update({"written": written, "failed": failed, "skipped": len(plan["rows"]) - written - failed})
    plan["dry_run"] = False
    return plan


# --------------------------------------------------------------------------- #
#  "show me the code"
# --------------------------------------------------------------------------- #
_SLICE_START = "// >>> lab-fields slice"
_SLICE_END = "// <<< lab-fields slice"


def _slice(text: str) -> str:
    a, b = text.find(_SLICE_START), text.find(_SLICE_END)
    return text[a:b + len(_SLICE_END)] if a >= 0 and b > a else text


def lab_fields_source() -> dict[str, list[dict[str, str]]]:
    root = get_settings().project_root
    files = [
        ("backend-python/app/lab_fields.py", root / "backend-python" / "app" / "lab_fields.py"),
        ("catalog/90-lab/05-grp-to-map.yaml", root / "catalog" / "90-lab" / "05-grp-to-map.yaml"),
    ]
    backend = [{"title": t, "code": p.read_text(encoding="utf-8")} for t, p in files if p.exists()]
    js = root / "frontend" / "static" / "app.js"
    frontend = [{"title": "frontend/static/app.js (lab-fields slice)", "code": _slice(js.read_text(encoding="utf-8"))}] if js.exists() else []
    return {"backend": backend, "frontend": frontend}
