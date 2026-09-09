"""Execute a code snippet and capture its output.

* ``python`` runs here, in a child ``python`` process (isolated working dir,
  timeout, output redirected to FILES - never a pipe, which deadlocks on
  Windows when a chatty child fills the buffer).
* ``node``   is proxied to the Express service in ``backend-node/`` so Node code
  runs on a real Node runtime.
* ``browser`` never runs on the server - the frontend executes it in a
  sandboxed iframe.

Guardrails are deliberately light: this is a local learning tool that runs on a
machine with ELO installed and your ELO credentials in the environment.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx

from .catalog import get_topic
from .config import get_settings
from .models import RunRequest, RunResult

_DEFAULT_FIXTURE = "default.json"


def mock_data(topic_id: str | None) -> dict:
    """``fixtures/ix/default.json`` overlaid with the topic's ``mock:`` block.

    When ``topic_id`` is a *category* id (a Deep-dive panel passes one), the
    ``catalog/<category>/_deep.mock.json`` file is overlaid instead, if present.
    """
    s = get_settings()
    data: dict = {}
    default = s.fixtures_dir / _DEFAULT_FIXTURE
    if default.is_file():
        data.update(json.loads(default.read_text(encoding="utf-8")))
    if topic_id:
        topic = get_topic(topic_id)
        if topic:
            data.update(topic.mock)
        else:
            deep_mock = s.catalog_dir / topic_id / "_deep.mock.json"
            if deep_mock.is_file():
                data.update(json.loads(deep_mock.read_text(encoding="utf-8")))
    return data


_ATTACH_CAP = 12 * 1024 * 1024  # 12 MiB decoded - OCR test files are tiny


def _write_attachment(req: RunRequest, workdir: Path, env: dict[str, str]) -> None:
    """If the run carries a picked file, drop it in the workdir and point
    ELOPG_ATTACH at it (read by elo_playground.attachment())."""
    att = getattr(req, "attachment", None)
    if not att:
        return
    import base64

    try:
        raw = base64.b64decode(att.b64, validate=True)[:_ATTACH_CAP]
    except Exception:  # noqa: BLE001 - a bad upload must not crash the run
        return
    safe = Path(att.name or "attachment").name or "attachment"
    path = workdir / safe
    path.write_bytes(raw)
    env["ELOPG_ATTACH"] = str(path)
    env["ELOPG_ATTACH_NAME"] = att.name or safe


def _base_env(req: RunRequest, workdir: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.pop("ELOPG_MOCK", None)
    env.pop("ELOPG_MOCK_DATA", None)
    env.pop("ELOPG_ATTACH", None)
    env.pop("ELOPG_ATTACH_NAME", None)
    if req.mock:
        env["ELOPG_MOCK"] = "1"
        mock_path = workdir / "mock.json"
        mock_path.write_text(json.dumps(mock_data(req.topic_id)), encoding="utf-8")
        env["ELOPG_MOCK_DATA"] = str(mock_path)
    elif req.credentials:
        env["ELOPG_ELO_BASE_URL"] = req.credentials.base_url
        env["ELOPG_ELO_USER"] = req.credentials.user
        env["ELOPG_ELO_PASSWORD"] = req.credentials.password
        env["ELOPG_TLS_VERIFY"] = "1" if req.credentials.tls_verify else "0"
    _write_attachment(req, workdir, env)
    return env


def _read_capped(path: Path, cap: int) -> str:
    if not path.exists():
        return ""
    raw = path.read_bytes()
    text = raw[:cap].decode("utf-8", errors="replace")
    if len(raw) > cap:
        text += f"\n... [output truncated at {cap} bytes]"
    return text


def run_python(req: RunRequest) -> RunResult:
    s = get_settings()
    workdir = s.runtime_dir / "run" / uuid.uuid4().hex[:12]
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "snippet.py").write_text(req.code, encoding="utf-8")

    env = _base_env(req, workdir)
    # shared/python on PYTHONPATH so ``import elo_playground`` resolves.
    env["PYTHONPATH"] = str(s.shared_python) + os.pathsep + env.get("PYTHONPATH", "")

    out_f, err_f = workdir / "stdout.txt", workdir / "stderr.txt"
    start = time.time()
    code: int | None
    detail = ""
    try:
        with out_f.open("wb") as o, err_f.open("wb") as e:
            proc = subprocess.run(
                [sys.executable, "-B", "-u", str(workdir / "snippet.py")],
                cwd=workdir,
                env=env,
                stdout=o,
                stderr=e,
                timeout=s.run_timeout_s,
                check=False,
            )
        code = proc.returncode
    except subprocess.TimeoutExpired:
        code = None
        detail = f"timed out after {s.run_timeout_s}s"

    result = RunResult(
        ok=(code == 0),
        stdout=_read_capped(out_f, s.run_output_cap),
        stderr=_read_capped(err_f, s.run_output_cap),
        exit_code=code,
        duration_ms=int((time.time() - start) * 1000),
        detail=detail,
    )
    shutil.rmtree(workdir, ignore_errors=True)
    return result


def run_node(req: RunRequest) -> RunResult:
    s = get_settings()
    payload = {
        "code": req.code,
        "mock": req.mock,
        "mockData": mock_data(req.topic_id) if req.mock else None,
        "credentials": req.credentials.model_dump() if req.credentials else None,
        "attachment": req.attachment.model_dump() if req.attachment else None,
        "timeoutMs": s.run_timeout_s * 1000,
        "outputCap": s.run_output_cap,
    }
    try:
        r = httpx.post(f"{s.node_url}/run", json=payload, timeout=s.run_timeout_s + 10)
    except httpx.HTTPError as exc:
        return RunResult(
            ok=False,
            detail=(
                f"Node backend not reachable at {s.node_url}. Start it with: "
                f"cd backend-node && npm install && npm start   ({exc})"
            ),
        )
    if r.status_code != 200:
        return RunResult(ok=False, detail=f"Node backend error HTTP {r.status_code}: {r.text[:300]}")
    d = r.json()
    return RunResult(
        ok=bool(d.get("ok")),
        stdout=d.get("stdout", ""),
        stderr=d.get("stderr", ""),
        exit_code=d.get("exitCode"),
        duration_ms=int(d.get("durationMs", 0)),
        detail=d.get("detail", ""),
    )


def run(req: RunRequest) -> RunResult:
    if req.language == "python":
        return run_python(req)
    if req.language == "node":
        return run_node(req)
    return RunResult(ok=False, detail="browser snippets run in the page, not on the server")
