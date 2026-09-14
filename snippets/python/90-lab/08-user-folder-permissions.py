# import the shared client:  from elo_playground import connect
# topic:    Check user/folder permissions
# category: Testing lab
# id:       lab.user-folder-permissions

import os
from elo_playground import connect, EloError

# --- local ELO test box (override with ELOPG_* env vars or a .env) ---
ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url
ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user
ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password

elo = connect(base_url=ELO_BASE_URL, user=ELO_USER, password=ELO_PASS)
ALL = "449304431574384639"  # SordC.mbAllIndex - every Sord field, incl. aclItems

# access bits: 1 R  2 W  4 D  8 edit-rights  16 L  32 P ; 63 = full
_ACCESS_BITS = [(1, "R"), (2, "W"), (4, "D"), (8, "ER"), (16, "L"), (32, "P")]


def access_label(bits):
    if bits == 63:
        return "full"
    if not bits:
        return "no access"
    return ", ".join(name for bit, name in _ACCESS_BITS if bits & bit)


def resolve_access(acl_items, principal_ids):
    """A principal - their own id, plus (for a user) every group id they
    belong to - has access when any of those ids appears in aclItems.
    Matching entries' access bits are OR-ed together."""
    bits = 0
    for entry in acl_items:
        if int(entry.get("id", -1)) in principal_ids:
            bits |= int(entry.get("access", 0))
    return bits


def folder_children(parent_id):
    """One level of the ELO folder tree, folders only (mirrors the
    Testing lab filesystem panel's list_children)."""
    res = elo.call("findFirstSords", {
        "findInfo": {"findChildren": {"parentId": str(parent_id), "mainParent": True, "endLevel": 1}},
        "max": 1000,
        "sordZ": {"bset": ALL},
    })
    rows = [s for s in (res.get("sords") or []) if int(s.get("type", 0)) < 254]
    if res.get("searchId"):
        elo.call("findClose", {"searchId": res["searchId"]})
    return rows


def folder_acl(folder_id):
    sord = elo.call("checkoutSord", {
        "objId": str(folder_id), "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}},
    })["sord"]
    return sord.get("aclItems") or []


# groups and users - the same findFirstUsers/findNextUsers loop as catalog
# "List users (and groups)"; onlyGroups vs onlyUsers selects which.
groups = elo.find_all("findFirstUsers", "findNextUsers", "sortedResult", {"findUserInfo": {"onlyGroups": True}, "max": 200})
users = elo.find_all("findFirstUsers", "findNextUsers", "sortedResult", {"findUserInfo": {"onlyUsers": True}, "max": 200})
print(f"{len(groups)} groups, {len(users)} users")

# One batched checkoutUsers call resolves every user's groupList at once.
detail = elo.call("checkoutUsers", {
    "ids": [u["id"] for u in users],
    "checkoutUsersZ": {"bset": "513"},   # CHECKOUT_USERS.BY_IDS
})
detail = detail if isinstance(detail, list) else (detail.get("result") or detail.get("users") or [])
group_lists = {int(u["id"]): u.get("groupList") or [] for u in detail}

# Pick the first group as the demo principal - the interactive panel lets
# you click any group or user in the left-hand list instead.
principal = groups[0]
principal_ids = {int(principal["id"])}
members = [u for u in users if int(principal["id"]) in group_lists.get(int(u["id"]), [])]
print(f"\n{principal['name']!r} members ({len(members)}):", [u["name"] for u in members[:10]])

# Walk the folder tree from the repository root, printing each folder's
# permission label for the chosen principal - exactly what the interactive
# panel's right-hand tree renders (greyed out + struck through at "no access").
def walk(parent_id, indent=0):
    for row in folder_children(parent_id):
        bits = resolve_access(folder_acl(row["id"]), principal_ids)
        print("  " * indent + f"{row['name']} ({access_label(bits)})")
        if int(row.get("childCount", 0)):
            walk(row["id"], indent + 1)


print(f"\nfolders visible to {principal['name']!r}:")
try:
    walk("1")
except EloError as exc:
    print("could not read the tree:", exc)

elo.close()
