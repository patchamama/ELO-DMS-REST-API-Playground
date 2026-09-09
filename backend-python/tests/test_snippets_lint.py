"""No snippet may reference an undefined name.

Python  -> pyflakes over snippets/python/ and every fenced ```python block in
           catalog/**/_deep.md.
Node / browser -> scripts/check_snippets_js.mjs (acorn-based; also covers the
           ```js blocks in the deep dives).
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
_SNIPPETS_PY = _ROOT / "snippets" / "python"
_JS_CHECK = _ROOT / "scripts" / "check_snippets_js.mjs"


def _pyflakes(*paths: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pyflakes", *paths],
        capture_output=True, text=True, check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_python_snippets_have_no_undefined_names():
    pytest.importorskip("pyflakes")
    rc, out = _pyflakes(str(_SNIPPETS_PY))
    assert rc == 0, f"pyflakes flagged a snippet:\n{out}"


def test_python_deep_dive_blocks_have_no_undefined_names():
    pytest.importorskip("pyflakes")
    blocks: list[tuple[str, str]] = []
    for md in (_ROOT / "catalog").glob("*/_deep.md"):
        for i, code in enumerate(re.findall(r"```python\n(.*?)```", md.read_text(encoding="utf-8"), re.S)):
            blocks.append((f"{md.relative_to(_ROOT)}#py{i}", code))
    assert blocks, "expected at least one python deep-dive block"
    with tempfile.TemporaryDirectory() as d:
        files = []
        for n, (label, code) in enumerate(blocks):
            f = Path(d) / f"block_{n}.py"
            f.write_text(f"# {label}\n{code}", encoding="utf-8")
            files.append(str(f))
        rc, out = _pyflakes(*files)
    # "imported but unused" is fine in a teaching excerpt; undefined names are not
    real = [ln for ln in out.splitlines() if ln and "imported but unused" not in ln]
    assert rc == 0 and not real, "pyflakes flagged a deep-dive block:\n" + "\n".join(real)


def test_node_and_browser_snippets_have_no_undefined_names():
    node = shutil.which("node")
    if not node or not _JS_CHECK.is_file():
        pytest.skip("node or check_snippets_js.mjs unavailable")
    proc = subprocess.run([node, str(_JS_CHECK)], capture_output=True, text=True, cwd=_ROOT, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
