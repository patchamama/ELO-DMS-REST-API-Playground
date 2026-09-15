# Building an org chart from ELO's supervisor field

How to draw a "who reports to whom" chart for an ELO repository using only
the ELO IX REST API. Everything below was verified against a live ELO IX
(ix-Contelo, September 2026); the playground's own implementation is
`backend-python/app/lab_perms.py::org_chart()` and
`frontend/static/app.js::wireOrgChart()`.

## 1. Where the hierarchy lives

ELO has **no org-chart RPC** (the paid *ELO HR Personnel File* module draws
one, but from personnel files, not from users). The reporting line is a single
field on every user record, `UserInfo.superiorId`, maintained in the Admin
Console as **Supervisor** (German UI: *Vorgesetzter*). ELO workflows use it for
escalations ("send to superior"), so it is usually populated.

| `UserInfo` field | Meaning | Watch out |
|---|---|---|
| `id` | numeric user id | |
| `name` | login name | |
| `displayName` | display name (from `findFirstUsers` rows) | may equal `name` |
| `superiorId` | **id of the supervisor**. If the user has none it **equals `id`** | "no supervisor" is *not* `null` - compare with `id` |
| `type` | `1` = user, `0` = group | groups also carry `superiorId` (= own id): filter them out |
| `flags` | bit 1 (`AccessC.FLAG_ADMIN`) = main administrator | handy for a badge |
| `groupList` | ids of the user's *direct* groups | for "member of ..." on click |
| `orgUnitIds` | organisational units | a second, optional dimension |
| `userProps` | reserved array, indexed by `UserInfoC.PROP_*` | e-mail / names depending on setup |

Javadoc: "superiorId - ID of the users superior. If the user does not have a
superior, this value is equal to id."

## 2. The two RPCs you need

All IX calls are `POST {base}/rest/IXServicePortIF/<method>` with a JSON body
and a logged-in session cookie (`login` first; the playground's
`elo_playground.connect()` does that).

### a) List users (paginated)

```http
POST {base}/rest/IXServicePortIF/findFirstUsers
{ "findUserInfo": { "onlyUsers": true }, "max": 1000 }
```

```json
{ "result": { "searchId": "...", "moreResults": false,
              "sortedResult": [ { "id": 12, "name": "Felix Unger", "displayName": "Felix Unger", "type": 1 }, ... ] } }
```

While `moreResults` is true call `findNextUsers {searchId, idx, max}`; finish
with `findClose {searchId}`.

### b) Full records in one batch

```http
POST {base}/rest/IXServicePortIF/checkoutUsers
{ "ids": [0, 12, 13, ...], "checkoutUsersZ": { "bset": "513" } }
```

`513` = `CheckoutUsersC.BY_IDS`. One call regardless of how many ids.

```json
[ { "id": 12, "name": "Felix Unger", "type": 1, "flags": 0,
    "superiorId": 9500, "groupList": [9999, 150], "orgUnitIds": [], ... }, ... ]
```

The response envelope is **inconsistent across IX versions**: sometimes a bare
list, sometimes `{"result": [...]}` or `{"users": [...]}`. Accept all three.

Cost on the test box: 18 users, ~60 ms for both calls.

## 3. Algorithm

```python
from collections import defaultdict

def load_people(elo):
    rows = elo.find_all("findFirstUsers", "findNextUsers", "sortedResult",
                        {"findUserInfo": {"onlyUsers": True}, "max": 1000})
    res = elo.call("checkoutUsers", {"ids": [int(r["id"]) for r in rows],
                                     "checkoutUsersZ": {"bset": "513"}})
    detail = res if isinstance(res, list) else res.get("result") or res.get("users") or []
    people = {int(u["id"]): u for u in detail if int(u.get("type", 1)) == 1}
    for u in people.values():
        sup = u.get("superiorId")
        # own id or a deleted user -> no supervisor (root of a tree)
        u["boss"] = sup if sup not in (None, u["id"]) and sup in people else None
    return people

def forest(people):
    reports = defaultdict(list)
    for u in people.values():
        if u["boss"] is not None:
            reports[u["boss"]].append(u["id"])
    roots = [uid for uid, u in people.items() if u["boss"] is None]

    def walk(uid, depth=0, seen=frozenset()):
        if uid in seen:            # ELO does not validate cycles (A boss of B, B boss of A)
            return
        yield depth, people[uid]
        for r in sorted(reports[uid], key=lambda i: people[i]["name"].lower()):
            yield from walk(r, depth + 1, seen | {uid})

    for root in sorted(roots, key=lambda i: (-len(reports[i]), people[i]["name"].lower())):
        yield from walk(root)

for depth, u in forest(load_people(elo)):
    print("  " * depth + u["name"] + ("  (admin)" if int(u.get("flags", 0)) & 1 else ""))
```

Real-data cases the code above handles:

- `superiorId` pointing at a **deleted** user -> treated as a root.
- **Cycles** -> the `seen` set.
- **Several roots** -> it is a forest, not a tree (on the test box:
  `Administrator` and `Bodo Kraft`).
- **Service accounts** (`ELO Service`, `ELOxc Service`) report to
  `Administrator`; decide whether to show them (e.g. hide `internalUser`
  or names matching `Service`).
- Groups are excluded by `type == 1`.

## 4. Drawing it

The playground draws a pure-CSS tree (no library): nested `<ul>/<li>`, roots
side by side, connectors with `::before/::after` - see
`.labperm-orgtree` in `frontend/static/style.css`. Click a node to reveal the
person's groups (`groupList` resolved to names via `findFirstUsers
{onlyGroups: true}`).

For a richer chart feed the same `{id, boss}` pairs to:

- **Mermaid**: `graph TD` with one `boss --> user` edge per person.
- **D3**: `d3.stratify().id(d => d.id).parentId(d => d.boss)` then
  `d3.tree()`.
- **Graphviz**: `digraph { rankdir=TB; "Bodo Kraft" -> "Felix Unger"; ... }`.

The playground endpoint that returns the ready-made JSON (live only):

```http
POST /api/lab/perm-org-chart
{ "credentials": { "base_url": "...", "user": "...", "password": "...", "tls_verify": false } }
```

```json
{ "users":  [ { "id": "12", "name": "Felix Unger", "display_name": "Felix Unger",
                "superior_id": "9500", "group_ids": ["150", "9999"], "is_main_admin": false } ],
  "groups": [ { "id": "150", "name": "Sales", "parent_ids": ["9999"], "member_count": 2,
                "total_members": 2, "everyone": false, "is_main_admin": false } ] }
```

`superior_id` is already normalised (`null` when it is the user's own id or a
missing user).

## 5. Writing the supervisor (populating the chart from code)

```http
POST {base}/rest/IXServicePortIF/checkinUsers
{ "userInfos": [ { ...the full UserInfo from checkoutUsers..., "superiorId": 9500 } ],
  "checkinUsersZ": { "bset": "1" }, "unlockZ": { "bset": "0" } }
```

Rule: `checkoutUsers` -> change **only** `superiorId` -> `checkinUsers` with
the **whole** object. A partial `UserInfo` overwrites the other fields with
empty values (same trap as `checkinSord`). `checkinUsers` needs the
"Edit users" right (`FLAG_EDIT_USERS`) or a main administrator.

## 6. Related structure you can add to the same chart

- **Group nesting**: a *group's* own `groupList` names its **parent** groups
  (a user's `groupList` only holds direct memberships; membership is the
  transitive closure). The playground's "Groups" chart is built from that.
- **Organisational units**: `orgUnitIds` (a user or group belongs to at most
  one directly, more through groups); members only see users of their own
  unit.
- **Everyone-groups** ("Jeder"): every user is a member; park them aside
  instead of drawing an edge from everyone.

## Sources

- UserInfo javadoc: https://forum.elo.com/javadoc/ix/20/de/elo/ix/client/UserInfo.html
- FindUserInfo javadoc: https://forum.elo.com/javadoc/ix/20/de/elo/ix/client/FindUserInfo.html
- Users (Admin Console, "Supervisor" field): https://docs.elo.com/admin/config/23-lts/en-us/user-management/users-and-groups/users.html
- ELO HR Personnel File org chart (the paid, file-based alternative): https://docs.elo.com/solutions/hr-personnel-file/de-de/elo-business-solutions-hr-personnel-file/create-an-organizational-chart.html
