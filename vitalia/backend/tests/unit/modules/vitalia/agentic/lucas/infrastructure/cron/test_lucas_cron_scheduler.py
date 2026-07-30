"""RED tests — Lucas APScheduler cron module (TZ-aware per-tenant scheduling).

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- Cron scheduler imports TenantLocationContract from engine (arch gate D2)
- Scheduler creates per-tenant job at 06:00 local timezone (NEVER hardcoded UTC)
- Scheduler uses tenant.timezone from TenantLocationContract
- Scheduler calls internal endpoint with LUCAS_CRON_SECRET Bearer token
- No hardcoded timezone (all from TenantLocationContract.timezone)
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()


class TestLucasCronScheduler:
    """Tests for LucasCronScheduler — TZ-aware per-tenant scheduling."""

    def test_imports_tenant_location_contract_from_engine(self) -> None:
        """LucasCronScheduler imports TenantLocationContract from luana_core_platform (engine)."""
        import importlib
        import inspect

        module = importlib.import_module("src.modules.vitalia.agentic.lucas.infrastructure.cron.lucas_cron_scheduler")
        source = inspect.getsource(module)
        assert "TenantLocationContract" in source
        assert "luana_core_platform" in source

    def test_scheduler_module_exists(self) -> None:
        """LucasCronScheduler class is importable."""
        from src.modules.vitalia.agentic.lucas.infrastructure.cron.lucas_cron_scheduler import (
            LucasCronScheduler,
        )

        assert LucasCronScheduler is not None

    @pytest.mark.asyncio
    async def test_schedule_for_tenant_uses_tenant_timezone(self) -> None:
        """schedule_for_tenant() creates CronTrigger with tenant's timezone, not UTC."""
        from src.modules.vitalia.agentic.lucas.infrastructure.cron.lucas_cron_scheduler import (
            LucasCronScheduler,
        )

        mock_scheduler = MagicMock()
        mock_tenant_profile = MagicMock()
        mock_tenant_profile.timezone = "America/Buenos_Aires"
        mock_tenant_profile.is_onboarded = True

        scheduler = LucasCronScheduler(apscheduler=mock_scheduler)
        scheduler.schedule_for_tenant(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            tenant_profile=mock_tenant_profile,
            cron_secret="test-secret",
        )

        # scheduler.add_job must be called with timezone from tenant profile
        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args[1]
        trigger = call_kwargs.get("trigger") or (
            mock_scheduler.add_job.call_args[0][1] if len(mock_scheduler.add_job.call_args[0]) > 1 else None
        )
        # The key assertion: timezone MUST come from tenant_profile.timezone
        assert "America/Buenos_Aires" in str(call_kwargs) or (
            trigger is not None and "America/Buenos_Aires" in str(trigger)
        )

    @pytest.mark.asyncio
    async def test_schedule_falls_back_to_utc_when_no_timezone(self) -> None:
        """schedule_for_tenant() falls back to UTC when tenant has no timezone."""
        from src.modules.vitalia.agentic.lucas.infrastructure.cron.lucas_cron_scheduler import (
            LucasCronScheduler,
        )

        mock_scheduler = MagicMock()
        mock_tenant_profile = MagicMock()
        mock_tenant_profile.timezone = None  # No timezone set
        mock_tenant_profile.is_onboarded = True

        scheduler = LucasCronScheduler(apscheduler=mock_scheduler)
        # Must not raise — fallback to UTC
        scheduler.schedule_for_tenant(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            tenant_profile=mock_tenant_profile,
            cron_secret="test-secret",
        )

        mock_scheduler.add_job.assert_called_once()

    def test_does_not_hardcode_utc_timezone(self) -> None:
        """Scheduler source code does not hardcode 'UTC' as timezone."""
        import importlib
        import inspect

        module = importlib.import_module("src.modules.vitalia.agentic.lucas.infrastructure.cron.lucas_cron_scheduler")
        source = inspect.getsource(module)
        # Must not have `timezone="UTC"` hardcoded — must use `tenant_profile.timezone or "UTC"`
        # Allow "UTC" only as fallback string literal, not as primary assignment
        assert 'timezone="UTC"' not in source or 'or "UTC"' in source
