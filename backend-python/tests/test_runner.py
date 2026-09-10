"""The Python side of the snippet runner (offline / mock only)."""
import base64
import json
import os
import textwrap

import pytest

from app.catalog import get_topic
from app.models import Attachment, RunRequest
from app.runner import _run_command, mock_data, run, run_python


def _run(code: str, topic_id: str | None = None, attachment: Attachment | None = None) -> object:
    return run_python(
        RunRequest(
            language="python", code=textwrap.dedent(code), mock=True,
            topic_id=topic_id, attachment=attachment,
        )
    )


def test_trivial_snippet_captures_stdout():
    res = _run("print('hello from python')")
    assert res.ok
    assert res.exit_code == 0
    assert "hello from python" in res.stdout


def test_failing_snippet_reports_stderr_and_nonzero_exit():
    res = _run("raise SystemExit(3)")
    assert not res.ok
    assert res.exit_code == 3


def test_attachment_reaches_the_snippet():
    code = """
        from elo_playground import attachment
        got = attachment()
        print("none" if got is None else f"{got[0]}:{got[1].decode()}")
    """
    # no attachment -> None
    assert "none" in _run(code).stdout
    # with one -> (name, bytes)
    att = Attachment(name="scan.pdf", b64=base64.b64encode(b"hello ocr").decode())
    assert "scan.pdf:hello ocr" in _run(code, attachment=att).stdout


def test_shared_client_is_importable_and_returns_mock_data():
    res = _run(
        """
        from elo_playground import connect
        elo = connect()
        print(elo.call('getServerInfo', {})['version'])
        """,
        topic_id="connection.server-info",
    )
    assert res.ok, res.stderr
    assert "25.00.001.003" in res.stdout


def test_timeout_is_reported(monkeypatch):
    from app import runner as runner_mod

    slow = runner_mod.get_settings()
    monkeypatch.setattr(slow, "run_timeout_s", 2)
    monkeypatch.setattr(runner_mod, "get_settings", lambda: slow)

    res = run_python(RunRequest(language="python", code="while True: pass", mock=True))
    assert not res.ok
    assert "timed out" in res.detail


def test_mock_data_merges_default_and_topic():
    data = mock_data("connection.server-info")
    assert "login" in data              # from fixtures/ix/default.json
    assert "getServerInfo" in data      # from the topic's mock: block


def test_new_runtime_dispatches_to_compiled_runner(monkeypatch):
    """Go, PHP and Java use the isolated runner rather than the browser path."""
    from app import runner as runner_mod

    seen: list[str] = []

    def fake_compiled(req, language):
        seen.append(language)
        return runner_mod.RunResult(ok=True, stdout=language)

    monkeypatch.setattr(runner_mod, "run_compiled", fake_compiled)
    for language in ("go", "php", "java"):
        result = run(RunRequest(language=language, code="ignored", mock=True))
        assert result.ok
    assert seen == ["go", "php", "java"]


def test_run_request_accepts_only_registered_new_runtime_names():
    for language in ("go", "php", "java", "rhino"):
        assert RunRequest(language=language, code="", mock=True).language == language


def test_missing_toolchain_is_an_explicit_runner_error():
    result = _run_command(
        RunRequest(language="go", code="", mock=True),
        ["elopg-definitely-not-installed"],
        "snippet.go",
    )
    assert not result.ok
    assert result.exit_code is None
    assert "toolchain not installed: elopg-definitely-not-installed" == result.detail


def test_rhino_is_not_executed_as_browser_or_local_code():
    result = run(RunRequest(language="rhino", code="throw 'must not run'", mock=True))
    assert not result.ok
    assert result.exit_code is None
    assert "IndexServer script artifacts" in result.detail
    assert "Web Client injection" in result.detail


@pytest.mark.parametrize("language", ["go", "php", "java"])
def test_shared_runtime_example_matches_canonical_fixture(language):
    """Portable toolchains execute the same fixture-backed payload contract."""
    topic = get_topic("connection.server-info")
    code = getattr(topic.snippets, language)
    result = run(RunRequest(language=language, code=code, mock=True, topic_id=topic.id))
    assert result.ok, f"{language}: {result.detail}\n{result.stderr}"
    assert json.loads(result.stdout) == mock_data(topic.id)["getServerInfo"]
