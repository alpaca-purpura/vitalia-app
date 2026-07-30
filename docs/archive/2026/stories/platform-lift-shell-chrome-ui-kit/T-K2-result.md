# T-K2 Result — Kit chrome components: port verbatim brand-agnostic

**Story:** platform-lift-shell-chrome-ui-kit · **Ticket:** T-K2 · **Branch:** wip/vitalia · **Date:** 2026-06-11
**Commits:** `41ec956d` (bloque 1 layout+supervisor+ribbon+topbar) · `63f1e56c` (bloque 2 chat panel + message atoms) · `d406ff27` (bloque 3 sub-tabs + app panel slot) · `24ef5401` (bloque 4 barrel + testid defaults neutros)

## Ejecución (3 builders + cierre orchestrator)

Ticket ejecutado con patrón continuation (builders mueren ~140 tool-uses):
- Builder #1 (~276 tool-uses): portó 17 componentes UNCOMMITTED (violó incremental-commit) y murió.
- Builder #2: murió por session-limit tras mover impl-log al path correcto.
- Builder #3 (~136 tool-uses): auditó el parcial heredado vs fuente, commiteó bloques 1-3 incrementales, completó Chat*/SubTabs*/AppPanelSlot/_agent-tw-classes, murió al cerrar bloque 3 (ya commiteado).
- Orchestrator: barrel + gates finales + neutralización de 3 defaults data-testid.

## Componentes portados (fuente vitalia/.../shell-organism/ → kit organism/shell/)

| Fuente (vitalia) | Kit | Parametrización |
|---|---|---|
| ShellOrganismLayoutClient | ShellLayoutClient | fixes v4 VERBATIM (key-remount + retry-rAF + collapsedSize=44px + push ±histPct + floor min+hist + ★ Live-fix comments); stores/splitGroupId por prop |
| ShellOrganismLayout | ShellLayout | dynamic({ssr:false}) en kit + skeletonSlot prop |
| ValeriaSidebar/CollapsedStrip/History | Supervisor{Sidebar,CollapsedStrip,History} | supervisorName/avatar/labels por prop |
| ValeriaChat | ChatPanel | grid-cols-[minmax(0,1fr)] + min-w-0 VERBATIM |
| ChatHeader | ChatHeader | @container + @[24rem] VERBATIM |
| ChatComposer/ChatMessages/MessageBubble/TypingIndicator/DelegateMarker/StatusDot/TogglePill/EmptyState(Inline)/ChannelBadge/HistoryGroup/HistoryItem/PlaceholderCard | idem | catalog/store/labels por prop |
| Ribbon/RibbonTab/SubTabsBar/SubTab/SubSubTabsBar/SubTabContent/ConfigTab | idem | agentCatalog/ribbonOrder/subTabsByAgent/routing por prop |
| TopBarGlobal | TopBarShell | slots logoSlot/rightClusterSlot/onBurgerClick (Tenant*/LogoMark quedan brand) |
| useViewportGuard/useKeyboardShortcuts/_agent-tw-classes | idem | const genéricas / catalog por arg |

## Gates (G5)

| Gate | Result |
|---|---|
| vitest kit | **169/169 PASS** (13 files — incluye 33 de T-K1) |
| tsc organism/shell | **0 errores** (kit-wide: 116 errores PRE-EXISTENTES en 10 files NO tocados por la story — jest-dom matcher types + timezone-select Intl; confirmado `git diff 87a3ae7a..HEAD` no los toca → deuda CIL L3, fuera de scope del lift) |
| grep brand-token lógica | **0** (`#01b2f8\|vitalia\|valeria\|nicolify` — solo comentarios-origen permitidos; 3 defaults data-testid `valeria-*` neutralizados a `supervisor-*` en cierre) |
| barrel sin colisión | NO re-exporta Group/Panel/Separator de react-resizable-panels ✅ |

## ⚠️ Nota CRÍTICA para T-V1 (downstream)

Defaults `data-testid` del kit son NEUTROS (`supervisor-*`). La e2e de vitalia usa los legacy (`valeria-*`). **T-V1 DEBE inyectar el mapa completo `testIds` (ShellTestIds) en el layout de vitalia** con los valores legacy exactos que la suite 68+7 espera — sin eso T-V2 falla. Verificar greps de `data-testid` en e2e/regression/shell-core-hardening/ al armar el mapa.

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When |
|---|---|---|
| frontend-expert | ✅ (builders #1/#3) | port patterns + Server/Client split |
| 03-arch.md § API contract + corte | ✅ | pre-build + spot-check continuation |
| checkpoint § Aprendizajes (v4 props-capture/grid/container-queries) | ✅ | port verbatim |
| .claude/rules/anti-duplication.md | ✅ | un solo origen, cero mirror |
