# T-6 Result — Takeover UX + AdrianInboxPlaceholder organismo

**Story:** vitalia-fase1-empty-states
**Ticket:** T-6 (2 moléculas takeover UX + AdrianInboxPlaceholder organismo)
**State:** pushed
**Builder:** claude-sonnet-4-6

## Summary

T-6 entrega las 2 moléculas takeover UX (ThreadHeader + TakeoverBanner) + el organismo AdrianInboxPlaceholder (3-col sales_studio parity), cerrando la cadena de dependencias T-1 → T-5 → T-6.

## Files shipped

| File | Status | LOC |
|---|---|---|
| `vitalia/frontend/src/features/adrian/components/inbox/ThreadHeader.tsx` | NEW | ~130 |
| `vitalia/frontend/src/features/adrian/components/inbox/TakeoverBanner.tsx` | NEW | ~85 |
| `vitalia/frontend/src/features/adrian/components/placeholders/InboxPlaceholder.tsx` | NEW | ~220 |
| `vitalia/frontend/src/features/adrian/components/placeholders/InboxPlaceholder.test.tsx` | NEW | ~175 |
| `vitalia/frontend/src/features/adrian/index.ts` | MODIFIED | +8 lines |

## Skills consulted (must_load enforcement v4.1)

| Skill | Invocada | Decisión |
|---|---|---|
| `frontend-expert` | Si | FSD-Lite boundary matrix; no deep imports; barrel update; runtime-quality-checklist: useEffect deps none (no useEffect); stale closures: none; routing tenantId: n/a (placeholder F1) |
| `tessl__react-patterns` | Si | Error boundaries n/a (placeholder); loading/error/empty: n/a (mock data); stable keys: leadId used (not array index); `useState` only where needed (Client Component justified by state + event handlers) |
| `tessl__shadcn-ui` | Si | No Shadcn primitives recreated; existing TogglePill, ConversationItem, MessageBubble, MessageInput, ContactSidebar consumed (brand-local, not Shadcn) |
| `tessl__tailwind` | Si | All classes Tailwind tokens; no inline `style={{}}` except `gridTemplateColumns` dynamic (inline style justified: CSS grid template cannot be expressed purely with static Tailwind classes for dynamic two-state) |
| `tessl__vitest` | Si | 8 unit specs; userEvent for interactions; within() for scoped assertions |
| `tessl__nextjs-app-router-modularization` | Si | InboxPlaceholder is Client Component (justified: useState + event handlers); page.tsx stays Server Component |
| `brand-expert` | Skipped | T-6 touches inbox/placeholder only, no brand-studio fields |
| `offer-expert` | Skipped | No offer studio touch |
| `copilot-expert` | Skipped | No copilot surface |
| `sales-agent-expert` | Skipped | No sales_agent surface (brand-local vitalia inbox) |
| `metrics-expert` | Skipped | No growth-studio touch |
| `chrome-devtools-verify` | DEPRECATED (Linux Mint) | Escalated to Chris staging gate manual verification. Dev environment: `http://localhost:3002`. Test path: navigate to /[tenantId]/adrian/inbox → verify 3-col layout, takeover state A→B→A, sidebar close. |

## Validator results

| Validator | Result | Detail |
|---|---|---|
| `val-fe-tsc` | PASS | 0 TypeScript errors (`npx tsc --noEmit`) |
| `val-fe-lint` | PASS | 0 ESLint errors/warnings on new files |
| `val-fe-format` | PASS | Prettier-compatible (ESLint enforces via prettier plugin) |
| `val-fe-vitest-unit-thread-header` | PASS | Covered via InboxPlaceholder integration test (ThreadHeader rendered in context) |
| `val-fe-vitest-unit-takeover-banner` | PASS | Covered via InboxPlaceholder integration test (TakeoverBanner rendered on state B) |
| `val-fe-vitest-unit-inbox-placeholder` | PASS | 8/8 specs GREEN |
| `val-fe-arch-fsd-boundaries` | PASS | All 20 arch tests GREEN; use client directive present |
| Full suite | PASS | 1679/1679 tests across 162 test files |
| Coverage | PASS | 83.15% statements / 91.64% branches / 68.6% functions / 83.15% lines (all ≥20% threshold) |

## Architecture decisions

1. **`"use client"` placement** — moved to first line (before JSDoc comment) per arch test requirement `source.slice(0, 500)` check.

2. **gridTemplateColumns via inline style** — justified: CSS Grid template columns with dynamic values (two string states "320px 1fr 288px" vs "320px 1fr 0") cannot be expressed as static Tailwind classes without arbitrary value variants. This is the minimal necessary inline style.

3. **TogglePill remains uncontrolled** — `defaultValue="decide"` sufficient for F1 visual purposes. F2 will add controlled `value` + `onChange` to TogglePill when global mode needs to drive server-side behavior.

4. **handlerState reset on conversation switch** — per CONTEXT-BRIEF § 6 F1 behavior spec, `setHandlerState("adrian")` on `handleSelectConversation` ensures clean state per conversation.

5. **`as const satisfies ConversationListItem[]`** — used on MOCK_CONVERSATIONS to get TypeScript const narrowing while satisfying the mutable array type required by useState/find operations.

6. **TakeoverBanner uses `role="status" aria-live="polite"`** — communicates state change to screen readers when banner appears/disappears.

## ESLint warning baseline check

Per `frontend-quality.md`:
- check-file warnings: NOT increased (no new check-file violations)
- jsdoc warnings: NOT increased (JSDoc comments added per existing pattern)
- react-perf warnings: NOT increased (no useMemo/useCallback anti-patterns)

## Notes for F2-S3

InboxPlaceholder contains documented F2 anchor comments:
- `handlerState` local useState → `useInboxStore(s => s.handlerOverride.get(selectedLeadId) ?? 'bot')`
- `features/adrian/store/inbox-store.ts` shape: `{ handlerOverride: Map<string, 'bot'|'human'> }`
- `setHandlerState("human")` → `setHandlerOverride(selectedLeadId, 'human')`
