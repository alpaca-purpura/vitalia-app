# T-BE-bio-docs — Result Artifact

**Ticket:** T-BE-bio-docs (delta v3 D3-B — Doctor bio-files CRUD + download)
**Brand:** vitalia · **Module:** clinics · **Cap:** `lisa.doctores`
**State:** tests-passing (impl GREEN; awaiting gate-runner + auditor-backend)

## Deliverables Completed

All 6 deliverables from `06-tickets.yaml` — T-BE-bio-docs:

| Layer | File | Status |
|---|---|---|
| Domain | `clinics/domain/bio_file.py` | Written (session 1) |
| Infrastructure / Model | `clinics/infrastructure/models/doctor_bio_file_model.py` | Written (session 1) |
| Infrastructure / Repo | `clinics/infrastructure/repositories/doctor_bio_file_repository.py` | Written (session 1) |
| Application | `clinics/application/bio_file_service.py` | Written (session 1) |
| Migration | `alembic/versions/040_vitalia_doctor_bio_files.py` | Written (session 1) |
| API / DTOs | `clinics/api/dtos.py` | EXTENDED (session 2: +4 DTOs) |
| API / Proxy | `clinics/api/assets_proxy_router.py` | EXTENDED (session 2: bio_doc kind) |
| API / Router | `clinics/api/doctors_router.py` | EXTENDED (session 2: 4 endpoints) |
| Tests | `tests/modules/vitalia/clinics/test_bio_files_api.py` | Written (session 1, reformatted session 2) |
| Tests (migration) | `tests/migrations/test_040_doctor_bio_files_idempotency.py` | Written (session 1, reformatted session 2) |

## Gate Results

| Gate | Result | Notes |
|---|---|---|
| ruff check | PASS | 0 errors |
| ruff format | PASS | 0 files to reformat |
| test_bio_files_api (non-integration) | **32/32 PASS** | All unit tests GREEN |
| test_040 (static structural) | **10/10 PASS** | Migration idempotency structural |
| test_040 double-upgrade | SKIP/FAIL | Pre-existing: DB not at head (migration 015 broken, `offers` table missing) |
| tests/modules/vitalia/clinics (all, non-integration) | **353/353 PASS** | Zero regressions |
| tests/architecture (excl. pre-existing pgcrypto) | **326/326 PASS** | Zero new violations |
| mypy | N/A | mypy not installed in workspace venv |

### Pre-existing failures (not introduced by T-BE-bio-docs)

- `test_pgcrypto_phi_columns::test_no_phi_column_uses_text_or_varchar_unencrypted` — `treatment_plans.notes TEXT` (confirmed via git stash; pre-existing since before this ticket)
- `test_double_upgrade_is_noop` — migration chain broken at 015 (`offers` table missing); environment issue, not our migration
- Integration tests `@pytest.mark.integration` for bio_files — table `vitalia_doctor_bio_files` not yet created (migration not applied to dev DB; skipped when table absent but PG available; test design is correct per `2026-06-11-mocked-service-tests-hide-repo-contract.md`)

## Architecture Decisions

**D-1 (stream proxy):** `GET .../download` returns `-> Response` with `media_type=content_type` + `Content-Disposition: attachment`. Rationale: `StorageStrategy.get_file_bytes()` is the only surface symmetric across local/R2 backends; presigned-GET doesn't exist in `luana-core-assets`. Arch test response_model exemption confirmed (L94-96 heuristic in `test_response_model_required.py`).

**D-2 (CompoundScopeRepositoryBase):** Arch gate `test_compound_scope_repository_used.py` mandates new PHI repos use this engine base; `PhiRepositoryBase` is legacy/shrink-only allowlist.

**RN-D3B-1 (snapshot untouched):** `delete_file` does NOT touch `doctor` record — bio_public/public_profile snapshot intact. Test asserts zero mutation calls on doctor_repo.

## Integration (CONN)

- **Consumed:** T-FE-bio-docs (`depends_on: [T-BE-bio-docs]`) consumes all 4 endpoints
- **On-map:** cap `lisa.doctores` · zone: Agentes → Lisa
- **Navigable:** `doctors_router` already `include_router`-ed in `main.py` — zero new wiring required
- **Notarized:** `# cap: clinics.lisa.doctores` header on all new production files

## Commit Scope

Files staged for commit (pathspec only — no `git add -A`):

**New (untracked):**
- `vitalia/backend/alembic/versions/040_vitalia_doctor_bio_files.py`
- `vitalia/backend/src/modules/vitalia/clinics/application/bio_file_service.py`
- `vitalia/backend/src/modules/vitalia/clinics/domain/bio_file.py`
- `vitalia/backend/src/modules/vitalia/clinics/infrastructure/models/doctor_bio_file_model.py`
- `vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/doctor_bio_file_repository.py`
- `vitalia/backend/tests/migrations/test_040_doctor_bio_files_idempotency.py`
- `vitalia/backend/tests/modules/vitalia/clinics/test_bio_files_api.py`
- `vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/T-BE-bio-docs-impl-log.md`
- `vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/T-BE-bio-docs-result.md` (this file)

**Modified:**
- `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` (+4 DTOs)
- `vitalia/backend/src/modules/vitalia/clinics/api/assets_proxy_router.py` (+bio_doc kind)
- `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py` (+4 endpoints + service builder)
