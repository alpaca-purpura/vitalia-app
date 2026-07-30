# T-1 result — BE · offer domain + VOs + migration + repos (net-new module)

story: vitalia-fase2-lisa-servicios · ticket: T-1 · surface: backend · agent: builder-backend (workhorse) · phase: A

## Verdict: PUSHED · all validators GREEN

## Scope delivered (net-new module `vitalia/backend/src/modules/vitalia/offer/`)
- **domain/** (pure, zero framework): `enums.py` (ServiceModality·InitialApptType·IntervalUnit·PriceMode·ReservationKind), `vos.py` (ValueWithUnit·ServiceVariant·ReservationConfig·AdvanceConfig·FinancingConfig·ThreeChargePricing·FaqPair·ObjectionPair), `offer_ext.py` (OfferExt brand projection over engine `products.id`), `sales_brief.py` (SalesBrief), `specialist_link.py` (ServiceSpecialistLink), `proof.py` (Case PHI+consent gate · Testimonial), `pricing_calc.py` (derived 3-charge math · **mutation-critical**), `completeness.py` (26-must-have score · NEVER blocks is_active · AC-19 · **mutation-critical**).
- **infrastructure/models/** (SQLA 2.0 async · tenant_id indexed · deleted_at · TIMESTAMPTZ · JSONB VO bundles): offer_service_ext, _sales_brief, _specialist_link, _case, _testimonial.
- **infrastructure/repositories/** (AsyncSession · tenant_id every method incl get_by_id): offer_ext, specialist_link (link/unlink), case (`PhiRepositoryBase` · consent gate), testimonial, sales_brief. + `serializers.py` (VO↔JSONB).
- **alembic/versions/045_vitalia_offer_service_tables.py** — 5 tables, raw SQL `IF NOT EXISTS`, idempotent (down_revision `044_vitalia`). NOTE: real version_location = `alembic/versions/` (NOT `persistence/migrations/` — legacy non-scanned; cited for auditor).
- **tests/modules/vitalia/offer/**: test_vos, test_pricing_calc (mutation), test_completeness (mutation), test_offer_ext_repository (dual-tenant), test_specialist_link_repository, test_case_repository (consent gate + dual-filter).

## Reconciliations applied (CONTEXT-BRIEF §11)
- M3/M4: engine `Offer` has ~12 required no-default fields + NO literal `description` → engine Offer creation + medical default-factory = T-2 (ServiceCatalogService). T-1 = brand domain/infra/repos only. "descripción" → brand `OfferExt.description_long`.
- Engine `OfferRepository` is sync; new vitalia repos use AsyncSession (backend-ddd new-code-async).
- `vos` module name tripped the voseo pre-commit scanner (false positive — value-objects, not the pronoun) → whole-file `# voseo-allowed` escape on the 5 files that reference it (sanctioned by `scripts/git-hooks/checks/02-voseo.sh` §line 64).

## Gate results (G5 pre-commit smoke gate)
- `pytest tests/modules/vitalia/offer/` → 48/48 PASS
- `ruff check` + `ruff format --check` (offer module) → clean
- voseo scanner → clean (false-positive escaped, tests path-excluded)
- migration idempotent (raw SQL IF NOT EXISTS)

## Skills consulted (must_load enforcement v4.1)
| Skill / rule | Status | When |
|---|---|---|
| backend-expert | ✅ loaded | Step 0 — SQLA 2.0 + DDD patterns |
| offer-expert | ✅ loaded | Step 0 — engine Offer consume via import |
| .claude/rules/tenant-isolation.md | ✅ loaded | every model+repo tenant_id |
| .claude/rules/backend-ddd.md | ✅ loaded | Inside-Out layering, no cross-module import |
| .claude/rules/backend-migrations.md | ✅ loaded | idempotent raw SQL |
| .claude/rules/master-data.md (currency) | ✅ loaded | ThreeChargePricing currency from tenant_locale |
| .claude/rules/tdd-mandatory.md | ✅ loaded | RED-first per layer |
| vitalia/.claude/rules/hipaa-lite.md | ✅ loaded | Case PHI + consent gate + PhiRepositoryBase |

## Engine boundary
CERO edit of `core/luana-core-*/src` — engine Offer/OfferValueLevel/ServiceDetails consumed via import only. No cross-brand. `offer/api/` deferred to T-2.

done -> T-1-result.md
