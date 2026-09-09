"""Testing lab - generate an ELO structure on the local filesystem, or the
reverse.

Three primitives, all **live only** (they touch a real ELO and the local disk):

* :func:`list_children`      - one level of the ELO folder tree (lazy expansion)
* :func:`mirror_to_sandbox`  - copy an ELO subtree (folders + document bytes)
  into ``sandbox/elo-archiv-structure/`` (wiped first) and open it in the OS
  file manager. Every folder also gets a ``metadata.opf`` sidecar (XML) holding
  its mask, GRP + MAP field values, dates and ACL - a backup / import template.
* :func:`upload_tree`        - create a local folder tree (walked on the backend
  or sent by the browser) as folders + documents under a chosen ELO folder. A
  ``metadata.opf`` found in a folder is applied to the new ELO folder and is NOT
  itself uploaded as a document.

The FastAPI layer (``/api/lab/*`` in :mod:`app.main`) wraps every call so a
failure becomes ``{"error": "..."}`` instead of a 500 - same convention as the
browser proxy.
"""
from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .config import get_settings

try:  # the real client; a MockEloClient has the same surface in tests
    from elo_playground import EloError
except Exception:  # pragma: no cover - shared client always importable in practice
    class EloError(Exception):
        ...

# SordC.mbAllIndex - "give me / write every Sord field".
ALL = "449304431574384639"
# ELO object types: folders are < 254, documents are 254..998 (9999 = root).
_DOC_TYPE_MIN = 254
# Windows-reserved / path characters, replaced in file and folder names.
_BAD_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
# Per-folder metadata sidecar written on export / consumed on import.
METADATA_FILE = "metadata.opf"
# The Sord map domain (see collectMapDomains); "objekte" is the object map.
_MAP_DOMAIN = "objekte"


def _int_or(value: Any, default: int | None = 0) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _sandbox_dir() -> Path:
    """``<project root>/sandbox/elo-archiv-structure`` - the mirror target."""
    return get_settings().project_root / "sandbox" / "elo-archiv-structure"


def _safe_name(name: str, fallback: str = "item") -> str:
    cleaned = _BAD_NAME.sub("_", str(name or "")).strip().strip(".")
    return cleaned or fallback


def _is_folder(row: dict[str, Any]) -> bool:
    try:
        return int(row.get("type", 0)) < _DOC_TYPE_MIN
    except (TypeError, ValueError):
        return True


# --------------------------------------------------------------------------- #
#  ELO -> tree / local
# --------------------------------------------------------------------------- #
def list_children(client: Any, parent_id: str | int) -> list[dict[str, Any]]:
    """Direct children of one ELO folder, as
    ``[{id, name, type, is_folder, child_count}, ...]``."""
    res = client.call(
        "findFirstSords",
        {
            "findInfo": {
                "findChildren": {"parentId": str(parent_id), "mainParent": True, "endLevel": 1}
            },
            "max": 1000,
            "sordZ": {"bset": ALL},
        },
    )
    sords = res.get("sords") or [] if isinstance(res, dict) else []
    search_id = res.get("searchId") if isinstance(res, dict) else None
    if search_id:
        try:
            client.call("findClose", {"searchId": search_id})
        except EloError:
            pass

    rows: list[dict[str, Any]] = []
    for s in sords:
        if not isinstance(s, dict):
            continue
        # endLevel 1 already limits to direct children; filter defensively so a
        # server that returns the parent or a deeper level cannot leak in.
        if s.get("parentId") is not None and str(s.get("parentId")) != str(parent_id):
            continue
        rows.append(
            {
                "id": str(s.get("id")),
                "name": str(s.get("name") or s.get("id")),
                "type": int(s.get("type", 0) or 0),
                "is_folder": _is_folder(s),
                "child_count": int(s.get("childCount", 0) or 0),
            }
        )
    return rows


def _download_doc(client: Any, obj_id: str, max_bytes: int) -> tuple[bytes, str] | None:
    """``(bytes, ext)`` for one document, or ``None`` when it has no content."""
    info = client.call(
        "checkoutDoc",
        {"objId": obj_id, "editInfoZ": {"bset": "320", "sordZ": {"bset": "0"}}},
    )
    docs = ((info.get("document") or {}).get("docs")) or [] if isinstance(info, dict) else []
    if not docs or not isinstance(docs[0], dict) or not docs[0].get("url"):
        return None
    ext = str(docs[0].get("ext") or "").lstrip(".")
    body = client.download(docs[0]["url"], max_bytes=max_bytes)
    if isinstance(body, str):  # the Node/browser client hands back text
        body = body.encode("utf-8")
    return body, ext


def _full_sord(client: Any, obj_id: str | int) -> dict[str, Any]:
    """The complete Sord record for one object (every field)."""
    res = client.call(
        "checkoutSord",
        {"objId": str(obj_id), "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}},
    )
    return (res.get("sord") or {}) if isinstance(res, dict) else {}


def _resolve_folder_name(client: Any, folder_id: str | int) -> str:
    try:
        return str(_full_sord(client, folder_id).get("name") or "")
    except EloError:
        return ""


def _read_map_items(client: Any, obj_id: str | int) -> list[dict[str, str]]:
    """The object's MAP (free key/value) entries, or ``[]`` (best effort)."""
    try:
        res = client.call(
            "checkoutMap",
            {
                "objId": _int_or(obj_id, 0),
                "id": str(obj_id),
                "domainName": _MAP_DOMAIN,
                "keyNames": ["*"],
                "lockZ": {"bset": "0"},
            },
        )
    except EloError:
        return []
    items = res.get("items") if isinstance(res, dict) else None
    out: list[dict[str, str]] = []
    for it in items or []:
        if isinstance(it, dict) and it.get("key") is not None:
            out.append({"key": str(it["key"]), "value": "" if it.get("value") is None else str(it["value"])})
    return out


# --------------------------------------------------------------------------- #
#  metadata.opf  -  per-container XML sidecar (export template / backup)
# --------------------------------------------------------------------------- #
def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _sub_text(parent: ET.Element, tag: str, value: Any) -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = "" if value is None else str(value)
    return el


def build_metadata_xml(sord: dict[str, Any], map_items: list[dict[str, str]], *, repo_url: str = "") -> str:
    """Render one container's full metadata as a structured XML document."""
    root = ET.Element(
        "eloContainer",
        {"version": "1", "generator": "elo-api-playground", "exportedIso": _now_iso()},
    )
    ET.SubElement(
        root,
        "source",
        {
            "repository": repo_url or "",
            "objId": str(sord.get("id", "")),
            "guid": str(sord.get("guid", "")),
            "parentId": str(sord.get("parentId", "")),
        },
    )
    s = ET.SubElement(root, "sord")
    _sub_text(s, "name", sord.get("name"))
    _sub_text(s, "desc", sord.get("desc"))
    _sub_text(s, "type", sord.get("type"))
    ET.SubElement(
        s,
        "mask",
        {"id": str(sord.get("mask", sord.get("maskId", ""))), "name": str(sord.get("maskName", ""))},
    )
    _sub_text(s, "kind", sord.get("kind"))
    ET.SubElement(
        s, "owner", {"id": str(sord.get("ownerId", "")), "name": str(sord.get("ownerName", ""))}
    )
    ET.SubElement(
        s,
        "dates",
        {
            "iDateIso": str(sord.get("IDateIso", "")),
            "xDateIso": str(sord.get("XDateIso", "")),
            "tStamp": str(sord.get("TStamp", "")),
            "delDateIso": str(sord.get("delDateIso", "")),
        },
    )
    details = sord.get("details")
    if isinstance(details, dict):
        ET.SubElement(
            s,
            "details",
            {"sortOrder": str(details.get("sortOrder", "")), "archivingMode": str(details.get("archivingMode", ""))},
        )

    gf = ET.SubElement(root, "groupFields")
    for k in sord.get("objKeys") or []:
        if not isinstance(k, dict) or not k.get("name"):
            continue
        fe = ET.SubElement(gf, "field", {"name": str(k["name"])})
        for v in k.get("data") or []:
            _sub_text(fe, "value", v)

    mf = ET.SubElement(root, "mapFields")
    for it in map_items or []:
        fe = ET.SubElement(mf, "field", {"key": str(it["key"])})
        _sub_text(fe, "value", it.get("value"))

    acl = ET.SubElement(root, "acl")
    for a in sord.get("aclItems") or []:
        if isinstance(a, dict):
            ET.SubElement(
                acl,
                "entry",
                {
                    "id": str(a.get("id", "")),
                    "type": str(a.get("type", "")),
                    "name": str(a.get("name", "")),
                    "access": str(a.get("access", "")),
                },
            )

    ET.indent(root, space="  ")
    return "<?xml version='1.0' encoding='utf-8'?>\n" + ET.tostring(root, encoding="unicode") + "\n"


def parse_metadata_xml(text: str) -> dict[str, Any]:
    """Inverse of :func:`build_metadata_xml`; tolerant of missing pieces."""
    out: dict[str, Any] = {
        "name": None, "desc": None, "mask_id": None, "mask_name": None, "type": None,
        "kind": None, "i_date": None, "x_date": None, "owner_name": None,
        "group_fields": {}, "map_fields": {}, "acl": [], "guid": None, "source_id": None,
    }
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return out

    src = root.find("source")
    if src is not None:
        out["guid"] = src.get("guid") or None
        out["source_id"] = src.get("objId") or None

    s = root.find("sord")
    if s is not None:
        out["name"] = s.findtext("name") or None
        out["desc"] = s.findtext("desc")
        out["type"] = _int_or(s.findtext("type"), None)
        m = s.find("mask")
        if m is not None:
            out["mask_id"] = _int_or(m.get("id"), None)
            out["mask_name"] = m.get("name") or None
        kind = s.findtext("kind")
        out["kind"] = _int_or(kind, None) if kind not in (None, "") else None
        d = s.find("dates")
        if d is not None:
            out["i_date"] = d.get("iDateIso") or None
            out["x_date"] = d.get("xDateIso") or None
        ow = s.find("owner")
        if ow is not None:
            out["owner_name"] = ow.get("name") or None

    gf = root.find("groupFields")
    for fe in gf.findall("field") if gf is not None else []:
        name = fe.get("name")
        if name:
            out["group_fields"][name] = [v.text or "" for v in fe.findall("value")]

    mf = root.find("mapFields")
    for fe in mf.findall("field") if mf is not None else []:
        key = fe.get("key")
        if key is not None:
            out["map_fields"][key] = fe.findtext("value") or ""

    acl = root.find("acl")
    for e in acl.findall("entry") if acl is not None else []:
        out["acl"].append(
            {
                "id": _int_or(e.get("id")),
                "type": _int_or(e.get("type")),
                "name": e.get("name") or "",
                "access": _int_or(e.get("access")),
            }
        )
    return out


def apply_metadata(client: Any, obj_id: str | int, meta: dict[str, Any]) -> list[str]:
    """Write the round-trippable subset of *meta* (desc, dates, colour, GRP and
    MAP fields) onto an existing ELO folder. Returns a list of warnings.

    The sidecar's original ``id`` / ``guid`` (``<source>`` in the XML) are never
    sent: a freshly created container already has its own new id and guid, and
    that is the record we check out, edit and check back in here.
    """
    warnings: list[str] = []
    try:
        sord = _full_sord(client, obj_id)  # the NEW container - keeps its own id/guid
    except EloError as exc:
        return [f"{obj_id}: checkout failed: {exc}"]
    if not sord:
        return [f"{obj_id}: could not read the folder back"]

    changed = False
    if meta.get("desc"):
        sord["desc"] = meta["desc"]
        changed = True
    if meta.get("i_date"):
        sord["IDateIso"] = meta["i_date"]
        changed = True
    if meta.get("x_date"):
        sord["XDateIso"] = meta["x_date"]
        changed = True
    if meta.get("kind") is not None:
        sord["kind"] = meta["kind"]
        changed = True
    if meta.get("group_fields"):
        by_name = {k.get("name"): k for k in sord.get("objKeys", []) if isinstance(k, dict) and k.get("name")}
        for name, values in meta["group_fields"].items():
            if name in by_name:
                by_name[name]["data"] = list(values)
            else:
                sord.setdefault("objKeys", []).append({"name": name, "data": list(values)})
        changed = True

    if changed:
        try:
            client.call("checkinSord", {"sord": sord, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})
        except EloError as exc:
            warnings.append(f"{obj_id}: sord update failed: {exc}")

    if meta.get("map_fields"):
        try:
            client.call(
                "checkinMap",
                {
                    "objId": _int_or(obj_id, 0),
                    "domainName": _MAP_DOMAIN,
                    "data": [{"key": k, "value": v} for k, v in meta["map_fields"].items()],
                    "unlockZ": {"bset": "1"},
                },
            )
        except EloError as exc:
            warnings.append(f"{obj_id}: map update failed: {exc}")
    return warnings


def mirror_to_sandbox(
    client: Any,
    folder_id: str | int,
    *,
    folder_name: str | None = None,
    max_objects: int = 500,
    max_bytes: int = 25 * 1024 * 1024,
) -> dict[str, Any]:
    """Wipe ``sandbox/elo-archiv-structure/`` and rebuild it from the ELO subtree
    rooted at *folder_id*. The selected folder itself becomes the top directory,
    holding its whole recursive content - subfolders AND document bytes. Then
    open that folder in the OS file manager."""
    dst = _sandbox_dir()
    sandbox_root = (get_settings().project_root / "sandbox").resolve()
    try:
        dst.resolve().relative_to(sandbox_root)
    except ValueError:  # pragma: no cover - _sandbox_dir is fixed
        raise EloError("refusing to write outside the sandbox directory")

    # the picked folder becomes the top directory in the mirror
    top = _safe_name(folder_name or "", "") or _safe_name(
        _resolve_folder_name(client, folder_id), ""
    ) or f"folder-{folder_id}"

    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    dest_root = dst / top
    dest_root.mkdir(parents=True, exist_ok=True)

    repo_url = str(getattr(client, "base_url", "") or "")
    state = {
        "n": 0, "folders": 1, "documents": 0, "metadata": 0, "bytes": 0,
        "truncated": False, "skipped": [],
    }

    def write_metadata(obj_id: str | int, folder_path: Path) -> None:
        try:
            sord = _full_sord(client, obj_id)
            xml = build_metadata_xml(sord, _read_map_items(client, obj_id), repo_url=repo_url)
        except EloError as exc:
            xml = (
                "<?xml version='1.0' encoding='utf-8'?>\n"
                f"<eloContainer error={_xml_attr(str(exc))}/>\n"
            )
        (folder_path / METADATA_FILE).write_text(xml, encoding="utf-8")
        state["metadata"] += 1

    write_metadata(folder_id, dest_root)

    def walk(parent_id: str | int, here: Path) -> None:
        for row in list_children(client, parent_id):
            if state["n"] >= max_objects:
                state["truncated"] = True
                return
            state["n"] += 1
            name = _safe_name(row["name"], f"obj-{row['id']}")
            if row["is_folder"]:
                sub = here / name
                sub.mkdir(parents=True, exist_ok=True)
                state["folders"] += 1
                write_metadata(row["id"], sub)
                walk(row["id"], sub)
            else:
                try:
                    got = _download_doc(client, row["id"], max_bytes)
                except EloError as exc:
                    state["skipped"].append(f"{row['name']}: {exc}")
                    continue
                if got is None:
                    continue
                body, ext = got
                fname = name if ("." in name or not ext) else f"{name}.{ext}"
                (here / _safe_name(fname, f"obj-{row['id']}")).write_bytes(body)
                state["documents"] += 1
                state["bytes"] += len(body)

    walk(folder_id, dest_root)
    opened = open_in_file_manager(dest_root)
    return {
        "root": str(dest_root),
        "top": top,
        "folders": state["folders"],
        "documents": state["documents"],
        "metadata": state["metadata"],
        "bytes": state["bytes"],
        "truncated": state["truncated"],
        "skipped": state["skipped"][:20],
        "opened": opened,
    }


def _xml_attr(value: str) -> str:
    """Quote a string for use as an XML attribute value."""
    esc = value.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
    return f'"{esc}"'


def open_in_file_manager(path: str | Path) -> bool:
    """Reveal *path* in the desktop file manager. Never raises; returns whether
    the launch was attempted successfully."""
    p = str(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(p)  # type: ignore[attr-defined]  # noqa: S606 - local folder only
        elif sys.platform == "darwin":
            subprocess.run(["open", p], check=False)
        else:
            subprocess.run(["xdg-open", p], check=False)
        return True
    except Exception:  # noqa: BLE001 - opening a folder must never break the request
        return False


# --------------------------------------------------------------------------- #
#  local -> ELO
# --------------------------------------------------------------------------- #
def _rel_dir(root_name: str, root: Path, here: Path) -> str:
    sub = here.relative_to(root).as_posix()
    return root_name if sub in ("", ".") else f"{root_name}/{sub}"


def _collect_from_server_path(base: str, root_name: str, max_bytes: int) -> tuple[list, list, dict, int]:
    root = Path(base).expanduser()
    if not root.is_dir():
        raise EloError(f"not a directory on the backend host: {base}")
    files: list[tuple[str, bytes]] = []
    dirs: list[str] = []
    meta_by_dir: dict[str, str] = {}
    skipped = 0
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        for dn in sorted(dirnames):  # keep every subfolder, including empty ones
            rel = (here / dn).relative_to(root).as_posix()
            dirs.append(str(PurePosixPath(root_name) / rel))
        for fn in sorted(filenames):
            fp = here / fn
            if fn.lower() == METADATA_FILE:  # a sidecar, not a document
                try:
                    meta_by_dir[_rel_dir(root_name, root, here)] = fp.read_text(
                        encoding="utf-8", errors="replace"
                    )
                except OSError:
                    pass
                continue
            try:
                if fp.stat().st_size > max_bytes:
                    skipped += 1
                    continue
                body = fp.read_bytes()
            except OSError:
                skipped += 1
                continue
            rel = fp.relative_to(root).as_posix()
            files.append((str(PurePosixPath(root_name) / rel), body))
    return files, dirs, meta_by_dir, skipped


def _collect_from_items(
    items: list[dict[str, Any]], root_name: str, max_bytes: int
) -> tuple[list, list, dict, int]:
    files: list[tuple[str, bytes]] = []
    meta_by_dir: dict[str, str] = {}
    skipped = 0
    for it in items:
        rel = str(it.get("rel_path") or "").replace("\\", "/").strip("/")
        parts = rel.split("/")
        if not rel or ".." in parts or rel.startswith("/") or ":" in parts[0]:
            raise EloError(f"unsafe path in upload: {it.get('rel_path')!r}")
        try:
            body = base64.b64decode(it.get("b64") or "", validate=False)
        except Exception:  # noqa: BLE001
            raise EloError(f"bad base64 for {rel!r}")
        if parts[-1].lower() == METADATA_FILE:  # a sidecar, not a document
            parent = "/".join(parts[:-1])
            key = f"{root_name}/{parent}" if parent else root_name
            meta_by_dir[key] = body.decode("utf-8", "replace")
            continue
        if len(body) > max_bytes:
            skipped += 1
            continue
        files.append((str(PurePosixPath(root_name) / rel), body))
    # the browser directory picker only yields files, so empty folders cannot be
    # seen; ensure_folder() still recreates every folder that holds a file.
    return files, [], meta_by_dir, skipped


def upload_tree(
    client: Any,
    *,
    target_id: str | int,
    root_name: str | None = None,
    server_path: str | None = None,
    items: list[dict[str, Any]] | None = None,
    max_objects: int = 500,
    max_bytes: int = 25 * 1024 * 1024,
) -> dict[str, Any]:
    """Recreate *server_path* / *items* under ELO *target_id* - the whole tree:
    the picked folder itself, every subfolder (empty ones included, for a server
    path) and every document."""
    items = items or []
    if server_path:
        root_name = _safe_name(root_name or Path(server_path).name, "uploaded")
        files, dirs, meta_by_dir, skipped = _collect_from_server_path(server_path, root_name, max_bytes)
    elif items:
        root_name = _safe_name(root_name or "uploaded", "uploaded")
        files, dirs, meta_by_dir, skipped = _collect_from_items(items, root_name, max_bytes)
    else:
        raise EloError("nothing to upload: give a server path or pick a folder")

    # a metadata.opf sidecar per folder -> mask at create time + fields afterwards
    dir_meta: dict[str, dict[str, Any]] = {rel: parse_metadata_xml(txt) for rel, txt in meta_by_dir.items()}

    folder_cache: dict[str, str] = {"": str(target_id)}
    counters = {"folders": 0, "documents": 0, "bytes": 0, "truncated": False}

    def capped() -> bool:
        if counters["folders"] + counters["documents"] >= max_objects:
            counters["truncated"] = True
            return True
        return False

    def ensure_folder(rel_dir: str) -> str:
        if rel_dir in folder_cache:
            return folder_cache[rel_dir]
        parent_rel, _, name = rel_dir.rpartition("/")
        parent_id = ensure_folder(parent_rel)
        mask_id = (dir_meta.get(rel_dir) or {}).get("mask_id")
        tpl = client.call(
            "createSord",
            {
                "parentId": str(parent_id),
                "maskId": mask_id if isinstance(mask_id, int) else 1,
                "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
            },
        )["sord"]
        tpl["name"] = name
        new_id = str(
            client.call("checkinSord", {"sord": tpl, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}})
        )
        folder_cache[rel_dir] = new_id
        counters["folders"] += 1
        return new_id

    ensure_folder(root_name)  # the picked folder itself, even when it holds nothing
    for d in dirs:
        if capped():
            break
        ensure_folder(d)

    for rel_path, body in files:
        if capped():
            break
        rel_dir, _, fname = rel_path.rpartition("/")
        parent_id = ensure_folder(rel_dir)
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else "bin"
        sord = client.call(
            "createDoc",
            {"parentId": str(parent_id), "maskId": 0, "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}},
        )["sord"]
        sord["name"] = fname
        doc = client.call("checkinDocBegin", {"sord": sord, "document": {"docs": [{"ext": ext}]}})
        doc["docs"][0]["uploadResult"] = client.upload(doc["docs"][0]["url"], body)
        client.call(
            "checkinDocEnd",
            {"sord": sord, "document": doc, "sordZ": {"bset": ALL}, "unlockZ": {"bset": "1"}},
        )
        counters["documents"] += 1
        counters["bytes"] += len(body)

    # apply every metadata.opf onto its (now existing) ELO folder
    applied = 0
    warnings: list[str] = []
    for rel_dir, meta in dir_meta.items():
        fid = folder_cache.get(rel_dir)
        if fid is None and not capped():
            fid = ensure_folder(rel_dir)
        if fid is None:
            continue
        warnings.extend(apply_metadata(client, fid, meta))
        applied += 1

    return {
        "target_id": str(target_id),
        "root_name": root_name,
        "folders": counters["folders"],
        "documents": counters["documents"],
        "metadata_applied": applied,
        "warnings": warnings[:20],
        "bytes": counters["bytes"],
        "skipped": skipped,
        "truncated": counters["truncated"],
    }


# --------------------------------------------------------------------------- #
#  "show me the code" - real source, so the panel and its listing never drift
# --------------------------------------------------------------------------- #
_SLICE_START = "// >>> lab-fs slice"
_SLICE_END = "// <<< lab-fs slice"


def _slice(text: str) -> str:
    i = text.find(_SLICE_START)
    j = text.find(_SLICE_END)
    if i == -1 or j == -1 or j < i:
        return text
    return text[i : j + len(_SLICE_END)]


def lab_fs_source() -> dict[str, list[dict[str, str]]]:
    root = get_settings().project_root
    out: dict[str, list[dict[str, str]]] = {"backend": [], "frontend": []}
    be = root / "backend-python" / "app" / "lab_fs.py"
    yml = root / "catalog" / "90-lab" / "07-elo-local-filesystem.yaml"
    fe = root / "frontend" / "static" / "app.js"
    if be.is_file():
        out["backend"].append({"title": "backend-python/app/lab_fs.py", "code": be.read_text(encoding="utf-8")})
    if yml.is_file():
        out["backend"].append(
            {"title": "catalog/90-lab/07-elo-local-filesystem.yaml", "code": yml.read_text(encoding="utf-8")}
        )
    if fe.is_file():
        out["frontend"].append(
            {"title": "frontend/static/app.js  (lab-fs panel)", "code": _slice(fe.read_text(encoding="utf-8"))}
        )
    return out
