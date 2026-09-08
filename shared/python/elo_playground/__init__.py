"""elo-api-playground - a tiny teaching client for the ELO IX REST API.

Typical use inside a snippet::

    from elo_playground import connect

    elo = connect()                        # reads connection settings from the environment
    info = elo.call("getServerInfo", {})   # one RPC call
    print(info["version"])

``connect()`` returns a real :class:`EloClient` - or a :class:`MockEloClient`
when ``ELOPG_MOCK`` is set - and has already called ``login()`` for you.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .client import EloClient
from .errors import EloError
from .mock import MockEloClient

__all__ = ["EloClient", "MockEloClient", "EloError", "connect"]

_DEFAULT_BASE_URL = "http://localhost:9090/ix-Repository1"


def connect(*, login: bool = True) -> "EloClient | MockEloClient":
    """Build a client from environment variables and (by default) log in.

    Environment - all optional, with sensible defaults for a local ELO:

      ELOPG_MOCK           "1" / "true"   -> return a MockEloClient
      ELOPG_MOCK_DATA      path to the JSON mock map (the playground sets this)
      ELOPG_ELO_BASE_URL   default http://localhost:9090/ix-Repository1
      ELOPG_ELO_USER       default "Administrator"
      ELOPG_ELO_PASSWORD   default ""  (empty)
      ELOPG_TLS_VERIFY     "0" -> skip TLS verification (self-signed ELO certs)
    """
    if _truthy(os.environ.get("ELOPG_MOCK")):
        data: dict[str, Any] = {}
        path = os.environ.get("ELOPG_MOCK_DATA")
        if path and Path(path).is_file():
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        client = MockEloClient(data)
        if login:
            client.login()
        return client

    client = EloClient(
        base_url=os.environ.get("ELOPG_ELO_BASE_URL", _DEFAULT_BASE_URL),
        user=os.environ.get("ELOPG_ELO_USER", "Administrator"),
        password=os.environ.get("ELOPG_ELO_PASSWORD", ""),
        verify=not _falsy(os.environ.get("ELOPG_TLS_VERIFY")),
    )
    if login:
        client.login()
    return client


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _falsy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"0", "false", "no", "off"}
