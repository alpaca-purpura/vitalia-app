# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""Referral domain entity — patient referral program tracking.

Per HIPAA-lite: patient_id is stored as UUID reference (no name/DNI/PHI).
Referral codes contain NO PHI.

Status lifecycle per spec § 2.4:
  OPEN → SHARED → SIGNED_UP → CONVERTED (terminal positive)
  OPEN | SHARED | SIGNED_UP → EXPIRED (terminal negative — cron sweep)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.modules.vitalia.marketing.domain.enums import ReferralStatus


@dataclass
class Referral:
    """A patient referral record linking referrer to referred patient.

    Uniquely identified by the referral code.
    PHI-free: uses patient_id UUID reference only, no name/DNI stored here.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    code: str
    status: ReferralStatus
    created_at: datetime
    updated_at: datetime

    # Conversion tracking
    referred_patient_id: uuid.UUID | None = None
    converted_at: datetime | None = None
    expires_at: datetime | None = None
    deleted_at: datetime | None = None

    # Value tracking — populated by referrals_value_sync cron
    conversion_value_cents: int | None = None
    # ISO-4217 currency code — NEVER hardcoded; from tenant locale
    currency: str | None = None

    # Engagement timestamps
    shared_at: datetime | None = field(default=None)
    signed_up_at: datetime | None = field(default=None)

    def share(self, now: datetime) -> None:
        """Mark this referral as shared with a prospect.

        Args:
            now: current UTC datetime.
        """
        self.status = ReferralStatus.SHARED
        self.shared_at = now
        self.updated_at = now

    def sign_up(self, *, referred_patient_id: uuid.UUID, now: datetime) -> None:
        """Mark that the referred prospect has signed up (booked first appointment).

        Args:
            referred_patient_id: UUID of the referred patient who signed up.
            now: current UTC datetime.
        """
        self.status = ReferralStatus.SIGNED_UP
        self.referred_patient_id = referred_patient_id
        self.signed_up_at = now
        self.updated_at = now

    def convert(self, *, referred_patient_id: uuid.UUID, now: datetime) -> None:
        """Mark this referral as converted (appointment completed with value).

        Args:
            referred_patient_id: UUID of the newly registered patient.
            now: current UTC datetime.
        """
        self.status = ReferralStatus.CONVERTED
        self.referred_patient_id = referred_patient_id
        self.converted_at = now
        self.updated_at = now

    def expire(self, now: datetime) -> None:
        """Mark this referral as expired (cron job action).

        Only OPEN, SHARED, and SIGNED_UP referrals can expire.
        CONVERTED referrals are terminal — they cannot expire.
        """
        if self.status in (
            ReferralStatus.OPEN,
            ReferralStatus.SHARED,
            ReferralStatus.SIGNED_UP,
        ):
            self.status = ReferralStatus.EXPIRED
            self.updated_at = now
