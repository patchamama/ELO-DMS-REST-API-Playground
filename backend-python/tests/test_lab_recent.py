"""Unit tests for app.lab_recent (newest files below a folder + preview) and
app.lab_workflows (template usage). MockEloClient consumes list-valued mock
entries one item per call, in call order."""
import base64
import io
import zipfile
from datetime import datetime

from elo_playground import MockEloClient

from app import lab_recent, lab_workflows

NOW = datetime(2026, 9, 16, 12, 0, 0)


def _doc(oid, name, idate, *, path=(), parent=None, ext="txt", size=10, typ=254):
    return {"id": oid, "name": name, "type": typ, "IDateIso": idate, "parentId": parent or (path[-1][0] if path else 1),
            "ownerName": "Administrator", "docVersion": {"ext": ext, "size": size},
            "refPaths": [{"path": [{"id": i, "name": n} for i, n in path]}]}


def _page(rows, more=False, sid="(S)"):
    return {"searchId": sid, "moreResults": more, "sords": rows}


def test_recent_files_walks_windows_newest_first_and_filters_by_path():
    # windows: 1d (empty), 3d (empty), 7d (two docs, one outside folder 2),
    # 14d (one more) -> limit 2 reached after the 14d window is exhausted.
    client = MockEloClient({
        "findFirstSords": [
            _page([]), _page([]),
            _page([_doc(11, "a", "20260912100000", path=((2, "Administration"), (5, "Sub")), ext="js"),
                   _doc(12, "elsewhere", "20260913100000", path=((9, "Sales"),))]),
            _page([_doc(13, "b", "20260905100000", path=((2, "Administration"),), typ=297)]),
        ],
        "findClose": {},
        "checkoutSord": {"sord": {"id": 2, "name": "Administration"}},
    })
    res = lab_recent.recent_files(client, "2", limit=2, now=NOW)
    assert res["folder"] == {"id": "2", "name": "Administration"}
    assert [r["name"] for r in res["rows"]] == ["a", "b"]
    assert res["rows"][0]["path"] == "Administration / Sub" and res["rows"][0]["modified"] == "2026-09-12 10:00"
    assert res["rows"][0]["ext"] == "js" and res["scanned"] == 3 and res["complete"] is True
    assert res["oldest_scanned"] == "2026-09-02 12:00"    # the 14-day window's start


def test_recent_files_root_takes_everything_and_skips_folders_and_duplicates():
    client = MockEloClient({
        "findFirstSords": [_page([_doc(1, "doc", "20260916090000"), _doc(1, "doc", "20260916090000"),
                                  _doc(2, "folder", "20260916090000", typ=1)])],
        "findClose": {},
        "checkoutSord": {"sord": {"id": 1, "name": "Contelo"}},
    })
    res = lab_recent.recent_files(client, "1", limit=5, now=NOW)
    assert [r["id"] for r in res["rows"]] == ["1"]


def test_recent_files_reports_an_exhausted_budget_as_incomplete():
    # first window has moreResults but the budget (2 rows) is gone
    client = MockEloClient({
        "findFirstSords": [_page([_doc(1, "x", "20260916090000"), _doc(2, "y", "20260916080000")], more=True)],
        "findNextSords": [_page([_doc(3, "z", "20260916070000")], more=True)],
        "findClose": {},
        "checkoutSord": {"sord": {"id": 1, "name": "Contelo"}},
    })
    res = lab_recent.recent_files(client, "1", limit=50, max_scan=2, now=NOW)
    assert res["complete"] is False and len(res["rows"]) == 2


def test_recent_files_pages_with_findnext():
    client = MockEloClient({
        "findFirstSords": [_page([_doc(1, "x", "20260916090000")], more=True)],
        "findNextSords": [_page([_doc(2, "y", "20260916080000")], more=False)],
        "findClose": {},
        "checkoutSord": {"sord": {"id": 1, "name": "Contelo"}},
    })
    res = lab_recent.recent_files(client, "1", limit=50, now=NOW)
    assert [r["name"] for r in res["rows"]] == ["x", "y"] and res["complete"] is True


def test_decode_text_handles_bom_utf16_and_cp1252():
    assert lab_recent._decode_text("héllo".encode("utf-8-sig")) == "héllo"
    assert lab_recent._decode_text("<a/>".encode("utf-16-le")) == "<a/>"
    assert lab_recent._decode_text("<a/>".encode("utf-16")) == "<a/>"
    assert lab_recent._decode_text("Grüße".encode("cp1252")) == "Grüße"


def _docx_bytes(paragraphs):
    xml = '<?xml version="1.0"?><w:document><w:body>' + "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs) + "</w:body></w:document>"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


def test_docx_text_extracts_paragraphs():
    assert lab_recent.docx_text(_docx_bytes(["Hello", "World &amp; co"])) == "Hello\nWorld & co"


def _preview_client(data, ext):
    client = MockEloClient({
        "checkoutSord": {"sord": {"id": 7, "name": "file", "IDateIso": "20260101120000", "docVersion": {"ext": ext, "size": len(data)},
                                  "refPaths": [{"path": [{"id": 2, "name": "Administration"}]}]}},
        "checkoutDoc": {"document": {"docs": [{"url": "http://mock/dl/7", "ext": ext}]}},
        "_download": data.decode("latin-1") if isinstance(data, bytes) and ext != "docx" else "",
    })
    if ext in ("docx", "pdf", "png"):
        client.download = lambda url, max_bytes=0: data      # binary payloads
    return client


def test_file_preview_shapes_text_docx_pdf_and_binary():
    text = lab_recent.file_preview(_preview_client(b'{"a": 1}', "json"), 7)
    assert (text["kind"], text["language"], text["text"], text["path"]) == ("text", "json", '{"a": 1}', "Administration")
    docx = lab_recent.file_preview(_preview_client(_docx_bytes(["Para"]), "docx"), 7)
    assert (docx["kind"], docx["text"]) == ("docx", "Para")
    pdf = lab_recent.file_preview(_preview_client(b"%PDF-1.7 x", "pdf"), 7)
    assert pdf["kind"] == "pdf" and base64.b64decode(pdf["b64"]) == b"%PDF-1.7 x" and pdf["content_type"] == "application/pdf"
    png = lab_recent.file_preview(_preview_client(b"\x89PNG\x00\x00", "png"), 7)
    assert png["kind"] == "image" and png["content_type"] == "image/png"
    exe = lab_recent.file_preview(_preview_client(b"MZ\x00\x00\x00\x01", "exe"), 7)
    assert exe["kind"] == "binary"


def test_file_preview_without_content_is_binary():
    client = MockEloClient({"checkoutSord": {"sord": {"id": 7, "name": "folderish"}}, "checkoutDoc": {"document": {"docs": []}}})
    assert lab_recent.file_preview(client, 7)["kind"] == "binary"


# --------------------------------------------------------------------------- #
#  workflows
# --------------------------------------------------------------------------- #
def test_top_workflows_counts_instances_per_template():
    client = MockEloClient({
        "findFirstWorkflows": [
            {"searchId": "(T)", "moreResults": False, "workflows": [
                {"id": 55, "name": "extend", "ownerName": "Admin", "version": {"version": "3.0"},
                 "nodes": [{"id": 0, "comment": "Extend a contract"}, {"id": 1}]},
                {"id": 60, "name": "banf", "ownerName": "Admin", "version": {"version": "1.0"}, "nodes": [{"id": 0}]},
            ]},
            {"searchId": "(A)", "moreResults": False, "workflows": [
                {"id": 1, "templateId": 55, "templateName": "extend", "startDateIso": "20260819111600", "objName": "CD8"},
            ]},
            {"searchId": "(F)", "moreResults": True, "workflows": [
                {"id": 2, "templateId": 55, "templateName": "extend", "startDateIso": "20260301090000", "objName": "CD3"},
            ]},
        ],
        "findNextWorkflows": [
            {"searchId": "(F)", "moreResults": False, "workflows": [
                {"id": 3, "templateId": 99, "templateName": "gone", "startDateIso": "20250101000000", "objName": "old"},
            ]},
        ],
        "findClose": {},
    })
    res = lab_workflows.top_workflows(client, limit=25)
    assert res["totals"] == {"templates": 2, "active": 1, "finished": 2, "used_templates": 2}
    top, gone, unused = res["rows"]
    assert (top["name"], top["count"], top["active"], top["finished"]) == ("extend", 2, 1, 1)
    assert top["last_used"] == "2026-08-19 11:16" and top["last_object"] == "CD8" and top["first_used"] == "2026-03-01 09:00"
    assert top["description"] == "Extend a contract" and top["nodes"] == 2 and top["version"] == "3.0"
    assert gone["name"] == "gone" and gone["template_exists"] is False and gone["count"] == 1
    assert unused["name"] == "banf" and unused["count"] == 0 and unused["last_used"] == ""


def test_lab_sources_return_real_files():
    src = lab_recent.lab_recent_source()
    assert any("lab_recent.py" in f["title"] for f in src["backend"]) and "lab-recent slice" in src["frontend"][0]["code"]
    src = lab_workflows.lab_workflows_source()
    assert any("lab_workflows.py" in f["title"] for f in src["backend"]) and "lab-workflows slice" in src["frontend"][0]["code"]
