"""Local, allow-listed activation of optional snippet runtimes.

The web API deliberately accepts runtime *names*, never commands, URLs or file
paths.  The only installer it can start is this repository's pinned portable
bootstrap script.  Activation state is local runtime data and is ignored by Git.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from .config import get_settings

CORE_RUNTIMES = ("python", "node", "browser")
OPTIONAL_RUNTIMES = ("go", "php", "java", "rhino")
INSTALLABLE_RUNTIMES = ("go", "php", "java")
ALL_RUNTIMES = CORE_RUNTIMES + OPTIONAL_RUNTIMES


def _state_path() -> Path:
    return get_settings().runtime_dir / "activated-runtimes.json"


def _load_enabled() -> set[str]:
    try:
        raw = json.loads(_state_path().read_text(encoding="utf-8"))
        values = raw.get("enabled", []) if isinstance(raw, dict) else []
        return set(CORE_RUNTIMES) | {v for v in values if v in ALL_RUNTIMES}
    except (OSError, ValueError, TypeError):
        return set(CORE_RUNTIMES)


def _save_enabled(enabled: set[str]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"enabled": [name for name in ALL_RUNTIMES if name in enabled]}
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def is_enabled(runtime: str) -> bool:
    return runtime in _load_enabled()


def _installed(name: str) -> bool:
    s = get_settings()
    checks = {
        "python": Path(sys.executable).is_file(),
        "node": bool(shutil.which("node")) or (s.runtime_dir / "toolchains" / "node" / "node.exe").is_file(),
        "browser": True,
        "go": (s.runtime_dir / "toolchains" / "go" / "bin" / "go.exe").is_file(),
        "php": (s.runtime_dir / "toolchains" / "php" / "php.exe").is_file(),
        "java": (s.runtime_dir / "toolchains" / "jdk" / "bin" / "java.exe").is_file()
        and (s.runtime_dir / "toolchains" / "jdk" / "bin" / "javac.exe").is_file(),
        # Rhino is deployed to IndexServer, not installed or executed locally.
        "rhino": False,
    }
    return checks[name]


def progress_lines() -> list[str]:
    """Tail of the installer's progress log, refreshed on every bootstrap run.

    Best-effort: no install may be running, or the file may not exist yet.
    """
    path = get_settings().runtime_dir / "toolchains" / ".install-progress.log"
    try:
        # utf-8-sig: Windows PowerShell 5.1's `Add-Content -Encoding utf8`
        # writes a BOM on the first line, unlike pwsh 7's utf8NoBOM.
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return []
    return lines[-200:]


def status() -> dict:
    enabled = _load_enabled()
    descriptions = {
        "python": "Local Python teaching client",
        "node": "Node.js teaching client",
        "browser": "Browser JavaScript mock client",
        "go": "Portable Go compiler installed in runtime/toolchains",
        "php": "Portable PHP runtime installed in runtime/toolchains",
        "java": "Portable JDK installed in runtime/toolchains",
        "rhino": "Reviewed IndexServer script artifact; deployment is server-side",
    }
    return {
        "runtimes": [
            {
                "id": name,
                "enabled": name in enabled,
                "installed": _installed(name),
                "installable": name in INSTALLABLE_RUNTIMES,
                "core": name in CORE_RUNTIMES,
                "description": descriptions[name],
            }
            for name in ALL_RUNTIMES
        ]
    }


def update(requested: list[str], *, enabled: bool) -> dict:
    """Enable or disable a fixed set of runtimes, installing only allow-listed ones."""
    names = list(dict.fromkeys(requested))
    unknown = set(names) - set(ALL_RUNTIMES)
    if unknown:
        raise ValueError("unsupported runtime: " + ", ".join(sorted(unknown)))
    if any(name in CORE_RUNTIMES for name in names) and not enabled:
        raise ValueError("Python, Node.js and Browser JS are always enabled")

    active = _load_enabled()
    if enabled:
        missing = [name for name in names if name in INSTALLABLE_RUNTIMES and not _installed(name)]
        if missing:
            s = get_settings()
            script = s.project_root / "scripts" / "bootstrap-toolchains.ps1"
            command = [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
                "-SkipPythonDeps", "-RuntimesCsv", ",".join(missing),
            ]
            # Captured and bounded output prevents a download failure from
            # leaking an arbitrary process stream through the web API.
            # errors="replace" avoids a UnicodeDecodeError masking the real
            # installer failure when PowerShell prints a localized (non-UTF8)
            # error message under a non-English Windows console codepage.
            try:
                proc = subprocess.run(
                    command, cwd=s.project_root, capture_output=True, text=True,
                    errors="replace", timeout=900, check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise RuntimeError(f"portable runtime installation failed: {exc}") from exc
            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout).strip()[-1000:]
                raise RuntimeError(f"portable runtime installation failed: {detail or 'unknown installer error'}")
        active.update(names)
    else:
        active.difference_update(names)
    _save_enabled(active)
    return status()
