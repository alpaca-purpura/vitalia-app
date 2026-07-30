# T-1 result — root login redirect soft-nav (edge-redirect del root `/`)

**Story:** vitalia-bugfix-root-login-redirect-softnav · **type:** bugfix lite · **cap:** `auth.clerk-middleware` (`cap_change_type: fix`)
**Scope:** SOLO `vitalia/frontend/` (proxy/routing). No core, no BE, no otras marcas.
**Estado:** tests-passing + live-verified contra stack dev real.

---

## Decisión: Opción A vs B → **Opción B (variante liviana)**

Resolví el tenant en el middleware vía **`clerkClient().users.getUser(userId).publicMetadata.tenant_id`** (Clerk Backend API), NO vía `fetchUserTenants` ni vía session claims.

**Por qué NO Opción A (session claims):** el JWT de dev **no inyecta claims custom** en `sessionClaims`. Confirmado por el handoff de `vitalia-bugfix-agenda-actor-headers-422` (T-1-result.md: "el JWT dev NO trae clinic claim, era el agujero del SSR" → tuvieron que resolver `clinic_id` vía `clerkClient().getUser().publicMetadata`, no vía claim). Mismo agujero para `tenant_id`. Un edge-redirect basado en un claim vacío nunca dispararía → no arregla el bug.

**Por qué Opción B con `clerkClient`, NO con `fetchUserTenants` (lo que sugería el checkpoint):**
- El tenant ya vive en `user.publicMetadata.tenant_id` (UUID) — es la MISMA fuente canónica que `useTenantId()` (client) y `resolveClinicId()` (server, agenda-server.ts). Leerlo es 1 sola llamada a Clerk, sin round-trip al BE.
- `fetchUserTenants` pega al BE, que desde el container FE necesita `INTERNAL_API_URL=http://vitalia_backend_dev:8002` (hostname de red Docker). Eso agrega una dependencia frágil en el edge runtime + una request extra. `clerkClient` es HTTPS a Clerk → **edge-runtime safe** y más liviano.
- Mantengo `fetchUserTenants` donde corresponde: en `app/page.tsx` (el fallback), que ya lo usa con su error-mapping completo.

**Anti-duplicación:** reutilizo el patrón YA probado en `features/mateo/api/agenda-server.ts::resolveClinicId` (mismo `clerkClient().getUser().publicMetadata`, mismo graceful `catch → null`). No inventé un resolver nuevo.

## Runtime del proxy

**Edge runtime (default, sin cambio).** NO declaré `export const runtime = 'nodejs'`. `clerkClient()` usa `fetch` HTTPS a la Clerk Backend API → es edge-compatible. `clerkMiddleware` corre en edge por default y la llamada es la única I/O. No hay APIs node-only en el path.

## Archivos tocados

| Archivo | Cambio |
|---|---|
| `vitalia/frontend/src/lib/shell-routes.ts` | **+** `isAuthedRootPath(pathname)` (scope HARD a `/`), `rootLandingRedirect(tenantId)` (compone `/{uuid}/mateo/agenda`, retorna `null` si tenant no-UUID/ausente), `TENANT_UUID` regex. Funciones puras, testables sin Clerk. |
| `vitalia/frontend/src/proxy.ts` | **+** `resolveTenantId(userId)` (clerkClient → `publicMetadata.tenant_id`, graceful null) + bloque en el middleware: si `pathname === "/"` y autenticado → resolver tenant → 307 al landing; si no resuelve → cae a `app/page.tsx`. Comentario "Root-login hardening" nuevo. |
| `vitalia/frontend/src/app/page.tsx` | Docblock actualizado: ahora es **fallback defensivo** (el edge cubre el happy path). Lógica intacta (no borrado). |
| `vitalia/frontend/src/lib/shell-routes.test.ts` | **+** 6 tests RED-first (isAuthedRootPath scope + rootLandingRedirect compose/null/non-UUID). |
| `vitalia/frontend/e2e/regression/vitalia-bugfix-root-login-redirect-softnav/root-login-lands-clean.spec.ts` | **NEW** regression guard real-backend ×8 loop. |

## Cómo preservé los edge-cases que hacía `app/page.tsx`

El edge **solo** 307ea cuando hay tenant UUID válido resuelto. En cualquier otro caso NO redirige → `app/page.tsx` corre con TODA su lógica:
- **Sin sesión** → `auth.protect()` (ya arriba en el proxy) manda a sign-in; además `app/page.tsx` re-chequea `userId` → `/sign-in`.
- **Sin tenants / publicMetadata cold** → `resolveTenantId` retorna `null` → no 307 → `app/page.tsx` hace `fetchUserTenants` → `/sign-in?error=no_tenants_assigned`.
- **Clerk API caída / fetch falla** → `resolveTenantId` graceful `catch → null` → no 307 → `app/page.tsx` fallback (`/sign-in?error=no_tenants_assigned`). El login NUNCA se rompe por este resolver.
- **Tenant no-UUID (ej. `org_xxx`)** → `rootLandingRedirect` retorna `null` (regex `TENANT_UUID`) → no 307 → fallback. Nunca 307 a algo que 500ee el shell layout.

**NO cambié** el `dynamic({ssr:false})` del shell (por diseño). Comentario "Bug #1 hardening" extendido implícitamente con el bloque root-login (mismo patrón documentado).

## Estado del Playwright guard: **PASSED (8/8 determinístico)**

`root-login-lands-clean.spec.ts` corrido contra stack dev real (BE :8002 + FE :3002 UP, Clerk auth real `dr.demo@vitalialat.com`, tenant `e69a691d-…`):
- **`3 passed (22.6s)`** (incluye setup Clerk). El test loopea ×8 navegaciones a `/`, asserta cada vez `/{tenant}/mateo/agenda` + `main#main-content` montado + captura `pageerror`/`console.error` de "Rendered more hooks".
- Cero "Rendered more hooks" en las 8 corridas → fix **100% determinístico** (el bug era ~40% flaky).
- Gate anti-burbuja `base.ts` verde (cero error runtime tras hidratación).
- **Adjacent bug1 bare-tenant e2e: 4/4 passed** (sin regresión en el redirect hermano).

## Gates (native Linux, NUNCA Docker)

| Gate | Resultado |
|---|---|
| `tsc --noEmit` (strict, full) | ✅ 0 errores |
| `eslint` (touched files) | ✅ 0 errores |
| `vitest run` (full) | ✅ 257 files / 2436 tests passed |
| arch fitness (shell-routes + subtab-keys + **no-clerk-organizations**) | ✅ 31/31 (el resolver lee `publicMetadata.tenant_id`, NO trip al no-Clerk-Orgs guard) |
| Playwright regression guard (live) | ✅ 8/8 determinístico |
| Playwright adjacent bug1 (live) | ✅ 4/4 sin regresión |

## DoD #37 (live-verify)

Ejercida la **acción real del usuario** (aterrizaje en `/` post-login) contra el stack corriendo, ×8, con efecto observado (shell montado, sin colgarse, sin refresh) + logs (FE 307 en `/`, BE forwarding sin 4xx/5xx). `dod_evidence` + `dev_app_verified.evidence` poblados en checkpoint. Chrome DevTools MCP estaba CAÍDO → cubierto con Playwright real-backend determinístico (no mock del surface). Eyeball manual de Chris = signoff G pendiente.

## Notas de scope / cross-brand

- Brand-local vitalia FE. Cero core/BE/otras marcas.
- nicolify/comunify pueden tener el mismo bug (shell `ssr:false` + root redirect). El helper `rootLandingRedirect`/`isAuthedRootPath` + `resolveTenantId` es candidato a lift cross-brand vía `/pm-luana` si reaparece. Por ahora vitalia-only (no escalado — fuera de scope de este bugfix).
