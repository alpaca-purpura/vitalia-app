# T-2 impl-log — `offer` application + API layer (vitalia-fase2-lisa-servicios)

**Builder:** `builder-backend` · **Brand:** vitalia · **Branch:** `wip/vitalia` (single-hub, in-place)
**Scope:** APPLICATION + API only. Domain/infra/repos (T-1) read-only consume.

---

## Skills Consulted

- `backend-expert` — Skill tool unavailable in builder context (error: "Skill exists but is not enabled"). Consulted via Read of `references/runtime-quality-checklist.md` (anti-patterns: Annotated inline dep, override factory no-params, no `response: Response` in stubs, datetime query direct, `Mapped[]` not `Column()`, ConfigDict extra+from_attributes, tenant filter every query, 404-not-403 on cross-tenant) + `references/offer-catalogs.md`. **Decisions taken:**
  - DI: factory `_svc(session: Annotated[AsyncSession, Depends(get_async_session_committing)])` returns service; `Annotated[Service, Depends(_svc)]` inline per call site (NOT a module-level type alias with AsyncSession inside) — avoids "AsyncSession not valid Pydantic field" (checklist §FastAPI DI).
  - All DTOs `ConfigDict(from_attributes=True)`; request DTOs add `extra="forbid"`.
  - Every repo query keeps `tenant_id` first predicate + `deleted_at IS NULL`; cross-tenant returns `None` → API 404 (no 403 leak).
  - `response_model=` on every route (arch test `test_response_model_required.py`).
- `offer-expert` — Consulted via Read of `references/offer-catalogs.md`. **Decision:** EP-2 brand preset packs are BRAND-CONFIG (no `_CATALOG_VERSION` bump; engine catalog untouched). Preset DATA lives brand-local; registered via Extension SDK EP-2. Typeahead reads the pack. Did NOT touch `core/luana-core-offer-studio`.

---

## §11 / §14 reconciliations cited (CONTEXT-BRIEF partial Faithfulness)

- **§11 EP-2 home:** `offer/extensions.py` does NOT exist. The brand's single Extension SDK entry point is `vitalia/backend/src/modules/vitalia/extensions.py` (`# cap: __shared__`, AGENTIC-mounting) with an existing `presets=()` stub (lines 259-266). arch-be §7 directs MODIFY-in-place. **Resolution:** preset DATA placed in brand-local `offer/biblioteca_seed.py` (`# cap: lisa.servicios`, pure data, testable); `extensions.py` stub gets a one-line import+spread of that seed (minimal touch to the shared file, no agentic logic added). `BibliotecaService` reads the seed module directly (deterministic, unit-testable without the SDK registry).
- **§14 medical default factory (highest mechanical risk):** engine `Offer` aggregate has **13 required no-default fields**: `internal_sku, public_name, archetype, headline_promise, target_avatar_match, primary_outcome, time_to_value, requires_application, min_financial_capacity, pricing_options, guarantee_type, guarantee_terms, status`. Factory fills all with sane medical-service neutral defaults (archetype=SERVICIO, one `PricingStructure(label, total_amount)`, guarantee=none, status passed by caller). `@model_validator validate_consistency` auto-fills `delivery_model`/`has_editions`. See `offer/application/services/medical_offer_factory.py`.
- **D-1 sync/async seam:** engine `OfferRepository` + `get_offer_repository(db)` are SYNC (`Session`). vitalia repos are ASYNC. `OfferEnginePort` impl bridges via a sync Session opened against the same engine for engine writes (engine create/update is NOT hot-path; `TenantKnowledgeBuilder` consumes sync `get_all_by_tenant`). Bridge keeps the keystone sync-consume intact.

---

## Plan — technical design per DDD layer

### Ports (`offer/application/ports/`) — ABCs
- `OfferEnginePort` — `create_service_offer / update_service_offer / get / list_service_offers` (returns engine Offer or offer_id). Impl wraps SYNC `get_offer_repository`.
- `DoctorRosterPort` — `list_doctors(tenant_id) / get_doctor(tenant_id, doctor_id)`. Impl wraps clinics `DoctorService` (cross-module via port, NO raw import).
- `BrandVoicePort` — `draft_description(tenant_id, raw) -> str`. Impl consumes lisa-marca voz (read-only; degrades to identity passthrough if unavailable).
- `DocExtractPort` — `extract_from_document(tenant_id, file_or_url) -> ExtractionPrefill`. Impl one-shot copilot extract (NOT RAG). Sub-phase A: graceful stub returning empty prefill if engine extract absent.

### Repo interface ABCs (`offer/application/ports/repositories.py`)
Protocols mirroring T-1 concrete repos so services depend on abstractions. T-1 repos extended (infrastructure, NOT forbidden — only `offer/domain` is read-only):
- `OfferServiceExtRepository`: add `update(ext)` (PATCH autosave) + `list_by_tenant(tenant_id, *, search, category, active, origin, cursor, limit)` (RN-15 server-side).
- `SalesBriefRepository`: add `update(brief)` (autosave PATCH).

### Infra adapters (`offer/infrastructure/adapters/`)
- `offer_engine_adapter.py`, `doctor_roster_adapter.py`, `brand_voice_adapter.py`, `doc_extract_adapter.py`.

### Services (`offer/application/services/`)
- `medical_offer_factory.py` — builds engine `Offer` (13 required fields) status param. **Keystone (AC-6).**
- `catalog_service.py` — create(template|custom)=engine Offer + OfferExt unit-of-work + rollback; search/filter/cursor; patch autosave; activate toggle (engine status ACTIVE↔PAUSED); soft-delete. Telemetry best-effort.
- `biblioteca_service.py` — typeahead over EP-2 seed (name+synonyms, scoped to clinic type).
- `specialist_link_service.py` — link/unlink via DoctorRosterPort (vincular ≠ crear doctor).
- `document_autocomplete_service.py` — DocExtractPort → editable prefill + KnowledgeSource row (indexer stub OK).
- `sales_brief_service.py` — CRUD + write-through to engine Offer fields (D-2).
- `proof_service.py` — Case (consent gate + audit_log sync write HIPAA-lite) + Testimonial CRUD.

### API (`offer/api/`)
- `dtos.py` — all DTOs (`ServiceListItemDTO/ServiceListResponse/ServiceDetailDTO/ServiceCreateFromTemplateRequest/ServiceCreateCustomRequest/ServicePatchRequest/ServiceActivateRequest/SpecialistLinkRequest/SpecialistLinkDTO/CaseCreateRequest/CaseDTO/TestimonialCreateRequest/TestimonialDTO/SalesBriefPatchRequest/SalesBriefDTO/BibliotecaSearchResponse/BibliotecaItemDTO/KnowledgeSourceDTO/ExtractionPrefillDTO`).
- `servicios_router.py` — 16 endpoints (§4 table). `response_model=` every route. Headers `X-Tenant-ID`, `X-User-ID`, `X-User-Role`. RBAC writes via `require_brand_owner_access()`. Case create → audit_log sync write pre-response.
- Register in `src/main.py` prefix `/api/v1/offer` (anti-orphan CONN: router consumed by FE lisa-servicios sub-tab T-3+; registered in lifespan via include_router).

### Test battery (TDD RED-first · nature → tests per test-design-doctrine)
- `test_keystone_offer_shape.py` (RED FIRST) — medical factory builds engine Offer w/ all 13 fields + status ACTIVE surfaces via `get_all_by_tenant`. **Mutation-critical.**
- `test_catalog_service.py` — create=Offer+Ext; activate; soft-delete; search filters server-side.
- `test_biblioteca_service.py` — typeahead "fundas"→"Carillas"; scoped clinic type.
- `test_specialist_link_service.py` — link/unlink via roster port; vincular no crea doctor.
- `test_servicios_rbac.py` — admin/owner write OK; doctor/nurse/staff/patient write→403. **Mutation-critical (RN-7).**
- `test_servicios_cross_tenant.py` — cross-tenant→404; no leak.
- `test_case_consent_gate.py` — consent=false→blocked; consent=true→audit_log row. **HIPAA-lite.**

### CONN (anti-orphan)
- **Consumed:** router → FE lisa-servicios hooks (T-3); keystone Offer → Adrián agent via `build_identity`.
- **On map:** cap `lisa.servicios`.
- **Navigable:** `/api/v1/offer/servicios` reachable post include_router.
- **Notarized:** `app.include_router(servicios_router, prefix="/api/v1/offer")` in main.py.

### Prior-art audit
- Engine `OfferRepository`/`Offer`/`get_offer_repository` CONSUMED via import (no mirror). RBAC `require_brand_owner_access()` REUSED (no hand-rolled). `GrowthStudioEmitter`, `AsyncAuditWriter`, `_resolve_audit_actor` REUSED from `_shared`. `CompoundScopeRepositoryBase` (T-1 CaseRepository) inherited. No cross-brand mirror.

---

## Implementation log (chronological)

1. **RED-first** — wrote `test_keystone_offer_shape.py` (3 cases) before the factory existed (TDD). Then `test_catalog_service.py`, `test_biblioteca_service.py`, `test_specialist_link_service.py`, `test_document_autocomplete_service.py`, `test_proof_service.py`, `test_sales_brief_service.py`, `test_completeness.py`, `test_pricing_calc.py`, `test_vos.py`, repo tests.
2. **Domain** — `vos.py` (frozen VOs), `enums.py`, `offer_ext.py` (brand projection over engine Offer), `proof.py` (Case PHI + Testimonial), `sales_brief.py`, `specialist_link.py`, `completeness.py` (AC-19 scoring), `pricing_calc.py` (RN-6 derived 3-charge math).
3. **Infrastructure** — models (5: ext/case/testimonial/sales_brief/specialist_link), repos (offer_ext + keyset pagination RN-15, case/testimonial via `CompoundScopeRepositoryBase`, sales_brief, specialist_link), `serializers.py` (VO↔JSONB), adapters (offer_engine async→sync D-1 bridge, doctor_roster, doc_extract, brand_voice, knowledge_source).
4. **Application** — ports (offer_engine/doctor_roster/doc_extract/brand_voice), services (catalog, biblioteca, specialist_link, proof w/ consent gate + audit sync write, sales_brief, document_autocomplete, medical_offer_factory KEYSTONE).
5. **Extension SDK EP-2** — `extensions.py` registers the biblioteca preset pack (BRAND-CONFIG, no `_CATALOG_VERSION` bump); `biblioteca_seed.py` holds the seed.
6. **Audit wiring (Task 1 origin)** — `proof_service.create_case` raises `ConsentNotSignedError` (RN-33) BEFORE any audit write; on success persists then `await self._write_audit(...)` building `AuditLogEntry(tenant_id, clinic_id, user_id, action="service_case.create", resource_type="service_case", resource_id, payload_redacted=b"")` — NO PHI in payload, SYNC pre-response per `hipaa-lite.md`. `_Audit` Protocol matches the real `_shared/repositories/audit_log_repository.py::AuditLogRepository.write(entry)` async signature.
7. **list_by_tenant contract** — extended to return `tuple[list[OfferExt], datetime | None]` (page, next_cursor) for RN-15 server-side keyset pagination; updated the T-1 repo test to unpack.
8. **Gates** — full offer battery GREEN (82 pass; only cosmetic `Testimonial` PytestCollectionWarning, a dataclass not a test). `ruff check` + `ruff format` clean. arch fitness: all GREEN except 1 PRE-EXISTING pgcrypto failure on `treatment_plans.notes` (fidelizacion module, NOT offer — out of scope).

## Remaining (NOT done — honest scope)

**API layer of T-2 was NOT built.** `offer/api/` contains only `__init__.py`. Specifically missing:

- `offer/api/dtos.py` — the 19 DTOs planned in §3 (`ServiceListResponse`, `ServiceDetailDTO`, `ServiceCreateFromTemplateRequest`, … `ExtractionPrefillDTO`).
- `offer/api/servicios_router.py` — the 16-endpoint FastAPI router (`response_model=` each, `X-Tenant-ID/X-User-ID/X-User-Role` headers, RBAC `require_brand_owner_access()` on writes, Case-create→audit sync write).
- `src/main.py` registration `app.include_router(servicios_router, prefix="/api/v1/offer")`.

**Anti-orphan CONN status:** the HTTP surface is currently an island for FE consumption — the **N**otarized + **N**avigable contentions are UNMET for the router (no `include_router`). BUT the KEYSTONE engine-surfacing path (AC-6) IS satisfied: `medical_offer_factory` → `OfferEngineAdapter.create_service_offer` → engine `OfferRepository.create`; `list_service_offers` mirrors `get_all_by_tenant` (the path `TenantKnowledgeBuilder`/Adrián reads). So the offer is reachable by the agent layer; only the FE REST surface is pending.

**What this means:** the application + domain + infrastructure + Extension SDK + KEYSTONE work of T-2/T-3/T-4 is GREEN and complete. The API/router/DTO slice of T-2 is the genuine remainder — a follow-up build (1 router file + 1 dtos file + 1 main.py line + RBAC/cross-tenant/consent-gate HTTP tests `test_servicios_rbac.py`/`test_servicios_cross_tenant.py`/`test_case_consent_gate.py`). Did NOT fake-register a router.
