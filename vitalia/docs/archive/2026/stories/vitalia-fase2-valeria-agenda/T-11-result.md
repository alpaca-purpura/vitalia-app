# T-11 Result — Agenda TypeScript Types + Zod Schemas

**Story:** vitalia-fase2-valeria-agenda
**Ticket:** T-11
**Branch:** wip/vitalia
**Date:** 2026-05-26

## Files Created/Modified

### Created
- `vitalia/frontend/src/features/valeria/types/agenda.types.ts` — Pure TS types mirroring Pydantic DTOs (camelCase, ISO 8601 strings, PHI masking documented)
- `vitalia/frontend/src/features/valeria/types/agenda-schema.ts` — Zod v4 runtime schemas including ChargeRequestSchema discriminated union by currency (6 variants)
- `vitalia/frontend/src/features/valeria/types/__tests__/agenda-schema.test.ts` — 41 TDD tests (RED-first → GREEN)

### Modified
- `vitalia/frontend/src/features/valeria/index.ts` — Barrel exports updated for T-11 types and schemas

## Quality Gates

| Gate | Result |
|---|---|
| TypeScript strict (`tsc --noEmit`) | PASS — 0 errors |
| ESLint (60+ rules) | PASS — 0 errors, 0 warnings |
| Vitest (41 tests) | PASS — 41/41 GREEN |
| Coverage (overall) | PASS — 81.89% (threshold 20%) |
| Full suite (1746 tests) | PASS — 167 test files, 1746 tests |

## Acceptance Criteria Verification

| AC | Description | Status |
|---|---|---|
| A1 | All 6 currencies (PEN/ARS/MXN/USD/COP/CLP) validate correctly | PASS — `test_currency_discriminated_union` covers all 6 |
| A2 | `emitInvoice=true` requires `fiscalDocType` via cross-field `.refine()` | PASS — `emitInvoice refine` test suite |
| A3 | Spanish neutro LatAm error messages (no voseo) | PASS — all Zod error strings use tuteo |
| A4 | PHI fields documented as masked strings only | PASS — JSDoc on `patientNameMasked`, `patientDniMasked`, `patientPhoneMasked`, `patientEmailMasked` |
| G5 | Pre-commit smoke gate (tsc 0, eslint 0, vitest GREEN) | PASS |

## Gherkin Coverage (SC-11)

- `test_currency_discriminated_union` — scenario: "currency-discriminated fiscalDocType validation"
- `test_ChargeRequestSchema_validates_PEN_with_boleta` — scenario: "PEN accepts boleta"
- `test_ChargeRequestSchema_emitInvoice_refine_*` — scenario: "emitInvoice cross-field refine"
- `test_phi_fields_are_masked_strings` — scenario: "PHI masking documented on AppointmentDetailSchema"
- `test_AgendaGridResponseSchema_parses_list_of_slots` — scenario: "grid response parsing"

## Key Design Decisions

1. **ChargeRequestSchema discriminated union by `currency`** (follows 03-arch.md §6.7 SSoT, not prompt description which mentioned `method`). Each of 6 currency variants restricts `fiscalDocType` to country-specific values.

2. **Zod v4 API** — used `{ error: "message" }` (not v3's `errorMap`) for `z.enum()` custom messages. Strict RFC4122 UUID validation requires variant bits `[89abAB]` — test fixtures use `550e8400-e29b-41d4-a716-446655440001` format.

3. **HIPAA-lite**: PHI fields are opaque masked strings only (`patientNameMasked`, `patientDniMasked`, etc.). Frontend never receives raw PHI. Documented via JSDoc in both `.types.ts` and `.schema.ts`.

4. **ISO 8601 datetimes as string** — no `Date` objects to avoid hydration mismatch.

5. **`AgendaSlot` naming collision** — the component `./components/agenda/AgendaSlot` and the type `AgendaSlot` from types. Barrel re-exports the type as `AgendaSlotDTO` to avoid conflict.

## §11 Gaps from CONTEXT-BRIEF (partial faithfulness)

- MSW stubs completeness: not yet addressed in T-11 (types-only ticket; stubs belong to API client tickets T-3 / T-12+)
- Test path traceability: addressed via Gherkin coverage table above
- HIPAA dual filter audit: BE concern tracked in 03-arch.md; FE types do not bypass it

## IMPL-LOG Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, barrel exports pattern | Named exports only, `types/` slice under `features/valeria/` |
| `tessl__zod` | Zod schemas for form runtime, discriminated union | Zod v4 `{ error: "..." }` syntax, `z.discriminatedUnion("currency", [...])` |
| `tessl__react-patterns` | Baseline always-on | No components in T-11 (types-only); patterns applied for future component layers |
| `hipaa-lite` overlay | PHI field masking documentation | `patientNameMasked` / `patientDniMasked` / `patientPhoneMasked` / `patientEmailMasked` — opaque masked strings, never raw PHI |

## Live Verification

`chrome-devtools-verify` skill marked DEPRECATED for Linux Mint (requires WSL2+Windows bridge rewrite). T-11 is types/schemas only — no user-facing UI introduced. Live verification will be needed at T-12+ when API hooks and components are built. Escalated to Chris staging gate at that point.
