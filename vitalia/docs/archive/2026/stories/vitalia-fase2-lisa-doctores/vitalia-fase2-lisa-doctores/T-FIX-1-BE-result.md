# T-FIX-1-BE — Result: Doctors 500 → UUID header guard

**ticket:** T-FIX-1-BE  
**story:** vitalia-fase2-lisa-doctores  
**state:** tests-passing  
**date:** 2026-06-01  

## Bug (reproduced)

`GET /api/v1/vitalia/clinics/doctors?page=1&page_size=24` with a non-UUID
`X-Clinic-ID` header → `ValueError: badly formed hexadecimal UUID string` →
HTTP 500 ASGI. Root cause: every endpoint in `doctors_router.py` declared
headers as `str` and called `UUID(tenant_id)` / `UUID(clinic_id)` bare
(no try/except), so any malformed or missing header surfaced as an unhandled
500 rather than a 422.

## Fix (defensa en profundidad — decisión Chris 2026-06-01)

Changed ALL header parameters in `doctors_router.py` that feed UUID values from
`str` to `UUID` type directly:

```python
# Before (every endpoint):
tenant_id: str = Header(alias="X-Tenant-ID")
clinic_id: str = Header(alias="X-Clinic-ID")
...
await service.list_doctors(tenant_id=UUID(tenant_id), clinic_id=UUID(clinic_id), ...)

# After:
tenant_id: UUID = Header(alias="X-Tenant-ID")
clinic_id: UUID = Header(alias="X-Clinic-ID")
...
await service.list_doctors(tenant_id=tenant_id, clinic_id=clinic_id, ...)
```

FastAPI 0.136.1 natively validates `UUID` typed headers and returns HTTP 422
with a clear Pydantic error message when the value is not a valid UUID or when
the header is missing. No try/except boilerplate needed.

Endpoints fixed (all 9 in the router):
- `list_doctors` (GET /)
- `create_doctor` (POST /)
- `get_doctor` (GET /{doctor_id})
- `patch_doctor` (PATCH /{doctor_id})
- `generate_doctor_bio` (POST /{doctor_id}/generate-bio)
- `list_availability_blocks` (GET /{doctor_id}/availability-blocks)
- `create_availability_block` (POST /{doctor_id}/availability-blocks)
- `patch_availability_block` (PATCH /{doctor_id}/availability-blocks/{block_id})
- `delete_availability_block` (DELETE /{doctor_id}/availability-blocks/{block_id})

## Step 0: Anti-duplication grep

Checked for existing UUID-header parsers before creating any new helper:

- `vitalia/backend/src/modules/vitalia/api/routes.py:84` — defines `TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID")]` and a `_parse_tenant_id()` helper (used in other routes). Not used by `doctors_router.py`.
- `vitalia/backend/src/modules/vitalia/scheduling/api/notify_router.py:150-161` — uses try/except pattern with `UUID()`.

Decision: use native `UUID` typed header (FastAPI built-in validation) — cleaner than importing a helper or duplicating try/except. The native type approach is the same pattern confirmed working in FastAPI 0.136.1 (verified with a test script before implementing).

## TDD (RED → GREEN)

1. **RED:** wrote `test_doctors_uuid_header_validation.py` with 12 regression tests.
   First run: 1 test failed immediately (500 instead of 422) confirming the bug.
2. **Applied fix:** changed `str` → `UUID` typed headers + removed `UUID()` coercions.
3. **GREEN:** 12/12 tests pass.

## Skills Consulted

- `backend-expert` — invoked. Loaded `runtime-quality-checklist.md` before commit. Key decision: "FastAPI validates UUID typed headers natively → 422; no try/except needed."
- `brand-expert`, `offer-expert`, `offer-type-preset-expert`, `metrics-expert` — NOT invoked (this is a clinics/doctors module bugfix; no brand/offer/analytics surfaces touched).
- Tenant isolation: confirmed all endpoints pass `tenant_id` + `clinic_id` to service (dual filter — hipaa-lite.md requirement met; no change in filtering logic).

## Gates

| Gate | Result |
|---|---|
| ruff check (scoped) | PASS — 0 errors |
| ruff format --check (scoped) | PASS — 0 files to reformat |
| pytest tests/modules/vitalia/clinics/ | PASS — 193/193 |
| pytest tests/architecture/ (excl. pre-existing pgcrypto failure) | PASS — 320/320 |
| mypy | SKIP — not installed in workspace venv |

**Pre-existing failure (not introduced by this PR):**
`tests/architecture/test_pgcrypto_phi_columns.py` fails on `wip/vitalia` branch
before this change (`treatment_plans.notes defined as TEXT instead of BYTEA`).
Confirmed via `git stash` + rerun. Not in scope of T-FIX-1-BE.

## Files changed

- `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py` — 9 endpoint signatures changed
- `vitalia/backend/tests/modules/vitalia/clinics/test_doctors_uuid_header_validation.py` — new regression test file (12 tests)
