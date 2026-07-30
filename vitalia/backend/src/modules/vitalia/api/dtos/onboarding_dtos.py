# cap: onboarding.clinic-onboarding-3step
# story-origin: TBD
"""Onboarding DTOs — Pydantic v2 request/response models.

Per 03-arch-be.md § 6.1 + § 7.1 + Tessl pii-sanitisation:
  - Every response DTO is the response_model= used in routes (PII allowlist).
  - No raw phone/email exposed in responses.
  - Timestamps stored UTC; returned as ISO-8601 datetime.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Request DTOs ──────────────────────────────────────────────────────────────


class CreateClinicProfileRequest(BaseModel):
    """POST /onboarding/clinic-profile — create clinic tenant + brand config defaults.

    Creates tenant record in luana_core_iam + initialises BrandConfig YAML defaults
    (vitalia/config/brand.yaml SSoT). Idempotent: same clerk_user_id within 1s TTL
    returns existing tenant (is_new=False).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    clinic_name: str = Field(min_length=2, max_length=255)
    clinic_type: str = Field(
        description="dental | psychology | psychiatry | wellness",
        pattern=r"^(dental|psychology|psychiatry|wellness)$",
    )
    country: str = Field(
        description="ISO 3166-1 alpha-2 (AR, CL, MX, PE, CO)",
        min_length=2,
        max_length=2,
    )
    city: str = Field(min_length=1, max_length=255)
    plan_tier: str = Field(
        description="starter | clinic | multi_site | enterprise",
        pattern=r"^(starter|clinic|multi_site|enterprise)$",
    )


class SubscribeRequest(BaseModel):
    """POST /onboarding/subscribe — Stripe Checkout session creation.

    Creates subscription record and returns Stripe-hosted checkout URL.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    plan_tier: str = Field(
        pattern=r"^(starter|clinic|multi_site|enterprise)$",
    )
    success_url: str = Field(description="Redirect URL after successful payment")
    cancel_url: str = Field(description="Redirect URL on payment cancel")


# ── Response DTOs ─────────────────────────────────────────────────────────────


class CreateClinicProfileResponse(BaseModel):
    """Response for POST /onboarding/clinic-profile.

    PII allowlist: no owner_email exposed (stored but not returned per Tessl rule).
    """

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    clinic_name: str
    clinic_type: str
    country: str
    city: str
    plan_tier: str
    is_new: bool = Field(description="False if idempotent hit (existing tenant within TTL)")
    created_at: datetime


class PlanTierItem(BaseModel):
    """Single plan tier entry."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    label_es: str
    price_usd_monthly: float
    included_user_count: int
    features_enabled: list[str]


class PlanTierListResponse(BaseModel):
    """Response for GET /onboarding/plans."""

    model_config = ConfigDict(from_attributes=True)

    plans: list[PlanTierItem]
    currency: str | None = None  # ISO 4217 — from tenant locale, not hardcoded


class OnboardingStatusResponse(BaseModel):
    """Response for GET /onboarding/status — step progress check."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    clinic_profile_complete: bool
    subscription_active: bool
    first_offer_created: bool
    onboarding_complete: bool


class SubscribeResponse(BaseModel):
    """Response for POST /onboarding/subscribe."""

    model_config = ConfigDict(from_attributes=True)

    checkout_url: str
    subscription_id: str | None = None
    plan_tier: str


class OfferPresetResponse(BaseModel):
    """Response for GET /offer/presets — medical_services_v1 preset config."""

    model_config = ConfigDict(from_attributes=True)

    preset_id: str
    label_es: str
    description_es: str
    archetype: str
    base_sections: list[str]
    default_flags: list[str]
    examples_es: list[str]
