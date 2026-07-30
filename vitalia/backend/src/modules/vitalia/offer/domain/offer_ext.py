# cap: lisa.servicios
# voseo-allowed: "vos" matched by hook is the value-objects module name (domain.vos), not voseo
"""OfferExt aggregate — brand projection over the engine Offer (offer_id → products.id).

Pure domain (zero framework import). Mutable (autosave-per-field at the api layer
patches individual attributes). is_active defaults False and is NEVER blocked by
completeness (RN-10 / AC-19). MANDATORY: tenant_id, soft-delete (deleted_at).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from src.modules.vitalia.offer.domain.enums import InitialApptType, ServiceModality
from src.modules.vitalia.offer.domain.vos import ServiceVariant, ThreeChargePricing, ValueWithUnit


@dataclass
class OfferExt:
    """Brand-level projection of a medical service over the engine Offer."""

    tenant_id: UUID
    offer_id: UUID  # FK → products.id (engine)
    modality: ServiceModality
    is_active: bool = False  # RN-10 · never blocked by completeness (AC-19)
    canonical_service_ref: str | None = None  # RN-25/30 (null = personalizado)
    category: str | None = None  # clinic area; locked if standard template
    clinic_scope: UUID | None = None  # RN-12 (null = all clinics)
    # — Qué es —
    description_long: str | None = None
    includes: str | None = None
    excludes: str | None = None
    warranty: str | None = None
    variants: list[ServiceVariant] = field(default_factory=list)  # RN-29
    # — Procedimiento (paciente-facing · RN-26) —
    procedure_steps: str | None = None
    anesthesia_pain: str | None = None
    prep: str | None = None
    aftercare: str | None = None
    downtime: str | None = None
    # — Resultados —
    expected_result: str | None = None
    result_timing: str | None = None
    result_lifespan: str | None = None
    realistic_expectations: str | None = None
    # — Riesgos (capa curada · RN-22/26) —
    risks: str | None = None
    red_flags: str | None = None
    # — Modalidad y agenda —
    session_interval: ValueWithUnit | None = None  # if modality=sesiones
    recurrence_interval: ValueWithUnit | None = None  # if modality=recurrente
    initial_appt_duration_minutes: int | None = None  # RN-31 (Mateo agenda)
    initial_appt_type: InitialApptType | None = None  # RN-32
    pricing: ThreeChargePricing | None = None  # RN-6
    candidate_for_library: bool = False  # RN-27
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None  # MANDATORY soft-delete
