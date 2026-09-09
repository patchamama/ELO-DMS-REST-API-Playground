"""Pydantic models shared across the API boundary."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

Lang = Literal["en", "de", "es"]
RunLanguage = Literal["python", "node", "browser"]


class EloCreds(BaseModel):
    base_url: str
    user: str
    password: str = ""
    tls_verify: bool = True


class ApiRef(BaseModel):
    """One ELO IX method a topic uses, with a pointer into the docs."""

    method: str            # e.g. "findFirstSords"
    rpc: str               # e.g. "POST /rest/IXServicePortIF/findFirstSords"
    doc_url: str           # link to the schema / Swagger UI ({base} is substituted client-side)
    spec: str = ""         # operationId to search for in openapi.json
    notes: str = ""


class Snippets(BaseModel):
    python: str = ""
    node: str = ""
    browser: str = ""


class Topic(BaseModel):
    id: str
    category_id: str
    category: str
    order: int = 0
    title: str
    summary: str = ""
    elo_api: list[ApiRef] = []
    result_shape: str = ""
    snippets: Snippets = Snippets()
    mock: dict[str, Any] = {}
    attach_file: bool = False   # show a "Choose file" button on this topic


class Attachment(BaseModel):
    """A file the user picked with the topic's "Choose file" button."""

    name: str
    b64: str   # base64 of the file bytes


class RunRequest(BaseModel):
    language: RunLanguage
    code: str
    mock: bool = True
    topic_id: str | None = None
    credentials: EloCreds | None = None
    attachment: Attachment | None = None


class RunResult(BaseModel):
    ok: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration_ms: int = 0
    detail: str = ""       # runner-level problem (timeout, node backend down, ...)


class ProxyRequest(BaseModel):
    method: str
    body: dict[str, Any] = {}
    mock: bool = True
    topic_id: str | None = None
    credentials: EloCreds | None = None
