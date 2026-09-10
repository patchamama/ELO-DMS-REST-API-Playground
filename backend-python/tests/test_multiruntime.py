"""Cross-runtime semantic parity for generated teaching examples."""
import json
import re

import yaml

from app.catalog import get_topic
from app.config import get_settings
from app.multiruntime import operation_plan


def test_generated_operation_plans_match_python_calls_for_every_topic():
    """Go/PHP/Java must retain Python method order and normalized parameters."""
    marker = re.compile(r"ELOPG_PLAN: (\[.*\])")
    for path in sorted(get_settings().catalog_dir.glob("*/*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        topic = get_topic(data["id"])
        expected = operation_plan(data)
        for language in ("go", "php", "java"):
            match = marker.search(getattr(topic.snippets, language))
            assert match, f"{data['id']} {language} missing semantic operation marker"
            assert json.loads(match.group(1)) == expected, f"{data['id']} {language} drifted from Python calls"
