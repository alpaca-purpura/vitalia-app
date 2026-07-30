# cap: lisa.servicios
"""RED-first · ServiceDetailDTO and ServiceView carry rich ficha fields — T-R1 § A.4.

Verifies the read-path half of F2:
- After a rich-fields patch, GET detail (via _detail_dto/patch_service) returns
  the rich fields in the ServiceDetailDTO response.
- ServiceView carries each rich field from OfferExt.
- Dual-tenant: detail request by wrong tenant → 404 (router) / None (service).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from luana_core_offer_studio.domain.enums import OfferStatus

from src.modules.vitalia.offer.api.dtos import ServiceDetailDTO
from src.modules.vitalia.offer.application.services.catalog_service import ServiceCatalogService, _view
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


# ── fakes (reused pattern from test_catalog_service.py) ──────────────────────


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


# ── ServiceView carries rich fields ──────────────────────────────────────────


def test_view_carries_rich_str_fields() -> None:
    """_view() must transfer rich OfferExt fields into ServiceView."""
    offer_id = uuid4()
    offer = build_medical_service_offer(
        tenant_id=TENANT_A,
        public_name="Ortodoncia",
        price=5000.0,
        currency="PEN",
        status=OfferStatus.DRAFT,
        canonical_ref=None,
        offer_id=offer_id,
    )
    ext = OfferExt(
        tenant_id=TENANT_A,
        offer_id=offer_id,
        modality=ServiceModality.SESIONES,
        description_long="Corrección de maloclusión con brackets metálicos.",
        includes="Brackets + controles mensuales.",
        excludes="Retención post-tratamiento.",
        warranty="Garantía 12 meses en materiales.",
        procedure_steps="Diagnóstico → bandas → ajuste mensual.",
        anesthesia_pain="Sin anestesia. Molestia leve post-ajuste.",
        prep="Profilaxis previa obligatoria.",
        aftercare="Higiene con cepillo interproximal.",
        downtime="Sin tiempo de recuperación.",
        expected_result="Oclusión correcta + mejora estética.",
        result_timing="18-24 meses.",
        result_lifespan="Permanente con retención.",
        realistic_expectations="Cumplimiento del tratamiento es determinante.",
        risks="Desmineralización del esmalte si higiene inadecuada.",
        red_flags="Dolor agudo → consultar.",
        initial_appt_type=InitialApptType.VALORACION_DIAGNOSTICO,
        initial_appt_duration_minutes=60,
        candidate_for_library=True,
    )

    view = _view(offer, ext)

    assert view.description_long == "Corrección de maloclusión con brackets metálicos."
    assert view.includes == "Brackets + controles mensuales."
    assert view.excludes == "Retención post-tratamiento."
    assert view.warranty == "Garantía 12 meses en materiales."
    assert view.procedure_steps == "Diagnóstico → bandas → ajuste mensual."
    assert view.anesthesia_pain == "Sin anestesia. Molestia leve post-ajuste."
    assert view.prep == "Profilaxis previa obligatoria."
    assert view.aftercare == "Higiene con cepillo interproximal."
    assert view.downtime == "Sin tiempo de recuperación."
    assert view.expected_result == "Oclusión correcta + mejora estética."
    assert view.result_timing == "18-24 meses."
    assert view.result_lifespan == "Permanente con retención."
    assert view.realistic_expectations == "Cumplimiento del tratamiento es determinante."
    assert view.risks == "Desmineralización del esmalte si higiene inadecuada."
    assert view.red_flags == "Dolor agudo → consultar."
    assert view.initial_appt_type == InitialApptType.VALORACION_DIAGNOSTICO
    assert view.initial_appt_duration_minutes == 60
    assert view.candidate_for_library is True


def test_view_carries_variant_vo() -> None:
    offer_id = uuid4()
    offer = build_medical_service_offer(
        tenant_id=TENANT_A,
        public_name="Depilación",
        price=300.0,
        currency="PEN",
        status=OfferStatus.DRAFT,
        canonical_ref=None,
        offer_id=offer_id,
    )
    ext = OfferExt(
        tenant_id=TENANT_A,
        offer_id=offer_id,
        modality=ServiceModality.UNICA,
        variants=[ServiceVariant(name="Zona pequeña", price=Decimal("150"))],
    )
    view = _view(offer, ext)
    assert len(view.variants) == 1
    assert view.variants[0].name == "Zona pequeña"


def test_view_carries_session_interval_vo() -> None:
    offer_id = uuid4()
    offer = build_medical_service_offer(
        tenant_id=TENANT_A,
        public_name="Fisioterapia",
        price=200.0,
        currency="PEN",
        status=OfferStatus.DRAFT,
        canonical_ref=None,
        offer_id=offer_id,
    )
    ext = OfferExt(
        tenant_id=TENANT_A,
        offer_id=offer_id,
        modality=ServiceModality.SESIONES,
        session_interval=ValueWithUnit(value=2, unit=IntervalUnit.SEMANAS),
    )
    view = _view(offer, ext)
    assert view.session_interval is not None
    assert view.session_interval.value == 2
    assert view.session_interval.unit == IntervalUnit.SEMANAS


def test_view_carries_pricing_vo() -> None:
    offer_id = uuid4()
    offer = build_medical_service_offer(
        tenant_id=TENANT_A,
        public_name="Implante dental",
        price=4000.0,
        currency="PEN",
        status=OfferStatus.DRAFT,
        canonical_ref=None,
        offer_id=offer_id,
    )
    ext = OfferExt(
        tenant_id=TENANT_A,
        offer_id=offer_id,
        modality=ServiceModality.UNICA,
        pricing=ThreeChargePricing(
            price=Decimal("4000"),
            price_mode=PriceMode.FIJO,
            price_publishable=True,
            currency="PEN",
            reservation=ReservationConfig(enabled=True, amount=Decimal("800"), kind=ReservationKind.MONTO),
            advance=None,
            financing=FinancingConfig(offered=True, installments=4, interest_kind="msi"),
        ),
    )
    view = _view(offer, ext)
    assert view.pricing is not None
    assert view.pricing.price == Decimal("4000")
    assert view.pricing.reservation is not None
    assert view.pricing.financing is not None
    assert view.pricing.financing.installments == 4


# ── ServiceDetailDTO carries rich fields ─────────────────────────────────────


@pytest.mark.asyncio
async def test_get_service_detail_dto_carries_rich_fields_after_patch() -> None:
    """Full integration path: create → patch rich fields → get → ServiceDetailDTO carries them."""
    svc, _, ext_repo = _svc()

    view = await svc.create_service(
        tenant_id=TENANT_A,
        public_name="Dermoabrasión",
        price=Decimal("800"),
        currency="PEN",
        canonical_ref=None,
        modality=ServiceModality.SESIONES,
        category="Dermatología estética",
    )
    await svc.patch_service(
        tenant_id=TENANT_A,
        offer_id=view.offer_id,
        description_long="Renovación celular con microdermoabrasión.",
        includes="Crema regeneradora post-sesión.",
        risks="Rojez transitoria 24-48h.",
        initial_appt_type=InitialApptType.PRIMERA_SESION_DIRECTA,
        initial_appt_duration_minutes=50,
        session_interval=ValueWithUnit(value=3, unit=IntervalUnit.SEMANAS),
        candidate_for_library=True,
    )

    enriched_view = await svc.get_service(tenant_id=TENANT_A, offer_id=view.offer_id)
    assert enriched_view is not None

    # Build ServiceDetailDTO from the enriched view (mirrors _detail_dto in router)
    dto = ServiceDetailDTO(
        offer_id=enriched_view.offer_id,
        public_name=enriched_view.public_name,
        category=enriched_view.category,
        modality=enriched_view.modality,
        is_active=enriched_view.is_active,
        status=enriched_view.status,
        canonical_service_ref=enriched_view.canonical_service_ref,
        price=enriched_view.price,
        currency=enriched_view.currency,
        description_long=enriched_view.description_long,
        includes=enriched_view.includes,
        risks=enriched_view.risks,
        initial_appt_type=enriched_view.initial_appt_type,
        initial_appt_duration_minutes=enriched_view.initial_appt_duration_minutes,
        session_interval=enriched_view.session_interval,
        candidate_for_library=enriched_view.candidate_for_library,
    )
    assert dto.description_long == "Renovación celular con microdermoabrasión."
    assert dto.includes == "Crema regeneradora post-sesión."
    assert dto.risks == "Rojez transitoria 24-48h."
    assert dto.initial_appt_type == InitialApptType.PRIMERA_SESION_DIRECTA
    assert dto.initial_appt_duration_minutes == 50
    assert dto.session_interval is not None
    assert dto.session_interval.value == 3  # type: ignore[union-attr]  # fix: patch sets value=3
    assert dto.candidate_for_library is True


@pytest.mark.asyncio
async def test_get_service_cross_tenant_returns_none_detail() -> None:
    svc, _, _ = _svc()
    view = await svc.create_service(
        tenant_id=TENANT_A,
        public_name="X",
        price=Decimal("1"),
        currency="PEN",
        canonical_ref=None,
        modality=ServiceModality.UNICA,
        category=None,
    )
    result = await svc.get_service(tenant_id=TENANT_B, offer_id=view.offer_id)
    assert result is None  # cross-tenant → 404 at router level
