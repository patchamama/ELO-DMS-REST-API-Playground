"""Serve the source of the shared ``elo_playground`` teaching client so the
catalogue can show what ``from elo_playground import connect`` actually does."""
from __future__ import annotations

from .config import get_settings

# (runtime, display title, path relative to the project root)
_FILES = [
    ("python", "elo_playground/__init__.py", "shared/python/elo_playground/__init__.py"),
    ("python", "elo_playground/client.py", "shared/python/elo_playground/client.py"),
    ("python", "elo_playground/errors.py", "shared/python/elo_playground/errors.py"),
    ("python", "elo_playground/mock.py", "shared/python/elo_playground/mock.py"),
    ("node", "eloClient.mjs", "shared/node/eloClient.mjs"),
    ("browser", "eloClient.browser.js", "shared/browser/eloClient.browser.js"),
    ("go", "elo.go", "shared/go/elo.go"),
    ("php", "EloClient.php", "shared/php/EloClient.php"),
    ("java", "EloClient.java", "shared/java/EloClient.java"),
    ("rhino", "README.md", "catalog/90-lab/_rhino.md"),
]


def client_lib() -> dict[str, list[dict[str, str]]]:
    root = get_settings().project_root
    out: dict[str, list[dict[str, str]]] = {"python": [], "node": [], "browser": [], "go": [], "php": [], "java": [], "rhino": []}
    for runtime, title, rel in _FILES:
        path = root / rel
        if path.is_file():
            out[runtime].append({"title": title, "code": path.read_text(encoding="utf-8")})
    return out
