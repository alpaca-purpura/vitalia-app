# T-mk-be-3 result — Application services + Pydantic v2 DTOs

**Ticket:** T-mk-be-3
**Story:** vitalia-slice-1-marketing
**Brand:** vitalia
**Wave:** 2
**SHA:** 978d002
**Branch:** wip/vitalia
**Date:** 2026-05-20

---

## Summary

Implemented the full application layer for the vitalia marketing module on top of Wave 1 (entities/events/models/repos from T-mk-be-1 and T-mk-be-2).

---

## Files created

### DTOs
- `vitalia/backend/src/modules/vitalia/marketing/application/__init__.py`
- `vitalia/backend/src/modules/vitalia/marketing/application/dtos/__init__.py`
- `vitalia/backend/src/modules/vitalia/marketing/application/dtos/marketing_dtos.py`
  - 12 Pydantic v2 DTOs, all with `ConfigDict(from_attributes=True)`
  - Currency fields always `str | None = None` (never hardcoded "USD")
  - BowtieSummaryResponse, StageDetailResponse, ChannelDetailResponse
  - LucasRecommendationResponse, ApproveRecommendationRequest, RejectRecommendationRequest
  - AttributionMatrixResponse, ReferralsResponse, ReferrerEntryResponse
  - OAuthConnectRequest, OAuthConnectResponse, SyncResponse

### Application services
- `vitalia/backend/src/modules/vitalia/marketing/application/services/__init__.py`
- `vitalia/backend/src/modules/vitalia/marketing/application/services/lucas_recommendations_service.py`
  - Full state machine: OPEN → APPROVED (5min undo window) or OPEN → REJECTED; APPROVED → OPEN (undo)
  - HIPAA-lite: audit log SYNC write (`await audit_writer.write(...)`) BEFORE outbox publish
  - Outbox events: LucasRecommendationApproved, LucasRecommendationRejected, LucasRecommendationUndone
  - try/except ImportError fallback for dev environments without luana_core_events installed
  - Range validation: `action_payload_json.budget_amount_cents <= 100_000_00` (SC-MK-04)
  - Error messages in Spanish neutro LatAm (tuteo)
  - `get_by_id(id=..., tenant_id=..., scope_id=...)` — correct CompoundScopeRepositoryBase signature
- `vitalia/backend/src/modules/vitalia/marketing/application/services/marketing_service.py`
  - `_STAGE_CHANNEL_MAP` mapping BowtieStage → channel slug lists
  - `bowtie_summary()`, `stage_detail()`, `channel_detail()` reading channel metrics persisted by Lucas cron
- `vitalia/backend/src/modules/vitalia/marketing/application/services/attribution_service.py`
  - Thin proxy to `LucasAttributionService.compute_attribution()`
  - Maps `AttributionMatrixSnapshot` → `AttributionMatrixResponse` DTO
- `vitalia/backend/src/modules/vitalia/marketing/application/services/referrals_service.py`
  - `leaderboard()` proxies to `LucasReferralsService.compute_referrals()`
  - `generate_code()` creates `ReferralModel` with cryptographically random 8-char code (`secrets.choice()`)
  - Publishes `ReferralCodeGenerated` outbox event

### Tests (TDD — RED before GREEN)
- `vitalia/backend/tests/modules/vitalia/marketing/application/__init__.py`
- `vitalia/backend/tests/modules/vitalia/marketing/application/services/__init__.py`
- `vitalia/backend/tests/modules/vitalia/marketing/application/services/test_lucas_recommendations_service.py`
  - 8 tests covering SC-MK-01 and SC-MK-04 gherkin scenarios

---

## Files modified

- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/lucas_recommendation_repository.py`
  - Added `save()` method: `session.merge(model)` + `session.flush()` pattern
- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/channel_metric_repository.py`
  - Added `from sqlalchemy import select` import
  - Added `list_for_stage()` method: dual filter + channel slug list + date range, excludes `deleted_at IS NULL`
- `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/referral_repository.py`
  - Added `save()` method: same merge+flush pattern

---

## Gherkin coverage

### SC-MK-01 (Lucas approve happy — service flow)
| Test | Status |
|---|---|
| `test_approve_sets_status_audit_outbox` | PASS |
| `test_approve_undo_within_5min` | PASS |
| `test_approve_idempotency_dedup` | PASS |

### SC-MK-04 (adversarial — range validation)
| Test | Status |
|---|---|
| `test_approve_action_payload_out_of_range_rejected` | PASS |

### Additional coverage
| Test | Scenario |
|---|---|
| `test_reject_sets_status_audit_outbox` | reject state machine |
| `test_list_returns_open_recommendations` | list() filtering |
| `test_approve_already_approved_raises` | idempotency / invalid transition guard |
| `test_undo_after_window_expired_raises` | undo timing guard |

---

## Key design decisions

### CompoundScopeRepositoryBase.get_by_id signature
The base class signature is `get_by_id(*, id, tenant_id, scope_id)` — NOT `entity_id` or `clinic_id`. All service calls and test mocks use this exact signature.

### Audit log SYNC write ordering
Per HIPAA-lite rule: `await audit_writer.write(...)` is called BEFORE `adapter_bus.publish(event)`. This ensures the audit record exists even if the outbox publish fails (best-effort with try/except).

### Outbox fallback
```python
try:
    from luana_core_events.outbox import adapter_bus
except ImportError:
    # dev environment fallback
    class _FallbackBus:
        publish = AsyncMock()
    adapter_bus = _FallbackBus()
```

### Range validation constant
`_MAX_BUDGET_AMOUNT_CENTS = 100_000_00` (100k USD in cents). Checked in `_validate_action_payload()` before any state transition.

---

## Gate results

| Gate | Result |
|---|---|
| `ruff check` | 0 errors |
| `ruff format --check` | 0 files to reformat |
| `pytest tests/modules/vitalia/marketing/application/ -v` | 8/8 PASS |
| `pytest tests/modules/vitalia/marketing/ -v` | 92 passed, 1 skipped (Postgres-gated integration) |
| `pytest tests/architecture/ -v` | 270/270 PASS |

---

## Next ticket

T-mk-be-4 is being worked in parallel (Meta Ads + Google Ads OAuth adapters, `vitalia/backend/src/modules/vitalia/connections/` — NOT touched by this ticket).

T-mk-be-5 (FastAPI endpoints) is blocked by T-mk-be-3 + T-mk-be-4. After T-mk-be-4 lands, T-mk-be-5 can proceed.
