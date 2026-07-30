# Gherkin verification matrix — vitalia/vitalia-crm-phi-base-tables-migration

> Auditor Phase D · 2026-05-30 · service-story BE
> Evidencia live: VERIFICATION-godmatrix-live.md (JWT real + conteos DB) · tests: gates GREEN

| Scenario (01-spec) | Ticket | Test path / evidencia | Status |
|---|---|---|---|
| SC-1 doctor → GET /patients/{id} 200 + audit row | T-2/T-3 | integration test_doctor_reads_patient_200_audit (skip-clean sin DB) + LIVE: 200, name descifrado len=20, audit read_patient rows 0→1→3 | ✅ PASS (live) |
| SC-2 marketing/recepcion → 403 | T-3 | integration test_marketing_403 + LIVE: marketing JWT real → 403 | ✅ PASS (live) |
| SC-3 migración idempotente (re-run = no-op) | T-1 | tests/migrations/test_035_crm_phi_base_tables_idempotency.py (GREEN) + LIVE: alembic upgrade head re-run no-op, head=035 | ✅ PASS |
| SC-4 cross-tenant 404 / cross-clinic 403 / forjado 401 | T-3 | integration test_cross_tenant_404 + test_cross_clinic_403 + LIVE: cross-tenant 403(role-reject)/not-found 404/forjado 401 | ✅ PASS (no-leak; cross-clinic 404 vs 403 = W-2 nuance, sin leak) |
| SC-5 PHI cifrado at-rest (round-trip) | T-2/T-3 | test_phi_repo_encrypt_decrypt.py (GREEN) + LIVE: raw name=88 octets magic byte 0xc3 (PGP ciphertext), API descifra para rol autorizado | ✅ PASS (live) |

**Verdict Phase D:** 5/5 scenarios PASS. Cobertura por código (tests) + verificación live real (JWT Clerk + conteos DB). Cero NO_COVERAGE.
