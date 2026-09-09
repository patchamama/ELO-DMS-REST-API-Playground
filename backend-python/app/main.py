"""FastAPI entrypoint: the page, the catalogue API, the snippet runner, the
browser -> ELO proxy.

Run it with::

    cd backend-python
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8010

or ``python -m app.main``.
"""
from __future__ import annotations

import hashlib
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from . import __version__ as BACKEND_VERSION
from . import catalog as catalog_mod
from . import openapi_ref
from .client_lib import client_lib
from .config import get_settings
from .elo_session import EloError, get_client, mock_client
from .i18n import catalogue
from .lab_fs import lab_fs_source, list_children, mirror_to_sandbox, upload_tree
from .models import (
    EloCreds,
    LabMirrorRequest,
    LabTreeRequest,
    LabUploadRequest,
    ProxyRequest,
    RunRequest,
    RunResult,
)
from .runner import mock_data, run

settings = get_settings()

_ver_file = settings.frontend_dir / "VERSION"
FRONTEND_VERSION = _ver_file.read_text(encoding="utf-8").strip() if _ver_file.is_file() else "0"

app = FastAPI(title="ELO API Playground", version=BACKEND_VERSION)

# The browser run-sandbox is an <iframe srcdoc> with an opaque ("null") origin;
# its fetch() to /api/elo/proxy is therefore cross-origin. This is a local
# learning tool bound to localhost, so a permissive CORS policy is acceptable.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(settings.frontend_dir / "templates"))

app.mount("/static", StaticFiles(directory=str(settings.frontend_dir / "static")), name="static")
app.mount("/vendor", StaticFiles(directory=str(settings.frontend_dir / "vendor")), name="vendor")
# The browser client module, served straight from shared/browser/.
app.mount("/client", StaticFiles(directory=str(settings.shared_browser)), name="client")


def _static_version() -> str:
    """Hash of the newest mtime under frontend/static - a cache-bust token."""
    newest = 0.0
    for p in (settings.frontend_dir / "static").glob("**/*"):
        if p.is_file():
            newest = max(newest, p.stat().st_mtime)
    return hashlib.sha1(str(newest).encode()).hexdigest()[:8]


def _default_port() -> str:
    return str(urlsplit(settings.elo_base_url).port or 9090)


# ---- page ------------------------------------------------------------- #
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "static_v": _static_version(),
            "default_base_url": settings.elo_base_url,
            "default_port": _default_port(),
            "default_user": settings.elo_user,
            # pre-fill the password only from a LOCAL .env (never baked into the
            # static build); empty by default so nothing is shipped.
            "default_password": settings.elo_password,
            "mock_default": settings.mock,
        },
    )


@app.get("/api/version")
def api_version():
    return {"backend": BACKEND_VERSION, "frontend": FRONTEND_VERSION}


@app.get("/api/faq")
def api_faq():
    """The FAQ page (Markdown), rendered client-side in the FAQ tab."""
    p = settings.frontend_dir / "faq.md"
    return {"markdown": p.read_text(encoding="utf-8") if p.is_file() else ""}


# ---- catalogue ------------------------------------------------------- #
@app.get("/api/i18n/{lang}")
def api_i18n(lang: str):
    return catalogue(lang)


@app.get("/api/catalog")
def api_catalog(lang: str = "en"):
    return {"categories": catalog_mod.categories(lang)}


@app.get("/api/topics/{topic_id}")
def api_topic(topic_id: str, lang: str = "en"):
    topic = catalog_mod.get_topic(topic_id, lang)
    if topic is None:
        raise HTTPException(404, f"unknown topic: {topic_id}")
    return topic.model_dump()


@app.get("/api/deep/{category_id}")
def api_deep(category_id: str):
    md = catalog_mod.deep_doc(category_id)
    if md is None:
        raise HTTPException(404, f"no deep-dive for category: {category_id}")
    return {"category_id": category_id, "markdown": md}


@app.get("/api/client-lib")
def api_client_lib():
    """Source of the shared elo_playground teaching client (all three runtimes)."""
    return client_lib()


# ---- openapi.json reference ("API reference" tab) ---------------- #
def _spec(mock: bool, base_url: str | None):
    return openapi_ref.load_spec(base_url or settings.elo_base_url, mock=mock)


@app.get("/api/spec/services")
def api_spec_services(mock: bool = True, base_url: str | None = None):
    spec = _spec(mock, base_url)
    return {"info": openapi_ref.spec_info(spec), "services": openapi_ref.services(spec)}


@app.get("/api/spec/operations")
def api_spec_operations(service: str | None = None, mock: bool = True, base_url: str | None = None):
    return {"operations": openapi_ref.operations(_spec(mock, base_url), service)}


@app.get("/api/spec/op/{operation_id}")
def api_spec_op(operation_id: str, mock: bool = True, base_url: str | None = None):
    detail = openapi_ref.operation_detail(_spec(mock, base_url), operation_id)
    if detail is None:
        raise HTTPException(404, f"unknown operation: {operation_id}")
    detail["snippets"] = {lang: openapi_ref.generate(detail, lang) for lang in ("python", "node", "browser")}
    return detail


# ---- runner -------------------------------------------------------- #
@app.post("/api/run", response_model=RunResult)
def api_run(req: RunRequest):
    return run(req)


# ---- browser -> ELO proxy --------------------------------------- #
@app.post("/api/elo/proxy")
def api_proxy(req: ProxyRequest):
    """One RPC call on behalf of a browser snippet. Never raises across the
    boundary - returns ``{"result": ...}`` or ``{"error": "..."}``."""
    try:
        if req.mock:
            client = mock_client(mock_data(req.topic_id))
        else:
            if not req.credentials:
                return {"error": "mock mode is off and no credentials were provided"}
            client = get_client(
                req.credentials.base_url,
                req.credentials.user,
                req.credentials.password,
                verify=req.credentials.tls_verify,
            )
        # The proxy already holds a logged-in session (get_client / mock_client
        # both log in). Do not forward login/logout: a body-less "login" RPC is
        # rejected by IX, and "logout" would drop the shared cached session
        # other browser calls in the same run still need.
        if req.method == "login":
            return {"result": {"user": client.user}}
        if req.method == "logout":
            return {"result": {}}
        return {"result": client.call(req.method, req.body)}
    except EloError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - a browser call must not 500 the app
        return {"error": f"{type(exc).__name__}: {exc}"}


# ---- Testing lab: ELO <-> local filesystem (live only) ---------- #
def _lab_client(creds: EloCreds | None):
    if not creds or not creds.base_url:
        raise EloError(
            "live mode required - untick Mock, fill in the connection form and press Check connection"
        )
    return get_client(creds.base_url, creds.user, creds.password, verify=creds.tls_verify)


def _lab_guard(fn):
    """Run *fn* and turn any failure into ``{"error": "..."}`` (never a 500)."""
    try:
        return fn()
    except EloError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - a lab call must not 500 the app
        return {"error": f"{type(exc).__name__}: {exc}"}


@app.post("/api/lab/elo-children")
def api_lab_children(req: LabTreeRequest):
    return _lab_guard(lambda: {"rows": list_children(_lab_client(req.credentials), req.parent_id)})


@app.post("/api/lab/mirror")
def api_lab_mirror(req: LabMirrorRequest):
    return _lab_guard(
        lambda: mirror_to_sandbox(
            _lab_client(req.credentials),
            req.folder_id,
            folder_name=req.folder_name,
            max_objects=req.max_objects,
            max_bytes=req.max_bytes,
        )
    )


@app.post("/api/lab/upload-tree")
def api_lab_upload(req: LabUploadRequest):
    return _lab_guard(
        lambda: upload_tree(
            _lab_client(req.credentials),
            target_id=req.target_id,
            root_name=req.root_name,
            server_path=req.server_path,
            items=[i.model_dump() for i in req.items],
            max_objects=req.max_objects,
            max_bytes=req.max_bytes,
        )
    )


@app.get("/api/lab/fs-source")
def api_lab_fs_source():
    """Real source of the lab-fs backend module + frontend slice + topic YAML."""
    return lab_fs_source()


@app.post("/api/elo/login-check")
def api_login_check(creds: EloCreds):
    try:
        client = get_client(creds.base_url, creds.user, creds.password, verify=creds.tls_verify)
        user = client.user or {}
        return {"ok": True, "detail": f"logged in as {user.get('name', '?')} (id {user.get('id', '?')})"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "detail": f"{type(exc).__name__}: {exc}"}


@app.get("/health")
def health():
    return {"ok": True, "service": "backend-python", "node_url": settings.node_url}


@app.get("/favicon.ico")
def favicon():
    icon = settings.frontend_dir / "static" / "favicon.ico"
    if icon.exists():
        return FileResponse(icon)
    raise HTTPException(404)


def main() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    main()
