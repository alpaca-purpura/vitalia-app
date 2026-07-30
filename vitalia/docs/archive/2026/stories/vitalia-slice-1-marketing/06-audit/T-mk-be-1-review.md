<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review — T-mk-be-1

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-be-1 (Wave 1 — Domain entities + enums + events + 5 Alembic migrations 026-030)
**Date:** 2026-05-20
**Brand:** vitalia
**Commit:** f0e395e
**Files Reviewed:** 21 (4 entities + enums + events + exceptions + 5 migrations + 3 test files)
**Domains touched:** marketing domain layer (foundation for repos/services/routes)
**Skills consulted:** backend-expert (DDD layering · migrations idempotentes · TDD · brand-docs schema)
**Verdict:** **CHANGES_REQUESTED** (spec drift — BowtieStage enum: 3 stages shipped vs 5 in arch spec/01-spec-extract; RejectReason values diverge)

## /test-backend Gate Status (per gate-output.json iter=1)

| Gate | Result | Detail |
|---|---|---|
| ruff-check | PASS | 0 errors |
| ruff-format | PASS | 0 reformats |
| pytest-architecture | PASS | 270/270 |
| pytest-marketing-module | PASS | 152/152 (T-mk-be-1 contributes 48 domain tests) |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Layer Compliance | PASS | 0 |
| 2 | Tenant Isolation | PASS | clinic_id present on entities — repo dual filter in T-mk-be-2 |
| 3 | Soft Deletes | PASS | deleted_at on Lucas/ChannelSyncState/Referral entities |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | N/A | Migrations idempotent raw SQL — no SA in domain (correct) |
| 6 | Async Consistency | N/A | Pure domain layer |
| 7 | Pydantic v2 / PII | N/A | Pure dataclasses domain |
| 8 | Migration Quality | PASS | All 5 migrations `IF NOT EXISTS` raw SQL idempotent |
| 9 | Security (PII) | PASS | No PHI in entities (UUID refs only) |
| 10 | Tests / TDD | PASS | RED-first evidence in T-mk-be-1-result.md · 48/48 tests pass |
| 11 | Cross-cutting (Spanish/UTC/decisions) | WARN | UTC `datetime.now(UTC)` correct · Spanish n/a · spec drift hidden in enums |
| 12 | Mirror detection | PASS | No cross-brand mirror (no marketing modules in nicolify/comunify/lupulo) |

## Cross-scope flags

None — all files in `vitalia/backend/src/modules/vitalia/marketing/domain/` + brand-local migrations. Zero engine edits.

## Findings

### FAIL: Spec drift — BowtieStage enum diverges from arch spec / Gherkin SC-MK-03
**Category:** 1 (DDD) + 11 (cross-cutting) + Contract compliance
**File:** `vitalia/backend/src/modules/vitalia/marketing/domain/enums.py:44-49`
**Issue:** Builder defines `BowtieStage` with 3 stages: `ATTRACT | CONVERT | RETAIN`. The arch spec § 2.3 (lucas_recommendations table comment, line 136) and 01-spec-extract.md § 2 (5 stages: Atracción · Calificación · Reserva · Adopción · Expansión) explicitly require 5 stages: `attraction | qualification | reservation | adoption | expansion`.

```python
class BowtieStage(str, Enum):
    ATTRACT = "attract"
    CONVERT = "convert"
    RETAIN = "retain"
```

Gherkin SC-MK-03 expects "stage tab change `attraction` → `reservation` re-renders AttributionMatrix on stage Reserva". With only 3 stages, the FE cannot render the spec'd stage tabs (Atracción · Calificación · Reserva · Adopción · Expansión) nor map `?tab=reservation` to a stage. AttributionMatrixWidget (stage Reserva only) breaks.

Downstream cascade:
- `LucasRecommendationModel.stage VARCHAR(32)` stores wrong values (`attract`/`convert`/`retain`) — production data corrupted
- `marketing_service._STAGE_CHANNEL_MAP` (T-mk-be-3) maps 3 wrong keys
- `routes.py::list_recommendations` iterates `BowtieStage` (3 stages) — UI only sees 3 panels
- FE T-mk-fe-2 `MarketingStageTabs` cannot match arch spec mockup (5 tabs)
- Tests `test_enums.py::TestBowtieStage::test_has_exactly_three_stages` CEMENT the wrong cardinality (ratchet trap)

**Fix:** Replace the enum verbatim:
```python
class BowtieStage(str, Enum):
    ATTRACTION = "attraction"
    QUALIFICATION = "qualification"
    RESERVATION = "reservation"
    ADOPTION = "adoption"
    EXPANSION = "expansion"
```
Update test_enums.py (5 stages, exactly 5 cardinality). Update all 6 downstream consumers (model column comment, marketing_service map, routes, cron stage parsing, jobs default, FE marketing-shared types).
**Skill ref:** Contract compliance (auditor SOP) + `.claude/rules/story-closure-gate.md § gherkin_coverage` (SC-MK-03 fails if 5 tabs not rendered).

### WARN: RejectReason values diverge from arch spec § 2.3
**Category:** Contract compliance
**File:** `vitalia/backend/src/modules/vitalia/marketing/domain/enums.py:52-58`
**Issue:** Builder defines `RejectReason` as `NOT_RELEVANT | TOO_EXPENSIVE | ALREADY_DONE | OTHER`. Arch spec § 2.3 line 150 explicitly says: `reject_reason VARCHAR(64) NULL,                   -- not_priority | already_doing | data_wrong | too_risky | other`. The DTO arch spec § 3 (line 248 `RejectRecommendationRequest.reason`) uses regex `^(not_priority|already_doing|data_wrong|too_risky|other)$`.

**Fix:** Align enum values with spec:
```python
class RejectReason(str, Enum):
    NOT_PRIORITY = "not_priority"
    ALREADY_DOING = "already_doing"
    DATA_WRONG = "data_wrong"
    TOO_RISKY = "too_risky"
    OTHER = "other"
```
Update `test_enums.py::TestRejectReason` + Pydantic DTO regex in T-mk-be-3 `RejectRecommendationRequest`.
**Skill ref:** Contract compliance.

### info: Migrations renumbered 050-054 → 026-030 (rationale documented)
**Category:** 8 (Migrations)
**File:** `vitalia/backend/alembic/versions/026_slice1_marketing_channel_sync_state.py` (et al.)
**Issue:** Arch spec § 11 lists migrations 050-054. Builder used 026-030 because vitalia migrations chain already had 025 as head + initial tables 007-010 already created the base tables. Result.md § "Migration chain note" documents rationale. Migrations are `ALTER TABLE … ADD COLUMN IF NOT EXISTS` only (idempotent) — acceptable per `.claude/rules/backend-migrations.md`.

**Action:** No fix needed. Update arch spec § 11 in 03-arch-be.md post-merge so future readers see actual numbers (or note "renumbered to 026-030 in implementation"). Tracking nice-to-have for `07-merge.md § 5`.

## Contract Compliance (business surface only)

- [x] 4 entities from CONTRACT § 1 implemented (ChannelSyncState, ChannelMetric, LucasRecommendation, Referral)
- [x] 9 events from CONTRACT § 7 declared
- [ ] **BowtieStage enum 5 values per CONTRACT § 2.3 — FAIL (3 shipped)**
- [ ] **RejectReason enum 5 values per CONTRACT § 2.3 — diverges (4 shipped)**
- [x] 5 migrations idempotent raw SQL (renumbered 026-030; rationale documented)
- [x] All domain entities have soft-delete `deleted_at` where required
- [x] No PHI in any entity field (UUID refs only)

## Allowlist Movement

- [x] No allowlist grew. Arch fitness 270/270 PASS.

## Native-First Audit

- [x] No `docker exec` in commits
- [x] No `git add .` / `-A` / `-u` in commits
- [x] Not pushed to main (wip/vitalia)

## Verdict Math

- BowtieStage 3-vs-5 mismatch = **FAIL Cat 1 (DDD/Contract)** — drift affects 4 downstream tickets and FE
- RejectReason mismatch = **WARN Cat 11 (cross-cutting)**
- Other categories all PASS
- Overall: **CHANGES_REQUESTED** — Case B (spawn `dev-team builder-backend` to fix BowtieStage + RejectReason verbatim; whitelist allows neither because it's a business enum cascade change touching 4+ files >10 LOC).

## Action policy per `.claude/rules/auditor-self-fix-policy.md`

Per § "NUNCA self-fix" #2 (Cambiar/agregar branch lógico) + #4 (Agregar nuevo método/función) — enum cardinality change with downstream cascade is dev-team scope, NOT auditor self-fix.

**Recommended handoff to `/dev-team`:**
- Fix BowtieStage enum (5 stages literally per spec)
- Fix RejectReason enum (5 values literally per spec)
- Update test_enums.py cardinality + value assertions
- Verify all consumers (model VARCHAR comment, marketing_service map, jobs, routes, DTOs, FE types) align
- Re-run gate-runner

Builder should NOT touch other findings (currency/PHI/migration shape) — those are PASS.

---

## Audit iteration 2 (2026-05-21T00:50:00Z — post AUDITOR_AUTO_FIX_LOOP commit ac8ec6f3)

### Verdict
**APPROVED**

### Re-verification (iter 1 findings)

| Finding | Status | Evidence |
|---|---|---|
| FAIL: BowtieStage 3-vs-5 mismatch | ✅ FIXED | `domain/enums.py:57-72` — 5 values (ATTRACTION/QUALIFICATION/RESERVATION/ADOPTION/EXPANSION) per spec verbatim |
| WARN: RejectReason 4-vs-5 mismatch | ✅ FIXED | `domain/enums.py:75-90` — 5 values (NOT_PRIORITY/ALREADY_DOING/DATA_WRONG/TOO_RISKY/OTHER) per spec verbatim |
| info: Migration renumbering 026-030 | unchanged | (was non-blocking already) |

### Downstream cascade verified

- `marketing_service._STAGE_CHANNEL_MAP` (`services/marketing_service.py:31-37`) — 5 keys mapping correctly to ATTRACTION/QUALIFICATION/RESERVATION/ADOPTION/EXPANSION ✓
- `events.LucasRecommendationGenerated.stage: BowtieStage = BowtieStage.ATTRACTION` default ✓
- `routes.py:471-474` provider→stage mapping uses `BowtieStage.ATTRACTION` ✓
- `test_enums.py::TestBowtieStage::test_has_exactly_five_stages` ✓ (was `_three_`)
- `test_enums.py::TestRejectReason::test_has_exactly_five_reasons` ✓ (was 4)
- `lucas_daily_analysis_sweep.py:185-187` uses `BowtieStage(rec_stage_raw).value` for safety (string conversion — see T-mk-be-6 note about type misuse)

### Category re-summary

| # | Category | Status |
|---|---|---|
| 1 | DDD Layer Compliance | PASS |
| 11 | Cross-cutting | PASS (no more spec drift) |
| Contract compliance | PASS |

### Verdict math
- All iter 1 findings addressed verbatim per spec
- 0 regressions introduced in this ticket's surface
- Overall: **APPROVED**

