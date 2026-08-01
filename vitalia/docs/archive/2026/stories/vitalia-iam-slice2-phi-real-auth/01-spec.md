---
story_id: vitalia-iam-slice2-phi-real-auth
brand: vitalia
type: service-story
state: refining
po_version: 2
cap_target: iam-scaffold-slice-1
cap_change_type: extend
architecture_pattern: ADR-vitalia-004
adr_004_compliance: n/a-with-rationale
ratified_by_chris: true   # v2 ratificado 2026-05-30 (Q1 incluir FE / Q2 stub env-gated / Q3 proceder)
prior_story: vitalia-stub-caps-scenario-backfill
last_modified: 2026-05-30
---

> **★ v2 ratificado Chris 2026-05-30:** Q1 → **incluir** el switch FE (rol desde `/me`) en esta story. Q2 → **stub test-only env-gated** (`VITALIA_AUTH_STUB=1` solo en tests; runtime/dev-app SIEMPRE JWKS real). Q3 → proceder a `/architect` (build supervisado, autonomous_mode false).

# 01-spec — Slice 2 PHI: decoder JWT real (JWKS) + rol desde DB + repos reales

## Context

**Origen:** hallazgo de `vitalia-stub-caps-scenario-backfill` (done). Las superficies PHI (`crm`, `clinics`, `inbox`, `marketing`) usan un **decoder STUB Slice-1** (`vitalia/backend/src/modules/vitalia/iam/infrastructure/clerk_jwt_decoder.py`) que:
- Solo acepta tokens `stub:{tenant}:{clinic}:{role}:{user}` y **rechaza el JWT real de Clerk → 401** (confirmado empíricamente).
- Saca el rol del propio token (no de `user_tenants`).
- Los routers PHI usan repos `AsyncMock()` (sin DB) en algunos paths.

Mientras siga stub, **ningún cap PHI puede verificarse live en dev-app** (el FE manda JWT real → 401). Slice 2 desentuba esto **reusando el JWKS del engine** (anti-duplication) + hace fluir el rol desde DB + cablea repos reales.

## Objetivo

Reemplazar el decoder stub por verificación **JWKS real reusando `core/luana-core-iam`**, hacer que el rol venga de `user_tenants.role` (DB), cablear repos reales (DI), y mantener HIPAA-lite (dual filter tenant+clinic, audit log sync, `@require_phi_access`). Verificación final con la **god-matrix** (8 usuarios RBAC sobre Sanaré, seed ya existente).

## Prior art applied (anti-duplication-refining)

- **REUSE engine JWKS:** `core/luana-core-iam/src/luana_core_iam/application/auth.py::verify_token_payload(token) -> dict` (usa `jwt.PyJWKClient(JWKS_URL)`, RS256, leeway 60s, `verify_aud: False` para dev). El decoder vitalia lo IMPORTA — NO recrea PyJWKClient ni la lógica JWKS.
- **REUSE rol DB:** `core/luana-core-iam/.../repositories/user_tenant_repository.py` + `user_tenant_model.py` (`user_tenants.role`). El rol se resuelve desde DB por `(user_id, tenant_id)`, NO del token.
- **MANTENER contrato brand:** `ClerkJwtPayload` dataclass + `VitaliaRole` domain (`vitalia/.../iam/domain/role.py`) se preservan — los consumers no cambian su interfaz.
- **REUSE fixture verificación:** god-matrix (8 usuarios Sanaré, `vitalia/backend/scripts/seed_test_users_link.py`, password `<VITALIA_TEST_USERS_PASSWORD — pedir a Chris>`, tenant Sanaré `e69a691d-…`, clinic `f035be5b-…`).
- **Engine boundary:** consume engine vía import; NO edita `core/luana-core-*/src/`. Si requiere cambio engine → escala /pm-luana (no esperado).

## Consumers afectados (cablear repos reales)

`crm/api/router.py` + `crm/api/consent_endpoints.py` · `marketing/api/routes.py` + `marketing/api/deps.py` · `inbox/api/router.py` · `iam/application/services/clinic_resolver.py` (hoy saca rol del token → debe sacarlo de DB).

## Decisión a ratificar — 3ª inconsistencia de rol (FE source)

Hoy: FE lee `publicMetadata.role` (Clerk), BE engine lee `user_tenants.role` (DB). El seed los dejó alineados, pero la doble fuente es deuda. **Propuesta:** el FE toma el rol del BE (`/api/v1/iam/users/me` ya devuelve `role`) → 1 sola fuente de verdad (DB). ¿Ratificás incluir el switch FE en esta story o lo dejamos como follow-up? (Default propuesto: incluir el cambio FE mínimo — `useRole` lee de `/me`, no de Clerk metadata.)

## Definición de DONE

1. El decoder vitalia verifica el **JWT real de Clerk vía JWKS del engine** (reuse `verify_token_payload`). Un JWT válido → payload verificado; inválido/expirado → 401 honesto.
2. El rol fluye desde `user_tenants.role` (DB) al `ClinicContext` (no del token). `clinic_id` desde header `X-Clinic-ID` (FE ya lo manda en `AuditedSection.tsx`).
3. Repos reales cableados (DI FastAPI `Depends`) en crm + consent + marketing + inbox (cero `AsyncMock` en runtime).
4. HIPAA-lite respetado: dual filter `tenant_id + clinic_id` en queries PHI, audit log sync write pre-response, sanitization en traces, `@require_phi_access(roles=[doctor,nurse,admin_clinic])`.
5. **Verificación god-matrix (anti-teatro, deployed):** doctor.demo ve PHI (200 + efecto + audit row), recepcion/marketing → 403, cross-tenant → 404, cross-clinic → 403. Ejercido con **JWT real** (mint vía Clerk Backend API o login dev-app) + logs backend leídos.
6. **(RATIFICADO — in scope)** FE toma rol de `GET /api/v1/iam/users/me` (1 fuente de verdad DB), no de Clerk `publicMetadata.role`. Cambio mínimo en el hook de rol FE.

## Scenarios (4/4 obligatorios · graders ejecutables)

### SC-1 · happy — doctor con JWT real ve PHI
- **given:** doctor.demo (rol `doctor` en user_tenants para Sanaré) con JWT real de Clerk + X-Tenant-ID Sanaré + X-Clinic-ID sanare-principal.
- **when:** GET a un endpoint PHI (ej. crm pacientes).
- **then:** 200 + data filtrada por tenant+clinic + audit_log row escrito (action+user+timestamp) + rol resuelto desde DB (no token).
- **graders:**
  - `{ type: integration, path: "vitalia/backend/tests/integration/test_phi_real_auth.py::test_doctor_jwt_real_sees_phi" }`
  - `{ type: state_check, target: db, query: "SELECT 1 FROM vitalia_audit_log WHERE user_id=... AND action LIKE 'phi.%'" }`
  - `{ type: manual_audit, who: claude-dev-app, expect: "JWT real minteado (Clerk Backend API) → GET PHI 200 + log backend sin 401" }`

### SC-2 · negative — rol no autorizado (recepcion/marketing) → 403
- **given:** recepcion@ (rol `recepcion`) o marketing.demo (rol `marketing`) con JWT real válido.
- **when:** GET endpoint PHI.
- **then:** 403 (rol sin PHI access) + NO leak de data + audit log del intento denegado.
- **graders:** `{ type: integration, path: ".../test_phi_real_auth.py::test_recepcion_403" }` + `{ type: manual_audit, expect: "recepcion JWT real → 403 + log denied" }`

### SC-3 · edge — cross-tenant / cross-clinic bloqueado
- **given:** doctor.demo (Sanaré) con JWT real.
- **when:** request con X-Tenant-ID de OTRO tenant (cross-tenant) o X-Clinic-ID de otra clínica del mismo tenant (cross-clinic).
- **then:** cross-tenant → 404 (no leak); cross-clinic → 403. audit log del intento.
- **graders:** `{ type: integration, path: ".../test_phi_real_auth.py::test_cross_tenant_404" }` + `{ ...::test_cross_clinic_403 }`

### SC-4 · adversarial — JWT inválido/expirado/forjado → 401
- **given:** token inválido (firma mala / expirado / `stub:...` legacy / Authorization ausente).
- **when:** request a endpoint PHI.
- **then:** 401 honesto (vía JWKS verify) — NUNCA bypass. Sin leak en error body. (El stub `stub:...` legacy YA no se acepta en runtime — solo JWKS real.)
- **graders:** `{ type: integration, path: ".../test_phi_real_auth.py::test_invalid_token_401" }` + `{ type: manual_audit, expect: "JWT forjado → 401" }`

## Acceptance gates (resumen)

```bash
WS=$(git rev-parse --show-toplevel); cd ${WS}
cd vitalia/backend && ${WS}/.venv/bin/pytest tests/integration/test_phi_real_auth.py tests/architecture/test_phi_dual_filter.py -v
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/ruff check src/modules/vitalia/{iam,crm,marketing,inbox}/ && ${WS}/.venv/bin/pytest tests/architecture/ -q
# Verificación god-matrix con JWT real (mint Clerk Backend API — ver handoff) contra dev-app:
#   doctor.demo → PHI 200 ; recepcion → 403 ; cross-tenant → 404 ; logs leídos
```

## Open questions — RESUELTAS (Chris 2026-05-30)

- **Q1 — FE role source** → RESUELTA: **incluir** en Slice 2. El hook de rol FE lee de `GET /api/v1/iam/users/me` (devuelve `role`) en vez de `publicMetadata.role` de Clerk → 1 sola fuente de verdad (DB). Cambio FE mínimo (DONE point 6).
- **Q2 — stub en tests** → RESUELTA: **stub test-only env-gated**. Runtime/dev-app SIEMPRE JWKS real (cero bypass). Los tests optan al stub vía `VITALIA_AUTH_STUB=1` explícito (documentado, NUNCA en runtime). El decoder: si `VITALIA_AUTH_STUB=1` Y token empieza con `stub:` → parse stub (solo test); en cualquier otro caso → JWKS real. Arch test debe verificar que el runtime no setea esa env.
- **Q3 — alcance repos** → el architect confirma en el ready package que los repos reales existen para crm/marketing/inbox; si alguno falta → lo marca sub-scope explícito (no se inventa repo nuevo sin nota).

## Próximo paso

`/architect` produce ready package → build **SUPERVISADO** (autonomous_mode false: auth/PHI). Verificación final god-matrix con JWT real (anti-teatro): doctor PHI 200 / recepcion 403 / cross-tenant 404 — ejercido + logs. El orchestrator reporta a Chris en el gate de verificación PHI antes de cerrar.
