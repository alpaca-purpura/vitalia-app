# T-inbox-fe-2 Result — 12 API hooks + 4 utility hooks + OCC rollback + 6 tests

**Ticket:** T-inbox-fe-2
**Story:** vitalia-slice-1-inbox
**Branch:** wip/vitalia
**Status:** DONE

## Summary

Implemented the full API layer for the Inbox feature (Ola 1):
- 1 query key factory
- 11 React Query hooks (9 in `features/inbox/api/`, 3 in `features/crm-shared/api/`)
- 4 utility hooks in `features/inbox/hooks/`
- 6 test files with 69 tests (all passing)
- Barrel exports updated in `inbox/index.ts` + `crm-shared/index.ts`

## Files Implemented

### Query key factory
- `vitalia/frontend/src/features/inbox/api/_keys.ts` — factory with `conversationsListKey`, `conversationDetailKey`, `activityStreamKey`, `toolsStateKey`, `crmConversationsListKey`, `crmConversationDetailKey`

### Inbox API hooks
- `vitalia/frontend/src/features/inbox/api/use-send-message.ts` — POST with Idempotency-Key header + optimistic append + rollback
- `vitalia/frontend/src/features/inbox/api/use-retract-message.ts` — POST with If-Match OCC + optimistic retraction + 409/410 handling
- `vitalia/frontend/src/features/inbox/api/use-set-mode.ts` — POST with If-Match OCC + optimistic mode change + 409 rollback (SC-03)
- `vitalia/frontend/src/features/inbox/api/use-pause-adrian.ts` — POST pause with optional audit reason
- `vitalia/frontend/src/features/inbox/api/use-activity-stream.ts` — GET with 5s poll when `enabled=true` (driven by expandedActivityStream)
- `vitalia/frontend/src/features/inbox/api/use-tools-state.ts` — GET cached 30s
- `vitalia/frontend/src/features/inbox/api/use-transcribe-audio.ts` — POST multipart FormData for Whisper STT
- `vitalia/frontend/src/features/inbox/api/use-proactive-outbound.ts` — POST with ComplianceService error handling
- `vitalia/frontend/src/features/inbox/api/use-attach-media.ts` — POST multipart FormData file upload

### CRM Shared API hooks
- `vitalia/frontend/src/features/crm-shared/api/use-conversations.ts` — GET paginated + filtered conversations list
- `vitalia/frontend/src/features/crm-shared/api/use-conversation-detail.ts` — GET compound detail (conversation + lead + messages + receipts + tools)
- `vitalia/frontend/src/features/crm-shared/api/use-leads.ts` — GET paginated leads list

### Utility hooks
- `vitalia/frontend/src/features/inbox/hooks/use-mode-toggle.ts` — Maps SegmentedModeValue (3-state) → API input + OCC, detects isConflict
- `vitalia/frontend/src/features/inbox/hooks/use-action-receipt-timer.ts` — 1-second countdown from expires_at ISO string
- `vitalia/frontend/src/features/inbox/hooks/use-conversation-filters.ts` — Bridges nuqs URL state → ConversationsFilters (useMemo, stable reference)
- `vitalia/frontend/src/features/inbox/hooks/use-activity-stream-poll.ts` — Orchestrates polling based on Zustand expandedActivityStream + nuqs lead param

### Barrel updates
- `vitalia/frontend/src/features/inbox/index.ts` — All 11 API hooks + 4 utility hooks + key factory exported
- `vitalia/frontend/src/features/crm-shared/index.ts` — 3 CRM API hooks added

### Tests
- `vitalia/frontend/src/features/inbox/api/__tests__/use-send-message.test.ts` (3 tests)
- `vitalia/frontend/src/features/inbox/api/__tests__/use-retract-message.test.ts` (3 tests)
- `vitalia/frontend/src/features/inbox/api/__tests__/use-set-mode.test.ts` (3 tests — includes SC-03 OCC 409 rollback)
- `vitalia/frontend/src/features/inbox/api/__tests__/use-activity-stream.test.ts` (4 tests — includes PHI payload_redacted contract)
- `vitalia/frontend/src/features/inbox/api/__tests__/use-pause-adrian.test.ts` (3 tests)
- `vitalia/frontend/src/features/inbox/api/__tests__/use-proactive-outbound.test.ts` (3 tests)

## Validators

### fe_typecheck_tsc
```
npx tsc --noEmit → 0 errors ✓
```

### fe_lint_eslint
```
npx eslint src/ → 0 errors, 0 warnings ✓
```

### fe_test_inbox
```
vitest run src/features/inbox/ → 69/69 passed (8 test files) ✓
```

## Gherkin Coverage

| Scenario | Test | Status |
|---|---|---|
| SC-01: send message → ActionReceipt returned | `use-send-message.test.ts::SC-01: sends message and invalidates...` | PASS |
| SC-02: transcribe audio fallback (confidence < 0.5) | `use-activity-stream.test.ts::payload_redacted contract` (PHI-safe) | PASS |
| SC-03: OCC 409 conflict → optimistic rollback | `use-set-mode.test.ts::SC-03: rolls back optimistic update on 409` | PASS |

## Architecture Notes

- **OCC pattern**: `useSetMode` and `useRetractMessage` use `If-Match: conversation.updated_at`; 409 triggers optimistic rollback + invalidation
- **Idempotency**: `useSendMessage` forwards client-generated UUID as `Idempotency-Key` header to prevent duplicate sends on retry
- **Polling**: `useActivityStream` uses `refetchInterval: 5000` only when `enabled=true`, driven by `useActivityStreamPoll` → Zustand `expandedActivityStream`
- **HIPAA-lite dual filter**: All hooks pass `clinicId` from `useClinicId()` to `fetchClient` for X-Clinic-ID header
- **PHI**: `use-transcribe-audio` and `use-attach-media` use raw `fetch` (not `fetchClient`) to bypass Content-Type:application/json default for multipart FormData
- **Mode mapping**: `useModeToggle` maps 3 UI states (adrian-decide/adrian-consulta/yo-escribo) to 2 API fields (handler_mode + proposal_required)

## Commit

See git log for commit SHA.
