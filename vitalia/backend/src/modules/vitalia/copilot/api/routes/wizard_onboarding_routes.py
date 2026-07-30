# cap: copilot.valeria-wizard-onboarding-agentic
# story-origin: TBD
"""Valeria wizard onboarding API routes.

API layer — thin: validate headers → resolve service → call service → map exceptions → response.
No business logic here. Business logic lives in application/services/.

Endpoints:
  POST   /api/v1/vitalia/onboarding/drafts                            — Start new onboarding session
  GET    /api/v1/vitalia/onboarding/drafts/{draft_id}                 — Get draft state
  POST   /api/v1/vitalia/onboarding/drafts/{draft_id}/extract         — Extract from URL/document
  POST   /api/v1/vitalia/onboarding/drafts/{draft_id}/slots/{slot_id}/confirm  — Confirm a slot
  POST   /api/v1/vitalia/onboarding/drafts/{draft_id}/simulate        — Simulate personality
  POST   /api/v1/vitalia/onboarding/drafts/{draft_id}/complete        — Complete onboarding
  GET    /api/v1/vitalia/onboarding/drafts/{draft_id}/stream          — SSE stream (no response_model)

response_model= is MANDATORY on every endpoint except SSE stream (per arch fitness V-AE-2).
redirect_slashes=False is set on the FastAPI *app* in main.py, NOT here.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated, Any, AsyncGenerator
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session, get_async_session_committing
from src.modules.vitalia.copilot.api.dtos.wizard_dtos import (
    CompleteRequest,
    CompleteResponse,
    ConfirmSlotRequest,
    ConfirmSlotResponse,
    DraftResponse,
    ExtractRequest,
    ExtractResponse,
    SimulateRequest,
    SimulateResponse,
    StartDraftRequest,
    StartDraftResponse,
    WizardSlotDTO,
)
from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
    CompleteOnboardingService,
    DraftNotFoundError,
)
from src.modules.vitalia.copilot.application.services.extract_tenant_context_service import (
    ExtractTenantContextService,
)
from src.modules.vitalia.copilot.application.services.onboarding_draft_service import (
    DraftAlreadyExistsError,
    OnboardingDraftService,
)
from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
    SimulatePersonalityService,
    ThrottleExceededError,
)
from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot
from src.modules.vitalia.copilot.infrastructure.repositories.brand_studio_draft_repository import (
    SqlAlchemyBrandStudioDraftRepository,
)
from src.modules.vitalia.copilot.infrastructure.repositories.onboarding_progress_repository import (
    SqlAlchemyOnboardingProgressRepository,
)

logger = structlog.get_logger()

router = APIRouter(tags=["wizard-onboarding"])

# Header type aliases
TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID")]


# ---------------------------------------------------------------------------
# Dependency factories — real SQLA 2.0 repositories replacing AsyncMock stubs
# Per runtime-quality-checklist.md: factory functions (closures), NOT type aliases
# ---------------------------------------------------------------------------


async def get_onboarding_progress_repo(
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> SqlAlchemyOnboardingProgressRepository:
    """Provide SqlAlchemyOnboardingProgressRepository with the committing session.

    The repo's save() flushes-only ("Caller commits"); the wizard handlers
    (start_draft/confirm_slot/extract/complete) route their draft writes through
    here. Without a committing unit-of-work the draft is flushed-then-rolled-back
    at session close → HTTP 200 with no row (HB-80, the HB-50 silent-killer class).
    """
    return SqlAlchemyOnboardingProgressRepository(session=session)


async def get_brand_studio_draft_repo(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> SqlAlchemyBrandStudioDraftRepository:
    """Provide SqlAlchemyBrandStudioDraftRepository with live DB session."""
    return SqlAlchemyBrandStudioDraftRepository(session=session)


async def get_onboarding_draft_service(
    progress_repo: Annotated[
        SqlAlchemyOnboardingProgressRepository,
        Depends(get_onboarding_progress_repo),
    ],
) -> OnboardingDraftService:
    """Provide OnboardingDraftService wired to real SQLA 2.0 progress repository.

    progress_repo implements the save() + get_by_id() bridge methods
    required by OnboardingDraftService's draft_repo interface.
    """
    return OnboardingDraftService(draft_repo=progress_repo)


async def get_extract_service(
    progress_repo: Annotated[
        SqlAlchemyOnboardingProgressRepository,
        Depends(get_onboarding_progress_repo),
    ],
) -> ExtractTenantContextService:
    """Provide ExtractTenantContextService with real draft_repo + stub adapters (Slice 1).

    website_scraper + document_extractor remain stubbed until T-onboarding-2.
    """
    from unittest.mock import AsyncMock

    website_scraper = AsyncMock()
    website_scraper.extract = AsyncMock(return_value={})
    document_extractor = AsyncMock()
    document_extractor.extract = AsyncMock(return_value={})
    return ExtractTenantContextService(
        draft_repo=progress_repo,
        website_scraper=website_scraper,
        document_extractor=document_extractor,
    )


async def get_simulate_service() -> SimulatePersonalityService:
    """Provide SimulatePersonalityService with stub adapters (Slice 1 scaffold).

    personality_adapter + cache + rate_limiter remain stubbed until T-onboarding-2.
    No DB dependency — stub adapters only.
    """
    from unittest.mock import AsyncMock

    personality_adapter = AsyncMock()
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    rate_limiter = AsyncMock()
    rate_limiter.check = AsyncMock(return_value=True)
    return SimulatePersonalityService(
        personality_adapter=personality_adapter,
        cache=cache,
        rate_limiter=rate_limiter,
    )


async def get_complete_service(
    progress_repo: Annotated[
        SqlAlchemyOnboardingProgressRepository,
        Depends(get_onboarding_progress_repo),
    ],
) -> CompleteOnboardingService:
    """Provide CompleteOnboardingService with real draft_repo + stub ports (Slice 1).

    personality_adapter + brand_studio_port + tenant_port + event_bus remain
    stubbed until T-onboarding-3 (complete onboarding wire-up).
    """
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4

    personality_adapter = AsyncMock()
    personality_adapter.compile_full = AsyncMock(return_value=MagicMock(id=uuid4()))
    brand_studio_port = AsyncMock()
    tenant_port = AsyncMock()
    tenant_port.mark_onboarded = AsyncMock()
    audit_log_repo = AsyncMock()
    audit_log_repo.write = AsyncMock()
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()
    return CompleteOnboardingService(
        draft_repo=progress_repo,
        personality_adapter=personality_adapter,
        brand_studio_port=brand_studio_port,
        tenant_port=tenant_port,
        audit_log_repo=audit_log_repo,
        event_bus=event_bus,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _draft_to_start_response(draft: "object") -> StartDraftResponse:
    """Map OnboardingDraft entity to StartDraftResponse DTO."""
    return StartDraftResponse(
        draft_id=draft.id,
        tenant_id=draft.tenant_id,
        mode=draft.mode,
        slots_required={
            k: WizardSlotDTO(
                slot_id=v.slot_id,
                value=v.value,
                confidence=v.confidence,
                confirmed_at=v.confirmed_at,
                source=v.source,
            )
            for k, v in draft.slots_required.items()
        },
        slots_optional={
            k: WizardSlotDTO(
                slot_id=v.slot_id,
                value=v.value,
                confidence=v.confidence,
                confirmed_at=v.confirmed_at,
                source=v.source,
            )
            for k, v in draft.slots_optional.items()
        },
        created_at=draft.created_at,
    )


def _draft_to_full_response(draft: "object") -> DraftResponse:
    """Map OnboardingDraft entity to DraftResponse DTO."""
    return DraftResponse(
        draft_id=draft.id,
        tenant_id=draft.tenant_id,
        user_id=draft.user_id,
        clinic_id=draft.clinic_id,
        mode=draft.mode,
        slots_required={
            k: WizardSlotDTO(
                slot_id=v.slot_id,
                value=v.value,
                confidence=v.confidence,
                confirmed_at=v.confirmed_at,
                source=v.source,
            )
            for k, v in draft.slots_required.items()
        },
        slots_optional={
            k: WizardSlotDTO(
                slot_id=v.slot_id,
                value=v.value,
                confidence=v.confidence,
                confirmed_at=v.confirmed_at,
                source=v.source,
            )
            for k, v in draft.slots_optional.items()
        },
        consent_voice_activation=draft.consent_voice_activation,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
        completed_at=draft.completed_at,
    )


def _count_filled_slots(draft: "object") -> int:
    """Count slots that have a non-None value."""
    count = 0
    for slot in draft.slots_required.values():
        if slot.value is not None:
            count += 1
    for slot in draft.slots_optional.values():
        if slot.value is not None:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/drafts", response_model=StartDraftResponse)
async def start_draft(
    request: StartDraftRequest,
    x_tenant_id: TenantIdHeader,
    draft_svc: Annotated[OnboardingDraftService, Depends(get_onboarding_draft_service)],
) -> StartDraftResponse:
    """Start a new Valeria wizard onboarding session.

    Creates a new OnboardingDraft with the default required slot set
    (tenant.name, tenant.vertical, tenant.location) and optional slots.

    Args:
        request: StartDraftRequest with mode and optional clinic_id.
        x_tenant_id: Tenant isolation header.
        draft_svc: Injected OnboardingDraftService.

    Returns:
        StartDraftResponse with draft_id, mode, and initial slot state.

    Raises:
        409: A draft already exists for this tenant+user (HB-88).
        422: Missing X-Tenant-ID header.
    """
    tenant_id = UUID(x_tenant_id)
    clinic_id = request.clinic_id

    try:
        draft = await draft_svc.create_draft(
            tenant_id=tenant_id,
            user_id=tenant_id,  # Slice 1: use tenant_id as user_id stub
            mode=request.mode,
            clinic_id=clinic_id,
        )
    except DraftAlreadyExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un borrador de onboarding para este usuario.",
        ) from exc
    logger.info("wizard_draft_started", draft_id=str(draft.id), tenant_id=x_tenant_id)
    return _draft_to_start_response(draft)


@router.get("/drafts/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: UUID,
    x_tenant_id: TenantIdHeader,
    draft_svc: Annotated[OnboardingDraftService, Depends(get_onboarding_draft_service)],
) -> DraftResponse:
    """Retrieve the current state of an onboarding draft.

    Args:
        draft_id: OnboardingDraft UUID.
        x_tenant_id: Tenant isolation header.
        draft_svc: Injected OnboardingDraftService.

    Returns:
        DraftResponse with all slots and metadata.

    Raises:
        404: Draft not found for tenant.
    """
    tenant_id = UUID(x_tenant_id)
    draft = await draft_svc.get_draft(draft_id=draft_id, tenant_id=tenant_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Borrador de onboarding no encontrado.")
    return _draft_to_full_response(draft)


@router.post("/drafts/{draft_id}/extract", response_model=ExtractResponse)
async def extract_tenant_context(
    draft_id: UUID,
    request: ExtractRequest,
    x_tenant_id: TenantIdHeader,
    extract_svc: Annotated[ExtractTenantContextService, Depends(get_extract_service)],
) -> ExtractResponse:
    """Extract tenant context from a website URL or document text.

    Args:
        draft_id: OnboardingDraft to update with extracted context.
        request: ExtractRequest with optional url and/or text_content.
        x_tenant_id: Tenant isolation header.
        extract_svc: Injected ExtractTenantContextService.

    Returns:
        ExtractResponse with updated slots and count of updated slots.

    Raises:
        404: Draft not found.
    """
    tenant_id = UUID(x_tenant_id)
    draft = await extract_svc.extract(
        draft_id=draft_id,
        tenant_id=tenant_id,
        url=request.url,
        text_content=request.text_content,
    )
    filled = _count_filled_slots(draft)
    return ExtractResponse(
        draft_id=draft.id,
        slots_required={
            k: WizardSlotDTO(
                slot_id=v.slot_id,
                value=v.value,
                confidence=v.confidence,
                confirmed_at=v.confirmed_at,
                source=v.source,
            )
            for k, v in draft.slots_required.items()
        },
        slots_optional={
            k: WizardSlotDTO(
                slot_id=v.slot_id,
                value=v.value,
                confidence=v.confidence,
                confirmed_at=v.confirmed_at,
                source=v.source,
            )
            for k, v in draft.slots_optional.items()
        },
        slots_updated=filled,
    )


@router.post(
    "/drafts/{draft_id}/slots/{slot_id}/confirm",
    response_model=ConfirmSlotResponse,
)
async def confirm_slot(
    draft_id: UUID,
    slot_id: str,
    request: ConfirmSlotRequest,
    x_tenant_id: TenantIdHeader,
    draft_svc: Annotated[OnboardingDraftService, Depends(get_onboarding_draft_service)],
) -> ConfirmSlotResponse:
    """Confirm a specific wizard slot with user-provided value.

    Creates a new confirmed WizardSlot (confirmed_at = UTC now) and
    persists it into the draft.

    Args:
        draft_id: OnboardingDraft to update.
        slot_id: Dot-notation slot identifier to confirm.
        request: ConfirmSlotRequest with confirmed value and source.
        x_tenant_id: Tenant isolation header.
        draft_svc: Injected OnboardingDraftService.

    Returns:
        ConfirmSlotResponse with confirmed slot details.

    Raises:
        404: Draft not found.
    """
    tenant_id = UUID(x_tenant_id)
    now = datetime.now(tz=timezone.utc)

    confirmed_slot = WizardSlot(
        slot_id=slot_id,
        value=request.value,
        confidence=1.0,
        confirmed_at=now,
        source=request.source,
    )

    draft = await draft_svc.update_slot(
        draft_id=draft_id,
        tenant_id=tenant_id,
        slot_id=slot_id,
        new_slot=confirmed_slot,
    )

    # Check if all required slots are confirmed
    all_confirmed = all(s.confirmed_at is not None for s in draft.slots_required.values())

    return ConfirmSlotResponse(
        draft_id=draft.id,
        slot_id=slot_id,
        confirmed_at=now,
        value=request.value,
        all_required_confirmed=all_confirmed,
    )


@router.post("/drafts/{draft_id}/simulate", response_model=SimulateResponse)
async def simulate_personality(
    draft_id: UUID,
    request: SimulateRequest,
    x_tenant_id: TenantIdHeader,
    draft_svc: Annotated[OnboardingDraftService, Depends(get_onboarding_draft_service)],
    simulate_svc: Annotated[SimulatePersonalityService, Depends(get_simulate_service)],
) -> SimulateResponse:
    """Generate a personality simulation sample for the current draft state.

    Retrieves confirmed slots from the draft, then calls the personality
    simulation service with the partial profile. Applies cache (10min) and
    rate limiting (5/min/tenant).

    Args:
        draft_id: OnboardingDraft to simulate from.
        request: SimulateRequest with scenario.
        x_tenant_id: Tenant isolation header.
        draft_svc: Injected OnboardingDraftService.
        simulate_svc: Injected SimulatePersonalityService.

    Returns:
        SimulateResponse with sample_text and cache_hit flag.

    Raises:
        404: Draft not found.
        429: Rate limit exceeded (5/min/tenant).
    """
    tenant_id = UUID(x_tenant_id)
    draft = await draft_svc.get_draft(draft_id=draft_id, tenant_id=tenant_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Borrador de onboarding no encontrado.")

    # Build profile partial from all confirmed slots
    profile_partial: dict[str, Any] = {slot_id: slot.value for slot_id, slot in draft.all_confirmed_slots().items()}

    try:
        result = await simulate_svc.simulate(
            profile_partial=profile_partial,
            scenario=request.scenario,
            tenant_id=tenant_id,
        )
    except ThrottleExceededError as exc:
        raise HTTPException(
            status_code=429,
            detail="Límite de simulaciones alcanzado. Intenta nuevamente en 1 minuto.",
        ) from exc

    return SimulateResponse(
        sample_text=result.sample_text,
        scenario=request.scenario,
        generated_at=result.generated_at,
        cache_hit=result.cache_hit,
    )


@router.post("/drafts/{draft_id}/complete", response_model=CompleteResponse)
async def complete_onboarding(
    draft_id: UUID,
    request: CompleteRequest,
    x_tenant_id: TenantIdHeader,
    complete_svc: Annotated[CompleteOnboardingService, Depends(get_complete_service)],
) -> CompleteResponse:
    """Complete the Valeria wizard onboarding session.

    Finalizes onboarding: compiles personality profile, commits brand,
    marks tenant as active, writes audit log, and emits TenantOnboardedEvent.

    Args:
        draft_id: OnboardingDraft to complete.
        request: CompleteRequest (currently empty — confirmation trigger only).
        x_tenant_id: Tenant isolation header.
        complete_svc: Injected CompleteOnboardingService.

    Returns:
        CompleteResponse with tenant_activated=True and redirect_url.

    Raises:
        404: Draft not found.
    """
    tenant_id = UUID(x_tenant_id)

    try:
        result = await complete_svc.complete(
            draft_id=draft_id,
            tenant_id=tenant_id,
            user_id=tenant_id,  # Slice 1: stub user_id = tenant_id
        )
    except DraftNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Borrador de onboarding no encontrado.",
        ) from exc

    return CompleteResponse(
        tenant_activated=result.tenant_activated,
        redirect_url=result.redirect_url,
    )


# ---------------------------------------------------------------------------
# SSE stream — NO response_model (StreamingResponse, not JSON)
# ---------------------------------------------------------------------------


async def _onboarding_event_generator(
    draft_id: UUID,
    tenant_id: UUID,
) -> AsyncGenerator[str, None]:
    """Yield SSE events for wizard onboarding state changes."""
    # Slice 1: stub events — real implementation in T-ag-workflows-1
    yield f"data: {json.dumps({'event': 'connected', 'draft_id': str(draft_id)})}\n\n"
    yield f"data: {json.dumps({'event': 'waiting', 'message': 'Esperando actividad del wizard...'})}\n\n"


@router.get("/drafts/{draft_id}/stream")
async def stream_onboarding_events(
    draft_id: UUID,
    x_tenant_id: TenantIdHeader,
) -> StreamingResponse:
    """Stream wizard onboarding events via Server-Sent Events (SSE).

    No response_model — returns StreamingResponse (SSE protocol).
    This is the only endpoint in this router without response_model.

    Args:
        draft_id: OnboardingDraft to stream events for.
        x_tenant_id: Tenant isolation header.

    Returns:
        StreamingResponse with text/event-stream content type.
    """
    tenant_id = UUID(x_tenant_id)
    return StreamingResponse(
        _onboarding_event_generator(draft_id, tenant_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
