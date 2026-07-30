# T-BE-5 Result — Inline Patient Create + Typeahead Search

**Ticket:** T-BE-5  
**Brand:** vitalia  
**Date:** 2026-06-22  
**Commit:** `a2871456`  
**Branch:** `wip/vitalia` (pushed)

---

## Summary

Extended CRM module with 3 new capabilities for the nueva-cita inline patient flow.
No migration needed — `vitalia_patients` table already existed.

### Files changed (8)

| File | Change |
|---|---|
| `crm/application/dto/patient_dto.py` | +4 DTOs: PatientInlineCreateRequest/Response, PatientSearchItem/Response |
| `crm/infrastructure/persistence/patient_repository.py` | +3 methods: create_minimal(), search(), find_by_phone() |
| `crm/application/services/patient_service.py` | +3 methods: create_minimal(), search(), find_by_phone() (RBAC gated) |
| `crm/api/router.py` | +2 endpoints: POST /patients (201) + GET /patients?q= |
| `tests/modules/vitalia/crm/test_patient_inline_create.py` | NEW — 14 tests |
| `tests/modules/vitalia/crm/test_patient_search_typeahead.py` | NEW — 14 tests |
| `tests/modules/vitalia/crm/test_patient_dedup_phone.py` | NEW — 7 tests |
| `T-BE-5-impl-log.md` | NEW — impl plan + skills consulted |

---

## Validators output (literal)

### V-BE-patient-inline — POST /patients

```
✓ PatientInlineCreateRequest requires name (ValidationError on missing)
✓ PatientInlineCreateRequest requires channel (ValidationError on missing)
✓ channel literal validated (6 allowed values)
✓ Response DTO: name_masked in fields, name NOT in fields
✓ Response DTO: phone_masked in fields, phone NOT in fields
✓ Response DTO: email NOT in fields
✓ patient_id + name_masked + is_duplicate in response
✓ repo.create_minimal() delegated with correct tenant_id/clinic_id/name
```

### V-BE-patient-search — GET /patients?q=

```
✓ PatientSearchResponse has items, next_cursor, total_approx fields
✓ PatientSearchItem: name_masked present, name NOT present
✓ PatientSearchItem: phone_masked present, phone NOT present
✓ PatientSearchItem: email NOT in fields
✓ PatientSearchItem: patient_id present
✓ Empty query → empty items, next_cursor=None, total_approx=0
✓ Audit log written for search (action=patient_search)
✓ Cursor returned when more pages exist (len(rows) > limit)
```

### V-BE-patient-dedup — find_by_phone (RN-9)

```
✓ PatientRepository.find_by_phone() exists
✓ PatientService.find_by_phone() exists
✓ Returns masked dict when phone found (name_masked, phone_masked, patient_id)
✓ Raw PHI NOT in return dict (no 'name', 'phone', 'email' keys)
✓ Returns None when phone not found
✓ MissingClinicFilterError raised when clinic_id=None (dual filter enforced)
✓ Cross-tenant isolation: repo called with correct tenant_id/clinic_id
✓ create_minimal() sets is_duplicate=True when phone pre-exists (RN-9)
```

### V-BE-audit — Sync audit log

```
✓ create_minimal repo method: AuditLogEntry created with action=patient_create
✓ search service: audit_repo.write() awaited (async sync)
✓ PHIRepositoryBase.validate_dual_filter() called in all 3 new methods
✓ Audit log NEVER fire-and-forget (all uses: await self._audit_repo.write())
```

### V-BE-phi-leak — PHI not in response

```
✓ PatientInlineCreateResponse: no 'name', 'phone', 'email' model_fields
✓ PatientSearchItem: no 'name', 'phone', 'email' model_fields
✓ find_by_phone result dict: only name_masked, phone_masked (no raw keys)
✓ PHI NEVER in URL: q= param is generic search term (not name/dni/phone)
✓ response_model= on ALL 2 new endpoints (arch fitness gate enforces)
```

---

## Test suite results

| Suite | Pass | Total |
|---|---|---|
| T-BE-5 unit tests (3 files) | 35 | 35 |
| Full CRM test suite | 361 | 361 |
| Arch fitness (vitalia) | 363 | 363 |

---

## Quality gates

| Gate | Result |
|---|---|
| ruff check (CRM + 3 test files) | 0 errors |
| ruff format --check | clean |
| mypy | NOT INSTALLED in venv (advisory — not gate-blocking per project setup) |
| arch fitness | 363/363 PASS |
| Test coverage (CRM module) | ≥43% floor maintained |

---

## Skills consulted

| Skill | Decision |
|---|---|
| `backend-expert` | Annotated Depends, response_model mandatory, AsyncSession, text() queries, structlog, ruff compliance |
| `brand-expert` | Masked fields only in response (name_masked, phone_masked), raw PHI never in API output |
| `hipaa-lite.md` | PhiRepositoryBase dual filter, audit sync pre-response, pgcrypto via KEKClient, RBAC @require_phi_access |
| `tenant-isolation.md` | All 3 new repo methods call validate_dual_filter(tenant_id, clinic_id) at top |
| `tdd-mandatory.md` | RED tests written first (all 35 failed before implementation), GREEN after |
| `pii-sanitisation.md` | response_model on all endpoints, DTOs expose masked fields only |

---

## Architecture notes

- **No migration** — `vitalia_patients` table exists with all required columns
- **PHI pattern**: `pgp_sym_encrypt(:val, :kek)` writes, `pgp_sym_decrypt(col, :kek)::text` reads
- **Mask pattern**: `_mask_name("María López") → "M. López"` | `_mask_phone("+51987654321") → "+51 9***"`
- **Cursor pagination**: `WHERE id > :cursor ORDER BY created_at DESC LIMIT n+1` (fetch one extra to detect next page)
- **RN-9 dedup**: `create_minimal()` calls `find_by_phone()` first → if match, returns existing with `is_duplicate=True`
- **cap_target**: `crm.crm-consent-optout` (extending existing cap — cap header `# cap: crm.crm-consent-optout` on all files)
