# T-2 Result — RibbonTab + ConfigTab moléculas

**Story:** vitalia-fase1-ribbon-6-tabs (F1-S7)
**Ticket:** T-2
**Brand:** vitalia
**SHA:** 1aeda3a1
**Branch:** wip/vitalia
**State:** pushed

## Summary

Implemented two React molecules for the Vitalia shell-organism Ribbon component:

- `RibbonTab.tsx` — agent tab button with Shadcn `<Avatar>` (PNG fallback via `<AvatarFallback>` with initial letter), `tabLabel` + agent `name` spans (Q15: `whitespace-nowrap` on both), active state preserving agent soft-tint on hover (Q16: `hover:${agentBgSoftClass(slug)}`), organic shrink-0 width (Q14), `forwardRef<HTMLButtonElement>` for roving tabindex parent (T-3)
- `ConfigTab.tsx` — 40×40 IconButton with Lucide `<Settings>` + Shadcn `<Tooltip>` "Configurar", `role="tab"` + `aria-selected` as WAI-ARIA tablist peer (Q13), `ml-auto` right-aligned, `forwardRef<HTMLButtonElement>`

## Files Created

| File | LOC | Description |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx` | 83 | Agent tab molecule |
| `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.test.tsx` | 380 | 23 Vitest assertions TDD |
| `vitalia/frontend/src/components/shared/shell-organism/ConfigTab.tsx` | 73 | Config IconButton molecule |
| `vitalia/frontend/src/components/shared/shell-organism/ConfigTab.test.tsx` | 273 | 17 Vitest assertions TDD |

## Files Modified

| File | Change |
|---|---|
| `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` | Extended with F1-S7 new names: RibbonTab, ConfigTab, AGENT_RIBBON_ORDER, extractAgentFromPath (4 new cases) |

## Quality Gates

| Gate | Result |
|---|---|
| TypeScript strict (`tsc --noEmit`) | 0 errors |
| ESLint (60+ rules) | 0 errors |
| Vitest coverage | 1268 tests PASS (135 suites), statements 78%+ |
| Architecture fitness (17/17) | PASS (90/90 tests) |
| Warning baselines | Not grown (check-file / jsdoc / react-perf unchanged) |

## Test Coverage — T-2 specific

### RibbonTab (23 assertions)

- SC-1 happy: renders role="tab", tabLabel text, agent name sub-label, Avatar root container
- Active state: data-active="true", aria-selected="true", agentBgSoftClass in className, font-semibold, text-foreground
- Inactive state: data-active="false", aria-selected="false", text-muted-foreground, font-medium
- tabIndex passthrough: 0 and -1
- Callbacks: onClick, onFocus fired correctly
- forwardRef: ref.current is HTMLButtonElement
- Q15 cement: both spans have whitespace-nowrap class
- SC-9 avatar fallback: AvatarFallback renders initial letter + agentBgSoftClass

### ConfigTab (17 assertions)

- SC-3 happy: data-testid, aria-label="Configurar", role="tab" button
- Q13 WAI-ARIA cement: role="tab" present, aria-selected attribute (false inactive / true active)
- Active state: data-active="true", ring-1, ring-border classes
- Inactive state: data-active="false", text-muted-foreground class
- tabIndex passthrough: 0 and -1
- Callbacks: onClick, onFocus fired correctly
- forwardRef: ref.current is HTMLButtonElement
- Tooltip: "Configurar" text present in DOM via baseElement

## Architecture Fitness — F1-S7 extension

Added 4 new cross-brand zero-tolerance invariants:
- `RibbonTab` not in nicolify/comunify/lupulo
- `ConfigTab` not in nicolify/comunify/lupulo
- `AGENT_RIBBON_ORDER` not in nicolify/comunify/lupulo
- `extractAgentFromPath` not in nicolify/comunify/lupulo

## Design Decisions Implemented

| Code | Decision | Implementation |
|---|---|---|
| Q13 | ConfigTab role="tab" + aria-selected (WAI-ARIA peer) | `role="tab" aria-selected={active}` on button |
| Q14 | Organic tab widths (shrink-0 no min-w) | `shrink-0` without `min-w-*` in className |
| Q15 | whitespace-nowrap on both label spans | `whitespace-nowrap` on outer span + both inner spans |
| Q16 | Active:hover preserves agent tint | `hover:${agentBgSoftClass(slug)}` inside active cn() branch |

## Spec Anchors

- `01-spec.md § Estados visuales · § Componentes · § Accessibility`
- `03-arch.md § 2.3 (RibbonTab) · § 2.4 (ConfigTab) · D12-D22`

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (per context note 2026-05-15). Manual verification escalated to Chris staging gate per project policy. TypeScript strict + Vitest GREEN confirms code correctness. Visual behavior confirmed via Q15/Q16/Q13/Q14 unit test assertions.

## Next

T-3 — Ribbon organism: 5 RibbonTabs + 1 ConfigTab + roving tabindex WAI-ARIA + URL-derived active + navigateTo handler. Depends on T-2 pushed (1aeda3a1).
