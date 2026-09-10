"""Pydantic models shared across the API boundary."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

Lang = Literal["en", "de", "es"]
RunLanguage = Literal["python", "node", "browser", "go", "php", "java", "rhino"]
RuntimeName = Literal["python", "node", "browser", "go", "php", "java", "rhino"]


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
    go: str = ""
    php: str = ""
    java: str = ""
    rhino: str = ""


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
    lab_fs: bool = False        # render the interactive ELO <-> local filesystem panel


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


class RuntimeUpdateRequest(BaseModel):
    """Names are validated before the installer is ever reached."""

    runtimes: list[RuntimeName]
    enabled: bool = True


class ProxyRequest(BaseModel):
    method: str
    body: dict[str, Any] = {}
    mock: bool = True
    topic_id: str | None = None
    credentials: EloCreds | None = None


# ---- Testing lab: ELO <-> local filesystem panel (live only) ---------- #
class LabTreeRequest(BaseModel):
    """One level of the ELO folder tree, for lazy expansion."""

    parent_id: str = "1"                     # "1" = repository root
    credentials: EloCreds | None = None


class LabMirrorRequest(BaseModel):
    """Mirror an ELO subtree (folders + document bytes) into
    ``sandbox/elo-archiv-structure/`` and open it in the OS file manager."""

    folder_id: str
    folder_name: str | None = None           # becomes the top directory in the mirror
    credentials: EloCreds | None = None
    max_objects: int = 500
    max_bytes: int = 25 * 1024 * 1024


class LabUploadItem(BaseModel):
    rel_path: str                            # POSIX path relative to the picked folder root
    b64: str                                 # base64 of the file bytes


class LabUploadRequest(BaseModel):
    """Upload a local folder tree into a selected ELO folder. Exactly one
    source: ``server_path`` (walked on the backend) or ``items`` (browser-picked)."""

    target_id: str
    root_name: str | None = None             # top folder name in ELO; defaults to the local folder's name
    server_path: str | None = None
    items: list[LabUploadItem] = []
    credentials: EloCreds | None = None
    max_objects: int = 500
    max_bytes: int = 25 * 1024 * 1024
