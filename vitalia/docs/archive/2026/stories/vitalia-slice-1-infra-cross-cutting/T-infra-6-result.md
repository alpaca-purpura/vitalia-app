# T-infra-6 — Storybook setup + 12 critical component stories

**State:** tests-passing
**Builder:** Claude Sonnet 4.6
**Branch:** wip/vitalia-slice-1-shipping
**Date:** 2026-05-18

## Summary

Storybook v10 configured and 12 component stories implemented for the Vitalia frontend. This completes all 10 infra tickets for `vitalia-slice-1-infra-cross-cutting`.

## Validators

| Validator | Result | Detail |
|---|---|---|
| `fe_typecheck_tsc` | PASS | `tsc --noEmit` EXIT 0 — 0 errors |
| `fe_lint_eslint` | PASS | 0 new errors introduced (2 pre-existing baseline from T-infra-4 remain: `dirname` unused in `test_fsd_boundaries.test.ts` + `ALLOWED_PADDING_CLASSES` unused in `test_page_padding.test.ts`) |
| `visual_storybook_build` | PASS | `storybook build` completed successfully — no errors |

## Files Created

### Storybook configuration

- `vitalia/frontend/.storybook/main.ts` — StorybookConfig: stories glob `../src/components/**/*.stories.@(ts|tsx)`, addons: a11y (essentials bundled in v10), framework: `@storybook/nextjs`, autodocs
- `vitalia/frontend/.storybook/preview.ts` — Preview: imports globals.css, vitalia background tokens (vitalia-bg/vitalia-surface), a11y config, controls matchers

### Scaffold stub components (Slice 2 implementation pending)

- `vitalia/frontend/src/components/shared/lucas-recommendations/LucasStageRecommendationsCard.tsx` — Stage recommendation widget scaffold (loading/empty/recommendation list states)
- `vitalia/frontend/src/components/shared/marketing/MarketingBowtieSVG.tsx` — Marketing bowtie funnel SVG scaffold (accessible role="img", cian/purpura linearGradients)
- `vitalia/frontend/src/components/shared/channels/ChannelBreakdownRow.tsx` — Channel metrics row scaffold (change indicator with vt-text-success/danger)
- `vitalia/frontend/src/components/shared/attribution/AttributionMatrixWidget.tsx` — Attribution matrix scaffold (accessible role="table", heatmap cells)
- `vitalia/frontend/src/components/shared/wizard/WizardChatThread.tsx` — Conversational wizard scaffold (progress bar, message bubbles, typing indicator)
- `vitalia/frontend/src/components/shared/deposits/DepositBadge.tsx` — Deposit status badge (5 statuses, currency via `toLocaleString("es-419")`, NEVER hardcoded 'USD')

### Stories (12 total)

- `vitalia/frontend/src/components/shared/agents/AgentAvatar.stories.tsx` — 7 stories: Valeria/Adrian/Lucas + size variants + status indicator
- `vitalia/frontend/src/components/shared/agents/AgentAttribution.stories.tsx` — 6 stories: 3 agents + with/without target/timestamp + stacked
- `vitalia/frontend/src/components/shared/phi/PiiMaskedSpan.stories.tsx` — 8 stories: name/dni/cuit/phone/email/dob masking + null value + role-reveal demo (FAKE data only)
- `vitalia/frontend/src/components/shared/phi/RequireRole.stories.tsx` — 6 stories: doctor/nurse allowed, marketing denied, patient restricted, null role, no fallback
- `vitalia/frontend/src/components/shared/contact-sidebar/ContactSidebar.stories.tsx` — 5 stories: full patient, lead (email only), empty, with actions, phone+email (FAKE PHI)
- `vitalia/frontend/src/components/shared/activity-stream/ActivityStreamSticky.stories.tsx` — 5 stories: empty, loading, few events, many events, collapsed default
- `vitalia/frontend/src/components/shared/lucas-recommendations/LucasStageRecommendationsCard.stories.tsx` — 4 stories: empty, loading, with recs, single high-priority
- `vitalia/frontend/src/components/shared/marketing/MarketingBowtieSVG.stories.tsx` — 4 stories: placeholder, loading, with data, compact
- `vitalia/frontend/src/components/shared/channels/ChannelBreakdownRow.stories.tsx` — 6 stories: positive change, negative, flat, minimal, loading, multi-row
- `vitalia/frontend/src/components/shared/attribution/AttributionMatrixWidget.stories.tsx` — 4 stories: empty, loading, full matrix, single channel
- `vitalia/frontend/src/components/shared/wizard/WizardChatThread.stories.tsx` — 4 stories: empty, typing indicator, mid-conversation, complete
- `vitalia/frontend/src/components/shared/deposits/DepositBadge.stories.tsx` — 6 stories: all 5 statuses + small size + all statuses grid + MXN

### Package.json modifications

- Added scripts: `"storybook": "storybook dev -p 6006"`, `"build-storybook": "storybook build"`
- Added devDependencies: `storybook@^10.4.0`, `@storybook/nextjs@^10.4.0`, `@storybook/addon-a11y@^10.4.0`

## Key Design Decisions

1. **Storybook v10 (not v8)**: essentials bundled in v10 core — no separate `@storybook/addon-essentials` package needed
2. **No `staticDirs`**: `vitalia/frontend/public/` does not exist — removed to avoid build failure
3. **HIPAA-lite compliance**: all story fixtures use FAKE/redacted data — no real PHI anywhere
4. **Scaffold stubs**: 6 components scaffold with proper TypeScript interfaces for Slice 2 implementation. Footer note in each: "Implementación completa en Slice 2"
5. **CSS design tokens**: no `hsl()` literals in `.tsx` files — all colors via `vt-*` utility classes or Tailwind tokens (complies with arch test `test_no_hardcoded_colors.test.ts`)
6. **Currency**: `DepositBadge` uses `toLocaleString("es-419")` per master-data rule — NEVER hardcoded 'USD'
7. **a11y addon mandatory**: per HIPAA-lite chromatic visual regression spec

## Pre-existing ESLint baseline (NOT from T-infra-6)

2 pre-existing warnings from T-infra-4 baselines carried forward:
- `test_fsd_boundaries.test.ts:32:35` — `'dirname' is defined but never used`
- `test_page_padding.test.ts:36:7` — `'ALLOWED_PADDING_CLASSES' is assigned a value but never used`

These were present before T-infra-6 began. Recommend `/pm-vitalia` schedule cleanup ticket.

<!-- @pm: build phase done (state: tests-passing). Files: 26 new + 1 modified. Native ticket tests: validators 3/3 PASS (tsc EXIT 0 / eslint 0 new / storybook build success). Awaiting orchestrator → gate-runner → auditor-frontend (independent verdict). -->
