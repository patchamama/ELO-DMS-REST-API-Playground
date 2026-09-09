"""`elo_playground` must be importable from a bare `python file.py`.

The editable install (`-e ./shared/python`, from requirements-dev.txt) is what
makes `from elo_playground import connect` work outside the app / test process,
so a copied snippet in `sandbox/` runs with no PYTHONPATH ceremony.
"""
import subprocess
import sys
import tempfile
from importlib.metadata import PackageNotFoundError, version

import pytest


def test_client_importable_from_an_unrelated_cwd():
    try:
        version("elo-playground")
    except PackageNotFoundError:
        pytest.skip("elo-playground is not installed (run: pip install -r backend-python/requirements-dev.txt)")

    # a fresh process from an unrelated directory - no inherited sys.path, no conftest
    with tempfile.TemporaryDirectory() as d:
        proc = subprocess.run(
            [sys.executable, "-c", "import elo_playground, httpx; print(elo_playground.connect.__name__)"],
            cwd=d, capture_output=True, text=True, check=False,
        )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "connect" in proc.stdout
