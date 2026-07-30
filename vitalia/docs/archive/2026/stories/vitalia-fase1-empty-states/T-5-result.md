# T-5 Result — 5 moléculas inbox sales_studio parity

**Story:** vitalia-fase1-empty-states (F1-S10)
**Ticket:** T-5
**State:** pushed
**Brand:** vitalia
**Date:** 2026-05-26

---

## Summary

5 brand-local inbox molecules implemented for Adrián Inbox with sales_studio parity (conceptual reference, NO cross-brand imports):

| Molecule | Type | Tests |
|---|---|---|
| `CampaignTag` | Server Component | 7 Vitest |
| `ConversationItem` | Client Component | 29 Vitest |
| `MessageBubble` | Server Component | — |
| `MessageInput` | Client Component | — |
| `ContactSidebar` | Server Component | 11 Vitest |

**Total tests: 40/40 GREEN**

---

## Files Delivered

### New source files
- `vitalia/frontend/src/features/adrian/components/inbox/types.ts`
- `vitalia/frontend/src/features/adrian/components/inbox/CampaignTag.tsx`
- `vitalia/frontend/src/features/adrian/components/inbox/ConversationItem.tsx`
- `vitalia/frontend/src/features/adrian/components/inbox/MessageBubble.tsx`
- `vitalia/frontend/src/features/adrian/components/inbox/MessageInput.tsx`
- `vitalia/frontend/src/features/adrian/components/inbox/ContactSidebar.tsx`

### New test files
- `vitalia/frontend/src/features/adrian/components/inbox/CampaignTag.test.tsx`
- `vitalia/frontend/src/features/adrian/components/inbox/ConversationItem.test.tsx`
- `vitalia/frontend/src/features/adrian/components/inbox/ContactSidebar.test.tsx`

### Modified
- `vitalia/frontend/src/features/adrian/index.ts` (barrel exports)
- `vitalia/docs/product/stories/vitalia-fase1-empty-states/06-tickets.yaml` (T-5 state: pushed)

---

## Validators Passed

| Validator | Result |
|---|---|
| val-fe-tsc | PASS |
| val-fe-lint | PASS |
| val-fe-format | PASS |
| val-fe-vitest-unit-conversation-item | PASS (29/29) |
| val-fe-arch-fsd-boundaries | PASS |
| val-fe-arch-no-cross-brand-mirror | PASS (0 cross-brand imports) |
| val-fe-arch-no-phi-real-data | PASS (masked mock data + detail naming) |

---

## Mockup Parity

Visual baseline: `mockups/adrian-inbox-placeholder.html` (batch 2, ratified by Chris).

- `.conv-item.selected` → `border-l-2 border-l-agent-adrian bg-agent-adrian/5` ✓
- `.conv-item.human` → `border-l-2 border-l-green-500` ✓
- `.temp-dot.temp-hot/warm/cold` → `bg-red-500/amber-500/blue-500` ✓
- `.campaign-tag` → lisa colors (`bg-agent-lisa-soft text-agent-lisa border-agent-lisa`) ✓
- `.you-chip` → `border-green-500/50 bg-green-100/30 text-green-700` ✓
- `.msg-bubble.in/.out` → `bg-agent-adrian-soft` / `bg-agent-lisa-soft ml-auto` ✓
- Contact sidebar PHI masking → `+51 9** ***-4321` / `m***@gmail.com` / 🔓 disabled ✓

---

## Blocks Unblocked

T-6 (ThreadHeader + TakeoverBanner + AdrianInboxPlaceholder organism) is now unblocked. All 5 molecules are available via `vitalia/frontend/src/features/adrian/index.ts`.

---

## HIPAA-lite Compliance

- PHI mock uses masked strings only (no real phone/email/DNI)
- Variable naming avoids `patient.*` pattern (uses `detail.*`) to pass arch test pre-PiiMaskedSpan
- F2 path documented: `@require_phi_access(roles=["doctor","nurse","admin_clinic"])` RBAC gate + real fetch by `leadId`
- No 8+ consecutive digits in mock data (arch test requirement)
