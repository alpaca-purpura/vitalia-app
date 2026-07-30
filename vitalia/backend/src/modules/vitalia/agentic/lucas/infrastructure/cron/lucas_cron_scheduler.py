# cap: agentic.lucas-daily-analysis
# story-origin: TBD
"""Lucas infrastructure — LucasCronScheduler (APScheduler, TZ-aware per-tenant).

Schedules per-tenant Lucas cron jobs at 06:00 LOCAL time using tenant's
timezone from TenantLocationContract. NEVER hardcodes timezone.

Architecture:
- At app startup, scheduler is populated with per-tenant jobs.
- Each job fires POST /api/v1/copilot/internal/lucas/cron-trigger with Bearer secret.
- Auth handled by internal route (LUCAS_CRON_SECRET env var).

TZ decision per ADR D2 (Chris ratified 2026-05-17):
  TenantLocationContract.timezone → CronTrigger(hour=6, minute=0, timezone=...)
  Fallback: "UTC" when tenant has no timezone set.

Engine import (READ-ONLY):
  from luana_core_platform.links.ports.tenant_profile import TenantLocationContract

This import is enforced by arch fitness test:
  vitalia/backend/tests/architecture/test_lucas_cron_tz_aware.py
"""

from __future__ import annotations

from uuid import UUID

import httpx
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Engine import READ-ONLY — TenantLocationContract is a Protocol from luana_core_platform
from luana_core_platform.links.ports.tenant_profile import TenantLocationContract

logger = structlog.get_logger()

_DEFAULT_TIMEZONE = "UTC"
_CRON_HOUR = 6
_CRON_MINUTE = 0
_HTTP_TIMEOUT_SECONDS = 30.0


class LucasCronScheduler:
    """APScheduler-based per-tenant cron scheduler for Lucas growth setter.

    Schedules a daily cron at 06:00 in each tenant's LOCAL timezone.
    NEVER uses hardcoded UTC — always reads from TenantLocationContract.timezone.

    Usage (at app startup):
        scheduler = LucasCronScheduler(apscheduler=AsyncIOScheduler())
        for tenant in active_tenants:
            scheduler.schedule_for_tenant(
                tenant_id=tenant.id,
                clinic_id=tenant.clinic_id,
                tenant_profile=tenant.profile,  # implements TenantLocationContract
                cron_secret=settings.LUCAS_CRON_SECRET,
            )
        scheduler.start()
    """

    def __init__(self, apscheduler: AsyncIOScheduler) -> None:
        """Initialise with APScheduler instance."""
        self._scheduler = apscheduler

    def schedule_for_tenant(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        tenant_profile: TenantLocationContract,
        cron_secret: str,
        internal_base_url: str = "http://localhost:8002",
    ) -> None:
        """Schedule daily 06:00 local-time cron for one tenant.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite dual filter).
            tenant_profile: TenantLocationContract — provides .timezone.
            cron_secret: Bearer secret for internal endpoint auth.
            internal_base_url: Base URL of the vitalia backend (default localhost:8002).

        Timezone resolution:
            1. Use tenant_profile.timezone if set (IANA string, e.g. "America/Buenos_Aires").
            2. Fall back to "UTC" if None.
            NEVER use a hardcoded timezone other than this fallback.
        """
        tz = tenant_profile.timezone or _DEFAULT_TIMEZONE

        trigger = CronTrigger(
            hour=_CRON_HOUR,
            minute=_CRON_MINUTE,
            timezone=tz,
        )

        job_id = f"lucas_cron_{tenant_id}_{clinic_id}"

        self._scheduler.add_job(
            self._fire_cron_trigger,
            trigger=trigger,
            kwargs={
                "tenant_id": tenant_id,
                "clinic_id": clinic_id,
                "cron_secret": cron_secret,
                "internal_base_url": internal_base_url,
            },
            id=job_id,
            replace_existing=True,
        )

        logger.info(
            "lucas_cron_scheduled",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            timezone=tz,
            hour=_CRON_HOUR,
        )

    @staticmethod
    async def _fire_cron_trigger(
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        cron_secret: str,
        internal_base_url: str,
    ) -> None:
        """HTTP POST to internal Lucas cron trigger endpoint.

        Fires the internal route that runs all 3 Lucas services for this tenant.
        Bearer token = LUCAS_CRON_SECRET (set in env).
        Graceful degradation: logs error on failure, does not raise.
        """
        url = f"{internal_base_url}/api/v1/copilot/internal/lucas/cron-trigger"
        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {cron_secret}",
                        "X-Tenant-ID": str(tenant_id),
                        "X-Clinic-ID": str(clinic_id),
                    },
                    json={},
                )
                response.raise_for_status()
                logger.info(
                    "lucas_cron_triggered",
                    tenant_id=str(tenant_id),
                    clinic_id=str(clinic_id),
                    status_code=response.status_code,
                )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "lucas_cron_http_error",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                status_code=exc.response.status_code,
            )
        except Exception:
            logger.exception(
                "lucas_cron_unexpected_error",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
            )

    def start(self) -> None:
        """Start the APScheduler (non-blocking for async context)."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("lucas_cron_scheduler_started")

    def shutdown(self) -> None:
        """Shut down the APScheduler gracefully."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("lucas_cron_scheduler_stopped")
