<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review: estabilizar-harness-e2e-lisa-marca (T-1 + T-2 + demo-bug-fixes, FE surfaces)

**Date:** 2026-06-03
**Brand:** vitalia
**PR folder:** `vitalia/docs/product/stories/estabilizar-harness-e2e-lisa-marca/`
**Ticket:** T-1 (e2e de-mock) + T-2 (FE actor) + demo-bug-fixes (identidad components)
**Files Reviewed (scoped):** 8 prod/fixture + 3 tests + next.config.ts
**Domains touched:** brand_studio (sub lisa/marca)
**Skills consulted:** frontend-expert, brand-expert, playwright-expert (via CONTEXT-BRIEF §5.5)
**Live-verified:** PARTIAL — `dod_evidence` covers identity/colors/typography/logo-UPLOAD live against dev-app R2; logo-DELETE NOT verified (see FAIL-1)
**Verdict:** **CHANGES_REQUESTED**

> R24 brief gate: CONTEXT-BRIEF `Validator pass` populated, `Faithfulness flag: partial` (non-blocking, MEDIUM M1/M2/M3 are BE/validator findings). Proceeded; §11 gaps cited where FE-relevant.

## /test-frontend Gate Status (from gate-output.json — fresh, exit 0)

| Gate | Result | Detail |
|---|---|---|
| ruff / ruff format | PASS | BE, 0 errors (out of FE scope, noted) |
| pytest architecture (335) | PASS | 0 errors |
| pytest brand_studio | PASS | 0 failed (skips present) |
| tsc --noEmit (strict) | PASS | 0 errors |
| eslint src/ | PASS | 0 problems |
| vitest (231 files / 2525) | PASS | 0 failed. Google-Fonts NetworkError noise = happy-dom offline, NOT failures |

No gate blocker. The CHANGES_REQUESTED is a **functional/contract gap the gates do not catch** (a runtime FE↔BE mismatch on an untested control) — exactly the class this story exists to kill.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | 0 |
| 3 | React Patterns | WARN | 1 (delete control wired to broken path) |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | PASS | 0 |
| 6 | Forms (RHF + Zod) | PASS | 0 |
| 7 | Multitenancy | PASS | 0 |
| 8 | Master Data / Spanish | PASS | 0 |
| 9 | Security / Deps | PASS | 0 |
| 10 | Tests / TDD | FAIL | 1 (deleteLogo zero coverage) |
| 11 | Domain Alignment / Agentic UI | FAIL | 1 (FE↔BE delete-logo contract mismatch) |
| 12 | Architecture Fitness | PASS | 0 |
| 13 | Mirror detection | PASS | 0 |
| 14 | Decisions honored cite (R6) | NA | no `decisions_applicable` in 06-tickets for FE tickets |
| 15 | Connectivity (anti-isla) | PASS | 0 (de-mock cap re-cable + components reachable) |
| 16 | Visual fidelity | WARN | 1 (delete-logo control not live-verified/demoed) |

## Findings

### FAIL-1 — Logo DELETE control points at a non-existent BE route + has zero coverage
**Category:** 11 (Domain Alignment) + 10 (Tests/TDD) + 16 (visual — not live-verified)
**Files:**
- `vitalia/frontend/src/features/lisa/api/marca.ts:273-278` (`deleteLogo`)
- `vitalia/frontend/src/features/lisa/components/marca/identidad/IdentidadView.tsx:300-301` (`onDelete` wiring — added in commit `ce6547af`)
- `vitalia/frontend/src/features/lisa/components/marca/identidad/LogoDropZone.tsx:238-250` ("Eliminar logo" button)

**Issue:** The demo-fix commit `ce6547af` added a working "Eliminar logo" button (`onDelete={() => logoDeleteMutation.mutate()}` → `deleteLogo()`). But `deleteLogo` calls `DELETE /api/v1/lisa/marca/logos` with **no path id and no actor headers**, while the real BE route is:
```python
# vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py:401-413
@router.delete("/logos/{logo_id}", status_code=204)
async def delete_logo(
    logo_id: UUID,                              # ← path param REQUIRED
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id:   str = Header(alias="X-User-ID"), # ← REQUIRED (no default)
    _role:     str = _brand_owner_required,     # ← X-User-Role REQUIRED
    ...
```
So a real click resolves to `DELETE /logos` (≠ `/logos/{logo_id}`) → 404/405, and even with the right path the request omits `X-User-ID`/`X-User-Role`. Worse: `VisualsResponse` (marca.ts:106-111) exposes only `logoUrl`, **never a `logo_id`** — the FE has no id to send, so this cannot be closed by a header tweak alone; it needs a contract decision (BE return `logo_id`, or a delete-by-tenant route).

This is the exact false-green class the story targets: a `GET 200`-clean view ships a write-button that fails after the click. It was added in the LAST commit, AFTER `dod_evidence` was recorded — so it is in **none** of: `dod_evidence` (checkpoint:228-243 covers upload, not delete), the `demo-script.md` HAPPY/EDGE (covers upload + oversized-reject, not delete), or any unit/e2e test (`marca-contract.test.ts` covers `uploadLogo` incl. actor/throw — `deleteLogo` is conspicuously absent; grep finds 0 spec/test references).

**Fix (Carril B — builder-frontend, NEW test required + contract decision):**
1. Decide the delete contract: either surface `logo_id` on `VisualsResponse`/`LogoUploadResponse` and have `deleteLogo(opts, logoId)` call `DELETE /logos/{logoId}` with `buildMutationHeaders(opts)`; OR add a BE delete-by-tenant route. This is a small FE↔BE-boundary decision — if non-trivial, loop `/architect`.
2. Add a `marca-contract.test.ts` case for `deleteLogo` (path id + `X-User-ID`/`X-User-Role` + throw-on-missing-userId, mirroring the `uploadLogo` block at :193-216) — RED first.
3. Live-verify the delete in dev-app (Chrome MCP: upload → delete → reload → gone + BE log 204, no traceback) and add to `dod_evidence` + `demo-script.md`. Chris signed off on the *placement* ("Eliminar logo" junto a "Cambiar logo"), not the *function* — the demo never exercised a delete.

**Skill ref:** `definition-of-done-live-verify.md` #37 (write exercised + effect observed, not GET 200) · `test-design-doctrine.md` (bug fix → test reproducing it first) · `auditor-self-fix-policy.md` v4.2 (NEW test ⇒ Carril B, auditor never writes tests).

> Not auditor self-fixable: requires a new test (uncovered behavior) + an FE↔BE contract decision. Not stake-asymmetric (no PHI/auth/migration) → not escalate; hand to builder-frontend.

## Passing highlights (verified, not assumed)

- **E2E de-mock (T-1) is a GENUINE de-mock, not a false green** — directly re-checked per the recurring hybrid-mock pattern:
  - 0 direct `@playwright/test` imports in the 11 lisa-marca specs; all route through `lisa-marca.fixture.ts`/`base.ts`.
  - `lisa-marca.fixture.ts` `extend`s the composed `real-backend-forward.fixture.ts` (`mergeTests(base.ts runtime gate, auth + forwarding-to-:8002)`); `setupLisaMarcaMocks` deleted; seed values are now expected round-trip values, not `route.fulfill`.
  - 0 `page.route` over `identity|visuals|personality` (was the bug). `route.fulfill` dropped 53→5; the 5 are honest fault-injection in `network-failure.ts` (`route.abort`/500/504/503), used only by `autosave-timeout`/`cross-tenant` which correctly `failOnRuntimeError:false`.
  - `concurrent-owners.spec.ts` imports `base.ts` AND wires `forwardApiToRealBackend(page)` per context (:69) → real backend + anti-burbuja gate active.
  - `base.ts` allowlist is TIGHT and does NOT swallow hydration/5xx/404 — the hydration regexes (:46-48) feed a `hydrationErrors` collector the gate asserts empty (:120-121), i.e. hydration DOES fail the gate. Allowlist shrink-only, not widened.
- **Point 1 (autosave-on-load skip):** `IdentityCard` `isHydrated` ref skips ONLY the first effect run; subsequent `valuesJson` changes still fire `onSaveRef.current(values)` → real user-edit autosave preserved. ESLint exhaustive-deps clean (refs + stringified proxy = canonical pattern, 0 disables).
- **Point 2 (page-level badge):** `aggregateAutosaveStatus` is a pure helper with full priority (saving>error>dirty>saved>idle) coverage; single `AutosaveBadge` (reused `components/marca/shared/` molecule, NOT reinvented) in `IdentidadView` header aggregating identity+visuals. Per-card badge removed.
- **Point 3 (next.config R2):** `images.remotePatterns: **.r2.dev` correct + commented for prod domain. LogoDropZone delete grouped next to "Cambiar logo" with `onDelete`/`isDeleting` props (placement OK — function broken, see FAIL-1).
- **Point 4 (TypographyEditor):** `ensureGoogleFont` idempotent `<link>` injection; preview `style={{fontFamily}}` is a justified inline-style exception (dynamic user-selected font, not a Tailwind utility). Tested (`TypographyEditor.test.tsx`: injection + multi-word `+` + preview fontFamily).
- **marca.ts contract mapping** (the keystone): `getIdentity` null-safe BE→form, `updateIdentity` name-omit/tagline-null, `updateVisuals` 6-field whitelist, `buildMutationHeaders` throws on missing userId — all covered by `marca-contract.test.ts`.
- **no-clerk-organizations:** `IdentidadView` uses `useAuth()` only for token/userId; `tenantId` from props (route params), never `orgId`. Arch test `test-no-clerk-organizations.test.ts` in gate (PASS).
- **FSD/Server-Client/RHF+Zod/Spanish-neutro:** clean. `"use client"` only on leaf interactive components; RHF+`zodResolver(identitySchema)` autosave-on-change (no Guardar button); strings neutro LatAm.

## Downstream regression scope (Step 4.5)

| Surface changed | Downstream | Gate status |
|---|---|---|
| `features/lisa/api/marca.ts` | lisa-only consumers (presencia/voz-y-tono/identidad/hooks) — NO cross-feature/cross-brand import | full `vitest run` (231 files) covered unit surfaces; `deleteLogo` has 0 tests at any layer (FAIL-1) |
| `next.config.ts` images | global next/image | tsc+eslint PASS; logo render live-verified (upload) |

Contained to lisa feature; no engine/other-brand edit.

## Native-First / Live Verification / Scope Audit
- [x] No `docker exec tsc|eslint|vitest|playwright`, no `make e2e*`, no `git add .`/`-A` in story commits.
- [x] No cross-brand pollution, no root-legacy `frontend/src/`, no `core/luana-core-*/src/` edit.
- [ ] Live-verify INCOMPLETE for the delete-logo control (FAIL-1).

## Verdict Math
- Cat 11 FAIL (FE↔BE delete-logo contract mismatch) → **overall CHANGES_REQUESTED** (Cat 11 is in the auto-FAIL set).
- Cat 10 FAIL (deleteLogo zero coverage) reinforces.
- All gates GREEN + e2e de-mock genuine → everything else PASS/WARN. Single blocking finding; the de-mock deliverable itself is sound.

**Disposition:** hand FAIL-1 to `builder-frontend` (Carril B — new test + small FE↔BE contract decision; loop `/architect` only if the route shape decision is non-trivial). Re-run gate-runner after fix. All other surfaces APPROVED.

---

## Audit iteration 2 (delete-logo fix)

**Date:** 2026-06-03
**Scope:** FOCUSED re-audit of FAIL-1 ONLY (logo DELETE contract). All other surfaces remain APPROVED from iter 1 — not re-audited.
**Fix commit:** `8d493dee` (`git show 8d493dee`)
**Verdict:** **APPROVED**

### FAIL-1 resolution — verified

The builder chose the cleaner of the two contract options I flagged: **"una marca = un logo"** → drop `{logo_id}` from the path entirely (rather than surfacing `logo_id` on `VisualsResponse`). This kills the root cause — there is no longer an id the FE lacks. Both sides now speak the same shape.

**(1) Contract FE↔BE aligned — confirmed**
- BE: `marca_router.py:401-412` — route is now `DELETE /logos` (no `{logo_id}` path param), docstring + module header updated (`marca_router.py:12`). Service `delete_logo(tenant_id, user_id)` (`marca_service.py:1090-1095`) drops the `logo_id` arg; unsets `visuals.logo_url`, best-effort storage cleanup, HIPAA audit write now carries `payload={"logo_url_removed": old_url}` (`:1137`) instead of the dead `logo_id`.
- FE: `marca.ts:273-283` — `deleteLogo` hits `/api/v1/lisa/marca/logos` (no id) with `method: "DELETE"`. Path was already `/logos`; the fix adds `headers: buildMutationHeaders(opts)`. **Same path on both sides, no id needed.** The contract mismatch that produced 404/422 is gone.
- Wiring sound end-to-end: `IdentidadView.tsx:190` `deleteLogo({...authOpts, token})` where `authOpts = {tenantId, clinicId, userId}` (`:122`, `userId` from `useAuth()` — no-clerk-org compliant) → `onDelete`/`isDeleting` props (`:300-301`) → real `LogoDropZone` button. No runtime throw: `userId` is present.

**(2) Test coverage — confirmed (zero → covered)**
- FE: `marca-contract.test.ts:218-238` — new `describe("deleteLogo ...")` block: asserts URL `=== "/api/v1/lisa/marca/logos"` (no id), `method === "DELETE"`, headers `toMatchObject({"X-User-ID": OPTS.userId, "X-User-Role": OPTS.userRole})`, AND throw-on-missing-userId (`deleteLogo({...OPTS, userId: null})` rejects `/userId/i`). Mirrors the `uploadLogo` actor block exactly. This is the coverage whose absence was the iter-1 FAIL.
- BE: `test_marca_service.py:351-372` — `test_delete_logo_removes_from_storage` updated to call `service.delete_logo(tenant_id=_TENANT_A, user_id=_USER_A)` (no `logo_id`), asserts `visuals.logo_url is None` + storage key deleted. Signature change is locked by the test.
- Reported gates (post-fix): FE marca-contract 10/10, BE marca 14/14, tsc + eslint clean, FE lisa 371/371. `gate-output.json` (17:39) predates the fix (17:52) — verdict here rests on the per-test results in the handoff + my direct read of source, which match.

**(3) RBAC + actor headers — confirmed**
- BE route guarded by `_role: str = _brand_owner_required` (`marca_router.py:410` = `Depends(require_brand_owner_access())`, `:134`) + `X-User-ID` Header required (`:409`, no default). Identical guard to PATCH/POST mutations.
- FE `buildMutationHeaders` (`marca.ts:136-146`) throws if `userId` absent, sends `X-User-ID` + `X-User-Role` (default `"owner"`, accepted by `_brand_owner_required`). Honest actor contract, same as upload/PATCH.
- Live evidence (orchestrator curl against :8002, accepted): `POST /logos 201 → DELETE /logos 204 → GET /visuals logo_url None (CLEARED) → DELETE without X-User-Role → 403 (RBAC enforced)`. This exercises the real write + observes the effect (field cleared) + confirms RBAC — the exact DoD #37 bar that was missing in iter 1.

### Category deltas (only categories FAIL-1 touched)

| # | Category | iter 1 | iter 2 | Note |
|---|---|---|---|---|
| 3 | React Patterns | WARN | PASS | delete control now wired to a real route |
| 10 | Tests / TDD | FAIL | PASS | deleteLogo covered FE (path+headers+throw) + BE (no logo_id) |
| 11 | Domain Alignment | FAIL | PASS | FE↔BE delete contract aligned (`/logos`, no id, actor headers) |
| 16 | Visual fidelity | WARN | PASS | delete write live-verified (POST→DELETE→cleared) + RBAC 403 |

### Self-fix log
None. FAIL-1 required a new test + an FE↔BE contract decision → correctly handed to builder-frontend (Carril B). Builder produced the fix + RED tests; auditor verified, did not write tests (per `auditor-self-fix-policy.md` v4.2).

### Verdict math (iter 2)
- The single iter-1 blocker (Cat 11 + Cat 10) is resolved: contract aligned, coverage added, RBAC + actor headers correct, write live-verified.
- No new findings; scope was FAIL-1 only.
- All gates GREEN (reported per-test + source-confirmed). → **overall APPROVED**.

**Disposition:** FAIL-1 closed. Story FE surfaces fully APPROVED. Ready for `/pm-vitalia` merge (Fase F) — `dod_evidence` + `demo-script.md` should append the delete flow (POST→DELETE→reload-gone + 403-without-role) before `done`, per DoD #37.
