# T-BE-2 Result — FunnelService + ScoreService + DiagnoseService + DTOs + API routes

**Ticket:** T-BE-2 (vitalia-fase2-adrian-embudo)
**Branch:** wip/vitalia
**Status:** tests-passing (25 new tests GREEN, 320 arch tests GREEN)
**Date:** 2026-06-03

---

## Files Created / Modified (paths relative to repo root)

### NEW — Application DTOs
- `vitalia/backend/src/modules/vitalia/crm/application/dto/board_dto.py`
  (LeadCardDTO · BoardColumn · BoardKpis · BoardResponse)
- `vitalia/backend/src/modules/vitalia/crm/application/dto/transition_dto.py`
  (StageTransitionRequest · TransitionDTO · StageTransitionResponse · TimelineEntry · TimelineResponse)
- `vitalia/backend/src/modules/vitalia/crm/application/dto/lead_detail_dto.py`
  (ScoreFactor · AutonomyInfo · LeadDetailResponse)
- `vitalia/backend/src/modules/vitalia/crm/application/dto/frozen_dto.py`
  (FrozenLeadDTO · FrozenListResponse · DiagnoseResponse · ReactivateRequest)

### MODIFIED — Application DTOs
- `vitalia/backend/src/modules/vitalia/crm/application/dto/lead_dto.py`
  (EXTEND LeadResponse + LeadCreateRequest with 14 funnel fields;
  currency: str | None — NEVER hardcoded; version: int for optimistic lock)

### NEW — Application Services
- `vitalia/backend/src/modules/vitalia/crm/application/services/lead_score_service.py`
  (LeadScoreService · glass-box scoring formula · ScoreFactor · derive_temperature)
- `vitalia/backend/src/modules/vitalia/crm/application/services/diagnose_service.py`
  (DiagnoseService · deterministic frozen lead diagnosis · 7 rules)
- `vitalia/backend/src/modules/vitalia/crm/application/services/funnel_service.py`
  (FunnelService · transition_stage · get_board · get_lead_detail · get_timeline ·
  get_frozen_list · diagnose · reactivate · create_lead)

### MODIFIED — API Router
- `vitalia/backend/src/modules/vitalia/crm/api/router.py`
  (EXTEND: _build_funnel_service helper + 8 new endpoints:
  GET /board · PATCH /leads/{id}/stage · GET /leads/{id}/detail ·
  GET /leads/{id}/transitions · GET /frozen ·
  POST /leads/{id}/diagnose · POST /leads/{id}/reactivate ·
  POST /leads/{id}/reservado-side-effect (stub))

### MODIFIED — Telemetry
- `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py`
  (EXTEND _KNOWN_EVENT_NAMES: +4 embudo events: embudo_stage_changed,
  embudo_lead_created, embudo_lead_reactivated, embudo_lead_frozen)

### NEW — Tests
- `vitalia/backend/tests/modules/vitalia/crm/test_funnel_service.py` (9 tests)
- `vitalia/backend/tests/modules/vitalia/crm/test_funnel_api.py` (7 tests)
- `vitalia/backend/tests/modules/vitalia/crm/test_cross_tenant_lead_block.py` (2 tests)
- `vitalia/backend/tests/modules/vitalia/crm/test_auto_freeze_and_reactivate.py` (5 tests)
- `vitalia/backend/tests/modules/vitalia/crm/test_stage_transition_optimistic_lock.py` (2 tests)

---

## Validator Gates Output (literal)

```
# My new test files (25 tests):
cd vitalia/backend && pytest test_funnel_service.py test_funnel_api.py \
  test_cross_tenant_lead_block.py test_auto_freeze_and_reactivate.py \
  test_stage_transition_optimistic_lock.py -q
→ 25 passed in 0.73s

# Architecture tests (320 gates):
cd vitalia/backend && pytest tests/architecture/ --ignore=test_pgcrypto_phi_columns.py
→ 320 passed, 2 warnings in 3.60s

# Combined:
→ 345 passed, 2 warnings in 3.91s

# Ruff check (all new+modified files):
ruff check src/modules/vitalia/crm/... → All checks passed!

# Pre-existing failures (NOT caused by T-BE-2):
  FAIL test_pgcrypto_phi_columns.py (pre-exists, T-BE-1 era)
  FAIL test_router_conversations_list.py::test_list_conversations_403_marketing (pre-exists)
  FAIL test_router_conversation_detail.py::test_get_conversation_detail_403_marketing (pre-exists)
  FAIL test_phi_repo_encrypt_decrypt.py::test_get_by_id_maps_none_email_to_none (pre-exists)
  → All verified failing BEFORE T-BE-2 via git stash check
```

---

## Skills Consulted (must_load enforcement v4.1)

| Skill | Why Invoked | Decision Taken |
|---|---|---|
| `backend-expert` | Mandatory per spec — anti-patterns checklist, FastAPI Annotated deps, tenant isolation, SQLA 2.0 | Confirmed: no session.query(), response_model= on all 8 endpoints, tenant_id required params, soft-delete only pattern. Read `references/runtime-quality-checklist.md`. |
| `brand-expert` | Not applicable — no brand/offer/analytics surfaces touched | Skipped (correctly) |
| `offer-expert` | Not applicable — offer module not touched | Skipped (correctly) |
| `metrics-expert` | Not applicable — analytics module not touched | Skipped (correctly) |

**Rules loaded (mandatory):**
- `.claude/rules/tenant-isolation.md` — every funnel method requires `tenant_id`, raises ValueError if None, cross-tenant returns None→404 not 403 (no info leak)
- `.claude/rules/backend-ddd.py` — Inside-Out: domain exceptions from domain/, services in application/, repo calls in services, thin API layer
- `.claude/rules/currency-handling.md` — `currency: str | None = None` in all DTOs, NEVER hardcoded 'USD' or 'MXN'
- `.claude/rules/master-data.md` — UTC storage confirmed, DateTime(timezone=True) in all models (from T-BE-1)
- `.claude/rules/pii-sanitisation.md` — PII (name/email/phone) only in allowlisted DTO fields; LeadCardDTO explicitly notes "masked at FE via PiiMaskedSpan"
- `.claude/rules/tdd-mandatory.md` — tests written FIRST (RED), then implementation (GREEN). Confirmed: first pytest run showed ModuleNotFoundError, GREEN after implementation
- `vitalia/.claude/rules/hipaa-lite.md` — Lead non-PHI confirmed: no clinic_id dual filter, no PhiRepositoryBase; audit_log sync write applied where business events require it; PHI firewall in timeline (RN-2 comment + code)

**Context-brief § 11 gaps acknowledged:**
1. Path consistency (§ Open Questions #1): FE calls `/api/v1/vitalia/crm/...` but BE mounts at `/api/v1/crm`. The test app uses `/api/v1/crm` prefix consistent with existing endpoints. FE must verify with `curl` in dev-app before wiring (deferred to FE builder per CONTEXT-BRIEF recommendation).
2. ChannelBadge lift candidate: documented as comment in `channel-meta.ts` (T-FE-1, already done). No escalation needed now.
3. Override context wire (RN-4.1): `lead_stage_overridden` event emitted with correct shape for T-AG-1. Observability deferred until Inbox/sales_agent live (acknowledged).

---

## Key Decisions

### Event `lead_stage_overridden` shape (for T-AG-1)
```json
{
  "event_type": "lead_stage_overridden",
  "tenant_id": "<uuid>",
  "lead_id": "<uuid>",
  "from_stage": "<stage>",
  "to_stage": "<stage>",
  "reason": "<override context — commercial, NON-PHI>",
  "actor_user_id": "<uuid>",
  "version_after": <int>
}
```
Published via `event_bus.publish()` when `triggered_by=manual_override` AND `reason is not None`.
Falls back to stub bus (no-op + debug log) when `luana_core_events` not installed.

### Score Formula
```
base = STAGE_BASE[stage]  (10/25/50/70/100/0)
+ Σ signal_weights (pregunto_precio=25, presupuesto_ok=20, respondio_rapido=15, campana_pagada=10, urgencia=10, consulto_fecha=8, manda_referencias=5)
- recency_penalty (min(days_over_sla_green × 2, 20) — only for non-terminal stages)
→ clamp(0, 100)
temperature: hot=≥70, warm=≥40, cold=<40
```

### Freeze Logic (FunnelService.reactivate vs auto-freeze)
- Auto-freeze evaluated ON-READ in `get_board()` via `funnel_machine.should_freeze()` (deterministic, no extra DB query)
- Reactivate: clears `is_frozen`, `frozen_reason`, `frozen_at` via `lead_repo.reactivate()` + records activity
- Worker stub for scheduled freeze sweep: referenced in arch but NOT implemented in this ticket (ARQ cron = future story per 03-arch-be.md § 7)

### Endpoint Paths (confirmed consistent with existing router)
All new endpoints mount at `/api/v1/crm/...` (consistent with existing `GET /crm/leads`, `POST /crm/leads`, etc.):
- `GET /api/v1/crm/board`
- `PATCH /api/v1/crm/leads/{id}/stage`
- `GET /api/v1/crm/leads/{id}/detail`
- `GET /api/v1/crm/leads/{id}/transitions`
- `GET /api/v1/crm/frozen`
- `POST /api/v1/crm/leads/{id}/diagnose`
- `POST /api/v1/crm/leads/{id}/reactivate`
- `POST /api/v1/crm/leads/{id}/reservado-side-effect` (MSW stub)

### DDD Boundaries
- `FunnelService` does NOT import from `sales_agent/` or `copilot/` modules
- Cross-module integration = domain event `lead_stage_overridden` via outbox (T-AG-1 subscribes)
- No hard deletes anywhere (soft-delete only via `deleted_at`)
- PHI firewall: `get_timeline()` returns commercial activities only + redirects clinical data to Inbox (RN-2 comment in code)

### _build_funnel_service DI Pattern
`_build_funnel_service(session: AsyncSession) → FunnelService` is a plain function
(not a FastAPI Depends) so it can be easily patched in tests with `patch("...router._build_funnel_service", ...)`.
This avoids the "override fixture without Depends" anti-pattern from runtime-quality-checklist.md.

---

## Pre-existing Failures (NOT caused by this ticket)

Verified via `git stash` before T-BE-2 implementation:
1. `test_pgcrypto_phi_columns.py::test_no_phi_column_uses_text_or_varchar_unencrypted` — pre-T-BE-1 issue with `treatment_plans.notes` migration
2. `test_router_conversations_list.py::test_list_conversations_403_marketing` — async_resolve MagicMock issue in pre-existing test
3. `test_router_conversation_detail.py::test_get_conversation_detail_403_marketing` — same pre-existing issue
4. `test_phi_repo_encrypt_decrypt.py::TestLeadRepositoryNullSafe::test_get_by_id_maps_none_email_to_none` — T-BE-1 UUID parsing issue in `_row_to_lead` (T-BE-1 regression to fix in T-BE-3 or hotfix)
