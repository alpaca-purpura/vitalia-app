# Embudo ↔ Inbox Sync Architecture Fix (2026-06-11)

## Problem

When user moved a lead **stage in Embudo**, the **stage in Inbox conversation was stale** (didn't update until user manually refreshed, or waited ~10 seconds).

**Root cause:** Two separate React Query namespaces with no cross-invalidation.

| Surface | RQ Namespace | Lead.stage visibility |
|---|---|---|
| **Embudo** | `['crm','board']`, `['crm','lead',id]` | ✅ Updated immediately |
| **Inbox** | `['crm','conversation',id]` | ❌ Stale (10s polling) |

**Arch problem:** Inbox's `useConversationDetail` returned a compound object `{conversation, lead, messages, ...}` with `lead.stage` but NEVER refetched when Embudo moved the stage.

## Solution

### 1. Cross-namespace invalidation in `lead-stage-mutation.ts`

When `PATCH /crm/leads/{id}/stage` succeeds:
- **Before:** Only invalidated `['crm','board']` + `['crm','lead',id]`
- **After:** Also invalidates `['crm','conversation']` (entire Inbox namespace)

```typescript
onSuccess: (_data, vars) => {
  queryClient.invalidateQueries({ queryKey: boardKey(currentFilters) });
  queryClient.invalidateQueries({ queryKey: leadDetailKey(vars.leadId) });
  // ★ NEW: Invalidate all Inbox conversations (lead.stage changed)
  queryClient.invalidateQueries({ queryKey: ["crm", "conversation"] });
  queryClient.invalidateQueries({ queryKey: ["adrian", "inbox"] });
}
```

### 2. Reduced `staleTime` in `useConversationDetail`

**Before:** `staleTime: 10_000ms` (10 seconds polling)
**After:** `staleTime: 5_000ms` (5 seconds polling)

This ensures faster re-fetch when invalidation is triggered.

### 3. Centralized RQ Keys in `_keys.ts`

Removed duplicated key definitions from individual mutation hooks:
- Added `conversationDetailKeyForInvalidation(id)` → `["crm", "conversation", id]`
- Added `conversationsListKeyForInvalidation()` → `["crm", "conversations"]`

Updated mutations to use centralized keys:
- `use-send-message.ts`
- `use-pause-adrian.ts`
- `use-retract-message.ts`
- `use-set-mode.ts`

## Result

**Sync flow now works bidirectionally:**

```
Embudo: PATCH /stage
   ↓
lead-stage-mutation.onSuccess
   ├─ invalidate ['crm','lead',id]           → Embudo board refreshes
   ├─ invalidate ['crm','conversation']      → Inbox conversation refreshes
   └─ invalidate ['adrian','inbox']          → Inbox list refreshes

Inbox: stage in useConversationDetail updates immediately (or within 5s stale window)
```

## Testing

1. **Manual flow (dev-app):**
   - Open Inbox conversation + Embudo board side-by-side
   - Move lead stage in Embudo
   - Inbox conversation detail should show new stage within ~5s max
   - Conversation list should update immediately (invalidation)

2. **Playwright test:**
   - Add E2E scenario: drag-stage-in-embudo → check-inbox-syncs

## Architecture notes

- **No API change required** — both surfaces already consume correct endpoints
- **Conversation detail** MUST continue to include `lead.stage` (it does via `/api/v1/crm/conversations/{id}` BE response)
- **Future improvement:** Conversation response could include `leadId` to make the relationship explicit (currently implicit)
- **Cost:** No extra API calls (just React Query cache invalidation = free)

## Files changed

- `vitalia/frontend/src/features/adrian/api/lead-stage-mutation.ts` — Added cross-invalidation
- `vitalia/frontend/src/features/crm-shared/api/use-conversation-detail.ts` — Reduced staleTime
- `vitalia/frontend/src/features/adrian/api/_keys.ts` — Added centralized key factories
- `vitalia/frontend/src/features/adrian/api/use-send-message.ts` — Use centralized keys
- `vitalia/frontend/src/features/adrian/api/use-pause-adrian.ts` — Use centralized keys
- `vitalia/frontend/src/features/adrian/api/use-retract-message.ts` — Use centralized keys
- `vitalia/frontend/src/features/adrian/api/use-set-mode.ts` — Use centralized keys
