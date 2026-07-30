# cap: lisa.servicios
"""RED-first · patch_service() routes rich ficha fields to OfferExt — T-R1 § A.3.

Verifies (G reconcile reconcile-delta):
- All rich str fields (description_long, includes, excludes, warranty,
  procedure_steps, anesthesia_pain, prep, aftercare, downtime,
  expected_result, result_timing, result_lifespan, realistic_expectations,
  risks, red_flags) are persisted on OfferExt when patched.
- VO fields (variants, session_interval, recurrence_interval, pricing,
  initial_appt_type, initial_appt_duration_minutes, candidate_for_library)
  are routed correctly.
- None = not-present → last-write-wins (existing value NOT clobbered).
- Dual-tenant isolation: patch by tenant_B over tenant_A's offer → None.
- Cross-tenant 403 (service returns None → router maps to 404 — service level).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.modules.vitalia.offer.application.services.catalog_service import ServiceCatalogService
from src.modules.vitalia.offer.application.services.medical_offer_factory import build_medical_service_offer
from src.modules.vitalia.offer.domain.enums import (
    InitialApptType,
    IntervalUnit,
    PriceMode,
    ReservationKind,
    ServiceModality,
)
from src.modules.vitalia.offer.domain.offer_ext import OfferExt
from src.modules.vitalia.offer.domain.vos import (
    FinancingConfig,
    ReservationConfig,
    ServiceVariant,
    ThreeChargePricing,
    ValueWithUnit,
)

TENANT_A = UUID("11111111-1111-1111-1111-111111111111")
TENANT_B = UUID("22222222-2222-2222-2222-222222222222")


# ── fakes ────────────────────────────────────────────────────────────────────


class _FakeEngine:
    def __init__(self) -> None:
        self.store: dict[UUID, object] = {}

    async def create_service_offer(self, *, tenant_id, public_name, price, currency, status, canonical_ref):
        offer = build_medical_service_offer(
            tenant_id=tenant_id,
            public_name=public_name,
            price=price,
            currency=currency,
            status=status,
            canonical_ref=canonical_ref,
            offer_id=uuid4(),
        )
        self.store[offer.id] = offer  # type: ignore[index]
        return offer

    async def update_service_offer(
        self, *, tenant_id, offer_id, public_name=None, price=None, currency=None, status=None
    ):
        offer = self.store.get(offer_id)
        if offer is None:
            return None
        if public_name is not None:
            offer.public_name = public_name  # type: ignore[attr-defined]
        if status is not None:
            offer.status = status  # type: ignore[attr-defined]
        return offer

    async def get(self, *, tenant_id, offer_id):
        return self.store.get(offer_id)

    async def list_service_offers(self, *, tenant_id):
        return list(self.store.values())  # type: ignore[arg-type]


class _FakeExtRepo:
    def __init__(self) -> None:
        self.store: dict[UUID, OfferExt] = {}

    async def create(self, ext: OfferExt) -> OfferExt:
        self.store[ext.id] = ext
        return ext

    async def get_by_offer(self, offer_id: UUID, *, tenant_id: UUID) -> OfferExt | None:
        for ext in self.store.values():
            if ext.offer_id == offer_id and ext.tenant_id == tenant_id and ext.deleted_at is None:
                return ext
        return None

    async def update(self, ext: OfferExt) -> OfferExt:
        self.store[ext.id] = ext
        return ext

    async def list_by_tenant(self, *, tenant_id, category=None, active=None, origin=None, cursor=None, limit=24):
        rows = [e for e in self.store.values() if e.tenant_id == tenant_id and e.deleted_at is None]
        return rows, None

    async def soft_delete(self, entity_id: UUID, *, tenant_id: UUID) -> None:
        ext = self.store.get(entity_id)
        if ext is not None:
            ext.deleted_at = datetime.now(UTC)


class _NullEmitter:
    async def emit_event(self, **kwargs: object) -> None:  # noqa: ANN003
        return None


def _svc() -> tuple[ServiceCatalogService, _FakeEngine, _FakeExtRepo]:
    engine = _FakeEngine()
    ext_repo = _FakeExtRepo()
    svc = ServiceCatalogService(engine=engine, ext_repo=ext_repo, emitter=_NullEmitter())
    return svc, engine, ext_repo


async def _create_offer(svc: ServiceCatalogService, tenant_id: UUID = TENANT_A):
    return await svc.create_service(
        tenant_id=tenant_id,
        public_name="Blanqueamiento dental",
        price=Decimal("350"),
        currency="PEN",
        canonical_ref=None,
        modality=ServiceModality.UNICA,
        category="Odontología estética",
    )


# ── str fields routing ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_patch_description_long_persists() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    patched = await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        description_long="Técnica de fotopolimerización avanzada.",
    )
    assert patched is not None
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.description_long == "Técnica de fotopolimerización avanzada."


@pytest.mark.asyncio
async def test_patch_includes_excludes_warranty() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        includes="Kit blanqueamiento de alta concentración.",
        excludes="Restauraciones previas.",
        warranty="6 meses de mantenimiento.",
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.includes == "Kit blanqueamiento de alta concentración."
    assert ext.excludes == "Restauraciones previas."
    assert ext.warranty == "6 meses de mantenimiento."


@pytest.mark.asyncio
async def test_patch_procedure_fields() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        procedure_steps="Profilaxis → aplicación gel → fotopolimerización 20 min.",
        anesthesia_pain="No requiere anestesia. Sensibilidad leve post-sesión.",
        prep="Evitar café y vino 48h previas.",
        aftercare="Dieta blanca 48h post sesión.",
        downtime="Sin tiempo de recuperación.",
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.procedure_steps == "Profilaxis → aplicación gel → fotopolimerización 20 min."
    assert ext.anesthesia_pain == "No requiere anestesia. Sensibilidad leve post-sesión."
    assert ext.prep == "Evitar café y vino 48h previas."
    assert ext.aftercare == "Dieta blanca 48h post sesión."
    assert ext.downtime == "Sin tiempo de recuperación."


@pytest.mark.asyncio
async def test_patch_result_fields() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        expected_result="Dientes 4-8 tonos más claros.",
        result_timing="Desde la primera sesión.",
        result_lifespan="12-18 meses.",
        realistic_expectations="Resultados varían según pigmentación previa.",
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.expected_result == "Dientes 4-8 tonos más claros."
    assert ext.result_timing == "Desde la primera sesión."
    assert ext.result_lifespan == "12-18 meses."
    assert ext.realistic_expectations == "Resultados varían según pigmentación previa."


@pytest.mark.asyncio
async def test_patch_risk_fields() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        risks="Sensibilidad dentinaria transitoria.",
        red_flags="Dolor agudo persistente → consultar dentista.",
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.risks == "Sensibilidad dentinaria transitoria."
    assert ext.red_flags == "Dolor agudo persistente → consultar dentista."


# ── VO fields routing ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_patch_variants_routes_list_of_frozen_vos() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    variants = [
        ServiceVariant(name="Arcada superior", price=Decimal("200")),
        ServiceVariant(name="Arcada inferior", price=Decimal("200")),
    ]
    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        variants=variants,
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert len(ext.variants) == 2
    assert ext.variants[0].name == "Arcada superior"


@pytest.mark.asyncio
async def test_patch_session_interval_routes_frozen_vo() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    interval = ValueWithUnit(value=3, unit=IntervalUnit.SEMANAS)
    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        session_interval=interval,
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.session_interval is not None
    assert ext.session_interval.value == 3
    assert ext.session_interval.unit == IntervalUnit.SEMANAS


@pytest.mark.asyncio
async def test_patch_recurrence_interval_routes_frozen_vo() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    interval = ValueWithUnit(value=6, unit=IntervalUnit.MESES)
    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        recurrence_interval=interval,
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.recurrence_interval is not None
    assert ext.recurrence_interval.value == 6


@pytest.mark.asyncio
async def test_patch_initial_appt_type_routes_enum() -> None:
    """F3 — initial_appt_type persists (was missing before G reconcile)."""
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        initial_appt_type=InitialApptType.VALORACION_DIAGNOSTICO,
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.initial_appt_type == InitialApptType.VALORACION_DIAGNOSTICO


@pytest.mark.asyncio
async def test_patch_initial_appt_duration_minutes() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        initial_appt_duration_minutes=45,
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.initial_appt_duration_minutes == 45


@pytest.mark.asyncio
async def test_patch_pricing_routes_three_charge_vo() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    pricing = ThreeChargePricing(
        price=Decimal("1200"),
        price_mode=PriceMode.FIJO,
        price_publishable=True,
        currency="PEN",
        reservation=ReservationConfig(enabled=True, amount=Decimal("200"), kind=ReservationKind.MONTO),
        advance=None,
        financing=FinancingConfig(offered=True, installments=3, interest_kind="msi"),
    )
    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        pricing=pricing,
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.pricing is not None
    assert ext.pricing.price == Decimal("1200")
    assert ext.pricing.reservation is not None
    assert ext.pricing.reservation.enabled is True
    assert ext.pricing.financing is not None
    assert ext.pricing.financing.installments == 3


@pytest.mark.asyncio
async def test_patch_candidate_for_library_bool() -> None:
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        candidate_for_library=True,
    )
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.candidate_for_library is True


# ── last-write-wins (None = not-present, don't clobber) ──────────────────────


@pytest.mark.asyncio
async def test_patch_none_does_not_clobber_existing_value() -> None:
    """None = absent key → last-write-wins semantics preserve stored value."""
    svc, _, ext_repo = _svc()
    view = await _create_offer(svc)

    # First patch sets description_long
    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        description_long="Descripción original.",
    )

    # Second patch touches a different field; description_long=None means "not sent"
    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        includes="Kit incluido.",
        description_long=None,  # not sent → must NOT overwrite
    )

    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.description_long == "Descripción original."  # preserved
    assert ext.includes == "Kit incluido."  # new value written


# ── dual-tenant isolation ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_patch_cross_tenant_returns_none() -> None:
    """TENANT_B cannot patch TENANT_A's offer."""
    svc, _, _ = _svc()
    view = await _create_offer(svc, tenant_id=TENANT_A)

    result = await svc.patch_service(
        tenant_id=TENANT_B,
        offer_id=view.offer_id,
        description_long="intento de inyección cross-tenant.",
    )
    assert result is None  # cross-tenant → service returns None → router 404
