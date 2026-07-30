"""Architecture fitness gate — Lucas cron scheduler TZ-aware import.

Enforces ADR D2 (Chris ratified 2026-05-17):
  LucasCronScheduler MUST import TenantLocationContract from
  luana_core_platform.links.ports.tenant_profile (engine).

This ensures the cron scheduler uses tenant-local timezone from the
engine contract — never hardcodes timezone.

Gate: if this test fails, the scheduler was refactored to remove the
      engine import and must be restored.
"""

from __future__ import annotations

import importlib
import inspect


def test_lucas_cron_scheduler_imports_tenant_location_contract() -> None:
    """LucasCronScheduler imports TenantLocationContract from luana_core_platform engine."""
    module = importlib.import_module("src.modules.vitalia.agentic.lucas.infrastructure.cron.lucas_cron_scheduler")
    source = inspect.getsource(module)
    assert "TenantLocationContract" in source, (
        "LucasCronScheduler must import TenantLocationContract (per ADR D2 + 05-guidelines.md)"
    )


def test_lucas_cron_scheduler_imports_from_engine_package() -> None:
    """TenantLocationContract import MUST come from luana_core_platform (engine, not local copy)."""
    module = importlib.import_module("src.modules.vitalia.agentic.lucas.infrastructure.cron.lucas_cron_scheduler")
    source = inspect.getsource(module)
    assert "luana_core_platform" in source, (
        "TenantLocationContract must be imported from luana_core_platform (engine package) — not defined locally."
    )


def test_lucas_cron_scheduler_no_hardcoded_timezone() -> None:
    """LucasCronScheduler must not use hardcoded 'America/...' or non-fallback timezone."""
    module = importlib.import_module("src.modules.vitalia.agentic.lucas.infrastructure.cron.lucas_cron_scheduler")
    source = inspect.getsource(module)
    # The only timezone= literal allowed is the fallback "UTC" in `or "UTC"` pattern
    # or `_DEFAULT_TIMEZONE = "UTC"`. Hardcoded specific zones are forbidden.
    forbidden_patterns = [
        'timezone="America/',
        "timezone='America/",
        'timezone="Europe/',
        "timezone='Europe/",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in source, (
            f"LucasCronScheduler must not hardcode timezone '{pattern}'. "
            "Use tenant_profile.timezone from TenantLocationContract."
        )


def test_lucas_cron_class_uses_tenant_profile_timezone() -> None:
    """LucasCronScheduler.schedule_for_tenant() must read .timezone from tenant_profile."""
    module = importlib.import_module("src.modules.vitalia.agentic.lucas.infrastructure.cron.lucas_cron_scheduler")
    source = inspect.getsource(module)
    # Must reference tenant_profile.timezone
    assert "tenant_profile.timezone" in source, (
        "LucasCronScheduler must use tenant_profile.timezone for CronTrigger "
        "(per ADR D2 — TenantLocationContract.timezone)"
    )
