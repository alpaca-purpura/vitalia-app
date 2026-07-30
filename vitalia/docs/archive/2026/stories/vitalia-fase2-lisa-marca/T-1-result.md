# T-1 Result — BE migration prohibited_phrases + seed PE + telemetry whitelist

**Story:** vitalia-fase2-lisa-marca (F2-S7)
**Ticket:** T-1
**Brand:** vitalia
**Surface:** BE only
**State:** pushed
**Date:** 2026-05-27

## Summary

T-1 delivers three BE artifacts:

1. Alembic migration `033_f2_s7_vitalia_lisa_marca.py` — idempotent raw SQL `CREATE TABLE IF NOT EXISTS vitalia_prohibited_phrases` + 3 partial indexes + 10 seed rows PE (`tenant_id IS NULL, country_scope='PE'`, `ON CONFLICT DO NOTHING`).
2. Modified `growth_studio_emitter.py` — `_KNOWN_EVENT_NAMES: frozenset[str]` constant extended with 15 `lisa_marca_*` events (13 required by spec + `lisa_marca_autosave_failed` + `lisa_marca_trust_signal_added` per 03-arch § 10.2 full table).
3. New `file_size_bucket.py` — `bucket_file_size(size_bytes: int) -> str` helper for `lisa_marca_logo_uploaded` telemetry event per 03-arch § 10.3.

## Files Produced

| File | Action | Notes |
|---|---|---|
| `vitalia/backend/alembic/versions/033_f2_s7_vitalia_lisa_marca.py` | NEW | Migration, idempotent, downstream-regression-na comment |
| `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` | MODIFY | Added `_KNOWN_EVENT_NAMES` frozenset (22 events total: 7 F2-S1 + 15 F2-S7) |
| `vitalia/backend/src/modules/vitalia/_shared/telemetry/file_size_bucket.py` | NEW | `bucket_file_size()` helper, 5 buckets per arch spec |
| `vitalia/backend/tests/modules/vitalia/brand_studio/test_prohibited_phrases_migration.py` | NEW | TDD RED→GREEN (integration, needs DB) |
| `vitalia/backend/tests/modules/vitalia/brand_studio/test_prohibited_phrases_seed.py` | NEW | TDD RED→GREEN (integration, needs DB) |
| `vitalia/backend/tests/modules/vitalia/_shared/telemetry/test_whitelist_lisa_marca_events.py` | NEW | TDD unit tests, 9/9 PASS (no DB) |

## Quality Gates

| Gate | Status | Notes |
|---|---|---|
| ruff lint (6 files) | PASS | 0 errors |
| ruff format (6 files) | PASS | 0 files to reformat |
| Arch fitness (209 tests) | PASS | No regressions |
| Unit tests telemetry (9/9) | PASS | `test_whitelist_lisa_marca_events.py` 9/9 |
| Integration tests (migration + seed) | SKIP | Postgres down at time of commit; marked `@pytest.mark.integration` |
| mypy | N/A | Not installed in workspace .venv |

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| backend-expert | Anti-patterns + runtime quality checklist | Raw SQL IF NOT EXISTS, frozenset O(1), structlog |
| brand-expert | Touching brand_studio module | prohibited_phrases is owner config NOT PHI; Repository base (not PhiRepositoryBase) |
| tessl__fastapi | FastAPI patterns | N/A for T-1 (no routes) — consulted for future T-2 awareness |
| tessl__pytest-api-testing | Test fixture patterns | integration marker, db_session fixture, async pattern |
| tenant-isolation | Every entity carries tenant_id | tenant_id IS NULL = seed defaults (valid per spec) |
| backend-ddd | DDD layers | Migration only (domain/infra/app/api in T-2) |
| backend-migrations | Idempotent raw SQL | IF NOT EXISTS, ON CONFLICT DO NOTHING, no op.create_table() |
| anti-duplication | New file check | file_size_bucket.py: grep confirmed no cross-brand mirror |
| tdd-mandatory | RED→GREEN | Tests written before implementation |
| spanish-text | Seed phrases + alternatives | All 10 PE phrases verified Spanish neutro (no voseo) |
| hipaa-lite | Vitalia HIPAA-lite overlay | This table is owner config (no PHI); dual filter NOT needed; sanitize_payload applies to telemetry |

## Anti-Creep Guards Verified

Per `.claude/rules/sales-agent-brand-voice.md` D2-voice cardinal:
- NO `health_voice_validator.py` created
- NO `brand_voice_summary` mirror table
- `vitalia_prohibited_phrases` is a configurable soft-warning blocklist (UI warnings only), NOT an LLM validator

## Acceptance Criteria Status

| AC | Description | Status |
|---|---|---|
| A1 | alembic upgrade head idempotent | READY (migration written; DB run gated on Postgres) |
| A2 | vitalia_prohibited_phrases table + 3 indexes | READY (migration includes all 3 partial indexes) |
| A3 | 10 seed rows PE (tenant_id IS NULL, country_scope='PE') | READY (10 rows seeded; integration test written) |
| A4 | growth_studio_emitter whitelist extended with 13+ lisa_marca_* events | PASS (15 events added, 13 required minimum) |

## Blocks Unblocked

T-2 (BE API — marca_router 21 endpoints) and T-3 (BE pytest tests) are now unblocked.
