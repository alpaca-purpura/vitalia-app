# T-BE-generate-profile — Result

**Ticket:** T-BE-generate-profile  
**Story:** vitalia-fase2-lisa-doctores  
**Commit:** d4eec32f  
**Branch:** wip/vitalia  
**State:** tests-passing

## Gap closed

`POST /{doctor_id}/generate-profile` existed in the FE contract but returned 404.
`generate-bio` only wrote 3-blob legacy `bio_public`; `bio_generated_at` was never set.

## Files modified (7)

| File | Change |
|---|---|
| `vitalia/backend/tests/modules/vitalia/clinics/test_generate_profile_endpoint.py` | NEW — 16 TDD tests (RED first) |
| `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` | Added `GenerateProfileResponse` DTO |
| `vitalia/backend/src/modules/vitalia/clinics/application/ports/doctor_repo_port.py` | Added `update_public_profile()` ABC method |
| `vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/doctor_repository.py` | Added `update_public_profile()` raw SQL implementation |
| `vitalia/backend/src/modules/vitalia/clinics/application/bio_generation_service.py` | Added `generate_structured()` + helpers |
| `vitalia/backend/src/modules/vitalia/clinics/application/doctor_service.py` | Added `generate_public_profile()` + `_slugify()` |
| `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py` | New endpoint `POST /{doctor_id}/generate-profile` |

## Implementation summary

### Endpoint (doctors_router.py)
- `POST /{doctor_id}/generate-profile`
- `response_model=GenerateProfileResponse` (PII allowlist)
- RBAC: `require_brand_owner_access(roles=_STAFF_MUTATION_ROLES)`
- Headers: `X-Tenant-ID` + `X-Clinic-ID`
- Flow: load doctor → load bio file filenames → `BioGenerationService.generate_structured()` → compute slug if null → `service.generate_public_profile()` (audit sync inside) → `db.commit()` → return response
- Graceful degradation: LLM failure → empty profile, HTTP 200 (no 500)

### BioGenerationService.generate_structured()
- `_STRUCTURED_SYSTEM_PROMPT`: 6-section JSON output format, no-invent guardrail, Spanish neutro LatAm
- `_STRUCTURED_USER_TEMPLATE`: includes bio_inputs_notes, bio_links, bio_files filenames, languages, credential
- `_parse_structured_response()`: strips markdown fences, parses JSON, handles partial/missing sections (RN-D3D-6), graceful fallback on any parse error → empty `DoctorPublicProfile`
- Never raises

### DoctorService.generate_public_profile()
- Sets `bio_generated_at = datetime.now(tz=timezone.utc)`
- Calls `repo.update_public_profile()` then writes audit log sync
- `_slugify()` utility: unicodedata NFKD → ASCII → lowercase → `re.sub([^a-z0-9]+, "-")`

### DoctorRepoPort.update_public_profile() / DoctorRepository.update_public_profile()
- Raw SQL: `UPDATE vitalia_doctors SET public_profile=CAST(:v AS jsonb), bio_generated_at=:ts, public_slug=COALESCE(:slug, public_slug) WHERE id=:id AND tenant_id=:t AND clinic_id=:c AND deleted_at IS NULL RETURNING id`
- Tenant + clinic dual-filter (HIPAA-lite)
- Re-reads full entity via `get_by_id` after UPDATE

### GenerateProfileResponse DTO
```python
class GenerateProfileResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
    profile: PublicDoctorProfileDTO
    generated_at: datetime
    public_slug: str | None = None
```

## RN satisfaction

| Rule | Status |
|---|---|
| RN-D3B-4: `bio_generated_at` ONLY set via generate-profile | PASS — `update()` does not touch `bio_generated_at`; only `update_public_profile()` sets it |
| RN-D3D-6: sections without material → None/[] | PASS — `_parse_structured_response()` handles partial/missing gracefully |
| Cross-tenant 404 | PASS — dual-filter enforced in repo; test_cross_tenant_404 covers it |
| Audit sync write | PASS — `AuditLogEntry(action="doctor.profile_generated")` written before response |
| `profile_state.material_new` false after generation | PASS — timestamp comparison: `bio_generated_at` set ≥ `updated_at` → `material_new=False` |

## Gate results

| Gate | Result |
|---|---|
| `pytest tests/modules/vitalia/clinics/` (unit, no Postgres) | 382/382 PASS (16 new) |
| `ruff check` | All checks passed |
| `ruff format --check` | All files formatted |
| `pytest tests/architecture/` (vitalia) | 339 passed, 2 warnings |
| Pre-existing arch failure | `test_pgcrypto_phi_columns.py` — `treatment_plans.notes TEXT vs BYTEA` — confirmed pre-existing via `git stash` baseline test |
| Postgres-dependent tests | `test_bio_files_api.py` — requires running DB — pre-existing skip |

## Notes

- `generate-bio` legacy endpoint untouched (backward compat preserved)
- `public_doctors_router.py` untouched
- FE untouched
- No push made
- Pre-commit cap validator: SOFT_DRIFT advisory on new test file (no cap header on test file — expected; test files are not production code surfaces)
