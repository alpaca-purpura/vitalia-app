# cap: marketing.referrals-leaderboard
# story-origin: TBD
"""ReferralsService — patient referral leaderboard + code generation.

Application layer — proxies to LucasReferralsService snapshot reads
and Referral repository for code generation.

HIPAA-lite:
  - Dual filter: tenant_id + clinic_id on all queries.
  - top_referrers uses referrer_id (UUID hash) only — NO patient names.
  - Referral codes do NOT contain PHI.

downstream-regression-na: brand-local marketing application service (vitalia-only)
"""

from __future__ import annotations

import datetime
import secrets
import string
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.agentic.lucas.application.services.lucas_referrals_service import (
    LucasReferralsService,
    TenantLocaleProtocol,
)
from src.modules.vitalia.marketing.application.dtos.marketing_dtos import (
    ReferralsResponse,
    ReferrerEntryResponse,
)
from src.modules.vitalia.marketing.domain.events import ReferralCodeGenerated
from src.modules.vitalia.marketing.infrastructure.models.referral_model import ReferralModel

# Outbox adapter_bus per anti-duplication.md — use core engine
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

_REFERRAL_CODE_LENGTH = 8
_REFERRAL_CODE_CHARS = string.ascii_uppercase + string.digits


class ReferralsService:
    """Application service for patient referral program.

    Responsibilities:
      - get_referrals(): proxy to LucasReferralsService snapshot
      - generate_code(): create referral code for a patient + persist + emit event

    HIPAA: No patient names stored or returned. referrer_id = UUID hash.
    """

    def __init__(
        self,
        *,
        lucas_referrals_service: LucasReferralsService,
        referral_repo: object,
        locale: TenantLocaleProtocol,
    ) -> None:
        """Initialise with DI'd services.

        Args:
            lucas_referrals_service: LucasReferralsService (read-only).
            referral_repo: ReferralRepository for persisting new codes.
            locale: TenantLocale VO (available for future currency-related metrics).
        """
        self._lucas_referrals_service = lucas_referrals_service
        self._referral_repo = referral_repo
        self._locale = locale

    async def get_referrals(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: datetime.date,
        period_end: datetime.date,
    ) -> ReferralsResponse:
        """Return referrals leaderboard snapshot for a clinic period.

        Proxies to LucasReferralsService.compute_referrals() which
        queries analytics engine + persists snapshot.

        HIPAA: top_referrers contains referrer_id (UUID hash) — no patient names.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA dual filter).
            period_start: Start of period (inclusive).
            period_end: End of period (inclusive).

        Returns:
            ReferralsResponse with leaderboard data.
        """
        snapshot = await self._lucas_referrals_service.compute_referrals(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start,
            period_end=period_end,
            locale=self._locale,
        )

        top_referrers = [
            ReferrerEntryResponse(
                referrer_id=str(entry.get("referrer_id", "")),
                referral_count=int(entry.get("referral_count", 0)),
                converted_count=int(entry.get("converted_count", 0)),
                rank=int(entry.get("rank", 0)),
            )
            for entry in snapshot.top_referrers
        ]

        logger.info(
            "referrals_service.get_referrals",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            total_referrals=snapshot.total_referrals,
        )

        return ReferralsResponse(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            clinic_id=snapshot.clinic_id,
            period_start=snapshot.period_start,
            period_end=snapshot.period_end,
            top_referrers=top_referrers,
            total_referrals=snapshot.total_referrals,
            total_converted=snapshot.total_converted,
            computed_at=snapshot.computed_at,
        )

    async def generate_code(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> ReferralModel:
        """Generate a unique referral code for a patient.

        Creates a new Referral record with a cryptographically random code.
        Emits ReferralCodeGenerated domain event via outbox.

        HIPAA: patient_id is UUID reference only — no patient names stored.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA dual filter).
            patient_id: UUID of the patient generating the referral code.

        Returns:
            Persisted ReferralModel with the generated code.
        """
        code = self._generate_unique_code()
        referral_id = uuid4()

        model = ReferralModel()
        model.id = referral_id
        model.tenant_id = tenant_id
        model.clinic_id = clinic_id
        model.patient_id = patient_id
        model.code = code
        model.status = "open"

        saved = await self._referral_repo.save(model)

        # Outbox event
        event = ReferralCodeGenerated(
            tenant_id=tenant_id,
            referral_id=referral_id,
            patient_id=patient_id,
            code=code,
        )
        await adapter_bus.publish(event)

        logger.info(
            "referrals_service.code_generated",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            referral_id=str(referral_id),
        )

        return saved

    @staticmethod
    def _generate_unique_code() -> str:
        """Generate a cryptographically random referral code.

        Returns:
            8-character alphanumeric uppercase code (e.g. 'A3KJ9PQZ').
        """
        return "".join(secrets.choice(_REFERRAL_CODE_CHARS) for _ in range(_REFERRAL_CODE_LENGTH))
