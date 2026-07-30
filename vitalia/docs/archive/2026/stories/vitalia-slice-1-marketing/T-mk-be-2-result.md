# T-mk-be-2 Result — SQLAlchemy 2.0 Models + Repositories

> Story: vitalia-slice-1-marketing
> Ticket: T-mk-be-2
> Wave: 1 (BE Foundation — models + repositories)
> Builder: claude-sonnet-4-6
> State: pushed
> Date: 2026-05-20

## Summary

Wave 1 step 2 complete. Four SQLAlchemy 2.0 models + four repositories subclassing
`CompoundScopeRepositoryBase` (engine `luana-core-platform` v0.4.0). HIPAA-lite dual filter
`tenant_id` + `clinic_id` enforced on all queries. ON CONFLICT DO UPDATE upsert for
channel metrics. Pgcrypto roundtrip for OAuth token encryption.

## Files Created

### Infrastructure models (4)

- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/models/__init__.py`
- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/models/channel_sync_state_model.py`
  - Table `vitalia_channel_sync_state`, `oauth_token_encrypted` as `LargeBinary` (pgcrypto)
- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/models/channel_metric_model.py`
  - Table `vitalia_channel_metrics`, natural key `UniqueConstraint` for ON CONFLICT DO UPDATE
  - `spend_cents: BigInteger` (no float), `currency: String(3) | None` (not defaulted)
- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/models/lucas_recommendation_model.py`
  - Table `vitalia_lucas_recommendations`, dual-index for list_open_by_stage + list_pending_undo_expired
- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/models/referral_model.py`
  - Table `vitalia_referrals`, PHI-free (UUID refs only)

### Infrastructure repositories (4)

- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/__init__.py`
- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/lucas_recommendation_repository.py`
  - Custom queries: `list_open_by_stage(stage, limit=3)`, `list_pending_undo_expired(now)`
- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/channel_sync_state_repository.py`
  - `get_active_by_provider(provider)` — filters status=OK + enabled=True + soft delete
  - `save_with_encrypted_token(model, plain_token)` — pgcrypto `pgp_sym_encrypt` via KEKClient
  - `decrypt_token(model_id, tenant_id, clinic_id)` — dual filter first, then `pgp_sym_decrypt`
- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/channel_metric_repository.py`
  - `upsert_metric(...)` — ON CONFLICT DO UPDATE on `uq_vitalia_channel_metrics_natural_key`
- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/referral_repository.py`
  - Minimal — base class provides get_by_id + list_for_scope with dual filter

### Init files

- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/__init__.py`

### Tests (4 files, RED-first)

- `vitalia/backend/tests/modules/vitalia/marketing/infrastructure/__init__.py`
- `vitalia/backend/tests/modules/vitalia/marketing/infrastructure/repositories/__init__.py`
- `vitalia/backend/tests/modules/vitalia/marketing/infrastructure/repositories/test_lucas_recommendation_repository.py`
- `vitalia/backend/tests/modules/vitalia/marketing/infrastructure/repositories/test_channel_sync_state_repository.py`
- `vitalia/backend/tests/modules/vitalia/marketing/infrastructure/repositories/test_channel_metric_repository.py`
- `vitalia/backend/tests/modules/vitalia/marketing/infrastructure/repositories/test_referral_repository.py`

## Test Results

```
84 passed, 1 skipped (pgcrypto integration — no VITALIA_PHI_KEK in env)
Arch fitness: 270 passed, 2 warnings (unknown mark no_eval — pre-existing)
Lint: 0 errors
Format: 17 files already formatted
```

## Key Technical Decisions

1. **CompoundScopeRepositoryBase pattern**: `scope_field="clinic_id"` enforces HIPAA-lite dual
   filter (`tenant_id` + `clinic_id`) on all base class queries without repetition.

2. **UUID rendering in tests**: SQLAlchemy `literal_binds` renders UUIDs without dashes.
   Test assertions strip dashes from both UUID string and compiled SQL before comparing:
   `assert str(uuid).replace("-", "") in stmt_str.replace("-", "")`.

3. **pgcrypto integration test**: Marked `@pytest.mark.integration` and skips without
   `VITALIA_PHI_KEK` env var. Correct pattern — requires live Postgres with pgcrypto extension.

4. **ON CONFLICT DO UPDATE**: Uses `pg_insert(Model).on_conflict_do_update(constraint="...", set_={})`
   from `sqlalchemy.dialects.postgresql.insert`. The `id` field is freshly generated via `uuid4()`
   on each call; conflict on natural key preserves existing `id`.

5. **Currency**: `currency: String(3) | None` — NOT defaulted to "USD" per currency-handling.md.
   Set from provider response only.

6. **Soft deletes**: All queries filter `deleted_at.is_(None)`. Models have `deleted_at` column.

## Gherkin Coverage

| Scenario | Test | Status |
|---|---|---|
| SC-MK-01 Lucas approve happy (repo state) | `test_approve_updates_status` | PASS |
| SC-MK-01 Dual filter tenant+clinic | `test_dual_filter_tenant_and_clinic` | PASS |
| SC-MK-04 Cross-clinic isolation | `test_other_clinic_cannot_read` | PASS |
| SC-MK-04 OAuth pgcrypto roundtrip | `test_oauth_token_pgcrypto_roundtrip` | SKIP (no live PG) |

## Next Ticket

T-mk-be-3: Application services + Pydantic v2 DTOs
(MarketingService · AttributionService · ReferralsService · LucasRecommendationsService)
