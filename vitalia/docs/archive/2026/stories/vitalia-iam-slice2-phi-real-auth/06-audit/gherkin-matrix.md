# Gherkin verification matrix — vitalia/vitalia-iam-slice2-phi-real-auth

> Auditor: Phase D · Date: 2026-05-30

| Scenario (Gherkin) | Test path | Live (anti-teatro) | Status |
|---|---|---|---|
| SC-1 happy — doctor JWT real ve PHI | test_phi_real_auth.py::test_doctor_jwt_real_sees_phi | JWT real Clerk → GET /crm/conversations **200** | ✅ PASS |
| SC-2 negative — recepcion/marketing → 403 | test_phi_real_auth.py::{test_recepcion_403,test_marketing_403} | marketing real JWT → **403** | ✅ PASS |
| SC-3 edge — cross-tenant 404 / cross-clinic 403 | test_phi_real_auth.py::{test_cross_tenant_404,test_cross_clinic_403} | doctor cross-tenant → **403** (sin rol, no leak) | ✅ PASS |
| SC-4 adversarial — JWT inválido/expirado/stub-legacy → 401 | test_phi_real_auth.py::{test_invalid_token_401,test_expired_token_401,test_legacy_stub_token_rejected} | forjado → **401** · stub legacy → **401** | ✅ PASS |

**4/4 scenarios PASS** (integration 49 passed × 7 random seeds + verificación live god-matrix con JWT real). Detalle live: `VERIFICATION-godmatrix-live.md`.
