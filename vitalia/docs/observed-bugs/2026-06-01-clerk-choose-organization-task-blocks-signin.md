# Observed bug — Clerk `choose-organization` session-task bloquea TODO sign-in (e2e + real)

**Fecha:** 2026-06-01
**Estado:** ✅ **RESUELTO 2026-06-01** (ver § Resolución abajo).
**Detectado por:** `/dev-team` (cierre Pendiente B, story `vitalia-fase2-lisa-doctores`) al regenerar visual goldens.
**Severidad:** ALTA — bloqueaba toda verificación browser-based (e2e completo + login real a dev-app).
**Conexión:** consecuencia directa de [[no-clerk-organizations]] aplicado a medias (se borró la Clerk org, NO se deshabilitó la tarea de org a nivel instancia).

## ✅ Resolución (2026-06-01)

Causa exacta confirmada vía Clerk Backend API (`GET /v1/instance/organization_settings`):
`enabled: true` + **`force_organization_selection: true`** + **0 organizations** (la borrada) + sin auto-creación → todo sign-in forzaba la tarea `choose-organization` sin org que elegir → sesión nunca activa.

**Fix aplicado** (Clerk Backend API, instancia test `pk_test_...`):
```
PATCH https://api.clerk.com/v1/instance/organization_settings
{ "force_organization_selection": false }   → HTTP 200
```
Verificado: `enabled: true | force_organization_selection: false`. Login real restaurado — `npx playwright test --project=setup` GREEN (2/2, auth state saved attempt 1).

**Por qué `force_organization_selection: false` (y no `enabled: false`):** es el fix quirúrgico que elimina la tarea forzada sin tocar más. Con 0 orgs + sin auto-creación + sin force, **nunca se requiere ni se lee una org** → satisface no-clerk-organizations en la práctica (el FE ya no lee `orgId` post sesión 1). Deshabilitar Organizations por completo (`enabled: false`) queda como alineación opcional futura (más agresivo; innecesario para funcionar).

> ⚠️ **Config de instancia, NO en git.** Este setting vive en la instancia Clerk (no en el repo). Si se restaura un backup de instancia o se re-habilita force-org, el bug vuelve. Registrado también en `[[no-clerk-organizations]]` (MEMORY) + learning `2026-06-01-fe-tenant-from-clerk-org-systemic.md`.

## Síntoma

`npx playwright test --project=setup` (Clerk auth bootstrap, estrategia ticket/sign-in-token + `setActive`) falla 3/3 intentos:

```
Post-signIn navigation landed on /sign-in (session not active):
http://localhost:3002/sign-in/tasks/choose-organization?redirect_url=http%3A%2F%2Flocalhost%3A3002%2F
```

El sign-in token autentica, pero Clerk redirige a `/sign-in/tasks/choose-organization` (Clerk **session tasks**: tarea forzada de selección de organización después de autenticar). Como `dr.demo@vitalialat.com` ya **no tiene membresía de ninguna org** (la org `org_3DzUI3...` "Sanaré MX — Vitalia Test Tenant" se borró en sesión 1, correcto per no-clerk-organizations), no hay org que elegir → la tarea nunca se completa → la sesión nunca queda activa → todo sign-in browser queda colgado en esa pantalla.

## Causa raíz

La **instancia Clerk** de Vitalia tiene **Organizations habilitado** con la session-task `choose-organization` (forzar pertenencia/selección de org tras login). Borrar la fila de la org sin deshabilitar esa feature/tarea dejó el flujo de autenticación roto **platform-wide** (no solo e2e — un usuario real que inicia sesión en dev-app caería en la misma pantalla).

Esto NO es un problema de código del FE/BE: es **configuración de la instancia Clerk** (outward-facing). El FE ya está correcto (no-clerk-org: `useTenantId()`/`useClinicId()` leen `public_metadata`, no `useAuth().orgId`). El problema es que Clerk, ANTES de entregar la sesión, exige completar la tarea de org.

## Evidencia de que el flujo funcionaba antes (storageState pre-deleción)

El builder de hoy creó 3 doctores reales vía Playwright autenticado a las 18:10 UTC (3 filas en `vitalia_doctors` + 3 `doctor.created` en `vitalia_audit_log`). Eso requirió un storageState válido — capturado mientras la org aún existía o cacheado de sesión 1. Una vez forzado un setup fresco (sin storageState), el `choose-organization` task aparece. La live-verify "GREEN" de sesión 1 (que terminó borrando la org) usó un storageState pre-deleción.

## Fix recomendado (Clerk instance — dominio Chris)

Deshabilitar Organizations / la session-task `choose-organization` a nivel de la instancia Clerk de Vitalia (dev), que es la **completitud correcta de no-clerk-organizations**:

- Clerk Dashboard → **Configure → Sessions → Tasks**: quitar/deshabilitar la tarea "Choose organization" (o "Force organization membership").
- Y/O Clerk Dashboard → **Organizations**: deshabilitar la feature por completo (Luana NO usa Clerk Orgs).
- Posible vía `npx clerk` (ver [[clerk-cli-automation-pattern]] — 7/8 items del checklist automatizan; verificar si session-tasks/org-settings está cubierto).

Tras el cambio: `npm run test:e2e:fresh` (regenera storageState) → setup GREEN → desbloquea regen de visual goldens + flujos profundos + re-verificación de asserts revertidos.

## Impacto en el cierre de `vitalia-fase2-lisa-doctores`

- (a) seed-by-WRITE real: ✅ YA verificado independientemente (3 filas DB + 3 audit rows) — NO depende de este blocker.
- (b)/(d)/(c-relocation): ✅ committeados (fd512f33). La **re-verificación** de asserts revertidos (b) y la **regeneración de baselines** (c) quedan bloqueadas hasta el fix Clerk.
- (e) flujos profundos: bloqueado hasta el fix Clerk.

## Referencias

- `.claude/rules/definition-of-done-live-verify.md` — DoD live (ADR-vitalia-008)
- `vitalia/docs/learnings/2026-06-01-fe-tenant-from-clerk-org-systemic.md` — la remediación FE no-clerk-org (sesión 1)
- `MEMORY.md` → `no-clerk-organizations`, `clerk-cli-automation-pattern`
- `.claude/skills/playwright-expert` → `clerk-auth-deep-dive` (session tasks lifecycle)
