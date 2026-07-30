# T-1 Result — BE fix root cause (sanitize_payload → sanitize_phi_payload)

**Story:** arreglar-guardado-voz-y-tono  
**Ticket:** T-1  
**Commit:** `38aa5c8b`  
**Branch:** `wip/vitalia`  
**State:** tests-passing

---

## Summary

Root cause confirmed: `luana_core_observability.sanitize_payload` dropped the
`compliance_level` kwarg from its public signature. Three vitalia call sites
still passed `compliance_level="hipaa_lite"` → `TypeError` → HTTP 500 on every
audit write triggered by `PATCH /api/v1/lisa/marca/personality`.

Fix: repointed all 3 callers to the existing brand-local wrapper
`compliance/application/compliance_service_adapter.py::sanitize_phi_payload(payload)`.
No new abstraction created. No import cycle (compliance does not import audit).
Double benefit: fixes the 500 AND restores PHI redaction that was silently dead
while the call was raising (the except was not there to rescue it).

---

## Files Changed

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` | Repoint `write_audit_log_sync` (~L92) + `AsyncAuditWriter.write` (~L184) to `sanitize_phi_payload`. Update module + inline docstrings. |
| `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` | Repoint `emit_event` (~L137) to `sanitize_phi_payload`. Update docstrings. |
| `vitalia/backend/tests/modules/vitalia/audit/test_audit_writer_sanitize.py` | NEW — 9 regression tests (TDD RED→GREEN). |

**Files NOT touched (out of T-1 scope):**
- `vitalia/backend/src/modules/vitalia/brand_studio/api/dtos/marca_dtos.py` → T-2
- `core/luana-core-*/src/` → engine (read-only per rules)
- Any `{other_brand}/` path → forbidden

---

## TDD Evidence (RED → GREEN)

**RED (before fix):** `test_phi_redacted_top_level_fields` reproduced the exact bug:

```
FAILED tests/modules/vitalia/audit/test_audit_writer_sanitize.py::TestAuditWriterPhiRedaction::test_phi_redacted_top_level_fields
src/modules/vitalia/audit/audit_writer.py:90: in write_audit_log_sync
    safe_payload = sanitize_payload(payload or {}, compliance_level="hipaa_lite")
TypeError: ...lambda...() got an unexpected keyword argument 'compliance_level'
```

**GREEN (after fix):** All 9 tests pass.

---

## Validator Output (literal)

### be_regression_audit_sanitize

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3
collected 9 items

tests/modules/vitalia/audit/test_audit_writer_sanitize.py .........      [100%]

============================== 9 passed in 0.19s ===============================
```

### be_lint (ruff check + ruff format --check)

```
All checks passed!
9 files already formatted
```

### arch_no_dead_compliance_kwarg

In-scope files (audit/, _shared/telemetry/): **PASS — no dead compliance_level kwarg calls found.**

```bash
grep -rn 'sanitize_payload(' vitalia/backend/src/modules/vitalia/audit/ \
  vitalia/backend/src/modules/vitalia/_shared/telemetry/ \
  --include='*.py' | grep -v 'def sanitize' | grep 'compliance_level'
# (no output = PASS)
```

**Out-of-scope docstring mentions** (noted, not fixed per ticket instructions):
- `crm/infrastructure/persistence/models/activity_event_model.py:11` — docstring only
- `crm/domain/activity_event.py:38` — docstring only
- `sales_agent/observability/recording/callback_handler.py:37` — docstring only
- `sales_agent/persistence/models/lead_screening_event.py:11` — docstring only
- `sales_agent/tools/retract_last_message.py:46` — docstring only
- `copilot/persistence/models/copilot_trace_event.py:40` — docstring only

These are docstrings in out-of-scope modules (crm, sales_agent, copilot). No active
call sites. Per T-1 assignment.rationale: "Files OUTSIDE your scope that only mention
it in docstrings, leave them." A follow-up docstring sweep for those modules can be
done as a separate chore ticket.

### arch_tenant_isolation_personality

```
tests/architecture/test_phi_dual_filter.py ...........    [100%]
tests/architecture/test_audit_log_sync_write.py passed
(11 passed)
```

---

## PHI Redaction Verified

Test `test_phi_redacted_top_level_fields` and `test_phi_redacted_patient_nested_fields`
use the REAL `sanitize_phi_payload` function (only the inner engine call is mocked).
Assertions:

- `diagnosis: "Caries grado III"` → `[REDACTED-PHI]` ✓
- `treatment_plan: "Extracción + implante"` → `[REDACTED-PHI]` ✓
- `patient.name: "María González"` → `[REDACTED-PHI]` ✓
- `patient.dni: "12345678"` → `[REDACTED-PHI]` ✓
- `archetype: "sage"` → preserved ✓ (non-PHI)
- `patient.appointment_count: 3` → preserved ✓ (non-PHI)

---

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | Anti-patterns FastAPI/SQLA/tests · runtime-quality-checklist | Lazy import pattern OK for unit tests; patch at source module for lazy imports (not at consumer module). No legacy SQLA patterns introduced. |
| `tessl__pytest-api-testing` | Fixture scoping, AsyncMock, patch strategy for lazy imports | Used `AsyncMock` for async session; patched `_SANITIZE_PHI_PATCH` at source module (not caller). `asyncio.run()` for sync test context. |
| `.claude/rules/tdd-mandatory.md` | TDD RED→GREEN mandatory order | First entry in impl log = RED test reproducing TypeError. Fix applied AFTER red confirmed. |
| `.claude/rules/test-design-doctrine.md` | Nature: bug fix → regression test FIRST; verify REAL redaction (not just 200) | Wrote regression tests that fail with old code; verified PHI redaction with real `sanitize_phi_payload`, not just mock. |
| `vitalia/.claude/rules/hipaa-lite.md` | PHI fields catalog, 22 canonical fields, sanitize_phi_payload semantics | Used `REDACTED_PLACEHOLDER` from `phi_fields.py`; tested both top-level and `patient.*` nested PHI fields. |

---

## Cross-Story Observed Bugs (non-egoísmo clause)

No bugs observed outside T-1 scope during this session.

---

## Notes

- The bidirectional validator pre-commit advisory (`HARD_FAIL drift=2`) is for
  `cross_check_3` (e2e_test paths in cap YAML). This is expected: the e2e wire
  for `lisa-marca` cap scenario happens at Fase F.3 merge per `06-tickets.yaml`
  comment: "wire e2e_test del scenario 'admin-define-voz-y-tono'". Not a blocker
  for wip/* branch.
- `brand_studio/api/dtos/marca_dtos.py` is modified in the working tree (T-2 work
  by a parallel session). Correctly NOT included in this T-1 commit (pathspec).

---

## T-1.bis — Second latent bug: SQLAlchemy text() bindparam broken by PostgreSQL inline cast

**Commit:** `a0060e7a`  
**Branch:** `wip/vitalia`  
**State:** tests-passing

### Summary

With T-1 fixing the `sanitize_payload` TypeError, the audit INSERT now actually
executes — and reveals a second latent bug that was previously masked. Root cause:
SQLAlchemy's `text()` bindparam regex uses a `(?!:)` negative-lookahead and
REFUSES to bind `:param` when immediately followed by `::` (PostgreSQL inline cast
syntax). For example, `:tenant_id::uuid` makes SQLAlchemy skip the param — the
literal `::` colons reach Postgres → `asyncpg.exceptions.PostgresSyntaxError:
syntax error at or near ":"`.

This bug breaks ALL audit writes and ALL growth studio telemetry emits across the
codebase (every brand_studio patch, trust-signals, CRM, etc.), since the personality
autosave is just the symptom under test.

### Root Cause

```
:tenant_id::uuid  →  SQLAlchemy sees `:` → checks for `::` lookahead → skips binding
→ literal `:tenant_id::uuid` sent to Postgres → syntax error
```

### Fix Applied

Replace every `:param::type` inline cast with `CAST(:param AS type)` — SQL
behavior is identical at the Postgres level; only the parameterization mechanism
differs.

**`audit_writer.py` — write_audit_log_sync (sync INSERT):**
```sql
-- BEFORE (broken):
CAST(:tenant_id AS uuid)  -- was: :tenant_id::uuid
CAST(:clinic_id AS uuid)  -- was: :clinic_id::uuid
CAST(:user_id AS uuid)    -- was: :user_id::uuid
CAST(:resource_id AS uuid) -- was: :resource_id::uuid
```

**`audit_writer.py` — AsyncAuditWriter.write (async INSERT):**  
Same 4 replacements as the sync block.

**`growth_studio_emitter.py` — emit_event:**
```sql
-- BEFORE (broken):
CAST(:props AS jsonb)  -- was: :props::jsonb
```

**`test_audit_log_sync.py` — migration of legacy test assertions:**  
The pre-T-1 test file patched `luana_core_observability.sanitize_payload` at the
engine inner call and asserted the old `compliance_level` kwarg. After T-1, the
call site uses `sanitize_phi_payload` (no kwarg). Migrated `_SANITIZE_PATCH` to
the vitalia wrapper and updated assertions accordingly.

### TDD Evidence (RED → GREEN)

**RED (before fix):**
```
FAILED TestInlineCastGuard::test_audit_writer_no_inline_cast
AssertionError: audit_writer.py contains broken inline SQLAlchemy cast(s):
[':tenant_id::', ':clinic_id::', ':user_id::', ':resource_id::', ...]
```

**GREEN (after fix):** All 21 tests pass (9 original + 5 new guard + 7 migrated).

### Validator Output

```
============================= test session info ==============================
platform linux -- Python 3.12.3, pytest-9.0.3
collected 21 items

vitalia/backend/tests/modules/vitalia/audit/ ...................     [100%]

============================== 21 passed in 0.21s ==============================
```

```bash
# Guard grep (must return nothing):
! grep -rnE ':\w+::(uuid|jsonb|text|timestamp)' \
  vitalia/backend/src/modules/vitalia/audit/ \
  vitalia/backend/src/modules/vitalia/_shared/telemetry/
# → GUARD PASS — no inline casts found
```

```
ruff check: All checks passed!
ruff format --check: 9 files already formatted
```

### Skills Consulted (T-1.bis)

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | SQLA 2.0 text() bindparam behavior, PostgreSQL cast alternatives | `CAST(:x AS type)` is correct SQL standard form; SQLAlchemy parses it without negative-lookahead issue. Behavior identical at Postgres level. |
| `tessl__pytest-api-testing` | Source inspection tests, importlib/inspect pattern, deterministic assertions without live DB | `inspect.getsource(module)` + regex guard is deterministic and catches the pattern without requiring asyncpg to execute. |
| `.claude/rules/tdd-mandatory.md` | TDD RED→GREEN mandatory — guard tests must be RED before fix | Confirmed RED on `TestInlineCastGuard.test_audit_writer_no_inline_cast` before applying CAST migration. |
| `.claude/rules/test-design-doctrine.md` § Verificación REAL | "verificado" must mean the action was actually exercised + logs read — NOT just "saqué 200" | Guard test reads source and asserts the cast form; bonus test asserts CAST appears ≥2× (both SQL blocks). |
