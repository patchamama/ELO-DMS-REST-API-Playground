"""Runtime activation is allow-listed and never changes global toolchains."""
import json

import pytest

from app import runtime_manager


def test_status_defaults_to_core_runtimes_when_no_state_file(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_manager, "_state_path", lambda: tmp_path / "missing.json")
    data = runtime_manager.status()
    by_id = {item["id"]: item for item in data["runtimes"]}
    assert all(by_id[name]["enabled"] for name in runtime_manager.CORE_RUNTIMES)
    assert not by_id["go"]["enabled"]
    assert by_id["go"]["installable"]
    assert not by_id["rhino"]["installable"]


def test_disable_preserves_core_and_persists_only_optional_names(monkeypatch, tmp_path):
    state = tmp_path / "activated-runtimes.json"
    monkeypatch.setattr(runtime_manager, "_state_path", lambda: state)
    monkeypatch.setattr(runtime_manager, "_installed", lambda _name: True)
    runtime_manager.update(["go", "php"], enabled=True)
    runtime_manager.update(["php"], enabled=False)
    assert json.loads(state.read_text(encoding="utf-8"))["enabled"] == ["python", "node", "browser", "go"]
    with pytest.raises(ValueError, match="always enabled"):
        runtime_manager.update(["python"], enabled=False)


def test_activation_rejects_unknown_runtime_before_running_installer():
    with pytest.raises(ValueError, match="unsupported runtime"):
        runtime_manager.update(["not-a-runtime"], enabled=True)
