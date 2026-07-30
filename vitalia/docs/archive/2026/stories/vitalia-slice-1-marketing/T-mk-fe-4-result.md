# T-mk-fe-4 Result — AttributionMatrixWidget + ReferralsWidget + 5 Stage Section Components

> Brand: vitalia
> Ticket: T-mk-fe-4 (Wave 5)
> Commit: fc8f6aa
> Branch: wip/vitalia (pushed origin)
> Builder: claude-sonnet-4-6
> Date: 2026-05-20

## Files created (14 new)

### Test files (RED written first — TDD per tdd-mandatory.md)

| File | Tests |
|---|---|
| `vitalia/frontend/src/features/marketing/__tests__/AttributionMatrixWidget.test.tsx` | 8 tests |
| `vitalia/frontend/src/features/marketing/__tests__/ReferralsWidget.test.tsx` | 7 tests |
| `vitalia/frontend/src/features/marketing/__tests__/ReservationStage.test.tsx` | 5 tests (SC-MK-03) |
| `vitalia/frontend/src/features/marketing/__tests__/ExpansionStage.test.tsx` | 6 tests (SC-MK-03) |
| `vitalia/frontend/src/features/marketing/__tests__/AttractionStage.test.tsx` | 5 tests |
| `vitalia/frontend/src/features/marketing/__tests__/QualificationStage.test.tsx` | 6 tests |
| `vitalia/frontend/src/features/marketing/__tests__/AdoptionStage.test.tsx` | 5 tests |

### Component files (GREEN implementation)

| File | LOC | Description |
|---|---|---|
| `vitalia/frontend/src/features/marketing/components/AttributionMatrixWidget.tsx` | ~195 | Semantic table heatmap, 4 origins × 5 KPI columns, per-cell aria-label, conv rate coloring, topInsightText from Lucas |
| `vitalia/frontend/src/features/marketing/components/ReferralsWidget.tsx` | ~215 | 3 KPI hero cards + top-5 leaderboard with referrerPatientIdHash only (HIPAA) |
| `vitalia/frontend/src/features/marketing/components/AttractionStage.tsx` | ~90 | Lucas card + KPIs + channel-breakdown placeholder (data-testid, T-mk-fe-5 slot) |
| `vitalia/frontend/src/features/marketing/components/QualificationStage.tsx` | ~75 | Lucas card + KPIs (standard) |
| `vitalia/frontend/src/features/marketing/components/ReservationStage.tsx` | ~95 | Lucas card + KPIs + AttributionMatrixWidget inline (SC-MK-03) |
| `vitalia/frontend/src/features/marketing/components/AdoptionStage.tsx` | ~75 | Lucas card + KPIs (standard) |
| `vitalia/frontend/src/features/marketing/components/ExpansionStage.tsx` | ~100 | Lucas card + KPIs + ReferralsWidget + NPS placeholder (SC-MK-03) |

## Files modified (2)

| File | Change |
|---|---|
| `vitalia/frontend/src/features/marketing/components/StageDispatcher.tsx` | Replaced StagePlaceholder dispatch with real AttractionStage/Qualification/Reservation/Adoption/Expansion components. Props forwarding: `period` added to dispatcher and each stage component. |
| `vitalia/frontend/src/features/marketing/index.ts` | Appended 14 new named exports for T-mk-fe-4 components + prop types |

## Quality gate results

| Gate | Result | Detail |
|---|---|---|
| `tsc --noEmit` | PASS | 0 errors |
| ESLint `src/` | PASS | 0 errors, 0 new warnings |
| Vitest run | PASS | 700/700 tests (95 test files, +42 new) |
| Architecture fitness | PASS | 42/42 tests |
| Coverage | PASS | 47.84% (threshold 20%) |
| ESLint warnings | PASS | No new baseline growth |

## Gherkin coverage mapping

### SC-MK-03 — Tab change re-renders stage panel

| Scenario step | Test path | Status |
|---|---|---|
| Reservation tab renders AttributionMatrixWidget inline | `__tests__/ReservationStage.test.tsx::test_renders_attribution_matrix_inline` | PASS |
| Expansion tab renders ReferralsWidget inline | `__tests__/ExpansionStage.test.tsx::test_renders_referrals_widget` | PASS |

### Additional coverage

| Behavior | Test path | Status |
|---|---|---|
| Attribution matrix semantic table with 4 origin rows + total | `AttributionMatrixWidget.test.tsx::test_renders_table_with_4_origins` | PASS |
| Attribution matrix column headers (Leads/Calificados/Conv.Listo/Reservas/Adopción) | `AttributionMatrixWidget.test.tsx::test_renders_column_headers` | PASS |
| Attribution matrix topInsightText from Lucas data | `AttributionMatrixWidget.test.tsx::test_renders_top_insight` | PASS |
| Attribution matrix per-cell aria-label for screen readers | `AttributionMatrixWidget.test.tsx::test_heatmap_cells_have_aria_label` | PASS |
| Attribution matrix loading skeleton | `AttributionMatrixWidget.test.tsx::test_loading_state` | PASS |
| Attribution matrix empty/error states | `AttributionMatrixWidget.test.tsx::test_empty_state + test_error_state` | PASS |
| Referrals 3 KPI hero cards (count, convRate, avgLTV) | `ReferralsWidget.test.tsx::test_renders_3_kpi_hero_cards` | PASS |
| Referrals leaderboard hashed IDs only (HIPAA compliance) | `ReferralsWidget.test.tsx::test_renders_top_referrers_leaderboard` | PASS |
| Referrals HIPAA: "Referidor (ID anónimo)" label, no patient.name | `ReferralsWidget.test.tsx::test_hipaa_no_patient_names` | PASS |
| AttractionStage channel-breakdown placeholder (data-testid) | `AttractionStage.test.tsx::test_renders_channel_breakdown_placeholder` | PASS |
| All stage aria-tabpanel with correct id | `*Stage.test.tsx::test_aria_tabpanel` × 5 stages | PASS |
| QualificationStage/AdoptionStage do NOT render attribution/referrals | `QualificationStage.test.tsx::test_no_attribution_widget + test_no_referrals_widget` | PASS |

## Key implementation decisions

- **Semantic table for a11y**: `AttributionMatrixWidget` uses `<table>` with `<thead>/<tbody>/<th scope="col">` + `aria-label` on every data `<td>`. Heatmap coloring uses `vt-text-success/warning/danger` CSS utility classes (no hardcoded HEX).
- **HIPAA referrals**: `ReferralsWidget` leaderboard column header is "Referidor (ID anónimo)" per `MARKETING_COPY.referrals.referrerLabel`. Renders `referrerPatientIdHash` in `font-mono` span — NEVER `patient.name`. PHI test asserts DOM contains no `patient.name` string.
- **Conversion rate heatmap thresholds**: `≥40%` = success, `≥20%` = warning, `<20%` = danger. Each cell shows raw count + pct in parentheses: `"20 (40%)"`.
- **StageDispatcher refactored**: Removed `StagePlaceholder` function entirely. Conditional rendering `{activeTab === "attraction" && <AttractionStage />}` pattern per stage. `period` prop forwarded to all stage components.
- **Channel breakdown stub**: `AttractionStage` renders `<div data-testid="channel-breakdown-placeholder" data-slot="channel-breakdown">` — T-mk-fe-5 will swap this with real `ChannelBreakdownRow` components without modifying the stage component (slot pattern).
- **NPS placeholder**: `ExpansionStage` renders `<div data-testid="nps-placeholder" data-slot="nps-widget">` — future ticket handles real NPS chart.
- **TDD flow**: 7 test files written RED first (42 tests failing) → GREEN implementation → all 42 pass → 0 regressions in existing 658 tests.
- **useTenantLocale mock**: Added `useOrganization` mock to Clerk mock factory + explicit `vi.mock("@/hooks/useTenantLocale")` in ReferralsWidget tests to avoid real Clerk org fetch.
- **forwardRef + displayName**: All 7 new components use `forwardRef` with `.displayName` set for React DevTools.
- **HIPAA dual filter**: All hooks pass `clinicId` from `useClinicId()` + `orgId` from `useAuth()`. Stage components are composing from hooks that already enforce dual filter.

## Live verification status

`chrome-devtools-verify` skill is marked DEPRECATED for Linux (designed for WSL2+Windows bridge). Live verification escalated to Chris staging gate — manual verification steps:

1. `make dev-vitalia` (stack up)
2. Navigate to `http://localhost:3002/marketing?tab=attraction`
3. Verify AttractionStage renders: Lucas cards + KPI heroes + channel-breakdown placeholder
4. Click `?tab=qualification` — QualificationStage: Lucas cards + KPIs (no attribution/referrals)
5. Click `?tab=reservation` — ReservationStage: Lucas cards + KPIs + **attribution matrix table** with 4 origin rows
6. Click `?tab=adoption` — AdoptionStage: Lucas cards + KPIs
7. Click `?tab=expansion` — ExpansionStage: Lucas cards + KPIs + **referrals widget** (hashed IDs) + NPS placeholder
8. Verify attribution matrix cells show conv rate colors (green/yellow/red based on %)
9. Verify referrals leaderboard shows only anonymized IDs, never patient names

## Downstream regression notes

`downstream-regression-na: brand-local FE component; no cross-brand consumers` — all new files include this marker in their JSDoc header. No engine packages modified. StageDispatcher.tsx modification is additive dispatch refactoring (no API surface change).
