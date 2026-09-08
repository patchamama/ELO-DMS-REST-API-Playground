"""Offline smoke test - no ELO, no network. Wired into CI.

  * catalogue loads and has enough topics
  * snippets/ is in sync with catalog/
  * one Python snippet runs in mock mode and prints the expected value
  * one Node snippet runs in mock mode  (skipped if `node` / node_modules absent)

Exit code is non-zero on any failure.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend-python"))
sys.path.insert(0, str(ROOT / "shared" / "python"))


def _step(msg: str) -> None:
    print(f"  .. {msg}")


def main() -> int:
    from app.catalog import load_topics
    from app.models import RunRequest
    from app.runner import run_node, run_python

    # 1 - catalogue
    topics = load_topics("en")
    assert len(topics) >= 10, f"only {len(topics)} topics"
    _step(f"catalogue: {len(topics)} topics in {len({t.category_id for t in topics})} categories")

    # 2 - snippets in sync
    spec = importlib.util.spec_from_file_location("build_snippets", ROOT / "scripts" / "build_snippets.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    assert builder.build(check=True) == 0, "snippets/ out of date - run scripts/build_snippets.py"
    _step("snippets/ is in sync with catalog/")

    # 3 - python snippet in mock mode
    code = (
        "from elo_playground import connect\n"
        "elo = connect()\n"
        "print(elo.call('getServerInfo', {})['version'])\n"
    )
    res = run_python(RunRequest(language="python", code=code, mock=True, topic_id="connection.server-info"))
    assert res.ok, res.stderr or res.detail
    assert "25.00.001.003" in res.stdout, res.stdout
    _step("python snippet ran in mock mode")

    # 4 - node snippet in mock mode (best effort)
    node = shutil.which("node")
    if node and (ROOT / "node_modules" / "elo-playground").exists():
        r = _run_node_direct(node)
        assert "25.00.001.003" in r, r
        _step("node snippet ran in mock mode")
    else:
        _step("node snippet SKIPPED (run `npm install` in the project root to enable)")

    print("smoke: OK")
    return 0


def _run_node_direct(node: str) -> str:
    """Run a Node snippet the same way backend-node would, without the HTTP hop."""
    (ROOT / "runtime" / "node-run").mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(dir=ROOT / "runtime" / "node-run"))
    try:
        (work / "mock.json").write_text(
            json.dumps({"login": {"user": {"id": 0}}, "getServerInfo": {"version": "25.00.001.003"}}),
            encoding="utf-8",
        )
        (work / "snippet.mjs").write_text(
            'import { connect } from "elo-playground";\n'
            "const elo = await connect();\n"
            'console.log((await elo.call("getServerInfo", {})).version);\n',
            encoding="utf-8",
        )
        out = subprocess.run(
            [node, str(work / "snippet.mjs")],
            cwd=work,
            env={
                **_clean_env(),
                "ELOPG_MOCK": "1",
                "ELOPG_MOCK_DATA": str(work / "mock.json"),
            },
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert out.returncode == 0, out.stderr
        return out.stdout
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _clean_env() -> dict:
    import os

    e = dict(os.environ)
    e.pop("ELOPG_MOCK", None)
    e.pop("ELOPG_MOCK_DATA", None)
    return e


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"smoke: FAIL - {exc}")
        sys.exit(1)
