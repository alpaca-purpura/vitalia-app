# cap: __shared__
"""Multibrand contract: Settings() must INSTANTIATE (not only import) under a
minimal multibrand env, and database_url must resolve from DATABASE_URL.

The earlier brand-mountable lift made the import path lazy (chat.py imports
without crashing). This test guards the next, stronger property the lift
actually needs: a brand that EXERCISES a core router hits get_db() ->
get_settings() -> Settings(), which validates every field. Before this fix
the legacy-only required fields (POSTGRES_*/WHATSAPP_*/QDRANT_URL/...) made
that raise ValidationError for any brand that does not provide them.

Two layers:
  * subprocess (real cold-start, clean env): instantiate under multibrand-only
    env + resolve database_url from DATABASE_URL.
  * in-process unit: the database_url resolution branches (scheme normalize,
    POSTGRES_* fallback, neither -> RuntimeError).
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest
from luana_core_platform.core.config import Settings

# Legacy "Visionarias Brain" vars a multibrand brand backend does NOT provide.
_LEGACY_VARS = (
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "WHATSAPP_API_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_VERIFY_TOKEN",
    "QDRANT_URL",
    "TRAEFIK_NETWORK",
    "DOMAIN_NAME",
    "API_SECRET_KEY",
    "OPENAI_API_KEY",
    "LOG_LEVEL",
    "API_URL",
)

# Driver run inside a clean subprocess interpreter: instantiate Settings with
# ONLY multibrand env present and assert database_url resolves to the sync
# scheme. Exit 0 + the OK marker == contract holds.
_DRIVER = (
    "from luana_core_platform.core.config import get_settings;"
    "s = get_settings();"
    "u = s.database_url;"
    "assert u == 'postgresql://luana:luana@localhost:5432/comunify_dev', u;"
    "print('OK')"
)


def test_settings_instantiates_with_multibrand_env_only() -> None:
    """Settings() under a minimal multibrand env (DATABASE_URL + REDIS_URL +
    LITELLM_*) must instantiate AND resolve database_url — no ValidationError
    for the absent legacy fields."""
    env = os.environ.copy()
    for var in _LEGACY_VARS:
        env.pop(var, None)
    # Brands set the asyncpg form in docker-compose — must be normalized to sync.
    env["DATABASE_URL"] = "postgresql+asyncpg://luana:luana@localhost:5432/comunify_dev"
    env["REDIS_URL"] = "redis://localhost:6379/0"
    env["LITELLM_BASE_URL"] = "http://litellm:4000"

    result = subprocess.run(
        [sys.executable, "-c", _DRIVER],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0 and "OK" in result.stdout, (
        "Settings() with multibrand-only env failed to instantiate/resolve — a "
        "legacy field is still required, or database_url did not resolve from "
        f"DATABASE_URL.\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )


# DB env keys the conftest seeds into os.environ — cleared per-test so each
# case controls resolution unambiguously (init kwargs do NOT override an env
# value already present, so we drive via the environment).
_DB_ENV_KEYS = (
    "DATABASE_URL",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
)


def _clear_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _DB_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_database_url_prefers_and_normalizes_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DATABASE_URL wins over POSTGRES_* and is normalized to the sync scheme
    (so create_engine works; async consumers re-add +asyncpg themselves)."""
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
    monkeypatch.setenv("POSTGRES_USER", "legacy")
    monkeypatch.setenv("POSTGRES_HOST", "legacy-host")
    assert Settings(_env_file=None).database_url == "postgresql://u:p@h:5432/db"


def test_database_url_falls_back_to_postgres_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With DATABASE_URL absent, compose from POSTGRES_* (legacy-standalone)."""
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "pw")
    monkeypatch.setenv("POSTGRES_DB", "legacy_db")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    assert Settings(_env_file=None).database_url == "postgresql://postgres:pw@localhost:5432/legacy_db"


def test_database_url_raises_when_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Neither DATABASE_URL nor POSTGRES_* -> loud RuntimeError at use-time,
    never a silent/blanket import crash."""
    _clear_db_env(monkeypatch)
    with pytest.raises(RuntimeError, match="No database configured"):
        _ = Settings(_env_file=None).database_url
