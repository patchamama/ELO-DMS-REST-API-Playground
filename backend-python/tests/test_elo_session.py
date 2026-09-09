"""The TTL client cache keys on the TLS-verify setting too, so toggling
"Verify TLS certificate" in the UI never hands back a stale client."""
import app.elo_session as es


class _FakeClient:
    def __init__(self, base_url, user, password, *, verify=True):
        self.base_url, self.user, self.password, self.verify = base_url, user, password, verify
        self.user_obj = {"name": user}

    def login(self):
        self.user = self.user_obj

    def close(self):
        pass


def test_get_client_caches_per_verify_flag(monkeypatch):
    monkeypatch.setattr(es, "EloClient", _FakeClient)
    monkeypatch.setattr(es, "_cache", {})

    secure = es.get_client("http://elo:9090/ix", "u", "p", verify=True)
    insecure = es.get_client("http://elo:9090/ix", "u", "p", verify=False)

    assert secure is not insecure
    assert secure.verify is True and insecure.verify is False
    # asking again returns each side's own cached client
    assert es.get_client("http://elo:9090/ix", "u", "p", verify=False) is insecure
    assert es.get_client("http://elo:9090/ix", "u", "p", verify=True) is secure
