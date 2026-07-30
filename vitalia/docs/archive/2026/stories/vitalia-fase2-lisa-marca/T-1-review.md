<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# T-1 Code Review — BE migration `vitalia_prohibited_phrases` + seed PE + telemetry whitelist

**Story:** vitalia-fase2-lisa-marca (F2-S7)
**Ticket:** T-1
**Brand:** vitalia
**Surface:** BE (migration + telemetry whitelist + helper)
**State:** pushed
**Push commit SHA:** c4a4f8e9
**Auditor:** auditor-backend (Opus 4.7)
**Audit iter:** 1
**Audit date:** 2026-05-27T09:32:41Z

## Verdict: **CHANGES_REQUESTED**

WARN-grade overall — migration + helper + whitelist are sound; one cross-cutting violation (`datetime.utcnow()` in domain entities created in adjacent T-2 commit but linked logically to T-1's seed lifecycle) plus minor schema mismatch must be addressed.

> NB: T-1's own diff is clean (migration uses `DateTime(timezone=True)` on every column; seed phrases verbatim Spanish neutro). The findings below are scoped to the T-1 deliverables (migration + telemetry whitelist + file_size_bucket).

## Domains touched

- BE migrations (Alembic raw SQL idempotent)
- BE telemetry whitelist (`growth_studio_emitter.py`)
- BE helper (`file_size_bucket.py`)
- BE persistence model (`prohibited_phrase_model.py` — created here logically, referenced T-2)

## Skills consulted

- `backend-expert` (anti-pattern check + runtime-quality-checklist.md)
- `.claude/rules/backend-migrations.md` (idempotent raw SQL only)
- `.claude/rules/tenant-isolation.md` (seed `tenant_id IS NULL` whitelisted exception)
- `.claude/rules/spanish-text.md` (R1 + R2)
- `vitalia/.claude/rules/hipaa-lite.md` (owner-config exception → no dual filter, no PHI)
- `.claude/rules/anti-duplication.md` (brand-local cross-brand mirror scan)

## Gate Status (from `gate-output.json` iter 1)

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | ruff (lint) | PASS | 0 errors |
| 2 | ruff (format) | PASS | 957 files already formatted |
| 3 | pytest arch fitness | PASS | 203 passed (warns: `pytest.mark.no_eval` unknown) |
| 4 | pytest brand_studio unit | PASS | 58 passed (warn: `datetime.utcnow()` deprecation — see Finding W1) |
| 5 | tsc | PASS | n/a for T-1 |
| 6 | eslint | PASS | n/a for T-1 |
| 7 | vitest | WARN | n/a for T-1 (FE-related) |
| 8 | playwright syntax | PASS | n/a for T-1 |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | PASS | 0 (seed `IS NULL` whitelisted exception documented) |
| 3 | Soft Deletes | PASS | `deleted_at` column present |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | PASS | `mapped_column`/`Mapped[]` correctly used in `prohibited_phrase_model.py` |
| 6 | Async Consistency | PASS | n/a for migration |
| 7 | Pydantic v2 / PII | PASS | n/a for T-1 (DTOs in T-2) |
| 8 | Migration Quality | PASS | `IF NOT EXISTS`, partial indexes, idempotent re-run safe, `ON CONFLICT DO NOTHING` |
| 9 | Security | PASS | No PHI in this table (owner-config) — confirmed in `hipaa-lite.md` overlay |
| 10 | Tests / TDD | WARN | Migration tests `@pytest.mark.integration` skipped — Postgres down ratified per gate-output.json |
| 11 | Cross-cutting | WARN | F1 — `datetime.utcnow()` in domain entity (cross-cutting `master-data.md` violation) |
| 12 | Mirror detection | PASS | No cross-brand mirror; `vitalia_prohibited_phrases` is brand-local SSoT |

## Findings

### WARN: F1 — `datetime.utcnow()` deprecated default in domain entity (master-data violation)

**Category:** 11 (Cross-cutting — master-data.md)
**File:** `vitalia/backend/src/modules/vitalia/brand_studio/domain/prohibited_phrase.py:46`
**Issue:**
```python
created_at: datetime = field(default_factory=datetime.utcnow)
```
Same pattern at `domain/trust_signal.py:32`. The pytest output explicitly captured this:
> `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).`

`.claude/rules/master-data.md` § Prohibido lists `datetime.utcnow()` as forbidden.

**Fix:** replace with `datetime.now(timezone.utc)` (already imported at top of file) or use the shared `utc_now()` helper if it exists in `core/luana-core-platform/`. 2-line edit per file.

**Skill ref:** `.claude/rules/master-data.md` § Prohibido. `backend-expert/references/master-data.md`.

> NOTE: this code was committed under T-2 logically but the entity was created in service of T-1's migration table. The reviewer scopes it to T-1 because the table+entity pair forms the migration deliverable surface; an alternative is to attribute the finding to T-2. Either attribution produces the same fix.

### WARN: F2 — Migration runtime validation deferred (acceptance A1 ratified gated)

**Category:** 10 (Tests)
**File:** `vitalia/backend/tests/modules/vitalia/brand_studio/test_prohibited_phrases_migration.py`, `test_prohibited_phrases_seed.py`
**Issue:** All migration + seed integration tests carry `@pytest.mark.integration` and were SKIPPED (Postgres down at audit time per gate-output.json). Acceptance A1 (`alembic upgrade head succeeds idempotent`) and A3 (10 seed rows PE) cannot be verified offline.

**Fix:** non-blocking for this review — gate runner must execute integration suite against Postgres before merge gate G6. `/pm-vitalia` should ratify at Fase F merge that gate ran integration markers GREEN once Postgres available; otherwise add this to release blocker list.

**Skill ref:** `.claude/rules/tdd-mandatory.md`; `parallel-safety.md` M3.

### info: F3 — Naming convention drift (low priority)

**Category:** 4 (Code Quality)
**File:** `vitalia/backend/alembic/versions/033_f2_s7_vitalia_lisa_marca.py:42-54`
**Issue:** Migration creates table `vitalia_prohibited_phrases` (singular `prohibited` not `prohibited_phrases_v2` or similar). Index naming convention `idx_vit_phrase_*` mixes abbreviation styles (`vit_phrase` instead of `vit_prohibited_phrase`). Not a bug — just stylistic inconsistency with prior migrations.

**Fix:** N/A for this review (info-only); future story can rename via Alembic alter without functional break.

## Contract Compliance (T-1 deliverables vs `06-tickets.yaml::T-1`)

- [x] `vitalia/backend/alembic/versions/XXXX_f2_s7_vitalia_lisa_marca.py` — created as `033_f2_s7_vitalia_lisa_marca.py` ✅
- [x] 3 composite indexes per `03-arch § 9.1` ✅ (verified: `idx_vit_phrase_tenant_severity`, `idx_vit_phrase_country_severity`, `idx_vit_phrase_lookup`)
- [x] 10 seed rows PE (`tenant_id IS NULL`, `country_scope='PE'`) ✅
- [x] `growth_studio_emitter.py` MODIFY — `_KNOWN_EVENT_NAMES` extended with 15 events (13 required + 2 extras as documented in result.md) ✅
- [x] `file_size_bucket.py` NEW helper — 5 buckets ✅
- [x] Migration idempotent verification gated on Postgres (T-1 acceptance A1) — DEFERRED (see F2)

## Allowlist Movement
- No allowlists grew. Architecture fitness 203 PASS unchanged.
- Test coverage: brand_studio unit at 58 passed (baseline established for T-1 + T-2).

## Native-First Audit
- [x] No `docker exec ... ruff|pytest` in commits — confirmed git log `c4a4f8e9` uses native venv
- [x] No `git add .` / `-A` / `-u` in commit body
- [x] Commit body lists exact files staged

## Cross-scope flags

None for T-1.

## Decisions honored (per `06-tickets.yaml::T-1.decisions_applicable`)

- [x] D2-voice anti-creep: NO `health_voice_validator.py` created. NO `brand_voice_summary` mirror table. Soft warning table only. ✅
- [x] OQ-D: hybrid catalog seed PE 10 phrases verified Spanish neutro LatAm (no voseo glosario triggers). ✅
- [x] A4: 13+ `lisa_marca_*` events added (`_KNOWN_EVENT_NAMES` frozenset, 15 events total). ✅
- [x] A5: brand-local soft warning table — NOT a `PhiRepositoryBase` consumer. ✅
- [x] A14: schema raw SQL idempotent `IF NOT EXISTS`. ✅

## Verdict Math

- 0 FAILs in categories 1/2/8/9/12. PASS gate.
- 2 WARNs (F1 `datetime.utcnow` deprecation + F2 integration tests skipped pending Postgres). → overall WARN.
- Allowlist did not grow. → PASS gate.
- All `/test-backend` gates (per gate-output.json) PASSED for T-1 scope. → PASS gate.
- IMPL-LOG documents skills consulted with traceable decision per skill. → PASS gate.
- Builder cited `backend-expert/references/runtime-quality-checklist.md` in impl-log. → PASS gate.
- 2 category WARNs ≥ 2 → overall WARN → CHANGES_REQUESTED (because F1 is whitelisted self-fix candidate, not blocking).

**Verdict: CHANGES_REQUESTED** — Self-fix candidate (Case C per `.claude/rules/auditor-self-fix-policy.md`):
- F1 is whitelist item 14 (currency/date hardcoded → tenant_locale equivalent). 2 files, ~2 lines each. Self-fix authorized.
- F2 is non-blocking, deferred to merge gate.

Auditor will self-fix F1 in iter 2 if Chris ratifies — see Self-fix log section below.

## Self-fix log (proposed iter 2)

**STATUS: PROPOSED — NOT applied this iter.**

- **Iter 2 plan:** Caso C self-fix per `.claude/rules/auditor-self-fix-policy.md` whitelist item 14:
  - Edit `vitalia/backend/src/modules/vitalia/brand_studio/domain/prohibited_phrase.py:46` — replace `default_factory=datetime.utcnow` → `default_factory=lambda: datetime.now(timezone.utc)` (import `timezone` already in scope).
  - Edit `vitalia/backend/src/modules/vitalia/brand_studio/domain/trust_signal.py:32` — same.
  - Run `cd vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/brand_studio/ tests/architecture/ -x -q --tb=short`.
  - Commit: `chore(vitalia/f2-s7): auditor self-fix T-1 iter 2 — datetime.utcnow → datetime.now(timezone.utc) per master-data.md`.
- **Caps:** 2 files / 4 lines (within cap 2/10).
- **Awaiting:** Chris ratify OR delegate to dev-team if self-fix declined.

## Last iteration timestamp

2026-05-27T09:32:41Z (iter 1, audit-only — no commits made)
