"""Build a fully static, backend-free copy of the playground into ``dist/``.

What survives without a backend:
  * the whole catalogue, every snippet, the shared-client source, the deep dives
  * the "API reference" tab (from the trimmed openapi.sample.json)
  * **Browser** snippets run for real, in the sandboxed iframe, against a
    JavaScript mock seeded from each topic's ``mock:`` block
  * **Python / Node** snippets show their pre-computed mock-mode output (this
    script runs every one at build time and caches stdout/stderr)

The output is served as-is (GitHub Pages): all asset paths are relative and the
former ``/api/...`` endpoints become static ``api/....json`` files.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend-python"))
sys.path.insert(0, str(ROOT / "shared" / "python"))

from app import __version__ as BACKEND_VERSION  # noqa: E402
from app import catalog as cat  # noqa: E402
from app import client_lib as clib  # noqa: E402
from app import openapi_ref  # noqa: E402
from app.i18n import catalogue  # noqa: E402
from app.models import RunRequest  # noqa: E402
from app.runner import mock_data, run_python  # noqa: E402

DIST = ROOT / "dist"
LANGS = ("en", "de", "es")


def _write(rel: str, obj) -> None:
    path = DIST / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def _copy_tree(src: Path, dst_rel: str) -> None:
    dst = DIST / dst_rel
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


# ---- Node snippet runner without the Express hop ------------------------ #
def _run_node_mock(code: str, mock: dict) -> dict:
    (ROOT / "runtime").mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(dir=ROOT / "runtime"))
    try:
        (work / "mock.json").write_text(json.dumps(mock), encoding="utf-8")
        (work / "snippet.mjs").write_text(code, encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if not k.startswith("ELOPG_")}
        env["ELOPG_MOCK"] = "1"
        env["ELOPG_MOCK_DATA"] = str(work / "mock.json")
        started = time.time()
        proc = subprocess.run(
            ["node", str(work / "snippet.mjs")],
            cwd=work, env=env, capture_output=True, text=True, timeout=20, check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout[:200_000],
            "stderr": proc.stderr[:200_000],
            "exit_code": proc.returncode,
            "duration_ms": int((time.time() - started) * 1000),
            "detail": "",
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return {"ok": False, "stdout": "", "stderr": "", "exit_code": None,
                "duration_ms": 0, "detail": f"node: {exc}"}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _run_python_mock(code: str, topic_id: str | None) -> dict:
    res = run_python(RunRequest(language="python", code=code, mock=True, topic_id=topic_id))
    return res.model_dump()


_HAVE_NODE = shutil.which("node") is not None
_FENCE = re.compile(r"```(python|js|javascript|browser)\n(.*?)```", re.DOTALL)


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # ---- static assets (relative paths) -----------------------------------
    _copy_tree(ROOT / "frontend" / "static", "static")
    _copy_tree(ROOT / "frontend" / "vendor", "vendor")
    (DIST / "client").mkdir()
    shutil.copy2(ROOT / "shared" / "browser" / "eloClient.browser.js", DIST / "client" / "eloClient.browser.js")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    # ---- index.html ------------------------------------------------------
    import jinja2

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(ROOT / "frontend" / "templates")), autoescape=True)
    build_id = format(int(time.time()), "x")[-8:]
    html = env.get_template("index.html").render(
        static_v=build_id, default_base_url="", default_port="9090",
        default_user="", mock_default=True,
    )
    html = (
        html.replace('href="/vendor/', 'href="vendor/')
        .replace('src="/vendor/', 'src="vendor/')
        .replace('href="/static/', 'href="static/')
        .replace('src="/static/', 'src="static/')
        .replace('src="/client/', 'src="client/')
        .replace(
            "window.__PLAYGROUND__ = {",
            "window.__PLAYGROUND__ = {\n    staticMode: true,",
        )
    )
    (DIST / "index.html").write_text(html, encoding="utf-8")

    fe_ver = (ROOT / "frontend" / "VERSION").read_text(encoding="utf-8").strip()
    _write("api/version.json", {"backend": BACKEND_VERSION, "frontend": fe_ver})

    faq_path = ROOT / "frontend" / "faq.md"
    _write("api/faq.json", {"markdown": faq_path.read_text(encoding="utf-8") if faq_path.is_file() else ""})

    # ---- i18n + catalogue ---------------------------------------------
    for lang in LANGS:
        _write(f"api/i18n/{lang}.json", catalogue(lang))
        _write(f"api/catalog/{lang}.json", {"categories": cat.categories(lang)})

    topics = cat.load_topics("en")
    default_mock = json.loads((ROOT / "fixtures" / "ix" / "default.json").read_text(encoding="utf-8"))

    for lang in LANGS:
        for t in cat.load_topics(lang):
            d = t.model_dump()
            d["mock"] = mock_data(t.id)  # default + topic, merged (for the browser JS mock)
            _write(f"api/topics/{lang}/{t.id}.json", d)

    # ---- deep dives + run cache -------------------------------------
    run_cache: dict[str, dict] = {}
    for t in topics:
        merged = mock_data(t.id)
        for language in ("python", "node"):
            code = getattr(t.snippets, language)
            if not code:
                continue
            key = f"t:{t.id}|{language}"
            if language == "python":
                run_cache[key] = _run_python_mock(code, t.id)
            elif _HAVE_NODE:
                run_cache[key] = _run_node_mock(code, merged)
            print(f"  ran {key}: ok={run_cache.get(key, {}).get('ok')}")

    for c in cat.categories("en"):
        md = cat.deep_doc(c["id"])
        if not md:
            continue
        deep_mock_path = ROOT / "catalog" / c["id"] / "_deep.mock.json"
        merged = dict(default_mock)
        if deep_mock_path.is_file():
            merged.update(json.loads(deep_mock_path.read_text(encoding="utf-8")))
        _write(f"api/deep/{c['id']}.json", {"category_id": c["id"], "markdown": md, "mock": merged})
        for i, m in enumerate(_FENCE.finditer(md)):
            language = {"js": "node", "javascript": "node"}.get(m.group(1), m.group(1))
            if language not in ("python", "node"):
                continue
            code = m.group(2).strip()
            key = f"d:{c['id']}#{i}|{language}"
            if language == "python":
                run_cache[key] = _run_python_mock(code, c["id"])
            elif _HAVE_NODE:
                run_cache[key] = _run_node_mock(code, merged)
            print(f"  ran {key}: ok={run_cache.get(key, {}).get('ok')}")

    _write("api/run-cache.json", run_cache)

    # ---- client library + openapi reference ------------------------
    _write("api/client-lib.json", clib.client_lib())

    spec = openapi_ref.load_spec(None, mock=True)
    _write("api/spec/services.json", {"info": openapi_ref.spec_info(spec), "services": openapi_ref.services(spec)})
    for svc in openapi_ref.services(spec):
        _write(f"api/spec/operations/{svc['service']}.json", {"operations": openapi_ref.operations(spec, svc["service"])})
    for op in openapi_ref.operations(spec):
        detail = openapi_ref.operation_detail(spec, op["operation_id"])
        detail["snippets"] = {l: openapi_ref.generate(detail, l) for l in ("python", "node", "browser")}
        _write(f"api/spec/op/{op['operation_id']}.json", detail)

    n_files = sum(1 for _ in DIST.glob("**/*") if _.is_file())
    print(f"\ndist/ built - {n_files} files, {sum(f.stat().st_size for f in DIST.glob('**/*') if f.is_file()) // 1024} KiB")
    print(f"run cache: {sum(1 for v in run_cache.values() if v.get('ok'))}/{len(run_cache)} ok")
    if not _HAVE_NODE:
        print("  (node not found - Node run outputs were skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
