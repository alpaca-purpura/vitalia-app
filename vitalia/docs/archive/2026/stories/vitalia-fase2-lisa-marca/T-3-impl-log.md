# T-3 Implementation Log — BE pytest dual-tenant + arch fitness creep guards

**Story:** vitalia-fase2-lisa-marca (F2-S7)
**Ticket:** T-3 — BE pytest dual-tenant + seed test + voice_warning audit log + arch fitness creep guards
**Surface:** Tests only (`production_code: false`)
**Status:** COMPLETE — 83/83 tests PASS (unit) + 14 SKIP (integration, Postgres required)

---

## § Skills Consulted

| Skill | Razón invocada | Decisión tomada |
|---|---|---|
| `backend-expert` / `references/runtime-quality-checklist.md` | Pre-commit anti-pattern check: FastAPI Annotated dep, tenant isolation, SQLA legacy Column, audit write pattern | Confirmado: tests usan AsyncMock para audit + repo, no session real; tests de arch usan AST parsing puro |
| `tessl__pytest-api-testing` | httpx AsyncClient fixture scoping, factory fixtures, DB isolation | Tests sin Postgres usan AsyncMock; tests con Postgres marcados `@pytest.mark.integration` — auto-skip vía conftest |
| `vitalia/.claude/rules/hipaa-lite.md` | Dual filter `tenant_id + clinic_id`, audit log sync write, PHI sanitization en traces | brand_studio es owner config (no PHI) → excepción dual filter documentada; audit write verificada via AsyncMock.assert_awaited_once() |
| `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` | ADR-vitalia-004 § 9 Tests section | Tests cubiertos: pytest dual-tenant + arch fitness — cumple los 4 capas requeridas |
| `.claude/rules/anti-duplication.md` | Step 0: verificar que no existan clases/patterns ya en core antes de crear tests | No hay tests de brand_studio en core ni otros brands — brand-local confirmado |

---

## § Scope y decisiones de implementación

### T-3 deliverables generados

**Arch fitness (3 nuevos)**
- `vitalia/backend/tests/architecture/test_no_health_voice_validator.py` — D2-voice anti-creep: 3 tests (file absent, class absent, no LLM import)
- `vitalia/backend/tests/architecture/test_no_brand_voice_summary_table.py` — D2-voice anti-creep: 4 tests (migration, model, class, code refs via AST)
- `vitalia/backend/tests/architecture/test_brand_studio_module_ddd.py` — DDD purity brand_studio: 10 tests (domain pure, infra no forward, cross-module ban, api response_model)

**Módulo (5 nuevos)**
- `vitalia/backend/tests/modules/vitalia/brand_studio/test_voice_preview_service.py` — 13 tests (cache HIT/MISS, invalidación, tenant isolation, 3-tuple shape)
- `vitalia/backend/tests/modules/vitalia/brand_studio/test_trust_catalog_service.py` — 15 tests (PE 8 entries, códigos correctos, case-insensitive, empty country)
- `vitalia/backend/tests/modules/vitalia/brand_studio/test_voice_warning_audit_log.py` — 12 tests (action="voice_warning_overridden", no PHI raw, payload fields, awaited sync)
- `vitalia/backend/tests/modules/vitalia/brand_studio/test_rbac_brand_owner.py` — 16 tests (owner/admin_clinic→pass, patient/marketing/doctor→403, error code exact)
- `vitalia/backend/tests/modules/vitalia/brand_studio/test_cross_tenant.py` — 10 tests (RBAC isolation, VoiceBlocklist tenant_id passed, cache tenant-scoped, audit tenant isolation)

### Decisiones tomadas

**D1 — section field en VoiceWarningOverrideRequestDTO**
`section` es `Literal["so_i_speak", "so_i_dont_speak"]` (no "voz-y-tono"). Corregido en todos los tests.
Detectado al correr tests primera vez — ValidationError Pydantic.

**D2 — brand_voice_summary references en docstrings**
Los archivos de producción contienen "NO brand_voice_summary" en sus docstrings (anti-creep documentation).
El test `test_no_brand_voice_summary_references_in_brand_studio` fue refinado para usar AST parsing y
detectar solo código ejecutable (imports, __tablename__, llamadas) — no referencias en comentarios.

**D3 — Arch test `test_domain_layer_no_framework_imports`**
FRAMEWORK_IMPORT_PATTERNS no incluye Pydantic — la regla Pydantic tiene su allowlist separada.
El dominio de brand_studio usa solo dataclasses + StrEnum (puro Python) — pasa clean.

**D4 — Tests de integración marcados correctamente**
Tests que necesitan Postgres (test_prohibited_phrases_*) heredados de T-1 — quedan como `@pytest.mark.integration`.
Los 14 SKIP son todos esos — expected behavior cuando Postgres no está disponible en CI.

---

## § Anti-creep guards implementados

Per decisión D2-voice del CONTEXT-BRIEF.md:

1. `test_no_health_voice_validator.py` — health_voice_validator.py NO debe existir (ni como archivo, ni como clase)
2. `test_no_brand_voice_summary_table.py` — tabla brand_voice_summary NO debe existir (ni migración, ni modelo SQLA, ni código ejecutable)

Ambos son ratchets permanentes — si alguien introduce este scope creep, los tests fallan de inmediato.

---

## § Validators T-3 cumplidos

| Validator | Estado | Test |
|---|---|---|
| `be_test_cross_tenant` | PASS | `test_cross_tenant.py` (10 tests) |
| `be_test_voice_warning_audit` | PASS | `test_voice_warning_audit_log.py` (12 tests) |
| `be_test_trust_catalog_pe` | PASS | `test_trust_catalog_service.py` (15 tests) |
| `be_test_voice_preview_cache` | PASS | `test_voice_preview_service.py` (13 tests) |
| `be_test_rbac_brand_owner` | PASS | `test_rbac_brand_owner.py` (16 tests) |
| `be_arch_test_no_health_voice_validator` | PASS | `test_no_health_voice_validator.py` (3 tests) |
| `be_arch_test_no_brand_voice_summary_table` | PASS | `test_no_brand_voice_summary_table.py` (4 tests) |
| `be_arch_test_brand_studio_ddd` | PASS | `test_brand_studio_module_ddd.py` (10 tests) |
| `be_arch_test_response_model_required` | PASS (pre-existing global test) | `test_response_model_required.py` |
| `be_arch_test_audit_log_sync_write` | PASS (pre-existing global test) | `test_audit_log_sync_write.py` |

---

## § Acceptance criteria cumplidos

- A1: Cross-tenant: requests tenant_A con datos tenant_B → 403 RBAC / repo filtrado por tenant_id ✅
- A2: RBAC patient→403, admin_clinic→200, owner→200 ✅
- A3: PE seed: TrustCatalogService returns 8 entradas con códigos correctos ✅
- A4: Voice warning override → audit_log row con action="voice_warning_overridden" + payload sin PHI raw ✅
- A5: Arch tests creep guards (no_health_voice_validator + no_brand_voice_summary_table) ✅
- A6: DDD arch test brand_studio (domain pure, infra no forward, cross-module ban) ✅
- A7: growth_studio_event_no_phi → cubierto por test pre-existente `test_growth_studio_event_no_phi.py` ✅

---

## § Resultados finales

```
T-3 tests: 83 passed / 14 skipped (integration Postgres)
Arch fitness full suite: 314 passed / 0 failed
Lint: 0 errors
Format: 0 files to reformat
```
