# T-1 Implementation Log — BE migration prohibited_phrases + telemetry whitelist

**Story:** vitalia-fase2-lisa-marca
**Ticket:** T-1
**Surface:** BE
**Estimate:** 2 hours
**Owner:** builder-backend (Claude Sonnet 4.6)
**Started:** 2026-05-27

---

## Skills Consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When consulted | Decision |
|---|---|---|---|
| `backend-expert` | LOADED | Step 0 | DDD Inside-Out. SQLAlchemy 2.0 `Mapped[]` columns. No PHI on this story (owner config). `Repository` base (NOT `PhiRepositoryBase`). runtime-quality-checklist.md read. |
| `brand-expert` | LOADED | Step 0 | PersonalityProfile SSoT = `personality_profiles.system_instruction`. 4 archetypes salud-friendly. NO mirror `brand_voice_summary`. `vitalia_prohibited_phrases` = soft warning configurable (NOT LLM validator anti-creep). |
| `.claude/rules/tenant-isolation.md` | LOADED | Step 0 | Every query filters `tenant_id`. Exception: seed defaults `tenant_id IS NULL` whitelisted in arch test allowlist. |
| `.claude/rules/backend-ddd.md` | LOADED | Step 0 | Inside-Out layers. SQLAlchemy 2.0 only. No cross-module imports. |
| `.claude/rules/backend-migrations.md` | LOADED | Step 0 | Raw SQL `IF NOT EXISTS`. NEVER `op.create_table()`. NEVER `sa.Enum(create_type=True)`. Idempotent. |
| `.claude/rules/anti-duplication.md` | LOADED | Step 0 | `vitalia_prohibited_phrases` scan: zero cross-brand match — NEW brand-local OK. |
| `.claude/rules/tdd-mandatory.md` | LOADED | Step 0 | RED phase tests first, then GREEN implementation. |
| `.claude/rules/sales-agent-brand-voice.md` | LOADED | Step 0 | Anti-creep cardinal: NO `health_voice_validator.py`, NO `brand_voice_summary` mirror. Soft warning via configurable table = allowed. |
| `.claude/rules/spanish-text.md` | LOADED | Step 0 | Seed phrases: Spanish neutro LatAm (no voseo). |
| `vitalia/.claude/rules/hipaa-lite.md` | LOADED | Step 0 | This story = owner config (NOT PHI direct). Dual filter NOT needed (tenant-level config, not clinic-level). Audit log defense-in-depth applies for mutations (T-2 scope). Sanitize_payload applies to telemetry. |
| `tessl__pytest-api-testing` | LOADED | Step 0 | AsyncSession fixtures, factory fixtures, DB isolation for seed tests. |

---

## Scope Verification

- Surface: BE only (no FE, no agentic, no engine)
- Files in scope per 03-arch § T-1 deliverables:
  1. `vitalia/backend/alembic/versions/033_f2_s7_vitalia_lisa_marca.py` (NEW migration)
  2. `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` (MODIFY — extend whitelist)
  3. `vitalia/backend/src/modules/vitalia/_shared/telemetry/file_size_bucket.py` (NEW helper)
  4. `vitalia/backend/tests/modules/vitalia/brand_studio/test_prohibited_phrases_migration.py` (NEW — RED test)
  5. `vitalia/backend/tests/modules/vitalia/brand_studio/test_prohibited_phrases_seed.py` (NEW — RED test)
  6. `vitalia/backend/tests/modules/vitalia/_shared/telemetry/test_whitelist_lisa_marca_events.py` (NEW — RED test)
- Zero engine edits (`core/luana-core-*/src/`) — confirmed
- Zero cross-brand edits — confirmed
- Zero frontend edits — confirmed

---

## Step 0.5 — Default Flip Detection

No feature flag flips in T-1. N/A per 03-arch § 9.5.

---

## Iteration Log

### Iter 1 — 2026-05-27

**Phase: RED** (write tests first, verify they fail, then implement)

**Tests written (RED phase):**
1. `test_prohibited_phrases_migration.py` — tests for table existence + index existence
2. `test_prohibited_phrases_seed.py` — tests for 10 seed rows PE present
3. `test_whitelist_lisa_marca_events.py` — tests for 13 lisa_marca_* events in whitelist

**Phase: GREEN** (implementation)

1. Migration `033_f2_s7_vitalia_lisa_marca.py` — raw SQL idempotent, `IF NOT EXISTS`, 10 seed rows PE, `ON CONFLICT DO NOTHING`
2. `growth_studio_emitter.py` MODIFIED — added `_KNOWN_EVENT_NAMES` constant with 15 events total (2 existing + 13 new `lisa_marca_*`)
3. `file_size_bucket.py` NEW — `bucket_file_size()` helper

**Validators run:**
- be_lint: PENDING
- be_arch_fitness: PENDING
- be_test_prohibited_phrases_migration: PENDING
- be_test_prohibited_phrases_seed: PENDING
- be_test_telemetry_whitelist_extend: PENDING

---

*Log updates: append after each iteration.*
