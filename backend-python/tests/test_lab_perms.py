"""Unit tests for app.lab_perms (the Testing lab user/folder permissions panel).

The real ELO client is stood in for by MockEloClient, which has the same
surface (call / find_all). A list-valued mock entry is consumed one item per
*call*, in call order - so each test's mock is shaped to match the exact RPC
call sequence the function under test actually makes (see each function's
docstring in app.lab_perms for that sequence).
"""
from elo_playground import MockEloClient

from app import lab_perms


# --------------------------------------------------------------------------- #
def test_access_label_covers_full_none_and_partial():
    assert lab_perms.access_label(63) == "full"
    assert lab_perms.access_label(0) == "no access"
    assert lab_perms.access_label(1 | 16) == "R, L"


def test_resolve_access_unions_matching_acl_entries():
    acl = [
        {"id": 150, "access": 3},   # Sales-Team: R + W
        {"id": 9999, "access": 1},  # Jeder: R
    ]
    # a user in both Sales-Team (150) and Jeder (9999) gets the union: R + W
    res = lab_perms.resolve_access(acl, {150, 9999})
    assert res == {"access": True, "bits": 3, "label": "R, W"}
    # a principal matching nothing gets no access
    assert lab_perms.resolve_access(acl, {9998}) == {"access": False, "bits": 0, "label": "no access"}


def test_resolve_access_is_main_admin_bypasses_the_acl_entirely():
    # a real ELO bug this guards against: a main-administrator principal (its
    # own UserInfo.flags bit 1) must see everything, even an ACL that grants
    # it nothing at all.
    acl = [{"id": 9999, "access": 1}]  # no entry for our principal
    res = lab_perms.resolve_access(acl, {12345}, is_main_admin=True)
    assert res == {"access": True, "bits": 63, "label": "full"}


# --------------------------------------------------------------------------- #
def test_list_groups_and_users_are_sorted_by_name():
    # list_groups() then list_users() - two ordered findFirstUsers calls.
    client = MockEloClient({
        "findFirstUsers": [
            {"moreResults": False, "searchId": "(G)", "sortedResult": [
                {"id": 9999, "name": "Jeder", "type": 0, "displayName": "Jeder"},
                {"id": 150, "name": "Sales-Team", "type": 0, "displayName": "Sales-Team"},
            ]},
            {"moreResults": False, "searchId": "(U)", "sortedResult": [
                {"id": 0, "name": "Administrator", "type": 1, "displayName": "Administrator"},
                {"id": 12, "name": "m.muster", "type": 1, "displayName": "Max Muster"},
                {"id": 13, "name": "a.gruber", "type": 1, "displayName": "Anna Gruber"},
            ]},
        ],
        "findClose": {},
    })
    assert [g["name"] for g in lab_perms.list_groups(client)] == ["Jeder", "Sales-Team"]
    assert [u["name"] for u in lab_perms.list_users(client)] == ["a.gruber", "Administrator", "m.muster"]


def _users_only_client() -> MockEloClient:
    # group_members() only ever calls list_users() (never list_groups()), so
    # a single non-list findFirstUsers entry (always the users page) is enough.
    return MockEloClient({
        "findFirstUsers": {
            "moreResults": False, "searchId": "(U)",
            "sortedResult": [
                {"id": 0, "name": "Administrator", "type": 1, "displayName": "Administrator"},
                {"id": 12, "name": "m.muster", "type": 1, "displayName": "Max Muster"},
                {"id": 13, "name": "a.gruber", "type": 1, "displayName": "Anna Gruber"},
            ],
        },
        "checkoutUsers": {"result": [
            {"id": 0, "name": "Administrator", "flags": 2013265919, "groupList": [9998, 9999]},
            {"id": 12, "name": "m.muster", "flags": 536870912, "groupList": [9999, 150]},
            {"id": 13, "name": "a.gruber", "flags": 536870912, "groupList": [9999]},
        ]},
        "findClose": {},
    })


def test_group_members_resolves_membership_via_one_batched_checkout():
    res = lab_perms.group_members(_users_only_client(), 150, preview=10)
    assert res["total"] == 1
    assert [m["name"] for m in res["members"]] == ["m.muster"]


def test_group_members_preview_is_capped_but_total_is_not():
    res = lab_perms.group_members(_users_only_client(), 9999, preview=1)  # everyone is in "Jeder"
    assert res["total"] == 3
    assert len(res["members"]) == 1


def test_list_principals_reports_each_users_group_names_and_admin_flag():
    # list_groups() [findFirstUsers#1] then _all_users_with_groups() ->
    # list_users() [findFirstUsers#2] + checkoutUsers#1, then the connected
    # user's own flags via checkoutUsers#2.
    client = MockEloClient({
        "findFirstUsers": [
            {"moreResults": False, "sortedResult": [
                {"id": 9999, "name": "Jeder", "type": 0, "displayName": "Jeder"},
                {"id": 150, "name": "Sales-Team", "type": 0, "displayName": "Sales-Team"},
            ]},
            {"moreResults": False, "sortedResult": [
                {"id": 0, "name": "Administrator", "type": 1, "displayName": "Administrator"},
                {"id": 12, "name": "m.muster", "type": 1, "displayName": "Max Muster"},
            ]},
        ],
        "checkoutUsers": [
            {"result": [
                {"id": 0, "name": "Administrator", "flags": 1, "groupList": [9999]},
                {"id": 12, "name": "m.muster", "flags": 0, "groupList": [9999, 150]},
            ]},
            {"result": [{"id": 0, "name": "Administrator", "flags": 1}]},
        ],
        "findClose": {},
    })
    client.user = {"id": 0, "name": "Administrator"}
    res = lab_perms.list_principals(client)
    by_name = {u["name"]: u for u in res["users"]}
    assert by_name["m.muster"]["group_names"] == ["Jeder", "Sales-Team"]
    assert by_name["Administrator"]["is_main_admin"] is True
    assert by_name["m.muster"]["is_main_admin"] is False
    assert res["connected"] == {"id": "0", "name": "Administrator", "is_main_admin": True}


# --------------------------------------------------------------------------- #
def test_subtree_depth_one_annotates_children_without_recursing():
    # subtree() first checks the principal's own flags (one checkoutUsers
    # call for a group principal), then depth=1 never recurses: one
    # findFirstSords call (root) and one checkoutSord call per root child.
    client = MockEloClient({
        "checkoutUsers": {"result": [{"id": 150, "name": "Sales-Team", "flags": 0}]},
        "findFirstSords": {"searchId": "(root)", "sords": [
            {"id": 200, "parentId": 1, "name": "Sales", "type": 1, "childCount": 1},
            {"id": 201, "parentId": 1, "name": "Finance", "type": 1, "childCount": 0},
        ]},
        "checkoutSord": [
            {"sord": {"id": 200, "name": "Sales", "aclItems": [{"id": 150, "type": 0, "access": 3}]}},
            {"sord": {"id": 201, "name": "Finance", "aclItems": [{"id": 150, "type": 0, "access": 16}]}},
        ],
        "findClose": {},
    })
    res = lab_perms.subtree(client, "1", {"kind": "group", "id": "150"}, depth=1)
    assert res["truncated"] is False
    assert res["is_main_admin"] is False
    by_id = {r["id"]: r for r in res["rows"]}
    assert by_id["200"]["label"] == "R, W" and by_id["200"]["children"] is None
    assert by_id["201"]["label"] == "L"


def test_subtree_depth_two_recurses_one_more_level():
    # depth=2 recurses into 200 (child_count=1) but not into 201 (child_count=0):
    # findFirstSords [root, sales], checkoutSord [200, 210, 201] in that order.
    client = MockEloClient({
        "checkoutUsers": {"result": [{"id": 150, "name": "Sales-Team", "flags": 0}]},
        "findFirstSords": [
            {"searchId": "(root)", "sords": [
                {"id": 200, "parentId": 1, "name": "Sales", "type": 1, "childCount": 1},
                {"id": 201, "parentId": 1, "name": "Finance", "type": 1, "childCount": 0},
            ]},
            {"searchId": "(sales)", "sords": [
                {"id": 210, "parentId": 200, "name": "Contracts", "type": 1, "childCount": 0},
            ]},
        ],
        "checkoutSord": [
            {"sord": {"id": 200, "name": "Sales", "aclItems": [{"id": 150, "type": 0, "access": 3}]}},
            {"sord": {"id": 210, "name": "Contracts", "aclItems": [{"id": 9998, "type": 0, "access": 63}]}},
            {"sord": {"id": 201, "name": "Finance", "aclItems": [{"id": 150, "type": 0, "access": 16}]}},
        ],
        "findClose": {},
    })
    res = lab_perms.subtree(client, "1", {"kind": "group", "id": "150"}, depth=2)
    sales = next(r for r in res["rows"] if r["id"] == "200")
    assert sales["children"] is not None
    contracts = sales["children"][0]
    assert contracts["id"] == "210" and contracts["access"] is False  # group 150 not in its ACL


def test_subtree_honours_the_node_cap():
    # the cap trips before the second root-level child is even visited.
    client = MockEloClient({
        "checkoutUsers": {"result": [{"id": 150, "name": "Sales-Team", "flags": 0}]},
        "findFirstSords": {"searchId": "(root)", "sords": [
            {"id": 200, "parentId": 1, "name": "Sales", "type": 1, "childCount": 1},
            {"id": 201, "parentId": 1, "name": "Finance", "type": 1, "childCount": 0},
        ]},
        "checkoutSord": {"sord": {"id": 200, "name": "Sales", "aclItems": []}},
        "findClose": {},
    })
    res = lab_perms.subtree(client, "1", {"kind": "group", "id": "150"}, depth=1, max_nodes=1)
    assert res["truncated"] is True
    assert len(res["rows"]) == 1


def test_subtree_grants_full_access_when_the_principal_is_a_main_administrator():
    # real-world bug this guards against: a group (here "Administratoren")
    # can itself carry the main-administrator flag on its own UserInfo
    # record, which bypasses every ACL check server-side - deliberately no
    # checkoutSord mock entry here, proving it is never even called.
    client = MockEloClient({
        "checkoutUsers": {"result": [{"id": 9998, "name": "Administratoren", "flags": 1}]},
        "findFirstSords": {"searchId": "(root)", "sords": [
            {"id": 200, "parentId": 1, "name": "Sales", "type": 1, "childCount": 0},
        ]},
        "findClose": {},
    })
    res = lab_perms.subtree(client, "1", {"kind": "group", "id": "9998"}, depth=1)
    assert res["is_main_admin"] is True
    assert res["rows"][0]["label"] == "full" and res["rows"][0]["bits"] == 63


# --------------------------------------------------------------------------- #
def test_folder_principals_resolves_every_group_and_user():
    # folder_acl (checkoutSord#1), then _all_users_with_groups (findFirstUsers
    # #1[users] + checkoutUsers#1[users]), then list_groups (findFirstUsers
    # #2[groups]), then _flags_by_id for groups (checkoutUsers#2[groups]).
    client = MockEloClient({
        "checkoutSord": {"sord": {"id": 200, "name": "Sales", "aclItems": [{"id": 150, "type": 0, "access": 3}]}},
        "findFirstUsers": [
            {"moreResults": False, "sortedResult": [
                {"id": 0, "name": "Administrator", "type": 1, "displayName": "Administrator"},
                {"id": 12, "name": "m.muster", "type": 1, "displayName": "Max Muster"},
                {"id": 13, "name": "a.gruber", "type": 1, "displayName": "Anna Gruber"},
            ]},
            {"moreResults": False, "sortedResult": [
                {"id": 9999, "name": "Jeder", "type": 0, "displayName": "Jeder"},
                {"id": 150, "name": "Sales-Team", "type": 0, "displayName": "Sales-Team"},
            ]},
        ],
        "checkoutUsers": [
            {"result": [
                {"id": 0, "name": "Administrator", "flags": 0, "groupList": [9998, 9999]},
                {"id": 12, "name": "m.muster", "flags": 0, "groupList": [9999, 150]},
                {"id": 13, "name": "a.gruber", "flags": 0, "groupList": [9999]},
            ]},
            {"result": [
                {"id": 9999, "name": "Jeder", "flags": 0},
                {"id": 150, "name": "Sales-Team", "flags": 0},
            ]},
        ],
        "findClose": {},
    })
    res = lab_perms.folder_principals(client, "200")
    by_name = {p["name"]: p for p in res["principals"]}
    assert by_name["Sales-Team"]["label"] == "R, W"
    assert by_name["Sales-Team"]["member_count"] == 1  # only m.muster
    assert by_name["Jeder"]["label"] == "no access"
    # m.muster is in Sales-Team (150) -> inherits R, W; a.gruber is not
    assert by_name["m.muster"]["label"] == "R, W"
    assert by_name["a.gruber"]["label"] == "no access"


def test_folder_principals_marks_a_main_admin_group_as_full_regardless_of_acl():
    client = MockEloClient({
        "checkoutSord": {"sord": {"id": 1, "name": "root", "aclItems": [{"id": 9999, "type": 0, "access": 1}]}},
        "findFirstUsers": [
            {"moreResults": False, "sortedResult": [{"id": 0, "name": "Administrator", "type": 1}]},
            {"moreResults": False, "sortedResult": [{"id": 9998, "name": "Administratoren", "type": 0}]},
        ],
        "checkoutUsers": [
            {"result": [{"id": 0, "name": "Administrator", "flags": 0, "groupList": []}]},
            {"result": [{"id": 9998, "name": "Administratoren", "flags": 1}]},
        ],
        "findClose": {},
    })
    res = lab_perms.folder_principals(client, "1")
    admin_group = next(p for p in res["principals"] if p["name"] == "Administratoren")
    assert admin_group["access"] is True and admin_group["label"] == "full"


# --------------------------------------------------------------------------- #
def test_lab_perms_source_returns_real_files():
    src = lab_perms.lab_perms_source()
    assert any("lab_perms.py" in f["title"] for f in src["backend"])
    assert any("08-user-folder-permissions.yaml" in f["title"] for f in src["backend"])
    assert src["frontend"] and "lab-perms slice" in src["frontend"][0]["code"]
