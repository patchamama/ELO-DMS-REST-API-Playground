"""Vendored browser libraries are pinned by hash (supply-chain guard).

If you deliberately upgrade a library, run it through the app once, then update
the hash here in the same commit.
"""
import hashlib

import pytest

from app.config import get_settings

_PINS = {
    "highlight.github.css": "3a9a5def8b9c311e5ae43abde85c63133185eed4f0d9f67fea4b00a8308cf066",
    "highlight.min.js": "471ef9ae90c407af440fcdc48edfeeb562106b3267bd12d99071c162fb52ed32",
    "marked.min.js": "15fabce5b65898b32b03f5ed25e9f891a729ad4c0d6d877110a7744aa847a894",
    "purify.min.js": "6407576993a5aa1303eaf9fefb95e5cfc1c0c80645bd3717db671727e6b55b91",
    "codemirror.min.js": "f102bb61fb2ac45c3a611847edd9948faad0ab22a83a2dfa9974be5031079b15",
    "codemirror.min.css": "11077112ab6955d29fe41085c62365c7d4a2f00a570c7475e2aec2a8cbc85fc4",
    "cm-python.min.js": "6d19a4ba8b05a354935ceebf490582faffa047c86c4715a2b504b14319eb6399",
    "cm-javascript.min.js": "99b46f351b4b1ce8a14cdf04fe4235ecb429b5b7b986867034a7dc195a710a58",
    "cm-multiruntime.min.js": "023c5a8e19c8417e4290ce8236fc68337bede7098d53b4e787a87bacfc2dbf0e",
}


@pytest.mark.parametrize("name,expected", sorted(_PINS.items()))
def test_vendor_file_matches_pin(name: str, expected: str):
    path = get_settings().frontend_dir / "vendor" / name
    assert path.is_file(), f"missing vendored file: {name}"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == expected, f"{name} changed - review and update the pin"


def test_editor_mode_selection_covers_every_runtime():
    """Every selectable runtime must choose a locally loaded CodeMirror mode."""
    app_js = (get_settings().frontend_dir / "static" / "app.js").read_text(encoding="utf-8")
    for runtime, mode in {"go": "go", "php": "php", "java": "java", "rhino": "javascript"}.items():
        assert f'{runtime}: "{mode}"' in app_js
    base = (get_settings().frontend_dir / "templates" / "base.html").read_text(encoding="utf-8")
    assert "cm-multiruntime.min.js" in base
