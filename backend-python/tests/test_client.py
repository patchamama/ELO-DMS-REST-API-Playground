"""The shared teaching client: real transport shape + mock behaviour."""
import json

import httpx
import pytest

from elo_playground import EloError, MockEloClient
from elo_playground.client import EloClient


def _client(handler) -> EloClient:
    c = EloClient("http://elo.test/ix-Repository1", "Administrator", "secret")
    c._http.close()  # drop the real pool built in __init__
    c._http = httpx.Client(transport=httpx.MockTransport(handler), auth=("Administrator", "secret"))
    return c


def test_call_unwraps_result_envelope():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/ix-Repository1/rest/IXServicePortIF/getServerInfo"
        return httpx.Response(200, json={"result": {"version": "25.00.001.003"}})

    with _client(handler) as elo:
        assert elo.call("getServerInfo", {}) == {"version": "25.00.001.003"}


def test_call_raises_on_exception_envelope():
    def handler(_request):
        return httpx.Response(200, json={"exception": {"message": "objectNotFound [TICKET:abc] [DETAILS]"}})

    with _client(handler) as elo:
        with pytest.raises(EloError) as exc:
            elo.call("checkoutSord", {"objId": "1"})
    # the [TICKET:...] / [DETAILS] breadcrumbs are stripped
    assert "objectNotFound" in str(exc.value)
    assert "TICKET" not in str(exc.value)


def test_call_maps_401_to_auth_error():
    def handler(_request):
        return httpx.Response(401, text="nope")

    with _client(handler) as elo:
        with pytest.raises(EloError) as exc:
            elo.call("login", {})
    assert "authentication failed" in str(exc.value)


def test_find_all_drives_the_pagination_loop():
    pages = [
        {"result": {"searchId": "S1", "moreResults": True, "sords": [{"id": 1}, {"id": 2}]}},
        {"result": {"moreResults": True, "sords": [{"id": 3}]}},
        {"result": {"moreResults": False, "sords": [{"id": 4}]}},
        {"result": {}},  # findClose
    ]
    seen = []

    def handler(request: httpx.Request):
        seen.append(request.url.path.rsplit("/", 1)[-1])
        return httpx.Response(200, json=pages.pop(0))

    with _client(handler) as elo:
        rows = elo.find_all("findFirstSords", "findNextSords", "sords", {"max": 2})
    assert [r["id"] for r in rows] == [1, 2, 3, 4]
    assert seen == ["findFirstSords", "findNextSords", "findNextSords", "findClose"]


# ---- mock client ---------------------------------------------------- #
def test_mock_returns_configured_result():
    m = MockEloClient({"getServerInfo": {"version": "25.x"}})
    assert m.call("getServerInfo", {}) == {"version": "25.x"}


def test_mock_supports_result_and_exception_entries():
    m = MockEloClient({"a": {"result": 1}, "b": {"exception": "boom"}})
    assert m.call("a") == 1
    with pytest.raises(EloError):
        m.call("b")


def test_mock_consumes_list_entries_in_order():
    m = MockEloClient({"findNextSords": [{"moreResults": True}, {"moreResults": False}]})
    assert m.call("findNextSords")["moreResults"] is True
    assert m.call("findNextSords")["moreResults"] is False
    assert m.call("findNextSords")["moreResults"] is False  # last entry repeats


def test_mock_explains_a_missing_method():
    with pytest.raises(EloError) as exc:
        MockEloClient({}).call("getServerInfo")
    assert "no mock response configured" in str(exc.value)


def test_find_all_carries_the_z_selector_onto_findnext():
    seen: list[dict] = []

    def handler(request: httpx.Request):
        body = json.loads(request.content or b"{}")
        seen.append(body)
        name = request.url.path.rsplit("/", 1)[-1]
        if name == "findFirstSords":
            return httpx.Response(200, json={"result": {"searchId": "S", "moreResults": True, "sords": [{"id": 1}]}})
        if name == "findNextSords":
            return httpx.Response(200, json={"result": {"moreResults": False, "sords": [{"id": 2}]}})
        return httpx.Response(200, json={"result": {}})

    with _client(handler) as elo:
        elo.find_all("findFirstSords", "findNextSords", "sords", {"sordZ": {"bset": "42"}, "max": 1})
    next_body = next(b for b in seen if "idx" in b)
    assert next_body["sordZ"] == {"bset": "42"}  # selector carried forward


def test_mock_download_returns_configured_text():
    m = MockEloClient({"_download": {"version": 3}})
    assert b'"version": 3' in m.download("ignored")


def test_mock_upload_returns_token():
    assert MockEloClient({"_upload": "TOK"}).upload("url", b"data") == "TOK"
    assert MockEloClient({}).upload("url", b"data") == "MOCK-UPLOAD-TOKEN"
