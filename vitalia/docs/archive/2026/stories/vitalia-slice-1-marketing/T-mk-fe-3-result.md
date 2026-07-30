# T-mk-fe-3 Result — LucasStageRecommendationsCard + DetailModal + ApprovalModal + UndoChip + RejectModal

> Brand: vitalia
> Ticket: T-mk-fe-3 (Wave 5)
> Commit: 205e8d9
> Branch: wip/vitalia (pushed origin)
> Builder: claude-sonnet-4-6
> Date: 2026-05-20

## Files created (9 new)

### Test files (RED written first — TDD per tdd-mandatory.md)

| File | Tests |
|---|---|
| `vitalia/frontend/src/features/marketing/__tests__/LucasStageRecommendationsCard.test.tsx` | 5 tests |
| `vitalia/frontend/src/features/marketing/__tests__/LucasApprovalModal.test.tsx` | 5 tests |
| `vitalia/frontend/src/features/marketing/__tests__/LucasRejectModal.test.tsx` | 4 tests |
| `vitalia/frontend/src/features/marketing/__tests__/LucasUndoChip.test.tsx` | 3 tests |

### Component files (GREEN implementation)

| File | LOC | Description |
|---|---|---|
| `vitalia/frontend/src/features/marketing/components/LucasStageRecommendationsCard.tsx` | ~220 | Top-3 sticky + expand + modal routing |
| `vitalia/frontend/src/features/marketing/components/LucasRecommendationDetailModal.tsx` | ~210 | Two-tab detail view + RBAC approve gate |
| `vitalia/frontend/src/features/marketing/components/LucasApprovalModal.tsx` | ~175 | Confirm + receipt phases + 5-min undo store write |
| `vitalia/frontend/src/features/marketing/components/LucasUndoChip.tsx` | ~95 | Countdown chip reading marketing-store |
| `vitalia/frontend/src/features/marketing/components/LucasRejectModal.tsx` | ~215 | Zod-validated reason enum (native React state) |

## Files modified (2)

| File | Change |
|---|---|
| `vitalia/frontend/src/features/marketing/components/StageDispatcher.tsx` | Replaced placeholder slot with `<LucasStageRecommendationsCard stage={stage} />` |
| `vitalia/frontend/src/features/marketing/index.ts` | Appended 10 named exports for Lucas components + prop types |

## Quality gate results

| Gate | Result | Detail |
|---|---|---|
| `tsc --noEmit` | PASS | 0 errors |
| ESLint `src/` | PASS | 0 errors |
| Vitest run | PASS | 658/658 tests (88 test files) |
| Architecture fitness | PASS | 42/42 tests |
| Coverage | PASS | 47.84% (threshold 20%) |
| ESLint warnings | PASS | No new baseline growth |

## Gherkin coverage mapping

### SC-MK-01 — Lucas approve happy path

| Scenario step | Test path | Status |
|---|---|---|
| Renders top 3 recommendations inline | `__tests__/LucasStageRecommendationsCard.test.tsx::test_renders_top_3_cards` | PASS |
| Approve button calls mutation with Idempotency-Key | `__tests__/LucasApprovalModal.test.tsx::test_approve_invokes_mutation_with_idempotency_key` | PASS |
| Post-approve shows undo chip with 5-min timer | `__tests__/LucasApprovalModal.test.tsx::test_post_approve_shows_undo_chip_5min` | PASS |

### SC-MK-04 — RBAC denied UI

| Scenario step | Test path | Status |
|---|---|---|
| `recepcion` role sees disabled approve button | `__tests__/LucasApprovalModal.test.tsx::test_role_recepcion_disables_approve_button_with_tooltip` | PASS |

### Additional coverage (not in gherkin_coverage field but covered)

| Behavior | Test path | Status |
|---|---|---|
| Reject modal requires reason (Zod validation) | `__tests__/LucasRejectModal.test.tsx::test_submit_without_reason_shows_error` | PASS |
| Reject with valid reason calls mutation | `__tests__/LucasRejectModal.test.tsx::test_submit_with_valid_reason_calls_mutation` | PASS |
| Cancel buttons call onClose | Multiple tests across all modal tests | PASS |
| ESC key closes modals | `__tests__/LucasApprovalModal.test.tsx::test_esc_key_closes_modal` | PASS |
| Undo chip hidden when no active timer | `__tests__/LucasUndoChip.test.tsx::test_hidden_when_no_timer` | PASS |
| Undo chip shows countdown + button | `__tests__/LucasUndoChip.test.tsx::test_shows_undo_button_when_timer_active` | PASS |
| Undo button calls mutation | `__tests__/LucasUndoChip.test.tsx::test_undo_button_calls_mutation` | PASS |
| Loading skeleton state | `__tests__/LucasStageRecommendationsCard.test.tsx::test_loading_state` | PASS |
| Empty state renders message | `__tests__/LucasStageRecommendationsCard.test.tsx::test_empty_state` | PASS |
| "Ver todas" expand shows all recs | `__tests__/LucasStageRecommendationsCard.test.tsx::test_expand_shows_all` | PASS |
| Card click opens detail modal | `__tests__/LucasStageRecommendationsCard.test.tsx::test_card_click_opens_detail_modal` | PASS |

## Key implementation decisions

- **No react-hook-form**: not installed in vitalia frontend. `LucasRejectModal` uses native `useState` + Zod v4 `safeParse`. `result.error.issues[0]?.message` (Zod v4 API, not `errors`).
- **Hooks ordering**: `useCallback(handleUndo)` declared before conditional early return in `LucasUndoChip` — Rules of Hooks compliance.
- **HIPAA-lite dual filter**: all hooks (`useLucasRecommendations`, `useApproveRecommendation`, etc.) pass `clinicId` from `useClinicId()` + `orgId` from `useAuth()`; hooks disabled when `clinicId` is falsy. No PHI stored in URL or localStorage.
- **Idempotency-Key**: `crypto.randomUUID()` generated per `handleApprove()` call, passed via custom header in `useApproveRecommendation` mutation.
- **5-min undo timer**: `setPendingUndoTimer(rec.id, new Date(result.undoUntil).getTime())` persisted in Zustand `useMarketingStore`, consumed by `LucasUndoChip`.
- **RBAC**: `userRole` prop passed to `LucasRecommendationDetailModal` and `LucasApprovalModal`; `recepcion` role disables approve button.
- **No hardcoded colors**: all styling uses `vt-*` CSS utility classes per `frontend-quality.md`.
- **userEvent for controlled inputs**: `LucasRejectModal` radio buttons are controlled — tests use `userEvent.setup()` + `await user.click()` (not `fireEvent`) for proper React state triggering.

## Live verification status

`chrome-devtools-verify` skill is marked DEPRECATED for Linux (designed for WSL2+Windows bridge). Live verification escalated to Chris staging gate — manual verification steps:

1. `make dev-vitalia` (stack up)
2. Navigate to `http://localhost:3002/marketing?tab=attraction`
3. Verify top 3 Lucas cards render in attraction tab panel
4. Click a card → DetailModal opens with Análisis and Acción tabs
5. Click "Aprobar" → ApprovalModal warning appears → confirm → approval mutation fires + undo chip appears with 5-min countdown
6. Click "Deshacer" in chip → undo mutation fires + chip disappears
7. Open another card → click "Rechazar" → RejectModal with 5 radio options → select one → submit → mutation fires
8. Switch to `?tab=qualification` → Lucas cards show for qualification stage

## Downstream regression notes

`downstream-regression-na: brand-local FE component; no cross-brand consumers` — all new files include this marker in their JSDoc header. No engine packages modified.
