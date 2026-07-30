# Gherkin verification matrix — vitalia/vitalia-fase2-lisa-doctores (DELTA v3)

> Auditor: /auditor (Fable 5 sub-auditores + orchestrator consolidación) · Phase D
> Date: 2026-06-12T10:07:16.214452
> Cobertura: 41/41 SCs delta → ≥1 test cada uno. Suites: BE clinics 440/440 · FE lisa 501/501 + 139 targeted · e2e delta real-backend (switcher 6/6 · D3-C 3 · D3-E 4 · editor 4/4 · axe 2/2) · ui-kit 266/266.
> Build mayo (SC-1..11): matriz histórica en T-E2E-result.md (ciclo previo) — sin regresión (suites superset verdes).

| Scenario | Test path | Status | Notes |
|---|---|---|---|
| SC-D3A-1 | `frontend/e2e/regression/vitalia-fase2-lisa-doctores/staff-picker-switcher.spec.ts`, `frontend/src/features/lisa/components/staff/__tests__/staff-picker-wire.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3A-2 | `frontend/e2e/regression/vitalia-fase2-lisa-doctores/staff-picker-switcher.spec.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3A-3 | `frontend/e2e/regression/vitalia-fase2-lisa-doctores/staff-picker-switcher.spec.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3A-4 | `frontend/e2e/regression/vitalia-fase2-lisa-doctores/staff-picker-switcher.spec.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3B-1 | `backend/tests/modules/clinics/test_bio_files_api.py`, `backend/tests/modules/clinics/__pycache__/test_bio_files_api.cpython-312-pytest-9.0.3.pyc` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3B-2 | `backend/tests/modules/clinics/test_bio_files_api.py`, `backend/tests/modules/clinics/__pycache__/test_bio_files_api.cpython-312-pytest-9.0.3.pyc` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3B-3 | `frontend/e2e/regression/vitalia-fase2-lisa-doctores/bio-docs-d3b.spec.ts`, `frontend/src/features/lisa/components/staff/workspace/perfil/BioRepoInputs.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3B-4 | `backend/tests/modules/clinics/test_bio_files_api.py`, `backend/tests/modules/clinics/__pycache__/test_bio_files_api.cpython-312-pytest-9.0.3.pyc` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3B-5 | `frontend/e2e/regression/vitalia-fase2-lisa-doctores/bio-docs-d3b.spec.ts`, `frontend/src/features/lisa/components/staff/workspace/perfil/BioRepoInputs.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3C-1 | `frontend/e2e/regression/vitalia-fase2-lisa-doctores/horarios-occurrences-d3c.spec.ts`, `frontend/src/features/lisa/api/__tests__/staff-occurrences-api.test.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3C-2 | `backend/tests/modules/clinics/__pycache__/test_availability_occurrences.cpython-312-pytest-9.0.3.pyc`, `backend/tests/modules/clinics/test_availability_occurrences.py` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3C-3 | `backend/tests/modules/clinics/__pycache__/test_availability_occurrences.cpython-312-pytest-9.0.3.pyc`, `backend/tests/modules/clinics/test_availability_occurrences.py` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3C-4 | `backend/tests/modules/clinics/__pycache__/test_availability_occurrences.cpython-312-pytest-9.0.3.pyc`, `backend/tests/modules/clinics/test_availability_occurrences.py` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3C-5 | `frontend/e2e/regression/vitalia-fase2-lisa-doctores/horarios-occurrences-d3c.spec.ts`, `frontend/src/features/lisa/api/__tests__/staff-occurrences-api.test.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3C-6 | `frontend/e2e/regression/vitalia-fase2-lisa-doctores/horarios-occurrences-d3c.spec.ts`, `frontend/src/features/lisa/api/__tests__/staff-occurrences-api.test.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3C-7 | `frontend/e2e/regression/vitalia-fase2-lisa-doctores/horarios-occurrences-d3c.spec.ts`, `frontend/src/features/lisa/api/__tests__/staff-occurrences-api.test.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3C-8 | `backend/tests/modules/clinics/__pycache__/test_availability_occurrences.cpython-312-pytest-9.0.3.pyc`, `backend/tests/modules/clinics/test_availability_occurrences.py` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-1 | `frontend/e2e/specs/a11y/pagina-publica-axe.spec.ts`, `frontend/e2e/specs/pagina-publica-editor.spec.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-2 | `frontend/src/features/lisa/components/staff/workspace/pagina/DoctorPaginaView.test.tsx`, `backend/tests/modules/clinics/__pycache__/test_public_doctor_profile_endpoint.cpython-312-pytest-9.0.3.pyc` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-3 | `frontend/src/features/lisa/components/staff/workspace/pagina/DoctorPaginaView.test.tsx`, `backend/tests/modules/clinics/__pycache__/test_public_doctor_profile_endpoint.cpython-312-pytest-9.0.3.pyc` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-4 | `frontend/src/features/lisa/components/staff/workspace/pagina/DoctorPaginaView.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-5 | `frontend/src/features/lisa/components/staff/workspace/pagina/DoctorPaginaView.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-6 | `frontend/src/features/lisa/components/staff/workspace/pagina/DoctorPaginaView.test.tsx`, `backend/tests/modules/clinics/__pycache__/test_public_doctor_profile_endpoint.cpython-312-pytest-9.0.3.pyc` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-7 | `frontend/src/features/lisa/components/staff/workspace/pagina/DoctorPaginaView.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-8 | `frontend/src/features/lisa/components/staff/workspace/pagina/DoctorPaginaView.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-9 | `frontend/src/features/lisa/components/staff/workspace/pagina/PublicLinkBar.test.tsx`, `backend/tests/modules/clinics/__pycache__/test_public_doctor_profile_endpoint.cpython-312-pytest-9.0.3.pyc` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-10 | `frontend/src/features/lisa/components/staff/workspace/pagina/PublicLinkBar.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-11 | `frontend/src/features/lisa/components/staff/workspace/pagina/PublicLinkBar.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-12 | `frontend/src/features/lisa/components/staff/workspace/pagina/PublicLinkBar.test.tsx`, `backend/tests/modules/clinics/__pycache__/test_public_doctor_profile_endpoint.cpython-312-pytest-9.0.3.pyc` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-13 | `frontend/e2e/specs/a11y/pagina-publica-axe.spec.ts`, `frontend/e2e/specs/pagina-publica-editor.spec.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-14 | `frontend/src/features/lisa/components/staff/workspace/pagina/PublicLinkBar.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3D-15 | `frontend/src/features/lisa/components/staff/workspace/pagina/PublicLinkBar.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3E-1 | `frontend/e2e/specs/horarios-month-view.spec.ts`, `frontend/src/features/lisa/components/staff/__tests__/month-calendar.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3E-2 | `frontend/e2e/specs/horarios-month-view.spec.ts`, `frontend/src/features/lisa/components/staff/__tests__/month-calendar.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3E-3 | `frontend/e2e/specs/horarios-month-view.spec.ts`, `frontend/src/features/lisa/components/staff/__tests__/month-calendar.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3E-4 | `frontend/e2e/specs/horarios-month-view.spec.ts`, `frontend/src/features/lisa/components/staff/__tests__/month-calendar.test.tsx` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3F-1 | `backend/tests/modules/clinics/__pycache__/test_availability_occurrences.cpython-312-pytest-9.0.3.pyc`, `backend/tests/modules/clinics/test_availability_occurrences.py` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3F-2 | `backend/tests/modules/clinics/__pycache__/test_availability_occurrences.cpython-312-pytest-9.0.3.pyc`, `backend/tests/modules/clinics/test_availability_occurrences.py` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3F-3 | `frontend/src/features/lisa/components/staff/workspace/horarios/__tests__/recurrence-summary.test.ts`, `frontend/src/features/lisa/api/__tests__/staff-blocks-api.test.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3F-4 | `backend/tests/modules/clinics/__pycache__/test_availability_occurrences.cpython-312-pytest-9.0.3.pyc`, `backend/tests/modules/clinics/test_availability_occurrences.py` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |
| SC-D3F-5 | `frontend/e2e/specs/lisa-recurrencia-chips.spec.ts` | PASS | suite verde (BE 440 · FE 501+139 · e2e delta live) |

**Huecos:** ninguno. **MISSING:** ninguno. Verificación REAL: writes ejercidos live (dod_evidence ×7 checkpoint + e2e real-backend anti-burbuja base.ts).
