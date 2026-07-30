# cap: marketing.referrals-leaderboard
# story-origin: TBD
"""referrals_value_sync — ARQ cron job, daily 10:00 UTC.

Refreshes referral conversion_value_cents from completed appointments
for referred patients. Transitions referrals to 'converted' status when
non-zero appointment value is detected.

Steps per referral (status in 'signed_up', 'converted'):
  1. Sum conversion_value_cents from vitalia_appointments for referred_patient_id.
  2. If value changed: update referral.conversion_value_cents + save.
  3. If status was 'signed_up' and new value > 0: transition to 'converted' +
     publish ReferralConverted event.

HIPAA-lite:
  - referred_patient_id is UUID reference only (no PHI stored in this table).
  - Dual filter tenant_id + clinic_id enforced on appointment queries.
  - No patient name or health data in payloads.

Soft-fail: one referral processing failure does not abort the sync.

downstream-regression-na: brand-local marketing cron — no cross-brand consumers
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from luana_core_platform.workers.cron_envelope import cron_envelope

from src.modules.vitalia.marketing.domain.events import ReferralConverted
from src.modules.vitalia.marketing.infrastructure.repositories.referral_repository import (
    ReferralRepository,
)

try:
    from luana_core_events.outbox import adapter_bus  # type: ignore[import]
except ImportError:  # pragma: no cover
    import structlog as _structlog

    _fb_logger = _structlog.get_logger()

    class _FallbackBus:  # type: ignore[no-redef]
        """No-op fallback bus for dev environments without luana_core_events installed."""

        async def publish(self, event: object) -> None:  # noqa: D102
            _fb_logger.warning("adapter_bus.fallback_publish", event=repr(event))

    adapter_bus = _FallbackBus()

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Appointment query helper (in-module, patchable for tests)
# ---------------------------------------------------------------------------


class _AppointmentRepository:
    """Lightweight query helper for vitalia_appointments.

    Used only by the referrals_value_sync cron — reads conversion_value_cents
    for a given referred_patient_id (UUID reference, no PHI access).

    Dual filter: tenant_id + clinic_id on all queries.
    """

    def __init__(self, session: Any) -> None:
        """Initialize with an async SQLAlchemy session."""
        self._session = session

    async def sum_conversion_value_for_patient(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        referred_patient_id: UUID,
    ) -> int | None:
        """Sum conversion_value_cents for completed appointments of a referred patient.

        Queries vitalia_appointments WHERE:
          - tenant_id = tenant_id
          - clinic_id = clinic_id (HIPAA-lite dual filter)
          - patient_id = referred_patient_id
          - status = 'completed'
          - deleted_at IS NULL

        Args:
            tenant_id: Tenant UUID for root isolation.
            clinic_id: Clinic UUID for secondary isolation.
            referred_patient_id: UUID of the referred patient (no PHI).

        Returns:
            Total conversion_value_cents as integer, or None if no completed appointments.
        """
        from sqlalchemy import text  # noqa: PLC0415

        sql = text(
            "SELECT COALESCE(SUM(conversion_value_cents), 0) AS total "
            "FROM vitalia_appointments "
            "WHERE tenant_id = :tenant_id "
            "AND clinic_id = :clinic_id "
            "AND patient_id = :patient_id "
            "AND status = 'completed' "
            "AND deleted_at IS NULL"
        )
        result = await self._session.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "clinic_id": clinic_id,
                "patient_id": referred_patient_id,
            },
        )
        row = result.fetchone()
        if row is None:
            return None
        total: int = int(row.total or 0)
        return total


# ---------------------------------------------------------------------------
# Injectable factory helpers (patchable for tests)
# ---------------------------------------------------------------------------


def _get_referral_repo() -> ReferralRepository:
    """Return ReferralRepository instance (patchable in tests)."""
    from src.core.db import get_sync_session  # type: ignore[import]  # noqa: PLC0415

    return ReferralRepository(session=get_sync_session())


def _get_appointment_repo() -> _AppointmentRepository:
    """Return _AppointmentRepository instance (patchable in tests)."""
    from src.core.db import get_sync_session  # type: ignore[import]  # noqa: PLC0415

    return _AppointmentRepository(session=get_sync_session())


# ---------------------------------------------------------------------------
# Cron job
# ---------------------------------------------------------------------------


@cron_envelope("vitalia.cron.referrals_value_sync", ttl=86400)  # 24h TTL
async def referrals_value_sync(ctx: dict[str, Any]) -> None:
    """Daily 10:00 UTC — refresh referral conversion values from completed appointments.

    Iterates all active referrals (status signed_up or converted) and recomputes
    conversion_value_cents from the sum of completed appointment values for the
    referred patient.

    Transitions referral from 'signed_up' → 'converted' when non-zero value detected.
    Publishes ReferralConverted domain event on transition.

    Soft-fail per referral — one DB error does not abort the sync.
    """
    referral_repo = _get_referral_repo()
    appointment_repo = _get_appointment_repo()

    # Query all active referrals (cross-tenant sweep — no tenant_id filter here)
    active_referrals = await referral_repo.list_active_for_value_sync()

    updated = 0
    converted = 0
    failed = 0

    for referral in active_referrals:
        tenant_id: UUID = referral.tenant_id
        clinic_id: UUID = referral.clinic_id
        referred_patient_id: UUID | None = referral.referred_patient_id

        if referred_patient_id is None:
            continue

        try:
            total_value = await appointment_repo.sum_conversion_value_for_patient(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                referred_patient_id=referred_patient_id,
            )

            if total_value is None:
                continue

            old_value = referral.conversion_value_cents
            if old_value == total_value:
                # No change — skip write
                continue

            # Value changed — update referral
            was_signed_up = referral.status == "signed_up"
            referral.conversion_value_cents = total_value

            if was_signed_up and total_value > 0:
                referral.status = "converted"
                referral.converted_at = datetime.now(UTC)
                converted += 1

            await referral_repo.save(referral)
            updated += 1

            logger.info(
                "referrals_value_sync.referral_updated",
                referral_id=str(referral.id),
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                old_value=old_value,
                new_value=total_value,
                transitioned_to_converted=was_signed_up and total_value > 0,
            )

            # Publish ReferralConverted if newly transitioned
            if was_signed_up and total_value > 0:
                try:
                    await adapter_bus.publish(
                        ReferralConverted(
                            tenant_id=tenant_id,
                            referral_id=referral.id,
                            referred_patient_id=referred_patient_id,
                        )
                    )
                except Exception as event_exc:
                    logger.warning(
                        "referrals_value_sync.event_publish_failed",
                        referral_id=str(referral.id),
                        error=str(event_exc),
                    )

        except Exception as exc:
            # Soft-fail per referral
            failed += 1
            logger.warning(
                "referrals_value_sync.referral_error",
                referral_id=str(referral.id),
                tenant_id=str(tenant_id),
                error=str(exc),
            )

    logger.info(
        "referrals_value_sync.completed",
        total=len(active_referrals),
        updated=updated,
        converted=converted,
        failed=failed,
    )
