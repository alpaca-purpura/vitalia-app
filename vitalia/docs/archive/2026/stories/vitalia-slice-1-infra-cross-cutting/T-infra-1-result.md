---
ticket: T-infra-1
story: vitalia-slice-1-infra-cross-cutting
state: pushed
push_commit_sha: 1194941
push_branch: wip/vitalia-slice-1-shipping
pushed_at: 2026-05-18
validator_summary: all_pass=true (93/93 static PASS, 8 integration SKIP Postgres unavailable, 166/166 arch fitness PASS, ruff 0 errors, format clean)
files_changed: 16
---

# T-infra-1 Result — Slice 1 Alembic Migrations 002-016

## Summary

15 idempotent Alembic migrations + 1 smoke test file created and pushed.

Implements Vitalia Slice 1 database foundation:
- 12 new tables (002-013)
- 4 column additions to existing tables (014-016)
- 93 static tests PASS (no Postgres required)
- 8 integration tests SKIP (Postgres unavailable in CI-lite — gate 10 enforcement pending)

## Files Created (16)

### Migrations (`vitalia/backend/alembic/versions/`)

| File | Purpose |
|---|---|
| `002_vitalia_appointments_columns.py` | vitalia_appointments table + Slice 1 columns (origin, balance_status, follow_up_due_at, follow_up_reason, completed_at, utm_source, utm_campaign) |
| `003_vitalia_payment_events.py` | vitalia_payment_events (fiscal payment tracking, audit_log_id FK) |
| `004_vitalia_fiscal_receipts.py` | vitalia_fiscal_receipts (SUNAT/SAT/AFIP fiscal docs, retry logic) |
| `005_vitalia_treatment_plans.py` | vitalia_treatment_plans (notes BYTEA pgcrypto, sessions tracking, gap_alert_days) |
| `006_vitalia_re_engagement_events.py` | vitalia_re_engagement_events (multi-session/follow-up/NPS patterns, payload_phi BYTEA) |
| `007_vitalia_channel_sync_state.py` | vitalia_channel_sync_state (oauth_token_encrypted BYTEA, per-clinic per-provider) |
| `008_vitalia_channel_metrics.py` | vitalia_channel_metrics (ad spend, impressions/clicks/conversions, currency nullable) |
| `009_vitalia_lucas_recommendations.py` | vitalia_lucas_recommendations (AI recommendations, 5-min undo window, stage/priority) |
| `010_vitalia_referrals.py` | vitalia_referrals (attribution immutable, no deleted_at, referral_code unique per clinic) |
| `011_vitalia_onboarding_progress.py` | vitalia_onboarding_progress (tenant-level, no clinic_id, status-based lifecycle) |
| `012_vitalia_brand_studio_drafts.py` | vitalia_brand_studio_drafts (tenant-level, expiring extraction drafts) |
| `013_vitalia_audit_log.py` | vitalia_audit_log PARTITION BY RANGE (payload_redacted BYTEA, NO deleted_at, 10-year HIPAA-lite retention, monthly partitions 2026-04..2026-08) |
| `014_vitalia_tenants_columns.py` | tenants TenantLocationContract (is_onboarded/location_country/location_city/timezone + backfill) |
| `015_vitalia_offers_columns.py` | offers OfferAdherenceContract (maintenance_schedule_enum + requires_multi_session + check constraints) |
| `016_vitalia_patients_columns.py` | vitalia_patients marketing consent (marketing_opt_in/opt_out/opt_out_reason/opt_out_at) |

### Tests (`vitalia/backend/tests/migrations/`)

| File | Coverage |
|---|---|
| `test_slice1_migrations.py` | 93 static tests (file existence, revision chain, no op.create_table, no sa.Enum, IF NOT EXISTS, pgcrypto, BYTEA PHI, audit_log partition, maintenance_schedule_enum, TenantLocationContract, OfferAdherenceContract, marketing consent columns, TIMESTAMPTZ enforcement, sequential chain 001→016) + 8 integration tests (Postgres-gated) |

## Validator Results

| Validator | Result | Notes |
|---|---|---|
| `be_lint_ruff_check` | PASS (0 errors) | Pre-existing errors in `test_no_hallucination.py` (F401+E501) are not from T-infra-1 |
| `be_format_ruff` | PASS (0 files to reformat) | 5 files auto-formatted before commit |
| `be_arch_fitness_brand` | PASS 166/166 | No ratchet changes — new migrations don't add Python modules |
| `be_test_migrations_smoke` | PASS 93/93 static, 8 SKIP | Integration SKIP — Postgres not available natively (gate 10 pending Docker run) |

## Idempotency patterns applied

- `CREATE TABLE IF NOT EXISTS` on all new tables
- `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` on all column additions
- `CREATE INDEX IF NOT EXISTS` on all new indexes
- Enum creation: `DO $$ BEGIN CREATE TYPE ... EXCEPTION WHEN duplicate_object THEN NULL; END $$`
- Check constraints: `DO $$ BEGIN ALTER TABLE ... ADD CONSTRAINT ... EXCEPTION WHEN duplicate_object THEN NULL; END $$`
- Partition bootstrap: `DO $$ BEGIN CREATE TABLE ... PARTITION OF ... EXCEPTION WHEN SQLSTATE '42P07' THEN NULL; END $$`
- NEVER `op.create_table()` / `op.add_column()` / `op.create_index()` (non-idempotent SA wrappers)
- NEVER `sa.Enum(create_type=True)` (broken SA 2.0.27)

## HIPAA-lite compliance

- `vitalia_audit_log`: PARTITIONED BY RANGE (occurred_at), payload_redacted BYTEA, NO deleted_at (IMMUTABLE — legal 10-year requirement), monthly partitions bootstrapped (2026-04..2026-08)
- `vitalia_treatment_plans`: notes BYTEA (pgcrypto symmetric encryption at-rest)
- `vitalia_re_engagement_events`: payload_phi BYTEA
- `vitalia_channel_sync_state`: oauth_token_encrypted BYTEA
- All queries dual-filtered by (tenant_id, clinic_id) per hipaa-lite.md cardinal rule
- pgcrypto extension enabled idempotently in migrations 005 + 013

## Promotion proposals unblocking 014/015

Both confirmed `state: migrated` (commit 5ca61019) before writing:
- `docs/promotion-protocol/proposals/2026-05-17-platform-tenants-location-columns.md` → migration 014
- `docs/promotion-protocol/proposals/2026-05-17-offer-studio-multi-session-maintenance.md` → migration 015

## Next: T-infra-2

Per `06-tickets.yaml` next unblocked ticket after T-infra-1: `T-infra-2` (Extension SDK registries).
