# Gherkin verification matrix — vitalia/vitalia-fase2-config-cuenta

> Auditor: /auditor Phase D (Opus orchestrator · consolida evidencia de auditor-backend iter 1-2 + auditor-frontend + E2E smoke run + live curls)
> Date: 2026-06-12
> Spec: 01-spec.md RONDA 2 (12 scenarios · § Matriz de cobertura)
> Verification bar: acción REAL ejercida + efecto observado (verification-real-not-200)

| Scenario (Gherkin) | RN | Test path / evidencia | Status | Notes |
|---|---|---|---|---|
| SC-01 happy: edita nombre → autosave + persist + audit | RN-4 | `e2e/shell-organism/config-cuenta.spec.ts::SC-04` (write real + reload persist) + `tests/.../test_account_audit_durability.py` (audit row REAL en DB) | **PASS** | Audit row live-confirmed ×2 por auditor-backend (count 1→2) |
| SC-02 fiscal inválido → 422 + NO persiste | RN-2 | `tests/.../test_account_router.py::test_patch_account_invalid_fiscal_id_returns_422` + `test_fiscal_id_validator.py` (hypothesis AR/PE/MX/CL/CO/UY) | **PASS** | Checksum AR CUIT/UY RUT mód-11 (Q1) |
| SC-03 cross-tenant → 404 | RN-5 | `tests/.../test_account_router.py` cross-tenant + auditor-backend live (tenant_B → 404, no leak) | **PASS** | tenant-scoped en repo (incl. get_active_for_tenant) |
| SC-04 RBAC no-admin → read-only + 403 | RN-1 | `tests/.../test_clinic_account_service.py` (403 non-write-role) + live 403 con rol `doctor` (debug session) | **PASS** | `_WRITE_ROLES={owner,admin_clinic}` alineado a canónico plataforma |
| SC-04b specialties editable (D3-revoked) → valida catálogo + persiste config_json | RN-3 | `test_specialty_catalog.py::validate_specialties` + live: PATCH `['odontologia-estetica','medicina-estetica']` → 200 → GET refleja (2026-06-12) + negativo live `['invalid-id']` → 422 + atomicidad (auditor-backend iter 2) | **PASS** | Persiste IDs en `tenant.config_json.clinic_config.primary_specialties` (engine-boundary RMW) |
| SC-05 timezone → autosave + persiste | RN-6 | `e2e::SC-02` (TimezoneSelect render) + `PreferencesView.test.tsx` + PATCH path compartido (campo en loop, contrato verificado) | **PASS** | `@luana/ui-kit timezone-select` (no `<select>` nativo) |
| SC-06 currency → autosave + símbolo | RN-6 | `e2e::SC-02` (CurrencySelector render) + `PreferencesView.test.tsx` | **PASS** | Sin hardcode 'USD' (fallback TenantLocale) |
| SC-07 idioma read-only | RN-3 | `e2e::SC-02` + `PreferencesView.test.tsx` (badge "definido en el alta") | **PASS** | Derivado del país; coerce None→es-419 back-compat |
| SC-08 país read-only | RN-3 | `e2e::SC-01` (ReadOnlyBadge) + `AccountDataView.test.tsx` | **PASS** | PATCH rechaza country (no está en PatchRequest) |
| SC-09 tipo clínica read-only | RN-3 | `e2e::SC-01` + `AccountDataView.test.tsx` | **PASS** | clinic_type vive en config_json, no editable acá |
| SC-10 DPO read-only + link Seguridad | — | `e2e::SC-03` (responsible-view + link seguridad) + `ResponsibleView.test.tsx` (empty state) | **PASS** | Q3: config_json.compliance.dpo o empty state |
| SC-11 abre Mi cuenta → datos reales (no placeholder) | — | `e2e::SC-01` (name input = 'Sanaré LATAM — Sede Principal' de BD) + CuentaPlaceholder retirado del PLACEHOLDER_MAP | **PASS** | Fix useAccountQuery (el form nacía vacío — cazado live) |
| SC-12 live-verify: write + persist + audit observable | RN-4 | E2E smoke 6/6 (Clerk real + BE real) + auditor-backend live ×2 + `test_account_audit_durability.py` integration | **PASS** | dod_evidence en checkpoint · audit row REAL (no structlog line) |

## Cobertura de business_rules (04-validators)

| RN | Cubierta por | Status |
|---|---|---|
| RN-1 RBAC | SC-04 | ✅ |
| RN-2 fiscal por país | SC-02 | ✅ |
| RN-3 read-only + specialties editables | SC-04b/07/08/09 | ✅ |
| RN-4 audit SYNC | SC-01/12 + integration test (durabilidad REAL post C9-1) | ✅ |
| RN-5 tenant-scoped | SC-03 | ✅ |
| RN-6 locale no hardcode | SC-05/06 | ✅ |

**12/12 PASS · 0 MISSING · 0 FAIL.** Matriz de cobertura del spec: happy-path completo `✅ construido` (cap_change_type=new → piso HARD cumplido).

## Ledger notes
- Visual goldens (cuenta-{datos,prefs,resp}.png): PENDIENTES — WARN no-bloqueante del auditor-frontend (mockup ratificado existe + 6/6 e2e funcional). → seguimiento en merge notes.
