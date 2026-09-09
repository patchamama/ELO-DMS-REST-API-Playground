"""Make ``app`` and the shared ``elo_playground`` package importable from tests,
regardless of the directory pytest is started from."""
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent
_SHARED_PY = _BACKEND.parent / "shared" / "python"

for p in (_BACKEND, _SHARED_PY, _BACKEND.parent):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
