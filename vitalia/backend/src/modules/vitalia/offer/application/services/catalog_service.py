# cap: lisa.servicios
# voseo-allowed: "vos" matched by hook is the value-objects module name (domain.vos), not voseo
"""ServiceCatalogService — Lisa's service catalog CRUD (T-2 § 6).

The create of a service is the ONLY multi-write: an engine ``Offer`` row (so
``TenantKnowledgeBuilder.build_identity`` surfaces it — keystone AC-6) plus a
brand ``OfferExt`` projection. The application orchestrates both in a single
brand unit-of-work and rolls the ext back if the engine create fails, so no
orphan ext is left behind. All reads/writes filter ``tenant_id`` (catalog is
NOT PHI — RN-13 — so no clinic dual filter here). Telemetry is best-effort.

T-R1 (G reconcile): ServiceView widened to carry all rich OfferExt fields;
_view() populates them; patch_service() routes all rich kwargs to OfferExt
setters (None = not-present → last-write-wins, no clobber).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol
from uuid import UUID

import structlog
from luana_core_offer_studio.domain.enums import OfferStatus

from src.modules.vitalia.offer.application.ports.offer_engine_port import OfferEnginePort
from src.modules.vitalia.offer.domain.enums import InitialApptType, ServiceModality
from src.modules.vitalia.offer.domain.offer_ext import OfferExt
from src.modules.vitalia.offer.domain.vos import ServiceVariant, ThreeChargePricing, ValueWithUnit

logger = structlog.get_logger()


class _ExtRepo(Protocol):
    async def create(self, ext: OfferExt) -> OfferExt: ...
    async def get_by_offer(self, offer_id: UUID, *, tenant_id: UUID) -> OfferExt | None: ...
    async def update(self, ext: OfferExt) -> OfferExt: ...
    async def list_by_tenant(
        self,
        *,
        tenant_id: UUID,
        category: str | None = None,
        active: bool | None = None,
        origin: str | None = None,
        cursor: object | None = None,
        limit: int = 24,
    ) -> tuple[list[OfferExt], object | None]: ...
    async def soft_delete(self, entity_id: UUID, *, tenant_id: UUID) -> None: ...


class _Emitter(Protocol):
    async def emit_event(self, **kwargs: object) -> None: ...


@dataclass(frozen=True)
class ServiceView:
    """Composed read model: engine Offer headline + brand ext projection.

    Widened in T-R1 (G reconcile) to carry all rich OfferExt fields so the
    GET response (ServiceDetailDTO) can hydrate the FE ResumenView.
    currency: str | None — NEVER hardcoded 'USD' (currency-handling rule).
    """

    offer_id: UUID
    public_name: str
    price: Decimal | None
    currency: str | None
    status: OfferStatus
    is_active: bool
    modality: ServiceModality
    category: str | None
    canonical_service_ref: str | None
    # — Rich ficha fields (T-R1 § A.4 — read-path widening) —
    description_long: str | None = None
    includes: str | None = None
    excludes: str | None = None
    warranty: str | None = None
    variants: list[ServiceVariant] = field(default_factory=list)  # RN-29
    procedure_steps: str | None = None
    anesthesia_pain: str | None = None
    prep: str | None = None
    aftercare: str | None = None
    downtime: str | None = None
    expected_result: str | None = None
    result_timing: str | None = None
    result_lifespan: str | None = None
    realistic_expectations: str | None = None
    risks: str | None = None
    red_flags: str | None = None
    session_interval: ValueWithUnit | None = None
    recurrence_interval: ValueWithUnit | None = None
    initial_appt_duration_minutes: int | None = None
    initial_appt_type: InitialApptType | None = None
    pricing: ThreeChargePricing | None = None
    candidate_for_library: bool = False


class ServiceCatalogService:
    """Orchestrates the engine Offer + brand OfferExt lifecycle for Lisa's catalog."""

    def __init__(self, *, engine: OfferEnginePort, ext_repo: _ExtRepo, emitter: _Emitter) -> None:
        self._engine = engine
        self._ext = ext_repo
        self._emitter = emitter

    async def create_service(
        self,
        *,
        tenant_id: UUID,
        public_name: str,
        price: Decimal,
        currency: str | None,
        canonical_ref: str | None,
        modality: ServiceModality,
        category: str | None,
    ) -> ServiceView:
        # 1) Engine Offer first (DRAFT). If it fails, nothing brand-side was written.
        offer = await self._engine.create_service_offer(
            tenant_id=tenant_id,
            public_name=public_name,
            price=float(price),
            currency=currency,
            status=OfferStatus.DRAFT,
            canonical_ref=canonical_ref,
        )
        ext = OfferExt(
            tenant_id=tenant_id,
            offer_id=offer.id,
            modality=modality,
            is_active=False,
            canonical_service_ref=canonical_ref,
            category=category,
        )
        # 2) Brand ext. Roll the engine row back if the ext insert fails so the
        #    catalog never shows a service without its brand projection.
        try:
            ext = await self._ext.create(ext)
        except Exception:
            await self._archive_quietly(tenant_id=tenant_id, offer_id=offer.id)
            raise
        await self._emit(
            tenant_id, "service_created", offer.id, {"origin": "biblioteca" if canonical_ref else "personalizado"}
        )
        return _view(offer, ext)

    async def get_service(self, *, tenant_id: UUID, offer_id: UUID) -> ServiceView | None:
        ext = await self._ext.get_by_offer(offer_id, tenant_id=tenant_id)
        if ext is None:
            return None
        offer = await self._engine.get(tenant_id=tenant_id, offer_id=offer_id)
        if offer is None:
            return None
        return _view(offer, ext)

    async def patch_service(  # noqa: PLR0912,PLR0913
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        public_name: str | None = None,
        price: Decimal | None = None,
        category: str | None = None,
        modality: ServiceModality | None = None,
        # — widened (T-R1 G reconcile) — rich ficha fields; None = not-present (last-write-wins)
        description_long: str | None = None,
        includes: str | None = None,
        excludes: str | None = None,
        warranty: str | None = None,
        variants: list[ServiceVariant] | None = None,
        procedure_steps: str | None = None,
        anesthesia_pain: str | None = None,
        prep: str | None = None,
        aftercare: str | None = None,
        downtime: str | None = None,
        expected_result: str | None = None,
        result_timing: str | None = None,
        result_lifespan: str | None = None,
        realistic_expectations: str | None = None,
        risks: str | None = None,
        red_flags: str | None = None,
        session_interval: ValueWithUnit | None = None,
        recurrence_interval: ValueWithUnit | None = None,
        initial_appt_duration_minutes: int | None = None,
        initial_appt_type: InitialApptType | None = None,
        pricing: ThreeChargePricing | None = None,
        candidate_for_library: bool | None = None,
    ) -> ServiceView | None:
        ext = await self._ext.get_by_offer(offer_id, tenant_id=tenant_id)
        if ext is None:
            return None  # cross-tenant or missing → caller maps to 404
        # Apply only present fields (None = "not sent" → don't clobber stored value).
        if category is not None:
            ext.category = category
        if modality is not None:
            ext.modality = modality
        if description_long is not None:
            ext.description_long = description_long
        if includes is not None:
            ext.includes = includes
        if excludes is not None:
            ext.excludes = excludes
        if warranty is not None:
            ext.warranty = warranty
        if variants is not None:
            ext.variants = variants
        if procedure_steps is not None:
            ext.procedure_steps = procedure_steps
        if anesthesia_pain is not None:
            ext.anesthesia_pain = anesthesia_pain
        if prep is not None:
            ext.prep = prep
        if aftercare is not None:
            ext.aftercare = aftercare
        if downtime is not None:
            ext.downtime = downtime
        if expected_result is not None:
            ext.expected_result = expected_result
        if result_timing is not None:
            ext.result_timing = result_timing
        if result_lifespan is not None:
            ext.result_lifespan = result_lifespan
        if realistic_expectations is not None:
            ext.realistic_expectations = realistic_expectations
        if risks is not None:
            ext.risks = risks
        if red_flags is not None:
            ext.red_flags = red_flags
        if session_interval is not None:
            ext.session_interval = session_interval
        if recurrence_interval is not None:
            ext.recurrence_interval = recurrence_interval
        if initial_appt_duration_minutes is not None:
            ext.initial_appt_duration_minutes = initial_appt_duration_minutes
        if initial_appt_type is not None:
            ext.initial_appt_type = initial_appt_type
        if pricing is not None:
            ext.pricing = pricing
        if candidate_for_library is not None:
            ext.candidate_for_library = candidate_for_library
        ext = await self._ext.update(ext)
        if public_name is not None or price is not None:
            await self._engine.update_service_offer(
                tenant_id=tenant_id,
                offer_id=offer_id,
                public_name=public_name,
                price=float(price) if price is not None else None,
            )
        offer = await self._engine.get(tenant_id=tenant_id, offer_id=offer_id)
        if offer is None:
            return None
        return _view(offer, ext)

    async def set_active(self, *, tenant_id: UUID, offer_id: UUID, active: bool) -> ServiceView | None:
        ext = await self._ext.get_by_offer(offer_id, tenant_id=tenant_id)
        if ext is None:
            return None
        ext.is_active = active
        ext = await self._ext.update(ext)
        status = OfferStatus.ACTIVE if active else OfferStatus.PAUSED
        await self._engine.update_service_offer(tenant_id=tenant_id, offer_id=offer_id, status=status)
        offer = await self._engine.get(tenant_id=tenant_id, offer_id=offer_id)
        if offer is None:
            return None
        await self._emit(tenant_id, "service_activated" if active else "service_paused", offer_id, {})
        return _view(offer, ext)

    async def soft_delete(self, *, tenant_id: UUID, offer_id: UUID) -> None:
        ext = await self._ext.get_by_offer(offer_id, tenant_id=tenant_id)
        if ext is None:
            return
        await self._ext.soft_delete(ext.id, tenant_id=tenant_id)
        await self._archive_quietly(tenant_id=tenant_id, offer_id=offer_id)
        await self._emit(tenant_id, "service_deleted", offer_id, {})

    async def list_services(
        self,
        *,
        tenant_id: UUID,
        name_query: str | None = None,
        category: str | None = None,
        active: bool | None = None,
        origin: str | None = None,
        cursor: object | None = None,
        limit: int = 24,
    ) -> tuple[list[ServiceView], object | None]:
        # RN-15: server-side ext filters + keyset cursor (never load-all). Name
        # search is composed via the engine (Offer.public_name lives engine-side).
        exts, next_cursor = await self._ext.list_by_tenant(
            tenant_id=tenant_id,
            category=category,
            active=active,
            origin=origin,
            cursor=cursor,
            limit=limit,
        )
        views: list[ServiceView] = []
        needle = name_query.strip().lower() if name_query else None
        for ext in exts:
            offer = await self._engine.get(tenant_id=tenant_id, offer_id=ext.offer_id)
            if offer is None:
                continue
            if needle and needle not in offer.public_name.lower():
                continue
            views.append(_view(offer, ext))
        return views, next_cursor

    async def _archive_quietly(self, *, tenant_id: UUID, offer_id: UUID) -> None:
        try:
            await self._engine.update_service_offer(tenant_id=tenant_id, offer_id=offer_id, status=OfferStatus.ARCHIVED)
        except Exception as exc:  # noqa: BLE001 — best-effort cleanup, log only
            logger.warning("offer_archive_failed", tenant_id=str(tenant_id), offer_id=str(offer_id), error=str(exc))

    async def _emit(self, tenant_id: UUID, event_type: str, offer_id: UUID, props: dict[str, object]) -> None:
        try:
            await self._emitter.emit_event(event_type=event_type, tenant_id=tenant_id, entity_id=offer_id, props=props)
        except Exception as exc:  # noqa: BLE001 — telemetry is fire-forget
            logger.warning("telemetry_emit_failed", event_type=event_type, error=str(exc))


def _view(offer: object, ext: OfferExt) -> ServiceView:
    """Build ServiceView from engine Offer + brand OfferExt.

    T-R1: now populates all rich ficha fields so GET response can hydrate the FE.
    """
    price = offer.pricing_options[0].total_amount if getattr(offer, "pricing_options", None) else None  # type: ignore[attr-defined]
    return ServiceView(
        offer_id=ext.offer_id,
        public_name=offer.public_name,  # type: ignore[attr-defined]
        price=Decimal(str(price)) if price is not None else None,
        currency=offer.currency,  # type: ignore[attr-defined]
        status=offer.status,  # type: ignore[attr-defined]
        is_active=ext.is_active,
        modality=ext.modality,
        category=ext.category,
        canonical_service_ref=ext.canonical_service_ref,
        # — Rich ficha fields (T-R1 § A.4 read-path widening) —
        description_long=ext.description_long,
        includes=ext.includes,
        excludes=ext.excludes,
        warranty=ext.warranty,
        variants=list(ext.variants) if ext.variants else [],
        procedure_steps=ext.procedure_steps,
        anesthesia_pain=ext.anesthesia_pain,
        prep=ext.prep,
        aftercare=ext.aftercare,
        downtime=ext.downtime,
        expected_result=ext.expected_result,
        result_timing=ext.result_timing,
        result_lifespan=ext.result_lifespan,
        realistic_expectations=ext.realistic_expectations,
        risks=ext.risks,
        red_flags=ext.red_flags,
        session_interval=ext.session_interval,
        recurrence_interval=ext.recurrence_interval,
        initial_appt_duration_minutes=ext.initial_appt_duration_minutes,
        initial_appt_type=ext.initial_appt_type,
        pricing=ext.pricing,
        candidate_for_library=ext.candidate_for_library if ext.candidate_for_library is not None else False,
    )
