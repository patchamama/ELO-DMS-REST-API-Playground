"""The Python side of the snippet runner (offline / mock only)."""
import textwrap

from app.models import RunRequest
from app.runner import mock_data, run_python


def _run(code: str, topic_id: str | None = None) -> object:
    return run_python(RunRequest(language="python", code=textwrap.dedent(code), mock=True, topic_id=topic_id))


def test_trivial_snippet_captures_stdout():
    res = _run("print('hello from python')")
    assert res.ok
    assert res.exit_code == 0
    assert "hello from python" in res.stdout


def test_failing_snippet_reports_stderr_and_nonzero_exit():
    res = _run("raise SystemExit(3)")
    assert not res.ok
    assert res.exit_code == 3


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
