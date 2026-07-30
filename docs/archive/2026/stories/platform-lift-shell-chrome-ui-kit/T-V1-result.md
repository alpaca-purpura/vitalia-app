# T-V1 Result — Vitalia re-wire: ShellLayout del kit montado

**Story:** platform-lift-shell-chrome-ui-kit · **Ticket:** T-V1 · **Branch:** wip/vitalia · **Date:** 2026-06-11
**Commits:** `15b6ee79` (bloque 1 stores) · `065dd907` (bloque 2 wire+layout+@source+kit alias)

## Ejecución

Builder murió ~145 tool-uses bloqueado por gate G1 (header `// cap:` → cap inexistente, HARD vitalia). Resolución PM: story es `cap_change_type: fix` + `cap_target: null` (precedente hardening) → headers cap REMOVIDOS de archivos vitalia nuevos (advisory 5c acepta archivos sin header). Orchestrator cerró: gates + lockfile container + commits.

## Deliverables

1. **shell-store.ts dual:** `useShellStoreKit` = `createShellStore({storageKey:'vitalia-shell-state', version:1, migrate})` — key canónica CONSERVADA (SC-6). Store legacy → key `vitalia-shell-state-legacy` (transición; muere en T-V2 con el chrome local).
2. **ShellLayoutWire.tsx** (`(shell-organism)/_components/`): bridge client que monta `ShellLayout` de `@luana/ui-kit` con props brand: supervisorName='Valeria', AGENT_CATALOG array, ribbonOrder, subTabsByAgent, getAgentClasses (switch JIT-static), useShellStoreKit, useChatStore (cast — kit no llama .persist), splitGroupId='vitalia-shell-split-agentic' (CONSERVADO), logoSlot/rightClusterSlot (LogoMark/ThemeToggle/TenantSwitcher quedan brand), **testIds legacy** (`valeria-sidebar`, `valeria-collapsed-strip`, `valeria-chat`, etc. — contrato e2e intacto).
3. **layout.tsx:** monta ShellLayoutWire (ShellOrganismLayout local queda huérfano hasta T-V2).
4. **globals.css:** `@source "../../../core/@luana/ui-kit/src/organism/shell"` — JIT escanea el kit (clases @[24rem]/grid-cols-[minmax]).
5. **Mocks movidos** a `stores/` (pre-borrado T-V2). chat-store re-pointed.
6. **Kit index.ts:** colisión `EmptyState`/`EmptyStateInline` con `./layout` → alias `Shell*` en barrel global (additivo).

## Gates

| Gate | Result |
|---|---|
| tsc vitalia | 0 errors |
| eslint (stores + _components) | 0 errors |
| vitest vitalia FULL | **2485/2485 PASS** (233 files) |
| storageKey/splitGroupId conservados | ✅ grep ok |
| Live smoke FE :3002 | ✅ `/mateo/agenda` GET/POST 200 vía shell del KIT (tras fix lockfile container) |

## Hallazgo operativo (symlink-war confirmado)

Container FE tenía `pnpm-lock.yaml` COPIA vieja (Jun 8, root-owned, no-bind) → `Module not found: @tanstack/react-virtual` al importar barrel global del kit. Fix: `docker cp` lockfile actual + `pnpm install --frozen-lockfile` dentro del container. Documentar en runbook (CIL L1 ya trackea symlink-war).

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When |
|---|---|---|
| frontend-expert + vitalia-design-system | ✅ (builder) | wire props + SHELL-DESIGN-CONTRACT |
| T-K2-result § Nota testIds | ✅ | mapa legacy inyectado |
| checkpoint § Aprendizajes (symlink-war) | ✅ (orchestrator) | fix container lockfile |
