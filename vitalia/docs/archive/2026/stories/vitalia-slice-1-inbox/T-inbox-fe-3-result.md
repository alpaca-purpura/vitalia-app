# T-inbox-fe-3 — Result

## Summary

Ticket: T-inbox-fe-3 "Frontend conversation list panel + filters venta consultiva ética (SegmentedControl3Modes adjacent)"
Story: vitalia-slice-1-inbox
Commit: b9f1598
Branch: wip/vitalia
Date: 2026-05-20

## Files Delivered

### Production components (6 new files)

| File | LOC | Notes |
|---|---|---|
| `src/features/inbox/components/ConversationListPanel.tsx` | ~110 | "use client"; wires URL state ↔ React Query ↔ child components |
| `src/features/inbox/components/ConversationList.tsx` | ~100 | Server-compatible; loading skeleton + empty state + listbox |
| `src/features/inbox/components/ConversationItem.tsx` | ~120 | React.memo; 🔴 + 📎 badges; stage chip; aria-selected |
| `src/features/inbox/components/SearchInput.tsx` | ~90 | "use client"; debounce 300ms; controlled; clear button |
| `src/features/inbox/components/FilterChips.tsx` | ~230 | "use client"; single-active per dimension; collapsible advanced |
| `src/features/inbox/components/ListEmptyState.tsx` | ~80 | 4 variants; all copy from INBOX_COPY SSoT |

### Test files (4 new files, 24 new test cases)

| File | Tests | Key |
|---|---|---|
| `components/__tests__/ConversationList.test.tsx` | 10 | `test_render_with_help_needed_badge` (SC-02 gherkin) |
| `components/__tests__/FilterChips.test.tsx` | 8 | `test_single_active_per_dimension` (SC-01 gherkin) |
| `components/__tests__/SearchInput.test.tsx` | 6 | debounce 300ms + clear button + aria |
| `components/__tests__/ListEmptyState.test.tsx` | 6 | all 4 variants + onClearFilters CTA |

### Updated files (3)

- `src/__tests__/architecture/test_fsd_boundaries.test.ts` — expanded allowlist for crm-shared PRODUCER pattern (T-inbox-fe-2 pre-existing + T-inbox-fe-3 new components)
- `src/__tests__/architecture/test_no_cross_feature_imports.test.ts` — same
- `src/features/inbox/index.ts` — barrel exports for 6 new components + types

## Validators

| # | Validator | Result |
|---|---|---|
| 1 | `tsc --noEmit` | PASS — 0 errors |
| 2 | `eslint src/features/inbox/` | PASS — 0 errors |
| 3 | `vitest run src/__tests__/architecture/` | PASS — 38/38 tests |
| 4 | `vitest run src/features/inbox/` | PASS — 100/100 tests (12 files) |

## Gherkin Coverage

| Scenario | Test | Status |
|---|---|---|
| SC-01: single-active filter per dimension | `FilterChips.test.tsx::test_single_active_per_dimension` | PASS |
| SC-02: help_needed badge renders | `ConversationList.test.tsx::test_render_with_help_needed_badge` | PASS |

## Architecture Notes

- **crm-shared PRODUCER pattern**: inbox components importing from `@/features/crm-shared` (Conversation type + useConversations hook) are intentional per 03-arch-fe.md § 1. Added to arch test allowlists with justification. Pre-existing violations from T-inbox-fe-2 also backfilled.
- **Physical fork**: ConversationList/Item are vitalia-native implementations (not cross-brand import from nicolify). Per ADR-vitalia-001.
- **HIPAA-lite**: Patient names pass through as plain text at list level (preview only). Full PHI masking (PiiMaskedSpan/RequireRole) applies in ConversationThread/ContactSidebar where diagnosis/treatment data is shown.
- **Server/Client boundaries**: FilterChips + SearchInput declare `"use client"` as first line (useState). ConversationList, ListEmptyState, ConversationItem are server-compatible (no hooks). ConversationListPanel is client (React Query + URL state).

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (designed for WSL2+Windows bridge). Manual verification required at staging gate. Escalated to Chris for staging-gate sign-off per project-context § Step 4 NOTE 2026-05-15.
