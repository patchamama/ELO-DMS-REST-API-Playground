"""Application configuration, loaded from the environment / a local .env file.

All variables use the ``ELOPG_`` prefix, e.g. ``ELOPG_ELO_BASE_URL``.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .../elo-api-playground/  (parent of backend-python/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # .env lives at the project root (elo-api-playground/.env), so the same file
    # is used whether the app is started from the repo root or from backend-python/.
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"), env_prefix="ELOPG_", extra="ignore"
    )

    host: str = "127.0.0.1"
    port: int = 8010  # 8000 is the sibling ELOphant app; keep them apart

    # ---- default ELO connection ------------------------------------------- #
    # These pre-fill the connection form. A snippet can still be run in mock
    # mode with no ELO reachable.
    elo_base_url: str = "http://localhost:9090/ix-Repository1"
    elo_user: str = "Administrator"
    elo_password: str = ""            # left blank on purpose; type it in the UI
    tls_verify: bool = True

    # ---- runner --------------------------------------------------------- #
    mock: bool = True                 # default state of the UI "Mock mode" toggle
    node_url: str = "http://127.0.0.1:8787"   # the backend-node runner service
    run_timeout_s: int = 15
    run_output_cap: int = 262_144     # 256 KiB per stream

    project_root: Path = _PROJECT_ROOT

    # ---- derived paths ------------------------------------------------- #
    @property
    def catalog_dir(self) -> Path:
        return self.project_root / "catalog"

    @property
    def snippets_dir(self) -> Path:
        return self.project_root / "snippets"

    @property
    def fixtures_dir(self) -> Path:
        return self.project_root / "fixtures" / "ix"

    @property
    def shared_python(self) -> Path:
        return self.project_root / "shared" / "python"

    @property
    def shared_browser(self) -> Path:
        return self.project_root / "shared" / "browser"

    @property
    def frontend_dir(self) -> Path:
        return self.project_root / "frontend"

    @property
    def runtime_dir(self) -> Path:
        return self.project_root / "runtime"

    def ensure_dirs(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s
