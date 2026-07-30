# 07-merge — vitalia-iam-slice2-phi-real-auth

> Fase F MERGE · /pm-vitalia · 2026-05-30 · state reviewing → done

## § 1 — Gherkin verification matrix

(copia de `06-audit/gherkin-matrix.md`)

| Scenario | Test | Live (anti-teatro) | Status |
|---|---|---|---|
| SC-1 doctor JWT real ve PHI | test_phi_real_auth.py::test_doctor_jwt_real_sees_phi | JWT real → GET /crm/conversations **200** | ✅ PASS |
| SC-2 recepcion/marketing → 403 | ::{test_recepcion_403,test_marketing_403} | marketing real → **403** | ✅ PASS |
| SC-3 cross-tenant 404 / cross-clinic 403 | ::{test_cross_tenant_404,test_cross_clinic_403} | doctor cross-tenant → **403** (no leak) | ✅ PASS |
| SC-4 inválido/expirado/stub-legacy → 401 | ::{test_invalid_token_401,test_expired_token_401,test_legacy_stub_token_rejected} | forjado → **401** · stub → **401** | ✅ PASS |

**4/4 PASS** (integration 49 passed × 7 random seeds + verificación live god-matrix con JWT real de Clerk).

## § 2 — Playwright E2E run

N/A (service-story BE-auth + 1 hook FE; sin ruta UI nueva). **Verificación equivalente = god-matrix live** con JWT real de Clerk Backend API contra dev-app (`VERIFICATION-godmatrix-live.md`):

```
doctor.demo JWT real → GET /api/v1/crm/conversations → HTTP 200
marketing.demo JWT real → HTTP 403
doctor cross-tenant → HTTP 403 (no leak)
token forjado → HTTP 401 · stub legacy → HTTP 401
```

FE hook: vitest 6/6 (useCurrentUser success/loading/error) + tsc 0 + eslint 0.

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/iam/iam-scaffold-slice-1.yaml` — **cap_change_type: extend**:
  - change_log entry `type: extend` (story vitalia-iam-slice2-phi-real-auth)
  - 4 scenarios nuevos appendeados (sc1-doctor-jwt-real-ve-phi, sc2-rol-no-autorizado-403, sc3-cross-tenant-cross-clinic-bloqueado, sc4-jwt-invalido-401) con `added_in_story` + `e2e_test` reales
  - `dev_preview.e2e_test` → `test_phi_real_auth.py` (era null) + fixtures god-matrix
  - surface narrativa: ClerkJwtDecoder stub → **JWKS real** (reusa engine)
  - `last_modified: 2026-05-30`

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/iam.md` — auto-list regen post-merge (reconcile_capabilities). Narrativa: decoder JWKS real + rol desde DB + repos PHI reales.

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel); cd ${WS}/vitalia/backend
# Tests deterministas (monkeypatch verify_token_payload):
${WS}/.venv/bin/pytest tests/integration/test_phi_real_auth.py tests/architecture/test_auth_stub_env_gate.py -v   # 49 passed
${WS}/.venv/bin/pytest tests/architecture/ -q                                                                    # 324 passed
${WS}/.venv/bin/ruff check src/modules/vitalia/{iam,crm,marketing,inbox}/                                        # clean

# Verificación REAL live (anti-teatro · requiere dev-app up + CLERK_SECRET_KEY):
#   mint JWT real: POST https://api.clerk.com/v1/sessions {user_id} → POST /v1/sessions/{id}/tokens
#   doctor.demo (user_3EQJjxsvxiZ5exQjucSB651xnUd) → GET /api/v1/crm/conversations + X-Tenant-ID Sanaré → 200
#   marketing.demo → 403 · forjado → 401 · stub:... → 401
#   (detalle: VERIFICATION-godmatrix-live.md)

# FE:
cd ${WS}/vitalia/frontend && npx vitest run src/hooks/__tests__/useCurrentUser.test.tsx && npx tsc --noEmit
```

## Commits

- T-1 `ad5957f2` — decoder JWKS real + rol desde DB
- T-2 `744ea896` — repos PHI reales DI + SC-2/SC-3
- T-3 `af3c6fda` — useCurrentUser rol desde /me
- verificación + developed `d55f5b24` · audit `88d0ceb0`

## Follow-ups (NO bloquean — observed-bug 2026-05-30)

- Tablas base `vitalia_patients` + `vitalia_leads` faltan en DB dev → endpoints paciente/lead dan 500 (pre-existente, gap de migración dev, ajeno al scope auth). Candidato a story de migración/seed dev. El audit-on-patient quedó probado por código (`patient_repository.py` escribe AuditLogEntry) + integration tests, no live (bloqueado por tabla faltante).
