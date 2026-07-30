# T-2 result — FE-prod: actor de audit real (sub-bug #2)

> Story: `estabilizar-harness-e2e-lisa-marca` (bugfix-lite) · Ticket T-2 · surface FE-prod (api-layer).
> Builder: builder-frontend (Sonnet). Estado: **tests-passing** (awaiting gate-runner + auditor-frontend).
> Depende de T-3 (pushed `5ef8cdd4`) — BE resuelve `clerk_sub → users.id` (actor real).

## Qué cambió (diff resumen)

| Archivo | Cambio |
|---|---|
| `vitalia/frontend/src/features/lisa/api/marca-voice-api.ts` (prod) | `updatePersonality`: `"X-User-ID": opts.tenantId` → `"X-User-ID": opts.userId` (Clerk userId real). Guard `if (!opts.userId) throw Error` (no mutación anónima, **sin** fallback a `tenantId`). Comentario placeholder reescrito → ahora documenta que el BE (T-3 #2b) resuelve el actor desde `clerk_sub` y el FE forwardea el userId real. RBAC `X-User-Role` intacto. |
| `vitalia/frontend/src/features/lisa/api/__tests__/marca-voice-api.test.ts` (NEW test) | Test HONESTO a nivel api-function: mockea la **dependencia** (`fetchClient`), ejerce `updatePersonality` real, asserta `X-User-ID === Clerk userId` y `!== tenantId` + 2 guards (userId null/undefined → rejects, fetchClient NO llamado) + role/method preservados. NO mockea `updatePersonality` (eso sería el false-green RN-1). 7 tests. |
| `vitalia/frontend/src/features/lisa/hooks/__tests__/usePersonalityAutosave.test.ts` (coverage_update) | `userId` agregado al mock de `@clerk/nextjs` (antes omitido → `undefined`) + 2 tests: el hook pasa `opts.userId === Clerk userId` y `!== tenantId` a `updatePersonality`. El assert del HEADER vive en el api-fn test (donde se construye); aquí se asserta el ORIGEN del actor (el hook). |

**El cambio prod es load-bearing sobre T-3 #2b:** el BE ahora resuelve el actor desde el JWT `clerk_sub` (no del header crudo), por lo que mandar el Clerk userId real (`user_2abc…`, no-UUID) no rompe el `UUID(user_id)` del PATCH — el BE ya no castea el header como actor.

## Detalle del fix (líneas load-bearing)

ANTES (`marca-voice-api.ts`):
```ts
//   X-User-ID: BE requires a valid UUID for audit log. Clerk userIds are not
//   UUID-format ("user_2abc..."); tenantId (Clerk org UUID) is used as a
//   stable placeholder. The audit log records this opaque ID — no FK lookup.
const mutationHeaders: Record<string, string> = {
  "X-User-ID": opts.tenantId,   // ← BUG sub-bug #2: el tenant como actor de audit
```
DESPUÉS:
```ts
//   X-User-ID = the REAL Clerk userId... The BE (T-3 #2b) resolves the audit
//   actor from the JWT clerk_sub → users.id UUID... NEVER the tenantId...
//   No fallback to tenantId: a missing userId means an anonymous mutation,
//   which we refuse rather than mislabel.
if (!opts.userId) {
  throw new Error("updatePersonality requires an authenticated Clerk userId (X-User-ID audit actor)");
}
const mutationHeaders: Record<string, string> = {
  "X-User-ID": opts.userId,     // ← actor real
```

## Gate output (literal — G5 pre-commit smoke gate, todos verdes)

```
$ npx tsc --noEmit
EXIT=0                                       # 0 errores

$ npx eslint src/features/lisa/api/ --max-warnings 0
EXIT=0
$ npx eslint src/features/lisa/hooks/__tests__/usePersonalityAutosave.test.ts --max-warnings 0
EXIT=0                                       # 0 errores / 0 warnings

$ vitest run src/features/lisa/api/ src/features/lisa/hooks/__tests__/usePersonalityAutosave.test.ts
 ✓ src/features/lisa/api/__tests__/marca-voice-api.test.ts (7 tests)
 ✓ src/features/lisa/api/__tests__/marca.test.ts (25 tests)
 ✓ src/features/lisa/hooks/__tests__/usePersonalityAutosave.test.ts (15 tests)
 ✓ src/features/lisa/api/__tests__/staff-blocks-api.test.ts (11 tests)
 ✓ src/features/lisa/api/__tests__/staff-api.test.ts (16 tests)
 Test Files  5 passed (5)
      Tests  74 passed (74)

$ vitest run src/__tests__/architecture/
 ✓ src/__tests__/architecture/test-no-clerk-organizations.test.ts (16 tests)   # ← clave: seguimos useAuth().userId, NO orgId
 ... (25 files)
 Test Files  25 passed (25)
      Tests  171 passed (171)
```

**RED previo (TDD, antes del fix):** `marca-voice-api.test.ts` → `Tests 4 failed | 3 passed (7)` contra el código que mandaba `tenantId`. Fallos: `X-User-ID === userId`, `X-User-ID !== tenantId`, guard null, guard undefined. GREEN tras el fix → 7/7.

## Commit

- SHA: `e51432dd` (commit por pathspec, 5 files, +357/-5)
- Branch: `wip/vitalia` (hub canónico ADR-009)
- Archivos staged (pathspec exacto, NUNCA `git add .`):
  - `vitalia/frontend/src/features/lisa/api/marca-voice-api.ts`
  - `vitalia/frontend/src/features/lisa/api/__tests__/marca-voice-api.test.ts`
  - `vitalia/frontend/src/features/lisa/hooks/__tests__/usePersonalityAutosave.test.ts`
  - `vitalia/docs/product/stories/estabilizar-harness-e2e-lisa-marca/T-2-impl-log.md`
  - `vitalia/docs/product/stories/estabilizar-harness-e2e-lisa-marca/T-2-result.md`

## Live verification (DoD #37) — estado honesto

El assert determinista del actor a nivel código está cubierto por vitest (api-fn + hook, GREEN). La verificación LIVE end-to-end de SC-6 (`PATCH personality real → fila en vitalia_audit_log con user_id = users.id real ≠ tenant_id`) es **cross-ticket** (FE T-2 manda el actor real + BE T-3 lo resuelve) y requiere `make dev-vitalia` UP + Chrome DevTools MCP + query DB. Esa evidencia se produce en el gate `sc6_audit_actor_real`/`live_verify` (04-validators) cuando la suite de-mockeada (T-1) corre contra el BE real — punto de cierre de la story, no de este ticket aislado. **No declaro SC-6 LIVE-verificado desde T-2**; el cambio de T-2 es la mitad FE necesaria, verificada a nivel api-function contra su dependencia real (`fetchClient`).

## Fuera de scope (follow-up para /pm-vitalia — NO tocado)

- `postVoiceWarningOverride` (mismo file): no manda `X-User-ID` (gap pre-existente separado del sub-bug #2 declarado).
- `identity` / `visuals` / `contact` mutations (OTROS api files): mismo bug latente (mandan `tenantId` como actor); el BE T-3 ya soporta el actor real, falta el FE. Follow-up bugfix.
- `fetchClient.ts` (forbidden_to_touch), BE (T-3, done), e2e (T-1).

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Por qué invocada | Decisión tomada (cita) |
|---|---|---|
| `frontend-expert` | Ticket FE api-layer. SOP §6 "Integrar datos" + §7 runtime-quality-checklist (routing tenantId, mock anti-patterns). | api-layer permanece en `features/lisa/api/` (FSD-Lite). Mock anti-pattern evitado: se mockea la **dependencia** (`fetchClient`), no la función bajo prueba. `useAuth().userId` es el actor (≠ tenantId que va en `useTenantId()`). |
| `brand-expert` | Touch en `features/lisa/` (sub-feature marca/voz). | Sin cambios de shape de PersonalityProfile/dimensions; el fix es transport-only (header de audit). `identity.voice_tone` DEPRECATED NO tocado. Cross-module brand read no aplica (FE api-layer brand-local). |
| `vitalia-design-system` (overlay) | Contexto brand vitalia FE. | N/A visual — sin UI nueva (bugfix transport). No se tocan átomos/moléculas/tokens. Citado por completitud must_load. |
| `.claude/rules/frontend-fsd.md` | Boundaries FSD-Lite. | api-fn vive en `features/lisa/api/`; sin cross-feature import; sin default export. `test_fsd_boundaries` + `test_no_cross_feature_imports` GREEN. |
| `vitalia/.claude/rules/hipaa-lite.md` | Es el corazón del bug: actor de audit = "quién" HIPAA-lite. | El actor de audit DEBE ser el usuario real (no el tenant). Fix manda el Clerk userId real → BE lo resuelve a `users.id` (audit_log "quién" fiel). Sin PHI en la mutación (endpoint brand-config no-PHI). |
| `.claude/rules/tenant-isolation.md` | `tenant_id` de `useTenantId`, NUNCA `useAuth().orgId`; pero el ACTOR de audit SÍ es `useAuth().userId`. | `X-Tenant-ID` (tenant isolation) lo sigue inyectando `fetchClient` (no tocado). `X-User-ID` (actor) ahora = `useAuth().userId`. `test-no-clerk-organizations` 16/16 GREEN (no usamos `orgId`). |
| `.claude/rules/tdd-mandatory.md` | Bug fix → regression test que reproduce el bug PRIMERO (RED). | RED confirmado (4 fallos contra `tenantId`) ANTES del fix → GREEN tras `opts.userId`. Sin código sin test. |
| `.claude/rules/auditor-self-fix-policy.md` | Carril del fix-loop si el auditor pide cambios. | Fix mecánico de api-layer (carril A self-fix gate-verified si aplica); cualquier cambio de comportamiento de test nuevo = carril B (dev-team escribe el test, ya hecho aquí RED→GREEN). |
| `chrome-devtools-verify` | Live-verify gate FE. | Invocada conceptualmente: la verificación LIVE de SC-6 es cross-ticket + requiere dev-vitalia UP (ver § Live verification). No declaro LIVE desde T-2; escalado al gate `live_verify` de la story (auditor/dev-team con stack UP). |

---

done -> vitalia/docs/product/stories/estabilizar-harness-e2e-lisa-marca/T-2-result.md
