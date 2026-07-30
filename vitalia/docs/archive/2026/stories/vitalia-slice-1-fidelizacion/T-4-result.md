<!-- voseo-allowed: VOs = abbreviation for Value Objects (not voseo pronoun) -->
# T-4 Result — BE fidelización domain + infrastructure

> Brand: vitalia
> Story: vitalia-slice-1-fidelizacion
> Ticket: T-4
> State: tests-passing
> Completed: 2026-05-20
> Commit: (see git log)

## Summary

Implemented complete fidelización domain + infrastructure layer for vitalia:
- 4 StrEnum value objects (domain pure Python)
- 3 Pydantic v2 domain entities with PHI BYTEA fields
- 4 domain events (@dataclass, DomainEvent subclasses)
- 3 SQLAlchemy 2.0 ORM models (matching migrations 020-023)
- 3 CompoundScopeRepositoryBase repositories (HIPAA-lite dual filter)
- 6 test files (55 domain unit + 12 infra contract = 67 unit tests GREEN)

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Mandatory gate per role — anti-patterns checklist for FastAPI/SQLA/migrations | Confirmed: Pydantic v2 ConfigDict(from_attributes=True), no inner class Config, SQLA 2.0 Mapped[] only, structlog not print |
| `tessl__fastapi` | Domain entities use Pydantic v2 patterns | Confirmed: field_validator @classmethod pattern for score range validation, model_config = ConfigDict(from_attributes=True) |
| `tessl__pytest-api-testing` | Integration test patterns, fixture scoping | Confirmed: @pytest.mark.integration marker, db_session fixture from conftest, uuid4() per-test isolation |

## Test Results

### Domain unit tests (no DB)

```
55 passed, 0 failed
```

Covers:
- `TestReEngagementPattern` — 5 StrEnum values, from_string, is_str, invalid raises
- `TestReEngagementOutcome` — 7 StrEnum values
- `TestUrgencyLevel` — 5 StrEnum values, ordering intent
- `TestNPSBand` — 3 values, from_score boundaries (0-6=DETRACTOR, 7-8=PASSIVE, 9-10=PROMOTER), invalid raises
- `TestTreatmentPlanStatus` — 4 values
- `TestTreatmentPlan` — construction, from_attributes, required fields, notes bytes/None, soft delete
- `TestReEngagementEvent` — construction, from_attributes, required fields, outcome enum, soft delete
- `TestNPSResponse` — construction, from_attributes, required fields, comment bytes/None, score range, band
- `TestDomainEventConstants` — prefix "vitalia.fidelizacion.", all distinct
- `TestReEngagementTriggered` — .create() API, event_name, DomainEvent subclass, optional fields
- `TestNPSScoreCollected` — .create() API, optional appointment_id
- `TestPatientOptedOut` — .create() API, optional reason + triggered_by_user_id
- `TestPatientPausedReEngagement` — .create() API, optional fields

### Infrastructure contract tests (no DB)

```
12 passed, 0 failed
```

All 3 repos pass:
- `test_inherits_compound_scope_repository` — issubclass check
- `test_scope_field_is_clinic_id` — inspect.getsource() verifies "clinic_id" presence
- `test_model_class_defined` — MODEL class attribute is correct model class
- `test_has_required_methods` — get_by_id, save, domain-specific methods

### Architecture fitness gates

```
265 passed, 0 failed (full vitalia arch suite)
```

Key gates for T-4:
- `test_compound_scope_repository_used.py` — all 4 tests PASS (fidelizacion repos use CompoundScopeRepositoryBase)
- `test_phi_dual_filter.py` — all 4 tests PASS (dual filter tenant_id + clinic_id enforced)

### Lint + Format

```
ruff check: 0 errors (after --fix for import ordering I001)
ruff format: 0 files to reformat
```

## Files Created

### Domain layer (pure Python, no ORM)

**Value Objects** (`src/modules/vitalia/fidelizacion/domain/value_objects/`):
- `re_engagement_pattern.py` — ReEngagementPattern StrEnum (5 values: multi_session, follow_up, maintenance, absence, nps)
- `re_engagement_outcome.py` — ReEngagementOutcome StrEnum (7 values)
- `urgency_level.py` — UrgencyLevel StrEnum (5 values)
- `nps_band.py` — NPSBand StrEnum (3 values) + `from_score(int) -> NPSBand` classmethod

**Entities** (`src/modules/vitalia/fidelizacion/domain/entities/`):
- `treatment_plan.py` — TreatmentPlanStatus StrEnum (4 values) + TreatmentPlan Pydantic v2 entity (notes: bytes | None for pgcrypto PHI)
- `re_engagement_event.py` — ReEngagementEvent Pydantic v2 entity (payload_phi: bytes | None for pgcrypto PHI)
- `nps_response.py` — NPSResponse Pydantic v2 entity (comment: bytes | None for pgcrypto PHI, score field_validator 0-10)

**Domain Events** (`src/modules/vitalia/fidelizacion/domain/events/`):
- `events.py` — 4 event name constants + 4 @dataclass DomainEvent subclasses with `.create()` classmethods:
  - `ReEngagementTriggered` (FIDELIZACION_RE_ENGAGEMENT_TRIGGERED)
  - `NPSScoreCollected` (FIDELIZACION_NPS_SCORE_COLLECTED)
  - `PatientOptedOut` (FIDELIZACION_PATIENT_OPTED_OUT)
  - `PatientPausedReEngagement` (FIDELIZACION_PATIENT_PAUSED_RE_ENGAGEMENT)

### Infrastructure layer (SQLAlchemy 2.0 + repos)

**Models** (`src/modules/vitalia/fidelizacion/infrastructure/models/`):
- `treatment_plan_model.py` — TreatmentPlanModel (vitalia_treatment_plans, migration 020)
- `re_engagement_event_model.py` — ReEngagementEventModel (vitalia_re_engagement_events, migration 021, partitioned RANGE(trigger_at), composite PK (id, trigger_at))
- `nps_response_model.py` — NPSResponseModel (vitalia_nps_responses, migration 022)

**Repositories** (`src/modules/vitalia/fidelizacion/infrastructure/repositories/`):
- `treatment_plan_repository.py` — TreatmentPlanRepository extends CompoundScopeRepositoryBase, scope_field="clinic_id", methods: save, list_for_patient
- `re_engagement_event_repository.py` — ReEngagementEventRepository extends CompoundScopeRepositoryBase, scope_field="clinic_id", methods: save, list_by_pattern, check_throttle
- `nps_response_repository.py` — NPSResponseRepository extends CompoundScopeRepositoryBase, scope_field="clinic_id", methods: save, list_for_patient, list_detractors_untagged

### Tests

**Domain** (`tests/modules/vitalia/fidelizacion/domain/`):
- `test_value_objects.py` — 20 tests for 4 StrEnum VOs
- `test_entities.py` — 18 tests for 3 entities + TreatmentPlanStatus
- `test_events.py` — 17 tests for 4 domain events

**Infrastructure** (`tests/modules/vitalia/fidelizacion/infrastructure/`):
- `test_treatment_plan_repository.py` — 4 contract + 4 integration tests (marked @pytest.mark.integration)
- `test_re_engagement_event_repository.py` — 4 contract + 9 integration tests (Gherkin SC-02 + SC-04 covered)
- `test_nps_response_repository.py` — 4 contract + 4 integration tests

## Architecture Compliance

| Constraint | Status |
|---|---|
| CompoundScopeRepositoryBase (engine) | PASS — all 3 repos inherit from engine class |
| HIPAA-lite dual filter (tenant_id + clinic_id) | PASS — every query filters both; arch gate PASS |
| pgcrypto BYTEA PHI fields | PASS — notes/payload_phi/comment are `Mapped[bytes | None]` with BYTEA type |
| Soft delete only (deleted_at) | PASS — no hard DELETE, all models have deleted_at |
| SQLAlchemy 2.0 Mapped[] syntax | PASS — no Column() or session.query() usage |
| Pydantic v2 ConfigDict | PASS — no inner class Config |
| structlog only | PASS — no print() or stdlib logging |
| scope_field="clinic_id" | PASS — constructor arg + inspect.getsource arch test |
| Domain pure (no ORM imports) | PASS — entities only import from pydantic + stdlib + own VOs |
| DomainEvent subclasses from engine | PASS — from luana_core_platform.domain.events import DomainEvent |

## Pending (downstream tickets)

- T-5: Application services (use FidelizacionService, event dispatch)
- T-7: API routes + DTOs
- T-8: Cron fidelización (independent parallel, may already be started)
- Integration tests (require live Postgres, marked @pytest.mark.integration)

## Notes for T-5 (application layer)

1. All 3 repos constructor: `TreatmentPlanRepository(session=session, scope_field="clinic_id")`
2. `check_throttle` returns `bool` — if True, skip sending (anti-spam)
3. Domain events use `.create()` classmethod API — not `__init__` directly
4. NPSBand.from_score() raises ValueError for score outside 0-10
5. `ReEngagementEventModel` has composite PK (id, trigger_at) for RANGE partitioning
