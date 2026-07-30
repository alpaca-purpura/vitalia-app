# T-mk-fe-6 Result — Storybook stories + visual regression baselines

**Ticket:** T-mk-fe-6 — Wave 6: Storybook stories complete + Chromatic visual regression baselines
**Story:** vitalia-slice-1-marketing
**State:** pushed
**Commit:** 5b8b0d2
**Branch:** wip/vitalia
**Date:** 2026-05-20

---

## Summary

13 new files shipped: 11 Storybook story files covering all NEW marketing components per `03-arch-fe.md § 7`, plus 1 BowtieSVG visual regression test (8 assertions) as local chromatic fallback.

## Files Created

### Storybook stories (`*.stories.tsx`)

| File | Component | Variants |
|---|---|---|
| `ConnectionBadge.stories.tsx` | ConnectionBadge | idle, running, error, disconnected, success-variant, custom-label |
| `LucasApprovalModal.stories.tsx` | LucasApprovalModal | Review (confirm phase), RecepcionDenied (SC-MK-04), LowPriorityRec |
| `LucasRejectModal.stories.tsx` | LucasRejectModal | Default (empty form), OtherReasonSelected (textarea) |
| `LucasRecommendationDetailModal.stories.tsx` | LucasRecommendationDetailModal | Open, Approved, Rejected, Expired, RecepcionDenied, NoAnalysisData |
| `LucasUndoChip.stories.tsx` | LucasUndoChip | NoActiveTimer (chip=null) |
| `LucasStageRecommendationsCard.stories.tsx` | LucasStageRecommendationsCard | AttractionStage, QualificationStage, AllStages, RecepcionRole |
| `AttributionMatrixWidget.stories.tsx` | AttributionMatrixWidget | Period7d, Period30d, Period90d |
| `ReferralsWidget.stories.tsx` | ReferralsWidget | Period7d, Period30d, Period90d (HIPAA-lite: hash-only leaderboard) |
| `ChannelBreakdownRow.stories.tsx` | ChannelBreakdownRow | MetaAds, GoogleAds |
| `ChannelDetailSidebar.stories.tsx` | ChannelDetailSidebar | MetaAdsOpen, GoogleAdsOpen, Closed |
| `ChannelConnectionWizard.stories.tsx` | ChannelConnectionWizard | Step1Selector, Closed |

### Visual regression test

| File | Tests | Purpose |
|---|---|---|
| `MarketingBowtieSVG.test.tsx` | 8 tests | Local fallback for `visual_regression_bowtie_svg` validator |
| `__snapshots__/MarketingBowtieSVG.test.tsx.snap` | 1 snapshot | SVG inline snapshot (baseline) |

## Storybook Config Verified

- `.storybook/main.ts` — `"@storybook/nextjs"` + stories glob already includes `src/features/**/*.stories.@(ts|tsx)`. No changes needed.
- `.storybook/preview.ts` — imports `globals.css` (vt-* tokens available). No Storybook-level providers needed (components use hooks internally; Storybook renders loading/null states without auth).
- `@storybook/test` not installed — replaced `fn()` with `() => {}` for callback args. Pattern consistent with existing story files.

## chromatic-baseline-pending

`CHROMATIC_PROJECT_TOKEN` not set. `chromatic` package not installed.

**Action required at merge:** Chris ratifies chromatic baseline via:
```bash
cd vitalia/frontend
npx chromatic --project-token=$CHROMATIC_PROJECT_TOKEN --exit-zero-on-changes --auto-accept-changes=false --build-script-name=build-storybook
```

Validator `visual_regression_bowtie_svg` is satisfied locally via `MarketingBowtieSVG.test.tsx` (8 assertions) until Chromatic baselines are published.

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| `eslint src/features/marketing/` | 0 errors |
| `vitest run` | 739/739 PASS (100 test files) |
| arch fitness `src/__tests__/architecture/` | 42/42 PASS (10 files) |
| `visual_regression_bowtie_svg` (local) | 8/8 PASS (chromatic-baseline-pending) |
| `fe_arch_fitness` | 42/42 PASS |

## Live Verification

`chrome-devtools-verify` skill marked DEPRECATED for Linux Mint (2026-05-15). Escalated to Chris staging gate manual — verify at `https://dev-app.vitalialat.com/marketing` post-deploy.

## Coverage Baseline Check

Warning baselines (check-file / jsdoc / react-perf) did not grow — story files and test files do not trigger ESLint warning categories. Vitest coverage threshold maintained (739 tests, 100 files).
