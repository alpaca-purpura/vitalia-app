# T-1 Implementation Log — BE offer domain + VOs + migration + repos (net-new module)

story: vitalia-fase2-lisa-servicios · ticket: T-1 · surface: backend · agent: builder-backend
branch: wip/vitalia · bucket lock: code:offer (BE) · brief: CONTEXT-BRIEF.md (Validator pass: PASS · Faithfulness: partial)

## Skills Consulted (Step 0 GATE — no-skip)

| Skill / rule | Why invoked | Decision taken (cite) |
|---|---|---|
| `backend-expert` (runtime-quality-checklist) | net-new BE module | SQLA 2.0 `Mapped[]`/`mapped_column`, `Base` from `luana_core_platform.domain.base_entity`, `DateTime(timezone=True)`+`server_default=func.now()`, no `Session.query`, no `print` |
| `offer-expert` | touching `offer/` domain (engine Offer Studio) | CONSUME engine `Offer` aggregate via import (M3: ~12 required no-default fields → engine create is T-2, not T-1). Brand projection `OfferExt` over engine `products.id`. Archetype SERVICIO. NO bump `_CATALOG_VERSION` (brand preset = T-3). |
| `tenant-isolation.md` | every model + repo | every model carries `tenant_id`; every query `.where(Model.tenant_id == tenant_id)` incl `get_by_id`; cross-tenant → returns None (404 at api T-2). |
| `backend-ddd.md` | DDD Inside-Out layering | domain pure (zero framework import); infra implements; NO cross-module import (offer → clinics only via port, T-2). Repos `AsyncSession`. |
| `backend-migrations.md` | new migration | raw SQL `IF NOT EXISTS`; NO `op.create_table()`/`sa.Enum(create_type=True)`. Lives in `alembic/versions/` (the real version_location — `persistence/migrations/` is legacy non-scanned dir, see §Recon). |
| `currency-handling.md` (master-data) | monetary VO `ThreeChargePricing` | `currency: str \| None` from tenant_locale — NEVER hardcode `'USD'`. Derived (advance_equiv/per_month) NOT persisted → `pricing_calc.py`. |
| `tdd-mandatory.md` | all layers | RED per layer → GREEN. pricing_calc + completeness mutation-critical (100% mutants on new lines). |
| `vitalia/.claude/rules/hipaa-lite.md` | `Case` PHI (patient photo) | `CaseRepository` inherits `PhiRepositoryBase` (brand · dual-filter). Consent gate `consent_signed MUST true` (RN-33). audit_log sync write = api/service concern (T-2/T-4). Catalog NOT PHI (RN-13) → other repos plain `AsyncSession`. |

## Recon reconciliations (CONTEXT-BRIEF §11 + ground-truth re-verify)

- **M3 (engine Offer ~12 required no-default fields):** confirmed reading `core/luana-core-offer-studio/.../domain/offer.py` — `internal_sku, public_name, archetype, headline_promise, target_avatar_match, primary_outcome, time_to_value, requires_application, min_financial_capacity, pricing_options, guarantee_type, guarantee_terms, status`. **Engine Offer creation + medical default factory = T-2 (ServiceCatalogService) — OUT of T-1 scope.** T-1 = brand domain/infra/repos only.
- **M4 (no literal `description`):** confirmed — engine Offer has `public_name`/`headline_promise`/`before_state`/`after_state`/`primary_outcome`, NO `description`. "Descripción corta/larga" → brand-side `OfferExt.description_long` (arch-be line 102). Write-through to engine = T-2/T-4.
- **Migration dir reconciliation:** scope says `persistence/migrations/XXXX_offer_service_tables.py` BUT `alembic.ini` version_location = `alembic/versions/` (the `persistence/migrations/` dir is NOT a version_location — legacy numbered mirrors, not loaded by alembic). HB-37 ground-truth: `alembic current` head = `044_vitalia`. Migration written as `alembic/versions/045_vitalia_offer_service_tables.py`, `down_revision = "044_vitalia"`. Cited so auditor sees the divergence + rationale.
- **cap header:** checkpoint `cap_target: lisa.servicios` (SSoT). Header line 1 = `# cap: lisa.servicios` on every new production file.

## Plan — technical design (DDD layer order · TDD RED-first)

### Domain (pure · `offer/domain/`)
- `enums.py` — ServiceModality, InitialApptType, IntervalUnit, PriceMode, ReservationKind (StrEnum).
- `vos.py` — frozen dataclasses: ValueWithUnit, ServiceVariant, ReservationConfig, AdvanceConfig, FinancingConfig, ThreeChargePricing, FaqPair, ObjectionPair.
- `offer_ext.py` — `OfferExt` (brand projection · is_active default False · soft-delete).
- `sales_brief.py` — `SalesBrief`.
- `specialist_link.py` — `ServiceSpecialistLink`.
- `proof.py` — `Case` (PHI · consent gate field) + `Testimonial`.
- `pricing_calc.py` — `compute_derived(pricing) -> dict[str, Decimal | None]` (advance_equiv, per_month). PURE. mutation-critical.
- `completeness.py` — `compute_completeness(offer_ext, sales_brief, pricing) -> CompletenessResult(filled, total=26, missing)`. NEVER blocks is_active (AC-19). mutation-critical.

### Infrastructure (`offer/infrastructure/`)
- `models/` — SQLA 2.0 async: OfferServiceExtModel (`offer_service_ext`), ServiceSpecialistLinkModel, CaseModel (`offer_service_cases`), TestimonialModel, SalesBriefModel (`offer_service_sales_brief`). All `tenant_id` indexed, `deleted_at`, TIMESTAMPTZ, JSONB for VO bundles.
- `repositories/` — async, tenant_id every method incl get_by_id:
  - `OfferServiceExtRepository` (plain AsyncSession): get_by_offer_id, list_by_tenant, create, update, soft_delete.
  - `ServiceSpecialistLinkRepository`: list_by_offer, link, unlink.
  - `CaseRepository(PhiRepositoryBase)`: list_by_offer, create (consent gate), soft_delete.
  - `TestimonialRepository`, `SalesBriefRepository`.

### Migration
- `alembic/versions/045_vitalia_offer_service_tables.py` — 5 tables, raw SQL IF NOT EXISTS, idempotent (test run twice = no-op).

### Test battery (nature → tests · TDD RED-first)
1. RED `test_pricing_calc.py` — derived calc 3-charge (%/monto, installments, edge zero/none). mutation-critical. **FIRST.**
2. RED `test_completeness.py` — 26 must-have count, missing list, is_active NEVER blocked (AC-19). mutation-critical.
3. RED `test_vos.py` — frozen, RN-11 price≥0, RN-29 variant, RN-31 value≥1, RN-6 three-charge independence.
4. RED `test_offer_ext_repository.py` — dual-tenant (tenant A != tenant B → None), soft-delete excluded, get_by_id tenant-scoped.
5. RED `test_specialist_link_repository.py` — link/unlink, unique (offer,doctor) idempotent re-link.
6. RED `test_case_repository.py` — consent gate (consent=false → raise), PhiRepositoryBase dual-filter, tenant+clinic scope.
7. RED `test_migration_idempotent.py` — schema-clone double-upgrade no-op (or marked integration if PG down).

### Integration (CONN) — T-1 is domain/persistence substrate
- Repos consumed by `ServiceCatalogService` (T-2) + keystone (T-4). Models registered via `Base.metadata` (auto-discovered by alembic env import). NOT an island: T-2/T-3/T-4 depend_on T-1 (DAG). No router registration in T-1 (api = T-2).

### Prior-art (Step 0 grep core+brand)
- Engine `Offer`/`PricingStructure`/`ObjectionItem` = CONSUME via import (T-2 write-through). NO mirror.
- `PhiRepositoryBase` (brand `_shared`) = inherit for CaseRepository. NO new dual-filter logic.
- comunify `offer_ladder` = shape reference ONLY, NEVER import (cross-brand ban).

## Iterations
