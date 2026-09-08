"""Materialise every catalogue snippet as a standalone file under ``snippets/``.

    python scripts/build_snippets.py            # write the files
    python scripts/build_snippets.py --check    # fail if they are out of date

The files under ``snippets/`` are committed so the whole tree can also be read
as a plain, structured code library (``snippets/<language>/<category>/<topic>.<ext>``).
``scripts/smoke.py`` and the test suite call ``--check`` to keep them in sync.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
SNIPPETS = ROOT / "snippets"

_EXT = {"python": "py", "node": "mjs", "browser": "js"}
_IMPORT_HINT = {
    "python": "# import the shared client:  from elo_playground import connect",
    "node": '// import the shared client:  import { connect } from "elo-playground";',
    "browser": '// in a real page:  import { connect } from "./eloClient.browser.js"\n'
    "// (in the playground run-sandbox, connect() is already a global)",
}


def _pick(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("en") or next(iter(value.values()), ""))
    return str(value or "")


def _render(topic: dict, language: str) -> str:
    body = ((topic.get("snippets") or {}).get(language) or "").strip("\n")
    if not body:
        return ""
    header = (
        f"{_IMPORT_HINT[language]}\n"
        f"# topic:    {_pick(topic.get('title'))}\n"
        f"# category: {_pick(topic.get('category'))}\n"
        f"# id:       {topic.get('id')}\n"
    )
    if language != "python":
        header = header.replace("# ", "// ")
    return header + "\n" + body + "\n"


def build(check: bool) -> int:
    wanted: dict[Path, str] = {}
    for yaml_path in sorted(CATALOG.glob("*/*.yaml")):
        if yaml_path.name.startswith("_"):
            continue
        topic = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        category = yaml_path.parent.name
        slug = yaml_path.stem
        for language, ext in _EXT.items():
            text = _render(topic, language)
            if not text:
                continue
            wanted[SNIPPETS / language / category / f"{slug}.{ext}"] = text

    existing = {
        p for p in SNIPPETS.glob("**/*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }
    stale = existing - set(wanted)
    drift: list[str] = []

    for path, text in sorted(wanted.items()):
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            drift.append(str(path.relative_to(ROOT)))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    for path in sorted(stale):
        drift.append(f"(stale) {path.relative_to(ROOT)}")
        if not check:
            path.unlink()

    if check and drift:
        print("snippets/ is out of date - run: python scripts/build_snippets.py")
        for d in drift:
            print("  ", d)
        return 1
    if not check:
        print(f"wrote {len(wanted)} snippet files under snippets/")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="only report drift, do not write")
    sys.exit(build(ap.parse_args().check))
