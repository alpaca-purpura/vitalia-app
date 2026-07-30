<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review — T-mk-be-2

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-be-2 (Wave 1 — SQLA 2.0 models + 4 Repositories subclass CompoundScopeRepositoryBase)
**Date:** 2026-05-20
**Brand:** vitalia
**Commit:** 8211510
**Files Reviewed:** 11 (4 models + 4 repositories + 3 test files = ~800 LOC)
**Domains touched:** marketing infrastructure (models + repos with pgcrypto + dual filter)
**Skills consulted:** backend-expert (SA 2.0 patterns + repos), hipaa-lite (pgcrypto + dual filter), anti-duplication (engine consumer-only)
**Verdict:** **CHANGES_REQUESTED** (model missing `conversion_value_cents` column; ReferralStatus enum missing `signed_up` used by T-mk-be-6 cron)

## /test-backend Gate Status (per gate-output.json iter=1)

| Gate | Result | Detail |
|---|---|---|
| ruff-check | PASS | 0 errors |
| ruff-format | PASS | 0 reformats |
| pytest-architecture | PASS | 270/270 |
| pytest-marketing-module (infrastructure) | PASS | 84 passed, 1 skip (pgcrypto integration gated by VITALIA_PHI_KEK env) |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Layer Compliance | PASS | Engine `CompoundScopeRepositoryBase` correctly subclassed (no mirror) |
| 2 | Tenant Isolation | PASS | All 4 repos dual filter `tenant_id + clinic_id` via `scope_field="clinic_id"` |
| 3 | Soft Deletes | PASS | All queries `.where(deleted_at.is_(None))` |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | PASS | `mapped_column` + `Mapped[]` + `select()` (no legacy `Column()` / `.query()`) |
| 6 | Async Consistency | PASS | `AsyncSession`, all repo methods `async def` |
| 7 | Pydantic v2 / PII | N/A | No DTOs in this ticket (T-mk-be-3) |
| 8 | Migration Quality | N/A | Migrations live in T-mk-be-1 |
| 9 | Security (PII + pgcrypto) | PASS | OAuth token via `pgp_sym_encrypt`/`pgp_sym_decrypt` raw SQL · KEK via env (`VITALIA_PHI_KEK`) · dual filter `get_by_id` before decrypt |
| 10 | Tests / TDD | PASS | Result.md cites TDD RED-first; pgcrypto integration smartly skipped via `@pytest.mark.integration` |
| 11 | Cross-cutting | PASS | `currency: String(3) | None` (no hardcoded USD) · UTC `func.now()` server_default · DateTime(timezone=True) everywhere |
| 12 | Mirror detection | PASS | Engine CompoundScopeRepositoryBase consumed via Python import (not redefined) · No cross-brand mirror |

## Cross-scope flags

None — all infrastructure under `vitalia/backend/src/modules/vitalia/marketing/infrastructure/`. Engine package consumed correctly.

## Findings

### FAIL: ReferralModel missing `conversion_value_cents` + `signed_up_at` + `currency` columns
**Category:** 1 (DDD/Contract) + 8 (Migration spec drift inherited)
**File:** `vitalia/backend/src/modules/vitalia/marketing/infrastructure/models/referral_model.py:31-79`
**Issue:** Arch spec § 2.4 (lines 168-184) defines `vitalia_referrals` with columns:
- `shared_at TIMESTAMPTZ NULL`
- `signed_up_at TIMESTAMPTZ NULL`
- `conversion_value_cents BIGINT NULL`
- `currency CHAR(3) NULL`

These are all **missing** from `ReferralModel` (`code`, `status`, `referred_patient_id`, `converted_at`, `expires_at` only). Migration 029 (T-mk-be-1) only adds `deleted_at` + indexes — not the spec'd columns.

Downstream impact (T-mk-be-6 referrals_value_sync cron):
- `referral.conversion_value_cents` (line 183, 190 of cron) → `AttributeError` at runtime
- `referral.status == "signed_up"` (line 189) → always False (only PENDING/CONVERTED/EXPIRED exist)
- The whole cron silently no-ops (logs only `updated=0 converted=0`) — referrals_value_sync **non-functional**

**Fix:** Either:
- (a) Update T-mk-be-2 model + a new migration 031 adding missing columns + matching domain entity field + matching ReferralStatus enum value `SIGNED_UP = "signed_up"`, OR
- (b) Treat T-mk-be-6 cron as logical implementation pending (mark `notImplemented` / mark TODO) and document `signed_up` status as Slice 2 feature.

Recommended (a) since arch spec is explicit and the cron was shipped expecting them.
**Skill ref:** backend-ddd.md, arch spec § 2.4.

### FAIL: ReferralStatus enum missing `SIGNED_UP` value (consumed by T-mk-be-6 cron)
**Category:** 1 (DDD/Contract)
**File:** `vitalia/backend/src/modules/vitalia/marketing/domain/enums.py:36-41` (T-mk-be-1 origin)
**Issue:** Arch spec § 2.4 line 180 says status enum: `'open' | 'shared' | 'signed_up' | 'converted' | 'expired'`. T-mk-be-1 shipped only `PENDING | CONVERTED | EXPIRED`. T-mk-be-6 cron then assumes `signed_up` exists.

**Fix:** Add `SIGNED_UP = "signed_up"`, `SHARED = "shared"`, `OPEN = "open"` to `ReferralStatus`. Decide naming: spec says `open` but T-mk-be-1 used `pending` (default in migration 007). Pick one (`open` per spec) and migrate.

### WARN: Tests skip the only pgcrypto integration path (no live PG)
**Category:** 10 (Tests)
**File:** `vitalia/backend/tests/modules/vitalia/marketing/infrastructure/repositories/test_channel_sync_state_repository.py` (skip per result.md)
**Issue:** `test_oauth_token_pgcrypto_roundtrip` is `@pytest.mark.integration` + skipped when `VITALIA_PHI_KEK` env not set. While the design is correct (real pgcrypto requires live Postgres), CI in gate-output.json shows it skipped. HIPAA-lite explicitly mandates encryption at rest; a passing CI doesn't prove the encrypt/decrypt roundtrip works. There's no unit test mocking the SQL execution either.

**Fix (non-blocking, suggested):** Either:
- Add a unit-level test that mocks `session.execute` and asserts the SQL contains `pgp_sym_encrypt` / `pgp_sym_decrypt` + the encrypted bytes are stored on `model.oauth_token_encrypted`, OR
- Enable the integration test in CI via Postgres + pgcrypto extension (preferred).
**Skill ref:** hipaa-lite.md § Encryption at rest, tdd-mandatory.md.

### WARN: `test_oauth_token_pgcrypto_roundtrip` uses `.decode("latin-1")` which is not encryption-safe semantically
**Category:** 9 (Security / pgcrypto)
**File:** `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/channel_sync_state_repository.py:127-130, 170-180`
**Issue:** `plain_token.decode("latin-1")` is used to convert bytes → str before passing to `pgp_sym_encrypt`. While `latin-1` is a 1:1 byte-string mapping (correct for arbitrary bytes), the design pattern obscures intent. Real OAuth tokens are ASCII-safe; using `.decode("utf-8")` would be clearer and assert intent. Also `pgp_sym_encrypt` accepts `bytea` input directly if SQL is `pgp_sym_encrypt(:plain::bytea, :key)` — letting pg handle bytes is more robust.

**Fix (non-blocking):** Refactor to pass bytea via `psycopg.Binary` or use `pgp_sym_encrypt_bytea` variant. Or document why latin-1 was chosen in a code comment. Low priority; doesn't break runtime.
**Skill ref:** backend-ddd.md, hipaa-lite.md.

## Contract Compliance (business surface only)

- [x] 4 SQLA models with `mapped_column` + `Mapped[]` typing
- [x] 4 Repositories subclass `CompoundScopeRepositoryBase` with `scope_field="clinic_id"`
- [x] Pgcrypto encrypt/decrypt for `oauth_token_encrypted` via KEK
- [x] `ON CONFLICT DO UPDATE` upsert on `channel_metric` natural key
- [x] Custom queries: `list_open_by_stage`, `list_pending_undo_expired`, `get_active_by_provider`, `upsert_metric`
- [ ] **Referral columns `shared_at`, `signed_up_at`, `conversion_value_cents`, `currency` missing — FAIL**

## Allowlist Movement

- [x] No allowlist grew. Arch fitness 270/270.

## Native-First Audit

- [x] No `docker exec` in commits
- [x] No `git add .` / `-A` / `-u` in commits

## Verdict Math

- Cat 1 (DDD/Contract) ReferralModel + ReferralStatus = **FAIL** (downstream cron non-functional in T-mk-be-6)
- Cat 10 + Cat 9 = **WARN**
- Other categories PASS
- Overall: **CHANGES_REQUESTED** — Case B (spawn `dev-team builder-backend` to add missing columns + migration + enum value; whitelist excludes new-method/new-migration changes)

## Action policy

Per `.claude/rules/auditor-self-fix-policy.md` § NUNCA self-fix #4 (new field) + #6 (migration). Dev-team scope.

**Recommended handoff to `/dev-team`:**
1. Add `conversion_value_cents BIGINT NULL`, `currency CHAR(3) NULL`, `shared_at TIMESTAMPTZ NULL`, `signed_up_at TIMESTAMPTZ NULL` to `ReferralModel` + new idempotent migration `031_slice1_marketing_referrals_value_columns.py`.
2. Add `OPEN`, `SHARED`, `SIGNED_UP` to `ReferralStatus` (decide migration path for existing `pending` default — likely rename default to `open`).
3. Update `Referral` domain entity to mirror.
4. Update T-mk-be-6 cron tests to use real enum value.
5. Re-run gate-runner.

---

## Audit iteration 2 (2026-05-21T00:50:00Z — post AUDITOR_AUTO_FIX_LOOP commit ac8ec6f3)

### Verdict
**APPROVED**

### Re-verification (iter 1 findings)

| Finding | Status | Evidence |
|---|---|---|
| FAIL: ReferralModel missing `conversion_value_cents`, `currency`, `shared_at`, `signed_up_at` | ✅ FIXED | `infrastructure/models/referral_model.py:60-71` — all 4 columns added with correct types (BigInteger NULL, String(3) NULL, DateTime(tz=True) NULL × 2) |
| FAIL: ReferralStatus enum missing `SIGNED_UP` | ✅ FIXED | `domain/enums.py:39-54` — 5 values per spec (`OPEN`, `SHARED`, `SIGNED_UP`, `CONVERTED`, `EXPIRED`); model default changed `"pending" → "open"` (line 55) |
| WARN: pgcrypto unit test absent | unchanged | (non-blocking; CI skips integration test; recommend Slice 2 PG fixture) |
| WARN: `decode("latin-1")` design opaque | unchanged | (non-blocking; functionally correct) |

### Migration 031 (NEW)

- `vitalia/backend/alembic/versions/031_slice1_marketing_referrals_value_columns.py` — idempotent raw SQL `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` ✓
- Adds `conversion_value_cents BIGINT NULL`, `currency CHAR(3) NULL`, `shared_at TIMESTAMPTZ NULL`, `signed_up_at TIMESTAMPTZ NULL` to `vitalia_referrals` ✓
- Adds `conversion_value_cents BIGINT NULL` to `vitalia_appointments` (T-mk-be-6 cron SQL dependency satisfied) ✓
- Two partial indexes (`ix_vitalia_referrals_value_sync`, `ix_vitalia_appointments_conversion_value`) ✓
- `down_revision = "030_vitalia"` (correct chain) ✓
- `down()` non-destructive per spec ✓

### Domain entity update

- `Referral` dataclass (`domain/entities/referral.py:44-51`) mirrors new model columns ✓
- `share()` method (line 52-60) sets `status = SHARED + shared_at = now` ✓
- `sign_up()` method (line 62-72) sets `status = SIGNED_UP + signed_up_at = now + referred_patient_id` ✓
- Lifecycle Pep doc string updated (line 6-8) `open → shared → signed_up → converted → expired` ✓

### Tests verification

- Tests in `tests/modules/vitalia/marketing/domain/test_enums.py::TestReferralStatus` — 5 values asserted ✓
- gate-output pytest-marketing-module: 157 PASS (1 skip pgcrypto) — no regressions

### Category re-summary

| # | Category | Status |
|---|---|---|
| 1 | DDD/Contract | PASS |
| 8 | Migration Quality | PASS (idempotent raw SQL) |
| Contract compliance | PASS |

### Verdict math
- 2 FAIL findings addressed cleanly
- 2 WARN findings remain non-blocking (Slice 2 candidates)
- 0 regressions
- Overall: **APPROVED**

