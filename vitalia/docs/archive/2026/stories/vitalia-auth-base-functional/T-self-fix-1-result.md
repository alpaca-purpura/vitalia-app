# T-self-fix-1 — Auditor WARN self-fix (iteration 1)

> Brand: vitalia
> Surface: frontend
> Iteration: 1 (audit_iteration: 1)
> Commit: 65e82b8
> Branch: wip/vitalia
> Date: 2026-05-18

## Scope

Addresses 6 WARNs from auditor-frontend across T-3, T-6.a, T-6.b.
No FAIL items — all WARNs, none blocking.
BE WARNs (T-4, T-5) explicitly out of scope per auditor protocol (follow-up ticket post-merge).

## Files modified (8)

| File | WARN addressed |
|---|---|
| `vitalia/frontend/src/features/dashboard/components/SliceOneStubsRow.tsx` | T-3: remove unnecessary `"use client"` |
| `vitalia/frontend/e2e/auth/sign-in-redirect.spec.ts` | T-6.a (1): fix assertion-swallowing |
| `vitalia/frontend/e2e/auth/sign-in-form.spec.ts` | T-6.a (1): fix assertion-swallowing (4 occurrences) |
| `vitalia/frontend/e2e/admin/tenants-users.spec.ts` | T-6.a (1): fix assertion-swallowing on PHI leak assertions |
| `vitalia/frontend/e2e/dashboard/welcome.spec.ts` | T-6.a (2): fix mock route + remove orphan mocks |
| `vitalia/frontend/e2e/visual/visual-smoke.spec.ts` | T-6.b (1): tighten visual thresholds |
| `vitalia/frontend/e2e/a11y/a11y-smoke.spec.ts` | T-6.b (2): narrow iframe exclusion to Clerk-specific |
| `scripts/playwright_console_network_audit.sh` | T-6.b (3): add text-fallback caveat comment |

## Fix details

### T-3: SliceOneStubsRow.tsx

- Removed `"use client";` directive — component is purely presentational (STUB_CARDS array, no state/effects/event handlers/browser APIs)
- Updated JSDoc comment from speculative "future iterations will add interactive hover" to explicit "Server Component (default): if interactive hover state is genuinely required in a future iteration, re-add use client with measured justification"
- Pattern: Server-First default per CLAUDE.md + frontend-fsd.md

### T-6.a (1): Assertion-swallowing fix

Pattern replaced throughout: `await expect(...).catch(() => {})` → `await expect(...).toHaveCount(0, { timeout })`.

Rationale: `toHaveCount(0)` is semantically correct for "element must not exist" — passes when element is absent (count=0), fails loudly when element appears (count>0). `.catch(() => {})` on `expect()` silently swallows genuine test failures, defeating the purpose of the assertion.

**Preserved acceptable patterns (not changed):**
- `isVisible({ timeout }).catch(() => false)` — boolean coercion on method call, fine
- `waitForLoadState(...).catch(() => {})` — best-effort network state, fine

**HIPAA-lite note:** The PHI leak assertions (`diagnóstico`, `tratamiento` checks in tenants-users.spec.ts) now enforce correctly — a PHI leak would cause a loudly-failing test rather than a silently-swallowed assertion. This is the correct behavior per hipaa-lite.md.

### T-6.a (2): Dashboard mock route fix

- **Before:** `page.route("**/api/v1/vitalia/tenant/profile", ...)` — wrong path, production never fetches this
- **After:** `page.route("**/api/v1/iam/me", ...)` — matches `DashboardWelcome.tsx` production fetch exactly
- Updated response shape to match `DashboardUserData` interface (userId, firstName, lastName, email, role, isOnboarded, clinicName, planTier, tenantId, clinicId)
- Removed orphan mocks: `/dashboard/summary` and `/wizard/status` — no component in scope fetches these; orphan mocks waste test setup and obscure actual network behavior

### T-6.b (1): Visual threshold tightening

| Page | Before | After | Rationale |
|---|---|---|---|
| `/sign-in` | `0.2` | `0.05` | Clerk vendor UI renders with high consistency; captcha/avatar masked |
| `/sign-up` | `0.2` | `0.05` | Same as sign-in |
| `/` (dashboard) | `0.2` | `0.1` | Owned code; dynamic content masked; moderate tolerance for OS font antialiasing |

Added inline comment to file header explaining thresholds per page type.

### T-6.b (2): A11y iframe exclusion narrowed

- **Before:** `.exclude("iframe")` — excludes ALL iframes globally, can hide violations in non-Clerk iframes
- **After:** `.exclude({ selector: 'iframe[src*="clerk"]' })` — targets only Clerk auth iframes (dev mode widget)
- Applied to both the public routes scan and the authenticated dashboard scan

### T-6.b (3): Audit script text-fallback caveat

Added `LIMITACIÓN` section to script header documenting that `\b[45][0-9]{2}\b` is a coarse heuristic with false-positive risk (any 3-digit number starting 4/5). Canonical detection path is trace.zip parse via `--trace=on` (structured JSON).

## Quality gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| `eslint src/` | 0 errors |
| `vitest run src/__tests__/architecture/` | 38/38 PASS |
| `vitest run src/features/dashboard/` | 3/3 PASS |
| `bash -n scripts/playwright_console_network_audit.sh` | syntax OK |

## Live verification

`chrome-devtools-verify` skill is marked DEPRECATED for Linux Mint (designed for WSL2+Windows bridge, requires rewrite). Escalated to Chris staging gate manual per skill documentation.

## Commit

SHA: `65e82b8`
Branch: `wip/vitalia`
Message: `fix(vitalia/frontend): self-fix iter-1 — address auditor WARNs T-3/T-6.a/T-6.b`
