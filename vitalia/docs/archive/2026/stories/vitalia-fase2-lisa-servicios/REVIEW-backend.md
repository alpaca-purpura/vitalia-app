<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Backend Code Review: Lisa Servicios — Catálogo de servicios (offer module)

**Date:** 2026-06-19
**Brand:** vitalia
**Story:** vitalia-fase2-lisa-servicios (T-1..T-4 + T-8 BE + G-round BE fixes)
**Module audited:** `vitalia/backend/src/modules/vitalia/offer/`
**Files reviewed:** ~30 (domain · application · infrastructure · api · migration 045)
**Domains touched:** offer (brand extension, EP-2 over `core/luana-core-offer-studio`)
**Skills consulted:** offer-expert (engine consume-via-import + no `_CATALOG_VERSION` bump), brand-expert (port pattern reference), backend-expert (DDD/migrations/runtime-quality)
**Verdict:** **APPROVED** (PASS)

## /test-backend Gate Status (consumed from gate-output.json — NOT re-run)

| # | Gate | Result | Detail |
|---|---|---|---|
| ruff | Lint (offer/) | PASS | 0 errors |
| pytest | offer tests | PASS | 172 tests |
| arch | architecture fitness | PASS | 298 tests (incl. `test_offer_no_engine_edit.py` shrink-only ratchet) |
| tsc | typecheck | PASS | 0 errors (FE) |
| vitest | servicios feature | PASS | 164 tests (incl. ADR-009 autosave arch gate) |

`gate-output.json` `started_at` 2026-06-19T17:06:37Z post-dates the latest BE commits. All GREEN, `any_fail: false`. No re-run needed.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | PASS | 0 |
| 3 | Soft Deletes | PASS | 0 |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | PASS | 0 |
| 6 | Async Consistency | PASS | 0 |
| 7 | Pydantic v2 / PII | PASS | 0 |
| 8 | Migration Quality | PASS | 0 |
| 9 | Security / PHI (HIPAA-lite) | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 (4 deferred VR-D1..D4 owner-assigned) |
| 11 | Cross-cutting (UTC/currency/Spanish) | PASS | 0 |
| 12 | Default flip side-effect coverage | NA | n/a (no engine config flip) |
| 13 | Connectivity / anti-isla (CONN) | PASS | 0 |

## Cross-scope flags

None. Diff scope (HEAD~30) clean:
- **NO** `core/luana-core-*/src/` edits (engine consumed via import only — see § engine boundary).
- **NO** other-brand (`nicolify/comunify/lupulo/`) edits.
- The 2 `copilot/` files in the diff window (`wizard_onboarding_routes.py`, `onboarding_draft_service.py`) belong to OTHER stories (HB-88, HB-80, T-onboarding-1) — confirmed via `git log` provenance. NOT this story, NOT scored.

## Findings

No FAIL findings. No WARN findings on the BE surface.

### Informational (not findings — pre-verified compliant)

**INFO-1 — Engine boundary is a documented shrink-only ratchet (compliant).**
`offer/` imports `luana_core_offer_studio.domain.*` directly in 6 files (offer_engine_adapter, knowledge_source_adapter, offer_engine_port, medical_offer_factory, catalog_service, dtos). All are **consume-only** (import engine TYPES / enums, never edit). `test_offer_no_engine_edit.py` gates this as a `KNOWN_VIOLATIONS` Sub-phase-A baseline that **shrinks only** — the allowlist did NOT grow, and `test_known_violations_still_exist` prevents stale entries. This is the declared encapsulation plan, not a violation. Cap line 233 + 269 affirm "cero edit del engine". ✓

**INFO-2 — Cross-module `offer → clinics` read is via port (DDD-sanctioned).**
`DoctorRosterAdapter(DoctorRosterPort)` is the ONLY place that touches `clinics.DoctorRepository`. The offer services depend on the `DoctorRosterPort` interface; the concrete cross-module import is isolated to the infrastructure adapter (mirrors brand_studio's `BrandDataPort` pattern). `_project()` maps `Doctor → RosterDoctor` with NO PHI fields surfaced (id, full_name, specialty, active only). Arch tests (298) accept this pattern. ✓

**INFO-3 — Narrow `# type: ignore[union-attr]` in `servicios_router.py:426-432` are justified.**
Each is guarded by `if "X" in fields and fields["X"] is not None:` so the attribute is non-None at the call site; mypy can't infer through dict-membership. Acceptable narrow ignores, not blanket suppressions.

## Category detail (evidence)

### Cat 1 — DDD (PASS)
- Domain pure Python: `vos.py`, `pricing_calc.py`, `completeness.py` — zero framework/SQLA import; invariants in `__post_init__`.
- Router is THIN: validate DTO → call service → map domain exception → HTTPException. No business logic in `api/`.
- Services call repos (Protocols), never query DB directly.
- Infrastructure implements domain; never reverse.

### Cat 2 — Tenant Isolation (PASS · critical)
Every repo query filters `tenant_id` including `get_by_id`:
- `offer_ext_repository.py` — all of get_by_id/get_by_offer/update/list_by_tenant/soft_delete filter `tenant_id` + `deleted_at IS NULL`.
- `specialist_link_repository.py`, `sales_brief_repository.py` — same.
- `case_repository.py` — inherits engine `CompoundScopeRepositoryBase` (dual filter `tenant_id + clinic_id`, HIPAA-lite).
- Router: `tenant_id` from `X-Tenant-ID` header on every route; cross-tenant → service returns None → 404 (no leak). Scenario `cross-tenant-bloqueada` + `test_servicios_cross_tenant.py`.

### Cat 3 — Soft Deletes (PASS)
No `DELETE FROM` / `session.delete()`. All deletes = `update().values(deleted_at=now(UTC))`. All reads exclude `deleted_at IS NOT NULL`.

### Cat 5 — SQLAlchemy 2.0 (PASS)
`select(Model).where(...)`, `await session.execute(stmt)`, `mapped_column()`, `Mapped[...]` annotations throughout. No `session.query()`.

### Cat 7 — Pydantic v2 / PII (PASS)
- `response_model=` on every route (incl. `response_model=None` + 204 on deletes). Arch gate `test_response_model_required.py` green.
- Request DTOs `ConfigDict(extra="forbid")`; Response DTOs `ConfigDict(from_attributes=True)`. No inner `class Config`, no `from_orm()`, no `Any`, no raw `dict`.
- Decimal money serialized as STRING in JSONB (lossless, `serializers.py`) — wire contract; FE coerces at the wire→form border (G2-F14b). VO invariants intact (`FaqPair`/`ObjectionPair`/`ServiceVariant`/`ThreeChargePricing` require both/non-empty/≥0 — NOT weakened by the faq/objection coerce fix).
- PII: catalog is NOT PHI (RN-13); `CaseDTO` carries asset URLs + consent flags only, **no patient identifiers**. `currency: str | None` everywhere — no hardcoded `'USD'`.

### Cat 8 — Migration Quality (PASS)
`045_vitalia_offer_service_tables.py`: idempotent raw SQL (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`). No `op.create_table()`/`add_column()`/`sa.Enum()`. All timestamps `TIMESTAMPTZ` (+ model `DateTime(timezone=True)` on all 5 models). Indexes on `tenant_id` + `offer_id`. Partial unique index `(offer_id) WHERE deleted_at IS NULL`. Down migration drops in reverse-FK order.

### Cat 9 — Security / PHI HIPAA-lite (PASS · critical)
- RBAC: mutations gated by `require_brand_owner_access()` (owner + admin_clinic → 403 otherwise). `test_servicios_rbac.py`. RN-7.
- Case (PHI) consent gate RN-33: `consent_signed=False` → `ConsentNotSignedError` → 422; nothing persisted, no audit row for rejected access.
- Audit log: SYNC write pre-response on case create/delete via committing session (`get_async_session_committing` — avoids the rolled-back-audit-row trap). `payload_redacted` intentionally empty — **no PHI in audit payload** (no photo URL, no consent text), only action + resource_id.
- PHI dual filter via engine `CompoundScopeRepositoryBase`; `MissingClinicFilterError` if clinic_id absent. PHI never in URL (POST body). Roster projection surfaces no PHI.
- External calls graceful-degrade: `DocumentAutocompleteService._record` is best-effort (try/except → structlog warning → returns None, prefill survives); `DoctorRosterAdapter` enrichment degrades to None display_name/specialty.

### Cat 10 — Tests / TDD (PASS)
- 172 offer tests green; layers covered (domain pricing/completeness/vos → infra repos → application services → api RBAC/cross-tenant/consent/response_model). Keystone `test_medical_factory_fills_all_required_engine_fields` RED-first.
- G-round regressions cited with real wire shape + without mocking the component/hook under test (VR-1..VR-10 must_pass: true, gate-green).
- Deferred VR-D1 (E2E happy-path), VR-D2 (visual goldens), VR-D3 (contract-test HB-42), VR-D4 (Sub-phase B RAG engine-lift) are `must_pass: false` with explicit owners (per HB-79, NOT green-phantom). **BE does NOT block any deferred item** — endpoints exist and serve the declared shapes (verified against `dev_preview.api_endpoints` + ServiceDetailDTO read-path).

### Cat 11 — Cross-cutting (PASS)
- UTC: `datetime.now(UTC)` (no `datetime.utcnow()`). `DateTime(timezone=True)` + `TIMESTAMPTZ`.
- Currency from data source (`currency: str | None`), never hardcoded.
- Spanish neutro: no voseo in user-facing strings (biblioteca_seed + domain scanned clean). `# voseo-allowed` magic comments on `vos.py`/`pricing_calc.py`/`serializers.py`/`dtos.py` are technical escapes (hook matches the module name `domain.vos`, not voseo).
- No `git add -A`/`docker exec ... ruff|pytest` in commits.

### Cat 13 — Connectivity / anti-isla (PASS)
- All 16 endpoints registered + reachable (router served under `/api/v1/offer/`, declared in cap `dev_preview.api_endpoints`).
- Keystone: active service enters Adrián's knowledge via `TenantKnowledgeBuilder.build_identity` (consume-only path, `test_keystone_offer_shape.py` + DB live-verified). Cap `offer.lisa-servicios.yaml` is the home (functional_area `lisa.servicios`). `03-arch.md § Integration design` present. No orphan symbols.

## Contract Compliance (business surface)

- [x] Entities/VOs implemented (ThreeChargePricing 3-charge, ServiceVariant, ValueWithUnit, FaqPair, ObjectionPair, SalesBrief, Case, Testimonial, SpecialistLink, OfferExt).
- [x] DTOs match shapes (request/response separated, VO DTOs with `.to_domain()` boundary conversion).
- [x] All 16 routes registered with `response_model=`.
- [x] Repository interfaces fully implemented (tenant-scoped + soft-delete).
- [x] CONTRACT Agentic Surfaces (Sub-phase B RAG) flagged deferred → `/pm-luana` engine-lift (NOT this auditor's scope).
- [x] Test surfaces present at each layer (TDD RED-first per `test_construction_plan`).
- [x] cap YAML + business_rules code_refs verified to exist on disk (pricing_calc.py, servicios_router.py, infrastructure/).
- [x] Arch fitness allowlist shrunk-or-unchanged (engine-boundary ratchet did not grow).

## Allowlist Movement

- `test_offer_no_engine_edit.py` `KNOWN_VIOLATIONS` = 6 entries, declared Sub-phase-A baseline, **shrink-only** (did NOT grow). Justified per-entry with rationale. No FAIL.

## Native-First Audit

- [x] No `docker exec ... ruff|pytest|tsc` in commits.
- [x] No `git add .`/`-A`/`-u` (commits by pathspec, bucket `code:offer`).
- [x] Not pushed to main (wip/vitalia).

## DoD Live-Verify (Rule #37)

Story `verification_nature: ambas` · `demo_required: true`. The BE-critical writes WERE exercised live by Chris in dev-app vitalia (tenant Sanaré · dr.demo@vitalialat.com), with `dod_live_verified: true` + `dod_evidence`:
- POST `/offer/servicios/custom` → **201** (products row, status=draft, currency=ARS).
- PATCH `/offer/servicios/{id}` → **200** (DB products.name updated; rich field description_long persists, NO 422).
- POST `/offer/servicios/{id}/activate` → **200** (growth_studio_event service_activated, DB products.status=active).
- Keystone DB-confirmed + unit-tested.

`chris_verify.signoff = SATISFIED_WITH_FOLLOWUPS` (severity ≤ medium → merge-enabled, story-closure-gate Fase F). `reconciled: true` precondition satisfied.

**LIVE_VERIFY note (informational, NOT a BE FAIL):** the auditor could not independently exercise the write because lane B Chrome profile lacks Clerk auth (documented HB-89 lane-auth gap). The critical writes are evidenced by Chris's live-verify with BE logs + DB reads. This is an infrastructure/harness gap, not a BE code defect → routed to harness backlog (HB-89 already captured by /pm-vitalia in commit 789737de).

## Upstream deficiency

None attributable to architect for the BE surface. The recurring "contract imagined" lesson (G2-F11 camelCase / G2-F14b Decimal-string) is already captured as VR-D3 (contract-test FE↔BE, HB-42) + learning `2026-06-19-unit-green-not-runtime-truth` — a cross-cutting gate gap, not an offer-module BE defect.

## Verdict Math

- No FAIL in categories 1/2/8/9/12/13 → not FAIL.
- No allowlist growth → not FAIL.
- All `/test-backend` gates GREEN → not FAIL.
- Skills consulted documented (backend-expert + offer-expert) → no Skill-routing FAIL.
- Deferred items (VR-D1..D4) are owner-assigned `must_pass: false` per HB-79 — BE serves the shapes, does not block them → not FAIL.
- DoD live-verify present (BE writes exercised + evidenced) → no LIVE_VERIFY_MISSING.
- Zero category WARNs.
- **→ APPROVED (PASS).**

Next action: `/pm-vitalia` may proceed to Fase F merge (chris_verify.signoff SATISFIED_WITH_FOLLOWUPS gates it) for the BE surface; FE audit + deferred VR-D1/D2 are separate lanes.
