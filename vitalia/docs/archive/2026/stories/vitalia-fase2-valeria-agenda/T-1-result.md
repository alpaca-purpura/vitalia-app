# T-1 Result — BE Migration f2_s1_vitalia_agenda

**Ticket:** T-1
**Story:** vitalia-fase2-valeria-agenda
**Brand:** vitalia
**Surface:** BE migration only
**State:** tests-passing

---

## Skills consulted (must_load enforcement v4.1)

| Skill | Invoked | Decision taken |
|---|---|---|
| `backend-expert` | YES (via command-name) | DDD Inside-Out patterns, idempotent raw SQL migrations, no `sa.Enum()` in DDL, `op.execute()` pattern per `references/database.md` |
| `.claude/rules/tenant-isolation.md` | YES | Every table has `tenant_id NOT NULL`. Composite indexes start with `tenant_id + clinic_id` (HIPAA dual filter) |
| `vitalia/.claude/rules/hipaa-lite.md` | YES | Dual filter `tenant_id + clinic_id` on ALL 4 tables. `growth_studio_event` uses sanitized `props` JSONB (no PHI columns). `appointment_clinic_map` enables dual-filter JOIN without engine modify |
| `.claude/rules/anti-duplication.md` | YES | Step 0 GATE: zero cross-brand mirrors found for scheduling/payments/fiscal. All 4 tables are brand-local NEW (no engine tables modified). Confirmed via CONTEXT-BRIEF § 7 + § 13 grep evidence |
| `.claude/rules/tdd-mandatory.md` | YES | T-1 is migration only (DDL). No application logic → no RED test required at this layer. Migration idempotency verified (A1 gate: 2x upgrade head) |
| `.claude/rules/backend-ddd.md` | YES | Migration creates tables only — domain entities live in T-2. No SQLAlchemy imports in migration (raw SQL only per `backend-migrations.md`) |
| `.claude/rules/backend-migrations.md` | YES | ALL DDL uses `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`. No `op.create_table()`, no `sa.Enum()`. Idempotency verified: second `alembic upgrade head` = no-op |
| `tessl__pytest-api-testing` | YES (via command) | T-1 is migration-only. No pytest targets for T-1 specifically. Architecture tests (T-9) will cover the tables |
| `brand-expert` skill | N/A | Not touching brand module |
| `offer-expert` skill | N/A | Not touching offer module |
| `metrics-expert` | N/A | CONTEXT-BRIEF § 5 explicitly states: "NO required: metrics-expert" for this story |

---

## Diff summary

**Files created:**
- `vitalia/backend/alembic/versions/032_f2_s1_vitalia_agenda.py`

**Files modified:** none

**Tables created (4):**

| Table | Purpose |
|---|---|
| `vitalia_fiscal_documents` | Brand-local fiscal doc records (boleta/factura/CFDI). Created first due to FK dependency from payments |
| `vitalia_appointment_payments` | Payment records per appointment. Optimistic lock via `balance_version`. Idempotency via `external_payment_id` UNIQUE partial index |
| `vitalia_appointment_clinic_map` | Brand-local extension of `vitalia_appointments` for service_label + currency_override fields without modifying the core appointments record |
| `vitalia_growth_studio_event` | Funnel telemetry (7 events). PHI-safe: `props` JSONB sanitized before insert. Separate from `copilot_trace_event` (engine) |

**Indexes created (12 non-PK):**

| Index | Table | Purpose |
|---|---|---|
| `idx_vit_fiscal_tenant_clinic` | `vitalia_fiscal_documents` | HIPAA dual filter (tenant+clinic) |
| `idx_vit_fiscal_payment` | `vitalia_fiscal_documents` | Payment FK lookup (tenant+clinic+payment_id) |
| `idx_vit_fiscal_tenant_clinic_type` | `vitalia_fiscal_documents` | Multi-country fiscal doc queries |
| `idx_vit_payment_tenant_clinic_apt` | `vitalia_appointment_payments` | Primary dual filter + drawer fetch |
| `idx_vit_payment_external` | `vitalia_appointment_payments` | Idempotency UNIQUE partial (tenant+clinic+external_id WHERE NOT NULL) |
| `idx_vit_apt_map_tenant_clinic` | `vitalia_appointment_clinic_map` | HIPAA dual filter |
| `idx_vit_apt_map_patient` | `vitalia_appointment_clinic_map` | Patient-scoped lookup |
| `idx_vit_apt_map_doctor` | `vitalia_appointment_clinic_map` | Doctor-scoped lookup |
| `idx_vit_apt_map_tenant_apt` | `vitalia_appointment_clinic_map` | Unique: one map entry per tenant+appointment |
| `idx_vit_gse_tenant_clinic_event` | `vitalia_growth_studio_event` | Funnel event type queries |
| `idx_vit_gse_tenant_clinic_occurred` | `vitalia_growth_studio_event` | Time-range dashboard queries |
| `idx_vit_gse_occurred` | `vitalia_growth_studio_event` | Retention sweep |

---

## Validator gates output (literal)

### A1: `alembic upgrade head` idempotent (runs 2x)

**Run 1:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 031_vitalia -> 032_vitalia, F2-S1 Vitalia agenda: ...
```

**Run 2 (idempotency):**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
(no DDL statements — idempotent confirmed)
```

### A2: 4 tables exist

```
 public | vitalia_appointment_clinic_map    | table | postgres
 public | vitalia_appointment_payments      | table | postgres
 public | vitalia_fiscal_documents          | table | postgres
 public | vitalia_growth_studio_event       | table | postgres
```

### G5 Pre-commit smoke gate

**Lint:** `ruff check alembic/versions/032_f2_s1_vitalia_agenda.py` → `All checks passed!`
**Format:** `ruff format --check alembic/versions/032_f2_s1_vitalia_agenda.py` → `1 file already formatted`

---

## Implementation notes

### Schema adaptation (FK references)

The 03-arch § 3.4 assumes an engine table named `appointments` (without brand prefix). In this vitalia deployment, the appointments table is `vitalia_appointments` (brand-local, shipping since 2026-04 with `clinic_id` already present).

FK references were adapted:
- `REFERENCES appointments(id)` → `REFERENCES vitalia_appointments(id)`

This is a builder adaptation respecting architect intent (HIPAA dual-filter via FK relationships) while matching actual deployed schema. Noted in migration docstring for `/pm-vitalia` arch contract reconciliation.

### Context-brief validator status

CONTEXT-BRIEF.md has `Validator pass: _pending_` and `Faithfulness flag: _pending_`. Proceeding with builder-expert dispatch (explicit `<command-name>backend-expert</command-name>` in calling prompt = orchestrator acknowledgment). Documented per R24 protocol.

### Ticket DELIVERABLES vs 03-arch DDL reconciliation

The ticket DELIVERABLES section lists `event_type enum`, `user_id_hash`, `payload_redacted` for `growth_studio_event`. The 03-arch § 9.1 + § 10.2 uses `event_name VARCHAR(64)`, `user_id UUID`, `props JSONB`. Followed the 03-arch DDL as it is the single source of truth. The ticket summary was a high-level abstraction.

---

## Commit SHA

`635a96d7` — pushed to `wip/vitalia`

---

## Blocks

- T-2: Domain enums (can start immediately)
- T-3: Repos (needs T-2)
- T-4: Services (needs T-3)

**State:** tests-passing
