<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review: Lisa Servicios (vitalia-fase2-lisa-servicios)

**Date:** 2026-06-19
**Brand:** vitalia
**Scope:** FE surfaces — T-5/T-6/T-7/T-8(FE) + all G-round FE fixes (G2-F11/F12/F12b/F13/F14/F14b + F2/F4/F5/F6/F10)
**PR folder:** `vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/`
**Files reviewed:** 8 changed FE (4 leaves + types + api + 2 list editors) + 1 arch test + tests; cross-checked BE `offer/api/dtos.py`, reconciled `01-spec.md` §Matriz, `04-validators.yaml` §RECONCILE, `checkpoint.md`
**Domains touched:** offer-studio (Lisa Servicios catalog + workspace) · forms (RHF+Zod) · master-data (currency)
**Skills consulted:** frontend-expert (FSD/Server-Client/forms/runtime-quality) · offer-expert (catalog/value_level) · brand-expert (form-runtime array) · vitalia design-system (canon §2.6 autosave, currency canon C.2.2)
**Live-verified:** YES — `checkpoint.md::dod_evidence` exercises real writes (create POST→201 DB row · autosave PATCH→200 DB value · activate POST→200 growth_studio_event + status=active); Chris `chris_verify.signoff = SATISFIED_WITH_FOLLOWUPS` (2026-06-19)
**Verdict:** **APPROVED** (with 1 WARN already owned by ratified follow-up)

## /test-frontend Gate Status

Consumed `gate-output.json` (started `2026-06-19T17:06:37Z` = 12:06:37-05:00 — FRESH: ran after latest commit `789737de` 11:43-05:00 and last FE code change `2dc86a85` 23:56-05:00 prev day. NOT stale per [[stale-gate-output-predates-carril-r-fix]]).

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict |
| ESLint (offer module, via ruff/arch on BE side) | PASS | ruff offer 0 |
| pytest offer | PASS | 172 |
| pytest architecture (BE) | PASS | 298 |
| Vitest servicios + autosave arch-test | PASS | 164 (incl. `test-autosave-value-from-local-state.test.ts`) |

A FAIL on these would be auto-verdict-FAIL; none. Per-category checklist below.

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | FSD-Lite | PASS | leaves import only own feature + `@/components/{ui,shared}` + `@luana/ui-kit` + `@/hooks`. No cross-feature import. `cap:` headers present. |
| 2 | Server/Client | PASS | leaves correctly `"use client"` (RHF/state/events). Cards (ServiceCard/RungColumn) Server (no client directive) — correct. |
| 3 | React Patterns | PASS | loading skeletons (`aria-busy`) on every async leaf; stable keys (`pair.id`/`s.id`, not index); no conditional hooks; `useCallback` deps correct; defensive `?.` only as belt-and-suspenders behind `defaultValues` guard. |
| 4 | Code Quality | PASS | gates green; no new eslint-disable/ts-expect-error; allowlist `KNOWN_AUTOSAVE_VALUE_FROM_QUERY` empty (shrink-only respected). |
| 5 | Accessibility | PASS | `aria-label` on every input/switch/select, `role="alert"` on field errors, `aria-busy` skeletons, semantic `<button>`/`<Link>`, `aria-invalid` on errored fields. |
| 6 | Forms (RHF + Zod) | PASS | PlanPagoView: zodResolver + superRefine BE invariant (financing.offered ⇒ installments≥1) + autosave on-change, no "Guardar". ParaAdrianView: autosave on-change. List editors = local-state array (form-runtime doctrine, no modal/no save button). |
| 7 | Multitenancy | PASS | `useTenantId()` everywhere; comment "NEVER useAuth().orgId — arch test test-no-clerk-organizations"; mutations carry X-User-ID (audit actor) + X-Clinic-ID where PHI; no hardcoded tenantId. |
| 8 | Master Data / Spanish | **WARN** | `ServiceCard.tsx:67` + `RungColumn.tsx:54` use `currency ?? "USD"` (canon C.2.2 violation). Already owned by ratified follow-up. Spanish neutro clean (no voseo). See finding. |
| 9 | Security / Deps | PASS | No PHI in URL/localStorage (catalog NOT PHI, RN-13; specialist link is doctor_id not patient); no dangerouslySetInnerHTML/eval; no secrets in client. |
| 10 | Tests / TDD | PASS | Real regression guards — no vacuous `expect(true).toBe(true)`; G2-F14b uses real string-wire fixtures (asserts inputs NOT empty); G2-F12 asserts `not.toHaveBeenCalled()` for empty pairs. |
| 11 | Domain Alignment / Agentic UI | PASS | value_level GAP honestly modelled optional + `useMoveRung` DEGRADES to documented no-op (USE_VALUE_LEVEL_PATCH=false) with toast — not silently broken. No hardcoded archetype/preset metadata. |
| 12 | Architecture Fitness | PASS | BE 298 + FE autosave arch-test green; allowlists not grown. |
| 13 | Mirror detection | PASS | No cross-brand mirror; FaqPair/ObjecionPair local-state editors are feature-local (not duplicating @luana primitives — they compose @luana Input/Textarea/Button). |
| 14 | Decisions honored cite (R6) | PASS | ADR-vitalia-009 (autosave value-from-RHF-local) cited in arch-test + types + ResumenView; G-round commits cite findings. |
| 15 | Connectivity (anti-isla) | PASS | leaves consumed by ServicioWorkspaceShell SERVICIO_LEAVES; api hooks consumed by leaves; cap `offer.lisa-servicios` exists (cap-doctor 0). |
| 16 | Visual fidelity (canon + scope + states) | PASS | composes @luana/ui-kit Group/GroupHeader/FloatingAutosaveIndicator/Select/Switch + canon §2.6 (ONE indicator/page); gutter padding rule#34 (p-5 md:p-6); states present; live-verified render. 8 visual goldens deferred (VR-D2, honest). |

## Findings

### WARN: `currency ?? "USD"` hardcoded fallback in catalog cards
**Category:** 8 (Master Data / Currency)
**Files:** `vitalia/frontend/src/features/lisa/components/servicios/ServiceCard.tsx:67` · `RungColumn.tsx:54`
**Issue:** Both do `const cur = currency ?? "USD"` before `Intl.NumberFormat`. The currency canon (C.2.2) and master-data rule ban a `'USD'` literal as a fallback that does NOT exhaust the tenant-locale source first. A service whose wire `currency` is null renders `USD` instead of the tenant currency (ARS/PEN). Notably **inconsistent within the same story**: `ResumenView.tsx:390` already does it right — `currency={servicio.currency ?? undefined}` with the comment *"Canon currency rule: NEVER ?? 'USD'; pass undefined when null"* — and `ResumenView.test.tsx:323` even asserts the canon.
**Why NOT a FAIL / not a new finding:** Chris's `chris_verify.signoff.open_items` already ratifies the follow-up story **`vitalia-tenant-currency-config` ("kill ?? USD · primary/secondary ISO 4217 tenant-owned")** (checkpoint.md:61). It is ratified-scope-deferred, not a silently-missed bug. The leaves under primary review (PlanPago/ParaAdrian/Especialistas) are clean — PlanPagoView:224 uses `servicio?.currency ?? locale.currency` correctly.
**Why NOT Carril A self-fix:** ServiceCard/RungColumn are Server Components (no `"use client"`) → `useTenantLocale()` (client-only) is not a trivial drop-in; locale must be threaded as a prop from the client parent (CatalogoView/EscaleraView). Non-mechanical, no existing test covers the corrected wiring → out of Carril A.
**Fix (for the follow-up):** thread `locale.currency` from the client parent and pass it as the final fallback, or move `formatPrice` to receive a non-null resolved currency. Ensure the `vitalia-tenant-currency-config` follow-up scope EXPLICITLY includes these two files (currently the open_item names the locale config, not these call sites).
**Skill ref:** `.claude/rules/master-data.md` · `currency-handling.md` · vitalia design-system canon §C.2.2

## Contract / Spec Compliance

- [x] FE wire types are the VERBATIM snake_case mirror of `offer/api/dtos.py` (no `alias_generator` → snake_case). Verified: `ThreeChargePricingDTO`, `ReservationConfigDTO`/`AdvanceConfigDTO`/`FinancingConfigDTO`, `SpecialistLinkDTO` (display_name/specialty optional), `SalesBriefDTO`, `FaqPairDTO`/`ObjectionPairDTO` (`objection_type` not `objection`), `ServiceDetailDTO`, `ServicePatchRequest`/`SalesBriefPatchRequest`. Types file explicitly cites `2026-06-04-embudo-imagined-contract` and documents every drift fix — the "imagined contract" trap is actively guarded against.
- [x] G2-F14b Decimal-string-as-JSON reality handled: BE `amount: Decimal | None` serializes as string `"100"`; FE `toNum()` coerces at the wire→form boundary (PlanPagoView:133-152). BE comment confirms `currency: str | None # NEVER hardcode 'USD'`.
- [x] Header matrix (X-Tenant-ID / X-User-ID / X-Clinic-ID) matches verbatim per BE router (api/servicios.ts:426-434). Memory [[last-commit-write-control-broken-be-path]] check: every mutation's method+path+headers verified against the documented BE matrix; DELETE specialist uses doctor_id-in-path (available client-side from `s.doctor_id`), no broken-path write.
- [x] § Matriz de cobertura RECONCILIADA (01-spec.md:814-843) maps each finding→commit→spec§→REAL test→✅; every cited FE test verified to exist (PlanPagoView 15, EspecialistasView 9, ParaAdrianView 8, autosave arch-test).

## Deferred verification — confirmed HONEST (not green-phantom)

VR-D1..D4 (`04-validators.yaml:298-302`) are `must_pass:false` with explicit `owner`+`reason` per HB-79:
- **VR-D1 E2E happy-path:** specs exist but `test.skip(!E2E_OFFER_ID/!E2E_ENABLE_WRITES)` — genuinely skip-gated (verified). Fixture `real-backend-forward.fixture.ts` composes anti-burbuja `base.ts` via `mergeTests(runtimeGate, authed)` — so when un-skipped they DO carry the runtime-error gate. The `import { expect } from "@playwright/test"` is harmless (assertion lib); the `test` runner correctly comes from the composed fixture. No [[hybrid-mock-e2e-false-green]] class here.
- **VR-D2 8 visual goldens:** `e2e/__screenshots__/servicios/` empty (verified) — honestly absent. Chris live-verify covered the real render.
- **VR-D3 contract-test FE↔BE (HB-42):** absent — the right gap to flag (this story's G2-F11/F14b bugs were born of imagined contracts).
- **VR-D4 Sub-phase B RAG:** engine-lift `/pm-luana` (STOP-2), out of brand scope.

These deferrals are the CORRECT posture — flagged here as confirmation, NOT findings.

## Allowlist / Baseline Movement
- [x] `KNOWN_AUTOSAVE_VALUE_FROM_QUERY` allowlist EMPTY (ResumenView fixed by G2-F11, removed from allowlist — shrink respected).
- [x] No FE arch fitness allowlist grew. No warning baseline growth observed in scope.

## Native-First / Git-Safety Audit
- [x] No `docker exec ... tsc|eslint|vitest|playwright`; no `make e2e*`; gate-runner ran native.
- [x] No `git add .`/`-A`/`-u` in scoped commits (pathspec commits per single-operator memory).

## Self-fix log
None applied. The single WARN (currency `?? "USD"`) is (a) ratified-scope-deferred via Chris signoff follow-up and (b) non-mechanical (Server Component → locale must be prop-threaded; no existing test covers the corrected wiring) → out of Carril A. No FAIL findings to fix.

## Verdict Math
- No FAIL in Cat 1/2/3/7/11/12/14/16 → not overall-FAIL.
- No allowlist/baseline growth without justification.
- No `/test-frontend` blocker (tsc/eslint/vitest/arch) FAIL.
- Downstream regression scope: types/api are `downstream-regression-na` (brand-local vitalia FE; no cross-brand consumers — confirmed in file headers). Gate command full-suite for servicios + offer + arch. Covered.
- LIVE_VERIFY: `verification_nature: ambas` + `demo_required` → `dod_live_verified: true` + concrete `dod_evidence` (real writes + DB effect + BE logs) + `chris_verify.signoff = SATISFIED_WITH_FOLLOWUPS` (severity ≤ medium → merge-enabled). E2E that mocks the surface-under-test: NOT presented as live-verify (the live-verify is Chris's real-stack exercise; the skipped E2E is honestly deferred). NOT `LIVE_VERIFY_MISSING`.
- Decisions cite (R6): ADR-vitalia-009 honored + cited. PASS.
- One WARN (Cat 8), already owned → does not escalate to overall WARN gate (single, ratified-deferred).

**→ APPROVED.** Spine is exemplary proceso-v5: `reconciled: true`, signoff before auditor, honest deferred validators, verbatim contract mirroring (embudo trap actively guarded), real regression tests for every G-round bug. The lone currency `?? "USD"` in two catalog cards is a known, ratified follow-up — recommend the `vitalia-tenant-currency-config` follow-up explicitly name `ServiceCard.tsx:67` + `RungColumn.tsx:54` so it isn't lost.
