# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""Marketing domain enums for vitalia brand.

Covers ad provider slugs, sync states, recommendation lifecycle,
referral lifecycle, bowtie funnel stages, and rejection reasons.

BowtieStage follows the 5-stage health-clinic bowtie funnel per spec:
  Atracción → Calificación → Reserva → Adopción → Expansión
"""

from __future__ import annotations

from enum import Enum


class ProviderSlug(str, Enum):
    """Supported advertising channel providers."""

    GOOGLE_ADS = "google_ads"
    META_ADS = "meta_ads"


class SyncStatus(str, Enum):
    """OAuth sync state for a channel connection."""

    OK = "ok"
    ERROR = "error"
    PENDING = "pending"


class RecommendationStatus(str, Enum):
    """Lifecycle states of a LucasRecommendation."""

    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ReferralStatus(str, Enum):
    """Lifecycle states of a patient referral.

    Full lifecycle per spec § 2.4:
      OPEN      — code generated, not yet shared
      SHARED    — referrer has shared the code with a prospect
      SIGNED_UP — prospect signed up (booked first appointment)
      CONVERTED — appointment completed with non-zero value (triggers value sync)
      EXPIRED   — referral period elapsed without conversion
    """

    OPEN = "open"
    SHARED = "shared"
    SIGNED_UP = "signed_up"
    CONVERTED = "converted"
    EXPIRED = "expired"


class BowtieStage(str, Enum):
    """Bowtie marketing funnel stages for health clinics.

    5-stage model per spec § 2.1 (Atracción/Calificación/Reserva/Adopción/Expansión):
      ATTRACTION    — top-of-funnel awareness channels (Google/Meta ads)
      QUALIFICATION — mid-funnel lead qualification (forms, calls)
      RESERVATION   — appointment booking conversion
      ADOPTION      — first visit completion (patient becomes active)
      EXPANSION     — patient loyalty + referrals + upsell
    """

    ATTRACTION = "attraction"
    QUALIFICATION = "qualification"
    RESERVATION = "reservation"
    ADOPTION = "adoption"
    EXPANSION = "expansion"


class RejectReason(str, Enum):
    """Reasons a user can reject a Lucas recommendation.

    5 values per spec § 2.2:
      NOT_PRIORITY  — not a current business priority
      ALREADY_DOING — clinic already running this action
      DATA_WRONG    — the supporting data looks incorrect
      TOO_RISKY     — perceived risk is too high
      OTHER         — any other reason (requires free-text in payload)
    """

    NOT_PRIORITY = "not_priority"
    ALREADY_DOING = "already_doing"
    DATA_WRONG = "data_wrong"
    TOO_RISKY = "too_risky"
    OTHER = "other"
