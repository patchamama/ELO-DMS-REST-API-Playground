"""End-to-end checks of the HTTP surface, all offline / mock."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_page_renders():
    r = client.get("/")
    assert r.status_code == 200
    assert "ELO API Playground" in r.text
    assert 'name="port"' in r.text
    assert 'data-view="faq"' in r.text


def test_version_endpoint():
    from app import __version__

    v = client.get("/api/version").json()
    assert v["backend"] == __version__
    assert v["frontend"] and v["frontend"][0].isdigit()


def test_faq_endpoint():
    r = client.get("/api/faq")
    assert r.status_code == 200
    md = r.json()["markdown"]
    assert "elo_playground" in md


def test_spec_op_has_elo_doc_url():
    ops = client.get("/api/spec/operations").json()["operations"]
    op_id = ops[0]["operation_id"]
    detail = client.get(f"/api/spec/op/{op_id}").json()
    assert detail["elo_doc_url"].startswith("{base}/rest/")


def test_catalog_endpoint():
    r = client.get("/api/catalog")
    assert r.status_code == 200
    cats = r.json()["categories"]
    assert any(c["id"] == "00-connection" for c in cats)


def test_topic_endpoint_and_404():
    r = client.get("/api/topics/connection.login")
    assert r.status_code == 200
    assert r.json()["snippets"]["python"]
    assert client.get("/api/topics/nope").status_code == 404


def test_run_python_in_mock_mode():
    r = client.post(
        "/api/run",
        json={"language": "python", "code": "print('ok', 1 + 1)", "mock": True},
    )
    body = r.json()
    assert body["ok"] is True
    assert "ok 2" in body["stdout"]


def test_run_browser_is_rejected_server_side():
    r = client.post("/api/run", json={"language": "browser", "code": "x", "mock": True})
    assert r.json()["ok"] is False
    assert "run in the page" in r.json()["detail"]


def test_proxy_returns_mock_result():
    r = client.post(
        "/api/elo/proxy",
        json={"method": "getServerInfo", "body": {}, "mock": True, "topic_id": "connection.server-info"},
    )
    assert r.json()["result"]["version"] == "25.00.001.003"


def test_proxy_reports_missing_mock_method_as_error():
    r = client.post("/api/elo/proxy", json={"method": "nonExistentCall", "mock": True})
    assert "error" in r.json()
