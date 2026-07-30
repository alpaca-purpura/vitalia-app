"""Tests for wizard onboarding API routes — T-onboarding-3.

Coverage:
  - test_create_draft_happy                     — 200 + StartDraftResponse shape
  - test_get_draft_happy                        — 200 + DraftResponse shape
  - test_get_draft_not_found                    — 404
  - test_extract_happy                          — 200 + ExtractResponse shape
  - test_confirm_slot_happy                     — 200 + ConfirmSlotResponse shape
  - test_simulate_happy                         — 200 + SimulateResponse shape, cache_hit flag
  - test_complete_happy                         — 200, tenant_activated=True
  - test_cross_tenant_returns_404               — 404 when wrong tenant
  - test_missing_tenant_header_returns_422      — 422 when X-Tenant-ID absent

DI override pattern: per runtime-quality-checklist.md §
  "Multi-tenant test fixture — header-based dispatch".
  Single override per factory, no parallel `app.dependency_overrides` global mutations.

PII: no PHI in test data — wizard config only (clinic name, vertical, location).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.modules.vitalia.copilot.api.routes.wizard_onboarding_routes import (
    get_complete_service,
    get_extract_service,
    get_onboarding_draft_service,
    get_simulate_service,
)
from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft
from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TENANT_A = uuid4()
TENANT_B = uuid4()  # "other" tenant — used for cross-tenant isolation tests
BASE_URL = "http://testserver"
ONBOARDING_PREFIX = "/api/v1/vitalia/onboarding"


# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(tz=timezone.utc)


def _make_wizard_slot(slot_id: str, *, value: Any = None, confirmed: bool = False) -> WizardSlot:
    """Build a WizardSlot for test data."""
    return WizardSlot(
        slot_id=slot_id,
        value=value,
        confidence=0.9 if value is not None else 0.0,
        confirmed_at=_utc_now() if confirmed else None,
        source="extracted",
    )


def _make_draft(tenant_id: UUID, *, completed: bool = False) -> OnboardingDraft:
    """Build a minimal OnboardingDraft entity for test assertions."""
    now = _utc_now()
    return OnboardingDraft(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=tenant_id,
        clinic_id=None,
        mode="libre",
        slots_required={
            "tenant.name": _make_wizard_slot("tenant.name"),
            "tenant.vertical": _make_wizard_slot("tenant.vertical"),
            "tenant.location": _make_wizard_slot("tenant.location"),
        },
        slots_optional={
            "brand.tone_default": _make_wizard_slot("brand.tone_default"),
        },
        bonus_extracted={},
        consent_voice_activation=False,
        created_at=now,
        updated_at=now,
        deleted_at=None,
        completed_at=now if completed else None,
    )


# ---------------------------------------------------------------------------
# Stub service factories
# (factory functions — zero params, closures capture test state)
# per runtime-quality-checklist.md § "Test fixture override — bare params son Pydantic field"
# ---------------------------------------------------------------------------


def _make_stub_draft_service(draft: OnboardingDraft, tenant_id: UUID) -> "object":
    """Build an OnboardingDraftService stub that serves `draft` for `tenant_id`."""
    from src.modules.vitalia.copilot.application.services.onboarding_draft_service import (
        OnboardingDraftService,
    )

    svc = MagicMock(spec=OnboardingDraftService)
    svc.create_draft = AsyncMock(return_value=draft)

    # get_draft: return draft only when both draft_id AND tenant_id match
    async def get_draft_dispatch(*, draft_id: UUID, tenant_id: UUID) -> Optional[OnboardingDraft]:
        if draft_id == draft.id and tenant_id == draft.tenant_id:
            return draft
        return None

    svc.get_draft = get_draft_dispatch

    # update_slot: returns draft with the new slot applied
    async def update_slot_stub(
        *, draft_id: UUID, tenant_id: UUID, slot_id: str, new_slot: WizardSlot
    ) -> OnboardingDraft:
        if tenant_id != draft.tenant_id:
            return None  # type: ignore[return-value]
        draft.update_slot(slot_id, new_slot)
        return draft

    svc.update_slot = update_slot_stub
    return svc


def _make_stub_extract_service(draft: OnboardingDraft) -> "object":
    """Build an ExtractTenantContextService stub that returns `draft`."""
    from src.modules.vitalia.copilot.application.services.extract_tenant_context_service import (
        ExtractTenantContextService,
    )

    svc = MagicMock(spec=ExtractTenantContextService)
    svc.extract = AsyncMock(return_value=draft)
    return svc


@dataclass
class _FakeSimulateResult:
    sample_text: str
    generated_at: str
    cache_hit: bool


def _make_stub_simulate_service(*, throttled: bool = False, cache_hit: bool = False) -> "object":
    """Build a SimulatePersonalityService stub."""
    from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
        SimulatePersonalityService,
        ThrottleExceededError,
    )

    svc = MagicMock(spec=SimulatePersonalityService)

    async def simulate_stub(**kwargs: Any) -> _FakeSimulateResult:
        if throttled:
            raise ThrottleExceededError("simulate_personality")
        return _FakeSimulateResult(
            sample_text="Hola, soy el asistente de tu clínica. ¿En qué puedo ayudarte?",
            generated_at=_utc_now().isoformat(),
            cache_hit=cache_hit,
        )

    svc.simulate = simulate_stub
    return svc


@dataclass
class _FakeCompleteResult:
    tenant_activated: bool
    redirect_url: str


def _make_stub_complete_service(*, found: bool = True) -> "object":
    """Build a CompleteOnboardingService stub."""
    from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
        CompleteOnboardingService,
        DraftNotFoundError,
    )

    svc = MagicMock(spec=CompleteOnboardingService)

    async def complete_stub(*, draft_id: UUID, tenant_id: UUID, user_id: UUID) -> _FakeCompleteResult:
        if not found:
            raise DraftNotFoundError(draft_id, tenant_id)
        return _FakeCompleteResult(tenant_activated=True, redirect_url="/inbox")

    svc.complete = complete_stub
    return svc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def draft_a() -> OnboardingDraft:
    """OnboardingDraft belonging to TENANT_A."""
    return _make_draft(TENANT_A)


@pytest.fixture()
def app_with_stubs(draft_a: OnboardingDraft):
    """
    FastAPI app with dependency_overrides wired to stub services.

    Uses header-based dispatch per runtime-quality-checklist.md:
      Single override per factory, dispatch based on X-Tenant-ID at runtime.
    """
    draft_svc = _make_stub_draft_service(draft_a, TENANT_A)
    extract_svc = _make_stub_extract_service(draft_a)
    simulate_svc = _make_stub_simulate_service(cache_hit=False)
    complete_svc = _make_stub_complete_service(found=True)

    # Override all four dependency factories
    app.dependency_overrides[get_onboarding_draft_service] = lambda: draft_svc
    app.dependency_overrides[get_extract_service] = lambda: extract_svc
    app.dependency_overrides[get_simulate_service] = lambda: simulate_svc
    app.dependency_overrides[get_complete_service] = lambda: complete_svc

    yield app

    # Teardown — remove overrides to isolate tests
    app.dependency_overrides.pop(get_onboarding_draft_service, None)
    app.dependency_overrides.pop(get_extract_service, None)
    app.dependency_overrides.pop(get_simulate_service, None)
    app.dependency_overrides.pop(get_complete_service, None)


@pytest.fixture()
async def client_a(app_with_stubs) -> AsyncClient:
    """Async test client with X-Tenant-ID header set to TENANT_A."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_stubs),
        base_url=BASE_URL,
        headers={"X-Tenant-ID": str(TENANT_A)},
    ) as ac:
        yield ac


@pytest.fixture()
async def client_no_header(app_with_stubs) -> AsyncClient:
    """Async test client without X-Tenant-ID header — used for 422 test."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_stubs),
        base_url=BASE_URL,
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_draft_happy(client_a: AsyncClient, draft_a: OnboardingDraft) -> None:
    """POST /drafts — 200 + StartDraftResponse body shape."""
    resp = await client_a.post(f"{ONBOARDING_PREFIX}/drafts", json={"mode": "libre"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # StartDraftResponse shape
    assert "draft_id" in data
    assert "tenant_id" in data
    assert "mode" in data
    assert "slots_required" in data
    assert "slots_optional" in data
    assert "created_at" in data
    # tenant isolation — response tenant_id matches header
    assert data["tenant_id"] == str(draft_a.tenant_id)


@pytest.mark.asyncio
async def test_create_draft_duplicate_returns_409(draft_a: OnboardingDraft) -> None:
    """POST /drafts — a draft already exists for tenant+user → 409, not 500 (HB-88).

    Regression: start_draft used to leak the repo's IntegrityError as a raw 500
    (uq_vitalia_onboarding_progress_tenant_user). The service now maps it to
    DraftAlreadyExistsError and the route to 409.
    """
    from src.modules.vitalia.copilot.application.services.onboarding_draft_service import (
        DraftAlreadyExistsError,
        OnboardingDraftService,
    )

    svc = MagicMock(spec=OnboardingDraftService)
    svc.create_draft = AsyncMock(side_effect=DraftAlreadyExistsError("dup"))
    app.dependency_overrides[get_onboarding_draft_service] = lambda: svc
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url=BASE_URL,
            headers={"X-Tenant-ID": str(TENANT_A)},
        ) as ac:
            resp = await ac.post(f"{ONBOARDING_PREFIX}/drafts", json={"mode": "libre"})
        assert resp.status_code == 409, resp.text
    finally:
        app.dependency_overrides.pop(get_onboarding_draft_service, None)


@pytest.mark.asyncio
async def test_get_draft_happy(client_a: AsyncClient, draft_a: OnboardingDraft) -> None:
    """GET /drafts/{draft_id} — 200 + DraftResponse shape."""
    resp = await client_a.get(f"{ONBOARDING_PREFIX}/drafts/{draft_a.id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "draft_id" in data
    assert "tenant_id" in data
    assert "mode" in data
    assert "slots_required" in data
    assert "consent_voice_activation" in data
    assert data["tenant_id"] == str(TENANT_A)


@pytest.mark.asyncio
async def test_get_draft_not_found(client_a: AsyncClient) -> None:
    """GET /drafts/{unknown_id} — 404 when draft not found."""
    unknown_id = uuid4()
    resp = await client_a.get(f"{ONBOARDING_PREFIX}/drafts/{unknown_id}")
    assert resp.status_code == 404, resp.text
    data = resp.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_extract_happy(client_a: AsyncClient, draft_a: OnboardingDraft) -> None:
    """POST /drafts/{draft_id}/extract — 200 + ExtractResponse shape."""
    resp = await client_a.post(
        f"{ONBOARDING_PREFIX}/drafts/{draft_a.id}/extract",
        json={"url": "https://clinica-ejemplo.com", "text_content": None},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "draft_id" in data
    assert "slots_required" in data
    assert "slots_optional" in data
    assert "slots_updated" in data


@pytest.mark.asyncio
async def test_confirm_slot_happy(client_a: AsyncClient, draft_a: OnboardingDraft) -> None:
    """POST /drafts/{draft_id}/slots/{slot_id}/confirm — 200 + ConfirmSlotResponse shape."""
    resp = await client_a.post(
        f"{ONBOARDING_PREFIX}/drafts/{draft_a.id}/slots/tenant.name/confirm",
        json={"value": "Clínica San Martín", "source": "user_text"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["slot_id"] == "tenant.name"
    assert data["value"] == "Clínica San Martín"
    assert "confirmed_at" in data
    assert "all_required_confirmed" in data


@pytest.mark.asyncio
async def test_simulate_happy(client_a: AsyncClient, draft_a: OnboardingDraft) -> None:
    """POST /drafts/{draft_id}/simulate — 200 + SimulateResponse shape, cache_hit=False."""
    resp = await client_a.post(
        f"{ONBOARDING_PREFIX}/drafts/{draft_a.id}/simulate",
        json={"scenario": "primera_respuesta"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "sample_text" in data
    assert "cache_hit" in data
    assert "scenario" in data
    assert "generated_at" in data
    assert data["cache_hit"] is False  # stub returns fresh, not cached


@pytest.mark.asyncio
async def test_complete_happy(client_a: AsyncClient, draft_a: OnboardingDraft) -> None:
    """POST /drafts/{draft_id}/complete — 200, tenant_activated=True."""
    resp = await client_a.post(
        f"{ONBOARDING_PREFIX}/drafts/{draft_a.id}/complete",
        json={},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["tenant_activated"] is True
    assert "redirect_url" in data


@pytest.mark.asyncio
async def test_cross_tenant_returns_404(draft_a: OnboardingDraft, app_with_stubs) -> None:
    """GET /drafts/{draft_id} with wrong tenant header → 404 (not 403, not 200).

    Verifies tenant isolation: a draft owned by TENANT_A is not accessible by TENANT_B.
    Rule: repo returns None for cross-tenant request → API maps to 404.
    See runtime-quality-checklist.md § "Tenant isolation — 404 vs 403".
    """
    async with AsyncClient(
        transport=ASGITransport(app=app_with_stubs),
        base_url=BASE_URL,
        headers={"X-Tenant-ID": str(TENANT_B)},  # TENANT_B — not the owner
    ) as client_b:
        resp = await client_b.get(f"{ONBOARDING_PREFIX}/drafts/{draft_a.id}")
    assert resp.status_code == 404, (
        f"Expected 404 for cross-tenant request, got {resp.status_code}. "
        f"Tenant isolation may be broken. Response: {resp.text}"
    )


@pytest.mark.asyncio
async def test_missing_tenant_header_returns_422(client_no_header: AsyncClient, draft_a: OnboardingDraft) -> None:
    """GET /drafts/{draft_id} without X-Tenant-ID → 422 FastAPI validation error."""
    resp = await client_no_header.get(f"{ONBOARDING_PREFIX}/drafts/{draft_a.id}")
    assert resp.status_code == 422, resp.text
    data = resp.json()
    # FastAPI returns structured validation errors
    assert "detail" in data
