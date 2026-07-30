<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 -->
# Backend Code Review Summary — vitalia-slice-1-fidelizacion

**Date:** 2026-05-20
**Brand:** vitalia
**Story:** vitalia-slice-1-fidelizacion
**Audit iteration:** 2 (iter 1 BE partial — only T-1 + T-2 reviewed due to token cap; iter 2 completes T-3..T-9, T-15, T-16)
**Files Reviewed (cumulative BE iter 1 + 2):** ~70+ source + test files
**Verdict:** **CHANGES_REQUESTED**

## Tickets audit roll-up

| Ticket | Surface | Type | production_code | Verdict | Iteration |
|---|---|---|---|---|---|
| T-1 | backend | migration | true | PASS | iter 1 (existing) |
| T-2 | backend | backend | true | PASS | iter 1 (existing) |
| T-3 | backend | tests (arch fitness) | false | PASS | iter 2 |
| T-4 | backend | backend (domain+infra) | true | **WARN (F2)** | iter 2 |
| T-5 | backend | backend (application services) | true | **WARN (F1)** | iter 2 |
| T-6 | backend | backend (workers) | true | PASS | iter 2 |
| T-7 | backend | backend (API) | true | PASS | iter 2 |
| T-8 | backend | backend (templates registry) | true | PASS | iter 2 |
| T-9 | agentic | agentic (Adrián tool) | true | PASS (CROSS-SCOPE — primary auditor-agentic) | iter 2 |
| T-10 | agentic | agentic (Lucas tool) | true | NOT REVIEWED HERE (CROSS-SCOPE — escalate auditor-agentic) | iter 2 |
| T-15 | agentic | tests (eval goldens) | false | PASS (CROSS-SCOPE — primary auditor-agentic) | iter 2 |
| T-16 | backend | tests (cross-story contracts) | false | PASS | iter 2 |

**Roll-up:** 8 PASS · 2 WARN (T-4 F2 + T-5 F1) · 0 FAIL · 1 CROSS-SCOPE pending (T-10) · 1 CROSS-SCOPE deferred-confirm (T-9 + T-15)

## Pre-verified status (per prompt header)

- ✓ BE arch fitness 268/268 PASS (verified runtime `pytest vitalia/backend/tests/architecture/`)
- ✓ BE unit tests fideliz 141 passed + 15 skipped (verified runtime `pytest vitalia/backend/tests/modules/vitalia/fidelizacion/`)
- ✓ Agentic eval tests T-15 36/36 PASS (verified runtime)
- ✓ Cross-story contracts T-16 26/26 PASS (verified runtime)
- ✓ Ruff lint fideliz module 0 errors
- ✓ Inbox audit iter 2 APPROVED (BE+FE) — no contamination

## Findings critical (2)

### F1 — T-5 `proactive_outbound_service.py` step 2 bloquea ALL templates si `marketing_opt_in=False` (UTILITY incluido)

**Category:** Cat 9 (Security false-positive) + Cat 5 (service contract drift)
**File:** `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/proactive_outbound_service.py:164-180`
**Severity:** WARN
**Impact:** Pacientes sin marketing opt-in NO reciben recordatorios UTILITY (citas confirmadas, NPS post-tratamiento) → UX bug + contradice 03-arch-be.md § 7 + T-8 `WhatsAppTemplateDef.requires_marketing_opt_in` registry SSoT.

**Fix sugerido (en T-5-review.md § F1):**
```python
from src.modules.vitalia.connections.whatsapp.registry import WHATSAPP_TEMPLATE_REGISTRY
template_def = WHATSAPP_TEMPLATE_REGISTRY.get(template_id)
if template_def is None:
    return ProactiveReminderResponse(... blocked_reason="template_unknown" ...)
if template_def.requires_marketing_opt_in and not marketing_opt_in:
    return ProactiveReminderResponse(... blocked_reason="marketing_opt_in_required" ...)
```

**Per `.claude/rules/auditor-self-fix-policy.md`:**
- NO self-fix (toca import nuevo + cambio branch lógico + 2 archivos potencial test fixture)
- **SPAWN dev-team Caso B** con findings cita verbatim (paths + lines + fix sugerido)

**Downstream impact:** Tool T-9 (`send_proactive_reengagement`) hereda este bug — fix en service automáticamente lo arregla en tool surface.

### F2 — T-4 `nps_responses.comment` PHI plaintext en BYTEA sin pgcrypto

**Category:** Cat 8 (Migration Quality) + Cat 9 (Security)
**Files:**
- `vitalia/backend/src/modules/vitalia/persistence/migrations/022_slice1_nps_responses.py` (no pgcrypto extension/trigger)
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/nps_service.py:127-129` (docstring falso "El cifrado real ocurre en la DB" — no existe trigger)
- `vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py:20-24` (allowlist NO incluye `("nps_responses", "comment")` — gap arch coverage)

**Severity:** WARN
**Impact:** NPS comment es PHI free-text. Almacenado como bytes plaintext (`.encode("utf-8")`). Spec hipaa-lite.md § Encryption at rest exige `pgcrypto symmetric encryption`. Aceptable como riesgo Slice 1 SI documentado en commit body + DEPLOYMENT runbook + arch test extendido. Sin ello, gap silencioso.

**Fix sugerido (en T-4-review.md § F2):**
1. Migration 024 (Slice 2): `CREATE EXTENSION IF NOT EXISTS pgcrypto` + trigger BEFORE INSERT/UPDATE encrypt
2. **Slice 1 inmediato:** corregir docstring nps_service.py:127-129 (afirmación falsa) → describir como BYTEA + disk-level encryption deferred
3. Agregar `("nps_responses", "comment")` a `PHI_BYTEA_COLUMNS` allowlist en test_pgcrypto_phi_columns.py (cierra gate)

**Per `.claude/rules/auditor-self-fix-policy.md`:**
- Self-fix permitido step (3) — agregar tuple a `PHI_BYTEA_COLUMNS` (whitelist #16-17 trivial)
- Self-fix permitido step (2) — corregir docstring (whitelist #4 typo en string + comment correction)
- NO self-fix step (1) — Migration 024 es Slice 2 scope, no this story
- **Acción:** auditor puede self-fix los items (2) + (3) en próxima iter SI Chris ratifica; sino spawn dev-team Caso B con scope reducido

## Findings advisory (info — no verdict impact)

- T-5 `adapter_bus` import try/except wrapped — pattern intentional dev-env fallback (Slice 2 tracked)
- T-1 migration files viven en `persistence/migrations/` module-local (no `alembic/versions/`) — divergencia documentada, requires deployment runbook update
- T-9 hereda F1 downstream (no bug del tool)

## Allowlist movement

| Allowlist | Pre-story baseline | Post-story | Δ | Note |
|---|---|---|---|---|
| `KNOWN_LEGACY_CRONS` (cron_envelope_used) | 1 | 1 | 0 | sin growth — 6 nuevos workers usan engine direct |
| `KNOWN_LEGACY_PHI_REPOS` (compound_scope_repository_used) | 2 | 2 | 0 | sin growth — 3 nuevos repos usan engine direct |
| `PHI_BYTEA_COLUMNS` (pgcrypto_phi_columns) | 3 | 3 | 0 | **GAP F2 — nps_responses.comment debería estar pero NO** |
| `test_response_model_required.py` | N/A | N/A | 0 | 9 nuevas routes T-7 declaran `response_model=` |

## HIPAA-lite compliance summary

| Constraint | Status | Evidence |
|---|---|---|
| Dual filter `tenant_id + clinic_id` | PASS | Verified runtime — todos repos extend `CompoundScopeRepositoryBase(scope_field="clinic_id")` |
| Audit log sync write | PASS | Verified en proactive_outbound, nps, opt_out, pause_patient, manual_call services |
| `@require_phi_access` RBAC | PASS | API endpoints declarate decorator + roles |
| pgcrypto BYTEA PHI columns | **WARN F2** | treatment_plans.notes ✓, re_engagement_events.payload_phi ✓ — pero nps_responses.comment GAP |
| No PHI in logs | PASS | structlog UUIDs only; payload_redacted=b"" en audit |
| No PHI in URL params | PASS | POST body para identificadores |
| Soft delete only | PASS | `deleted_at TIMESTAMPTZ NULL` en 3 tablas |
| Outbox pattern para domain events | PASS | `adapter_bus.publish` (engine `luana_core_events`) en 4 services |

## Cross-scope flags (out of backend-auditor jurisdiction)

| Surface | Pending audit |
|---|---|
| `vitalia/backend/src/modules/vitalia/sales_agent/tools/send_proactive_reengagement.py` (T-9) | auditor-agentic primary verdict — LangGraph state, prompt cache, voice fidelity, observability invariants |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_re_engagement_recommendation.py` (T-10) | auditor-agentic primary verdict — ReAct agentic + cluster detection + Opus 4.7 R23 cement |
| `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/**` (T-15) | auditor-agentic primary verdict — golden schema + cost bucket invariant + persona archetype mapping |
| `vitalia/backend/tests/agentic_evals/lucas/re_engagement_recommendation/**` (T-15) | auditor-agentic primary verdict — Lucas internal recommendation tool eval coverage |
| `vitalia/frontend/src/features/fidelizacion/**` (T-11, T-12, T-13, T-14) | auditor-frontend primary verdict — FSD-Lite boundaries + a11y + E2E smoke + Storybook |

## Verdict math (BE-side aggregate)

- **Critical FAILs:** 0
- **WARNs:** 2 (T-4 F2 + T-5 F1) → **CHANGES_REQUESTED** (per `auditor-self-fix-policy.md` § cap 3 audit_iter)
- **Allowlist growth:** 0 (good)
- **Engine edits:** 0 (no `core/luana-core-*/src/` touched in BE)
- **Cross-brand pollution:** 0
- **Test gates:** all PASS

**Next action (per `auditor-self-fix-policy.md`):**

1. F1 (T-5) → **SPAWN dev-team Caso B** con prompt:
   ```
   findings_source: vitalia/docs/product/stories/vitalia-slice-1-fidelizacion/06-audit/T-5-review.md § F1
   Apply fix: consult WHATSAPP_TEMPLATE_REGISTRY.requires_marketing_opt_in en proactive_outbound_service.py step 2.
   Update test_proactive_outbound_service.py para distinguir UTILITY (template_id sin opt-in required) vs MARKETING.
   ```

2. F2 (T-4) → Decisión Chris:
   - **Opción A (self-fix iter 2):** auditor agrega `("nps_responses", "comment")` a allowlist arch test + corrige docstring nps_service.py:127-129 (whitelist #4 + #16-17)
   - **Opción B (deferral Slice 2):** documentar en `07-merge.md § 5 How to verify` warning + tracker en deployment runbook + crear Slice 2 ticket migration 024

3. Cross-scope tickets (T-9, T-10, T-15) → AUTO-HANDOFF a auditor-agentic para primary verdict. FE tickets (T-11..T-14) → auditor-frontend.

## Skills Consulted Trace (consolidated)

✓ backend-expert (runtime-quality-checklist + architectural-fitness)
✓ tessl__fastapi (Pydantic v2 + 501 stub patterns + response_model)
✓ tessl__pytest-api-testing (AsyncMock + fixture scoping + 4-marker pattern)
✓ backend-ddd (Inside-Out boundaries)
✓ tenant-isolation (cardinal rule)
✓ vitalia/.claude/rules/hipaa-lite (overlay — dual filter, audit log, PHI fields, encryption)
✓ anti-duplication (cross-codebase grep verified, no mirror)
✓ tdd-mandatory (RED→GREEN evidence per ticket)
✓ auditor-downstream-regression (engine_edit_detection: 0 engine edits — full multibrand scope acquitted)
✓ auditor-self-fix-policy (cap 3 audit_iter + whitelist categories applied)

---

## AUDIT ITER 3 (FINAL — cap 3 reached per .claude/rules/auditor-self-fix-policy.md)

**Date:** 2026-05-20
**Verifier:** auditor-backend (read-only re-audit)
**Source commit:** `9b676ee` — fix(vitalia/be/fidelizacion): audit iter 2 — F1 UTILITY vs MARKETING template + F2 pgcrypto migration 025 NPS comment
**Builder result doc:** `AUDIT-FIX-ITER-2-BE-result.md`

### Verdict (FINAL)

**APPROVED** — F1 + F2 both RESOLVED. No remaining BE-side blocking findings. Ready for merge (FE + agentic cross-scope cleanup pending separate auditor handoffs).

### Per-finding status

| Finding | Status | Verified path:line | Evidence |
|---|---|---|---|
| F1 UTILITY/MARKETING template gate | **RESOLVED** | `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/proactive_outbound_service.py:173-209` | Registry import L34-36 · template_def lookup L178 · unknown→blocked L179-193 · MARKETING gate L194-209 (only when `requires_marketing_opt_in=True`) · UTILITY pass-through implicit (falls through to step 3) |
| F2 pgcrypto nps_responses.comment | **RESOLVED** | `vitalia/backend/alembic/versions/025_vitalia_pgcrypto_nps_comment.py` (NEW) + service docstring + arch test allowlist | EXTENSION + trigger function + BEFORE INSERT/UPDATE trigger (all idempotent) · service docstring lines 125-131 truthful · `PHI_BYTEA_COLUMNS` allowlist row added (test_pgcrypto_phi_columns.py:27) · 2 new arch test methods enforce trigger presence |

### Re-run validators outputs

```
.venv/bin/pytest vitalia/backend/tests/architecture/ vitalia/backend/tests/modules/vitalia/fidelizacion/
  → 412 passed, 15 skipped, 6 warnings in 3.86s

.venv/bin/pytest vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py -v
  → 9/9 passed (2 new methods: test_nps_responses_comment_is_bytea, test_nps_responses_comment_has_pgcrypto_trigger)

.venv/bin/pytest vitalia/backend/tests/modules/vitalia/fidelizacion/application/test_proactive_outbound_service.py -v
  → 6/6 passed (NEW: test_utility_template_passes_without_marketing_opt_in [SC-03])

.venv/bin/ruff check  (5 modified files)
  → All checks passed!

.venv/bin/ruff format --check  (5 modified files)
  → 5 files already formatted
```

### F1 fix verification — detail

- ✅ Import `WHATSAPP_TEMPLATE_REGISTRY` from `src.modules.vitalia.connections.whatsapp.registry` (proactive_outbound_service.py L34-36)
- ✅ Step 2 consults `template_def.requires_marketing_opt_in` BEFORE applying marketing gate (L194)
- ✅ UTILITY templates (`recordatorio_proxima_sesion`, `recordatorio_control_doctor`, `nps_post_tratamiento`) verified in registry config as `requires_marketing_opt_in=False` (registry.py L88-92 `_TEMPLATE_CONFIGS`)
- ✅ MARKETING templates (`invitacion_mantenimiento`, `re_engagement_ausencia`) verified as `requires_marketing_opt_in=True` — gate remains intact (L194-209)
- ✅ Unknown `template_id` → returns `blocked_reason="template_unknown"` (L179-193) — defense-in-depth, prevents silent passthrough of malformed inputs
- ✅ Docstring updated to reflect SC-03 + cite 03-arch-be.md §7
- ✅ Tests updated: invalid slugs replaced with valid registry slugs · SC-02 assertion tightened to `blocked_reason == "marketing_opt_in_required"` · NEW SC-03 test `test_utility_template_passes_without_marketing_opt_in` covers the regression scenario
- ✅ Downstream consumer T-9 (`sales_agent/tools/send_proactive_reengagement.py`) consumes service via DI resolver (`_get_service()`) — inherits fix automatically without modification

### F2 fix verification — detail

- ✅ NEW migration `025_vitalia_pgcrypto_nps_comment.py` follows alembic chain (`down_revision="024_vitalia"` matches `024_inbox_tables.py::revision="024_vitalia"`)
- ✅ Migration idempotent per `.claude/rules/backend-migrations.md`:
  - `CREATE EXTENSION IF NOT EXISTS pgcrypto` (L45)
  - `CREATE OR REPLACE FUNCTION vitalia_encrypt_nps_comment` (L51-77)
  - `DROP TRIGGER IF EXISTS trg_encrypt_nps_comment` + recreate (L81-95)
  - All raw SQL via `op.execute()` (no `op.create_table` / `op.add_column`)
- ✅ Trigger uses `current_setting('app.encryption_key', true)` GUC pattern — KEK injected by connection pool (safe NULL fallback per hipaa-lite.md § Encryption at rest)
- ✅ `pgp_sym_encrypt(convert_from(NEW.comment, 'UTF8'), _kek)::BYTEA` — symmetric encryption pattern matches hipaa-lite.md spec
- ✅ Trigger fires `BEFORE INSERT OR UPDATE OF comment` with `WHEN (NEW.comment IS NOT NULL)` guard
- ✅ `downgrade()` drops trigger + function but preserves encrypted data + does NOT drop `pgcrypto` extension (shared by treatment_plans/re_engagement_events/channel_sync_state) — correct
- ✅ `nps_service.py:125-131` docstring corrected — no more false claim about trigger; accurately describes plaintext→bytes encoding + trigger-based encryption + KEK rotation policy
- ✅ Read path: NPS comment NOT exposed in API responses (line 159 `payload_redacted=b""` in audit log; service does not return comment in DTO — `get_nps_summary` returns only anonymized stats per L221 docstring)
- ✅ Arch test `PHI_BYTEA_COLUMNS` allowlist now includes `("nps_responses", "comment")` (test_pgcrypto_phi_columns.py L27)
- ✅ 2 new arch test methods enforce future regression protection:
  - `test_nps_responses_comment_is_bytea` (L167-191) — scans migrations for BYTEA type
  - `test_nps_responses_comment_has_pgcrypto_trigger` (L193-211) — scans for `trg_encrypt_nps_comment` or `pgp_sym_encrypt` reference

### HIPAA-lite compliance re-check

| Constraint | Pre-iter 3 | Post-iter 3 |
|---|---|---|
| Dual filter `tenant_id + clinic_id` | PASS | PASS (unchanged) |
| Audit log sync write | PASS | PASS (unchanged) |
| `@require_phi_access` RBAC | PASS | PASS (unchanged) |
| pgcrypto BYTEA PHI columns | **WARN F2** | **PASS** (trigger installed, allowlist closed) |
| No PHI in logs | PASS | PASS (unchanged) |
| No PHI in URL params | PASS | PASS (unchanged) |
| Soft delete only | PASS | PASS (unchanged) |
| Outbox pattern for domain events | PASS | PASS (unchanged) |
| UTILITY vs MARKETING template gate | **WARN F1** | **PASS** (registry-aware) |

### Allowlist movement (iter 3 final)

| Allowlist | Pre-story baseline | Post-iter 2 | Δ | Note |
|---|---|---|---|---|
| `KNOWN_LEGACY_CRONS` | 1 | 1 | 0 | no growth |
| `KNOWN_LEGACY_PHI_REPOS` | 2 | 2 | 0 | no growth |
| `PHI_BYTEA_COLUMNS` | 3 | 4 | +1 | **GAP CLOSED** — `("nps_responses", "comment")` added with justified pgcrypto trigger backing in migration 025 (commit `9b676ee`) |
| `test_response_model_required.py` | N/A | N/A | 0 | no change |

The `PHI_BYTEA_COLUMNS` growth is justified per `auditor-self-fix-policy.md` — represents net gain in arch coverage (column now monitored where it was previously a gap). The new entry has commit-backed pgcrypto trigger; this is *closing* a gap not relaxing the bar.

### Scope compliance audit (iter 3)

- ✅ NO scope creep — only files cited in F1/F2 findings touched
- ✅ NO engine edits (`core/luana-core-*/src/`) — promotion gate not triggered
- ✅ NO cross-brand pollution — only `vitalia/` paths modified
- ✅ Single commit `9b676ee` with conventional commits format + co-authored line
- ✅ Migration 025 in canonical `alembic/versions/` (not module-local) — follows brand alembic convention
- ✅ Native-First respected — all validators run via `.venv/bin/`, no `docker exec`

### Iter 3 ratchet (caps reached)

Per `.claude/rules/auditor-self-fix-policy.md`:
- `audit_iterations`: 3/3 (cap reached — iter 1 partial T-1+T-2 · iter 2 full review with F1+F2 · iter 3 verification of fix). No further iter permitted on this surface.
- `self_fix_iter`: 0/4 (auditor did NOT self-fix — spawn dev-team Caso B was the correct path for F1 branch logic + F2 migration scope)
- Both findings RESOLVED on iter 2 dev-team handoff; iter 3 verification = APPROVED. No ESCALATE triggered.

### Final action

→ **BE story status: APPROVED for merge** (pending cross-scope sub-auditors)
→ Cross-scope remaining (out of jurisdiction this auditor):
  - **auditor-frontend** primary verdict on T-11..T-14 (FE fidelización)
  - **auditor-agentic** primary verdict on T-9, T-10, T-15 (Adrián + Lucas tools + eval goldens)
→ Once both peer auditors APPROVED → auto-handoff to `/pm-vitalia` for `07-merge.md` composition + archive story to `vitalia/docs/archive/2026/stories/`

### Skills consulted (iter 3)

✓ backend-expert (runtime-quality-checklist applied to fix delta)
✓ backend-ddd (Inside-Out boundaries preserved — service consumes registry via shared import, no DDD violation)
✓ tenant-isolation (cardinal rule re-verified on modified path)
✓ vitalia/.claude/rules/hipaa-lite (overlay — encryption at rest requirement satisfied)
✓ .claude/rules/backend-migrations (idempotency verified on migration 025)
✓ .claude/rules/anti-default-flip-audit (N/A — no flag flip in fix)
✓ .claude/rules/anti-duplication (Cat 12 re-scan — no mirror introduced; WHATSAPP_TEMPLATE_REGISTRY import is brand-local consumption of T-8 SSoT)
✓ auditor-downstream-regression (engine_edit_detection: 0 engine edits · cross_brand_mirror_scan: 0 mirrors · T-9 downstream verified consumes modified service via DI)
✓ auditor-self-fix-policy (cap 3 reached → APPROVED no further iter)
