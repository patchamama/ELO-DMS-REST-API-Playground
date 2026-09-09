"""elo-api-playground - a tiny teaching client for the ELO IX REST API.

Typical use inside a snippet::

    from elo_playground import connect

    elo = connect("http://localhost:9090/ix-Repository1", "Administrator", "elo")
    info = elo.call("getServerInfo", {})                  # one RPC call
    print(info["version"])

``connect()`` returns a real :class:`EloClient` - or a :class:`MockEloClient`
when ``ELOPG_MOCK`` is set - and has already called ``login()`` for you. For
each of ``base_url`` / ``user`` / ``password`` / ``verify`` the order is:
**explicit argument -> ELOPG_* environment variable -> built-in default**.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .client import EloClient
from .errors import EloError
from .mock import MockEloClient

__all__ = ["EloClient", "MockEloClient", "EloError", "connect", "attachment"]

# Defaults for a stock local ELO test install. Any ELOPG_* env var overrides
# these, so real deployments never rely on them - but a copied snippet still
# runs out of the box.
_DEFAULT_BASE_URL = "http://localhost:9090/ix-Repository1"
_DEFAULT_USER = "Administrator"
_DEFAULT_PASSWORD = "elo"


def connect(
    base_url: str | None = None,
    user: str | None = None,
    password: str | None = None,
    *,
    verify: bool | None = None,
    login: bool = True,
) -> "EloClient | MockEloClient":
    """Build a client and (by default) log in.

    Each of ``base_url`` / ``user`` / ``password`` / ``verify`` is taken from,
    in order: the explicit argument, then the matching ``ELOPG_*`` environment
    variable, then the built-in default for a stock local ELO test box
    (``http://localhost:9090/ix-Repository1`` / ``Administrator`` / ``elo``).

      ELOPG_MOCK           "1" / "true"   -> return a MockEloClient
      ELOPG_MOCK_DATA      path to the JSON mock map (the playground sets this)
      ELOPG_ELO_BASE_URL   ELOPG_ELO_USER   ELOPG_ELO_PASSWORD
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
        base_url=base_url or os.environ.get("ELOPG_ELO_BASE_URL") or _DEFAULT_BASE_URL,
        user=user or os.environ.get("ELOPG_ELO_USER") or _DEFAULT_USER,
        password=password or os.environ.get("ELOPG_ELO_PASSWORD") or _DEFAULT_PASSWORD,
        verify=(verify if verify is not None else not _falsy(os.environ.get("ELOPG_TLS_VERIFY"))),
    )
    if login:
        client.login()
    return client


def attachment() -> "tuple[str, bytes] | None":
    """The file the user picked with the topic's "Choose file" button, as
    ``(filename, bytes)`` - or ``None`` when nothing was picked (the snippet then
    falls back to a small built-in sample). The playground writes the upload to a
    temp file and points ``ELOPG_ATTACH`` at it.
    """
    path = os.environ.get("ELOPG_ATTACH")
    if not path or not Path(path).is_file():
        return None
    name = os.environ.get("ELOPG_ATTACH_NAME") or Path(path).name
    return name, Path(path).read_bytes()


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _falsy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"0", "false", "no", "off"}
