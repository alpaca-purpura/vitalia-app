## 0.9.0 — 2026-06-26 (minor · `SmartDateTimePicker` prop aditiva `disablePast` · G #1 round-2 vitalia-fase2-mateo-nueva-cita)
### Changed — `SmartDateTimePicker`
- **Prop aditiva `disablePast?: boolean` (default `false`).** Con `true`: deshabilita (grisa) los días anteriores a hoy en la zona horaria del tenant (`timezone`) — calcula la medianoche browser-local de "hoy en `timezone`" vía `Intl.DateTimeFormat("en-CA", { timeZone })` y la pasa al `Calendar` existente como matcher `disabled={{ before: minDay }}` (react-day-picker). Default `false` = `disabled={undefined}` → **conducta idéntica previa, cero cambio para consumidores existentes** (open-closed). No toca `showTime`, el trigger, `onChange` ni ninguna otra conducta. Compone el mismo `Calendar` — no se creó un picker nuevo.
- Story `inputs.SmartDatetimePicker` += variante `DisablePast` · test `smart-datetime-picker.test.tsx` (días pasados deshabilitados con `disablePast` + regression-guard del default sin días deshabilitados). **tsc 0 · vitest verde (0 regresiones vs baseline 326).**
- **SEMVER 0.8.0 → 0.9.0 (minor — prop aditiva opt-in; default preserva conducta).**

## 0.8.0 — 2026-06-25 (minor · `SmartDateTimePicker` prop aditiva `showTime` date-only · comentario G #1 vitalia-fase2-mateo-nueva-cita)
### Changed — `SmartDateTimePicker`
- **Prop aditiva `showTime?: boolean` (default `true`).** Con `false`: oculta la sección de hora del popover (`TimePicker`) + formatea el trigger date-only (`dd/MM/yyyy`). Default `true` = conducta idéntica previa → **cero cambio para consumidores existentes** (open-closed). Compone el mismo `Calendar`/`Popover`/`TimePicker` que ya tenía — **NO se creó un `DatePicker` nuevo** (decisión Chris: extender, no duplicar; `Calendar` es la primitiva que `SmartDateTimePicker` compone, no su reemplazo). Uso: `<SmartDateTimePicker showTime={false}>` (campo Fecha) junto a `<TimePicker>` standalone (campo Hora).
- Story `inputs.SmartDatetimePicker` += variante date-only · test `smart-datetime-picker.test.tsx` (date-only + regression-guard del default que protege a los consumidores). **tsc 0 · vitest 326/326 (0 regresiones).**
- **SEMVER 0.7.0 → 0.8.0 (minor — prop aditiva opt-in; default preserva conducta).** SSoT: `docs/promotion-protocol/proposals/2026-06-25-ui-kit-datepicker-atom.md`.

## 0.6.0 — 2026-06-16 (minor · `CollapsibleSection` molécula colapsable de sección · lift vitalia-fase2-lisa-servicios)
### Added — `molecule/CollapsibleSection`
- **`CollapsibleSection`** — sección colapsable que compone `accordion` + `Group` (header + cuerpo colapsable). Exportada desde el barrel (`src/index.ts`) + test. SSoT: `docs/promotion-protocol/proposals/2026-06-16-collapsible-section-ui-kit.md`.
- **Reconciliación de integración (checkpoint 2026-06-16):** construido en `wip/vitalia` sobre base 0.4.1 en paralelo al lift `--radius-control` (0.5.0, nicolify). Al integrar ambos a `main` → **0.6.0** (radius-control + CollapsibleSection coexisten; `index.ts` auto-merge con ambos exports, sin conflicto).

## 0.5.0 — 2026-06-15 (minor · `--radius-control` brand-overridable control radius · RN-7 lift, nicolify-r0-design-system-adoption)
### Added — control-atom radius token
- **Control atoms (`Button`/`Input`/`Select` trigger/`Textarea`) usan `rounded-control`** en vez de `rounded-md` hardcodeado. `rounded-control` resuelve a `var(--radius-control)` con fallback al radio md de cada marca → **brand-overridable**: una marca puede hacer sus controles pill (nicolify) o mantenerlos md (vitalia/comunify/lupulo) sin tocar el kit.
- **`@luana/design-tokens` `RADIUS_NAMES`** += `"control"` (tuple: `sm·md·lg·bubble·pill·control`). Nombre compartido, valor por marca.
- **Cero cambio visual en marcas existentes (downstream-regression verificada):** cada marca mapea `borderRadius.control` + `--radius-control` a su radio `rounded-md` EXACTO previo — vitalia `calc(var(--radius) - 2px)` (8px) · comunify `0.375rem` (6px) · lupulo `var(--radius)` (6px). Solo nicolify (en su branch) opta a pill (`9999px`). tsc 0 errores + arch vitalia 187/187 + comunify 3/3 + ui-kit 270/270 + design-tokens 12/12.
- `SelectContent`/`SelectItem` radii SIN cambio (superficies de dropdown, no el control).
### Consumer requirement (coordinado en este lift)
- Una marca que consume `rounded-control` DEBE mapear `borderRadius.control` en su tailwind config (fallback `var(--radius-control, <su-md>)`). Hecho para las 4 marcas en este lift. Marca que omita token+utilidad rendiría controles sin radio → coordinar al bumpear.
- **SEMVER 0.4.1 → 0.5.0 (minor — token aditivo + opt-in pill por marca; fallback preserva md).** SSoT: `docs/promotion-protocol/proposals/2026-06-15-ui-kit-radius-control-token.md`.

## 0.4.1 — 2026-06-15 (fix · AppPanelSlot content-area flex-col · vitalia-bugfix-horarios-toolbar-sticky)
### Fixed — `organism/shell/AppPanelSlot`
- **Content-area host ahora es `flex flex-col` (no solo block scroll).** Era `<div className="flex-1 min-h-0 overflow-y-auto">`; pasa a `<div className="flex flex-col flex-1 min-h-0 overflow-y-auto">`. Las hojas que se montan con `EntityWorkspaceLayout` (N3 fijo + scroll interno propio, vía `flex-1`) necesitan un padre **flex-column** para CLAMPAR a la altura del panel; con el content-area en `block`, su `flex-1` era inerte → la hoja crecía a su contenido → el content-area scrolleaba TODO y arrastraba los toolbars de la hoja (la N3 sobrevivía solo por su `sticky`). Caso origen: vitalia Lisa › Staff › {doctor} › Horarios — el toolbar (Disponibilidad + Semana/Mes + nav-semana + Mostrar 24 horas) scrolleaba en vez de quedar fijo. Verificado LIVE en dev-app (Chrome DevTools MCP): EWL clampa, la grilla pasa a único scroller interno, toolbars FIJOS, página no scrollea. Páginas normales (hoja = un bloque alto) siguen scrolleando vía `overflow-y-auto` (no rompe el caso común).
- SSoT diagnóstico + mediciones: `vitalia/docs/product/stories/vitalia-bugfix-horarios-toolbar-sticky/T-1-LIVE-VERIFY.md`. Proposal: `docs/promotion-protocol/proposals/2026-06-15-ui-kit-app-panel-slot-flex-col.md`.
- **SEMVER 0.4.0 → 0.4.1 (patch — fix aditivo de className, cero cambio de API/contrato).** Consumidores: vitalia (verificado live), nicolify + comunify (downstream — montan el mismo `AppPanelSlot` vía `ShellLayout`).

## 0.4.0 — 2026-06-11 (platform-lift-shell-chrome-ui-kit · T-K1)
### Added — organism layer (`src/organism/shell/`)
- **`createShellStore({ storageKey, version?, migrate? })`** — generic SSR-safe Zustand store factory for the shell state machine. Brand-agnostic port of the per-brand `shell-store.ts` (vitalia/nicolify), re-parametrized to neutral naming (RN-2): `valeriaOpen → supervisorOpen`, `valeriaPct → splitPct`. CONSUMES `@luana/hooks/createSsrSafePersistedStore` (RN-8 — never reimplements SSR-safe persistence). Brand passes `storageKey` (SC-6 — conserved for e2e: `vitalia-shell-state` / `nicolify-shell-state`) + optional `migrate` for legacy shapes. Machine: A=closed (strip) · B=chat (split) · C=chat+history (additive push). `historyOpen` never persisted open (no-clobber). Default migrate validates the current shape; corrupt → fallback + warn.
- **`extractAgentFromPath` / `extractSubtabFromPath` / `isValidAgent` / `isValidSubtab`** (`routing.ts`) — generic catalog-driven routing helpers (port of vitalia `lib/agent-catalog.ts` helpers). The brand passes its agent slug-set + special tabs + sub-tab map by argument; the kit ships zero hardcoded brand slugs/labels.
- **Generic organism types** (`types.ts`) — `ShellAgentDescriptor`, `ShellSubTabMeta`, `SupervisorOpen`, `ShellPersistedState`, `ShellStoreState`, `ShellChatStoreApi`, `ShellStore`, `CreateShellStoreOptions`, `ShellLayoutProps`, `ShellLayoutLabels`, `ShellRoutingOptions`. Verbatim from `03-arch.md § API contract`. Zero brand tokens.
- Vitest: `src/organism/shell/__tests__/{create-shell-store,routing}.test.ts` (machine A/B/C transitions + migrate hook + no-clobber hydration SC-6 + generic routing helpers).
### Changed — deps + SEMVER
- New runtime deps: **`react-resizable-panels` `^4.11.1`** + **`zustand` `^5.0.5`** (exact ranges of `vitalia/frontend`) — required by the shell organism. Additive; zero breaking on existing exports.
- **SEMVER 0.3.0 → 0.4.0 (minor — additive organism layer · Decisión D).**
### Notes
- **Group-name collision (Decisión D):** the kit already exports a form `Group`. T-K1 does NOT re-export `react-resizable-panels`' `Group`/`Panel`/`Separator` from the barrel. If a resize handle must be public (later ticket), it is named `ShellResizeHandle`.
- T-K1 scope = scaffolding only (factory + types + routing). Visual components (`ShellLayout`, `SupervisorSidebar`, `Ribbon`, `ChatPanel`, …), the `ssr:false` wrapper, and the RN-4 v4 fixes (key-remount, retry-rAF, collapsedSize px, push ±histPct, grid implícito) land in T-K2.

### T-K2 — Shell organism visual components (2026-06-11)
Additive to 0.4.0 (same minor bump, no API break).
#### Added — visual components
- **`ShellLayout`** — SSR-safe wrapper (`next/dynamic ssr:false`) with brand `skeletonSlot`. Slot-based API: `logoSlot`, `rightClusterSlot`, `skeletonSlot`. Required: `useShellStore`, `useChatStore`, `splitGroupId`, `pathname`.
- **`ShellLayoutClient`** — client-side shell chrome with full resizable-panels v4 fixes SAGRADOS: key-remount, retry-rAF on collapsed, `collapsedSize` in px, push ±histPct, grid implícito clamp. RN-4: mode pill uses `@[24rem]:inline-flex` (container query, NOT viewport breakpoint).
- **`TopBarShell`** — brand-agnostic top bar (`variant: "interactive" | "skeleton"`). Slots: `logoSlot`, `rightClusterSlot`. `data-testid=topbar-global`. Hamburger `lg:hidden`.
- **`SupervisorCollapsedStrip`** — strip panel A (supervisor closed). Props: `supervisorName`, `supervisorThumbnail?`, `supervisorInitial?`, `supervisorSoftBg?`, `onOpenSupervisor`, `openLabel`, `stripTestId?`, `statusDotTestId?`.
- **`SupervisorSidebar`** — sidebar panel B/C (chat + history). Mobile drawer via `mobileDrawerOpen` store state.
- **`Ribbon` + `RibbonTab` + `ConfigTab`** — horizontal agent navigation. Prop-based catalog (`agentCatalog: ShellAgentDescriptor[]`, `ribbonOrder: string[]`). `data-testid=ribbon-tab-{slug}` (e2e-safe).
- **`SubTabsBar` + `SubTab`** — sub-section navigation bar. URL-driven active state via `usePathname`. WAI-ARIA tablist with roving tabindex + keyboard (Arrow/Home/End/Enter/Space). Props: `agentCatalog: Record<string, ShellAgentDescriptor>`, `subTabsByAgent: Record<string, readonly ShellSubTabMeta[]>`.
- **`SubSubTabsBar`** — N3-static third-level navigation (ADR-vitalia-004 v1.1). Prop-injected tabs.
- **`ChatPanel` + `ChatHeader` + `ChatMessages` + `ChatComposer`** — full chat organism. `ChatHeader` receives `agent: ShellAgentDescriptor` (NOT a string slug). Mode pill `@[24rem]:inline-flex` (RN-4 SACRED).
- **`SupervisorHistory` + `HistoryGroup` + `HistoryItem`** — conversation history panel.
- **`MessageBubble` + `TypingIndicator` + `DelegateMarker`** — chat message atoms.
- **`TogglePill`** — mode toggle (items-prop driven, no hardcoded modes).
- **`AppPanelSlot`** — app content panel placeholder slot.
- **`StatusDot`** — online/offline status indicator.
- **`EmptyState` + `EmptyStateInline` + `PlaceholderCard`** — empty states.
- **`useViewportGuard`** — exports `SUPERVISOR_MIN_PX=320` (was `VALERIA_MIN_PX` in vitalia). `DRAWER_BREAKPOINT=1024`, `INLINE_SPLIT_MIN_VIEWPORT=1280`. Store-inert (no mutations).
- **`useKeyboardShortcuts`** — keyboard shortcut hook (Ctrl+B open supervisor, etc.).
- **`resolveAgent`** — catalog lookup with fallback (`catalog.find(a => a.slug === slug) ?? fallbackSlug ?? catalog[0]`).
- **`AgentTwBundle` / `GetAgentClasses`** — type exports for brand-injected per-agent Tailwind class bundles.

#### Runtime deps added (T-K2)
- None new beyond T-K1. `react-resizable-panels ^4.11.1`, `zustand ^5.0.5` already added in T-K1.

### T-K3 — Kit barrel global + component tests (2026-06-11)
Additive to 0.4.0 (no API break).
#### Added
- **`src/index.ts` barrel**: `export * from "./organism/shell"` added. Shell organism symbols now reachable from `@luana/ui-kit` directly. Guard note in barrel: `react-resizable-panels` `Group`/`Panel`/`Separator` are NOT re-exported (shell barrel guards them; `Group` in kit root = form group component).
- **Vitest tests** — 7 new test files, 91 new tests (running total: 259 tests / 20 files):
  - `shell-layout.test.tsx` — mount + skeletonSlot render (next/dynamic mocked synchronous, ShellLayoutClient skipped).
  - `supervisor-collapsed-strip.test.tsx` — strip A: button aria-label, thumbnail, name, status dot, click, onError fallback.
  - `top-bar-shell.test.tsx` — D1 structure (header/h-12/testid), slots, hamburger, variant=interactive (store mutation + onBurgerClick override), labels override.
  - `use-viewport-guard.test.ts` — `SUPERVISOR_MIN_PX=320` exported; `VALERIA_MIN_PX`/`FULL_STATE_MIN_VIEWPORT`/`MOBILE_BREAKPOINT` NOT exported (legacy names retired).
  - `chat-header.test.tsx` — renders (SC-1: avatar/name/status/mode-pill), action buttons (nueva conv/historial toggle/colapsar), **RN-4 SACRED** `@[24rem]:inline-flex` present + `md:inline-flex` absent, avatar onError fallback.
  - `sub-tabs-bar.test.tsx` — SC-1 (nav tablist + N tabs + classes), SC-1 click (router.push / onNavigate), SC-2 (agent change), SC-3 (URL-derived active), SC-4 (invalid agent → null), SC-5 (invalid subtab → all inactive), SC-8 (roving tabindex + keyboard), SC-9 (aria-label), defensive (null params / empty params).
  - `toggle-pill.test.tsx` — renders, items, defaultValue active, 3-mode, Spanish neutro check.
- **Bugfix: `routing.ts` `segmentsOf()` + `extractAgentFromPath()` / `extractSubtabFromPath()` / `extractSubSubTabFromPath()`** now accept `string | null | undefined` pathname (guards `!pathname → []`). Previously crashed when `usePathname()` returned `null` in test/SSR context.

#### Migration notes (vitalia → @luana/ui-kit 0.4.0)
Brands consuming the kit shell must adapt:
1. Replace `import ... from "~/components/shared/shell-organism/..."` with `import ... from "@luana/ui-kit"`.
2. Replace `shell-store.ts` singleton with `createShellStore({ storageKey: "brand-shell-state", version: 1 })`.
3. Provide `getAgentClasses: (slug: string) => AgentClassBundle` (brand-side JIT-static literal class bundle — stays brand-side, never in kit).
4. `ChatHeader` now takes `agent: ShellAgentDescriptor` (full descriptor, not string slug).
5. `SubTabsBar` now takes `agentCatalog: Record<string, ShellAgentDescriptor>` + `subTabsByAgent: Record<string, readonly ShellSubTabMeta[]>` (no hardcoded `RIBBON_SUBTABS`).
6. Remove `VALERIA_MIN_PX` / `valeriaOpen` / `collapseValeria` references → use `SUPERVISOR_MIN_PX` / `supervisorOpen` / `collapseSupervisor`.

## 0.3.0 — 2026-06-08 (core-ds-foundation)
### Added
- Layout-primitives: PageContainer · PageContentStack · PageHeader · PageSection · Toolbar · FilterBar · EmptyState · ErrorState · ListPageSkeleton · FormPageSkeleton · Pagination · DetailLayout · FormLayout.
- Entity components: EntityWorkspaceLayout + EntitySubNavBar (lift nicolify, full-bleed N3 ribbon, store-free skeleton) · EntityInfoCard + Skeleton + Empty (lift vitalia StaffCard) · EntityPicker (net-new: searchFn-prop, debounced + cursor-paginated + @tanstack/react-virtual windowed).
- Autosave/Group: FloatingAutosaveIndicator + Group/GroupHeader (lifts).
- Page archetypes: ListPageScaffold · DetailPageScaffold · FormPageScaffold · DashboardPageScaffold.
### Changed
- Atoms dialog/sheet/alert-dialog/detail-panel no longer hard-couple to a consuming app's copilot store (via @luana/hooks use-copilot-offset decouple) → ui-kit now consumable cross-brand.

# @luana/ui-kit Changelog

## [0.2.0] — 2026-05-30

### Added (T-2 build-autosave-primitive-luana)

- **`AutosaveBadge`** component — autosave lifecycle status badge (ADR-012).
  - Props: `{ status: AutosaveStatus; savedAt?: Date | null; labels?: Partial<Record<AutosaveStatus, string>> }`
  - Composes the existing `Badge`/`badge.tsx` design system primitives.
  - `aria-live="polite"` for idle/dirty/saving/saved; `aria-live="assertive"` for error.
  - `role="status"` + `aria-atomic="true"` for screen reader support.
  - Icon + text on every non-idle state (never color alone — WCAG 1.4.1).
  - Contrast AA ≥4.5:1: uses `emerald-700` (5.49:1) for saved state, NOT vitalia's prior `emerald-600` (3.65:1 — known a11y bug not reproduced here).
  - `data-state={status}` attribute for test selectors.
  - Default labels Spanish neutro LatAm (no voseo): idle "" / dirty "Sin guardar" / saving "Guardando…" / saved "Guardado" / error "No se pudo guardar. Reintenta."
  - `labels` prop overrides any subset of labels (i18n-ready).
  - `savedAt` Date shows relative time when `status=saved`.
  - Design-token classes (Tailwind) — no hardcoded hex.
  - Zero Clerk coupling (`AutosaveStatus` imported from `@luana/hooks`).
- **`AutosaveShowcase`** (examples/AutosaveShowcase.tsx) — consumer-of-reference that wires `useAutosave` + `<AutosaveBadge>` end-to-end without brand coupling (proves the ADR-012 contract typechecks).
- Barrel export: `export * from "./AutosaveBadge"` added to `src/index.ts`.
- 32 Vitest unit/component tests (`src/__tests__/AutosaveBadge.test.tsx`).

## [0.1.0] — initial

- Lift from `AISALESHT/frontend/src/components/ui/` — 43 Shadcn/UI primitive components.
