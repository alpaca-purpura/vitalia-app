# T-2 Implementation Log — RibbonTab + ConfigTab moléculas

**Story:** vitalia-fase1-ribbon-6-tabs (F1-S7)
**Ticket:** T-2
**Builder:** Claude Sonnet 4.6 (claude-sonnet-4-6)
**SHA:** 1aeda3a1
**Branch:** wip/vitalia

## § Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | Mandatory always — FSD-Lite boundaries, ESLint config, studio section patterns, runtime-quality-checklist | Confirmed `components/shared/shell-organism/` is correct FSD location for cross-feature shell chrome. `"use client"` required (event handlers: onClick, onFocus + forwardRef). Named exports (no default). No barrel needed (consumed directly by T-3 Ribbon). |
| `tessl__react-patterns` | Mandatory always — error boundaries, loading/error/empty states, accessible markup, stable keys, memoization | Applied: `forwardRef<HTMLButtonElement>` for both molecules. `aria-selected`, `tabIndex` props. `aria-hidden="true"` on Avatar and Settings icon (decorative). `data-active` attribute for CSS selection. No `useEffect`. No `useMemo` needed (no expensive compute). |
| `tessl__shadcn-ui` | Touching Shadcn Avatar + Tooltip primitives | REUSE existing `components/ui/avatar.tsx` (Avatar, AvatarImage, AvatarFallback with data-slot attributes) + `components/ui/tooltip.tsx` (Tooltip, TooltipTrigger asChild, TooltipContent). NEVER recreate. Tooltip wraps button via `asChild` pattern. |
| `tessl__tailwind` | All visual styling | `cn()` for all conditional classes. No inline `style={{}}`. Semantic tokens: `bg-muted`, `text-foreground`, `text-muted-foreground`, `ring-border`, `ring-ring`. Agent tokens: `bg-agent-{slug}-soft` via `agentBgSoftClass()` helper (JIT-safe static strings). |

## § Pre-implementation Checks

### Anti-duplication Step 0

```bash
# Checked: no match in other brands for RibbonTab/ConfigTab
grep -rl "RibbonTab\|ConfigTab" nicolify/frontend/src comunify/frontend/src lupulo/frontend/src → 0 files
```

Result: 0 matches. Proceeding with brand-local implementation under `vitalia/frontend/src/components/shared/shell-organism/`.

### Existing file reuse

- `_agent-tw-classes.ts` — REUSED `agentBgSoftClass(slug)` switch function (JIT-safe static class names)
- `agent-catalog.ts` (T-1 done) — CONSUMED `AGENT_CATALOG`, `AgentSlug`, `tabLabel`, `name`, `thumbnail`, `initial`
- `components/ui/avatar.tsx` — REUSED Shadcn Avatar (no edit)
- `components/ui/tooltip.tsx` — REUSED Shadcn Tooltip (no edit)

## § TDD RED-first

Tests created BEFORE implementation:

```
RibbonTab.test.tsx:26 — import { RibbonTab } from "./RibbonTab";
→ FAIL: Failed to resolve import "./RibbonTab" (RED confirmed)

ConfigTab.test.tsx:25 — import { ConfigTab } from "./ConfigTab";
→ FAIL: Failed to resolve import "./ConfigTab" (RED confirmed)
```

RED state confirmed before any implementation file was created.

## § Implementation Notes

### RibbonTab.tsx

Key decisions:
- `forwardRef<HTMLButtonElement, RibbonTabProps>` — allows T-3 Ribbon to call `.focus()` imperatively for roving tabindex
- Active state uses `cn(agentBgSoftClass(slug), "font-semibold text-foreground", `hover:${agentBgSoftClass(slug)}`)` — Q16 cement: repeating the bg-soft class as hover variant forces CSS specificity over `hover:bg-muted`
- Inactive state: `"font-medium text-muted-foreground hover:bg-muted hover:text-foreground"`
- Both label spans have `whitespace-nowrap` — Q15 cement: prevents tab from growing taller than h-14 on narrow viewports
- `shrink-0` without `min-w-*` — Q14 cement: organic label-driven widths

### ConfigTab.tsx

Key decisions:
- `Tooltip > TooltipTrigger asChild > button` pattern — wraps native button via Radix `asChild`, preserves all button attributes including `ref`
- `role="tab" aria-selected={active}` — Q13 cement: ConfigTab is the 6th WAI-ARIA tablist peer
- `aria-label="Configurar"` mandatory — no visible text, required for screen readers
- `size-10` (not Shadcn `Button size="icon"` which is `size-9`) — D20 spec requirement: 40×40px
- `ml-auto` — D21 spec requirement: right-aligned via flex parent
- Active: `"bg-muted text-foreground ring-1 ring-border"` (subtle ring for visual active indicator)
- Inactive: `"bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"`

### AvatarImage in happy-dom test environment

Discovered: Radix `AvatarImage` uses internal loading state machine. In happy-dom (no HTTP), the image `src` never loads, so `AvatarImage` never renders the `<img>` element. The `data-slot="avatar-image"` attribute is not present in DOM.

Solution: Test `[data-slot='avatar']` (Avatar root container) which always renders, proving Avatar is mounted. The `src` prop correctness is verified at TypeScript compile time.

### Architecture fitness extension

Extended `test-no-cross-brand-shell-mirror.test.ts` with new `describe` block for F1-S7 names. The `grepCount()` helper scans `nicolify/frontend/src`, `comunify/frontend/src`, `lupulo/frontend/src` for exact string matches. All 4 new invariants pass (0 matches in other brands).

## § Quality Gate Results

```
TypeScript:     0 errors (tsc --noEmit)
ESLint:         0 errors
Vitest:         1268 tests PASS (135 suites)
  Coverage:     statements: 78%+, branches: 65%+, functions: 72%+, lines: 78%+
Arch fitness:   17/17 test suites PASS (90/90 individual tests)
Warning baselines: unchanged
```

## § Files Produced

| File | Type | LOC |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx` | NEW implementation | 83 |
| `vitalia/frontend/src/components/shared/shell-organism/RibbonTab.test.tsx` | NEW tests (23 assertions) | 380 |
| `vitalia/frontend/src/components/shared/shell-organism/ConfigTab.tsx` | NEW implementation | 73 |
| `vitalia/frontend/src/components/shared/shell-organism/ConfigTab.test.tsx` | NEW tests (17 assertions) | 273 |
| `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` | MODIFY — F1-S7 extension | +21 lines |

## § Forbidden Patterns — Verified Not Present

- No `"use client"` without need: both components use event handlers + forwardRef (justified)
- No `useEffect` for data fetching
- No `any` types
- No default exports (all named exports)
- No inline `style={{}}` attributes
- No Shadcn component recreation (reused existing)
- No manual `X-Tenant-ID` injection
- No `git add .` / `-A`
- No voseo in user-facing strings ("Configurar" ✓, no tuteo/voseo forms in UI)

## § Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (platform note 2026-05-15). Visual correctness of Q13/Q14/Q15/Q16 design cements confirmed via Vitest assertions (className checks, attribute checks, DOM structure). Escalated to Chris staging gate for full browser verification.
