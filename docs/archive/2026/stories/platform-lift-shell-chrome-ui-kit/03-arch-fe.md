---
story_id: platform-lift-shell-chrome-ui-kit
brand: platform
surface: FE
parent: 03-arch.md
---

# 03-arch-fe — Lift del chrome shell-organism (detalle FE, única superficie)

> Detalle del corte file-by-file + el contrato de re-wire + nicolify convergencia. El consolidado (decisiones A/B/C/D, API TS, store, ssr:false, CONN) vive en `03-arch.md`. Acá: el mapa de archivos exacto que cada ticket ejecuta.

## File map — KIT (NEW en `core/@luana/ui-kit/src/organism/shell/`)

> Destino: sub-dir nuevo `src/organism/shell/` + barrel `organism/shell/index.ts` re-exportado desde `src/index.ts` (precedente: `src/layout/` + `src/archetypes/` ya tienen barrels). Tests del kit en `core/@luana/ui-kit/src/organism/shell/__tests__/` (o `tests/` — seguir el patrón existente del kit).

| Archivo kit (NEW) | Origen vitalia | Parametrización (brand → prop) |
|---|---|---|
| `ShellLayout.tsx` | `ShellOrganismLayout.tsx` | `skeletonSlot`, todas las props de `ShellLayoutProps`; wrapper `dynamic({ssr:false})` |
| `ShellLayoutClient.tsx` | `ShellOrganismLayoutClient.tsx` | `splitGroupId`, `useShellStore` (prop), `useChatStore` (prop), `agentCatalog`, slots. **fixes v4 verbatim (RN-4)** |
| `SupervisorSidebar.tsx` | `ValeriaSidebar.tsx` | `useShellStore`/`useChatStore` (prop), `supervisorName`/`supervisorInitial`/`supervisorAvatar`, `keyboardShortcuts` cfg |
| `SupervisorCollapsedStrip.tsx` | `ValeriaCollapsedStrip.tsx` | `supervisorAvatar`/`initial`/`colorToken`, `useShellStore` (prop) |
| `SupervisorHistory.tsx` | `ValeriaHistory.tsx` | `useChatStore` (prop), `labels.history`/`newConversation` |
| `ChatPanel.tsx` | `ValeriaChat.tsx` | `useChatStore` (prop). **grid `grid-cols-[minmax(0,1fr)]`+`min-w-0`+`@container` verbatim (RN-4)** |
| `ChatHeader.tsx` | `ChatHeader.tsx` | `agentCatalog`, `useShellStore`/`useChatStore` (prop). **`@[24rem]` container query verbatim (RN-4)** |
| `ChatComposer.tsx` | `ChatComposer.tsx` | `useChatStore` (prop) |
| `ChatMessages.tsx` | `ChatMessages.tsx` | `agentCatalog`, `useChatStore` (prop) |
| `MessageBubble.tsx` | `MessageBubble.tsx` | `agentCatalog` |
| `TypingIndicator.tsx` | `TypingIndicator.tsx` | `agentCatalog` |
| `DelegateMarker.tsx` | `DelegateMarker.tsx` | `agentCatalog` |
| `StatusDot.tsx`, `TogglePill.tsx`, `EmptyStateInline.tsx`, `ChannelBadge.tsx`, `HistoryGroup.tsx`, `HistoryItem.tsx`, `EmptyState.tsx`, `PlaceholderCard.tsx` | idem | catalog/store por prop donde aplique; mayoría ya genéricos |
| `Ribbon.tsx` | `Ribbon.tsx` | `agentCatalog`, `ribbonOrder` |
| `RibbonTab.tsx` | `RibbonTab.tsx` | `agentCatalog` |
| `SubTabsBar.tsx` | `SubTabsBar.tsx` | `subTabsByAgent`, `agentCatalog` |
| `SubTab.tsx` | `SubTab.tsx` | catalog por prop |
| `SubSubTabsBar.tsx` | `SubSubTabsBar.tsx` | routing helpers por prop. **Superset del caso nicolify (SubSubTab)** — ver 03-arch § Open Q2 |
| `SubTabContent.tsx` | `SubTabContent.tsx` | `subTabsByAgent`, `shippedStaticSubtabs` por prop |
| `ConfigTab.tsx` | `ConfigTab.tsx` | label por prop ("Plataforma"/"Configurar") |
| `TopBarShell.tsx` | `TopBarGlobal.tsx` | slots `logoSlot`/`rightClusterSlot`/`onBurgerClick`, `variant` |
| `AppPanelSlot.tsx` | `AppPanelSlot.tsx` | genérico (ya sin coupling) |
| `useViewportGuard.ts` | `useViewportGuard.ts` | exporta consts `VALERIA_MIN_PX`→`SUPERVISOR_MIN_PX` genérico |
| `_agent-tw-classes.ts` | `_agent-tw-classes.ts` | toma `agentCatalog` por arg (no import del catalog) |
| `create-shell-store.ts` | `stores/shell-store.ts` (machine+migrate+sanitize) | factory `createShellStore({storageKey,version,migrate})` usando `@luana/hooks/createSsrSafePersistedStore` |
| `routing.ts` | `lib/agent-catalog.ts` (helpers) | `extractAgentFromPath`/`extractSubtabFromPath`/`isValidAgent`/`isValidSubtab` — genéricos, catalog por arg |
| `types.ts` | `types.ts` + agent-catalog types | `ShellAgentDescriptor`, `ShellSubTabMeta`, `ShellStoreState`, `ShellChatStoreApi`, `ShellLayoutProps` |
| `index.ts` | — | barrel; **NO re-export react-resizable-panels `Group`/`Panel`/`Separator`** (colisión con el `Group` form del kit) |

**Kit deps a agregar (`core/@luana/ui-kit/package.json` dependencies):** `react-resizable-panels` (versión idéntica a la que usa vitalia hoy — leerla de `vitalia/frontend/package.json`, v4.11.1) + `zustand` (versión idéntica). Additivo (Decisión D).

## File map — VITALIA (re-wire + borrado + thin wrappers)

| Archivo vitalia | Acción | Detalle |
|---|---|---|
| `app/[tenantId]/(shell-organism)/layout.tsx` | MODIFY | import `ShellOrganismLayout` (local) → `ShellLayout` (`@luana/ui-kit`); montar con props brand (supervisorName='Valeria', agentCatalog=AGENT_CATALOG, ribbonOrder=AGENT_RIBBON_ORDER, subTabsByAgent=RIBBON_SUBTABS, shippedStaticSubtabs=SHIPPED_STATIC_SUBTABS, useShellStore, useChatStore, splitGroupId='vitalia-shell-split-agentic', logoSlot=<LogoMark>, rightClusterSlot=<><ThemeToggle/><TenantSwitcher/></>, skeletonSlot=<store-free header>) |
| `stores/shell-store.ts` | REPLACE (thin) | `export const useShellStore = createShellStore({ storageKey: 'vitalia-shell-state', version: 1, migrate: migrateShellState })` — conserva la key (SC-6). El `migrateShellState` (v0 collapsed/rail/full) se mantiene local o se pasa al factory. |
| `components/shared/shell-organism/**` (chrome lifteado) | DELETE | TODOS los archivos de la tabla "KIT" + sus `.test.tsx` (RN-3). Quedan SOLO: `LogoMark.tsx`(+test), `ThemeToggle.tsx`(+test), `TenantSwitcher.tsx`/`TenantBadge.tsx`/`TenantOption.tsx`/`TenantStoreBootstrap.tsx`(+tests), `AddClinicPlaceholderModal.tsx`, `types.ts` (solo tipos Tenant). |
| `lib/agent-catalog.ts` | KEEP | AGENT_CATALOG/ORDER/SUBTABS/SHIPPED_STATIC quedan (brand data). Los helpers `extractAgentFromPath` etc. ahora viven en el kit → vitalia los importa de `@luana/ui-kit` (re-point) o mantiene wrappers thin que llaman al kit pasando AGENT_CATALOG. **Decisión:** re-point imports al kit; borrar las defs locales de los helpers (mata duplicación). Si algún call-site vitalia usa la firma vieja (sin catalog arg) → adaptar al wrapper. |
| `lib/shell-routes.ts` | KEEP | `DEFAULT_LANDING_SUBPATH` queda (brand). |
| `stores/chat-store.ts`, `_mock-*` | KEEP | mock conversacional brand. (Los `_mock-*` viven hoy en `shell-organism/` — si se borra la carpeta, MOVER `_mock-conversations.ts`/`_mock-messages.ts` a `stores/` o `lib/` brand antes de borrar el chrome.) ⚠️ ticket: mover mocks ANTES de borrar el chrome. |
| `tailwind` scan | MODIFY | agregar `@source` del kit organism (Decisión Tailwind — 03-arch § Tailwind) |
| `e2e/regression/shell-core-hardening/**`, `vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts`, `resizer-matrix.spec.ts` | KEEP (asserts) | **CERO cambio de assert** (RN-1/Bif-3). Usan `data-testid` + localStorage key `vitalia-shell-state`/`vitalia-shell-split-agentic` (conservadas). Si algún POM (`ShellLayoutPage.ts`/`ValeriaSidebarPage.ts`) importa de source path del chrome → ajustar SOLO el import (harness, no conducta). Verificar: ninguno importa source hoy (greps confirmaron testid-only). |
| `__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` | MODIFY | `KNOWN_SANCTIONED_SHELL_MIRROR` ENCOGE: remover cada símbolo lifteado (ValeriaSidebar/ValeriaChat/Ribbon/SubTabsBar/AGENT_CATALOG/useShellStore/ShellOrganismLayout/etc.) en el commit del move. Al final → allowlist vacío (o solo lo aún no convergido). Shrink-only (RN-5). |

## File map — NICOLIFY (convergencia RN-7)

| Archivo nicolify | Acción | Detalle |
|---|---|---|
| `app/[tenantId]/(shell-organism)/layout.tsx` | MODIFY | montar `ShellLayout` del kit con su catálogo (supervisorName='Luana', agentCatalog=nicolify AGENT_CATALOG [Luana sidebar + Abel/Brenda/Christian/Sara/Norvil], ribbonOrder, subTabsByAgent, useShellStore nicolify, splitGroupId='nicolify-shell-split', logoSlot/rightClusterSlot nicolify) |
| `components/shared/shell-organism/{LuanaSidebar,LuanaRail,LuanaChat,LuanaHistory,ShellModeToggle,SubSubTab,ShellOrganismLayout,ShellOrganismLayoutClient,Ribbon,RibbonTab,SubTabsBar,SubTab,SubSubTabsBar,SubTabContent,ConfigTab,TopBarGlobal,ChatComposer,ChatMessages,ChatHeader,MessageBubble,TypingIndicator,DelegateMarker,EmptyState,EmptyStateInline,HistoryGroup,HistoryItem,PlaceholderCard,AppPanelSlot,useViewportGuard,_agent-tw-classes,types}.tsx` | DELETE/RETIRE | el chrome legacy + la máquina `luanaState/LuanaRail/ShellModeToggle` se RETIRA (RN-7); se consume el kit. Quedan: `LogoMark`, `ThemeToggle`, `TenantSwitcher`(+Badge/Option), `AddAgencyPlaceholderModal`, `types.ts` (Tenant types). **N3 brand-local (`EntityWorkspaceLayout.tsx`/`EntitySubNavBar.tsx`) NO se toca acá** (ortogonal — 03-arch § Open Q1). |
| `stores/shell-store.ts` | REPLACE (thin) | `createShellStore({ storageKey:'nicolify-shell-state', version:1, migrate: migrateLuanaState })` — el `migrateLuanaState` mapea `luanaState collapsed→closed · history/full→chat`, DROP `shellMode`/`splitState` (SC-6/Bif-5). |
| `lib/agent-catalog.ts`, `lib/routing/shell-routes.ts` | KEEP | brand data nicolify; helpers re-point al kit. |
| tests legacy (`LuanaSidebar.test.tsx`, `LuanaChat.test.tsx`, `ShellOrganismLayoutClient.test.tsx`, `TopBarGlobal.test.tsx`, shell-store machine tests) | UPDATE/RETIRE | actualizar a la conducta del kit o retirar (el cambio de conducta nicolify está sancionado por la proposal — es la convergencia, NO regresión, RN-7). |
| tailwind scan | VERIFY (+@source si falta) | nicolify usa v4 auto-detect (sin `tailwind.config.ts`) → probablemente ya escanea el kit symlink; verificar JIT classes del shell con render-verify; agregar `@source` si faltan. |

## Brand-coupling matrix (evidencia que dicta el corte)

> Greps ejecutados 2026-06-11. Toda pieza con coupling a `useChatStore`/`useShellStore`/`AGENT_CATALOG` se liftea con esos por **prop/inyección**, no por import.

| Componente | coupling detectado | estrategia |
|---|---|---|
| ChatMessages, ChatHeader, MessageBubble, TypingIndicator, DelegateMarker, Ribbon, RibbonTab, SubTabsBar, SubTab, SubSubTabsBar, _agent-tw-classes | `AGENT_CATALOG` / `@/lib/agent-catalog` | `agentCatalog` por prop/arg |
| ChatMessages, ChatComposer, ChatHeader, ValeriaHistory, ChatPanel(ValeriaChat) | `@/stores/chat-store` (`useChatStore`) | `useChatStore` por prop |
| ChatHeader, ValeriaCollapsedStrip, ValeriaSidebar, TopBarGlobal | `@/stores/shell-store` (`useShellStore`) | `useShellStore` por prop |
| AppPanelSlot, ValeriaChat(grid), StatusDot, TogglePill, EmptyState, EmptyStateInline, PlaceholderCard, LogoMark, ThemeToggle, ChannelBadge, HistoryItem | sin coupling | lift directo (LogoMark/ThemeToggle/ChannelBadge → revaluar: ThemeToggle/ChannelBadge genéricos OK kit; LogoMark = BRAND queda, es el logo de la marca) |
| TenantSwitcher/TenantBadge/TenantOption/TenantStoreBootstrap | `@/stores/tenant-store` + IAM + Clerk | **BRAND queda** (inyectado por `rightClusterSlot`) |

## Test surfaces (TDD RED-first)

- **Kit vitest:** migrar los `.test.tsx` de vitalia re-parametrizados a props genéricas + grep gate brand-token. `createShellStore` máquina A/B/C + migrate genérico + no-clobber.
- **Vitalia:** suite existente como contrato (cero assert nuevo). e2e 68/68 + resizer 7/7 + arch (mirror allowlist encogida + clerk-org). Borrar vitest de componentes movidos.
- **Nicolify:** tsc + vitest (tests legacy actualizados/retirados) + arch + render-verify.
- **NO BE tests** (sin surface BE).
- **axe wcag2aa** preservado (los tests a11y del chrome corren contra el kit consumido).
