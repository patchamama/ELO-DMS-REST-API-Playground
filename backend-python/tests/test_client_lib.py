"""The /api/client-lib endpoint serves the shared client's source."""
from fastapi.testclient import TestClient

from app.client_lib import client_lib
from app.main import app

client = TestClient(app)


def test_client_lib_has_all_three_runtimes():
    lib = client_lib()
    assert lib["python"] and lib["node"] and lib["browser"]
    py_files = {f["title"] for f in lib["python"]}
    assert "elo_playground/client.py" in py_files
    assert any("def connect(" in f["code"] for f in lib["python"])
    assert any("class EloClient" in f["code"] for f in lib["node"])


def test_client_lib_endpoint():
    r = client.get("/api/client-lib")
    assert r.status_code == 200
    body = r.json()
    assert "connect" in "".join(f["code"] for f in body["python"])
