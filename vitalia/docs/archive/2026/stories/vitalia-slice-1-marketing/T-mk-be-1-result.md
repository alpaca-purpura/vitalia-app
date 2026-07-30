# T-mk-be-1 result — Marketing domain entities + 5 Alembic migrations

> Brand: vitalia
> Ticket: T-mk-be-1
> Wave: 1 (BE foundation)
> Commit: f0e395e
> Branch: wip/vitalia
> State: pushed

## Summary

Implemented the marketing domain layer (pure Python, no framework imports) for
`vitalia-slice-1-marketing`. Created domain entities, enums, events, exceptions,
and 5 idempotent Alembic migrations.

## Files created (21)

### Domain entities
- `vitalia/backend/src/modules/vitalia/marketing/domain/entities/lucas_recommendation.py`
  — LucasRecommendation with approve/reject/undo/expire business logic
- `vitalia/backend/src/modules/vitalia/marketing/domain/entities/channel_sync_state.py`
  — ChannelSyncState OAuth tracking
- `vitalia/backend/src/modules/vitalia/marketing/domain/entities/channel_metric.py`
  — ChannelMetric daily snapshot (PHI-free)
- `vitalia/backend/src/modules/vitalia/marketing/domain/entities/referral.py`
  — Referral patient referral program (PHI-free, UUID refs only)

### Domain layer support
- `vitalia/backend/src/modules/vitalia/marketing/domain/enums.py`
  — 6 enums: ProviderSlug, SyncStatus, RecommendationStatus, ReferralStatus, BowtieStage, RejectReason
- `vitalia/backend/src/modules/vitalia/marketing/domain/events.py`
  — 9 DomainEvent subclasses (all marketing domain events)
- `vitalia/backend/src/modules/vitalia/marketing/domain/exceptions.py`
  — InvalidStateTransitionError, ExpiredRecommendationError, UndoWindowExpiredError

### Migrations (026-030 chained from 025 — ADD COLUMN IF NOT EXISTS only)
- `vitalia/backend/alembic/versions/026_slice1_marketing_channel_sync_state.py`
  — ADD enabled + deleted_at + partial unique index
- `vitalia/backend/alembic/versions/027_slice1_marketing_channel_metrics.py`
  — ADD campaign_id + campaign_name + updated unique index
- `vitalia/backend/alembic/versions/028_slice1_marketing_lucas_recommendations.py`
  — ADD action_payload_json + confidence_pct + projected_impact_text + rejected_by_user_id + rejected_at + reject_reason + indexes
- `vitalia/backend/alembic/versions/029_slice1_marketing_referrals.py`
  — ADD deleted_at + partial indexes
- `vitalia/backend/alembic/versions/030_slice1_marketing_appointments_utm.py`
  — ADD utm_medium + UTM composite index

### Tests (48 total)
- `vitalia/backend/tests/modules/vitalia/marketing/domain/test_lucas_recommendation_entity.py`
  — 14 tests (includes mandatory SC-MK-01 gherkin coverage)
- `vitalia/backend/tests/modules/vitalia/marketing/domain/test_enums.py`
  — 20 tests
- `vitalia/backend/tests/modules/vitalia/marketing/domain/test_domain_events.py`
  — 14 tests

## Validator results

| Validator | Result | Detail |
|---|---|---|
| `be_lint_ruff_check` | PASS | 0 errors |
| `be_format_ruff_check` | PASS | 0 files to reformat |
| `be_arch_fitness_brand` | PASS | 270/270 arch tests pass |
| `be_test_marketing_domain` | PASS | 48/48 tests pass |

## Gherkin coverage SC-MK-01

| Scenario | Test path | Status |
|---|---|---|
| SC-MK-01 approve transitions status | `test_lucas_recommendation_entity.py::TestApproveTransitionsStatus::test_approve_transitions_status` | PASS |
| SC-MK-01 undo_until = approved_at + 5min | `test_lucas_recommendation_entity.py::TestApproveTransitionsStatus::test_approved_sets_undo_until_5min` | PASS |

## Migration chain note

The arch spec references migrations 050-054 but existing migrations 007-010 already created
the base tables (vitalia_channel_sync_state, vitalia_channel_metrics, vitalia_lucas_recommendations,
vitalia_referrals). Migrations 026-030 add only the MISSING columns using ADD COLUMN IF NOT EXISTS
to avoid duplicate table errors. This is per the idempotency rule in `.claude/rules/backend-migrations.md`.

## HIPAA-lite compliance

- Marketing tables contain NO PHI (no patient names, DNIs, diagnoses, medical data)
- UTM fields are campaign attribution metadata only (no patient identifiers)
- `clinic_id` included in all 4 entities for dual-filter support (T-mk-be-2 repos will enforce)
- Marketing entities are NOT in `PHI_ORM_MODELS` in `test_phi_dual_filter.py` (confirmed correct)

## Next: T-mk-be-2

SQLAlchemy 2.0 models + 4 repositories subclassing `CompoundScopeRepositoryBase`
with `scope_field="clinic_id"` per arch spec. Pgcrypto roundtrip for oauth_token_encrypted.
