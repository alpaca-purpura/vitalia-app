# T-3 Result — proxy polish + tenant validation layout + network fallback

**Story:** vitalia-fase1-routing-shell (F1-S9)
**Ticket:** T-3
**Brand:** vitalia
**Commit:** 0fdac50e (branch: wip/vitalia)
**Date:** 2026-05-25

## Verdict: PASS (tests-passing)

All quality gates GREEN. Implementation complete per 03-arch-fe.md § 2.1 + 06-tickets.yaml T-3 spec.

## Files changed (7)

| File | Action | Description |
|---|---|---|
| `vitalia/frontend/src/proxy.ts` | MODIFY | Added `/marketing(.*)` + `/__clerk/(.*)` to public matcher; comment anchor F1-S9 |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx` | MODIFY | Full tenant validation: auth() + fetchUserTenants + SC-4/5/7/8 |
| `vitalia/frontend/src/app/(auth)/sign-in/[[...rest]]/page.tsx` | EXTEND | `?error=no_tenants_assigned` detection + admin error panel |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/_components/NetworkErrorFallback.tsx` | NEW | Server Component fallback for network errors (SC-7) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/_components/RefreshButton.tsx` | NEW | Client leaf — `useRouter().refresh()` trigger |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/_components/NetworkErrorFallback.test.tsx` | NEW | 10 Vitest assertions GREEN |
| `vitalia/frontend/src/__tests__/architecture/test-no-middleware-ts.test.ts` | NEW | Arch test: proxy.ts exists + middleware.ts banned |

## Scenarios covered

| SC | Description | Status |
|---|---|---|
| SC-01 | No session → redirect /sign-in | ✅ layout.tsx auth() check |
| SC-4 | Cross-tenant URL → audit + redirect first valid tenant | ✅ logCrossTenantAttempt + redirect |
| SC-5 | Cross-tenant URL redirect lands on valeria/agenda | ✅ redirect(`/${tenants[0].id}/valeria/agenda`) |
| SC-7 | Network error fetching tenants → NetworkErrorFallback | ✅ try/catch + <NetworkErrorFallback /> |
| SC-8 | No tenants assigned → sign-out + sign-in error panel | ✅ logNoTenantsAssigned + redirect + error UI |
| SC-proxy-marketing | /marketing/* public (no auth required) | ✅ createRouteMatcher |
| SC-proxy-clerk | /__clerk/* internal routes public | ✅ createRouteMatcher |
| AC-15 | middleware.ts absent / proxy.ts present | ✅ arch test enforces |

## Quality gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | ✅ 0 errors |
| `eslint src/` | ✅ 0 errors, 0 new warnings |
| `vitest run` | ✅ 1514/1514 PASS |
| Coverage statements | ✅ 82.56% (threshold: 20%) |
| Architecture tests | ✅ All pass (includes new test-no-middleware-ts) |

## Dependencies satisfied

- T-1 (fetchUserTenants BE endpoint): consumed via `lib/iam/api.ts::fetchUserTenants` (T-2 artifact)
- T-2 (lib/iam/{api,audit,types}.ts): consumed in layout.tsx

## Live verification

`chrome-devtools-verify` skill marked DEPRECATED for Linux Mint (2026-05-15). Manual verification steps documented for Chris staging gate:
1. Navigate `http://localhost:3002/{tenantId}/valeria/agenda` signed out → should redirect to /sign-in
2. Sign in as user without tenants → should land at /sign-in?error=no_tenants_assigned with amber panel
3. Sign in as user, navigate to wrong tenantId URL → should redirect to /{correctTenantId}/valeria/agenda + console.warn [audit] cross_tenant_attempt
4. Kill BE (port 8002) → navigate to shell → should see NetworkErrorFallback with "Reintentar" button
5. Click "Reintentar" → router.refresh() fires → shell reloads
