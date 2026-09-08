"""Offline stand-in for :class:`EloClient`.

Same method surface, but :meth:`call` reads a canned response from a JSON map
instead of touching the network - so every example in the playground can run and
produce output on a machine with no ELO reachable (or with no credentials).

The JSON map is ``{ "<method>": <entry>, ... }`` where ``<entry>`` is one of:

  * the ``result`` value directly           -> returned as-is
  * ``{"result": <value>}``                 -> ``<value>`` is returned
  * ``{"exception": "<message>"}``           -> raises :class:`EloError`
  * a list of any of the above              -> consumed one entry per call,
                                               the last entry repeating

The map is assembled by the playground from ``fixtures/ix/default.json`` plus the
current topic's ``mock:`` block.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .client import _as_list
from .errors import EloError


class MockEloClient:
    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = data or {}
        self._calls: dict[str, int] = {}          # per-method call counter (for list entries)
        self.base_url = "mock://elo"
        self.user_name = "Administrator"
        self.user: dict[str, Any] | None = None

    def __enter__(self) -> "MockEloClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:  # nothing to release
        return None

    @classmethod
    def from_file(cls, path: str | Path) -> "MockEloClient":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def call(self, method: str, body: dict | None = None, *, service: str = "IXServicePortIF") -> Any:
        if method not in self._data:
            raise EloError(
                f"{method}: no mock response configured "
                f"- add it to the topic's 'mock:' block or fixtures/ix/default.json"
            )
        entry = self._data[method]
        if isinstance(entry, list):
            i = min(self._calls.get(method, 0), len(entry) - 1)
            self._calls[method] = i + 1
            entry = entry[i]
        if isinstance(entry, dict) and "exception" in entry:
            raise EloError(f"{method}: {entry['exception']}")
        if isinstance(entry, dict) and "result" in entry:
            return entry["result"]
        return entry

    def download(self, url: str, *, max_bytes: int = 200_000) -> bytes:
        entry = self._data.get("_download", '{"version": 3, "ocr": true}')
        text = entry if isinstance(entry, str) else json.dumps(entry)
        return text.encode("utf-8")[:max_bytes]

    def upload(self, url: str, data: bytes) -> str:
        return self._data.get("_upload", "MOCK-UPLOAD-TOKEN")

    def login(self) -> dict[str, Any]:
        raw = self.call("login", {}) if "login" in self._data else {"id": 0, "name": "Administrator"}
        self.user = raw.get("user") if isinstance(raw, dict) and "user" in raw else raw
        return self.user

    def find_all(
        self,
        first: str,
        nxt: str,
        result_key: str,
        first_body: dict,
        *,
        page: int = 100,
    ) -> list:
        # Same loop shape as the real client so snippet output is identical.
        carry = {k: v for k, v in first_body.items() if k.endswith("Z")}
        res = self.call(first, first_body)
        rows: list = list(_as_list(res.get(result_key))) if isinstance(res, dict) else []
        search_id = res.get("searchId") if isinstance(res, dict) else None
        while isinstance(res, dict) and res.get("moreResults"):
            res = self.call(nxt, {"searchId": search_id, "idx": len(rows), "max": page, **carry})
            chunk = _as_list(res.get(result_key)) if isinstance(res, dict) else []
            if not chunk:
                break
            rows.extend(chunk)
        if search_id and "findClose" in self._data:
            self.call("findClose", {"searchId": search_id})
        return rows
