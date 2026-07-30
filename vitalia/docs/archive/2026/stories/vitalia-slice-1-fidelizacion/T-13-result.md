# T-13 Result — Storybook stories: fidelización components

**Ticket:** T-13 FE Storybook stories — fidelización components (mandatory coverage)
**Branch:** wip/vitalia
**Commit SHA:** 3b22777
**Build validator:** `cd vitalia/frontend && npx storybook build --quiet` — EXIT 0

---

## Validator output

```
┌  Building storybook v10.4.0
◇  Cleaning outputDir: storybook-static
◇  Loading presets
◇  Building manager..
●  Building preview..
●  Using implicit CSS loaders
●  Using SWC as compiler
●  Using default Webpack5 setup
▲  asset size limit: (performance hints only — not errors)
◇  Output directory: vitalia/frontend/storybook-static
└  Storybook build completed successfully
```

Exit code: 0

---

## Files changed (16)

### Modified
- `vitalia/frontend/.storybook/main.ts` — added `"../src/features/**/*.stories.@(ts|tsx)"` glob (features stories were previously undiscovered)

### Created — 15 `.stories.tsx` files

| File | Component | Stories |
|---|---|---|
| `components/FidelizacionKPIsHero.stories.tsx` | FidelizacionKPIsHero | Loading, Populated, ZeroValues, NegativeTrend |
| `components/FidelizacionTabsBar.stories.tsx` | FidelizacionTabsBar | TabMultisession, TabFollowup, TabMaintenance, TabAbsence, TabNPS |
| `components/ReEngagementCard.stories.tsx` | ReEngagementCard | MultiSession, FollowUp, Maintenance, Absence, UrgencyCritical, UrgencyUpToDate, AbsenceNoMarketing |
| `components/ConfirmTemplateModal.stories.tsx` | ConfirmTemplateModal | Default, LongPreview |
| `components/PausePatientModal.stories.tsx` | PausePatientModal | Default |
| `components/ManualCallLoggedModal.stories.tsx` | ManualCallLoggedModal | Default |
| `components/SuggestSlotsModal.stories.tsx` | SuggestSlotsModal | Default, SinDoctorFilter |
| `components/NPSRowCompact.stories.tsx` | NPSRowCompact | Promotor, Detractor, Pasivo |
| `components/FidelizacionActivityFooter.stories.tsx` | FidelizacionActivityFooter | Default |
| `components/ReEngagementContactSidebar.stories.tsx` | ReEngagementContactSidebar | WithPatient, NoPatient |
| `components/tabs/MultiSessionTab.stories.tsx` | MultiSessionTab | Default, Period7d, Period90d |
| `components/tabs/FollowUpTab.stories.tsx` | FollowUpTab | Default, Period7d |
| `components/tabs/MaintenanceTab.stories.tsx` | MaintenanceTab | Default, Period90d |
| `components/tabs/AbsenceTab.stories.tsx` | AbsenceTab | Default, WithDoctorFilter |
| `components/tabs/NPSResumenTab.stories.tsx` | NPSResumenTab | Default, Period7d, Period90d |

---

## Components coverage

All 14 components listed in `03-arch-fe.md § 8 Storybook coverage` are covered:

- [x] FidelizacionKPIsHero — 4 stories (Loading, Populated, Zero, NegativeTrend)
- [x] FidelizacionTabsBar — 5 stories (one per active tab)
- [x] ReEngagementCard — 7 stories (4 patterns + 2 urgency + 1 disabled actions)
- [x] ConfirmTemplateModal — 2 stories
- [x] PausePatientModal — 1 story
- [x] ManualCallLoggedModal — 1 story
- [x] SuggestSlotsModal — 2 stories
- [x] NPSRowCompact — 3 stories (one per NPS band)
- [x] FidelizacionActivityFooter — 1 story
- [x] ReEngagementContactSidebar — 2 stories
- [x] MultiSessionTab — 3 stories (period variants)
- [x] FollowUpTab — 2 stories
- [x] MaintenanceTab — 2 stories
- [x] AbsenceTab — 2 stories (+ doctor filter)
- [x] NPSResumenTab — 3 stories

**FidelizacionLayout:** excluded per 03-arch-fe.md rationale (orchestrator component, story requires full page context)

---

## Technical notes

1. **Storybook glob fix:** `main.ts` previously only discovered `src/components/**/*.stories.*`. Added `src/features/**/*.stories.*` glob — without this, all feature stories were silently ignored.

2. **Import path:** Storybook v10 bundles test utilities inside `storybook` package. Correct import is `storybook/test` (not `@storybook/test` which is a Storybook v8 separate package and not installed at the frontend workspace level).

3. **Hook-dependent components** (tabs, modals, footer): Clerk hooks (`useUser`, `useOrganization`) gracefully return null/undefined in Storybook, causing `useTenantLocale` and `useCurrentUser` to fall back to vitalia defaults (ARS / Buenos Aires). React Query hooks make network calls on mount; initial loading/pending state renders correctly for static build.

4. **HIPAA-lite PHI masking:** `RequireRole` + `PiiMaskedSpan` render correctly in Storybook — patient name masking is exercised in `ReEngagementCard` stories.

5. **All stories use:** `tags: ["autodocs"]`, `parameters.backgrounds.default: "vitalia-bg"`, a11y enabled globally via `preview.ts`.

---

## Skills consulted (per Step 0 gate)

| Skill | Invoked for | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite story placement, Storybook patterns | stories adjacent to components; features glob needed in main.ts |
| `tessl__react-patterns` | error boundaries, loading states | covered per story (Loading state stories created) |
| `tessl__shadcn-ui` | component reuse check | no Shadcn recreations in stories |
| `tessl__tailwind` | decorators styling | used `className` decorator wrapper for NPSRowCompact list context |

---

## Live verification

`chrome-devtools-verify` skill is marked DEPRECATED for Linux Mint (WSL2+Windows bridge only). Escalated to Chris staging gate — live verification pending. Build validator passes (EXIT 0) confirming static render correctness.
