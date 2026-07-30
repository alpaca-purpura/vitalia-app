# T-K2 — Kit chrome components: port VERBATIM brand-agnostic — IMPL LOG

story: platform-lift-shell-chrome-ui-kit · ticket: T-K2 · autonomous_mode: true (Chris ratified)
target: `core/@luana/ui-kit/src/organism/shell/` (THIS worktree)
source (READ-ONLY): `vitalia/frontend/src/components/shared/shell-organism/` + `lib/` + `stores/` + `hooks/`

## Skills Consulted

| Skill | Why invoked | Decision (cita) |
|---|---|---|
| `frontend-expert` (SOP + `references/runtime-quality-checklist.md`) | OBLIGATORIO toda PR FE. Port toca splitter/store/effects. | (1) **routing tenantId** → checklist §"Routing tenant prefix": kit NUNCA importa `next/navigation`; consume `onNavigate(href)` prop (T-K1 contract). Brand wrappea `useParams`. (2) **useEffect deps** → checklist §"useEffect deps": los 2 Live-fix rAF retry effects del splitter portan VERBATIM (deps sagradas, fix v4). (3) **stable keys** → mock conv `id` / ribbon `slug` / subtab `id` ya estables, preservados. (4) **mock anti-patterns** N/A: cero tests nuevos; T-K1 vitest queda verde. (5) **live verify** → kit = lib de componentes pura, NO ruta → gate real = G5 (typecheck + T-K1 test + grep brand-token); contrato e2e = data-testid de vitalia preservados EXACTOS (68+7). |
| React patterns baseline | always-on | error/loading/empty ya en átomos source; portados verbatim. Stable keys preservadas. forwardRef/displayName preservados. |
| Shadcn UI conventions | always-on | kit primitivos ya existen en `src/` (avatar/button/badge/tooltip/tabs/card/skeleton/sonner/separator/input/textarea/scroll-area). Átomos importan por path relativo `../../button`. NUNCA recrear. |
| Tailwind conventions | always-on | clases utility verbatim. `_agent-tw-classes` JIT-static (literales per-slug) = brand → kit toma `getAgentClasses` inyectada por prop. Brand-token `bg-vitalia-success` → genérico (`bg-[hsl(var(--shell-status-online,var(--primary)))]` fallback neutro). |
| Next.js Server/Client split | toca page/layout boundary | `ShellLayout` = `"use client"` + `dynamic({ssr:false})` wrapper; `ShellLayoutClient` = client. Patrón source preservado. |
| graceful-degradation | N/A | sin HTTP/SSE en kit chrome (mock store por prop). |

## Plan (technical_design)

### Design-system-first (D1)
Reusar primitivos kit existentes (`src/*.tsx`): avatar, button, badge, tooltip, tabs, card, skeleton, sonner (Toaster), separator, input, textarea, scroll-area. Resizable: `react-resizable-panels` (alias local `Group as ResizableGroup` / `Separator as ResizeSeparator` — colisión con `Group` form-field ya exportado del kit barrel + kit `./separator`). NO re-exportar primitivos resizable.

### Parametrización (NAMES only, NUNCA lógica)
- store selectors: `valeriaOpen→s.supervisorOpen`, `openValeria→s.openSupervisor`, `collapseValeria→s.collapseSupervisor`. `historyOpen/openHistory/closeHistory/toggleHistory` STAY.
- consts: `SHELL_GROUP_ID`→prop `splitGroupId` · `VALERIA_MIN_PX`→`SUPERVISOR_MIN_PX` · `VALERIA_PANEL_ID`/`APP_PANEL_ID` → consts locales genéricos (`supervisor-panel`/`app-panel`).
- `cn` `@/lib/utils`→`@luana/format/utils`.
- brand data por prop: `supervisorName` (SIN default), `supervisorInitial`, `supervisorAvatar`, `agentCatalog`, `getAgentClasses` (fn), `useShellStore`, `useChatStore`, `onNavigate`, `logoSlot`/`rightClusterSlot`/`skeletonSlot`.
- REMOVE `useStoreHydration(useTenantStore)` (brand store, no en kit).
- brand-token `bg-vitalia-success`/`bg-agent-valeria-soft` → CSS var genérica + fallback neutro.
- mocks (`_mock-*`) + `chat-store` + `agent-catalog` + `_agent-tw-classes` NO se portan (brand data) — kit los consume por prop/inyección.

### Tests
T-K1 vitest (`__tests__/create-shell-store.test.ts`, `routing.test.ts`) queda verde. Sin tests nuevos (port; verificación = G5 + e2e vitalia testids).

### Integración (CONN)
kit organism barrel LOCAL `organism/shell/index.ts` (NO global `src/index.ts`). Brand consume `@luana/ui-kit/organism/shell`. ShellLayout = punto de entrada (consumed por brand `(shell-organism)/layout.tsx` en T-K3 wiring).

### EXCLUDED (flag en result)
- `ChannelBadge` — sin uso en chrome shell core.
- `SubTabContent` — content slot, brand-specific.

## Bloques

### Block 0 — routing.ts: add extractSubSubTabFromPath
status: IN PROGRESS
