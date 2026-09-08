"""The committed snippets/ tree must match what catalog/ would generate."""
import importlib.util
import sys
from pathlib import Path

_BUILD = Path(__file__).resolve().parent.parent.parent / "scripts" / "build_snippets.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_snippets", _BUILD)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_snippets"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_snippets_are_in_sync_with_catalog():
    builder = _load_builder()
    rc = builder.build(check=True)
    assert rc == 0, "run: python scripts/build_snippets.py"
