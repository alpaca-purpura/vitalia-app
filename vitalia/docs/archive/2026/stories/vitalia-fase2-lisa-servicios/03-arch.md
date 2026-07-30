---
story_id: vitalia-fase2-lisa-servicios
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
architect_run_on: 2026-06-15
autonomous_mode: true          # Sub-phase A only (Chris opt-in); Sub-phase B gated by /pm-luana
cap_target: lisa.servicios
cap_change_type: new
---

# Contract: vitalia-fase2-lisa-servicios — Catálogo de servicios de Lisa (agente-first)

> **SSoT del ready package.** Consolida BE (net-new `offer` module) + FE (features/lisa/servicios) +
> AGENTIC-consume (keystone, CERO engine edit). Per-surface splits: `03-arch-be.md` · `03-arch-fe.md` ·
> `03-arch-agentic.md`. **Faseado HARD (Chris):** Sub-phase A (NO-RAG, autónomo a live-verified) ·
> Sub-phase B (RAG · engine-lift `/pm-luana` · GATED, dimensionado NO buildable).

---

## § 0 — Context Summary

- **Story:** F2-S9 `vitalia-fase2-lisa-servicios`. Cap `lisa.servicios` (`cap_change_type: new`).
- **Architect run on:** 2026-06-15.
- **Módulos tocados:** BE net-new `vitalia/backend/src/modules/vitalia/offer/` · FE `vitalia/frontend/src/features/lisa/components/servicios/` + 1 shared primitive · `vitalia/backend/src/modules/vitalia/extensions.py` (EP-2) · `vitalia/frontend/src/lib/shell-routes.ts` (AGENT_SUBSUBTABS).
- **Knowledge cutoff disclosure:** patterns aquí (Next.js 16 App Router, RHF+Zod autosave, LangGraph consume-only, prompt-cache) están dentro del cutoff de mi modelo (enero 2026); NO se introdujo ningún pattern post-cutoff que requiriera WebSearch live (story = composición de engine + canon ya shipped). El research SoTA aplicado es el `00-research.md` (competidores, treatment-coordinator KBs) que `/pm-vitalia` ya validó 2026-06-06.

### Surface → builder → auditor mapping (PM/`/dev-team` usa esto para spawnear)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/offer/**` (net-new DDD) | `builder-backend` (workhorse) | `auditor-backend` (flagship) |
| `vitalia/backend/src/modules/vitalia/extensions.py` (EP-2 preset pack register) | `builder-backend` (workhorse) | `auditor-backend` (flagship) |
| KEYSTONE wiring (offer shape that `TenantKnowledgeBuilder` reads · consume-only data, NO engine edit, NO sales_agent runtime) | `builder-backend` (workhorse) | `auditor-backend` (flagship) |
| `vitalia/frontend/src/features/lisa/components/servicios/**` + `vitalia/frontend/src/lib/shell-routes.ts` | `builder-frontend` (workhorse) | `auditor-frontend` (flagship) |
| `vitalia/frontend/src/components/shared/NumberWithUnit.tsx` (vitalia-local shared primitive) | `builder-frontend` (workhorse) | `auditor-frontend` (flagship) |
| **Sub-phase B — RAG runtime** (`IRAGIndexerPort` Qdrant binding + sales_agent offer-knowledge retrieval tool) | **`/pm-luana` promotion gate (NOT a builder)** | n/a — `BLOCKED -> requires /pm-luana lift` |

> **No genuine agentic-runtime ticket in Sub-phase A.** The keystone (AC-6) is *consume-only*: vitalia persists active offers in the shape the engine `TenantKnowledgeBuilder` already reads (verified §0.K below). No `copilot/` or `sales_agent/` brand-extension code is written in Sub-phase A. R23 (flagship for agentic production) therefore does NOT apply to any Sub-phase A ticket. Sub-phase B is the only agentic-runtime work and it is engine-lift (escalate, do not build).

### Skills consulted (decision, not body)

- `offer-expert`: el catálogo = `Offer` de Offer Studio (engine), peldaño = `OfferValueLevel` (5 fijos: `lead_magnet·activacion·transformacion·maximizacion·corporativo`); NUNCA un `Treatment`/`LadderSlot` nuevo. Brand-level fields → OfferExt projection. EP-2 preset pack = la biblioteca estándar. CERO edit engine.
- `offer-type-preset-expert`: la biblioteca se sirve como `PresetPack(name="vitalia.medical_services_v1", presets=(...))` vía `registry.offer_preset_pack_register` en `extensions.py::register_all` (hoy stub con `presets=()` → materializar). `presets` = tuple de dicts validados por offer core; el typeahead nombre+sinónimos vive brand-level (catálogo de la biblioteca expuesto por el preset pack + un read-model brand).
- `brand-expert`: descripciones en voz de marca = consume `PersonalityProfile.system_instruction` (lisa-marca, slot 5 BRAND_VOICE) vía el extractor/redactor existente — NO mirror de voz. El tono es read-only en Servicios (tooltip "se ajusta en Lisa → Marca").
- `copilot-expert`: document→autocomplete reusa el copilot `application/tools/extract_from_doc.py` + `document_processor.py` (engine-existing). Es un one-shot extractor editable, NO RAG indexing. CERO edit engine; vitalia llama vía port.
- `sales-agent-expert`: KEYSTONE confirmado — `TenantKnowledgeBuilder.build_identity()` lee `get_offer_repository(db).get_all_by_tenant(tenant_id)` y filtra `status.value ∈ ("active","draft")`. NINGUNA plomería agéntica nueva en Sub-phase A. El tool de retrieval RAG (Sub-phase B) NO existe → engine-lift.
- `frontend-expert` + `vitalia-design-system`: el N3 se compone de `@luana/ui-kit` 0.4.1 (EntityWorkspaceLayout, EntitySubNavBar full-bleed, EntityPicker ▾, EntityInfoCard Opción B, Group/FloatingAutosaveIndicator, Select canónico, page-primitives). RichSelect YA shipped. NumberWithUnit = único net-new primitive (vitalia-local shared + lift-candidate /pm-luana, NO lift en esta story).

### CONTEXT-BRIEF source

Self-ran greps (Path B). No `CONTEXT-BRIEF.md` para esta story; el `00-research.md` (PM, ratified) + `01-spec.md` RONDA 2 (§ Mapa de campos + § Inventario) + greps de ground-truth (engine offer-studio, sales-agent knowledge_builder, ui-kit exports, clinics doctor, extensions.py) cubren §7/§8 equivalente. Evidencia en § Prior art audit.

### capability YAML + modules updates required (post-merge, Fase F.3)

- `vitalia/docs/product/capabilities/offer/lisa-servicios.yaml` — `cap_change_type: new` → bloques v3.2 (`scenarios[]` + `access` + `business_rules`). Generar con `make new-cap BRAND=vitalia MODULE=offer SLUG=lisa-servicios AREA=lisa.servicios` (HB-51, NUNCA hand-author).
- `vitalia/docs/product/modules/offer.md` — narrativa NEW module (no existía).
- Code headers `# cap: offer.lisa-servicios` (Python líneas 1-3) / `// cap: offer.lisa-servicios` (TS/TSX) en TODO archivo nuevo (G3 HARD vitalia).

### Architecture gates que deben quedar verdes (listadas, no editar allowlist sin justificar)

- `vitalia/backend/tests/architecture/test_phi_dual_filter.py` — N/A para offer (NO PHI · RN-13) salvo `Case` consent (HIPAA-lite). Ver § Cross-cutting.
- `vitalia/backend/tests/architecture/test_response_model_required.py` — todo endpoint nuevo con `response_model=`.
- `vitalia/backend/tests/architecture/test_audit_log_sync_write.py` — N/A (no-PHI writes) salvo `Case` consent gate.
- `vitalia/backend/tests/architecture/` DDD boundaries — offer module no hace cross-module import directo (clinics doctor vía port; engine offer-studio vía `luana_core_platform.links.ports.offer`).
- `vitalia/frontend/src/__tests__/architecture/test_features_no_cross_imports.test.ts` · `test_react_query_keys_convention.test.ts` · `test_no_phi_in_url_params.test.ts` · `test_no_clerk_organizations.test.ts` (tenant_id de `useTenantId()`, NUNCA orgId).
- `test_agent_subsubtabs_ssot.test.ts` — `AGENT_SUBSUBTABS["lisa.servicios"]` declarado en `shell-routes.ts` (FE arch test enforce SSoT).
- `core/luana-core-offer-studio/tests/test_catalogs_dag_smoke.py` — preset pack EP-2 NO toca engine catalog → no debe regresar (consume, no edita).
- `make ci-parity` (engine + vitalia) verde pre-merge.

### § 0 — ADR-vitalia-004 compliance map (9 secciones · `adr_004_compliance: full`)

| § ADR-004 | Cumplimiento en esta story |
|---|---|
| **3.1 Routing** | `(shell-organism)/lisa/servicios/page.tsx` (toggle Catálogo\|Escalera via N3-static) · `servicios/[offer-id]/page.tsx` (workspace N3 EntitySubNavBar 5 leaves) · `servicios/nuevo/page.tsx` (picker biblioteca inline → crea borrador → redirect a `[offer-id]`). Server Components default; `getServiciosInitialState`/`getServicioWorkspaceState` SSR. PHI nunca en URL (catálogo no es PHI; offer-id es UUID no-PHI). `params`/`searchParams` async (Promise). |
| **3.1.1 N3-static** | `AGENT_SUBSUBTABS["lisa.servicios"] = [catalogo, escalera]` (NO Shadcn Tabs internas). Routing `lisa/servicios/[subsubtab]/page.tsx`. El workspace `[offer-id]` usa `EntitySubNavBar` (N3 list/detail, NO N3-static). |
| **3.2 FSD-Lite** | `features/lisa/components/servicios/` + `api/servicios.ts` + `api/servicios-server.ts` + `hooks/` + `store/` + `types/servicios.types.ts` + `types/servicios-schema.ts`. NumberWithUnit (genérico) → `components/shared/` (no feature-locked). |
| **3.3 Client root** | `LisaServiciosView.tsx` (`"use client"` línea 1) hidrata React Query con `initialData`. `ServicioWorkspaceView.tsx` idem. |
| **3.4 Data layer** | React Query (server data: catálogo, workspace, biblioteca typeahead) + Zustand (UI: filtros, picker open, autosave dirty-state) + URL state (`?view=`). NO Redux/Context. Keys `[offer, servicios, ...]`. |
| **3.5 Forms** | RHF + Zod (`servicios-schema.ts` con discriminated union por `modality`). **Autosave debounce 600ms** (RN-20 — sin botón Guardar) via `use-autosave` (canon §2.6) + UNA `FloatingAutosaveIndicator`. Toggles (Activo) y "Descartar borrador" = acciones de estado, no autosave. |
| **3.6 BE DDD** | Inside-Out: `domain/` (OfferExt aggregate + VOs) → `infrastructure/` (SQLA 2.0 async models + repos + migrations) → `application/` (services + ports) → `api/` (routers thin, `response_model=`). Offer no-PHI → repos NO heredan `PhiRepositoryBase` (salvo `CaseRepository` por consentimiento HIPAA-lite). RBAC RN-7 (`admin_clinic`+`owner` edita). |
| **3.7 Migrations** | Raw SQL idempotente (`CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`). NUNCA `op.create_table()` / `sa.Enum(create_type=True)`. Enums vía `CREATE TYPE IF NOT EXISTS` raw o `String` + CHECK. |
| **3.8 Telemetría** | `vitalia_growth_studio_event` (NO `copilot_trace_event`). Events `lisa_servicios_*` (viewed, item_created, item_saved, filter_applied, error). Bucketed amounts (precio NUNCA verbatim). Emitter `_shared/telemetry/`. |
| **3.9 Tests** | Vitest unit (componentes + hooks) · Playwright funcional real-backend (auth fixture) · Playwright visual golden 4 mockups × light/dark = 8 PNGs (maxDiffPixelRatio 0.001 · ADR-003) · axe a11y · BE pytest dual-tenant + service + repo · arch fitness EXTEND. |

**Divergencias del ADR:** ninguna (`full`). Una decisión que el ADR NO contempla pero NO diverge: la persistencia del Offer se hace en el **engine `ProductModel`/`OfferRepository`** (no una tabla brand nueva para el Offer-core) porque el keystone lee de ahí — ver § BE arch · Decisión D-1. Esto es *consumir* el engine, no editarlo. El `OfferExt` brand-level (todo lo que el engine no tiene) SÍ es una tabla brand nueva con repo async, coherente con ADR-004 §3.6.

---

## § Prior art audit (NO-NEW-LAYER · anti-duplication)

### Source of evidence
- [x] Self-run greps (Path B — fallback)
- [ ] CONTEXT-BRIEF.md § 7 + § 8 (no existe para esta story)

### Audit cross-module ejecutado (greps verbatim 2026-06-15)

```bash
WS=/home/chalreme/Proyectos/luana-vitalia
# 1. offer module no existe en vitalia
ls -d $WS/vitalia/backend/src/modules/vitalia/offer   → No existe (net-new FROM SCRATCH)
# 2. engine offer-studio domain
ls $WS/core/luana-core-offer-studio/.../domain/  → offer.py, enums.py, details.py, value_level_catalog.py, knowledge_source.py, offer_ladder_hints.py, ...
grep "OfferValueLevel" enums.py  → lead_magnet·activacion·transformacion·maximizacion·corporativo (5 fijos)
# 3. keystone read path
grep "get_all_by_tenant\|status.value in" knowledge_builder.py  → reads get_offer_repository(db).get_all_by_tenant; filters active+draft
# 4. RichSelect / NumberWithUnit
ls $WS/core/@luana/ui-kit/src/rich-select.tsx  → SHIPPED (RichSelectOption {value,label?,description?})
grep -rln NumberWithUnit ui-kit/src vitalia/frontend/src  → 0 matches (genuinely net-new)
# 5. clinics doctor roster
ls .../clinics/domain/doctor.py + application/doctor_service.py  → SHIPPED (lisa-doctores)
# 6. cross-brand mirror check (comunify offer)
ls $WS/comunify/backend/.../offer_ladder_repository.py  → SHIPPED (creator vertical, distinct domain)
# 7. IRAGIndexerPort + extract_from_doc + KnowledgeSource
grep IRAGIndexerPort ports.py  → ABC with STUB default binding (marks indexed synthetic chunk count)
ls copilot/.../tools/extract_from_doc.py  → SHIPPED
grep "class KnowledgeSource" knowledge_source.py  → SHIPPED (tenant_id, offer_id, status, qdrant fields)
```

### Sistemas existentes encontrados

| Sistema | Path | Enum/Config | Factory/Router | Providers/Adapters | Estado | Decisión |
|---|---|---|---|---|---|---|
| Offer Studio engine | `core/luana-core-offer-studio/.../domain/offer.py` (Offer aggregate · ProductModel `products` table) | `OfferValueLevel`, `OfferStatus`, `OfferArchetype` | `OfferRepository` (sync Session: create/update/get_all_by_tenant/list_active/search/soft_delete) | — | active | **CONSUME vía import** (`luana_core_platform.links.ports.offer.get_offer_repository`). Persistir el Offer-core como `ProductModel` row. CERO edit. |
| TenantKnowledgeBuilder | `core/luana-core-sales-agent/.../knowledge_builder.py` | — | — | — | active | **CONSUME (keystone)** — diseñar offer persistence para que `get_all_by_tenant` + `status active/draft` lo recoja. CERO plomería nueva. |
| RichSelect | `core/@luana/ui-kit/src/rich-select.tsx` | `RichSelectOption {value,label?,description?}` | — | — | active | **CONSUME** (RN-32 "Tipo de cita inicial"). NO recrear. |
| Entity* + page-primitives | `@luana/ui-kit` 0.4.1 (EntityWorkspaceLayout, EntitySubNavBar, EntityPicker, EntityInfoCard, Group, FloatingAutosaveIndicator, Select, layout/, archetypes/) | — | — | — | active | **CONSUME** (canon §2). ❌ `<select>` nativo, ❌ arbitrary values. |
| copilot extract_from_doc | `core/luana-core-copilot/.../tools/extract_from_doc.py` + `services/document_processor.py` | — | — | — | active | **CONSUME** (document→autocomplete AC-11). One-shot extractor, NOT RAG. CERO edit. |
| KnowledgeSource engine | `core/luana-core-offer-studio/.../domain/knowledge_source.py` + `api/knowledge.py` + `services/offer_knowledge_service.py` + `infrastructure/repositories/knowledge_source_repository.py` | `KnowledgeSourceType`, `KnowledgeSourceStatus` | — | `IRAGIndexerPort` (ABC · STUB default binding) | active (RAG runtime = stub) | **CONSUME** the per-offer KnowledgeSource + upload api. Sub-phase A: extract-only (stub indexer OK). Sub-phase B: real Qdrant binding = engine-lift. |
| clinics Doctor roster | `vitalia/.../clinics/domain/doctor.py` + `application/doctor_service.py` + `doctor_repository.py` | — | `DoctorService` (async) | — | active | **EXTEND via port** — `ServiceSpecialistLink` FK → `vitalia_doctors`. Cross-module read vía port/interface (backend-ddd), NO raw import. |
| lisa-marca voz | `core/luana-core-brand-studio` PersonalityProfile + `core/luana-core-sales-agent` knowledge_builder.build_brand_voice | — | — | — | active | **CONSUME** voz para descripciones. NO mirror de voz. |
| comunify offer_ladder | `comunify/backend/.../offer_ladder_repository.py` (+ model + service + dtos) | — | — | — | active (otra brand) | **STUDY as prior-art template** for brand-level offer persistence shape (NOT a lift — creator vs clinical). Documentar shape (repo async + value_level grouping) en § BE arch. NO cross-brand import. |

### Decisión por sistema (EXTEND > REPLACE > NEW)

- **Offer Studio engine (engine):** CONSUME. El catálogo + escalera + value_level + el read del agente YA viven en el engine. NEW seria mirror = bug.
- **RichSelect, Entity*, page-primitives, FloatingAutosaveIndicator, Select (ui-kit):** CONSUME. NO recrear.
- **clinics Doctor roster (brand):** EXTEND via port. `ServiceSpecialistLink` FK → roster existente; no se duplica el roster.
- **lisa-marca voz (brand):** CONSUME. Descripciones en voz de marca via knowledge_builder, NO mirror.
- **copilot extract_from_doc + KnowledgeSource (engine):** CONSUME. Document→autocomplete + per-offer knowledge source ya existen.
- **comunify offer_ladder (otra brand):** STUDY only. NO lift (dominio distinto). Si una 3ra brand pidiera el mismo "catálogo clínico sobre Offer Studio" → escalar `/pm-luana`.

### NEW justificado — "por qué los existentes no sirven" (código real referenciado)

| NEW | Por qué el existente no sirve | Hogar | Lift-candidate? |
|---|---|---|---|
| `vitalia/backend/src/modules/vitalia/offer/` (módulo brand-level entero) | El engine `Offer` persiste el offer-core (`products` table) pero NO tiene: `canonical_service_ref` (grep: 0 matches), los 3 cobros separados (reserva/anticipo/financiamiento), `SalesBrief` (argumentario Para Adrián), `ServiceSpecialistLink`, `modality` brand enum, `variants[]` estructuradas, la ficha paciente (riesgos/procedimiento/cuidados), `Case`/`Testimonial` manuales, completitud. Editar el engine = `/pm-luana` (prohibido en esta story). → tabla(s) brand `OfferExt` que proyecta sobre el `products.id`. | brand vitalia | NO (clínico-específico) |
| `OfferExt` aggregate + 3-charge pricing VO + `SalesBrief` + `ServiceSpecialistLink` + `Case`/`Testimonial` | Idem — son los campos brand que el engine no tiene. | brand vitalia | NO |
| `vitalia/frontend/src/components/shared/NumberWithUnit.tsx` | grep `NumberWithUnit` en ui-kit + vitalia/frontend = 0 matches. Genuinamente net-new (number + unidad fija o selector de unidad). | vitalia-local shared (reusable cross-feature) | **SÍ — `/pm-luana` lift-candidate a `@luana/ui-kit`** (documentado, NO se liftea en esta story — lift = engine promotion gate = rompe autonomía; un solo stop /pm-luana ya alcanza para Sub-phase B RAG) |
| Componentes feature-local: `ModalidadPicker`, `RungPicker`, `VariantsRepeater`, `TestimonialsList`, `FaqPairList`, `ObjecionPairList`, `TagInput`, `FichaCompletenessChip`, `ServiceStatusBar`, `BibliotecaPicker`, `EspecialistaLinkPicker`, `KnowledgeSourcesPanel`, `chip-origen` (Badge variant) | No existen equivalentes en ui-kit (composiciones de dominio servicios). `OptionCardGroup` (generalización de `ModalidadPicker`) = feature-local now, lift-candidate futuro. | `features/lisa/components/servicios/` | `OptionCardGroup` + `RichSelect` (ya shipped) — solo nota |

> **Anti-orphan / cross-brand:** no se detectó mirror cross-brand de "catálogo clínico". `comunify/offer_ladder` es dominio creator distinto → STUDY, no lift. NumberWithUnit lift se difiere (decisión Chris delegada a /architect: vitalia-local + lift-candidate documentado).

---

## § BE arch — net-new `offer` module (DDD Inside-Out)

> Owner: `builder-backend`. Auditor: `auditor-backend`. Detalle entidades/modelos/DTOs/rutas en `03-arch-be.md`.

### Decisión D-1 (CRÍTICA) — dónde persiste el Offer-core vs el OfferExt brand

El keystone (AC-6) lee así (verificado en `knowledge_builder.py`):
```python
offer_repo = get_offer_repository(db)              # luana_core_platform.links.ports.offer
offers = offer_repo.get_all_by_tenant(tenant_id)   # engine OfferRepository (sync Session)
active = [o for o in offers if o.status.value in ("active", "draft")]
```
**Decisión:** el **offer-core** (lo que el agente necesita: `public_name`, `description`, `value_level`, `status`, `archetype=SERVICIO`, `specific_details=ServiceDetails(session_duration_minutes,total_sessions_count)`, `preset_id`, pricing engine) se persiste como **engine `ProductModel` row** (tabla `products`) vía el engine `OfferRepository.create/update`. Así el keystone funciona con CERO plomería — esto es *consumir* el engine, no editarlo.

El **OfferExt brand-level** (todo lo que el engine NO tiene) se persiste en tablas brand nuevas (`offer_service_ext`, `offer_service_specialist_links`, `offer_service_cases`, `offer_service_testimonials`) con FK `offer_id` → `products.id`. Repos brand **async** (`AsyncSession`, ADR-004 §3.6). El `OfferExt` se hidrata join-en-application (NO SQL JOIN cross-module — se resuelve por `offer_id` en el service layer, backend-ddd §Cross-module).

**Por qué NO mirror del Offer en brand:** mirror obligaría a sincronizar dos SSoT y el agente no lo leería → el keystone se rompería. La regla `anti-duplication` manda CONSUME.

**Cómo el service escribe el engine (sin import directo prohibido):** vía el port `luana_core_platform.links.ports.offer.get_offer_repository(db)`. El engine `OfferRepository` es **sync `Session`**; el service brand es async. El service usa un `OfferEnginePort` (interface brand en `application/ports/`) cuya impl envuelve el engine repo y corre el call sync dentro del request async (el engine repo no es hot-path; un wrapper `run_sync`/sync session dedicada es aceptable · documentar en `03-arch-be.md` el patrón exacto — el builder confirma si la sesión async puede compartir engine sync repo o usa una sync session scoped). Esto es coherente con cómo `TenantKnowledgeBuilder` (sync) ya lo consume.

### Domain (`offer/domain/`)
- `OfferExt` aggregate (brand projection) — `id`, `tenant_id` (MANDATORY), `offer_id` (FK→products.id), `clinic_scope: UUID | None` (RN-12), `category: str | None`, `canonical_service_ref: str | None` (null=personalizado · RN-25/30), `is_active: bool`, `modality: ServiceModality`, ficha paciente (procedure_steps, anesthesia_pain, prep, aftercare, downtime, risks, red_flags, expected_result, result_timing, result_lifespan, realistic_expectations, includes, excludes, warranty, description_long), `session_interval`/`recurrence_interval` (ValueWithUnit VO), `initial_appt_duration_minutes: int | None`, `initial_appt_type: InitialApptType` (enum 3 fijo · RN-32), `variants: list[ServiceVariant]`, `candidate_for_library: bool` (RN-27), `created_at`, `updated_at`, `deleted_at` (MANDATORY soft-delete).
- `ServiceModality` enum: `unica | sesiones | recurrente` (RN-28).
- `InitialApptType` enum (3 fijo · RN-32): `valoracion_diagnostico | primera_sesion_directa | consulta_informativa_gratuita`.
- `ServiceVariant` VO: `name: str`, `price: Decimal`, `note: str | None` (RN-29).
- `ValueWithUnit` VO: `value: int`, `unit: IntervalUnit` (`dias|semanas|meses|anios`) (RN-31).
- `ThreeChargePricing` VO (RN-6 · 3 cobros independientes): `price: Decimal | None`, `price_mode: PriceMode (fijo|rango)`, `price_publishable: bool`, `reservation: ReservationConfig | None` (monto/% que apartar el turno, se descuenta), `advance: AdvanceConfig | None` (% o monto del total para iniciar), `financing: FinancingConfig | None` (cuotas N + interés/MSI). **Montos derivados (≈equivale a, ≈por mes) son `Computed`, NO se persisten.** `currency` viene de `tenant_locale` (NUNCA hardcode · RN-3).
- `SalesBrief` aggregate/VO (Para Adrián · lo lee TenantKnowledgeBuilder indirecto — ver D-2): `candidate_ideal`, `contraindications`, `qualification_questions`, `escalation_conditions`, `requires_evaluation: bool`, `emotional_benefits`, `pain_of_not_treating`, `differentiators`, `promos`, `faq: list[FaqPair]`, `objections: list[ObjectionPair]`, `keywords: list[str]`, `problems_solved`, `language_to_avoid`.
- `ServiceSpecialistLink` entity: `id`, `tenant_id`, `offer_id`, `doctor_id` (FK→vitalia_doctors), `created_at`, `deleted_at`.
- `Case` entity (HIPAA-lite): `id`, `tenant_id`, `offer_id`, `before_asset_url`, `after_asset_url`, `consent_signed: bool` (gate RN-33), `consent_ref`, `deleted_at`. **Consent gate → escribe audit_log (HIPAA-lite).**
- `Testimonial` entity: `id`, `tenant_id`, `offer_id`, `rating: int`, `text`, `author`, `source`, `deleted_at`.
- `completeness` computation (pure fn `domain/completeness.py`): cuenta los 26 must-have del § MVP → `(filled, total, missing[])`. **NUNCA bloquea `is_active`** (AC-19). **Mutation-critical** (mutation gate hard).

### Decisión D-2 — SalesBrief: ¿cómo lo lee Adrián?
El engine `TenantKnowledgeBuilder` lee `Offer.model_dump()` del engine. Los campos del `SalesBrief` NO caben en el engine `Offer` sin editar el engine. **Opción A (Sub-phase A, elegida):** el `SalesBrief` se proyecta a campos del engine `Offer` que YA existen y que el agente ya lee — `Offer` tiene `headline_promise`, `primary_outcome`, `anti_avatar_keywords`, `objection_handlers` (verificar nombres exactos en build), `target_avatar_match`, `prerequisites`. El service mapea SalesBrief→esos campos engine al guardar (write-through). Lo que NO mapea a un campo engine existente (FAQ pairs, escalation_conditions, keywords/sinónimos para match) queda en `OfferExt`/`SalesBrief` brand y lo consume **canal-inbound** (fuera de scope · § Matriz). **El builder confirma en `03-arch-be.md` el mapeo exacto SalesBrief→campos engine existentes** (grep `Offer` fields: `objection_handlers`, `anti_avatar_keywords`, `headline_promise`, `primary_outcome`). Si un campo crítico no tiene hogar engine → queda brand y el keystone lo cubre solo parcialmente (documentado, NO bloquea AC-6 que es "el servicio aparece + Adrián lo cita/ofrece").

### Infrastructure (`offer/infrastructure/`)
- SQLA 2.0 async models: `OfferServiceExtModel` (`offer_service_ext`), `ServiceSpecialistLinkModel` (`offer_service_specialist_links`), `OfferServiceCaseModel` (`offer_service_cases`), `OfferServiceTestimonialModel` (`offer_service_testimonials`). Todos con `tenant_id` index + `deleted_at`. `mapped_column()` syntax. Tabla prefix `offer_service_*` (módulo `offer`, entidad plural).
- Repos async (`AsyncSession`), tenant_id filter en TODA query (incl. `get_by_id`). `OfferServiceExtRepository`, `ServiceSpecialistLinkRepository`, `CaseRepository` (hereda `PhiRepositoryBase` por consent HIPAA-lite — single-filter tenant OK, no dual clinic salvo multi-clínica), `TestimonialRepository`.
- `OfferEnginePort` impl: wraps `get_offer_repository(db)` para create/update/list del Offer-core engine.
- Migrations idempotentes raw SQL (un archivo `XXXX_offer_service_tables.py`).

### Application (`offer/application/`)
- `ServiceCatalogService`: CRUD servicios (crea Offer engine + OfferExt brand en una transacción de application), search+filtros (RN-15, server-side · paginación cursor RN-15 grande), autosave-patch (campo→persist, RN-20), toggle Activo, soft-delete.
- `BibliotecaService`: typeahead nombre+sinónimos sobre el preset pack EP-2 (RN-25 · AC-18), scoped al tipo de clínica del tenant; "Usar plantilla" pre-llena (devuelve un draft Offer+OfferExt con `canonical_service_ref` set, campos de contenido ✨); "Crear personalizado" (canonical_service_ref=null).
- `SpecialistLinkService`: vincular/desvincular (consume `clinics` doctor roster vía port; NO crea doctores).
- `DocumentAutocompleteService`: consume copilot `extract_from_doc` port (one-shot, editable prefill · AC-11). NO indexa RAG (eso es Sub-phase B). Crea `KnowledgeSource` engine row con status extraído.
- `SalesBriefService`: CRUD del argumentario + write-through a campos engine (D-2).
- `ProofService`: Case (consent gate HIPAA-lite + audit_log) + Testimonial CRUD.
- `ports/`: `OfferEnginePort`, `DoctorRosterPort` (clinics), `BrandVoicePort` (descripción voz de marca), `DocExtractPort` (copilot).

### API (`offer/api/`)
- `servicios_router.py` (under `/api/v1/offer/servicios/...`). FastAPI `redirect_slashes=False` (brand main ya set). Bearer + `X-Tenant-ID` mandatory. `response_model=` en TODA ruta. RBAC RN-7 (`admin_clinic`+`owner` write; resto read-only → 403).
- DTOs Pydantic v2 (`api/dtos.py`): `ConfigDict(from_attributes=True)`, sin `Any`. Monetary fields con `currency: str | None`.
- Idempotency: el draft-create (RN-16 "+ Nuevo servicio") usa natural-key dedup (`tenant_id` + draft session) o crea on-choose (el borrador recién se crea al elegir plantilla/personalizado — RN-16 "sin borradores fantasma"). PATCH autosave es idempotente por naturaleza (last-write-wins por campo).

### EP-2 preset pack (`extensions.py::register_all`)
Materializar el stub `PresetPack(name="vitalia.medical_services_v1", presets=())` → `presets=(...)` con la **biblioteca seed dental + estética Tier-1** (contenido generado por Lisa + curado). El typeahead nombre+sinónimos lee este pack. Coherente con `offer-type-preset-expert`: bump no aplica (es brand preset pack, no engine catalog). NO toca `core/luana-core-offer-studio`.

---

## § FE arch — `features/lisa/components/servicios/`

> Owner: `builder-frontend`. Auditor: `auditor-frontend`. Detalle component tree + props + schemas en `03-arch-fe.md`.

### Routing (ADR-004 §3.1 + §3.1.1)
- `app/[tenantId]/(shell-organism)/lisa/servicios/page.tsx` → redirect a `/lisa/servicios/catalogo` (default leaf via N3-static). Server Component.
- `lisa/servicios/[subsubtab]/page.tsx` (subsubtab ∈ `catalogo|escalera`) → `LisaServiciosView initialView`. N3-static. Persiste `?view=` opcional (el subsubtab es el SSoT del toggle).
- `lisa/servicios/[offer-id]/page.tsx` → workspace `EntityWorkspaceLayout` (5 leaves). N3 list/detail. `[offer-id]` UUID no-PHI.
- `lisa/servicios/nuevo/page.tsx` → picker biblioteca inline (NO modal). Al elegir → crea borrador → `router.replace` a `[offer-id]`.
- **`shell-routes.ts` EDIT:** `AGENT_SUBSUBTABS["lisa.servicios"] = [{id:"catalogo",label:"Catálogo",icon:"📋"},{id:"escalera",label:"Escalera",icon:"🪜"}]` + `N3_DEFAULT_LEAF` entry `^/{uuid}/lisa/servicios/?$ → catalogo`. (arch test `test_agent_subsubtabs_ssot` enforce.)

### Data layer (ADR-004 §3.4)
- React Query keys: `["offer","servicios","list",filters]` · `["offer","servicios","detail",offerId]` · `["offer","biblioteca","search",q]` · `["offer","servicios","specialists",offerId]`. Mutations invalidan keys explícito.
- Zustand UI-only: `servicios-ui-store.ts` (filtros del catálogo, picker open, autosave dirty per-field). NO data fetched en Zustand.
- URL state: `?view=` (toggle es N3-static segment; `?view=` legacy back-compat opcional).

### Forms + autosave (ADR-004 §3.5 + RN-20)
- RHF + Zod en `types/servicios-schema.ts`. **Discriminated union por `modality`** (`unica` sin extra · `sesiones` → sessions+interval · `recurrente` → cadence). Precio ≥ 0 (RN-11). Numéricos tipados (RN-31).
- Autosave on-change debounce 600ms (`use-autosave` canon §2.6) → PATCH por campo. UNA `FloatingAutosaveIndicator` (sticky abajo-centro). Sin botón Guardar. "Activar"/"Descartar borrador" = acciones de estado.

### Component tree (cada § Inventario B → archivo · primitiva ui-kit que compone)
Ver `03-arch-fe.md` § component map (mapea cada componente NEW a su archivo + props + qué ui-kit primitive compone + qué mockup). Resumen:
- Organismos NEW (feature-local): `LisaServiciosView`, `ServicioWorkspaceView` (crear=editar · RN-16), `ServiciosDirectoryHeader`, `EscaleraView`+`RungColumn`, `BibliotecaPicker`, `EspecialistaLinkPicker`, `KnowledgeSourcesPanel`, `ServiceStatusBar`, 5 leaves (`ResumenView`·`ParaAdrianView`·`EspecialistasView`·`PlanPagoView`·`PruebaSocialView`).
- Moléculas NEW (feature-local): `ModalidadPicker`, `RungPicker`, `VariantsRepeater`, `TestimonialsList`, `FaqPairList`, `ObjecionPairList`, `TagInput`, `FichaCompletenessChip`.
- Átomos NEW: `chip-origen` (Badge variant), `NumberWithUnit` (**`components/shared/` — vitalia-local shared, lift-candidate**).
- CONSUME (NO recrear): `RichSelect` (RN-32 · ui-kit shipped), `EntityWorkspaceLayout`/`EntitySubNavBar`/`EntityPicker`/`EntityInfoCard`/`Group`/`FloatingAutosaveIndicator`/`Select`/page-primitives (ui-kit 0.4.1), `SubSubTabsBar` (shell-organism shipped), `@dnd-kit/core` (escalera drag + keyboard a11y), Shadcn `Tooltip` (FieldTooltip RN-18).

### Escalera (AC-3 · drag + a11y)
5 peldaños FIJOS (labels médicos sobre `OfferValueLevel`): Gancho gratuito (`lead_magnet`) · Primera visita (`activacion`) · Tratamiento principal (`transformacion`) · Premium (`maximizacion`) · Plan/convenio (`corporativo`). Layout: Gancho gratuito full-width arriba · 3 columnas medio · Plan/convenio full-width abajo. Drag mueve `value_level` (autosave). Personalizado: drag libre. Estándar: peldaño bloqueado (RN-30 · drag aplica solo a personalizados — decisión confirmada en `03-arch-fe.md`). Keyboard a11y: Space→Arrow→Space + `aria-live` (AC-8). Peldaño vacío → guía + ejemplos de la biblioteca + "crear aquí".

---

## § AGENTIC — KEYSTONE (consume-only · CERO engine edit)

> Owner: `builder-backend` (data shape, consume-only). NO `builder-agentic` en Sub-phase A. Detalle en `03-arch-agentic.md`.

### Sub-phase A — KEYSTONE wiring (AC-6, verificable LIVE)
- `TenantKnowledgeBuilder.build_identity(tenant_id)` (engine) lee `get_offer_repository(db).get_all_by_tenant` y filtra `status ∈ (active, draft)`.
- **Lo que esta story garantiza:** los servicios activos se persisten como engine `Offer`/`ProductModel` rows (D-1) con `status=active` → el agente los recoge SIN plomería nueva. `SalesBrief` write-through a campos engine existentes (D-2) → Adrián los cita.
- **Verificación LIVE (DoD #37):** activar un servicio en dev-app → query `products` (status active) → invocar Adrián / inspeccionar `build_identity` output → confirmar que el servicio aparece + se cita (leer logs). Write real ejercido. NO `GET 200`.
- **CERO engine edit · CERO sales_agent/copilot brand-extension code en Sub-phase A.**
- Document→autocomplete: consume copilot `extract_from_doc` (one-shot extractor, NOT RAG). El `IRAGIndexerPort` **stub default binding** marca la fuente como indexada con chunk count sintético → la UI del panel Fuentes funciona en Sub-phase A (estado "extraído") sin Qdrant real.

### Sub-phase B — RAG runtime (ENGINE-LIFT · `/pm-luana` · DIMENSION ONLY, NO buildable tickets)
RN-17(b) + RN-22 + AC-15(B part) + Gherkin §14 (b)+adversariales dependen de:
- **(b)** impl real de `IRAGIndexerPort` con binding Qdrant (engine `core/luana-core-offer-studio`).
- **(c)** sales_agent **offer-knowledge retrieval tool** (engine `core/luana-core-sales-agent/.../application/tools/` — hoy = payment/scheduling/registry, NO existe retrieval de offer-knowledge).
- **(d)** RAG guards: commercial-only · price-always-from-field (anti-staleness) · clinical→escalate-to-doctor · PHI scrub on ingest (HIPAA-lite).

**Promotion proposal a dimensionar (es de `/pm-luana` finalizarla; aquí se referencia el path + contenido):**
`docs/promotion-protocol/proposals/2026-06-15-offer-knowledge-rag-indexer-and-sales-agent-retrieval.md` — debe contener: (1) las DOS superficies engine (IRAGIndexerPort real binding + sales_agent retrieval tool), (2) el contrato del retrieval tool (input: query+tenant+offer_id scope; output: chunks comerciales con cita; tenant-scoped Qdrant collection), (3) los 4 guards, (4) goldens del sales_agent (commercial answer + 3 adversariales: precio-del-doc-rechazado · clínico-escala · PHI-scrub). **R23: flagship** (agentic production).

→ En `06-tickets.yaml`: Sub-phase B = tickets `phase: B-rag-engine-lift`, `status: blocked`, `blocked_on: "/pm-luana promotion proposal"`, `owner_eligibility: flagship`. En `dispatch-plan.md`: la cadena autónoma cubre Sub-phase A SOLAMENTE y PARA antes de B.

---

## § Cross-cutting concerns

- **Tenant isolation (RN-12/13):** TODA query filtra `tenant_id` (incl. `get_by_id`). Catálogo **NO es PHI** (info comercial) → tenant-filter raíz, SIN dual-filter clinic. **Excepción HIPAA-lite:** `Case` (foto antes/después de paciente) → consent gate RN-33 + `CaseRepository` hereda `PhiRepositoryBase` + audit_log sync write en el consent. `clinic_scope` opcional por servicio (null=todas).
- **RBAC (RN-7):** `admin_clinic` + `owner` editan (crear/precio/activar/vincular); `doctor`+`nurse`+`staff` read-only (403 en write). `@require_role` decorator.
- **Currency (RN-3):** moneda de `tenant_locale` (`TenantLocale` VO), NUNCA hardcode `'USD'`/`'S/'`. DTOs monetary con `currency: str | None`; FE `formatMoney(amount, currency)`. Read-only en UI con tooltip de origen (RN-23).
- **Master data:** `DateTime(timezone=True)` UTC store; display via `useTenantLocale()`. NUNCA `datetime.utcnow()`.
- **Spanish neutro LatAm (RN-14):** toda UI/schema/placeholder. Placeholders orientados al tipo de clínica (RN-24) sin forkear estructura (RN-19). Voseo NO aplica (no es output sales_agent).
- **PII/PHI:** `response_model=` allowlist en toda ruta. `Case` (PHI) → consent + audit. Document ingest (Sub-phase B) → `sanitize_payload` scrub. Telemetría bucketed amounts.
- **Native-first:** lint/tests host (`${WS}/.venv/bin/{ruff,pytest}`, `npx {tsc,eslint,vitest,playwright}`). NUNCA docker exec para lint/tests.
- **Telemetría:** `vitalia_growth_studio_event` (no `copilot_trace_event`). Eventos `lisa_servicios_*`. Bucketed.

---

## § Integration design (CONN · anti-orphan — nada llega a `done` como isla)

| Contención | Cómo se cumple |
|---|---|
| **C — Consumed** (≥1 consumidor real) | KEYSTONE: `TenantKnowledgeBuilder` consume las Offers activas → Adrián las cita (verificable LIVE AC-6). Downstream: Adrián canal-inbound (keywords+link), Adrián propuestas (line-item+financiamiento), Mateo (duración), landing (futuro). El service-specialist-link y el catálogo NO son islas. |
| **O — On the map** | cap `lisa.servicios` (zona Agentes · caja Lisa · área `lisa.servicios` en SYSTEM-MAP). `dev_preview.main_component` → `LisaServiciosView`. |
| **N — Navigable/reachable** | shell → Ribbon Lisa → SubTab Servicios → N3 [Catálogo·Escalera]. Ruta `(shell-organism)/lisa/servicios`. Reachability path concreto: `ShellLayoutWire` → `SubTabsBar(lisa)` → `servicios/page.tsx` → redirect `catalogo`. |
| **N — Notarized/registered** | (1) `servicios_router` `include_router` en el app router de offer + mount en main · (2) `AGENT_SUBSUBTABS["lisa.servicios"]` en `shell-routes.ts` (SSoT, arch test) · (3) EP-2 `PresetPack` registered en `extensions.py::register_all` · (4) el Offer activo lo descubre `TenantKnowledgeBuilder` (runtime discovery — sin registro manual, lee `get_all_by_tenant`). |

Reachability path verbatim: usuario autenticado `admin_clinic` → `/{tenantId}/lisa/servicios` → (N3 default) `/catalogo` → grid `EntityInfoCard` → click card → `/{offerId}` workspace → toggle Activo → engine `products` row status=active → `build_identity` lo inyecta → Adrián lo cita.

---

## § Architecture fitness impact

- EXTEND (no nuevos allowlists que crezcan): los arch tests existentes (response_model, no-cross-imports FE, react-query-keys, no-phi-in-url, no-clerk-org, subsubtabs-ssot) cubren el surface. El offer module nuevo respeta DDD boundaries (engine via port, clinics via port).
- NEW arch test sugerido (no obligatorio para Sub-phase A): `test_offer_no_engine_edit.py` — verifica que `offer/` no importa `luana_core_offer_studio.domain` directo (solo vía `luana_core_platform.links.ports.offer`). Si el builder lo agrega, debe ser shrink-only.
- Mutation gate (hard, diff-scoped) sobre: `ThreeChargePricing` derived calc · `completeness` computation · RBAC gate · tenant-isolation filter. Ver `04-validators.yaml`.
- `make ci-parity` (engine + vitalia) verde. No flip de feature flag side-effect → § 9.5 N/A.

## § 9 — Migration notes
Un archivo migration brand `offer/persistence/migrations/XXXX_offer_service_tables.py` (Alembic, idempotente raw SQL): `CREATE TABLE IF NOT EXISTS offer_service_ext (...)`, `offer_service_specialist_links`, `offer_service_cases`, `offer_service_testimonials` + `CREATE INDEX IF NOT EXISTS` sobre `tenant_id`, `offer_id`. Enums → `CREATE TYPE IF NOT EXISTS` raw (modality, initial_appt_type, price_mode, interval_unit) o `String` + CHECK. FK `offer_id` → `products(id)` (engine table) con `ON DELETE` policy explícita; FK `doctor_id` → `vitalia_doctors(id)`. NO `op.create_table()` / `sa.Enum(create_type=True)`. Test prod-clone: `make verify-vitalia-migration-idempotency` (o steps manuales `backend-migrations.md`).

## § 9.5 — Tests audit (default-flip)
[x] No aplica — 03-arch.md no flipea defaults side-effect. (El `IRAGIndexerPort` stub→real binding es Sub-phase B engine-lift, no un flag flip brand.)

## § 14 — Test surfaces (TDD RED-first)
- **BE:** domain (VOs/completeness/3-charge calc) → infrastructure (repos tenant-scoped dual-tenant) → application (catalog/biblioteca/link/proof services) → API/E2E (RBAC 403, cross-tenant 404, response_model). RED por capa.
- **FE:** hooks (use-autosave, useServiciosQuery) → componentes (RungPicker, ModalidadPicker discriminated union, VariantsRepeater, FichaCompletenessChip) → store. RED antes.
- **E2E:** Playwright smoke (ruta nueva `/lisa/servicios`) + funcional real-backend (crear-desde-plantilla, crear-personalizado, autosave, vincular-especialista, drag-escalera, keyboard-a11y) + visual goldens (4 mockups × light/dark = 8) + axe.
- **Agentic (keystone):** assertion BE que el Offer activo aparece en `build_identity` output + LIVE-verify (ejercer activación + leer logs). NO eval goldens en Sub-phase A (sin sales_agent code nuevo). Sub-phase B: ≥3 goldens (engine-lift, gated).

## § 15 — Research notes (date-aware)
- `00-research.md` (PM, ratified 2026-06-06) — SSoT del reframe (servicio=Offer, competidores cero.ai/botclinico/rendu/Dentalink/doctocliq, treatment-coordinator KB research). Accessed 2026-06-15. Takeaway: el catálogo debe cargar lo que el AGENTE necesita para vender (no solo lo que una grilla muestra) → § Mapa de campos.
- `core/luana-core-offer-studio/.../knowledge_builder.py` + `domain/offer.py` + `domain/enums.py` + `infrastructure/repositories/offer_repository.py` — engine ground truth (accessed 2026-06-15, greps verbatim § Prior art audit). Within model cutoff (no live SoTA needed).
- `core/@luana/ui-kit/src/{rich-select.tsx,index.ts,EntityWorkspaceLayout.tsx,EntitySubNavBar.tsx}` — ui-kit 0.4.1 shipped surface (accessed 2026-06-15).
- `docs/architecture/luana-platform/design-system-canon.md` (cement 2026-06-08) — FE composition canon. Accessed 2026-06-15.
- `core/luana-core-offer-studio/.../application/ports.py::IRAGIndexerPort` — STUB default binding confirmado (accessed 2026-06-15) → habilita Sub-phase A document→autocomplete sin Qdrant real; real binding = Sub-phase B engine-lift.

## § 16 — Open questions for PM
1. **D-2 SalesBrief→engine mapping:** el builder debe confirmar los nombres exactos de los campos engine `Offer` que reciben el write-through (grep `objection_handlers`/`anti_avatar_keywords`/`headline_promise`). Si un campo crítico del argumentario no tiene hogar engine, queda brand-only y lo consume canal-inbound — AC-6 (keystone) sigue verde (el servicio aparece+se cita), pero el "argumentario completo en la identidad del agente" es parcial hasta canal-inbound. ¿OK?
2. **Engine sync repo desde service async (D-1):** el `OfferRepository` engine es sync `Session`. El builder debe elegir el patrón de wrapping (sync session scoped por request vs `run_sync`). Sin regresión a `TenantKnowledgeBuilder` (que ya lo usa sync). Confirmar en `03-arch-be.md`.
3. **Drag escalera de servicios estándar (RN-30):** Gherkin §11 adversarial deja la decisión a /architect — **resuelto:** el drag aplica SOLO a personalizados; el peldaño del estándar es fijo (locked, lo define la biblioteca). El builder lo implementa así.
4. **NumberWithUnit lift:** se difiere a `/pm-luana` (NO lift en esta story). ¿PM confirma el lift-candidate post-merge?
