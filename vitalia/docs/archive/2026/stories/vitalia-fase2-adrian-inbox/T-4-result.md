# T-4 result — FE consolidación features/inbox → features/adrian + DELETE huérfano

**State:** pushed (GREEN) · **Commits:** `f9b1b14b` (consolidación WIP) + `0a717431` (test-fix mocks) en `wip/vitalia`.

## Qué se hizo

- **Consolidación:** ~36 componentes ricos del huérfano `features/inbox/` migrados a `features/adrian/components/inbox/` (git detectó 68 renames limpios). Se conservó la versión rica al mergear con el subset parity.
- **Hooks/API/store/types migrados:** `features/adrian/{api,hooks,store,types}/` (RQ hooks consolidados con keys `['adrian','inbox',...]` vía `_keys.ts`; store extendido).
- **DELETE huérfano:** `features/inbox/` eliminado completo (24 deletions). **Zero refs** `@/features/inbox` restantes (verificado).
- **InboxPlaceholder removido:** dead-code tras ruta estática real (T-3); sacado del barrel + `SubTabContent` PLACEHOLDER_MAP (cambio aislado, no se entrelazó el refactor `SubTabHeader` de otra sesión).
- **Cross-feature:** `crm-shared/api/use-conversation-detail.ts` re-apunta al tipo `ConversationDetail` nuevo.
- **Test-fix (0a717431):** 7 tests migrados perdieron sus mocks (`useTenantLocale`/Clerk) → restaurados con el patrón canónico de la suite (`vi.mock("@/hooks/useTenantLocale", ...)`). 222→259 green.

## Gates (hub, GREEN)

- `tsc --noEmit`: **0 errores**
- `eslint src/features/adrian`: **clean**
- `vitest src/features/adrian`: **259/259** (33 files)
- arch fitness `src/__tests__/architecture/`: **171/171** (incl. PLACEHOLDER_MAP === RIBBON_SUBTABS − SHIPPED_STATIC_SUBTABS, no-orphan, no-cross-brand-mirror)
- jscpd: sin duplicación (dos sets de tipos ya no coexisten)

## Notas de integración (single-hub)

El builder corrió en worktree aislado off-main y stalleó 2× (consolidación grande + debug de test-mocks). El orchestrator integró: rsync del parcial al hub + un fix-builder enfocado con el patrón de mock en mano (cerró en 1 pasada). Sesiones paralelas (embudo `4c15b93e`) se intercalaron sin colisión (archivos distintos).

## Pendiente downstream

- **T-5:** ensamblar `AdrianInboxView` 3-pane real (usando InboxLayout/ConvList/Thread migrados) + piezas NEW: `ConversationModeButton` (botón "Modo conversación" = colapsa Valeria, RN-12), `ToolCallCard` (tool inline colapsable), `NudgeButton` (consume `POST /nudge` de T-2), Valeria-reacciona-básica.
- **T-6:** e2e (base.ts anti-burbuja) + visual goldens + a11y + demo-script.

## Skills consulted

| Skill / Rule | Status |
|---|---|
| frontend-expert | ✅ |
| vitalia-design-system | ✅ |
| frontend-fsd.md · anti-duplication.md · spanish-text.md | ✅ |
