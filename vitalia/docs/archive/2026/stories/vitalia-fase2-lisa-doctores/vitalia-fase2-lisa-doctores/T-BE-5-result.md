# T-BE-5 Result — Public doctors endpoint + allow-list channel guard + arch test

**Ticket:** T-BE-5  
**Story:** vitalia-fase2-lisa-doctores  
**Branch:** wip/vitalia  
**State:** tests-passing (awaiting gate-runner + auditor-backend)  
**Completed:** 2026-05-31  

## Summary

Implemented the public doctors endpoint with explicit allow-list channel guard (PHI security boundary). TDD RED→GREEN order strictly followed.

## Deliverables shipped

### New files

| File | Purpose |
|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/application/public_doctor_serializer.py` | Allow-list serializer: `to_public_dto(doctor, *, credential_label=None) -> PublicDoctorDTO`. Exactly 7 fields. NEVER accesses PHI. |
| `vitalia/backend/src/modules/vitalia/clinics/api/public_doctors_router.py` | `GET /{tenant_slug}/doctors` — no auth, `response_model=PublicDoctorsResponse`, resolves clinic by slug, fetches visible+active doctors, channel guard via serializer |
| `vitalia/backend/tests/modules/vitalia/clinics/test_public_doctors_endpoint.py` | 29 tests (TDD RED first): serializer unit tests, router contract tests, PHI leak tests, main.py registration test |

### Modified files

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/clinic_repository.py` | Added `get_by_slug_public(slug)` — public lookup by clinic slug without tenant_id |
| `vitalia/backend/src/main.py` | Added `include_router(public_doctors_router, prefix="/api/public/clinic", tags=["public"])` |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/06-tickets.yaml` | T-BE-5 `state: pushed` |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/chris-input.md` | T-BE-5 verdict appended |

### Arch test: skip resolved

`tests/architecture/test_public_doctors_allowlist.py::test_public_doctor_serializer_exists` was `pytest.skip("T-BE-5 scope")` in T-BE-1.  
**Now PASSES**: 5/5 tests GREEN (was 4+1 skip).

## Architecture invariants enforced

### Allow-list (not deny-list) security model

The serializer `to_public_dto()` physically cannot emit PHI because it only reads 7 named fields:

```python
return PublicDoctorDTO(
    display_name=doctor.display_name,     # 1. derived property
    specialty=doctor.specialty,            # 2.
    avatar_key=doctor.avatar_key,          # 3.
    years_experience=doctor.years_experience,  # 4.
    languages=doctor.languages,            # 5.
    bio_public=bio_dto,                    # 6.
    credential_label=credential_label,     # 7. optional
)
```

Adding `dni`, `email`, `phone`, or `credential` to `Doctor` in the future does NOT leak them — the allow-list ignores all other fields.

### Double filter at repo level

`DoctorRepository.list_public()` filters `visible_en_landing = TRUE AND active = TRUE AND deleted_at IS NULL` at SQL level — no runtime filtering needed.

### Tenant resolved from clinic slug (no auth)

`ClinicRepository.get_by_slug_public(slug)` → finds active, non-deleted clinic by slug → uses its `tenant_id` + `id` for the doctor query. Tenant_id never exposed in response.

### response_model= mandatory

`GET /{tenant_slug}/doctors` declares `response_model=PublicDoctorsResponse`. Arch test V-ARCH-7 (`test_public_doctors_router_get_has_response_model`) verifies this.

## Test results

```
vitalia/backend/tests/modules/vitalia/clinics/  — 172 passed, 0 failed, 1 warning
vitalia/backend/tests/architecture/test_public_doctors_allowlist.py — 5 passed (0 skipped)

Total new tests this ticket: 29
V-FN-11: PASS
V-ARCH-7: PASS (skip resolved → PASS)
```

## Skills consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Runtime quality checklist (runtime-quality-checklist.md) — pre-commit anti-patterns: FastAPI Depends pattern, SQLA 2.0 text() queries, PII channel guards | Confirmed `_get_db()` Depends pattern for router; explicit allow-list not deny-list; `response_model=` mandatory |
| `tessl__fastapi` | Public endpoint without auth — FastAPI dependency injection, Path params, response_model= | Used `Depends(_get_db)` correctly; no `Depends(auth_guard)` on public route |
| `hipaa-lite.md` (vitalia brand rule) | Channel guard design — HIPAA-lite § Channel guards, PHI never in public endpoint | Allow-list 7 fields; `visible_en_landing AND active` double filter; `tenant_id/clinic_id` not in public DTO |

## Pre-existing issues (not introduced by T-BE-5)

- `test_pgcrypto_phi_columns.py::test_no_phi_column_uses_text_or_varchar_unencrypted` — `treatment_plans.notes TEXT vs BYTEA` failure (from migration 021 / T-BE-CRM debt). Per ticket spec: "ignore pre-existing treatment_plans.notes CRM debt".

## CONN anti-orphan check

- **Consumed by:** vitalia-fase2-lisa-landing-public (future story FE landing page). Route registered at `GET /api/public/clinic/{tenant_slug}/doctors`. Navigable via HTTP without auth.
- **On the map:** `cap_target: lisa.doctores` (same as parent story).
- **Navigable/reachable:** registered in `main.py`. Public URL pattern `https://{domain}/api/public/clinic/{slug}/doctors` accessible by any HTTP client.
- **Notarized:** `include_router(public_doctors_router, prefix="/api/public/clinic")` in `main.py` — routing confirmed.
