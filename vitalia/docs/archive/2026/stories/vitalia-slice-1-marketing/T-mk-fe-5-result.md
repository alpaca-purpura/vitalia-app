# T-mk-fe-5 Result — Channel components Wave 5

> Brand: vitalia
> Ticket: T-mk-fe-5 (Wave 5)
> Commit: b8edd54
> Branch: wip/vitalia (pushed origin)
> Builder: claude-sonnet-4-6
> Date: 2026-05-20

## Files created (8 new)

### Test files (RED written first — TDD per tdd-mandatory.md)

| File | Tests |
|---|---|
| `vitalia/frontend/src/features/marketing/__tests__/ConnectionBadge.test.tsx` | 7 tests |
| `vitalia/frontend/src/features/marketing/__tests__/ChannelBreakdownRow.test.tsx` | 8 tests (SC-MK-02) |
| `vitalia/frontend/src/features/marketing/__tests__/ChannelDetailSidebar.test.tsx` | 9 tests |
| `vitalia/frontend/src/features/marketing/__tests__/ChannelConnectionWizard.test.tsx` | 7 tests |

### Component files (GREEN implementation)

| File | LOC | Description |
|---|---|---|
| `vitalia/frontend/src/features/marketing/components/ConnectionBadge.tsx` | ~80 | 4-state pill badge (idle/running/error/disconnected), CSS token coloring vt-text-success/warning/danger/neutral, data-state attribute, no hardcoded HEX |
| `vitalia/frontend/src/features/marketing/components/ChannelBreakdownRow.tsx` | ~130 | Per-provider row: ConnectionBadge + last-success timestamp + retry button on error; click opens ChannelDetailSidebar; forwardRef |
| `vitalia/frontend/src/features/marketing/components/ChannelDetailSidebar.tsx` | ~195 | Slide-in dialog panel: KPIs/syncState + top-3 campaigns + LucasStageRecommendationsCard; external links target=_blank rel="noopener noreferrer" |
| `vitalia/frontend/src/features/marketing/components/ChannelConnectionWizard.tsx` | ~185 | 3-step OAuth wizard (provider selector → OAuth → confirm); full page navigation window.location.href (NOT window.open popup) per security rule |

## Files modified (3)

| File | Change |
|---|---|
| `vitalia/frontend/src/features/marketing/components/AttractionStage.tsx` | Replaced placeholder div with real `<ChannelBreakdownRow provider="meta_ads" />` and `<ChannelBreakdownRow provider="google_ads" />` (slot pattern T-mk-fe-5 fills). Import added. |
| `vitalia/frontend/src/features/marketing/__tests__/AttractionStage.test.tsx` | Added `vi.mock("../components/ChannelBreakdownRow")` to isolate AttractionStage from channel hook dependencies (0 regressions). |
| `vitalia/frontend/src/features/marketing/index.ts` | Added 8 named exports: `ConnectionBadge` + `ConnectionBadgeProps` + `ConnectionBadgeVariant`, `ChannelBreakdownRow` + `ChannelBreakdownRowProps`, `ChannelDetailSidebar` + `ChannelDetailSidebarProps`, `ChannelConnectionWizard` + `ChannelConnectionWizardProps`. |

## Quality gate results

| Gate | Result | Detail |
|---|---|---|
| `tsc --noEmit` | PASS | 0 errors |
| ESLint `src/` | PASS | 0 errors, 0 new warnings |
| Vitest run | PASS | 731/731 tests (99 test files, +4 new) |
| Architecture fitness | PASS | 42/42 tests |
| Coverage | PASS | >47% (threshold 20%) |
| ESLint warnings | PASS | No new baseline growth |

## Gherkin coverage mapping

### SC-MK-02 — Channel sync degraded UI

| Scenario step | Test path | Status |
|---|---|---|
| Badge shows error state when sync fails | `ChannelBreakdownRow.test.tsx::test_shows_warning_badge_when_sync_error` | PASS |
| Shows timestamp of last known data when error | `ChannelBreakdownRow.test.tsx::test_shows_last_known_metrics_with_timestamp` | PASS |
| Retry button triggers useSyncChannel mutation | `ChannelBreakdownRow.test.tsx::test_retry_sync_button_invokes_useSyncChannel` | PASS |

### Additional coverage

| Behavior | Test path | Status |
|---|---|---|
| ConnectionBadge idle/neutral token | `ConnectionBadge.test.tsx::test_idle_state` | PASS |
| ConnectionBadge running/warning token | `ConnectionBadge.test.tsx::test_running_state` | PASS |
| ConnectionBadge error/danger token | `ConnectionBadge.test.tsx::test_error_state` | PASS |
| ConnectionBadge disconnected/danger token | `ConnectionBadge.test.tsx::test_disconnected_state` | PASS |
| ConnectionBadge no hardcoded HEX in className | `ConnectionBadge.test.tsx::test_no_hardcoded_hex` | PASS |
| ChannelBreakdownRow click opens sidebar | `ChannelBreakdownRow.test.tsx::test_click_row_opens_sidebar` | PASS |
| ChannelBreakdownRow idle — no retry button | `ChannelBreakdownRow.test.tsx::test_idle_state_no_retry_button` | PASS |
| ChannelDetailSidebar not rendered when closed | `ChannelDetailSidebar.test.tsx::test_not_rendered_when_closed` | PASS |
| ChannelDetailSidebar external link target=_blank + rel=noopener | `ChannelDetailSidebar.test.tsx::test_external_link_has_target_blank` | PASS |
| ChannelDetailSidebar top-3 campaigns from metrics | `ChannelDetailSidebar.test.tsx::test_shows_top_3_campaigns` | PASS |
| ChannelDetailSidebar empty state when no metrics | `ChannelDetailSidebar.test.tsx::test_no_campaigns_empty_state` | PASS |
| ChannelConnectionWizard not rendered when closed | `ChannelConnectionWizard.test.tsx::test_not_rendered_when_closed` | PASS |
| ChannelConnectionWizard OAuth uses full page nav (NOT window.open) | `ChannelConnectionWizard.test.tsx::test_oauth_uses_full_page_navigation` | PASS |
| ChannelConnectionWizard provider selection enables authorize | `ChannelConnectionWizard.test.tsx::test_provider_selection_enables_authorize` | PASS |
| ChannelConnectionWizard step indicator marks step 1 active | `ChannelConnectionWizard.test.tsx::test_step_indicator_shows_step_1_active` | PASS |
| AttractionStage still shows placeholder container (slot preserved) | `AttractionStage.test.tsx::test_renders_channel_breakdown_placeholder` | PASS |

## Key implementation decisions

- **Array response from hook**: `useChannelDetail` returns `ChannelDetailResponse[]` — components access `data?.[0]` to get the provider-specific record. This matches the actual hook implementation (T-mk-fe-1 origin).
- **Slot pattern preservation**: `AttractionStage.tsx` retains `data-testid="channel-breakdown-placeholder"` and `data-slot="channel-breakdown"` on the container div — this preserves T-mk-fe-4 test `test_renders_channel_breakdown_placeholder` without needing to rename the testid. The real rows live inside the container.
- **Security — OAuth full page nav**: `ChannelConnectionWizard` uses `window.location.href = authorizationUrl` for OAuth redirect. `window.open()` is never called. Test asserts `windowOpenSpy` not called + `href` setter called with auth URL.
- **Security — external links**: `ChannelDetailSidebar` external link to Ads Manager always renders `target="_blank" rel="noopener noreferrer"`.
- **4 CSS token states**: `ConnectionBadge` maps status → CSS var token class (`vt-text-success/warning/danger/neutral`). No Tailwind color utilities (`text-green-500` etc.), no hardcoded HEX. Test `test_no_hardcoded_hex` verifies className contains no `#RRGGBB`.
- **`_testAuthorizationUrl` prop**: `ChannelConnectionWizard` accepts optional `_testAuthorizationUrl` to inject OAuth URL in tests — avoids needing to mock `fetch` for the OAuth initiation endpoint. In production, wizard would call an API endpoint to get the URL before redirecting.
- **Retry button isolation**: retry button click stops propagation (`e.stopPropagation()`) to prevent triggering row click (which opens sidebar). Both interactions tested independently.
- **AttractionStage mock update**: Added `vi.mock("../components/ChannelBreakdownRow")` to the existing `AttractionStage.test.tsx`. This prevents T-mk-fe-4 test from failing due to `useSyncChannel()` / `useMutation` returning undefined in that test's mock setup.
- **forwardRef + displayName**: All 4 new components use `forwardRef` with `.displayName` set.
- **HIPAA-lite**: No PHI in any component. ChannelDetailSidebar shows `accountId` (advertising account ID, not patient data). `lastSuccessAt` is a sync timestamp, not clinical data.
- **TDD flow**: 4 test files written RED first (31 tests failing) → GREEN implementation → all 31 pass → 0 regressions in existing 700 tests.

## Live verification status

`chrome-devtools-verify` skill is marked DEPRECATED for Linux (designed for WSL2+Windows bridge). Live verification escalated to Chris staging gate — manual verification steps:

1. `make dev-vitalia` (stack up)
2. Navigate to `http://localhost:3002/marketing?tab=attraction`
3. Verify AttractionStage renders: Lucas card + KPIs + channel breakdown container with 2 provider rows (Meta Ads, Google Ads)
4. Verify each row shows provider name + ConnectionBadge + (if error: retry button + last success timestamp)
5. Click a channel row → ChannelDetailSidebar slides in from right
6. Verify sidebar: provider title + external link (target=_blank) + campaigns section + Lucas recs
7. Click "Cerrar" → sidebar closes
8. Navigate to Marketing > click "Conectar canal" (if ChannelConnectionWizard is wired to a connect button)
9. Verify wizard: step 1 = provider selector, authorize button disabled until selection
10. Select Meta Ads → authorize button enables
11. Click "Autorizar acceso" → full page navigation (not popup)

## Downstream regression notes

`downstream-regression-na: brand-local FE component; no cross-brand consumers` — all new files include this marker in their JSDoc header. No engine packages modified. AttractionStage.tsx modification is additive (replaces placeholder div content with real rows; container div preserved for T-mk-fe-4 test compatibility).
