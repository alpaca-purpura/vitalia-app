# T-BE-5 Implementation Log — Inline Patient Create + Typeahead Search

**Ticket:** T-BE-5  
**Brand:** vitalia  
**Story:** vitalia-fase2-mateo-nueva-cita  
**Date:** 2026-06-22

---

## § Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Always-on: FastAPI/SQLA patterns, runtime quality checklist, arch fitness | Annotated Depends, response_model mandatory, AsyncSession, text() queries, structlog |
| `brand-expert` | CRM module PHI-data context (patient entity) | All PHI masked in responses (name_masked, phone_masked), never raw PHI in DTO output |
| `hipaa-lite.md` | HIPAA-lite rule for vitalia: dual filter + audit + pgcrypto | `PhiRepositoryBase` dual filter, audit sync before response, pgcrypto encrypt/decrypt via KEK, RBAC @require_phi_access |
| `tenant-isolation.md` | Every query tenant-scoped | All queries: `.where(tenant_id == X, clinic_id == Y)`, incl. get_by_id |
| `tdd-mandatory.md` | RED tests before implementation | Test files written first (this log entry = first item in plan) |
| `pii-sanitisation.md` | PII gate — response_model whitelist | response_model on ALL endpoints, DTOs only expose masked fields |

---

## § Plan

### TDD order (RED first per DDD layer)

1. **RED: Write test files** → `test_patient_inline_create.py`, `test_patient_search_typeahead.py`, `test_patient_dedup_phone.py`
2. **GREEN: Extend `patient_dto.py`** → add 4 DTOs (PatientInlineCreateRequest, PatientInlineCreateResponse, PatientSearchItem, PatientSearchResponse)
3. **GREEN: Extend `patient_repository.py`** → add `create_minimal()`, `search()`, `find_by_phone()`
4. **GREEN: Extend `patient_service.py`** → add `create_minimal()`, `search()`, `find_by_phone()` (all RBAC-gated)
5. **GREEN: Extend `crm/api/router.py`** → add `POST /patients` + `GET /patients?q=`
6. **Gate: ruff check/format, mypy, arch fitness, pytest**
7. **Commit by pathspec, push wip/vitalia**

### DTOs to add (per 03-arch-be.md)

```
PatientInlineCreateRequest:
  name: str (1-120 chars)
  phone: str | None = None (E.164 regex)
  email: EmailStr | None = None
  channel: Literal["whatsapp","instagram","web","phone","walk_in","other"]
  note: str | None = None (≤500 chars)

PatientInlineCreateResponse:
  patient_id: UUID
  name_masked: str    ← "M. López" style — NEVER raw name
  phone_masked: str | None   ← "+51 9***" style or None
  is_duplicate: bool
  created_at: datetime

PatientSearchItem:
  patient_id: UUID
  name_masked: str
  phone_masked: str | None
  channel_first: str | None
  created_at: datetime

PatientSearchResponse:
  items: list[PatientSearchItem]
  next_cursor: str | None  ← base64-encoded UUID cursor
  total_approx: int
```

### Repo methods to add

```python
async def create_minimal(
    self,
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    user_id: UUID,
    name: str,
    phone: str | None = None,
    email: str | None = None,
    channel: str,
    note: str | None = None,
) -> dict[str, Any]

async def search(
    self,
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    q: str,
    cursor: UUID | None = None,
    limit: int = 20,
) -> dict[str, Any]  # {items: list[dict], next_cursor: UUID | None, total_approx: int}

async def find_by_phone(
    self,
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    phone: str,
) -> dict[str, Any] | None
```

### Integration (CONN)

- **Consumed by**: `PatientInlineService` (application layer) → `POST /api/v1/crm/patients` + `GET /api/v1/crm/patients?q=`
- **Registered at**: `vitalia/backend/src/modules/vitalia/crm/api/router.py` (existing router, EXTEND)
- **Router registered in**: `vitalia/backend/src/main.py` (already registered — no change needed)
- **FE consumer**: `features/mateo/api/patients.ts` hook (T-FE-5 scope — not this ticket)
- **cap_target**: `crm.crm-consent-optout` (extending existing cap)

### Security constraints (hard gates)

- PHI NEVER in URL params → search param is `q` (generic), never `name`/`dni`/`phone`
- dual filter MANDATORY: `tenant_id + clinic_id` in every query
- audit log SYNC before response (not fire-and-forget)
- response_model= MANDATORY on every endpoint
- @require_phi_access(roles=["doctor","nurse","admin_clinic"]) on ALL PHI ops
- pgp_sym_encrypt for writes, pgp_sym_decrypt for reads (via KEKClient)
- Masked ONLY in API response: name_masked, phone_masked

### Test suite plan (HIPAA-lite required)

| Test | Nature | Covers |
|---|---|---|
| `test_phi_not_leaked` | unit (API response) | response_model whitelist: no raw name/phone in body |
| `test_audit_log_created` | unit | audit_repo.write() called before response return |
| `test_cross_tenant_blocked` | unit | tenant_id_A + clinic_id_B returns 404 |
| `test_cross_clinic_blocked` | unit | same tenant, wrong clinic → 403 / MissingClinicFilterError |
| `test_create_patient_success` | unit (SC-crear-paciente) | row created, patient_id returned, name_masked correct |
| `test_create_patient_no_name` | unit (SC-paciente-incompleto) | 422, no row |
| `test_search_returns_masked` | unit (SC-empty-pacientes + SC-pacientes-grandes) | items masked, cursor present |
| `test_search_empty` | unit | empty q → empty items |
| `test_find_by_phone_detects_dup` | unit (SC-paciente-duplicado / RN-9) | existing phone → returns patient dict |
| `test_find_by_phone_no_match` | unit | unknown phone → None |

---

## § cap header

All new/modified production files carry:
```
# cap: crm.crm-consent-optout
```
(extending existing cap, not creating new)
