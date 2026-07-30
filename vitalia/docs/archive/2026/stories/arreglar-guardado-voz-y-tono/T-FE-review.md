<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review: arreglar-guardado-voz-y-tono (FE surface — T-3/T-3.bis)

**Date:** 2026-05-30
**Story:** `vitalia/docs/product/stories/arreglar-guardado-voz-y-tono/` · type=bugfix (ADR-011 lite)
**Ticket:** T-3 / T-3.bis (FE surface)
**Commits reviewed:** 2b12924e · 560a5f54 · f19a21c3 · 24331331
**Files Reviewed:** 6 prod/test + 5 e2e specs + 1 POM + 1 observed-bug doc
**Domains touched:** brand_studio / lisa-marca (voz-y-tono sub-sub-tab)
**Skills consulted:** frontend-expert · brand-expert (voz/tono surface) · playwright-expert · tessl__react-patterns · test-design-doctrine.md · vitalia hipaa-lite.md
**Live-verified:** N/A for FE diff (no presentation change). Real-backend E2E for the regression is the live evidence (PATCH 200, no 500/422 — orchestrator-confirmed 2× deterministic).
**Verdict:** **WARN (APPROVED with one tracked follow-up)**

## /test-frontend Gate Status (consumed — orchestrator-verified)

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | tsc --noEmit | PASS | 0 errors strict (orchestrator + T-3-result) |
| QUALITY | ESLint | PASS | clean (orchestrator) |
| FUNCTIONAL | Vitest usePersonalityAutosave | PASS | 13/13 (incl. 3 new camelCase payload guards) |
| FUNCTIONAL | E2E voz-y-tono smoke | PASS | DETERMINISTIC 2× consecutive, 0 flaky — archetype autosave (PATCH 200) + bloque no-422, REAL backend |

Verdict source is the gate result + the 16-category scan below. No re-run performed (gate-runner output trusted per orchestrator).

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | 0 |
| 3 | React Patterns | PASS | 0 |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | PASS | 0 (pre-existing contrast deferred — Cat 16) |
| 6 | Forms (RHF + Zod) | PASS | 0 (no form change) |
| 7 | Multitenancy | PASS | 0 |
| 8 | Master Data / Spanish | PASS | 0 |
| 9 | Security / Deps | WARN | 1 (audit-identity fidelity) |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Domain Alignment | PASS | 0 |
| 12 | Architecture Fitness | PASS | 0 (no arch change FE) |
| 13 | Mirror detection | PASS | 0 (new POM justified, distinct contract) |
| 14 | Decisions honored cite | NA | no decisions_applicable field |
| 15 | Connectivity (anti-isla) | PASS | 0 (no new symbol; testids only) |
| 16 | Visual fidelity / scope | PASS | 0 (purely non-visual instrumentation) |

## Findings

### PASS: `getTokenReady()` is a sound, bounded robustness fix
**Category:** 2/3 · **File:** `VozTonoView.tsx:69-76`
The only production-logic change. Bounded loop (max 10 × 200ms ≈ 2s) then `throw new Error("Not authenticated")` — no infinite loop, does NOT mask a genuine auth failure (still throws after the bound). Wrapped in `useCallback([getToken])` (correct dep). Recovers the screen from the prior permanent-error state where a transient `getToken()===null` immediately threw. Paired `retry: 5` + capped exponential `retryDelay (Math.min(300*2**attempt, 2000))` on both queries is idiomatic React Query for the same Clerk readiness race. Idempotent hydration guard (`hydrated` flag) untouched. **Idiomatic and safe.**

### PASS: `data-testid`/`data-state`/`data-selected` additions are purely non-visual
**Category:** 16 (visual fidelity / scope discipline) · **Files:** `VozTonoView.tsx:192` · `ArchetypeSelector.tsx:106,118-119` · `VoiceCompilerBlocks.tsx` (testId prop threaded to `<Textarea data-testid>`) · `VoiceTextareaWithWarning.tsx:46,60,99` · `AutosaveBadge.tsx:84-85`
Verified line-by-line: every addition is an attribute on an existing element or an optional `testId?: string`/`"data-testid"?` prop threaded down to an existing `<Textarea>`. No className/layout/style/logic change. `data-state={status}` on AutosaveBadge mirrors the existing `role="status"` semantic. Scope discipline honored: zero touches to `components/ui/`, `components/shared/`, layout. The bugfix does NOT change presentation — confirmed.

### PASS: Quarantine is honest and well-pointed; regression itself is NOT quarantined
**Category:** 10 (Tests/TDD)
The 2 non-quarantined specs cover the actual fix against the REAL backend: `voz-arquetipo-autosave.spec.ts` asserts PATCH 200 (not 500) + badge never `error` + body.archetype echoed; `voz-bloque-autosave.spec.ts` asserts PATCH 200 (not 422 extra_forbidden) on a camelCase `soISpeak` edit + debounce coalescing. Both forward `/api/v1/**` to the real BE (:8002) — genuine round-trip, not a mock (honors test-design-doctrine § Verificación REAL ≠ 200). Every `authTest.fixme` (reload-persist ×2, full SC-5 error suite, a11y describes) cites the follow-up story `estabilizar-harness-e2e-lisa-marca` and the precise cause (Clerk auth-readiness race on the in-browser GET re-hydrate after reload). Reload-persist is independently verified via curl PATCH→GET round-trip (T-3-result). **We are quarantining harness-race-dependent assertions, NOT the regression.** Correct.

### PASS: Pre-existing a11y contrast finding deferral is reasonable
**Category:** 5/16 · **File:** `observed-bugs/2026-05-30-voz-y-tono-contraste-verde-wcag.md`
Green `#009966` 12px on white = 3.65:1 (needs 4.5:1). Pre-existing (the green predates this story), it's a visual/token change, and this is a guardado bugfix that must NOT touch presentation. Logged per non-egoismo clause with file:line + a concrete fix suggestion + the exact quarantined describe to re-enable. Deferring is correct — fixing it inline would violate the bugfix scope (frontend-visual-fidelity § D3).

### WARN: PATCH audit identity is the tenant ID, not the acting user (HIPAA-lite fidelity)
**Category:** 9 (Security) · **File:** `marca-voice-api.ts:101-116`
`updatePersonality` now sends `X-User-ID: opts.tenantId` and `X-User-Role: opts.userRole ?? "owner"`. Two observations:
1. **Net-positive:** before this diff the PATCH sent NEITHER header (one reason the save failed — the BE `marca_router` requires `X-User-ID` and `require_brand_owner_access()` reads `X-User-Role`). Supplying them is what makes autosave reach the BE. The `X-User-Role` client-asserted pattern is the established codebase convention (`rbac.py:88` + fiscal/fidelizacion routers read it the same way) — not a new vulnerability this story introduced.
2. **The fidelity gap:** the hook plumbs the real Clerk `userId` (`usePersonalityAutosave.ts:50,61`) but `updatePersonality` IGNORES `opts.userId` and substitutes `tenantId` as the audit-log `X-User-ID`. The honest comment documents the cause: BE requires UUID format, Clerk userIds are `user_2abc...`. Result: the immutable HIPAA-lite audit row records the org UUID as the actor, not the person — `who` is degraded (hipaa-lite.md § Audit log demands quién/qué/cuándo).
**Why WARN, not FAIL:** the root is a platform-level identity-format mismatch (Clerk userId vs BE-required UUID) that an FE-only diff cannot properly close; touching audit-identity/RBAC is stake-asymmetric (Carril C — NOT auditor self-fixable). The fix is required for the feature to work and the `userId` param is already plumbed for the day the BE accepts a non-UUID actor id (or a mapping exists).
**Fix (follow-up, not blocking):** escalate to `/pm-vitalia` / `/pm-luana` — either (a) BE accepts a stable opaque Clerk userId for `X-User-ID` (drop UUID constraint for the audit actor field), or (b) FE resolves a UUID-format internal user id and passes it through `opts.userId` (already plumbed). Track alongside `estabilizar-harness-e2e-lisa-marca` or a dedicated audit-identity ticket. Do NOT block this guardado bugfix.

## Contract / UI-SPEC Compliance
- [x] camelCase TS types match BE camelCase alias DTOs (T-2) — `PersonalityResponse`/`PersonalityPatchPayload` snake↔camel mirror correct
- [x] ISO 8601 datetimes typed as `string` (`compiledAt`, `updatedAt`)
- [x] Server/Client boundary unchanged (`VozTonoView` `"use client"` root, page.tsx Server)
- [x] Data flow unchanged (React Query GET + useMutation PATCH)
- [x] Test surfaces from 04-validators § test_construction_plan exist (POM + 3 regression specs + a11y)

## Native-First Audit
- [x] E2E commands use `E2E_BASE_URL=http://localhost:3002 npx playwright test` (native, never `make e2e`)
- [x] No `docker exec ... tsc|eslint|vitest` in commits
- [x] Commits scoped by exact filename (T-3-result § Commit lists exact paths)

## Live Verification Audit
- [x] No user-facing presentation change → `chrome-devtools-verify` not required
- [x] Live evidence = real-backend E2E (PATCH 200 round-trip) + curl PATCH→GET persistence, both cited in checkpoint/T-3-result

## Verdict Math
- No FAIL in categories 1/2/3/7/11/12/14.
- No allowlist/baseline growth (no arch/ESLint-baseline change in FE diff).
- No `/test-frontend` blocker FAIL (tsc/eslint/vitest/e2e GREEN).
- Cat 9 WARN (audit-identity fidelity) — single non-blocking WARN, tracked follow-up, stake-asymmetric (Carril C, NOT self-fixed).
- All other categories PASS.
- One category WARN ⇒ **overall WARN** (approve-with-follow-up). The guardado regression is fixed, deterministically green on the real backend, presentation untouched. The WARN is a pre-existing platform identity gap surfaced (not introduced) by the necessary header fix.

## Self-fix log
None. The single WARN is stake-asymmetric (audit identity / RBAC surface, Carril C per auditor-self-fix-policy v4.2) and its root is a BE/platform constraint — not auditor-self-fixable on the FE surface. Escalated to PM as a tracked follow-up instead.
