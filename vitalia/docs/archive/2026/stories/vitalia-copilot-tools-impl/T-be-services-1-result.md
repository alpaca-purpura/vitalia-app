---
ticket: T-be-services-1
story: vitalia-copilot-tools-impl
brand: vitalia
builder: claude-sonnet-4-6
state: tests-passing
completed_at: 2026-05-18
---

# T-be-services-1 — Result

## Verdict

`tests-passing` — 1317 passed, 58 skipped, 0 failed. Awaiting gate-runner + auditor-backend independent verdict.

## Deliverables

### Domain layer
- `WizardSlot` frozen dataclass value object (immutable, `value: str | dict | None`)
- `OnboardingDraft` mutable entity with `update_slot()` + `all_confirmed_slots()` methods
- `WizardState` StrEnum (COLLECTING/CONFIRMING/SIMULATING/COMPLETING/DONE/ABANDONED)
- `PersonalityServicePort` ABC + `PersonalitySimulationResult` dataclass

### Application services
- `OnboardingDraftService` — create/get/update_slot with tenant isolation
- `ExtractTenantContextService` — website scraper + document extractor adapter orchestration, slot merging
- `SimulatePersonalityService` — cache 600s TTL + rate limit 5/min/tenant sliding window + `ThrottleExceededError`
- `CompleteOnboardingService` — personality compile → brand commit → mark_onboarded → sync audit_log → `TenantOnboardedEvent`

### API layer
7 FastAPI routes at `/api/v1/vitalia/onboarding`:
- `POST /drafts` → `StartDraftResponse`
- `GET /drafts/{draft_id}` → `DraftResponse` (404 on not found)
- `POST /drafts/{draft_id}/extract` → `ExtractResponse`
- `POST /drafts/{draft_id}/slots/{slot_id}/confirm` → `ConfirmSlotResponse`
- `POST /drafts/{draft_id}/simulate` → `SimulateResponse` (429 on throttle)
- `POST /drafts/{draft_id}/complete` → `CompleteResponse` (404 on not found)
- `GET /drafts/{draft_id}/stream` → `StreamingResponse` text/event-stream (no response_model)

### Test coverage
48 new tests across 6 test files. All GREEN.

## Quality gates passed
- `ruff check`: 0 errors
- `ruff format --check`: 0 files to reformat
- Full suite: 1317 passed, 58 skipped, 0 failed

## Limitations (Slice 1)
- Dependency factories inject stub implementations (in-memory). Real Redis cache/rate-limiter + PostgreSQL async repos wired in T-ag-tools-1 + T-infra-3.
- Audit log write calls injected mock in integration tests (real `AuditLogRepository` is T-infra-3 scope).

## Next ticket
T-be-services-2 (Adrián sales_agent backend) or T-ag-tools-1 (Valeria 4 tools + observability) — both ready after this push.
