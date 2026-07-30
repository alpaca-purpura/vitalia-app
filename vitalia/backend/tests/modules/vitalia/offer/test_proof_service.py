# cap: lisa.servicios
"""RED-first unit tests for ProofService (T-2 § 6).

Two surfaces:
  - Case (PHI · before/after photo) — consent gate RN-33 + HIPAA-lite audit_log
    SYNC write BEFORE the case is considered persisted (never fire-forget). A
    Case with consent_signed=False is rejected and writes NOTHING (no audit row,
    no case row). Dual-scoped tenant_id + clinic_id.
  - Testimonial (NOT PHI) — plain tenant-scoped CRUD, no consent, no audit.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from src.modules.vitalia.offer.application.services.proof_service import ProofService
from src.modules.vitalia.offer.domain.proof import Case, Testimonial
from src.modules.vitalia.offer.infrastructure.repositories.case_repository import ConsentNotSignedError

TENANT = UUID("11111111-1111-1111-1111-111111111111")
CLINIC = UUID("33333333-3333-3333-3333-333333333333")
OFFER = UUID("44444444-4444-4444-4444-444444444444")
USER = UUID("66666666-6666-6666-6666-666666666666")


class _FakeCaseRepo:
    def __init__(self) -> None:
        self.rows: list[Case] = []

    async def create(self, case: Case, *, clinic_id: UUID) -> Case:
        if not case.consent_signed:
            raise ConsentNotSignedError()
        self.rows.append(case)
        return case

    async def list_by_offer(self, offer_id, *, tenant_id, clinic_id):
        return [c for c in self.rows if c.offer_id == offer_id and c.tenant_id == tenant_id]

    async def soft_delete(self, entity_id, *, tenant_id, clinic_id) -> None:
        self.rows = [c for c in self.rows if c.id != entity_id]


class _FakeTestimonialRepo:
    def __init__(self) -> None:
        self.rows: list[Testimonial] = []

    async def create(self, t: Testimonial) -> Testimonial:
        self.rows.append(t)
        return t

    async def list_by_offer(self, offer_id, *, tenant_id):
        return [t for t in self.rows if t.offer_id == offer_id and t.tenant_id == tenant_id]

    async def soft_delete(self, entity_id, *, tenant_id) -> None:
        self.rows = [t for t in self.rows if t.id != entity_id]


class _FakeAudit:
    def __init__(self) -> None:
        self.entries: list[object] = []

    async def write(self, entry) -> None:
        self.entries.append(entry)


def _svc() -> tuple[ProofService, _FakeCaseRepo, _FakeTestimonialRepo, _FakeAudit]:
    case_repo = _FakeCaseRepo()
    test_repo = _FakeTestimonialRepo()
    audit = _FakeAudit()
    svc = ProofService(case_repo=case_repo, testimonial_repo=test_repo, audit=audit)
    return svc, case_repo, test_repo, audit


# ---- Case (PHI) ----------------------------------------------------------


@pytest.mark.asyncio
async def test_case_with_consent_persists_and_writes_audit():
    svc, case_repo, _, audit = _svc()
    case = await svc.create_case(
        tenant_id=TENANT,
        clinic_id=CLINIC,
        user_id=USER,
        offer_id=OFFER,
        before_asset_url="https://assets/before.jpg",
        after_asset_url="https://assets/after.jpg",
        consent_signed=True,
        consent_ref="consent-001",
    )
    assert case.consent_signed is True
    assert len(case_repo.rows) == 1
    assert len(audit.entries) == 1  # sync audit row written


@pytest.mark.asyncio
async def test_case_without_consent_blocked_and_writes_nothing():
    svc, case_repo, _, audit = _svc()
    with pytest.raises(ConsentNotSignedError):
        await svc.create_case(
            tenant_id=TENANT,
            clinic_id=CLINIC,
            user_id=USER,
            offer_id=OFFER,
            before_asset_url="https://assets/before.jpg",
            after_asset_url="https://assets/after.jpg",
            consent_signed=False,
        )
    assert len(case_repo.rows) == 0  # nothing persisted
    assert len(audit.entries) == 0  # no audit row for a rejected (non-)access


@pytest.mark.asyncio
async def test_list_cases_scoped():
    svc, _, _, _ = _svc()
    await svc.create_case(
        tenant_id=TENANT,
        clinic_id=CLINIC,
        user_id=USER,
        offer_id=OFFER,
        before_asset_url="b",
        after_asset_url="a",
        consent_signed=True,
    )
    cases = await svc.list_cases(tenant_id=TENANT, clinic_id=CLINIC, offer_id=OFFER)
    assert len(cases) == 1


@pytest.mark.asyncio
async def test_delete_case_writes_audit():
    svc, case_repo, _, audit = _svc()
    case = await svc.create_case(
        tenant_id=TENANT,
        clinic_id=CLINIC,
        user_id=USER,
        offer_id=OFFER,
        before_asset_url="b",
        after_asset_url="a",
        consent_signed=True,
    )
    audit.entries.clear()
    await svc.delete_case(tenant_id=TENANT, clinic_id=CLINIC, user_id=USER, case_id=case.id)
    assert len(case_repo.rows) == 0
    assert len(audit.entries) == 1  # delete of PHI is audited too


# ---- Testimonial (NOT PHI) ----------------------------------------------


@pytest.mark.asyncio
async def test_testimonial_crud_no_audit():
    svc, _, test_repo, audit = _svc()
    t = await svc.create_testimonial(
        tenant_id=TENANT,
        offer_id=OFFER,
        rating=5,
        text="Excelente atención",
        author="María G.",
        source="google",
    )
    assert t.rating == 5
    listed = await svc.list_testimonials(tenant_id=TENANT, offer_id=OFFER)
    assert len(listed) == 1
    await svc.delete_testimonial(tenant_id=TENANT, testimonial_id=t.id)
    assert len(test_repo.rows) == 0
    assert len(audit.entries) == 0  # testimonial is not PHI
