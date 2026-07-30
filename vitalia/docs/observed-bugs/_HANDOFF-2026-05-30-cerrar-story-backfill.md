<!-- voseo-allowed: handoff técnico interno entre sesiones, no es texto user-facing -->
# HANDOFF · 2026-05-30 · cerrar bien la story `vitalia-stub-caps-scenario-backfill`

> Archivo TEMPORAL de traspaso entre sesiones (borrar cuando se consuma). NO es memory.
> Worktree: `~/Proyectos/luana-vitalia` · branch `wip/vitalia` (HUB único, ADR-009).
> Supersede a `_HANDOFF-2026-05-29-lisa-marca-verificacion.md` (ya consumido — se puede borrar).

## Objetivo de la próxima conversación
**Cerrar BIEN** la user story `vitalia-stub-caps-scenario-backfill` (20 caps "declarados live" → **verificados live de verdad**). "Bien" = con el bar anti-teatro que Chris fijó: **ejercer la acción real + leer logs + confirmar efecto, en dev-app cuando aplique** (NO "saqué 200 = funciona"). P1 splitter NO se toca (ya arreglado). Hacer todo a criterio: lo mejor para el usuario, mantenible y escalable.

## REGLA DE ORO (cementada · `.claude/rules/test-design-doctrine.md` § "Verificación REAL ≠ HTTP 200")
Nada se declara "funciona/verified-live" por un GET 200. Para cada cap: **ejercer la acción real (especialmente writes), leer los logs del backend, confirmar el efecto (DB/render/persistencia al recargar)**. e2e que mockean el backend del surface = falso verde. Caso origen: lisa-marca shippeó "LIVE" con suite mockeada → 3 bugs reales.

---

## ✅ Lo que YA quedó listo esta sesión (commit `f8d7e313`, pusheado)

### P2 — Matriz de usuarios de prueba RBAC (god-matrix) — CERRADO y verificado
8 usuarios de prueba sobre el tenant demo **Sanaré** (`e69a691d-070e-5caf-a053-6e74642ec100`), **DB ↔ Clerk alineados**, vía RBAC real (sin bypass):

| usuario | rol (user_tenants + Clerk publicMetadata.role) | PHI |
|---|---|---|
| owner.demo@vitalialat.com | owner | — |
| admin.clinic.demo@vitalialat.com | admin_clinic | ✅ |
| doctor.demo@vitalialat.com | doctor | ✅ |
| nurse.demo@vitalialat.com | nurse | ✅ |
| marketing.demo@vitalialat.com | marketing | — |
| dr.demo@vitalialat.com *(intacto, legacy)* | owner | — |
| recepcion@vitalialat.com | recepcion | — |
| admin@vitalialat.com | super_admin (×3 tenants) | — |

- **Password** (los nuevos): `VitaliaRoles2026!`. dr.demo legacy mantiene `DrDemo2026!`.
- **Clínica branch** seedeada en Sanaré: `f035be5b-0ac4-5210-8fc3-395650ca2b83` (slug `sanare-principal`) → es el `clinicId` para `X-Clinic-ID` (dual-filter PHI) y `useClinicId` (FE).
- **SSoT idempotente**: `vitalia/backend/scripts/seed_test_users_link.py`. Reconstruye todo (Clerk + DB) con un comando (abajo). Lint/format limpios.
- **Verificado ejerciendo** (no 200 a secas): minté JWT real de Clerk para doctor.demo → `GET /me` 200, body `role:"doctor"`, mapeo DB correcto, log `200 OK`.

### Cómo re-correr el seed (host, full sync Clerk + DB)
```bash
cd ~/Proyectos/luana-vitalia
SK=$(grep -E '^CLERK_SECRET_KEY=' vitalia/.env.dev | head -1 | cut -d= -f2-)
CLERK_SECRET_KEY="$SK" POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5435 POSTGRES_DB=vitalia_dev \
POSTGRES_USER=postgres POSTGRES_PASSWORD=password \
.venv/bin/python vitalia/backend/scripts/seed_test_users_link.py --clerk-sync
```

---

## 🔑 Datos/claves que necesitás (auth + infra)

- **Clerk dev**: `CLERK_SECRET_KEY=sk_test_w93s1hJ4…` está en `vitalia/.env.dev` (línea `CLERK_SECRET_KEY=`). Issuer: `https://moral-gator-27.clerk.accounts.dev`. **Trampa real**: la API de Clerk está detrás de Cloudflare → el `User-Agent` por defecto de `Python-urllib` da **403 (CF error 1010)**. Usá un UA tipo `curl/...` o `vitalia-seed/1.0` (ya resuelto en el seed script).
- **Ejercer auth REAL sin browser** (para verificación anti-teatro): minteá un session token vía Clerk Backend API y golpeá el backend:
  ```bash
  SK=$(grep -E '^CLERK_SECRET_KEY=' vitalia/.env.dev | head -1 | cut -d= -f2-)
  DOCTOR=user_3EQJjxsvxiZ5exQjucSB651xnUd   # doctor.demo
  sid=$(curl -s -X POST https://api.clerk.com/v1/sessions -H "Authorization: Bearer $SK" -H "Content-Type: application/json" -d "{\"user_id\":\"$DOCTOR\"}" | jq -r .id)
  JWT=$(curl -s -X POST https://api.clerk.com/v1/sessions/$sid/tokens -H "Authorization: Bearer $SK" -d '{"expires_in_seconds":300}' | jq -r .jwt)
  curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $JWT" -H "X-Tenant-ID: e69a691d-070e-5caf-a053-6e74642ec100" http://localhost:8002/api/v1/iam/users/me
  ```
  (La sesión queda `pending` pero el JWT verifica por JWKS para los endpoints del engine. Para verificación visual real, mejor login en dev-app con email+password.)
- **Stack docker**: PG `luana-dev-luana_postgres_dev-1` (host `127.0.0.1:5435`, in-container `luana_postgres_dev:5432`, db `vitalia_dev`, postgres/password) · BE `luana-dev-vitalia_backend_dev-1` (:8002) · FE :3002 · cloudflared → **dev-app.vitalialat.com**.
- **Logs**: `docker logs luana-dev-vitalia_backend_dev-1 --tail 60 | grep -iE '4..|5..|traceback|error|denied|does not exist'`.

---

## 🚧 Bloqueo arquitectónico que destrabé (es lo PRIMERO a resolver) — Slice 2 PHI

Las superficies **PHI** (`crm`, `clinics`, `inbox`, `marketing`) usan un **decoder STUB de Slice-1** que:
- Solo acepta tokens `stub:{tenant}:{clinic}:{role}:{user}` y **RECHAZA el JWT real de Clerk → 401** ("Token inválido o expirado"). Confirmado empíricamente.
- Usa repos `AsyncMock()` (sin DB). El rol sale del propio token, no de `user_tenants`.

Mientras esto siga stub, **ningún cap PHI puede ser "verified-live en dev-app"** (el FE manda JWT real → 401). Por eso Slice 2 es prerequisito para cerrar bien los caps PHI del backfill.

**Slice 2 (story propia vía `/pm-vitalia` → /architect → /dev-team):**
- Reemplazar `vitalia/backend/src/modules/vitalia/iam/infrastructure/clerk_jwt_decoder.py` (stub) por verificación **JWKS real** — **reusar** lo que ya existe en el engine: `core/luana-core-iam/src/luana_core_iam/application/auth.py` (`verify_token_payload`, `PyJWKClient`). NO recrear (anti-duplication).
- Hacer fluir el rol desde `user_tenants.role` (DB) al `ClinicContext` (hoy `ClinicResolver.resolve` lo saca del token). El `clinic_id` viene del header `X-Clinic-ID` (FE ya lo manda en `AuditedSection.tsx`).
- Cablear **repos reales** (DI vía FastAPI `Depends`) en `crm/api/router.py` + `consent_endpoints.py` + marketing/inbox (hoy `AsyncMock`).
- Respetar HIPAA-lite (`vitalia/.claude/rules/hipaa-lite.md`): dual filter tenant+clinic, audit log sync, sanitization, `@require_phi_access`.
- **Cerrar la 3ª inconsistencia** de rol: FE lee `publicMetadata.role`, BE engine lee `user_tenants.role`. Decisión a tomar: que el FE tome el rol del BE (`/me` ya devuelve `role`) en vez de Clerk metadata → 1 sola fuente de verdad. (Hoy quedaron alineados por el seed, pero la doble fuente es deuda.)
- Verificación anti-teatro: doctor.demo ve PHI (200 + efecto), recepcion/marketing → 403, cross-tenant/cross-clinic → 404/403, audit_log row escrito. Ejercido con auth real + logs.

## 📋 La story a cerrar — `vitalia-stub-caps-scenario-backfill`

- **Estado**: `refining`, phase `REFINING_SPEC_REVISION_V2`, `autonomous_mode:false` (pausado), `ratified_by_chris:false`. Path: `vitalia/docs/product/stories/vitalia-stub-caps-scenario-backfill/{checkpoint.md, chris-input.md, 01-spec.md, 03-arch.md(parcial)}` (01-spec.md + 03-arch.md están **untracked** — commitearlos al avanzar).
- **Scope**: 20 caps que computan stub/declared-live → verified-live, en 3 baterías: **A** (UI wire) · **B** (admin wire) · **C** (infra pytest). **T-0** = extender `scripts/validate_code_cap_bidirectional.py` cross_check_3 para reconocer pytest (`.py` con `def test_`; hoy solo JS `test(`). `scripts/compute_capability_status.py` NO necesita cambio.
- **Decisiones YA ratificadas por Chris (v2 del spec, falta escribirlas)**: (1) smoke **REAL contra dev-app** (no solo local/mocks), (2) **fix-to-green dentro de la story** (los 20 deben funcionar de verdad; si están rotos, arreglar), (3) **anti-teatro**: correr-verde + relevancia por cada `e2e_test`.
- **Gate mecánico**: `verified-live` = `live` + TODO scenario con `e2e_test` que EXISTE en disco + el archivo contiene `test(`/`test.describe(` o (post-T-0) `def test_`. Schema golden de `scenarios[]`: `vitalia/docs/product/capabilities/auth/clerk-middleware.yaml`.
- **Decisión pendiente clave**: estratificar los 20 caps en **UI-visible / admin / infra-pytest / backend-justificado**, y marcar cuáles son **PHI → bloqueados por Slice 2** (no se pueden verificar live hasta desentubar). El stub PHI hallado obliga a esta estratificación.

## 🔭 Plan sugerido para cerrar (secuencia)
1. **Slice 2 PHI** (story nueva vía `/pm-vitalia`): desentubar → JWKS + rol de `user_tenants` + repos reales. Verificar con la god-matrix. **Prerequisito de los caps PHI del backfill.**
2. **Backfill spec v2** (`/pm-vitalia` → encadena `/po` o /po-ux): reescribir `01-spec.md` con bar deployed-visible + estratificación (marcando PHI-bloqueados-por-Slice-2 si Slice 2 no se hizo aún) + reporte de verificación por-cap. Re-ratificar.
3. `/architect` (authored directo, no orchestrator) → `06-tickets` con T-0 (gate) + T-A/T-B/T-C.
4. `/dev-team` autónomo (fix-to-green) → `/auditor` → `/pm-vitalia` merge → `done` + archive.
5. **Verificación final en dev-app** por cada cap (anti-teatro): ejercer la acción real + logs. Reporte por-cap en la story.

## Observaciones sueltas (no perseguidas)
- En logs aparece `PUT /api/v1/lisa/marca/personality 405` desde IP externa = tu browser con JS viejo del fix PUT→PATCH (commit `61f1049c`). Probablemente necesita **hard-refresh** o rebuild del contenedor FE. No es bug nuevo.
- `GET /api/v1/scheduling/agenda/grid?view=semana&date=... → 422` repetido en logs (posible bug agenda, sin investigar — su propia story).
- Dejé una sesión Clerk `pending` (sess_3EQJwTEau5l4nrwffZeMUOAuYsh) de testing — inocua, expira sola. Revocable si molesta.

## Doctrina / rules a tener presentes
- `.claude/rules/test-design-doctrine.md` § Verificación REAL ≠ HTTP 200 (la regla de oro).
- `.claude/rules/anti-duplication.md` (Slice 2 REUSA el JWKS del engine, no recrea).
- `.claude/rules/anti-orphan-integration.md` (CONN: nada llega a done como isla).
- `vitalia/.claude/rules/hipaa-lite.md` (dual filter + audit + RBAC PHI).
- `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` (ADR-vitalia-004 para sub-tabs UI).
- Hub único + commit por pathspec (`scripts/git/commit-paths.sh`), nunca `git add .`.
