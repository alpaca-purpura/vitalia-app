<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Backend Code Review: T-reconcile-be — inbox mutation session-lifecycle fix

**Date:** 2026-06-04
**Brand:** vitalia
**Commit:** 042193b8 (BE surface only) + 1 Carril R self-fix (this audit)
**Files Reviewed (BE in scope):** 1 — `vitalia/backend/src/modules/vitalia/inbox/api/router.py`
**Domains touched:** inbox (business), reads from crm (ConversationRepository), audit (AsyncAuditWriter)
**Skills consulted:** backend-expert (session lifecycle, DDD), hipaa-lite.md (PHI dual filter + audit sync write)
**Verdict:** **APPROVED (with Carril R self-fix applied)**

---

## Scope check

`git diff --name-only 042193b8^..042193b8 -- core/ nicolify/ comunify/ lupulo/` → **empty**.
The BE change touches ONLY `vitalia/backend/src/modules/vitalia/inbox/api/router.py`.
No core/ edit, no other brand, no crm repo edit (`set_pause_until`/`update_handler_mode` already existed in crm). No legacy root paths. No copilot/sales_agent files in the BE surface. Scope discipline: PASS.

---

## /test-backend Gate Status (relevant subset, run natively)

| Gate | Result | Detail |
|---|---|---|
| Lint (ruff check) | PASS | `src/modules/vitalia/inbox/` — All checks passed |
| Format (ruff format --check) | PASS | router.py already formatted |
| Inbox regression (`tests/modules/vitalia/inbox/`) | PASS | 103 passed in 1.13s |
| Arch — response_model required | PASS | mutation handlers keep `response_model=` |
| Arch — PHI dual filter (`test_phi_dual_filter.py`) | PASS | tenant_id + clinic_id intact |
| Arch — audit log sync write (`test_audit_log_sync_write.py`) | PASS | audit row written on session pre-response |
| Arch full suite (minus 1 deselect) | PASS | all pass except 1 PRE-EXISTING unrelated failure (below) |

### Pre-existing unrelated arch failure (NOT this commit, NOT inbox — out of scope)

`tests/architecture/test_pgcrypto_phi_columns.py::...::test_no_phi_column_uses_text_or_varchar_unencrypted`
fails with `treatment_plans.notes defined as TEXT instead of BYTEA`.

- `treatment_plans` lives in the `fidelizacion` module (migration 020/005, created in commit `540249cb`), NOT inbox.
- Commit 042193b8 touched **no** migration / treatment_plans / pgcrypto files.
- Inbox has **zero** reference to `treatment_plans`.

This is a genuine pre-existing PHI-encryption arch gap in `fidelizacion` that this focused change neither introduced nor could fix. It does **not** enter this verdict. **Recommend a separate bugfix story for `fidelizacion` (`treatment_plans.notes` → pgcrypto BYTEA).**

---

## Correctness verification (the session-lifecycle question — verified, not assumed)

### Root cause confirmed
`src/db.py:57` `get_async_session` NEVER commits (delegates to caller). No inbox service calls `.commit()` (grep: zero `.commit()` in the whole inbox module). Therefore every mutation INSERT/UPDATE + audit row was flushed-then-rolled-back at session close → HTTP 200 with no DB row (`pause_until` NULL, `handler_mode` unchanged). This is the same bug CRM hit; the fix reuses the same proven `get_async_session_committing` (`src/db.py:73`, commits on clean return, rolls back on any exception incl. HTTPException, `expire_on_commit=False`).

### The two-session hazard — verified SOUND
Each mutation handler depends on BOTH `session` (handler param → `get_async_session`, non-committing) AND the service factory (now `get_async_session_committing`). FastAPI resolves these as two distinct generators → **two sessions per request**. Verified this is safe:
- Handler-level non-committing `session` is used ONLY by `_resolve_context` (auth/role resolution — reads only). A read-only session that's never written to closes without commit harmlessly.
- The committing session is threaded into `conv_repo` + `audit_writer` + the service's own `session=` (router lines 268-273, 281-287, 295-305, 341-351). So the business write AND the audit row share ONE committing session → commit/rollback atomically.
- **No read-after-write-in-wrong-session hazard:** handlers build `ConversationResponse` from the service `result` DTO (router 762-772, 861-871), NOT from a re-read on the non-committing session. The repo `set_pause_until` does UPDATE then SELECT on the **same** committing session within one transaction (crm `conversation_repository.py:184-199`) → read-back sees the just-written value via autoflush. `expire_on_commit=False` keeps `result` attributes usable while building the response. Sound.

### PHI / security NOT regressed (hipaa-lite.md)
- `response_model=` present on every mutation handler (arch test PASS).
- Dual filter `tenant_id` + `clinic_id` (`scope_attr`) + `deleted_at IS NULL` intact in `update_handler_mode` / `set_pause_until`.
- Audit log written sync via `AsyncAuditWriter.write()` on the committing session with `sanitize_phi_payload` applied + `gen_random_uuid()` server-side; now actually committed (previously silently lost on 200 — this fix *restores* a HIPAA-lite obligation that was broken). No PII echoed in responses/errors.
- Read/other factories left untouched: `_get_activity_service` (read) stays on `get_async_session`. Correct.

---

## Findings

### FAIL → FIXED (Carril R mechanical self-fix): a 6th mutation factory was omitted
**Category:** 1 (DDD / session lifecycle correctness)
**File:** `vitalia/backend/src/modules/vitalia/inbox/api/router.py:248` `_get_retract_service`
**Issue:** The commit fixed 5 factories and the message claims "ALL inbox mutation endpoints." But `_get_retract_service` (endpoint `POST .../revert`, handler `revert_message`) was **left on `get_async_session` (non-committing)** despite `RetractMessageService.retract()` performing real writes — `mark_retracted` (UPDATE message), `update_handler_mode` (UPDATE conversation), and `audit_writer.write` (INSERT audit row) (`retract_message_service.py:95,113,127`). Same root cause, same module, same file → the revert endpoint returned 200 but persisted nothing. Identical latent HB-50 bug.
**Fix applied (this audit):** switched `_get_retract_service` to `Depends(get_async_session_committing)` + explanatory comment. One-line mechanical change, no business logic touched. Re-ran gates: ruff PASS, format PASS, 103 inbox tests PASS, 3 PHI/contract arch tests PASS.
**Rule ref:** auditor-self-fix-policy.md v5 Carril R (mechanical sub-case — session-lifecycle, BE surface, no stake-asymmetric logic change, no new test required).

### WARN: retract persistence was never live-verified (DoD #37)
**Category:** 10 / Live-verify
**Issue:** The orchestrator's golden (7/7 dev-app + DB-verified) covered mode/pause and the other 5. Because `_get_retract_service` was on the non-committing session and is now changed by this audit, retract/revert persistence has **not** been DB-verified live. The 103 inbox tests pass but did NOT catch the original 5-factory bug either (test-controlled transactions mask commit behavior — verification-≠-200). Existing tests therefore do not *verify* persistence.
**Recommendation:** before `done`, exercise `POST .../{conv_id}/revert` live against dev-app and confirm the message row flips `retracted` + an audit row appears in `vitalia_audit_log` (the same DB-verify standard already applied to mode/pause). Non-blocking for this BE correctness verdict, but required by the story's DoD gate.

---

## Contract / scope compliance (BE surface only)

- [x] Only the intended 5 mutation factories switched (verified diff).
- [x] 6th mutation factory (`_get_retract_service`) — corrected by this audit (Carril R).
- [x] Read factory (`_get_activity_service`) left on non-committing session — correct.
- [x] `response_model=` on all mutation handlers.
- [x] Dual filter + soft-delete aware in repo writes.
- [x] Audit sync write preserved + now committed.
- [x] No core/ / cross-brand / crm-repo edits.

## Allowlist Movement
No arch-fitness allowlist grew. (The pgcrypto `treatment_plans.notes` entry is pre-existing and unrelated.)

## Self-fix log (Carril R — mechanical)
- `router.py:248` `_get_retract_service`: `Depends(get_async_session) → Depends(get_async_session_committing)` + comment. Verified by existing suite `tests/modules/vitalia/inbox/` (103 passed) which exercises retract service wiring, plus arch tests. Diff: one dependency swap, no logic change.

## Verdict Math
- Correctness of the 5-factory fix: SOUND (no transaction-leak / double-session / read-after-write hazard).
- PHI/security: NOT regressed (response_model + dual-filter + audit sync intact; fix restores a broken HIPAA obligation).
- One incomplete-fix FAIL (6th mutation factory) → **fixed in-audit via Carril R**, gates re-run ALL GREEN.
- Pre-existing unrelated `fidelizacion` pgcrypto failure → out of scope, separate story recommended.
- One WARN (retract live-verify pending) → non-blocking for BE correctness, required by DoD before `done`.

**Verdict: APPROVED** (BE session-lifecycle fix is correct and complete after the Carril R self-fix; one DoD WARN to clear before merge→done).
