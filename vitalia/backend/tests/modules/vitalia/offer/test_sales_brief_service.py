# cap: lisa.servicios
"""Unit tests for SalesBriefService (T-2 § 6 + G2-F12-BE regression).

CRUD + idempotent autosave on the brand-local SalesBrief (1:1 per offer, NOT
PHI). D-2: the sales brief fields are vitalia-specific (faq/objections/keywords/
contraindications) with no direct engine Offer home, so the write-through is a
no-op today (documented) — the service owns the brand table and stays the SSoT.
First save creates; subsequent saves update the same row (no duplicates).

Regression G2-F12-BE: _apply must coerce faq/objections list[dict] → VOs before
setattr so that faq_to_list(brief.faq) in the real repository does not crash with
AttributeError on dict.question (500 → 200).
"""

from __future__ import annotations

from uuid import UUID

import pytest

from src.modules.vitalia.offer.application.services.sales_brief_service import SalesBriefService
from src.modules.vitalia.offer.domain.sales_brief import SalesBrief
from src.modules.vitalia.offer.domain.vos import FaqPair, ObjectionPair
from src.modules.vitalia.offer.infrastructure.serializers import faq_to_list, objections_to_list

TENANT = UUID("11111111-1111-1111-1111-111111111111")
OFFER = UUID("44444444-4444-4444-4444-444444444444")


class _FakeBriefRepo:
    def __init__(self) -> None:
        self.rows: list[SalesBrief] = []

    async def get_by_offer(self, offer_id, *, tenant_id):
        for b in self.rows:
            if b.offer_id == offer_id and b.tenant_id == tenant_id:
                return b
        return None

    async def create(self, brief: SalesBrief) -> SalesBrief:
        self.rows.append(brief)
        return brief

    async def update(self, brief: SalesBrief) -> SalesBrief:
        for i, b in enumerate(self.rows):
            if b.id == brief.id and b.tenant_id == brief.tenant_id:
                self.rows[i] = brief
                return brief
        raise AssertionError("update on missing row")


def _svc() -> tuple[SalesBriefService, _FakeBriefRepo]:
    repo = _FakeBriefRepo()
    return SalesBriefService(brief_repo=repo), repo


@pytest.mark.asyncio
async def test_get_returns_none_when_absent():
    svc, _ = _svc()
    assert await svc.get(tenant_id=TENANT, offer_id=OFFER) is None


@pytest.mark.asyncio
async def test_first_save_creates_row():
    svc, repo = _svc()
    saved = await svc.save(
        tenant_id=TENANT,
        offer_id=OFFER,
        fields={"candidate_ideal": "Pacientes 30-45 buscando estética facial"},
    )
    assert saved.candidate_ideal == "Pacientes 30-45 buscando estética facial"
    assert len(repo.rows) == 1


@pytest.mark.asyncio
async def test_autosave_is_idempotent_no_duplicate_row():
    svc, repo = _svc()
    await svc.save(tenant_id=TENANT, offer_id=OFFER, fields={"candidate_ideal": "v1"})
    again = await svc.save(tenant_id=TENANT, offer_id=OFFER, fields={"candidate_ideal": "v2"})
    assert again.candidate_ideal == "v2"
    assert len(repo.rows) == 1  # same row, updated in place


@pytest.mark.asyncio
async def test_save_persists_keywords_and_requires_evaluation():
    svc, repo = _svc()
    saved = await svc.save(
        tenant_id=TENANT,
        offer_id=OFFER,
        fields={"keywords": ["botox", "arrugas"], "requires_evaluation": True},
    )
    assert saved.keywords == ["botox", "arrugas"]
    assert saved.requires_evaluation is True


@pytest.mark.asyncio
async def test_save_ignores_unknown_fields():
    svc, _ = _svc()
    saved = await svc.save(
        tenant_id=TENANT,
        offer_id=OFFER,
        fields={"candidate_ideal": "ok", "not_a_field": "drop me"},
    )
    assert saved.candidate_ideal == "ok"
    assert not hasattr(saved, "not_a_field")


@pytest.mark.asyncio
async def test_get_after_save_returns_persisted():
    svc, _ = _svc()
    await svc.save(tenant_id=TENANT, offer_id=OFFER, fields={"promos": "2x1 marzo"})
    got = await svc.get(tenant_id=TENANT, offer_id=OFFER)
    assert got is not None
    assert got.promos == "2x1 marzo"


# ---------------------------------------------------------------------------
# Regression G2-F12-BE: faq/objections dicts → VOs coercion (500 bug)
# ---------------------------------------------------------------------------
# The real SalesBriefRepository calls faq_to_list(brief.faq) which does
#   `f.question for f in faq`
# If _apply left faq as list[dict], that raises AttributeError → HTTP 500.
# These tests verify that after save(), brief.faq is list[FaqPair] (not dicts)
# so the serializer round-trip is safe.


class _SerializingFakeBriefRepo(_FakeBriefRepo):
    """Like _FakeBriefRepo but validates VO types on create/update,
    simulating the real repo's faq_to_list / objections_to_list calls."""

    async def create(self, brief: SalesBrief) -> SalesBrief:
        # This is what the real repo does — raises AttributeError if dict:
        faq_to_list(brief.faq)
        objections_to_list(brief.objections)
        return await super().create(brief)

    async def update(self, brief: SalesBrief) -> SalesBrief:
        faq_to_list(brief.faq)
        objections_to_list(brief.objections)
        return await super().update(brief)


def _serializing_svc() -> tuple[SalesBriefService, _SerializingFakeBriefRepo]:
    repo = _SerializingFakeBriefRepo()
    return SalesBriefService(brief_repo=repo), repo


@pytest.mark.asyncio
async def test_save_faq_dicts_coerced_to_vos_no_attribute_error():
    """Regression G2-F12-BE: PATCH with faq=[dict] must NOT raise AttributeError.

    Before the fix, _apply set brief.faq = list[dict]; the repo then called
    faq_to_list(brief.faq) → f.question on a dict → AttributeError → 500.
    """
    svc, repo = _serializing_svc()
    saved = await svc.save(
        tenant_id=TENANT,
        offer_id=OFFER,
        fields={"faq": [{"question": "¿Duele?", "answer": "No duele"}]},
    )
    # brief.faq must be list[FaqPair], not list[dict]
    assert len(saved.faq) == 1
    assert isinstance(saved.faq[0], FaqPair)
    assert saved.faq[0].question == "¿Duele?"
    # serializer round-trip must be clean
    serialized = faq_to_list(saved.faq)
    assert serialized == [{"question": "¿Duele?", "answer": "No duele"}]


@pytest.mark.asyncio
async def test_save_objections_dicts_coerced_to_vos():
    """Regression G2-F12-BE: PATCH with objections=[dict] must NOT raise AttributeError."""
    svc, repo = _serializing_svc()
    saved = await svc.save(
        tenant_id=TENANT,
        offer_id=OFFER,
        fields={"objections": [{"objection_type": "precio", "response": "Financiamiento disponible"}]},
    )
    assert len(saved.objections) == 1
    assert isinstance(saved.objections[0], ObjectionPair)
    assert saved.objections[0].objection_type == "precio"
    serialized = objections_to_list(saved.objections)
    assert serialized == [{"objection_type": "precio", "response": "Financiamiento disponible"}]


@pytest.mark.asyncio
async def test_save_faq_empty_list_clears_faq():
    """Clearing faq by passing [] should persist as empty list[FaqPair]."""
    svc, _ = _serializing_svc()
    # Seed with an entry first
    await svc.save(
        tenant_id=TENANT,
        offer_id=OFFER,
        fields={"faq": [{"question": "¿Funciona?", "answer": "Sí"}]},
    )
    # Now clear
    cleared = await svc.save(tenant_id=TENANT, offer_id=OFFER, fields={"faq": []})
    assert cleared.faq == []


@pytest.mark.asyncio
async def test_save_faq_update_second_call_still_typed():
    """Second autosave with new faq dicts must also coerce (update path)."""
    svc, _ = _serializing_svc()
    await svc.save(
        tenant_id=TENANT,
        offer_id=OFFER,
        fields={"faq": [{"question": "Primera", "answer": "Respuesta 1"}]},
    )
    updated = await svc.save(
        tenant_id=TENANT,
        offer_id=OFFER,
        fields={
            "faq": [
                {"question": "Primera", "answer": "Respuesta 1"},
                {"question": "Segunda", "answer": "Respuesta 2"},
            ]
        },
    )
    assert len(updated.faq) == 2
    assert all(isinstance(f, FaqPair) for f in updated.faq)
    # Serializer must not raise
    faq_to_list(updated.faq)
