<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review: T-3 useCurrentUser (rol desde GET /api/v1/iam/users/me)

**Date:** 2026-05-30
**Story:** vitalia-iam-slice2-phi-real-auth · **Ticket:** T-3 · **Commit:** af3c6fda
**Brand:** vitalia
**Files Reviewed:** 1 prod (`useCurrentUser.ts`) + 1 test (`useCurrentUser.test.tsx`) + 1 impl-log
**Domains touched:** iam (FE hook, global layer) — no studio/copilot/sales-agent/offer/brand UI
**Skills consulted:** frontend-expert, tessl__react-patterns, tessl__vitest, vitalia-design-system (N/A hook puro)
**Live-verified:** N/A — hook puro sin UI nueva; verificación funcional del rol real es el gate god-matrix BE (T-1/T-2, supervisado Chris). Documentado en impl-log.
**Verdict:** **APPROVED**

## Gate Status (FE — independently re-run by auditor)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit (strict) | PASS | 0 errores (re-corrido por auditor) |
| eslint (60+ rules) | PASS | 0 errores `useCurrentUser.ts` + test (re-corrido) |
| vitest (T-3 target) | PASS | 6/6 `useCurrentUser.test.tsx` (re-corrido, 278ms) |
| vitest suite (regresión) | PASS | 2302/2302 (builder, T-3-result.md) |

> Nota: `gate-output.json` en la story es el gate **BACKEND** (test-vitalia: 53 integration + 277 arch-fitness). Para T-3 (FE) el auditor re-corrió tsc+eslint+vitest de forma independiente (verificación no-cómplice). Todos GREEN.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 — hook en `src/hooks/` global, cero cross-feature import |
| 2 | Server/Client | PASS | 0 — `"use client"` línea 3 correcto (useAuth/useUser/useQuery) |
| 3 | React Patterns | PASS | 0 — loading (`isLoaded:false`)/error (`role:null`)/success cubiertos; hooks top-level; sin stale closure |
| 4 | Code Quality | PASS | 0 — tsc/eslint clean, sin baselines movidos (hook único) |
| 5 | Accessibility | N/A | hook puro, sin markup |
| 6 | Forms (RHF+Zod) | N/A | sin form |
| 7 | Multitenancy | PASS | `fetchClient` + `tenantId: orgId`; query key incluye `orgId` (cache isolation por tenant); cero hardcode |
| 8 | Master Data / Spanish | PASS | sin strings user-facing; cero voseo; sin `'USD'` |
| 9 | Security / Deps | PASS | sin secrets/eval/dangerouslySetInnerHTML; `enabled` gate evita query sin auth; error → `role:null` (no data leak) |
| 10 | Tests / TDD | PASS | RED→GREEN documentado; 6 tests success/loading/error/PHI true-false/shape |
| 11 | Domain Alignment | PASS | AD-3 honrado (consume engine `/me` directo, OQ-2 confirmado, cero endpoint brand) |
| 12 | Arch Fitness | PASS | sin nuevas violaciones (suite arch BE green; FE hook no impacta arch FE) |
| 13 | Mirror detection | PASS | `useCurrentUser.ts` modificado (no NEW file); cero mirror cross-brand/cross-feature |
| 14 | Decisions honored | PASS | AD-3 citado en commit body + impl-log § OQ-2 con file:line del engine /me |
| 15 | Connectivity (CONN) | PASS | hook ya consumido por `usePiiRoleGate` + `RequireRole` (props); no isla |
| 16 | Visual fidelity | N/A | hook sin UI |

## Findings

Cero FAIL. Cero WARN bloqueante.

### Observación (no-blocker, informativa)
- `ME_QUERY_KEY = ["iam","me"]` se exporta y se compone con `orgId` en la queryKey (`[...ME_QUERY_KEY, orgId]`). Correcto para cache isolation por tenant. La constante exportada documenta intención de invalidación futura. Sin acción.

## Verificación de los 7 puntos del encargo

1. **cat-5 (rol desde /me, no Clerk publicMetadata):** ✅ `useQuery` a `/api/v1/iam/users/me` (líneas 98-113); el rol sale de `meData.role` (línea 137-140). Cero `publicMetadata.role`. RED test 1 confirmó el cambio de fuente.
2. **shape CurrentUser INTACTO:** ✅ `{ id, firstName, lastName, email, role, hasPhiAccess, isLoaded }` (líneas 41-50) idéntico. Consumers verificados: `usePiiRoleGate` destructura `{ role, hasPhiAccess, isLoaded }` (sin cambios); `RequireRole` es pure-props (no consume el hook). tsc del proyecto completo GREEN → todos los consumers compilan. Anti-isla CONN cumplido.
3. **estados loading/error/success:** ✅ test 2 (loading, `isLoaded:false`), test 3 (error → `role:null`, no-leak), tests 1/4/5/6 (success). Re-corridos por auditor: 6/6.
4. **forbidden_to_touch:** ✅ git diff = solo `useCurrentUser.ts` + test + impl-log. `components/ui/`, `layout.tsx`, `useClinicId.ts` NO tocados (verificado).
5. **★ ENGINE BOUNDARY:** ✅ `git show af3c6fda --name-only` → cero `core/`, cero otra brand. El engine auth_router.py solo se LEYÓ (impl-log § OQ-2). HARD BAN respetado.
6. **OQ-2:** ✅ impl-log líneas 33-58 confirma shape engine `/me` (User{id,full_name,email,role,tenant_id,is_active}) basta → cero endpoint brand nuevo, cero DTO. Default AD-3 honrado.
7. **FSD-Lite + Spanish neutro:** ✅ hook en global layer importa solo `@/lib/api/fetchClient` + `@clerk/nextjs` + `@tanstack/react-query` (boundary OK). Cero voseo (sin strings user-facing).

## Downstream regression scope

| Surface modificado | downstream_test_targets | Status |
|---|---|---|
| `src/hooks/useCurrentUser.ts` (global hook) | `usePiiRoleGate`, `RequireRole`, consumers en fidelizacion/inbox/adrian/crm-shared | tsc proyecto completo GREEN (todos compilan) + suite vitest 2302/2302 GREEN |

Shape intacto → cambio interno (fuente del rol) sin breaking contract. Sin regresión.

## Native-First / Live Verification / Allowlist
- [x] Sin `docker exec ... tsc|eslint|vitest`, sin `make e2e`, sin `git add .` en commit.
- [x] Live verification N/A (hook sin UI nueva) — funcional cubierto por gate god-matrix BE supervisado Chris.
- [x] Cero allowlist/baseline movido.

## Verdict Math
- Cero FAIL en cat 1/2/3/7/11/12/14 → no FAIL.
- Gates FE (tsc/eslint/vitest) GREEN (re-verificados independientemente) → no FAIL.
- AD-3 (decisión binding) honrada y citada → no FAIL.
- Cero WARN bloqueante (1 observación informativa).
- **Resultado: APPROVED.**
