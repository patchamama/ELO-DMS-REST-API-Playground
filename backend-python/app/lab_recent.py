"""Testing lab - browse the ELO folder tree and list the newest documents
below a folder, then preview one.

Read-only, **live only**. Two primitives back the panel:

* :func:`recent_files` - the *limit* most recently modified documents in a
  folder **or anywhere below it**. There is no cheap "recursive children,
  newest first" query in IX: ``findChildren`` with ``endLevel = -1`` walks
  the whole subtree server-side (10-30 s on a mid-size repository) and
  ``FindOptions.sortOrder`` does not sort by date. What *is* fast is the
  indexed ``findByIndex.iDateIso`` range search (~1200 rows/s with a lean
  ``sordZ``), so this walks backwards through date windows (last week, then
  the month before, ...) and keeps the rows whose ``refPaths`` pass through
  the chosen folder, until *limit* matches are in hand and the window they
  came from is fully scanned - which makes the answer exact, not "newest of
  the first N".
* :func:`file_preview` - one document's bytes via ``checkoutDoc`` +
  download, turned into something a browser can show: decoded text (with a
  highlight.js language hint), the text inside a ``.docx`` (``word/document.xml``,
  no extra library), a PDF/image as base64 for the browser's own viewer.

``sordZ`` bits used here (verified against IX 23+; ``SordC.mbAllIndex``
does *not* include the last two): 5 name, 7 IDateIso, 17 ownerName,
54 docVersion (ext/size), 59 refPaths (the folder path).
"""
from __future__ import annotations

import base64
import io
import re
import zipfile
from datetime import datetime, timedelta
from typing import Any

from .config import get_settings

try:  # the real client; a MockEloClient has the same surface in tests
    from elo_playground import EloError
except Exception:  # pragma: no cover
    class EloError(Exception):
        ...

# SordC member bits - only what the listing needs, so paging stays fast.
_MB_NAME, _MB_IDATE, _MB_OWNER_NAME, _MB_DOC_VERSION, _MB_REF_PATHS = 5, 7, 17, 54, 59
LEAN = str((1 << _MB_NAME) | (1 << _MB_IDATE) | (1 << _MB_OWNER_NAME) | (1 << _MB_DOC_VERSION) | (1 << _MB_REF_PATHS))
# ELO object types: folders are < 254, documents 254..998.
_DOC_TYPE_MIN = 254
# date windows walked backwards from "now" (days back, cumulative); None =
# everything older. Fine-grained on purpose: a window is scanned whole, so
# the finer the ladder, the smaller the chance one window blows the budget.
WINDOWS: tuple[int | None, ...] = (1, 3, 7, 14, 30, 60, 90, 180, 365, 730, 1460, 2920, None)
_PAGE = 500

# extension -> (kind, highlight.js language)
_TEXT_LANG = {
    "js": "javascript", "mjs": "javascript", "ts": "typescript", "json": "json", "xml": "xml", "html": "xml",
    "htm": "xml", "svg": "xml", "css": "css", "less": "less", "scss": "scss", "csv": "plaintext", "txt": "plaintext",
    "md": "markdown", "markdown": "markdown", "properties": "ini", "ini": "ini", "yaml": "yaml", "yml": "yaml",
    "py": "python", "java": "java", "sql": "sql", "sh": "bash", "bat": "dos", "ps1": "powershell", "log": "plaintext",
    "eml": "plaintext", "rtf": "plaintext",
}
_IMAGE_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _iso_compact(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S")


def _pretty_date(iso: str) -> str:
    """``20240607120600`` -> ``2024-06-07 12:06``; anything odd passes through."""
    s = str(iso or "")
    if len(s) >= 12 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}"
    return s


def _path_ids_and_names(row: dict[str, Any]) -> tuple[list[str], str]:
    paths = row.get("refPaths") or []
    first = paths[0] if paths and isinstance(paths[0], dict) else {}
    parts = [p for p in (first.get("path") or []) if isinstance(p, dict)]
    return [str(p.get("id")) for p in parts], " / ".join(str(p.get("name") or p.get("id")) for p in parts)


def _close(client: Any, search_id: Any) -> None:
    if search_id:
        try:
            client.call("findClose", {"searchId": search_id})
        except EloError:
            pass


def _sord_name(client: Any, obj_id: str | int) -> str:
    res = client.call("checkoutSord", {"objId": str(obj_id), "editInfoZ": {"bset": "1", "sordZ": {"bset": str(1 << _MB_NAME)}}})
    sord = (res.get("sord") or {}) if isinstance(res, dict) else {}
    return str(sord.get("name") or obj_id)


def _scan_window(client: Any, since: str, until: str, *, budget: int) -> tuple[list[dict[str, Any]], bool]:
    """Every document modified in ``[since, until]`` (ELO range syntax
    ``A...B``), page by page, up to *budget* rows. Returns the rows and
    whether the window was exhausted."""
    rows: list[dict[str, Any]] = []
    res = client.call(
        "findFirstSords",
        {
            "findInfo": {"findByIndex": {"iDateIso": f"{since}...{until}"}, "findByType": {"typeDocuments": True}},
            "max": min(_PAGE, budget),
            "sordZ": {"bset": LEAN},
        },
    )
    if not isinstance(res, dict):
        return rows, True
    search_id = res.get("searchId")
    rows.extend(s for s in (res.get("sords") or []) if isinstance(s, dict))
    more = bool(res.get("moreResults"))
    while more and len(rows) < budget:
        nxt = client.call("findNextSords", {"searchId": search_id, "idx": len(rows), "max": min(_PAGE, budget - len(rows)), "sordZ": {"bset": LEAN}})
        page = [s for s in ((nxt.get("sords") or []) if isinstance(nxt, dict) else []) if isinstance(s, dict)]
        if not page:
            more = False
            break
        rows.extend(page)
        more = bool(nxt.get("moreResults"))
    _close(client, search_id)
    return rows, not more


def recent_files(
    client: Any,
    folder_id: str | int = "1",
    *,
    limit: int = 50,
    max_scan: int = 6000,
    now: datetime | None = None,
) -> dict[str, Any]:
    """The *limit* newest documents in *folder_id* or any subfolder, newest
    first. Walks the date windows backwards; ``complete`` says whether the
    list is exact (the window the last match came from was fully scanned
    within *max_scan*) or a best effort cut short by the scan budget."""
    fid = str(folder_id)
    at_root = fid in ("1", "0", "")
    now = now or datetime.now()
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    state = {"scanned": 0, "complete": True, "oldest": _iso_compact(now)}

    def keep(rows: list[dict[str, Any]]) -> None:
        for r in rows:
            # both range ends are inclusive, so a row on the boundary second
            # can show up in two windows
            if _int(r.get("type")) < _DOC_TYPE_MIN or str(r.get("id")) in seen:
                continue
            seen.add(str(r.get("id")))
            ids, path = _path_ids_and_names(r)
            if not at_root and fid not in ids and str(r.get("parentId")) != fid:
                continue
            dv = r.get("docVersion") or {}
            matches.append({
                "id": str(r.get("id")), "name": str(r.get("name") or r.get("id")),
                "ext": str(dv.get("ext") or "").lower(), "size": _int(dv.get("size")),
                "modified_iso": str(r.get("IDateIso") or ""), "modified": _pretty_date(r.get("IDateIso")),
                "path": path, "owner": str(r.get("ownerName") or ""), "parent_id": str(r.get("parentId") or ""),
            })

    until = now + timedelta(days=1)
    for days in WINDOWS:
        since = now - timedelta(days=days) if days else datetime(1970, 1, 1)
        budget = max_scan - state["scanned"]
        if budget <= 0:
            state["complete"] = False
            break
        rows, exhausted = _scan_window(client, _iso_compact(since), _iso_compact(until), budget=budget)
        state["scanned"] += len(rows)
        keep(rows)
        if not exhausted:
            # the budget ran out inside this window: its rows are unordered,
            # so the list may miss newer files from the same window
            state["oldest"] = min(state["oldest"], min((str(r.get("IDateIso") or "") for r in rows), default=state["oldest"]) or state["oldest"])
            state["complete"] = False
            break
        state["oldest"] = min(state["oldest"], _iso_compact(since))
        until = since
        if len(matches) >= limit or days is None:
            break
    matches.sort(key=lambda m: m["modified_iso"], reverse=True)
    return {
        "folder": {"id": fid, "name": _sord_name(client, fid)},
        "rows": matches[:limit],
        "scanned": state["scanned"],
        "oldest_scanned": _pretty_date(state["oldest"]),
        "complete": state["complete"],
        "total_matches": len(matches),
    }


# --------------------------------------------------------------------------- #
#  preview
# --------------------------------------------------------------------------- #
def _decode_text(data: bytes) -> str:
    """UTF-8 (with or without BOM), UTF-16 (BOM or the tell-tale NUL bytes
    Windows tools leave), else cp1252 - never raises."""
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8", "replace")
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", "replace")
    sample = data[:400]
    if len(sample) >= 4 and sample[1::2].count(0) > len(sample) // 4:
        return data.decode("utf-16-le", "replace")
    if len(sample) >= 4 and sample[0::2].count(0) > len(sample) // 4:
        return data.decode("utf-16-be", "replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", "replace")


def docx_text(data: bytes) -> str:
    """Paragraph text of a .docx - ``word/document.xml`` with the tags
    stripped, one line per paragraph; no python-docx needed."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab/>", "\t", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"')
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _download(client: Any, obj_id: str, max_bytes: int) -> tuple[bytes, str] | None:
    info = client.call("checkoutDoc", {"objId": str(obj_id), "editInfoZ": {"bset": "320", "sordZ": {"bset": "0"}}})
    docs = ((info.get("document") or {}).get("docs")) or [] if isinstance(info, dict) else []
    if not docs or not isinstance(docs[0], dict) or not docs[0].get("url"):
        return None
    ext = str(docs[0].get("ext") or "").lstrip(".").lower()
    body = client.download(docs[0]["url"], max_bytes=max_bytes)
    if isinstance(body, str):
        body = body.encode("utf-8")
    return body, ext


def file_preview(client: Any, doc_id: str | int, *, max_bytes: int = 2 * 1024 * 1024) -> dict[str, Any]:
    """One document, shaped for a viewer: ``kind`` is ``text`` (``text`` +
    ``language``), ``docx`` (extracted ``text``), ``pdf`` / ``image``
    (``b64`` + ``content_type``) or ``binary`` (nothing to show)."""
    res = client.call("checkoutSord", {"objId": str(doc_id), "editInfoZ": {"bset": "1", "sordZ": {"bset": LEAN}}})
    sord = (res.get("sord") or {}) if isinstance(res, dict) else {}
    _, path = _path_ids_and_names(sord)
    dv = sord.get("docVersion") or {}
    out: dict[str, Any] = {
        "id": str(doc_id), "name": str(sord.get("name") or doc_id), "path": path,
        "modified": _pretty_date(sord.get("IDateIso")), "size": _int(dv.get("size")),
        "ext": str(dv.get("ext") or "").lower(), "truncated": False,
    }
    got = _download(client, str(doc_id), max_bytes)
    if got is None:
        return {**out, "kind": "binary", "reason": "no document content"}
    data, ext = got
    out["ext"] = ext or out["ext"]
    out["truncated"] = len(data) >= max_bytes
    ext = out["ext"]
    if ext == "pdf":
        return {**out, "kind": "pdf", "content_type": "application/pdf", "b64": base64.b64encode(data).decode("ascii")}
    if ext in _IMAGE_TYPES:
        return {**out, "kind": "image", "content_type": _IMAGE_TYPES[ext], "b64": base64.b64encode(data).decode("ascii")}
    if ext == "docx":
        try:
            return {**out, "kind": "docx", "language": "plaintext", "text": docx_text(data)}
        except (zipfile.BadZipFile, KeyError) as exc:
            return {**out, "kind": "binary", "reason": f"not a readable .docx ({exc})"}
    if ext == "doc":
        return {**out, "kind": "binary", "reason": "legacy .doc (binary Word) - open it in ELO or Word"}
    if ext in _TEXT_LANG or not ext:
        return {**out, "kind": "text", "language": _TEXT_LANG.get(ext, "plaintext"), "text": _decode_text(data)}
    # unknown extension: show it as text when it looks like text
    if data[:2000].count(0) == 0:
        return {**out, "kind": "text", "language": "plaintext", "text": _decode_text(data)}
    return {**out, "kind": "binary", "reason": f"binary content (.{ext})"}


# --------------------------------------------------------------------------- #
#  "show me the code"
# --------------------------------------------------------------------------- #
_SLICE_START = "// >>> lab-recent slice"
_SLICE_END = "// <<< lab-recent slice"


def _slice(text: str) -> str:
    a, b = text.find(_SLICE_START), text.find(_SLICE_END)
    return text[a:b + len(_SLICE_END)] if a >= 0 and b > a else text


def lab_recent_source() -> dict[str, list[dict[str, str]]]:
    root = get_settings().project_root
    files = [
        ("backend-python/app/lab_recent.py", root / "backend-python" / "app" / "lab_recent.py", None),
        ("catalog/90-lab/09-recent-files.yaml", root / "catalog" / "90-lab" / "09-recent-files.yaml", None),
    ]
    backend = [{"title": t, "code": p.read_text(encoding="utf-8")} for t, p, _ in files if p.exists()]
    js = root / "frontend" / "static" / "app.js"
    frontend = [{"title": "frontend/static/app.js (lab-recent slice)", "code": _slice(js.read_text(encoding="utf-8"))}] if js.exists() else []
    return {"backend": backend, "frontend": frontend}
