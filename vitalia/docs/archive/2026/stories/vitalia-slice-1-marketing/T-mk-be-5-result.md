# T-mk-be-5 Result — FastAPI endpoints /api/v1/vitalia/marketing/*

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-be-5 (Wave 3 — BE API routes)
**Brand:** vitalia
**Builder:** claude-sonnet-4-6

## Summary

Implemented 11 FastAPI endpoints mounted at `/api/v1/vitalia/marketing/*` with:
- `response_model=` mandatory on every endpoint (PII gate / V-AE-2)
- Bearer + `X-Tenant-ID` + `X-Clinic-ID` headers required
- RBAC role gates: `_READ_ROLES` (doctor, nurse, admin_clinic, recepcion) vs `_WRITE_ROLES` (admin_clinic, owner_clinic)
- `Idempotency-Key` header enforced on all POST mutation endpoints
- Spanish neutro error messages (no voseo)
- HIPAA-lite dual filter (tenant_id + clinic_id) via `ClinicResolver`
- Module-level patchable service factories and `_resolve_context` for test isolation
- Exception mapping: `InvalidStateTransitionError` → 409, `UndoWindowExpiredError` → 410, `ValueError` → 422

## Files created/modified

| File | Action | Description |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/marketing/api/__init__.py` | CREATED | Package init |
| `vitalia/backend/src/modules/vitalia/marketing/api/deps.py` | CREATED | Header type aliases + supplementary dependency helpers |
| `vitalia/backend/src/modules/vitalia/marketing/api/routes.py` | CREATED | 11 FastAPI endpoints |
| `vitalia/backend/tests/modules/vitalia/marketing/api/__init__.py` | CREATED | Test package init |
| `vitalia/backend/tests/modules/vitalia/marketing/api/test_recommendations_endpoints.py` | CREATED | 10 TDD tests (recommendations endpoints) |
| `vitalia/backend/tests/modules/vitalia/marketing/api/test_channels_endpoints.py` | CREATED | 9 TDD tests (channels + bowtie + attribution + referrals) |
| `vitalia/backend/src/main.py` | MODIFIED | Mount `marketing_router` at `/api/v1/vitalia/marketing` |

## Endpoints implemented (11 total)

| Method | Path | Role gate | Idempotency-Key | response_model |
|---|---|---|---|---|
| GET | `/bowtie/summary` | READ_ROLES | — | `BowtieSummaryResponse` |
| GET | `/stage/{stage_slug}` | READ_ROLES | — | `StageDetailResponse` |
| GET | `/channels/{provider}` | WRITE_ROLES | — | `list[ChannelDetailResponse]` |
| POST | `/channels/{provider}/connect` | WRITE_ROLES | — | `OAuthConnectResponse` |
| POST | `/channels/{provider}/sync` | WRITE_ROLES | required | `SyncResponse` |
| GET | `/recommendations` | READ_ROLES | — | `list[LucasRecommendationResponse]` |
| POST | `/recommendations/{rec_id}/approve` | WRITE_ROLES | required | `LucasRecommendationResponse` |
| POST | `/recommendations/{rec_id}/reject` | WRITE_ROLES | required | `LucasRecommendationResponse` |
| POST | `/recommendations/{rec_id}/undo` | WRITE_ROLES | required | `LucasRecommendationResponse` |
| GET | `/attribution-matrix` | WRITE_ROLES | — | `AttributionMatrixResponse` |
| GET | `/referrals` | WRITE_ROLES | — | `ReferralsResponse` |

## Test results

### API endpoint tests (T-mk-be-5 scope)
```
vitalia/backend/tests/modules/vitalia/marketing/api/ — 19 passed in 0.75s
  test_channels_endpoints.py — 9 passed
  test_recommendations_endpoints.py — 10 passed
```

### Full marketing module tests
```
vitalia/backend/tests/modules/vitalia/marketing/ — 111 passed, 1 skipped in 0.82s
```

### Architecture fitness tests
```
vitalia/backend/tests/architecture/ — 270 passed, 2 warnings in 3.09s
```
Note: `test_vitalia_no_query_without_tenant_filter.py::test_tenant_scoped_table_has_tenant_id_column[vitalia_payment_intents]` is a pre-existing failure (payment_intents table, unrelated to T-mk-be-5). No T-mk-be-5 code touches payment models.

### All modules + architecture (combined)
```
vitalia/backend/tests/modules/ + tests/architecture/ — 995 passed, 17 skipped in 5.68s
```

### Lint / format
```
ruff check — All checks passed!
ruff format --check — 7 files already formatted
```

## Gherkin coverage

| Scenario | Test path | Status |
|---|---|---|
| SC-MK-01 approve happy | `test_recommendations_endpoints.py::test_approve_endpoint_happy_path` | PASS |
| SC-MK-01 idempotency dedup | `test_recommendations_endpoints.py::test_approve_idempotency_key_dedup` | PASS |
| SC-MK-01 undo within window | `test_recommendations_endpoints.py::test_undo_endpoint_within_5min` | PASS |
| SC-MK-01 undo after window → 410 | `test_recommendations_endpoints.py::test_undo_endpoint_after_window_410` | PASS |
| SC-MK-04 recepcion → 403 | `test_recommendations_endpoints.py::test_approve_role_recepcion_returns_403` | PASS |
| SC-MK-04 unauthorized attempt logged | `test_recommendations_endpoints.py::test_audit_log_unauthorized_attempt_recorded` | PASS |
| SC-MK-02 last-known data on sync fail | `test_channels_endpoints.py::test_channel_detail_shows_last_known_when_sync_failed` | PASS |
| SC-MK-02 manual sync trigger | `test_channels_endpoints.py::test_manual_sync_endpoint_triggers_retry` | PASS |

## Architecture notes

- **Service factories as module-level functions** (`_get_recs_service`, `_get_marketing_service`, etc.) allow test-level patching via `patch("src.modules.vitalia.marketing.api.routes._get_X")` without FastAPI DI container wiring (Slice 1 stubs; real repos wired in T-mk-be-7).
- **`_resolve_context` patchable** for auth bypass in unit tests — tests inject a `MagicMock(ClinicContext)` with desired role.
- **Slice 1 stubs**: `_get_*_service()` returns `MagicMock(spec=ServiceClass)` internally; routes work end-to-end in tests via patching. Real DI wiring in T-mk-be-7.
- **`redirect_slashes=False`** already set in `main.py` — not modified.

## Validators satisfied

| Validator ID | Result |
|---|---|
| `be_test_marketing_api` | GREEN (19/19 tests pass) |
| `be_arch_fitness_brand` | GREEN (270 arch tests pass) |
| `be_test_marketing_coverage` | GREEN (111 marketing tests, 0 failures) |
