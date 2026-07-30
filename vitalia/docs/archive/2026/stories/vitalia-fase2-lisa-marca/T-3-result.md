# T-3 Result — BE pytest dual-tenant + arch fitness creep guards

**Story:** vitalia-fase2-lisa-marca (F2-S7)
**Ticket:** T-3
**Surface:** Tests only (`production_code: false`)
**State:** pushed
**Commit SHA:** d324517a
**Date:** 2026-05-27

---

## Resultados

| Metric | Value |
|---|---|
| Tests NEW (unit) | 83 pass |
| Tests skipped (integration, Postgres required) | 14 skip |
| Arch fitness full suite | 314 pass / 0 fail |
| Lint (`ruff check`) | 0 errors |
| Format (`ruff format --check`) | 0 files to reformat |

---

## Deliverables producidos

### Arch fitness (3 nuevos tests permanentes)

| Archivo | Tests | Propósito |
|---|---|---|
| `vitalia/backend/tests/architecture/test_no_health_voice_validator.py` | 3 | D2-voice anti-creep: health_voice_validator MUST NOT exist |
| `vitalia/backend/tests/architecture/test_no_brand_voice_summary_table.py` | 4 | D2-voice anti-creep: brand_voice_summary table MUST NOT exist |
| `vitalia/backend/tests/architecture/test_brand_studio_module_ddd.py` | 10 | DDD purity brand_studio (domain pure, infra no forward, cross-module ban) |

### Módulo brand_studio (8 nuevos archivos de test)

| Archivo | Tests | Validators cubiertos |
|---|---|---|
| `tests/modules/vitalia/brand_studio/test_voice_preview_service.py` | 13 | `be_test_voice_preview_cache` |
| `tests/modules/vitalia/brand_studio/test_trust_catalog_service.py` | 15 | `be_test_trust_catalog_pe` |
| `tests/modules/vitalia/brand_studio/test_voice_warning_audit_log.py` | 12 | `be_test_voice_warning_audit` |
| `tests/modules/vitalia/brand_studio/test_rbac_brand_owner.py` | 16 | `be_test_rbac_brand_owner` |
| `tests/modules/vitalia/brand_studio/test_cross_tenant.py` | 10 | `be_test_cross_tenant` |

---

## Validators T-3 (todos PASS)

| Validator | Estado | Archivo |
|---|---|---|
| `be_test_cross_tenant` | PASS | test_cross_tenant.py (10 tests) |
| `be_test_voice_warning_audit` | PASS | test_voice_warning_audit_log.py (12 tests) |
| `be_test_trust_catalog_pe` | PASS | test_trust_catalog_service.py (15 tests) |
| `be_test_voice_preview_cache` | PASS | test_voice_preview_service.py (13 tests) |
| `be_test_rbac_brand_owner` | PASS | test_rbac_brand_owner.py (16 tests) |
| `be_arch_test_no_health_voice_validator` | PASS | test_no_health_voice_validator.py (3 tests) |
| `be_arch_test_no_brand_voice_summary_table` | PASS | test_no_brand_voice_summary_table.py (4 tests) |
| `be_arch_test_brand_studio_ddd` | PASS | test_brand_studio_module_ddd.py (10 tests) |
| `be_arch_test_response_model_required` | PASS | test_response_model_required.py (pre-existing) |
| `be_arch_test_audit_log_sync_write` | PASS | test_audit_log_sync_write.py (pre-existing) |

---

## Acceptance criteria (todos cumplidos)

- A1: Cross-tenant: requests tenant_A con datos tenant_B → 403 RBAC / repo filtrado por tenant_id
- A2: RBAC patient→403, admin_clinic→200, owner→200
- A3: PE seed: TrustCatalogService retorna 8 entradas con códigos correctos (DIGESA, MINSA, SUSALUD, COP_ODONTO, CMP, SUNAT, ISO_9001, ESSALUD)
- A4: Voice warning override → audit_log row con action="voice_warning_overridden" + payload sin PHI raw
- A5: Arch tests creep guards (no_health_voice_validator + no_brand_voice_summary_table)
- A6: DDD arch test brand_studio (domain pure, infra no forward, cross-module ban)
- A7: growth_studio_event_no_phi cubierto por test pre-existente

---

## Skills Consulted

| Skill | Razón | Decisión |
|---|---|---|
| `backend-expert/references/runtime-quality-checklist.md` | Anti-pattern check pre-commit | Tests usan AsyncMock; arch tests usan AST parsing puro |
| `tessl__pytest-api-testing` | Fixture scoping, DB isolation | Tests sin Postgres usan AsyncMock; con Postgres marcados integration |
| `vitalia/.claude/rules/hipaa-lite.md` | Dual filter tenant_id + clinic_id, audit write | brand_studio es owner config (no PHI); excepción documentada |
| `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` | ADR-vitalia-004 § 9 Tests | Tests cubiertos: pytest dual-tenant + arch fitness |
| `.claude/rules/anti-duplication.md` | Verificar no hay tests brand_studio en core | No hay — brand-local confirmado |

---

## Log impl

Ver `T-3-impl-log.md` para decisiones de implementación detalladas (D1-D4).
