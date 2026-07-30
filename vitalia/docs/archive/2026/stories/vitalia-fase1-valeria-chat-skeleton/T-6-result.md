# T-6 Result — Integration: ValeriaChatSlot → ValeriaChat swap + arch tests

**Ticket:** T-6  
**Story:** vitalia-fase1-valeria-chat-skeleton (F1-S6)  
**Commit:** `4820bb2c`  
**Branch:** wip/vitalia  
**State:** pushed  
**Date:** 2026-05-24  

## Summary

Wired real `ValeriaChat` organism (delivered in T-5) into `ValeriaSidebar`, replacing the legacy `ValeriaChatSlot` placeholder. Arch fitness tests extended for F1-S6 components.

## Files changed

### Modified
- `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx`  
  — import line: `ValeriaChatSlot` → `ValeriaChat`  
  — JSX: 2 occurrences `<ValeriaChatSlot />` → `<ValeriaChat />` (mobile drawer + desktop)  
  — JSDoc updated  
- `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.test.tsx`  
  — 2 test assertions: `data-testid="valeria-chat-slot"` → `data-testid="valeria-chat"`  
  — test names updated, T-6 comments added  
- `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts`  
  — New F1-S6 describe block: zero-tolerance checks for `ValeriaChat`, `DelegateMarker`, `useChatStore`, `AGENT_CATALOG` across other brands  
  — Documented exclusion of generic UI names (pre-existing in nicolify)

### Created
- `vitalia/frontend/src/__tests__/architecture/test-agent-catalog-ssot.test.ts`  
  — FE-A9: no hardcoded agent hex colors outside AGENT_CATALOG SSoT  
  — FE-A10: no hardcoded agent thumbnail paths outside AGENT_CATALOG  
  — KNOWN_HARDCODES allowlist (shrink-only ratchet): `agent-catalog.ts`, `agents.ts`, `globals.css`, `agent-catalog.test.ts`, `_mock-messages.ts`

### Deleted
- `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx`
- `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.test.tsx`

## Validators (all GREEN)

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| `eslint src/` | 0 errors, 0 new warnings |
| `vitest run --coverage` | 1189/1189 PASS · coverage 75%/89%/62%/75% (≥20% all) |
| Architecture fitness (90 tests) | 90/90 PASS |
| Cross-brand mirror (16 checks) | 16/16 PASS |
| Agent catalog SSoT (3 checks) | 3/3 PASS |

## Key decisions

- `globals.css` added to KNOWN_HARDCODES: defines CSS custom properties `--agent-{slug}` using hex values as gradient tokens — this IS the CSS-layer SSoT for design tokens, analogous to `agent-catalog.ts` in TS layer.
- Generic UI component names (`ChatComposer`, `ChatHeader`, `MessageBubble`, `TypingIndicator`) excluded from cross-brand checks: nicolify has pre-existing independent implementations in `features/copilot/` and `features/closer-studio/` — these are not mirrors of vitalia's shell-organism pattern.
- `ValeriaSidebar.tsx` all other logic preserved: keyboard shortcuts, D2 auto-coupling effect, mobile drawer portal, Rail/History XOR, live region announcements.

## Gherkin coverage

- (integration) ValeriaSidebar swap ValeriaChatSlot → ValeriaChat: PASS
- (architectural) agent-catalog SSoT invariant: PASS (FE-A9 + FE-A10)
- (architectural) anti-duplication cross-brand mirror extended: PASS
- (architectural) shell-store invariant heredado F1-S5: PASS
- (cleanup) ValeriaChatSlot files deleted: PASS
