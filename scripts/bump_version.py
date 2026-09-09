#!/usr/bin/env python3
"""Pre-commit version bumper.

Looks at the files staged for the current commit and bumps the **patch** number
of the layer(s) they belong to:

    frontend/**                                   -> frontend/VERSION
    backend-python/**  backend-node/**  shared/**
    catalog/**  snippets/**  fixtures/**          -> backend-python/app/__init__.py

Rules:
  * one patch bump per layer per commit - if that layer's version file is already
    staged ahead of HEAD (a hand bump), it is left alone;
  * the bumped file is re-staged so it lands in the same commit;
  * anything goes wrong -> print a note and exit 0. Bumping never blocks a commit.

Wired in by ``.githooks/pre-commit``; also safe to run by hand.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_VERSION = ROOT / "frontend" / "VERSION"
BACKEND_INIT = ROOT / "backend-python" / "app" / "__init__.py"

FRONTEND_VERSION_REL = "frontend/VERSION"
BACKEND_INIT_REL = "backend-python/app/__init__.py"

FRONTEND_PREFIXES = ("frontend/",)
# "backend" here means the server + everything it serves (the learning content).
BACKEND_PREFIXES = (
    "backend-python/", "backend-node/", "shared/",
    "catalog/", "snippets/", "fixtures/",
)

_VER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def _staged_files() -> list[str]:
    out = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    return [line.strip() for line in out.splitlines() if line.strip()]


def _head_blob(rel: str) -> str | None:
    r = subprocess.run(
        ["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, text=True
    )
    return r.stdout if r.returncode == 0 else None


def _parse(text: str | None) -> tuple[int, int, int] | None:
    m = _VER_RE.search(text or "")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def _already_ahead(rel: str, current_text: str) -> bool:
    """True if the working copy version is already higher than HEAD's."""
    old, cur = _parse(_head_blob(rel)), _parse(current_text)
    return bool(old and cur and cur > old)


def _bump_frontend() -> str | None:
    text = FRONTEND_VERSION.read_text(encoding="utf-8").strip()
    if _already_ahead(FRONTEND_VERSION_REL, text):
        return None
    v = _parse(text)
    if not v:
        return None
    new = f"{v[0]}.{v[1]}.{v[2] + 1}"
    FRONTEND_VERSION.write_text(new + "\n", encoding="utf-8")
    return new


def _bump_backend() -> str | None:
    text = BACKEND_INIT.read_text(encoding="utf-8")
    if _already_ahead(BACKEND_INIT_REL, text):
        return None
    m = _VER_RE.search(text)
    if not m:
        return None
    new = f"{int(m.group(1))}.{int(m.group(2))}.{int(m.group(3)) + 1}"
    BACKEND_INIT.write_text(text[: m.start()] + new + text[m.end() :], encoding="utf-8")
    return new


def _main() -> int:
    staged = _staged_files()
    if not staged:
        return 0

    def touched(prefixes: tuple[str, ...], exclude: str) -> bool:
        return any(f.startswith(prefixes) and f != exclude for f in staged)

    done: list[str] = []
    if touched(FRONTEND_PREFIXES, FRONTEND_VERSION_REL):
        new = _bump_frontend()
        if new:
            _git("add", "--", FRONTEND_VERSION_REL)
            done.append(f"frontend -> {new}")
    if touched(BACKEND_PREFIXES, BACKEND_INIT_REL):
        new = _bump_backend()
        if new:
            _git("add", "--", BACKEND_INIT_REL)
            done.append(f"backend -> {new}")

    if done:
        print("bump_version: " + ", ".join(done))
    return 0


def main() -> int:
    try:
        return _main()
    except Exception as exc:  # noqa: BLE001 - a bump must never block a commit
        print(f"bump_version: skipped ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
