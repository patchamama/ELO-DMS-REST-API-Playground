"""Unit tests for app.lab_fields (GRP <-> MAP copy across a mask).
MockEloClient consumes list-valued mock entries one item per call, in call
order; a small recording wrapper captures the bodies of the writes."""
import pytest
from elo_playground import EloError, MockEloClient

from app import lab_fields


class Recording(MockEloClient):
    """MockEloClient that also remembers every (method, body)."""

    def __init__(self, data):
        super().__init__(data)
        self.calls = []

    def call(self, method, body=None, *, service="IXServicePortIF"):
        self.calls.append((method, body))
        return super().call(method, body, service=service)

    def bodies(self, method):
        return [b for m, b in self.calls if m == method]


_MASKS = {"maskNames": [
    {"id": 5, "name": "Invoice", "displayName": "Invoice", "documentMask": True, "folderMask": False},
    {"id": 2, "name": "Basic", "displayName": "Basic entry", "documentMask": True, "folderMask": True},
]}
_LINES = [
    {"id": 0, "key": "INVOICE_NO", "name": "Invoice no.", "type": 3000, "editRow": 4},
    {"id": 2, "key": "DUE", "name": "Due", "type": 3001, "editRow": 5, "hidden": True},
]


def _mask(lines=None):
    # a fresh copy per call: add_grp_field mutates the checked-out mask, as
    # it would with a real reply
    import copy
    return {"id": 5, "name": "Invoice", "lines": copy.deepcopy(lines if lines is not None else _LINES)}


def _sord(oid, name, **keys):
    return {"id": oid, "name": name, "type": 254, "refPaths": [{"path": [{"id": 2, "name": "Administration"}]}],
            "objKeys": [{"id": i, "name": k, "data": [v] if v else []} for i, (k, v) in enumerate(keys.items())]}


def test_list_masks_sorts_by_display_name_and_flags_kinds():
    res = lab_fields.list_masks(MockEloClient({"checkoutSord": _MASKS}))
    assert [m["display_name"] for m in res["masks"]] == ["Basic entry", "Invoice"]
    assert res["masks"][0]["folder_mask"] is True and res["masks"][1]["id"] == "5"


def test_mask_fields_names_types_and_finds_the_first_free_line_id():
    res = lab_fields.mask_fields(MockEloClient({"checkoutDocMask": _mask()}), 5)
    assert res["mask"] == {"id": "5", "name": "Invoice"}
    assert [(l["key"], l["type_name"], l["hidden"]) for l in res["lines"]] == [("INVOICE_NO", "text", False), ("DUE", "date", True)]
    assert res["next_line_id"] == 1                      # 0 and 2 are taken


def test_add_grp_field_appends_a_text_line_and_commits_the_whole_mask():
    client = Recording({"checkoutDocMask": [_mask(), _mask(_LINES + [{"id": 1, "key": "MAP_COPY", "name": "From map", "type": 3000}])],
                        "checkinDocMask": 5})
    res = lab_fields.add_grp_field(client, 5, "map_copy", "From map")
    checkout, = client.bodies("checkoutDocMask")[:1]
    assert checkout["lockZ"] == {"bset": "1"}
    (checkin,) = client.bodies("checkinDocMask")
    new = checkin["docMask"]["lines"][-1]
    assert (new["id"], new["key"], new["name"], new["type"], new["editRow"]) == (1, "MAP_COPY", "From map", 3000, 6)
    assert len(checkin["docMask"]["lines"]) == 3 and checkin["unlockZ"] == {"bset": "1"}
    assert res["created"]["key"] == "MAP_COPY" and [l["key"] for l in res["lines"]][-1] == "MAP_COPY"


def test_add_grp_field_rejects_bad_and_duplicate_keys():
    with pytest.raises(EloError):
        lab_fields.add_grp_field(MockEloClient({"checkoutDocMask": _mask()}), 5, "1bad key", "x")
    client = Recording({"checkoutDocMask": _mask(), "checkinDocMask": 5})
    with pytest.raises(EloError):
        lab_fields.add_grp_field(client, 5, "invoice_no", "dup")
    assert len(client.bodies("checkinDocMask")) == 1          # the lock was released, nothing added
    assert client.bodies("checkinDocMask")[0]["docMask"]["lines"] == _LINES


def _copy_client(extra=None):
    data = {
        "checkoutDocMask": _mask(),
        "findFirstSords": {"searchId": "(M)", "moreResults": False, "sords": [
            _sord(10, "empty-grp", INVOICE_NO=""), _sord(11, "has-grp", INVOICE_NO="OLD"), _sord(12, "equal", INVOICE_NO="X"), _sord(13, "no-map", INVOICE_NO="")]},
        "findClose": {},
        "checkoutMap": [{"items": [{"key": "map_no", "value": "A"}]}, {"items": [{"key": "map_no", "value": "B"}]},
                        {"items": [{"key": "map_no", "value": "X"}]}, {"items": []}],
    }
    data.update(extra or {})
    return Recording(data)


def test_plan_copy_map_to_grp_classifies_every_object():
    res = lab_fields.plan_copy(_copy_client(), 5, direction="map_to_grp", map_key="map_no", grp_key="invoice_no")
    assert res["grp_key"] == "INVOICE_NO" and res["dry_run"] is True
    assert {r["name"]: r["action"] for r in res["rows"]} == {"empty-grp": "write", "has-grp": "skip_target_has_value", "equal": "same", "no-map": "skip_empty_source"}
    assert res["summary"] == {"total": 4, "write": 1, "skip_target_has_value": 1, "same": 1, "skip_empty_source": 1}
    assert res["rows"][0]["path"] == "Administration"


def test_plan_copy_overwrite_and_reverse_direction():
    res = lab_fields.plan_copy(_copy_client(), 5, direction="map_to_grp", map_key="map_no", grp_key="INVOICE_NO", overwrite=True)
    assert {r["name"]: r["action"] for r in res["rows"]}["has-grp"] == "write"
    res = lab_fields.plan_copy(_copy_client(), 5, direction="grp_to_map", map_key="map_no", grp_key="INVOICE_NO")
    # GRP -> MAP: source = GRP value; "has-grp" has OLD vs MAP B -> skip (target set), "equal" same, others empty source
    assert {r["name"]: r["action"] for r in res["rows"]} == {"empty-grp": "skip_empty_source", "has-grp": "skip_target_has_value", "equal": "same", "no-map": "skip_empty_source"}


def test_plan_copy_needs_an_existing_grp_line():
    with pytest.raises(EloError):
        lab_fields.plan_copy(_copy_client(), 5, direction="map_to_grp", map_key="map_no", grp_key="NOPE")


def test_execute_copy_map_to_grp_writes_objkeys_and_collects_failures():
    client = _copy_client({
        # object 10 is checked out for writing: its objKeys lack INVOICE_NO -> appended
        "checkoutSord": {"sord": {"id": 10, "name": "empty-grp", "objKeys": [{"id": 2, "name": "DUE", "data": []}]}},
        "checkinSord": 10,
    })
    res = lab_fields.execute_copy(client, 5, direction="map_to_grp", map_key="map_no", grp_key="INVOICE_NO")
    (checkin,) = client.bodies("checkinSord")
    keys = {k["name"]: k for k in checkin["sord"]["objKeys"]}
    assert keys["INVOICE_NO"]["data"] == ["A"] and keys["INVOICE_NO"]["id"] == 0 and checkin["unlockZ"] == {"bset": "1"}
    assert res["summary"]["written"] == 1 and res["summary"]["failed"] == 0 and res["summary"]["skipped"] == 3
    assert {r["name"]: r["result"] for r in res["rows"]}["empty-grp"] == "written"

    failing = _copy_client({"checkoutSord": {"exception": "ELOIX:1234 locked"}})
    res = lab_fields.execute_copy(failing, 5, direction="map_to_grp", map_key="map_no", grp_key="INVOICE_NO")
    row = next(r for r in res["rows"] if r["name"] == "empty-grp")
    assert row["result"] == "failed" and "locked" in row["error"] and res["summary"]["failed"] == 1


def test_execute_copy_grp_to_map_uses_checkinmap():
    client = _copy_client({"checkinMap": {}})
    res = lab_fields.execute_copy(client, 5, direction="grp_to_map", map_key="map_no", grp_key="INVOICE_NO", overwrite=True)
    bodies = client.bodies("checkinMap")
    assert [(b["objId"], b["data"]) for b in bodies] == [(11, [{"key": "map_no", "value": "OLD"}])]
    assert bodies[0]["domainName"] == "objekte" and bodies[0]["unlockZ"] == {"bset": "1"}
    assert res["summary"]["written"] == 1


def test_map_keys_for_mask_counts_keys_across_sampled_objects():
    res = lab_fields.map_keys_for_mask(_copy_client(), 5, sample=4)
    assert res["sampled"] == 4 and res["keys"] == [{"key": "map_no", "count": 3, "example": "A"}]


def test_lab_fields_source_returns_real_files():
    src = lab_fields.lab_fields_source()
    assert any("lab_fields.py" in f["title"] for f in src["backend"]) and "lab-fields slice" in src["frontend"][0]["code"]
