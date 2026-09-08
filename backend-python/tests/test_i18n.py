"""UI translation catalogue: three languages, all keys present, fallback works."""
import json
import re

from app.config import get_settings
from app.i18n import FALLBACK, catalogue, t

_PLACEHOLDER = re.compile(r"\{[^}]+\}")


def _raw(lang: str) -> dict:
    p = get_settings().frontend_dir / "i18n" / f"{lang}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_english_catalogue_is_populated():
    en = catalogue("en")
    assert en.get("app.title")
    assert en.get("run.button")


def test_de_and_es_have_the_same_keys_as_en():
    en_keys = set(_raw("en"))
    for lang in ("de", "es"):
        missing = en_keys - set(_raw(lang))
        assert not missing, f"{lang}.json is missing: {sorted(missing)}"


def test_placeholder_sets_match_across_languages():
    en = _raw("en")
    for lang in ("de", "es"):
        cat = _raw(lang)
        for key, en_text in en.items():
            if key not in cat:
                continue
            assert set(_PLACEHOLDER.findall(en_text)) == set(_PLACEHOLDER.findall(cat[key])), key


def test_unknown_language_falls_back_to_english():
    assert catalogue("zz").get("app.title") == catalogue("en").get("app.title")


def test_unknown_key_returns_the_key():
    assert t("no.such.key", "en") == "no.such.key"


def test_fallback_language_constant():
    assert FALLBACK == "en"
