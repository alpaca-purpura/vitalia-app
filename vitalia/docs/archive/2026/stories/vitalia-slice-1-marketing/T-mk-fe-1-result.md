# T-mk-fe-1 Result — FE Foundation: TS types + Zod + nuqs + MARKETING_COPY + React Query hooks

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-fe-1 (Wave 4 — FE foundation)
**Brand:** vitalia
**Builder:** claude-sonnet-4-6
**Commit:** 866079b

## Summary

Implemented the complete FE data layer for the marketing module. All 23 files
created from scratch (new module — no prior FE marketing feature existed).

## Files created

| File | Description |
|---|---|
| `vitalia/frontend/src/features/marketing/types/lucas-recommendation.ts` | LucasRecommendation, RecommendationStage, RecommendationStatus, RejectReason, response types |
| `vitalia/frontend/src/features/marketing/types/bowtie.ts` | BowtieSummaryResponse, StageDetailResponse, BowtieStage |
| `vitalia/frontend/src/features/marketing/types/attribution.ts` | AttributionMatrixResponse, AttributionOriginRow, AttributionOrigin |
| `vitalia/frontend/src/features/marketing/types/referrals.ts` | ReferralsResponse, ReferrerLeaderboardRow (HIPAA hash-only) |
| `vitalia/frontend/src/features/marketing/types/channel.ts` | ChannelDetailResponse, ChannelSyncState, ChannelMetricRow, ProviderSlug, SyncStatus |
| `vitalia/frontend/src/features/marketing/types/url-state.ts` | marketingParsers (nuqs, replace:true for intra-route) |
| `vitalia/frontend/src/lib/zod-schemas/lucas-recommendation.ts` | Zod schema mirrors Pydantic LucasRecommendationResponse (snake_case) |
| `vitalia/frontend/src/features/marketing/copy.ts` | MARKETING_COPY namespace (Spanish neutro, no voseo) |
| `vitalia/frontend/src/features/marketing/api/use-bowtie-summary.ts` | useQuery hook for /bowtie/summary |
| `vitalia/frontend/src/features/marketing/api/use-stage-detail.ts` | useQuery hook for /stage/{slug} |
| `vitalia/frontend/src/features/marketing/api/use-channel-detail.ts` | useQuery hook for /channels/{provider} |
| `vitalia/frontend/src/features/marketing/api/use-lucas-recommendations.ts` | useQuery hook for /recommendations |
| `vitalia/frontend/src/features/marketing/api/use-approve-recommendation.ts` | useMutation + Idempotency-Key for /approve |
| `vitalia/frontend/src/features/marketing/api/use-reject-recommendation.ts` | useMutation + Idempotency-Key for /reject (with RejectReason payload) |
| `vitalia/frontend/src/features/marketing/api/use-undo-recommendation.ts` | useMutation + Idempotency-Key for /undo |
| `vitalia/frontend/src/features/marketing/api/use-sync-channel.ts` | useMutation + Idempotency-Key for /channels/{provider}/sync |
| `vitalia/frontend/src/features/marketing/api/use-attribution-matrix.ts` | useQuery hook for /attribution-matrix |
| `vitalia/frontend/src/features/marketing/api/use-referrals.ts` | useQuery hook for /referrals |
| `vitalia/frontend/src/features/marketing/store/marketing-store.ts` | Zustand store (bowtieAnimating + pendingUndoTimers Map) |
| `vitalia/frontend/src/features/marketing/index.ts` | Public API barrel (named exports only) |
| `vitalia/frontend/src/features/marketing-shared/types.ts` | Re-exports for cross-story consumption (T-mk-fe-2..5) |
| `vitalia/frontend/src/features/marketing-shared/index.ts` | Public API barrel for marketing-shared |
| `vitalia/frontend/src/features/marketing/__tests__/marketing-parsers.test.ts` | 7 unit tests (SC-MK-03 gherkin + schema smoke) |

## Test results

```
src/features/marketing/__tests__/marketing-parsers.test.ts — 7 passed
  ✓ test_default_tab_is_attraction — default tab is attraction (SC-MK-03)
  ✓ test_tab_param_replace_intra_route — tab parser is configured for replace (intra-route) (SC-MK-03)
  ✓ period parser default is 30d
  ✓ approvalModal parser default is false
  ✓ MARKETING_COPY is defined and has no voseo (basic smoke)
  ✓ parses a valid recommendation (Zod schema smoke)
  ✓ rejects invalid status (Zod schema smoke)

Full suite: 82 test files, 630 tests — all PASS
Coverage: 47.84% statements (threshold: 20% — GREEN)
Architecture fitness: 42/42 tests PASS
TSC: 0 errors (strict mode)
ESLint: 0 errors, 0 warnings (new files)
```

## Gherkin coverage

| Scenario | Test | Status |
|---|---|---|
| SC-MK-03 Tab change URL state (default attraction) | `marketing-parsers.test.ts::test_default_tab_is_attraction` | PASS |
| SC-MK-03 Tab change uses replace (intra-route) | `marketing-parsers.test.ts::test_tab_param_replace_intra_route` | PASS |

## Architecture notes

- **HIPAA-lite dual filter**: every hook passes `clinicId` from `useClinicId()` + `tenantId` from Clerk `orgId`. No hook is `enabled` when `clinicId` is falsy.
- **Idempotency-Key**: all 4 mutation hooks generate `crypto.randomUUID()` per call, passed as header (BE enforces for POST mutations).
- **nuqs replace:true**: all 7 marketingParsers use `withOptions({ history: "replace" })` — intra-route tab changes do not create browser history entries.
- **HIPAA comment on referrals**: `ReferrerLeaderboardRow.referrerPatientIdHash` has JSDoc noting it is NEVER patient.name per `phi_fields.py`.
- **Zod v4 compatibility**: `z.record(z.string(), z.unknown())` (2 args required in v4 vs 1 in v3). Matches pattern in `conversation.ts`.
- **No default exports**: all exports are named (arch test gate).
- **marketing-shared**: re-exports LucasRecommendation + Attribution + Channel types for T-mk-fe-2..5 without circular deps.

## Validators satisfied

| Validator ID | Result |
|---|---|
| `fe_typecheck_tsc` | GREEN (0 errors) |
| `fe_lint_eslint` | GREEN (0 errors) |
| `fe_arch_fitness` | GREEN (42/42 tests pass) |
| `fe_test_marketing_unit` | GREEN (7/7 tests pass; SC-MK-03 covered) |
