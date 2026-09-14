"""Testing lab - explore who can see what.

Read-only, **live only** (it touches a real ELO, never mock data). Two
primitives back the interactive panel:

* by principal - :func:`list_principals` (groups + users) and
  :func:`group_members` (first N members of a group), then :func:`subtree`
  walks the folder tree from a parent, annotating every child with the
  selected principal's resolved access.
* by folder - :func:`folder_principals` resolves every group/user's access to
  one folder, for the reverse "who can see this" view.

ELO has no "effective permission" RPC. Access is resolved from two primitives
that do exist: a folder's own ``sord.aclItems`` (:func:`folder_acl`, via
``checkoutSord``) and a user's ``UserInfo.groupList`` (via a batched
``checkoutUsers``, since there is no "members of group X" RPC either). See
:func:`resolve_access` for the exact rule.

The FastAPI layer (``/api/lab/*`` in :mod:`app.main`) wraps every call so a
failure becomes ``{"error": "..."}`` instead of a 500 - same convention as
``app.lab_fs``.
"""
from __future__ import annotations

from typing import Any

from .config import get_settings

try:  # the real client; a MockEloClient has the same surface in tests
    from elo_playground import EloError
except Exception:  # pragma: no cover - shared client always importable in practice
    class EloError(Exception):
        ...

# SordC.mbAllIndex - "give me every Sord field", incl. aclItems.
ALL = "449304431574384639"
# CHECKOUT_USERS.BY_IDS.
_CHECKOUT_USERS_BY_IDS = "513"
# ELO object types: folders are < 254, documents are 254..998 (9999 = root).
_DOC_TYPE_MIN = 254
# access bits: 1 R  2 W  4 D  8 edit-rights  16 L  32 P ; 63 = full.
_ACCESS_BITS = ((1, "R"), (2, "W"), (4, "D"), (8, "ER"), (16, "L"), (32, "P"))
_ACCESS_FULL = 63


def _is_folder(row: dict[str, Any]) -> bool:
    try:
        return int(row.get("type", 0)) < _DOC_TYPE_MIN
    except (TypeError, ValueError):
        return True


def _as_rows(res: Any, *fallback_keys: str) -> list[dict[str, Any]]:
    """IX's own envelope is inconsistent across calls - sometimes a bare
    list, sometimes ``{"result": [...]}"`` or ``{"<key>": [...]}"``."""
    if isinstance(res, list):
        return [r for r in res if isinstance(r, dict)]
    if isinstance(res, dict):
        for key in ("result", *fallback_keys):
            value = res.get(key)
            if isinstance(value, list):
                return [r for r in value if isinstance(r, dict)]
    return []


def access_label(bits: int) -> str:
    if bits == _ACCESS_FULL:
        return "full"
    if not bits:
        return "no access"
    return ", ".join(name for bit, name in _ACCESS_BITS if bits & bit)


def resolve_access(
    acl_items: list[dict[str, Any]], principal_ids: set[int], *, is_main_admin: bool = False
) -> dict[str, Any]:
    """A principal - their own id, plus (for a user) every group id they
    belong to - has access when any of those ids appears in *acl_items*.
    Matching entries' ``access`` bits are OR-ed together.

    ``is_main_admin`` short-circuits to full access regardless of aclItems:
    a user or group whose own ``UserInfo.flags`` bit 1 is set bypasses every
    ACL check server-side in real ELO (a UserInfo record - and its main
    administrator flag - exists for groups too, not just users)."""
    if is_main_admin:
        return {"access": True, "bits": _ACCESS_FULL, "label": access_label(_ACCESS_FULL)}
    bits = 0
    for entry in acl_items:
        try:
            entry_id = int(entry.get("id", -1))
        except (TypeError, ValueError):
            continue
        if entry_id in principal_ids:
            bits |= int(entry.get("access", 0) or 0)
    return {"access": bool(bits), "bits": bits, "label": access_label(bits)}


# --------------------------------------------------------------------------- #
#  groups / users
# --------------------------------------------------------------------------- #
def _list_users_of_kind(client: Any, *, only_groups: bool) -> list[dict[str, Any]]:
    selector = {"onlyGroups": True} if only_groups else {"onlyUsers": True}
    rows = client.find_all(
        "findFirstUsers", "findNextUsers", "sortedResult",
        {"findUserInfo": selector, "max": 1000},
    )
    out = [
        {"id": str(r.get("id")), "name": str(r.get("name") or r.get("id")),
         "display_name": str(r.get("displayName") or r.get("name") or r.get("id"))}
        for r in rows if isinstance(r, dict)
    ]
    out.sort(key=lambda r: r["name"].lower())
    return out


def list_groups(client: Any) -> list[dict[str, Any]]:
    return _list_users_of_kind(client, only_groups=True)


def list_users(client: Any) -> list[dict[str, Any]]:
    return _list_users_of_kind(client, only_groups=False)


def _flags_by_id(client: Any, ids: list[int]) -> dict[int, int]:
    """``UserInfo.flags`` for a batch of user/group ids, one ``checkoutUsers``
    call regardless of how many ids (IX treats groups and users uniformly)."""
    ids = [int(i) for i in ids]
    if not ids:
        return {}
    res = client.call("checkoutUsers", {"ids": ids, "checkoutUsersZ": {"bset": _CHECKOUT_USERS_BY_IDS}})
    rows = _as_rows(res, "users")
    return {int(r["id"]): int(r.get("flags", 0) or 0) for r in rows if r.get("id") is not None}


def _all_users_with_groups(client: Any) -> list[dict[str, Any]]:
    """Every user's id/name plus their ``groupList`` and ``is_main_admin`` -
    one ``find_all`` and one *batched* ``checkoutUsers`` call, regardless of
    user count (there is no "members of group X" RPC, so this is the
    cheapest way to answer it)."""
    users = list_users(client)
    if not users:
        return []
    ids = [int(u["id"]) for u in users]
    res = client.call("checkoutUsers", {"ids": ids, "checkoutUsersZ": {"bset": _CHECKOUT_USERS_BY_IDS}})
    detail_by_id = {
        int(d["id"]): d for d in _as_rows(res, "users") if d.get("id") is not None
    }
    out = []
    for u in users:
        detail = detail_by_id.get(int(u["id"]), {})
        group_list = detail.get("groupList") or []
        flags = int(detail.get("flags", 0) or 0)
        out.append({
            **u,
            "group_ids": {int(g) for g in group_list if str(g).lstrip("-").isdigit()},
            "is_main_admin": bool(flags & 1),
        })
    return out


def list_principals(client: Any) -> dict[str, Any]:
    """Groups + users for the left panel - users carry ``group_names`` (for
    the "member of ..." hint) and every principal carries ``is_main_admin``,
    plus who the connected session is (a UI nicety; ELO's own admin ACL
    bypass happens server-side regardless of what this reports)."""
    groups = list_groups(client)
    users = _all_users_with_groups(client)
    group_name_by_id = {int(g["id"]): g["name"] for g in groups}
    users_out = [
        {
            "id": u["id"], "name": u["name"], "display_name": u["display_name"],
            "is_main_admin": u["is_main_admin"],
            "group_names": sorted(group_name_by_id.get(gid, str(gid)) for gid in u["group_ids"]),
        }
        for u in users
    ]
    connected: dict[str, Any] = {"id": None, "name": None, "is_main_admin": False}
    me = client.user or {}
    if me.get("id") is not None:
        flags = _flags_by_id(client, [int(me["id"])])
        connected = {
            "id": str(me["id"]), "name": str(me.get("name") or ""),
            "is_main_admin": bool(flags.get(int(me["id"]), 0) & 1),
        }
    return {"groups": groups, "users": users_out, "connected": connected}


def group_members(client: Any, group_id: str | int, *, preview: int = 10) -> dict[str, Any]:
    gid = int(group_id)
    everyone = _all_users_with_groups(client)
    members = sorted(
        ({"id": u["id"], "name": u["name"], "display_name": u["display_name"]} for u in everyone if gid in u["group_ids"]),
        key=lambda u: u["name"].lower(),
    )
    return {"members": members[: max(0, preview)], "total": len(members)}


# --------------------------------------------------------------------------- #
#  folders
# --------------------------------------------------------------------------- #
def folder_children(client: Any, parent_id: str | int) -> list[dict[str, Any]]:
    """One level of the ELO folder tree, folders only (mirrors
    ``app.lab_fs.list_children``, filtered to folders for this panel)."""
    res = client.call(
        "findFirstSords",
        {
            "findInfo": {"findChildren": {"parentId": str(parent_id), "mainParent": True, "endLevel": 1}},
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
    rows = []
    for s in sords:
        if not isinstance(s, dict) or not _is_folder(s):
            continue
        if s.get("parentId") is not None and str(s.get("parentId")) != str(parent_id):
            continue
        rows.append({
            "id": str(s.get("id")), "name": str(s.get("name") or s.get("id")),
            "child_count": int(s.get("childCount", 0) or 0),
        })
    return rows


def folder_acl(client: Any, folder_id: str | int) -> list[dict[str, Any]]:
    res = client.call(
        "checkoutSord",
        {"objId": str(folder_id), "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}},
    )
    sord = res.get("sord") if isinstance(res, dict) else {}
    return (sord or {}).get("aclItems") or []


def _principal_ids(principal: dict[str, Any], everyone: list[dict[str, Any]] | None = None) -> set[int]:
    ids = {int(principal["id"])}
    if principal.get("kind") == "user" and everyone is not None:
        by_id = {int(u["id"]): u for u in everyone}
        ids |= by_id.get(int(principal["id"]), {}).get("group_ids", set())
    return ids


def subtree(
    client: Any,
    parent_id: str | int,
    principal: dict[str, Any],
    *,
    depth: int = 1,
    max_nodes: int = 300,
) -> dict[str, Any]:
    """Children of *parent_id*, each annotated with the resolved access for
    *principal* (``{"kind": "user"|"group", "id": ...}``), recursed up to
    *depth* levels. One call serves both a manual one-level expand (``depth=1``)
    and the auto-expand-N-levels-on-select interaction (``depth=N``): children
    come back already annotated in a single round trip either way.

    When *principal* is itself a main administrator (its own ``flags`` bit 1),
    every folder resolves to full access without even reading its aclItems -
    matching ELO's real server-side ACL bypass, and skipping a checkoutSord
    call per node."""
    pid = int(principal["id"])
    if principal.get("kind") == "user":
        everyone = _all_users_with_groups(client)
        principal_ids = _principal_ids(principal, everyone)
        is_main_admin = next((u["is_main_admin"] for u in everyone if int(u["id"]) == pid), False)
    else:
        principal_ids = {pid}
        is_main_admin = bool(_flags_by_id(client, [pid]).get(pid, 0) & 1)

    state = {"n": 0, "truncated": False}

    def visit(p: str | int, levels_remaining: int) -> list[dict[str, Any]]:
        rows = []
        for child in folder_children(client, p):
            if state["n"] >= max_nodes:
                state["truncated"] = True
                break
            state["n"] += 1
            if is_main_admin:
                resolved = resolve_access([], principal_ids, is_main_admin=True)
            else:
                resolved = resolve_access(folder_acl(client, child["id"]), principal_ids)
            node = {**child, **resolved, "children": None}
            if levels_remaining > 1 and child["child_count"] and not state["truncated"]:
                node["children"] = visit(child["id"], levels_remaining - 1)
            rows.append(node)
        return rows

    # depth < 1 still returns one level - a selection always shows at least
    # its immediate children.
    rows = visit(parent_id, max(1, depth))
    return {"rows": rows, "truncated": state["truncated"], "is_main_admin": is_main_admin}


def folder_principals(client: Any, folder_id: str | int) -> dict[str, Any]:
    """Every group/user's resolved access to one folder - the reverse "who
    can see this" view. Each group also carries ``member_count`` (from the
    already-fetched user list, no extra RPC). The permission checkbox filter
    and the "groups with access first" ordering the UI applies both run
    client-side over this already-resolved list; no extra round trip."""
    acl_items = folder_acl(client, folder_id)
    everyone = _all_users_with_groups(client)
    groups = list_groups(client)
    group_flags = _flags_by_id(client, [int(g["id"]) for g in groups])

    principals = []
    for g in groups:
        gid = int(g["id"])
        resolved = resolve_access(acl_items, {gid}, is_main_admin=bool(group_flags.get(gid, 0) & 1))
        member_count = sum(1 for u in everyone if gid in u["group_ids"])
        principals.append({"kind": "group", "id": g["id"], "name": g["name"], "member_count": member_count, **resolved})
    for u in everyone:
        uid = int(u["id"])
        resolved = resolve_access(acl_items, {uid} | u["group_ids"], is_main_admin=u["is_main_admin"])
        principals.append({
            "kind": "user", "id": u["id"], "name": u["name"],
            "group_ids": sorted(u["group_ids"]), **resolved,
        })
    principals.sort(key=lambda p: p["name"].lower())
    return {"acl_items": acl_items, "principals": principals}


# --------------------------------------------------------------------------- #
#  "show me the code" - real source, so the panel and its listing never drift
# --------------------------------------------------------------------------- #
_SLICE_START = "// >>> lab-perms slice"
_SLICE_END = "// <<< lab-perms slice"


def _slice(text: str) -> str:
    i = text.find(_SLICE_START)
    j = text.find(_SLICE_END)
    if i == -1 or j == -1 or j < i:
        return text
    return text[i : j + len(_SLICE_END)]


def lab_perms_source() -> dict[str, list[dict[str, str]]]:
    root = get_settings().project_root
    out: dict[str, list[dict[str, str]]] = {"backend": [], "frontend": []}
    be = root / "backend-python" / "app" / "lab_perms.py"
    yml = root / "catalog" / "90-lab" / "08-user-folder-permissions.yaml"
    fe = root / "frontend" / "static" / "app.js"
    if be.is_file():
        out["backend"].append({"title": "backend-python/app/lab_perms.py", "code": be.read_text(encoding="utf-8")})
    if yml.is_file():
        out["backend"].append(
            {"title": "catalog/90-lab/08-user-folder-permissions.yaml", "code": yml.read_text(encoding="utf-8")}
        )
    if fe.is_file():
        out["frontend"].append(
            {"title": "frontend/static/app.js  (permissions panel)", "code": _slice(fe.read_text(encoding="utf-8"))}
        )
    return out
