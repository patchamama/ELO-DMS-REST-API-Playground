"""Tiny UI translation catalogue (same shape as ELOphant's app/i18n).

Flat ``{"dotted.key": "text"}`` JSON per language under ``frontend/i18n/``.
Unknown key or missing language falls back to English, then to the key itself.
For Milestone 1 only ``en.json`` is populated.
"""
from __future__ import annotations

import json
from functools import lru_cache

from .config import get_settings

FALLBACK = "en"


@lru_cache
def _catalogue(lang: str) -> dict[str, str]:
    path = get_settings().frontend_dir / "i18n" / f"{lang}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def t(key: str, lang: str = "en", **kwargs: object) -> str:
    template = _catalogue(lang).get(key) or _catalogue(FALLBACK).get(key) or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template


def catalogue(lang: str) -> dict[str, str]:
    """The merged catalogue (English base overlaid with ``lang``) for the frontend."""
    merged = dict(_catalogue(FALLBACK))
    merged.update(_catalogue(lang))
    return merged
