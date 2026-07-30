# T-FE2bis — BE Board Contract Repair Result

**Story:** vitalia-fase2-adrian-embudo  
**Ticket:** T-FE2bis (live-verify integration repair)  
**Date:** 2026-06-03  
**Status:** done

## Problem

The FE `LeadCardDTO` (`vitalia/frontend/src/features/adrian/types/embudo.types.ts`) declared
fields that the BE `LeadCardDTO` Pydantic model (`board_dto.py`) did NOT send.
The `keysToCamel<BoardResponse>(raw)` cast at the FE edge is unchecked → absent fields arrive
as `undefined` at runtime. `version: number` (non-optional, used by the optimistic-concurrency
drag-transition PATCH mutation) was one of the absent fields → any drag-drop would break.

## Files Modified

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/crm/application/dto/board_dto.py` | Expanded `LeadCardDTO` Pydantic model with 10 new fields |
| `vitalia/backend/src/modules/vitalia/crm/application/services/funnel_service.py` | Updated board card mapper in `get_board()` to populate all new fields; changed `last_activities` dict to store `LeadActivity` objects |
| `vitalia/backend/tests/modules/vitalia/crm/test_funnel_service.py` | Added RED→GREEN test `test_board_card_exposes_full_fe_contract` |

## Per-Field Disposition Table

| FE field (camelCase) | BE field (snake_case) | Domain source | Action taken |
|---|---|---|---|
| `id` | `id` | `lead.id` | Already present — no change |
| `tenantId` | `tenant_id` | `lead.tenant_id` | **ADDED** — T-FE2bis |
| `name` | `name` | `lead.name` | Already present — no change |
| `stage` | `stage` | `lead.stage` | Already present — no change |
| `stageEnteredAt` | `stage_entered_at` | `lead.stage_entered_at.isoformat()` | Already present — no change |
| `score` | `score` | `lead.score` | Already present — no change |
| `temperature` | `temperature` | `lead.temperature` | Already present — no change |
| `operatedBy` | `operated_by` | `lead.operated_by` | Already present — no change |
| `channel` | `channel` | `lead.channel` | Already present — no change |
| `estimatedValue` | `estimated_value` | `lead.estimated_value` | Already present — no change |
| `currency` | `currency` | `lead.currency` | Already present — no change |
| `buyingSignals` | `buying_signals` | `list(lead.buying_signals)` | Already present — no change |
| `depositStatus` | `deposit_status` | `lead.deposit_status` | Already present — no change |
| `isFrozen` | `is_frozen` | `lead.is_frozen` | **ADDED** — T-FE2bis |
| `frozenReason` | `frozen_reason` | `lead.frozen_reason` | **ADDED** — T-FE2bis |
| `closureReason` | `closure_reason` | `lead.closure_reason` | **ADDED** — T-FE2bis |
| `reactivationCohortAt` | `reactivation_cohort_at` | `lead.reactivation_cohort_at.isoformat()` | **ADDED** — T-FE2bis |
| `serviceInterest` | `service_interest` | `lead.service_interest` | **ADDED** — T-FE2bis |
| `assignedDoctorId` | `assigned_doctor_id` | `lead.assigned_doctor_id` | **ADDED** — T-FE2bis |
| `isBlacklisted` | `is_blacklisted` | `lead.is_blacklisted` | **ADDED** — T-FE2bis |
| `version` | `version` | `lead.version` | **ADDED (CRITICAL)** — T-FE2bis |
| `lastActivityDescription` (optional) | `last_activity_description` | `activity.description_es` | **RENAMED** from `last_activity` — T-FE2bis |
| `lastActivityAt` (optional) | `last_activity_at` | `activity.occurred_at.isoformat()` | **ADDED (derived)** — T-FE2bis |

## Genuine Product Gaps (flagged — NOT fabricated)

None detected. All FE-required fields exist on the `Lead` domain entity or are
trivially derivable from `LeadActivity.occurred_at` (already fetched per-lead for
the micro-log). No fabricated values, no silent fallbacks.

The FE marks `lastActivityDescription` and `lastActivityAt` as optional (`?:`), so
when a lead has no activity records (e.g. a brand-new lead), both arrive as `null`
and the FE renders gracefully. This is correct.

## Board Endpoint JSON Shape (new)

Every `BoardColumn.leads[]` card now emits the following fields (snake_case from BE,
camelized by `keysToCamel` at FE):

```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "name": "Ana Torres",
  "stage": "calificando",
  "score": 72,
  "temperature": "warm",
  "channel": "wa",
  "estimated_value": "4500.00",
  "currency": "MXN",
  "operated_by": "agent",
  "buying_signals": ["pregunta_precio"],
  "stage_entered_at": "2026-05-10T00:00:00+00:00",
  "sla_state": "green",
  "deposit_status": "pending",
  "is_frozen": false,
  "frozen_reason": null,
  "closure_reason": null,
  "reactivation_cohort_at": null,
  "service_interest": "implante_dental",
  "assigned_doctor_id": "uuid-or-null",
  "is_blacklisted": false,
  "version": 3,
  "last_activity_description": "Adrián envió el catálogo de implantes.",
  "last_activity_at": "2026-06-01T12:00:00+00:00",
  "is_highlighted": false
}
```

## Gate Output

```
ruff check board_dto.py funnel_service.py   → 0 errors
ruff format --check ...                     → 2 files already formatted
test_funnel_service.py (10 tests)           → 10/10 PASS
test_funnel_api.py (7 tests)               → 7/7 PASS
test_cross_tenant_lead_block.py (2 tests)   → 2/2 PASS
test_auto_freeze_and_reactivate.py (5 tests)→ 5/5 PASS
test_stage_transition_optimistic_lock.py (2)→ 2/2 PASS
architecture/ (321 tests, excl. pre-existing pgcrypto TEXT→BYTEA violation)
                                           → 320/320 PASS

Pre-existing arch failure (NOT caused by this ticket):
  test_pgcrypto_phi_columns.py::test_no_phi_column_uses_text_or_varchar_unencrypted
  FAIL: treatment_plans.notes TEXT instead of BYTEA
  Confirmed pre-existing via git stash test. Scope: PHI migration story (different ticket).
```

## Notes on `sla_state`

The BE board card also emits `sla_state: str` (green | amber | red), which the FE
`LeadCardDTO` does NOT declare. This is fine — the FE ignores extra fields from the
camelized JSON. `sla_state` is used internally for `over_sla_count` column KPI
computation. Left as-is (no removal needed, no FE-side contract issue).

## Notes on Migration

No DB migration required. All fields added to the Pydantic board card DTO already
exist as columns on the `leads` table (added in T-BE-1 / T-infra-9). This fix is
purely at the serialization/mapping layer.

## Transition Endpoint Verification

`FunnelService.transition_stage()` already reads and passes `version` to
`lead_repo.update_stage(expected_version=version)` (optimistic lock). After
transition, the returned `LeadCardDTO` via `StageTransitionResponse` goes through
`_lead_to_response()` → `LeadResponse` (not the board card DTO). The FE
`StageTransitionResponse.lead` is typed as `LeadCardDTO` — but `LeadResponse`
already includes `version` (confirmed in `lead_dto.py`). No change needed there.

The drag mutation flow:
1. FE reads `card.version` from board card (now present — fixed)
2. FE sends `PATCH /crm/leads/{id}/stage` with `{version: N, ...}` 
3. BE `transition_stage()` passes `version` to repo optimistic lock
4. Returns `StageTransitionResponse.lead` which includes updated `version`
5. FE updates store with new `version` from response

This is now end-to-end correct.
