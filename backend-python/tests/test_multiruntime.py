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
        "python": (
            'ELO_BASE_URL = os.getenv("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") # ELOPG_DEFAULT:base_url',
            'ELO_USER = os.getenv("ELOPG_ELO_USER", "Administrator") # ELOPG_DEFAULT:user',
            'ELO_PASS = os.getenv("ELOPG_ELO_PASSWORD", "elo") # ELOPG_DEFAULT:password',
        ),
        "node": (
            'const ELO_BASE_URL = process.env.ELOPG_ELO_BASE_URL || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url',
            'const ELO_USER = process.env.ELOPG_ELO_USER || "Administrator"; // ELOPG_DEFAULT:user',
            'const ELO_PASS = process.env.ELOPG_ELO_PASSWORD || "elo"; // ELOPG_DEFAULT:password',
        ),
        "go": (
            'ELO_BASE_URL := elo.Env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1") // ELOPG_DEFAULT:base_url',
            'ELO_USER := elo.Env("ELOPG_ELO_USER", "Administrator") // ELOPG_DEFAULT:user',
            'ELO_PASS := elo.Env("ELOPG_ELO_PASSWORD", "elo") // ELOPG_DEFAULT:password',
        ),
        "php": (
            "$ELO_BASE_URL = getenv('ELOPG_ELO_BASE_URL') ?: 'http://localhost:9090/ix-Repository1'; // ELOPG_DEFAULT:base_url",
            "$ELO_USER = getenv('ELOPG_ELO_USER') ?: 'Administrator'; // ELOPG_DEFAULT:user",
            "$ELO_PASS = getenv('ELOPG_ELO_PASSWORD') ?: 'elo'; // ELOPG_DEFAULT:password",
        ),
        "java": (
            'String ELO_BASE_URL = EloClient.env("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"); // ELOPG_DEFAULT:base_url',
            'String ELO_USER = EloClient.env("ELOPG_ELO_USER", "Administrator"); // ELOPG_DEFAULT:user',
            'String ELO_PASS = EloClient.env("ELOPG_ELO_PASSWORD", "elo"); // ELOPG_DEFAULT:password',
        ),
        "rhino": (
            'var ELO_BASE_URL = java.lang.System.getenv("ELOPG_ELO_BASE_URL") || "http://localhost:9090/ix-Repository1"; // ELOPG_DEFAULT:base_url',
            'var ELO_USER = java.lang.System.getenv("ELOPG_ELO_USER") || "Administrator"; // ELOPG_DEFAULT:user',
            'var ELO_PASS = java.lang.System.getenv("ELOPG_ELO_PASSWORD") || "elo"; // ELOPG_DEFAULT:password',
        ),
    }
    client_use = {
        "go": "elo.New(ELO_BASE_URL, ELO_USER, ELO_PASS)",
        "php": "EloClient::connect($ELO_BASE_URL, $ELO_USER, $ELO_PASS)",
        "java": "EloClient.connect(ELO_BASE_URL, ELO_USER, ELO_PASS)",
        "rhino": "playgroundIx(ELO_BASE_URL, ELO_USER, ELO_PASS)",
    }
    for path in sorted(get_settings().catalog_dir.glob("*/*.yaml")):
        topic = get_topic((yaml.safe_load(path.read_text(encoding="utf-8")) or {})["id"])
        for runtime, lines in expected.items():
            code = getattr(topic.snippets, runtime)
            for line in lines:
                assert line in code, f"{topic.id} {runtime} missing visible connection default: {line}"
            password_end = code.index(lines[-1]) + len(lines[-1])
            assert code[password_end:].startswith("\n\n"), f"{topic.id} {runtime} must leave a blank line after ELO_PASS"
            if runtime in client_use:
                assert client_use[runtime] in code, f"{topic.id} {runtime} does not use its visible connection defaults"
