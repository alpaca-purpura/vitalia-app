---
story_id: vitalia-fase2-lisa-servicios
surface: backend
owner: builder-backend
auditor: auditor-backend
parent: 03-arch.md
---

# 03-arch-be — net-new `offer` module (DDD Inside-Out) · Sub-phase A

> CONSUME engine Offer Studio (CERO edit) + EXTEND clinics doctor roster (port) + lisa-marca voz (port).
> Detalle de entidades, modelos SQLA 2.0 async, DTOs Pydantic v2, rutas, services, ports, EP-2 preset pack.
> El offer-core persiste como engine `ProductModel` row (keystone D-1); el OfferExt brand-level en tablas brand.

## 1. Domain entities (`offer/domain/`)

> `# cap: offer.lisa-servicios` header (líneas 1-3) en TODO archivo nuevo.

### Enums
```python
class ServiceModality(StrEnum):          # RN-28
    UNICA = "unica"
    SESIONES = "sesiones"
    RECURRENTE = "recurrente"

class InitialApptType(StrEnum):          # RN-32 (3 fijo del sistema · NO configurable)
    VALORACION_DIAGNOSTICO = "valoracion_diagnostico"
    PRIMERA_SESION_DIRECTA = "primera_sesion_directa"
    CONSULTA_INFORMATIVA_GRATUITA = "consulta_informativa_gratuita"

class IntervalUnit(StrEnum):             # RN-31
    DIAS = "dias"; SEMANAS = "semanas"; MESES = "meses"; ANIOS = "anios"

class PriceMode(StrEnum):
    FIJO = "fijo"; RANGO = "rango"

class ReservationKind(StrEnum):
    MONTO = "monto"; PORCENTAJE = "porcentaje"
```

### Value Objects (frozen dataclasses, pure — no framework)
```python
@dataclass(frozen=True)
class ValueWithUnit:                       # RN-31
    value: int                             # >= 1
    unit: IntervalUnit

@dataclass(frozen=True)
class ServiceVariant:                      # RN-29
    name: str
    price: Decimal                         # >= 0
    note: str | None = None

@dataclass(frozen=True)
class ReservationConfig:                   # RN-6 (a) — apartar el turno, se descuenta del total
    enabled: bool
    amount: Decimal | None                 # >= 0
    kind: ReservationKind                  # monto | porcentaje

@dataclass(frozen=True)
class AdvanceConfig:                       # RN-6 (b) — pago para iniciar (≠ reserva)
    enabled: bool
    amount: Decimal | None                 # % o monto del total
    kind: ReservationKind

@dataclass(frozen=True)
class FinancingConfig:                     # RN-6 (c) — financiar el saldo
    offered: bool
    installments: int | None               # >= 1
    interest_kind: str | None              # "msi" | "con_interes"
    finance_partner: str | None = None

@dataclass(frozen=True)
class ThreeChargePricing:                  # RN-6 — 3 cobros INDEPENDIENTES
    price: Decimal | None                  # >= 0 (RN-11)
    price_mode: PriceMode
    price_publishable: bool                # off → Adrián agenda valoración
    currency: str | None                   # de tenant_locale (RN-3 · NUNCA hardcode)
    reservation: ReservationConfig | None
    advance: AdvanceConfig | None
    financing: FinancingConfig | None
    # Derivados (≈equivale a, ≈por mes) NO se persisten → domain/pricing_calc.py (Computed)

@dataclass(frozen=True)
class FaqPair:    q: str; a: str
@dataclass(frozen=True)
class ObjectionPair:  objection_type: str; response: str   # 5 universales: precio·miedo·tiempo·pensar·confianza
```

### Aggregates / Entities
```python
@dataclass
class OfferExt:                            # brand projection sobre el engine Offer (offer_id → products.id)
    tenant_id: UUID                        # MANDATORY
    offer_id: UUID                         # FK → products.id (engine)
    modality: ServiceModality
    is_active: bool = False                # RN-10 · NUNCA bloqueado por completitud (AC-19)
    canonical_service_ref: str | None = None  # RN-25/30 (null = personalizado)
    category: str | None = None            # opciones = áreas de la clínica (Tenant); locked si estándar
    clinic_scope: UUID | None = None       # RN-12 (null = todas)
    # — Qué es —
    description_long: str | None = None
    includes: str | None = None
    excludes: str | None = None
    warranty: str | None = None
    variants: list[ServiceVariant] = field(default_factory=list)   # RN-29
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
    session_interval: ValueWithUnit | None = None        # si modality=sesiones
    recurrence_interval: ValueWithUnit | None = None      # si modality=recurrente
    initial_appt_duration_minutes: int | None = None      # RN-31 (Mateo agenda)
    initial_appt_type: InitialApptType | None = None      # RN-32
    pricing: ThreeChargePricing | None = None             # RN-6
    candidate_for_library: bool = False                   # RN-27
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None                    # MANDATORY soft-delete

@dataclass
class SalesBrief:                          # Para Adrián (leaf 2) · write-through a engine + brand
    tenant_id: UUID
    offer_id: UUID
    candidate_ideal: str | None = None
    contraindications: str | None = None   # safety RN-22
    qualification_questions: str | None = None
    escalation_conditions: str | None = None   # safety RN-22
    requires_evaluation: bool = False
    emotional_benefits: str | None = None
    pain_of_not_treating: str | None = None
    differentiators: str | None = None
    promos: str | None = None
    faq: list[FaqPair] = field(default_factory=list)
    objections: list[ObjectionPair] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)     # RN-16 match canal-inbound
    problems_solved: str | None = None
    language_to_avoid: str | None = None
    id: UUID = field(default_factory=uuid4)
    deleted_at: datetime | None = None

@dataclass
class ServiceSpecialistLink:               # FK → vitalia_doctors (roster lisa-doctores)
    tenant_id: UUID; offer_id: UUID; doctor_id: UUID
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

@dataclass
class Case:                                # HIPAA-lite (foto paciente)
    tenant_id: UUID; offer_id: UUID
    before_asset_url: str; after_asset_url: str
    consent_signed: bool                   # gate RN-33 (False → no se guarda)
    consent_ref: str | None = None
    id: UUID = field(default_factory=uuid4)
    deleted_at: datetime | None = None

@dataclass
class Testimonial:                         # carga manual RN-33
    tenant_id: UUID; offer_id: UUID
    rating: int; text: str; author: str; source: str
    id: UUID = field(default_factory=uuid4)
    deleted_at: datetime | None = None
```

### Pure functions
- `domain/completeness.py::compute_completeness(offer_ext, sales_brief, pricing) -> (filled:int, total:int=26, missing:list[str])` — los 26 must-have del § MVP. **NUNCA bloquea is_active.** Mutation-critical.
- `domain/pricing_calc.py::compute_derived(pricing) -> {advance_equiv: Decimal, per_month: Decimal}` — `advance_equiv = price * advance.amount/100` (si %); `per_month = (price - reservation - advance) / installments`. Computed, read-only. Mutation-critical.

## 2. SQLAlchemy 2.0 models (`offer/infrastructure/models/`)

Async-first, `mapped_column()`. Tabla prefix `offer_service_*`. Engine `products` table NO se toca.

| Tabla | Cols clave | Index |
|---|---|---|
| `offer_service_ext` | `id PK`, `tenant_id` (idx), `offer_id` (FK products.id, unique idx), `modality`, `is_active`, `canonical_service_ref`, `category`, `clinic_scope`, ficha (JSONB para los campos texto largos opcional · o columnas), `session_interval JSONB`, `recurrence_interval JSONB`, `initial_appt_duration_minutes`, `initial_appt_type`, `pricing JSONB` (ThreeChargePricing serializado), `variants JSONB`, `candidate_for_library`, `created_at TIMESTAMPTZ`, `updated_at`, `deleted_at` | `ix_offer_service_ext_tenant (tenant_id)`, `ix_offer_service_ext_offer (offer_id) UNIQUE` |
| `offer_service_specialist_links` | `id PK`, `tenant_id` (idx), `offer_id` (FK), `doctor_id` (FK vitalia_doctors), `created_at`, `deleted_at` | `ix...tenant (tenant_id)`, `ix...offer (offer_id)`, unique `(offer_id, doctor_id)` partial WHERE deleted_at IS NULL |
| `offer_service_cases` | `id PK`, `tenant_id` (idx), `offer_id`, `before_asset_url`, `after_asset_url`, `consent_signed`, `consent_ref`, `deleted_at` | `ix...tenant` |
| `offer_service_testimonials` | `id PK`, `tenant_id` (idx), `offer_id`, `rating`, `text`, `author`, `source`, `deleted_at` | `ix...tenant` |

SalesBrief: o tabla `offer_service_sales_brief` (1:1 offer · JSONB para faq/objections/keywords) **o** write-through a campos engine + tabla brand para lo que no cabe (D-2). Builder decide forma exacta; default = tabla brand `offer_service_sales_brief` (1:1) + service hace el write-through al engine Offer al guardar.

## 3. Pydantic v2 DTOs (`offer/api/dtos.py`)
`model_config = ConfigDict(from_attributes=True)`. Sin `Any`. Monetary con `currency: str | None`. Ejemplos:
- `ServiceListItemDTO` (catálogo card): `id, public_name, category, value_level, is_active, canonical_service_ref (→origin chip), specialist_count, completeness_filled, completeness_total, duration_minutes, price, currency, price_mode`.
- `ServiceDetailDTO` (workspace): offer-core engine fields + OfferExt + SalesBrief + specialists + cases + testimonials + completeness + pricing (with derived computed).
- `ServiceCreateFromTemplateRequest` (`canonical_service_ref`), `ServiceCreateCustomRequest`, `ServicePatchRequest` (autosave por campo · partial), `SpecialistLinkRequest` (`doctor_id`), `CaseCreateRequest` (`consent_signed` MUST true), `TestimonialCreateRequest`, `BibliotecaSearchResponse` (typeahead).
- Response models con `response_model=` en TODA ruta (PII allowlist).

## 4. API routes (`offer/api/servicios_router.py`)
Under `/api/v1/offer/servicios/...`. Bearer + `X-Tenant-ID`. `redirect_slashes=False` (main set). RBAC RN-7.

| Method | Path | Auth/RBAC | Request DTO | response_model | Desc |
|---|---|---|---|---|---|
| GET | `/api/v1/offer/servicios` | Bearer+tenant · all roles read | query (search,category,active,origin,cursor) | `ServiceListResponse` | catálogo + filtros (RN-15, cursor) |
| GET | `/api/v1/offer/servicios/{offer_id}` | read | — | `ServiceDetailDTO` | workspace |
| POST | `/api/v1/offer/servicios/from-template` | admin/owner | `ServiceCreateFromTemplateRequest` | `ServiceDetailDTO` | crea Offer engine + OfferExt (canonical_ref · RN-16/25) |
| POST | `/api/v1/offer/servicios/custom` | admin/owner | `ServiceCreateCustomRequest` | `ServiceDetailDTO` | personalizado (canonical_ref=null) |
| PATCH | `/api/v1/offer/servicios/{offer_id}` | admin/owner | `ServicePatchRequest` | `ServiceDetailDTO` | autosave por campo (RN-20) |
| POST | `/api/v1/offer/servicios/{offer_id}/activate` | admin/owner | `{is_active:bool}` | `ServiceDetailDTO` | toggle Activo (RN-10) |
| DELETE | `/api/v1/offer/servicios/{offer_id}` | admin/owner | — | `204` | soft-delete (RN-edge) |
| GET | `/api/v1/offer/biblioteca/search?q=` | read | — | `BibliotecaSearchResponse` | typeahead nombre+sinónimos (RN-25/AC-18) |
| POST | `/api/v1/offer/servicios/{offer_id}/specialists` | admin/owner | `SpecialistLinkRequest` | `SpecialistLinkDTO` | vincular (autosave · RN-20) |
| DELETE | `/api/v1/offer/servicios/{offer_id}/specialists/{doctor_id}` | admin/owner | — | `204` | desvincular |
| POST | `/api/v1/offer/servicios/{offer_id}/cases` | admin/owner | `CaseCreateRequest` (consent MUST) | `CaseDTO` | HIPAA-lite consent gate + audit_log |
| DELETE | `/api/v1/offer/servicios/{offer_id}/cases/{id}` | admin/owner | — | `204` | quitar caso |
| POST | `/api/v1/offer/servicios/{offer_id}/testimonials` | admin/owner | `TestimonialCreateRequest` | `TestimonialDTO` | testimonio manual |
| DELETE | `/api/v1/offer/servicios/{offer_id}/testimonials/{id}` | admin/owner | — | `204` | quitar |
| PATCH | `/api/v1/offer/servicios/{offer_id}/sales-brief` | admin/owner | `SalesBriefPatchRequest` | `SalesBriefDTO` | argumentario (autosave) + write-through engine |
| POST | `/api/v1/offer/servicios/{offer_id}/knowledge/extract` | admin/owner | upload (file/url) | `KnowledgeSourceDTO` + `ExtractionPrefillDTO` | document→autocomplete (consume copilot extract_from_doc · AC-11 · NOT RAG) |

> **Idempotency:** create endpoints crean on-choose (RN-16 sin borradores fantasma) — no dedup key necesario (el draft es explícito al elegir template/custom). PATCH autosave idempotente (last-write-wins por campo). Specialist link unique `(offer_id, doctor_id)` partial → re-vincular es no-op idempotente.

## 5. Repository interfaces (`offer/application/ports/` + `infrastructure/repositories/`)
ABC, async, `tenant_id` en CADA método (incl `get_by_id`):
- `OfferServiceExtRepository` (async): `get_by_offer_id(tenant_id, offer_id)`, `list_by_tenant(tenant_id, filters, cursor)`, `create`, `update`, `soft_delete`.
- `ServiceSpecialistLinkRepository` (async): `list_by_offer(tenant_id, offer_id)`, `link`, `unlink`.
- `CaseRepository` (async · **hereda `PhiRepositoryBase`** por PHI foto): `list_by_offer(tenant_id, offer_id)`, `create` (consent gate), `soft_delete`. Single tenant-filter OK (no dual clinic salvo multi-clínica).
- `TestimonialRepository`, `SalesBriefRepository` (async).
- `OfferEnginePort` (ABC, application): `create_service_offer(tenant_id, ...) -> offer_id`, `update_service_offer(...)`, `list_service_offers(tenant_id)`, `get(tenant_id, offer_id)`. Impl en `infrastructure/` wraps `get_offer_repository(db)` (engine sync repo). **D-1 wrapping pattern:** el builder confirma sync-session-scoped vs run_sync; el engine repo no es hot-path. NO romper el consume sync de `TenantKnowledgeBuilder`.
- `DoctorRosterPort` (ABC): `list_doctors(tenant_id)`, `get_doctor(tenant_id, doctor_id)` — impl wraps `clinics` `DoctorService` (cross-module via port, NO raw import · backend-ddd).
- `BrandVoicePort` (ABC): `draft_description(tenant_id, raw) -> str` — impl consume lisa-marca voz (knowledge_builder.build_brand_voice / brand-studio). NO mirror de voz.
- `DocExtractPort` (ABC): `extract_from_document(tenant_id, file_or_url) -> ExtractionPrefill` — impl consume copilot `extract_from_doc` (engine). One-shot, NOT RAG.

## 6. Application services (`offer/application/services/`)
- `ServiceCatalogService` — CRUD (create = engine Offer + OfferExt en una unit-of-work brand; el engine create + brand insert; rollback coherente), search/filtros server-side, autosave-patch, activate toggle, soft-delete. Emite `vitalia_growth_studio_event` best-effort.
- `BibliotecaService` — typeahead sobre EP-2 preset pack (nombre+sinónimos, scoped al tipo de clínica del tenant). "Usar plantilla" → draft Offer+OfferExt pre-llenado con canonical_ref + campos contenido ✨. "Crear personalizado" → canonical_ref=null.
- `SpecialistLinkService` — link/unlink vía DoctorRosterPort.
- `DocumentAutocompleteService` — DocExtractPort → prefill editable + crea `KnowledgeSource` engine row (status extraído; indexer stub OK Sub-phase A).
- `SalesBriefService` — CRUD + write-through a campos engine Offer existentes (D-2 · builder confirma mapeo).
- `ProofService` — Case (consent gate + audit_log sync write HIPAA-lite) + Testimonial CRUD.
- Transaction boundaries: el create de servicio es la única multi-write (engine Offer + brand OfferExt) → application orquesta + rollback. Resto single-aggregate.

## 7. EP-2 preset pack (`extensions.py::register_all` · MODIFY)
Reemplazar el stub:
```python
registry.offer_preset_pack_register(
    PresetPack(
        name=_ns("medical_services_v1"),
        presets=(  # ← biblioteca seed dental + estética Tier-1 (Lisa-generated + curado)
            {"canonical_ref": "diseno_de_sonrisa", "name": "Diseño de sonrisa", "synonyms": ["fundas","carillas premium"],
             "category": "Estética dental", "value_level": "transformacion", "modality": "sesiones",
             "procedure_steps": "...", "risks": "...", "faq": [...], "keywords": [...]},
            {"canonical_ref": "carillas_porcelana", "name": "Carillas de porcelana", "synonyms": ["fundas","carillas"], ...},
            {"canonical_ref": "botox_facial", "name": "Botox facial", "synonyms": ["toxina botulínica","bótox"],
             "category": "Medicina estética", "value_level": "activacion", "modality": "recurrente", ...},
            # ... dental + estética Tier-1 ...
        ),
        applies_to_brand=_BRAND_SLUG,
        description="Vitalia medical services library (dental + estética Tier-1)",
    ),
)
```
`presets` = tuple de dicts (validados por offer core). NO toca `core/luana-core-offer-studio` catalog (no bump `_CATALOG_VERSION` — es brand preset pack). El typeahead nombre+sinónimos lee este pack vía `BibliotecaService`.

## 8. Tenant isolation + RBAC + HIPAA-lite
- TODA query `.where(Model.tenant_id == tenant_id)` (incl get_by_id). Cross-tenant → 404, no leak.
- RBAC `@require_role(["admin_clinic","owner"])` en write endpoints; resto 403.
- `Case` → consent_signed MUST true (RN-33) + `write_audit_log_sync` pre-response (HIPAA-lite). `CaseRepository` hereda `PhiRepositoryBase`.
- Catálogo NO PHI (RN-13) → resto de repos NO heredan PhiRepositoryBase.

## 9. Tests (TDD RED-first · `vitalia/backend/tests/modules/vitalia/offer/`)
- `test_pricing_calc.py` — derived calc (3-charge) · mutation-critical.
- `test_completeness.py` — 26 must-have · is_active NUNCA bloqueado (AC-19) · mutation-critical.
- `test_offer_ext_repository.py` — tenant-scoped (dual-tenant: tenant A no ve tenant B → 404).
- `test_catalog_service.py` — create = engine Offer + OfferExt; activate; soft-delete; search filtros.
- `test_biblioteca_service.py` — typeahead nombre+sinónimo ("fundas"→"Carillas"); scoped al tipo clínica.
- `test_specialist_link_service.py` — link/unlink vía roster port; vincular no crea doctor.
- `test_servicios_rbac.py` — admin/owner write OK; doctor/staff write → 403.
- `test_servicios_cross_tenant.py` — cross-tenant 404; cross-clinic (cases) bloqueado.
- `test_case_consent_gate.py` — consent=false → bloqueado; consent=true → audit_log row.
- `test_keystone_offer_shape.py` — Offer activo creado por el service aparece en `OfferRepository.get_all_by_tenant` con status active (KEYSTONE data shape · AC-6 BE side).
- Arch fitness EXTEND: `test_response_model_required` (todas las rutas), DDD boundaries (offer no importa engine domain directo).
