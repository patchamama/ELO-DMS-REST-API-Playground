"""Unit tests for app.lab_perms (the Testing lab user/folder permissions panel).

The real ELO client is stood in for by MockEloClient, which has the same
surface (call / find_all). A list-valued mock entry is consumed one item per
*call*, in call order - so each test's mock is shaped to match the exact RPC
call sequence the function under test actually makes.

Shared shape used below: groups Jeder(9999), Sales-Team(150), Sales-Leads
(151, a child group of Sales-Team - i.e. its groupList names 150); users
Administrator(0, main admin), m.muster(12, in Sales-Leads + Jeder),
a.gruber(13, in Jeder only).
"""
from elo_playground import MockEloClient

from app import lab_perms

_GROUPS_PAGE = {"moreResults": False, "searchId": "(G)", "sortedResult": [
    {"id": 9999, "name": "Jeder", "type": 0, "displayName": "Jeder"},
    {"id": 150, "name": "Sales-Team", "type": 0, "displayName": "Sales-Team"},
    {"id": 151, "name": "Sales-Leads", "type": 0, "displayName": "Sales-Leads"},
]}
_USERS_PAGE = {"moreResults": False, "searchId": "(U)", "sortedResult": [
    {"id": 0, "name": "Administrator", "type": 1, "displayName": "Administrator"},
    {"id": 12, "name": "m.muster", "type": 1, "displayName": "Max Muster"},
    {"id": 13, "name": "a.gruber", "type": 1, "displayName": "Anna Gruber"},
]}
_GROUPS_DETAIL = {"result": [
    {"id": 9999, "name": "Jeder", "flags": 0, "groupList": []},
    {"id": 150, "name": "Sales-Team", "flags": 0, "groupList": [9999]},
    {"id": 151, "name": "Sales-Leads", "flags": 0, "groupList": [150]},   # nested under Sales-Team
]}
_USERS_DETAIL = {"result": [
    {"id": 0, "name": "Administrator", "flags": 1, "groupList": [9999]},
    {"id": 12, "name": "m.muster", "flags": 0, "groupList": [9999, 151]},
    {"id": 13, "name": "a.gruber", "flags": 0, "groupList": [9999]},
]}


def _ctx(kind, pid, group_ids, admin=False):
    return {"kind": kind, "id": pid, "group_ids": set(group_ids), "is_main_admin": admin}


# --------------------------------------------------------------------------- #
#  the pure ACL model
# --------------------------------------------------------------------------- #
def test_access_label_covers_full_none_and_partial():
    assert lab_perms.access_label(63) == "full"
    assert lab_perms.access_label(0) == "no access"
    assert lab_perms.access_label(1 | 16) == "R, L"


def test_resolve_access_unions_matching_group_entries():
    acl = [{"id": 150, "type": 0, "access": 3}, {"id": 9999, "type": 0, "access": 1}]
    res = lab_perms.resolve_access(acl, _ctx("user", 12, {150, 9999}))
    assert (res["access"], res["bits"], res["label"], res["conditional"]) == (True, 3, "R, W", False)
    assert lab_perms.resolve_access(acl, _ctx("group", 9998, {9998}))["label"] == "no access"


def test_resolve_access_distinguishes_user_and_group_entries_by_type():
    # TYPE_USER (1) entry for id 12 must not match GROUP id 12, and vice versa.
    acl = [{"id": 12, "type": 1, "access": 1}]
    assert lab_perms.resolve_access(acl, _ctx("user", 12, {9999}))["access"] is True
    assert lab_perms.resolve_access(acl, _ctx("group", 12, {12}))["access"] is False


def test_resolve_access_and_groups_require_every_listed_group():
    acl = [{"id": 150, "type": 0, "access": 63, "andGroups": [{"id": 9999, "name": "Jeder"}]}]
    assert lab_perms.resolve_access(acl, _ctx("user", 12, {150, 9999}))["access"] is True
    assert lab_perms.resolve_access(acl, _ctx("user", 12, {150}))["access"] is False
    # a group alone can't tell whether its members satisfy the AND part
    res = lab_perms.resolve_access(acl, _ctx("group", 150, {150}))
    assert res["access"] is False and res["conditional"] is True


def test_resolve_access_owner_entry_applies_to_the_owning_user_only():
    acl = [{"id": 0, "type": 200, "access": 7}]  # TYPE_OWNER
    assert lab_perms.resolve_access(acl, _ctx("user", 13, {9999}), owner_id=13)["label"] == "R, W, D"
    assert lab_perms.resolve_access(acl, _ctx("user", 12, {9999}), owner_id=13)["access"] is False
    assert lab_perms.resolve_access(acl, _ctx("group", 13, {13}), owner_id=13)["access"] is False


def test_resolve_access_main_admin_bypasses_the_acl_entirely():
    acl = [{"id": 9999, "type": 0, "access": 1}]
    res = lab_perms.resolve_access(acl, _ctx("group", 12345, {12345}, admin=True))
    assert (res["access"], res["bits"], res["label"]) == (True, 63, "full")


def test_effective_acl_merges_the_parent_on_an_inherit_marker():
    own = [{"id": 12, "type": 1, "access": 1}, {"type": 100, "id": 0, "access": 0}]  # TYPE_INHERIT
    parent = [{"id": 150, "type": 0, "access": 63}]
    eff = lab_perms._effective_acl(own, parent)
    assert [e["type"] for e in eff] == [1, 0]
    assert lab_perms._effective_acl([{"id": 1, "type": 0, "access": 1}], parent) == [{"id": 1, "type": 0, "access": 1}]


# --------------------------------------------------------------------------- #
#  directory: nested groups
# --------------------------------------------------------------------------- #
def test_directory_closure_follows_parent_groups_transitively():
    client = MockEloClient({"findFirstUsers": _GROUPS_PAGE, "checkoutUsers": _GROUPS_DETAIL, "findClose": {}})
    d = lab_perms._Directory(client)
    assert d.closure({151}) == {151, 150, 9999}   # Sales-Leads -> Sales-Team -> Jeder
    assert d.closure({9999}) == {9999}


def test_list_groups_and_users_are_sorted_by_name():
    client = MockEloClient({"findFirstUsers": [_GROUPS_PAGE, _USERS_PAGE], "findClose": {}})
    assert [g["name"] for g in lab_perms.list_groups(client)] == ["Jeder", "Sales-Leads", "Sales-Team"]
    assert [u["name"] for u in lab_perms.list_users(client)] == ["a.gruber", "Administrator", "m.muster"]


def test_group_members_lists_direct_members_only():
    client = MockEloClient({"findFirstUsers": _USERS_PAGE, "checkoutUsers": _USERS_DETAIL, "findClose": {}})
    assert [m["name"] for m in lab_perms.group_members(client, 151)["members"]] == ["m.muster"]
    assert lab_perms.group_members(client, 150)["total"] == 0   # nobody is *directly* in Sales-Team
    res = lab_perms.group_members(client, 9999, preview=1)
    assert res["total"] == 3 and len(res["members"]) == 1


def test_list_principals_reports_groups_admin_flags_and_connected_user():
    # _Directory: findFirstUsers#1 + checkoutUsers#1; users: findFirstUsers#2 +
    # checkoutUsers#2; connected: checkoutUsers#3.
    client = MockEloClient({
        "findFirstUsers": [_GROUPS_PAGE, _USERS_PAGE],
        "checkoutUsers": [_GROUPS_DETAIL, _USERS_DETAIL, {"result": [{"id": 0, "name": "Administrator", "flags": 1}]}],
        "findClose": {},
    })
    client.user = {"id": 0, "name": "Administrator"}
    res = lab_perms.list_principals(client)
    by_name = {u["name"]: u for u in res["users"]}
    assert [g["name"] for g in by_name["m.muster"]["groups"]] == ["Jeder", "Sales-Leads"]
    assert by_name["Administrator"]["is_main_admin"] is True
    assert res["connected"] == {"id": "0", "name": "Administrator", "is_main_admin": True}


# --------------------------------------------------------------------------- #
#  subtree
# --------------------------------------------------------------------------- #
_ROOT_SORD = {"sord": {"id": 1, "name": "Contelo", "parentId": 0, "ownerId": 0,
                       "aclItems": [{"id": 9999, "type": 0, "name": "Jeder", "access": 63}]}}


def _root_rows():
    # aclItems ride along on every findFirstSords row (sordZ = mbAllIndex)
    return {"searchId": "(root)", "sords": [
        {"id": 200, "parentId": 1, "name": "Sales", "type": 1, "childCount": 1, "ownerId": 0,
         "aclItems": [{"id": 150, "type": 0, "access": 3}]},
        {"id": 201, "parentId": 1, "name": "Finance", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 9998, "type": 0, "access": 63}]},
        {"id": 202, "parentId": 1, "name": "Archive", "type": 1, "childCount": 0, "ownerId": 13,
         "aclItems": [{"id": 0, "type": 200, "access": 1}]},
    ]}


def _subtree_client(find_first_sords, *, user_detail=None, groups_page=_GROUPS_PAGE,
                    groups_detail=_GROUPS_DETAIL, parent_sord=_ROOT_SORD):
    # subtree() call order: _Directory (findFirstUsers#1 + checkoutUsers#1),
    # the principal's own detail for a *user* (checkoutUsers), every user
    # (findFirstUsers#2 + checkoutUsers), the starting parent's ACL
    # (checkoutSord, exactly once), then one findFirstSords per level.
    checkout_users = [groups_detail] + ([user_detail] if user_detail else []) + [_USERS_DETAIL]
    return MockEloClient({
        "findFirstUsers": [groups_page, _USERS_PAGE],
        "checkoutUsers": checkout_users,
        "checkoutSord": [parent_sord],
        "findFirstSords": find_first_sords,
        "findClose": {},
    })


def test_subtree_for_a_group_uses_row_acls_and_checks_out_only_the_parent():
    res = lab_perms.subtree(_subtree_client(_root_rows()), "1", {"kind": "group", "id": "150"}, depth=1)
    by_id = {r["id"]: r for r in res["rows"]}
    assert by_id["200"]["label"] == "R, W" and by_id["200"]["children"] is None
    assert by_id["201"]["access"] is False and by_id["202"]["access"] is False
    assert res["is_main_admin"] is False and res["truncated"] is False


def test_subtree_for_a_nested_group_inherits_the_parent_groups_access():
    # Sales-Leads (151) is a member of Sales-Team (150): a folder granting
    # 150 is accessible to 151 too.
    res = lab_perms.subtree(_subtree_client(_root_rows()), "1", {"kind": "group", "id": "151"}, depth=1)
    assert {r["id"]: r["label"] for r in res["rows"]}["200"] == "R, W"


def test_subtree_for_a_user_resolves_through_transitive_groups_and_owner():
    client = _subtree_client(_root_rows(), user_detail={"result": [{"id": 13, "name": "a.gruber", "flags": 0, "groupList": [151]}]})
    res = lab_perms.subtree(client, "1", {"kind": "user", "id": "13"}, depth=1)
    by_id = {r["id"]: r for r in res["rows"]}
    assert by_id["200"]["label"] == "R, W"      # via 151 -> 150
    assert by_id["202"]["label"] == "R"         # TYPE_OWNER: a.gruber owns Archive
    assert by_id["201"]["access"] is False


_ADMIN_GROUPS_PAGE = {"moreResults": False, "sortedResult": _GROUPS_PAGE["sortedResult"] + [{"id": 9998, "name": "Administratoren", "type": 0}]}
_ADMIN_GROUPS_DETAIL = {"result": _GROUPS_DETAIL["result"] + [{"id": 9998, "name": "Administratoren", "flags": 1, "groupList": []}]}


def _exclusive_rows():
    return {"searchId": "(root)", "sords": [
        # only Sales-Team (plus the main-admin group) -> exclusive to Sales-Team
        {"id": 1, "parentId": 1, "name": "Only-Sales", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 150, "type": 0, "access": 3}, {"id": 9998, "type": 0, "access": 63}]},
        # Sales-Team AND Jeder -> not exclusive
        {"id": 2, "parentId": 1, "name": "Shared", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 150, "type": 0, "access": 3}, {"id": 9999, "type": 0, "access": 1}]},
        # Sales-Team plus one of its own members (m.muster via Sales-Leads) -> still exclusive
        {"id": 3, "parentId": 1, "name": "Sales-plus-member", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 150, "type": 0, "access": 3}, {"id": 12, "type": 1, "access": 63}]},
        # one user entry plus the main administrator -> exclusive to that user
        {"id": 4, "parentId": 1, "name": "Mine", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 13, "type": 1, "access": 63}, {"id": 0, "type": 1, "access": 63}]},
    ]}


def test_subtree_marks_exclusive_access_ignoring_administrators():
    res = lab_perms.subtree(_subtree_client(_exclusive_rows(), groups_page=_ADMIN_GROUPS_PAGE, groups_detail=_ADMIN_GROUPS_DETAIL),
                            "1", {"kind": "group", "id": "150"}, depth=1)
    assert {r["name"]: r["exclusive"] for r in res["rows"]} == {
        "Only-Sales": True, "Shared": False, "Sales-plus-member": True, "Mine": False}

    client = _subtree_client(_exclusive_rows(), groups_page=_ADMIN_GROUPS_PAGE, groups_detail=_ADMIN_GROUPS_DETAIL,
                             user_detail={"result": [{"id": 13, "name": "a.gruber", "flags": 0, "groupList": [9999]}]})
    res = lab_perms.subtree(client, "1", {"kind": "user", "id": "13"}, depth=1)
    ex = {r["name"]: r["exclusive"] for r in res["rows"]}
    assert ex["Mine"] is True            # Administrator (flags=1) is ignored
    assert ex["Shared"] is False         # Jeder grants everyone
    assert ex["Only-Sales"] is False     # no access at all


def test_subtree_bubbles_exclusivity_up_to_the_parent_row():
    rows = [
        {"searchId": "(root)", "sords": [
            {"id": 1, "parentId": 1, "name": "Top", "type": 1, "childCount": 1, "aclItems": [{"id": 9999, "type": 0, "access": 63}]},
        ]},
        {"searchId": "(top)", "sords": [
            {"id": 10, "parentId": 1, "name": "Only-Sales", "type": 1, "childCount": 0, "aclItems": [{"id": 150, "type": 0, "access": 1}]},
        ]},
    ]
    res = lab_perms.subtree(_subtree_client(rows), "1", {"kind": "group", "id": "150"}, depth=2)
    top = res["rows"][0]
    assert top["exclusive"] is False and top["descendant_exclusive"] is True
    assert top["children"][0]["exclusive"] is True


def test_subtree_flags_folders_whose_acl_departs_from_the_parents():
    rows = {"searchId": "(root)", "sords": [
        {"id": 1, "parentId": 1, "name": "Same", "type": 1, "childCount": 0, "aclItems": [{"id": 9999, "type": 0, "access": 63}]},
        {"id": 2, "parentId": 1, "name": "Special", "type": 1, "childCount": 0, "aclItems": [{"id": 150, "type": 0, "access": 63}]},
    ]}
    res = lab_perms.subtree(_subtree_client(rows), "1", {"kind": "group", "id": "150"}, depth=1)
    assert {r["name"]: r["acl_differs"] for r in res["rows"]} == {"Same": False, "Special": True}


def test_subtree_orders_accessible_first_then_paths_to_accessible_then_the_rest():
    client = _subtree_client([
        {"searchId": "(root)", "sords": [
            {"id": 1, "parentId": 1, "name": "Zebra", "type": 1, "childCount": 1, "aclItems": []},
            {"id": 2, "parentId": 1, "name": "Apple", "type": 1, "childCount": 0, "aclItems": [{"id": 150, "type": 0, "access": 1}]},
            {"id": 3, "parentId": 1, "name": "Mango", "type": 1, "childCount": 0, "aclItems": []},
        ]},
        {"searchId": "(zebra)", "sords": [
            {"id": 10, "parentId": 1, "name": "Deep", "type": 1, "childCount": 0, "aclItems": [{"id": 150, "type": 0, "access": 1}]},
        ]},
    ])
    res = lab_perms.subtree(client, "1", {"kind": "group", "id": "150"}, depth=2)
    names = [r["name"] for r in res["rows"]]
    assert names == ["Apple", "Zebra", "Mango"]   # accessible, then path-to-accessible, then nothing
    zebra = res["rows"][1]
    assert zebra["access"] is False and zebra["descendant_access"] is True
    assert zebra["children"][0]["name"] == "Deep" and zebra["children"][0]["access"] is True


def test_subtree_honours_the_node_cap():
    res = lab_perms.subtree(_subtree_client(_root_rows()), "1", {"kind": "group", "id": "150"}, depth=1, max_nodes=1)
    assert res["truncated"] is True and len(res["rows"]) == 1


def test_subtree_grants_full_access_to_a_main_admin_group():
    res = lab_perms.subtree(_subtree_client(_root_rows(), groups_page=_ADMIN_GROUPS_PAGE, groups_detail=_ADMIN_GROUPS_DETAIL),
                            "1", {"kind": "group", "id": "9998"}, depth=1)
    assert res["is_main_admin"] is True
    assert all(r["label"] == "full" and r["exclusive"] is False for r in res["rows"])


def test_subtree_follows_an_inherit_marker_to_the_parent_acl():
    # the child says "inherit"; the parent's ACL (checked out once) grants
    # Sales-Team, so the child is accessible to it and equals its parent.
    parent = {"sord": {"id": 77, "name": "Parent", "parentId": 1, "aclItems": [{"id": 150, "type": 0, "access": 16}]}}
    rows = {"searchId": "(p)", "sords": [
        {"id": 300, "parentId": 77, "name": "Child", "type": 1, "childCount": 0, "aclItems": [{"type": 100, "id": 0, "access": 0}]},
    ]}
    res = lab_perms.subtree(_subtree_client(rows, parent_sord=parent), "77", {"kind": "group", "id": "150"}, depth=1)
    assert res["rows"][0]["label"] == "L" and res["rows"][0]["acl_differs"] is False


# --------------------------------------------------------------------------- #
#  special folders (ACL departs from the parent)
# --------------------------------------------------------------------------- #
def test_acl_diff_reports_added_removed_and_changed_entries():
    parent = [{"id": 9999, "type": 0, "access": 63}, {"id": 150, "type": 0, "access": 3}]
    child = [{"id": 150, "type": 0, "access": 1}, {"id": 12, "type": 1, "access": 63}]
    d = lab_perms.acl_diff(child, parent)
    assert d["differs"] is True
    assert [e["id"] for e in d["added"]] == [12]
    assert [e["id"] for e in d["removed"]] == [9999]
    assert d["changed"] == [{"entry": child[0], "parent_access": 3, "access": 1}]
    assert lab_perms.acl_diff(parent, list(reversed(parent)))["differs"] is False   # order is irrelevant


def test_special_folders_marks_differing_folders_and_keeps_the_path():
    client = MockEloClient({
        "checkoutSord": _ROOT_SORD,
        "findFirstSords": [
            {"searchId": "(root)", "sords": [
                {"id": 1, "parentId": 1, "name": "Same", "type": 1, "childCount": 1, "aclItems": [{"id": 9999, "type": 0, "access": 63}]},
                {"id": 2, "parentId": 1, "name": "Special", "type": 1, "childCount": 0, "aclItems": [{"id": 150, "type": 0, "name": "Sales-Team", "access": 63}]},
            ]},
            {"searchId": "(same)", "sords": [
                {"id": 10, "parentId": 1, "name": "Deep-special", "type": 1, "childCount": 0, "aclItems": [{"id": 9999, "type": 0, "access": 1}]},
            ]},
        ],
        "findClose": {},
    })
    res = lab_perms.special_folders(client, "1", depth=2)
    assert res["parent"]["name"] == "Contelo" and res["truncated"] is False
    assert [r["name"] for r in res["rows"]] == ["Special", "Same"]
    special, same = res["rows"]
    assert special["differs"] and (special["added"], special["removed"], special["changed"]) == (1, 1, 0)
    assert special["added_names"] == ["Sales-Team"]
    assert same["differs"] is False and same["descendant_differs"] is True
    assert same["children"][0]["differs"] is True and same["children"][0]["changed"] == 1


# --------------------------------------------------------------------------- #
#  by folder
# --------------------------------------------------------------------------- #
def test_folder_principals_resolves_every_group_and_user_with_nesting():
    # _Directory (findFirstUsers#1 + checkoutUsers#1), checkoutSord, users
    # (findFirstUsers#2 + checkoutUsers#2).
    client = MockEloClient({
        "findFirstUsers": [_GROUPS_PAGE, _USERS_PAGE],
        "checkoutUsers": [_GROUPS_DETAIL, _USERS_DETAIL],
        "checkoutSord": {"sord": {"id": 200, "name": "Sales", "parentId": 1, "ownerId": 13,
                                  "aclItems": [{"id": 150, "type": 0, "access": 3}, {"id": 0, "type": 200, "access": 4}]}},
        "findClose": {},
    })
    res = lab_perms.folder_principals(client, "200")
    by_name = {p["name"]: p for p in res["principals"]}
    assert res["folder"]["name"] == "Sales"
    assert by_name["Sales-Team"]["label"] == "R, W"
    assert by_name["Sales-Leads"]["label"] == "R, W"         # nested under Sales-Team
    assert by_name["Sales-Leads"]["member_count"] == 1       # m.muster, directly
    assert by_name["Jeder"]["label"] == "no access"
    assert by_name["m.muster"]["label"] == "R, W"            # 151 -> 150
    assert by_name["a.gruber"]["label"] == "D"               # owner entry only
    assert by_name["Administrator"]["label"] == "full"       # main admin


def test_folder_acl_detail_decodes_entries_diff_and_resolves_a_principal():
    # checkoutSord order: the folder, then its parent (once - name + ACL).
    client = MockEloClient({
        "findFirstUsers": _GROUPS_PAGE, "checkoutUsers": _GROUPS_DETAIL,
        "checkoutSord": [
            {"sord": {"id": 200, "name": "Sales", "parentId": 1, "ownerId": 0, "ownerName": "Administrator",
                      "aclItems": [{"id": 150, "type": 0, "name": "Sales-Team", "access": 3},
                                   {"id": 0, "type": 1, "name": "Administrator", "access": 63}]}},
            _ROOT_SORD,
        ],
        "findClose": {},
    })
    res = lab_perms.folder_acl_detail(client, "200", {"kind": "group", "id": "151"})
    assert res["folder"]["name"] == "Sales" and res["folder"]["parent_name"] == "Contelo"
    assert res["owner"]["name"] == "Administrator"
    assert [(e["kind"], e["name"], e["label"]) for e in res["entries"]] == [("group", "Sales-Team", "R, W"), ("user", "Administrator", "full")]
    assert res["diff"]["differs"] is True
    assert [e["name"] for e in res["diff"]["added"]] == ["Sales-Team", "Administrator"]
    assert [e["name"] for e in res["diff"]["removed"]] == ["Jeder"]
    assert res["principal"]["label"] == "R, W"
    assert res["principal"]["group_names"] == ["Jeder", "Sales-Leads", "Sales-Team"]


def test_path_of_joins_ref_paths_and_falls_back_to_the_name():
    # IX lists the parents below the root, not the root and not the folder
    sord = {"id": 5, "name": "Leads", "refPaths": [{"path": [{"id": 2, "name": "Administration"}, {"id": 200, "name": "Sales"}], "pathAsString": "¶Administration¶Sales"}]}
    assert lab_perms._path_of(sord) == "Administration / Sales / Leads"
    assert lab_perms._path_of({"id": 2, "name": "Administration", "refPaths": [{"path": [], "pathAsString": "¶"}]}) == "Administration"
    assert lab_perms._path_of({"id": 7}) == "7"


def test_folder_acl_detail_at_the_root_has_no_diff():
    client = MockEloClient({"findFirstUsers": _GROUPS_PAGE, "checkoutUsers": _GROUPS_DETAIL,
                            "checkoutSord": _ROOT_SORD, "findClose": {}})
    res = lab_perms.folder_acl_detail(client, "1")
    assert res["diff"] is None and res["folder"]["parent_name"] is None and "principal" not in res


# --------------------------------------------------------------------------- #
#  org chart + diagnostics
# --------------------------------------------------------------------------- #
_USERS_DETAIL_SUP = {"result": [
    {"id": 0, "name": "Administrator", "flags": 1, "groupList": [9999], "superiorId": 0},
    {"id": 12, "name": "m.muster", "flags": 0, "groupList": [9999, 151], "superiorId": 13},
    {"id": 13, "name": "a.gruber", "flags": 0, "groupList": [9999], "superiorId": 13},
]}


def test_org_chart_reports_parent_groups_member_counts_and_supervisors():
    client = MockEloClient({"findFirstUsers": [_GROUPS_PAGE, _USERS_PAGE],
                            "checkoutUsers": [_GROUPS_DETAIL, _USERS_DETAIL_SUP], "findClose": {}})
    res = lab_perms.org_chart(client)
    g = {x["name"]: x for x in res["groups"]}
    assert g["Sales-Leads"]["parent_ids"] == ["150"] and g["Sales-Team"]["parent_ids"] == ["9999"]
    assert g["Sales-Team"]["member_count"] == 0 and g["Sales-Team"]["total_members"] == 1   # via Sales-Leads
    assert g["Jeder"]["everyone"] is True and g["Sales-Team"]["everyone"] is False
    u = {x["name"]: x for x in res["users"]}
    assert u["m.muster"]["superior_id"] == "13" and u["a.gruber"]["superior_id"] is None
    assert u["Administrator"]["superior_id"] is None and u["Administrator"]["is_main_admin"] is True


def test_diagnose_reports_each_smell_once_with_its_code():
    # _Directory (findFirstUsers#1 + checkoutUsers#1), users (findFirstUsers#2
    # + checkoutUsers#2), checkoutSord(parent), findFirstSords per level.
    rows = {"searchId": "(root)", "sords": [
        {"id": 1, "parentId": 1, "name": "Ghost", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 4242, "type": 0, "access": 63}, {"id": 0, "type": 1, "access": 63}]},          # orphan group + admin -> admin_only too
        {"id": 2, "parentId": 1, "name": "WriteOnly", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 150, "type": 0, "access": 2}]},                                               # W without R
        {"id": 3, "parentId": 1, "name": "OpenBar", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 9999, "type": 0, "access": 63}]},                                             # everyone gains full (parent gave R)
        {"id": 4, "parentId": 1, "name": "Empty", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 152, "type": 0, "access": 63}]},                                              # group without members
        {"id": 5, "parentId": 1, "name": "Impossible", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 150, "type": 0, "access": 63, "andGroups": [{"id": 152, "name": "Nobody"}]}]},  # AND nobody satisfies
        {"id": 6, "parentId": 1, "name": "Fine", "type": 1, "childCount": 0, "ownerId": 0,
         "aclItems": [{"id": 150, "type": 0, "access": 63}]},
    ]}
    groups_page = {"moreResults": False, "sortedResult": _GROUPS_PAGE["sortedResult"] + [{"id": 152, "name": "Nobody", "type": 0}]}
    groups_detail = {"result": _GROUPS_DETAIL["result"] + [{"id": 152, "name": "Nobody", "flags": 0, "groupList": []}]}
    root = {"sord": {"id": 1, "name": "Contelo", "parentId": 0, "aclItems": [{"id": 9999, "type": 0, "access": 1}]}}
    client = MockEloClient({"findFirstUsers": [groups_page, _USERS_PAGE], "checkoutUsers": [groups_detail, _USERS_DETAIL_SUP],
                            "checkoutSord": root, "findFirstSords": rows, "findClose": {}})
    res = lab_perms.diagnose(client, "1", depth=1)
    by_code = {}
    for f in res["findings"]:
        by_code.setdefault(f["code"], []).append(f)
    assert [f["folder"]["name"] for f in by_code["orphan_entry"]] == ["Ghost"] and by_code["orphan_entry"][0]["entry"]["id"] == "4242"
    assert [f["folder"]["name"] for f in by_code["admin_only"]] == ["Ghost"]
    assert [f["folder"]["name"] for f in by_code["write_without_read"]] == ["WriteOnly"]
    assert [f["folder"]["name"] for f in by_code["everyone_full"]] == ["OpenBar"]
    assert [f["folder"]["name"] for f in by_code["empty_group"]] == ["Empty"]
    assert [f["folder"]["name"] for f in by_code["and_unsatisfiable"]] == ["Impossible"] and by_code["and_unsatisfiable"][0]["and_groups"] == ["Nobody"]
    assert [f["entry"]["name"] for f in by_code["users_without_groups"]] == ["a.gruber"]   # only in Jeder
    assert [f["entry"]["name"] for f in by_code["groups_without_members"]] == ["Nobody"]
    assert res["scanned"] == 6 and res["summary"]["admin_only"] == 1
    assert by_code["everyone_full"][0]["folder"]["path"] == "OpenBar"


# --------------------------------------------------------------------------- #
def test_lab_perms_source_returns_real_files():
    src = lab_perms.lab_perms_source()
    assert any("lab_perms.py" in f["title"] for f in src["backend"])
    assert any("08-user-folder-permissions.yaml" in f["title"] for f in src["backend"])
    assert src["frontend"] and "lab-perms slice" in src["frontend"][0]["code"]
