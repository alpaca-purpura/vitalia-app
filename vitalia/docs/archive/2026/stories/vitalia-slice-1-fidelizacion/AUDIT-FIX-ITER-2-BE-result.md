# Audit Fix Iter 2 — BE result
# vitalia-slice-1-fidelizacion

> Mode: AUDITOR_AUTO_FIX_LOOP  
> Iteration: 2 (BE)  
> Date: 2026-05-20  
> Findings fixed: F1 + F2  
> Validator verdict: ALL GREEN

## Findings resolved

### F1 — UTILITY vs MARKETING template gate (T-5-review.md WARN)

**Root cause:** `proactive_outbound_service.py` step 2 blocked ALL templates when
`marketing_opt_in=False`, ignoring `WHATSAPP_TEMPLATE_REGISTRY.requires_marketing_opt_in`.
UTILITY templates (appointment reminders) were incorrectly blocked for patients without
marketing opt-in — contradicting 03-arch-be.md §7 and T-8 registry SSoT.

**Fix applied:**

File: `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/proactive_outbound_service.py`

- Added import: `from src.modules.vitalia.connections.whatsapp.registry import WHATSAPP_TEMPLATE_REGISTRY`
- Replaced simple `if not marketing_opt_in` block with registry-aware logic:
  1. Look up `template_def = WHATSAPP_TEMPLATE_REGISTRY.get(template_id)`
  2. Unknown template → return `blocked_reason="template_unknown"`
  3. `template_def.requires_marketing_opt_in and not marketing_opt_in` → return `blocked_reason="marketing_opt_in_required"`
  4. UTILITY templates (`requires_marketing_opt_in=False`) → proceed regardless of `marketing_opt_in`
- Updated module docstring to document SC-03 (UTILITY passes without opt-in) and cite 03-arch-be.md §7

File: `vitalia/backend/tests/modules/vitalia/fidelizacion/application/test_proactive_outbound_service.py`

- Updated all test slugs from invalid (`"multi_session_reminder_01"`, `"follow_up_reminder_01"`)
  to valid registry slugs: `"invitacion_mantenimiento"` (MARKETING) and `"recordatorio_proxima_sesion"` (UTILITY)
- SC-02 assertion tightened: `result.blocked_reason == "marketing_opt_in_required"`
- Added SC-03 test `test_utility_template_passes_without_marketing_opt_in`:
  - `template_id="recordatorio_proxima_sesion"` (UTILITY, `requires_marketing_opt_in=False`)
  - `marketing_opt_in=False` (patient without marketing consent)
  - Expected: `status="sent"`, `blocked_reason is None`, `nps_repo.save` called once

### F2 — pgcrypto trigger for nps_responses.comment PHI (T-4-review.md WARN)

**Root cause:** `nps_responses.comment` (patient free-text PHI) stored as plaintext BYTEA
with no pgcrypto encryption. Migration 022 created column but never added extension or trigger.
False docstring at nps_service.py:127-128 claimed trigger existed. Arch test had no coverage
for this column.

**Fix applied:**

File: `vitalia/backend/alembic/versions/025_vitalia_pgcrypto_nps_comment.py` (NEW)
- `revision="025_vitalia"`, `down_revision="024_vitalia"`
- `upgrade()`:
  1. `CREATE EXTENSION IF NOT EXISTS pgcrypto` (idempotent)
  2. `CREATE OR REPLACE FUNCTION vitalia_encrypt_nps_comment()` — PLPGSQL trigger function
     that reads KEK from `current_setting('app.encryption_key', true)` GUC and applies
     `pgp_sym_encrypt(convert_from(NEW.comment, 'UTF8'), _kek)::BYTEA`
  3. `DROP TRIGGER IF EXISTS trg_encrypt_nps_comment` + `CREATE TRIGGER trg_encrypt_nps_comment`
     `BEFORE INSERT OR UPDATE OF comment ON vitalia_nps_responses`
- `downgrade()`: drops trigger + function (preserves encrypted data, does NOT drop pgcrypto extension)

File: `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/nps_service.py`
- Lines 125-131: corrected docstring to accurately describe trigger-based encryption flow and
  KEK rotation policy (anual per hipaa-lite.md)

File: `vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py`
- Added `("nps_responses", "comment")` to `PHI_BYTEA_COLUMNS` allowlist
- Added `test_nps_responses_comment_is_bytea()` — checks BYTEA in migration source
- Added `test_nps_responses_comment_has_pgcrypto_trigger()` — checks `trg_encrypt_nps_comment`
  or `pgp_sym_encrypt` present in migration source
- Updated `test_no_phi_column_uses_text_or_varchar_unencrypted()` to include comment column check
- Updated module docstring to cite migration 025 and audit iter 2 fix F2

## Validator results

```
vitalia/backend/tests/modules/vitalia/fidelizacion/application/test_proactive_outbound_service.py
  6 passed (was 5 — SC-03 added)

vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py
  9 passed (was 7 — 2 new tests added)

vitalia/backend/tests/modules/vitalia/fidelizacion/ (full suite)
  142 passed, 15 skipped

vitalia/backend/tests/architecture/ (full suite)
  270 passed, 2 warnings (no failures)

ruff check (lint): 0 errors
ruff format --check: 5 files already formatted
```

## Files modified

| File | Action | Finding |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/proactive_outbound_service.py` | MODIFIED | F1 |
| `vitalia/backend/tests/modules/vitalia/fidelizacion/application/test_proactive_outbound_service.py` | MODIFIED | F1 |
| `vitalia/backend/alembic/versions/025_vitalia_pgcrypto_nps_comment.py` | CREATED | F2 |
| `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/nps_service.py` | MODIFIED | F2 (docstring) |
| `vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py` | MODIFIED | F2 |

## Scope compliance

- NO scope creep: only files cited in T-4-review.md and T-5-review.md findings
- Migration 025 is the only new file; no new modules created
- All existing tests remain GREEN (no regressions)
- hipaa-lite.md compliance: pgcrypto encryption on PHI free-text column enforced
- 03-arch-be.md §7 contract: UTILITY vs MARKETING opt-in gate now implemented per spec
