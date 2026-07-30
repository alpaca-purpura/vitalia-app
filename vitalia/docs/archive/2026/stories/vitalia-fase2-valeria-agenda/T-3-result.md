# T-3 Result — BE Scheduling Infrastructure

**Ticket:** T-3 — SA 2.0 models + repositories (HIPAA-lite dual filter, optimistic lock, idempotency)
**Story:** vitalia-fase2-valeria-agenda
**Status:** tests-passing (36/36 unit + 270/270 arch fitness)
**Branch:** wip/vitalia

---

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `backend-expert` | Pre-write quality checklist (anti-patterns FastAPI/SQLA/tests/migrations) | SA 2.0 `select(Model).where()` only; async session; HIPAA dual filter on ALL queries; soft deletes only; ruff 0 errors |
| `tessl__fastapi` | Async patterns, response_model, Pydantic v2 | Annotated DI, async def everywhere, no sync Session |
| `tessl__pytest-api-testing` | httpx AsyncClient, fixture scoping, factory fixtures, DB isolation | AsyncMock session pattern for unit tests; postgresql dialect for compile() |

---

## Deliverables Produced

### Production files (9)

| File | Purpose |
|---|---|
| `vitalia/backend/src/modules/vitalia/scheduling/persistence/models/appointment_payment_model.py` | SA 2.0 model — vitalia_appointment_payments, optimistic lock via balance_version |
| `vitalia/backend/src/modules/vitalia/scheduling/persistence/models/appointment_clinic_map_model.py` | SA 2.0 model — vitalia_appointment_clinic_map, service_label + origin per appointment |
| `vitalia/backend/src/modules/vitalia/fiscal/infrastructure/models/fiscal_document_model.py` | SA 2.0 model — vitalia_fiscal_documents, saga compensation status lifecycle |
| `vitalia/backend/src/modules/vitalia/scheduling/domain/exceptions.py` | Domain exceptions: BalanceAlreadyChargedError (optimistic lock), AppointmentNotFoundError, InvalidPresetFilterError |
| `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/agenda_grid_repository.py` | Protocol interface for AgendaGridRepository |
| `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/agenda_grid_repository_impl.py` | SQLA 2.0 async impl — JOIN vitalia_appointments + clinic_map + payments, PHI masking, preset filters; inherits CompoundScopeRepositoryBase |
| `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/appointment_detail_repository.py` | Detail view repo — JOIN + payment history + PHI masking; inherits CompoundScopeRepositoryBase |
| `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/appointment_payment_repository.py` | CRUD + optimistic lock (lock_for_charge) + idempotency key lookup (find_by_idempotency_key) |
| `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/appointment_aggregates_repository.py` | Monthly slot counts for virtualized calendar (count_per_day, count_by_status) |
| `vitalia/backend/src/modules/vitalia/fiscal/infrastructure/repositories/fiscal_document_repository.py` | CRUD + update_status (saga compensation) + list_failed_for_retry |

### Test files (4)

| File | Coverage |
|---|---|
| `vitalia/backend/tests/modules/vitalia/scheduling/test_agenda_grid_repository.py` | Dual filter, cross-clinic isolation, preset filters, JOIN contract, PHI projection |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_appointment_payment_repository.py` | Optimistic lock (success + stale version raises), idempotency key lookup, dual filter |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_appointment_aggregates_repository.py` | count_per_day dual filter, aggregates query |
| `vitalia/backend/tests/modules/vitalia/fiscal/test_fiscal_document_repository.py` | create(), get_by_id dual filter, get_by_payment_id dual filter, update_status |

---

## Acceptance Criteria Status

| AC | Description | Status |
|---|---|---|
| A1 | HIPAA dual filter: EVERY query filters tenant_id + clinic_id | PASS — all repos enforce dual filter in WHERE clauses |
| A2 | Unit tests pass (no Postgres needed) | PASS — 36/36 unit tests GREEN |
| A3 | Cross-clinic queries return empty (session mock returns [] for wrong clinic) | PASS — test_agenda_grid_cross_clinic_returns_empty passes |
| A4 | Optimistic lock: rowcount=0 raises BalanceAlreadyChargedError | PASS — test_lock_for_charge_optimistic_stale_version_raises passes |
| A5 | Idempotency key: find_by_idempotency_key returns prior payment | PASS — test_find_by_idempotency_key_returns_prior_payment passes |

---

## Architecture Fitness

- 270/270 architecture tests GREEN
- test_compound_scope_repository_used: PASS (both new PHI repos use CompoundScopeRepositoryBase from engine, not brand-local PhiRepositoryBase)
- test_phi_dual_filter: PASS
- test_no_legacy_paths: PASS
- test_migrations_idempotent: PASS

---

## Key Technical Decisions

1. **vitalia_appointments table**: No Python SA model class exists (table created by migration 002 without a Python model). All queries against it use `text()` + Core select(). AgendaGridRepositoryImpl and AppointmentDetailRepository JOIN via `select_from(text("vitalia_appointments va")).outerjoin(OrmModel, text(...))`.

2. **PHI masking**: `patient_name_masked` and `dni_masked` columns are pre-masked in vitalia_appointments. Repository SELECTs these pre-masked columns. Raw `patient.name` is NEVER returned.

3. **CompoundScopeRepositoryBase migration**: Both `AgendaGridRepositoryImpl` and `AppointmentDetailRepository` inherit `CompoundScopeRepositoryBase` from engine (not brand-local `PhiRepositoryBase`). `MODEL = None` since these repos issue complex JOIN queries; all query methods are fully overridden.

4. **Optimistic lock**: `lock_for_charge()` uses `UPDATE WHERE balance_version == expected_version` + `.execution_options(synchronize_session=False)`. Rowcount 0 → raises `BalanceAlreadyChargedError`. Pattern verbatim from 03-arch A7.

5. **SQL compile in tests**: ORM queries (using model column comparisons) require `postgresql.dialect()` in `stmt.compile()` to render UUID literals. Queries using `text(f"col = '{uuid}'"`) embed UUID directly via f-string and can use `stmt.whereclause` string inspection.

---

## Validator Output (native)

```
ruff check: All checks passed (0 errors)
ruff format --check: 23 files already formatted (0 files to reformat)
pytest T-3 unit tests: 36 passed in 0.22s
pytest tests/architecture/: 270 passed in 2.79s
```

---

## Blocks Unblocked

- T-4 (AppointmentService + charge saga) — can now import AppointmentPaymentRepository, FiscalDocumentRepository
- T-6 (API routes + DTOs) — can now import all repository classes from persistence + infrastructure layers
