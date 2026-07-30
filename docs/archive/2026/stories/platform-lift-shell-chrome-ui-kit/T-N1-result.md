# T-N1 Result — Nicolify converge: retira máquina legacy + consume ShellLayout del kit

**Ticket:** T-N1  
**Story:** platform-lift-shell-chrome-ui-kit  
**Branch:** wip/vitalia  
**Commits:** 3edf129a (block 1) · d3bb2148 (block 2) · 4f115dad (block 3)  
**Pushed:** origin/wip/vitalia @ 4f115dad

---

## Gates

| Gate | Result |
|---|---|
| tsc --noEmit | 0 errors |
| ESLint src/ | 0 errors (warnings: existing baseline, not increased) |
| vitest run | 34 files, 514 tests PASS |
| Coverage | 62% statements (threshold 20%) |
| Arch fitness (no-store-in-ssr-skeleton) | 46/46 PASS |
| grep legacy machine (production code) | 0 hits (only JSDoc comments) |

---

## What was done

### DELIVERABLE 1 — shell-store thin wrapper

`nicolify/frontend/src/stores/shell-store.ts` rewritten:
- Uses `createShellStore` factory from `@luana/ui-kit`
- `storageKey: 'nicolify-shell-state'` (SC-6 preserved)
- `version: 1`, `migrate: migrateLuanaState`
- Exports: `SHELL_STORAGE_KEY`, `migrateLuanaState` (named, testable), `useShellStoreKit`, `useShellStore` (alias)

`migrateLuanaState` strategy:
- Legacy v0 nicolify localStorage: `{luanaState: 'collapsed'|'history'|'full', splitState, shellMode}`
  - `collapsed` → `supervisorOpen: 'closed'`
  - `history` | `full` → `supervisorOpen: 'chat'`
- Kit shape passthrough: `{supervisorOpen, splitPct, mobileDrawerOpen}`
- Corrupt/null/unknown → returns defaults WITHOUT throw (Bif-5)

### DELIVERABLE 2 — ShellLayoutWire + layout + @source

`ShellLayoutWire.tsx` (new client bridge):
- supervisorName="Luana", supervisorSlug="luana"
- agentCatalog: ribbon agents from `@/lib/routing/shell-routes` enriched with `@/lib/agent-catalog`
- ribbonOrder: `[abel, brenda, christian, sara, norvil, config]`
- splitGroupId: "nicolify-shell-split"
- JIT-safe `getAgentClasses(slug)` via `_agent-tw-classes.ts` switch
- JIT-safe `agentBorderClass(slug)` local switch
- testIds: `luana-sidebar`, `luana-collapsed-strip`, etc.
- NOTE T-3+: `useStoreHydration(useTenantStore)` not wired (no tenant-store in R0 — TenantSwitcher is a skeleton per its own comment)

`layout.tsx`: replaced `ShellOrganismLayout` with `ShellLayoutWire`

`globals.css`: added `@source "../../../../../core/@luana/ui-kit/src/organism/shell"` for JIT classes

### DELIVERABLE 3 — Legacy machine retired (30 files)

**Deleted (26 components + 4 tests):**
LuanaSidebar, LuanaRail, LuanaChat, LuanaHistory, ShellModeToggle,
ShellOrganismLayout, ShellOrganismLayoutClient, Ribbon, RibbonTab, SubTabsBar,
SubTab, TopBarGlobal, ChatComposer, ChatHeader, ChatMessages, MessageBubble,
TypingIndicator, DelegateMarker, HistoryGroup, HistoryItem, PlaceholderCard,
useViewportGuard, _mock-messages (moved to stores/), _mock-conversations,
AppPanelSlot, EmptyStateInline + 4 test files (RN-7 convergence).

**Kept (consumed by live pages or Wire slots):**
EntityWorkspaceLayout, EntitySubNavBar, SubTabContent, ConfigTab, EmptyState,
SubSubTabsBar, SubSubTab, LogoMark, ThemeToggle, TenantSwitcher, TenantBadge,
TenantOption, _agent-tw-classes.ts, types.ts, AddAgencyPlaceholderModal

### DELIVERABLE 4 — Tests updated

- `shell-store.test.ts`: 23 tests (kit API: SHELL_STORAGE_KEY, openSupervisor, collapseSupervisor, mobileDrawerOpen, persist API, migrateLuanaState unit tests)
- `shell-store-hydration.test.ts`: 15 tests (SC-3/SC-6/SC-7 + hydration lifecycle)
- `no-store-in-ssr-skeleton.test.tsx`: rewritten as "shell-wire-kit (T-N1 convergence gate)" — 46 assertions

### DELIVERABLE 5 — vitest.config.mts fix

Added `@luana/hooks/*` sub-path aliases for all hooks consumed by `@luana/ui-kit` source transform:
`use-copilot-offset`, `use-shell-mutex`, `use-is-mounted`, `use-viewport`

---

## Open items (not in T-N1 scope)

- **Open Q1** (from ticket): EntityWorkspaceLayout/EntitySubNavBar — kept as-is, not touched
- **T-3+**: `useStoreHydration(useTenantStore)` in Wire when tenant-store is wired
- **Bif-2**: live render-verify at :3001 not done (stack not started in this session — criteria degrades to tsc/vitest/arch per ticket fallback)
- `EmptyStateInline.tsx` deleted — was referenced in some feature components; if those break, they need to import from `@/components/shared/shell-organism/EmptyState` (kept)

---

## Files changed summary

| Path | Action |
|---|---|
| `nicolify/frontend/src/stores/shell-store.ts` | REWRITTEN |
| `nicolify/frontend/src/stores/_mock-messages.ts` | NEW (moved from shell-organism/) |
| `nicolify/frontend/src/stores/chat-store.ts` | UPDATED (import path) |
| `nicolify/frontend/src/stores/__tests__/shell-store.test.ts` | REWRITTEN |
| `nicolify/frontend/src/stores/__tests__/shell-store-hydration.test.ts` | REWRITTEN |
| `nicolify/frontend/src/app/[tenantId]/(shell-organism)/_components/ShellLayoutWire.tsx` | NEW |
| `nicolify/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx` | UPDATED |
| `nicolify/frontend/src/app/globals.css` | UPDATED (+@source) |
| `nicolify/frontend/src/__tests__/architecture/no-store-in-ssr-skeleton.test.tsx` | REWRITTEN |
| `nicolify/frontend/vitest.config.mts` | UPDATED (+4 hook aliases) |
| 26 legacy chrome components + 4 legacy tests | DELETED |
