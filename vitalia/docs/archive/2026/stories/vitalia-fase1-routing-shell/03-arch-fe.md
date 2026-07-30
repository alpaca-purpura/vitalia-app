<!-- voseo-allowed: internal architect documentation -->
---
story_id: vitalia-fase1-routing-shell
brand: vitalia
surface: frontend
type: ui-story
last_modified: 2026-05-26
parent_arch: 03-arch.md
---

# F1-S9 · `03-arch-fe.md` — frontend slice (FE-only)

See consolidated `03-arch.md` for full context. This file is the FE-scoped view used by `builder-frontend` + `auditor-frontend`.

## § 1 — Scope (FE)

| Surface | Acción |
|---|---|
| `proxy.ts` | MODIFY (docs anchor + verify matcher) |
| Routing tree under `app/[tenantId]/(shell-organism)/` | NEW pages + MODIFY layout/page + DELETE `[...slug]` |
| `lib/agent-catalog.ts` | EXTEND (2 validators) |
| `lib/iam/api.ts` + `lib/iam/audit.ts` + `lib/iam/types.ts` | NEW |
| `(shell-organism)/_components/NetworkErrorFallback.tsx` + `RefreshButton.tsx` | NEW |
| `app/(dashboard)/**` + `app/(app)/**` | DELETE |
| 5 E2E specs apuntando legacy | MODIFY/DELETE |
| `e2e/regression/vitalia-fase1-routing-shell/**` | NEW (POM + 8 spec files + visual goldens) |
| 2 NEW arch tests | NEW (no-middleware-ts, no-dashboard-route-group) |

## § 2 — Files index (NEW vs MODIFY vs DELETE)

### § 2.1 — NEW

| Path | Type | Owner |
|---|---|---|
| `vitalia/frontend/src/lib/iam/api.ts` | helper (server-safe) | T-2 |
| `vitalia/frontend/src/lib/iam/audit.ts` | helper (server-safe) | T-2 |
| `vitalia/frontend/src/lib/iam/types.ts` | TS types | T-2 |
| `vitalia/frontend/src/lib/iam/__tests__/api.test.ts` | vitest | T-2 |
| `vitalia/frontend/src/lib/iam/__tests__/audit.test.ts` | vitest | T-2 |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/not-found.tsx` | Server Component | T-4 |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/layout.tsx` | Server Component | T-4 |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/page.tsx` | Server Component | T-4 |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/not-found.tsx` | Client Component (useParams) | T-4 |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` | Server Component | T-4 |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/_components/NetworkErrorFallback.tsx` | Server Component | T-3 |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/_components/RefreshButton.tsx` | Client Component (useRouter) | T-3 |
| `vitalia/frontend/src/__tests__/architecture/test-no-middleware-ts.test.ts` | vitest arch | T-3 |
| `vitalia/frontend/src/__tests__/architecture/test-no-dashboard-route-group.test.ts` | vitest arch | T-4 |
| `vitalia/frontend/e2e/pages/RoutingShellPage.ts` | POM | T-6 |
| `vitalia/frontend/e2e/fixtures/routing-shell.fixture.ts` | fixtures | T-6 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/happy-navigation.spec.ts` | E2E | T-6 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/not-found-outer.spec.ts` | E2E | T-6 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/not-found-inner.spec.ts` | E2E | T-6 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/cross-tenant-blocked.spec.ts` | E2E | T-6 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/network-failure-tenant-fetch.spec.ts` | E2E | T-6 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/a11y-keyboard-nav.spec.ts` | E2E + axe | T-6 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/i18n-spanish-neutro.spec.ts` | E2E | T-6 |
| `vitalia/frontend/e2e/regression/vitalia-fase1-routing-shell/no-tenants-edge.spec.ts` | E2E | T-6 |

### § 2.2 — MODIFY

| Path | Change |
|---|---|
| `vitalia/frontend/src/proxy.ts` | docs anchor + add `/marketing(.*)` explicit to public matcher (already worked implicitly) |
| `vitalia/frontend/src/lib/agent-catalog.ts` | append `isValidAgent` + `isValidSubtab` (+ extend tests) |
| `vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts` | extend with ~14 new cases |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx` | add tenant validation + network fallback + no-tenants edge |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/page.tsx` | change redirect target `lisa/marca` → `valeria/agenda` |
| `vitalia/frontend/e2e/visual/visual-smoke.spec.ts` | drop `(dashboard)` assertions; target test-stack or shell |
| `vitalia/frontend/e2e/visual/stack-stability/dev-stack-baseline.spec.ts` | idem |
| `vitalia/frontend/e2e/mobile/mobile-smoke.spec.ts` | idem |
| `vitalia/frontend/e2e/a11y/a11y-smoke.spec.ts` | idem |

### § 2.3 — DELETE

| Path | Reason |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[...slug]/page.tsx` | F1-S7 stub obsoleto |
| `vitalia/frontend/src/app/(dashboard)/` (entire dir, 9+ sub-routes) | Chris dictum: no legacy en pre-prod |
| `vitalia/frontend/src/app/(app)/` (entire dir, inbox/) | idem |
| `vitalia/frontend/src/features/dashboard/` (if no remaining consumer) | verify post (dashboard)/ delete; if `DashboardWelcome.tsx` only consumer → delete feature |
| `vitalia/frontend/e2e/pages/fidelizacion.page.ts` | POM legacy |
| `vitalia/frontend/e2e/specs/regression/fidelizacion-*.spec.ts` (4 specs) | route group gone |
| `vitalia/frontend/e2e/specs/smoke/fidelizacion.smoke.spec.ts` | idem |

**Note on `features/dashboard/`**: verify in T-5 if anything else imports it (likely zero — it was bootstrap stub for Slice 1). If zero → delete feature dir entirely. If non-zero (unlikely) → leave feature, only delete route group. Decision recorded in T-5 result.

## § 3 — Server vs Client component boundary

Of the new routing pages, only **2 are Client Components** (justified):
- `(shell-organism)/[agent]/not-found.tsx` — uses `useParams()` to know `agent` slug for contextual label.
- `(shell-organism)/_components/RefreshButton.tsx` — uses `useRouter().refresh()`.

All other pages (`layout.tsx`, `page.tsx`, outer `not-found.tsx`, subtab `page.tsx`, `NetworkErrorFallback.tsx` parent) are **Server Components**. Arch test `test_server_first.test.ts` allowlist must shrink (remove obsolete allowlisted files) and stay green.

## § 4 — Constraints

- **FSD-Lite**: `lib/iam/` is a NEW lib sub-folder (parallel to `lib/api/`, `lib/format/`, `lib/zod-schemas/`). No `features/` cross-import (safe by design). Boundary matrix per `.claude/rules/frontend-fsd.md` satisfied.
- **Anti-duplication**: `fetchUserTenants` consumes core endpoint — zero duplication of listing logic.
- **Cross-brand**: pattern Vitalia-local (Next.js 16 first-mover). LIFT-candidate annotation in `vitalia/docs/learnings/2026-05-26-nextjs16-proxy-pattern.md` (T-5 deliverable).
- **Next.js 16 specifics**: `params: Promise<>` async — must `await params` before use. `redirect()` / `notFound()` are server actions; cannot be called from Client Components without throwing. `proxy.ts` runtime defaults to Node.js (don't set `runtime` config).
- **Spanish neutro**: all user-facing strings checked against `.claude/rules/spanish-text.md` glosario. No voseo.
- **PII**: audit log payload includes ONLY userId + attemptedTenant + timestamp. No PHI.
- **No hardcoded hex**: not-found uses `text-muted-foreground` + `opacity-50` semantic tokens.
- **A11y**: `not-found.tsx` outer uses `role="main"`; inner uses `role="region" aria-label`. Focus visible via Shadcn Button default. Screen reader announces page changes via `<title>` metadata.

## § 5 — Test surface (TDD RED first)

| Layer | RED first | GREEN file |
|---|---|---|
| lib agent-catalog validators | extend `lib/__tests__/agent-catalog.test.ts` | `lib/agent-catalog.ts` |
| lib iam api | NEW `lib/iam/__tests__/api.test.ts` | `lib/iam/api.ts` |
| lib iam audit | NEW `lib/iam/__tests__/audit.test.ts` | `lib/iam/audit.ts` |
| arch no-middleware-ts | NEW arch test | proxy.ts already there |
| arch no-dashboard-route-group | NEW arch test | (dashboard) deletion |
| E2E SC-1..SC-8 | NEW 8 spec files RED | new pages |
| Visual goldens | iter 1 `--update-snapshots` post-Chris ratify | iter 2+ shrink-only |

## § 6 — Verification (post-merge)

```bash
WS=$(git rev-parse --show-toplevel)

# 1. TypeScript + ESLint
cd ${WS}/vitalia/frontend && npx tsc --noEmit
cd ${WS}/vitalia/frontend && npx eslint src/ --cache

# 2. Vitest (unit + arch)
cd ${WS}/vitalia/frontend && npx vitest run --coverage

# 3. E2E suite F1-S9
cd ${WS} && bash scripts/e2e-preflight.sh
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=regression vitalia-fase1-routing-shell

# 4. Visual goldens (after Chris ratify iter 1)
cd ${WS}/vitalia/frontend && npx playwright test --project=visual vitalia-fase1-routing-shell

# 5. grep verifications (T-3, T-4)
grep -rln "middleware.ts" ${WS}/vitalia/frontend/src/ || echo "✅ no middleware.ts"
test ! -d ${WS}/vitalia/frontend/src/app/\(dashboard\) && echo "✅ no (dashboard)"
test ! -d ${WS}/vitalia/frontend/src/app/\(app\) && echo "✅ no (app)"
```
