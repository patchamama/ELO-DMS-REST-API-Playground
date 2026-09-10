"""Cross-runtime semantic parity for generated teaching examples."""
import json
import re

import yaml

from app.catalog import get_topic
from app.config import get_settings
from app.multiruntime import operation_plan

_ROOT = get_settings().project_root


def test_generated_operation_plans_match_python_calls_for_every_topic():
    """Go/PHP/Java must retain Python method order and normalized parameters."""
    marker = re.compile(r"ELOPG_PLAN: (\[.*\])")
    for path in sorted(get_settings().catalog_dir.glob("*/*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        topic = get_topic(data["id"])
        expected = operation_plan(data)
        for language in ("go", "php", "java"):
            match = marker.search(getattr(topic.snippets, language))
            assert match, f"{data['id']} {language} missing semantic operation marker"
            assert json.loads(match.group(1)) == expected, f"{data['id']} {language} drifted from Python calls"


def test_shared_clients_reject_ix_exception_envelopes_and_java_has_timeouts():
    go = (_ROOT / "shared" / "go" / "elo.go").read_text(encoding="utf-8")
    php = (_ROOT / "shared" / "php" / "EloClient.php").read_text(encoding="utf-8")
    java = (_ROOT / "shared" / "java" / "EloClient.java").read_text(encoding="utf-8")
    assert 'json:"exception"' in go and "IX exception:" in go
    assert "array_key_exists('exception'" in php and "IX exception:" in php
    assert 'contains("\\\"exception\\\"")' in java and "connectTimeout" in java and ".timeout(" in java


def test_go_client_has_request_timeout_for_login_and_every_ix_call():
    go = (_ROOT / "shared" / "go" / "elo.go").read_text(encoding="utf-8")
    assert "defaultRequestTimeout" in go
    assert "&http.Client{Timeout: defaultRequestTimeout}" in go
    assert "context.WithTimeout" in go
    assert "http.NewRequestWithContext" in go


def test_all_runtime_snippets_expose_marked_environment_defaults():
    """The frontend updates only these markers, never a guessed user-code line."""
    expected = {
        "python": ('os.getenv("ELOPG_ELO_PASSWORD", "elo")', "# ELOPG_DEFAULT:password"),
        "node": ('process.env.ELOPG_ELO_PASSWORD || "elo"', "// ELOPG_DEFAULT:password"),
        "go": ('elo.Env("ELOPG_ELO_PASSWORD", "elo")', "// ELOPG_DEFAULT:password"),
        "php": ("getenv('ELOPG_ELO_PASSWORD') ?: 'elo'", "// ELOPG_DEFAULT:password"),
        "java": ('EloClient.env("ELOPG_ELO_PASSWORD", "elo")', "// ELOPG_DEFAULT:password"),
        "rhino": ('java.lang.System.getenv("ELOPG_ELO_PASSWORD") || "elo"', "// ELOPG_DEFAULT:password"),
    }
    for path in sorted(get_settings().catalog_dir.glob("*/*.yaml")):
        topic = get_topic((yaml.safe_load(path.read_text(encoding="utf-8")) or {})["id"])
        for runtime, (fallback, password_marker) in expected.items():
            code = getattr(topic.snippets, runtime)
            assert "ELOPG_ELO_BASE_URL" in code, f"{topic.id} {runtime} missing base URL default"
            assert "ELOPG_ELO_USER" in code, f"{topic.id} {runtime} missing user default"
            assert fallback in code, f"{topic.id} {runtime} missing password fallback"
            assert "ELOPG_DEFAULT:base_url" in code
            assert "ELOPG_DEFAULT:user" in code
            assert password_marker in code
