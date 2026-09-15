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
    lab_perms: bool = False     # render the interactive user/folder permissions panel
    lab_recent: bool = False    # render the recent-files browser panel
    lab_workflows: bool = False # render the workflow-usage panel


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


class LabRepositoryBrowseRequest(BaseModel):
    """Files below one folder of the configured local ELO repository."""

    folder: str = "Administration"


class LabRepositoryFileRequest(BaseModel):
    """A repository-relative file path selected in the Test Lab browser."""

    path: str


# ---- Testing lab: user/folder permissions panel (live only) ---------- #
class LabPrincipal(BaseModel):
    kind: Literal["user", "group"]
    id: str


class LabPermPrincipalsRequest(BaseModel):
    """Groups + users for the left panel, plus who the connected session is."""

    credentials: EloCreds | None = None


class LabPermMembersRequest(BaseModel):
    """First N members of a group, plus the total member count."""

    group_id: str
    preview: int = 10
    credentials: EloCreds | None = None


class LabPermSubtreeRequest(BaseModel):
    """Children of ``parent_id``, annotated with the resolved access of
    ``principal``, recursed up to ``depth`` levels. ``depth: 1`` serves a
    manual one-level expand; a larger ``depth`` serves auto-expand-on-select."""

    parent_id: str = "1"                     # "1" = repository root
    principal: LabPrincipal
    depth: int = 1
    max_nodes: int = 1500                    # one findFirstSords per level, so this is cheap
    credentials: EloCreds | None = None


class LabPermFolderPrincipalsRequest(BaseModel):
    """Every group/user's resolved access to one folder - the reverse
    "who can see this" view."""

    folder_id: str
    credentials: EloCreds | None = None


class LabPermSpecialRequest(BaseModel):
    """Folders below ``parent_id`` whose effective ACL departs from their
    parent's ("special permissions"), recursed up to ``depth`` levels."""

    parent_id: str = "1"
    depth: int = 3
    max_nodes: int = 1500
    credentials: EloCreds | None = None


class LabPermDiagnoseRequest(BaseModel):
    """ACL findings below ``parent_id`` (orphan entries, admin-only folders,
    write-without-read, ...), recursed up to ``depth`` levels."""

    parent_id: str = "1"
    depth: int = 3
    max_nodes: int = 1500
    credentials: EloCreds | None = None


class LabPermOrgChartRequest(BaseModel):
    """Groups with their parent groups and users with their direct groups
    and supervisor - the data behind the org chart."""

    credentials: EloCreds | None = None


class LabPermFolderAclRequest(BaseModel):
    """One folder's ACL, decoded, optionally with how ``principal`` resolves
    against it - what the panel prints in its log when a folder is clicked."""

    folder_id: str
    principal: LabPrincipal | None = None
    credentials: EloCreds | None = None


# ---- Testing lab: recent files + workflow usage (live only) ----------- #
class LabRecentFilesRequest(BaseModel):
    """Newest documents in ``folder_id`` or any subfolder."""

    folder_id: str = "1"
    limit: int = 50
    max_scan: int = 6000                     # rows walked through the date windows at most
    pattern: str | None = None               # "*.js, *.json" - matched against name.ext
    credentials: EloCreds | None = None


class LabFilePreviewRequest(BaseModel):
    doc_id: str
    max_bytes: int = 2 * 1024 * 1024
    credentials: EloCreds | None = None


class LabWorkflowUsageRequest(BaseModel):
    limit: int = 25
    credentials: EloCreds | None = None
