<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review: config-cuenta — Mi cuenta (N3-static)

**Date:** 2026-06-12
**Story / Ticket:** vitalia-fase2-config-cuenta · T-1 (FE)
**Brand:** vitalia
**Commits audited:** `5cc668d8` (T-1 FE build) + `0350bd73` (fix_session_2026-06-12 — 7 integration bugs + ui-kit N3 lift regression)
**Files Reviewed:** 27 (FE surface) + 3 (`@luana/ui-kit` engine hotfix)
**Domains touched:** config (FE feature), shell-organism (`@luana/ui-kit` engine — hotfix), brand_studio (specialties read reference, BE side T-2 not in scope)
**Skills consulted:** frontend-expert (runtime-quality-checklist), vitalia-design-system (canon), brand-expert (specialties JSONB SSoT), playwright-expert (anti-burbuja fixture)
**Live-verified:** YES — checkpoint `dod_evidence` (E2E browser 6/6 real Clerk + real BE, write→autosave→PATCH 200→reload persist→audit_log row ×2) + auditor re-ran FE gates on current working tree (tsc/eslint/vitest GREEN, see § Gate Status).
**Verdict:** **APPROVED**

---

## /test-frontend Gate Status

> ⚠️ **gate-output.json was STALE** (`started_at: 2026-06-11T00:00:00Z` placeholder midnight, predates BOTH surface commits @18:42 and @20:05). Per `stale-gate-output-predates-carril-r-fix` discipline the auditor re-ran the FE gates on the current working tree — the verdict below is the re-run, not the JSON. Re-run confirms the stale JSON was nonetheless accurate.

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | tsc --noEmit | PASS | 0 errors strict (full project, auditor re-run) |
| QUALITY | ESLint (60+ rules) | PASS | 0 errors / 0 warnings on `features/config/` + all touched lib/app/shared files (auditor re-run) |
| QUALITY | Arch fitness (FE) | PASS | 35 test files / 210 tests GREEN incl. test-agent-subsubtabs-ssot, test-no-native-select, test-no-div-layout, test-ds-tokens-lock, test_server_first, test-no-clerk-organizations, test-no-cross-brand-shell-mirror |
| FUNCTIONAL | Vitest (config feature) | PASS | AccountDataView 5 · PreferencesView 4 · ResponsibleView 4 · use-account-form 3 (auditor re-run) |
| FUNCTIONAL | E2E live-verify (smoke, real BE) | PASS | 6/6 — real-backend-forward.fixture (anti-burbuja via base.ts mergeTests), real Clerk auth, SC-04 WRITE persists + audit row (checkpoint dod_evidence) |
| HEALTH | jscpd / knip / madge | N/A this re-run | scoped FE feature; no new cross-feature cycles introduced (barrel-only imports) |

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | 1 (watch-item WARN, non-blocking) |
| 3 | React Patterns | PASS | 1 (minor WARN) |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | PASS | 0 |
| 6 | Forms (RHF + Zod) | PASS | 1 (minor WARN — type/runtime nullable) |
| 7 | Multitenancy | PASS | 0 |
| 8 | Master Data / Spanish | PASS | 0 |
| 9 | Security / Deps | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Domain Alignment / Agentic UI | PASS | 0 |
| 12 | Architecture Fitness (20) | PASS | 0 |
| 13 | Mirror detection | PASS | 0 |
| 14 | Decisions honored cite (R6) | PASS | D1/D2/D3/D3-revoked/D-AUTO honored in commit bodies + checkpoint |
| 15 | Connectivity (anti-isla) | PASS | 0 |
| 16 | Visual fidelity (canon + scope + states) | PASS | 1 (WARN — visual goldens PNG pending) |

---

## Findings

### WARN: Server `redirect()` to N3 leaf — Next 16 soft-nav watch-item
**Category:** 2 (Server/Client)
**File:** `app/[tenantId]/(shell-organism)/config/cuenta/page.tsx:32`
**Issue:** `config/cuenta/page.tsx` is a Server Component doing `redirect(/${tenantId}/config/cuenta/datos)`. The documented Next 16.2.3 "Rendered more hooks" flaky (learning `2026-06-03-next16-softnav-redirect-rendered-more-hooks`) triggers when a Server `redirect()` lands on an `ssr:false` `dynamic()` layout via soft-nav intra route-group. Here the target leaf mounts `AccountDataView` inside a plain `Suspense` (not an `ssr:false` layout) and the shell `(shell-organism)/layout.tsx` is already mounted, so the high-risk condition is NOT met. Mitigated further by the `N3_DEFAULT_LEAF` edge-redirect entry in `shell-routes.ts` and the e2e navigating directly to `/datos`.
**Fix:** None required now. If the flaky surfaces post-merge, convert the bare `cuenta` redirect to an edge-redirect (middleware/proxy 307) per the learning. **Non-blocking.**
**Skill ref:** learning 2026-06-03-next16-softnav-redirect; memory `next16-softnav-redirect`.

### WARN: `legalName`/`fiscalId` patch DTO declares non-nullable but FE sends `null`
**Category:** 6 (Forms)
**File:** `features/config/types/cuenta.types.ts:65-75` (ClinicAccountPatchDTO) vs `AccountDataView.tsx:275,293,311` (handleFieldChange("legalName", e.target.value || null))
**Issue:** `ClinicAccountPatchDTO.legalName?: string` (no `| null`) but the view passes `null` to clear a field, cast via `as ClinicAccountPatchDTO` in `handleFieldChange`. The `as` cast masks the variance. Runtime is correct (BE accepts null to clear), but the type doesn't model the nullable-clear path.
**Fix:** Widen optional editable fields to `string | null` in `ClinicAccountPatchDTO` (or drop the `null` and send `""`). Trivial; does not break contract-parity (PATCH DTO is FE-only request shape). **Non-blocking — Carril R candidate** (existing tests cover the autosave path; covered by `use-account-form.test.ts`).
**Skill ref:** frontend-quality (no `as` to bypass types).

### WARN: Visual goldens PNG not yet generated
**Category:** 16 (Visual fidelity)
**File:** spec `04-validators § visual_goldens` lists 3×2=6 PNGs (datos/prefs/resp × default+filled).
**Issue:** Goldens not generated this iteration. Mockup `mockups/cuenta.html` is ratified (Chris 2026-06-11) and mockup adherence is verifiable structurally + the 6/6 functional e2e exercises every view. Per spec § visual_goldens the PNGs are listed.
**Fix:** Generate the 6 goldens in `project=visual` (maxDiffPixelRatio 0.001) as a fast follow. Given autonomous_mode + functional e2e GREEN + ratified mockup + all 4 async states rendered, severity is WARN not FAIL. **Non-blocking.**
**Skill ref:** frontend-visual-fidelity.md D2; shell-mockup-per-component ADR-vitalia-003.

### WARN (doc-only): stale `useCurrentUser` reference in patch-account docstring
**Category:** 4 (Code Quality)
**File:** `features/config/api/patch-account.ts:23` — `/** Rol vitalia (de useCurrentUser /me) ... */`
**Issue:** Docstring says `userRole` comes from `useCurrentUser /me`, but the views correctly source it from `useTenants()` per-tenant (the F-engine-me-role-drift workaround). Misleading comment; implementation is correct.
**Fix:** Update comment to `useTenants()/me/tenants per-tenant`. Cosmetic. **Non-blocking.**

---

## ★ Engine touch (`@luana/ui-kit`) — HOTFIX assessment

**Files:** `core/@luana/ui-kit/src/organism/shell/{types.ts, ShellLayoutClient.tsx, AppPanelSlot.tsx}` (commit `0350bd73`).

**Verdict: WARN + retroactive proposal note — NOT CHANGES_REQUESTED.** This is a legitimate fix of a regression introduced TODAY by the lift `3cb9d5a0`: `subSubTabsByKey` was declared in `AppPanelSlot` props but never threaded from `ShellLayoutClient`, and `config` was excluded from `validSlugs` → the SubSubTabsBar N3 bar was DEAD for the entire platform (lisa/marca shipped included). Verified backward-compat:

- **(a) additive/optional:** `types.ts` adds `subSubTabsByKey?: Record<...>` with documented default `{}`. `ShellLayoutClient` only adds a pass-through. **Additive.**
- **(b) nicolify not broken:** nicolify `ShellLayoutWire` passes `configTabSlug="config"` (so the `validSlugs` widening applies) but does NOT pass `subSubTabsByKey` → defaults `{}`. `SubSubTabsBar` "returns null automatically for agent.subtab combos without N3 entries" (verified in `AppPanelSlot.tsx`), so for nicolify it always renders nothing → **no-op, static analysis sufficient** (downstream-regression). vitalia arch suite `test-no-cross-brand-shell-mirror` GREEN.
- **(c) proposal flagged:** retroactive `/pm-luana` promotion proposal for the lift regression fix is noted in `chris-input.md`. **Required follow-up, not a blocker.**

---

## Self-fix log

None applied. Two Carril-R candidates (nullable PATCH DTO widen, stale docstring) left as WARN — both trivial, covered by existing tests, and the story is autonomous_mode with all gates GREEN; bundling cosmetic fixes here adds churn without behavioral change. Recommend folding into the next config touch or a `/pm-luana` follow-up alongside the F-engine-me-role-drift proposal.

---

## Contract / UI-SPEC Compliance

- [x] TypeScript types camelCase exact mirror of Pydantic DTO (ClinicAccountDTO: `clinicId` ← `clinic_id`, ISO/optionals explicit) — registered in `test_fe_be_contract_parity.py` (HB-42), 6/6 GREEN
- [x] No imagined fields — the fix_session corrected `string[]` → `SpecialtyEntryDTO {id,name,tier}` to match real BE shape (HB-42 lesson applied)
- [x] camelize boundary (GET response) + **decamelize boundary** (`keysToSnake` on PATCH body — the silent-200-no-persist fix) wired
- [x] Server/Client split per ADR-vitalia-004: pages pure SC (thin, `await params`, Suspense), `*View.tsx` `"use client"`
- [x] Data flow: client GET via `useAccountQuery` is canonical source (pages pass `initialData=null`) — the SC-11 form-empty fix
- [x] Test surfaces exist: 4 vitest suites + e2e SC-01..SC-04 (real BE)
- [x] capability `configuracion.cuenta` headers `// cap:` present on all new files; CuentaPlaceholder→SHIPPED_STATIC

## Allowlist / Baseline Movement

- [x] No FE arch fitness allowlist GREW. `PLACEHOLDER_MAP` SHRANK (config.cuenta removed → SHIPPED_STATIC_SUBTABS); arch test `test_no_hardcoded_subtab_keys` + `test-agent-subsubtabs-ssot` enforce sync, both GREEN.
- [x] No ESLint warning baseline growth (config feature + touched files = 0 warnings).

## Downstream regression scope

| Surface modified | Downstream consumers | Gate status |
|---|---|---|
| `@luana/ui-kit` shell (types/ShellLayoutClient/AppPanelSlot) | vitalia ShellLayoutWire, nicolify ShellLayoutWire | vitalia arch suite GREEN (incl. no-cross-brand-shell-mirror); nicolify static analysis: subSubTabsByKey unset → `{}` → SubSubTabsBar null → no-op |
| `lib/api/keys-to-camel.ts` (+keysToSnake NEW) | config feature only (camelize is per-feature, NOT fetchClient global) | covered — additive export, no existing consumer of keysToCamel touched |
| `lib/shell-routes.ts` (AGENT_SUBSUBTABS + N3_DEFAULT_LEAF) | shell N3 routing, arch test SSoT | test-agent-subsubtabs-ssot GREEN |
| `lib/agent-catalog.ts` (SHIPPED_STATIC_SUBTABS) | SubTabContent PLACEHOLDER_MAP | arch test (map === RIBBON_SUBTABS − SHIPPED_STATIC) GREEN |

## Native-First Audit

- [x] No `docker exec ... tsc|eslint|vitest|playwright` in commits
- [x] No `make e2e` / `make e2e-smoke` (e2e run native via `npx playwright test --project=smoke`)
- [x] No `git add .` / `-A` / `-u` (commits pathspec-scoped)

## Live Verification Audit

- [x] User-facing change → live-verified. checkpoint `dod_live_verified: true` + `dod_evidence` with real writes (PATCH 200, DB persist on reload, audit_log_async_written ×2), real Clerk auth, anti-burbuja fixture (0 console errors). E2E 6/6 in smoke project (real BE :8002, no surface mock). Negative paths (422 invalid specialty, 422 missing X-User-ID, 403 wrong role) exercised live via curl.
- [x] The `fix_session_2026-06-12` writes (X-User-ID header, keysToSnake decamelize, useAccountQuery client GET, name field in PATCH) are exactly the integration bugs the orchestrator caught by EXERCISING the browser (verification-real-not-200) — the live-verify gate did its job: unit-green masked all 7.

## Upstream deficiency

- **`/architect`:** 03-arch § 5 prescribed `clinicType` and `fiscalIdLabel` in `ClinicAccountResponse` and `primarySpecialties: string[]`, but the real BE emits neither the first two (FE-derived, allowlisted) nor a flat `string[]` (BE emits `{id,name,tier}`). This is the same "imagined contract" class as the embudo case (HB-42) — caught here only at live-verify, not at design. The contract-parity test (HB-42) caught the field-name drift but NOT the shape drift (`string[]` vs `{id,name,tier}`) because the catalog DTO was not in the registered pair. **Recommend:** architect declares the specialty catalog DTO shape verbatim from BE + registers `SpecialtyCatalogResponse` in contract-parity. Auto-captured: see harness-backlog (contract-parity should cover nested/array shapes, not just top-level field names).
- **`luana-core-iam` (→ /pm-luana):** engine GET `/me` returns `users.role` LEGACY global, not `user_tenants.role` per-tenant (drift `F-engine-me-role-drift`, dr.demo global=doctor vs per-tenant=owner). Brand workaround (`useTenants()`) is correct; promotion proposal pending. Documented in checkpoint `auditor_findings_preload`.

## Verdict Math

- No FAIL in categories 1 / 2 / 3 / 7 / 11 / 12 / 14 → not overall FAIL on those axes.
- Cat 16: no primitive reinvented, no scope creep, no hardcoded token, all async states present (loading/error/empty/success), visual verified (functional e2e + ratified mockup) — goldens-pending = WARN only, NOT FAIL.
- No allowlist/baseline growth.
- No `/test-frontend` blocker FAIL (tsc/eslint/vitest re-run GREEN); 0/20 arch fitness FAIL.
- Downstream regression scope GREEN (nicolify no-op static-verified).
- Cat 14 (Decisions honored): D1/D2/D3/D3-revoked/D-AUTO cited in commit bodies + checkpoint ratified_decisions → PASS.
- IMPL-LOG / T-1-result § Skills Consulted populated (frontend-expert + runtime-quality + design-system + playwright) → PASS.
- LIVE_VERIFY present (`dod_live_verified: true` + dod_evidence with real writes + e2e composes anti-burbuja base.ts, does NOT mock the surface BE) → satisfied. demo_required waived per D-AUTO (Chris ratified); auditor technical floor met.
- Engine touch = backward-compat HOTFIX (additive optional prop, nicolify no-op) → WARN + proposal note, not blocking.
- 4 WARNs (all minor/non-blocking, no Cat with ≥2 blocking WARNs).

→ **Overall: APPROVED.** Recommend merge. Follow-ups (non-blocking): (1) `/pm-luana` retroactive proposal for the `@luana/ui-kit` N3-wiring fix + F-engine-me-role-drift; (2) generate 6 visual goldens; (3) widen PATCH DTO nullable + fix patch-account docstring (Carril-R, trivial); (4) extend contract-parity to cover nested/array DTO shapes (HB).
