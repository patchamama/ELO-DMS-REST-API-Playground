"""Testing lab - explore who can see what.

Read-only, **live only** (it touches a real ELO, never mock data). Two
primitives back the interactive panel:

* by principal - :func:`list_principals` (groups + users) and
  :func:`group_members` (first N members of a group), then :func:`subtree`
  walks the folder tree from a parent, annotating every child with the
  selected principal's resolved access.
* by folder - :func:`folder_principals` resolves every group/user's access to
  one folder, for the reverse "who can see this" view, and
  :func:`folder_acl_detail` lists one folder's raw ACL, decoded, for the log.

ELO has no "effective permission" RPC, so :func:`resolve_access` applies the
IX ACL model (``de.elo.ix.client.AclItemC`` / ``AccessC``) itself:

* ``aclItems`` entries carry ``type``: 0 = group, 1 = user, 100 = inherit the
  parent's ACL, 200 = rights for the object's owner. ``access`` is a bitset
  1 R, 2 W, 4 D, 8 E(dit), 16 L(ist), 32 P(ermission); 63 = full.
* a group entry may carry ``andGroups`` - the user must be in the entry's
  group AND every listed group.
* groups nest: a group's own ``UserInfo.groupList`` names its parent groups,
  and a user's ``groupList`` holds only direct memberships, so membership is
  the transitive closure over parent groups.
* ``UserInfo.flags`` bit 1 (``AccessC.FLAG_ADMIN``) on a user OR a group is a
  main administrator - server-side that bypasses every ACL check.

Every folder's ``aclItems`` already comes back on a ``findFirstSords`` row
(with ``sordZ = mbAllIndex``), so walking a level costs one RPC, not one per
folder. The FastAPI layer (``/api/lab/*`` in :mod:`app.main`) wraps every
call so a failure becomes ``{"error": "..."}`` instead of a 500 - same
convention as ``app.lab_fs``.
"""
from __future__ import annotations

from typing import Any

from .config import get_settings

try:  # the real client; a MockEloClient has the same surface in tests
    from elo_playground import EloError
except Exception:  # pragma: no cover - shared client always importable in practice
    class EloError(Exception):
        ...

# SordC.mbAllIndex - "give me every Sord field", incl. aclItems / ownerId.
ALL = "449304431574384639"
# CHECKOUT_USERS.BY_IDS.
_CHECKOUT_USERS_BY_IDS = "513"
# ELO object types: folders are < 254, documents are 254..998 (9999 = root).
_DOC_TYPE_MIN = 254
# AclItemC.TYPE_*
TYPE_GROUP, TYPE_USER, TYPE_KEY, TYPE_INHERIT, TYPE_OWNER, TYPE_PARTICIPANTS = 0, 1, 10, 100, 200, 300
_TYPE_NAMES = {TYPE_GROUP: "group", TYPE_USER: "user", TYPE_KEY: "key", TYPE_INHERIT: "inherit",
               TYPE_OWNER: "owner", TYPE_PARTICIPANTS: "participants"}
# AccessC.LUR_*: 1 R  2 W  4 D  8 E  16 L  32 P ; 63 = full.
_ACCESS_BITS = ((1, "R"), (2, "W"), (4, "D"), (8, "E"), (16, "L"), (32, "P"))
_ACCESS_FULL = 63
# AccessC.FLAG_ADMIN - main administrator.
_FLAG_ADMIN = 1


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_folder(row: dict[str, Any]) -> bool:
    return _int(row.get("type", 0)) < _DOC_TYPE_MIN


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


def _details_by_id(client: Any, ids: list[int]) -> dict[int, dict[str, Any]]:
    """Full ``UserInfo`` for a batch of user/group ids - one ``checkoutUsers``
    call regardless of how many ids (IX treats groups and users uniformly)."""
    ids = [int(i) for i in ids]
    if not ids:
        return {}
    res = client.call("checkoutUsers", {"ids": ids, "checkoutUsersZ": {"bset": _CHECKOUT_USERS_BY_IDS}})
    return {int(r["id"]): r for r in _as_rows(res, "users") if r.get("id") is not None}


def _group_ids_of(detail: dict[str, Any]) -> set[int]:
    return {_int(g, -1) for g in (detail.get("groupList") or []) if _int(g, -1) >= 0}


def _is_admin(detail: dict[str, Any]) -> bool:
    return bool(_int(detail.get("flags", 0)) & _FLAG_ADMIN)


class _Directory:
    """Groups, their parent groups and admin flags - the context every
    access resolution needs. Two RPCs (``findFirstUsers`` + one batched
    ``checkoutUsers``), fetched once per request."""

    def __init__(self, client: Any) -> None:
        self.groups = list_groups(client)
        details = _details_by_id(client, [int(g["id"]) for g in self.groups])
        self.parents: dict[int, set[int]] = {gid: _group_ids_of(d) for gid, d in details.items()}
        self.admin_groups: set[int] = {gid for gid, d in details.items() if _is_admin(d)}
        self.name_of: dict[int, str] = {int(g["id"]): g["name"] for g in self.groups}

    def closure(self, seed: set[int]) -> set[int]:
        """*seed* plus every (transitive) parent group."""
        seen = set(seed)
        stack = list(seed)
        while stack:
            for parent in self.parents.get(stack.pop(), ()):
                if parent not in seen:
                    seen.add(parent)
                    stack.append(parent)
        return seen


def _all_users_with_groups(client: Any) -> list[dict[str, Any]]:
    """Every user's id/name plus their *direct* ``groupList`` and
    ``is_main_admin`` - one ``find_all`` and one batched ``checkoutUsers``."""
    users = list_users(client)
    details = _details_by_id(client, [int(u["id"]) for u in users])
    out = []
    for u in users:
        d = details.get(int(u["id"]), {})
        out.append({**u, "group_ids": _group_ids_of(d), "is_main_admin": _is_admin(d)})
    return out


def list_principals(client: Any) -> dict[str, Any]:
    """Groups + users for the left panel - each user carries ``groups``
    (``[{id, name}]``, direct memberships, for the clickable "member of ..."
    list) and every principal carries ``is_main_admin``, plus who the
    connected session is."""
    directory = _Directory(client)
    users = _all_users_with_groups(client)
    groups_out = [{**g, "is_main_admin": int(g["id"]) in directory.admin_groups} for g in directory.groups]
    users_out = [
        {
            "id": u["id"], "name": u["name"], "display_name": u["display_name"],
            "is_main_admin": u["is_main_admin"],
            "groups": sorted(
                ({"id": str(gid), "name": directory.name_of.get(gid, str(gid))} for gid in u["group_ids"]),
                key=lambda g: g["name"].lower(),
            ),
        }
        for u in users
    ]
    connected: dict[str, Any] = {"id": None, "name": None, "is_main_admin": False}
    me = client.user or {}
    if me.get("id") is not None:
        d = _details_by_id(client, [int(me["id"])]).get(int(me["id"]), {})
        connected = {"id": str(me["id"]), "name": str(me.get("name") or ""), "is_main_admin": _is_admin(d)}
    return {"groups": groups_out, "users": users_out, "connected": connected}


def group_members(client: Any, group_id: str | int, *, preview: int = 10) -> dict[str, Any]:
    """Direct members of a group (users whose own groupList names it)."""
    gid = int(group_id)
    everyone = _all_users_with_groups(client)
    members = sorted(
        ({"id": u["id"], "name": u["name"], "display_name": u["display_name"]} for u in everyone if gid in u["group_ids"]),
        key=lambda u: u["name"].lower(),
    )
    return {"members": members[: max(0, preview)], "total": len(members)}


# --------------------------------------------------------------------------- #
#  the ACL model
# --------------------------------------------------------------------------- #
def _principal_context(client: Any, principal: dict[str, Any], directory: _Directory) -> dict[str, Any]:
    """Everything :func:`resolve_access` needs to know about one principal:
    its kind/id, the transitive set of groups it belongs to (for a group:
    itself plus its parent groups) and whether it is a main administrator."""
    pid = int(principal["id"])
    if principal.get("kind") == "user":
        d = _details_by_id(client, [pid]).get(pid, {})
        return {
            "kind": "user", "id": pid,
            "group_ids": directory.closure(_group_ids_of(d)),
            "is_main_admin": _is_admin(d),
        }
    return {
        "kind": "group", "id": pid,
        "group_ids": directory.closure({pid}),
        "is_main_admin": pid in directory.admin_groups,
    }


def resolve_access(acl_items: list[dict[str, Any]], ctx: dict[str, Any], *, owner_id: int | None = None) -> dict[str, Any]:
    """Apply the IX ACL model for one principal (see the module docstring).

    Matching entries' ``access`` bits are OR-ed. ``conditional`` is set when
    a *group* principal only matches through an ``andGroups`` entry that its
    members may or may not satisfy individually."""
    if ctx.get("is_main_admin"):
        return {"access": True, "bits": _ACCESS_FULL, "label": access_label(_ACCESS_FULL), "conditional": False}
    bits = 0
    conditional = False
    group_ids: set[int] = ctx.get("group_ids") or set()
    for entry in acl_items:
        etype = _int(entry.get("type", TYPE_GROUP))
        eid = _int(entry.get("id", -1), -1)
        access = _int(entry.get("access", 0))
        if etype == TYPE_USER:
            if ctx["kind"] == "user" and eid == ctx["id"]:
                bits |= access
        elif etype == TYPE_GROUP:
            if eid not in group_ids:
                continue
            ands = {_int(a.get("id"), -1) for a in (entry.get("andGroups") or []) if isinstance(a, dict)}
            if ands and not ands <= group_ids:
                if ctx["kind"] == "group":
                    conditional = True
                continue
            bits |= access
        elif etype == TYPE_OWNER:
            if ctx["kind"] == "user" and owner_id is not None and int(owner_id) == ctx["id"]:
                bits |= access
        # TYPE_INHERIT is resolved structurally by _effective_acl(); TYPE_KEY /
        # TYPE_PARTICIPANTS (workflows) never grant folder access here.
    return {"access": bool(bits), "bits": bits, "label": access_label(bits), "conditional": conditional}


def _has_inherit(acl_items: list[dict[str, Any]]) -> bool:
    return any(_int(e.get("type", TYPE_GROUP)) == TYPE_INHERIT for e in acl_items)


def _effective_acl(acl_items: list[dict[str, Any]], parent_effective: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """An ACL with a TYPE_INHERIT marker takes the parent's effective ACL
    on top of its own entries."""
    if not _has_inherit(acl_items):
        return acl_items
    own = [e for e in acl_items if _int(e.get("type", TYPE_GROUP)) != TYPE_INHERIT]
    return own + list(parent_effective or [])


# SordC.mbAllIndex does not include the reference paths; bit 59 is
# SordC.mbRefPaths (verified against IX: refPaths comes back only with it).
_ALL_WITH_PATHS = str(int(ALL) | (1 << 59))


def _sord(client: Any, obj_id: str | int) -> dict[str, Any]:
    res = client.call(
        "checkoutSord",
        {"objId": str(obj_id), "editInfoZ": {"bset": "1", "sordZ": {"bset": _ALL_WITH_PATHS}}},
    )
    return (res.get("sord") or {}) if isinstance(res, dict) else {}


def _path_of(sord: dict[str, Any]) -> str:
    """``Administration / Business Solutions`` - the first ``refPaths`` entry
    (parents below the repository root, the root itself is not listed) plus
    the folder's own name; falls back to the bare name."""
    name = str(sord.get("name") or sord.get("id") or "")
    paths = sord.get("refPaths") or []
    first = paths[0] if paths and isinstance(paths[0], dict) else {}
    parts = [str(p.get("name") or p.get("id")) for p in (first.get("path") or []) if isinstance(p, dict)]
    return " / ".join(parts + [name]) if parts else name


def effective_acl_of(
    client: Any, folder_id: str | int, *, cache: dict[str, list] | None = None, hops: int = 12,
    sord: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """A folder's effective ACL, following TYPE_INHERIT up the parent chain
    (bounded; ELO's root has no parent). Pass *sord* when the folder was
    already checked out, to save the round trip."""
    cache = cache if cache is not None else {}
    key = str(folder_id)
    if key in cache:
        return cache[key]
    sord = sord if sord is not None else _sord(client, folder_id)
    items = list(sord.get("aclItems") or [])
    parent_eff = None
    parent_id = sord.get("parentId")
    if _has_inherit(items) and hops > 0 and parent_id not in (None, "", 0, "0") and str(parent_id) != key:
        parent_eff = effective_acl_of(client, parent_id, cache=cache, hops=hops - 1)
    cache[key] = _effective_acl(items, parent_eff)
    return cache[key]


def folder_children(client: Any, parent_id: str | int) -> list[dict[str, Any]]:
    """One level of the ELO folder tree, folders only, each row carrying its
    own ``acl_items`` / ``owner_id`` (already on the ``findFirstSords`` row
    with ``sordZ = mbAllIndex`` - no per-folder checkoutSord needed)."""
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
            "child_count": _int(s.get("childCount", 0)),
            "acl_items": list(s.get("aclItems") or []),
            "owner_id": _int(s.get("ownerId"), -1) if s.get("ownerId") is not None else None,
        })
    return rows


def _acl_key(entry: dict[str, Any]) -> tuple:
    ands = tuple(sorted(_int(a.get("id"), -1) for a in (entry.get("andGroups") or []) if isinstance(a, dict)))
    return (_int(entry.get("type", TYPE_GROUP)), _int(entry.get("id", -1), -1), ands)


def _norm_acl(items: list[dict[str, Any]]) -> dict[tuple, int]:
    """``{(type, id, andGroups): access}`` - the comparable shape of an ACL."""
    out: dict[tuple, int] = {}
    for e in items:
        if _int(e.get("type", TYPE_GROUP)) == TYPE_INHERIT:
            continue
        out[_acl_key(e)] = out.get(_acl_key(e), 0) | _int(e.get("access", 0))
    return out


def acl_diff(child: list[dict[str, Any]], parent: list[dict[str, Any]] | None) -> dict[str, Any]:
    """How *child*'s effective ACL departs from *parent*'s: entries only in the
    child (``added``), only in the parent (``removed``) and present in both
    with different access (``changed``). ELO copies the parent's ACL onto a
    new child, so any difference is a deliberate "special permission"."""
    c, p = _norm_acl(child), _norm_acl(parent or [])
    by_key_c = {_acl_key(e): e for e in child if _int(e.get("type", TYPE_GROUP)) != TYPE_INHERIT}
    by_key_p = {_acl_key(e): e for e in (parent or []) if _int(e.get("type", TYPE_GROUP)) != TYPE_INHERIT}
    added = [by_key_c[k] for k in c if k not in p]
    removed = [by_key_p[k] for k in p if k not in c]
    changed = [{"entry": by_key_c[k], "parent_access": p[k], "access": c[k]} for k in c if k in p and c[k] != p[k]]
    return {"differs": bool(added or removed or changed), "added": added, "removed": removed, "changed": changed}


def _exclusive_to(
    eff: list[dict[str, Any]], ctx: dict[str, Any], directory: _Directory,
    admin_users: set[int], user_closure: dict[int, set[int]], owner_id: int | None,
) -> bool:
    """True when *ctx* has access and nobody else does - ignoring main
    administrators (users or groups), and, for a group principal, its own
    members and sub-groups (they hold the group's access, not their own)."""
    for e in eff:
        etype = _int(e.get("type", TYPE_GROUP))
        eid = _int(e.get("id", -1), -1)
        if _int(e.get("access", 0)) <= 0:
            continue
        if etype == TYPE_GROUP:
            if eid in directory.admin_groups:
                continue
            if ctx["kind"] == "group" and (eid == ctx["id"] or ctx["id"] in directory.closure({eid})):
                continue
            return False
        if etype == TYPE_USER:
            if eid in admin_users:
                continue
            if ctx["kind"] == "user" and eid == ctx["id"]:
                continue
            if ctx["kind"] == "group" and ctx["id"] in user_closure.get(eid, set()):
                continue
            return False
        if etype == TYPE_OWNER and owner_id is not None:
            if owner_id in admin_users:
                continue
            if ctx["kind"] == "user" and owner_id == ctx["id"]:
                continue
            if ctx["kind"] == "group" and ctx["id"] in user_closure.get(owner_id, set()):
                continue
            return False
    return True


def subtree(
    client: Any,
    parent_id: str | int,
    principal: dict[str, Any],
    *,
    depth: int = 1,
    max_nodes: int = 1500,
) -> dict[str, Any]:
    """Children of *parent_id*, each annotated with the resolved access for
    *principal* (``{"kind": "user"|"group", "id": ...}``), recursed up to
    *depth* levels; one findFirstSords per level. Per node it also says whether
    any *fetched* descendant is accessible (``descendant_access`` - a UI can
    keep an inaccessible folder visible as the path to accessible ones),
    whether the principal is the only non-administrator with access
    (``exclusive`` / ``descendant_exclusive``) and whether the folder's ACL
    departs from its parent's (``acl_differs``)."""
    directory = _Directory(client)
    ctx = _principal_context(client, principal, directory)
    users = _all_users_with_groups(client)
    admin_users = {int(u["id"]) for u in users if u["is_main_admin"]}
    user_closure = {int(u["id"]): directory.closure(u["group_ids"]) for u in users}
    state = {"n": 0, "truncated": False}
    acl_cache: dict[str, list] = {}

    def visit(p: str | int, levels_remaining: int, p_eff: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for child in folder_children(client, p):
            if state["n"] >= max_nodes:
                state["truncated"] = True
                break
            state["n"] += 1
            eff = _effective_acl(child["acl_items"], p_eff)
            acl_cache[child["id"]] = eff
            resolved = resolve_access(eff, ctx, owner_id=child["owner_id"])
            exclusive = bool(resolved["access"]) and not ctx["is_main_admin"] and _exclusive_to(
                eff, ctx, directory, admin_users, user_closure, child["owner_id"]
            )
            node = {
                "id": child["id"], "name": child["name"], "child_count": child["child_count"],
                **resolved,
                "exclusive": exclusive, "descendant_exclusive": False,
                "acl_differs": _norm_acl(eff) != _norm_acl(p_eff),
                "descendant_access": False, "children": None,
            }
            if levels_remaining > 1 and child["child_count"] and not state["truncated"]:
                node["children"] = visit(child["id"], levels_remaining - 1, eff)
                node["descendant_access"] = any(c["access"] or c["descendant_access"] for c in node["children"])
                node["descendant_exclusive"] = any(c["exclusive"] or c["descendant_exclusive"] for c in node["children"])
            rows.append(node)
        # accessible folders first, then those leading to accessible ones,
        # then the rest - alphabetical within each tier.
        rows.sort(key=lambda r: (not r["access"], not r["descendant_access"], r["name"].lower()))
        return rows

    # the starting parent's effective ACL, once: the baseline every first-level
    # child is compared against (and inherited from, if it says so)
    rows = visit(parent_id, max(1, depth), effective_acl_of(client, parent_id, cache=acl_cache))
    return {"rows": rows, "truncated": state["truncated"], "is_main_admin": ctx["is_main_admin"]}


def special_folders(client: Any, parent_id: str | int, *, depth: int = 3, max_nodes: int = 1500) -> dict[str, Any]:
    """Folders whose effective ACL departs from their parent's - ELO copies
    the parent's ACL onto a new child, so a difference means someone set
    special permissions on purpose. Each node carries the diff counts and
    whether any fetched descendant is special (to keep the path visible)."""
    state = {"n": 0, "truncated": False}
    acl_cache: dict[str, list] = {}
    name_of: dict[str, str] = {}

    def visit(p: str | int, levels_remaining: int, p_eff: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for child in folder_children(client, p):
            if state["n"] >= max_nodes:
                state["truncated"] = True
                break
            state["n"] += 1
            eff = _effective_acl(child["acl_items"], p_eff)
            acl_cache[child["id"]] = eff
            diff = acl_diff(eff, p_eff)
            node = {
                "id": child["id"], "name": child["name"], "child_count": child["child_count"],
                "differs": diff["differs"], "inherits_marker": _has_inherit(child["acl_items"]),
                "added": len(diff["added"]), "removed": len(diff["removed"]), "changed": len(diff["changed"]),
                "added_names": [str(e.get("name") or e.get("id")) for e in diff["added"]][:6],
                "descendant_differs": False, "children": None,
            }
            if levels_remaining > 1 and child["child_count"] and not state["truncated"]:
                node["children"] = visit(child["id"], levels_remaining - 1, eff)
                node["descendant_differs"] = any(c["differs"] or c["descendant_differs"] for c in node["children"])
            rows.append(node)
        rows.sort(key=lambda r: (not r["differs"], not r["descendant_differs"], r["name"].lower()))
        return rows

    parent_sord = _sord(client, parent_id)
    name_of[str(parent_id)] = str(parent_sord.get("name") or parent_id)
    own = list(parent_sord.get("aclItems") or [])
    grand_id = parent_sord.get("parentId")
    grand_eff = None
    if _has_inherit(own) and grand_id not in (None, "", 0, "0") and str(grand_id) != str(parent_id):
        grand_eff = effective_acl_of(client, grand_id, cache=acl_cache)
    rows = visit(parent_id, max(1, depth), _effective_acl(own, grand_eff))
    return {"parent": {"id": str(parent_id), "name": name_of[str(parent_id)]}, "rows": rows, "truncated": state["truncated"]}


def folder_principals(client: Any, folder_id: str | int) -> dict[str, Any]:
    """Every group/user's resolved access to one folder - the reverse "who
    can see this" view. Groups carry ``member_count`` (direct members);
    users carry their direct ``group_ids``. Filtering/ordering is client-side."""
    directory = _Directory(client)
    sord = _sord(client, folder_id)
    own = list(sord.get("aclItems") or [])
    parent_id = sord.get("parentId")
    parent_eff = None
    if _has_inherit(own) and parent_id not in (None, "", 0, "0"):
        parent_eff = effective_acl_of(client, parent_id)
    acl = _effective_acl(own, parent_eff)
    owner_id = _int(sord.get("ownerId"), -1) if sord.get("ownerId") is not None else None
    everyone = _all_users_with_groups(client)

    principals = []
    for g in directory.groups:
        gid = int(g["id"])
        ctx = {"kind": "group", "id": gid, "group_ids": directory.closure({gid}), "is_main_admin": gid in directory.admin_groups}
        resolved = resolve_access(acl, ctx, owner_id=owner_id)
        member_count = sum(1 for u in everyone if gid in u["group_ids"])
        principals.append({"kind": "group", "id": g["id"], "name": g["name"], "member_count": member_count,
                           "is_main_admin": ctx["is_main_admin"], **resolved})
    for u in everyone:
        uid = int(u["id"])
        ctx = {"kind": "user", "id": uid, "group_ids": directory.closure(u["group_ids"]), "is_main_admin": u["is_main_admin"]}
        resolved = resolve_access(acl, ctx, owner_id=owner_id)
        principals.append({"kind": "user", "id": u["id"], "name": u["name"], "group_ids": sorted(u["group_ids"]),
                           "is_main_admin": u["is_main_admin"], **resolved})
    principals.sort(key=lambda p: p["name"].lower())
    return {"folder": {"id": str(folder_id), "name": str(sord.get("name") or folder_id), "path": _path_of(sord)},
            "acl_items": acl, "principals": principals}


def folder_acl_detail(client: Any, folder_id: str | int, principal: dict[str, Any] | None = None) -> dict[str, Any]:
    """One folder's ACL, decoded for humans: every entry with its kind, name,
    access bits and label, plus (optionally) how *principal* resolves
    against it - the panel prints this in its log when a folder is clicked."""
    directory = _Directory(client)
    sord = _sord(client, folder_id)
    own = list(sord.get("aclItems") or [])
    cache: dict[str, list] = {}
    parent_id = sord.get("parentId")
    parent_sord = None
    parent_eff = None
    if parent_id not in (None, "", 0, "0") and str(parent_id) != str(folder_id):
        # one checkout of the parent serves both its name and its ACL
        parent_sord = _sord(client, parent_id)
        parent_eff = effective_acl_of(client, parent_id, cache=cache, sord=parent_sord)
    eff = _effective_acl(own, parent_eff)
    owner_id = _int(sord.get("ownerId"), -1) if sord.get("ownerId") is not None else None

    def decode(e: dict[str, Any]) -> dict[str, Any]:
        etype = _int(e.get("type", TYPE_GROUP))
        return {
            "type": etype,
            "kind": _TYPE_NAMES.get(etype, str(etype)),
            "id": str(e.get("id", "")),
            "name": str(e.get("name") or directory.name_of.get(_int(e.get("id"), -1), e.get("id", ""))),
            "access": _int(e.get("access", 0)),
            "label": access_label(_int(e.get("access", 0))),
            "and_groups": [str(a.get("name") or a.get("id")) for a in (e.get("andGroups") or []) if isinstance(a, dict)],
        }

    # how this ACL departs from the parent's (ELO copies it down on creation,
    # so any difference is a deliberate special permission)
    parent_name = None
    diff_out = None
    if parent_sord is not None:
        parent_name = str(parent_sord.get("name") or parent_id)
        d = acl_diff(eff, parent_eff)
        diff_out = {
            "differs": d["differs"],
            "added": [decode(e) for e in d["added"]],
            "removed": [decode(e) for e in d["removed"]],
            "changed": [{**decode(c["entry"]), "parent_access": c["parent_access"], "parent_label": access_label(c["parent_access"])} for c in d["changed"]],
        }
    out: dict[str, Any] = {
        "folder": {"id": str(folder_id), "name": str(sord.get("name") or folder_id), "path": _path_of(sord),
                   "parent_id": str(parent_id) if parent_id is not None else None, "parent_name": parent_name},
        "owner": {"id": str(owner_id) if owner_id is not None else None, "name": str(sord.get("ownerName") or "")},
        "inherits": _has_inherit(own),
        "entries": [decode(e) for e in eff],
        "diff": diff_out,
    }
    if principal:
        ctx = _principal_context(client, principal, directory)
        out["principal"] = {
            "kind": ctx["kind"], "id": str(ctx["id"]),
            "group_ids": sorted(ctx["group_ids"]),
            "group_names": sorted(directory.name_of.get(g, str(g)) for g in ctx["group_ids"]),
            "is_main_admin": ctx["is_main_admin"],
            **resolve_access(eff, ctx, owner_id=owner_id),
        }
    return out


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
