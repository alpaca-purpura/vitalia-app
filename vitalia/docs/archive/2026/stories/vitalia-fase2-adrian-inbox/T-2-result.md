# T-2 Result — NudgeService + POST /nudge (RN-13)

**Story:** vitalia-fase2-adrian-inbox
**Ticket:** T-2
**Brand:** vitalia
**Commit:** `40646037`
**Branch:** `worktree-agent-aa3e80a7ed98b7b8c`
**Date:** 2026-06-03

---

## Deliverables

| File | Status | Notes |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/inbox/application/dto/nudge_dto.py` | NEW | NudgeRequest + NudgeResponse (Pydantic v2, `from_attributes=True`, no PHI) |
| `vitalia/backend/src/modules/vitalia/inbox/application/services/nudge_service.py` | NEW | NudgeService + ConvNotFoundError + NudgeNotApplicableError + NudgeResult |
| `vitalia/backend/src/modules/vitalia/inbox/api/router.py` | MODIFIED | POST /conversations/{conv_id}/nudge + _get_nudge_service DI + header cap updated |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/activity_event_repository.py` | MODIFIED | Added `create()` and `find_nudge_today()` methods (dual-filter, append-only) |
| `vitalia/backend/tests/modules/vitalia/inbox/application/test_nudge_service.py` | NEW | 9 service tests (TDD RED-first confirmed) |
| `vitalia/backend/tests/modules/vitalia/inbox/api/test_router_nudge.py` | NEW | 9 API tests (PHI gate, cross-tenant, idempotency, response_model) |

---

## Validator Output

### fn-be-nudge (18/18 PASS)
```
tests/modules/vitalia/inbox/application/test_nudge_service.py .........  [50%]
tests/modules/vitalia/inbox/api/test_router_nudge.py .........           [100%]
18 passed in 0.42s
```

### fn-be-inbox-suite — regression_guard (89/89 PASS)
```
89 passed in 1.13s
```

### av-be-arch-fitness (335/335 PASS)
```
335 passed, 2 warnings in 3.53s
```

### nf-be-ruff + nf-be-format
```
All checks passed! (ruff check)
50 files already formatted (ruff format --check)
```

### av-no-sales-agent-import
```
PASS — no direct sales_agent import in inbox/
```

### av-no-core-edit
```
PASS — core/ untouched
```

---

## Skills Consulted

| Skill | Why Invoked | Decision |
|---|---|---|
| `backend-expert` | Mandatory — anti-patterns FastAPI/SQLA/tests | Applied `response_model=`, `ConfigDict(from_attributes=True)`, `AsyncSession`, dual filter tenant+clinic on every repo call, audit sync write pre-response, structlog |
| `sales-agent-expert` (§ anti-duplication only) | Consumed `send_proactive_reengagement` brand tool via DI resolver — NEVER direct import | Service resolver pattern: `_proactive_resolver` async callable injected in DI factory; NudgeService is fully decoupled from sales_agent/ module. `av-no-sales-agent-import` PASS |
| `tenant-isolation.md` | Every query must filter tenant_id + clinic_id (hipaa-lite dual filter) | `conv_repo.get_by_id(id=..., tenant_id=..., scope_id=...)` — dual filter enforced. Activity repo `create()` and `find_nudge_today()` both dual-filtered |
| `backend-ddd.md` | Inside-Out DDD layers | domain exceptions → service → DTO → API thin router. No business logic in router.py |
| `tdd-mandatory.md` | RED tests first | Wrote `test_nudge_service.py` + `test_router_nudge.py` RED (ModuleNotFoundError) → then implemented → GREEN 18/18 |
| `hipaa-lite.md` | HIPAA-lite dual filter + audit sync | `clinic_id` dual filter on all repo calls; audit log `action="inbox.nudge.sent"` written sync in `NudgeService.nudge()` before return; activity event `description_es` contains no raw PHI |

---

## Design Notes

### Idempotency
Natural key dedup: `ActivityEventRepository.find_nudge_today(tenant_id, clinic_id, conversation_id)` returns existing `nudge_sent` event if any in current UTC day. On hit → `NudgeResult(nudge_sent=False)` → router returns HTTP 200 (not 201). On miss → send + write activity + audit → HTTP 201.

### Service Resolver Pattern (anti-coupling)
`_get_nudge_service` DI factory in `router.py` creates an inner `_proactive_resolver` async callable that wraps `ProactiveOutboundService.send_proactive()`. The `NudgeService` constructor only sees the resolver callable interface — zero dependency on `sales_agent/` module tree. Architecture validator `av-no-sales-agent-import` confirms.

### Conv Validation
NudgeService checks two preconditions before sending:
1. `conv.status == 'open'` — must be live (not closed/resolved)
2. `conv.last_message_at` > `_STALE_THRESHOLD_HOURS` (24h) ago — must be stalled

Both raise `NudgeNotApplicableError` → router maps to 422.

### Activity Event Repository Extension
Added `create()` and `find_nudge_today()` to `ActivityEventRepository`. These respect the append-only invariant (no update/delete). Both apply dual filter (tenant_id + clinic_id via `CompoundScopeRepositoryBase._scope_attr()`).

---

## Known Gaps / Notes

1. **This worktree does not include T-1 changes** — this worktree was forked from `main` before T-1 was committed to `wip/vitalia`. The router in this worktree still has `_NoOpComplianceService` (Slice 1). The T-2 deliverables are complete and coherent on their own. When T-1 and T-2 are squash-merged into `wip/vitalia`, the compliance wiring from T-1 applies on top.

2. **`find_nudge_today` requires DB** — idempotency dedup uses a DB query. In test context, `find_nudge_today` is mocked. Integration test would exercise the real dedup path (PostgreSQL required, gate 9 `integration-marker`).

3. **`nudge_reengagement` template** — the `_proactive_resolver` in router.py uses template_id `"nudge_reengagement"` which is not in the 5 Meta-approved templates registered in `_templates.py`. For real outbound to work, this template needs to be added to the registry (out of T-2 scope — deferred to `ProactiveOutboundService` extension ticket). The NudgeService itself is correct; the resolver's `send_proactive` call will raise `TemplateNotFoundError` at runtime unless the template is registered. This is documented here for the next ticket.

---

## Files Changed (6)

```
M  vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/activity_event_repository.py
M  vitalia/backend/src/modules/vitalia/inbox/api/router.py
A  vitalia/backend/src/modules/vitalia/inbox/application/dto/nudge_dto.py
A  vitalia/backend/src/modules/vitalia/inbox/application/services/nudge_service.py
A  vitalia/backend/tests/modules/vitalia/inbox/api/test_router_nudge.py
A  vitalia/backend/tests/modules/vitalia/inbox/application/test_nudge_service.py
```

**Net delta:** +1503 lines (1499 new, 4 modified in existing files).
**Tests:** 18 new (9 service + 9 API). Native ticket tests: 18/18 PASS.
