"""A small TTL cache of logged-in :class:`EloClient` instances.

Used by the browser proxy endpoint (``POST /api/elo/proxy``) so a run of many
small browser calls does not re-login on every request. Mirrors ELOphant's
``app/elo_session.py`` (300 s TTL, small cap), trimmed to the sync teaching client.
"""
from __future__ import annotations

import hashlib
import sys
import threading
import time
from pathlib import Path

# Make the shared teaching client importable (it lives outside this package).
_SHARED_PY = Path(__file__).resolve().parent.parent.parent / "shared" / "python"
if str(_SHARED_PY) not in sys.path:
    sys.path.insert(0, str(_SHARED_PY))

from elo_playground import EloClient, EloError, MockEloClient  # noqa: E402

__all__ = ["get_client", "mock_client", "EloError"]

_TTL_SECONDS = 300.0
_MAX_ENTRIES = 16

_lock = threading.Lock()
_cache: dict[str, tuple[float, EloClient]] = {}


def _key(base_url: str, user: str, password: str) -> str:
    return hashlib.sha256(f"{base_url}\0{user}\0{password}".encode()).hexdigest()


def get_client(base_url: str, user: str, password: str, *, verify: bool = True) -> EloClient:
    """Return a cached logged-in client, creating (and logging in) one if needed."""
    now = time.time()
    k = _key(base_url, user, password)
    with _lock:
        hit = _cache.get(k)
        if hit and now - hit[0] < _TTL_SECONDS:
            return hit[1]
        for dead in [kk for kk, (ts, _) in _cache.items() if now - ts >= _TTL_SECONDS]:
            _drop(dead)
        if len(_cache) >= _MAX_ENTRIES:
            _drop(min(_cache, key=lambda kk: _cache[kk][0]))

    client = EloClient(base_url, user, password, verify=verify)
    client.login()  # raises EloError on bad host / credentials - caller handles it
    with _lock:
        _cache[k] = (time.time(), client)
    return client


def mock_client(data: dict) -> MockEloClient:
    c = MockEloClient(data)
    c.login()
    return c


def _drop(k: str) -> None:
    entry = _cache.pop(k, None)
    if entry:
        try:
            entry[1].close()
        except Exception:  # noqa: BLE001 - closing a stale client must not raise
            pass
