# T-inbox-fe-7 — Result

**Ticket:** T-inbox-fe-7 — Frontend Storybook stories per component NEW Slice 1 + arch fitness test_no_hardcoded_strings_inbox
**Brand:** vitalia
**Branch:** wip/vitalia
**Commit SHA:** 22a1476
**Files created:** 11

## Files delivered

### Storybook stories (10)

| File | Stories | Notes |
|---|---|---|
| `src/features/inbox/components/SegmentedControl3Modes.stories.tsx` | 5 | 3 modos + pending + conflict |
| `src/features/inbox/components/FilterChips.stories.tsx` | 6 | sin filtros, canal, estado, ayuda, multimedia, múltiple |
| `src/features/inbox/components/VoiceMessagePlayer.stories.tsx` | 5 | incl. SC-02 baja confianza |
| `src/features/inbox/components/ImageAnalysisCard.stories.tsx` | 3 | stub Slice 1, nextjs appDirectory |
| `src/features/inbox/components/PauseAdrianConfirmModal.stories.tsx` | 3 | abierto, enviando, cerrado |
| `src/features/inbox/components/AdrianToolsSheet.stories.tsx` | 4 | vi.mock useToolsState, beforeEach |
| `src/features/inbox/components/AgentActivityStream.stories.tsx` | 4 | vi.mock useInboxStore + useActivityStream, unknown cast |
| `src/features/inbox/components/ActionReceiptUndoChip.stories.tsx` | 4 | SC-01 chip visible + expirado |
| `src/features/inbox/components/ProactiveOutboundModal.stories.tsx` | 4 | vi.mock useProactiveOutbound |
| `src/features/inbox/components/ContactSidebar.stories.tsx` | 4 | vi.mock useCurrentUser + PHI stubs |

### Architecture fitness test (1)

| File | Tests | Notes |
|---|---|---|
| `src/__tests__/architecture/test_no_hardcoded_strings_inbox.test.ts` | 4 | FE-A2c: copy.ts SSoT enforcement, ratchet allowlist vacío |

## Validators

| # | Gate | Result | Details |
|---|---|---|---|
| 1 | `tsc --noEmit` | PASS | 0 errors. Fix: unknown cast para Zustand UseBoundStore ↔ vi.fn |
| 2 | `eslint src/features/inbox/ src/__tests__/architecture/` | PASS | 0 errors. Fix: removed unused `beforeEach` import from vitest |
| 3 | `vitest run src/__tests__/architecture/` | PASS | 42/42 tests pass (4 nuevos en test_no_hardcoded_strings_inbox) |
| 4 | `storybook build` | PASS | Build completed successfully (asset size warnings = normal Webpack bundles) |

## Mock patterns used

- **Simple components** (SegmentedControl3Modes, FilterChips, VoiceMessagePlayer, ImageAnalysisCard, PauseAdrianConfirmModal): no external hooks — stories use controlled props + `fn()` callbacks directly.
- **Hook-dependent components**: `vi.mock()` at module level + `beforeEach` async dynamic import per story variant.
  - `AdrianToolsSheet`: `useToolsState` mocked
  - `AgentActivityStream`: `useInboxStore` (Zustand) + `useActivityStream` mocked; Zustand required `unknown as InboxStoreMock` double cast
  - `ActionReceiptUndoChip`: `useActionReceiptTimer` + `useRetractMessage` mocked
  - `ProactiveOutboundModal`: `useProactiveOutbound` mocked
  - `ContactSidebar`: `useCurrentUser` + PHI components (`PiiMaskedSpan`, `RequireRole`, `AuditedSection`) stubbed inline

## Gherkin coverage

| Scenario | Story / Test |
|---|---|
| SC-01: Countdown chip visible after agent_ai send | `ActionReceiptUndoChip.stories.tsx::ChipVisible` |
| SC-02: Low confidence transcript shows fallback | `VoiceMessagePlayer.stories.tsx::TranscriptBajaConfianza` |
| FE-A2c: inbox strings in INBOX_COPY SSoT | `test_no_hardcoded_strings_inbox.test.ts::componentes inbox no tienen copy español inline` |
