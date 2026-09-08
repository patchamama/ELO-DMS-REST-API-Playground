"""A deliberately small, heavily-commented client for the ELO IX REST API.

The ELO 25 "REST" API is really an RPC mapping of the SOAP ``IXServicePortIF``:

    POST {base_url}/rest/IXServicePortIF/<method>
    Content-Type: application/json
    Authorization: Basic <base64(user:password)>     <-- on EVERY request

    request body : a JSON object with the method's parameters ({} if none)
    response     : {"result": <value>}    on success
                   {"exception": <info>}  on a handled error (HTTP is still 200)

The authoritative request/response schema for *your* server is published by the
server itself at ``{base_url}/rest/openapi.json``.

This module exists to be read. It is synchronous (one call at a time), it keeps
a single ``httpx.Client`` alive so the login cookie and the Basic-auth header
ride along on every later call, and it turns every failure into one
:class:`EloError`.
"""
from __future__ import annotations

import re
from typing import Any

import httpx

from .errors import EloError

# Any short string is fine here - ELO just records it in the session log as the
# "client computer" that opened the session.
_CLIENT_NAME = "elo-api-playground"

# ClientInfo: the locale / timezone ELO should assume for this session. It only
# affects server-side formatting of a few values; "de / DE" matches a stock
# German ELO install.
_CI = {"language": "de", "country": "DE", "timeZone": "Europe/Berlin"}

# IX prefixes exception messages with breadcrumbs like "[TICKET:...] [DETAILS]".
_EX_NOISE = re.compile(r"\[TICKET:[^\]]*\]|\[(?:NO-)?DETAILS[^\]]*\]")


class EloClient:
    """One IX session. Create it, call :meth:`login`, then :meth:`call` anything."""

    def __init__(
        self,
        base_url: str,
        user: str,
        password: str,
        *,
        verify: bool = True,
        timeout: float = 30.0,
    ) -> None:
        # ``base_url`` is the IX repository root, e.g.
        #   http://localhost:9090/ix-Repository1
        # Everything else is derived from it.
        self.base_url = base_url.rstrip("/")
        self._rest = f"{self.base_url}/rest"
        self.user_name = user
        # Kept so :meth:`login` can send it in the request body. In production
        # code you would avoid holding the password longer than necessary.
        self._password = password

        # ONE connection pool for the whole session:
        #  * auth=(user, password) makes httpx attach "Authorization: Basic ..."
        #    to every request - exactly what IX wants.
        #  * the client keeps a cookie jar, so the JSESSIONID handed out by
        #    login() is sent back automatically on later calls.
        #  * verify=False is needed for ELO's usual self-signed internal HTTPS.
        self._http = httpx.Client(
            auth=(user, password),
            timeout=timeout,
            follow_redirects=True,
            verify=verify,
        )

        # Filled in by login(): the UserInfo of the account we logged in as
        # (id, name, group membership, flags, ...).
        self.user: dict[str, Any] | None = None

    # -- so snippets can write ``with EloClient(...) as elo:`` -------------- #
    def __enter__(self) -> "EloClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Release the connection pool. Always call this (or use the client as a
        context manager)."""
        self._http.close()

    # ---- the one method every other call goes through ------------------- #
    def call(self, method: str, body: dict | None = None, *, service: str = "IXServicePortIF") -> Any:
        """Make one IX RPC call and return its ``result``.

        ``method``  - e.g. "getServerInfo", "findFirstSords", "checkoutSord".
        ``body``    - the JSON parameters object for that method ({} if none).
        ``service`` - almost always "IXServicePortIF"; a handful of calls live
                      on side services such as "PackageService" or "LdapService".

        Raises :class:`EloError` on a transport failure, an HTTP error status,
        a non-JSON body, or an ``{"exception": ...}`` envelope.
        """
        url = f"{self._rest}/{service}/{method}"
        try:
            resp = self._http.post(url, json=body or {})
        except httpx.HTTPError as exc:
            # host unreachable, DNS failure, TLS error, timeout, ...
            raise EloError(f"{method}: request failed: {exc}") from exc

        if resp.status_code in (401, 403):
            raise EloError(
                f"{method}: authentication failed (HTTP {resp.status_code}) - check user / password"
            )
        if resp.status_code >= 400:
            raise EloError(f"{method}: HTTP {resp.status_code} - {resp.text[:200]}")

        try:
            data = resp.json()
        except ValueError as exc:
            raise EloError(f"{method}: response body was not JSON") from exc

        # IX reports a *handled* error with an "exception" object and HTTP 200.
        if isinstance(data, dict) and data.get("exception"):
            raise EloError(f"{method}: {_exception_text(data['exception'])}")
        # Normal success envelope.
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        # A few endpoints answer with a bare value.
        return data

    # ---- session ------------------------------------------------------- #
    def login(self) -> dict[str, Any]:
        """Open an IX session and return the logged-in ``UserInfo``.

        Basic auth alone is enough for many calls, but ``login`` is what
        allocates the server-side session (licence slot, session options, the
        search-id space used by every ``findFirst*``) - always call it first.
        """
        result = self.call(
            "login",
            {
                "userName": self.user_name,
                "userPwd": self._password,
                "clientComputer": _CLIENT_NAME,
                "runAsUser": "",
                "ci": _CI,
            },
        )
        # ELO 25 answers login with {"user": {...}, ...}; older shapes return
        # the UserInfo directly. Normalise to "the UserInfo".
        self.user = result.get("user") if isinstance(result, dict) and "user" in result else result
        return self.user

    def download(self, url: str, *, max_bytes: int = 200_000) -> bytes:
        """GET a document's bytes from a ``checkoutDoc`` download URL, reusing
        this authenticated session. Capped at ``max_bytes`` - meant for a
        bounded text preview (e.g. a config JSON), not for archival.

        The URL host is the archive's ``readdoc`` connector, which is often on a
        different port than IX and carries its own self-signed certificate - the
        client already runs with ``verify=False`` for that reason.
        """
        try:
            resp = self._http.get(url)
        except httpx.HTTPError as exc:
            raise EloError(f"download: request failed: {exc}") from exc
        if resp.status_code >= 400:
            raise EloError(f"download: HTTP {resp.status_code}")
        return resp.content[:max_bytes]

    def upload(self, url: str, data: bytes) -> str:
        """POST document bytes to a ``checkinDocBegin`` upload URL, reusing this
        authenticated session. Returns the server's upload-result token, which
        you then put into ``document.docs[0].uploadResult`` before
        ``checkinDocEnd``."""
        try:
            resp = self._http.post(url, content=data)
        except httpx.HTTPError as exc:
            raise EloError(f"upload: request failed: {exc}") from exc
        if resp.status_code >= 400:
            raise EloError(f"upload: HTTP {resp.status_code}")
        return resp.text

    # ---- the paginated-search helper --------------------------------- #
    def find_all(
        self,
        first: str,
        nxt: str,
        result_key: str,
        first_body: dict,
        *,
        page: int = 100,
    ) -> list:
        """Drive a ``findFirst<X>`` / ``findNext<X>`` / ``findClose`` loop to the
        end and return every row.

        ELO's search calls are stateful and paginated:

          1. findFirst<X>  -> first page + a ``searchId`` + a ``moreResults`` flag
          2. findNext<X>   -> the next page for that ``searchId``  (repeat)
          3. findClose     -> release the server-side search

        ``result_key`` is the field that holds the rows in the response, e.g.
        "sords" for findFirstSords, "sortedResult" for findFirstUsers.
        """
        # IX rejects a paged search that drops its "...Z" selector on findNext
        # ("Incorrect parameter: sordZ==null"), so carry those forward.
        carry = {k: v for k, v in first_body.items() if k.endswith("Z")}
        res = self.call(first, first_body)
        rows: list = list(_as_list(res.get(result_key))) if isinstance(res, dict) else []
        search_id = res.get("searchId") if isinstance(res, dict) else None
        try:
            while isinstance(res, dict) and res.get("moreResults"):
                res = self.call(nxt, {"searchId": search_id, "idx": len(rows), "max": page, **carry})
                chunk = _as_list(res.get(result_key)) if isinstance(res, dict) else []
                if not chunk:
                    break
                rows.extend(chunk)
        finally:
            if search_id:
                # Best effort: the search also times out server-side on its own.
                try:
                    self.call("findClose", {"searchId": search_id})
                except EloError:
                    pass
        return rows


# ---- small module-level helpers (shared with mock.py) ------------------ #
def _as_list(value: Any) -> list:
    """IX sometimes returns a list, sometimes an object keyed by index."""
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    return []


def _exception_text(exc: object) -> str:
    """Pull a readable message out of IX's exception object and strip its
    ``[TICKET:...]`` / ``[DETAILS]`` breadcrumbs."""
    if isinstance(exc, dict):
        text = exc.get("message") or exc.get("Exception") or str(exc)
    else:
        text = str(exc)
    return _EX_NOISE.sub("", text).strip()
