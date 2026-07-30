# HB-42 — FE↔BE Contract Parity Arch Test

**Story:** vitalia-fase2-adrian-embudo
**Ticket:** HB-42 (harness backlog)
**Date:** 2026-06-04
**Status:** DONE — all gates GREEN

---

## What was built

`vitalia/backend/tests/architecture/test_fe_be_contract_parity.py` — a deterministic,
server-free arch fitness test that catches the "imagined contract" class of bug at BUILD
time.

**Root cause being prevented:** In vitalia-fase2-adrian-embudo, the FE `LeadCardDTO`
TypeScript interface declared fields (`version`, `tenantId`, `isFrozen`, `frozenReason`,
`closureReason`, `reactivationCohortAt`, `serviceInterest`, `assignedDoctorId`,
`isBlacklisted`, `lastActivityDescription`, `lastActivityAt`) that the original BE DTO
never emitted. Both sides were mocked in tests. The board crashed live with `undefined`
field accesses. 6/8 tickets appeared GREEN before the live crash.

---

## How the test works

Three test functions:

### 1. `test_fe_fields_are_subset_of_be_fields` (parametrized over CONTRACT_PAIRS)

For each registered pair:
1. Import the BE Pydantic class via `importlib.import_module` → call `model_fields`.
2. Convert all BE field names from `snake_case` to `camelCase` via `_snake_to_camel`.
3. Parse the FE TypeScript file with a regex-based interface extractor
   (`_fe_interface_fields`) → get the set of declared field names.
4. Assert: `FE_fields - allowlist ⊆ BE_fields_camelized`.
5. On failure: lists every "imagined field" by name with fix options A/B.

No live server, no database, no network. Pure filesystem + Python import introspection.

### 2. `test_contract_registry_is_non_empty`

Asserts `len(CONTRACT_PAIRS) >= 1`. Prevents the registry from being silently cleared,
which would make the gate a no-op.

### 3. `test_contract_registry_files_exist`

For every registered pair, checks the FE file exists on disk. Catches registry rot when
FE files are moved or renamed.

---

## CONTRACT_PAIRS registry (current)

| BE module | BE class | FE file | FE interface | allowlist |
|---|---|---|---|---|
| `src.modules.vitalia.crm.application.dto.board_dto` | `LeadCardDTO` | `vitalia/frontend/src/features/adrian/types/embudo.types.ts` | `LeadCardDTO` | (empty — all FE fields covered by BE) |

---

## BE vs FE field verification

**BE `LeadCardDTO.model_fields` (25 fields, snake_case → camelCase):**

| snake_case | camelCase |
|---|---|
| assigned_doctor_id | assignedDoctorId |
| buying_signals | buyingSignals |
| channel | channel |
| closure_reason | closureReason |
| currency | currency |
| deposit_status | depositStatus |
| estimated_value | estimatedValue |
| frozen_reason | frozenReason |
| id | id |
| is_blacklisted | isBlacklisted |
| is_frozen | isFrozen |
| is_highlighted | isHighlighted |
| last_activity_at | lastActivityAt |
| last_activity_description | lastActivityDescription |
| name | name |
| operated_by | operatedBy |
| reactivation_cohort_at | reactivationCohortAt |
| score | score |
| service_interest | serviceInterest |
| sla_state | slaState |
| stage | stage |
| stage_entered_at | stageEnteredAt |
| temperature | temperature |
| tenant_id | tenantId |
| version | version |

**FE `LeadCardDTO` interface (23 fields declared):**

`id`, `tenantId`, `name`, `stage`, `stageEnteredAt`, `score`, `temperature`,
`operatedBy`, `channel`, `estimatedValue`, `currency`, `buyingSignals`,
`isFrozen`, `frozenReason`, `depositStatus`, `closureReason`, `reactivationCohortAt`,
`serviceInterest`, `assignedDoctorId`, `version`, `isBlacklisted`,
`lastActivityDescription`, `lastActivityAt`

**Imagined fields (FE declared but not in BE):** NONE

**BE-only fields (not in FE):** `isHighlighted`, `slaState`
(These are fine — the test only checks FE ⊆ BE, not equality.)

---

## Gate output

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3
rootdir: /home/chalreme/Proyectos/luana-vitalia/vitalia/backend
configfile: pyproject.toml
collected 3 items

tests/architecture/test_fe_be_contract_parity.py ...                     [100%]

============================== 3 passed in 0.18s ===============================
```

Lint: `ruff check` → 0 errors. Format: `ruff format --check` → already formatted.

---

## Honest coverage limit

This test is **REGISTRY-BASED**, not a universal scanner. It covers only the pairs
explicitly listed in `CONTRACT_PAIRS`. As of this commit: 1 pair (embudo board card).

**This is intentional.** Auto-discovery of all FE↔BE pairs is fragile (TS naming
conventions vary, interfaces may not directly mirror DTOs). The explicit registry is
honest about what it covers and forces developers to actively maintain it.

**Protocol going forward:** When a new FE view-model is built against a BE DTO, add
the pair to `CONTRACT_PAIRS` in the same PR as the implementation. The arch test will
gate it from day one.

**FE interfaces NOT yet registered (candidates for future entries):**

- `BoardKpis` (FE) ↔ `BoardKpis` (BE) — BE has different field names (`active` vs
  `totalActive`, `agent_count` vs `adrianCount`). Would require an allowlist for the
  FE-only remapped fields, or a rename alignment.
- `BoardColumn` (FE) ↔ `BoardColumn` (BE) — similar field renaming (`sum_value` vs
  `sumValue` is auto-camelized, but `over_sla_count` vs `overSlaCount` etc. should align).
- `TransitionDTO` (FE) ↔ transition response DTO (BE) — if a BE DTO is created for it.

---

## References

- `vitalia/backend/tests/architecture/test_fe_be_contract_parity.py` — the gate
- `vitalia/backend/src/modules/vitalia/crm/application/dto/board_dto.py` — BE DTO
- `vitalia/frontend/src/features/adrian/types/embudo.types.ts` — FE types
- `.claude/rules/definition-of-done-live-verify.md` — DoD live verification doctrine
- `T-FE2bis-be-contract-result.md` — earlier fix that extended the BE DTO
