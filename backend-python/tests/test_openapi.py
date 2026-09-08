"""The 'API reference' backend: parse the sample openapi.json + generate calls."""
from fastapi.testclient import TestClient

from app import openapi_ref
from app.main import app

client = TestClient(app)
SPEC = openapi_ref.load_spec(None, mock=True)  # the trimmed sample


def test_sample_spec_loads():
    info = openapi_ref.spec_info(SPEC)
    assert info["version"]
    assert info["operations"] >= 10
    assert info["sample"] is True


def test_services_lists_ixserviceportif():
    svcs = {s["service"]: s["count"] for s in openapi_ref.services(SPEC)}
    assert svcs.get("IXServicePortIF", 0) > 0


def test_operations_have_ids_and_paths():
    ops = openapi_ref.operations(SPEC, "IXServicePortIF")
    assert ops
    for o in ops:
        assert o["operation_id"] and o["path"].startswith("/IXServicePortIF/")
        assert o["http_method"] == "POST"


def test_operation_detail_resolves_request_props():
    d = openapi_ref.operation_detail(SPEC, "IXServicePortIF_login")
    assert d is not None
    names = {p["name"] for p in d["request_props"]}
    assert {"userName", "userPwd"} <= names


def test_nested_ref_props_are_expanded_one_level():
    d = openapi_ref.operation_detail(SPEC, "IXServicePortIF_findFirstSords")
    find_info = next(p for p in d["request_props"] if p["name"] == "findInfo")
    assert find_info["ref"] == "FindInfo"
    child_names = {f["name"] for f in find_info["fields"]}
    assert "findByIndex" in child_names  # one level deep


def test_response_props_come_from_the_result_wrapper():
    d = openapi_ref.operation_detail(SPEC, "IXServicePortIF_login")
    assert d["result_ref"] == "LoginResult"
    assert d["response_props"], "expected the LoginResult fields"


def test_used_by_links_back_to_catalogue():
    d = openapi_ref.operation_detail(SPEC, "IXServicePortIF_findFirstSords")
    ids = {u["id"] for u in d["used_by"]}
    assert "repository.folder-children" in ids


def test_z_selector_gets_a_bset_placeholder():
    d = openapi_ref.operation_detail(SPEC, "IXServicePortIF_findFirstSords")
    py = openapi_ref.generate(d, "python")
    assert '"sordZ": { "bset": "0" }' in py


def test_generate_python_and_node():
    d = openapi_ref.operation_detail(SPEC, "IXServicePortIF_login")
    py = openapi_ref.generate(d, "python")
    assert 'elo.call("login"' in py and "userName" in py and "connect()" in py
    node = openapi_ref.generate(d, "node")
    assert 'await elo.call("login"' in node and 'import { connect }' in node
    browser = openapi_ref.generate(d, "browser")
    assert "import" not in browser and "await connect()" in browser


def test_non_default_service_adds_service_arg():
    ops = openapi_ref.operations(SPEC)
    non_ix = next((o for o in ops if o["service"] != "IXServicePortIF"), None)
    if non_ix is None:
        return  # the sample happens to only carry IXServicePortIF
    d = openapi_ref.operation_detail(SPEC, non_ix["operation_id"])
    assert non_ix["service"] in openapi_ref.generate(d, "python")


# ---- HTTP endpoints ------------------------------------------------- #
def test_spec_services_endpoint():
    r = client.get("/api/spec/services?mock=1")
    body = r.json()
    assert body["info"]["sample"] is True
    assert any(s["service"] == "IXServicePortIF" for s in body["services"])


def test_spec_operations_endpoint():
    r = client.get("/api/spec/operations?mock=1&service=IXServicePortIF")
    assert any(o["method"] == "login" for o in r.json()["operations"])


def test_spec_op_endpoint_returns_snippets():
    r = client.get("/api/spec/op/IXServicePortIF_login?mock=1")
    d = r.json()
    assert set(d["snippets"]) == {"python", "node", "browser"}
    assert client.get("/api/spec/op/Nope_nope?mock=1").status_code == 404


def test_generated_login_snippet_runs_in_mock():
    op = client.get("/api/spec/op/IXServicePortIF_login?mock=1").json()
    r = client.post("/api/run", json={"language": "python", "code": op["snippets"]["python"], "mock": True})
    assert r.json()["ok"] is True
