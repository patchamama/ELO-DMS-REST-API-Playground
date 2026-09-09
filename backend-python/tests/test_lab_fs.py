"""Unit tests for app.lab_fs (the Testing lab ELO <-> local filesystem panel).

The real ELO client is stood in for by MockEloClient, which has the same
surface (call / download / upload) and reads canned responses.
"""
import pytest
from elo_playground import MockEloClient

from app import lab_fs


class _FakeSettings:
    def __init__(self, root):
        self.project_root = root


class _RecordingClient(MockEloClient):
    """MockEloClient that also records every (method, body) it is asked for."""

    def __init__(self, data):
        super().__init__(data)
        self.calls = []

    def call(self, method, body=None, *, service="IXServicePortIF"):
        self.calls.append((method, body or {}))
        return super().call(method, body, service=service)


# --------------------------------------------------------------------------- #
def test_list_children_parses_rows_and_classifies_type():
    client = MockEloClient(
        {
            "findFirstSords": {
                "searchId": "s1",
                "sords": [
                    {"id": 2, "parentId": 1, "name": "Administration", "type": 1, "childCount": 7},
                    {"id": 40, "parentId": 1, "name": "invoice.pdf", "type": 254},
                    {"id": 99, "parentId": 999, "name": "not a child", "type": 1},
                ],
            },
            "findClose": {},
        }
    )
    rows = lab_fs.list_children(client, "1")
    assert [r["id"] for r in rows] == ["2", "40"]  # the parentId 999 row is filtered out
    assert rows[0]["is_folder"] is True and rows[0]["child_count"] == 7
    assert rows[1]["is_folder"] is False


# --------------------------------------------------------------------------- #
def test_open_in_file_manager_reports_failure(monkeypatch):
    monkeypatch.setattr(lab_fs.sys, "platform", "linux")

    def boom(*_a, **_k):
        raise OSError("no display")

    monkeypatch.setattr(lab_fs.subprocess, "run", boom)
    assert lab_fs.open_in_file_manager("/tmp/whatever") is False


def test_open_in_file_manager_posix(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(lab_fs.sys, "platform", "linux")
    monkeypatch.setattr(lab_fs.subprocess, "run", lambda *a, **k: calls.append(a))
    assert lab_fs.open_in_file_manager(tmp_path) is True
    assert calls


def test_open_in_file_manager_windows(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(lab_fs.sys, "platform", "win32")
    monkeypatch.setattr(lab_fs.os, "startfile", lambda p: seen.append(p), raising=False)
    assert lab_fs.open_in_file_manager(tmp_path) is True
    assert seen == [str(tmp_path)]


# --------------------------------------------------------------------------- #
def _mirror_stub() -> MockEloClient:
    return MockEloClient(
        {
            "checkoutSord": {
                "sord": {
                    "id": 1, "name": "Picked", "type": 1, "mask": 1, "maskName": "Ordner",
                    "desc": "the picked one", "kind": 2, "IDateIso": "20260101120000",
                    "objKeys": [{"name": "REF", "data": ["R-1"]}],
                    "aclItems": [{"id": 9999, "type": 0, "name": "Jeder", "access": 63}],
                }
            },
            "checkoutMap": {"items": [{"key": "SOL_TYPE", "value": "Invoice"}]},
            "findFirstSords": [
                {
                    "searchId": "s",
                    "sords": [
                        {"id": 10, "parentId": 1, "name": "Sub", "type": 1, "childCount": 1},
                        {"id": 11, "parentId": 1, "name": "note", "type": 254},
                    ],
                },
                {"searchId": "s", "sords": [{"id": 12, "parentId": 10, "name": "deep", "type": 254}]},
                {"searchId": "s", "sords": []},
            ],
            "findClose": {},
            "checkoutDoc": {"document": {"docs": [{"url": "mock://d", "ext": "txt"}]}},
            "_download": "hello",
        }
    )


def test_mirror_to_sandbox_wipes_then_rebuilds_under_the_selected_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(lab_fs, "get_settings", lambda: _FakeSettings(tmp_path))
    monkeypatch.setattr(lab_fs, "open_in_file_manager", lambda _p: True)

    dst = lab_fs._sandbox_dir()
    dst.mkdir(parents=True)
    (dst / "STALE.txt").write_text("from a previous run", encoding="utf-8")

    res = lab_fs.mirror_to_sandbox(_mirror_stub(), "1", folder_name="Picked")

    assert not (dst / "STALE.txt").exists()                       # wiped first
    assert (dst / "Picked").is_dir()                              # the selected folder itself
    assert (dst / "Picked" / "Sub" / "deep.txt").read_bytes() == b"hello"
    assert (dst / "Picked" / "note.txt").read_bytes() == b"hello"
    assert res["top"] == "Picked"
    assert res["root"].endswith("Picked")
    assert res["folders"] == 2 and res["documents"] == 2          # Picked + Sub
    assert res["truncated"] is False and res["opened"] is True

    # every container gets a metadata.opf with mask + GRP + MAP + dates
    assert res["metadata"] == 2                                   # Picked + Sub
    meta = (dst / "Picked" / "metadata.opf").read_text(encoding="utf-8")
    assert "<eloContainer" in meta and 'name="Ordner"' in meta
    assert "REF" in meta and "R-1" in meta and "SOL_TYPE" in meta
    assert (dst / "Picked" / "Sub" / "metadata.opf").is_file()


def test_mirror_resolves_the_top_folder_name_from_elo_when_not_given(monkeypatch, tmp_path):
    monkeypatch.setattr(lab_fs, "get_settings", lambda: _FakeSettings(tmp_path))
    monkeypatch.setattr(lab_fs, "open_in_file_manager", lambda _p: True)
    lab_fs.mirror_to_sandbox(_mirror_stub(), "1")  # no folder_name -> checkoutSord
    assert (lab_fs._sandbox_dir() / "Picked").is_dir()


def test_mirror_to_sandbox_honours_the_object_cap(monkeypatch, tmp_path):
    monkeypatch.setattr(lab_fs, "get_settings", lambda: _FakeSettings(tmp_path))
    monkeypatch.setattr(lab_fs, "open_in_file_manager", lambda _p: True)
    client = MockEloClient(
        {
            "checkoutSord": {"sord": {"name": "X"}},
            "findFirstSords": {
                "searchId": "s",
                "sords": [
                    {"id": i, "parentId": 1, "name": f"d{i}", "type": 254} for i in range(5)
                ],
            },
            "findClose": {},
            "checkoutDoc": {"document": {"docs": [{"url": "mock://d", "ext": "txt"}]}},
            "_download": "x",
        }
    )
    res = lab_fs.mirror_to_sandbox(client, "1", folder_name="X", max_objects=2)
    assert res["truncated"] is True
    assert res["documents"] == 2


# --------------------------------------------------------------------------- #
_UPLOAD_MOCK = {
    "createSord": {"sord": {"id": 0, "name": ""}},
    "checkinSord": [101, 102, 103, 104, 105, 106],
    "createDoc": {"sord": {"id": 0, "name": ""}},
    "checkinDocBegin": {"docs": [{"url": "mock://up"}]},
    "checkinDocEnd": {"objId": "900"},
    "checkoutSord": {"sord": {"id": 900, "name": "x", "objKeys": []}},
    "checkinMap": {},
}


def _upload_stub() -> MockEloClient:
    return MockEloClient(dict(_UPLOAD_MOCK))


def test_upload_tree_from_a_server_path_recreates_the_whole_tree(tmp_path):
    src = tmp_path / "Invoices"
    (src / "sub").mkdir(parents=True)
    (src / "empty").mkdir()                  # an empty folder must survive too
    (src / "a.txt").write_bytes(b"AAA")
    (src / "sub" / "b.txt").write_bytes(b"BBBB")

    res = lab_fs.upload_tree(_upload_stub(), target_id="5", server_path=str(src))

    assert res["root_name"] == "Invoices"    # derived from the local folder name
    assert res["documents"] == 2
    assert res["folders"] == 3               # "Invoices", "Invoices/sub", "Invoices/empty"
    assert res["bytes"] == 7
    assert res["target_id"] == "5"


def test_upload_tree_creates_the_top_folder_even_when_empty(tmp_path):
    (tmp_path / "blank").mkdir()
    res = lab_fs.upload_tree(_upload_stub(), target_id="1", server_path=str(tmp_path / "blank"))
    assert res["folders"] == 1 and res["documents"] == 0


def test_upload_tree_from_browser_items(tmp_path):
    import base64

    items = [
        {"rel_path": "a.txt", "b64": base64.b64encode(b"hi").decode()},
        {"rel_path": "sub/b.txt", "b64": base64.b64encode(b"there").decode()},
    ]
    res = lab_fs.upload_tree(_upload_stub(), target_id="1", root_name="drop", items=items)
    assert res["documents"] == 2 and res["folders"] == 2


def test_upload_tree_rejects_a_traversal_path():
    with pytest.raises(lab_fs.EloError):
        lab_fs.upload_tree(
            _upload_stub(), target_id="1", items=[{"rel_path": "../evil.txt", "b64": ""}]
        )


def test_upload_tree_needs_a_source():
    with pytest.raises(lab_fs.EloError):
        lab_fs.upload_tree(_upload_stub(), target_id="1")


# --------------------------------------------------------------------------- #
def test_metadata_xml_roundtrips():
    sord = {
        "id": 42, "guid": "(G)", "parentId": 1, "name": "Docs", "desc": "d", "type": 1,
        "mask": 3, "maskName": "Invoice", "kind": 2, "ownerName": "Administrator",
        "IDateIso": "20260101120000", "XDateIso": "",
        "objKeys": [{"name": "NR", "data": ["N-1", "N-2"]}, {"name": "EMPTY", "data": []}],
        "aclItems": [{"id": 9999, "type": 0, "name": "Jeder", "access": 63}],
    }
    xml = lab_fs.build_metadata_xml(sord, [{"key": "K1", "value": "V1"}], repo_url="http://x")
    meta = lab_fs.parse_metadata_xml(xml)
    assert meta["name"] == "Docs" and meta["desc"] == "d"
    assert meta["mask_id"] == 3 and meta["mask_name"] == "Invoice"
    assert meta["kind"] == 2 and meta["i_date"] == "20260101120000"
    assert meta["group_fields"]["NR"] == ["N-1", "N-2"]
    assert meta["group_fields"]["EMPTY"] == []
    assert meta["map_fields"] == {"K1": "V1"}
    assert meta["acl"][0]["access"] == 63
    assert meta["guid"] == "(G)" and meta["source_id"] == "42"


def test_parse_metadata_xml_tolerates_garbage():
    assert lab_fs.parse_metadata_xml("not xml at all")["name"] is None


def test_upload_applies_metadata_opf_and_does_not_upload_it(tmp_path):
    src = tmp_path / "Backup"
    (src / "sub").mkdir(parents=True)
    (src / "doc.txt").write_bytes(b"x")
    (src / "metadata.opf").write_text(
        lab_fs.build_metadata_xml(
            {
                "id": 7, "name": "Backup", "mask": 5, "maskName": "Invoice", "desc": "restored",
                "objKeys": [{"name": "NR", "data": ["N-9"]}],
            },
            [{"key": "K", "value": "V"}],
        ),
        encoding="utf-8",
    )

    client = _RecordingClient(dict(_UPLOAD_MOCK))
    res = lab_fs.upload_tree(client, target_id="1", server_path=str(src))

    assert res["documents"] == 1                 # doc.txt only - the sidecar is not a document
    assert res["metadata_applied"] == 1
    assert res["warnings"] == []
    # the top folder was created with the mask id from the sidecar
    first_create = next(c for c in client.calls if c[0] == "createSord")
    assert first_create[1]["maskId"] == 5
    assert any(c[0] == "checkinMap" for c in client.calls)


def test_upload_never_sends_the_sidecars_original_id_or_guid(tmp_path):
    src = tmp_path / "X"
    src.mkdir()
    (src / "metadata.opf").write_text(
        lab_fs.build_metadata_xml({"id": 424242, "guid": "(OLD-GUID)", "name": "X", "desc": "d"}, []),
        encoding="utf-8",
    )
    client = _RecordingClient(dict(_UPLOAD_MOCK))
    lab_fs.upload_tree(client, target_id="1", server_path=str(src))

    checkins = [b for m, b in client.calls if m == "checkinSord" and isinstance(b.get("sord"), dict)]
    assert checkins
    for b in checkins:
        assert b["sord"].get("id") != 424242
        assert b["sord"].get("guid") != "(OLD-GUID)"
    # parse_metadata_xml keeps the source id/guid only for reference
    meta = lab_fs.parse_metadata_xml((src / "metadata.opf").read_text(encoding="utf-8"))
    assert meta["source_id"] == "424242" and meta["guid"] == "(OLD-GUID)"


def test_lab_fs_source_returns_real_files():
    src = lab_fs.lab_fs_source()
    assert any("lab_fs.py" in f["title"] for f in src["backend"])
    assert src["frontend"] and "lab-fs slice" in src["frontend"][0]["code"]
