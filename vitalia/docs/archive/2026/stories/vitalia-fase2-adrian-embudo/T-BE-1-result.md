# T-BE-1 Result — Funnel domain + migration + repos

**Story:** vitalia-fase2-adrian-embudo
**Ticket:** T-BE-1
**Agent:** builder-backend (Sonnet 4.6)
**Date:** 2026-06-03
**State:** tests-passing (60 new GREEN, 212 total domain+infra GREEN)

---

## Files created / modified (paths relative to repo root)

### NEW files

| File | Purpose |
|---|---|
| `vitalia/backend/src/modules/vitalia/crm/domain/funnel_machine.py` | STAGE_MACHINE 6 etapas, SLA_DAYS, FREEZE_RULES, HOT_BOARD_STAGES, helper fns |
| `vitalia/backend/src/modules/vitalia/crm/domain/lead_stage_transition.py` | LeadStageTransition dataclass (non-PHI, `reason` NOT `notes`) |
| `vitalia/backend/src/modules/vitalia/crm/domain/lead_activity.py` | LeadActivity dataclass (commercial micro-log, non-PHI) |
| `vitalia/backend/src/modules/vitalia/crm/domain/exceptions.py` | StaleStateError, InvalidTransitionError, ManualReservadoForbiddenError, ReasonRequiredError |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/lead_stage_transition_repository.py` | LeadStageTransitionRepository (record + list_for_lead, tenant isolation) |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/lead_activity_repository.py` | LeadActivityRepository (record + last_for_lead + list_for_lead, tenant isolation) |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/models/lead_stage_transition_model.py` | SA 2.0 model for vitalia_lead_stage_transition |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/models/lead_activity_model.py` | SA 2.0 model for vitalia_lead_activity |
| `vitalia/backend/alembic/versions/038_vitalia_adrian_embudo_funnel.py` | Idempotent migration: +18 ADD COLUMN IF NOT EXISTS + 2 CREATE TABLE IF NOT EXISTS + indexes + backfill |
| `vitalia/backend/tests/modules/vitalia/crm/domain/test_funnel_machine.py` | 31 RED→GREEN tests: stage machine, SLA, freeze, hot board |
| `vitalia/backend/tests/modules/vitalia/crm/infrastructure/test_lead_repository_stage.py` | 12 RED→GREEN tests: update_stage, list_for_board, freeze, reactivate signatures + optimistic lock |
| `vitalia/backend/tests/modules/vitalia/crm/infrastructure/test_lead_stage_transition_repository.py` | 17 RED→GREEN tests: repository interface, tenant isolation, domain entities |

### MODIFIED files

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/crm/domain/lead.py` | +18 funnel fields (stage, score, version, is_frozen, channel, estimated_value, currency, buying_signals, etc.) |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/lead_repository.py` | +update_stage() optimistic lock, +list_for_board() RN-17 sort, +freeze(), +reactivate(), +_row_to_lead() helper; updated get_by_id + list_by_filter SELECT to include funnel columns |

---

## Validator gates output

### NF-1 — Ruff lint
```
All checks passed! (ruff check src/modules/vitalia/crm/ tests/modules/vitalia/crm/ --no-cache)
```

### NF-2 — Ruff format
```
69 files already formatted (ruff format --check)
```

### NF-3 — Pytest (T-BE-1 tests)
```
60 passed in 0.24s
  - test_funnel_machine.py: 31 passed
  - test_lead_repository_stage.py: 12 passed
  - test_lead_stage_transition_repository.py: 17 passed
```

### NF-6 — Architecture fitness (scoped)
```
- test_no_hardcoded_strings_inbox.py: PASS (fixed USD comment in domain/lead.py)
- test_lead_repository.py (existing): PASS (not-phi-repository gate still holds)
```

**Pre-existing failure (NOT caused by T-BE-1):**
- `test_pgcrypto_phi_columns.py` — `treatment_plans.notes TEXT` from migration 005 (commit 11949417, predates this ticket). My migration 038 uses `reason TEXT` (NOT `notes TEXT`) to avoid the regex pattern per 03-arch-be.md § 2 note.

### F-9 — Migration idempotency
- 38 `IF NOT EXISTS` / `IF EXISTS` clauses in migration 038
- No `op.create_table()`, `op.add_column()`, or `sa.Enum(create_type=True)` (verified by grep — only appear in NEVER-use comment section)
- Backfill UPDATE: `WHERE stage IS NULL OR stage = 'interesado'` (idempotent)

---

## Technical decisions

### 1. Funnel machine transitions
- `STAGE_MACHINE`: forward-only dict, empty list = terminal. `reservado` listed in machine (for service validation) but `is_manual_reservado_forbidden()` guards manual→403 at service layer (T-BE-2).
- `SLA_DAYS`: 4 active stages with green/amber/red thresholds per 03-arch-be.md § 1 + RN-11.
- `FREEZE_RULES`: 3 triggers — no_response 14d / hard 30d / 2×SLA multiplier per RN-13.

### 2. Optimistic lock mechanism
`update_stage()` uses raw SQL `UPDATE ... WHERE tenant_id=:t AND id=:id AND version=:expected_version AND deleted_at IS NULL`. `result.rowcount == 0` → raises `StaleStateError` (domain exception). Service layer (T-BE-2) catches and maps to 409 HTTP. Version incremented by DB (`version = version + 1`) atomically in same UPDATE.

### 3. `reason` vs `notes` field naming
`LeadStageTransition.reason` is named `reason` NOT `notes` to avoid the arch fitness test `test_pgcrypto_phi_columns.py` regex pattern `r"(?<![\w])notes\s+TEXT"` which detects PHI columns that should use BYTEA encryption. `reason` = commercial override context (non-PHI), correctly uses TEXT.

### 4. Backfill logic
Status→stage mapping preserves existing data backward-compatibly:
- `new` → `interesado`, `contacted` → `calificando`, `qualified` → `consulta_agendada`, `converted` → `reservado`, `lost` → `decidio_no`. WHERE clause is idempotent (only updates NULL/default-stage rows).

### 5. _row_to_lead() helper
Unified row mapper in LeadRepository handles both pre-funnel (missing columns → default values) and post-funnel rows. Uses `getattr(row, attr, default)` pattern for backward-compat — queries to old schema return `stage='interesado'` etc.

### 6. Lift candidate comments
Added lift candidate comments in `funnel_machine.py` and `channel-meta` (FE per arch) per anti-duplication.md mandate: "do NOT lift proactively; create PR if 2nd brand requests."

---

## Skills Consulted (must_load enforcement v4.1)

| Skill/Rule | Status | Decision cited |
|---|---|---|
| `backend-expert` | Invoked | Loaded `runtime-quality-checklist.md`: Annotated deps pattern, tenant isolation per query, SA 2.0 `select().where()`, `response_model=` mandatory, no `Column()` legacy, `ConfigDict` v2. Migration: raw SQL `IF NOT EXISTS` enforced. |
| `tenant-isolation.md` | Loaded | Every method (get_by_id, update_stage, list_for_board, freeze, reactivate, record, list_for_lead) raises ValueError if tenant_id is None. No query without `WHERE tenant_id = :tenant_id`. |
| `backend-ddd.md` | Loaded | Inside-Out: domain (pure Python) → infra (SA 2.0 + raw SQL repos) → no app/api in this ticket (T-BE-1 scope). No cross-module imports. |
| `backend-migrations.md` | Loaded | All DDL raw SQL `IF NOT EXISTS`. No `op.create_table()`, no `sa.Enum(create_type=True)`. Backfill UPDATE idempotent. |
| `vitalia/.claude/rules/hipaa-lite.md` | Loaded | Lead = non-PHI → single `tenant_id` filter only (no clinic_id dual filter). `LeadActivity.description_es` must never contain clinical data (domain docstring enforces). `reason` field in transitions = commercial context, non-PHI. |
| `tdd-mandatory.md` | Applied | RED tests written first (60 tests all failed on missing modules), implementation second, all GREEN after. |
| `anti-duplication.md` | Applied | Cross-brand grep confirmed: `lead_stage_transition|funnel|board|pipeline` = 0 matches in comunify/nicolify/lupulo. NET-NEW justified (vertical-specific dental). Lift candidate comment added. |
| CONTEXT-BRIEF.md R24 | Verified | `Validator pass: DEFERRED` (not `_pending_`), `Faithfulness flag: partial` (not `blocking`). §11 gaps acknowledged (path consistency + reservado stub + override-context deferred). |

---

## Faithfulness gaps acknowledged (§11 CONTEXT-BRIEF.md)

1. **Path consistency (Open Q #1):** `/api/v1/crm/` vs `/api/v1/vitalia/crm/` — NOT resolved in T-BE-1 (pure domain/infra). T-BE-2 must verify with `curl` before wiring new endpoints.
2. **ChannelBadge lift candidate:** comment in code, no proposal created (per anti-duplication.md decision).
3. **override-context (RN-4.1):** T-AG-1 only, not T-BE-1 scope.

---

## Integration registration (CONN check)

T-BE-1 is foundational layer. Not directly exposed to consumers yet.
- `FunnelMachine` → consumed by `FunnelService` (T-BE-2)
- `LeadStageTransitionRepository` → consumed by `FunnelService` (T-BE-2)
- `LeadActivityRepository` → consumed by `FunnelService` (T-BE-2) and T-AG-1 wire
- `update_stage` on `LeadRepository` → consumed by `FunnelService.transition_stage()` (T-BE-2)

Registration: T-BE-2 wires DI via `Depends(get_async_session_committing)` and registers router in `main.py`.

---

## What BLOCKS on T-BE-1

- T-BE-2: FunnelService + ScoreService + DiagnoseService + DTOs + API routes
- T-FE-2: board hooks (needs board endpoint from T-BE-2)
- T-FE-3: lead workspace (needs detail endpoint from T-BE-2)
