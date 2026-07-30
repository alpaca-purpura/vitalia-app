"""Architecture test conftest.

``_deferred/`` contains tests ported verbatim from AISALESHT that depend
on ``src.modules.*`` paths not yet available in luana-platform.  They are
excluded from collection and serve as an audit trail of what still needs
migration when the corresponding packages are lifted.

Story 6 T-20: registry contract stability tests need to import the actual
registries which trigger luana_core_platform.core.config Settings validation.
Set safe CI defaults so arch tests run standalone without a full .env.
"""

from __future__ import annotations

import os

# Story 6 T-20 — env defaults so registry import (assets_tools → SessionLocal
# → Settings()) doesn't ValidationError. Mirrors luana-core-copilot/tests/
# conftest.py pattern. Arch tests are introspection-only — runtime values
# don't matter, only presence.
_ENV_DEFAULTS = {
    "LOG_LEVEL": "DEBUG",
    "DOMAIN_NAME": "localhost",
    "TRAEFIK_NETWORK": "test_network",
    "API_SECRET_KEY": "ci-test-secret-key-not-for-prod",
    "WHATSAPP_API_TOKEN": "ci-dummy-token",
    "WHATSAPP_PHONE_NUMBER_ID": "000000000",
    "WHATSAPP_VERIFY_TOKEN": "ci-verify-token",
    "OPENAI_API_KEY": "sk-ci-dummy-key",
    "REDIS_URL": "redis://localhost:6379/0",
    "QDRANT_URL": "http://localhost:6333",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres",
    "POSTGRES_DB": "test_db",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "API_URL": "http://localhost:8000",
    "DASHBOARD_DOMAIN": "http://localhost:3000",
    "PROMPT_SOURCE": "file",
    "AI_PROVIDER": "openai",
    "AI_MODEL_NANO": "gpt-4o-mini",
    "AI_MODEL_FAST": "deepseek-v4-flash",
    "AI_MODEL_REASONING": "deepseek-v4-pro",
    "AI_MODEL_AGENT": "kimi-k2.6",
    "AI_MODEL_VISION": "gpt-4o",
    "AI_MODEL_EMBEDDING": "text-embedding-3-large",
    "AI_PROVIDER_NANO": "openai",
    "AI_PROVIDER_FAST": "deepseek",
    "AI_PROVIDER_REASONING": "deepseek",
    "AI_PROVIDER_AGENT": "kimi",
    "AI_PROVIDER_VISION": "openai",
    "AI_PROVIDER_EMBEDDING": "openai",
    "KIMI_API_KEY": "ci-dummy-key",
    "DEEPSEEK_API_KEY": "ci-dummy-key",
    "DASHSCOPE_API_KEY": "ci-dummy-key",
}
for _k, _v in _ENV_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

collect_ignore_glob = ["_deferred/*"]
