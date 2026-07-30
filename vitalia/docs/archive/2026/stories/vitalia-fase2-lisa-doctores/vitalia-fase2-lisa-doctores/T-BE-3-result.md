# T-BE-3 — Resultado: Availability blocks endpoints + slot materialization + audit

**Story:** vitalia-fase2-lisa-doctores
**Ticket:** T-BE-3
**Estado:** pushed
**Branch:** wip/vitalia
**Fecha:** 2026-05-31

## Deliverables implementados

### Archivos nuevos

| Archivo | Descripción |
|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/application/availability_block_service.py` | `AvailabilityBlockService` — orchestrates AvailabilityProjectionService + AvailabilityBlockRepository + audit SYNC writes. `delete_block` returns `(True, preserved_count)` — CRITICAL invariant (SC-3b). |
| `vitalia/backend/tests/modules/vitalia/clinics/test_availability_blocks_api.py` | 30 tests TDD RED-first: response_model= gates, DTO existence/structure, RBAC dependencies, service unit tests (list/create/update/delete/preserve), biweekly occurrences, one-off materialization, delete-preserves-confirmed (CRITICAL SC-3b, V-FN-7) |

### Archivos modificados

| Archivo | Qué se extendió |
|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` | +`RecurrentBlockCreateRequest` (discriminated kind='recurrent'), `OneOffBlockCreateRequest` (kind='one_off'), `AvailabilityBlockDTO`, `AvailabilityBlocksResponse`, `DeleteBlockResponse{deleted, preserved_appointments}` |
| `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py` | +4 availability-blocks sub-routes: GET list, POST create, PATCH edit, DELETE retire + `_build_block_service()` DI builder + `_to_block_dto()` mapper |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/06-tickets.yaml` | T-BE-3 `state: pushed` |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/chris-input.md` | T-BE-3 build verdict appended |

## Routes implemented

| Method | Path | Auth | response_model | Notes |
|---|---|---|---|---|
| GET | `/{doctor_id}/availability-blocks` | dual filter | `AvailabilityBlocksResponse` | Lists active blocks for doctor |
| POST | `/{doctor_id}/availability-blocks` | admin_clinic | `AvailabilityBlockDTO` (201) | Create + materialize slots + audit `doctor.availability_block_created` |
| PATCH | `/{doctor_id}/availability-blocks/{block_id}` | admin_clinic | `AvailabilityBlockDTO` | Edit + reproject-future-only |
| DELETE | `/{doctor_id}/availability-blocks/{block_id}` | admin_clinic | `DeleteBlockResponse` | Retire future free slots + audit `doctor.availability_block_deleted` |

## DTOs (discriminated union by kind)

- `RecurrentBlockCreateRequest` — kind, start_time, end_time, day_of_week, freq, end_condition_kind, end_date|occurrences|None
- `OneOffBlockCreateRequest` — kind, start_time, end_time, specific_date
- `AvailabilityBlockDTO` — full read DTO (id, tenant_id, clinic_id, doctor_id, kind, times, recurrent/one-off fields)
- `AvailabilityBlocksResponse` — `{blocks: list[AvailabilityBlockDTO]}`
- `DeleteBlockResponse` — `{deleted: bool, preserved_appointments: int}`

## Quality gates

| Gate | Result |
|---|---|
| Clinics tests | 126/126 PASS |
| Architecture tests (excl. pre-existing CRM debt) | 333/333 PASS |
| Pre-existing failure | `test_pgcrypto_phi_columns::treatment_plans.notes` — CRM debt, pre-exists T-BE-1, NOT introduced by T-BE-3 |
| ruff lint | 0 errors |
| ruff format | 0 files to reformat |
| TDD order | RED tests confirmed (30 failing) → GREEN after implementation |

## Architecture compliance

- response_model= on all 4 routes (V-ARCH-2) — verified by test assertions
- RBAC admin_clinic on all mutations via `Depends(require_brand_owner_access)` (V-NF-7) — verified by test assertions
- Dual filter (tenant_id+clinic_id) on all routes — via `AvailabilityBlockRepository(CompoundScopeRepositoryBase)`
- Audit log SYNC pre-response (HIPAA-lite): `doctor.availability_block_created` + `doctor.availability_block_deleted` — verified by test assertions
- `forbidden_to_touch` respected: `core/luana-core-*/src/**` NOT touched, `scheduling/**` NOT touched
- Slots materialize to brand-local `vitalia_availability_slots` — scheduling reads without modification

## CRITICAL invariant verified

**delete-block-preserves-confirmed-appointments (SC-3b, V-FN-7):**
- `AvailabilityBlockRepository.delete_block()` (T-BE-2): soft-deletes future slots WHERE `has_confirmed_appointment=False` ONLY
- `AvailabilityBlockService.delete_block()` (T-BE-3): calls repo + returns `(True, preserved_count)` 
- Router returns `DeleteBlockResponse(deleted=True, preserved_appointments=N)` so FE can show warning
- Test `test_availability_block_service_delete_preserves_confirmed_appointments` asserts `preserved == 3` when repo returns 3

## Skills consulted

| Skill | Why | Decision |
|---|---|---|
| `backend-expert` | Runtime quality checklist, DDD patterns, SQLA 2.0, tenant isolation | Used `CompoundScopeRepositoryBase` (engine), SQLA `select()` pattern, `ConfigDict(from_attributes=True)`, `response_model=` mandatory |
| `tessl__fastapi` | Annotated deps, response_model, async lifespan, discriminated union routing | Used `Depends()` for RBAC, `Header(alias=...)` for X-Tenant-ID/X-Clinic-ID/X-User-ID, `Union` type for discriminated request body |
| `tessl__pytest-api-testing` | httpx AsyncClient, fixture scoping, factory fixtures, DB isolation | Used `AsyncMock` for repo/audit mocks, `pytest.mark.asyncio`, parametrized assertions on audit entries |

## Step 0 anti-default-flip-audit

No feature flags touched. No core/luana-core-*/src/ modified. N/A.

## Cross-module isolation

- `scheduling/**` NOT touched (per `forbidden_to_touch`)
- `vitalia_availability_slots` brand-local table exists (created in migration 036, T-BE-1)
- scheduling reads from `vitalia_availability_slots` via existing repos — no scheduling module modification needed
- No `core/luana-core-*/src/` modification — consuming `CompoundScopeRepositoryBase` via import only

## Notes for auditor

1. `treatment_plans.notes TEXT vs BYTEA` arch test failure is pre-existing CRM debt from before T-BE-1. Ticket explicitly documented: "pre-existing failure test_pgcrypto_phi_columns::treatment_plans.notes is CRM debt, NOT yours — ignore it".
2. `AvailabilityBlockService.update_block` does NOT write audit log (only create/delete audited — read-only schedule management). This matches the arch spec § 6.
3. The discriminated union in FastAPI (POST body `RecurrentBlockCreateRequest | OneOffBlockCreateRequest`) uses `getattr(..., field, None)` on the request to extract kind-specific fields — avoids tight coupling to `kind` string.
4. PATCH route includes `doctor_id` in path for routing clarity (consistent with other sub-resource patterns), but the block is identified by `block_id` via dual filter (tenant+clinic).
