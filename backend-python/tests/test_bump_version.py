"""Unit tests for the pre-commit version bumper (pure helpers, no git needed)."""
import importlib.util
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent.parent / "scripts" / "bump_version.py"


def _load():
    spec = importlib.util.spec_from_file_location("bump_version", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bump_version"] = mod
    spec.loader.exec_module(mod)
    return mod


bump = _load()


def test_parse_reads_a_semver_triple():
    assert bump._parse('__version__ = "1.4.9"') == (1, 4, 9)
    assert bump._parse("0.3.0\n") == (0, 3, 0)
    assert bump._parse("no version here") is None


def test_already_ahead_compares_working_copy_to_head(monkeypatch):
    monkeypatch.setattr(bump, "_head_blob", lambda rel: "0.3.0")
    assert bump._already_ahead("x", "0.3.1") is True
    assert bump._already_ahead("x", "0.3.0") is False
    monkeypatch.setattr(bump, "_head_blob", lambda rel: None)  # new file
    assert bump._already_ahead("x", "9.9.9") is False


def test_backend_prefixes_cover_server_and_content_layers():
    for p in ("backend-python/", "backend-node/", "shared/", "catalog/", "snippets/", "fixtures/"):
        assert p in bump.BACKEND_PREFIXES
    assert bump.FRONTEND_PREFIXES == ("frontend/",)


def test_touched_matches_by_prefix():
    assert "catalog/90-lab/06-share-link.yaml".startswith(bump.BACKEND_PREFIXES)
    assert not "README.md".startswith(bump.BACKEND_PREFIXES)
    assert "frontend/static/app.js".startswith(bump.FRONTEND_PREFIXES)
