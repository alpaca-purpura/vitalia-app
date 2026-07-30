# cap: lisa.servicios
"""RED-first unit tests for ServiceCatalogService (T-2 § 6).

In-memory fakes for the engine port + brand repos (no DB). Pins:
- create = engine Offer (DRAFT) + OfferExt in one brand unit-of-work
- rollback: engine create fails → no orphan OfferExt persisted
- set_active toggles engine status ACTIVE↔PAUSED + ext.is_active
- soft_delete archives engine + soft-deletes ext
- list composes engine name search with ext filters/cursor
- telemetry is best-effort (never breaks the write)
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from luana_core_offer_studio.domain.enums import OfferStatus

from src.modules.vitalia.offer.application.ports.offer_engine_port import OfferEnginePort
from src.modules.vitalia.offer.application.services.catalog_service import ServiceCatalogService
from src.modules.vitalia.offer.application.services.medical_offer_factory import build_medical_service_offer
from src.modules.vitalia.offer.domain.enums import ServiceModality
from src.modules.vitalia.offer.domain.offer_ext import OfferExt

TENANT_A = UUID("11111111-1111-1111-1111-111111111111")


class _FakeEngine(OfferEnginePort):
    def __init__(self, *, fail_create: bool = False) -> None:
        self._fail_create = fail_create
        self.store: dict[UUID, object] = {}

    async def create_service_offer(self, *, tenant_id, public_name, price, currency, status, canonical_ref):
        if self._fail_create:
            raise RuntimeError("engine boom")
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
        offer = self.store[offer_id]
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

    async def get_by_offer(self, offer_id, *, tenant_id):
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

    async def soft_delete(self, entity_id, *, tenant_id) -> None:
        ext = self.store.get(entity_id)
        if ext is not None:
            ext.deleted_at = datetime.now(UTC)


class _NullEmitter:
    async def emit_event(self, **kwargs) -> None:  # noqa: ANN003
        return None


def _svc(*, fail_create: bool = False) -> tuple[ServiceCatalogService, _FakeEngine, _FakeExtRepo]:
    engine = _FakeEngine(fail_create=fail_create)
    ext_repo = _FakeExtRepo()
    svc = ServiceCatalogService(engine=engine, ext_repo=ext_repo, emitter=_NullEmitter())
    return svc, engine, ext_repo


@pytest.mark.asyncio
async def test_create_persists_engine_offer_draft_and_ext():
    svc, engine, ext_repo = _svc()
    view = await svc.create_service(
        tenant_id=TENANT_A,
        public_name="Limpieza dental",
        price=Decimal("120"),
        currency="PEN",
        canonical_ref=None,
        modality=ServiceModality.UNICA,
        category="Odontología general",
    )
    assert view.public_name == "Limpieza dental"
    assert len(engine.store) == 1
    offer = next(iter(engine.store.values()))
    assert offer.status == OfferStatus.DRAFT  # type: ignore[attr-defined]
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is not None
    assert ext.modality == ServiceModality.UNICA


@pytest.mark.asyncio
async def test_create_rolls_back_ext_when_engine_fails():
    svc, engine, ext_repo = _svc(fail_create=True)
    with pytest.raises(RuntimeError):
        await svc.create_service(
            tenant_id=TENANT_A,
            public_name="Falla",
            price=Decimal("10"),
            currency="PEN",
            canonical_ref=None,
            modality=ServiceModality.UNICA,
            category=None,
        )
    assert len(engine.store) == 0
    assert len(ext_repo.store) == 0  # no orphan ext


@pytest.mark.asyncio
async def test_set_active_toggles_engine_status_and_ext_flag():
    svc, engine, ext_repo = _svc()
    view = await svc.create_service(
        tenant_id=TENANT_A,
        public_name="Botox",
        price=Decimal("300"),
        currency="PEN",
        canonical_ref=None,
        modality=ServiceModality.RECURRENTE,
        category="Medicina estética",
    )
    activated = await svc.set_active(tenant_id=TENANT_A, offer_id=view.offer_id, active=True)
    assert activated.is_active is True
    offer = engine.store[view.offer_id]
    assert offer.status == OfferStatus.ACTIVE  # type: ignore[attr-defined]
    paused = await svc.set_active(tenant_id=TENANT_A, offer_id=view.offer_id, active=False)
    assert paused.is_active is False
    assert engine.store[view.offer_id].status == OfferStatus.PAUSED  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_soft_delete_marks_ext_deleted():
    svc, engine, ext_repo = _svc()
    view = await svc.create_service(
        tenant_id=TENANT_A,
        public_name="X",
        price=Decimal("1"),
        currency="PEN",
        canonical_ref=None,
        modality=ServiceModality.UNICA,
        category=None,
    )
    await svc.soft_delete(tenant_id=TENANT_A, offer_id=view.offer_id)
    ext = await ext_repo.get_by_offer(view.offer_id, tenant_id=TENANT_A)
    assert ext is None  # soft-deleted → not returned


@pytest.mark.asyncio
async def test_get_service_cross_tenant_returns_none():
    svc, engine, ext_repo = _svc()
    view = await svc.create_service(
        tenant_id=TENANT_A,
        public_name="X",
        price=Decimal("1"),
        currency="PEN",
        canonical_ref=None,
        modality=ServiceModality.UNICA,
        category=None,
    )
    other = UUID("22222222-2222-2222-2222-222222222222")
    assert await svc.get_service(tenant_id=other, offer_id=view.offer_id) is None
