# T-mk-fe-2 — result

> Ticket: T-mk-fe-2 (Wave 5 — Bowtie SVG + StageTabs + Layout + StageDispatcher + ActivityFooter + page.tsx)
> Story: vitalia-slice-1-marketing
> Commit: ac7b3e9
> Date: 2026-05-20

## Summary

Implemented Wave 5 of the marketing module FE, fulfilling SC-MK-03 (bowtie sticky top + stage tab navigation).

## Files Created

| File | Description |
|---|---|
| `vitalia/frontend/src/features/marketing/components/MarketingBowtieSVG.tsx` | Pixel-invariante SVG bowtie per mockup Batch 6 |
| `vitalia/frontend/src/features/marketing/components/MarketingBowtieSVG.stories.tsx` | Storybook stories |
| `vitalia/frontend/src/features/marketing/components/MarketingStageTabs.tsx` | 5-tab horizontal nav with cian active state |
| `vitalia/frontend/src/features/marketing/components/MarketingStageTabs.stories.tsx` | Storybook stories |
| `vitalia/frontend/src/features/marketing/components/MarketingLayout.tsx` | Page layout orchestrator (sticky bowtie + tabs + dispatcher + footer) |
| `vitalia/frontend/src/features/marketing/components/MarketingLayout.stories.tsx` | Storybook stories |
| `vitalia/frontend/src/features/marketing/components/StageDispatcher.tsx` | Stage panel dispatcher with slot placeholders for T-mk-fe-3..5 |
| `vitalia/frontend/src/features/marketing/components/StageDispatcher.stories.tsx` | Storybook stories |
| `vitalia/frontend/src/features/marketing/components/MarketingActivityFooter.tsx` | Activity/sync status footer |
| `vitalia/frontend/src/features/marketing/components/MarketingActivityFooter.stories.tsx` | Storybook stories |
| `vitalia/frontend/src/app/marketing/page.tsx` | Server Component page with Clerk auth guard |
| `vitalia/frontend/src/features/marketing/__tests__/MarketingLayout.test.tsx` | 6 tests covering SC-MK-03 bowtie sticky + DOM order |
| `vitalia/frontend/src/features/marketing/__tests__/MarketingStageTabs.test.tsx` | 5 tests covering SC-MK-03 tab click + cian active state |

## Files Modified

| File | Change |
|---|---|
| `vitalia/frontend/src/app/globals.css` | Added 3 new `vt-*` utility classes + `--vitalia-text-color` pre-computed CSS var |
| `vitalia/frontend/src/features/marketing/index.ts` | Appended exports for 5 new components + prop types (parallel-safety: append-only) |

## Key Technical Decisions

**Hardcoded color elimination (FE-A1):**
- All 5 components use `vt-*` CSS utility classes instead of `hsl(var(--vitalia-*))` Tailwind arbitrary values
- SVG attributes (`fill`, `stroke`, `stopColor`) use pre-computed `var(--vitalia-*-color)` CSS vars (defined in globals.css `:root`, not hsl() in TSX)
- New CSS vars added to globals.css: `--vitalia-text-color`
- New utility classes: `vt-bg-tab-active`, `vt-border-b-cian`, `vt-text-azul-marino-bold`

**SVG geometry (pixel-invariante per mockup Batch 6):**
- viewBox="0 0 900 180"
- 5 ellipses: attraction(cx=100,rx=70), qualification(cx=290,rx=50), reservation(cx=450,rx=35), adoption(cx=600,rx=50), expansion(cx=800,rx=70)
- Arrow connectors: [170→240], [340→400], [485→545], [650→710]
- Gradients: stages 1-4 use cian→azul-marino; stage 5 uses cian→purpura→verde-lima

**SC-MK-03 bowtie sticky:**
- `data-testid="bowtie-sticky-container"` on the sticky div with `className="sticky top-0 z-10 ..."`
- Tab changes use nuqs `replace` (intra-route, no browser history entry)

**Server Component page.tsx:**
- Pure Server Component (Clerk `auth()` server-side)
- Imports from barrel `@/features/marketing` only (FE-A4 cross-feature test passes)
- `MarketingLayout` handles all client interactivity

**Parallel safety (T-mk-fe-3):**
- `index.ts` modified with append-only — no Lucas* component files touched
- StageDispatcher has `data-slot="lucas-recommendations"` placeholder div for T-mk-fe-3 to fill

## Quality Gates

| Gate | Result |
|---|---|
| TSC --noEmit | 0 errors |
| ESLint (marketing + page files) | 0 errors |
| Vitest total | 641/641 PASS |
| Architecture fitness (42 tests) | 42/42 PASS |
| FE-A1 hardcoded colors | PASS (0 new violations) |
| FE-A4 cross-feature imports | PASS |
| FE-A5 Server Components | PASS |
| Coverage | 47.84% (threshold: 20%) |

## Gherkin Coverage

| Scenario | Test | Status |
|---|---|---|
| SC-MK-03 bowtie sticky top | `MarketingLayout.test.tsx::test_bowtie_sticky_top` | PASS |
| SC-MK-03 bowtie visible on render | `MarketingLayout.test.tsx::renders MarketingBowtieSVG at top` | PASS |
| SC-MK-03 tabs below bowtie | `MarketingLayout.test.tsx::renders MarketingStageTabs below bowtie` | PASS |
| SC-MK-03 stage content rendered | `MarketingLayout.test.tsx::renders StageDispatcher as main content` | PASS |
| SC-MK-03 activity footer | `MarketingLayout.test.tsx::renders MarketingActivityFooter at bottom` | PASS |
| SC-MK-03 DOM order bowtie before tabs | `MarketingLayout.test.tsx::has correct DOM order` | PASS |
| SC-MK-03 tab click URL update | `MarketingStageTabs.test.tsx::test_tab_click_updates_url_replace` | PASS |
| SC-MK-03 active tab cian highlight | `MarketingStageTabs.test.tsx::test_active_tab_highlight_cian` | PASS |
| SC-MK-03 inactive tab styling | `MarketingStageTabs.test.tsx::inactive tab does not have active classes` | PASS |
| SC-MK-03 count badges | `MarketingStageTabs.test.tsx::renders count badge with stage count` | PASS |
| SC-MK-03 all 5 tabs rendered | `MarketingStageTabs.test.tsx::renders all stage tabs` | PASS |
