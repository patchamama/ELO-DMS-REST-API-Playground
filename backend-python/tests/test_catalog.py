"""The curated catalogue loads and every topic is well-formed."""
import json

from app.catalog import categories, get_topic, load_topics
from app.config import get_settings


def test_topics_load_and_have_required_fields():
    topics = load_topics("en")
    assert len(topics) >= 10
    for t in topics:
        assert t.id and t.title and t.category
        assert t.category_id.startswith(tuple("0123456789"))
        # at least one runnable snippet
        assert t.snippets.python or t.snippets.node or t.snippets.browser
        # Every catalogue entry also gets standard-library mock examples for
        # backend runtimes and a reviewed server-side Rhino artifact.
        assert t.snippets.go and t.snippets.php and t.snippets.java and t.snippets.rhino
        assert "ELOPG_MOCK_DATA" in t.snippets.go
        assert "ELOPG_MOCK_DATA" in t.snippets.php
        assert "ELOPG_MOCK_DATA" in t.snippets.java
        assert "NOT Web Client injection" in t.snippets.rhino


def test_every_api_ref_points_somewhere():
    for t in load_topics("en"):
        for ref in t.elo_api:
            assert ref.method and ref.rpc
            assert ref.doc_url  # link template (contains {base} or an absolute URL)


def test_topic_ids_are_unique():
    ids = [t.id for t in load_topics("en")]
    assert len(ids) == len(set(ids))


def test_categories_group_topics_in_order():
    cats = categories("en")
    assert cats == sorted(cats, key=lambda c: c["id"])
    total = sum(len(c["topics"]) for c in cats)
    assert total == len(load_topics("en"))


def test_mock_blocks_are_json_serialisable():
    for t in load_topics("en"):
        json.dumps(t.mock)  # would raise on a bad value


def test_attach_file_flag_loads():
    by_id = {t.id: t for t in load_topics("en")}
    assert by_id["ocr.extract"].attach_file is True
    assert by_id["connection.login"].attach_file is False


def test_lab_fs_flag_loads():
    by_id = {t.id: t for t in load_topics("en")}
    assert by_id["lab.fs-sync"].lab_fs is True
    assert by_id["connection.login"].lab_fs is False


def test_default_fixture_is_valid_json_and_has_login():
    default = get_settings().fixtures_dir / "default.json"
    data = json.loads(default.read_text(encoding="utf-8"))
    assert "login" in data


def test_get_topic_roundtrips():
    assert get_topic("connection.login", "en") is not None
    assert get_topic("does.not.exist", "en") is None


def test_localised_titles_resolve_per_language():
    en = get_topic("connection.login", "en")
    de = get_topic("connection.login", "de")
    es = get_topic("connection.login", "es")
    assert en.title != de.title != es.title
    assert de.category == "Verbindung & Sitzung"
    assert es.category == "Conexión y sesión"


def test_summaries_and_notes_are_translated_in_de_and_es():
    for lang in ("de", "es"):
        for t in load_topics(lang):
            en = get_topic(t.id, "en")
            assert t.summary and t.summary != en.summary, f"{t.id} summary not translated to {lang}"
            for i, (ref, en_ref) in enumerate(zip(t.elo_api, en.elo_api)):
                if en_ref.notes:
                    assert ref.notes and ref.notes != en_ref.notes, f"{t.id} note #{i} not translated to {lang}"
