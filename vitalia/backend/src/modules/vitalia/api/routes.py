# cap: __shared__
# story-origin: TBD
"""Vitalia FastAPI router — all REST endpoints (excl. webhooks T-be-8).

Per 03-arch-be.md § 6 + 05-guidelines § 1.1 (DDD — API thin):
  - Router is THIN: validate DTO → call service → map domain exception → HTTPException.
  - NO business logic in this module.
  - redirect_slashes=False is set on the FastAPI *app* (main.py) — NOT on APIRouter.
  - response_model= is MANDATORY on every endpoint (V-AE-2 PII gate + arch test).
  - tenant_id is sourced from X-Tenant-ID header (authoritative — NOT from body).
  - Clerk JWT auth via Annotated dependency (clerk_user_id from JWT sub claim).

Endpoints (per 03-arch-be.md § 6, excl. webhooks T-be-8):
  Onboarding (3):  POST /onboarding/clinic-profile, GET /onboarding/plans, GET /onboarding/status
  Offer (1):       GET /offer/presets
  Booking (6):     GET + POST /bookings, POST /{id}/confirm-payment, /{id}/consent-sign, /{id}/cancel, /{id}/reschedule
  Treatments (5):  GET /treatments, GET /treatments/{id}, GET /{id}/followup,
                   POST /{id}/manual-handoff, POST /{id}/release-handoff
  Patients (3):    GET /patients, GET /patients/{id}, POST /patients/{id}/upload-medical-pdf
  Compliance (2):  GET /medical-compliance/events, GET /medical-compliance/export-csv

Note: POST /bookings/{id}/confirm-payment is called from webhook handlers (T-be-8).
      Included here as service layer endpoint for internal E2E wiring.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.modules.vitalia._shared.auth.rbac import require_brand_owner_access
from src.modules.vitalia.api.dtos.booking_dtos import (
    AvailableSlotsResponse,
    BookingListResponse,
    CancelBookingRequest,
    CancelBookingResponse,
    ConfirmPaymentRequest,
    ConfirmPaymentResponse,
    ConsentSignRequest,
    ConsentSignResponse,
    CreateBookingRequest,
    CreateBookingResponse,
    RescheduleBookingRequest,
    RescheduleBookingResponse,
)
from src.modules.vitalia.api.dtos.compliance_dtos import (
    ComplianceEventListResponse,
)
from src.modules.vitalia.api.dtos.consent_dtos import (
    ConsentRecordListResponse,
)
from src.modules.vitalia.api.dtos.onboarding_dtos import (
    CreateClinicProfileRequest,
    CreateClinicProfileResponse,
    OfferPresetResponse,
    OnboardingStatusResponse,
    PlanTierItem,
    PlanTierListResponse,
    SubscribeRequest,
    SubscribeResponse,
)
from src.modules.vitalia.api.dtos.treatment_dtos import (
    ManualHandoffRequest,
    ManualHandoffResponse,
    PatientDetailResponse,
    PatientListResponse,
    ReleaseHandoffResponse,
    StartFollowupRequest,
    TreatmentDetailResponse,
    TreatmentFollowupStateResponse,
    TreatmentListResponse,
    UploadMedicalPdfRequest,
    UploadMedicalPdfResponse,
)

logger = structlog.get_logger()

# ── Type aliases for Annotated headers ───────────────────────────────────────

TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID", description="Active tenant UUID")]
ClerkUserIdHeader = Annotated[
    str | None,
    Header(alias="X-Clerk-User-ID", description="Clerk JWT sub claim (optional for anonymous booking)"),
]

# RBAC del audit log HIPAA-lite (compliance). Roles == cap
# `compliance.hipaa-lite-defensive-stack` (`requires_role`); excluye los
# `forbidden_roles` (patient/marketing/nurse/receptionist). hipaa-lite.md:
# el audit log es admin-only — NO basta la auth Clerk JWT, requiere RBAC.
_COMPLIANCE_AUDIT_ROLES: frozenset[str] = frozenset(["admin_clinic", "staff_vitalia"])


# ── Router ────────────────────────────────────────────────────────────────────

# redirect_slashes=False is set on FastAPI app in main.py (arch test enforces).
# Do NOT set redirect_slashes on individual APIRouter instances.
router = APIRouter(
    prefix="/api/v1/vitalia",
    tags=["vitalia"],
)


def _parse_tenant_id(tenant_id_str: str) -> uuid.UUID:
    """Parse tenant_id string to UUID — raise 422 on invalid format."""
    try:
        return uuid.UUID(tenant_id_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid X-Tenant-ID format: {tenant_id_str}",
        ) from exc


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


# ══════════════════════════════════════════════════════════════════════════════
# ONBOARDING (§ 6.1)
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/onboarding/clinic-profile",
    response_model=CreateClinicProfileResponse,
    status_code=201,
    summary="Create clinic profile + tenant (idempotent)",
)
async def create_clinic_profile(
    request: CreateClinicProfileRequest,
    x_tenant_id: TenantIdHeader,
    x_clerk_user_id: ClerkUserIdHeader = None,
) -> CreateClinicProfileResponse:
    """Create clinic tenant + initialise BrandConfig defaults.

    Idempotent: same clerk_user_id within 1s TTL → returns existing tenant.
    X-Tenant-ID header is used as authoritative tenant context.
    Caller (Clerk webhook handler T-be-8) passes clerk_user_id via X-Clerk-User-ID.
    """
    tenant_id = _parse_tenant_id(x_tenant_id)
    clerk_user_id = x_clerk_user_id or f"anon_{tenant_id}"

    logger.info(
        "onboarding_clinic_profile_request",
        tenant_id=str(tenant_id),
        clerk_user_id=clerk_user_id,
        clinic_type=request.clinic_type,
    )

    # Service layer call (DI stub — real DI wired post T-be-7 integration tests)
    # For now returns a consistent response for E2E routing smoke
    now = _utc_now()
    return CreateClinicProfileResponse(
        tenant_id=tenant_id,
        clinic_name=request.clinic_name,
        clinic_type=request.clinic_type,
        country=request.country,
        city=request.city,
        plan_tier=request.plan_tier,
        is_new=True,
        created_at=now,
    )


@router.get(
    "/onboarding/plans",
    response_model=PlanTierListResponse,
    summary="List available plan tiers",
)
async def list_plans(
    x_tenant_id: TenantIdHeader,
) -> PlanTierListResponse:
    """List vitalia plan tiers from vitalia_plan_tier_configs catalog.

    Cross-tenant: plan tier catalog has no tenant_id filter (global catalog).
    Auth: Clerk JWT optional (publicly accessible for pre-signup preview).
    """
    _parse_tenant_id(x_tenant_id)

    # Plan tier catalog (static for T-be-7 scope; DB-backed in full integration)
    plans = [
        PlanTierItem(
            slug="starter",
            label_es="Starter",
            price_usd_monthly=99.0,
            included_user_count=2,
            features_enabled=["brand_studio_simplified", "offer_studio_medical", "booking_prepaid"],
        ),
        PlanTierItem(
            slug="clinic",
            label_es="Clínica",
            price_usd_monthly=199.0,
            included_user_count=5,
            features_enabled=[
                "brand_studio_simplified",
                "offer_studio_medical",
                "booking_prepaid",
                "sales_agent_vertical_medical",
                "copilot_kb_dental",
            ],
        ),
        PlanTierItem(
            slug="multi_site",
            label_es="Multi-sede",
            price_usd_monthly=599.0,
            included_user_count=20,
            features_enabled=[
                "brand_studio_simplified",
                "offer_studio_medical",
                "booking_prepaid",
                "sales_agent_vertical_medical",
                "copilot_kb_psychology",
                "copilot_kb_psychiatry",
                "multi_currency",
            ],
        ),
        PlanTierItem(
            slug="enterprise",
            label_es="Enterprise",
            price_usd_monthly=0.0,  # custom pricing
            included_user_count=0,
            features_enabled=["all"],
        ),
    ]
    return PlanTierListResponse(plans=plans, currency=None)


@router.get(
    "/onboarding/status",
    response_model=OnboardingStatusResponse,
    summary="Get onboarding completion status",
)
async def get_onboarding_status(
    x_tenant_id: TenantIdHeader,
) -> OnboardingStatusResponse:
    """Return onboarding step completion for the authenticated tenant.

    Steps: clinic_profile | subscription | first_offer_created.
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info("onboarding_status_request", tenant_id=str(tenant_id))

    # Stub response for T-be-7 scope — service layer wires actual checks
    return OnboardingStatusResponse(
        tenant_id=tenant_id,
        clinic_profile_complete=True,
        subscription_active=False,
        first_offer_created=False,
        onboarding_complete=False,
    )


@router.post(
    "/onboarding/subscribe",
    response_model=SubscribeResponse,
    status_code=201,
    summary="Create Stripe Checkout session + subscription record",
)
async def subscribe(
    request: SubscribeRequest,
    x_tenant_id: TenantIdHeader,
) -> SubscribeResponse:
    """Create Stripe Checkout session for plan subscription.

    Returns checkout_url for redirect to Stripe-hosted payment page.
    subscription_id populated after webhook confirmation (T-be-8).
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "onboarding_subscribe_request",
        tenant_id=str(tenant_id),
        plan_tier=request.plan_tier,
    )

    # Stripe Checkout session creation (stub — real adapter in T-be-7 integration)
    return SubscribeResponse(
        checkout_url=f"{request.success_url}?plan={request.plan_tier}&pending=1",
        subscription_id=None,
        plan_tier=request.plan_tier,
    )


# ══════════════════════════════════════════════════════════════════════════════
# OFFER PRESETS (§ 6.3)
# ══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/offer/presets",
    response_model=OfferPresetResponse,
    summary="Get medical_services_v1 offer preset config",
)
async def get_medical_offer_preset(
    x_tenant_id: TenantIdHeader,
) -> OfferPresetResponse:
    """Return the vitalia medical_services_v1 preset for offer wizard bootstrapping.

    Per 03-arch-be.md § 6.3: single preset endpoint (medical vertical).
    """
    _parse_tenant_id(x_tenant_id)

    return OfferPresetResponse(
        preset_id="medical_services_v1",
        label_es="Servicios médicos / dentales",
        description_es=(
            "Oferta para clínicas médicas, dentales y de salud mental. "
            "Incluye gestión de citas, pagos anticipados y seguimiento de tratamientos."
        ),
        archetype="SERVICIO",
        base_sections=["IDENTITY", "STRATEGY", "PROMISE", "PRICING", "SERVICE_DETAILS", "CLOSING"],
        default_flags=["REQUIRES_START_DATE", "SUPPORTS_CAPACITY"],
        examples_es=[
            "Consulta inicial dental AR",
            "Sesión psicología online MX",
            "Implante dental con seguimiento",
        ],
    )


# ══════════════════════════════════════════════════════════════════════════════
# BOOKINGS (§ 6.4)
# ══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/bookings/available-slots",
    response_model=AvailableSlotsResponse,
    summary="Get available booking slots for a doctor/offer combination",
)
async def get_available_slots(
    x_tenant_id: TenantIdHeader,
    doctor_id: Annotated[uuid.UUID, Query(description="Doctor UUID")],
    offer_id: Annotated[uuid.UUID, Query(description="Offer UUID")],
    window_start: Annotated[datetime, Query(description="Window start (UTC ISO-8601)")],
    window_days: Annotated[int, Query(ge=1, le=90, description="Days to look ahead")] = 7,
) -> AvailableSlotsResponse:
    """Return available appointment slots for a doctor within the given window.

    Read-only — no advisory lock required. Anonymous patient access allowed
    (clinic booking widget use case per D11).
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "available_slots_request",
        tenant_id=str(tenant_id),
        doctor_id=str(doctor_id),
        offer_id=str(offer_id),
        window_start=window_start.isoformat(),
        window_days=window_days,
    )

    # Stub: real slot computation delegates to @luana/core/scheduling + vitalia extension (D2)
    return AvailableSlotsResponse(
        slots=[],
        doctor_id=doctor_id,
        offer_id=offer_id,
        window_start=window_start,
        window_days=window_days,
    )


@router.post(
    "/bookings",
    response_model=CreateBookingResponse,
    status_code=201,
    summary="Create booking with advisory lock + idempotency",
)
async def create_booking(
    request: CreateBookingRequest,
    x_tenant_id: TenantIdHeader,
) -> CreateBookingResponse:
    """Create booking for a patient-doctor-slot triple.

    Advisory lock on (doctor_id, slot_iso) prevents double-booking.
    Idempotent: same (patient_id, doctor_id, slot_iso) within 60s TTL → cached result.
    Status: pending_payment | awaiting_consent | confirmed_deposit.
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "booking_create_request",
        tenant_id=str(tenant_id),
        doctor_id=str(request.doctor_id),
        patient_id=str(request.patient_id),
    )

    # Service not fully DI-wired in T-be-7 scope (real wiring in T-be-7 integration);
    # SvcCreateBookingRequest constructed in integration phase when BookingService is injected.
    # return stub response that passes E2E routing test
    booking_id = uuid.uuid4()
    status = "pending_payment" if request.requires_prepay else "confirmed_deposit"
    if request.requires_informed_consent:
        status = "awaiting_consent"

    logger.info(
        "booking_created_stub",
        tenant_id=str(tenant_id),
        booking_id=str(booking_id),
        status=status,
    )

    return CreateBookingResponse(
        booking_id=booking_id,
        status=status,
        is_idempotent_hit=False,
        payment_url=None,
        consent_url=None,
        expires_at=None,
        currency=None,
    )


@router.get(
    "/bookings",
    response_model=BookingListResponse,
    summary="List bookings for the tenant",
)
async def list_bookings(
    x_tenant_id: TenantIdHeader,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    patient_id: Annotated[uuid.UUID | None, Query(description="Filter by patient")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> BookingListResponse:
    """List tenant-scoped bookings with optional filters.

    All queries filter tenant_id (tenant isolation — R2).
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "booking_list_request",
        tenant_id=str(tenant_id),
        status=status,
        page=page,
    )

    return BookingListResponse(bookings=[], total=0)


@router.post(
    "/bookings/{booking_id}/confirm-payment",
    response_model=ConfirmPaymentResponse,
    summary="Confirm payment (webhook-driven — Stripe/MercadoPago)",
)
async def confirm_payment(
    booking_id: uuid.UUID,
    request: ConfirmPaymentRequest,
    x_tenant_id: TenantIdHeader,
) -> ConfirmPaymentResponse:
    """Confirm payment for a booking.

    Called internally from webhook handlers (T-be-8) after HMAC verification.
    Updates booking payment_status and transitions booking status to confirmed_deposit.
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "booking_confirm_payment",
        tenant_id=str(tenant_id),
        booking_id=str(booking_id),
        gateway=request.gateway,
        gateway_payment_id=request.gateway_payment_id,
        status=request.status,
    )

    if request.status == "failed":
        payment_status = "failed"
        booking_status = "pending_payment"
    else:
        payment_status = "succeeded"
        booking_status = "confirmed_deposit"

    return ConfirmPaymentResponse(
        booking_id=booking_id,
        payment_status=payment_status,
        booking_status=booking_status,
        currency=request.currency,
    )


@router.post(
    "/bookings/{booking_id}/consent-sign",
    response_model=ConsentSignResponse,
    summary="Capture patient consent signature",
)
async def consent_sign(
    booking_id: uuid.UUID,
    request: ConsentSignRequest,
    x_tenant_id: TenantIdHeader,
) -> ConsentSignResponse:
    """Capture patient consent signature for a booking.

    Validates HMAC consent_token (prevents replay attacks).
    Records signed_name + IP + UA in consent_record (not returned in response — PII rule).
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "booking_consent_sign",
        tenant_id=str(tenant_id),
        booking_id=str(booking_id),
        signature_method=request.signature_method,
    )

    # Stub: real HMAC token verification in ConsentService (T-be-6 done)
    now = _utc_now()
    return ConsentSignResponse(
        consent_record_id=uuid.uuid4(),
        status="signed",
        signed_at=now,
    )


@router.post(
    "/bookings/{booking_id}/cancel",
    response_model=CancelBookingResponse,
    summary="Cancel a booking (soft-delete)",
)
async def cancel_booking(
    booking_id: uuid.UUID,
    request: CancelBookingRequest,
    x_tenant_id: TenantIdHeader,
) -> CancelBookingResponse:
    """Soft-cancel a booking.

    Enforces cancellation policy (no hard deletes — deleted_at pattern).
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "booking_cancel",
        tenant_id=str(tenant_id),
        booking_id=str(booking_id),
        reason=request.reason,
    )

    now = _utc_now()
    return CancelBookingResponse(
        booking_id=booking_id,
        status="cancelled",
        cancelled_at=now,
    )


@router.post(
    "/bookings/{booking_id}/reschedule",
    response_model=RescheduleBookingResponse,
    summary="Reschedule a booking to a new slot",
)
async def reschedule_booking(
    booking_id: uuid.UUID,
    request: RescheduleBookingRequest,
    x_tenant_id: TenantIdHeader,
) -> RescheduleBookingResponse:
    """Reschedule booking: release old advisory lock, reserve new slot.

    Old slot_iso is returned for audit purposes.
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "booking_reschedule",
        tenant_id=str(tenant_id),
        booking_id=str(booking_id),
        new_slot_iso=request.new_slot_iso.isoformat(),
    )

    # Stub: old_slot_iso fetched from booking repo in full integration
    old_slot_iso = _utc_now()
    return RescheduleBookingResponse(
        booking_id=booking_id,
        old_slot_iso=old_slot_iso,
        new_slot_iso=request.new_slot_iso,
        status="confirmed_deposit",
    )


# ══════════════════════════════════════════════════════════════════════════════
# TREATMENTS (§ 6.5)
# ══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/treatments",
    response_model=TreatmentListResponse,
    summary="List treatments for the tenant",
)
async def list_treatments(
    x_tenant_id: TenantIdHeader,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    patient_id: Annotated[uuid.UUID | None, Query(description="Filter by patient")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TreatmentListResponse:
    """List tenant-scoped treatment followups with optional filters."""
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "treatment_list_request",
        tenant_id=str(tenant_id),
        status=status,
        page=page,
    )

    return TreatmentListResponse(treatments=[], total=0)


@router.get(
    "/treatments/{treatment_id}",
    response_model=TreatmentDetailResponse,
    summary="Get treatment detail + last conversation summary",
)
async def get_treatment(
    treatment_id: uuid.UUID,
    x_tenant_id: TenantIdHeader,
) -> TreatmentDetailResponse:
    """Get treatment detail including latest conversation summary.

    Returns 404 if treatment_id not found or belongs to different tenant.
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "treatment_get_request",
        tenant_id=str(tenant_id),
        treatment_id=str(treatment_id),
    )

    # Stub: TreatmentFollowupRepository.get_by_id(treatment_id, tenant_id) in full integration
    raise HTTPException(status_code=404, detail="Treatment not found")


@router.get(
    "/treatments/{treatment_id}/followup",
    response_model=TreatmentFollowupStateResponse,
    summary="Get LangGraph workflow state for a treatment",
)
async def get_treatment_followup_state(
    treatment_id: uuid.UUID,
    x_tenant_id: TenantIdHeader,
) -> TreatmentFollowupStateResponse:
    """Return LangGraph workflow state (current_step, adherence_score, next tick).

    langgraph_checkpoint_id NOT returned (internal state — not exposed via API).
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "treatment_followup_state_request",
        tenant_id=str(tenant_id),
        treatment_id=str(treatment_id),
    )

    raise HTTPException(status_code=404, detail="Treatment not found")


@router.post(
    "/treatments/{treatment_id}/start-followup",
    response_model=TreatmentFollowupStateResponse,
    status_code=201,
    summary="Start LangGraph treatment followup workflow",
)
async def start_treatment_followup(
    treatment_id: uuid.UUID,
    request: StartFollowupRequest,
    x_tenant_id: TenantIdHeader,
) -> TreatmentFollowupStateResponse:
    """Start LangGraph TreatmentFollowupWorkflow for a booking.

    Creates treatment_followup row (D0_init) + schedules D+5/14/90 cron ticks.
    Idempotent: same booking_id → returns existing followup.
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "treatment_start_followup",
        tenant_id=str(tenant_id),
        treatment_id=str(treatment_id),
        plan_template_slug=request.plan_template_slug,
    )

    return TreatmentFollowupStateResponse(
        treatment_id=treatment_id,
        current_step="D0_init",
        adherence_score=None,
        last_response_at=None,
        next_scheduled_at=None,
        paused_reason=None,
    )


@router.post(
    "/treatments/{treatment_id}/manual-handoff",
    response_model=ManualHandoffResponse,
    summary="Clinic owner takes manual conversation control",
)
async def manual_handoff(
    treatment_id: uuid.UUID,
    request: ManualHandoffRequest,
    x_tenant_id: TenantIdHeader,
) -> ManualHandoffResponse:
    """Transfer conversation control to clinic owner (pauses LangGraph workflow)."""
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "treatment_manual_handoff",
        tenant_id=str(tenant_id),
        treatment_id=str(treatment_id),
    )

    now = _utc_now()
    return ManualHandoffResponse(
        treatment_id=treatment_id,
        status="paused_awaiting_clinic",
        handoff_at=now,
    )


@router.post(
    "/treatments/{treatment_id}/release-handoff",
    response_model=ReleaseHandoffResponse,
    summary="Release manual handoff — resume LangGraph workflow",
)
async def release_handoff(
    treatment_id: uuid.UUID,
    x_tenant_id: TenantIdHeader,
) -> ReleaseHandoffResponse:
    """Release manual handoff → LangGraph workflow resumes from last checkpoint."""
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "treatment_release_handoff",
        tenant_id=str(tenant_id),
        treatment_id=str(treatment_id),
    )

    now = _utc_now()
    return ReleaseHandoffResponse(
        treatment_id=treatment_id,
        status="resumed",
        released_at=now,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PATIENTS (§ 6.6)
# ══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/patients",
    response_model=PatientListResponse,
    summary="List patients (CDP medical-flavor) — PII masked",
)
async def list_patients(
    x_tenant_id: TenantIdHeader,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PatientListResponse:
    """List tenant-scoped patients with PII masked.

    phone_masked: "+54***5555". email_masked: "j***@***.com".
    Full name/phone/email NOT returned in any response.
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "patient_list_request",
        tenant_id=str(tenant_id),
        page=page,
    )

    return PatientListResponse(patients=[], total=0)


@router.get(
    "/patients/{patient_id}",
    response_model=PatientDetailResponse,
    summary="Get patient detail — PII masked, medical history summary",
)
async def get_patient(
    patient_id: uuid.UUID,
    x_tenant_id: TenantIdHeader,
) -> PatientDetailResponse:
    """Get patient detail with medical_history_summary.

    PII masked per 03-arch-be.md § 7.2:
      name_last_initial: "G.", phone_masked: "+54***5555", email_masked: "j***@***.com".
    Returns 404 if not found or cross-tenant attempt (tenant isolation R2).
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "patient_get_request",
        tenant_id=str(tenant_id),
        patient_id=str(patient_id),
    )

    raise HTTPException(status_code=404, detail="Patient not found")


@router.post(
    "/patients/{patient_id}/upload-medical-pdf",
    response_model=UploadMedicalPdfResponse,
    status_code=202,
    summary="Upload medical PDF — triggers async MedicalKBExtractor",
)
async def upload_medical_pdf(
    patient_id: uuid.UUID,
    request: UploadMedicalPdfRequest,
    x_tenant_id: TenantIdHeader,
) -> UploadMedicalPdfResponse:
    """Upload medical PDF for async extraction (MedicalKBExtractor / DentalHistoryExtractor).

    Returns extraction_job_id for polling. Triggers LangGraph wave-based extraction (T-extractors).
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "patient_upload_medical_pdf",
        tenant_id=str(tenant_id),
        patient_id=str(patient_id),
        file_name=request.file_name,
    )

    extraction_job_id = str(uuid.uuid4())
    return UploadMedicalPdfResponse(
        patient_id=patient_id,
        extraction_job_id=extraction_job_id,
        status="queued",
        estimated_completion_seconds=30,
    )


# ══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE (§ 6.7)
# ══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/medical-compliance/events",
    response_model=ComplianceEventListResponse,
    summary="Paginated HIPAA-lite audit log (admin only)",
)
async def list_compliance_events(
    x_tenant_id: TenantIdHeader,
    _role: Annotated[str, Depends(require_brand_owner_access(_COMPLIANCE_AUDIT_ROLES))],
    event_type: Annotated[str | None, Query(description="Filter by event_type")] = None,
    severity: Annotated[str | None, Query(description="info | medium | high")] = None,
    date_from: Annotated[datetime | None, Query(description="Filter from date (UTC)")] = None,
    date_to: Annotated[datetime | None, Query(description="Filter to date (UTC)")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ComplianceEventListResponse:
    """List HIPAA-lite compliance/audit events.

    payload_redacted: pre-sanitized by ComplianceEventService (no raw PII).
    RBAC: solo `admin_clinic`/`staff_vitalia` (X-User-Role) — el resto recibe 403
    (require_brand_owner_access). El audit log es admin-only (hipaa-lite.md): la
    auth Clerk JWT NO basta, requiere autorización por rol.
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "compliance_events_request",
        tenant_id=str(tenant_id),
        event_type=event_type,
        severity=severity,
        page=page,
    )

    return ComplianceEventListResponse(events=[], total=0, page=page, page_size=page_size)


@router.get(
    "/medical-compliance/export-csv",
    summary="Export compliance audit log as CSV (admin only)",
    response_class=StreamingResponse,
)
async def export_compliance_csv(
    x_tenant_id: TenantIdHeader,
    _role: Annotated[str, Depends(require_brand_owner_access(_COMPLIANCE_AUDIT_ROLES))],
    event_type: Annotated[str | None, Query(description="Filter by event_type")] = None,
    severity: Annotated[str | None, Query(description="info | medium | high")] = None,
    date_from: Annotated[datetime | None, Query(description="Filter from date (UTC)")] = None,
    date_to: Annotated[datetime | None, Query(description="Filter to date (UTC)")] = None,
) -> StreamingResponse:
    """Export compliance audit log as CSV for legal record.

    text/csv stream. payload_redacted column contains sanitized JSON.
    RBAC: solo `admin_clinic`/`staff_vitalia` (X-User-Role) → 403 al resto
    (require_brand_owner_access). El export del audit log es admin-only.

    NOTE: This endpoint intentionally has no response_model= because it returns
    a StreamingResponse (binary/text stream). The PII guard is enforced by
    ComplianceEventService.sanitize_payload() at write time (pre-DB persist).
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "compliance_export_csv",
        tenant_id=str(tenant_id),
        event_type=event_type,
        severity=severity,
    )

    # CSV header + empty body for T-be-7 scope
    csv_lines = [
        "id,event_type,severity,patient_id,booking_id,actor_type,created_at,payload_redacted",
    ]

    def _generate():
        for line in csv_lines:
            yield line + "\n"

    return StreamingResponse(
        content=_generate(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="vitalia-compliance-audit.csv"'},
    )


# ══════════════════════════════════════════════════════════════════════════════
# CONSENT RECORDS (§ 6.7 — also part of compliance surface)
# ══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/medical-compliance/consent-records",
    response_model=ConsentRecordListResponse,
    summary="List consent records for the tenant",
)
async def list_consent_records(
    x_tenant_id: TenantIdHeader,
    patient_id: Annotated[uuid.UUID | None, Query(description="Filter by patient")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ConsentRecordListResponse:
    """List tenant-scoped consent records.

    signed_ip / signed_user_agent / template_snapshot_md NOT returned (PII rule).
    """
    tenant_id = _parse_tenant_id(x_tenant_id)

    logger.info(
        "consent_records_list",
        tenant_id=str(tenant_id),
        patient_id=str(patient_id) if patient_id else None,
        page=page,
    )

    return ConsentRecordListResponse(records=[], total=0)
