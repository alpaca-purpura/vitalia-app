# cap: __shared__
"""T-2 — driver test: verify that importing luana_core_copilot.api.chat
does NOT crash when only multibrand env vars are present (no legacy
POSTGRES_*, WHATSAPP_*, QDRANT_URL, TRAEFIK_NETWORK, etc.).

RED at T-2 start — any module on the import-path that does a module-level
``settings`` access (e.g. ``from database import redis_client`` or
``settings = Settings()`` eager) triggers Settings() instantiation →
pydantic ValidationError because the legacy mandatory fields are absent.

GREEN once every module on the import-path uses ``get_settings()`` *inside
functions* (lazy real), not at module-level.

The check runs in a FRESH SUBPROCESS interpreter with a clean env, so it
tests the real cold-start import behaviour of a brand backend AND never
mutates the parent test process's ``sys.modules`` / lru_caches (no
cross-test pollution — earlier in-process ``del sys.modules`` + reload
caused duplicate-module identity hazards in unrelated tests).
"""

from __future__ import annotations

import os
import subprocess
import sys

# Legacy app-config vars a multibrand brand backend does NOT provide.
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
)


def test_chat_api_importable_with_multibrand_env_only() -> None:
    """Importing luana_core_copilot.api.chat must NOT raise ValidationError
    when the environment contains only multibrand vars (DATABASE_URL +
    LITELLM_* etc) and the legacy POSTGRES_*/WHATSAPP_*/QDRANT_URL vars
    are absent.

        RED  → at least one module on the import-path does a module-level
               settings access → Settings() at import → ValidationError.
        GREEN → every on-path module defers settings access to inside
               functions (``get_settings()`` called within a function body).
    """
    # Start from the real system env (PATH, venv, locale, …) so the
    # subprocess interpreter + editable installs resolve, then strip the
    # legacy app-config vars and inject only the multibrand ones.
    env = os.environ.copy()
    for var in _LEGACY_VARS:
        env.pop(var, None)
    env["DATABASE_URL"] = "postgresql://luana:luana@localhost:5432/vitalia"
    env["REDIS_URL"] = "redis://localhost:6379/0"
    env["LITELLM_BASE_URL"] = "http://litellm:4000"
    env["LITELLM_API_KEY"] = "lk-multibrand-ci-key"

    result = subprocess.run(
        [sys.executable, "-c", "import luana_core_copilot.api.chat"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0 and "ValidationError" not in result.stderr, (
        "importing luana_core_copilot.api.chat with multibrand-only env raised — "
        "a module on the import-path still instantiates Settings() at module-level "
        "(migrate it to get_settings() inside a function).\n"
        f"--- stderr ---\n{result.stderr}"
    )
