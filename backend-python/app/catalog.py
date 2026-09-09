"""Load the curated learning catalogue from ``catalog/**/*.yaml``.

Layout::

    catalog/
      00-connection/            <- directory name = category id (prefix orders it)
        01-login.yaml           <- one topic per file
        02-server-info.yaml
        _deep.md               <- optional "Deep dive" companion (fenced runnable blocks)

Each topic YAML carries localisable fields as ``{en: "...", de: "...", es: "..."}``
maps. For Milestone 1 only ``en`` is filled; ``_pick`` falls back to it.
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

from .config import get_settings
from .models import ApiRef, Snippets, Topic
from .multiruntime import generate as generate_multiruntime


def _pick(value: Any, lang: str) -> str:
    if isinstance(value, dict):
        return str(value.get(lang) or value.get("en") or next(iter(value.values()), ""))
    return str(value or "")


@functools.lru_cache
def _raw_topics() -> tuple[dict[str, Any], ...]:
    out: list[dict[str, Any]] = []
    root = get_settings().catalog_dir
    for path in sorted(root.glob("*/*.yaml")):
        if path.name.startswith("_"):
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data["_category_id"] = path.parent.name
        data["_file"] = str(path.relative_to(root))
        out.append(data)
    return tuple(out)


def load_topics(lang: str = "en") -> list[Topic]:
    topics: list[Topic] = []
    for d in _raw_topics():
        snip = d.get("snippets") or {}
        topics.append(
            Topic(
                id=d["id"],
                category_id=d["_category_id"],
                category=_pick(d.get("category"), lang),
                order=int(d.get("order", 0)),
                title=_pick(d.get("title"), lang),
                summary=_pick(d.get("summary"), lang),
                elo_api=[
                    ApiRef(
                        method=a["method"],
                        rpc=a["rpc"],
                        doc_url=a.get("doc_url", "{base}/rest/openapi.json"),
                        spec=a.get("spec", ""),
                        notes=_pick(a.get("notes"), lang),
                    )
                    for a in d.get("elo_api", [])
                ],
                result_shape=str(d.get("result_shape", "")).strip(),
                snippets=Snippets(
                    python=snip.get("python", "").strip("\n"),
                    node=snip.get("node", "").strip("\n"),
                    browser=snip.get("browser", "").strip("\n"),
                    go=snip.get("go", generate_multiruntime(d, "go")).strip("\n"),
                    php=snip.get("php", generate_multiruntime(d, "php")).strip("\n"),
                    java=snip.get("java", generate_multiruntime(d, "java")).strip("\n"),
                    rhino=snip.get("rhino", generate_multiruntime(d, "rhino")).strip("\n"),
                ),
                mock=d.get("mock") or {},
                attach_file=bool(d.get("attach_file", False)),
                lab_fs=bool(d.get("lab_fs", False)),
            )
        )
    topics.sort(key=lambda t: (t.category_id, t.order, t.id))
    return topics


def get_topic(topic_id: str, lang: str = "en") -> Topic | None:
    return next((t for t in load_topics(lang) if t.id == topic_id), None)


def categories(lang: str = "en") -> list[dict[str, Any]]:
    cats: dict[str, dict[str, Any]] = {}
    for t in load_topics(lang):
        c = cats.setdefault(
            t.category_id,
            {"id": t.category_id, "title": t.category, "topics": [], "has_deep": _deep_path(t.category_id).exists()},
        )
        c["topics"].append({"id": t.id, "title": t.title})
    return list(cats.values())


def _deep_path(category_id: str) -> Path:
    return get_settings().catalog_dir / category_id / "_deep.md"


def deep_doc(category_id: str) -> str | None:
    p = _deep_path(category_id)
    return p.read_text(encoding="utf-8") if p.exists() else None
